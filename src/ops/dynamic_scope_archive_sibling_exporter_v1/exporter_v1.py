"""Bounded 1:1 Dynamic Scope archive sibling exporter V1.

CAPABILITY_ID=CAPABILITY_DYNAMIC_SCOPE_ARCHIVE_SIBLING_EXPORTER_V1

Loads an already-persisted CanonicalDynamicScopeStateV1 via the canonical ops
loader and writes ``state.to_dict()`` atomically to:

    archive_root/readmodels/dynamic_scope_state_v1.json

Invariants:
- AUTHORITY_EFFECT=NONE
- no trading / dynamic-scope / orchestrator mutation
- no Dual-Write into persist_dynamic_scope_state_atomic_v1
- no presentation / dashboard imports
- no invented generated_at / effective_at / next_scope_ref / timestamps
- fail-closed on missing/corrupt/invalid source
- library-only (no automatic productive caller)
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ops.dynamic_scope_archive_sibling_exporter_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    ERROR_DIGEST_MISMATCH,
    ERROR_IDENTICAL_PATHS,
    ERROR_SOURCE_CORRUPT,
    ERROR_SOURCE_LOAD_FAILED,
    ERROR_SOURCE_MISSING,
    ERROR_SOURCE_SCHEMA_MISMATCH,
    ERROR_SOURCE_STATE_VERSION_MISMATCH,
    ERROR_WRITE_FAILED,
    OWNER,
    READMODELS_DIRNAME,
    SOURCE_SCHEMA,
    SOURCE_STATE_VERSION,
    TARGET_FILENAME,
    TARGET_RELATIVE_PATH,
)
from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    SCHEMA_VERSION,
    STATE_VERSION,
)
from src.ops.dynamic_scope_persistence_binding_v1.models_v1 import (
    CanonicalDynamicScopeStateV1,
    canonical_digest_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.persistence_v1 import (
    DynamicScopePersistenceError,
    load_dynamic_scope_state_v1,
    scope_state_path,
)
from src.ops.dynamic_scope_persistence_binding_v1.reason_codes_v1 import (
    DynamicScopeBindingFailureCodeV1,
)


@dataclass(frozen=True)
class DynamicScopeArchiveSiblingExportResultV1:
    """Structured result of a fail-closed archive sibling export attempt."""

    exported: bool
    source_path: str
    target_path: str
    schema_version: str | None = None
    state_version: str | None = None
    scope_session_id: str | None = None
    instrument_id: str | None = None
    source_payload_digest: str | None = None
    target_payload_digest: str | None = None
    bytes_written: int = 0
    replaced_existing: bool = False
    error_code: str | None = None
    failure_reason: str | None = None
    capability_id: str = CAPABILITY_ID
    authority_effect: str = AUTHORITY_EFFECT
    owner: str = OWNER


def _fail(
    *,
    source_path: str,
    target_path: str,
    error_code: str,
    failure_reason: str = "",
    replaced_existing: bool = False,
) -> DynamicScopeArchiveSiblingExportResultV1:
    return DynamicScopeArchiveSiblingExportResultV1(
        exported=False,
        source_path=source_path,
        target_path=target_path,
        error_code=error_code,
        failure_reason=failure_reason or error_code,
        replaced_existing=replaced_existing,
    )


def _serialize_payload(payload: dict[str, Any]) -> str:
    """Match canonical persistence pretty-print convention exactly."""
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"


def _atomic_write_text(*, destination: Path, body: str) -> None:
    """Atomic replace within the destination directory (tmp + fsync + os.replace)."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=destination.name + ".", dir=str(destination.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(body)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, destination)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _map_load_error(exc: DynamicScopePersistenceError) -> str:
    # from_dict() raises ValueError for unsupported state_version before the
    # loader's STATE_VERSION_MISMATCH branch; classify that message explicitly.
    detail = " ".join(str(a) for a in exc.args)
    if (
        exc.code is DynamicScopeBindingFailureCodeV1.STATE_VERSION_MISMATCH
        or "UNSUPPORTED_DYNAMIC_SCOPE_STATE_VERSION:" in detail
    ):
        return ERROR_SOURCE_STATE_VERSION_MISMATCH
    if exc.code is DynamicScopeBindingFailureCodeV1.CORRUPTED_CHECKPOINT:
        return ERROR_SOURCE_CORRUPT
    if exc.code in {
        DynamicScopeBindingFailureCodeV1.CHECKPOINT_MISSING_BEFORE_FIRST_STATE,
        DynamicScopeBindingFailureCodeV1.CHECKPOINT_MISSING_AFTER_PRIOR_COMMIT,
    }:
        return ERROR_SOURCE_MISSING
    return ERROR_SOURCE_LOAD_FAILED


def export_dynamic_scope_state_to_archive_sibling_v1(
    *,
    dynamic_scope_state_root: str | Path,
    archive_root: str | Path,
) -> DynamicScopeArchiveSiblingExportResultV1:
    """Export CanonicalDynamicScopeStateV1 1:1 into the dashboard archive sibling path.

    Uses only ``load_dynamic_scope_state_v1`` + ``CanonicalDynamicScopeStateV1.to_dict()``.
    Does not invent presentation timestamps or derived fields.
    """
    state_root = Path(dynamic_scope_state_root).expanduser().resolve()
    archive = Path(archive_root).expanduser().resolve()
    source_path = scope_state_path(state_root).resolve()
    target_path = (archive / TARGET_RELATIVE_PATH).resolve()

    if source_path == target_path:
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=ERROR_IDENTICAL_PATHS,
            failure_reason="source_path and target_path resolve to the same file",
        )

    if not source_path.is_file():
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=ERROR_SOURCE_MISSING,
            failure_reason=f"missing source file: {source_path}",
        )

    try:
        loaded = load_dynamic_scope_state_v1(state_root, require_present=True)
    except DynamicScopePersistenceError as exc:
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=_map_load_error(exc),
            failure_reason=str(exc),
        )
    except Exception as exc:  # noqa: BLE001 — fail-closed wrapper for unexpected load faults
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=ERROR_SOURCE_LOAD_FAILED,
            failure_reason=str(exc),
        )

    if loaded is None:
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=ERROR_SOURCE_MISSING,
            failure_reason="load_dynamic_scope_state_v1 returned None",
        )

    if not isinstance(loaded, CanonicalDynamicScopeStateV1):
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=ERROR_SOURCE_LOAD_FAILED,
            failure_reason="loaded object is not CanonicalDynamicScopeStateV1",
        )

    payload = loaded.to_dict()
    schema_version = str(payload.get("schema_version") or "")
    state_version = str(payload.get("state_version") or "")
    if schema_version != SCHEMA_VERSION or schema_version != SOURCE_SCHEMA:
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=ERROR_SOURCE_SCHEMA_MISMATCH,
            failure_reason=f"schema_version={schema_version!r} expected={SCHEMA_VERSION!r}",
        )
    if state_version != STATE_VERSION or state_version != SOURCE_STATE_VERSION:
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=ERROR_SOURCE_STATE_VERSION_MISMATCH,
            failure_reason=f"state_version={state_version!r} expected={STATE_VERSION!r}",
        )

    source_digest = canonical_digest_v1(payload)
    body = _serialize_payload(payload)
    replaced_existing = target_path.is_file()

    # Ensure target stays under archive_root/readmodels/<filename> only.
    expected_parent = (archive / READMODELS_DIRNAME).resolve()
    if target_path.parent != expected_parent or target_path.name != TARGET_FILENAME:
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason="resolved target escaped authorized sibling path",
        )

    try:
        _atomic_write_text(destination=target_path, body=body)
    except OSError as exc:
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=str(exc),
            replaced_existing=replaced_existing,
        )

    if not target_path.is_file():
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason="target missing after atomic write",
            replaced_existing=replaced_existing,
        )

    try:
        written_raw = target_path.read_text(encoding="utf-8")
        written_payload = json.loads(written_raw)
    except (OSError, json.JSONDecodeError) as exc:
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=f"post-write verify failed: {exc}",
            replaced_existing=replaced_existing,
        )

    if not isinstance(written_payload, dict):
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason="post-write payload is not a JSON object",
            replaced_existing=replaced_existing,
        )

    target_digest = canonical_digest_v1(written_payload)
    if target_digest != source_digest:
        return _fail(
            source_path=str(source_path),
            target_path=str(target_path),
            error_code=ERROR_DIGEST_MISMATCH,
            failure_reason=f"{source_digest}!={target_digest}",
            replaced_existing=replaced_existing,
        )

    return DynamicScopeArchiveSiblingExportResultV1(
        exported=True,
        source_path=str(source_path),
        target_path=str(target_path),
        schema_version=schema_version,
        state_version=state_version,
        scope_session_id=str(payload.get("scope_session_id") or ""),
        instrument_id=str(payload.get("instrument_id") or ""),
        source_payload_digest=source_digest,
        target_payload_digest=target_digest,
        bytes_written=len(body.encode("utf-8")),
        replaced_existing=replaced_existing,
        error_code=None,
        failure_reason=None,
    )
