"""Tests for §11.12.8 productive campaign RUN CONSUMER."""

from __future__ import annotations

import pytest

from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.constants_v1 import (
    LIVE_ORDER_EFFECT,
    MODE_GOVERNED_RUN_CONSUMER_GATE,
    MODE_PROVE_RUN_CONSUMER_ONLY,
    NETWORK_EFFECT,
    NEW_WRAPPER_LAYER_CREATED,
    ORDER_EFFECT,
    PRODUCTIVE_RUN_CONSUMER_PRESENT,
    PRODUCTIVE_RUN_EXECUTION_AUTHORIZED,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    SECTION_11_13_STARTED,
)
from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.run_consumer_v1 import (
    Section11128RunConsumerError,
    build_section_11_12_8_run_consumer_record_v1,
    execute_section_11_12_8_productive_campaign_run_v1,
    prove_section_11_12_8_run_consumer_v1,
    refuse_cap_11_13_v1,
    refuse_credential_load_v1,
    refuse_live_path_v1,
    refuse_network_session_v1,
    refuse_order_submit_v1,
    refuse_productive_campaign_execution_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.verifier_v1 import (
    verify_section_11_12_8_run_consumer_v1,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.constants_v1 import (
    PRODUCTIVE_RUN_AUTHORIZED as TERMINAL_PRODUCTIVE_RUN_AUTHORIZED,
    TERMINAL_CONSUMER_CANONICAL_ROLE,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.terminal_consumer_v1 import (
    Section11128TerminalConsumerError,
    run_section_11_12_8_terminal_consumer_v1,
)

_SHA = "a" * 40
_CFG = "cfg-" + ("b" * 64)
_DIGEST = "c" * 64


def _complete(**overrides):
    base = {
        "repository_sha": _SHA,
        "config_digest": _CFG,
        "confirm_token_digest": _DIGEST,
        "expected_confirm_token_digest": _DIGEST,
        "owner_go_bound": True,
        "campaign_enabled": True,
        "campaign_armed": True,
    }
    base.update(overrides)
    return base


def test_prove_mode_never_may_arm() -> None:
    record = build_section_11_12_8_run_consumer_record_v1(
        mode=MODE_PROVE_RUN_CONSUMER_ONLY, **_complete()
    )
    assert record.run_consumer_may_arm is False
    assert record.campaign_started is False
    assert record.execution_authorized is False


def test_gate_may_arm_without_side_effects() -> None:
    record = build_section_11_12_8_run_consumer_record_v1(
        mode=MODE_GOVERNED_RUN_CONSUMER_GATE, **_complete()
    )
    assert record.run_consumer_may_arm is True
    assert record.run_consumer_present is True
    assert record.execution_authorized is False
    assert record.campaign_started is False
    assert record.network_effect == "NONE"
    assert record.order_effect == "NONE"
    assert record.live_order_effect == "NONE"
    assert record.credential_plaintext_loaded is False
    assert record.hidden_confirm_reused is True
    assert record.risk_gate_reused is True
    assert record.kill_switch_reused is True
    assert record.terminal_predecessor_bound is True
    assert record.terminal_role_unchanged is True
    assert record.new_wrapper_layer_created is False
    assert NEW_WRAPPER_LAYER_CREATED is False
    assert PRODUCTIVE_RUN_EXECUTION_AUTHORIZED is False
    assert PRODUCTIVE_RUN_CONSUMER_PRESENT is True
    assert PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False


def test_enabled_armed_fail_closed() -> None:
    assert (
        "campaign_enabled"
        in build_section_11_12_8_run_consumer_record_v1(
            mode=MODE_GOVERNED_RUN_CONSUMER_GATE,
            **_complete(campaign_enabled=False),
        ).missing_preconditions
    )
    assert (
        "campaign_armed"
        in build_section_11_12_8_run_consumer_record_v1(
            mode=MODE_GOVERNED_RUN_CONSUMER_GATE,
            **_complete(campaign_armed=False),
        ).missing_preconditions
    )
    assert (
        "owner_go_bound"
        in build_section_11_12_8_run_consumer_record_v1(
            mode=MODE_GOVERNED_RUN_CONSUMER_GATE,
            **_complete(owner_go_bound=False),
        ).missing_preconditions
    )


def test_live_path_blocked() -> None:
    missing = build_section_11_12_8_run_consumer_record_v1(
        mode=MODE_GOVERNED_RUN_CONSUMER_GATE,
        **_complete(runtime_mode="LIVE", live_endpoint_configured=True),
    ).missing_preconditions
    assert "testnet_only_scope" in missing
    assert "live_path_blocked" in missing


def test_kill_switch_blocks_gate() -> None:
    missing = build_section_11_12_8_run_consumer_record_v1(
        mode=MODE_GOVERNED_RUN_CONSUMER_GATE,
        **_complete(force_kill_switch_killed=True),
    ).missing_preconditions
    assert "kill_switch_operational" in missing or "risk_gate_allows" in missing


def test_terminal_hard_refuse_role_unchanged() -> None:
    assert TERMINAL_CONSUMER_CANONICAL_ROLE == "TERMINAL_PRODUCTIVE_CONSUMER_SECTION_11_12_8"
    assert TERMINAL_PRODUCTIVE_RUN_AUTHORIZED is False
    with pytest.raises(Section11128TerminalConsumerError, match="FORBIDDEN_IN_THIS_IMPLEMENTATION"):
        run_section_11_12_8_terminal_consumer_v1()


def test_entrypoint_and_refusals() -> None:
    with pytest.raises(Section11128RunConsumerError, match="FORBIDDEN_IN_THIS_IMPLEMENTATION"):
        execute_section_11_12_8_productive_campaign_run_v1()
    with pytest.raises(Section11128RunConsumerError, match="CAMPAIGN_RUN_EXECUTION_FORBIDDEN"):
        refuse_productive_campaign_execution_v1()
    with pytest.raises(Section11128RunConsumerError, match="NETWORK_SESSION_FORBIDDEN"):
        refuse_network_session_v1()
    with pytest.raises(Section11128RunConsumerError, match="ORDER_SUBMIT_FORBIDDEN"):
        refuse_order_submit_v1()
    with pytest.raises(Section11128RunConsumerError, match="LIVE_PATH_FORBIDDEN"):
        refuse_live_path_v1()
    with pytest.raises(Section11128RunConsumerError, match="CAPABILITY_11_13_FORBIDDEN"):
        refuse_cap_11_13_v1()
    with pytest.raises(Section11128RunConsumerError, match="CREDENTIAL_LOAD_FORBIDDEN"):
        refuse_credential_load_v1()


def test_prove_and_verifier() -> None:
    proof = prove_section_11_12_8_run_consumer_v1()
    assert proof["ok"] is True
    assert proof["PRODUCTIVE_RUN_CONSUMER_PRESENT"] is True
    assert proof["PRODUCTIVE_RUN_EXECUTION_AUTHORIZED"] is False
    assert proof["TERMINAL_CONSUMER_ROLE_UNCHANGED"] is True
    assert proof["NEW_WRAPPER_LAYER_CREATED"] is False
    assert proof["CREDENTIAL_PLAINTEXT_LOADED"] is False
    assert proof["NETWORK_EFFECT"] == NETWORK_EFFECT == "NONE"
    assert proof["ORDER_EFFECT"] == ORDER_EFFECT == "NONE"
    assert proof["LIVE_ORDER_EFFECT"] == LIVE_ORDER_EFFECT == "NONE"
    assert proof["SECTION_11_13_STARTED"] is False is SECTION_11_13_STARTED
    verification = verify_section_11_12_8_run_consumer_v1()
    assert verification["ok"] is True
    assert verification["claims"]["PRODUCTIVE_RUN_CONSUMER_PRESENT"] is True
    assert verification["claims"]["PRODUCTIVE_RUN_EXECUTION_AUTHORIZED"] is False
    assert verification["claims"]["TERMINAL_CONSUMER_ROLE_UNCHANGED"] is True
