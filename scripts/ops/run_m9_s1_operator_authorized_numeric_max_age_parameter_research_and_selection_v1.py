#!/usr/bin/env python3
"""CLI: M9-S1 operator-authorized max-age parameter research and selection boundary v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "src"):
    text = str(_path)
    if text not in sys.path:
        sys.path.insert(0, text)

from src.governance.m9_s1_operator_authorized_numeric_max_age_parameter_research_and_selection_v1 import (  # noqa: E402
    load_committed_owner_m9_s1_research_authorization_input_v1,
    run_m9_s1_operator_authorized_parameter_research_and_selection_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run operator-authorized M9-S1 max-age parameter research and emit "
            "owner-review selection boundary evidence (no numeric ratification)."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="Repository root",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="Output directory for M9-S1 owner-review package",
    )
    parser.add_argument(
        "--ledger-path",
        type=Path,
        default=None,
        help="Optional research evidence ledger JSONL",
    )
    parser.add_argument(
        "--repository-sha",
        type=str,
        default=None,
        help="Optional repository SHA binding",
    )
    args = parser.parse_args(argv)

    owner_input = load_committed_owner_m9_s1_research_authorization_input_v1()
    result = run_m9_s1_operator_authorized_parameter_research_and_selection_v1(
        repo_root=args.repo_root.resolve(),
        owner_authorization_input=owner_input,
        output_root=args.output_root.resolve(),
        ledger_path=None if args.ledger_path is None else args.ledger_path.resolve(),
        repository_sha=args.repository_sha,
    )
    print(json.dumps(result, sort_keys=True, indent=2, default=str))
    return (
        0
        if result.get("authorization_status") == "AUTHORIZED_FOR_OPERATOR_BOUND_PARAMETER_RESEARCH"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
