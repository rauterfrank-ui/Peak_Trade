"""Frozen venue-pretrade conjunction for the offline Core→Live path.

Core intent is not submit permission. Existing canary consumers remain the
pretrade owner; this module evaluates frozen evidence without GET/POST.
"""

from __future__ import annotations

from decimal import Decimal

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import (
    FrozenPretradeEvidenceV1,
    PretradeConjunctionResultV1,
    VenuePlanCandidateV1,
)


def evaluate_frozen_pretrade_conjunction_v1(
    *,
    plan: VenuePlanCandidateV1,
    frozen: FrozenPretradeEvidenceV1,
    owner_go: str | None,
) -> PretradeConjunctionResultV1:
    reasons: list[str] = []
    core_intent_valid = plan.quantity_source == "STEP_29Q_CANONICAL_ORDER_INTENT"
    instrument_binding_valid = plan.instrument_source == "CAP_2_4_BOUND_INSTRUMENT"
    if not core_intent_valid:
        reasons.append("CORE_INTENT_INVALID")
    if not instrument_binding_valid:
        reasons.append("INSTRUMENT_BINDING_INVALID")
    if frozen.source_kind != "FROZEN_OFFLINE_PRETRADE_EVIDENCE":
        reasons.append("PRETRADE_SOURCE_NOT_FROZEN_OFFLINE")
    freshness = str(getattr(frozen, "freshness_status", "") or "")
    if frozen.source_kind == "FROZEN_OFFLINE_PRETRADE_EVIDENCE" and freshness == "LIVE_FRESH":
        reasons.append("FROZEN_PRETRADE_CANNOT_CLAIM_LIVE_FRESH")
    planned = Decimal(str(plan.quantity))
    if frozen.max_available <= 0:
        reasons.append("MAX_AVAILABLE_ZERO")
    if frozen.max_size <= 0:
        reasons.append("MAX_SIZE_ZERO")
    if planned > frozen.max_available:
        reasons.append("UNAVAILABLE_MARGIN")
    if planned > frozen.max_size:
        reasons.append("MAX_SIZE_ZERO")
    if not frozen.price_band_ok:
        reasons.append("PRICE_BAND_FAIL")
    if not frozen.available_margin_ok:
        reasons.append("UNAVAILABLE_MARGIN")
    if not frozen.instrument_state_ok:
        reasons.append("INSTRUMENT_STATE_FAIL")
    if not frozen.account_mode_ok:
        reasons.append("ACCOUNT_MODE_FAIL")
    if not frozen.pos_mode_ok:
        reasons.append("POS_MODE_FAIL")
    if not frozen.margin_mode_ok:
        reasons.append("MARGIN_MODE_FAIL")
    if not frozen.leverage_ok:
        reasons.append("LEVERAGE_FAIL")
    pretrade_valid = not any(
        code
        in {
            "MAX_AVAILABLE_ZERO",
            "MAX_SIZE_ZERO",
            "UNAVAILABLE_MARGIN",
            "PRICE_BAND_FAIL",
            "INSTRUMENT_STATE_FAIL",
            "ACCOUNT_MODE_FAIL",
            "POS_MODE_FAIL",
            "MARGIN_MODE_FAIL",
            "LEVERAGE_FAIL",
            "PRETRADE_SOURCE_NOT_FROZEN_OFFLINE",
            "FROZEN_PRETRADE_CANNOT_CLAIM_LIVE_FRESH",
        }
        for code in reasons
    )
    owner_go_valid = bool(str(owner_go or "").strip())
    if not owner_go_valid:
        reasons.append("MISSING_OWNER_GO")
    return PretradeConjunctionResultV1(
        ok=pretrade_valid and core_intent_valid and instrument_binding_valid,
        reason_codes=tuple(reasons) if reasons else ("PRETRADE_CONJUNCTION_EVALUATED",),
        core_intent_valid=core_intent_valid,
        instrument_binding_valid=instrument_binding_valid,
        pretrade_valid=pretrade_valid,
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        owner_go_valid=owner_go_valid,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
    )
