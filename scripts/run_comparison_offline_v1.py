#!/usr/bin/env python3
"""Offline CLI for comparison_ssot.v1 manifest production."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_ssot_v1.constants import (
    LEXICOGRAPHIC_RANKING_RULE_V1,
    RANKING_RULE_NONE,
)
from src.meta.learning_loop.comparison_ssot_v1.models import ComparisonSsotError
from src.meta.learning_loop.comparison_ssot_v1.producer import produce_comparison_offline_v1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Produce comparison_definition_manifest_v1.json and comparison_result_manifest_v1.json"
    )
    parser.add_argument(
        "--input-manifest",
        action="append",
        required=True,
        type=Path,
        dest="input_manifests",
        help="Path to comparison_metric_input_manifest_v1.json (repeat 2..32 times)",
    )
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument(
        "--ranking-rule-version",
        default=RANKING_RULE_NONE,
        choices=[RANKING_RULE_NONE, LEXICOGRAPHIC_RANKING_RULE_V1],
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if len(args.input_manifests) < 2:
        print("ERROR: at least 2 --input-manifest paths required", file=sys.stderr)
        return 1
    if len(args.input_manifests) > 32:
        print("ERROR: at most 32 --input-manifest paths allowed", file=sys.stderr)
        return 1
    try:
        result = produce_comparison_offline_v1(
            input_manifest_paths=list(args.input_manifests),
            output_root=args.output_root,
            ranking_rule_version=args.ranking_rule_version,
        )
    except ComparisonSsotError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(result.definition_path)
    print(result.result_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
