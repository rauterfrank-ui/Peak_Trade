#!/usr/bin/env python3
"""Local-only S3 finalized evidence export dry preflight (taxonomy §6a.3.1).

Non-network, non-mutating: inspects a finalized evidence root and emits JSON eligibility.
Does not upload, download, sync, copy archives, or call AWS/rclone.
"""

from __future__ import annotations

import argparse
import json
import re
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
REGISTRY_SCHEMA = "peak_trade.generic_evidence_run_registry.v1"
SAFE_PATH_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
COMPATIBLE_EVIDENCE_TRANSPORT = frozenset({"local_only", "s3_export_after_finalize"})

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

EXPORT_PLAN_BOUNDARY_FIELDS: dict[str, bool] = {
    "finalized_evidence_required": True,
    "manifest_verify_required": True,
    "download_verify_required": True,
    "active_staging_sync_forbidden": True,
    "upload_does_not_authorize_runtime": True,
    "s3_authority": False,
    "notion_authority": False,
    "market_dashboard_authority": False,
    "live_authority": False,
    "testnet_authority": False,
    "network_actions_called": False,
    "aws_cli_called": False,
    "rclone_called": False,
    "upload_called": False,
    "download_called": False,
    "mutation_called": False,
}


def _base_result(
    evidence_root: str,
    *,
    dry_run: bool,
    no_network: bool,
    export_prefix_plan_enabled: bool = False,
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
        "export_prefix_plan_enabled": export_prefix_plan_enabled,
        "export_prefix_plan": None,
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


def _load_registry_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "registry_json_missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "registry_json_malformed"
    if not isinstance(payload, dict):
        return None, "registry_json_invalid_shape"
    schema = payload.get("schema")
    if schema is not None and schema != REGISTRY_SCHEMA:
        return None, f"registry_schema_unsupported:{schema}"
    return payload, None


def _find_registry_run(
    registry: dict[str, Any],
    run_id: str,
    lane_id: str | None,
) -> tuple[dict[str, Any] | None, str | None]:
    runs = registry.get("runs")
    if not isinstance(runs, list):
        return None, "registry_runs_missing"
    matches = [row for row in runs if isinstance(row, dict) and row.get("run_id") == run_id]
    if lane_id is not None:
        matches = [row for row in matches if row.get("lane_id") == lane_id]
    if not matches:
        return None, "registry_run_not_found"
    if len(matches) > 1 and lane_id is None:
        return None, "registry_run_ambiguous:lane_id_required"
    return matches[0], None


def _sanitize_path_segment(value: str) -> tuple[str | None, str | None]:
    if not value or value.strip() != value:
        return None, "unsafe_path_segment:empty_or_whitespace"
    if ".." in value or "/" in value or "\\" in value:
        return None, "unsafe_path_segment:path_traversal"
    if not SAFE_PATH_SEGMENT.match(value):
        return None, f"unsafe_path_segment:{value!r}"
    return value, None


def _resolve_registry_evidence_path(
    registry: dict[str, Any], record: dict[str, Any]
) -> Path | None:
    archive_path = record.get("archive_path")
    if not archive_path or not isinstance(archive_path, str):
        return None
    archive_root = registry.get("archive_root")
    if archive_root:
        return (Path(str(archive_root)) / archive_path).resolve()
    path = Path(archive_path)
    if path.is_absolute():
        return path.resolve()
    return None


def _evidence_transport_compatible(record: dict[str, Any]) -> bool:
    transport = record.get("evidence_transport", "local_only")
    return transport in COMPATIBLE_EVIDENCE_TRANSPORT


def _validate_registry_record(
    registry: dict[str, Any],
    record: dict[str, Any],
    evidence_root: Path,
) -> list[str]:
    reasons: list[str] = []
    if not _evidence_transport_compatible(record):
        transport = record.get("evidence_transport")
        reasons.append(f"registry_evidence_transport_incompatible:{transport!r}")
    expected = _resolve_registry_evidence_path(registry, record)
    if expected is not None and expected != evidence_root.resolve():
        reasons.append("registry_evidence_root_mismatch")
    return reasons


def _build_export_prefix_plan(
    *,
    status: str,
    run_id: str | None,
    lane_id: str | None,
    evidence_root: Path,
    object_prefix_proposed: str | None,
    reasons: list[str],
) -> dict[str, Any]:
    plan: dict[str, Any] = {
        "status": status,
        "run_id": run_id,
        "lane_id": lane_id,
        "evidence_root": str(evidence_root),
        "object_prefix_proposed": object_prefix_proposed,
        **EXPORT_PLAN_BOUNDARY_FIELDS,
        "reasons": list(reasons),
    }
    return plan


def _propose_object_prefix(run_id: str, lane_id: str) -> str:
    return f"s3-finalized-evidence/{run_id}/{lane_id}/"


def run_preflight(
    evidence_root: Path,
    *,
    dry_run: bool,
    no_network: bool,
    registry_json: Path | None = None,
    run_id: str | None = None,
    lane_id: str | None = None,
    export_prefix_plan: bool = False,
) -> dict[str, Any]:
    """Evaluate S3 export eligibility for a local evidence root (no side effects)."""
    result = _base_result(
        str(evidence_root),
        dry_run=dry_run,
        no_network=no_network,
        export_prefix_plan_enabled=export_prefix_plan,
    )
    reasons: list[str] = result["reasons"]
    registry: dict[str, Any] | None = None
    registry_record: dict[str, Any] | None = None
    plan_reasons: list[str] = []

    if not dry_run:
        reasons.append("missing_required_flag:dry_run")
    if not no_network:
        reasons.append("missing_required_flag:no_network")
    if not dry_run or not no_network:
        result["status"] = "invalid"
        if export_prefix_plan:
            result["export_prefix_plan"] = _build_export_prefix_plan(
                status="blocked",
                run_id=run_id,
                lane_id=lane_id,
                evidence_root=evidence_root,
                object_prefix_proposed=None,
                reasons=reasons.copy(),
            )
        return result

    if registry_json is not None:
        registry, reg_err = _load_registry_json(registry_json)
        if reg_err:
            reasons.append(reg_err)
            result["status"] = "invalid"
            if export_prefix_plan:
                result["export_prefix_plan"] = _build_export_prefix_plan(
                    status="blocked",
                    run_id=run_id,
                    lane_id=lane_id,
                    evidence_root=evidence_root,
                    object_prefix_proposed=None,
                    reasons=reasons.copy(),
                )
            return result

    if not evidence_root.exists():
        reasons.append("evidence_root_missing")
        result["status"] = "invalid"
        if export_prefix_plan:
            result["export_prefix_plan"] = _build_export_prefix_plan(
                status="blocked",
                run_id=run_id,
                lane_id=lane_id,
                evidence_root=evidence_root,
                object_prefix_proposed=None,
                reasons=reasons.copy(),
            )
        return result

    ok, msg = require_durable_archive_root(evidence_root)
    if not ok:
        reasons.append(msg)
        result["status"] = "blocked" if evidence_root.exists() else "invalid"
        if export_prefix_plan:
            result["export_prefix_plan"] = _build_export_prefix_plan(
                status="blocked",
                run_id=run_id,
                lane_id=lane_id,
                evidence_root=evidence_root,
                object_prefix_proposed=None,
                reasons=reasons.copy(),
            )
        return result

    if _active_staging_sync_detected(evidence_root):
        reasons.append("active_staging_sync_forbidden")
        result["status"] = "blocked"
        if export_prefix_plan:
            result["export_prefix_plan"] = _build_export_prefix_plan(
                status="blocked",
                run_id=run_id,
                lane_id=lane_id,
                evidence_root=evidence_root,
                object_prefix_proposed=None,
                reasons=reasons.copy(),
            )
        return result

    manifest = evidence_root / MANIFEST_FILENAME
    result["manifest_present"] = manifest.is_file()
    if not manifest.is_file():
        reasons.append("MANIFEST.sha256 missing")
        result["status"] = "blocked"
        if export_prefix_plan:
            result["export_prefix_plan"] = _build_export_prefix_plan(
                status="blocked",
                run_id=run_id,
                lane_id=lane_id,
                evidence_root=evidence_root,
                object_prefix_proposed=None,
                reasons=reasons.copy(),
            )
        return result

    verify_ok, verify_msg = verify_manifest_sha256(evidence_root)
    result["manifest_verify_rc"] = 0 if verify_ok else 1
    if not verify_ok:
        reasons.append(verify_msg or "MANIFEST.sha256 verify failed")
        result["status"] = "blocked"
        if export_prefix_plan:
            result["export_prefix_plan"] = _build_export_prefix_plan(
                status="blocked",
                run_id=run_id,
                lane_id=lane_id,
                evidence_root=evidence_root,
                object_prefix_proposed=None,
                reasons=reasons.copy(),
            )
        return result

    closeout_present = _has_closeout_marker(evidence_root)
    result["closeout_marker_present"] = closeout_present
    if not closeout_present:
        reasons.append("finalized_closeout_marker_missing")
        result["status"] = "blocked"
        if export_prefix_plan:
            result["export_prefix_plan"] = _build_export_prefix_plan(
                status="blocked",
                run_id=run_id,
                lane_id=lane_id,
                evidence_root=evidence_root,
                object_prefix_proposed=None,
                reasons=reasons.copy(),
            )
        return result

    resolved_run_id = run_id
    resolved_lane_id = lane_id

    if registry is not None:
        if not resolved_run_id:
            reasons.append("registry_run_id_required")
            result["status"] = "invalid"
            if export_prefix_plan:
                result["export_prefix_plan"] = _build_export_prefix_plan(
                    status="blocked",
                    run_id=resolved_run_id,
                    lane_id=resolved_lane_id,
                    evidence_root=evidence_root,
                    object_prefix_proposed=None,
                    reasons=reasons.copy(),
                )
            return result
        registry_record, find_err = _find_registry_run(registry, resolved_run_id, resolved_lane_id)
        if find_err:
            reasons.append(find_err)
            result["status"] = "blocked"
            if export_prefix_plan:
                result["export_prefix_plan"] = _build_export_prefix_plan(
                    status="blocked",
                    run_id=resolved_run_id,
                    lane_id=resolved_lane_id,
                    evidence_root=evidence_root,
                    object_prefix_proposed=None,
                    reasons=reasons.copy(),
                )
            return result
        assert registry_record is not None
        if resolved_lane_id is None:
            lane_val = registry_record.get("lane_id")
            resolved_lane_id = str(lane_val) if lane_val is not None else None
        reg_reasons = _validate_registry_record(registry, registry_record, evidence_root)
        if reg_reasons:
            reasons.extend(reg_reasons)
            result["status"] = "blocked"
            if export_prefix_plan:
                result["export_prefix_plan"] = _build_export_prefix_plan(
                    status="blocked",
                    run_id=resolved_run_id,
                    lane_id=resolved_lane_id,
                    evidence_root=evidence_root,
                    object_prefix_proposed=None,
                    reasons=reasons.copy(),
                )
            return result

    result["status"] = "eligible"

    if not export_prefix_plan:
        return result

    if not resolved_run_id:
        plan_reasons.append("export_prefix_plan_run_id_required")
        result["status"] = "blocked"
        result["export_prefix_plan"] = _build_export_prefix_plan(
            status="blocked",
            run_id=resolved_run_id,
            lane_id=resolved_lane_id,
            evidence_root=evidence_root,
            object_prefix_proposed=None,
            reasons=plan_reasons,
        )
        return result

    if not resolved_lane_id:
        plan_reasons.append("export_prefix_plan_lane_id_required")
        result["status"] = "blocked"
        result["export_prefix_plan"] = _build_export_prefix_plan(
            status="blocked",
            run_id=resolved_run_id,
            lane_id=resolved_lane_id,
            evidence_root=evidence_root,
            object_prefix_proposed=None,
            reasons=plan_reasons,
        )
        return result

    safe_run_id, run_err = _sanitize_path_segment(resolved_run_id)
    if run_err:
        plan_reasons.append(run_err)
    safe_lane_id, lane_err = _sanitize_path_segment(resolved_lane_id)
    if lane_err:
        plan_reasons.append(lane_err)

    if plan_reasons:
        reasons.extend(plan_reasons)
        result["status"] = "blocked"
        result["export_prefix_plan"] = _build_export_prefix_plan(
            status="blocked",
            run_id=resolved_run_id,
            lane_id=resolved_lane_id,
            evidence_root=evidence_root,
            object_prefix_proposed=None,
            reasons=plan_reasons,
        )
        return result

    assert safe_run_id is not None and safe_lane_id is not None
    object_prefix = _propose_object_prefix(safe_run_id, safe_lane_id)
    result["export_prefix_plan"] = _build_export_prefix_plan(
        status="proposed",
        run_id=safe_run_id,
        lane_id=safe_lane_id,
        evidence_root=evidence_root,
        object_prefix_proposed=object_prefix,
        reasons=[],
    )
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
    parser.add_argument(
        "--registry-json",
        type=Path,
        help="Optional Registry v1 JSON for registry-aware export planning",
    )
    parser.add_argument("--run-id", help="Target run_id for registry row or export-prefix-plan")
    parser.add_argument("--lane-id", help="Target lane_id for registry row or export-prefix-plan")
    parser.add_argument(
        "--export-prefix-plan",
        action="store_true",
        help="Emit non-executing export-prefix-plan in JSON output (no upload)",
    )
    args = parser.parse_args(argv)

    payload = run_preflight(
        args.evidence_root,
        dry_run=args.dry_run,
        no_network=args.no_network,
        registry_json=args.registry_json,
        run_id=args.run_id,
        lane_id=args.lane_id,
        export_prefix_plan=args.export_prefix_plan,
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
