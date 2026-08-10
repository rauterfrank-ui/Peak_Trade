"""Contract tests for §11.12.8 OKX Global Demo binding package (NO_ORDER)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1.binding_contract_v1 import (
    OkxGlobalDemoBindingError,
    assert_order_send_forbidden_v1,
    canonical_binding_headers_v1,
    default_canonical_binding_v1,
    evaluate_okx_global_demo_binding_v1,
)
from src.ops.section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1.constants_v1 import (
    CANONICAL_NEXT_STEP_AFTER_MERGE,
    CAPABILITY_ID,
    CREDENTIAL_CLASS,
    INSTRUMENT_SCOPE_EXACT,
    LIVE_AUTHORIZED,
    ORDER_POST_AUTHORIZED,
    PRE_LIVE_CYBERSECURITY_GATE,
    REST_HOST,
    SECTION_11_13_STARTED,
    VENUE,
)
from src.ops.section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1.threat_model_delta_v1 import (
    build_threat_model_delta_v1,
)
from src.ops.section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1.verifier_v1 import (
    verify_okx_global_demo_binding_package_v1,
)


def test_canonical_binding_accepts_exact_scope() -> None:
    binding = default_canonical_binding_v1()
    assert binding.venue == VENUE
    assert binding.rest_host == REST_HOST
    assert binding.instrument_scope_exact == INSTRUMENT_SCOPE_EXACT
    assert binding.credential_class == CREDENTIAL_CLASS
    assert binding.demo_marker_header_value == "1"
    assert binding.order_post_authorized is False
    assert binding.venue_activated is False
    assert binding.secret_reference.startswith("secretref://")


def test_demo_header_mandatory_fail_closed() -> None:
    with pytest.raises(OkxGlobalDemoBindingError, match="DEMO_MARKER_HEADER_MISSING"):
        evaluate_okx_global_demo_binding_v1(headers={})
    with pytest.raises(OkxGlobalDemoBindingError, match="DEMO_MARKER_HEADER_VALUE_MISMATCH"):
        evaluate_okx_global_demo_binding_v1(headers={"x-simulated-trading": "0"})
    with pytest.raises(OkxGlobalDemoBindingError, match="DEMO_MARKER_HEADER_VALUE_MISMATCH"):
        evaluate_okx_global_demo_binding_v1(demo_marker_header_value="")


def test_demo_credential_class_mandatory_and_live_eea_blocked() -> None:
    headers = canonical_binding_headers_v1()
    with pytest.raises(OkxGlobalDemoBindingError, match="LIVE_CREDENTIAL_CLASS_HARD_BLOCK"):
        evaluate_okx_global_demo_binding_v1(headers=headers, credential_class="OKX_LIVE_API_KEY")
    with pytest.raises(OkxGlobalDemoBindingError, match="EEA_CREDENTIAL_CLASS_HARD_BLOCK"):
        evaluate_okx_global_demo_binding_v1(headers=headers, credential_class="OKX_EEA_DEMO")
    with pytest.raises(OkxGlobalDemoBindingError, match="DEMO_CREDENTIAL_CLASS_REQUIRED"):
        evaluate_okx_global_demo_binding_v1(headers=headers, credential_class="OTHER_DEMO")


def test_exact_instrument_btc_usdt_swap_mandatory() -> None:
    headers = canonical_binding_headers_v1()
    with pytest.raises(OkxGlobalDemoBindingError, match="EXACT_INSTRUMENT_SCOPE_REQUIRED"):
        evaluate_okx_global_demo_binding_v1(headers=headers, instrument_scope_exact="ETH-USDT-SWAP")
    with pytest.raises(
        OkxGlobalDemoBindingError, match="GENERIC_OR_ALTERNATE_SYMBOL_SUBSTITUTION_FORBIDDEN"
    ):
        evaluate_okx_global_demo_binding_v1(headers=headers, instrument_scope_exact="BTCUSDT")
    with pytest.raises(
        OkxGlobalDemoBindingError, match="GENERIC_OR_ALTERNATE_SYMBOL_SUBSTITUTION_FORBIDDEN"
    ):
        evaluate_okx_global_demo_binding_v1(
            headers=headers, instrument_scope_exact="ETH-USD_UM_XPERP-310328"
        )


def test_environment_mismatch_fail_closed() -> None:
    headers = canonical_binding_headers_v1()
    with pytest.raises(OkxGlobalDemoBindingError, match="ENVIRONMENT_MISMATCH_FAIL_CLOSED"):
        evaluate_okx_global_demo_binding_v1(headers=headers, environment="LIVE")
    with pytest.raises(OkxGlobalDemoBindingError, match="RUNTIME_MODE_MISMATCH_FAIL_CLOSED"):
        evaluate_okx_global_demo_binding_v1(headers=headers, runtime_mode="LIVE")


def test_live_credential_live_mode_fail_closed() -> None:
    headers = canonical_binding_headers_v1()
    with pytest.raises(OkxGlobalDemoBindingError, match="LIVE_MODE_OR_ACCOUNT_HARD_BLOCK"):
        evaluate_okx_global_demo_binding_v1(headers=headers, live_mode=True)
    with pytest.raises(OkxGlobalDemoBindingError, match="LIVE_MODE_OR_ACCOUNT_HARD_BLOCK"):
        evaluate_okx_global_demo_binding_v1(headers=headers, live_account=True)


def test_silent_host_symbol_venue_fallback_impossible() -> None:
    headers = canonical_binding_headers_v1()
    with pytest.raises(OkxGlobalDemoBindingError, match="SILENT_HOST_FALLBACK_FORBIDDEN"):
        evaluate_okx_global_demo_binding_v1(headers=headers, rest_base="https://eea.okx.com")
    with pytest.raises(OkxGlobalDemoBindingError, match="SILENT_HOST_FALLBACK_FORBIDDEN"):
        evaluate_okx_global_demo_binding_v1(headers=headers, rest_base="https://www.okx.com")
    with pytest.raises(OkxGlobalDemoBindingError, match="SILENT_VENUE_FALLBACK_FORBIDDEN"):
        evaluate_okx_global_demo_binding_v1(headers=headers, venue="okx_eea")
    with pytest.raises(OkxGlobalDemoBindingError, match="HOST_NOT_OKX_GLOBAL_DEMO_ALLOWLIST"):
        evaluate_okx_global_demo_binding_v1(
            headers=headers, rest_base="https://testnet.binancefuture.com"
        )


def test_no_order_send_by_this_package() -> None:
    assert ORDER_POST_AUTHORIZED is False
    with pytest.raises(OkxGlobalDemoBindingError, match="ORDER_POST_HARD_BLOCK"):
        evaluate_okx_global_demo_binding_v1(
            headers=canonical_binding_headers_v1(), order_post_authorized=True
        )
    with pytest.raises(OkxGlobalDemoBindingError, match="ORDER_MUTATION_ENDPOINT_HARD_BLOCK"):
        assert_order_send_forbidden_v1(endpoint="/api/v5/trade/order")
    with pytest.raises(OkxGlobalDemoBindingError, match="ORDER_MUTATION_ENDPOINT_HARD_BLOCK"):
        assert_order_send_forbidden_v1(endpoint="/api/v5/trade/cancel-order")
    # Allowlisted no-order GET paths remain permitted for later preflight GO only.
    assert_order_send_forbidden_v1(endpoint="/api/v5/account/balance")


def test_governance_defaults_preserved() -> None:
    assert LIVE_AUTHORIZED is False
    assert SECTION_11_13_STARTED is False
    assert PRE_LIVE_CYBERSECURITY_GATE == "NOT_PASSED"
    assert CANONICAL_NEXT_STEP_AFTER_MERGE == (
        "OWNER_GO_EXECUTE_BOUNDED_NO_ORDER_PREFLIGHT_ON_OKX_GLOBAL_DEMO_BTC_USDT_SWAP"
    )
    threat = build_threat_model_delta_v1()
    assert threat["ok"] is True
    assert threat["SHARED_HOST_WITH_LIVE"] is True
    assert CAPABILITY_ID.endswith("BINDING_V1")


def test_verifier_seals_evidence(tmp_path: Path) -> None:
    result = verify_okx_global_demo_binding_package_v1(work_dir=tmp_path / "evidence")
    assert result["ok"] is True
    assert result["summary"]["ORDER_EFFECT"] == "NONE"
    assert (tmp_path / "evidence" / "MANIFEST.sha256").is_file()
    assert (tmp_path / "evidence" / "THREAT_MODEL_DELTA.json").is_file()
    assert (tmp_path / "evidence" / "BINDING_CONTRACT_PROOF.json").is_file()
