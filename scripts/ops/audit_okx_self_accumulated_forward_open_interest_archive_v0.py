#!/usr/bin/env python3
"""Offline-only integrity audit for OKX self-accumulated forward OI archive snapshots.

Default-off, operator-GO-required. No network collection.
Operator GO: GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ARCHIVE_INTEGRITY_AUDIT_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.okx_self_accumulated_forward_open_interest_archive_integrity_audit_v0 import (  # noqa: E402
    CONFIRM_GO,
    ArchiveIntegrityAuditStatus,
    audit_archive_snapshot_v0,
    audit_result_to_dict_v0,
    write_audit_evidence_bundle_v0,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline integrity audit for OKX self-accumulated forward OI archive."
    )
    parser.add_argument(
        "--confirm-go-token",
        required=True,
        help=f"Required operator GO token ({CONFIRM_GO})",
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        required=True,
        help="Archive snapshot directory containing observations.jsonl",
    )
    parser.add_argument(
        "--prior-snapshot-dir",
        type=Path,
        default=None,
        help="Optional prior snapshot for append-only prefix verification",
    )
    parser.add_argument(
        "--require-manifest-sha256",
        action="store_true",
        help="Fail closed when MANIFEST.sha256 is missing or invalid",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional evidence output directory",
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
    if not args.snapshot_dir.is_dir():
        _die(f"ERR: missing_snapshot_dir:{args.snapshot_dir}")

    result = audit_archive_snapshot_v0(
        snapshot_dir=args.snapshot_dir,
        prior_snapshot_dir=args.prior_snapshot_dir,
        require_manifest_sha256=args.require_manifest_sha256,
    )
    report = audit_result_to_dict_v0(result)
    print(json.dumps(report, sort_keys=True, indent=2))

    if args.output_dir is not None:
        write_audit_evidence_bundle_v0(result=result, output_dir=args.output_dir)

    if result.status in {
        ArchiveIntegrityAuditStatus.PASS,
        ArchiveIntegrityAuditStatus.VALID_EMPTY,
        ArchiveIntegrityAuditStatus.INSUFFICIENT_DATA,
    }:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
