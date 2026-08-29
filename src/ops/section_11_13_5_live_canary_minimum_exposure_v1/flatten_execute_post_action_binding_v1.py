"""Bind CHOICE_B post-action and Category-C completeness into flatten_execute.

Caller-supplied snapshots/status only. Never GETs, never POSTs, never
enables live wire, never consumes Class D, and never claims
LIVE_FLATTEN_PROVABILITY=PROVEN. Category C is not added to GATE_NAMES.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.category_c_open_algo_pending_observer_v1 import (
    CategoryCObservationOutcomeV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_action_eligibility_v1 import (
    classify_flatten_action_eligibility_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    LIVE_FLATTEN_PROVABILITY_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_action_proof_contract_v1 import (
    evaluate_canary_flatten_post_action_proof_contract_v1,
    flatten_post_action_submit_evidence_from_submit_result_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_UNKNOWN,
    classify_target_position_state_v1,
)

POST_ACTION_WIRED_IN_FLATTEN_EXECUTE = True
POST_ACTION_READBACK_UNAVAILABLE = "POST_ACTION_READBACK_UNAVAILABLE"
CATEGORY_C_STATE_UNAVAILABLE = "CATEGORY_C_STATE_UNAVAILABLE"
CATEGORY_C_STATUS_UNRECOGNIZED = "CATEGORY_C_STATUS_UNRECOGNIZED"
CATEGORY_C_UNIVERSAL_ABSENCE_PROVEN = False
CATEGORY_C_SEND_WIRING_IN_PRE_SEND_GATE = False
PENDING_EMPTY_COMPLETENESS_REQUIRES_CATEGORY_C = True

_CATEGORY_C_KNOWN = frozenset(item.value for item in CategoryCObservationOutcomeV1)


def classify_category_c_flatten_completeness_v1(
    category_c_runtime_status: str | None,
) -> dict[str, Any]:
    """Record Category-C completeness without treating not-observed as no-algo."""
    if category_c_runtime_status is None or not str(category_c_runtime_status).strip():
        return {
            "category_c_runtime_status": CATEGORY_C_STATE_UNAVAILABLE,
            "category_c_pending_completeness": "UNPROVEN",
            "category_c_open_algo_present": False,
            "category_c_universal_absence_proven": False,
            "CATEGORY_C_SEND_WIRING_IN_PRE_SEND_GATE": CATEGORY_C_SEND_WIRING_IN_PRE_SEND_GATE,
        }
    status = str(category_c_runtime_status).strip()
    if status not in _CATEGORY_C_KNOWN:
        return {
            "category_c_runtime_status": CATEGORY_C_STATUS_UNRECOGNIZED,
            "category_c_pending_completeness": "UNPROVEN",
            "category_c_open_algo_present": False,
            "category_c_universal_absence_proven": False,
            "CATEGORY_C_SEND_WIRING_IN_PRE_SEND_GATE": CATEGORY_C_SEND_WIRING_IN_PRE_SEND_GATE,
            "reason": CATEGORY_C_STATUS_UNRECOGNIZED,
        }
    open_algo = status == CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_OBSERVED.value
    incomplete = status in {
        CategoryCObservationOutcomeV1.CATEGORY_C_OBSERVATION_INCOMPLETE.value,
        CategoryCObservationOutcomeV1.CATEGORY_C_UNKNOWN_TYPE_PRESENT.value,
        CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN.value,
    }
    not_observed = status == CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED.value
    completeness = "UNPROVEN"
    if open_algo:
        completeness = "OPEN_ALGO_PRESENT"
    elif incomplete:
        completeness = "UNPROVEN"
    elif not_observed:
        completeness = "NAMED_TYPES_NOT_OBSERVED_THIS_WINDOW_NOT_UNIVERSAL_ABSENCE"
    return {
        "category_c_runtime_status": status,
        "category_c_pending_completeness": completeness,
        "category_c_open_algo_present": open_algo,
        "category_c_universal_absence_proven": False,
        "CATEGORY_C_SEND_WIRING_IN_PRE_SEND_GATE": CATEGORY_C_SEND_WIRING_IN_PRE_SEND_GATE,
    }


def bind_flatten_execute_post_action_v1(
    *,
    submit_result: Any,
    pre_positions_payload: Mapping[str, Any] | None,
    post_positions_payload: Mapping[str, Any] | None,
    post_pending_orders_payload: Mapping[str, Any] | None,
    category_c_runtime_status: str | None,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
) -> dict[str, Any]:
    """Attach CHOICE_B post-action and Category-C completeness to flatten_execute."""
    pre_state = classify_target_position_state_v1(
        positions_payload=pre_positions_payload,
        instrument_id=instrument_id,
    )
    eligibility = classify_flatten_action_eligibility_v1(
        positions_payload=pre_positions_payload,
        instrument_id=instrument_id,
    )
    category_c = classify_category_c_flatten_completeness_v1(category_c_runtime_status)
    binding: dict[str, Any] = {
        "POST_ACTION_WIRED_IN_FLATTEN_EXECUTE": POST_ACTION_WIRED_IN_FLATTEN_EXECUTE,
        "pre_position_state": pre_state.to_dict(),
        "flatten_action_eligibility": eligibility.to_dict(),
        "flatten_position_proven": False,
        "LIVE_FLATTEN_PROVABILITY": LIVE_FLATTEN_PROVABILITY_STATUS,
        "productive_sequence_required": True,
        **category_c,
    }
    send_attempted = bool(getattr(submit_result, "send_attempted", False))
    post_ready = post_positions_payload is not None and post_pending_orders_payload is not None
    if not send_attempted:
        binding["post_action_status"] = "POST_ACTION_NOT_APPLICABLE_SEND_NOT_ATTEMPTED"
        binding["post_action_verdict"] = None
        return binding
    if not post_ready:
        binding["post_action_status"] = POST_ACTION_READBACK_UNAVAILABLE
        binding["post_action_verdict"] = None
        binding["choice_b_pos_eq_0"] = False
        return binding

    evidence = flatten_post_action_submit_evidence_from_submit_result_v1(
        submit_result,
        post_readback_after_submit=True,
    )
    verdict = evaluate_canary_flatten_post_action_proof_contract_v1(
        pre_positions_payload=pre_positions_payload or {},
        post_positions_payload=post_positions_payload or {},
        post_pending_orders_payload=post_pending_orders_payload or {},
        instrument_id=instrument_id,
        submit_evidence=evidence,
    )
    binding["post_action_status"] = verdict.contract_state
    binding["post_action_verdict"] = verdict.to_dict()
    binding["choice_b_pos_eq_0"] = bool(verdict.choice_b_pos_eq_0)
    binding["offline_contract_satisfied"] = bool(verdict.offline_contract_satisfied)
    if (
        pre_state.state == TARGET_POSITION_NOT_OBSERVED
        or pre_state.state == TARGET_POSITION_UNKNOWN
    ):
        binding["flatten_position_proven"] = False
    if category_c["category_c_open_algo_present"] or category_c[
        "category_c_pending_completeness"
    ] in {"UNPROVEN", "OPEN_ALGO_PRESENT"}:
        binding["pending_empty_completeness"] = "UNPROVEN"
    elif verdict.pending_empty:
        binding["pending_empty_completeness"] = (
            "REGULAR_PENDING_EMPTY_AND_NAMED_CATEGORY_C_NOT_OBSERVED_NOT_UNIVERSAL"
        )
    else:
        binding["pending_empty_completeness"] = "REGULAR_PENDING_NOT_EMPTY"
    binding["flatten_position_proven"] = False
    binding["LIVE_FLATTEN_PROVABILITY"] = LIVE_FLATTEN_PROVABILITY_STATUS
    return binding
