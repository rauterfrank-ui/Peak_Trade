"""Bound Live identity and known evidence roots for restart reconstruction.

This module does not GET and does not POST. It does not invent a durable
pre-restart handoff. Missing facts remain missing.
"""

from __future__ import annotations

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_identity_v1 import (
    BOUND_FEE_EVIDENCE_RUN_ID,
    BOUND_FILL_RAW_RELPATH,
    BOUND_POSITION_EVIDENCE_RUN_ID,
    BOUND_POSITION_RAW_RELPATH,
    BOUND_TRADE_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.fill_observed_identity_v1 import (
    BOUND_ACK_EVIDENCE_RUN_ID,
    BOUND_ACK_SOURCE_KIND,
    BOUND_CLORDID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
)

BOUND_ACCOUNTING_EVIDENCE_RUN_ID = "20260904T185000Z"
TESTNET_RESTART_PROVEN_EVIDENCE_RELPATH = (
    "evidence/ops/section_11_12_testnet_restart_proven_v1/20260810T223606Z/"
)
TESTNET_RESTART_PROVEN_INSTID = "BTC-USD_UM_XPERP-310328"
TESTNET_RESTART_PROVEN_ENVIRONMENT = "DEMO"
KNOWN_LIVE_EVIDENCE_RUN_IDS: tuple[str, ...] = (
    BOUND_ACK_EVIDENCE_RUN_ID,
    "20260904T165859Z",
    BOUND_FEE_EVIDENCE_RUN_ID,
    BOUND_POSITION_EVIDENCE_RUN_ID,
    BOUND_ACCOUNTING_EVIDENCE_RUN_ID,
)
LIVE_EVIDENCE_DIRNAME = "section_11_14_live_order_and_economic_evidence_ladder_v1"
DURABLE_HANDOFF_RELATIVE_MARKERS: tuple[str, ...] = (
    "durable_state",
    "pre_restart",
    "restart_with_open_position_pre_restart_v1.json",
    "restart_with_open_order_pre_restart_v1.json",
)


def bound_live_restart_identity_v1() -> dict[str, str]:
    return {
        "ordId": BOUND_ORDID,
        "clOrdId": BOUND_CLORDID,
        "instId": BOUND_INSTID,
        "posSide": BOUND_POS_SIDE,
        "fillSz": BOUND_FILL_SZ,
        "tradeId": BOUND_TRADE_ID,
        "ack_source_kind": BOUND_ACK_SOURCE_KIND,
        "ack_evidence_run_id": BOUND_ACK_EVIDENCE_RUN_ID,
        "fee_evidence_run_id": BOUND_FEE_EVIDENCE_RUN_ID,
        "position_evidence_run_id": BOUND_POSITION_EVIDENCE_RUN_ID,
        "accounting_evidence_run_id": BOUND_ACCOUNTING_EVIDENCE_RUN_ID,
        "fill_raw_relpath": BOUND_FILL_RAW_RELPATH,
        "position_raw_relpath": BOUND_POSITION_RAW_RELPATH,
        "testnet_restart_proven_relpath": TESTNET_RESTART_PROVEN_EVIDENCE_RELPATH,
        "testnet_restart_proven_instId": TESTNET_RESTART_PROVEN_INSTID,
        "testnet_restart_proven_environment": TESTNET_RESTART_PROVEN_ENVIRONMENT,
    }
