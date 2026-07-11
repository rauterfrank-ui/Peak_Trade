#!/usr/bin/env python3
"""Execute one bounded OKX self-accumulated forward OI archive correction v0.

Thin canonical entry point for append-only archive correction against a bound
execution plan. Default-off validate-only; explicit flags required for mutation.
Operator GO: GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ARCHIVE_CORRECTION_EXECUTION_V0_AGAINST_EXECUTABLE_BINDING
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding_v0 import (  # noqa: E402
    CONFIRM_GO_EXECUTION,
    correction_execution_result_to_dict_v0,
    execute_archive_correction_v0,
    exit_code_for_correction_execution_result_v0,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Bounded default-off OKX self-accumulated forward OI archive correction "
            "execution entry point v0."
        )
    )
    parser.add_argument(
        "--confirm-go-token",
        required=True,
        help=f"Required operator GO token ({CONFIRM_GO_EXECUTION})",
    )
    parser.add_argument(
        "--bound-plan",
        type=Path,
        required=True,
        help="Bound archive correction execution plan JSON",
    )
    parser.add_argument(
        "--target-archive",
        type=Path,
        required=True,
        help="Target self-accumulated archive snapshot directory",
    )
    parser.add_argument(
        "--source-manifest-dir",
        type=Path,
        action="append",
        default=[],
        help="Optional source evidence directory with MANIFEST.sha256 to verify",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        default=True,
        help="Validate plan and mutation set without mutating archive (default)",
    )
    parser.add_argument(
        "--execute-mutation",
        action="store_true",
        default=False,
        help="Explicitly authorize one append-only archive correction mutation",
    )
    parser.add_argument(
        "--enabled",
        action="store_true",
        default=False,
        help="Explicit enable flag required together with --execute-mutation",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional JSON result output path",
    )
    args = parser.parse_args(argv)

    validate_only = not args.execute_mutation
    if args.execute_mutation and not args.enabled:
        _die("ERR: EXECUTE_MUTATION_REQUIRES_ENABLED_FLAG")

    result = execute_archive_correction_v0(
        confirm=args.confirm_go_token,
        validate_only=validate_only,
        execute_mutation=args.execute_mutation,
        enabled=args.enabled,
        bound_plan_path=args.bound_plan,
        target_archive_path=args.target_archive,
        source_manifest_dirs=tuple(args.source_manifest_dir),
    )
    report = correction_execution_result_to_dict_v0(result)
    serialized = json.dumps(report, sort_keys=True, indent=2)
    print(serialized)
    if args.output_file is not None:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_file.write_text(serialized + "\n", encoding="utf-8")
    return exit_code_for_correction_execution_result_v0(result)


if __name__ == "__main__":
    raise SystemExit(main())
