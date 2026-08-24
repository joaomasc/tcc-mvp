"""Evaluate VS-ePL-KRLS on a user-supplied local ANP fuel-price CSV."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vs_epl_krls import (
    VSEPLKRLS,
    evaluate_fuel_product,
    load_anp_fuel_csv,
    make_lagged_dataset,
)


# (alpha, beta0/tau, gamma, error threshold, alphaVS1, alphaVS2),
# reported for weekly S10 experiments in the dissertation.
PAPER_PARAMETERS = {
    ("S10", 2): (0.02, 0.05, 0.95, 0.001, 0.94, 0.74),
    ("S10", 4): (0.26, 0.01, 0.99, 0.002, 0.89, 0.62),
}


def run(args: argparse.Namespace) -> pd.DataFrame:
    frame = load_anp_fuel_csv(
        args.csv,
        date_column=args.date_column,
        product_column=args.product_column,
        price_column=args.price_column,
        products=args.products,
        weekly=args.weekly,
        generic_diesel_as_s500=False,
    )
    if args.start:
        frame = frame[frame["date"] >= pd.Timestamp(args.start)]
    if args.end:
        frame = frame[frame["date"] <= pd.Timestamp(args.end)]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for horizon in args.horizons:
        lagged = make_lagged_dataset(frame, lags=args.lags, horizon=horizon)
        for product in args.products:
            alpha, beta, gamma, gamma_bar, alpha_vs1, alpha_vs2 = PAPER_PARAMETERS[(product, horizon)]

            def factory() -> VSEPLKRLS:
                return VSEPLKRLS(
                    alpha=alpha,
                    beta_initial=beta,
                    arousal_threshold=beta,
                    merge_threshold=gamma,
                    error_threshold=gamma_bar,
                    alpha_vs1=alpha_vs1,
                    alpha_vs2=alpha_vs2,
                    error_normalization="none",
                    kernel_sigma=0.5,
                    regularization=1e-4,
                    initial_rule_dispersion=0.05,
                    max_dictionary_size=args.max_dictionary_size,
                    random_state=args.random_state,
                )

            evaluation = evaluate_fuel_product(
                lagged,
                product=product,
                horizon=horizon,
                train_fraction=args.train_fraction,
                model_factory=factory,
            )
            rows.append(evaluation.summary_row())
            prediction_path = args.output_dir / f"predictions_{product.lower()}_h{horizon}.csv"
            evaluation.predictions.to_csv(prediction_path, index=False)
            figure, axis = plt.subplots(figsize=(11, 4))
            axis.plot(evaluation.predictions["target_date"], evaluation.predictions["actual"], label="real")
            axis.plot(evaluation.predictions["target_date"], evaluation.predictions["prediction"], label="VS-ePL-KRLS")
            axis.plot(evaluation.predictions["target_date"], evaluation.predictions["naive"], label="persistência", alpha=0.7)
            axis.set_title(f"Diesel {product} — horizonte {horizon} semanas")
            axis.set_ylabel("preço")
            axis.grid(alpha=0.2)
            axis.legend()
            figure.tight_layout()
            figure.savefig(args.output_dir / f"forecast_{product.lower()}_h{horizon}.png", dpi=150)
            plt.close(figure)
    summary = pd.DataFrame(rows)
    summary.to_csv(args.output_dir / "results.csv", index=False)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, help="CSV local obtido da ANP")
    parser.add_argument("--date-column")
    parser.add_argument("--product-column")
    parser.add_argument("--price-column")
    parser.add_argument("--products", nargs="+", choices=["S10"], default=["S10"])
    parser.add_argument("--horizons", nargs="+", type=int, choices=[2, 4], default=[2, 4])
    parser.add_argument("--lags", nargs="+", type=int, default=[0, 1, 2, 3, 4, 8, 12])
    parser.add_argument("--weekly", choices=["preserve", "mean", "median"], default="mean")
    parser.add_argument("--start", default="2012-12-01")
    parser.add_argument("--end", default="2020-05-31")
    parser.add_argument("--train-fraction", type=float, default=0.8)
    parser.add_argument("--max-dictionary-size", type=int, default=40)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports" / "vs_epl_krls" / "fuel")
    args = parser.parse_args()
    if args.csv is None:
        parser.print_help()
        print("\nForneça --csv com dados reais da ANP; o exemplo não cria dados substitutos.")
        return 2
    results = run(args)
    print(results.to_string(index=False))
    print(f"Artifacts: {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
