#!/usr/bin/env python3
"""Run the original F2 cost grid against its bound Step29M archive."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from src.experiments.canonical_f2_research_backtest_cost_grid_research_execution_v1 import (  # noqa: E402
    run_f2_research_backtest_cost_grid_offline_v1,
)
from src.experiments.canonical_research_prepared_execution_v1 import (  # noqa: E402
    publish_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        required=True,
        help="Directory with bars.parquet and dataset_manifest.json",
    )
    parser.add_argument("--native-baseline-admission-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Immutable F2 result JSON")
    args = parser.parse_args(argv)
    try:
        baseline = json.loads(args.native_baseline_admission_json.read_bytes())
        if not isinstance(baseline, dict):
            raise ValueError("F2_BASELINE_MUST_BE_AN_OBJECT")
        result = run_f2_research_backtest_cost_grid_offline_v1(
            native_baseline_evidence_v1=baseline,
            research_dataset_dir_v1=args.dataset_dir,
        )
        publish_v1(args.output, dict(result))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"F2 research stopped: {exc}\n")
    print(result["execution_digest"])
    grid = result["parameter_sensitivity_result"]
    return int(bool(grid["failed_point_count"] or grid["blocked_point_count"]))


if __name__ == "__main__":
    raise SystemExit(main())
