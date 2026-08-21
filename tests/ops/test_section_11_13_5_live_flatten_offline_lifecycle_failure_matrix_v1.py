"""LF-04 offline lifecycle failure-matrix tests. No network, no submit."""

from __future__ import annotations

import inspect
from typing import Any, Mapping

import pytest

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    REDUCE_ONLY_WIRE_TYPE_STATUS,
    build_venue_native_order_body_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    ENDPOINT_CANCEL,
    ENDPOINT_SUBMIT,
    ORDER_COUNT_LIMIT,
    POST_ENDPOINTS_GATED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_orchestration_contract_v1 import (
    ACCOUNT_MUTATION_EFFECT_NONE,
    LF04_FAILURE_CLASSES,
    LIFECYCLE_FLATTEN_RUNTIME_REACHABLE,
    LIVE_FLATTEN_PROVABILITY_STATUS,
    NETWORK_EFFECT_NONE,
    ORDER_EFFECT_NONE,
    CanaryFlattenLifecycleFailureMatrixVerdictV1,
    CanaryFlattenLifecycleObservationV1,
    CanaryFlattenSubmitPermitV1,
    LiveCanaryFlattenOrchestrationError,
    evaluate_canary_flatten_lifecycle_failure_matrix_v1,
    evaluate_canary_flatten_orchestration_contract_v1,
    issue_canary_flatten_submit_permit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.lifecycle_v1 import (
    LiveCanaryLifecycleError,
    build_lifecycle_and_closeout_contract_v1,
    refuse_ungated_lifecycle_transition_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    FLATTEN_LIMIT_PRICE_GATE_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_transport_v1 import (
    run_canary_submit_transport_v1,
)

OWNER_GO = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
ORIGIN_SHA = "34163718d7e053e1f4f93f842b86968729551b09"
TARGET = DEFAULT_INSTRUMENT_ID


def _positions(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _pending(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _obs(**overrides: Any) -> CanaryFlattenLifecycleObservationV1:
    payload: dict[str, Any] = {
        "positions_payload": _positions({"instId": TARGET, "pos": "1"}),
    }
    payload.update(overrides)
    return CanaryFlattenLifecycleObservationV1(**payload)


def _evaluate(
    *,
    case: str,
    initial_state: str,
    observations: tuple[CanaryFlattenLifecycleObservationV1, ...],
    submitted_entry_sz: str | None = "1",
    prior_flatten_orchestration_attempts: int = 0,
    reconstructed_permit: CanaryFlattenSubmitPermitV1 | None = None,
) -> CanaryFlattenLifecycleFailureMatrixVerdictV1:
    return evaluate_canary_flatten_lifecycle_failure_matrix_v1(
        case=case,
        initial_state=initial_state,
        observation_sequence=observations,
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
        submitted_entry_sz=submitted_entry_sz,
        prior_flatten_orchestration_attempts=prior_flatten_orchestration_attempts,
        reconstructed_permit=reconstructed_permit,
    )


def _assert_safety_invariants(verdict: CanaryFlattenLifecycleFailureMatrixVerdictV1) -> None:
    assert verdict.submit_reachable is False
    assert verdict.flatten_action_authorized is False
    assert verdict.second_effect_authorized is False
    assert verdict.position_flip_authorized is False
    assert verdict.implicit_runtime_authorization is False
    assert verdict.fail_closed is True
    assert verdict.network_effect == NETWORK_EFFECT_NONE == "none"
    assert verdict.order_effect == ORDER_EFFECT_NONE == "none"
    assert verdict.account_mutation_effect == ACCOUNT_MUTATION_EFFECT_NONE == "none"
    assert verdict.live_flatten_provability == LIVE_FLATTEN_PROVABILITY_STATUS == "UNPROVEN"
    assert verdict.lifecycle_flatten_runtime_reachable is False
    assert LIFECYCLE_FLATTEN_RUNTIME_REACHABLE is False
    if verdict.permit is not None:
        assert verdict.permit.submit_reachable is False
        assert verdict.permit.kind == "FLATTEN_SUBMIT"


FAILURE_MATRIX: list[tuple[Any, ...]] = [
    (
        "PARTIAL_ENTRY_FILL",
        "PARTIAL_FILL",
        (
            _obs(
                positions_payload=_positions({"instId": TARGET, "pos": "1"}),
                pending_orders_payload=_pending({"instId": TARGET, "clOrdId": "entry1", "sz": "2"}),
                entry_submit_outcome="PARTIAL_FILL",
            ),
        ),
        False,
        "NONE",
        "PARTIAL_FILL",
        "OPEN_ORDER_REMAINDER_CANCEL_ELIGIBILITY_UNPROVEN",
        "no flatten while entry remainder is still open",
    ),
    (
        "CANCEL_RACE",
        "CANCEL_PENDING",
        (
            _obs(
                cancel_status="RACE",
                pending_orders_payload=_pending({"instId": TARGET, "clOrdId": "entry1"}),
            ),
        ),
        False,
        "NONE",
        "CANCEL_PENDING",
        "CANCEL_RACE_ELIGIBILITY_UNPROVEN_NO_FLATTEN",
        "cancel race cannot release flatten",
    ),
    (
        "CANCEL_TIMEOUT",
        "CANCEL_PENDING",
        (_obs(cancel_status="TIMEOUT"),),
        False,
        "NONE",
        "CANCEL_PENDING",
        "CANCEL_TIMEOUT_ELIGIBILITY_UNPROVEN_NO_FLATTEN",
        "cancel timeout cannot release flatten",
    ),
    (
        "STALE_POSITION_OBSERVATION",
        "FILLED",
        (_obs(observation_fresh=False),),
        False,
        "NONE",
        "HALTED",
        "STALE_POSITION_OBSERVATION",
        "stale observation is fail-closed",
    ),
    (
        "STALE_POSITION_OBSERVATION",
        "FILLED",
        (
            _obs(positions_payload=_positions({"instId": TARGET, "pos": "2"})),
            _obs(positions_payload=_positions({"instId": TARGET, "pos": "-1"})),
        ),
        False,
        "NONE",
        "HALTED",
        "CONTRADICTORY_POSITION_SIGN_FLIP_FAIL_CLOSED",
        "sign flip cannot authorize a position flip",
    ),
    (
        "FLATTEN_REJECT",
        "FLATTEN_PENDING",
        (_obs(flatten_submit_outcome="REJECTED"),),
        False,
        "NONE",
        "HALTED",
        "FLATTEN_REJECT_NO_RETRY_TRANSPORT_UNPROVEN",
        "flatten reject does not retry and remains UNPROVEN",
    ),
    (
        "FLATTEN_TIMEOUT",
        "FLATTEN_PENDING",
        (_obs(flatten_submit_outcome="TIMEOUT"),),
        False,
        "NONE",
        "HALTED",
        "FLATTEN_TIMEOUT_NO_RETRY_DUPLICATE_RISK",
        "flatten timeout does not retry because of duplicate risk",
    ),
    (
        "PARTIAL_FLATTEN",
        "FLATTEN_PENDING",
        (
            _obs(
                positions_payload=_positions({"instId": TARGET, "pos": "1"}),
                flatten_submit_outcome="PARTIAL",
                claimed_flat=False,
            ),
        ),
        False,
        "NONE",
        "FLATTEN_PENDING",
        "PARTIAL_FLATTEN_REMAINING_POSITION_NOT_FLAT",
        "remaining observed position is never FLAT",
    ),
    (
        "DUPLICATE_ORCHESTRATION",
        "FILLED",
        (_obs(),),
        False,
        "NONE",
        "FLATTEN_PENDING",
        "DUPLICATE_FLATTEN_ORCHESTRATION_FORBIDDEN",
        "second orchestration attempt cannot authorize another flatten action",
    ),
    (
        "RESTART_RECONSTRUCTED_STATE",
        "FILLED",
        (_obs(reconstructed=True),),
        False,
        "NONE",
        "FILLED",
        "RESTART_RECONSTRUCTION_DOES_NOT_ISSUE_PERMIT",
        "restart reconstruction does not implicitly issue a permit",
    ),
    (
        "UNKNOWN_SUBMIT",
        "UNKNOWN_SUBMIT",
        (
            _obs(
                entry_submit_outcome="UNKNOWN",
                pending_orders_payload=_pending(),
                history_payload=_pending(),
                entry_clordid="unknownentryclordid1",
            ),
        ),
        False,
        "NONE",
        "UNKNOWN_SUBMIT",
        "UNKNOWN_SUBMIT_NO_AUTOMATIC_RETRY_NO_FLATTEN",
        "unknown submit does not retry or flatten",
    ),
]


@pytest.mark.parametrize(
    (
        "case",
        "initial_state",
        "observations",
        "expected_permit",
        "expected_action",
        "expected_state",
        "expected_reason",
        "fail_closed_assertion",
    ),
    FAILURE_MATRIX,
    ids=[f"{row[0]}:{row[6]}" for row in FAILURE_MATRIX],
)
def test_lf04_failure_matrix_cases(
    case: str,
    initial_state: str,
    observations: tuple[CanaryFlattenLifecycleObservationV1, ...],
    expected_permit: bool,
    expected_action: str,
    expected_state: str,
    expected_reason: str,
    fail_closed_assertion: str,
) -> None:
    prior = 1 if case == "DUPLICATE_ORCHESTRATION" else 0
    verdict = _evaluate(
        case=case,
        initial_state=initial_state,
        observations=observations,
        prior_flatten_orchestration_attempts=prior,
    )
    _assert_safety_invariants(verdict)
    assert verdict.case == case
    assert verdict.initial_state == initial_state
    assert verdict.permit_issued is expected_permit
    assert (verdict.permit is not None) is expected_permit
    assert verdict.expected_action == expected_action
    assert verdict.terminal_or_intermediate_state == expected_state
    assert verdict.reason == expected_reason
    assert fail_closed_assertion
    encoded = verdict.to_dict()
    assert encoded["permit_issued"] is expected_permit
    assert encoded["fail_closed"] is True
    assert encoded["submit_reachable"] is False


def test_lf04_canonical_failure_classes_are_all_covered() -> None:
    covered = {row[0] for row in FAILURE_MATRIX}
    assert covered == set(LF04_FAILURE_CLASSES)
    assert LF04_FAILURE_CLASSES == (
        "PARTIAL_ENTRY_FILL",
        "CANCEL_RACE",
        "CANCEL_TIMEOUT",
        "STALE_POSITION_OBSERVATION",
        "FLATTEN_REJECT",
        "FLATTEN_TIMEOUT",
        "PARTIAL_FLATTEN",
        "DUPLICATE_ORCHESTRATION",
        "RESTART_RECONSTRUCTED_STATE",
        "UNKNOWN_SUBMIT",
    )


def test_partial_entry_fill_does_not_use_submitted_entry_sz() -> None:
    verdict = _evaluate(
        case="PARTIAL_ENTRY_FILL",
        initial_state="PARTIAL_FILL",
        observations=(
            _obs(
                positions_payload=_positions({"instId": TARGET, "pos": "1"}),
                pending_orders_payload=_pending({"instId": TARGET, "clOrdId": "entry1"}),
                entry_submit_outcome="PARTIAL_FILL",
            ),
        ),
        submitted_entry_sz="2",
    )
    _assert_safety_invariants(verdict)
    assert verdict.permit_issued is False
    assert verdict.permit is None


def test_partial_fill_after_proven_cancel_issues_inert_permit_only() -> None:
    verdict = _evaluate(
        case="PARTIAL_ENTRY_FILL",
        initial_state="PARTIAL_FILL",
        observations=(
            _obs(
                positions_payload=_positions({"instId": TARGET, "pos": "1"}),
                pending_orders_payload=_pending(),
                cancel_status="CANCELED",
                entry_submit_outcome="PARTIAL_FILL",
            ),
        ),
        submitted_entry_sz="2",
    )
    _assert_safety_invariants(verdict)
    assert verdict.permit_issued is True
    assert verdict.permit is not None
    assert verdict.permit.quantity == "1"
    assert verdict.permit.quantity != "2"
    assert verdict.permit.submitted_entry_sz_used is False
    assert verdict.expected_action == "ISSUE_INERT_PERMIT_SUBMIT_BLOCKED"
    assert verdict.flatten_action_authorized is False
    assert verdict.orchestration_verdict is not None
    assert verdict.orchestration_verdict.transport_invoked is False


def test_partial_flatten_claimed_flat_with_rest_position_fail_closed() -> None:
    verdict = _evaluate(
        case="PARTIAL_FLATTEN",
        initial_state="FLATTEN_PENDING",
        observations=(
            _obs(
                positions_payload=_positions({"instId": TARGET, "pos": "1"}),
                flatten_submit_outcome="PARTIAL",
                claimed_flat=True,
            ),
        ),
    )
    _assert_safety_invariants(verdict)
    assert verdict.claimed_flat is True
    assert verdict.terminal_or_intermediate_state != "FLAT"
    assert verdict.reason == "PARTIAL_FLATTEN_REMAINING_POSITION_NOT_FLAT"
    assert verdict.permit_issued is False


def test_restart_reconstructed_permit_is_not_authorization() -> None:
    reconstructed = issue_canary_flatten_submit_permit_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    verdict = _evaluate(
        case="RESTART_RECONSTRUCTED_STATE",
        initial_state="FILLED",
        observations=(_obs(reconstructed=True),),
        reconstructed_permit=reconstructed,
    )
    _assert_safety_invariants(verdict)
    assert verdict.permit is None
    assert verdict.permit_issued is False
    assert verdict.implicit_runtime_authorization is False
    assert reconstructed.submit_reachable is False


def test_unknown_submit_classifies_unresolved_and_does_not_retry() -> None:
    verdict = _evaluate(
        case="UNKNOWN_SUBMIT",
        initial_state="UNKNOWN_SUBMIT",
        observations=(
            _obs(
                entry_submit_outcome="UNKNOWN",
                pending_orders_payload=_pending(),
                history_payload=_pending(),
                entry_clordid="unknownentryclordid1",
            ),
        ),
    )
    _assert_safety_invariants(verdict)
    assert "UNKNOWN_SUBMIT_UNRESOLVED_HALT" in verdict.blocking_reasons
    assert verdict.expected_action == "NONE"
    assert verdict.permit_issued is False


def test_unknown_submit_pending_resolution_still_forbids_flatten_and_retry() -> None:
    verdict = _evaluate(
        case="UNKNOWN_SUBMIT",
        initial_state="UNKNOWN_SUBMIT",
        observations=(
            _obs(
                entry_submit_outcome="UNKNOWN",
                pending_orders_payload=_pending(
                    {"instId": TARGET, "clOrdId": "unknownentryclordid1"}
                ),
                entry_clordid="unknownentryclordid1",
            ),
        ),
    )
    _assert_safety_invariants(verdict)
    assert "UNKNOWN_SUBMIT_RESOLVED_PENDING" in verdict.blocking_reasons
    assert verdict.permit_issued is False
    assert verdict.second_effect_authorized is False


def test_duplicate_second_evaluate_does_not_authorize_second_effect() -> None:
    first = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert first.permit_issued is True
    second = _evaluate(
        case="DUPLICATE_ORCHESTRATION",
        initial_state="FILLED",
        observations=(_obs(),),
        prior_flatten_orchestration_attempts=1,
    )
    _assert_safety_invariants(second)
    assert second.permit_issued is False
    assert second.second_effect_authorized is False
    assert first.submit_reachable is False


def test_ungated_flat_transition_remains_refused() -> None:
    with pytest.raises(
        LiveCanaryLifecycleError, match="UNGATED_LIFECYCLE_TRANSITION_FORBIDDEN:FLAT"
    ):
        refuse_ungated_lifecycle_transition_v1(claimed_state="FLAT")


def test_empty_observation_sequence_is_contract_error() -> None:
    with pytest.raises(LiveCanaryFlattenOrchestrationError, match="OBSERVATION_SEQUENCE_REQUIRED"):
        evaluate_canary_flatten_lifecycle_failure_matrix_v1(
            case="UNKNOWN_SUBMIT",
            initial_state="UNKNOWN_SUBMIT",
            observation_sequence=(),
            owner_go=OWNER_GO,
            origin_main_sha=ORIGIN_SHA,
        )


def test_entry_semantics_and_policy_surfaces_unchanged() -> None:
    body = build_venue_native_order_body_v1(
        client_order_id="c1",
        instrument=TARGET,
        order_type="LIMIT",
        side="buy",
        quantity="1",
        px="10000",
    )
    assert "reduceOnly" not in body
    assert REDUCE_ONLY_WIRE_TYPE_STATUS == "UNPROVEN"
    assert DEFAULT_ORDER_TYPE == "LIMIT"
    assert ORDER_COUNT_LIMIT == 1
    assert POST_ENDPOINTS_GATED == (
        "/api/v5/trade/order",
        "/api/v5/trade/cancel-order",
    )
    assert ENDPOINT_SUBMIT == "/api/v5/trade/order"
    assert ENDPOINT_CANCEL == "/api/v5/trade/cancel-order"
    assert "/api/v5/trade/close-position" not in POST_ENDPOINTS_GATED
    lifecycle = build_lifecycle_and_closeout_contract_v1()
    assert lifecycle["ACTIVATED"] is False
    assert lifecycle["order_count_limit"] == 1
    assert lifecycle["order_type_semantics"] == "LIMIT_ONLY_NO_MARKET"


def test_lf04_offline_path_invokes_no_transport_and_is_not_wired() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1 import (
        flatten_orchestration_contract_v1,
        http_client_v1,
        runner_v1,
    )

    matrix_src = inspect.getsource(evaluate_canary_flatten_lifecycle_failure_matrix_v1)
    orch_src = inspect.getsource(flatten_orchestration_contract_v1)
    transport_src = inspect.getsource(run_canary_submit_transport_v1)
    http_src = inspect.getsource(http_client_v1)
    runner_src = inspect.getsource(runner_v1)
    assert "transport.send" not in matrix_src
    assert "post_flatten_order" not in orch_src
    assert "post_entry_order" not in matrix_src
    assert "urllib" not in orch_src
    assert "evaluate_canary_flatten_orchestration_contract_v1" in matrix_src
    for banned in (
        "evaluate_canary_flatten_lifecycle_failure_matrix_v1",
        "issue_canary_flatten_submit_permit_v1",
        "evaluate_canary_flatten_orchestration_contract_v1",
        "post_flatten_order",
        "CanaryFlattenSubmitPermitV1",
    ):
        assert banned not in transport_src
        assert banned not in runner_src
    assert "post_flatten_order" in http_src
    assert "CanaryFlattenHttpPermitV1" in http_src
    assert "CanaryFlattenSubmitPermitV1" not in http_src
    assert FLATTEN_LIMIT_PRICE_GATE_STATUS == "FAIL_CLOSED_UNTIL_SEPARATE_OWNER_GO"
