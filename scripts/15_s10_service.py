"""Run the S10 Intelligence HTTP service against an immutable release."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vs_epl_krls.api import APISettings, create_app
from vs_epl_krls.product import S10ProductService


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact",
        type=Path,
        default=ROOT / "artifacts" / "releases" / "s10_production_2026-08-16.joblib",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "reports" / "vs_epl_krls" / "s10_product" / "releases" / "2026-08-16.json",
    )
    parser.add_argument(
        "--selection-manifest",
        type=Path,
        default=ROOT / "reports" / "vs_epl_krls" / "s10_selection" / "selection_manifest_h1.json",
    )
    parser.add_argument(
        "--procurement-report",
        type=Path,
        default=ROOT / "reports" / "vs_epl_krls" / "s10_product" / "procurement_backtest.json",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or not 1 <= args.workers <= 16:
        raise ValueError("invalid port or worker count")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    service = S10ProductService(
        args.artifact,
        args.manifest,
        selection_manifest=args.selection_manifest,
        procurement_report=args.procurement_report,
    )
    application = create_app(service, settings=APISettings.from_environment())
    import uvicorn

    uvicorn.run(
        application,
        host=args.host,
        port=args.port,
        workers=args.workers,
        server_header=False,
        date_header=False,
        proxy_headers=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
