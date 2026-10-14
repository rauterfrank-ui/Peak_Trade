"""Authorized provenance for productive RISK_REDUCING venue POST envelopes.

Caller-supplied reduce_only alone is insufficient. Reuses CURRENT exact-object
flatten identity contract (no new authorization source).

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.current_productive_exact_object_flatten_plan_v1 import (
    INSTRUMENT_SOURCE as EXACT_OBJECT_FLATTEN_INSTRUMENT_SOURCE,
    PATH_KIND_EXACT_OBJECT_FLATTEN,
    QUANTITY_SOURCE as EXACT_OBJECT_FLATTEN_QUANTITY_SOURCE,
    SIDE_SOURCE as EXACT_OBJECT_FLATTEN_SIDE_SOURCE,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)

CONTRACT_ID = "CURRENT_PRODUCTIVE_RISK_REDUCING_ENVELOPE_PROVENANCE_V1"
EXACT_OBJECT_FLATTEN_ADMISSION_REF = "OWNER_GRANTED_EXACT_OBJECT_DISPOSITION"
EXACT_OBJECT_FLATTEN_PROVENANCE_REF = "FRESH_AUTHENTICATED_READ_ONLY_GET"
FORBIDDEN_MANUAL_PROVENANCE_MARKERS = frozenset(
    {
        "TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        "TEST_ADMISSION_REF",
        "TEST_PROVENANCE_REF",
        "FULL_CORE_TRANSFORMED_VENUE_PLAN_FIXTURE",
    }
)


class RiskReducingEnvelopeProvenanceError(RuntimeError):
    """Fail-closed: reduce_only without authorized CURRENT provenance."""


def _matches_exact_object_flatten_provenance_v1(envelope: FinalOrderEnvelopeV1) -> bool:
    return (
        envelope.path_kind == PATH_KIND_EXACT_OBJECT_FLATTEN
        and envelope.provenance_ref == EXACT_OBJECT_FLATTEN_PROVENANCE_REF
        and envelope.admission_ref == EXACT_OBJECT_FLATTEN_ADMISSION_REF
        and envelope.instrument_source == EXACT_OBJECT_FLATTEN_INSTRUMENT_SOURCE
        and envelope.quantity_source == EXACT_OBJECT_FLATTEN_QUANTITY_SOURCE
        and envelope.side_source == EXACT_OBJECT_FLATTEN_SIDE_SOURCE
        and envelope.reduce_only is True
    )


def verify_authorized_risk_reducing_envelope_provenance_v1(
    envelope: FinalOrderEnvelopeV1,
) -> None:
    """Require CURRENT-authorized reduce-only provenance or fail closed (no POST)."""
    assert_envelope_unmodified_v1(envelope)
    if envelope.reduce_only is not True:
        raise RiskReducingEnvelopeProvenanceError("RISK_REDUCING_REQUIRES_REDUCE_ONLY_TRUE")
    for field_name, value in (
        ("provenance_ref", envelope.provenance_ref),
        ("admission_ref", envelope.admission_ref),
        ("instrument_source", envelope.instrument_source),
        ("quantity_source", envelope.quantity_source),
        ("side_source", envelope.side_source),
        ("path_kind", envelope.path_kind),
    ):
        text = str(value or "").strip()
        if not text:
            raise RiskReducingEnvelopeProvenanceError(
                f"RISK_REDUCING_PROVENANCE_IDENTITY_MISSING:{field_name}"
            )
        if text in FORBIDDEN_MANUAL_PROVENANCE_MARKERS:
            raise RiskReducingEnvelopeProvenanceError(
                f"RISK_REDUCING_MANUAL_PROVENANCE_FORBIDDEN:{field_name}"
            )
    if "TEST_" in envelope.provenance_ref or "FIXTURE" in envelope.provenance_ref.upper():
        raise RiskReducingEnvelopeProvenanceError("RISK_REDUCING_TEST_FIXTURE_PROVENANCE_FORBIDDEN")
    if _matches_exact_object_flatten_provenance_v1(envelope):
        return
    raise RiskReducingEnvelopeProvenanceError("RISK_REDUCING_PROVENANCE_NOT_AUTHORIZED")


def is_authorized_risk_reducing_envelope_v1(envelope: FinalOrderEnvelopeV1) -> bool:
    try:
        verify_authorized_risk_reducing_envelope_provenance_v1(envelope)
    except RiskReducingEnvelopeProvenanceError:
        return False
    return True


__all__ = [
    "CONTRACT_ID",
    "EXACT_OBJECT_FLATTEN_ADMISSION_REF",
    "EXACT_OBJECT_FLATTEN_PROVENANCE_REF",
    "RiskReducingEnvelopeProvenanceError",
    "is_authorized_risk_reducing_envelope_v1",
    "verify_authorized_risk_reducing_envelope_provenance_v1",
]
