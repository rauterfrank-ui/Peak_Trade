"""Tests for Cap 11 §11.12.8 productive Testnet campaign path."""

from __future__ import annotations

import pytest

from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_path_v1.constants_v1 import (
    CANONICAL_ALLOWED_ORDER_TYPES,
    CANONICAL_INSTRUMENT_SCOPE,
    CANONICAL_POSITION_COUNT_LIMIT,
    CANONICAL_VENUE,
    MODE_GOVERNED_START_GATE,
    MODE_PROVE_PATH_ONLY,
    NETWORK_EFFECT,
    ORDER_EFFECT,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    PRODUCTIVE_TESTNET_CAPABILITY_IMPLEMENTED,
    PRODUCTIVE_TESTNET_EXECUTION_AUTHORIZED,
    SECTION_11_13_STARTED,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_path_v1.productive_path_v1 import (
    Productive11128CampaignPathError,
    attempt_productive_campaign_execution_v1,
    build_productive_campaign_path_record_v1,
    prove_productive_testnet_campaign_path_v1,
    refuse_cap_11_13_v1,
    refuse_campaign_start_v1,
    refuse_live_path_v1,
    refuse_network_session_v1,
    refuse_order_submit_v1,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_path_v1.verifier_v1 import (
    verify_capability_11_section_11_12_8_productive_testnet_campaign_path_v1,
)

_SHA = "a" * 40
_CFG = "cfg-" + ("b" * 64)
_DIGEST = "c" * 64


def _complete(**overrides):
    base = {
        "runtime_mode": "TESTNET",
        "venue": CANONICAL_VENUE,
        "account_identity": "acct-uid-demo",
        "instrument_scope": CANONICAL_INSTRUMENT_SCOPE,
        "allowed_order_types": CANONICAL_ALLOWED_ORDER_TYPES,
        "position_count_limit": CANONICAL_POSITION_COUNT_LIMIT,
        "repository_sha": _SHA,
        "config_digest": _CFG,
        "expected_repository_sha": _SHA,
        "expected_config_digest": _CFG,
        "expected_account_identity": "acct-uid-demo",
        "expected_venue": CANONICAL_VENUE,
        "credential_scope": "TESTNET",
        "secret_reference": "secretref://vault/testnet/okx-demo",
        "confirm_token_digest": _DIGEST,
        "expected_confirm_token_digest": _DIGEST,
        "owner_go_bound": True,
        "campaign_enabled": True,
        "campaign_armed": True,
    }
    base.update(overrides)
    return base


def test_path_proof_mode_never_may_start() -> None:
    record = build_productive_campaign_path_record_v1(mode=MODE_PROVE_PATH_ONLY, **_complete())
    assert record.campaign_may_start is False
    assert record.campaign_started is False
    assert record.network_effect == "NONE"
    assert record.order_effect == "NONE"
    assert record.fixture_predecessor_bound is True


def test_start_gate_may_start_but_does_not_start() -> None:
    record = build_productive_campaign_path_record_v1(mode=MODE_GOVERNED_START_GATE, **_complete())
    assert record.campaign_may_start is True
    assert record.campaign_started is False
    assert PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False
    assert PRODUCTIVE_TESTNET_EXECUTION_AUTHORIZED is False
    assert PRODUCTIVE_TESTNET_CAPABILITY_IMPLEMENTED is True


def test_live_endpoint_rejected() -> None:
    record = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **_complete(runtime_mode="LIVE", live_endpoint_configured=True),
    )
    assert record.campaign_may_start is False
    assert "testnet_only_scope" in record.missing_preconditions
    assert "live_path_blocked" in record.missing_preconditions


def test_wrong_credential_scope_rejected() -> None:
    record = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE, **_complete(credential_scope="LIVE")
    )
    assert record.campaign_may_start is False
    assert "credential_scope_testnet" in record.missing_preconditions


def test_enabled_and_armed_false_rejected() -> None:
    enabled = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE, **_complete(campaign_enabled=False)
    )
    armed = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE, **_complete(campaign_armed=False)
    )
    assert "campaign_enabled" in enabled.missing_preconditions
    assert "campaign_armed" in armed.missing_preconditions


def test_missing_owner_authorization_rejected() -> None:
    record = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE, **_complete(owner_go_bound=False)
    )
    assert "owner_authorization_bound" in record.missing_preconditions


def test_invalid_and_mismatched_confirm_digest_rejected() -> None:
    with pytest.raises(Productive11128CampaignPathError, match="CONFIRM_TOKEN_DIGEST_INVALID"):
        build_productive_campaign_path_record_v1(
            mode=MODE_GOVERNED_START_GATE, **_complete(confirm_token_digest="nope")
        )
    with pytest.raises(Productive11128CampaignPathError, match="CONFIRM_TOKEN_DIGEST_MISMATCH"):
        build_productive_campaign_path_record_v1(
            mode=MODE_GOVERNED_START_GATE,
            **_complete(expected_confirm_token_digest="d" * 64),
        )
    with pytest.raises(Productive11128CampaignPathError, match="CONFIRM_TOKEN_ARGV_FORBIDDEN"):
        build_productive_campaign_path_record_v1(
            mode=MODE_GOVERNED_START_GATE,
            **_complete(argv=["--confirm-token", "secret"]),
        )


def test_kill_switch_and_emergency_control_not_operational_rejected() -> None:
    kill_bad = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **_complete(kill_switch_binding_status="UNBOUND"),
    )
    emergency_bad = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **_complete(emergency_commands=("HALT_ONLY",)),
    )
    assert "kill_switch_operational" in kill_bad.missing_preconditions
    assert kill_bad.campaign_may_start is False
    assert "emergency_control_operational" in emergency_bad.missing_preconditions
    assert emergency_bad.campaign_may_start is False


def test_risk_instrument_order_scope_rejected() -> None:
    instrument = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **_complete(instrument_scope=("ETH-USDT-SWAP",)),
    )
    order_type = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **_complete(allowed_order_types=("MARKET",)),
    )
    position = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **_complete(position_count_limit=2),
    )
    assert "instrument_scope_within_authority" in instrument.missing_preconditions
    assert "order_types_within_authority" in order_type.missing_preconditions
    assert "position_count_within_authority" in position.missing_preconditions


def test_execution_and_11_13_and_effects_refused() -> None:
    with pytest.raises(Productive11128CampaignPathError, match="CAMPAIGN_START_FORBIDDEN"):
        refuse_campaign_start_v1()
    with pytest.raises(Productive11128CampaignPathError, match="EXECUTION_FORBIDDEN"):
        attempt_productive_campaign_execution_v1()
    with pytest.raises(Productive11128CampaignPathError, match="CAPABILITY_11_13_FORBIDDEN"):
        refuse_cap_11_13_v1()
    with pytest.raises(Productive11128CampaignPathError, match="ORDER_SUBMIT_FORBIDDEN"):
        refuse_order_submit_v1()
    with pytest.raises(Productive11128CampaignPathError, match="NETWORK_SESSION_FORBIDDEN"):
        refuse_network_session_v1()
    with pytest.raises(Productive11128CampaignPathError, match="LIVE_PATH_FORBIDDEN"):
        refuse_live_path_v1()
    assert NETWORK_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"
    assert SECTION_11_13_STARTED is False


def test_contract_proof_and_verifier_pass() -> None:
    proof = prove_productive_testnet_campaign_path_v1()
    assert proof["ok"] is True
    verification = verify_capability_11_section_11_12_8_productive_testnet_campaign_path_v1()
    assert verification["ok"] is True
    assert verification["claims"]["PRODUCTIVE_TESTNET_CAPABILITY_IMPLEMENTED"] is True
    assert verification["claims"]["PRODUCTIVE_TESTNET_CAMPAIGN_STARTED"] is False
    assert verification["claims"]["NETWORK_EFFECT"] == "NONE"
    assert verification["claims"]["ORDER_EFFECT"] == "NONE"
    assert verification["claims"]["SECTION_11_13_STARTED"] is False
    assert verification["claims"]["FIXTURE_PROOF_PRESERVED"] is True
