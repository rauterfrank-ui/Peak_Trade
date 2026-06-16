"""Offline tests for order_capability_killswitch_abort_binding_contract_v1.

Class-4 scoped: no network, credentials, orders, or Testnet execute.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.order_capability_killswitch_abort_binding_contract_v1 import (
    FORBIDDEN_SERIALIZATION_KEYS,
    PACKAGE_MARKER,
    REASON_ABORT_ACK_NOT_CONFIRMED,
    REASON_CORRELATION_MISMATCH,
    REASON_KILLSWITCH_STATE_UNKNOWN,
    REASON_KILLSWITCH_TRIPPED,
    REASON_LIVE_ENVIRONMENT_REJECTED,
    REASON_MISSING_EVIDENCE_CORRELATION,
    REASON_MISSING_KILLSWITCH_SOURCE,
    REASON_PAYLOAD_UNSAFE_FLAGS,
    REASON_STALE_KILLSWITCH_SOURCE,
    REASON_TOKEN_MISMATCH,
    OrderCapabilityAbortBindingInput,
    OrderCapabilityBindingVerdict,
    OrderCapabilityKillSwitchSnapshot,
    OrderCapabilityPayloadSafetySummary,
    evaluate_order_capability_abort_binding,
    serialize_order_capability_abort_binding_verdict,
)

CONTRACT_MODULE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "ops"
    / "order_capability_killswitch_abort_binding_contract_v1.py"
)
RISK_LAYER_DIR = Path(__file__).resolve().parents[2] / "src" / "risk_layer" / "kill_switch"
EXECUTION_DIR = Path(__file__).resolve().parents[2] / "src" / "execution"

TEST_PACKAGE_MARKER = "ORDER_CAPABILITY_KILLSWITCH_ABORT_BINDING_CONTRACT_V1_TEST=true"
OPERATOR_GO_BINDING = "GO_ORDER_CAPABILITY_KILLSWITCH_ABORT_BINDING_CONTRACT_IMPL_V1"
CORRELATION_ID = "ev-test-binding-001"
NOW_UTC = "2026-06-09T13:00:00Z"
OBSERVED_UTC = "2026-06-09T12:59:30Z"


def _valid_snapshot(**overrides: object) -> OrderCapabilityKillSwitchSnapshot:
    base = {
        "source": "offline_fixture",
        "source_id": "ks-fixture-001",
        "source_kind": "injected_offline_fixture",
        "state": "OK",
        "observed_at_utc": OBSERVED_UTC,
        "ttl_seconds": 120,
        "correlation_id": CORRELATION_ID,
        "environment": "demo_testnet_only",
    }
    base.update(overrides)
    return OrderCapabilityKillSwitchSnapshot(**base)


def _valid_payload(**overrides: object) -> OrderCapabilityPayloadSafetySummary:
    base = {
        "evidence_correlation_id": CORRELATION_ID,
        "no_submit": True,
        "no_network": True,
        "execute_authorized": False,
        "order_submission_executed": False,
        "cancel_executed": False,
        "trade_position_mutation_executed": False,
        "abort_ack_marker": "CONFIRMED",
        "operator_go_token_binding": OPERATOR_GO_BINDING,
        "environment": "demo_testnet_only",
    }
    base.update(overrides)
    return OrderCapabilityPayloadSafetySummary(**base)


def _valid_input(**overrides: object) -> OrderCapabilityAbortBindingInput:
    base = {
        "payload_summary": _valid_payload(),
        "expected_operator_go_token_binding": OPERATOR_GO_BINDING,
        "kill_switch_snapshot": _valid_snapshot(),
        "now_utc": NOW_UTC,
        "expected_environment": "demo_testnet_only",
    }
    base.update(overrides)
    if "payload_summary" not in overrides and any(key.startswith("payload_") for key in overrides):
        payload_overrides = {
            key.removeprefix("payload_"): value
            for key, value in overrides.items()
            if key.startswith("payload_")
        }
        base["payload_summary"] = _valid_payload(**payload_overrides)
    if "snapshot_" in "".join(overrides):
        snapshot_overrides = {
            key.removeprefix("snapshot_"): value
            for key, value in overrides.items()
            if key.startswith("snapshot_")
        }
        base["kill_switch_snapshot"] = _valid_snapshot(**snapshot_overrides)
    return OrderCapabilityAbortBindingInput(**base)


def test_package_marker_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_happy_path_pass_for_dry_submit_candidate_only_without_execute_authority() -> None:
    verdict = evaluate_order_capability_abort_binding(_valid_input())
    assert verdict.verdict == OrderCapabilityBindingVerdict.PASS_FOR_DRY_SUBMIT_CANDIDATE_ONLY
    assert verdict.reason_codes == ()
    assert verdict.execute_authorized is False
    assert verdict.no_authority_change is True
    assert verdict.preflight_remains_blocked is True


def test_default_missing_snapshot_source_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(kill_switch_snapshot=_valid_snapshot(source=""))
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_MISSING_KILLSWITCH_SOURCE in verdict.reason_codes


def test_stale_source_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(
            kill_switch_snapshot=_valid_snapshot(
                observed_at_utc="2026-06-09T11:00:00Z",
                ttl_seconds=60,
            )
        )
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_STALE_KILLSWITCH_SOURCE in verdict.reason_codes


def test_tripped_killswitch_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(kill_switch_snapshot=_valid_snapshot(state="TRIPPED"))
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_KILLSWITCH_TRIPPED in verdict.reason_codes


def test_unknown_state_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(kill_switch_snapshot=_valid_snapshot(state="UNKNOWN"))
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_KILLSWITCH_STATE_UNKNOWN in verdict.reason_codes


@pytest.mark.parametrize("environment", ["live", "prod", "mainnet", "production"])
def test_live_prod_mainnet_environment_rejected(environment: str) -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(payload_summary=_valid_payload(environment=environment))
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_LIVE_ENVIRONMENT_REJECTED in verdict.reason_codes


def test_missing_operator_token_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(payload_summary=_valid_payload(operator_go_token_binding=""))
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_TOKEN_MISMATCH in verdict.reason_codes


def test_mismatch_operator_token_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(expected_operator_go_token_binding="GO_OTHER_TOKEN")
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_TOKEN_MISMATCH in verdict.reason_codes


def test_abort_ack_marker_not_confirmed_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(payload_summary=_valid_payload(abort_ack_marker="PENDING"))
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_ABORT_ACK_NOT_CONFIRMED in verdict.reason_codes


def test_payload_no_submit_false_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(payload_summary=_valid_payload(no_submit=False))
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_PAYLOAD_UNSAFE_FLAGS in verdict.reason_codes


def test_payload_no_network_false_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(payload_summary=_valid_payload(no_network=False))
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_PAYLOAD_UNSAFE_FLAGS in verdict.reason_codes


def test_payload_execute_authorized_true_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(payload_summary=_valid_payload(execute_authorized=True))
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_PAYLOAD_UNSAFE_FLAGS in verdict.reason_codes


def test_payload_order_submission_executed_true_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(payload_summary=_valid_payload(order_submission_executed=True))
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_PAYLOAD_UNSAFE_FLAGS in verdict.reason_codes


def test_payload_cancel_executed_true_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(payload_summary=_valid_payload(cancel_executed=True))
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_PAYLOAD_UNSAFE_FLAGS in verdict.reason_codes


def test_payload_trade_position_mutation_executed_true_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(payload_summary=_valid_payload(trade_position_mutation_executed=True))
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_PAYLOAD_UNSAFE_FLAGS in verdict.reason_codes


def test_correlation_mismatch_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(
            payload_summary=_valid_payload(evidence_correlation_id="ev-a"),
            kill_switch_snapshot=_valid_snapshot(correlation_id="ev-b"),
        )
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_CORRELATION_MISMATCH in verdict.reason_codes


def test_missing_evidence_correlation_fail_closed() -> None:
    verdict = evaluate_order_capability_abort_binding(
        _valid_input(payload_summary=_valid_payload(evidence_correlation_id=""))
    )
    assert verdict.verdict == OrderCapabilityBindingVerdict.FAIL_CLOSED
    assert REASON_MISSING_EVIDENCE_CORRELATION in verdict.reason_codes


def test_serialization_excludes_secrets_and_contains_safety_flags() -> None:
    verdict = evaluate_order_capability_abort_binding(_valid_input())
    data = serialize_order_capability_abort_binding_verdict(verdict)
    for key in data:
        assert key.lower() not in FORBIDDEN_SERIALIZATION_KEYS
    assert data["no_submit"] is True
    assert data["no_network"] is True
    assert data["execute_authorized"] is False
    assert data["no_authority_change"] is True
    assert data["preflight_remains_blocked"] is True


def test_no_imports_from_risk_layer_or_execution() -> None:
    source = CONTRACT_MODULE.read_text(encoding="utf-8")
    assert "from src.risk_layer.kill_switch" not in source
    assert "import src.risk_layer.kill_switch" not in source
    assert "from src.execution" not in source
    assert "import src.execution" not in source
    test_import_block = Path(__file__).read_text(encoding="utf-8").split("def ")[0]
    assert "from src.risk_layer.kill_switch" not in test_import_block
    assert "from src.execution" not in test_import_block


def test_deterministic_stable_output_for_same_input() -> None:
    inp = _valid_input()
    first = evaluate_order_capability_abort_binding(inp)
    second = evaluate_order_capability_abort_binding(inp)
    assert first == second
    assert serialize_order_capability_abort_binding_verdict(first) == (
        serialize_order_capability_abort_binding_verdict(second)
    )


def test_armed_safe_and_clear_states_pass() -> None:
    for state in ("ARMED_SAFE", "CLEAR"):
        verdict = evaluate_order_capability_abort_binding(
            _valid_input(kill_switch_snapshot=_valid_snapshot(state=state))
        )
        assert verdict.verdict == OrderCapabilityBindingVerdict.PASS_FOR_DRY_SUBMIT_CANDIDATE_ONLY
