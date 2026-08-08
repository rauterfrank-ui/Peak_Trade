"""Tests for Cap 11 §11.12.8 productive Testnet campaign run surface."""

from __future__ import annotations

import pytest

from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_v1.constants_v1 import (
    LIVE_ORDER_EFFECT,
    MODE_GOVERNED_RUN_GATE,
    MODE_PROVE_RUN_ONLY,
    NETWORK_EFFECT,
    ORDER_EFFECT,
    PRODUCTIVE_TESTNET_CAMPAIGN_RUN_IMPLEMENTED,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    RUN_AUTHORIZED,
    SECTION_11_13_STARTED,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_v1.run_v1 import (
    Productive11128CampaignRunError,
    build_productive_campaign_run_record_v1,
    execute_productive_testnet_campaign_run_v1,
    prove_productive_testnet_campaign_run_v1,
    refuse_cap_11_13_v1,
    refuse_campaign_start_v1,
    refuse_future_run_go_consume_v1,
    refuse_live_path_v1,
    refuse_network_session_v1,
    refuse_order_submit_v1,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_v1.verifier_v1 import (
    verify_capability_11_section_11_12_8_productive_testnet_campaign_run_v1,
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
        "run_authorized_ephemeral": True,
    }
    base.update(overrides)
    return base


def test_prove_mode_never_may_start() -> None:
    record = build_productive_campaign_run_record_v1(mode=MODE_PROVE_RUN_ONLY, **_complete())
    assert record.run_may_start is False
    assert record.campaign_started is False


def test_gate_may_start_but_does_not_run() -> None:
    record = build_productive_campaign_run_record_v1(mode=MODE_GOVERNED_RUN_GATE, **_complete())
    assert record.run_may_start is True
    assert record.campaign_started is False
    assert record.run_authorized_constant is False
    assert RUN_AUTHORIZED is False
    assert PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False
    assert PRODUCTIVE_TESTNET_CAMPAIGN_RUN_IMPLEMENTED is True
    assert record.network_effect == "NONE"
    assert record.order_effect == "NONE"
    assert record.live_order_effect == "NONE"
    assert record.execution_predecessor_bound is True
    assert record.execution_may_start is True


def test_negative_gates() -> None:
    assert (
        "run_authorized_ephemeral"
        in build_productive_campaign_run_record_v1(
            mode=MODE_GOVERNED_RUN_GATE,
            **_complete(run_authorized_ephemeral=False),
        ).missing_preconditions
    )
    assert (
        "testnet_only_scope"
        in build_productive_campaign_run_record_v1(
            mode=MODE_GOVERNED_RUN_GATE,
            **_complete(runtime_mode="LIVE", live_endpoint_configured=True),
        ).missing_preconditions
    )
    assert (
        "credential_scope_testnet"
        in build_productive_campaign_run_record_v1(
            mode=MODE_GOVERNED_RUN_GATE,
            **_complete(credential_scope="LIVE"),
        ).missing_preconditions
    )
    assert (
        "campaign_enabled"
        in build_productive_campaign_run_record_v1(
            mode=MODE_GOVERNED_RUN_GATE,
            **_complete(campaign_enabled=False),
        ).missing_preconditions
    )
    assert (
        "campaign_armed"
        in build_productive_campaign_run_record_v1(
            mode=MODE_GOVERNED_RUN_GATE,
            **_complete(campaign_armed=False),
        ).missing_preconditions
    )
    assert (
        "owner_authorization_bound"
        in build_productive_campaign_run_record_v1(
            mode=MODE_GOVERNED_RUN_GATE,
            **_complete(owner_go_bound=False),
        ).missing_preconditions
    )
    assert (
        "future_run_go_not_consumed"
        in build_productive_campaign_run_record_v1(
            mode=MODE_GOVERNED_RUN_GATE,
            **_complete(future_run_go_consumed=True),
        ).missing_preconditions
    )
    kill_bad = build_productive_campaign_run_record_v1(
        mode=MODE_GOVERNED_RUN_GATE,
        **_complete(kill_switch_binding_status="UNBOUND"),
    )
    assert kill_bad.run_may_start is False
    assert kill_bad.missing_preconditions
    with pytest.raises(Productive11128CampaignRunError, match="CONFIRM_TOKEN_DIGEST_INVALID"):
        build_productive_campaign_run_record_v1(
            mode=MODE_GOVERNED_RUN_GATE,
            **_complete(confirm_token_digest="bad"),
        )


def test_run_and_effects_refused() -> None:
    with pytest.raises(
        Productive11128CampaignRunError, match="RUN_FORBIDDEN_IN_THIS_IMPLEMENTATION"
    ):
        execute_productive_testnet_campaign_run_v1()
    with pytest.raises(Productive11128CampaignRunError, match="CAMPAIGN_START_FORBIDDEN"):
        refuse_campaign_start_v1()
    with pytest.raises(Productive11128CampaignRunError, match="ORDER_SUBMIT_FORBIDDEN"):
        refuse_order_submit_v1()
    with pytest.raises(Productive11128CampaignRunError, match="NETWORK_SESSION_FORBIDDEN"):
        refuse_network_session_v1()
    with pytest.raises(Productive11128CampaignRunError, match="LIVE_PATH_FORBIDDEN"):
        refuse_live_path_v1()
    with pytest.raises(Productive11128CampaignRunError, match="CAPABILITY_11_13_FORBIDDEN"):
        refuse_cap_11_13_v1()
    with pytest.raises(
        Productive11128CampaignRunError, match="FUTURE_RUN_GO_CONSUMPTION_FORBIDDEN"
    ):
        refuse_future_run_go_consume_v1()
    assert NETWORK_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"
    assert LIVE_ORDER_EFFECT == "NONE"
    assert SECTION_11_13_STARTED is False


def test_contract_proof_and_verifier_pass() -> None:
    proof = prove_productive_testnet_campaign_run_v1()
    assert proof["ok"] is True
    verification = verify_capability_11_section_11_12_8_productive_testnet_campaign_run_v1()
    assert verification["ok"] is True
    assert verification["claims"]["PRODUCTIVE_TESTNET_CAMPAIGN_RUN_IMPLEMENTED"] is True
    assert verification["claims"]["PRODUCTIVE_TESTNET_CAMPAIGN_RUN_SURFACE_PRESENT"] is True
    assert verification["claims"]["PRODUCTIVE_TESTNET_CAMPAIGN_STARTED"] is False
    assert verification["claims"]["RUN_AUTHORIZED"] is False
    assert verification["claims"]["NETWORK_EFFECT"] == "NONE"
    assert verification["claims"]["ORDER_EFFECT"] == "NONE"
    assert verification["claims"]["LIVE_ORDER_EFFECT"] == "NONE"
    assert verification["claims"]["SECTION_11_13_STARTED"] is False
    assert verification["claims"]["FUTURE_RUN_GO_CONSUMED"] is False
