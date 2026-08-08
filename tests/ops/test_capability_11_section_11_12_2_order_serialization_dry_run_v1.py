"""Tests for Cap 11 §11.12.2 order serialization dry-run."""

from __future__ import annotations

import pytest

from src.ops.capability_11_section_11_12_2_order_serialization_dry_run_v1.constants_v1 import (
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_13_STARTED,
    NETWORK_WRITES_AUTHORIZED,
    ORDER_SEND_DISABLED,
    ORDER_SERIALIZATION_NETWORK_EFFECT,
    ORDERS_AUTHORIZED,
    PATH_CLASS,
    SECTION_11_12_3_STARTED,
)
from src.ops.capability_11_section_11_12_2_order_serialization_dry_run_v1.section_11_12_2_v1 import (
    Section11122OrderSerializationDryRunError,
    execute_section_11_12_2_order_serialization_dry_run_v1,
    mark_section_11_12_1_predecessor_bound_v1,
    prove_section_11_12_2_order_serialization_dry_run_v1,
    refuse_cap_11_4_adapter_activation_v1,
    refuse_cap_11_13_live_activation_v1,
    refuse_network_submit_v1,
    refuse_network_write_v1,
    refuse_order_send_v1,
    refuse_section_11_12_3_v1,
    reuse_cap_11_4_order_serialization_dry_run_v1,
)
from src.ops.capability_11_section_11_12_2_order_serialization_dry_run_v1.verifier_v1 import (
    verify_capability_11_section_11_12_2_order_serialization_dry_run_v1,
)

_SHA = "74024d06470df7d44e186e02f47ec4dc38bb92c1"
_CFG = "cfg-" + ("c" * 64)


def _complete_kwargs(**overrides):
    bound, pred_digest, pred_identity = mark_section_11_12_1_predecessor_bound_v1(
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
        "section_11_12_1_predecessor_bound": bound,
        "section_11_12_1_execution_binding_digest": pred_digest,
        "section_11_12_1_account_identity_observed": pred_identity,
        "client_order_id": "pt-coid-section-11-12-2-test",
    }
    base.update(overrides)
    return base


def test_productive_order_serialization_dry_run_binds_predecessor() -> None:
    record = execute_section_11_12_2_order_serialization_dry_run_v1(**_complete_kwargs())
    assert record.order_serialization_dry_run_performed is True
    assert record.cap_11_4_order_serialization_contract_reused is True
    assert record.network_effect == "NONE"
    assert record.submitted is False
    assert record.serialization_source == "FIXTURE_ONLY"
    assert record.venue_native_payload.get("dry_run") is True
    assert record.path_class == PATH_CLASS
    assert record.order_send_disabled is True
    assert record.orders_authorized is False
    assert record.network_writes_authorized is False
    assert record.network_write_performed is False
    assert record.exchange_order_submit_reachable is False
    assert record.testnet_order_submit_performed is False
    assert record.cap_11_4_adapter_activated is False
    assert record.section_11_12_3_started is False
    assert record.cap_11_13_started is False
    assert record.reference_only is False
    assert record.section_11_12_1_account_identity_observed == "acct-uid-demo"
    assert bool(record.serialization_digest)
    assert bool(record.execution_binding_digest)
    assert ORDER_SEND_DISABLED is True
    assert ORDERS_AUTHORIZED is False
    assert NETWORK_WRITES_AUTHORIZED is False
    assert ORDER_SERIALIZATION_NETWORK_EFFECT == "NONE"


def test_incomplete_preconditions_fail_closed() -> None:
    with pytest.raises(
        Section11122OrderSerializationDryRunError, match="SECTION_11_12_2_NOT_ADMISSIBLE"
    ):
        execute_section_11_12_2_order_serialization_dry_run_v1(
            **_complete_kwargs(section_11_12_1_predecessor_bound=False)
        )


def test_order_send_and_network_writes_hard_rejected() -> None:
    with pytest.raises(
        Section11122OrderSerializationDryRunError, match="ORDER_SEND_MUST_REMAIN_DISABLED"
    ):
        execute_section_11_12_2_order_serialization_dry_run_v1(
            **_complete_kwargs(order_send_disabled=False)
        )
    with pytest.raises(
        Section11122OrderSerializationDryRunError, match="ORDER_SEND_MUST_REMAIN_DISABLED"
    ):
        execute_section_11_12_2_order_serialization_dry_run_v1(
            **_complete_kwargs(orders_authorized=True)
        )
    with pytest.raises(Section11122OrderSerializationDryRunError, match="NETWORK_WRITES_FORBIDDEN"):
        execute_section_11_12_2_order_serialization_dry_run_v1(
            **_complete_kwargs(network_writes_authorized=True)
        )


def test_cap_11_4_reuse_negatives_and_submit_refusal() -> None:
    with pytest.raises(Section11122OrderSerializationDryRunError, match="NON_FIXTURE"):
        reuse_cap_11_4_order_serialization_dry_run_v1(
            client_order_id="pt-coid-bad",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            source="LIVE_NETWORK",
        )
    with pytest.raises(
        Section11122OrderSerializationDryRunError, match="ORDER_SERIALIZATION_FIELD_MISSING"
    ):
        reuse_cap_11_4_order_serialization_dry_run_v1(
            client_order_id="",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
        )
    ser = reuse_cap_11_4_order_serialization_dry_run_v1(
        client_order_id="pt-coid-submit-refuse",
        instrument_id="BTC-USDT-SWAP",
        side="BUY",
        order_type="LIMIT",
        quantity="1",
    )
    with pytest.raises(Section11122OrderSerializationDryRunError, match="NETWORK_SUBMIT_FORBIDDEN"):
        refuse_network_submit_v1(record=ser)


def test_downstream_and_activation_refusals() -> None:
    with pytest.raises(Section11122OrderSerializationDryRunError, match="ORDER_SEND_FORBIDDEN"):
        refuse_order_send_v1()
    with pytest.raises(Section11122OrderSerializationDryRunError, match="NETWORK_WRITE_FORBIDDEN"):
        refuse_network_write_v1(method="POST")
    with pytest.raises(Section11122OrderSerializationDryRunError, match="SECTION_11_12_3"):
        refuse_section_11_12_3_v1()
    with pytest.raises(
        Section11122OrderSerializationDryRunError,
        match="CAPABILITY_11_4_TESTNET_ADAPTER_ACTIVATION_FORBIDDEN",
    ):
        refuse_cap_11_4_adapter_activation_v1()
    with pytest.raises(
        Section11122OrderSerializationDryRunError,
        match="CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN",
    ):
        refuse_cap_11_13_live_activation_v1()
    assert CAPABILITY_11_4_STARTED is False
    assert SECTION_11_12_3_STARTED is False
    assert CAPABILITY_11_13_STARTED is False


def test_prove_and_verifier_pass() -> None:
    proof = prove_section_11_12_2_order_serialization_dry_run_v1()
    assert proof["ok"] is True
    assert proof["order_serialization_dry_run_performed"] is True
    assert proof["cap_11_4_order_serialization_contract_reused"] is True
    assert proof["network_effect"] == "NONE"
    assert proof["submitted"] is False
    assert proof["section_11_12_3_started"] is False
    verification = verify_capability_11_section_11_12_2_order_serialization_dry_run_v1()
    assert verification["ok"] is True
    assert verification["VERIFIER_RESULT"] == "PASS"
    assert verification["claims"]["ORDER_SEND_DISABLED"] is True
    assert verification["claims"]["ORDERS_AUTHORIZED"] is False
    assert verification["claims"]["NETWORK_WRITES_AUTHORIZED"] is False
    assert verification["claims"]["NETWORK_WRITE_PERFORMED"] is False
    assert verification["claims"]["ORDER_SERIALIZATION_DRY_RUN_PERFORMED"] is True
    assert verification["claims"]["SECTION_11_12_3_STARTED"] is False
    assert verification["claims"]["CAPABILITY_11_13_STARTED"] is False
    assert verification["claims"]["CAPABILITY_11_4_STARTED"] is False
