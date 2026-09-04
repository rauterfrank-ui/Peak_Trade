"""Exact bound Live submit identity for §11.14 LIVE_FILL_OBSERVED.

Does not derive the target from latest order, newest timestamp, instrument
alone, position, pending-order ordering, nearest clOrdId, or heuristics.
"""

from __future__ import annotations

from typing import Any, Mapping

BOUND_ORDID = "3893505043080286208"
BOUND_CLORDID = "ptokxeprod1fec928b1fec928b00"
BOUND_INSTID = "SUI-USD_UM_XPERP-310404"
BOUND_INST_TYPE = "FUTURES"
BOUND_SUBMITTED_SZ = "1"
BOUND_ACK_SOURCE_KIND = "GOVERNED_CURRENT_LIVE_POST"
BOUND_ACK_EVIDENCE_RUN_ID = "20260904T160450Z"
BOUND_SIDE = "buy"


def bound_live_submit_identity_v1() -> dict[str, str]:
    return {
        "ordId": BOUND_ORDID,
        "clOrdId": BOUND_CLORDID,
        "instId": BOUND_INSTID,
        "instType": BOUND_INST_TYPE,
        "submitted_sz": BOUND_SUBMITTED_SZ,
        "ack_source_kind": BOUND_ACK_SOURCE_KIND,
        "ack_evidence_run_id": BOUND_ACK_EVIDENCE_RUN_ID,
        "side": BOUND_SIDE,
    }


def exact_identity_match_v1(
    *,
    ord_id: object,
    clordid: object,
    inst_id: object,
) -> dict[str, bool]:
    ord_match = str(ord_id or "") == BOUND_ORDID
    clordid_match = str(clordid or "") == BOUND_CLORDID
    inst_match = str(inst_id or "") == BOUND_INSTID
    return {
        "ORDID_MATCH": ord_match,
        "CLORDID_MATCH": clordid_match,
        "INSTRUMENT_MATCH": inst_match,
        "ORDER_IDENTITY_MATCH": bool(ord_match and clordid_match and inst_match),
    }


def row_identity_fields_v1(row: Mapping[str, Any] | None) -> dict[str, str]:
    item = dict(row or {})
    return {
        "ordId": str(item.get("ordId") or ""),
        "clOrdId": str(item.get("clOrdId") or ""),
        "instId": str(item.get("instId") or ""),
    }
