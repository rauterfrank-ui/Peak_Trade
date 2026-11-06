"""Persist verified bounded P/S/T archive bundles into the owner evidence root."""

from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ops.durable_closeout_copy_verify_v0 import plan_and_execute
from scripts.ops.primary_evidence_retention_v0 import (
    BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS,
    BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS,
    MANIFEST_FILENAME,
    PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
    validate_durable_primary_evidence_root,
    verify_manifest_sha256,
)

from .constants_v1 import (
    ARCHIVE_RUN_CLASSES,
    RUN_CLASS_PAPER,
    RUN_CLASS_SHADOW,
    RUN_CLASS_TESTNET,
    RUN_STATUS_COMPLETE,
    SCHEMA_SIMPLE_RUN_EVIDENCE_INDEX_ENTRY_V1,
)
from .discover_v1 import ArchiveRunRef, archive_evidence_locator
from .index_v1 import (
    append_index_entries_jsonl,
    build_archive_run_entry,
    default_index_path,
    infer_archive_run_status,
)
from .storage_v1 import OwnerRunEvidenceRootError, resolve_owner_run_evidence_root

OWNER_PERSIST_MACHINE_PREFIX = "OWNER_RUN_EVIDENCE_PERSIST"


@dataclass(frozen=True)
class OwnerPersistResult:
    rc: int
    status: str
    message: str
    owner_dest: Path | None = None
    detail: dict[str, Any] | None = None


def _required_paths(run_class: str) -> tuple[str, ...]:
    if run_class == RUN_CLASS_PAPER:
        return PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS
    if run_class == RUN_CLASS_SHADOW:
        return BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS
    if run_class == RUN_CLASS_TESTNET:
        return BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS
    raise ValueError(f"unsupported run_class for owner persist: {run_class!r}")


def infer_run_class_from_archive_dest(archive_dest: Path) -> str | None:
    parts = archive_dest.resolve().parts
    for idx, part in enumerate(parts):
        if part == "runs" and idx + 1 < len(parts):
            lane = parts[idx + 1]
            if lane in ARCHIVE_RUN_CLASSES:
                return lane
    from .discover_v1 import infer_run_class_from_run_id

    return infer_run_class_from_run_id(archive_dest.name)


def owner_run_bundle_path(
    run_class: str,
    run_id: str,
    *,
    env: dict[str, str] | None = None,
    explicit_owner_root: str | Path | None = None,
) -> Path:
    owner_root = resolve_owner_run_evidence_root(env=env, explicit=explicit_owner_root)
    return owner_root / "runs" / run_class / run_id


def _primary_bundle_fingerprint(root: Path, required: tuple[str, ...]) -> str | None:
    digest = hashlib.sha256()
    found = False
    for rel in sorted(required):
        if rel == MANIFEST_FILENAME:
            continue
        path = root / rel
        if not path.is_file():
            continue
        found = True
        digest.update(rel.encode("utf-8"))
        digest.update(path.read_bytes())
    if not found:
        return None
    return digest.hexdigest()


def _append_owner_index_entry(
    *,
    owner_root: Path,
    run_class: str,
    run_id: str,
    run_dir: Path,
    env: dict[str, str] | None,
) -> None:
    ref = ArchiveRunRef(
        run_class=run_class,
        run_id=run_id,
        run_dir=run_dir,
        archive_root=owner_root,
    )
    entry = build_archive_run_entry(ref)
    entry["evidence_storage_kind"] = "owner_evidence_home"
    entry["archive_root_contract"] = "PEAK_TRADE_OWNER_RUN_EVIDENCE_ROOT"
    index_path = default_index_path(env=env)
    append_index_entries_jsonl(index_path, [entry])


def persist_bounded_run_to_owner_evidence(
    source_dir: Path,
    *,
    run_class: str,
    run_id: str,
    env: dict[str, str] | None = None,
    explicit_owner_root: str | Path | None = None,
) -> OwnerPersistResult:
    """Copy verified primary evidence from archive_dest into owner home storage."""
    env_map = env if env is not None else os.environ
    source = source_dir.resolve()
    if run_class not in ARCHIVE_RUN_CLASSES:
        return OwnerPersistResult(2, "blocked", f"invalid run_class={run_class!r}")

    try:
        owner_root = resolve_owner_run_evidence_root(env=env_map, explicit=explicit_owner_root)
    except OwnerRunEvidenceRootError as exc:
        return OwnerPersistResult(2, "blocked", str(exc))

    dest = owner_run_bundle_path(
        run_class, run_id, env=env_map, explicit_owner_root=explicit_owner_root
    )
    staging = dest.parent / f".{run_id}.owner_staging"

    ok_source, msg, _detail = validate_durable_primary_evidence_root(
        source,
        required_rel_paths=_required_paths(run_class),
    )
    if not ok_source:
        return OwnerPersistResult(
            2,
            "blocked",
            f"primary evidence not complete: {msg}",
            owner_dest=dest,
        )

    status = infer_archive_run_status(source, run_class)
    if status != RUN_STATUS_COMPLETE:
        return OwnerPersistResult(
            2,
            "blocked",
            f"run status {status!r} is not eligible for owner persistence",
            owner_dest=dest,
        )

    required = _required_paths(run_class)
    source_fingerprint = _primary_bundle_fingerprint(source, required)
    if dest.is_dir():
        dest_ok, _ = verify_manifest_sha256(dest)
        dest_fingerprint = _primary_bundle_fingerprint(dest, required)
        if (
            source_fingerprint
            and source_fingerprint == dest_fingerprint
            and dest_ok
            and infer_archive_run_status(dest, run_class) == status
        ):
            _append_owner_index_entry(
                owner_root=owner_root,
                run_class=run_class,
                run_id=run_id,
                run_dir=dest,
                env=env_map,
            )
            return OwnerPersistResult(
                0,
                "verified_existing",
                "owner bundle already present with identical manifest",
                owner_dest=dest,
            )
        return OwnerPersistResult(
            2,
            "collision",
            "owner destination exists with differing content (fail-closed)",
            owner_dest=dest,
        )

    if staging.exists():
        return OwnerPersistResult(
            2,
            "blocked",
            f"incomplete owner staging directory exists: {staging}",
            owner_dest=dest,
        )

    copy_result = plan_and_execute(
        source_dir=source,
        dest_dir=staging,
        dry_run=False,
        pr_number=None,
        pr_json=None,
        require_closeout_report=False,
        require_durable_pointer_evidence=False,
        durable_pointer_patterns=(),
        allow_tmp_source=False,
        force=True,
    )
    if copy_result.status != "pass":
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        return OwnerPersistResult(
            2,
            "copy_failed",
            copy_result.error or "durable closeout copy failed",
            owner_dest=dest,
        )

    ok_staging, verify_msg = verify_manifest_sha256(staging)
    if not ok_staging:
        shutil.rmtree(staging, ignore_errors=True)
        return OwnerPersistResult(
            2,
            "blocked",
            f"staging manifest verify failed: {verify_msg}",
            owner_dest=dest,
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    staging.rename(dest)

    _append_owner_index_entry(
        owner_root=owner_root,
        run_class=run_class,
        run_id=run_id,
        run_dir=dest,
        env=env_map,
    )
    locator = archive_evidence_locator(run_class, run_id)
    return OwnerPersistResult(
        0,
        "persisted",
        f"owner evidence persisted at {locator}",
        owner_dest=dest,
        detail={"schema": SCHEMA_SIMPLE_RUN_EVIDENCE_INDEX_ENTRY_V1},
    )


def emit_owner_persist_machine_lines(result: OwnerPersistResult) -> None:
    print(f"{OWNER_PERSIST_MACHINE_PREFIX}_RC={result.rc}")
    print(f"{OWNER_PERSIST_MACHINE_PREFIX}_STATUS={result.status}")
    print(f"{OWNER_PERSIST_MACHINE_PREFIX}_MESSAGE={result.message}")
    if result.owner_dest is not None:
        print(f"{OWNER_PERSIST_MACHINE_PREFIX}_DEST={result.owner_dest}")
