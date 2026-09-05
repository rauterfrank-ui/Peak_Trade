"""Translator-only venue mapping from CoreLiveExecutionIntentV1.

Does not own instrument, side, or quantity. Does not call canary DEFAULT_*.
"""

from __future__ import annotations

from src.governance.canonical_order_intent_v1 import IntentAction, IntentSide
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
    PATH_KIND,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import (
    CompositionStatusV1,
    CoreLiveExecutionIntentV1,
    VenuePlanCandidateV1,
)
from src.ops.okx_europe_adapter_lifecycle_contract_v0 import build_client_order_id
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    OkxResponseMapperError,
    build_venue_native_order_body_v1,
)

_ORDER_TYPE_MAP = {
    "MARKET_ONLY": "market",
    "LIMIT_ONLY": "limit",
}


class FullCoreVenueTranslationError(RuntimeError):
    """Fail-closed venue translation violation."""


def venue_side_from_core_intent_v1(intent: CoreLiveExecutionIntentV1) -> str:
    action = str(intent.intent_action)
    if action == IntentAction.ENTER_LONG.value:
        return "buy"
    if action == IntentAction.ENTER_SHORT.value:
        return "sell"
    if action in {IntentAction.REDUCE.value, IntentAction.EXIT.value}:
        if str(intent.side) == IntentSide.LONG.value:
            return "sell"
        if str(intent.side) == IntentSide.SHORT.value:
            return "buy"
    raise FullCoreVenueTranslationError(f"UNSUPPORTED_INTENT_ACTION:{action}")


def translate_core_live_intent_to_venue_plan_v1(
    intent: CoreLiveExecutionIntentV1,
    *,
    session_id: str,
    run_id: str,
    td_mode: str = "cross",
    injected_instrument_id: str | None = None,
    injected_side: str | None = None,
    injected_quantity: str | None = None,
) -> tuple[CompositionStatusV1, tuple[str, ...], VenuePlanCandidateV1 | None]:
    if injected_instrument_id is not None:
        return CompositionStatusV1.DENY, ("HARDCODED_INSTRUMENT_INJECTION_FORBIDDEN",), None
    if injected_side is not None:
        return CompositionStatusV1.DENY, ("HARDCODED_SIDE_INJECTION_FORBIDDEN",), None
    if injected_quantity is not None:
        return CompositionStatusV1.DENY, ("HARDCODED_QTY_INJECTION_FORBIDDEN",), None
    try:
        venue_side = venue_side_from_core_intent_v1(intent)
    except FullCoreVenueTranslationError as exc:
        return CompositionStatusV1.DENY, (str(exc),), None
    instrument = str(intent.venue_native_id or intent.instrument_id)
    if not instrument:
        return CompositionStatusV1.DENY, ("MISSING_INSTRUMENT",), None
    if (
        instrument == CANARY_DEFAULT_INSTRUMENT_ID
        and intent.instrument_id != CANARY_DEFAULT_INSTRUMENT_ID
    ):
        return CompositionStatusV1.DENY, ("HARDCODED_INSTRUMENT_INJECTION_FORBIDDEN",), None
    qty = str(intent.quantity)
    order_type = _ORDER_TYPE_MAP.get(str(intent.order_type_policy), "")
    if not order_type:
        return CompositionStatusV1.DENY, ("UNSUPPORTED_ORDER_TYPE_POLICY",), None
    clordid = build_client_order_id(
        run_id=run_id,
        session_id=session_id,
        intent_id=intent.source_intent_id,
        environment="simulation",
        instrument_id=instrument,
    )
    try:
        body = build_venue_native_order_body_v1(
            client_order_id=clordid,
            instrument=instrument,
            order_type=order_type,
            side=venue_side,
            quantity=qty,
            td_mode=td_mode,
            reduce_only=bool(intent.reduce_only),
        )
    except OkxResponseMapperError as exc:
        return CompositionStatusV1.DENY, (f"VENUE_TRANSLATION_MISMATCH:{exc}",), None
    if str(body.get("instId") or "") != instrument:
        return CompositionStatusV1.DENY, ("VENUE_TRANSLATION_MISMATCH",), None
    if str(body.get("side") or "") != venue_side:
        return CompositionStatusV1.DENY, ("VENUE_TRANSLATION_MISMATCH",), None
    if str(body.get("sz") or "") != qty:
        return CompositionStatusV1.DENY, ("VENUE_TRANSLATION_MISMATCH",), None
    plan = VenuePlanCandidateV1(
        instrument_id=instrument,
        side=venue_side,
        quantity=qty,
        order_type=order_type,
        td_mode=td_mode,
        reduce_only=bool(intent.reduce_only),
        clordid=clordid,
        venue_native_payload=dict(body),
        quantity_source="STEP_29Q_CANONICAL_ORDER_INTENT",
        side_source="STEP_29Q_CANONICAL_ORDER_INTENT",
        instrument_source="CAP_2_4_BOUND_INSTRUMENT",
        path_kind=PATH_KIND,
    )
    return CompositionStatusV1.PASS, ("PASS",), plan
