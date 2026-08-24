"""Treina o modelo de paridade em todo o historico e emite a previsao operacional.

Grava um artefato imutavel verificado por SHA-256, no mesmo espirito do bundle
existente, e imprime a previsao da proxima semana junto com a recomendacao da
politica de antecipacao de compra.

Uso::

    python scripts/21_s10_ingest_causal.py        # atualiza as fontes
    python scripts/23_s10_parity_production.py    # treina e preve
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vs_epl_krls.passthrough import (  # noqa: E402
    PARITY_FEATURES,
    PassThroughConfig,
    PassThroughECM,
    build_parity_panel,
)

CONTRACT_VERSION = "parity-1.0.0"
SIGNAL_THRESHOLD = 0.01
DEFAULT_MONTHLY_LITERS = 200_000.0
FLEXIBILITY = 0.25


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint(panel: pd.DataFrame) -> str:
    payload = panel[["date", "price"]].to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel", type=Path, default=ROOT / "data" / "processed" / "s10_causal_panel.csv"
    )
    parser.add_argument(
        "--artifact", type=Path, default=ROOT / "artifacts" / "s10_parity.joblib"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "reports" / "vs_epl_krls" / "s10_parity"
    )
    parser.add_argument("--monthly-liters", type=float, default=DEFAULT_MONTHLY_LITERS)
    args = parser.parse_args()
    args.artifact.parent.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    causal = pd.read_csv(args.panel, parse_dates=["date"])
    panel = build_parity_panel(causal)
    config = PassThroughConfig()

    model = PassThroughECM(config=config, feature_names=PARITY_FEATURES).fit(panel)
    summary = model.summary()

    # A ultima linha do painel ja tem todos os atributos prontos: eles descrevem
    # a semana seguinte a ultima revenda observada.
    last = panel.iloc[-1]
    origin_price = float(last["price"])
    origin_date = pd.Timestamp(last["date"])
    target_date = origin_date + pd.Timedelta(days=7)

    delta_parity = np.log(causal["parity"]).diff()
    next_row = pd.Series(
        {
            "dp1": float(last["y"]),
            "rpar1": float(delta_parity.iloc[-1] * origin_price),
            "rpar2": float(delta_parity.iloc[-2] * origin_price),
            "coint_par": float(last["coint_par"] / last["origin_price"] * origin_price)
            if np.isfinite(last["coint_par"]) and last["origin_price"]
            else np.nan,
            "volatility": float(last["volatility"]),
            "abs_cost_move": abs(float(delta_parity.iloc[-1] * origin_price)),
            "date": target_date,
            "origin_date": origin_date,
        }
    )
    forecast = model.forecast_row(next_row, origin_price=origin_price)

    expected_rise = forecast.point - origin_price
    recommend = bool(expected_rise > SIGNAL_THRESHOLD)
    weekly_liters = args.monthly_liters * 12.0 / 52.0
    liters = weekly_liters * FLEXIBILITY
    payload = {
        "contract_version": CONTRACT_VERSION,
        "generated_from_panel": str(args.panel),
        "data_fingerprint": fingerprint(panel),
        "n_train": summary["n_train"],
        "features": list(PARITY_FEATURES),
        "coefficients": summary["coefficients"],
        "forecast": forecast.as_dict(),
        "decision": {
            "policy": "antecipar 25% de uma semana quando a alta prevista supera R$ 0,01/L",
            "signal_threshold_brl_per_liter": SIGNAL_THRESHOLD,
            "expected_change_brl_per_liter": round(expected_rise, 6),
            "recommend_prebuy": recommend,
            "liters_if_triggered": round(liters, 1) if recommend else 0.0,
            "expected_saving_brl": round(expected_rise * liters, 2) if recommend else 0.0,
        },
    }

    joblib.dump(
        {"model": model, "config": asdict(config), "payload": payload},
        args.artifact,
        compress=3,
    )
    payload["artifact_sha256"] = sha256_file(args.artifact)
    payload["artifact_bytes"] = args.artifact.stat().st_size

    (args.output_dir / "latest_forecast.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"treino: {summary['n_train']} semanas ate {origin_date.date()}")
    print("coeficientes:")
    for name, value in summary["coefficients"].items():
        print(f"  {name:12s} {value:+.6f}")
    print(f"\norigem  {origin_date.date()}  R$ {origin_price:.4f}/L")
    print(f"alvo    {target_date.date()}")
    print(f"ponto   R$ {forecast.point:.4f}/L  (variacao {expected_rise:+.4f})")
    print(f"P10-P90 R$ {forecast.lower:.4f} a {forecast.upper:.4f}/L")
    print(f"fallback: {forecast.fallback_used}  {forecast.reason}")
    print(f"\ndecisao: {'ANTECIPAR' if recommend else 'NAO ANTECIPAR'} "
          f"({args.monthly_liters:,.0f} L/mes)")
    if recommend:
        print(f"  comprar {liters:,.0f} L uma semana antes; "
              f"economia esperada R$ {expected_rise * liters:,.2f}")
    print(f"\nartefato {args.artifact}")
    print(f"sha256   {payload['artifact_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
