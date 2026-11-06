"""Non-authoritative presentation projection for Execution/Reconciliation.

CAPABILITY_ID=CAPABILITY_PRESENTATION_EXECUTION_RECONCILIATION_PROJECTION_MATERIALIZER_AUTOBIND_V1

Reads already-produced Execution/Reconciliation binder-compatible fields from a
single durable archive path and maps them field-for-field into Landscape binder
injection fields. This module:

- AUTHORITY_EFFECT=NONE
- EXECUTION_AUTHORITY_EFFECT=NONE
- never creates, mutates, or evaluates order intents / reconciliation
- never imports src.governance.canonical_order_intent_v1 builders
- never imports trading.master_v2 order-intent offline adapters
- never invents execution_status, reconciliation_status, or order_intent_ref
- fail-closed: missing, invalid, or ambiguous sources → no fields (MISSING_SOURCE)

Deterministic source selection: exactly one well-known relative path under the
Workflow Dashboard archive root. No silent multi-candidate "latest" picking.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SCHEMA_NAME = "execution_reconciliation_presentation_projection.v1"
SCHEMA_VERSION = 1
STORAGE_RELATIVE_PATH = "readmodels/execution_reconciliation_presentation_projection.v1.json"
SOURCE_FIELDS_RELATIVE_PATH = "readmodels/execution_reconciliation.v1.json"
AUTHORITY_EFFECT = "NONE"
EXECUTION_AUTHORITY_EFFECT = "NONE"
PROJECTION_ROLE = "NON_AUTHORITATIVE_PRESENTATION_PROJECTION"
OWNER_MODULE = (
    "webui.workflow_dashboard_readmodel_v1.execution_reconciliation_presentation_projection_v1"
)

LOAD_ERROR_ABSENT = "EXECUTION_RECONCILIATION_PRESENTATION_PROJECTION_ABSENT"
LOAD_ERROR_INVALID_JSON = "EXECUTION_RECONCILIATION_PRESENTATION_PROJECTION_INVALID_JSON"
LOAD_ERROR_SCHEMA_MISMATCH = "EXECUTION_RECONCILIATION_PRESENTATION_PROJECTION_SCHEMA_MISMATCH"
LOAD_ERROR_AUTHORITY_CLAIM = "EXECUTION_RECONCILIATION_PRESENTATION_PROJECTION_AUTHORITY_CLAIM"
LOAD_ERROR_FIELDS_INVALID = "EXECUTION_RECONCILIATION_PRESENTATION_PROJECTION_FIELDS_INVALID"
LOAD_ERROR_AMBIGUOUS = "EXECUTION_RECONCILIATION_PRESENTATION_PROJECTION_AMBIGUOUS_SOURCE"
LOAD_ERROR_TIMESTAMP_MISSING = "EXECUTION_RECONCILIATION_PRESENTATION_PROJECTION_TIMESTAMP_MISSING"

_REQUIRED_FIELD_KEYS = ("execution_status",)


@dataclass(frozen=True)
class ExecutionReconciliationPresentationLoadV1:
    """Result of a fail-closed presentation projection load attempt."""

    loaded: bool
    load_errors: tuple[str, ...]
    binder_fields: Mapping[str, Any] | None = None
    source_path: str | None = None
    evidence_digest: str | None = None
    execution_status: str | None = None


def _empty(*, load_errors: tuple[str, ...]) -> ExecutionReconciliationPresentationLoadV1:
    return ExecutionReconciliationPresentationLoadV1(loaded=False, load_errors=load_errors)


def _require_nonempty_str(payload: Mapping[str, Any], key: str) -> str | None:
    raw = payload.get(key)
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip()


def _fields_payload_from_envelope(
    payload: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, tuple[str, ...]]:
    """Extract nested execution_reconciliation fields; fail closed on ambiguity."""
    if "execution_reconciliation" not in payload:
        return None, (LOAD_ERROR_FIELDS_INVALID,)
    fields = payload.get("execution_reconciliation")
    if not isinstance(fields, Mapping):
        return None, (LOAD_ERROR_FIELDS_INVALID,)
    # Reject dual top-level + nested execution_status with conflicting values.
    top_level_status = payload.get("execution_status")
    nested_status = fields.get("execution_status")
    if (
        isinstance(top_level_status, str)
        and top_level_status.strip()
        and isinstance(nested_status, str)
        and nested_status.strip()
        and top_level_status.strip() != nested_status.strip()
    ):
        return None, (LOAD_ERROR_AMBIGUOUS,)
    return fields, ()


def _validate_execution_fields(
    fields: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    missing = [key for key in _REQUIRED_FIELD_KEYS if key not in fields]
    if missing:
        return None, (LOAD_ERROR_FIELDS_INVALID,)

    execution_status = _require_nonempty_str(fields, "execution_status")
    if execution_status is None:
        return None, (LOAD_ERROR_FIELDS_INVALID,)

    out: dict[str, Any] = {"execution_status": execution_status}

    if "reconciliation_status" in fields and fields.get("reconciliation_status") is not None:
        recon = fields.get("reconciliation_status")
        if not isinstance(recon, str) or not recon.strip():
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out["reconciliation_status"] = recon.strip()

    if "order_intent_ref" in fields and fields.get("order_intent_ref") is not None:
        intent_ref = fields.get("order_intent_ref")
        if not isinstance(intent_ref, str) or not intent_ref.strip():
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out["order_intent_ref"] = intent_ref.strip()

    raw_codes = fields.get("reason_codes", ())
    if raw_codes is None:
        raw_codes = ()
    if not isinstance(raw_codes, (list, tuple)):
        return None, (LOAD_ERROR_FIELDS_INVALID,)
    out["reason_codes"] = tuple(str(code) for code in raw_codes)

    digest = fields.get("evidence_digest")
    if digest is None:
        digest = fields.get("semantic_digest")
    if digest is not None:
        if not isinstance(digest, str) or not digest.strip():
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out["evidence_digest"] = digest.strip()
        out["semantic_digest"] = digest.strip()

    schema_version = fields.get("schema_version")
    if schema_version is not None:
        if not isinstance(schema_version, str) or not schema_version.strip():
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out["schema_version"] = schema_version.strip()

    return out, ()


def map_execution_reconciliation_fields_to_binder_fields_v1(
    *,
    execution_reconciliation: Mapping[str, Any],
    generated_at: str,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Map Execution/Reconciliation fields → Landscape binder fields (projection only)."""
    mapped, errors = _validate_execution_fields(execution_reconciliation)
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
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        mapped["source_reference"] = source_reference
    return mapped, ()


def try_load_execution_reconciliation_presentation_projection_v1(
    archive_root: str | Path,
) -> ExecutionReconciliationPresentationLoadV1:
    """Verify-before-trust read of the sole durable Execution presentation projection.

    Returns loaded=False with load_errors on any fail-closed condition. Never
    invents Execution/Reconciliation facts.
    """
    root = Path(archive_root).expanduser().resolve()
    path = root / STORAGE_RELATIVE_PATH
    if not path.is_file():
        return _empty(load_errors=(LOAD_ERROR_ABSENT,))

    # Ambiguity guard: a second durable producer dump beside the projection is
    # allowed only when identical execution_status (and optional fields/digest
    # when both present); otherwise fail closed.
    sibling = root / SOURCE_FIELDS_RELATIVE_PATH
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
    execution_authority = payload.get("execution_authority_effect")
    if authority != AUTHORITY_EFFECT or execution_authority != EXECUTION_AUTHORITY_EFFECT:
        return _empty(load_errors=(LOAD_ERROR_AUTHORITY_CLAIM,))

    generated_at = _require_nonempty_str(payload, "generated_at")
    if generated_at is None:
        return _empty(load_errors=(LOAD_ERROR_TIMESTAMP_MISSING,))

    effective_at = payload.get("effective_at")
    if effective_at is not None and (not isinstance(effective_at, str) or not effective_at.strip()):
        return _empty(load_errors=(LOAD_ERROR_TIMESTAMP_MISSING,))
    effective_at_s = None if effective_at is None else str(effective_at).strip()

    fields, field_errors = _fields_payload_from_envelope(payload)
    if fields is None:
        return _empty(load_errors=field_errors)

    source_reference = payload.get("source_reference")
    if source_reference is None:
        source_reference = f"presentation://{STORAGE_RELATIVE_PATH}"
    elif not isinstance(source_reference, str):
        return _empty(load_errors=(LOAD_ERROR_FIELDS_INVALID,))

    binder_fields, map_errors = map_execution_reconciliation_fields_to_binder_fields_v1(
        execution_reconciliation=fields,
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
        sibling_fields: Mapping[str, Any] = sibling_payload
        if "execution_reconciliation" in sibling_payload and isinstance(
            sibling_payload.get("execution_reconciliation"), Mapping
        ):
            sibling_fields = sibling_payload["execution_reconciliation"]
        sibling_status = str(sibling_fields.get("execution_status") or "").strip()
        projection_status = str(binder_fields["execution_status"])
        if not sibling_status or sibling_status != projection_status:
            return _empty(load_errors=(LOAD_ERROR_AMBIGUOUS,))
        for optional_key in ("reconciliation_status", "order_intent_ref"):
            sibling_opt = sibling_fields.get(optional_key)
            projection_opt = binder_fields.get(optional_key)
            if (
                isinstance(sibling_opt, str)
                and sibling_opt.strip()
                and isinstance(projection_opt, str)
                and projection_opt.strip()
                and sibling_opt.strip() != projection_opt.strip()
            ):
                return _empty(load_errors=(LOAD_ERROR_AMBIGUOUS,))
        sibling_digest = sibling_fields.get("evidence_digest")
        if sibling_digest is None:
            sibling_digest = sibling_fields.get("semantic_digest")
        projection_digest = binder_fields.get("evidence_digest")
        if (
            isinstance(sibling_digest, str)
            and sibling_digest.strip()
            and isinstance(projection_digest, str)
            and projection_digest.strip()
            and sibling_digest.strip() != projection_digest.strip()
        ):
            return _empty(load_errors=(LOAD_ERROR_AMBIGUOUS,))

    return ExecutionReconciliationPresentationLoadV1(
        loaded=True,
        load_errors=(),
        binder_fields=binder_fields,
        source_path=str(path),
        evidence_digest=(
            None
            if binder_fields.get("evidence_digest") is None
            else str(binder_fields.get("evidence_digest"))
        ),
        execution_status=str(binder_fields["execution_status"]),
    )
