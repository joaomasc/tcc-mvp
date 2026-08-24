from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from vsepl_krls.model import VSePLKRLSConfig


def test_download_script_main_reports_gate(monkeypatch, capsys, load_script, tmp_path):
    script = load_script("01_download.py")
    raw_file = tmp_path / "raw.xlsx"
    raw_file.write_bytes(b"x")
    monkeypatch.setattr(script, "download_all", lambda: {"mensal": raw_file})
    monkeypatch.setattr(
        script,
        "save_processed",
        lambda: {
            "gate": {
                "ok": True,
                "observed": {"n": 90, "mean": 3.1},
                "expected": {"n": 90, "mean": 3.1},
                "diffs": {"n": 0, "mean": 0.0},
            },
            "monthly": pd.DataFrame(index=range(2)),
            "weekly": pd.DataFrame(index=range(3)),
            "paper": pd.DataFrame(index=range(1)),
        },
    )
    script.main()
    output = capsys.readouterr().out
    assert "Arquivos baixados" in output
    assert "ok = True" in output
    assert "Semanal completo: 3" in output


def test_reproduction_run_one_returns_finite_contract(load_script):
    script = load_script("02_reproducao.py")
    X = np.column_stack([np.linspace(0, 1, 25), np.linspace(1, 2, 25)])
    y = 2.0 + 0.2 * X[:, 0]
    metrics, preds, yte, model = script.run_one(
        X,
        y,
        n_train=18,
        cfg=VSePLKRLSConfig(use_variable_step=False, d_max=5),
    )
    assert len(preds) == len(yte) == 7
    assert np.isfinite(preds).all()
    assert metrics["n_rules"] == model.n_rules
    assert {"rmse", "mae", "ndei_full", "beta_final"}.issubset(metrics)


def test_reproduction_experiment_builds_expected_configuration(monkeypatch, load_script):
    script = load_script("02_reproducao.py")
    frame = pd.DataFrame({"revenda": np.arange(90.0), "distribuicao": np.arange(90.0)})
    monkeypatch.setattr(script.pd, "read_csv", lambda *args, **kwargs: frame)
    monkeypatch.setattr(
        script,
        "make_supervised",
        lambda *args, **kwargs: (np.ones((89, 2)), np.ones(89), np.arange(89)),
    )

    class Model:
        history_n_rules = [1]
        history_beta = [0.2]

    monkeypatch.setattr(
        script,
        "run_one",
        lambda X, y, n_train, cfg: (
            {"rmse": 1.0, "mae": 1.0, "ndei": 1.0, "n_rules": 1, "beta_final": 0.2},
            np.array([1.0]),
            np.array([1.0]),
            Model(),
        ),
    )
    result = script.experiment(1, "texto", True)
    assert result["horizon"] == 1
    assert result["convention"] == "texto"
    assert result["variable_step"] is True
    assert result["n_train"] == 72
    assert result["n_rules_path"] == [1]


@pytest.mark.integration
def test_reproduction_main_writes_table_json_plot_and_report(monkeypatch, load_script, tmp_path):
    script = load_script("02_reproducao.py")
    proc = tmp_path / "processed"
    res = tmp_path / "results"
    fig = tmp_path / "figures"
    rep = tmp_path / "reports"
    proc.mkdir()
    pd.DataFrame(
        {
            "data": pd.date_range("2012-12-01", periods=3, freq="MS"),
            "revenda": [3.0, 3.1, 3.2],
            "distribuicao": [2.8, 2.9, 3.0],
        }
    ).to_csv(proc / "mensal_s10_artigo.csv", index=False)

    def fake_experiment(horizon, convention, vs):
        base = 0.05 + 0.001 * horizon + (0.001 if convention == "texto" else 0.0)
        return {
            "horizon": horizon,
            "convention": convention,
            "variable_step": vs,
            "n_pairs": 80,
            "n_train": 60,
            "n_test": 2,
            "metrics": {
                "rmse": base,
                "mae": base,
                "ndei": base,
                "ndei_full": base,
                "n_rules": 1.0,
                "beta_final": 0.2,
            },
            "preds": [3.1, 3.2],
            "y_test": [3.1, 3.2],
            "n_rules_path": [1],
            "beta_path": [0.2],
        }

    monkeypatch.setattr(script, "PROC", proc)
    monkeypatch.setattr(script, "RES", res)
    monkeypatch.setattr(script, "FIG", fig)
    monkeypatch.setattr(script, "REP", rep)
    monkeypatch.setattr(script, "experiment", fake_experiment)
    script.main()
    table = pd.read_csv(res / "reproducao_mensal.csv")
    assert len(table) == 12
    assert (res / "reproducao_mensal.json").exists()
    assert (fig / "reproducao_h1.png").exists()
    assert "Bloco 1" in (rep / "01_reproducao.md").read_text(encoding="utf-8")


def test_weekly_scaling_panel_and_simple_predictors(monkeypatch, load_script, tmp_path):
    script = load_script("03_semanal.py")
    Xtr = np.array([[0.0, 2.0], [2.0, 2.0]])
    Xte = np.array([[1.0, 5.0]])
    scaled_tr, scaled_te, lo, span = script.minmax_train(Xtr, Xte)
    assert np.allclose(scaled_tr[:, 0], [0.0, 1.0])
    assert scaled_te[0, 0] == 0.5
    assert span[1] == 1.0
    frozen, _, _ = script.scale_frozen(np.vstack([Xtr, Xte]), n_min=2)
    assert frozen[-1, 1] == 1.25

    dates = pd.date_range("2021-01-03", periods=30, freq="7D")
    frame = pd.DataFrame(
        {
            "data": dates,
            "revenda": np.linspace(4.0, 5.0, 30),
            "revenda_l1": np.linspace(3.9, 4.9, 30),
            "brent_l1": np.linspace(50, 60, 30),
            "usdbrl_l1": np.linspace(4, 5, 30),
        }
    )
    frame.to_csv(tmp_path / "semanal_s10_features.csv", index=False)
    monkeypatch.setattr(script, "PROC", tmp_path)
    panel = script.load_panel(horizon=2)
    assert len(panel) == 28
    assert panel.loc[0, "y"] == pytest.approx(frame.loc[2, "revenda"])
    assert script.run_naive(np.array([1.0, 2.0, 3.0]), 1).tolist()[1:] == [2.0, 3.0]
    assert np.isfinite(script.run_ma(np.arange(1.0, 8.0), 2, window=2)[2:]).all()


def test_eval_model_aligns_conformal_coverage(load_script):
    script = load_script("03_semanal.py")
    y = np.linspace(4.0, 6.0, 80)
    residual_pattern = np.tile(np.array([-0.1, -0.05, 0.0, 0.05, 0.1]), 16)
    yhat = y - residual_pattern
    y_prev = y - 0.02
    metrics, residuals, lo, hi, mask, errors = script.eval_model(
        "modelo",
        y,
        yhat,
        y_prev,
        n_min=10,
    )
    assert metrics["coverage_p10_p90"] > 0.5
    assert 0.0 <= metrics["coverage_p10_p90"] <= 1.0
    assert len(residuals) == len(lo) == len(hi) == len(mask)
    assert len(errors) == int(mask.sum())


def test_weekly_model_runners_have_leak_safe_shapes(monkeypatch, load_script):
    script = load_script("03_semanal.py")
    X = np.column_stack([np.linspace(0, 1, 28), np.linspace(1, 2, 28)])
    y = np.linspace(4.0, 5.0, 28)
    price = y - 0.01
    vsepl, model, scaler = script.run_vsepl(X, y, n_min=5, horizon=2)
    assert np.isnan(vsepl[:5]).all()
    assert np.isfinite(vsepl[5:]).all()
    assert model.n_seen == len(y) - 2
    assert len(scaler) == 2

    arima_calls = []

    def fake_arima(history, steps, model=None):
        arima_calls.append((len(history), model is None))
        return np.repeat(history[-1], steps), object()

    monkeypatch.setattr(script, "arima_forecast", fake_arima)
    arima = script.run_arima(price, n_min=5, horizon=2, refit_every=3)
    assert np.isnan(arima[:5]).all()
    assert np.isfinite(arima[5:]).all()
    assert any(is_new for _, is_new in arima_calls)

    arimax_calls = []

    def fake_arimax(history, Xhist, Xfuture, steps, model=None):
        arimax_calls.append((len(history), model is None))
        return np.repeat(history[-1], steps), object()

    monkeypatch.setattr(script, "arimax_forecast", fake_arimax)
    arimax = script.run_arimax(price, X, n_min=5, horizon=2, refit_every=3)
    assert np.isfinite(arimax[5:]).all()
    assert arimax_calls

    monkeypatch.setattr(script, "fit_lgbm", lambda Xtr, ytr: FakePredictor(float(np.mean(ytr))))
    gbm_pred, fitted = script.run_gbm("lgbm", X, y, n_min=5, horizon=2, refit_every=3)
    assert fitted is not None
    assert np.isfinite(gbm_pred).sum() > 0
    monkeypatch.setattr(script, "fit_xgb", lambda Xtr, ytr: FakePredictor(float(np.mean(ytr))))
    xgb_pred, _ = script.run_gbm("xgb", X, y, n_min=5, horizon=2, refit_every=3)
    assert np.isfinite(xgb_pred).sum() > 0

    monkeypatch.setattr(script, "fit_lstm", lambda *args, **kwargs: object())
    monkeypatch.setattr(script, "predict_lstm", lambda *args, **kwargs: 4.5)
    lstm = script.run_lstm_wf(X, y, n_min=5, horizon=2, refit_every=3, seq_len=2)
    assert np.isfinite(lstm).sum() > 0


def test_markdown_table_and_forecast_plot(load_script, tmp_path):
    script = load_script("03_semanal.py")
    table = script.md_table(pd.DataFrame([{"modelo": "A", "rmse": 0.123456}]))
    assert "| modelo | rmse |" in table
    assert "0.12346" in table
    dates = pd.date_range("2024-01-01", periods=3)
    path = tmp_path / "forecast.png"
    script.plot_forecast(
        dates,
        np.array([1.0, 2.0, 3.0]),
        np.array([1.1, 1.9, 3.1]),
        np.array([0.9, 1.7, 2.8]),
        np.array([1.3, 2.1, 3.3]),
        "teste",
        path,
    )
    assert path.exists()


class FakePredictor:
    def __init__(self, value):
        self.value = value

    def predict(self, X):
        return np.repeat(self.value, len(X))


class FakeVS:
    n_rules = 2

    def __init__(self):
        self.updated = []

    def update(self, x, y):
        self.updated.append((np.asarray(x), y))

    def predict_one(self, x):
        return 8.5


def test_forecast_next_model_dispatches_every_supported_model(monkeypatch, load_script):
    script = load_script("03_semanal.py")
    price = np.array([4.0, 4.1, 4.2, 4.3])
    X = np.arange(24, dtype=float).reshape(12, 2)
    y = np.linspace(4.0, 5.0, 12)
    x_next = np.array([25.0, 26.0])
    Xex = np.arange(8, dtype=float).reshape(4, 2)

    monkeypatch.setattr(script, "arima_forecast", lambda *args, **kwargs: (np.array([7.1]), object()))
    monkeypatch.setattr(script, "arimax_forecast", lambda *args, **kwargs: (np.array([7.2]), object()))
    monkeypatch.setattr(script, "fit_lgbm", lambda *args, **kwargs: FakePredictor(7.3))
    monkeypatch.setattr(script, "fit_xgb", lambda *args, **kwargs: FakePredictor(7.4))
    monkeypatch.setattr(script, "fit_lstm", lambda *args, **kwargs: object())
    monkeypatch.setattr(script, "predict_lstm", lambda *args, **kwargs: 7.5)

    assert script.forecast_next_model("ARIMA", price, X, y, x_next, Xex)[0] == 7.1
    assert script.forecast_next_model("ARIMAX", price, X, y, x_next, Xex)[0] == 7.2
    assert script.forecast_next_model("naive", price, X, y, x_next, Xex)[0] == 4.3
    assert script.forecast_next_model("media_movel", price, X, y, x_next, Xex)[0] == pytest.approx(4.15)
    assert script.forecast_next_model("LightGBM", price, X, y, x_next, Xex)[0] == 7.3
    assert script.forecast_next_model("XGBoost", price, X, y, x_next, Xex)[0] == 7.4
    assert script.forecast_next_model("LSTM", price, X, y, x_next, Xex)[0] == 7.5

    vs = FakeVS()
    point, meta = script.forecast_next_model(
        "VS-ePL-KRLS",
        price,
        X,
        y,
        x_next,
        Xex,
        vs_model=vs,
        vs_scaler=(np.zeros(2), np.ones(2)),
    )
    assert point == 8.5
    assert meta == {"n_regras": 2}
    assert len(vs.updated) == 1
    with pytest.raises(ValueError, match="nao suportado"):
        script.forecast_next_model("desconhecido", price, X, y, x_next, Xex)


@pytest.mark.integration
def test_production_script_rejects_mismatch_and_writes_valid_report(monkeypatch, load_script, tmp_path):
    script = load_script("04_producao.py")
    results = tmp_path / "results"
    reports = tmp_path / "reports"
    results.mkdir()
    reports.mkdir()
    pd.DataFrame(
        [
            {
                "horizon": 1,
                "model": "ARIMA",
                "rmse": 0.1,
                "mae": 0.05,
                "smape": 1.0,
                "dir_acc": 0.6,
                "coverage_p10_p90": 0.8,
            },
            {
                "horizon": 1,
                "model": "naive",
                "rmse": 0.2,
                "mae": 0.1,
                "smape": 2.0,
                "dir_acc": 0.0,
                "coverage_p10_p90": 0.8,
            },
        ]
    ).to_csv(results / "semanal_benchmarks.csv", index=False)
    payload = {
        "modelo": "VS-ePL-KRLS",
        "ultima_semana_observada": "2026-08-09",
        "preco_observado_ultima_semana": 6.9,
        "previsao_pontual": 6.91,
        "p10": 6.85,
        "p90": 6.97,
        "probabilidades": {"p_alta": 0.2, "p_estavel": 0.6, "p_queda": 0.2},
    }
    (results / "previsao_proxima_semana.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(script, "RES", results)
    monkeypatch.setattr(script, "REP", reports)
    with pytest.raises(RuntimeError, match="inconsistente"):
        script.main()

    payload["modelo"] = "ARIMA"
    (results / "previsao_proxima_semana.json").write_text(json.dumps(payload), encoding="utf-8")
    script.main()
    report = (reports / "03_producao.md").read_text(encoding="utf-8")
    assert "Recomendado (h=1 semana, criterio RMSE walk-forward): ARIMA" in report
    assert "Previsao pontual: 6.91" in report


def test_lstm_subprocess_script_writes_predictions(monkeypatch, load_script, tmp_path):
    script = load_script("_lstm_wf.py")
    path = tmp_path / "sample.npz"
    X = np.arange(40, dtype=float).reshape(20, 2)
    y = np.linspace(1.0, 2.0, 20)
    np.savez(path, X=X, y=y)
    monkeypatch.setattr(script, "fit_lstm", lambda *args, **kwargs: object())
    monkeypatch.setattr(script, "predict_lstm", lambda *args, **kwargs: 1.5)
    monkeypatch.setattr(sys, "argv", ["_lstm_wf.py", str(path), "5", "1", "4", "2"])
    script.main()
    output = np.load(tmp_path / "sample_yhat.npy")
    assert output.shape == y.shape
    assert np.isfinite(output).sum() == 10


def test_production_payload_validation_rejects_invalid_contract(load_script):
    script = load_script("04_producao.py")
    valid = {
        "modelo": "ARIMA",
        "ultima_semana_observada": "2026-08-09",
        "preco_observado_ultima_semana": 6.9,
        "previsao_pontual": 6.91,
        "p10": 6.85,
        "p90": 6.97,
        "probabilidades": {"p_alta": 0.2, "p_estavel": 0.6, "p_queda": 0.2},
    }
    script.validate_forecast_payload(valid, "ARIMA")
    with pytest.raises(RuntimeError, match="incompleto"):
        script.validate_forecast_payload({"modelo": "ARIMA"}, "ARIMA")
    with pytest.raises(RuntimeError, match="inconsistente"):
        script.validate_forecast_payload(valid, "ARIMAX")
    with pytest.raises(RuntimeError, match="dentro do intervalo"):
        script.validate_forecast_payload({**valid, "p10": 7.0}, "ARIMA")
    with pytest.raises(RuntimeError, match="somam 1"):
        script.validate_forecast_payload(
            {**valid, "probabilidades": {"p_alta": 0.2, "p_estavel": 0.2, "p_queda": 0.2}},
            "ARIMA",
        )


@pytest.mark.integration
def test_weekly_main_runs_end_to_end_with_fast_models(monkeypatch, load_script, tmp_path):
    script = load_script("03_semanal.py")
    proc = tmp_path / "processed"
    res = tmp_path / "results"
    fig = tmp_path / "figures"
    rep = tmp_path / "reports"
    proc.mkdir()
    feat_cols = ["revenda_l1", "brent_l1", "usdbrl_l1"]
    full_dates = pd.date_range("2024-01-07", periods=91, freq="7D")
    full = pd.DataFrame(
        {
            "data": full_dates,
            "revenda": np.linspace(5.0, 6.0, 91),
            "revenda_l1": np.linspace(4.99, 5.99, 91),
            "brent_l1": np.linspace(70.0, 80.0, 91),
            "usdbrl_l1": np.linspace(4.8, 5.2, 91),
        }
    )
    full.to_csv(proc / "semanal_s10_features.csv", index=False)

    def fake_panel(horizon):
        n = 90
        y = np.linspace(5.1, 6.0, n)
        frame = pd.DataFrame(
            {
                "data": full_dates[:n],
                "revenda": y - 0.01,
                "y_prev": y - 0.01,
                "y": y,
                "revenda_l1": np.linspace(5.0, 5.9, n),
                "brent_l1": np.linspace(70.0, 79.0, n),
                "usdbrl_l1": np.linspace(4.8, 5.1, n),
            }
        )
        frame.attrs["feat_cols"] = feat_cols
        return frame

    class FastVS:
        n_rules = 1
        beta = 0.2

        def predict_one(self, x):
            return 5.5

        def update(self, x, y):
            return y

    def fake_vsepl(X, y, n_min, horizon):
        return y + 0.4, FastVS(), (np.zeros(X.shape[1]), np.ones(X.shape[1]))

    monkeypatch.setattr(script, "PROC", proc)
    monkeypatch.setattr(script, "RES", res)
    monkeypatch.setattr(script, "FIG", fig)
    monkeypatch.setattr(script, "REP", rep)
    monkeypatch.setattr(script, "load_panel", fake_panel)
    monkeypatch.setattr(script, "run_vsepl", fake_vsepl)
    monkeypatch.setattr(script, "run_naive", lambda price, n_min: fake_panel(1)["y"].to_numpy() - 0.01)
    monkeypatch.setattr(script, "run_ma", lambda price, n_min, window: fake_panel(1)["y"].to_numpy() + 0.1)
    monkeypatch.setattr(script, "run_arima", lambda price, n_min, horizon, refit: fake_panel(horizon)["y"].to_numpy())
    monkeypatch.setattr(script, "run_arimax", lambda price, Xex, n_min, horizon, refit: fake_panel(horizon)["y"].to_numpy() + 0.02)

    def fake_gbm(kind, X, y, n_min, horizon, refit_every):
        offset = 0.2 if kind == "lgbm" else 0.25
        return y + offset, FakePredictor(float(np.mean(y)))

    monkeypatch.setattr(script, "run_gbm", fake_gbm)

    def fake_subprocess_run(args, cwd):
        npz_path = script.Path(args[2])
        values = np.load(npz_path)["y"] + 0.3
        out = npz_path.with_name(npz_path.stem + "_yhat.npy")
        np.save(out, values)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(script.subprocess, "run", fake_subprocess_run)
    monkeypatch.setattr(
        script,
        "forecast_next_model",
        lambda name, *args, **kwargs: (6.01, {"origem_teste": True}),
    )
    script.main()
    payload = json.loads((res / "previsao_proxima_semana.json").read_text(encoding="utf-8"))
    assert payload["modelo"] == "ARIMA"
    assert payload["previsao_pontual"] == 6.01
    assert payload["origem_teste"] is True
    assert (res / "semanal_benchmarks.csv").exists()
    assert (rep / "02_semanal.md").exists()
    assert len(list(fig.glob("*.png"))) >= 6


def test_s10_selection_helpers_are_deterministic_and_validate_shapes(load_script):
    script = load_script("05_s10_model_selection.py")
    actual = np.array([1.0, 2.0, 3.0, 4.0])
    predictions = np.column_stack(
        [actual, actual + 0.5, np.repeat(2.5, 4), actual - 0.2]
    )
    weights = script._convex_weights(actual, predictions, resolution=5)
    assert np.all(weights >= 0)
    assert weights.sum() == pytest.approx(1.0)
    assert weights[0] == 1.0
    with pytest.raises(ValueError, match="shape"):
        script._convex_weights(actual, predictions[:-1])
    with pytest.raises(ValueError, match="finite"):
        script._convex_weights(actual, predictions * np.nan)

    row = script._metric_row("perfect", actual, actual, actual + 1.0, horizon=1)
    assert row["rmse"] == 0.0
    assert row["n"] == 4


def test_s10_production_approval_falls_back_to_arima(load_script):
    script = load_script("06_train_s10_production.py")
    base = {
        "selected_production_model": "ensemble",
        "comparison": [
            {"model": "ARIMA", "rmse": 1.0},
            {"model": "ensemble", "rmse": 1.1},
        ],
    }
    assert script._approved_primary(base) == "ARIMA"
    base["comparison"][1]["rmse"] = 1.01
    assert script._approved_primary(base) == "ensemble"
    base["selected_production_model"] = "missing"
    with pytest.raises(RuntimeError, match="absent"):
        script._approved_primary(base)
    table = script._markdown_table(pd.DataFrame([{"model": "A", "rmse": 0.123456}]))
    assert "| model | rmse |" in table
    assert "0.12346" in table


def test_next_challenger_helpers_are_causal_and_bounded(monkeypatch, load_script):
    script = load_script("08_s10_next_challenger.py")
    n = 70
    prices = np.linspace(5.0, 6.0, n)
    data = script.S10Supervised(
        x=prices[:, None],
        target_price=prices + 0.01,
        origin_price=prices,
        dates=pd.date_range("2024-01-01", periods=n, freq="7D").to_numpy(),
        target_dates=pd.date_range("2024-01-08", periods=n, freq="7D").to_numpy(),
        feature_names=("price_t",),
        horizon=1,
    )
    histories = []

    def fake_arima(history, steps, model=None):
        histories.append(np.asarray(history).copy())
        return np.array([history[-1]]), object()

    monkeypatch.setattr(script, "arima_forecast", fake_arima)
    predictions = script._causal_arima_predictions(
        data, end=60, min_history=52, refit_every=13
    )
    assert np.isnan(predictions[:52]).all()
    assert np.allclose(predictions[52:60], prices[52:60])
    assert [len(history) for history in histories] == list(range(53, 61))
    assert all(history[-1] == pytest.approx(prices[len(history) - 1]) for history in histories)

    frozen = script.S10Candidate(
        candidate_id="frozen",
        feature_set="lags",
        target_mode="delta",
        alpha=0.26,
        beta_initial=0.18,
        alpha_vs1=0.94,
        alpha_vs2=0.74,
        error_threshold=0.5,
        kernel_sigma=0.15,
        regularization=1e-3,
    )
    direct = script._targeted_direct_candidates(frozen)
    hybrid = script._targeted_hybrid_candidates(frozen)
    assert len(direct) == 13
    assert len(hybrid) == 9
    assert len({candidate.candidate_id for candidate in direct + hybrid}) == 22
    assert all(candidate.target_mode == "delta" for candidate in hybrid)
    assert max(candidate.max_dictionary_size for candidate in direct) == 40
    conservative = next(
        candidate for candidate in hybrid if candidate.candidate_id == "hybrid_lags_conservative"
    )
    assert conservative.residual_correction_weight == 0.5
    assert conservative.residual_correction_limit == 0.1

    table = script._markdown_table(pd.DataFrame([{"model": "A", "rmse": 0.1234567}]))
    assert "| model | rmse |" in table
    assert "0.123457" in table


def test_s10_runtime_cli_is_read_only_by_default_and_updates_atomically(
    monkeypatch, load_script, tmp_path
):
    script = load_script("07_s10_predict.py")

    class Payload:
        def __init__(self, value):
            self.value = value

        def as_dict(self):
            return self.value

    class FakeBundle:
        def __init__(self):
            self.updates = []
            self.saved = []

        def update_one(self, date, price, *, allow_anomalous_change=False):
            self.updates.append((date, price, allow_anomalous_change))
            return self

        def save(self, path):
            destination = script.Path(path)
            destination.write_bytes(b"model")
            self.saved.append(destination)
            return destination

        def predict_next(self):
            return Payload({"point": 6.9})

        def health(self):
            return Payload({"status": "healthy"})

        def metadata(self):
            return {"artifact_version": "1.0.0"}

    fake = FakeBundle()
    monkeypatch.setattr(
        script.S10ProductionForecaster,
        "load",
        lambda _, expected_sha256=None: fake,
    )
    artifact = tmp_path / "in.joblib"
    artifact.write_bytes(b"input")
    output = tmp_path / "forecast.json"
    base = SimpleNamespace(
        artifact=artifact,
        expected_sha256=None,
        allow_anomalous_change=False,
        update_date=None,
        update_price=None,
        output_artifact=None,
        output=output,
    )
    result = script.run(base)
    assert result["updated"] is False
    assert not fake.updates
    assert json.loads(output.read_text(encoding="utf-8"))["forecast"]["point"] == 6.9

    destination = tmp_path / "next.joblib"
    updated = script.run(
        SimpleNamespace(
            **{
                **vars(base),
                "update_date": "2026-08-16",
                "update_price": 6.91,
                "output_artifact": destination,
            }
        )
    )
    assert updated["updated"] is True
    assert fake.updates == [("2026-08-16", 6.91, False)]
    assert destination.exists()
    with pytest.raises(ValueError, match="together"):
        script.run(SimpleNamespace(**{**vars(base), "update_date": "2026-08-16"}))


def test_s10_shadow_cli_accepts_only_a_frozen_eligible_manifest(load_script, tmp_path):
    script = load_script("09_s10_shadow.py")
    candidate = script.S10Candidate(
        candidate_id="shadow",
        feature_set="dynamics",
        target_mode="delta",
        alpha=0.26,
        beta_initial=0.18,
        alpha_vs1=0.94,
        alpha_vs2=0.74,
        error_threshold=0.5,
        kernel_sigma=0.15,
        regularization=1e-3,
        residual_correction_weight=0.5,
        residual_correction_limit=0.1,
    )
    manifest = {
        "holdout_evaluated": False,
        "production_promotion_allowed": False,
        "best_hybrid_validation": {"eligible_for_shadow": True},
        "best_hybrid": candidate.__dict__,
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    loaded, raw = script._load_frozen_candidate(path)
    assert loaded == candidate
    assert raw["holdout_evaluated"] is False

    for key, value, message in (
        ("holdout_evaluated", True, "holdout_evaluated"),
        ("production_promotion_allowed", True, "must not authorize"),
    ):
        invalid = {**manifest, key: value}
        path.write_text(json.dumps(invalid), encoding="utf-8")
        with pytest.raises(RuntimeError, match=message):
            script._load_frozen_candidate(path)
    invalid = {
        **manifest,
        "best_hybrid_validation": {"eligible_for_shadow": False},
    }
    path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(RuntimeError, match="shadow gate"):
        script._load_frozen_candidate(path)


def test_s10_shadow_cli_dispatch_and_atomic_json(monkeypatch, load_script, tmp_path):
    script = load_script("09_s10_shadow.py")
    output = tmp_path / "nested" / "status.json"
    script._write_json(output, {"ok": True})
    assert json.loads(output.read_text(encoding="utf-8")) == {"ok": True}
    assert not output.with_suffix(".json.tmp").exists()

    monkeypatch.setattr(script, "freeze", lambda args: {"mode": "freeze"})
    monkeypatch.setattr(script, "operate", lambda args: {"mode": "operate"})
    assert script.run(SimpleNamespace(freeze=True))["mode"] == "freeze"
    assert script.run(SimpleNamespace(freeze=False))["mode"] == "operate"
