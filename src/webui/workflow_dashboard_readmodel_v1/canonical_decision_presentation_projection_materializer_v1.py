"""Non-authoritative materializer for canonical decision presentation projection.

CAPABILITY_ID=CAPABILITY_PRESENTATION_CANONICAL_DECISION_PROJECTION_MATERIALIZER_V1

Consumes already-produced CanonicalTradingDecisionEvidenceV1 field payloads (or
the durable sibling producer dump under the Workflow Dashboard archive root)
and writes the existing non-authoritative presentation projection schema to the
loader-owned path. This module:

- AUTHORITY_EFFECT=NONE
- DECISION_AUTHORITY_EFFECT=NONE
- never creates, mutates, or evaluates trading decisions
- never imports trading.master_v2 decision producers or evaluators
- never calls transition_state / compose_double_play / KillSwitch / risk / sizing
- never invents decision facts, timestamps, or default field values
- fail-closed: missing source → MISSING_SOURCE and no artifact write;
  invalid source → FAIL_CLOSED and no artifact write
- projection remains non-authoritative and must never flow back into runtime
  or authority chains

Deterministic serialization and atomic replace only. This projection path does
not own a separate MANIFEST contract; integrity follows the existing loader
schema/authority/evidence checks.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .canonical_decision_presentation_projection_v1 import (
    AUTHORITY_EFFECT,
    DECISION_AUTHORITY_EFFECT,
    LOAD_ERROR_EVIDENCE_INVALID,
    LOAD_ERROR_SCHEMA_MISMATCH,
    LOAD_ERROR_TIMESTAMP_MISSING,
    PRODUCER_EVIDENCE_SCHEMA_VERSION,
    PROJECTION_ROLE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STORAGE_RELATIVE_PATH,
    map_canonical_decision_evidence_to_binder_fields_v1,
)

CAPABILITY_ID = "CAPABILITY_PRESENTATION_CANONICAL_DECISION_PROJECTION_MATERIALIZER_V1"
OWNER_MODULE = (
    "webui.workflow_dashboard_readmodel_v1."
    "canonical_decision_presentation_projection_materializer_v1"
)
SOURCE_EVIDENCE_RELATIVE_PATH = "readmodels/canonical_trading_decision_evidence.v1.json"

STATUS_WRITTEN = "WRITTEN"
STATUS_MISSING_SOURCE = "MISSING_SOURCE"
STATUS_FAIL_CLOSED = "FAIL_CLOSED"

MATERIALIZE_ERROR_MISSING_SOURCE = "MISSING_SOURCE"
MATERIALIZE_ERROR_INVALID_JSON = "CANONICAL_DECISION_PRESENTATION_MATERIALIZER_INVALID_JSON"
MATERIALIZE_ERROR_INVALID_SOURCE = "CANONICAL_DECISION_PRESENTATION_MATERIALIZER_INVALID_SOURCE"
MATERIALIZE_ERROR_WRITE_FAILED = "CANONICAL_DECISION_PRESENTATION_MATERIALIZER_WRITE_FAILED"

_REQUIRED_EVIDENCE_ATTRS = (
    "instrument_id",
    "decision_outcome",
    "next_direction_state",
    "decision_id",
    "evidence_schema_version",
)


@dataclass(frozen=True)
class CanonicalDecisionPresentationMaterializeResultV1:
    """Result of a fail-closed presentation projection materialize attempt."""

    written: bool
    status: str
    errors: tuple[str, ...]
    projection_path: str | None = None
    source_path: str | None = None
    decision_id: str | None = None
    payload_digest: str | None = None


def _empty_result(
    *,
    status: str,
    errors: tuple[str, ...],
    source_path: str | None = None,
) -> CanonicalDecisionPresentationMaterializeResultV1:
    return CanonicalDecisionPresentationMaterializeResultV1(
        written=False,
        status=status,
        errors=errors,
        source_path=source_path,
    )


def _require_nonempty_str(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def coerce_canonical_decision_evidence_mapping_v1(
    source: object,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Copy producer evidence fields without mutating the caller-owned source."""
    if source is None:
        return None, (MATERIALIZE_ERROR_MISSING_SOURCE,)

    raw: Mapping[str, Any]
    if isinstance(source, Mapping):
        raw = source
    else:
        extracted: dict[str, Any] = {}
        for key in _REQUIRED_EVIDENCE_ATTRS:
            if not hasattr(source, key):
                return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_EVIDENCE_INVALID)
            extracted[key] = getattr(source, key)
        for optional in ("reason_codes", "semantic_digest", "evidence_digest"):
            if hasattr(source, optional):
                extracted[optional] = getattr(source, optional)
        raw = extracted

    # Nested producer dump envelope: {"evidence": {...}} without conflicting
    # top-level decision identity.
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
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_EVIDENCE_INVALID)
        # Prefer nested producer payload when present as the sole evidence body.
        if not all(key in raw for key in _REQUIRED_EVIDENCE_ATTRS):
            raw = nested

    evidence = deepcopy(dict(raw))
    missing = [key for key in _REQUIRED_EVIDENCE_ATTRS if key not in evidence]
    if missing:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_EVIDENCE_INVALID)

    schema_version = _require_nonempty_str(evidence.get("evidence_schema_version"))
    if schema_version is None:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_EVIDENCE_INVALID)
    if schema_version != PRODUCER_EVIDENCE_SCHEMA_VERSION:
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_SCHEMA_MISMATCH)

    for key in (
        "instrument_id",
        "decision_outcome",
        "next_direction_state",
        "decision_id",
    ):
        if _require_nonempty_str(evidence.get(key)) is None:
            return None, (MATERIALIZE_ERROR_INVALID_SOURCE, LOAD_ERROR_EVIDENCE_INVALID)

    return evidence, ()


def build_canonical_decision_presentation_projection_payload_v1(
    *,
    evidence: object,
    generated_at: str,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Build the loader-compatible projection envelope from producer evidence."""
    evidence_mapping, coerce_errors = coerce_canonical_decision_evidence_mapping_v1(evidence)
    if evidence_mapping is None:
        return None, coerce_errors

    if _require_nonempty_str(generated_at) is None:
        return None, (LOAD_ERROR_TIMESTAMP_MISSING,)

    binder_fields, map_errors = map_canonical_decision_evidence_to_binder_fields_v1(
        evidence=evidence_mapping,
        generated_at=generated_at,
        effective_at=effective_at,
        source_reference=source_reference,
    )
    if binder_fields is None:
        return None, map_errors

    evidence_out: dict[str, Any] = {
        "decision_id": binder_fields["decision_id"],
        "decision_outcome": binder_fields["decision_outcome"],
        "evidence_schema_version": binder_fields["evidence_schema_version"],
        "instrument_id": binder_fields["instrument_id"],
        "next_direction_state": binder_fields["next_direction_state"],
        "reason_codes": list(binder_fields.get("reason_codes", ())),
    }
    if "semantic_digest" in binder_fields:
        evidence_out["semantic_digest"] = binder_fields["semantic_digest"]

    payload: dict[str, Any] = {
        "authority_effect": AUTHORITY_EFFECT,
        "decision_authority_effect": DECISION_AUTHORITY_EFFECT,
        "evidence": evidence_out,
        "generated_at": binder_fields["generated_at"],
        "projection_role": PROJECTION_ROLE,
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
    }
    if "effective_at" in binder_fields:
        payload["effective_at"] = binder_fields["effective_at"]
    if "source_reference" in binder_fields:
        payload["source_reference"] = binder_fields["source_reference"]
    return payload, ()


def serialize_canonical_decision_presentation_projection_v1(
    payload: Mapping[str, Any],
) -> str:
    """Deterministic JSON serialization for the presentation projection artifact."""
    return json.dumps(dict(payload), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _atomic_write_text(*, destination: Path, body: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, destination)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def write_canonical_decision_presentation_projection_v1(
    archive_root: str | Path,
    payload: Mapping[str, Any],
) -> CanonicalDecisionPresentationMaterializeResultV1:
    """Atomically persist an already-validated projection payload."""
    if payload.get("schema_name") != SCHEMA_NAME:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(LOAD_ERROR_SCHEMA_MISMATCH,),
        )
    schema_version = payload.get("schema_version")
    if schema_version is not None and int(schema_version) != SCHEMA_VERSION:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(LOAD_ERROR_SCHEMA_MISMATCH,),
        )
    if (
        payload.get("authority_effect") != AUTHORITY_EFFECT
        or payload.get("decision_authority_effect") != DECISION_AUTHORITY_EFFECT
    ):
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_INVALID_SOURCE,),
        )

    root = Path(archive_root).expanduser().resolve()
    path = root / STORAGE_RELATIVE_PATH
    body = serialize_canonical_decision_presentation_projection_v1(payload)
    try:
        _atomic_write_text(destination=path, body=body)
    except OSError:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(MATERIALIZE_ERROR_WRITE_FAILED,),
        )

    evidence = payload.get("evidence")
    decision_id = None
    if isinstance(evidence, Mapping):
        raw_id = evidence.get("decision_id")
        if isinstance(raw_id, str) and raw_id.strip():
            decision_id = raw_id.strip()

    return CanonicalDecisionPresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=str(path),
        decision_id=decision_id,
        payload_digest=hashlib.sha256(body.encode("utf-8")).hexdigest(),
    )


def try_load_canonical_decision_evidence_source_v1(
    archive_root: str | Path,
) -> tuple[dict[str, Any] | None, tuple[str, ...], str | None]:
    """Load the sole durable producer evidence sibling without inventing content."""
    root = Path(archive_root).expanduser().resolve()
    path = root / SOURCE_EVIDENCE_RELATIVE_PATH
    source_path = str(path)
    if not path.is_file():
        return None, (MATERIALIZE_ERROR_MISSING_SOURCE,), source_path
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None, (MATERIALIZE_ERROR_INVALID_JSON,), source_path
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None, (MATERIALIZE_ERROR_INVALID_JSON,), source_path
    if not isinstance(payload, dict):
        return None, (MATERIALIZE_ERROR_INVALID_SOURCE,), source_path
    evidence, errors = coerce_canonical_decision_evidence_mapping_v1(payload)
    if evidence is None:
        return None, errors, source_path
    return evidence, (), source_path


def materialize_canonical_decision_presentation_projection_v1(
    archive_root: str | Path,
    *,
    evidence: object | None = None,
    generated_at: str | None = None,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> CanonicalDecisionPresentationMaterializeResultV1:
    """Materialize the presentation projection from producer evidence or durable source.

    Missing source yields MISSING_SOURCE and does not write an artifact.
    Invalid source or missing required timestamps fail closed without writing.
    Caller-owned evidence inputs are never mutated.
    """
    source_path: str | None = None
    source_obj: object | None = evidence
    if source_obj is None:
        loaded, load_errors, source_path = try_load_canonical_decision_evidence_source_v1(
            archive_root
        )
        if loaded is None:
            status = (
                STATUS_MISSING_SOURCE
                if MATERIALIZE_ERROR_MISSING_SOURCE in load_errors
                else STATUS_FAIL_CLOSED
            )
            return _empty_result(status=status, errors=load_errors, source_path=source_path)
        source_obj = loaded

    if _require_nonempty_str(generated_at) is None:
        return _empty_result(
            status=STATUS_FAIL_CLOSED,
            errors=(LOAD_ERROR_TIMESTAMP_MISSING,),
            source_path=source_path,
        )

    # Snapshot caller-owned mapping to prove / preserve non-mutation.
    caller_snapshot = deepcopy(evidence) if isinstance(evidence, Mapping) else None

    payload, build_errors = build_canonical_decision_presentation_projection_payload_v1(
        evidence=source_obj,
        generated_at=generated_at,
        effective_at=effective_at,
        source_reference=source_reference,
    )
    if isinstance(evidence, Mapping) and caller_snapshot is not None:
        if dict(evidence) != dict(caller_snapshot):
            return _empty_result(
                status=STATUS_FAIL_CLOSED,
                errors=(MATERIALIZE_ERROR_INVALID_SOURCE,),
                source_path=source_path,
            )
    if payload is None:
        status = (
            STATUS_MISSING_SOURCE
            if MATERIALIZE_ERROR_MISSING_SOURCE in build_errors
            else STATUS_FAIL_CLOSED
        )
        return _empty_result(status=status, errors=build_errors, source_path=source_path)

    result = write_canonical_decision_presentation_projection_v1(archive_root, payload)
    if not result.written:
        return result
    return CanonicalDecisionPresentationMaterializeResultV1(
        written=True,
        status=STATUS_WRITTEN,
        errors=(),
        projection_path=result.projection_path,
        source_path=source_path,
        decision_id=result.decision_id,
        payload_digest=result.payload_digest,
    )
