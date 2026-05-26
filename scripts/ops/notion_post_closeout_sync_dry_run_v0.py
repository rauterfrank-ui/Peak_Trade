#!/usr/bin/env python3
"""Offline Notion post-closeout sync dry-run report (taxonomy §6a.1.1).

Reads operator-supplied projection payload JSON only; emits a local dry-run report.
Does not call Notion MCP/API, does not write to Notion, and does not enable write mode.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]

PAYLOAD_SCHEMA_VERSION = "peak_trade.post_closeout_projection_payload.v0"
REPORT_SCHEMA_VERSION = "peak_trade.notion_post_closeout_sync_dry_run_report.v0"

DEFAULT_TARGET_NAME = "Evidence & Closeouts"

AUTHORITY_KEYS: tuple[str, ...] = (
    "notion_authority",
    "market_dashboard_authority",
    "runtime_authority",
    "scheduler_authority",
    "daemon_authority",
    "adapter_authority",
    "s3_authority",
    "workflow_dispatch_authority",
    "broker_exchange_authority",
    "testnet_authority",
    "live_authority",
    "master_v2_double_play_authority",
)

FORBIDDEN_REPORT_SUBSTRINGS: tuple[str, ...] = (
    "source_files",
    "/Users/",
    "AKIA",
    "sk-",
    "Bearer ",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _authority_object() -> dict[str, bool]:
    return {key: False for key in AUTHORITY_KEYS}


def _safe_basename(path_value: str | None) -> str:
    if not path_value:
        return "missing"
    name = Path(path_value).name
    return name if name else "configured"


def _redact_target_id(file_path: Path) -> str | None:
    if not file_path.is_file():
        return None
    digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
    return digest[:8]


def _load_payload(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "PAYLOAD_MISSING"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "PAYLOAD_MALFORMED"
    if not isinstance(data, dict):
        return None, "PAYLOAD_MALFORMED"
    if data.get("schema_version") != PAYLOAD_SCHEMA_VERSION:
        return None, "PAYLOAD_SCHEMA_UNSUPPORTED"
    return data, None


def _authority_violation(payload: dict[str, Any]) -> bool:
    authority = payload.get("authority")
    if isinstance(authority, dict):
        for key in AUTHORITY_KEYS:
            if authority.get(key) is True:
                return True
    return False


def _build_would_write_fields(payload: dict[str, Any]) -> dict[str, Any]:
    registry_pointer = payload.get("registry_pointer")
    closeout_pointer = payload.get("closeout_pointer")
    return {
        "run_id": payload.get("run_id"),
        "projection_ready": payload.get("projection_ready"),
        "manifest_verify_rc": payload.get("manifest_verify_rc"),
        "closeout_accepted": payload.get("closeout_accepted"),
        "primary_evidence_finalized": payload.get("primary_evidence_finalized"),
        "repo_commit": payload.get("repo_commit"),
        "s3_export_status": payload.get("s3_export_status"),
        "download_verify_rc": payload.get("download_verify_rc"),
        "registry_configured": bool(registry_pointer),
        "closeout_configured": bool(closeout_pointer),
        "authority": _authority_object(),
    }


def build_dry_run_report(
    *,
    payload_path: Path,
    target_name: str,
    boundary_text_verified: bool,
    target_id_file: Path | None = None,
    payload_basename: str | None = None,
) -> dict[str, Any]:
    """Build dry-run report dict (does not write files)."""
    payload, load_block = _load_payload(payload_path)
    basename = payload_basename or payload_path.name

    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": _utc_now_iso(),
        "dry_run": True,
        "write_requested": False,
        "write_allowed": False,
        "notion_mcp_write_ready": False,
        "notion_target_name_safe": target_name.strip() if target_name else "",
        "notion_target_id_redacted": None,
        "boundary_text_verified": boundary_text_verified,
        "projection_ready": False,
        "blocked_reason": load_block,
        "would_create": False,
        "would_update": False,
        "would_write_fields": _build_would_write_fields(payload or {}),
        "source": {
            "projection_payload_basename": basename,
            "registry_pointer_safe": "missing",
            "closeout_pointer_safe": "missing",
        },
    }

    if target_id_file is not None:
        report["notion_target_id_redacted"] = _redact_target_id(target_id_file)

    if payload is None:
        return report

    report["projection_ready"] = bool(payload.get("projection_ready"))
    report["would_write_fields"] = _build_would_write_fields(payload)
    report["source"]["registry_pointer_safe"] = _safe_basename(
        str(payload.get("registry_pointer") or "")
    )
    report["source"]["closeout_pointer_safe"] = _safe_basename(
        str(payload.get("closeout_pointer") or "")
    )

    blocked: str | None = load_block

    if not target_name.strip():
        blocked = blocked or "TARGET_DB_NOT_APPROVED"
    elif target_id_file is not None and not target_id_file.is_file():
        blocked = blocked or "TARGET_DB_NOT_APPROVED"

    if not boundary_text_verified:
        blocked = blocked or "BOUNDARY_TEXT_NOT_VERIFIED"

    if blocked is None and not payload.get("projection_ready"):
        reason = payload.get("projection_blocked_reason")
        blocked = str(reason) if reason else "PROJECTION_NOT_READY"

    consumers = payload.get("consumers")
    if blocked is None and isinstance(consumers, dict):
        if not consumers.get("notion_projection_allowed"):
            blocked = "NOTION_PROJECTION_NOT_ALLOWED"

    if blocked is None and payload.get("manifest_verify_rc") != 0:
        blocked = "MANIFEST_VERIFY_FAILED"

    if blocked is None and not payload.get("closeout_accepted"):
        blocked = "CLOSEOUT_NOT_ACCEPTED"

    if blocked is None and not payload.get("primary_evidence_finalized"):
        blocked = "PRIMARY_EVIDENCE_NOT_FINALIZED"

    if blocked is None and _authority_violation(payload):
        blocked = "UNSAFE_AUTHORITY_TRUE"

    report["blocked_reason"] = blocked
    report["projection_ready"] = bool(payload.get("projection_ready"))

    if blocked is None:
        report["would_update"] = True
        report["would_create"] = False
    else:
        report["would_update"] = False
        report["would_create"] = False

    return report


def _validate_report_redaction(report: dict[str, Any]) -> None:
    text = json.dumps(report)
    for forbidden in FORBIDDEN_REPORT_SUBSTRINGS:
        if forbidden in text:
            raise ValueError(f"report contains forbidden substring: {forbidden!r}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-payload-json", type=Path, required=True)
    parser.add_argument(
        "--target-name",
        default=DEFAULT_TARGET_NAME,
        help=f"Safe Notion database label (default: {DEFAULT_TARGET_NAME!r}).",
    )
    parser.add_argument(
        "--target-id-file",
        type=Path,
        default=None,
        help="Optional operator-local file with Notion target id; never echoed in full.",
    )
    parser.add_argument(
        "--boundary-text-verified",
        action="store_true",
        help="Operator attestation that §6a.1 boundary copy is present on target DB.",
    )
    parser.add_argument("--output-report-json", type=Path, required=True)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when report is blocked (default: exit 0 after writing report).",
    )
    parser.add_argument("--stdout", action="store_true", help="Also print report JSON to stdout.")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_arg_parser().parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code not in (0, None) else 0

    output_path = args.output_report_json.expanduser().resolve()
    repo_root = _REPO_ROOT.resolve()
    if repo_root in output_path.parents or output_path == repo_root:
        print("ERROR: --output-report-json must not be inside the repository", file=sys.stderr)
        return 2

    payload_path = args.projection_payload_json.expanduser().resolve()
    target_id_file = (
        args.target_id_file.expanduser().resolve() if args.target_id_file is not None else None
    )

    try:
        report = build_dry_run_report(
            payload_path=payload_path,
            target_name=args.target_name,
            boundary_text_verified=args.boundary_text_verified,
            target_id_file=target_id_file,
            payload_basename=payload_path.name,
        )
        _validate_report_redaction(report)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.stdout:
        print(json.dumps(report, indent=2, sort_keys=True))

    blocked = report.get("blocked_reason")
    if args.strict and blocked:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
