"""Tests for Cap 11 §11.12.3 single controlled order lifecycle."""

from __future__ import annotations

import pytest

from src.ops.capability_11_section_11_12_3_single_controlled_order_lifecycle_v1.constants_v1 import (
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_13_STARTED,
    LIFECYCLE_NETWORK_EFFECT,
    LIFECYCLE_PATH_NAME,
    NETWORK_WRITES_AUTHORIZED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    PATH_CLASS,
    SECTION_11_12_4_STARTED,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
)
from src.ops.capability_11_section_11_12_3_single_controlled_order_lifecycle_v1.section_11_12_3_v1 import (
    Section11123SingleControlledOrderLifecycleError,
    execute_section_11_12_3_single_controlled_order_lifecycle_v1,
    mark_section_11_12_2_predecessor_bound_v1,
    prove_section_11_12_3_single_controlled_order_lifecycle_v1,
    refuse_cap_11_4_adapter_activation_v1,
    refuse_cap_11_13_live_activation_v1,
    refuse_network_submit_v1,
    refuse_network_write_v1,
    refuse_order_send_v1,
    refuse_section_11_12_4_v1,
    reuse_cap_11_4_single_controlled_order_lifecycle_v1,
)
from src.ops.capability_11_section_11_12_3_single_controlled_order_lifecycle_v1.verifier_v1 import (
    verify_capability_11_section_11_12_3_single_controlled_order_lifecycle_v1,
)

_SHA = "2de0a4973e726f56c74a881f327130cc73706b17"
_CFG = "cfg-" + ("d" * 64)


def _complete_kwargs(**overrides):
    bound, pred_digest, pred_serialization = mark_section_11_12_2_predecessor_bound_v1(
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
        "section_11_12_2_predecessor_bound": bound,
        "section_11_12_2_execution_binding_digest": pred_digest,
        "section_11_12_2_serialization_digest": pred_serialization,
        "client_order_id": "pt-coid-section-11-12-3-test",
    }
    base.update(overrides)
    return base


def test_productive_single_controlled_lifecycle_binds_predecessor() -> None:
    record = execute_section_11_12_3_single_controlled_order_lifecycle_v1(**_complete_kwargs())
    assert record.single_controlled_order_lifecycle_performed is True
    assert record.cap_11_4_single_controlled_lifecycle_contract_reused is True
    assert record.network_effect == "NONE"
    assert record.exchange_submit_performed is False
    assert record.lifecycle_source == "FIXTURE_ONLY"
    assert record.path_name == LIFECYCLE_PATH_NAME
    assert record.terminal_state == "EVIDENCED"
    assert record.path_class == PATH_CLASS
    assert record.order_send_disabled is True
    assert record.orders_authorized is False
    assert record.network_writes_authorized is False
    assert record.network_write_performed is False
    assert record.exchange_order_submit_reachable is False
    assert record.testnet_order_submit_performed is False
    assert record.cap_11_4_adapter_activated is False
    assert record.section_11_12_4_started is False
    assert record.cap_11_13_started is False
    assert record.testnet_order_lifecycle_proven is False
    assert record.reference_only is False
    assert bool(record.history)
    assert bool(record.execution_binding_digest)
    assert bool(record.section_11_12_2_serialization_digest)
    assert ORDER_SEND_DISABLED is True
    assert ORDERS_AUTHORIZED is False
    assert NETWORK_WRITES_AUTHORIZED is False
    assert LIFECYCLE_NETWORK_EFFECT == "NONE"
    assert TESTNET_ORDER_LIFECYCLE_PROVEN is False


def test_incomplete_preconditions_fail_closed() -> None:
    with pytest.raises(
        Section11123SingleControlledOrderLifecycleError, match="SECTION_11_12_3_NOT_ADMISSIBLE"
    ):
        execute_section_11_12_3_single_controlled_order_lifecycle_v1(
            **_complete_kwargs(section_11_12_2_predecessor_bound=False)
        )


def test_order_send_and_network_writes_hard_rejected() -> None:
    with pytest.raises(
        Section11123SingleControlledOrderLifecycleError, match="ORDER_SEND_MUST_REMAIN_DISABLED"
    ):
        execute_section_11_12_3_single_controlled_order_lifecycle_v1(
            **_complete_kwargs(order_send_disabled=False)
        )
    with pytest.raises(
        Section11123SingleControlledOrderLifecycleError, match="ORDER_SEND_MUST_REMAIN_DISABLED"
    ):
        execute_section_11_12_3_single_controlled_order_lifecycle_v1(
            **_complete_kwargs(orders_authorized=True)
        )
    with pytest.raises(
        Section11123SingleControlledOrderLifecycleError, match="NETWORK_WRITES_FORBIDDEN"
    ):
        execute_section_11_12_3_single_controlled_order_lifecycle_v1(
            **_complete_kwargs(network_writes_authorized=True)
        )


def test_cap_11_4_reuse_negatives_and_path_refusal() -> None:
    with pytest.raises(
        Section11123SingleControlledOrderLifecycleError, match="SECTION_11_12_3_PATH_FORBIDDEN"
    ):
        reuse_cap_11_4_single_controlled_order_lifecycle_v1(path_name="entry_lifecycle")
    with pytest.raises(
        Section11123SingleControlledOrderLifecycleError, match="SECTION_11_12_3_PATH_FORBIDDEN"
    ):
        reuse_cap_11_4_single_controlled_order_lifecycle_v1(path_name="cancel_lifecycle")
    life = reuse_cap_11_4_single_controlled_order_lifecycle_v1()
    assert life.path_name == LIFECYCLE_PATH_NAME
    assert life.terminal_state == "EVIDENCED"
    assert life.network_effect == "NONE"
    assert life.exchange_submit_performed is False


def test_downstream_and_activation_refusals() -> None:
    with pytest.raises(
        Section11123SingleControlledOrderLifecycleError, match="ORDER_SEND_FORBIDDEN"
    ):
        refuse_order_send_v1()
    with pytest.raises(
        Section11123SingleControlledOrderLifecycleError, match="NETWORK_WRITE_FORBIDDEN"
    ):
        refuse_network_write_v1(method="POST")
    with pytest.raises(
        Section11123SingleControlledOrderLifecycleError, match="NETWORK_SUBMIT_FORBIDDEN"
    ):
        refuse_network_submit_v1()
    with pytest.raises(Section11123SingleControlledOrderLifecycleError, match="SECTION_11_12_4"):
        refuse_section_11_12_4_v1(path_name="entry_lifecycle")
    with pytest.raises(
        Section11123SingleControlledOrderLifecycleError,
        match="CAPABILITY_11_4_TESTNET_ADAPTER_ACTIVATION_FORBIDDEN",
    ):
        refuse_cap_11_4_adapter_activation_v1()
    with pytest.raises(
        Section11123SingleControlledOrderLifecycleError,
        match="CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN",
    ):
        refuse_cap_11_13_live_activation_v1()
    assert CAPABILITY_11_4_STARTED is False
    assert SECTION_11_12_4_STARTED is False
    assert CAPABILITY_11_13_STARTED is False


def test_prove_and_verifier_pass() -> None:
    proof = prove_section_11_12_3_single_controlled_order_lifecycle_v1()
    assert proof["ok"] is True
    assert proof["single_controlled_order_lifecycle_performed"] is True
    assert proof["cap_11_4_single_controlled_lifecycle_contract_reused"] is True
    assert proof["network_effect"] == "NONE"
    assert proof["exchange_submit_performed"] is False
    assert proof["section_11_12_4_started"] is False
    assert proof["testnet_order_lifecycle_proven"] is False
    verification = verify_capability_11_section_11_12_3_single_controlled_order_lifecycle_v1()
    assert verification["ok"] is True
    assert verification["VERIFIER_RESULT"] == "PASS"
    assert verification["claims"]["ORDER_SEND_DISABLED"] is True
    assert verification["claims"]["ORDERS_AUTHORIZED"] is False
    assert verification["claims"]["NETWORK_WRITES_AUTHORIZED"] is False
    assert verification["claims"]["NETWORK_WRITE_PERFORMED"] is False
    assert verification["claims"]["SINGLE_CONTROLLED_ORDER_LIFECYCLE_PERFORMED"] is True
    assert verification["claims"]["SECTION_11_12_4_STARTED"] is False
    assert verification["claims"]["CAPABILITY_11_13_STARTED"] is False
    assert verification["claims"]["CAPABILITY_11_4_STARTED"] is False
    assert verification["claims"]["TESTNET_ORDER_LIFECYCLE_PROVEN"] is False
    assert verification["claims"]["NETWORK_EFFECT"] == "NONE"
