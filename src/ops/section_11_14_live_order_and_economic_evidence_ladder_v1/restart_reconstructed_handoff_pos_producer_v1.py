"""Productive S05 §11.14 Live handoff pos producer.

Emits Peak_Trade-owned contemporaneous resulting/current position quantity
at the required handoff-commit window. Does not copy fillSz, venue GET,
submitted sz, accounting, A1 WAL, FILEGATE, or evidence-pack values.
Does not GET. Does not POST. Does not bind a restart reader.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    CONTEMPORANEOUS_PROVENANCE_CLASS,
    FORBIDDEN_PROVENANCE_CLASSES,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    FORBIDDEN_DERIVATIONS,
    POS_SIGN_SEMANTICS,
    POS_UNIT,
    PRODUCER_ID,
    SELECTED_SEMANTIC_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_validators_v1 import (
    parse_handoff_pos_v1,
)

ADMISSIBLE_POS_SOURCE_KIND = "CONTEMPORANEOUS_PEAK_TRADE_OWNED_RESULTING_CURRENT_POSITION_QTY"
REQUIRED_CAPTURE_TRIGGER = "REQUIRED_WINDOW_HANDOFF_COMMIT_AFTER_BOUND_FILL_BEFORE_RESTART"
NEW_PRODUCER_IMPLEMENTED = True
PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED = True
FORBIDDEN_INPUT_KEYS: frozenset[str] = frozenset(
    {
        "fillSz",
        "fill_sz",
        "submitted_sz",
        "sz",
        "ackSz",
        "venue_pos",
        "GET_pos",
        "accounting_pos",
    }
)


def _parse_unsigned_qty(raw: object) -> Decimal:
    text = str(raw or "").strip()
    if text == "":
        raise Section1114OfflineSurfaceError("QTY_UNAVAILABLE")
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise Section1114OfflineSurfaceError("QTY_MALFORMED") from exc
    if not value.is_finite():
        raise Section1114OfflineSurfaceError("QTY_MALFORMED")
    if value < 0:
        raise Section1114OfflineSurfaceError("UNSIGNED_MAGNITUDE_VIOLATION")
    return value


def _bound_identity_fields(
    *,
    bound_fill_identity: Mapping[str, Any] | None,
) -> tuple[str, str, str, str, str, bool]:
    if bound_fill_identity is None:
        return (
            BOUND_INSTID,
            BOUND_CLORDID,
            BOUND_ORDID,
            BOUND_POS_SIDE,
            BOUND_FILL_SZ,
            False,
        )
    inst_id = str(bound_fill_identity.get("instId") or "").strip()
    clordid = str(bound_fill_identity.get("clOrdId") or "").strip()
    ord_id = str(bound_fill_identity.get("ordId") or "").strip()
    pos_side = str(bound_fill_identity.get("posSide") or "").strip()
    fill_sz = str(bound_fill_identity.get("fillSz") or "").strip()
    if not inst_id or not clordid or not ord_id or not pos_side or not fill_sz:
        raise Section1114OfflineSurfaceError("FUTURE_BOUND_IDENTITY_INCOMPLETE")
    return inst_id, clordid, ord_id, pos_side, fill_sz, True


def emit_s05_handoff_pos_v1(
    *,
    resulting_current_position_qty: object,
    unit: object,
    source_kind: object,
    inst_id: object,
    clordid: object,
    ord_id: object,
    pos_side: object,
    bound_fill_identity_exists: bool,
    capture_trigger: object,
    provenance_class: object,
    restart_already_occurred: bool = False,
    extra_fields: Mapping[str, Any] | None = None,
    bound_fill_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    extras = dict(extra_fields or {})
    forbidden_keys = sorted(name for name in extras if name in FORBIDDEN_INPUT_KEYS)
    if forbidden_keys:
        raise Section1114OfflineSurfaceError("FORBIDDEN_DERIVATION_FIELD")
    kind = str(source_kind or "").strip()
    if kind in FORBIDDEN_DERIVATIONS or kind in FORBIDDEN_PROVENANCE_CLASSES:
        raise Section1114OfflineSurfaceError("FORBIDDEN_POS_DERIVATION")
    if kind != ADMISSIBLE_POS_SOURCE_KIND:
        raise Section1114OfflineSurfaceError("POS_SOURCE_KIND_REJECTED")
    if bound_fill_identity_exists is not True:
        raise Section1114OfflineSurfaceError("BOUND_FILL_IDENTITY_MISSING")
    if restart_already_occurred is True:
        raise Section1114OfflineSurfaceError("RETROACTIVE_SYNTHESIS_FORBIDDEN")
    if str(capture_trigger or "").strip() != REQUIRED_CAPTURE_TRIGGER:
        raise Section1114OfflineSurfaceError("CAPTURE_TRIGGER_MISMATCH")
    provenance = str(provenance_class or "").strip()
    if provenance in FORBIDDEN_PROVENANCE_CLASSES:
        raise Section1114OfflineSurfaceError("FORBIDDEN_PROVENANCE")
    if provenance != CONTEMPORANEOUS_PROVENANCE_CLASS:
        raise Section1114OfflineSurfaceError("NO_SYNTHETIC_PRE_RESTART_PROVENANCE")
    if str(unit or "").strip() != POS_UNIT:
        raise Section1114OfflineSurfaceError("WRONG_UNIT")
    expected_inst, expected_clordid, expected_ord, expected_pos_side, expected_sz, parameterized = (
        _bound_identity_fields(bound_fill_identity=bound_fill_identity)
    )
    if str(inst_id or "").strip() != expected_inst:
        raise Section1114OfflineSurfaceError("WRONG_INSTRUMENT")
    if str(clordid or "").strip() != expected_clordid:
        raise Section1114OfflineSurfaceError("IDENTITY_MISMATCH")
    if str(ord_id or "").strip() != expected_ord:
        raise Section1114OfflineSurfaceError("IDENTITY_MISMATCH")
    if str(pos_side or "").strip() != expected_pos_side:
        raise Section1114OfflineSurfaceError("IDENTITY_MISMATCH")
    qty = _parse_unsigned_qty(resulting_current_position_qty)
    fill_sz = parse_handoff_pos_v1(expected_sz)
    if fill_sz is not None and fill_sz != 0 and qty == 0:
        raise Section1114OfflineSurfaceError("SILENT_REINITIALIZATION_FORBIDDEN")
    if fill_sz is not None and qty != fill_sz:
        raise Section1114OfflineSurfaceError("POS_MUST_DECIMAL_EQUAL_BOUND_IDENTITY")
    pos_text = format(qty, "f")
    return {
        "PRODUCER_ID": PRODUCER_ID,
        "SELECTED_SEMANTIC_ID": SELECTED_SEMANTIC_ID,
        "NEW_PRODUCER_IMPLEMENTED": True,
        "PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED": True,
        "pos": pos_text,
        "POS_UNIT": POS_UNIT,
        "POS_SIGN_SEMANTICS": POS_SIGN_SEMANTICS,
        "source_kind": ADMISSIBLE_POS_SOURCE_KIND,
        "provenance_class": CONTEMPORANEOUS_PROVENANCE_CLASS,
        "capture_trigger": REQUIRED_CAPTURE_TRIGGER,
        "clOrdId": expected_clordid,
        "ordId": expected_ord,
        "instId": expected_inst,
        "posSide": expected_pos_side,
        "PEAK_TRADE_OWNED": True,
        "CONTEMPORANEOUS": True,
        "FILL_SZ_COPY": False,
        "VENUE_GET_USED": False,
        "FUTURE_BOUND_IDENTITY_PARAMETERIZED": parameterized,
    }
