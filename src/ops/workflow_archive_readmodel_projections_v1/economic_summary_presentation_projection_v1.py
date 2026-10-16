"""Non-authoritative presentation projection for Economic Summary.

CAPABILITY_ID=CAPABILITY_PRESENTATION_ECONOMIC_SUMMARY_PROJECTION_MATERIALIZER_AUTOBIND_V1

Reads already-produced EconomicViabilityEvidenceV1-compatible binder fields from a
single durable archive path and maps them field-for-field into Landscape binder
injection fields. This module:

- AUTHORITY_EFFECT=NONE
- ECONOMIC_AUTHORITY_EFFECT=NONE
- never recomputes metrics, thresholds, or viability status
- never imports src.backtest.economic_viability_evidence_v1 evaluators
- never binds promotion_economic_gate_v1
- never invents status, metrics, digests, or timestamps
- fail-closed: missing, invalid, or ambiguous sources → no fields (MISSING_SOURCE)

Deterministic source selection: exactly one well-known relative path under the
Workflow Dashboard archive root. No silent multi-candidate "latest" picking.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

SCHEMA_NAME = "economic_summary_presentation_projection.v1"
SCHEMA_VERSION = 1
STORAGE_RELATIVE_PATH = "readmodels/economic_summary_presentation_projection.v1.json"
SOURCE_FIELDS_RELATIVE_PATH = "readmodels/economic_summary.v1.json"
AUTHORITY_EFFECT = "NONE"
ECONOMIC_AUTHORITY_EFFECT = "NONE"
PROJECTION_ROLE = "NON_AUTHORITATIVE_PRESENTATION_PROJECTION"
OWNER_MODULE = "webui.workflow_dashboard_readmodel_v1.economic_summary_presentation_projection_v1"

LOAD_ERROR_ABSENT = "ECONOMIC_SUMMARY_PRESENTATION_PROJECTION_ABSENT"
LOAD_ERROR_INVALID_JSON = "ECONOMIC_SUMMARY_PRESENTATION_PROJECTION_INVALID_JSON"
LOAD_ERROR_SCHEMA_MISMATCH = "ECONOMIC_SUMMARY_PRESENTATION_PROJECTION_SCHEMA_MISMATCH"
LOAD_ERROR_AUTHORITY_CLAIM = "ECONOMIC_SUMMARY_PRESENTATION_PROJECTION_AUTHORITY_CLAIM"
LOAD_ERROR_FIELDS_INVALID = "ECONOMIC_SUMMARY_PRESENTATION_PROJECTION_FIELDS_INVALID"
LOAD_ERROR_AMBIGUOUS = "ECONOMIC_SUMMARY_PRESENTATION_PROJECTION_AMBIGUOUS_SOURCE"
LOAD_ERROR_TIMESTAMP_MISSING = "ECONOMIC_SUMMARY_PRESENTATION_PROJECTION_TIMESTAMP_MISSING"

_REQUIRED_FIELD_KEYS = (
    "status",
    "economic_validity_proven",
    "profitability_claim_allowed",
    "policy_threshold_status",
    "policy_version",
    "authority_effect",
    "runtime_effect",
    "order_effect",
    "profit_factor",
    "net_return",
    "max_drawdown",
    "sharpe",
    "trade_count",
    "funding_drag",
    "contract_version",
    "owner",
    "strategy_id",
    "strategy_version",
    "config_digest",
    "implementation_digest",
    "data_digest",
    "manifest_digest",
    "wiring_chain_digest",
    "policy_digest",
)

_REQUIRED_BOOL_KEYS = (
    "economic_validity_proven",
    "profitability_claim_allowed",
    "runtime_effect",
    "order_effect",
)

_REQUIRED_STR_KEYS = (
    "status",
    "policy_threshold_status",
    "policy_version",
    "authority_effect",
    "contract_version",
    "owner",
    "strategy_id",
    "strategy_version",
    "config_digest",
    "implementation_digest",
    "data_digest",
    "manifest_digest",
    "wiring_chain_digest",
    "policy_digest",
)

_METRIC_KEYS = (
    "profit_factor",
    "net_return",
    "max_drawdown",
    "sharpe",
    "trade_count",
    "funding_drag",
)


@dataclass(frozen=True)
class EconomicSummaryPresentationLoadV1:
    """Result of a fail-closed presentation projection load attempt."""

    loaded: bool
    load_errors: tuple[str, ...]
    binder_fields: Mapping[str, Any] | None = None
    source_path: str | None = None
    evidence_digest: str | None = None
    status: str | None = None


def _empty(*, load_errors: tuple[str, ...]) -> EconomicSummaryPresentationLoadV1:
    return EconomicSummaryPresentationLoadV1(loaded=False, load_errors=load_errors)


def _require_nonempty_str(payload: Mapping[str, Any], key: str) -> str | None:
    raw = payload.get(key)
    if isinstance(raw, Enum):
        raw = raw.value
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip()


def _normalize_reason_codes(raw_codes: object) -> tuple[str, ...] | None:
    if raw_codes is None:
        raw_codes = ()
    if not isinstance(raw_codes, (list, tuple)):
        return None
    return tuple(str(code) for code in raw_codes)


def _normalize_metric(raw: object) -> dict[str, Any] | None:
    """Accept MetricFieldV1-shaped mappings only; never invent metrics."""
    if raw is None:
        return None
    if hasattr(raw, "to_dict") and callable(raw.to_dict):
        raw = raw.to_dict()
    if not isinstance(raw, Mapping):
        return None
    semantic = raw.get("semantic")
    if isinstance(semantic, Enum):
        semantic = semantic.value
    if not isinstance(semantic, str) or not semantic.strip():
        return None
    out: dict[str, Any] = {"semantic": semantic.strip()}
    if "value" in raw and raw.get("value") is not None:
        try:
            value = float(raw["value"])
        except (TypeError, ValueError):
            return None
        if not math.isfinite(value):
            return None
        out["value"] = value
    if "reason_code" in raw and raw.get("reason_code") is not None:
        reason = raw.get("reason_code")
        if not isinstance(reason, str) or not reason.strip():
            return None
        out["reason_code"] = reason.strip()
    return out


def _fields_payload_from_envelope(
    payload: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, tuple[str, ...]]:
    """Extract nested economic_summary fields; fail closed on ambiguity."""
    if "economic_summary" not in payload:
        return None, (LOAD_ERROR_FIELDS_INVALID,)
    fields = payload.get("economic_summary")
    if not isinstance(fields, Mapping):
        return None, (LOAD_ERROR_FIELDS_INVALID,)
    top_level_status = payload.get("status")
    nested_status = fields.get("status")
    if (
        isinstance(top_level_status, str)
        and top_level_status.strip()
        and isinstance(nested_status, str)
        and nested_status.strip()
        and top_level_status.strip() != nested_status.strip()
    ):
        return None, (LOAD_ERROR_AMBIGUOUS,)
    return fields, ()


def _validate_economic_fields(
    fields: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    missing = [key for key in _REQUIRED_FIELD_KEYS if key not in fields]
    if missing:
        return None, (LOAD_ERROR_FIELDS_INVALID,)

    out: dict[str, Any] = {}
    for key in _REQUIRED_STR_KEYS:
        value = _require_nonempty_str(fields, key)
        if value is None:
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out[key] = value

    for key in _REQUIRED_BOOL_KEYS:
        raw = fields.get(key)
        if not isinstance(raw, bool):
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out[key] = raw

    for key in _METRIC_KEYS:
        metric = _normalize_metric(fields.get(key))
        if metric is None:
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out[key] = metric

    reason_codes = _normalize_reason_codes(fields.get("reason_codes", ()))
    if reason_codes is None:
        return None, (LOAD_ERROR_FIELDS_INVALID,)
    out["reason_codes"] = reason_codes

    digest = fields.get("evidence_digest")
    if digest is None:
        digest = fields.get("manifest_digest")
    if digest is not None:
        if not isinstance(digest, str) or not digest.strip():
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out["evidence_digest"] = digest.strip()

    evidence_ref = fields.get("evidence_ref")
    if evidence_ref is not None:
        if not isinstance(evidence_ref, str):
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out["evidence_ref"] = evidence_ref

    source_reference = fields.get("source_reference")
    if source_reference is not None:
        if not isinstance(source_reference, str):
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out["source_reference"] = source_reference

    producer_module = fields.get("producer_module")
    if producer_module is not None:
        if not isinstance(producer_module, str) or not producer_module.strip():
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out["producer_module"] = producer_module.strip()

    source_kind = fields.get("source_kind")
    if source_kind is not None:
        if not isinstance(source_kind, str) or not source_kind.strip():
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out["source_kind"] = source_kind.strip()

    schema_version = fields.get("schema_version")
    if schema_version is not None:
        if not isinstance(schema_version, str) or not schema_version.strip():
            return None, (LOAD_ERROR_FIELDS_INVALID,)
        out["schema_version"] = schema_version.strip()

    return out, ()


def map_economic_summary_fields_to_binder_fields_v1(
    *,
    economic_summary: Mapping[str, Any],
    generated_at: str,
    effective_at: str | None = None,
    source_reference: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Map Economic fields → Landscape binder fields (projection only)."""
    mapped, errors = _validate_economic_fields(economic_summary)
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


def try_load_economic_summary_presentation_projection_v1(
    archive_root: str | Path,
) -> EconomicSummaryPresentationLoadV1:
    """Verify-before-trust read of the sole durable Economic presentation projection.

    Returns loaded=False with load_errors on any fail-closed condition. Never
    invents EconomicViabilityEvidence facts or discovers latest evidence packs.
    """
    root = Path(archive_root).expanduser().resolve()
    path = root / STORAGE_RELATIVE_PATH
    if not path.is_file():
        return _empty(load_errors=(LOAD_ERROR_ABSENT,))

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
    economic_authority = payload.get("economic_authority_effect")
    if authority != AUTHORITY_EFFECT or economic_authority != ECONOMIC_AUTHORITY_EFFECT:
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

    binder_fields, map_errors = map_economic_summary_fields_to_binder_fields_v1(
        economic_summary=fields,
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
        if "economic_summary" in sibling_payload and isinstance(
            sibling_payload.get("economic_summary"), Mapping
        ):
            sibling_fields = sibling_payload["economic_summary"]
        sibling_status = str(sibling_fields.get("status") or "").strip()
        projection_status = str(binder_fields["status"])
        if not sibling_status or sibling_status != projection_status:
            return _empty(load_errors=(LOAD_ERROR_AMBIGUOUS,))
        sibling_digest = sibling_fields.get("evidence_digest")
        if sibling_digest is None:
            sibling_digest = sibling_fields.get("manifest_digest")
        projection_digest = binder_fields.get("evidence_digest")
        if (
            isinstance(sibling_digest, str)
            and sibling_digest.strip()
            and isinstance(projection_digest, str)
            and projection_digest.strip()
            and sibling_digest.strip() != projection_digest.strip()
        ):
            return _empty(load_errors=(LOAD_ERROR_AMBIGUOUS,))

    return EconomicSummaryPresentationLoadV1(
        loaded=True,
        load_errors=(),
        binder_fields=binder_fields,
        source_path=str(path),
        evidence_digest=(
            None
            if binder_fields.get("evidence_digest") is None
            else str(binder_fields.get("evidence_digest"))
        ),
        status=str(binder_fields["status"]),
    )
