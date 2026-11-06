"""Adjudicate LIVE_PRIVATE_READ_ONLY_PROVEN from current private GET conjunction."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_EXECUTION_CODE_EXISTS,
    LIVE_EXECUTION_PATH_REACHABLE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.private_read_only_predicate_v1 import (
    ADMISSIBILITY_PREDICATE,
    PRIVATE_READ_ONLY_CONSTITUENT_COUNT,
    PRIVATE_READ_ONLY_CONSTITUENTS,
    evaluate_private_read_only_conjunction_v1,
)


def adjudicate_live_private_read_only_proven_v1(
    *,
    private_read_only_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    get_ev = dict(private_read_only_evidence or {})
    if get_ev.get("POST_USED") is True:
        raise Section1114OfflineSurfaceError("POST_INVOKED_BY_PRIVATE_READ_ONLY_PROOF")
    if get_ev.get("LIVE_ORDER_PLAN_OBSERVED") is True:
        raise Section1114OfflineSurfaceError("GET_EVIDENCE_PROMOTED_LIVE_ORDER_PLAN_OBSERVED")
    source_kind = "GOVERNED_CURRENT_PRIVATE_GET" if get_ev else "GOVERNED_OFFLINE_CONTRACT"
    values: dict[str, bool | None] = {
        "PREDECESSOR_LIVE_EXECUTION_CODE_EXISTS": bool(LIVE_EXECUTION_CODE_EXISTS is True),
        "PREDECESSOR_LIVE_EXECUTION_PATH_REACHABLE": bool(LIVE_EXECUTION_PATH_REACHABLE is True),
        "CURRENT_PRIVATE_GET_CONFIG_HTTP_200_OKX_0": (
            None
            if not get_ev
            else bool(get_ev.get("CURRENT_PRIVATE_GET_CONFIG_HTTP_200_OKX_0") is True)
        ),
        "CURRENT_PRIVATE_GET_BALANCE_HTTP_200_OKX_0": (
            None
            if not get_ev
            else bool(get_ev.get("CURRENT_PRIVATE_GET_BALANCE_HTTP_200_OKX_0") is True)
        ),
        "BOTH_METHODS_GET": None if not get_ev else bool(get_ev.get("BOTH_METHODS_GET") is True),
        "NO_POST": None if not get_ev else bool(get_ev.get("NO_POST") is True),
        "PARSEABLE_ACCOUNT_CONFIG_DATA": (
            None if not get_ev else bool(get_ev.get("PARSEABLE_ACCOUNT_CONFIG_DATA") is True)
        ),
        "PARSEABLE_ACCOUNT_BALANCE_DATA": (
            None if not get_ev else bool(get_ev.get("PARSEABLE_ACCOUNT_BALANCE_DATA") is True)
        ),
        "NO_REDIRECT": None if not get_ev else bool(get_ev.get("NO_REDIRECT") is True),
    }
    result = evaluate_private_read_only_conjunction_v1(
        constituent_values=values,
        source_kind=source_kind,
    )
    return {
        "canonical_definition": result["canonical_definition"],
        "admissibility_predicate": ADMISSIBILITY_PREDICATE,
        "constituent_count": PRIVATE_READ_ONLY_CONSTITUENT_COUNT,
        "constituents": list(PRIVATE_READ_ONLY_CONSTITUENTS),
        "constituent_values": values,
        "conjunction": result,
        "adjudicated_value": bool(result["claim_value"] is True),
        "adjudication": result["adjudication"],
        "reason": result["reason"],
        "private_read_only_evidence_present": bool(get_ev),
        "LIVE_ORDER_PLAN_OBSERVED": False,
        "submit_authorization_inferred": False,
        "gate_mutation_performed": False,
        "post_used": False,
    }
