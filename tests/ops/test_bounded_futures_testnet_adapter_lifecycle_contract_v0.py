"""Static + offline bounded Futures Testnet adapter lifecycle contract (v0, PE-12).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Planning: bounded_futures_testnet_adapter_lifecycle_major_package_phase1_no_run_v1_20260617T040357Z
"""

from __future__ import annotations

from pathlib import Path

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    LIFECYCLE_EXECUTE_AUTHORIZED_NOW,
    LIFECYCLE_NETWORK_AUTHORIZED_NOW,
    LIFECYCLE_ORDERS_AUTHORIZED_NOW,
    LIFECYCLE_PHASE_ORDER,
    NETWORK_EXECUTION_PHASES,
    OPERATOR_GO_PRIVATE_READONLY,
    OPERATOR_GO_STATIC_PREFLIGHT,
    OPERATOR_GO_TINY_ORDER,
    OPERATOR_GO_ZERO_ORDER,
    PACKAGE_MARKER,
    PHASE_PRIVATE_READONLY,
    PHASE_READINESS_DECISION,
    PHASE_STATIC_PREFLIGHT,
    PHASE_TINY_ORDER,
    PHASE_ZERO_ORDER,
    PREFLIGHT_REMAINS_BLOCKED,
    READY_FOR_OPERATOR_ARMING,
    AdapterLifecycleState,
    PhaseTransitionRequest,
    default_blocked_lifecycle_state,
    evaluate_pe_contract_composition,
    evaluate_phase_transition,
    mark_phase_completed,
    mark_reconciliation_completed,
    validate_lifecycle_instrument_binding,
)
from src.ops.bounded_futures_testnet_contract_v0 import FUTURES_SESSION_AUTHORIZED_NOW

REPO_ROOT = Path(__file__).resolve().parents[2]
LIFECYCLE_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_adapter_lifecycle_contract_v0.py"
)
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
ADAPTER_TEST = REPO_ROOT / "tests" / "ops" / "test_bounded_futures_testnet_adapter_contract_v0.py"
HARNESS_TEST = REPO_ROOT / "tests" / "ops" / "test_bounded_futures_testnet_harness_contract_v0.py"
RUNTIME_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_bounded_futures_testnet_runtime_harness_contract_v0.py"
)
PRIVATE_READONLY_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_bounded_futures_private_readonly_contract_v0.py"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_ADAPTER_LIFECYCLE_CONTRACT_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_ADAPTER_LIFECYCLE_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
PLANNING_BUNDLE_SUFFIX = (
    "bounded_futures_testnet_adapter_lifecycle_major_package_phase1_no_run_v1_20260617T040357Z"
)


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in LIFECYCLE_MODULE.read_text(encoding="utf-8")


def test_lifecycle_guards_remain_blocked() -> None:
    assert LIFECYCLE_EXECUTE_AUTHORIZED_NOW is False
    assert LIFECYCLE_NETWORK_AUTHORIZED_NOW is False
    assert LIFECYCLE_ORDERS_AUTHORIZED_NOW is False
    assert PREFLIGHT_REMAINS_BLOCKED is True
    assert READY_FOR_OPERATOR_ARMING is False
    assert FUTURES_SESSION_AUTHORIZED_NOW is False


def test_lifecycle_phase_order_matches_pe12_contract() -> None:
    assert LIFECYCLE_PHASE_ORDER == (
        "static_preflight",
        "zero_order",
        "private_readonly",
        "validate_only",
        "tiny_order",
        "reconciliation_review",
        "readiness_decision",
    )
    assert NETWORK_EXECUTION_PHASES == frozenset(
        {"zero_order", "private_readonly", "validate_only", "tiny_order"}
    )


def test_pe_composition_passes_offline() -> None:
    result = evaluate_pe_contract_composition()
    assert result["pe_composition_pass"] is True
    assert result["pe8_adapter_pass"] is True
    assert result["pe9_harness_pass"] is True
    assert result["pe10_runtime_pass"] is True
    assert result["fail_reasons"] == []


def test_static_preflight_transition_from_blocked_default() -> None:
    state = default_blocked_lifecycle_state()
    request = PhaseTransitionRequest(
        target_phase=PHASE_STATIC_PREFLIGHT,
        operator_go_token=OPERATOR_GO_STATIC_PREFLIGHT,
        static_contract_self_check_pass=True,
    )
    result = evaluate_phase_transition(state, request)
    assert result["transition_allowed"] is True
    assert result["fail_reasons"] == []


def test_zero_order_requires_static_preflight_and_rejects_wrong_go() -> None:
    state = default_blocked_lifecycle_state()
    request = PhaseTransitionRequest(
        target_phase=PHASE_ZERO_ORDER,
        operator_go_token=OPERATOR_GO_STATIC_PREFLIGHT,
    )
    result = evaluate_phase_transition(state, request)
    assert result["transition_allowed"] is False
    assert any("prior phase not completed" in r for r in result["fail_reasons"])


def test_phase_skip_fails_for_private_readonly() -> None:
    state = mark_phase_completed(default_blocked_lifecycle_state(), PHASE_STATIC_PREFLIGHT)
    request = PhaseTransitionRequest(
        target_phase=PHASE_PRIVATE_READONLY,
        operator_go_token=OPERATOR_GO_PRIVATE_READONLY,
    )
    result = evaluate_phase_transition(state, request)
    assert result["transition_allowed"] is False
    assert any("prior phase not completed" in r for r in result["fail_reasons"])


def test_private_readonly_requires_zero_order_reconciliation() -> None:
    state = default_blocked_lifecycle_state()
    state = mark_phase_completed(state, PHASE_STATIC_PREFLIGHT)
    state = mark_phase_completed(state, PHASE_ZERO_ORDER)
    request = PhaseTransitionRequest(
        target_phase=PHASE_PRIVATE_READONLY,
        operator_go_token=OPERATOR_GO_PRIVATE_READONLY,
    )
    result = evaluate_phase_transition(state, request)
    assert result["transition_allowed"] is False
    assert any("reconciliation required" in r for r in result["fail_reasons"])


def test_private_readonly_passes_after_zero_order_reconciliation() -> None:
    state = default_blocked_lifecycle_state()
    state = mark_phase_completed(state, PHASE_STATIC_PREFLIGHT)
    state = mark_phase_completed(state, PHASE_ZERO_ORDER)
    state = mark_reconciliation_completed(state, PHASE_ZERO_ORDER)
    request = PhaseTransitionRequest(
        target_phase=PHASE_PRIVATE_READONLY,
        operator_go_token=OPERATOR_GO_PRIVATE_READONLY,
    )
    result = evaluate_phase_transition(state, request)
    assert result["transition_allowed"] is True


def test_tiny_order_requires_risk_flatten_and_durable_pe() -> None:
    state = _state_through_validate_only_reconciled()
    request = PhaseTransitionRequest(
        target_phase=PHASE_TINY_ORDER,
        operator_go_token=OPERATOR_GO_TINY_ORDER,
    )
    result = evaluate_phase_transition(state, request)
    assert result["transition_allowed"] is False
    assert "risk_killswitch_binding_acknowledged required" in result["fail_reasons"]
    assert "flatten_binding_acknowledged required" in result["fail_reasons"]
    assert "durable_primary_evidence_capable required" in result["fail_reasons"]


def test_readiness_decision_always_non_authorizing() -> None:
    state = _state_through_reconciliation_review()
    request = PhaseTransitionRequest(
        target_phase=PHASE_READINESS_DECISION,
        operator_go_token="GO_BOUNDED_FUTURES_TESTNET_READINESS_DECISION_V0",
        manifest_verify_rc_zero=True,
    )
    result = evaluate_phase_transition(state, request)
    assert result["transition_allowed"] is False
    assert any("non-authorizing" in r for r in result["fail_reasons"])


def test_rejected_instrument_fails_binding() -> None:
    reasons = validate_lifecycle_instrument_binding("BTCUSDT", "futures")
    assert reasons


def test_spot_market_type_fails_binding() -> None:
    reasons = validate_lifecycle_instrument_binding("PF_ETHUSD", "spot")
    assert any("market_type" in r for r in reasons)


def test_pe8_pe9_pe10_pe11_tests_crosslink() -> None:
    assert ADAPTER_TEST.is_file()
    assert HARNESS_TEST.is_file()
    assert RUNTIME_TEST.is_file()
    assert PRIVATE_READONLY_TEST.is_file()


def test_section5_pe12_crosslink_present() -> None:
    section5 = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_adapter_lifecycle_contract_v0" in section5
    assert "PE-12 guard" in section5


def test_ci_audit_pe12_crosslink_present() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert "PE-12 Bounded Futures Testnet adapter lifecycle" in ci_audit
    assert "bounded_futures_testnet_adapter_lifecycle_contract_v0" in ci_audit


def test_planning_bundle_suffix_documented_in_test() -> None:
    assert PLANNING_BUNDLE_SUFFIX in Path(__file__).read_text(encoding="utf-8")


def _state_through_validate_only_reconciled() -> AdapterLifecycleState:
    state = default_blocked_lifecycle_state()
    for phase in (
        PHASE_STATIC_PREFLIGHT,
        PHASE_ZERO_ORDER,
        PHASE_PRIVATE_READONLY,
        "validate_only",
    ):
        state = mark_phase_completed(state, phase)
        if phase in NETWORK_EXECUTION_PHASES:
            state = mark_reconciliation_completed(state, phase)
    return state


def _state_through_reconciliation_review() -> AdapterLifecycleState:
    state = _state_through_validate_only_reconciled()
    state = mark_phase_completed(state, PHASE_TINY_ORDER)
    state = mark_reconciliation_completed(state, PHASE_TINY_ORDER)
    state = mark_phase_completed(state, "reconciliation_review")
    return state
