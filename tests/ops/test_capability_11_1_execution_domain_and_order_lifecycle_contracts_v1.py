"""Tests for CAPABILITY_11_1_EXECUTION_DOMAIN_AND_ORDER_LIFECYCLE_CONTRACTS_V1."""

from __future__ import annotations

import pytest

from src.governance.canonical_order_intent_v1 import CanonicalOrderIntentV1
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.adapter_anti_corruption_v1 import (
    prove_adapter_anti_corruption_v1,
    prove_order_portfolio_atomicity_contract_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.canonical_execution_event_schema_v1 import (
    ExecutionModeV1,
    build_canonical_execution_event_v1,
    prove_one_canonical_execution_event_schema_v1,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.canonical_intent_schema_v1 import (
    assert_intent_is_canonical_order_intent_v1,
    prove_one_canonical_intent_schema_v1,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
    construct_testnet_execution_port_v1,
    declare_live_execution_port_v1,
    declare_testnet_execution_port_v1,
    prove_mode_specific_execution_boundary_v1,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.order_lifecycle_state_machine_v1 import (
    OrderLifecycleStateMachineV1,
    OrderLifecycleTransitionError,
    prove_order_lifecycle_state_machine_v1,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_with_simulated_port_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.submission_semantics_v1 import (
    SubmissionIdempotencyRegistryV1,
    UnknownSubmitSemanticsV1,
    derive_client_order_id_v1,
    prove_client_order_id_and_submission_semantics_v1,
)
from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.verifier_v1 import (
    verify_capability_11_1_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    SimulatedExecutionPortV1,
)


def test_intent_schema_parity() -> None:
    proof = prove_one_canonical_intent_schema_v1()
    assert proof["ok"] is True
    assert proof["ONE_CANONICAL_INTENT_SCHEMA"] is True
    assert proof["parallel_intent_schema_introduced"] is False
    assert proof["CORE_LOGIC_CHANGE"] is False


def test_intent_must_be_canonical_order_intent() -> None:
    with pytest.raises(TypeError, match="PHASE11_INTENT_SCHEMA_VIOLATION"):
        assert_intent_is_canonical_order_intent_v1(object())
    # CanonicalOrderIntentV1 is the sole accepted type (construction via fields not required here).
    assert CanonicalOrderIntentV1.__name__ == "CanonicalOrderIntentV1"


def test_execution_event_schema_parity() -> None:
    proof = prove_one_canonical_execution_event_schema_v1()
    assert proof["ok"] is True
    event = build_canonical_execution_event_v1(
        event_id="evt-1",
        event_kind="INTENT_ACCEPTED",
        execution_mode=ExecutionModeV1.SIMULATED.value,
        intent_id="intent-1",
        order_plan_id="plan-1",
        client_order_id="coid-1",
        lifecycle_state="INTENT_CREATED",
        instrument_id="INST-1",
        side="LONG",
        quantity="1",
        reduce_only=False,
    )
    assert event.adapter_decision_authority is False
    assert event.semantic_digest
    assert event.submission_authorized is False


def test_execution_event_testnet_live_non_authorizing() -> None:
    with pytest.raises(ValueError, match="PHASE11_EXECUTION_EVENT_SAFETY_VIOLATION"):
        build_canonical_execution_event_v1(
            event_id="evt-2",
            event_kind="SUBMIT_ATTEMPTED",
            execution_mode=ExecutionModeV1.TESTNET.value,
            intent_id="intent-1",
            order_plan_id="plan-1",
            client_order_id="coid-1",
            lifecycle_state="SUBMIT_ATTEMPTED",
            instrument_id="INST-1",
            side="LONG",
            quantity="1",
            reduce_only=False,
            submission_authorized=True,
        )


def test_lifecycle_positive_transitions() -> None:
    machine = OrderLifecycleStateMachineV1()
    for state in [
        "ORDER_PLAN_CREATED",
        "RISK_RESERVED",
        "PRE_SUBMIT_VALIDATED",
        "SUBMIT_PENDING",
        "SUBMIT_ATTEMPTED",
        "ACKNOWLEDGED",
        "OPEN",
        "PARTIALLY_FILLED",
        "FILLED",
        "ACCOUNTED",
        "RECONCILED",
        "EVIDENCED",
    ]:
        machine.transition(state)
    assert machine.current_state == "EVIDENCED"


def test_lifecycle_illegal_transition_fail_closed() -> None:
    machine = OrderLifecycleStateMachineV1()
    with pytest.raises(OrderLifecycleTransitionError, match="ILLEGAL_LIFECYCLE_TRANSITION"):
        machine.transition("FILLED")


def test_lifecycle_terminal_immutable() -> None:
    proof = prove_order_lifecycle_state_machine_v1()
    assert proof["ok"] is True
    assert proof["TERMINAL_STATE_IMMUTABLE"] is True


def test_deterministic_client_order_id() -> None:
    a = derive_client_order_id_v1(
        intent_id="i1",
        order_plan_id="p1",
        trading_epoch="e1",
        instrument_id="X",
        side="LONG",
        intent_action="ENTER_LONG",
    )
    b = derive_client_order_id_v1(
        intent_id="i1",
        order_plan_id="p1",
        trading_epoch="e1",
        instrument_id="X",
        side="LONG",
        intent_action="ENTER_LONG",
    )
    c = derive_client_order_id_v1(
        intent_id="i2",
        order_plan_id="p1",
        trading_epoch="e1",
        instrument_id="X",
        side="LONG",
        intent_action="ENTER_LONG",
    )
    assert a == b
    assert a != c
    assert a.startswith("pt-coid-")


def test_idempotency_and_duplicate_prevention() -> None:
    registry = SubmissionIdempotencyRegistryV1()
    coid = "pt-coid-demo"
    first = registry.claim_submission(coid, {"qty": "1"})
    replay = registry.claim_submission(coid, {"qty": "1"})
    assert first["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    with pytest.raises(ValueError, match="DUPLICATE_ORDER_CONFLICTING_PAYLOAD"):
        registry.claim_submission(coid, {"qty": "9"})
    assert registry.apply_fill("f1")["applied"] is True
    assert registry.apply_fill("f1")["applied"] is False


def test_unknown_submit_semantics_no_blind_retry_no_exchange_access() -> None:
    semantics = UnknownSubmitSemanticsV1()
    blind = semantics.evaluate_retry_admissibility(exchange_query_completed=False, blind_retry=True)
    gated = semantics.evaluate_retry_admissibility(exchange_query_completed=True, blind_retry=False)
    assert blind["admissible"] is False
    assert gated["admissible"] is True
    assert gated["exchange_access_performed"] is False
    proof = prove_client_order_id_and_submission_semantics_v1()
    assert proof["ok"] is True
    assert proof["EXCHANGE_ACCESS_IN_CAPABILITY_11_1"] is False


def test_adapter_anti_corruption_negative() -> None:
    proof = prove_adapter_anti_corruption_v1()
    assert proof["ok"] is True
    assert proof["NO_EXECUTION_ADAPTER_DECISION_AUTHORITY"] is True
    assert proof["may_alter_risk_result"] is False
    assert proof["may_alter_safety_result"] is False


def test_testnet_live_mode_boundary_negative_reachability() -> None:
    assert declare_testnet_execution_port_v1().REACHABLE is False
    assert declare_live_execution_port_v1().REACHABLE is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_testnet_execution_port_v1()
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()
    ports = prove_mode_specific_execution_boundary_v1()
    assert ports["ok"] is True
    assert ports["TESTNET_EXECUTION_REACHABLE"] is False
    assert ports["LIVE_EXECUTION_REACHABLE"] is False
    reach = prove_negative_reachability_v1()
    assert reach["ok"] is True
    assert reach["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False
    assert reach["EXCHANGE_ORDER_SUBMIT_REACHABLE"] is False
    assert reach["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert reach["NETWORK_SESSION_STARTED"] is False
    assert reach["REAL_CAPITAL_MOVEMENT_REACHABLE"] is False


def test_core_logic_parity_simulated_execution_port() -> None:
    proof = prove_core_logic_parity_with_simulated_port_v1()
    assert proof["ok"] is True
    assert proof["CORE_LOGIC_CHANGE"] is False
    assert isinstance(prove_mode_specific_execution_boundary_v1()["simulated_port_kind"], str)
    assert proof["after"]["PORT_KIND"] == SimulatedExecutionPortV1.PORT_KIND


def test_state_ownership_and_atomicity_contracts() -> None:
    ownership = prove_state_ownership_matrix_v1()
    atomicity = prove_order_portfolio_atomicity_contract_v1()
    assert ownership["ok"] is True
    assert atomicity["ok"] is True
    assert atomicity["ORDER_AND_PORTFOLIO_STATE_ATOMIC_OR_JOURNALED"] is True


def test_failure_injection_contract_violations_only() -> None:
    machine = OrderLifecycleStateMachineV1()
    machine.transition("ORDER_PLAN_CREATED")
    with pytest.raises(OrderLifecycleTransitionError):
        machine.mark_blind_retry_attempt()
    with pytest.raises(OrderLifecycleTransitionError):
        machine.transition("EVIDENCED")


def test_capability_verifier_pass() -> None:
    result = verify_capability_11_1_v1()
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    claims = result["claims"]
    assert claims["CORE_LOGIC_CHANGE"] is False
    assert claims["ACTIVATION_STATE"] == "not_activated"
    assert claims["TESTNET_AUTHORIZED"] is False
    assert claims["LIVE_AUTHORIZED"] is False
    assert claims["SIMULATED_EXECUTION_PORT_RETAINED"] is True
