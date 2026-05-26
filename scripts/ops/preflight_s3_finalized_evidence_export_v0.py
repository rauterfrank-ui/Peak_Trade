#!/usr/bin/env python3
"""Local-only S3 finalized evidence export dry preflight (taxonomy §6a.3.1).

Non-network, non-mutating: inspects a finalized evidence root and emits JSON eligibility.
Does not upload, download, sync, copy archives, or call AWS/rclone.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.ops.primary_evidence_retention_v0 import (
    KNOWN_CLOSEOUT_FILENAMES,
    MANIFEST_FILENAME,
    is_under_tmp,
    require_durable_archive_root,
    verify_manifest_sha256,
)

SCHEMA_VERSION = "peak_trade.s3_finalized_evidence_export_preflight.v0"
PREFLIGHT_NAME = "preflight_s3_finalized_evidence_export_v0"
ACTIVE_STAGING_SYNC_MARKER = ".active_staging_sync"

BOUNDARY_FIELDS: dict[str, bool] = {
    "network_actions_called": False,
    "aws_cli_called": False,
    "rclone_called": False,
    "upload_called": False,
    "download_called": False,
    "mutation_called": False,
    "finalized_evidence_required": True,
    "active_staging_sync_forbidden": True,
    "s3_export_after_finalize_only": True,
    "upload_does_not_authorize_runtime": True,
    "notion_authority": False,
    "market_dashboard_authority": False,
    "live_authority": False,
    "testnet_authority": False,
}


def _base_result(
    evidence_root: str,
    *,
    dry_run: bool,
    no_network: bool,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "preflight_name": PREFLIGHT_NAME,
        "evidence_root": evidence_root,
        "dry_run": dry_run,
        "no_network": no_network,
        **BOUNDARY_FIELDS,
        "manifest_present": False,
        "manifest_verify_rc": None,
        "closeout_marker_present": False,
        "status": "invalid",
        "reasons": [],
    }


def _has_closeout_marker(root: Path) -> bool:
    for name in KNOWN_CLOSEOUT_FILENAMES:
        if (root / name).is_file():
            return True
        for path in root.glob(f"*/{name}"):
            if path.is_file():
                return True
    if (root / "review" / "REVIEW_RESULT.json").is_file():
        return True
    return False


def _active_staging_sync_detected(root: Path) -> bool:
    if (root / ACTIVE_STAGING_SYNC_MARKER).is_file():
        return True
    return is_under_tmp(root) and "_staging_" in root.name


def run_preflight(
    evidence_root: Path,
    *,
    dry_run: bool,
    no_network: bool,
) -> dict[str, Any]:
    """Evaluate S3 export eligibility for a local evidence root (no side effects)."""
    result = _base_result(str(evidence_root), dry_run=dry_run, no_network=no_network)
    reasons: list[str] = result["reasons"]

    if not dry_run:
        reasons.append("missing_required_flag:dry_run")
    if not no_network:
        reasons.append("missing_required_flag:no_network")
    if not dry_run or not no_network:
        result["status"] = "invalid"
        return result

    if not evidence_root.exists():
        reasons.append("evidence_root_missing")
        result["status"] = "invalid"
        return result

    ok, msg = require_durable_archive_root(evidence_root)
    if not ok:
        reasons.append(msg)
        result["status"] = "blocked" if evidence_root.exists() else "invalid"
        return result

    if _active_staging_sync_detected(evidence_root):
        reasons.append("active_staging_sync_forbidden")
        result["status"] = "blocked"
        return result

    manifest = evidence_root / MANIFEST_FILENAME
    result["manifest_present"] = manifest.is_file()
    if not manifest.is_file():
        reasons.append("MANIFEST.sha256 missing")
        result["status"] = "blocked"
        return result

    verify_ok, verify_msg = verify_manifest_sha256(evidence_root)
    result["manifest_verify_rc"] = 0 if verify_ok else 1
    if not verify_ok:
        reasons.append(verify_msg or "MANIFEST.sha256 verify failed")
        result["status"] = "blocked"
        return result

    closeout_present = _has_closeout_marker(evidence_root)
    result["closeout_marker_present"] = closeout_present
    if not closeout_present:
        reasons.append("finalized_closeout_marker_missing")
        result["status"] = "blocked"
        return result

    result["status"] = "eligible"
    return result


def _exit_code_for_status(status: str) -> int:
    if status == "eligible":
        return 0
    if status == "blocked":
        return 1
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Local-only S3 finalized evidence export dry preflight (no network)."
    )
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--out", type=Path, help="Write JSON result to path (default: stdout)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required: preflight is dry-run only",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Required: forbid network actions in this preflight path",
    )
    args = parser.parse_args(argv)

    payload = run_preflight(
        args.evidence_root,
        dry_run=args.dry_run,
        no_network=args.no_network,
    )
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return _exit_code_for_status(str(payload["status"]))


if __name__ == "__main__":
    raise SystemExit(main())
