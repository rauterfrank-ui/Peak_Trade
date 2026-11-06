#!/usr/bin/env python3
"""Offline-only coverage/freshness report for OKX self-accumulated forward OI archive.

No network collection or collector execution.
Operator GO: GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_COVERAGE_FRESHNESS_REPORT_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.okx_self_accumulated_forward_open_interest_coverage_freshness_report_v0 import (  # noqa: E402
    CONFIRM_GO,
    CoverageFreshnessArchiveStatus,
    generate_coverage_freshness_report_v0,
    report_result_to_dict_v0,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _exit_code_for_status(archive_status: str) -> int:
    if archive_status in {
        CoverageFreshnessArchiveStatus.VALID_EMPTY.value,
        CoverageFreshnessArchiveStatus.NON_EMPTY_VALID.value,
    }:
        return 0
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline coverage/freshness report for OKX self-accumulated forward OI archive."
    )
    parser.add_argument(
        "--confirm-go-token",
        required=True,
        help=f"Required operator GO token ({CONFIRM_GO})",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=None,
        help="Read-only archive snapshot directory",
    )
    parser.add_argument(
        "--as-of-utc",
        required=True,
        help="Deterministic as-of UTC timestamp (YYYY-MM-DDTHH:MM:SSZ)",
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

    result = generate_coverage_freshness_report_v0(
        archive_root=args.archive_root,
        as_of_utc=args.as_of_utc,
    )
    print(json.dumps(report_result_to_dict_v0(result), sort_keys=True, indent=2))
    return _exit_code_for_status(result.archive_status)


if __name__ == "__main__":
    raise SystemExit(main())
