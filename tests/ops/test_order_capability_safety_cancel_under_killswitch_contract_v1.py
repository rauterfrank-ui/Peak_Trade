"""Offline tests for order_capability_safety_cancel_under_killswitch_contract_v1.

Class-4 scoped: no network, credentials, orders, or Testnet execute.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.order_capability_safety_cancel_under_killswitch_contract_v1 import (
    AUTHORITY_IMPACT,
    FORBIDDEN_SERIALIZATION_KEYS,
    PACKAGE_MARKER,
    REASON_AMBIGUOUS_ORDER_STATE,
    REASON_FORBIDDEN_ENDPOINT_BATCHORDER,
    REASON_FORBIDDEN_ENDPOINT_CANCELALLORDERS,
    REASON_FORBIDDEN_METHOD_NOT_POST,
    REASON_INTENDED_ORDER_ID_MISMATCH,
    REASON_KILLSWITCH_NOT_TRIPPED,
    REASON_LIVE_ENVIRONMENT_REJECTED,
    REASON_MAX_CANCEL_ATTEMPTS_EXCEEDED,
    REASON_MISSING_EVIDENCE_CORRELATION,
    REASON_MISSING_INTENDED_ORDER_ID,
    REASON_SENDORDER_NOT_ACCEPTED,
    REASON_WRONG_LIFECYCLE_PHASE,
    OrderCapabilitySafetyCancelInput,
    OrderCapabilitySafetyCancelVerdictKind,
    evaluate_order_capability_safety_cancel_under_killswitch,
    serialize_order_capability_safety_cancel_verdict,
    validate_order_capability_safety_cancel_verdict,
)

CONTRACT_MODULE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "ops"
    / "order_capability_safety_cancel_under_killswitch_contract_v1.py"
)
EXECUTION_DIR = Path(__file__).resolve().parents[2] / "src" / "execution"
RISK_LAYER_DIR = Path(__file__).resolve().parents[2] / "src" / "risk_layer" / "kill_switch"

TEST_PACKAGE_MARKER = "ORDER_CAPABILITY_SAFETY_CANCEL_UNDER_KILLSWITCH_CONTRACT_V1_TEST=true"
CORRELATION_ID = "ev-test-safety-cancel-001"
INTENDED_ORDER_ID = "ocpb-test-client-001"


def _valid_input(**overrides: object) -> OrderCapabilitySafetyCancelInput:
    base = {
        "lifecycle_phase": "post_sendorder_cleanup",
        "sendorder_accepted": True,
        "killswitch_state": "TRIPPED",
        "intended_order_id": INTENDED_ORDER_ID,
        "requested_order_id": INTENDED_ORDER_ID,
        "endpoint": "/cancelorder",
        "method": "POST",
        "cancel_attempts": 1,
        "evidence_correlation_present": True,
        "evidence_correlation_id": CORRELATION_ID,
        "environment": "demo_testnet_only",
        "order_state": "SUBMITTED",
        "cancelallorders": False,
        "batchorder": False,
    }
    base.update(overrides)
    return OrderCapabilitySafetyCancelInput(**base)


def test_package_marker_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_ready_safety_cancel_happy_path_tripped_intended_order() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(_valid_input())
    assert (
        verdict.status
        == OrderCapabilitySafetyCancelVerdictKind.READY_FOR_DRY_SAFETY_CANCEL_PLAN_ONLY
    )
    assert verdict.reason_codes == ()
    assert verdict.dry_safety_cancel_plan_candidate is True
    assert verdict.intended_order_id_binding_verified is True
    assert verdict.forbidden_endpoint_detected is False
    assert verdict.evidence_required is True
    assert verdict.authority_impact == AUTHORITY_IMPACT
    assert verdict.dry_safety_cancel_plan_id.startswith("ocsc-dryplan-")


def test_fail_tripped_missing_intended_order_id() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(
        _valid_input(intended_order_id="", requested_order_id="")
    )
    assert verdict.status == OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED
    assert REASON_MISSING_INTENDED_ORDER_ID in verdict.reason_codes


def test_fail_tripped_mismatched_order_id() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(
        _valid_input(requested_order_id="ocpb-other-order-002")
    )
    assert verdict.status == OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED
    assert REASON_INTENDED_ORDER_ID_MISMATCH in verdict.reason_codes


def test_fail_tripped_cancelallorders_endpoint() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(
        _valid_input(endpoint="/cancelallorders", cancelallorders=True)
    )
    assert verdict.status == OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED
    assert REASON_FORBIDDEN_ENDPOINT_CANCELALLORDERS in verdict.reason_codes
    assert verdict.forbidden_endpoint_detected is True


def test_fail_tripped_batchorder_endpoint() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(
        _valid_input(endpoint="/batchorder", batchorder=True)
    )
    assert verdict.status == OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED
    assert REASON_FORBIDDEN_ENDPOINT_BATCHORDER in verdict.reason_codes
    assert verdict.forbidden_endpoint_detected is True


def test_fail_max_cancel_attempts_exceeded() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(
        _valid_input(cancel_attempts=2)
    )
    assert verdict.status == OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED
    assert REASON_MAX_CANCEL_ATTEMPTS_EXCEEDED in verdict.reason_codes


def test_fail_missing_evidence_correlation() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(
        _valid_input(evidence_correlation_present=False, evidence_correlation_id="")
    )
    assert verdict.status == OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED
    assert REASON_MISSING_EVIDENCE_CORRELATION in verdict.reason_codes
    assert verdict.evidence_required is True


@pytest.mark.parametrize("environment", ["live", "prod", "mainnet", "production"])
def test_fail_live_environment(environment: str) -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(
        _valid_input(environment=environment)
    )
    assert verdict.status == OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED
    assert REASON_LIVE_ENVIRONMENT_REJECTED in verdict.reason_codes


def test_fail_ambiguous_order_state_unknown() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(
        _valid_input(order_state="UNKNOWN")
    )
    assert verdict.status == OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED
    assert REASON_AMBIGUOUS_ORDER_STATE in verdict.reason_codes


def test_fail_sendorder_not_accepted() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(
        _valid_input(sendorder_accepted=False)
    )
    assert verdict.status == OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED
    assert REASON_SENDORDER_NOT_ACCEPTED in verdict.reason_codes


def test_fail_wrong_lifecycle_phase() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(
        _valid_input(lifecycle_phase="pre_sendorder_validation")
    )
    assert verdict.status == OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED
    assert REASON_WRONG_LIFECYCLE_PHASE in verdict.reason_codes


def test_safety_flags_immutable_on_pass() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(_valid_input())
    assert verdict.cancel_authorized_now is False
    assert verdict.allowed_for_execute_now is False
    assert verdict.execute_authorized is False
    assert verdict.cancel_executed is False
    assert verdict.order_submission_executed is False
    assert verdict.no_authority_change is True
    assert verdict.preflight_remains_blocked is True
    assert verdict.live_ready is False
    assert verdict.dashboard_truth_granted is False
    validate_order_capability_safety_cancel_verdict(verdict)


def test_fail_method_not_post() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(_valid_input(method="GET"))
    assert verdict.status == OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED
    assert REASON_FORBIDDEN_METHOD_NOT_POST in verdict.reason_codes


def test_fail_killswitch_clear_not_safety_cancel_path() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(
        _valid_input(killswitch_state="CLEAR")
    )
    assert verdict.status == OrderCapabilitySafetyCancelVerdictKind.FAIL_CLOSED
    assert REASON_KILLSWITCH_NOT_TRIPPED in verdict.reason_codes


def test_serialization_excludes_secrets_and_contains_safety_flags() -> None:
    verdict = evaluate_order_capability_safety_cancel_under_killswitch(_valid_input())
    data = serialize_order_capability_safety_cancel_verdict(verdict)
    for key in data:
        assert key.lower() not in FORBIDDEN_SERIALIZATION_KEYS
    assert data["no_submit"] is True
    assert data["no_network"] is True
    assert data["cancel_authorized_now"] is False
    assert data["allowed_for_execute_now"] is False
    assert data["authority_impact"] == AUTHORITY_IMPACT
    assert data["no_authority_change"] is True
    assert data["preflight_remains_blocked"] is True


def test_no_imports_from_risk_layer_or_execution() -> None:
    source = CONTRACT_MODULE.read_text(encoding="utf-8")
    assert "from src.risk_layer.kill_switch" not in source
    assert "import src.risk_layer.kill_switch" not in source
    assert "from src.execution" not in source
    assert "import src.execution" not in source
    assert not EXECUTION_DIR.exists() or EXECUTION_DIR.is_dir()
    assert not RISK_LAYER_DIR.exists() or RISK_LAYER_DIR.is_dir()
    test_import_block = Path(__file__).read_text(encoding="utf-8").split("def ")[0]
    assert "from src.risk_layer.kill_switch" not in test_import_block
    assert "from src.execution" not in test_import_block


def test_deterministic_stable_output_for_same_input() -> None:
    inp = _valid_input()
    first = evaluate_order_capability_safety_cancel_under_killswitch(inp)
    second = evaluate_order_capability_safety_cancel_under_killswitch(inp)
    assert first == second
    assert serialize_order_capability_safety_cancel_verdict(first) == (
        serialize_order_capability_safety_cancel_verdict(second)
    )
