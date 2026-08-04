"""Bounded 1:1 Canonical Decision archive sibling exporter V1.

CAPABILITY_ID=CAPABILITY_CANONICAL_DECISION_ARCHIVE_SIBLING_EXPORTER_V1

Loads an already-produced CanonicalTradingDecisionEvidenceV1 JSON payload from
an explicit caller-supplied path and writes it atomically to:

    archive_root/readmodels/canonical_trading_decision_evidence.v1.json

Invariants:
- AUTHORITY_EFFECT=NONE
- DECISION_AUTHORITY_EFFECT=NONE
- no trading / decision recomputation / evaluator imports
- no presentation / dashboard / materializer imports
- no invented decision facts, timestamps, or generated_at
- no archive discovery / latest / registry selection
- fail-closed on missing/corrupt/invalid source
- library-only (no automatic productive caller)
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
from src.ops.canonical_decision_archive_sibling_exporter_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    DECISION_AUTHORITY_EFFECT,
    ERROR_DIGEST_MISMATCH,
    ERROR_IDENTICAL_PATHS,
    ERROR_PATH_REQUIRED,
    ERROR_SOURCE_CORRUPT,
    ERROR_SOURCE_INVALID,
    ERROR_SOURCE_LOAD_FAILED,
    ERROR_SOURCE_MISSING,
    ERROR_SOURCE_SCHEMA_MISMATCH,
    ERROR_WRITE_FAILED,
    OWNER,
    READMODELS_DIRNAME,
    REQUIRED_EVIDENCE_FIELDS,
    SOURCE_EVIDENCE_SCHEMA_VERSION,
    TARGET_FILENAME,
    TARGET_RELATIVE_PATH,
)


@dataclass(frozen=True)
class CanonicalDecisionArchiveSiblingExportResultV1:
    """Structured result of a fail-closed archive sibling export attempt."""

    exported: bool
    source_path: str
    target_path: str
    evidence_schema_version: str | None = None
    decision_id: str | None = None
    instrument_id: str | None = None
    decision_outcome: str | None = None
    source_payload_digest: str | None = None
    target_payload_digest: str | None = None
    bytes_written: int = 0
    replaced_existing: bool = False
    error_code: str | None = None
    failure_reason: str | None = None
    capability_id: str = CAPABILITY_ID
    authority_effect: str = AUTHORITY_EFFECT
    decision_authority_effect: str = DECISION_AUTHORITY_EFFECT
    owner: str = OWNER


def _fail(
    *,
    source_path: str,
    target_path: str,
    error_code: str,
    failure_reason: str = "",
    replaced_existing: bool = False,
) -> CanonicalDecisionArchiveSiblingExportResultV1:
    return CanonicalDecisionArchiveSiblingExportResultV1(
        exported=False,
        source_path=source_path,
        target_path=target_path,
        error_code=error_code,
        failure_reason=failure_reason or error_code,
        replaced_existing=replaced_existing,
    )


def _require_nonempty_str(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def coerce_canonical_decision_evidence_export_payload_v1(
    source: object,
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and copy producer evidence fields without mutation or recomputation."""
    if source is None:
        return None, ERROR_SOURCE_MISSING
    if not isinstance(source, Mapping):
        return None, ERROR_SOURCE_INVALID

    raw: Mapping[str, Any] = source
    if "evidence" in raw and isinstance(raw.get("evidence"), Mapping):
        nested = raw["evidence"]
        top_decision_id = raw.get("decision_id")
        nested_decision_id = nested.get("decision_id")
        if (
            isinstance(top_decision_id, str)
            and top_decision_id.strip()
            and isinstance(nested_decision_id, str)
            and nested_decision_id.strip()
            and top_decision_id.strip() != nested_decision_id.strip()
        ):
            return None, ERROR_SOURCE_INVALID
        if not all(key in raw for key in REQUIRED_EVIDENCE_FIELDS):
            raw = nested

    evidence = deepcopy(dict(raw))
    missing = [key for key in REQUIRED_EVIDENCE_FIELDS if key not in evidence]
    if missing:
        return None, ERROR_SOURCE_INVALID

    schema_version = _require_nonempty_str(evidence.get("evidence_schema_version"))
    if schema_version is None:
        return None, ERROR_SOURCE_INVALID
    if schema_version != SOURCE_EVIDENCE_SCHEMA_VERSION:
        return None, ERROR_SOURCE_SCHEMA_MISMATCH

    for key in (
        "instrument_id",
        "decision_outcome",
        "next_direction_state",
        "decision_id",
    ):
        if _require_nonempty_str(evidence.get(key)) is None:
            return None, ERROR_SOURCE_INVALID

    if "reason_codes" in evidence and evidence["reason_codes"] is not None:
        if not isinstance(evidence["reason_codes"], (list, tuple)):
            return None, ERROR_SOURCE_INVALID

    return evidence, None


def load_canonical_decision_evidence_export_payload_v1(
    evidence_source_path: str | Path,
) -> tuple[dict[str, Any] | None, str, str | None]:
    """Load explicit-path evidence JSON. Never discovers or selects latest."""
    if evidence_source_path is None or (
        isinstance(evidence_source_path, str) and not str(evidence_source_path).strip()
    ):
        return None, "", ERROR_PATH_REQUIRED

    source_path = Path(evidence_source_path).expanduser().resolve()
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

    evidence, error = coerce_canonical_decision_evidence_export_payload_v1(payload)
    if evidence is None:
        return None, source_str, error
    return evidence, source_str, None


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


def export_canonical_decision_evidence_to_archive_sibling_v1(
    *,
    evidence_source_path: str | Path,
    archive_root: str | Path,
) -> CanonicalDecisionArchiveSiblingExportResultV1:
    """Export already-produced decision evidence 1:1 into the archive sibling path.

    Does not invent presentation timestamps or recompute decisions.
    """
    archive = Path(archive_root).expanduser().resolve()
    target_path = (archive / TARGET_RELATIVE_PATH).resolve()

    evidence, source_str, load_error = load_canonical_decision_evidence_export_payload_v1(
        evidence_source_path
    )
    source_path = Path(source_str).resolve() if source_str else Path()
    if evidence is None:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=load_error or ERROR_SOURCE_LOAD_FAILED,
            failure_reason=load_error or ERROR_SOURCE_LOAD_FAILED,
        )

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

    try:
        source_digest = canonical_digest_v1(evidence)
    except CanonicalJsonErrorV1 as exc:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_SOURCE_INVALID,
            failure_reason=str(exc),
        )

    body = _serialize_payload(evidence)
    replaced_existing = target_path.is_file()

    try:
        _atomic_write_text(destination=target_path, body=body)
    except OSError as exc:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=str(exc),
            replaced_existing=replaced_existing,
        )

    if not target_path.is_file():
        return _fail(
            source_path=source_str,
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
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=f"post-write verify failed: {exc}",
            replaced_existing=replaced_existing,
        )

    if not isinstance(written_payload, dict):
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason="post-write payload is not a JSON object",
            replaced_existing=replaced_existing,
        )

    try:
        target_digest = canonical_digest_v1(written_payload)
    except CanonicalJsonErrorV1 as exc:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=str(exc),
            replaced_existing=replaced_existing,
        )

    if target_digest != source_digest:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_DIGEST_MISMATCH,
            failure_reason=f"{source_digest}!={target_digest}",
            replaced_existing=replaced_existing,
        )

    return CanonicalDecisionArchiveSiblingExportResultV1(
        exported=True,
        source_path=source_str,
        target_path=str(target_path),
        evidence_schema_version=str(evidence.get("evidence_schema_version") or ""),
        decision_id=str(evidence.get("decision_id") or ""),
        instrument_id=str(evidence.get("instrument_id") or ""),
        decision_outcome=str(evidence.get("decision_outcome") or ""),
        source_payload_digest=source_digest,
        target_payload_digest=target_digest,
        bytes_written=len(body.encode("utf-8")),
        replaced_existing=replaced_existing,
        error_code=None,
        failure_reason=None,
    )
