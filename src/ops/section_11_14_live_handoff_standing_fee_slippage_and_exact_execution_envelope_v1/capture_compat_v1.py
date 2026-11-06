"""Capture/restart compatibility for envelope provenance fields. No fill. No restart."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.constants_v1 import (
    CAPTURE_OPTIONAL_ENVELOPE_FIELDS,
    ENVELOPE_VERSION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    OPTIONAL_ENVELOPE_PROVENANCE_FIELDS,
    OPTIONAL_TEMPORAL_FIELDS,
    REQUIRED_HANDOFF_FIELDS,
)


def envelope_capture_optional_fields_v1() -> tuple[str, ...]:
    return CAPTURE_OPTIONAL_ENVELOPE_FIELDS


def project_envelope_onto_capture_record_v1(
    *,
    envelope: Mapping[str, Any],
    required_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach envelope provenance as optional capture fields.

    Does not rewrite required restart-identity fields. Does not claim a
    contemporaneous productive capture. Does not restart.
    """
    optional = {
        "execution_envelope_id": str(envelope.get("ENVELOPE_VERSION") or ENVELOPE_VERSION),
        "execution_envelope_version": str(envelope.get("ENVELOPE_VERSION") or ENVELOPE_VERSION),
        "fee_provenance": str(
            (envelope.get("FEE_POLICY") or {}).get("SOURCE_ENDPOINT") or "UNKNOWN"
        ),
        "slippage_provenance": str(
            (envelope.get("SLIPPAGE_POLICY") or {}).get("POLICY_ID") or "UNKNOWN"
        ),
        "expected_fee": str(envelope.get("EXPECTED_FEE_AMOUNT") or "UNKNOWN"),
        "expected_fee_ccy": str(envelope.get("EXPECTED_FEE_CCY") or "UNKNOWN"),
        "planned_fill_price": str(envelope.get("LIMIT_PRICE") or "UNKNOWN"),
        "worst_case_fill_price": str(envelope.get("WORST_FILL_PRICE") or "UNKNOWN"),
        "order_qty": str(envelope.get("ORDER_QTY") or "UNKNOWN"),
        "order_qty_unit": str(envelope.get("ORDER_QTY_UNIT") or "UNKNOWN"),
        "instrument_id": str(envelope.get("INSTRUMENT_ID") or "UNKNOWN"),
    }
    identity = dict(required_identity or {})
    for field in REQUIRED_HANDOFF_FIELDS:
        if field in optional:
            raise RuntimeError(f"OPTIONAL_ENVELOPE_FIELD_COLLIDES_WITH_REQUIRED:{field}")
    return {
        "REQUIRED_HANDOFF_FIELDS_UNCHANGED": list(REQUIRED_HANDOFF_FIELDS),
        "OPTIONAL_TEMPORAL_FIELDS_UNCHANGED": list(OPTIONAL_TEMPORAL_FIELDS),
        "OPTIONAL_ENVELOPE_PROVENANCE_FIELDS": list(OPTIONAL_ENVELOPE_PROVENANCE_FIELDS),
        "OPTIONAL_ENVELOPE_FIELDS": optional,
        "IDENTITY": identity,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CAPTURE_PATH_COMPATIBLE": True,
        "RESTART_CONSUMER_COMPATIBLE": True,
        "REQUIRED_IDENTITY_NOT_REWRITTEN_BY_ENVELOPE": True,
    }
