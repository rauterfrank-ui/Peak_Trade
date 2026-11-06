#!/usr/bin/env python3
"""Offline-only overlap validation for OKX self-accumulated forward OI archive.

Compares explicit self-accumulated archive input against explicit external reference input.
Operator GO: GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_OVERLAP_VALIDATION_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.okx_self_accumulated_forward_open_interest_overlap_validation_v0 import (  # noqa: E402
    CONFIRM_GO,
    exit_code_for_overlap_validation_result_v0,
    overlap_validation_result_to_dict_v0,
    validate_overlap_v0,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline overlap validation for OKX self-accumulated forward OI archive."
    )
    parser.add_argument(
        "--confirm-go-token",
        required=True,
        help=f"Required operator GO token ({CONFIRM_GO})",
    )
    parser.add_argument(
        "--self-accumulated-input",
        type=Path,
        required=True,
        help="Self-accumulated archive snapshot directory or observations.jsonl path",
    )
    parser.add_argument(
        "--external-reference-input",
        type=Path,
        default=None,
        help="External reference snapshot directory or observations.jsonl path",
    )
    parser.add_argument(
        "--instrument-id",
        default=None,
        help="Optional instrument_id filter",
    )
    parser.add_argument(
        "--requested-start-utc",
        default=None,
        help="Optional requested comparison window start UTC",
    )
    parser.add_argument(
        "--requested-end-utc",
        default=None,
        help="Optional requested comparison window end UTC",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional JSON output path",
    )
    parser.add_argument(
        "--enabled",
        action="store_true",
        help="Explicit enable flag; default-off without this flag",
    )
    args = parser.parse_args(argv)

    if not args.enabled:
        _die("ERR: DEFAULT_OFF_ENABLED_FLAG_REQUIRED")
    if args.confirm_go_token != CONFIRM_GO:
        _die(f"ERR: OPERATOR_GO_MISMATCH expected={CONFIRM_GO}")

    result = validate_overlap_v0(
        self_accumulated_source=args.self_accumulated_input,
        external_reference_source=args.external_reference_input,
        instrument_id=args.instrument_id,
        requested_start_utc=args.requested_start_utc,
        requested_end_utc=args.requested_end_utc,
    )
    report = overlap_validation_result_to_dict_v0(result)
    serialized = json.dumps(report, sort_keys=True, indent=2)
    print(serialized)
    if args.output_file is not None:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_file.write_text(serialized + "\n", encoding="utf-8")
    return exit_code_for_overlap_validation_result_v0(result)


if __name__ == "__main__":
    raise SystemExit(main())
