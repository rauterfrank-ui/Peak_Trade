#!/usr/bin/env python3
"""Run DEVELOPMENT-only Bollinger/MR economic failure decomposition (diagnostic).

Offline research diagnosis only. No holdout. No runtime/orders. No gate open.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.research.bollinger_mr_economic_failure_decomposition_development_v1.decompose_v1 import (  # noqa: E402
    run_baseline_decomposition,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bollinger/MR economic failure decomposition (DEVELOPMENT_ONLY, diagnostic)."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT
        / "docs/evidence/bollinger_mr_economic_failure_decomposition_development_v1",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=None,
        help="Optional sealed DEVELOPMENT panel archive root override.",
    )
    args = parser.parse_args()
    summary = run_baseline_decomposition(
        output_dir=args.output_dir,
        archive_root=args.archive_root,
    )
    print(f"DIAGNOSTIC_CLASS={summary.get('diagnostic_class')}")
    print(f"ENTRY_GROSS_EDGE_PRESENT={summary.get('flags', {}).get('ENTRY_GROSS_EDGE_PRESENT')}")
    print(f"TRADE_COUNT={summary.get('core_metrics', {}).get('trade_count')}")
    print(f"HOLDOUT_DATA_ACCESSED={summary.get('holdout_data_accessed')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
