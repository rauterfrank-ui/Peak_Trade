"""Offline tests for order_capability_cancel_cleanup_failclosed_contract_v1.

Class-4 scoped: no network, credentials, orders, or Testnet execute.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.order_capability_cancel_cleanup_failclosed_contract_v1 import (
    ABORT_BINDING_PASS_VERDICT,
    DEFAULT_CLEANUP_PLACEHOLDER_MARKER,
    FORBIDDEN_SERIALIZATION_KEYS,
    PACKAGE_MARKER,
    REASON_ABORT_BINDING_NOT_READY,
    REASON_CANCEL_CLEANUP_PLACEHOLDER_NOT_VALIDATED,
    REASON_CLEANUP_TOKEN_MISMATCH,
    REASON_CORRELATION_MISMATCH,
    REASON_ENDPOINT_BOUNDARY_NOT_SATISFIED,
    REASON_FILLED_STATE_REQUIRES_FLATTEN,
    REASON_IDEMPOTENCY_MISMATCH,
    REASON_LIVE_ENVIRONMENT_REJECTED,
    REASON_MISSING_CLEANUP_CORRELATION_MARKER,
    REASON_MISSING_EVIDENCE_CORRELATION,
    REASON_MISSING_ORDER_STATE_SOURCE,
    REASON_MISSING_PAYLOAD_CORRELATION,
    REASON_PARTIAL_FILL_WITHOUT_NO_MUTATION_POLICY,
    REASON_STALE_ORDER_STATE_SNAPSHOT,
    REASON_UNSAFE_PAYLOAD_OR_BINDING_FLAGS,
    REASON_UNKNOWN_ORDER_STATE,
    OrderCapabilityAbortBindingSummary,
    OrderCapabilityCleanupInput,
    OrderCapabilityCleanupPolicy,
    OrderCapabilityCleanupOrderStateSnapshot,
    OrderCapabilityCleanupVerdictKind,
    OrderCapabilityPayloadCleanupSummary,
    evaluate_order_capability_cancel_cleanup,
    serialize_order_capability_cleanup_verdict,
    validate_order_capability_cleanup_verdict,
)

CONTRACT_MODULE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "ops"
    / "order_capability_cancel_cleanup_failclosed_contract_v1.py"
)
EXECUTION_DIR = Path(__file__).resolve().parents[2] / "src" / "execution"
RISK_LAYER_DIR = Path(__file__).resolve().parents[2] / "src" / "risk_layer" / "kill_switch"

TEST_PACKAGE_MARKER = "ORDER_CAPABILITY_CANCEL_CLEANUP_FAILCLOSED_CONTRACT_V1_TEST=true"
OPERATOR_GO_BINDING = "GO_ORDER_CAPABILITY_CANCEL_CLEANUP_FAILCLOSED_CONTRACT_IMPL_V1"
CORRELATION_ID = "ev-test-cleanup-001"
CLIENT_ORDER_ID = "ocpb-test-client-001"
IDEMPOTENCY_KEY = "ocpb-test-client-001"
VALID_CLEANUP_MARKER = "cleanup-correlation-derived-from-idempotency-v1"
NOW_UTC = "2026-06-09T14:58:00Z"
OBSERVED_UTC = "2026-06-09T14:57:30Z"


def _valid_payload(**overrides: object) -> OrderCapabilityPayloadCleanupSummary:
    base = {
        "evidence_correlation_id": CORRELATION_ID,
        "client_order_id": CLIENT_ORDER_ID,
        "idempotency_key": IDEMPOTENCY_KEY,
        "cleanup_cancel_correlation_marker": VALID_CLEANUP_MARKER,
        "operator_go_token_binding": OPERATOR_GO_BINDING,
        "environment": "demo_testnet_only",
        "no_submit": True,
        "no_network": True,
        "execute_authorized": False,
        "cancel_executed": False,
        "trade_position_mutation_executed": False,
    }
    base.update(overrides)
    return OrderCapabilityPayloadCleanupSummary(**base)


def _valid_binding(**overrides: object) -> OrderCapabilityAbortBindingSummary:
    base = {
        "verdict": ABORT_BINDING_PASS_VERDICT,
        "evidence_correlation_id": CORRELATION_ID,
        "reason_codes": (),
        "execute_authorized": False,
        "cancel_executed": False,
    }
    base.update(overrides)
    return OrderCapabilityAbortBindingSummary(**base)


def _valid_snapshot(**overrides: object) -> OrderCapabilityCleanupOrderStateSnapshot:
    base = {
        "source_id": "order-state-fixture-001",
        "source_kind": "injected_offline_fixture",
        "order_state": "CANCELLED",
        "observed_at_utc": OBSERVED_UTC,
        "ttl_seconds": 120,
        "environment": "demo_testnet_only",
        "instrument": "PF_XBTUSD",
        "client_order_id": CLIENT_ORDER_ID,
        "idempotency_key": IDEMPOTENCY_KEY,
        "evidence_correlation_id": CORRELATION_ID,
        "filled_quantity": 0.0,
        "remaining_quantity": 0.0,
    }
    base.update(overrides)
    return OrderCapabilityCleanupOrderStateSnapshot(**base)


def _valid_input(**overrides: object) -> OrderCapabilityCleanupInput:
    base = {
        "payload_summary": _valid_payload(),
        "abort_binding_summary": _valid_binding(),
        "order_state_snapshot": _valid_snapshot(),
        "cleanup_policy": OrderCapabilityCleanupPolicy(),
        "operator_cleanup_go_token_binding": OPERATOR_GO_BINDING,
        "expected_operator_cleanup_go_token_binding": OPERATOR_GO_BINDING,
        "expected_environment": "demo_testnet_only",
        "now_utc": NOW_UTC,
        "private_endpoint_boundary_satisfied": True,
    }
    base.update(overrides)
    return OrderCapabilityCleanupInput(**base)


def test_package_marker_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_ready_for_dry_cleanup_plan_only_happy_path() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(_valid_input())
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.READY_FOR_DRY_CLEANUP_PLAN_ONLY
    assert verdict.reason_codes == ()
    assert verdict.cancel_authorized is False
    assert verdict.flatten_authorized is False
    assert verdict.execute_authorized is False
    assert verdict.order_submission_executed is False
    assert verdict.cancel_executed is False
    assert verdict.trade_position_mutation_executed is False
    assert verdict.no_authority_change is True
    assert verdict.preflight_remains_blocked is True
    assert verdict.dry_cleanup_plan_id.startswith("occc-dryplan-")


def test_fail_missing_payload_correlation() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(payload_summary=_valid_payload(client_order_id=""))
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_MISSING_PAYLOAD_CORRELATION in verdict.reason_codes


def test_fail_abort_binding_missing() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(abort_binding_summary=_valid_binding(verdict=""))
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_ABORT_BINDING_NOT_READY in verdict.reason_codes


def test_fail_abort_binding_not_pass() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(abort_binding_summary=_valid_binding(verdict="FAIL_CLOSED"))
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_ABORT_BINDING_NOT_READY in verdict.reason_codes


def test_fail_missing_order_state_source() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(order_state_snapshot=_valid_snapshot(source_id=""))
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_MISSING_ORDER_STATE_SOURCE in verdict.reason_codes


def test_fail_stale_snapshot() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(
            order_state_snapshot=_valid_snapshot(
                observed_at_utc="2026-06-09T12:00:00Z",
                ttl_seconds=60,
            )
        )
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_STALE_ORDER_STATE_SNAPSHOT in verdict.reason_codes


@pytest.mark.parametrize("environment", ["live", "prod", "mainnet", "production"])
def test_fail_live_environment(environment: str) -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(payload_summary=_valid_payload(environment=environment))
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_LIVE_ENVIRONMENT_REJECTED in verdict.reason_codes


def test_fail_cleanup_token_mismatch() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(expected_operator_cleanup_go_token_binding="GO_OTHER_TOKEN")
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_CLEANUP_TOKEN_MISMATCH in verdict.reason_codes


def test_fail_missing_cleanup_correlation_marker() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(payload_summary=_valid_payload(cleanup_cancel_correlation_marker=""))
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_MISSING_CLEANUP_CORRELATION_MARKER in verdict.reason_codes


def test_fail_endpoint_boundary_unsatisfied() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(private_endpoint_boundary_satisfied=False)
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_ENDPOINT_BOUNDARY_NOT_SATISFIED in verdict.reason_codes


def test_fail_unknown_order_state() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(order_state_snapshot=_valid_snapshot(order_state="UNKNOWN"))
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_UNKNOWN_ORDER_STATE in verdict.reason_codes


def test_fail_partial_fill_without_policy() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(
            order_state_snapshot=_valid_snapshot(
                order_state="PARTIALLY_FILLED",
                filled_quantity=0.01,
                remaining_quantity=0.01,
            )
        )
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_PARTIAL_FILL_WITHOUT_NO_MUTATION_POLICY in verdict.reason_codes


def test_fail_filled_state_requires_flatten() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(order_state_snapshot=_valid_snapshot(order_state="FILLED"))
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_FILLED_STATE_REQUIRES_FLATTEN in verdict.reason_codes


def test_fail_correlation_mismatch() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(
            payload_summary=_valid_payload(evidence_correlation_id="ev-a"),
            abort_binding_summary=_valid_binding(evidence_correlation_id="ev-b"),
        )
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_CORRELATION_MISMATCH in verdict.reason_codes


def test_fail_idempotency_mismatch() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(
            payload_summary=_valid_payload(idempotency_key="idem-a"),
            order_state_snapshot=_valid_snapshot(idempotency_key="idem-b"),
        )
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_IDEMPOTENCY_MISMATCH in verdict.reason_codes


def test_fail_missing_evidence_correlation() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(payload_summary=_valid_payload(evidence_correlation_id=""))
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_MISSING_EVIDENCE_CORRELATION in verdict.reason_codes


def test_fail_payload_unsafe_flags() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(payload_summary=_valid_payload(no_submit=False))
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_UNSAFE_PAYLOAD_OR_BINDING_FLAGS in verdict.reason_codes


def test_fail_cleanup_marker_placeholder() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(
        _valid_input(
            payload_summary=_valid_payload(
                cleanup_cancel_correlation_marker=DEFAULT_CLEANUP_PLACEHOLDER_MARKER
            )
        )
    )
    assert verdict.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_CANCEL_CLEANUP_PLACEHOLDER_NOT_VALIDATED in verdict.reason_codes


def test_serialization_excludes_secrets_and_contains_safety_flags() -> None:
    verdict = evaluate_order_capability_cancel_cleanup(_valid_input())
    data = serialize_order_capability_cleanup_verdict(verdict)
    for key in data:
        assert key.lower() not in FORBIDDEN_SERIALIZATION_KEYS
    assert data["no_submit"] is True
    assert data["no_network"] is True
    assert data["cancel_authorized"] is False
    assert data["flatten_authorized"] is False
    assert data["execute_authorized"] is False
    assert data["no_authority_change"] is True
    assert data["preflight_remains_blocked"] is True
    validate_order_capability_cleanup_verdict(verdict)


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
    first = evaluate_order_capability_cancel_cleanup(inp)
    second = evaluate_order_capability_cancel_cleanup(inp)
    assert first == second
    assert serialize_order_capability_cleanup_verdict(first) == (
        serialize_order_capability_cleanup_verdict(second)
    )
