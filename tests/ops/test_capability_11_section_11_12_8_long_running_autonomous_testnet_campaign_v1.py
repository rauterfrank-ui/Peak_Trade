"""Tests for Cap 11 §11.12.8 long-running autonomous Testnet campaign."""

from __future__ import annotations

import pytest

from src.ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.constants_v1 import (
    ALLOWED_SECTION_11_12_8_PATHS,
    CAPABILITY_11_6_STARTED,
    CAPABILITY_11_13_STARTED,
    KILL_SWITCH_BINDING_STATUS,
    KILL_SWITCH_CONTRACT_ACTIVATED,
    LIFECYCLE_NETWORK_EFFECT,
    NETWORK_WRITES_AUTHORIZED,
    ORDER_EFFECT,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    PATH_CLASS,
    SECTION_11_13_STARTED,
    TESTNET_CAMPAIGN_COMPLETED,
    TESTNET_CAMPAIGN_STARTED,
    TESTNET_EVIDENCE_VERIFIED,
    TESTNET_KILL_SWITCH_PROVEN,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
)
from src.ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.section_11_12_8_v1 import (
    Section11128LongRunningAutonomousTestnetCampaignError,
    execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1,
    mark_section_11_12_7_predecessor_bound_v1,
    prove_section_11_12_8_long_running_autonomous_testnet_campaign_v1,
    refuse_cap_11_6_adapter_activation_v1,
    refuse_cap_11_13_live_activation_v1,
    refuse_campaign_activation_v1,
    refuse_kill_switch_contract_activation_v1,
    refuse_kill_switch_runtime_clear_v1,
    refuse_kill_switch_side_effect_bypass_v1,
    refuse_network_submit_v1,
    refuse_network_write_v1,
    refuse_order_send_v1,
    refuse_scope_escalation_v1,
    refuse_testnet_campaign_network_session_v1,
    refuse_testnet_campaign_start_v1,
    refuse_testnet_proven_claim_v1,
    reuse_cap_11_6_section_11_12_8_campaign_path_v1,
)
from src.ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.verifier_v1 import (
    verify_capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1,
)

_SHA = "2de0a4973e726f56c74a881f327130cc73706b17"
_CFG = "cfg-" + ("d" * 64)


def _complete_kwargs(**overrides):
    bound, pred_digest = mark_section_11_12_7_predecessor_bound_v1(
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
        "section_11_12_7_predecessor_bound": bound,
        "section_11_12_7_execution_binding_digest": pred_digest,
        "client_order_id_prefix": "pt-coid-section-11-12-8-test",
    }
    base.update(overrides)
    return base


def test_productive_campaign_evidence_binds_predecessor() -> None:
    record = execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(
        **_complete_kwargs()
    )
    assert record.long_running_campaign_evidence_performed is True
    assert record.cap_11_6_long_running_campaign_evidence_contract_reused is True
    assert record.kill_switch_binding_status == "BOUND"
    assert record.network_effect == "NONE"
    assert record.order_effect == "NONE"
    assert record.exchange_submit_performed is False
    assert record.lifecycle_source == "FIXTURE_ONLY"
    assert record.paths_completed == ALLOWED_SECTION_11_12_8_PATHS
    assert len(record.path_results) == 3
    assert all(r.network_effect == "NONE" for r in record.path_results)
    assert all(r.exchange_submit_performed is False for r in record.path_results)
    assert all(r.campaign_activated is False for r in record.path_results)
    assert all(r.terminal_state == "EVIDENCED" for r in record.path_results)
    assert record.path_class == PATH_CLASS
    assert record.order_send_disabled is True
    assert record.orders_authorized is False
    assert record.network_writes_authorized is False
    assert record.network_write_performed is False
    assert record.exchange_order_submit_reachable is False
    assert record.testnet_order_submit_performed is False
    assert record.testnet_campaign_started is False
    assert record.testnet_campaign_completed is False
    assert record.campaign_activated is False
    assert record.network_session_started is False
    assert record.cap_11_6_adapter_activated is False
    assert record.kill_switch_contract_activated is False
    assert record.cap_11_13_started is False
    assert record.testnet_order_lifecycle_proven is False
    assert record.testnet_evidence_verified is False
    assert record.reference_only is False
    assert bool(record.execution_binding_digest)
    assert bool(record.section_11_12_7_execution_binding_digest)
    assert ORDER_SEND_DISABLED is True
    assert ORDERS_AUTHORIZED is False
    assert NETWORK_WRITES_AUTHORIZED is False
    assert LIFECYCLE_NETWORK_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"
    assert TESTNET_CAMPAIGN_STARTED is False
    assert TESTNET_CAMPAIGN_COMPLETED is False
    assert TESTNET_ORDER_LIFECYCLE_PROVEN is False
    assert TESTNET_KILL_SWITCH_PROVEN is False
    assert TESTNET_EVIDENCE_VERIFIED is False
    assert KILL_SWITCH_CONTRACT_ACTIVATED is False
    assert KILL_SWITCH_BINDING_STATUS == "BOUND"


def test_incomplete_preconditions_fail_closed() -> None:
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="SECTION_11_12_8_NOT_ADMISSIBLE",
    ):
        execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(
            **_complete_kwargs(section_11_12_7_predecessor_bound=False)
        )


def test_order_send_network_and_campaign_start_hard_rejected() -> None:
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="ORDER_SEND_MUST_REMAIN_DISABLED",
    ):
        execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(
            **_complete_kwargs(order_send_disabled=False)
        )
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="ORDER_SEND_MUST_REMAIN_DISABLED",
    ):
        execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(
            **_complete_kwargs(orders_authorized=True)
        )
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="NETWORK_WRITES_FORBIDDEN",
    ):
        execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(
            **_complete_kwargs(network_writes_authorized=True)
        )
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="TESTNET_CAMPAIGN_MUST_REMAIN_UNSTARTED",
    ):
        execute_section_11_12_8_long_running_autonomous_testnet_campaign_v1(
            **_complete_kwargs(testnet_campaign_started=True)
        )


def test_cap_11_6_reuse_negatives_and_path_refusal() -> None:
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="SECTION_11_12_8_PATH_FORBIDDEN",
    ):
        reuse_cap_11_6_section_11_12_8_campaign_path_v1(path_name="live_private_readonly_shadow")
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="SECTION_11_12_8_PATH_FORBIDDEN",
    ):
        reuse_cap_11_6_section_11_12_8_campaign_path_v1(
            path_name="productive_testnet_campaign_execution"
        )
    for path_name in ALLOWED_SECTION_11_12_8_PATHS:
        life = reuse_cap_11_6_section_11_12_8_campaign_path_v1(path_name=path_name)
        assert life.path_name == path_name
        assert life.campaign_activated is False
        assert life.exchange_submit_performed is False
        assert life.network_effect == "NONE"
        assert life.terminal_state == "EVIDENCED"


def test_runtime_gates_kill_switch_and_scope_escalation_refusals() -> None:
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError, match="ORDER_SEND_FORBIDDEN"
    ):
        refuse_order_send_v1()
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError, match="NETWORK_WRITE_FORBIDDEN"
    ):
        refuse_network_write_v1(method="POST")
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError, match="NETWORK_SUBMIT_FORBIDDEN"
    ):
        refuse_network_submit_v1()
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="TESTNET_CAMPAIGN_START_FORBIDDEN",
    ):
        refuse_testnet_campaign_start_v1(campaign_id="campaign-demo")
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="TESTNET_CAMPAIGN_NETWORK_SESSION_FORBIDDEN",
    ):
        refuse_testnet_campaign_network_session_v1(session_id="session-campaign")
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="CAMPAIGN_ACTIVATION_FORBIDDEN",
    ):
        refuse_campaign_activation_v1(campaign_id="campaign-demo")
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="KILL_SWITCH_RUNTIME_CLEAR_FORBIDDEN",
    ):
        refuse_kill_switch_runtime_clear_v1(actor="runtime_autonomy")
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="KILL_SWITCH_SIDE_EFFECT_BYPASS_FORBIDDEN",
    ):
        refuse_kill_switch_side_effect_bypass_v1(claimed_side_effect="order_submit")
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="SCOPE_ESCALATION_FORBIDDEN",
    ):
        refuse_scope_escalation_v1(claimed_scope="productive_testnet_campaign")
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="CAPABILITY_11_6_ADAPTER_ACTIVATION_FORBIDDEN",
    ):
        refuse_cap_11_6_adapter_activation_v1()
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="KILL_SWITCH_CONTRACT_ACTIVATION_FORBIDDEN",
    ):
        refuse_kill_switch_contract_activation_v1()
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN",
    ):
        refuse_cap_11_13_live_activation_v1(path_name="live_activation")
    with pytest.raises(
        Section11128LongRunningAutonomousTestnetCampaignError,
        match="TESTNET_PROVEN_OVERCLAIM_FORBIDDEN",
    ):
        refuse_testnet_proven_claim_v1(field_name="TESTNET_EVIDENCE_VERIFIED")
    assert CAPABILITY_11_6_STARTED is False
    assert CAPABILITY_11_13_STARTED is False
    assert SECTION_11_13_STARTED is False
    assert TESTNET_CAMPAIGN_STARTED is False
    assert TESTNET_CAMPAIGN_COMPLETED is False
    assert KILL_SWITCH_CONTRACT_ACTIVATED is False
    assert TESTNET_EVIDENCE_VERIFIED is False


def test_prove_and_verifier_pass() -> None:
    proof = prove_section_11_12_8_long_running_autonomous_testnet_campaign_v1()
    assert proof["ok"] is True
    assert proof["long_running_campaign_evidence_performed"] is True
    assert proof["cap_11_6_long_running_campaign_evidence_contract_reused"] is True
    assert proof["kill_switch_binding_status"] == "BOUND"
    assert proof["network_effect"] == "NONE"
    assert proof["order_effect"] == "NONE"
    assert proof["exchange_submit_performed"] is False
    assert proof["testnet_campaign_started"] is False
    assert proof["testnet_campaign_completed"] is False
    assert proof["campaign_activated"] is False
    assert proof["cap_11_13_started"] is False
    assert proof["testnet_evidence_verified"] is False
    assert proof["paths_completed"] == list(ALLOWED_SECTION_11_12_8_PATHS)
    verification = (
        verify_capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1()
    )
    assert verification["ok"] is True
    assert verification["VERIFIER_RESULT"] == "PASS"
    assert verification["claims"]["ORDER_SEND_DISABLED"] is True
    assert verification["claims"]["ORDERS_AUTHORIZED"] is False
    assert verification["claims"]["NETWORK_WRITES_AUTHORIZED"] is False
    assert verification["claims"]["NETWORK_WRITE_PERFORMED"] is False
    assert verification["claims"]["LONG_RUNNING_CAMPAIGN_EVIDENCE_PERFORMED"] is True
    assert verification["claims"]["TESTNET_CAMPAIGN_STARTED"] is False
    assert verification["claims"]["TESTNET_CAMPAIGN_COMPLETED"] is False
    assert verification["claims"]["CAPABILITY_11_13_STARTED"] is False
    assert verification["claims"]["SECTION_11_13_STARTED"] is False
    assert verification["claims"]["KILL_SWITCH_BINDING_STATUS"] == "BOUND"
    assert verification["claims"]["KILL_SWITCH_CONTRACT_ACTIVATED"] is False
    assert verification["claims"]["TESTNET_EVIDENCE_VERIFIED"] is False
    assert verification["claims"]["RUNTIME_CLEAR_BLOCKED"] is True
    assert verification["claims"]["SIDE_EFFECT_BYPASS_BLOCKED"] is True
    assert verification["claims"]["SCOPE_ESCALATION_BLOCKED"] is True
    assert verification["claims"]["CAMPAIGN_START_BLOCKED"] is True
    assert verification["claims"]["NETWORK_EFFECT"] == "NONE"
    assert verification["claims"]["ORDER_EFFECT"] == "NONE"
