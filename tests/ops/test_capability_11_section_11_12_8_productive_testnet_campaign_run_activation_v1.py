"""Tests for Cap 11 §11.12.8 productive Testnet campaign run activation surface."""

from __future__ import annotations

import pytest

from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1.activation_v1 import (
    Productive11128CampaignRunActivationError,
    activate_productive_testnet_campaign_run_v1,
    build_productive_campaign_run_activation_record_v1,
    prove_productive_testnet_campaign_run_activation_v1,
    refuse_activation_v1,
    refuse_cap_11_13_v1,
    refuse_campaign_start_v1,
    refuse_future_activation_go_consume_v1,
    refuse_live_path_v1,
    refuse_network_session_v1,
    refuse_order_submit_v1,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1.constants_v1 import (
    ACTIVATION_AUTHORIZED,
    LIVE_ORDER_EFFECT,
    MODE_GOVERNED_ACTIVATION_GATE,
    MODE_PROVE_ACTIVATION_ONLY,
    NETWORK_EFFECT,
    ORDER_EFFECT,
    PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_IMPLEMENTED,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    RUN_AUTHORIZED,
    RUN_PREDECESSOR_ORIGIN_MAIN_SHA,
    SECTION_11_13_STARTED,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1.verifier_v1 import (
    verify_capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1,
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
        "activation_authorized_ephemeral": True,
        "run_predecessor_origin_main_sha": RUN_PREDECESSOR_ORIGIN_MAIN_SHA,
    }
    base.update(overrides)
    return base


def test_prove_mode_never_may_start() -> None:
    record = build_productive_campaign_run_activation_record_v1(
        mode=MODE_PROVE_ACTIVATION_ONLY, **_complete()
    )
    assert record.activation_may_start is False
    assert record.campaign_started is False


def test_gate_may_start_but_does_not_activate() -> None:
    record = build_productive_campaign_run_activation_record_v1(
        mode=MODE_GOVERNED_ACTIVATION_GATE, **_complete()
    )
    assert record.activation_may_start is True
    assert record.campaign_started is False
    assert record.run_authorized_constant is False
    assert record.activation_authorized_constant is False
    assert RUN_AUTHORIZED is False
    assert ACTIVATION_AUTHORIZED is False
    assert PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False
    assert PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_IMPLEMENTED is True
    assert record.network_effect == "NONE"
    assert record.order_effect == "NONE"
    assert record.live_order_effect == "NONE"
    assert record.run_predecessor_bound is True
    assert record.run_may_start is True
    assert record.run_predecessor_origin_main_sha == RUN_PREDECESSOR_ORIGIN_MAIN_SHA


def test_negative_gates() -> None:
    assert (
        "activation_authorized_ephemeral"
        in build_productive_campaign_run_activation_record_v1(
            mode=MODE_GOVERNED_ACTIVATION_GATE,
            **_complete(activation_authorized_ephemeral=False),
        ).missing_preconditions
    )
    assert (
        "testnet_only_scope"
        in build_productive_campaign_run_activation_record_v1(
            mode=MODE_GOVERNED_ACTIVATION_GATE,
            **_complete(runtime_mode="LIVE", live_endpoint_configured=True),
        ).missing_preconditions
    )
    assert (
        "credential_scope_testnet"
        in build_productive_campaign_run_activation_record_v1(
            mode=MODE_GOVERNED_ACTIVATION_GATE,
            **_complete(credential_scope="LIVE"),
        ).missing_preconditions
    )
    assert (
        "campaign_enabled"
        in build_productive_campaign_run_activation_record_v1(
            mode=MODE_GOVERNED_ACTIVATION_GATE,
            **_complete(campaign_enabled=False),
        ).missing_preconditions
    )
    assert (
        "campaign_armed"
        in build_productive_campaign_run_activation_record_v1(
            mode=MODE_GOVERNED_ACTIVATION_GATE,
            **_complete(campaign_armed=False),
        ).missing_preconditions
    )
    assert (
        "owner_authorization_bound"
        in build_productive_campaign_run_activation_record_v1(
            mode=MODE_GOVERNED_ACTIVATION_GATE,
            **_complete(owner_go_bound=False),
        ).missing_preconditions
    )
    assert (
        "future_activation_go_not_consumed"
        in build_productive_campaign_run_activation_record_v1(
            mode=MODE_GOVERNED_ACTIVATION_GATE,
            **_complete(future_activation_go_consumed=True),
        ).missing_preconditions
    )
    assert (
        "run_predecessor_sha_bound"
        in build_productive_campaign_run_activation_record_v1(
            mode=MODE_GOVERNED_ACTIVATION_GATE,
            **_complete(run_predecessor_origin_main_sha="0" * 40),
        ).missing_preconditions
    )
    kill_bad = build_productive_campaign_run_activation_record_v1(
        mode=MODE_GOVERNED_ACTIVATION_GATE,
        **_complete(kill_switch_binding_status="UNBOUND"),
    )
    assert kill_bad.activation_may_start is False
    assert kill_bad.missing_preconditions
    emergency_bad = build_productive_campaign_run_activation_record_v1(
        mode=MODE_GOVERNED_ACTIVATION_GATE,
        **_complete(emergency_commands=("HALT_ONLY",)),
    )
    assert emergency_bad.activation_may_start is False
    risk_bad = build_productive_campaign_run_activation_record_v1(
        mode=MODE_GOVERNED_ACTIVATION_GATE,
        **_complete(instrument_scope=("ETH-USDT-SWAP",)),
    )
    assert risk_bad.activation_may_start is False
    with pytest.raises(
        Productive11128CampaignRunActivationError, match="CONFIRM_TOKEN_DIGEST_INVALID"
    ):
        build_productive_campaign_run_activation_record_v1(
            mode=MODE_GOVERNED_ACTIVATION_GATE,
            **_complete(confirm_token_digest="bad"),
        )


def test_activation_and_effects_refused() -> None:
    with pytest.raises(
        Productive11128CampaignRunActivationError,
        match="ACTIVATION_FORBIDDEN_IN_THIS_IMPLEMENTATION",
    ):
        activate_productive_testnet_campaign_run_v1()
    with pytest.raises(Productive11128CampaignRunActivationError, match="ACTIVATION_FORBIDDEN"):
        refuse_activation_v1()
    with pytest.raises(Productive11128CampaignRunActivationError, match="CAMPAIGN_START_FORBIDDEN"):
        refuse_campaign_start_v1()
    with pytest.raises(Productive11128CampaignRunActivationError, match="ORDER_SUBMIT_FORBIDDEN"):
        refuse_order_submit_v1()
    with pytest.raises(
        Productive11128CampaignRunActivationError, match="NETWORK_SESSION_FORBIDDEN"
    ):
        refuse_network_session_v1()
    with pytest.raises(Productive11128CampaignRunActivationError, match="LIVE_PATH_FORBIDDEN"):
        refuse_live_path_v1()
    with pytest.raises(
        Productive11128CampaignRunActivationError, match="CAPABILITY_11_13_FORBIDDEN"
    ):
        refuse_cap_11_13_v1()
    with pytest.raises(
        Productive11128CampaignRunActivationError,
        match="FUTURE_ACTIVATION_GO_CONSUMPTION_FORBIDDEN",
    ):
        refuse_future_activation_go_consume_v1()
    assert NETWORK_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"
    assert LIVE_ORDER_EFFECT == "NONE"
    assert SECTION_11_13_STARTED is False


def test_contract_proof_and_verifier_pass() -> None:
    proof = prove_productive_testnet_campaign_run_activation_v1()
    assert proof["ok"] is True
    verification = (
        verify_capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1()
    )
    assert verification["ok"] is True
    claims = verification["claims"]
    assert claims["PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_IMPLEMENTED"] is True
    assert claims["PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_SURFACE_PRESENT"] is True
    assert claims["PRODUCTIVE_ACTIVATION_ENTRYPOINT_PRESENT"] is True
    assert claims["PRODUCTIVE_TESTNET_CAMPAIGN_STARTED"] is False
    assert claims["RUN_AUTHORIZED"] is False
    assert claims["ACTIVATION_AUTHORIZED"] is False
    assert claims["NETWORK_EFFECT"] == "NONE"
    assert claims["ORDER_EFFECT"] == "NONE"
    assert claims["LIVE_ORDER_EFFECT"] == "NONE"
    assert claims["SECTION_11_13_STARTED"] is False
    assert claims["FUTURE_ACTIVATION_GO_CONSUMED"] is False
    assert claims["RUN_PREDECESSOR_ORIGIN_MAIN_SHA"] == RUN_PREDECESSOR_ORIGIN_MAIN_SHA
    assert (
        claims["NEXT_CONSUMER_CAPABILITY_ID"]
        == "SEPARATE_OWNER_GO_REQUIRED_FOR_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION"
    )
