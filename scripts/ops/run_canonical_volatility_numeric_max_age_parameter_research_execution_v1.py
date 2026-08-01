#!/usr/bin/env python3
"""CLI entrypoint: non-enforcing canonical volatility max-age research execution v1."""

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

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.runner_v1 import (  # noqa: E402
    run_max_age_parameter_research_execution_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Execute non-enforcing canonical volatility numeric max-age "
            "parameter research. Never selects or promotes a threshold."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="Repository root (default: detected from script location)",
    )
    parser.add_argument(
        "--ledger-path",
        type=Path,
        default=None,
        help="Optional path to research evidence ledger JSONL",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Optional output evidence root (defaults under docs/evidence/.../execution_id)",
    )
    parser.add_argument(
        "--repository-sha",
        type=str,
        default=None,
        help="Optional explicit repository SHA binding",
    )
    args = parser.parse_args(argv)

    result = run_max_age_parameter_research_execution_v1(
        repo_root=args.repo_root.resolve(),
        ledger_path=None if args.ledger_path is None else args.ledger_path.resolve(),
        output_root=None if args.output_root is None else args.output_root.resolve(),
        repository_sha=args.repository_sha,
    )
    print(json.dumps(result, sort_keys=True, indent=2, default=str))
    return 0 if result.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
