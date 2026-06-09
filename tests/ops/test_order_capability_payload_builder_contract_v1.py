"""Offline tests for order_capability_payload_builder_contract_v1.

Class-4 scoped: no network, credentials, orders, or Testnet execute.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_contract_v0 import DEFAULT_INSTRUMENT
from src.ops.order_capability_payload_builder_contract_v1 import (
    CANONICAL_VENUE,
    DEFAULT_ABORT_ACK_MARKER,
    DEFAULT_CLEANUP_CANCEL_CORRELATION_MARKER,
    DEFAULT_KILL_SWITCH_BINDING_MARKER,
    DEFAULT_MAX_LOSS_CAP_EUR,
    DEFAULT_MAX_NOTIONAL_EUR,
    DEFAULT_SESSION_DURATION_SECONDS,
    DEFAULT_STATUS,
    FORBIDDEN_SERIALIZATION_KEYS,
    PACKAGE_MARKER,
    PayloadBuildError,
    OrderCapabilityPayloadInput,
    build_order_capability_payload,
    serialize_order_capability_payload,
)

CONTRACT_MODULE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "ops"
    / "order_capability_payload_builder_contract_v1.py"
)

TEST_PACKAGE_MARKER = "ORDER_CAPABILITY_PAYLOAD_BUILDER_CONTRACT_V1_TEST=true"
OPERATOR_GO_BINDING = "GO_ORDER_CAPABILITY_PAYLOAD_BUILDER_CONTRACT_IMPL_V1"


def _valid_input(**overrides: object) -> OrderCapabilityPayloadInput:
    base = {
        "instrument": DEFAULT_INSTRUMENT,
        "venue": CANONICAL_VENUE,
        "environment": "demo_testnet_only",
        "side": "buy",
        "order_type": "limit",
        "limit_price": 100.0,
        "quantity": 0.01,
        "max_notional_eur": DEFAULT_MAX_NOTIONAL_EUR,
        "max_loss_cap_eur": DEFAULT_MAX_LOSS_CAP_EUR,
        "session_duration_seconds": DEFAULT_SESSION_DURATION_SECONDS,
        "operator_go_token_binding": OPERATOR_GO_BINDING,
        "abort_ack_marker": DEFAULT_ABORT_ACK_MARKER,
        "time_in_force": "GTC",
        "post_only": False,
        "reduce_only": False,
        "kill_switch_binding_marker": DEFAULT_KILL_SWITCH_BINDING_MARKER,
        "cleanup_cancel_correlation_marker": DEFAULT_CLEANUP_CANCEL_CORRELATION_MARKER,
        "evidence_correlation_id": "ev-test-001",
    }
    base.update(overrides)
    return OrderCapabilityPayloadInput(**base)


def test_package_marker_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_happy_path_deterministic_payload_with_safety_flags() -> None:
    inp = _valid_input()
    payload = build_order_capability_payload(inp)
    assert payload.status == DEFAULT_STATUS
    assert payload.no_submit is True
    assert payload.no_network is True
    assert payload.execute_authorized is False
    assert payload.order_submission_executed is False
    assert payload.cancel_executed is False
    assert payload.trade_position_mutation_executed is False
    assert payload.no_authority_change is True
    assert payload.preflight_remains_blocked is True
    assert payload.live_ready is False
    assert payload.dashboard_truth_granted is False
    assert payload.client_order_id == payload.idempotency_key
    assert payload.client_order_id.startswith("ocpb-")


def test_missing_side_fail_closed() -> None:
    with pytest.raises(PayloadBuildError, match="side"):
        build_order_capability_payload(_valid_input(side=""))


def test_missing_limit_price_fail_closed() -> None:
    with pytest.raises(PayloadBuildError, match="limit_price"):
        build_order_capability_payload(_valid_input(limit_price=0))


def test_negative_limit_price_fail_closed() -> None:
    with pytest.raises(PayloadBuildError, match="limit_price"):
        build_order_capability_payload(_valid_input(limit_price=-1.0))


def test_missing_quantity_fail_closed() -> None:
    with pytest.raises(PayloadBuildError, match="quantity"):
        build_order_capability_payload(_valid_input(quantity=0))


def test_negative_quantity_fail_closed() -> None:
    with pytest.raises(PayloadBuildError, match="quantity"):
        build_order_capability_payload(_valid_input(quantity=-0.01))


def test_live_environment_rejected() -> None:
    with pytest.raises(PayloadBuildError, match="environment"):
        build_order_capability_payload(_valid_input(environment="live"))


def test_prod_environment_rejected() -> None:
    with pytest.raises(PayloadBuildError, match="environment"):
        build_order_capability_payload(_valid_input(environment="production"))


def test_mainnet_environment_rejected() -> None:
    with pytest.raises(PayloadBuildError, match="environment"):
        build_order_capability_payload(_valid_input(environment="mainnet"))


def test_notional_cap_enforced() -> None:
    with pytest.raises(PayloadBuildError, match="notional"):
        build_order_capability_payload(
            _valid_input(limit_price=1000.0, quantity=0.02, max_notional_eur=10.0)
        )


def test_max_loss_cap_lte_max_notional_enforced() -> None:
    with pytest.raises(PayloadBuildError, match="max_loss_cap_eur"):
        build_order_capability_payload(_valid_input(max_loss_cap_eur=11.0, max_notional_eur=10.0))


def test_missing_operator_token_rejected() -> None:
    with pytest.raises(PayloadBuildError, match="operator_go_token_binding"):
        build_order_capability_payload(_valid_input(operator_go_token_binding=""))


def test_abort_ack_marker_not_confirmed_rejected() -> None:
    with pytest.raises(PayloadBuildError, match="abort_ack_marker"):
        build_order_capability_payload(_valid_input(abort_ack_marker="PENDING"))


def test_serialized_output_excludes_secret_like_fields() -> None:
    payload = build_order_capability_payload(_valid_input())
    data = serialize_order_capability_payload(payload)
    for key in data:
        assert key.lower() not in FORBIDDEN_SERIALIZATION_KEYS


def test_deterministic_idempotency_and_correlation_stable() -> None:
    inp = _valid_input()
    first = build_order_capability_payload(inp)
    second = build_order_capability_payload(inp)
    assert first.client_order_id == second.client_order_id
    assert first.evidence_correlation_id == second.evidence_correlation_id


def test_auto_evidence_correlation_id_deterministic() -> None:
    inp = _valid_input(evidence_correlation_id="")
    first = build_order_capability_payload(inp)
    second = build_order_capability_payload(inp)
    assert first.evidence_correlation_id == second.evidence_correlation_id
    assert first.evidence_correlation_id.startswith("evcorr-")


def test_order_type_other_than_limit_rejected() -> None:
    with pytest.raises(PayloadBuildError, match="order_type"):
        build_order_capability_payload(_valid_input(order_type="market"))


def test_non_canonical_venue_rejected() -> None:
    with pytest.raises(PayloadBuildError, match="venue"):
        build_order_capability_payload(_valid_input(venue="kraken_live"))


def test_empty_instrument_rejected() -> None:
    with pytest.raises(PayloadBuildError, match="instrument"):
        build_order_capability_payload(_valid_input(instrument=""))
