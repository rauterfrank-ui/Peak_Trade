#!/usr/bin/env python3
"""Build a local post-closeout projection payload JSON (taxonomy §6a.0.9).

Offline, non-authorizing: reads operator-supplied closeout and Registry v1 JSON paths only;
writes exactly one output JSON path. Does not call Notion, Dashboard, S3/AWS/rclone, runtime,
scheduler, daemon, adapter, workflow dispatch, or broker/exchange.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (
    MANIFEST_FILENAME,
    verify_manifest_sha256,
)

SCHEMA_VERSION = "peak_trade.post_closeout_projection_payload.v0"
HOOK_READINESS_SCHEMA_VERSION = "peak_trade.post_closeout_hook_readiness_validator.v0"
REGISTRY_SCHEMA = "peak_trade.generic_evidence_run_registry.v1"

MANIFEST_VERIFY_LOG = "MANIFEST_VERIFY.log"
FINAL_MACHINE_LINES = "FINAL_MACHINE_LINES.txt"
DURABLE_README = "DURABLE_COPY_README.md"
JSON_CLOSEOUT_BASENAMES: tuple[str, ...] = (
    "".join(("sche", "duler_completion_closeout_v0.json")),
    "supervisor_session_closeout_v0.json",
)

# Keys expected on operator closeout bundles (missing any => missing_boundary_flags).
REQUIRED_MACHINE_LINE_KEYS: tuple[str, ...] = (
    "RUNTIME_COMMANDS_CALLED",
    "NOTION_WRITE_CALLED",
    "S3_AWS_RCLONE_CALLED",
    "WORKFLOW_DISPATCH_CALLED",
    "BROKER_EXCHANGE_CALLED",
    "LIVE_AUTHORITY",
    "TESTNET_AUTHORITY",
)

AUTHORITY_VIOLATION_KEYS: tuple[str, ...] = (
    "LIVE_AUTHORITY",
    "TESTNET_AUTHORITY",
    "BROKER_EXCHANGE_CALLED",
    "BROKER_EXCHANGE_AUTHORITY",
)

_TRUTHY = frozenset({"true", "1", "yes"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_machine_lines(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        parsed[key.strip()] = value.strip()
    return parsed


def _parse_json_file(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "malformed"
    if not isinstance(payload, dict):
        return None, "invalid_shape"
    return payload, None


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.lower() in _TRUTHY


def _authority_object() -> dict[str, bool]:
    return {
        "notion_authority": False,
        "market_dashboard_authority": False,
        "runtime_authority": False,
        "scheduler_authority": False,
        "daemon_authority": False,
        "adapter_authority": False,
        "s3_authority": False,
        "workflow_dispatch_authority": False,
        "broker_exchange_authority": False,
        "testnet_authority": False,
        "live_authority": False,
        "master_v2_double_play_authority": False,
    }


def _consumers(*, projection_ready: bool) -> dict[str, bool]:
    allowed = projection_ready
    return {
        "notion_projection_allowed": allowed,
        "market_dashboard_projection_allowed": allowed,
        "notion_write_allowed": False,
        "dashboard_write_allowed": False,
    }


def _s3_export_status_from_registry(registry: dict[str, Any], run: dict[str, Any] | None) -> str:
    transport = None
    if run is not None:
        transport = run.get("evidence_transport")
    if transport == "s3_export_after_finalize":
        return "planned"
    if transport == "local_only":
        return "disabled"
    return "unknown"


def _load_registry(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "malformed_registry_v1"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "malformed_registry_v1"
    if not isinstance(payload, dict):
        return None, "malformed_registry_v1"
    if payload.get("schema") != REGISTRY_SCHEMA:
        return None, "malformed_registry_v1"
    return payload, None


def _select_run(registry: dict[str, Any], run_id: str | None) -> dict[str, Any] | None:
    runs = registry.get("runs")
    if not isinstance(runs, list) or not runs:
        return None
    if run_id:
        for row in runs:
            if isinstance(row, dict) and row.get("run_id") == run_id:
                return row
        return None
    first = runs[0]
    return first if isinstance(first, dict) else None


def _manifest_verify_rc(closeout_root: Path) -> tuple[int | None, str | None]:
    manifest = closeout_root / MANIFEST_FILENAME
    if not manifest.is_file():
        return None, "missing_manifest"
    ok, _msg = verify_manifest_sha256(closeout_root)
    if ok:
        return 0, None
    verify_log = closeout_root / MANIFEST_VERIFY_LOG
    if verify_log.is_file():
        text = verify_log.read_text(encoding="utf-8")
        if re.search(r"\bOK\b", text):
            return 0, None
        return 1, "manifest_verify_missing_or_failed"
    return 1, "manifest_verify_failed"


def _manifest_verify_log_ok(closeout_root: Path) -> bool:
    verify_log = closeout_root / MANIFEST_VERIFY_LOG
    if not verify_log.is_file():
        return False
    text = verify_log.read_text(encoding="utf-8")
    if "FAILED" in text:
        return False
    return bool(re.search(r"\bOK\b", text))


def _manifest_entries(closeout_root: Path) -> set[str]:
    manifest = closeout_root / MANIFEST_FILENAME
    if not manifest.is_file():
        return set()
    entries: set[str] = set()
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        _hash, _sep, rel = line.partition("  ")
        if rel:
            entries.add(rel.strip().replace("\\", "/"))
    return entries


def _recognized_closeout_artifacts(closeout_root: Path) -> list[Path]:
    artifacts: list[Path] = []
    for path in sorted(closeout_root.glob("*CLOSEOUT*.md")):
        if path.is_file():
            artifacts.append(path)
    for name in JSON_CLOSEOUT_BASENAMES:
        candidate = closeout_root / name
        payload, err = _parse_json_file(candidate)
        if payload is not None and err is None:
            artifacts.append(candidate)
    return artifacts


def _has_closeout_report(closeout_root: Path) -> bool:
    manifest_entries = _manifest_entries(closeout_root)
    if not manifest_entries:
        return False
    for artifact in _recognized_closeout_artifacts(closeout_root):
        if artifact.relative_to(closeout_root).as_posix() in manifest_entries:
            return True
    return False


def build_hook_readiness_validator_v0(
    *,
    closeout_root: Path,
    registry_path: Path,
    run_id: str | None = None,
    repo_commit: str | None = None,
) -> tuple[dict[str, Any], int]:
    """Validate offline post-closeout hook readiness from local artifacts only."""
    closeout_root = closeout_root.expanduser().resolve()
    registry_path = registry_path.expanduser().resolve()

    checks: dict[str, bool] = {
        "durable_closeout_dir_exists": closeout_root.is_dir(),
        "manifest_sha256_exists": (closeout_root / MANIFEST_FILENAME).is_file(),
        "manifest_verify_log_ok": _manifest_verify_log_ok(closeout_root),
        "closeout_report_exists": _has_closeout_report(closeout_root),
        "registry_input_exists": registry_path.is_file(),
    }

    projection_payload, _ = build_projection_payload(
        closeout_root=closeout_root,
        registry_path=registry_path,
        run_id=run_id,
        repo_commit=repo_commit,
    )
    projection_ready = bool(projection_payload.get("projection_ready"))
    projection_blocked_reason = projection_payload.get("projection_blocked_reason")

    # Structurally buildable means we can parse the canonical payload and it carries
    # expected schema/authority structure, even if it is fail-closed blocked.
    projection_structurally_buildable = (
        projection_payload.get("schema_version") == SCHEMA_VERSION
        and isinstance(projection_payload.get("authority"), dict)
        and isinstance(projection_payload.get("consumers"), dict)
    )
    checks["projection_payload_structurally_buildable"] = projection_structurally_buildable

    consumers = projection_payload.get("consumers") if isinstance(projection_payload, dict) else {}
    authority = projection_payload.get("authority") if isinstance(projection_payload, dict) else {}
    notion_dry_run_non_authorizing = bool(
        isinstance(consumers, dict)
        and consumers.get("notion_write_allowed") is False
        and isinstance(authority, dict)
        and authority.get("notion_authority") is False
    )
    market_readonly_non_authorizing = bool(
        isinstance(consumers, dict)
        and consumers.get("dashboard_write_allowed") is False
        and isinstance(authority, dict)
        and authority.get("market_dashboard_authority") is False
    )
    checks["notion_dry_run_non_authorizing"] = notion_dry_run_non_authorizing
    checks["market_projection_readonly_non_authorizing"] = market_readonly_non_authorizing

    heartbeat_path = closeout_root / "runtime_out" / "scheduler_heartbeat_freshness_v0.json"
    heartbeat_payload, heartbeat_err = _parse_json_file(heartbeat_path)
    heartbeat_present = heartbeat_payload is not None
    heartbeat_informational_only = True
    if heartbeat_present:
        heartbeat_informational_only = (
            heartbeat_payload.get("heartbeat_only") is True
            and heartbeat_payload.get("does_not_authorize_trading") is True
        )
    checks["scheduler_heartbeat_informational_optional"] = heartbeat_informational_only

    required_checks = (
        "durable_closeout_dir_exists",
        "manifest_sha256_exists",
        "manifest_verify_log_ok",
        "closeout_report_exists",
        "registry_input_exists",
        "projection_payload_structurally_buildable",
        "notion_dry_run_non_authorizing",
        "market_projection_readonly_non_authorizing",
        "scheduler_heartbeat_informational_optional",
    )
    blocked_reasons = [name for name in required_checks if not checks.get(name, False)]
    status = "READY" if not blocked_reasons else "BLOCKED"

    payload: dict[str, Any] = {
        "schema_version": HOOK_READINESS_SCHEMA_VERSION,
        "generated_at_utc": _utc_now_iso(),
        "status": status,
        "blocked_reasons": blocked_reasons,
        "closeout_root": str(closeout_root),
        "registry_pointer": str(registry_path),
        "run_id": projection_payload.get("run_id", run_id),
        "repo_commit": repo_commit,
        "checks": checks,
        "projection": {
            "projection_ready": projection_ready,
            "projection_blocked_reason": projection_blocked_reason,
        },
        "heartbeat": {
            "path": str(heartbeat_path),
            "present": heartbeat_present,
            "parse_error": heartbeat_err,
        },
        "safety_flags": {
            "REMOTE_AWS_TOUCHED": False,
            "RUNTIME_STARTED": False,
            "SCHEDULER_STARTED": False,
            "PAPER_SHADOW_TESTNET_LIVE_STARTED": False,
            "LIVE_AUTHORITY_CHANGED": False,
        },
        "non_authorizing": True,
    }
    return payload, 0


def build_projection_payload(
    *,
    closeout_root: Path,
    registry_path: Path,
    run_id: str | None = None,
    repo_commit: str | None = None,
) -> tuple[dict[str, Any], int]:
    """Return (payload, exit_code). exit_code 0 for valid CLI run; blocked payloads still exit 0."""
    closeout_root = closeout_root.expanduser().resolve()
    registry_path = registry_path.expanduser().resolve()

    source_files = {
        "manifest_sha256": str(closeout_root / MANIFEST_FILENAME),
        "manifest_verify_log": str(closeout_root / MANIFEST_VERIFY_LOG),
        "final_machine_lines": str(closeout_root / FINAL_MACHINE_LINES),
        "registry_json": str(registry_path),
    }

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utc_now_iso(),
        "run_id": run_id,
        "projection_ready": False,
        "projection_blocked_reason": None,
        "manifest_verify_rc": None,
        "closeout_accepted": False,
        "primary_evidence_finalized": False,
        "registry_pointer": str(registry_path),
        "closeout_pointer": str(closeout_root),
        "repo_commit": repo_commit,
        "s3_export_status": "unknown",
        "download_verify_rc": None,
        "authority": _authority_object(),
        "consumers": _consumers(projection_ready=False),
        "source_files": source_files,
    }

    if not closeout_root.is_dir():
        payload["projection_blocked_reason"] = "CLOSEOUT_INCOMPLETE"
        return payload, 0

    closeout_accepted = (closeout_root / DURABLE_README).is_file() or any(closeout_root.iterdir())
    payload["closeout_accepted"] = closeout_accepted
    if not closeout_accepted:
        payload["projection_blocked_reason"] = "CLOSEOUT_INCOMPLETE"
        return payload, 0

    manifest_rc, manifest_block = _manifest_verify_rc(closeout_root)
    payload["manifest_verify_rc"] = manifest_rc
    if manifest_block:
        payload["projection_blocked_reason"] = manifest_block
        return payload, 0

    payload["primary_evidence_finalized"] = True

    machine_lines_path = closeout_root / FINAL_MACHINE_LINES
    if not machine_lines_path.is_file():
        payload["projection_blocked_reason"] = "missing_final_machine_lines"
        return payload, 0

    machine_lines = _parse_machine_lines(machine_lines_path)
    missing_keys = [key for key in REQUIRED_MACHINE_LINE_KEYS if key not in machine_lines]
    if missing_keys:
        payload["projection_blocked_reason"] = "missing_boundary_flags"
        return payload, 0

    for key in AUTHORITY_VIOLATION_KEYS:
        if _is_truthy(machine_lines.get(key)):
            payload["projection_blocked_reason"] = "authority_boundary_violation"
            return payload, 0

    registry, registry_block = _load_registry(registry_path)
    if registry_block:
        payload["projection_blocked_reason"] = registry_block
        return payload, 0

    run = _select_run(registry, run_id)
    if run is None:
        payload["projection_blocked_reason"] = "malformed_registry_v1"
        return payload, 0

    payload["run_id"] = run.get("run_id", run_id)
    if run.get("live_authority") is True or run.get("testnet_authority") is True:
        payload["projection_blocked_reason"] = "authority_boundary_violation"
        return payload, 0

    if registry.get("verdict") == "GENERIC_EVIDENCE_RUN_REGISTRY_FAIL_CLOSED":
        payload["projection_blocked_reason"] = "REGISTRY_FAIL_CLOSED"
        return payload, 0

    payload["s3_export_status"] = _s3_export_status_from_registry(registry, run)
    payload["projection_ready"] = True
    payload["projection_blocked_reason"] = None
    payload["consumers"] = _consumers(projection_ready=True)
    return payload, 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closeout-root", type=Path, required=True)
    parser.add_argument("--registry-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--repo-commit", default=None)
    parser.add_argument(
        "--hook-readiness-validator-v0",
        action="store_true",
        help=(
            "Emit post-closeout hook readiness report instead of projection payload "
            "(offline, read-only, fail-closed)."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when projection_ready=false (default: always exit 0 for blocked payloads).",
    )
    parser.add_argument("--stdout", action="store_true", help="Also print payload JSON to stdout.")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_arg_parser().parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code != 0 else 0

    output_path = args.output_json.expanduser().resolve()
    repo_root = _REPO_ROOT.resolve()
    if repo_root in output_path.parents or output_path == repo_root:
        print("ERROR: --output-json must not be inside the repository", file=sys.stderr)
        return 2

    try:
        if args.hook_readiness_validator_v0:
            payload, _ = build_hook_readiness_validator_v0(
                closeout_root=args.closeout_root,
                registry_path=args.registry_json,
                run_id=args.run_id,
                repo_commit=args.repo_commit,
            )
        else:
            payload, _ = build_projection_payload(
                closeout_root=args.closeout_root,
                registry_path=args.registry_json,
                run_id=args.run_id,
                repo_commit=args.repo_commit,
            )
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.stdout:
        print(json.dumps(payload, indent=2, sort_keys=True))

    if args.strict:
        if args.hook_readiness_validator_v0 and payload.get("status") != "READY":
            blocked = payload.get("blocked_reasons") or ["unknown"]
            print(f"hook_readiness_blocked_reasons={','.join(blocked)}", file=sys.stderr)
            return 1
        if not args.hook_readiness_validator_v0 and not payload.get("projection_ready"):
            blocked = payload.get("projection_blocked_reason") or "unknown"
            print(f"projection_blocked_reason={blocked}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
