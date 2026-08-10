"""Contract tests for §11.12.8 OKX EEA Demo XPerp ephemeral campaign private-write gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.constants_v1 import (
    CANONICAL_NEXT_STEP_AFTER_MERGE,
    CANONICAL_ORDER_SZ,
    PACKAGE_DEFAULT_ORDER_POST_AUTHORIZED,
    SECTION_11_12_8_STATUS,
    SCOPED_OWNER_GO_SCOPE,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.gate_v1 import (
    OkxEeaDemoXperpCampaignPrivateWriteGateError,
    assert_mutation_allowed_under_ephemeral_gate_v1,
    evaluate_ephemeral_campaign_private_write_gate_v1,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.verifier_v1 import (
    verify_okx_eea_demo_xperp_campaign_private_write_gate_v1,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.binding_contract_v1 import (
    assert_order_send_forbidden_v1,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.constants_v1 import (
    ORDER_POST_AUTHORIZED as BINDING_ORDER_POST_AUTHORIZED,
)


def _full_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        owner_go_consumed=True,
        owner_go_scope=SCOPED_OWNER_GO_SCOPE,
        owner_go_authorization=SCOPED_OWNER_GO_SCOPE,
        confirm_latched=True,
        testnet_authorized_runtime=True,
        campaign_enabled=True,
        campaign_armed=True,
        risk_gate_pass=True,
        kill_switch_pass=True,
        emergency_control_pass=True,
        account_binding_pass=True,
        endpoint_allowlist_pass=True,
        bound_client_pass=True,
        secretref_ephemeral_loaded=True,
        headers={"x-simulated-trading": "1"},
    )
    base.update(overrides)
    return base


def test_package_defaults_remain_false() -> None:
    assert PACKAGE_DEFAULT_ORDER_POST_AUTHORIZED is False
    assert BINDING_ORDER_POST_AUTHORIZED is False
    assert SECTION_11_12_8_STATUS == (
        "OPEN_OKX_EEA_DEMO_XPERP_CAMPAIGN_WRITE_PATH_READY_AWAITING_OWNER_EXECUTE"
    )
    assert CANONICAL_ORDER_SZ == "0.0001"
    assert CANONICAL_NEXT_STEP_AFTER_MERGE.startswith(
        "OWNER_GO_EXECUTE_BOUNDED_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN"
    )


def test_canonical_go_pass_and_legacy_aliases() -> None:
    gate = evaluate_ephemeral_campaign_private_write_gate_v1(**_full_kwargs())
    assert gate.pass_gate is True
    assert gate.ephemeral_campaign_write_gate_pass is True
    legacy = evaluate_ephemeral_campaign_private_write_gate_v1(
        **_full_kwargs(
            owner_go_scope="EXECUTE_BOUNDED_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_NOW",
            owner_go_authorization="EXECUTE_BOUNDED_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_NOW",
        )
    )
    assert legacy.pass_gate is True
    alias = evaluate_ephemeral_campaign_private_write_gate_v1(
        **_full_kwargs(
            owner_go_scope="EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW",
            owner_go_authorization="EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW",
        )
    )
    assert alias.pass_gate is True


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"owner_go_scope": "WRONG", "owner_go_authorization": "WRONG"}, "OWNER_GO_SCOPE"),
        ({"venue": "okx_global"}, "VENUE_MISMATCH"),
        ({"rest_base": "https://openapi.okx.com"}, "HOST_NOT_OKX_EEA_DEMO"),
        ({"instrument_scope_exact": "BTC-USDT-SWAP"}, "INSTRUMENT_SCOPE_MISMATCH"),
        ({"confirm_latched": False}, "HIDDEN_CONFIRM_NOT_LATCHED"),
        ({"secretref_ephemeral_loaded": False}, "SECRETREF_EPHEMERAL_NOT_LOADED"),
        ({"live_authorized": True}, "LIVE_PATH_HARD_BLOCK"),
        (
            {"package_default_order_post_authorized": True},
            "PACKAGE_DEFAULT_ORDER_POST_MUST_REMAIN_FALSE",
        ),
    ],
)
def test_fail_closed_matrix(overrides: dict[str, object], match: str) -> None:
    with pytest.raises(OkxEeaDemoXperpCampaignPrivateWriteGateError, match=match):
        evaluate_ephemeral_campaign_private_write_gate_v1(**_full_kwargs(**overrides))


def test_mutation_requires_ephemeral_pass_and_binding_default_untouched() -> None:
    with pytest.raises(OkxEeaDemoXperpCampaignPrivateWriteGateError):
        assert_mutation_allowed_under_ephemeral_gate_v1(
            endpoint="/api/v5/trade/order",
            ephemeral_campaign_write_gate_pass=False,
        )
    assert_mutation_allowed_under_ephemeral_gate_v1(
        endpoint="/api/v5/trade/order",
        ephemeral_campaign_write_gate_pass=True,
    )
    with pytest.raises(Exception, match="ORDER_MUTATION_ENDPOINT_HARD_BLOCK"):
        assert_order_send_forbidden_v1(endpoint="/api/v5/trade/order")
    assert_order_send_forbidden_v1(
        endpoint="/api/v5/trade/order",
        order_post=True,
        ephemeral_campaign_write_gate_pass=True,
    )
    assert BINDING_ORDER_POST_AUTHORIZED is False


def test_verifier_seals_offline(tmp_path: Path) -> None:
    result = verify_okx_eea_demo_xperp_campaign_private_write_gate_v1(
        work_dir=tmp_path / "evidence"
    )
    assert result["ok"] is True
    assert result["summary"]["ORDER_EFFECT"] == "NONE"
    assert result["summary"]["LIVE_AUTHORIZED"] is False
    assert (tmp_path / "evidence" / "MANIFEST.sha256").is_file()
