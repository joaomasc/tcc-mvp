from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import pytest

from vs_epl_krls.production import S10ProductionForecaster
from vs_epl_krls.selection import S10Candidate


def _history(n: int = 100) -> pd.DataFrame:
    index = np.arange(n, dtype=float)
    return pd.DataFrame(
        {
            "date": pd.date_range("2023-01-01", periods=n, freq="7D"),
            "price": 5.5 + 0.004 * index + 0.05 * np.sin(index / 7.0),
        }
    )


def _candidate() -> S10Candidate:
    return S10Candidate(
        candidate_id="production-test",
        feature_set="price",
        target_mode="delta",
        alpha=0.05,
        beta_initial=0.03,
        alpha_vs1=0.94,
        alpha_vs2=0.74,
        error_threshold=1.0,
        kernel_sigma=0.5,
        regularization=1e-3,
        novelty_factor=0.2,
        max_dictionary_size=4,
        enable_rule_merging=False,
        adapt_kernel_width=False,
    )


@pytest.fixture
def bundle() -> S10ProductionForecaster:
    residuals = np.linspace(-0.08, 0.09, 40)
    return S10ProductionForecaster(
        _candidate(),
        calibration_residuals=residuals,
        fallback_calibration_residuals=residuals * 2,
    ).fit(_history())


def test_fit_predict_and_metadata_contract(bundle):
    forecast = bundle.predict_next()
    assert np.isfinite([forecast.point, forecast.p10, forecast.p90]).all()
    assert 0 < forecast.p10 <= forecast.point <= forecast.p90
    assert forecast.primary_model == "ARIMA"
    assert forecast.point == forecast.components["ARIMA"]
    assert set(forecast.components) == {
        "ARIMA", "Ridge", "persistencia", "VS-ePL-KRLS", "ensemble"
    }
    assert pd.Timestamp(forecast.target_date) - pd.Timestamp(forecast.last_observed_date) == pd.Timedelta(days=7)
    metadata = bundle.metadata()
    assert metadata["scope"].startswith("Diesel B S10")
    assert metadata["n_observations"] == 100
    assert len(metadata["data_fingerprint"]) == 64
    assert metadata["artifact_version"] == "1.1.0"
    assert metadata["interval_monitor_samples"] == 0


def test_atomic_roundtrip_is_exact(bundle, tmp_path):
    destination = bundle.save(tmp_path / "model.joblib")
    assert destination.exists()
    assert not (tmp_path / "model.joblib.tmp").exists()
    restored = S10ProductionForecaster.load(destination)
    assert restored.predict_next().as_dict() == bundle.predict_next().as_dict()
    expected = S10ProductionForecaster._file_sha256(destination)
    assert S10ProductionForecaster.load(destination, expected_sha256=expected).metadata()
    with pytest.raises(RuntimeError, match="SHA-256"):
        S10ProductionForecaster.load(destination, expected_sha256="0" * 64)


def test_online_update_changes_fingerprint_and_rejects_bad_updates(bundle):
    before = bundle.data_fingerprint_
    calibration_before = bundle.calibration_residuals.copy()
    forecast_before = bundle.predict_next()
    next_date = pd.Timestamp(bundle.training_end_) + pd.Timedelta(days=7)
    bundle.update_one(next_date, 5.95)
    assert bundle.metadata()["online_updates"] == 1
    assert bundle.data_fingerprint_ != before
    assert bundle.health().last_cadence_days == 7
    assert bundle.calibration_residuals.size == calibration_before.size + 1
    assert bundle.last_forecast_residual_ == pytest.approx(5.95 - forecast_before.point)
    assert bundle.calibration_residuals[-1] == pytest.approx(
        bundle.last_forecast_residual_
    )
    assert bundle.health().interval_monitor_samples == 1
    assert bundle.health().empirical_interval_coverage in {0.0, 1.0}
    assert bundle.health().recent_mae == pytest.approx(
        abs(bundle.last_forecast_residual_)
    )
    with pytest.raises(ValueError, match="after"):
        bundle.update_one(next_date, 5.96)
    with pytest.raises(ValueError, match="positive"):
        bundle.update_one(next_date + pd.Timedelta(days=7), np.nan)
    with pytest.raises(ValueError, match="robust limit"):
        bundle.update_one(next_date + pd.Timedelta(days=7), 50.0)


def test_health_reports_cadence_and_capacity_pressure(bundle):
    next_date = pd.Timestamp(bundle.training_end_) + pd.Timedelta(days=14)
    bundle.update_one(next_date, float(bundle.history_["price"].iloc[-1]))
    health = bundle.health()
    assert health.status == "warning"
    assert health.last_cadence_days == 14
    assert "unexpected_observation_cadence" in health.warnings
    assert "beta_floor_pressure" in health.warnings
    assert 0 <= health.rule_capacity_fraction <= 1
    assert 0 <= health.dictionary_capacity_fraction <= 1
    assert health.dictionary_replacements >= 0
    assert 0 <= health.dictionary_replacement_rate <= 1


def test_health_warns_on_sustained_interval_undercoverage(bundle):
    bundle.online_interval_hits_ = [False] * 20
    bundle.online_absolute_errors_ = [0.2] * 20
    health = bundle.health()
    assert health.empirical_interval_coverage == 0.0
    assert health.recent_mae == pytest.approx(0.2)
    assert "interval_coverage_degradation" in health.warnings


def test_initial_calibration_is_bounded_to_recent_window():
    model = S10ProductionForecaster(
        _candidate(),
        calibration_residuals=np.arange(40, dtype=float),
        fallback_calibration_residuals=np.arange(40, dtype=float),
        calibration_window=20,
    )
    assert model.calibration_residuals.tolist() == list(np.arange(20, 40, dtype=float))
    assert model.fallback_calibration_residuals.size == 20


def test_guardrail_uses_persistence_when_arima_primary_is_implausible(bundle, monkeypatch):
    last = float(bundle.history_["price"].iloc[-1])
    values = {
        "ARIMA": last + 50.0,
        "Ridge": last,
        "persistencia": last,
        "VS-ePL-KRLS": last,
        "ensemble": last,
    }
    monkeypatch.setattr(bundle, "_component_predictions", lambda: (values, 0.0))
    forecast = bundle.predict_next()
    assert forecast.fallback_used
    assert forecast.fallback_reason == "implausible_weekly_change"
    assert forecast.point == last


def test_guardrail_uses_safe_arima_for_an_implausible_challenger(monkeypatch):
    model = S10ProductionForecaster(
        _candidate(), primary_model="VS-ePL-KRLS"
    ).fit(_history())
    last = float(model.history_["price"].iloc[-1])
    values = {
        "ARIMA": last + 0.01,
        "Ridge": last,
        "persistencia": last,
        "VS-ePL-KRLS": last + 50.0,
        "ensemble": last,
    }
    monkeypatch.setattr(model, "_component_predictions", lambda: (values, 0.0))
    assert model.predict_next().point == pytest.approx(last + 0.01)


def test_predict_is_thread_safe_and_does_not_mutate_history(bundle):
    before = bundle.data_fingerprint_
    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(lambda _: bundle.predict_next().as_dict(), range(12)))
    assert all(output == outputs[0] for output in outputs)
    assert bundle.data_fingerprint_ == before


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"primary_model": "bad"}, "primary_model"),
        ({"ensemble_weights": (0.5, 0.5, 0.5, 0.5)}, "sum to one"),
        ({"ensemble_weights": (1.0, -1.0, 1.0, 0.0)}, "non-negative"),
        ({"calibration_residuals": [0.0] * 19}, "at least 20"),
        ({"fallback_calibration_residuals": [0.0] * 19}, "at least 20"),
        ({"expected_frequency_days": 0}, "positive"),
        ({"calibration_window": 19}, "at least 20"),
    ],
)
def test_constructor_rejects_invalid_operational_configuration(kwargs, message):
    with pytest.raises(ValueError, match=message):
        S10ProductionForecaster(_candidate(), **kwargs)


def test_history_schema_and_fitted_state_are_enforced(tmp_path):
    model = S10ProductionForecaster(_candidate())
    with pytest.raises(RuntimeError, match="not been fitted"):
        model.predict_next()
    with pytest.raises(ValueError, match="date and price"):
        model.fit(pd.DataFrame({"date": pd.date_range("2024-01-01", periods=80)}))
    duplicated = _history()
    duplicated.loc[1, "date"] = duplicated.loc[0, "date"]
    with pytest.raises(ValueError, match="unique"):
        model.fit(duplicated)
    wrong = tmp_path / "wrong.joblib"
    import joblib

    joblib.dump({"not": "a bundle"}, wrong)
    with pytest.raises(TypeError, match="not an S10"):
        S10ProductionForecaster.load(wrong)


def test_old_artifact_version_is_rejected(bundle, tmp_path):
    import joblib

    bundle.artifact_version_ = "1.0.0"
    path = tmp_path / "old.joblib"
    joblib.dump(bundle, path)
    with pytest.raises(RuntimeError, match="unsupported artifact version"):
        S10ProductionForecaster.load(path)
