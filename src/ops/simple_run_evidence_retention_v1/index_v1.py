"""Build and persist the simple run evidence index (non-authorizing)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from scripts.ops.primary_evidence_retention_v0 import (
    BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS,
    BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS,
    MANIFEST_FILENAME,
    PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
    verify_manifest_sha256,
)

from .constants_v1 import (
    ARCHIVE_RUN_CLASSES,
    GENERIC_EVIDENCE_RUN_REGISTRY_OWNER,
    PRIMARY_EVIDENCE_RETENTION_OWNER,
    RETENTION_CANARY,
    RETENTION_FORENSIC,
    RETENTION_KEEP,
    RETENTION_STANDARD,
    RUN_CLASS_CANARY,
    RUN_CLASS_PAPER,
    RUN_CLASS_SHADOW,
    RUN_CLASS_TESTNET,
    RUN_STATUS_ABORTED,
    RUN_STATUS_COMPLETE,
    RUN_STATUS_FAILED,
    RUN_STATUS_INCOMPLETE,
    RUN_STATUS_RUNNING,
    SCHEMA_SIMPLE_RUN_EVIDENCE_INDEX_ENTRY_V1,
    TERMINAL_STATUSES,
    VALID_RETENTION_CLASSES,
)
from .discover_v1 import (
    ArchiveRunRef,
    CanaryEvidenceRef,
    archive_evidence_locator,
    discover_archive_runs,
    discover_repo_canary_evidence,
    repo_canary_evidence_locator,
    synthetic_canary_run_id,
)
from .storage_v1 import OwnerRunEvidenceRootError, resolve_owner_run_evidence_root
from .metadata_v1 import (
    pick_code_sha,
    pick_config_ref,
    pick_instrument,
    pick_termination_reason,
    pick_times,
    pick_venue,
    read_retention_sidecar,
    read_run_metadata,
)

_DERIVED_HINT = (
    "Summaries, metrics, and diagnostics under review/, logs/, and ad-hoc reports "
    "are derived unless listed in primary_evidence_paths."
)

_DEBUG_HINT = (
    "Verbose wrapper logs and MANIFEST_VERIFY.log are debug/ephemeral unless "
    "required for primary reconstruction."
)


def _required_paths_for_class(run_class: str) -> tuple[str, ...]:
    if run_class == RUN_CLASS_PAPER:
        return PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS
    if run_class == RUN_CLASS_SHADOW:
        return BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS
    if run_class == RUN_CLASS_TESTNET:
        return BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS
    return (MANIFEST_FILENAME,)


def _review_required(run_class: str) -> bool:
    return run_class in (RUN_CLASS_SHADOW, RUN_CLASS_TESTNET)


def _missing_required(run_root: Path, required: tuple[str, ...]) -> list[str]:
    missing: list[str] = []
    for rel in required:
        if not (run_root / rel).is_file():
            missing.append(rel)
    return missing


def infer_archive_run_status(run_root: Path, run_class: str) -> str:
    metadata = read_run_metadata(run_root)
    required = _required_paths_for_class(run_class)
    missing = _missing_required(run_root, required)
    if missing:
        if any((run_root / rel).is_file() for rel in required):
            return RUN_STATUS_INCOMPLETE
        return RUN_STATUS_INCOMPLETE

    manifest_ok, _ = verify_manifest_sha256(run_root)
    if not manifest_ok:
        return RUN_STATUS_INCOMPLETE

    reason = pick_termination_reason(metadata)
    if reason and "adapter_rc=" in reason:
        return RUN_STATUS_FAILED

    if _review_required(run_class):
        review_path = run_root / "review" / "REVIEW_RESULT.json"
        if not review_path.is_file():
            return RUN_STATUS_INCOMPLETE
        try:
            review = json.loads(review_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return RUN_STATUS_INCOMPLETE
        if review.get("verdict") != "PASS":
            return RUN_STATUS_FAILED

    verdict = metadata.get("verdict") or metadata.get("review_verdict")
    if isinstance(verdict, str) and verdict.strip().upper() not in (
        "PASS",
        "SUCCESS",
        "COMPLETE",
        "",
    ):
        return RUN_STATUS_FAILED

    return RUN_STATUS_COMPLETE


def _resolve_retention_class(
    *,
    run_class: str,
    run_root: Path,
    default: str,
) -> str:
    sidecar = read_retention_sidecar(run_root)
    raw = sidecar.get("retention_class")
    if isinstance(raw, str) and raw in VALID_RETENTION_CLASSES:
        if run_class == RUN_CLASS_CANARY and raw == RETENTION_STANDARD:
            return RETENTION_CANARY
        return raw
    if run_class == RUN_CLASS_CANARY:
        return RETENTION_CANARY
    return default


def _primary_paths_for_archive(run_class: str) -> list[str]:
    return list(_required_paths_for_class(run_class))


def build_archive_run_entry(ref: ArchiveRunRef) -> dict[str, Any]:
    metadata = read_run_metadata(ref.run_dir)
    started_at, finished_at = pick_times(metadata)
    status = infer_archive_run_status(ref.run_dir, ref.run_class)
    flat_layout = ref.run_dir.parent.name not in ARCHIVE_RUN_CLASSES
    locator = archive_evidence_locator(ref.run_class, ref.run_id, flat_layout=flat_layout)
    retention = _resolve_retention_class(
        run_class=ref.run_class,
        run_root=ref.run_dir,
        default=RETENTION_STANDARD,
    )
    return {
        "schema": SCHEMA_SIMPLE_RUN_EVIDENCE_INDEX_ENTRY_V1,
        "run_id": ref.run_id,
        "run_class": ref.run_class,
        "started_at": started_at,
        "finished_at": finished_at,
        "status": status,
        "code_sha": pick_code_sha(metadata, ref.run_dir),
        "config_ref": pick_config_ref(metadata),
        "instrument": pick_instrument(metadata),
        "venue": pick_venue(metadata),
        "termination_reason": pick_termination_reason(metadata),
        "evidence_storage_kind": "data_archive",
        "archive_root_contract": "PEAK_TRADE_DATA_ARCHIVE_ROOT",
        "evidence_location": locator,
        "primary_evidence_paths": _primary_paths_for_archive(ref.run_class),
        "derived_evidence_note": _DERIVED_HINT,
        "debug_evidence_note": _DEBUG_HINT,
        "retention_class": retention,
        "index_finalized": status in TERMINAL_STATUSES,
        "upstream_owners": {
            "primary_evidence": PRIMARY_EVIDENCE_RETENTION_OWNER,
            "full_registry": GENERIC_EVIDENCE_RUN_REGISTRY_OWNER,
        },
    }


def infer_canary_status(evidence_dir: Path) -> str:
    if (evidence_dir / MANIFEST_FILENAME).is_file():
        ok, _ = verify_manifest_sha256(evidence_dir)
        return RUN_STATUS_COMPLETE if ok else RUN_STATUS_INCOMPLETE
    markers = (
        "SUMMARY.json",
        "LIVE_CANARY_CYBERSECURITY_GATE.json",
        "PRE_CANARY_READINESS_TERMINAL.json",
        "MACHINE_READABLE_PROOF.json",
    )
    if any((evidence_dir / name).is_file() for name in markers):
        return RUN_STATUS_COMPLETE
    if any(evidence_dir.iterdir()) if evidence_dir.is_dir() else False:
        return RUN_STATUS_INCOMPLETE
    return RUN_STATUS_INCOMPLETE


def build_canary_entry(ref: CanaryEvidenceRef, repo_root: Path) -> dict[str, Any]:
    run_id = synthetic_canary_run_id(ref.capability_id, ref.timestamp_dir)
    locator = repo_canary_evidence_locator(ref.capability_id, ref.timestamp_dir)
    status = infer_canary_status(ref.evidence_dir)
    retention = _resolve_retention_class(
        run_class=RUN_CLASS_CANARY,
        run_root=ref.evidence_dir,
        default=RETENTION_CANARY,
    )
    primary: list[str] = []
    for candidate in (
        MANIFEST_FILENAME,
        "SUMMARY.json",
        "LIVE_CANARY_CYBERSECURITY_GATE.json",
        "PRE_CANARY_READINESS_TERMINAL.json",
        "MACHINE_READABLE_PROOF.json",
    ):
        if (ref.evidence_dir / candidate).is_file():
            primary.append(candidate)
    metadata = read_run_metadata(ref.evidence_dir)
    started_at, finished_at = pick_times(metadata)
    return {
        "schema": SCHEMA_SIMPLE_RUN_EVIDENCE_INDEX_ENTRY_V1,
        "run_id": run_id,
        "run_class": RUN_CLASS_CANARY,
        "started_at": started_at or ref.timestamp_dir,
        "finished_at": finished_at,
        "status": status,
        "code_sha": pick_code_sha(metadata, ref.evidence_dir),
        "config_ref": ref.capability_id,
        "instrument": pick_instrument(metadata),
        "venue": pick_venue(metadata),
        "termination_reason": pick_termination_reason(metadata),
        "evidence_storage_kind": "repo_evidence_ops",
        "archive_root_contract": None,
        "evidence_location": locator,
        "primary_evidence_paths": primary,
        "derived_evidence_note": _DERIVED_HINT,
        "debug_evidence_note": _DEBUG_HINT,
        "retention_class": retention,
        "index_finalized": status in TERMINAL_STATUSES,
        "upstream_owners": {
            "primary_evidence": PRIMARY_EVIDENCE_RETENTION_OWNER,
            "full_registry": GENERIC_EVIDENCE_RUN_REGISTRY_OWNER,
        },
        "canary_capability_id": ref.capability_id,
        "canary_timestamp_dir": ref.timestamp_dir,
        "repo_root_anchor": str(repo_root.name),
    }


def build_index_entries(
    *,
    repo_root: Path,
    archive_root: Path | None,
    env: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    env_map = env if env is not None else dict(os.environ)
    merged: dict[tuple[str, str], dict[str, Any]] = {}

    try:
        owner_root = resolve_owner_run_evidence_root(env=env_map)
    except OwnerRunEvidenceRootError:
        owner_root = None

    if owner_root is not None and owner_root.is_dir():
        for ref in discover_archive_runs(owner_root):
            entry = build_archive_run_entry(ref)
            entry["evidence_storage_kind"] = "owner_evidence_home"
            entry["archive_root_contract"] = "PEAK_TRADE_OWNER_RUN_EVIDENCE_ROOT"
            merged[(ref.run_class, ref.run_id)] = entry

    if archive_root is not None and archive_root.is_dir():
        for ref in discover_archive_runs(archive_root):
            key = (ref.run_class, ref.run_id)
            if key not in merged:
                merged[key] = build_archive_run_entry(ref)

    entries: list[dict[str, Any]] = list(merged.values())
    for ref in discover_repo_canary_evidence(repo_root):
        entries.append(build_canary_entry(ref, repo_root))
    entries.sort(key=lambda row: (row.get("started_at") or "", row.get("run_id") or ""))
    return entries


def merge_index_entries(
    existing: Iterable[dict[str, Any]],
    fresh: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for row in existing:
        key = (str(row.get("run_class")), str(row.get("run_id")))
        merged[key] = row
    for row in fresh:
        key = (str(row.get("run_class")), str(row.get("run_id")))
        merged[key] = row
    return sorted(
        merged.values(),
        key=lambda row: (row.get("started_at") or "", row.get("run_id") or ""),
    )


def load_index_entries_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            continue
        if payload.get("schema") != SCHEMA_SIMPLE_RUN_EVIDENCE_INDEX_ENTRY_V1:
            continue
        rows.append(payload)
    return rows


def write_index_entries_jsonl(path: Path, entries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(entry, sort_keys=True) + "\n" for entry in entries]
    path.write_text("".join(lines), encoding="utf-8")


def append_index_entries_jsonl(path: Path, entries: list[dict[str, Any]]) -> None:
    existing = load_index_entries_jsonl(path)
    merged = merge_index_entries(existing, entries)
    write_index_entries_jsonl(path, merged)


def default_index_path(
    *,
    env: dict[str, str] | None = None,
    explicit_owner_root: str | Path | None = None,
) -> Path:
    from .storage_v1 import default_owner_index_path

    return default_owner_index_path(env=env, explicit=explicit_owner_root)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
