"""Adjudicate LIVE_ORDER_PLAN_OBSERVED from gated-path evidence.

Does not promote LIVE_SUBMIT_ACK_OBSERVED. Rejects POST in this field's pack.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ORDER_PLAN_OBSERVED,
    LIVE_ORDER_PLAN_OBSERVED_CANONICAL_DEFINITION,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    LIVE_SUBMIT_ACK_OBSERVED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.order_plan_observed_predicate_v1 import (
    ORDER_PLAN_OBSERVED_CONSTITUENTS,
    evaluate_order_plan_observed_conjunction_v1,
)


def _constituents_from_evidence_v1(evidence: Mapping[str, Any] | None) -> dict[str, bool | None]:
    if evidence is None:
        return {name: None for name in ORDER_PLAN_OBSERVED_CONSTITUENTS}
    return {
        "LIVE_EXECUTION_CODE_EXISTS": bool(evidence.get("LIVE_EXECUTION_CODE_EXISTS") is True),
        "LIVE_EXECUTION_PATH_REACHABLE": bool(
            evidence.get("LIVE_EXECUTION_PATH_REACHABLE") is True
        ),
        "LIVE_PRIVATE_READ_ONLY_PROVEN": bool(
            evidence.get("LIVE_PRIVATE_READ_ONLY_PROVEN") is True
        ),
        "PRODUCED_ON_CANONICAL_SUBMIT_PATH": bool(
            evidence.get("PRODUCED_ON_CANONICAL_SUBMIT_PATH") is True
        ),
        "AFTER_REFUSE_SUBMIT_UNLESS_GATES_PASS": bool(
            evidence.get("AFTER_REFUSE_SUBMIT_UNLESS_GATES_PASS") is True
        ),
        "CURRENT_VENUE_DERIVED_INPUTS": bool(evidence.get("CURRENT_VENUE_DERIVED_INPUTS") is True),
        "ORDER_PLAN_ARTIFACT_PRESENT": bool(evidence.get("ORDER_PLAN_ARTIFACT_PRESENT") is True),
        "NOT_BLOCKED_DRY_RUN": bool(evidence.get("NOT_BLOCKED_DRY_RUN") is True),
        "NOT_DIRECT_BUILDER_INVOCATION": bool(
            evidence.get("NOT_DIRECT_BUILDER_INVOCATION") is True
        ),
        "NO_POST_REQUIRED": bool(evidence.get("NO_POST_REQUIRED") is True),
    }


def adjudicate_live_order_plan_observed_v1(
    *,
    order_plan_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if order_plan_evidence is None:
        return {
            "canonical_definition": LIVE_ORDER_PLAN_OBSERVED_CANONICAL_DEFINITION,
            "adjudicated_value": False,
            "claim_value": False,
            "LIVE_ORDER_PLAN_OBSERVED": False,
            "LIVE_SUBMIT_ACK_OBSERVED": False,
            "reason": "UNOBSERVED",
        }
    if order_plan_evidence.get("POST_USED") is True or order_plan_evidence.get("POST") is True:
        raise Section1114OfflineSurfaceError("POST_INVOKED_BY_ORDER_PLAN_PROOF")
    if order_plan_evidence.get("LIVE_SUBMIT_ACK_OBSERVED") is True:
        raise Section1114OfflineSurfaceError("SUBMIT_ACK_PROMOTED_BY_ORDER_PLAN_PROOF")
    if LIVE_PRIVATE_READ_ONLY_PROVEN is not True:
        raise Section1114OfflineSurfaceError("PRIVATE_READ_ONLY_PREDECESSOR_FALSE")
    conjunction = evaluate_order_plan_observed_conjunction_v1(
        constituent_values=_constituents_from_evidence_v1(order_plan_evidence)
    )
    claim = bool(conjunction["claim_value"] is True)
    if claim is True and LIVE_SUBMIT_ACK_OBSERVED is True:
        raise Section1114OfflineSurfaceError("SUBMIT_ACK_STANDING_TRUE")
    return {
        "canonical_definition": LIVE_ORDER_PLAN_OBSERVED_CANONICAL_DEFINITION,
        "adjudicated_value": claim,
        "claim_value": claim,
        "LIVE_ORDER_PLAN_OBSERVED": claim,
        "LIVE_SUBMIT_ACK_OBSERVED": False,
        "reason": conjunction["adjudication"],
        "conjunction": conjunction,
        "constant_matches_claim": claim is bool(LIVE_ORDER_PLAN_OBSERVED is True),
    }
