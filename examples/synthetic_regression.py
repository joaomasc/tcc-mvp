"""Reproducible nonlinear stream with an abrupt regime change."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vs_epl_krls import EPLKRLSFixedBeta, VSEPLKRLS, regression_report


def make_stream(n_samples: int = 480, random_state: int = 42) -> tuple[np.ndarray, np.ndarray, int]:
    """Return bounded features/target and the known change-point index."""

    if n_samples < 100:
        raise ValueError("n_samples must be at least 100")
    rng = np.random.default_rng(random_state)
    time_axis = np.linspace(0.0, 1.0, n_samples)
    change = n_samples // 2
    target = np.empty(n_samples)
    target[:change] = 0.42 + 0.22 * np.sin(8.0 * np.pi * time_axis[:change])
    shifted = time_axis[change:] - time_axis[change]
    target[change:] = 0.55 + 0.17 * np.sin(18.0 * np.pi * shifted) + 0.14 * shifted
    target += rng.normal(0.0, 0.025, n_samples)
    target = np.clip(target, 0.01, 0.99)
    previous = np.r_[0.5, target[:-1]]
    features = np.column_stack((time_axis, previous))
    return features, target, change


def _run(model: VSEPLKRLS, x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float]:
    started = time.perf_counter()
    predictions = np.asarray([model.learn_one(row, target) for row, target in zip(x, y)])
    return predictions, time.perf_counter() - started


def run_experiment(
    *,
    output_dir: Path,
    n_samples: int = 480,
    random_state: int = 42,
) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    x, y, change = make_stream(n_samples, random_state)
    common = dict(
        alpha=0.04,
        beta_initial=0.18,
        beta_min=0.01,
        beta_max=0.80,
        alpha_vs1=0.90,
        alpha_vs2=0.78,
        error_threshold=0.04,
        error_normalization="none",
        kernel_sigma=0.18,
        regularization=1e-3,
        max_dictionary_size=30,
        replacement_strategy="least_used",
        max_rules=12,
        adapt_kernel_width=True,
        center_update="paper",
        random_state=random_state,
    )
    models: dict[str, VSEPLKRLS] = {
        "VS-ePL-KRLS": VSEPLKRLS(**common),
        "ePL-KRLS beta fixo": EPLKRLSFixedBeta(**common),
    }
    warmup = max(30, n_samples // 10)
    rows: list[dict[str, object]] = []
    traces: dict[str, tuple[np.ndarray, list[dict[str, object]]]] = {}
    final_dictionaries: list[dict[str, object]] = []
    for name, model in models.items():
        predictions, elapsed = _run(model, x, y)
        measured = regression_report(y[warmup:], predictions[warmup:])
        summary = model.summary()
        rows.append(
            {
                "model": name,
                **measured,
                "final_rules": summary["n_rules"],
                "max_rules": summary["max_rules_observed"],
                "rule_creations": summary["rule_creations"],
                "rule_merges": summary["rule_merges"],
                "mean_dictionary_size": summary["mean_dictionary_size"],
                "max_dictionary_size": summary["max_dictionary_size"],
                "elapsed_seconds": elapsed,
                "evaluation_start": warmup,
            }
        )
        traces[name] = (predictions, model.get_history())
        slug = "variable" if name.startswith("VS") else "fixed"
        (output_dir / f"rules_{slug}.json").write_text(
            json.dumps(model.get_rules(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        for rule in model.get_rules():
            final_dictionaries.append(
                {
                    "model": name,
                    "rule_id": rule["id"],
                    "dictionary_size": rule["krls"]["dictionary_size"],
                    "activations": rule["activations"],
                    "arousal": rule["arousal"],
                }
            )

    naive_predictions = x[:, 1].copy()
    rows.append(
        {
            "model": "Persistência",
            **regression_report(y[warmup:], naive_predictions[warmup:]),
            "final_rules": 0,
            "max_rules": 0,
            "rule_creations": 0,
            "rule_merges": 0,
            "mean_dictionary_size": 0.0,
            "max_dictionary_size": 0,
            "elapsed_seconds": 0.0,
            "evaluation_start": warmup,
        }
    )

    results = pd.DataFrame(rows)
    results.to_csv(output_dir / "metrics.csv", index=False)
    (output_dir / "metrics.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    trace_frame = pd.DataFrame({"step": np.arange(n_samples), "target": y})
    trace_frame["prediction_naive"] = naive_predictions
    trace_frame["error_naive"] = y - naive_predictions
    for name, (predictions, history) in traces.items():
        slug = "variable" if name.startswith("VS") else "fixed"
        trace_frame[f"prediction_{slug}"] = predictions
        trace_frame[f"error_{slug}"] = y - predictions
        trace_frame[f"beta_{slug}"] = [event["beta"] for event in history]
        trace_frame[f"rules_{slug}"] = [event["n_rules"] for event in history]
        trace_frame[f"dictionary_total_{slug}"] = [event["dictionary_size_total"] for event in history]
    trace_frame.to_csv(output_dir / "trace.csv", index=False)
    pd.DataFrame(final_dictionaries).to_csv(output_dir / "final_dictionaries.csv", index=False)

    figure, axes = plt.subplots(5, 1, figsize=(12, 14), sharex=True)
    axes[0].plot(y, color="black", linewidth=1.4, label="real")
    axes[0].plot(naive_predictions, linewidth=0.8, alpha=0.55, label="persistência")
    for name, (predictions, _) in traces.items():
        axes[0].plot(predictions, linewidth=1.0, alpha=0.85, label=name)
    axes[0].set_ylabel("y")
    axes[0].legend(ncol=3, fontsize=8)
    for name, (predictions, _) in traces.items():
        axes[1].plot(y - predictions, linewidth=0.9, label=name)
    axes[1].plot(y - naive_predictions, linewidth=0.8, alpha=0.55, label="persistência")
    axes[1].axhline(0.0, color="black", linewidth=0.6)
    axes[1].set_ylabel("erro")
    for name, (_, history) in traces.items():
        axes[2].plot([event["beta"] for event in history], label=name)
        axes[3].step(
            np.arange(n_samples),
            [event["n_rules"] for event in history],
            where="post",
            label=name,
        )
        creation_steps = [
            int(event["step"])
            for event in history
            if str(event["action"]).startswith("created")
        ]
        axes[3].scatter(creation_steps, [history[index]["n_rules"] for index in creation_steps], s=18)
        axes[4].plot(
            [event["dictionary_size_total"] for event in history],
            linewidth=1.0,
            label=name,
        )
    axes[2].set_ylabel("beta")
    axes[3].set_ylabel("regras")
    axes[4].set_ylabel("dicionário total")
    axes[4].set_xlabel("amostra")
    for axis in axes:
        axis.axvline(change, color="tab:red", linestyle="--", linewidth=1.0)
        axis.grid(alpha=0.2)
    figure.suptitle("Regressão online com mudança de regime")
    figure.tight_layout()
    figure.savefig(output_dir / "synthetic_regression.png", dpi=150)
    plt.close(figure)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports" / "vs_epl_krls" / "synthetic")
    parser.add_argument("--n-samples", type=int, default=480)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()
    results = run_experiment(
        output_dir=args.output_dir,
        n_samples=args.n_samples,
        random_state=args.random_state,
    )
    print(results.to_string(index=False))
    print(f"Artifacts: {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
