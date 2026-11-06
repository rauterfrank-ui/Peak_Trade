"""Contract tests for §11.12.8 OKX EEA Demo XPerp binding package (NO_ORDER)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1 import (
    constants_v1 as campaign_constants,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.binding_contract_v1 import (
    OkxEeaDemoXperpBindingError,
    assert_order_send_forbidden_v1,
    canonical_binding_headers_v1,
    default_canonical_binding_v1,
    evaluate_okx_eea_demo_xperp_binding_v1,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.constants_v1 import (
    CANONICAL_NEXT_STEP_AFTER_MERGE,
    CAPABILITY_ID,
    CREDENTIAL_CLASS,
    INSTRUMENT_SCOPE_EXACT,
    INSTRUMENT_TYPE,
    LEGACY_BTC_USDT_SWAP_ACTIVE_BINDING_REMOVED,
    LIVE_AUTHORIZED,
    OKX_GLOBAL_DEMO_ACTIVE_BINDING,
    ORDER_POST_AUTHORIZED,
    PRE_LIVE_CYBERSECURITY_GATE,
    RULE_TYPE,
    SECTION_11_13_STARTED,
    REST_HOST,
    VENUE,
    XPERP_PRIVATE_CAPABILITY_PROOF_BOUND,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.threat_model_delta_v1 import (
    build_threat_model_delta_v1,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.verifier_v1 import (
    verify_okx_eea_demo_xperp_binding_package_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1 import (
    constants_v1 as activation_constants,
)
from src.ops.section_11_12_8_productive_campaign_run_consumer_v1 import (
    constants_v1 as consumer_constants,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1 import (
    constants_v1 as terminal_constants,
)


def test_canonical_binding_accepts_exact_xperp_scope() -> None:
    binding = default_canonical_binding_v1()
    assert binding.venue == VENUE
    assert binding.rest_host == REST_HOST
    assert binding.instrument_scope_exact == INSTRUMENT_SCOPE_EXACT
    assert binding.instrument_type == INSTRUMENT_TYPE
    assert binding.rule_type == RULE_TYPE
    assert binding.credential_class == CREDENTIAL_CLASS
    assert binding.demo_marker_header_value == "1"
    assert binding.order_post_authorized is False
    assert binding.venue_activated is False
    assert binding.secret_reference.startswith("secretref://")


def test_demo_header_mandatory_fail_closed() -> None:
    with pytest.raises(OkxEeaDemoXperpBindingError, match="DEMO_MARKER_HEADER_MISSING"):
        evaluate_okx_eea_demo_xperp_binding_v1(headers={})
    with pytest.raises(OkxEeaDemoXperpBindingError, match="DEMO_MARKER_HEADER_VALUE_MISMATCH"):
        evaluate_okx_eea_demo_xperp_binding_v1(headers={"x-simulated-trading": "0"})


def test_live_and_global_credential_classes_blocked() -> None:
    headers = canonical_binding_headers_v1()
    with pytest.raises(OkxEeaDemoXperpBindingError, match="LIVE_CREDENTIAL_CLASS_HARD_BLOCK"):
        evaluate_okx_eea_demo_xperp_binding_v1(headers=headers, credential_class="OKX_LIVE_API_KEY")
    with pytest.raises(OkxEeaDemoXperpBindingError, match="GLOBAL_CREDENTIAL_CLASS_HARD_BLOCK"):
        evaluate_okx_eea_demo_xperp_binding_v1(
            headers=headers, credential_class="OKX_DEMO_TRADING_API_KEY_ONLY"
        )


def test_legacy_btc_usdt_swap_cannot_become_active_eea_instrument() -> None:
    headers = canonical_binding_headers_v1()
    with pytest.raises(
        OkxEeaDemoXperpBindingError, match="LEGACY_BTC_USDT_SWAP_ACTIVE_BINDING_FORBIDDEN"
    ):
        evaluate_okx_eea_demo_xperp_binding_v1(
            headers=headers, instrument_scope_exact="BTC-USDT-SWAP"
        )


def test_exact_xperp_instrument_type_and_rule_required() -> None:
    headers = canonical_binding_headers_v1()
    with pytest.raises(OkxEeaDemoXperpBindingError, match="EXACT_INSTRUMENT_SCOPE_REQUIRED"):
        evaluate_okx_eea_demo_xperp_binding_v1(
            headers=headers, instrument_scope_exact="ETH-USDT-SWAP"
        )
    with pytest.raises(OkxEeaDemoXperpBindingError, match="INSTRUMENT_TYPE_MISMATCH"):
        evaluate_okx_eea_demo_xperp_binding_v1(headers=headers, instrument_type="SWAP")
    with pytest.raises(OkxEeaDemoXperpBindingError, match="RULE_TYPE_MISMATCH"):
        evaluate_okx_eea_demo_xperp_binding_v1(headers=headers, rule_type="linear")


def test_silent_global_host_venue_fallback_impossible() -> None:
    headers = canonical_binding_headers_v1()
    with pytest.raises(OkxEeaDemoXperpBindingError, match="SILENT_HOST_FALLBACK_FORBIDDEN"):
        evaluate_okx_eea_demo_xperp_binding_v1(headers=headers, rest_base="https://openapi.okx.com")
    with pytest.raises(OkxEeaDemoXperpBindingError, match="SILENT_VENUE_FALLBACK_FORBIDDEN"):
        evaluate_okx_eea_demo_xperp_binding_v1(headers=headers, venue="okx_global")


def test_no_order_send_by_this_package() -> None:
    assert ORDER_POST_AUTHORIZED is False
    with pytest.raises(OkxEeaDemoXperpBindingError, match="ORDER_POST_HARD_BLOCK"):
        evaluate_okx_eea_demo_xperp_binding_v1(
            headers=canonical_binding_headers_v1(), order_post_authorized=True
        )
    with pytest.raises(OkxEeaDemoXperpBindingError, match="ORDER_MUTATION_ENDPOINT_HARD_BLOCK"):
        assert_order_send_forbidden_v1(endpoint="/api/v5/trade/order")
    assert_order_send_forbidden_v1(endpoint="/api/v5/account/instruments")
    assert_order_send_forbidden_v1(
        endpoint="/api/v5/trade/order",
        order_post=True,
        ephemeral_campaign_write_gate_pass=True,
    )
    assert ORDER_POST_AUTHORIZED is False


def test_governance_defaults_and_active_campaign_instrument_rebinding() -> None:
    assert LIVE_AUTHORIZED is False
    assert SECTION_11_13_STARTED is False
    assert PRE_LIVE_CYBERSECURITY_GATE == "NOT_PASSED"
    assert LEGACY_BTC_USDT_SWAP_ACTIVE_BINDING_REMOVED is True
    assert OKX_GLOBAL_DEMO_ACTIVE_BINDING is False
    assert XPERP_PRIVATE_CAPABILITY_PROOF_BOUND is True
    assert CANONICAL_NEXT_STEP_AFTER_MERGE == (
        "OWNER_GO_EXECUTE_BOUNDED_SECTION_11_12_8_OKX_EEA_DEMO_XPERP_CAMPAIGN"
        "_WITH_HIDDEN_CONFIRM_AND_SECRETREF_VAULT_RUNTIME"
    )
    from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.constants_v1 import (
        ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH,
        BTC_USDT_SWAP_PATH_STATUS,
        SWAP_RUNTIME_FALLBACK,
        SWAP_WRITE_AUTHORIZATION,
        XPERP_ONLY_ACTIVE_WRITE_SCOPE,
    )

    assert BTC_USDT_SWAP_PATH_STATUS == "CLOSED_DEPRECATED_HISTORICAL_EVIDENCE_ONLY"
    assert ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH == "OKX_EEA_DEMO_XPERP"
    assert SWAP_RUNTIME_FALLBACK is False
    assert SWAP_WRITE_AUTHORIZATION is False
    assert XPERP_ONLY_ACTIVE_WRITE_SCOPE is True
    assert campaign_constants.CANONICAL_INSTRUMENT_SCOPE == (INSTRUMENT_SCOPE_EXACT,)
    assert campaign_constants.CANONICAL_VENUE == VENUE
    assert campaign_constants.CANONICAL_ORDER_SZ_FOR_VENUE_NATIVE_BODY_V1 == "0.0001"
    assert terminal_constants.CANONICAL_INSTRUMENT_SCOPE == (INSTRUMENT_SCOPE_EXACT,)
    assert consumer_constants.CANONICAL_INSTRUMENT_SCOPE == (INSTRUMENT_SCOPE_EXACT,)
    assert activation_constants.CANONICAL_INSTRUMENT_SCOPE == (INSTRUMENT_SCOPE_EXACT,)
    assert "BTC-USDT-SWAP" not in campaign_constants.CANONICAL_INSTRUMENT_SCOPE
    threat = build_threat_model_delta_v1()
    assert threat["ok"] is True
    assert threat["SHARED_HOST_WITH_LIVE"] is False
    assert CAPABILITY_ID.endswith("BINDING_V1")


def test_verifier_seals_evidence(tmp_path: Path) -> None:
    result = verify_okx_eea_demo_xperp_binding_package_v1(work_dir=tmp_path / "evidence")
    assert result["ok"] is True
    assert result["summary"]["ORDER_EFFECT"] == "NONE"
    assert result["summary"]["PRIVATE_WRITE_COUNT"] == 0
    assert (tmp_path / "evidence" / "MANIFEST.sha256").is_file()
    assert (tmp_path / "evidence" / "THREAT_MODEL_DELTA.json").is_file()
    assert (tmp_path / "evidence" / "BINDING_CONTRACT_PROOF.json").is_file()
