"""Bound Live economic-path identity for §11.14 LIVE_ACCOUNTING_RECONSTRUCTED.

Values are the identity-bound fill/fee/position observations already
persisted on the acknowledged Live submit. They are not inferred from
rate, notional, mark, or balance. This module does not GET and does not POST.
"""

from __future__ import annotations

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_ACK_EVIDENCE_RUN_ID,
    BOUND_ACK_SOURCE_KIND,
    BOUND_CLORDID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
)

BOUND_TRADE_ID = "1055244"
BOUND_FILL_FEE = "-0.000374"
BOUND_FILL_FEE_CCY = "USDC"
BOUND_FILL_PNL = "0"
BOUND_POSITION_CCY = "USDC"
BOUND_FEE_EVIDENCE_RUN_ID = "20260904T173813Z"
BOUND_POSITION_EVIDENCE_RUN_ID = "20260904T181817Z"
BOUND_FILL_RAW_RELPATH = (
    "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
    "20260904T173813Z/GET_FILLS.raw.json"
)
BOUND_POSITION_RAW_RELPATH = (
    "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
    "20260904T181817Z/GET_POSITIONS.raw.json"
)
ACCOUNTING_UNIT = "USDC"
ACCOUNTING_TOLERANCE = "0"
ACCOUNTING_TOLERANCE_AUTHORITY = "EXACT_DECIMAL_EQUALITY_NO_INVENTED_TOLERANCE"


def bound_live_accounting_identity_v1() -> dict[str, str]:
    return {
        "ordId": BOUND_ORDID,
        "clOrdId": BOUND_CLORDID,
        "instId": BOUND_INSTID,
        "posSide": BOUND_POS_SIDE,
        "fillSz": BOUND_FILL_SZ,
        "tradeId": BOUND_TRADE_ID,
        "fillFee": BOUND_FILL_FEE,
        "fillFeeCcy": BOUND_FILL_FEE_CCY,
        "fillPnl": BOUND_FILL_PNL,
        "positionCcy": BOUND_POSITION_CCY,
        "ack_source_kind": BOUND_ACK_SOURCE_KIND,
        "ack_evidence_run_id": BOUND_ACK_EVIDENCE_RUN_ID,
        "fee_evidence_run_id": BOUND_FEE_EVIDENCE_RUN_ID,
        "position_evidence_run_id": BOUND_POSITION_EVIDENCE_RUN_ID,
        "unit": ACCOUNTING_UNIT,
        "tolerance": ACCOUNTING_TOLERANCE,
    }
