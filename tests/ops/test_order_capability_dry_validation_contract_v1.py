"""Offline tests for order_capability_dry_validation_contract_v1.

Class-4 scoped: no network, credentials, orders, or Testnet execute.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_contract_v0 import DEFAULT_INSTRUMENT
from src.ops.bounded_testnet_order_cap_contract_v0 import default_bounded_normal_v0_spec
from src.ops.order_capability_dry_validation_contract_v1 import (
    DEFAULT_MAX_SESSION_DURATION_SECONDS,
    DEFAULT_ORDER_TYPE,
    DEFAULT_VENUE_HOST,
    PACKAGE_MARKER,
    OrderCapabilityDryValidationInputs,
    build_dry_validation_result,
    evaluate_order_capability_dry_validation,
)

CONTRACT_MODULE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "ops"
    / "order_capability_dry_validation_contract_v1.py"
)

TEST_PACKAGE_MARKER = "ORDER_CAPABILITY_DRY_VALIDATION_CONTRACT_V1_TEST=true"


def _valid_inputs(**overrides: object) -> OrderCapabilityDryValidationInputs:
    spec = default_bounded_normal_v0_spec()
    base = {
        "instrument": DEFAULT_INSTRUMENT,
        "venue": f"Kraken Futures Demo / {DEFAULT_VENUE_HOST}",
        "max_loss_cap_eur": 1.0,
        "max_notional_eur": spec.max_notional_eur,
        "order_type": DEFAULT_ORDER_TYPE,
        "session_duration_seconds": DEFAULT_MAX_SESSION_DURATION_SECONDS,
        "abort_ack_confirmed": True,
        "max_notional_confirmed": True,
    }
    base.update(overrides)
    return OrderCapabilityDryValidationInputs(**base)


def test_package_marker_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_pass_with_conservative_inputs_and_blockers_confirmed() -> None:
    result = evaluate_order_capability_dry_validation(_valid_inputs())
    assert result["verdict"] == "PASS"
    assert result["execute_ready"] is False
    assert result["fail_reasons"] == []
    assert result["safety_flags"]["order_capability_execute_authorized"] is False
    assert result["safety_flags"]["dry_validation_authorized"] is False
    assert result["safety_flags"]["live_authorized"] is False
    assert result["safety_flags"]["no_authority_change"] is True
    assert result["safety_flags"]["preflight_remains_blocked"] is True


def test_fail_closed_missing_abort_ack() -> None:
    result = evaluate_order_capability_dry_validation(_valid_inputs(abort_ack_confirmed=False))
    assert result["verdict"] == "FAIL_CLOSED"
    assert any("abort_ack" in r for r in result["fail_reasons"])


def test_fail_closed_missing_max_notional_confirmation() -> None:
    result = evaluate_order_capability_dry_validation(_valid_inputs(max_notional_confirmed=False))
    assert result["verdict"] == "FAIL_CLOSED"
    assert any("max_notional" in r for r in result["fail_reasons"])


def test_fail_closed_max_loss_cap_exceeds_max_notional() -> None:
    result = evaluate_order_capability_dry_validation(
        _valid_inputs(max_loss_cap_eur=11.0, max_notional_eur=10.0)
    )
    assert result["verdict"] == "FAIL_CLOSED"
    assert any("max_loss_cap" in r for r in result["fail_reasons"])


def test_fail_closed_non_demo_venue() -> None:
    result = evaluate_order_capability_dry_validation(
        _valid_inputs(venue="https://futures.kraken.com")
    )
    assert result["verdict"] == "FAIL_CLOSED"
    assert any("venue" in r for r in result["fail_reasons"])


def test_fail_closed_market_order_type() -> None:
    result = evaluate_order_capability_dry_validation(_valid_inputs(order_type="market"))
    assert result["verdict"] == "FAIL_CLOSED"
    assert any("order_type" in r for r in result["fail_reasons"])


def test_fail_closed_duration_over_sixty() -> None:
    result = evaluate_order_capability_dry_validation(_valid_inputs(session_duration_seconds=61))
    assert result["verdict"] == "FAIL_CLOSED"
    assert any("session_duration" in r for r in result["fail_reasons"])


def test_fail_closed_unsupported_instrument() -> None:
    result = evaluate_order_capability_dry_validation(_valid_inputs(instrument="BTCUSDT"))
    assert result["verdict"] == "FAIL_CLOSED"
    assert any("instrument" in r for r in result["fail_reasons"])


def test_fail_closed_pf_xbtusd_instrument() -> None:
    result = evaluate_order_capability_dry_validation(_valid_inputs(instrument="PF_XBTUSD"))
    assert result["verdict"] == "FAIL_CLOSED"
    assert any("instrument must be" in r for r in result["fail_reasons"])


def test_pass_pf_ethusd_with_kraken_futures_demo_venue() -> None:
    result = evaluate_order_capability_dry_validation(
        _valid_inputs(
            instrument="PF_ETHUSD",
            venue="kraken_futures_demo / demo-futures.kraken.com",
        )
    )
    assert result["verdict"] == "PASS"
    assert result["fail_reasons"] == []


def test_build_result_contains_machine_fields() -> None:
    payload = build_dry_validation_result(_valid_inputs())
    assert payload["schema_version"] == "order_capability_dry_validation_result.v1"
    assert payload["verdict"] == "PASS"
    assert payload["input_status"]["instrument"] == DEFAULT_INSTRUMENT
    assert payload["blocker_status"]["abort_ack_confirmed"] is True
    assert payload["blocker_status"]["max_notional_confirmed"] is True
    assert payload["safety_flags"]["no_order"] is True
    assert payload["safety_flags"]["no_network"] is True
