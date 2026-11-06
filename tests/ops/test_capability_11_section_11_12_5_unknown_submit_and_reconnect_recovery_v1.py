"""Tests for Cap 11 §11.12.5 unknown-submit and reconnect recovery."""

from __future__ import annotations

import pytest

from src.ops.capability_11_section_11_12_5_unknown_submit_and_reconnect_recovery_v1.constants_v1 import (
    ALLOWED_SECTION_11_12_5_PATHS,
    CAPABILITY_11_5_STARTED,
    CAPABILITY_11_13_STARTED,
    LIFECYCLE_NETWORK_EFFECT,
    NETWORK_WRITES_AUTHORIZED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    PATH_CLASS,
    SECTION_11_12_6_STARTED,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
    TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
)
from src.ops.capability_11_section_11_12_5_unknown_submit_and_reconnect_recovery_v1.section_11_12_5_v1 import (
    Section11125UnknownSubmitAndReconnectRecoveryError,
    execute_section_11_12_5_unknown_submit_and_reconnect_recovery_v1,
    mark_section_11_12_4_predecessor_bound_v1,
    prove_section_11_12_5_unknown_submit_and_reconnect_recovery_v1,
    refuse_blind_retry_v1,
    refuse_cap_11_5_adapter_activation_v1,
    refuse_cap_11_13_live_activation_v1,
    refuse_network_reconnect_activation_v1,
    refuse_network_submit_v1,
    refuse_network_write_v1,
    refuse_order_send_v1,
    refuse_section_11_12_6_v1,
    reuse_cap_11_5_section_11_12_5_recovery_path_v1,
)
from src.ops.capability_11_section_11_12_5_unknown_submit_and_reconnect_recovery_v1.verifier_v1 import (
    verify_capability_11_section_11_12_5_unknown_submit_and_reconnect_recovery_v1,
)

_SHA = "2de0a4973e726f56c74a881f327130cc73706b17"
_CFG = "cfg-" + ("d" * 64)


def _complete_kwargs(**overrides):
    bound, pred_digest = mark_section_11_12_4_predecessor_bound_v1(
        repository_sha=_SHA, config_digest=_CFG
    )
    base = {
        "runtime_mode": "TESTNET",
        "venue": "OKX",
        "account_identity": "acct-uid-demo",
        "instrument_scope": ("BTC-USDT-SWAP",),
        "repository_sha": _SHA,
        "config_digest": _CFG,
        "expected_repository_sha": _SHA,
        "expected_config_digest": _CFG,
        "expected_account_identity": "acct-uid-demo",
        "expected_venue": "OKX",
        "section_11_12_4_predecessor_bound": bound,
        "section_11_12_4_execution_binding_digest": pred_digest,
        "client_order_id_prefix": "pt-coid-section-11-12-5-test",
    }
    base.update(overrides)
    return base


def test_productive_unknown_submit_reconnect_binds_predecessor() -> None:
    record = execute_section_11_12_5_unknown_submit_and_reconnect_recovery_v1(**_complete_kwargs())
    assert record.unknown_submit_and_reconnect_recovery_performed is True
    assert record.cap_11_5_unknown_submit_reconnect_contract_reused is True
    assert record.network_effect == "NONE"
    assert record.exchange_submit_performed is False
    assert record.lifecycle_source == "FIXTURE_ONLY"
    assert record.paths_completed == ALLOWED_SECTION_11_12_5_PATHS
    assert len(record.path_results) == 2
    assert all(r.terminal_state == "EVIDENCED" for r in record.path_results)
    assert all(r.network_effect == "NONE" for r in record.path_results)
    assert all(r.exchange_submit_performed is False for r in record.path_results)
    assert all(r.exchange_query_completed is True for r in record.path_results)
    assert all(r.blind_retry_blocked is True for r in record.path_results)
    assert all("UNKNOWN" in r.history for r in record.path_results)
    assert record.path_class == PATH_CLASS
    assert record.order_send_disabled is True
    assert record.orders_authorized is False
    assert record.network_writes_authorized is False
    assert record.network_write_performed is False
    assert record.exchange_order_submit_reachable is False
    assert record.testnet_order_submit_performed is False
    assert record.cap_11_5_adapter_activated is False
    assert record.section_11_12_6_started is False
    assert record.cap_11_13_started is False
    assert record.testnet_order_lifecycle_proven is False
    assert record.testnet_unknown_submit_recovery_proven is False
    assert record.reference_only is False
    assert bool(record.execution_binding_digest)
    assert bool(record.section_11_12_4_execution_binding_digest)
    assert ORDER_SEND_DISABLED is True
    assert ORDERS_AUTHORIZED is False
    assert NETWORK_WRITES_AUTHORIZED is False
    assert LIFECYCLE_NETWORK_EFFECT == "NONE"
    assert TESTNET_ORDER_LIFECYCLE_PROVEN is False
    assert TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN is False


def test_incomplete_preconditions_fail_closed() -> None:
    with pytest.raises(
        Section11125UnknownSubmitAndReconnectRecoveryError,
        match="SECTION_11_12_5_NOT_ADMISSIBLE",
    ):
        execute_section_11_12_5_unknown_submit_and_reconnect_recovery_v1(
            **_complete_kwargs(section_11_12_4_predecessor_bound=False)
        )


def test_order_send_and_network_writes_hard_rejected() -> None:
    with pytest.raises(
        Section11125UnknownSubmitAndReconnectRecoveryError,
        match="ORDER_SEND_MUST_REMAIN_DISABLED",
    ):
        execute_section_11_12_5_unknown_submit_and_reconnect_recovery_v1(
            **_complete_kwargs(order_send_disabled=False)
        )
    with pytest.raises(
        Section11125UnknownSubmitAndReconnectRecoveryError,
        match="ORDER_SEND_MUST_REMAIN_DISABLED",
    ):
        execute_section_11_12_5_unknown_submit_and_reconnect_recovery_v1(
            **_complete_kwargs(orders_authorized=True)
        )
    with pytest.raises(
        Section11125UnknownSubmitAndReconnectRecoveryError,
        match="NETWORK_WRITES_FORBIDDEN",
    ):
        execute_section_11_12_5_unknown_submit_and_reconnect_recovery_v1(
            **_complete_kwargs(network_writes_authorized=True)
        )


def test_cap_11_5_reuse_negatives_and_path_refusal() -> None:
    with pytest.raises(
        Section11125UnknownSubmitAndReconnectRecoveryError,
        match="SECTION_11_12_5_PATH_FORBIDDEN",
    ):
        reuse_cap_11_5_section_11_12_5_recovery_path_v1(path_name="restart_with_open_order")
    with pytest.raises(
        Section11125UnknownSubmitAndReconnectRecoveryError,
        match="SECTION_11_12_5_PATH_FORBIDDEN",
    ):
        reuse_cap_11_5_section_11_12_5_recovery_path_v1(path_name="entry_lifecycle")
    for path_name in ALLOWED_SECTION_11_12_5_PATHS:
        life = reuse_cap_11_5_section_11_12_5_recovery_path_v1(path_name=path_name)
        assert life.path_name == path_name
        assert life.terminal_state == "EVIDENCED"
        assert life.network_effect == "NONE"
        assert life.exchange_submit_performed is False
        assert life.exchange_query_completed is True
        assert life.blind_retry_blocked is True
        assert "UNKNOWN" in life.history


def test_downstream_and_activation_refusals() -> None:
    with pytest.raises(
        Section11125UnknownSubmitAndReconnectRecoveryError, match="ORDER_SEND_FORBIDDEN"
    ):
        refuse_order_send_v1()
    with pytest.raises(
        Section11125UnknownSubmitAndReconnectRecoveryError, match="NETWORK_WRITE_FORBIDDEN"
    ):
        refuse_network_write_v1(method="POST")
    with pytest.raises(
        Section11125UnknownSubmitAndReconnectRecoveryError, match="NETWORK_SUBMIT_FORBIDDEN"
    ):
        refuse_network_submit_v1()
    with pytest.raises(
        Section11125UnknownSubmitAndReconnectRecoveryError,
        match="UNKNOWN_SUBMIT_BLIND_RETRY_FORBIDDEN",
    ):
        refuse_blind_retry_v1(client_order_id="pt-coid-blind")
    with pytest.raises(
        Section11125UnknownSubmitAndReconnectRecoveryError,
        match="UNKNOWN_SUBMIT_NETWORK_RECONNECT_ACTIVATION_FORBIDDEN",
    ):
        refuse_network_reconnect_activation_v1(session_id="session-reconnect")
    with pytest.raises(Section11125UnknownSubmitAndReconnectRecoveryError, match="SECTION_11_12_6"):
        refuse_section_11_12_6_v1(path_name="restart_with_open_order")
    with pytest.raises(
        Section11125UnknownSubmitAndReconnectRecoveryError,
        match="CAPABILITY_11_5_TESTNET_ADAPTER_ACTIVATION_FORBIDDEN",
    ):
        refuse_cap_11_5_adapter_activation_v1()
    with pytest.raises(
        Section11125UnknownSubmitAndReconnectRecoveryError,
        match="CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN",
    ):
        refuse_cap_11_13_live_activation_v1()
    assert CAPABILITY_11_5_STARTED is False
    assert SECTION_11_12_6_STARTED is False
    assert CAPABILITY_11_13_STARTED is False


def test_prove_and_verifier_pass() -> None:
    proof = prove_section_11_12_5_unknown_submit_and_reconnect_recovery_v1()
    assert proof["ok"] is True
    assert proof["unknown_submit_and_reconnect_recovery_performed"] is True
    assert proof["cap_11_5_unknown_submit_reconnect_contract_reused"] is True
    assert proof["network_effect"] == "NONE"
    assert proof["exchange_submit_performed"] is False
    assert proof["section_11_12_6_started"] is False
    assert proof["testnet_order_lifecycle_proven"] is False
    assert proof["testnet_unknown_submit_recovery_proven"] is False
    assert proof["paths_completed"] == list(ALLOWED_SECTION_11_12_5_PATHS)
    verification = verify_capability_11_section_11_12_5_unknown_submit_and_reconnect_recovery_v1()
    assert verification["ok"] is True
    assert verification["VERIFIER_RESULT"] == "PASS"
    assert verification["claims"]["ORDER_SEND_DISABLED"] is True
    assert verification["claims"]["ORDERS_AUTHORIZED"] is False
    assert verification["claims"]["NETWORK_WRITES_AUTHORIZED"] is False
    assert verification["claims"]["NETWORK_WRITE_PERFORMED"] is False
    assert verification["claims"]["UNKNOWN_SUBMIT_AND_RECONNECT_RECOVERY_PERFORMED"] is True
    assert verification["claims"]["SECTION_11_12_6_STARTED"] is False
    assert verification["claims"]["CAPABILITY_11_13_STARTED"] is False
    assert verification["claims"]["CAPABILITY_11_5_STARTED"] is False
    assert verification["claims"]["TESTNET_ORDER_LIFECYCLE_PROVEN"] is False
    assert verification["claims"]["TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN"] is False
    assert verification["claims"]["BLIND_RETRY_BLOCKED"] is True
    assert verification["claims"]["RECONNECT_ACTIVATION_BLOCKED"] is True
    assert verification["claims"]["NETWORK_EFFECT"] == "NONE"
