"""Non-authoritative presentation projection for canonical decision evidence.

CAPABILITY_ID=CAPABILITY_PRESENTATION_CANONICAL_DECISION_AUTOBIND_V1

Reads already-produced CanonicalTradingDecisionEvidenceV1 field payloads from a
single durable archive path and maps them field-for-field into Landscape binder
injection fields. This module:

- AUTHORITY_EFFECT=NONE
- DECISION_AUTHORITY_EFFECT=NONE
- never creates, mutates, or evaluates trading decisions
- never imports trading.master_v2 decision producers or evaluators
- never calls transition_state / compose_double_play / KillSwitch / risk / sizing
- fail-closed: missing, invalid, or ambiguous sources → no fields (MISSING_SOURCE)

Deterministic source selection: exactly one well-known relative path under the
Workflow Dashboard archive root. No silent multi-candidate "latest" picking.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SCHEMA_NAME = "canonical_decision_presentation_projection.v1"
SCHEMA_VERSION = 1
STORAGE_RELATIVE_PATH = "readmodels/canonical_decision_presentation_projection.v1.json"
PRODUCER_EVIDENCE_SCHEMA_VERSION = "canonical_trading_decision_evidence_v1"
AUTHORITY_EFFECT = "NONE"
DECISION_AUTHORITY_EFFECT = "NONE"
PROJECTION_ROLE = "NON_AUTHORITATIVE_PRESENTATION_PROJECTION"
OWNER_MODULE = "webui.workflow_dashboard_readmodel_v1.canonical_decision_presentation_projection_v1"

LOAD_ERROR_ABSENT = "CANONICAL_DECISION_PRESENTATION_PROJECTION_ABSENT"
LOAD_ERROR_INVALID_JSON = "CANONICAL_DECISION_PRESENTATION_PROJECTION_INVALID_JSON"
LOAD_ERROR_SCHEMA_MISMATCH = "CANONICAL_DECISION_PRESENTATION_PROJECTION_SCHEMA_MISMATCH"
LOAD_ERROR_AUTHORITY_CLAIM = "CANONICAL_DECISION_PRESENTATION_PROJECTION_AUTHORITY_CLAIM"
LOAD_ERROR_EVIDENCE_INVALID = "CANONICAL_DECISION_PRESENTATION_PROJECTION_EVIDENCE_INVALID"
LOAD_ERROR_AMBIGUOUS = "CANONICAL_DECISION_PRESENTATION_PROJECTION_AMBIGUOUS_SOURCE"
LOAD_ERROR_TIMESTAMP_MISSING = "CANONICAL_DECISION_PRESENTATION_PROJECTION_TIMESTAMP_MISSING"

_REQUIRED_EVIDENCE_KEYS = (
    "instrument_id",
    "decision_outcome",
    "next_direction_state",
    "decision_id",
    "evidence_schema_version",
)


@dataclass(frozen=True)
class CanonicalDecisionPresentationLoadV1:
    """Result of a fail-closed presentation projection load attempt."""

    loaded: bool
    load_errors: tuple[str, ...]
    binder_fields: Mapping[str, Any] | None = None
    source_path: str | None = None
    evidence_digest: str | None = None
    decision_id: str | None = None


def _empty(*, load_errors: tuple[str, ...]) -> CanonicalDecisionPresentationLoadV1:
    return CanonicalDecisionPresentationLoadV1(loaded=False, load_errors=load_errors)


def _require_nonempty_str(payload: Mapping[str, Any], key: str) -> str | None:
    raw = payload.get(key)
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip()


def _evidence_payload_from_envelope(
    payload: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, tuple[str, ...]]:
    """Extract nested producer evidence; fail closed on ambiguity."""
    if "evidence" not in payload:
        return None, (LOAD_ERROR_EVIDENCE_INVALID,)
    evidence = payload.get("evidence")
    if not isinstance(evidence, Mapping):
        return None, (LOAD_ERROR_EVIDENCE_INVALID,)
    # Reject dual top-level + nested producer identity (ambiguous source shape).
    top_level_decision_id = payload.get("decision_id")
    nested_decision_id = evidence.get("decision_id")
    if (
        isinstance(top_level_decision_id, str)
        and top_level_decision_id.strip()
        and isinstance(nested_decision_id, str)
        and nested_decision_id.strip()
        and top_level_decision_id.strip() != nested_decision_id.strip()
    ):
        return None, (LOAD_ERROR_AMBIGUOUS,)
    return evidence, ()


def _validate_evidence_fields(
    evidence: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    missing = [key for key in _REQUIRED_EVIDENCE_KEYS if key not in evidence]
    if missing:
        return None, (LOAD_ERROR_EVIDENCE_INVALID,)

    schema_version = _require_nonempty_str(evidence, "evidence_schema_version")
    if schema_version != PRODUCER_EVIDENCE_SCHEMA_VERSION:
        return None, (LOAD_ERROR_SCHEMA_MISMATCH,)

    instrument_id = _require_nonempty_str(evidence, "instrument_id")
    decision_outcome = _require_nonempty_str(evidence, "decision_outcome")
    next_direction_state = _require_nonempty_str(evidence, "next_direction_state")
    decision_id = _require_nonempty_str(evidence, "decision_id")
    if not instrument_id or not decision_outcome or not next_direction_state or not decision_id:
        return None, (LOAD_ERROR_EVIDENCE_INVALID,)

    out: dict[str, Any] = {
        "instrument_id": instrument_id,
        "decision_outcome": decision_outcome,
        "next_direction_state": next_direction_state,
        "decision_id": decision_id,
        "evidence_schema_version": schema_version,
    }

    raw_codes = evidence.get("reason_codes", ())
    if raw_codes is None:
        raw_codes = ()
    if not isinstance(raw_codes, (list, tuple)):
        return None, (LOAD_ERROR_EVIDENCE_INVALID,)
    out["reason_codes"] = tuple(str(code) for code in raw_codes)

    digest = evidence.get("semantic_digest")
    if digest is None:
        digest = evidence.get("evidence_digest")
    if digest is not None:
        if not isinstance(digest, str) or not digest.strip():
            return None, (LOAD_ERROR_EVIDENCE_INVALID,)
        out["semantic_digest"] = digest.strip()

    return out, ()


def map_canonical_decision_evidence_to_binder_fields_v1(
    *,
    evidence: Mapping[str, Any],
    generated_at: str,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Map producer evidence fields → Landscape binder fields (projection only)."""
    mapped, errors = _validate_evidence_fields(evidence)
    if mapped is None:
        return None, errors
    if not isinstance(generated_at, str) or not generated_at.strip():
        return None, (LOAD_ERROR_TIMESTAMP_MISSING,)
    mapped["generated_at"] = generated_at.strip()
    if effective_at is not None:
        if not isinstance(effective_at, str) or not effective_at.strip():
            return None, (LOAD_ERROR_TIMESTAMP_MISSING,)
        mapped["effective_at"] = effective_at.strip()
    if source_reference is not None:
        if not isinstance(source_reference, str):
            return None, (LOAD_ERROR_EVIDENCE_INVALID,)
        mapped["source_reference"] = source_reference
    return mapped, ()


def try_load_canonical_decision_presentation_projection_v1(
    archive_root: str | Path,
) -> CanonicalDecisionPresentationLoadV1:
    """Verify-before-trust read of the sole durable decision presentation projection.

    Returns loaded=False with load_errors on any fail-closed condition. Never
    invents decision facts.
    """
    root = Path(archive_root).expanduser().resolve()
    path = root / STORAGE_RELATIVE_PATH
    if not path.is_file():
        return _empty(load_errors=(LOAD_ERROR_ABSENT,))

    # Ambiguity guard: a second durable producer dump beside the projection is
    # allowed only when identical decision_id; otherwise fail closed.
    sibling = root / "readmodels" / "canonical_trading_decision_evidence.v1.json"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return _empty(load_errors=(LOAD_ERROR_INVALID_JSON,))

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return _empty(load_errors=(LOAD_ERROR_INVALID_JSON,))

    if not isinstance(payload, dict):
        return _empty(load_errors=(LOAD_ERROR_INVALID_JSON,))

    schema_name = payload.get("schema_name")
    if schema_name != SCHEMA_NAME:
        return _empty(load_errors=(LOAD_ERROR_SCHEMA_MISMATCH,))

    schema_version = payload.get("schema_version")
    if schema_version is not None and int(schema_version) != SCHEMA_VERSION:
        return _empty(load_errors=(LOAD_ERROR_SCHEMA_MISMATCH,))

    authority = payload.get("authority_effect")
    decision_authority = payload.get("decision_authority_effect")
    if authority != AUTHORITY_EFFECT or decision_authority != DECISION_AUTHORITY_EFFECT:
        return _empty(load_errors=(LOAD_ERROR_AUTHORITY_CLAIM,))

    generated_at = _require_nonempty_str(payload, "generated_at")
    if generated_at is None:
        return _empty(load_errors=(LOAD_ERROR_TIMESTAMP_MISSING,))

    effective_at = payload.get("effective_at")
    if effective_at is not None and (not isinstance(effective_at, str) or not effective_at.strip()):
        return _empty(load_errors=(LOAD_ERROR_TIMESTAMP_MISSING,))
    effective_at_s = None if effective_at is None else str(effective_at).strip()

    evidence, evidence_errors = _evidence_payload_from_envelope(payload)
    if evidence is None:
        return _empty(load_errors=evidence_errors)

    source_reference = payload.get("source_reference")
    if source_reference is None:
        source_reference = f"presentation://{STORAGE_RELATIVE_PATH}"
    elif not isinstance(source_reference, str):
        return _empty(load_errors=(LOAD_ERROR_EVIDENCE_INVALID,))

    binder_fields, map_errors = map_canonical_decision_evidence_to_binder_fields_v1(
        evidence=evidence,
        generated_at=generated_at,
        effective_at=effective_at_s,
        source_reference=source_reference,
    )
    if binder_fields is None:
        return _empty(load_errors=map_errors)

    if sibling.is_file():
        try:
            sibling_payload = json.loads(sibling.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return _empty(load_errors=(LOAD_ERROR_AMBIGUOUS,))
        if not isinstance(sibling_payload, dict):
            return _empty(load_errors=(LOAD_ERROR_AMBIGUOUS,))
        sibling_decision_id = sibling_payload.get("decision_id")
        if (
            not isinstance(sibling_decision_id, str)
            or not sibling_decision_id.strip()
            or sibling_decision_id.strip() != binder_fields["decision_id"]
        ):
            return _empty(load_errors=(LOAD_ERROR_AMBIGUOUS,))

    return CanonicalDecisionPresentationLoadV1(
        loaded=True,
        load_errors=(),
        binder_fields=binder_fields,
        source_path=str(path),
        evidence_digest=(
            None
            if binder_fields.get("semantic_digest") is None
            else str(binder_fields.get("semantic_digest"))
        ),
        decision_id=str(binder_fields["decision_id"]),
    )
