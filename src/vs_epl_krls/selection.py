"""Temporal model selection utilities focused on weekly Brazilian S10 prices.

This module deliberately keeps the final holdout separate from expanding
validation folds.  All feature and target scalers are fitted only on information
available before each validation origin, and labelled samples are revealed to
the online model only after their forecast horizon has elapsed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import time
from typing import Iterable, Literal

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .metrics import regression_report
from .model import VSEPLKRLS
from .utils import MinMaxScaler


FeatureSet = Literal["price", "lags", "dynamics", "exogenous"]
TargetMode = Literal["level", "delta"]

_CAUSAL_EXOGENOUS_COLUMNS = (
    "brent_l1",
    "usdbrl_l1",
    "brent_brl_l1",
    "petrobras_reajuste_l1",
)


@dataclass(frozen=True)
class S10Candidate:
    """A complete, serializable VS-ePL-KRLS candidate configuration."""

    candidate_id: str
    feature_set: FeatureSet
    target_mode: TargetMode
    alpha: float
    beta_initial: float
    alpha_vs1: float
    alpha_vs2: float
    error_threshold: float
    kernel_sigma: float
    regularization: float
    novelty_factor: float = 0.1
    max_dictionary_size: int = 24
    max_rules: int = 12
    beta_min: float = 1e-4
    beta_recovery_rate: float = 0.0
    forgetting_factor: float = 1.0
    dictionary_usage_decay: float = 1.0
    residual_correction_weight: float = 1.0
    residual_correction_limit: float | None = None
    center_update: Literal["paper", "compatibility"] = "compatibility"
    threshold_policy: Literal["dynamic", "fixed"] = "fixed"
    enable_rule_merging: bool = True
    adapt_kernel_width: bool = False

    def __post_init__(self) -> None:
        if (
            not np.isfinite(self.residual_correction_weight)
            or not 0 < self.residual_correction_weight <= 1
        ):
            raise ValueError("residual_correction_weight must be in (0, 1]")
        if self.residual_correction_limit is not None and (
            not np.isfinite(self.residual_correction_limit)
            or self.residual_correction_limit <= 0
        ):
            raise ValueError("residual_correction_limit must be finite and positive")

    def model_parameters(self) -> dict[str, object]:
        normalization = "none" if self.target_mode == "level" else "running_std"
        tau = self.beta_initial if self.threshold_policy == "fixed" else None
        gamma = 1.0 - self.beta_initial if self.threshold_policy == "fixed" else None
        return {
            "alpha": self.alpha,
            "beta_initial": self.beta_initial,
            "beta_min": self.beta_min,
            "beta_max": 0.95,
            "alpha_vs1": self.alpha_vs1,
            "alpha_vs2": self.alpha_vs2,
            "beta_recovery_rate": self.beta_recovery_rate,
            "error_threshold": self.error_threshold,
            "error_normalization": normalization,
            "arousal_threshold": tau,
            "merge_threshold": gamma,
            "enable_rule_merging": self.enable_rule_merging,
            "max_rules": self.max_rules,
            "center_update": self.center_update,
            "kernel_sigma": self.kernel_sigma,
            "regularization": self.regularization,
            "novelty_factor": self.novelty_factor,
            "max_dictionary_size": self.max_dictionary_size,
            "replacement_strategy": "least_used",
            "forgetting_factor": self.forgetting_factor,
            "dictionary_usage_decay": self.dictionary_usage_decay,
            "adapt_kernel_width": self.adapt_kernel_width,
            "input_bounds": (0.0, 1.0),
            "clip_inputs": False,
            "initial_prediction": 0.5 if self.target_mode == "level" else 0.0,
        }


@dataclass(frozen=True)
class TemporalFold:
    fold_id: str
    validation_start: int
    validation_end: int


@dataclass
class S10Supervised:
    """Origin-aligned weekly forecasting table."""

    x: NDArray[np.float64]
    target_price: NDArray[np.float64]
    origin_price: NDArray[np.float64]
    dates: NDArray[np.datetime64]
    target_dates: NDArray[np.datetime64]
    feature_names: tuple[str, ...]
    horizon: int

    @property
    def n_samples(self) -> int:
        return int(self.x.shape[0])


@dataclass
class FoldResult:
    candidate_id: str
    fold_id: str
    metrics: dict[str, float]
    naive_metrics: dict[str, float]
    rmse_ratio: float
    elapsed_seconds: float
    prediction_latency_ms_p95: float
    n_rules: int
    max_rules: int
    max_dictionary_size: int
    dictionary_replacements: int
    dictionary_replacement_rate: float
    predictions: NDArray[np.float64]
    actual: NDArray[np.float64]
    naive: NDArray[np.float64]
    dates: NDArray[np.datetime64]
    rule_counts: NDArray[np.int64]
    betas: NDArray[np.float64]
    dictionary_sizes: NDArray[np.int64]

    def summary_row(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "fold_id": self.fold_id,
            **self.metrics,
            "naive_rmse": self.naive_metrics["rmse"],
            "rmse_ratio": self.rmse_ratio,
            "elapsed_seconds": self.elapsed_seconds,
            "prediction_latency_ms_p95": self.prediction_latency_ms_p95,
            "n_rules": self.n_rules,
            "max_rules": self.max_rules,
            "max_dictionary_size": self.max_dictionary_size,
            "dictionary_replacements": self.dictionary_replacements,
            "dictionary_replacement_rate": self.dictionary_replacement_rate,
        }


def _validated_price_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if not {"date", "price"}.issubset(frame.columns):
        raise ValueError("S10 data must contain date and price columns")
    retained = ["date", "price"] + [
        column for column in _CAUSAL_EXOGENOUS_COLUMNS if column in frame.columns
    ]
    output = frame[retained].copy()
    output["date"] = pd.to_datetime(output["date"], errors="coerce")
    output["price"] = pd.to_numeric(output["price"], errors="coerce")
    for column in retained[2:]:
        output[column] = pd.to_numeric(output[column], errors="coerce")
    output = (
        output.dropna(subset=["date", "price"])
        .sort_values("date")
        .drop_duplicates("date")
        .reset_index(drop=True)
    )
    if len(output) < 80 or (output["price"] <= 0).any():
        raise ValueError("S10 data must contain at least 80 finite positive observations")
    return output


def build_s10_supervised(
    frame: pd.DataFrame,
    *,
    horizon: int = 1,
    feature_set: FeatureSet = "dynamics",
) -> S10Supervised:
    """Build causal features at origin ``t`` for the price at ``t+h``."""

    if horizon < 1:
        raise ValueError("horizon must be positive")
    feature_frame = build_s10_feature_frame(frame, feature_set=feature_set)
    feature_names = tuple(
        column for column in feature_frame.columns if column not in {"date", "price"}
    )
    table = feature_frame.copy()
    table["origin_price"] = table["price"]
    table["target_price"] = table["price"].shift(-horizon)
    table["target_date"] = table["date"].shift(-horizon)
    table = table.dropna().reset_index(drop=True)
    return S10Supervised(
        x=table[list(feature_names)].to_numpy(float),
        target_price=table["target_price"].to_numpy(float),
        origin_price=table["origin_price"].to_numpy(float),
        dates=table["date"].to_numpy(dtype="datetime64[ns]"),
        target_dates=table["target_date"].to_numpy(dtype="datetime64[ns]"),
        feature_names=feature_names,
        horizon=int(horizon),
    )


def build_s10_feature_frame(
    frame: pd.DataFrame,
    *,
    feature_set: FeatureSet = "dynamics",
) -> pd.DataFrame:
    """Return causal features through the latest, not-yet-labelled origin."""

    data = _validated_price_frame(frame)
    price = data["price"].astype(float)
    features = pd.DataFrame(index=data.index)
    if feature_set == "price":
        features["price_t"] = price
    elif feature_set == "lags":
        for lag in (0, 1, 2, 4, 8, 12):
            features[f"price_lag_{lag}"] = price.shift(lag)
    elif feature_set == "dynamics":
        features["price_t"] = price
        features["change_1"] = price.diff(1)
        features["change_2_avg"] = price.diff(2) / 2.0
        features["change_4_avg"] = price.diff(4) / 4.0
        features["change_8_avg"] = price.diff(8) / 8.0
        features["gap_ma4"] = price - price.rolling(4, min_periods=4).mean()
        features["gap_ma8"] = price - price.rolling(8, min_periods=8).mean()
        features["volatility_4"] = price.diff().rolling(4, min_periods=4).std(ddof=0)
        features["volatility_12"] = price.diff().rolling(12, min_periods=12).std(ddof=0)
    elif feature_set == "exogenous":
        missing = [column for column in _CAUSAL_EXOGENOUS_COLUMNS if column not in data]
        if missing:
            raise ValueError(f"exogenous feature set is missing causal columns: {missing}")
        features["price_t"] = price
        features["change_1"] = price.diff(1)
        features["change_4_avg"] = price.diff(4) / 4.0
        features["gap_ma8"] = price - price.rolling(8, min_periods=8).mean()
        features["volatility_12"] = price.diff().rolling(12, min_periods=12).std(ddof=0)
        for column in _CAUSAL_EXOGENOUS_COLUMNS:
            features[column] = data[column]
    else:
        raise ValueError(f"unsupported feature_set: {feature_set}")
    table = pd.DataFrame({"date": data["date"], "price": price})
    for column in features:
        table[column] = features[column]
    # Align every feature set to the same first eligible origin.
    table["_common_warmup"] = price.shift(12)
    return table.dropna().drop(columns=["_common_warmup"]).reset_index(drop=True)


def expanding_validation_folds(
    n_samples: int,
    *,
    holdout_size: int = 104,
    validation_size: int = 52,
    n_folds: int = 3,
    min_train_size: int = 156,
) -> tuple[list[TemporalFold], TemporalFold]:
    """Create expanding folds and a final untouched holdout."""

    if min(holdout_size, validation_size, n_folds, min_train_size) < 1:
        raise ValueError("fold sizes must be positive")
    development_end = n_samples - holdout_size
    first_start = development_end - n_folds * validation_size
    if first_start < min_train_size:
        raise ValueError("not enough samples for the requested temporal folds")
    folds = [
        TemporalFold(
            fold_id=f"validation_{index + 1}",
            validation_start=first_start + index * validation_size,
            validation_end=first_start + (index + 1) * validation_size,
        )
        for index in range(n_folds)
    ]
    holdout = TemporalFold("holdout", development_end, n_samples)
    return folds, holdout


def _target_values(data: S10Supervised, mode: TargetMode) -> NDArray[np.float64]:
    if mode == "level":
        return data.target_price.copy()
    if mode == "delta":
        return data.target_price - data.origin_price
    raise ValueError(f"unsupported target mode: {mode}")


def evaluate_temporal_fold(
    candidate: S10Candidate,
    data: S10Supervised,
    fold: TemporalFold,
) -> FoldResult:
    """Evaluate one candidate with delayed prequential target revelation."""

    start, end = fold.validation_start, fold.validation_end
    if not data.horizon <= start < end <= data.n_samples:
        raise ValueError("invalid temporal fold bounds")
    known_end = start - data.horizon
    x_scaler = MinMaxScaler().fit(data.x[:start])
    x_scaled = np.clip(x_scaler.transform(data.x), 0.0, 1.0)
    raw_target = _target_values(data, candidate.target_mode)
    target_scaler: MinMaxScaler | None = None
    if candidate.target_mode == "level":
        target_scaler = MinMaxScaler().fit(raw_target[:known_end])
        model_target = target_scaler.transform(raw_target)
    else:
        model_target = raw_target

    model = VSEPLKRLS(**candidate.model_parameters())
    started = time.perf_counter()
    learned_until = -1
    for index in range(known_end):
        model.learn_one(x_scaled[index], float(model_target[index]))
        learned_until = index

    model_predictions: list[float] = []
    latencies: list[float] = []
    rule_counts: list[int] = []
    betas: list[float] = []
    dictionary_sizes: list[int] = []
    for index in range(start, end):
        newly_available = index - data.horizon
        if newly_available > learned_until:
            model.learn_one(x_scaled[newly_available], float(model_target[newly_available]))
            learned_until = newly_available
        prediction_started = time.perf_counter_ns()
        model_predictions.append(model.predict_one(x_scaled[index]))
        latencies.append((time.perf_counter_ns() - prediction_started) / 1e6)
        current_summary = model.summary()
        rule_counts.append(model.n_rules)
        betas.append(model.beta_)
        dictionary_sizes.append(int(current_summary["max_dictionary_size"]))
    elapsed = time.perf_counter() - started

    model_array = np.asarray(model_predictions, dtype=float)
    if target_scaler is not None:
        price_prediction = target_scaler.inverse_transform(model_array)
    else:
        price_prediction = data.origin_price[start:end] + model_array
    actual = data.target_price[start:end]
    naive = data.origin_price[start:end]
    metrics = regression_report(actual, price_prediction)
    naive_metrics = regression_report(actual, naive)
    summary = model.summary()
    return FoldResult(
        candidate_id=candidate.candidate_id,
        fold_id=fold.fold_id,
        metrics=metrics,
        naive_metrics=naive_metrics,
        rmse_ratio=float(metrics["rmse"] / max(naive_metrics["rmse"], 1e-12)),
        elapsed_seconds=float(elapsed),
        prediction_latency_ms_p95=float(np.quantile(latencies, 0.95)),
        n_rules=int(summary["n_rules"]),
        max_rules=int(summary["max_rules_observed"]),
        max_dictionary_size=int(summary["max_dictionary_size"]),
        dictionary_replacements=int(summary["dictionary_replacements"]),
        dictionary_replacement_rate=float(summary["dictionary_replacement_rate"]),
        predictions=np.asarray(price_prediction, dtype=float),
        actual=actual.copy(),
        naive=naive.copy(),
        dates=data.target_dates[start:end].copy(),
        rule_counts=np.asarray(rule_counts, dtype=np.int64),
        betas=np.asarray(betas, dtype=float),
        dictionary_sizes=np.asarray(dictionary_sizes, dtype=np.int64),
    )


def candidate_grid(
    *,
    horizon: int,
    random_state: int = 42,
    n_random: int = 36,
) -> list[S10Candidate]:
    """Return source-informed seeds plus a deterministic compact random search."""

    if horizon < 1 or n_random < 0:
        raise ValueError("horizon and n_random are invalid")
    candidates: list[S10Candidate] = []
    if horizon == 2:
        source = (0.02, 0.05, 0.94, 0.74, 0.001)
    elif horizon == 4:
        source = (0.26, 0.01, 0.89, 0.62, 0.002)
    else:
        source = (0.05, 0.03, 0.94, 0.74, 0.003)
    for feature_set in ("price", "lags", "dynamics"):
        candidates.append(
            S10Candidate(
                candidate_id=f"source_{feature_set}_level",
                feature_set=feature_set,  # type: ignore[arg-type]
                target_mode="level",
                alpha=source[0],
                beta_initial=source[1],
                alpha_vs1=source[2],
                alpha_vs2=source[3],
                error_threshold=source[4],
                kernel_sigma=0.5,
                regularization=1e-4,
                center_update="paper",
                threshold_policy="fixed",
            )
        )

    rng = np.random.default_rng(random_state + horizon)
    combinations = [
        (feature, target)
        for feature in ("price", "lags", "dynamics")
        for target in ("level", "delta")
    ]
    for index in range(n_random):
        feature_set, target_mode = combinations[index % len(combinations)]
        threshold_values = (0.001, 0.003, 0.01, 0.03) if target_mode == "level" else (0.5, 0.8, 1.0, 1.5)
        alpha_vs1, alpha_vs2 = ((0.94, 0.74), (0.89, 0.62), (0.97, 0.84))[int(rng.integers(0, 3))]
        candidates.append(
            S10Candidate(
                candidate_id=f"random_{index:03d}_{feature_set}_{target_mode}",
                feature_set=feature_set,  # type: ignore[arg-type]
                target_mode=target_mode,  # type: ignore[arg-type]
                alpha=float(rng.choice([0.01, 0.03, 0.08, 0.15, 0.26])),
                beta_initial=float(rng.choice([0.01, 0.03, 0.05, 0.10, 0.18])),
                alpha_vs1=alpha_vs1,
                alpha_vs2=alpha_vs2,
                error_threshold=float(rng.choice(threshold_values)),
                kernel_sigma=float(rng.choice([0.08, 0.15, 0.25, 0.5, 0.8])),
                regularization=float(rng.choice([1e-4, 1e-3, 1e-2])),
                novelty_factor=float(rng.choice([0.05, 0.1, 0.2])),
                max_dictionary_size=int(rng.choice([12, 20, 30])),
                max_rules=int(rng.choice([6, 12, 20])),
                center_update=str(rng.choice(["paper", "compatibility"])),  # type: ignore[arg-type]
                threshold_policy=str(rng.choice(["fixed", "dynamic"])),  # type: ignore[arg-type]
                enable_rule_merging=bool(rng.choice([True, False])),
                adapt_kernel_width=False,
            )
        )
    return candidates


def rank_candidates(
    candidates: Iterable[S10Candidate],
    datasets: dict[FeatureSet, S10Supervised],
    folds: Iterable[TemporalFold],
) -> tuple[pd.DataFrame, list[FoldResult]]:
    """Evaluate candidates and rank by accuracy plus cross-fold instability."""

    all_results: list[FoldResult] = []
    candidate_lookup: dict[str, S10Candidate] = {}
    for candidate in candidates:
        candidate_lookup[candidate.candidate_id] = candidate
        data = datasets[candidate.feature_set]
        all_results.extend(evaluate_temporal_fold(candidate, data, fold) for fold in folds)
    rows = pd.DataFrame([result.summary_row() for result in all_results])
    grouped = rows.groupby("candidate_id", as_index=False).agg(
        mean_rmse=("rmse", "mean"),
        worst_rmse=("rmse", "max"),
        mean_rmse_ratio=("rmse_ratio", "mean"),
        worst_rmse_ratio=("rmse_ratio", "max"),
        rmse_ratio_std=("rmse_ratio", "std"),
        mean_mae=("mae", "mean"),
        mean_smape=("smape", "mean"),
        latency_ms_p95=("prediction_latency_ms_p95", "max"),
        max_rules=("max_rules", "max"),
        max_dictionary_size=("max_dictionary_size", "max"),
        dictionary_replacements=("dictionary_replacements", "max"),
        dictionary_replacement_rate=("dictionary_replacement_rate", "max"),
    )
    grouped["selection_score"] = (
        grouped["mean_rmse_ratio"]
        + 0.20 * grouped["worst_rmse_ratio"]
        + 0.10 * grouped["rmse_ratio_std"].fillna(0.0)
    )
    grouped["beats_naive_all_folds"] = grouped["worst_rmse_ratio"] < 1.0
    grouped["candidate"] = grouped["candidate_id"].map(
        lambda identifier: asdict(candidate_lookup[str(identifier)])
    )
    grouped = grouped.sort_values(
        ["selection_score", "mean_rmse", "latency_ms_p95"],
        ignore_index=True,
    )
    return grouped, all_results
