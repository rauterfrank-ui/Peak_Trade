#!/usr/bin/env python3
"""Offline CLI for comparison_metric_input.v1 manifest production."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_metric_input_v1.models import ComparisonMetricInputError
from src.meta.learning_loop.comparison_metric_input_v1.producer import (
    produce_comparison_metric_input_v1,
)


def _load_ref(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ComparisonMetricInputError(f"source ref must be JSON object: {path}")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Produce comparison_metric_input_manifest_v1.json")
    parser.add_argument(
        "--source-domain", required=True, choices=["EXPERIMENT", "BACKTEST", "VAR_SUITE"]
    )
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--source-ref", required=True, type=Path)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--manifest-dir", type=Path, default=None)
    parser.add_argument("--completed-run-dir", type=Path, default=None)
    parser.add_argument("--suite-report-dir", type=Path, default=None)
    parser.add_argument("--companion-run-dir", type=Path, default=None)
    parser.add_argument("--backtest-source-ref", type=Path, default=None)
    parser.add_argument("--evaluation-slice-id", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source_ref = _load_ref(args.source_ref)
        backtest_source_ref = (
            _load_ref(args.backtest_source_ref) if args.backtest_source_ref is not None else None
        )
        result = produce_comparison_metric_input_v1(
            source_domain=args.source_domain,
            output_root=args.output_root,
            source_ref=source_ref,
            run_dir=args.run_dir,
            manifest_dir=args.manifest_dir,
            completed_run_dir=args.completed_run_dir,
            suite_report_dir=args.suite_report_dir,
            companion_run_dir=args.companion_run_dir,
            backtest_source_ref=backtest_source_ref,
            evaluation_slice_id=args.evaluation_slice_id,
        )
    except ComparisonMetricInputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(result.manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
