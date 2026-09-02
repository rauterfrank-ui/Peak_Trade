"""Caller-supplied pre-wire validation. No GET. No invented live numerics."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    DEFAULT_TD_MODE,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    CanonicalLineageSnapshotV1,
    EvidenceFreshnessV1,
    PrewireEvidenceSnapshotV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LiveCanaryInstrumentBindingError,
    assert_live_canary_instrument_binding_v1,
)


class PrewireValidationError(RuntimeError):
    """Fail-closed pre-wire validation violation."""


def _positive_decimal(raw: str, *, field: str) -> Decimal:
    if not str(raw or "").strip() or str(raw).strip().upper() in {"UNKNOWN", "MISSING"}:
        raise PrewireValidationError(f"{field}_UNKNOWN_OR_MISSING")
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise PrewireValidationError(f"{field}_INVALID") from exc
    if value <= 0:
        raise PrewireValidationError(f"{field}_NOT_POSITIVE")
    return value


def validate_prewire_snapshots_v1(
    *,
    lineage: CanonicalLineageSnapshotV1,
    evidence: PrewireEvidenceSnapshotV1,
) -> tuple[str, ...]:
    """Return empty reasons on PASS. Never performs GET."""
    reasons: list[str] = []
    if evidence.get_performed_this_workpackage:
        reasons.append("GET_PERFORMED_THIS_WORKPACKAGE_FORBIDDEN")
    if evidence.source_kind != "CALLER_SUPPLIED_SNAPSHOT":
        reasons.append("PREWIRE_SOURCE_NOT_CALLER_SNAPSHOT")
    if evidence.freshness_status is EvidenceFreshnessV1.MISSING:
        reasons.append("PREWIRE_EVIDENCE_MISSING")
    elif evidence.freshness_status is EvidenceFreshnessV1.UNKNOWN:
        reasons.append("PREWIRE_EVIDENCE_UNKNOWN")
    elif evidence.freshness_status is EvidenceFreshnessV1.STALE:
        reasons.append("PREWIRE_EVIDENCE_STALE")
    elif evidence.freshness_status is not EvidenceFreshnessV1.PASS:
        reasons.append("PREWIRE_FRESHNESS_INVALID")
    try:
        assert_live_canary_instrument_binding_v1(instrument_id=evidence.instrument_id)
    except LiveCanaryInstrumentBindingError:
        reasons.append("INSTRUMENT_BINDING_FAIL_CLOSED")
    if evidence.instrument_id != lineage.instrument_id:
        reasons.append("PREWIRE_INSTRUMENT_MISMATCH")
    if evidence.instrument_id != CANONICAL_INSTRUMENT_ID:
        reasons.append("INSTRUMENT_NOT_CANONICAL")
    if evidence.instrument_state.strip().lower() in {"", "unknown", "missing"}:
        reasons.append("INSTRUMENT_STATE_UNKNOWN")
    elif evidence.instrument_state.strip().lower() != "live":
        reasons.append("INSTRUMENT_STATE_NOT_LIVE")
    order_type = evidence.order_type.strip().lower() or DEFAULT_ORDER_TYPE
    if order_type != DEFAULT_ORDER_TYPE:
        reasons.append("ORDER_TYPE_NOT_LIMIT")
    if evidence.td_mode.strip().lower() != DEFAULT_TD_MODE:
        reasons.append("TD_MODE_NOT_CROSS")
    try:
        qty = _positive_decimal(evidence.quantity, field="PREWIRE_QTY")
        plan_qty = _positive_decimal(lineage.plan_quantity, field="PLAN_QTY")
        if qty != plan_qty:
            reasons.append("PREWIRE_QUANTITY_PLAN_MISMATCH")
    except PrewireValidationError as exc:
        reasons.append(str(exc))
    if order_type == DEFAULT_ORDER_TYPE:
        try:
            _positive_decimal(evidence.limit_px, field="LIMIT_PX")
        except PrewireValidationError as exc:
            reasons.append(str(exc))
    for field, raw in (
        ("MAX_LMT_SZ", evidence.max_lmt_sz),
        ("AVAIL_BUY", evidence.avail_buy),
        ("AVAIL_SELL", evidence.avail_sell),
        ("LEVERAGE", evidence.leverage),
    ):
        token = str(raw or "").strip().upper()
        if token in {"", "UNKNOWN", "MISSING"}:
            reasons.append(f"{field}_UNKNOWN_OR_MISSING")
        elif token == "STALE":
            reasons.append(f"{field}_STALE")
        else:
            try:
                _positive_decimal(raw, field=field)
            except PrewireValidationError as exc:
                reasons.append(str(exc))
    if str(evidence.mgn_mode or "").strip().lower() in {"", "unknown", "missing"}:
        reasons.append("MGN_MODE_UNKNOWN")
    if str(evidence.pos_mode or "").strip().lower() in {"", "unknown", "missing"}:
        reasons.append("POS_MODE_UNKNOWN")
    if str(evidence.account_mode or "").strip().lower() in {"", "unknown", "missing"}:
        reasons.append("ACCOUNT_MODE_UNKNOWN")
    if str(evidence.position_observation_state or "").strip().upper() in {
        "",
        "UNKNOWN",
        "MISSING",
    }:
        reasons.append("POSITION_OBSERVATION_UNKNOWN")
    return tuple(dict.fromkeys(reasons))
