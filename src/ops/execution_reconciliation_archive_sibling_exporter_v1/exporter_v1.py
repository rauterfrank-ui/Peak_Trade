"""Bounded 1:1 Execution/Reconciliation archive sibling exporter V1.

CAPABILITY_ID=CAPABILITY_EXECUTION_RECONCILIATION_ARCHIVE_SIBLING_EXPORTER_V1

Writes already-mapped Execution/Reconciliation field dicts atomically to:

    archive_root/readmodels/execution_reconciliation.v1.json

Invariants:
- AUTHORITY_EFFECT=NONE
- no order-intent builder / reconciliation evaluator imports or recomputation
- no presentation / dashboard imports at module top level
- no invented statuses, refs, or timestamps
- fail-closed on missing/corrupt/invalid source
"""

from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.archive_sibling_export_contract_v1.canonical_digest import (
    CanonicalJsonErrorV1,
    canonical_digest_v1,
)
from src.ops.execution_reconciliation_archive_sibling_exporter_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    ERROR_DIGEST_MISMATCH,
    ERROR_IDENTICAL_PATHS,
    ERROR_SOURCE_CORRUPT,
    ERROR_SOURCE_INVALID,
    ERROR_SOURCE_LOAD_FAILED,
    ERROR_SOURCE_MISSING,
    ERROR_WRITE_FAILED,
    EXECUTION_AUTHORITY_EFFECT,
    OWNER,
    READMODELS_DIRNAME,
    TARGET_FILENAME,
    TARGET_RELATIVE_PATH,
)


@dataclass(frozen=True)
class ExecutionReconciliationArchiveSiblingExportResultV1:
    exported: bool
    source_path: str
    target_path: str
    execution_status: str | None = None
    source_payload_digest: str | None = None
    target_payload_digest: str | None = None
    bytes_written: int = 0
    replaced_existing: bool = False
    error_code: str | None = None
    failure_reason: str | None = None
    capability_id: str = CAPABILITY_ID
    authority_effect: str = AUTHORITY_EFFECT
    execution_authority_effect: str = EXECUTION_AUTHORITY_EFFECT
    owner: str = OWNER


def _fail(
    *,
    source_path: str,
    target_path: str,
    error_code: str,
    failure_reason: str = "",
    replaced_existing: bool = False,
) -> ExecutionReconciliationArchiveSiblingExportResultV1:
    return ExecutionReconciliationArchiveSiblingExportResultV1(
        exported=False,
        source_path=source_path,
        target_path=target_path,
        error_code=error_code,
        failure_reason=failure_reason or error_code,
        replaced_existing=replaced_existing,
    )


def coerce_execution_reconciliation_fields_export_payload_v1(
    source: object,
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate export fields via the materializer-owned coerce contract (lazy bind)."""
    from src.webui.workflow_dashboard_readmodel_v1.execution_reconciliation_presentation_projection_materializer_v1 import (
        coerce_execution_reconciliation_fields_mapping_v1,
    )

    coerced, errors = coerce_execution_reconciliation_fields_mapping_v1(source)
    if coerced is None:
        code = errors[0] if errors else ERROR_SOURCE_INVALID
        return None, code
    return deepcopy(dict(coerced)), None


def load_execution_reconciliation_fields_export_payload_v1(
    fields_source_path: str | Path,
) -> tuple[dict[str, Any] | None, str, str | None]:
    if fields_source_path is None or (
        isinstance(fields_source_path, str) and not str(fields_source_path).strip()
    ):
        return None, "", ERROR_SOURCE_MISSING

    source_path = Path(fields_source_path).expanduser().resolve()
    source_str = str(source_path)
    if not source_path.is_file():
        return None, source_str, ERROR_SOURCE_MISSING

    try:
        raw_text = source_path.read_text(encoding="utf-8")
    except OSError:
        return None, source_str, ERROR_SOURCE_LOAD_FAILED

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return None, source_str, ERROR_SOURCE_CORRUPT

    if not isinstance(payload, dict):
        return None, source_str, ERROR_SOURCE_INVALID

    fields, error = coerce_execution_reconciliation_fields_export_payload_v1(payload)
    if fields is None:
        return None, source_str, error
    return fields, source_str, None


def _serialize_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _atomic_write_text(*, destination: Path, body: str) -> None:
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


def export_execution_reconciliation_fields_payload_to_archive_sibling_v1(
    *,
    fields_payload: Mapping[str, Any],
    archive_root: str | Path,
    source_label: str = "in_memory_fields_payload",
) -> ExecutionReconciliationArchiveSiblingExportResultV1:
    archive = Path(archive_root).expanduser().resolve()
    target_path = (archive / TARGET_RELATIVE_PATH).resolve()
    label = source_label.strip() or "in_memory_fields_payload"

    fields, error = coerce_execution_reconciliation_fields_export_payload_v1(fields_payload)
    if fields is None:
        return _fail(
            source_path=label,
            target_path=str(target_path),
            error_code=error or ERROR_SOURCE_INVALID,
            failure_reason=error or ERROR_SOURCE_INVALID,
        )

    try:
        source_digest = canonical_digest_v1(fields)
    except CanonicalJsonErrorV1 as exc:
        return _fail(
            source_path=label,
            target_path=str(target_path),
            error_code=ERROR_SOURCE_INVALID,
            failure_reason=str(exc),
        )

    replaced_existing = target_path.is_file()
    body = _serialize_payload(fields)
    try:
        _atomic_write_text(destination=target_path, body=body)
    except OSError as exc:
        return _fail(
            source_path=label,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=str(exc),
            replaced_existing=replaced_existing,
        )

    try:
        written_payload = json.loads(target_path.read_text(encoding="utf-8"))
        target_digest = canonical_digest_v1(written_payload)
    except (OSError, json.JSONDecodeError, CanonicalJsonErrorV1) as exc:
        return _fail(
            source_path=label,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=str(exc),
            replaced_existing=replaced_existing,
        )

    if target_digest != source_digest:
        return _fail(
            source_path=label,
            target_path=str(target_path),
            error_code=ERROR_DIGEST_MISMATCH,
            failure_reason=f"{source_digest}!={target_digest}",
            replaced_existing=replaced_existing,
        )

    return ExecutionReconciliationArchiveSiblingExportResultV1(
        exported=True,
        source_path=label,
        target_path=str(target_path),
        execution_status=str(fields.get("execution_status") or ""),
        source_payload_digest=source_digest,
        target_payload_digest=target_digest,
        bytes_written=len(body.encode("utf-8")),
        replaced_existing=replaced_existing,
        error_code=None,
        failure_reason=None,
    )


def export_execution_reconciliation_fields_to_archive_sibling_v1(
    *,
    fields_source_path: str | Path,
    archive_root: str | Path,
) -> ExecutionReconciliationArchiveSiblingExportResultV1:
    archive = Path(archive_root).expanduser().resolve()
    target_path = (archive / TARGET_RELATIVE_PATH).resolve()

    fields, source_str, load_error = load_execution_reconciliation_fields_export_payload_v1(
        fields_source_path
    )
    if fields is None:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=load_error or ERROR_SOURCE_LOAD_FAILED,
            failure_reason=load_error or ERROR_SOURCE_LOAD_FAILED,
        )

    source_path = Path(source_str).resolve()
    if source_path == target_path:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_IDENTICAL_PATHS,
            failure_reason="source_path and target_path resolve to the same file",
        )

    expected_parent = (archive / READMODELS_DIRNAME).resolve()
    if target_path.parent != expected_parent or target_path.name != TARGET_FILENAME:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason="resolved target escaped authorized sibling path",
        )

    return export_execution_reconciliation_fields_payload_to_archive_sibling_v1(
        fields_payload=fields,
        archive_root=archive,
        source_label=source_str,
    )


def export_execution_reconciliation_to_archive_sibling_from_replay_commit_v1(
    *,
    archive_root: str | Path,
    replay_intermediate: object | None,
    decision_evidence: object | None,
    source_label: str = "integrated_replay_commit",
) -> ExecutionReconciliationArchiveSiblingExportResultV1:
    from src.ops.execution_reconciliation_archive_sibling_exporter_v1.replay_commit_source_v1 import (
        build_execution_reconciliation_sibling_payload_from_replay_commit_v1,
    )

    label = source_label.strip() or "integrated_replay_commit"
    archive = Path(archive_root).expanduser().resolve()
    target_path = (archive / TARGET_RELATIVE_PATH).resolve()

    payload, build_errors = build_execution_reconciliation_sibling_payload_from_replay_commit_v1(
        replay_intermediate=replay_intermediate,
        decision_evidence=decision_evidence,
    )
    if payload is None:
        code = build_errors[0] if build_errors else ERROR_SOURCE_INVALID
        return _fail(
            source_path=label,
            target_path=str(target_path),
            error_code=code,
            failure_reason=code,
        )
    return export_execution_reconciliation_fields_payload_to_archive_sibling_v1(
        fields_payload=payload,
        archive_root=archive,
        source_label=label,
    )
