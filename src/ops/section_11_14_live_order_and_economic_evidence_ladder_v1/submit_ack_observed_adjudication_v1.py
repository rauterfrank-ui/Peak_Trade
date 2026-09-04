"""Adjudicate LIVE_SUBMIT_ACK_OBSERVED from the bound proof criterion.

Does not POST. Does not GET. Does not promote the standing ladder field.
Injected response evidence may satisfy the synchronous conjunction; that is
not LIVE_SUBMIT_ACK_OBSERVED.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CASE_ADJUDICATION,
    LIVE_ORDER_PLAN_OBSERVED,
    LIVE_SUBMIT_ACK_OBSERVED,
    LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_DEFINITION,
    LIVE_SUBMIT_ACK_OBSERVED_PRODUCER,
    LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.submit_ack_observed_predicate_v1 import (
    ACK_FIELD_CONSTITUENT_COUNT,
    ACK_FIELD_CONSTITUENTS,
    ACK_RESPONSE_CONSTITUENT_COUNT,
    ACK_RESPONSE_CONSTITUENTS,
    ADMISSIBLE_SOURCE_KIND,
    CLASS_ACK_SUCCESS,
    INJECTED_EVIDENCE_SOURCE_KIND,
    classify_submit_response_v1,
    evaluate_ack_response_conjunction_v1,
    evaluate_live_submit_ack_observed_conjunction_v1,
    response_constituents_from_evidence_v1,
)


def refuse_live_submit_ack_observed_true_v1(*, claimed_true: bool) -> None:
    if claimed_true is True or LIVE_SUBMIT_ACK_OBSERVED is True:
        raise Section1114OfflineSurfaceError("LIVE_SUBMIT_ACK_OBSERVED_MUST_REMAIN_FALSE")


def adjudicate_live_submit_ack_observed_v1(
    *,
    submit_ack_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    refuse_live_submit_ack_observed_true_v1(claimed_true=False)
    if LIVE_ORDER_PLAN_OBSERVED is not True:
        raise Section1114OfflineSurfaceError("ORDER_PLAN_PREDECESSOR_FALSE")
    evidence = dict(submit_ack_evidence or {})
    if evidence.get("POST_USED") is True or evidence.get("POST") is True:
        raise Section1114OfflineSurfaceError("POST_INVOKED_BY_ACK_PROOF_CRITERION_GO")
    if evidence.get("LIVE_SUBMIT_ACK_OBSERVED") is True:
        raise Section1114OfflineSurfaceError("ACK_FIELD_PROMOTED_BY_INJECTED_EVIDENCE")
    if evidence.get("LIVE_FILL_OBSERVED") is True:
        raise Section1114OfflineSurfaceError("FILL_PROMOTED_BEFORE_ACK")

    response_constituents = response_constituents_from_evidence_v1(
        http_status=evidence.get("http_status"),
        okx_code=evidence.get("okx_code"),
        json_parse_ok=evidence.get("json_parse_ok"),
        redirect_followed=bool(evidence.get("redirect_followed")),
        redirectish=bool(evidence.get("redirectish")),
        data_count=evidence.get("data_count"),
        s_code=evidence.get("s_code"),
        ord_id=evidence.get("ord_id"),
        returned_clordid=evidence.get("returned_clordid"),
        sent_clordid=evidence.get("sent_clordid"),
    )
    response_eval = evaluate_ack_response_conjunction_v1(constituent_values=response_constituents)
    classified = classify_submit_response_v1(
        send_attempted=bool(evidence.get("send_attempted")),
        entry_submit_count=int(evidence.get("entry_submit_count") or 0),
        http_status=evidence.get("http_status"),
        okx_code=evidence.get("okx_code"),
        json_parse_ok=evidence.get("json_parse_ok"),
        redirect_followed=bool(evidence.get("redirect_followed")),
        redirectish=bool(evidence.get("redirectish")),
        data_count=evidence.get("data_count"),
        s_code=evidence.get("s_code"),
        ord_id=evidence.get("ord_id"),
        returned_clordid=evidence.get("returned_clordid"),
        sent_clordid=evidence.get("sent_clordid"),
        transport_error=evidence.get("transport_error"),
    )
    field_constituents: dict[str, bool | None] = {
        "LIVE_ORDER_PLAN_OBSERVED": True,
        "CURRENT_PRODUCTIVE_POST_OF_FRESH_PLAN": False,
        "SYNCHRONOUS_RESPONSE_CRITERION_SATISFIED": bool(
            response_eval["claim_value"] is True
            and classified["classification"] == CLASS_ACK_SUCCESS
        ),
        "ADMISSIBLE_LIVE_POST_SOURCE": False,
        "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
    }
    # Standing field remains false: this GO forbids POST, so the field
    # conjunction is evaluated only to prove the missing live-post conjunct.
    field_eval = {
        "canonical_definition": LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_DEFINITION,
        "claim_value": False,
        "adjudication": "FALSE_FAIL_CLOSED_NO_LIVE_POST",
        "false_required": [
            name for name in ACK_FIELD_CONSTITUENTS if field_constituents.get(name) is not True
        ],
        "constituent_count": ACK_FIELD_CONSTITUENT_COUNT,
        "source_kind": INJECTED_EVIDENCE_SOURCE_KIND,
        "admissible_live_source_kind": ADMISSIBLE_SOURCE_KIND,
    }
    recon_match = bool(evidence.get("read_only_recon_clordid_match") is True)
    if recon_match and LIVE_SUBMIT_ACK_OBSERVED is True:
        raise Section1114OfflineSurfaceError("RECON_MATCH_PROMOTED_ACK")
    return {
        "canonical_definition": LIVE_SUBMIT_ACK_OBSERVED_CANONICAL_DEFINITION,
        "producer": LIVE_SUBMIT_ACK_OBSERVED_PRODUCER,
        "proof_criterion_bound": LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND,
        "response_constituents": ACK_RESPONSE_CONSTITUENTS,
        "response_constituent_count": ACK_RESPONSE_CONSTITUENT_COUNT,
        "response_constituent_values": response_constituents,
        "response_conjunction": response_eval,
        "field_constituents": ACK_FIELD_CONSTITUENTS,
        "field_constituent_values": field_constituents,
        "field_conjunction": field_eval,
        "classification": classified,
        "adjudicated_value": False,
        "claim_value": False,
        "LIVE_SUBMIT_ACK_OBSERVED": False,
        "LIVE_FILL_OBSERVED": False,
        "read_only_recon_clordid_match_is_not_ack": True,
        "read_only_recon_clordid_match": recon_match,
        "POST_USED": False,
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
    }


def assert_injected_success_cannot_promote_live_field_v1() -> None:
    """Prove GOVERNED_CURRENT_LIVE_POST is required for the ladder field."""

    refuse_live_submit_ack_observed_true_v1(claimed_true=False)
    with_false_post = {
        "LIVE_ORDER_PLAN_OBSERVED": True,
        "CURRENT_PRODUCTIVE_POST_OF_FRESH_PLAN": True,
        "SYNCHRONOUS_RESPONSE_CRITERION_SATISFIED": True,
        "ADMISSIBLE_LIVE_POST_SOURCE": True,
        "NOT_FIXTURE_TESTNET_OR_SIMULATED": True,
    }
    try:
        evaluate_live_submit_ack_observed_conjunction_v1(
            constituent_values=with_false_post,
            source_kind=INJECTED_EVIDENCE_SOURCE_KIND,
        )
    except Section1114OfflineSurfaceError as exc:
        if "INJECTED_EVIDENCE_CANNOT_SATISFY_LIVE_FIELD" not in str(exc):
            raise
        return
    raise Section1114OfflineSurfaceError("INJECTED_SOURCE_DID_NOT_FAIL_CLOSED")
