"""Offline tests for order_capability_side_price_qty_rules_contract_v1.

Class-4 scoped: no network, credentials, orders, or Testnet execute.
"""

from __future__ import annotations

import ast
import math
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_contract_v0 import DEFAULT_INSTRUMENT
from src.ops.order_capability_side_price_qty_rules_contract_v1 import (
    FORBIDDEN_SERIALIZATION_KEYS,
    PACKAGE_MARKER,
    REASON_LIVE_ENVIRONMENT_REJECTED,
    REASON_LOSS_CAP_REFERENCE_MISSING,
    REASON_MISSING_CORRELATION,
    REASON_MISSING_INSTRUMENT_RULES,
    REASON_MISSING_LIMIT_PRICE,
    REASON_MISSING_QUANTITY,
    REASON_NON_FINITE_LIMIT_PRICE,
    REASON_NON_FINITE_QUANTITY,
    REASON_NOTIONAL_ABOVE_MAX,
    REASON_PRICE_OUT_OF_POLICY_BOUNDS,
    REASON_PRICE_TICK_MISMATCH,
    REASON_QUANTITY_ABOVE_MAX,
    REASON_QUANTITY_BELOW_MIN,
    REASON_QUANTITY_NOT_POSITIVE,
    REASON_QUANTITY_STEP_MISMATCH,
    REASON_SIDE_POLICY_MISMATCH,
    REASON_UNSUPPORTED_POST_ONLY,
    REASON_UNSUPPORTED_REDUCE_ONLY,
    REASON_UNSUPPORTED_SIDE,
    REASON_UNSUPPORTED_TIME_IN_FORCE,
    REASON_UNSAFE_AUTHORITY_FLAGS,
    SidePriceQtyRulesError,
    SidePriceQtyVerdictKind,
    OrderCapabilityInstrumentRulesSummary,
    OrderCapabilitySidePriceQtyInput,
    OrderCapabilitySidePriceQtyPolicy,
    default_order_capability_side_price_qty_policy,
    evaluate_order_capability_side_price_qty_rules,
    map_side_price_qty_verdict_to_payload_builder_flag,
    serialize_order_capability_side_price_qty_verdict,
    validate_order_capability_side_price_qty_verdict,
)

CONTRACT_MODULE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "ops"
    / "order_capability_side_price_qty_rules_contract_v1.py"
)

TEST_PACKAGE_MARKER = "ORDER_CAPABILITY_SIDE_PRICE_QTY_RULES_CONTRACT_V1_TEST=true"
OPERATOR_GO_BINDING = "GO_ORDER_CAPABILITY_SIDE_PRICE_QTY_RULES_CONTRACT_IMPL_V1"


def _valid_instrument_rules(**overrides: object) -> OrderCapabilityInstrumentRulesSummary:
    base = {
        "instrument": DEFAULT_INSTRUMENT,
        "price_tick": Decimal("0.5"),
        "quantity_step": Decimal("0.001"),
        "min_quantity": Decimal("0.001"),
        "max_quantity": Decimal("100.0"),
        "metadata_source": "governed_metadata_snapshot_fixture",
        "metadata_verified_offline": True,
    }
    base.update(overrides)
    return OrderCapabilityInstrumentRulesSummary(**base)


def _valid_policy(**overrides: object) -> OrderCapabilitySidePriceQtyPolicy:
    base = {
        "allowed_sides": frozenset({"buy", "sell"}),
        "allow_long_short_aliases": False,
        "allowed_time_in_force": frozenset({"gtc", "ioc"}),
        "reduce_only_supported": False,
        "post_only_supported": False,
        "require_explicit_loss_cap_reference": True,
        "max_notional_eur": Decimal("10.0"),
        "max_loss_cap_eur": Decimal("1.0"),
        "optional_min_limit_price": None,
        "optional_max_limit_price": None,
    }
    base.update(overrides)
    return OrderCapabilitySidePriceQtyPolicy(**base)


def _valid_input(**overrides: object) -> OrderCapabilitySidePriceQtyInput:
    base = {
        "instrument_rules": _valid_instrument_rules(),
        "policy": _valid_policy(),
        "environment": "demo_testnet_only",
        "side": "buy",
        "limit_price": 100.0,
        "quantity": 0.01,
        "time_in_force": "GTC",
        "post_only": False,
        "reduce_only": False,
        "max_notional_eur": 10.0,
        "max_loss_cap_eur": 1.0,
        "evidence_correlation_id": "ev-spq-test-001",
        "execute_authorized": False,
        "cancel_authorized": False,
        "flatten_authorized": False,
    }
    base.update(overrides)
    return OrderCapabilitySidePriceQtyInput(**base)


def test_package_marker_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert OPERATOR_GO_BINDING
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_happy_path_valid_for_dry_payload_only() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input())
    assert verdict.verdict == SidePriceQtyVerdictKind.VALID_FOR_DRY_ORDER_CAPABILITY_PAYLOAD_ONLY
    assert verdict.side_price_qty_rules_satisfied is True
    assert verdict.reason_codes == ()
    assert verdict.normalized_side == "buy"
    assert verdict.computed_notional_eur == Decimal("1.0")
    assert verdict.safety_flags["execute_authorized"] is False
    assert verdict.safety_flags["preflight_remains_blocked"] is True
    validate_order_capability_side_price_qty_verdict(verdict)


def test_buy_side_valid() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(side="buy"))
    assert verdict.normalized_side == "buy"
    assert verdict.verdict == SidePriceQtyVerdictKind.VALID_FOR_DRY_ORDER_CAPABILITY_PAYLOAD_ONLY


def test_sell_side_valid() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(side="sell"))
    assert verdict.normalized_side == "sell"
    assert verdict.verdict == SidePriceQtyVerdictKind.VALID_FOR_DRY_ORDER_CAPABILITY_PAYLOAD_ONLY


def test_long_alias_when_policy_allows() -> None:
    policy = _valid_policy(allow_long_short_aliases=True)
    verdict = evaluate_order_capability_side_price_qty_rules(
        _valid_input(policy=policy, side="long")
    )
    assert verdict.normalized_side == "buy"
    assert verdict.verdict == SidePriceQtyVerdictKind.VALID_FOR_DRY_ORDER_CAPABILITY_PAYLOAD_ONLY


def test_short_alias_when_policy_allows() -> None:
    policy = _valid_policy(allow_long_short_aliases=True)
    verdict = evaluate_order_capability_side_price_qty_rules(
        _valid_input(policy=policy, side="short")
    )
    assert verdict.normalized_side == "sell"
    assert verdict.verdict == SidePriceQtyVerdictKind.VALID_FOR_DRY_ORDER_CAPABILITY_PAYLOAD_ONLY


def test_unsupported_side_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(side="hold"))
    assert verdict.verdict == SidePriceQtyVerdictKind.FAIL_CLOSED
    assert REASON_UNSUPPORTED_SIDE in verdict.reason_codes


def test_side_policy_mismatch_fail_closed() -> None:
    policy = _valid_policy(allowed_sides=frozenset({"sell"}))
    verdict = evaluate_order_capability_side_price_qty_rules(
        _valid_input(policy=policy, side="buy")
    )
    assert verdict.verdict == SidePriceQtyVerdictKind.FAIL_CLOSED
    assert REASON_SIDE_POLICY_MISMATCH in verdict.reason_codes


def test_missing_limit_price_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(limit_price=None))
    assert REASON_MISSING_LIMIT_PRICE in verdict.reason_codes


def test_non_finite_limit_price_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(limit_price=math.inf))
    assert REASON_NON_FINITE_LIMIT_PRICE in verdict.reason_codes
    verdict_nan = evaluate_order_capability_side_price_qty_rules(_valid_input(limit_price=math.nan))
    assert REASON_NON_FINITE_LIMIT_PRICE in verdict_nan.reason_codes


def test_non_positive_limit_price_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(limit_price=-1.0))
    assert "LIMIT_PRICE_NOT_POSITIVE" in verdict.reason_codes


def test_price_tick_mismatch_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(limit_price=100.3))
    assert REASON_PRICE_TICK_MISMATCH in verdict.reason_codes


def test_price_out_of_policy_bounds_fail_closed() -> None:
    policy = _valid_policy(optional_min_limit_price=Decimal("200.0"))
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(policy=policy))
    assert REASON_PRICE_OUT_OF_POLICY_BOUNDS in verdict.reason_codes


def test_missing_quantity_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(quantity=None))
    assert REASON_MISSING_QUANTITY in verdict.reason_codes


def test_non_finite_quantity_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(quantity=math.inf))
    assert REASON_NON_FINITE_QUANTITY in verdict.reason_codes


def test_non_positive_quantity_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(quantity=-0.01))
    assert REASON_QUANTITY_NOT_POSITIVE in verdict.reason_codes


def test_quantity_step_mismatch_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(quantity=0.0105))
    assert REASON_QUANTITY_STEP_MISMATCH in verdict.reason_codes


def test_quantity_below_min_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(quantity=0.0005))
    assert REASON_QUANTITY_BELOW_MIN in verdict.reason_codes


def test_quantity_above_max_fail_closed() -> None:
    rules = _valid_instrument_rules(max_quantity=Decimal("0.005"))
    verdict = evaluate_order_capability_side_price_qty_rules(
        _valid_input(instrument_rules=rules, quantity=0.01)
    )
    assert REASON_QUANTITY_ABOVE_MAX in verdict.reason_codes


def test_notional_above_max_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(
        _valid_input(limit_price=100.0, quantity=0.2, max_notional_eur=10.0)
    )
    assert REASON_NOTIONAL_ABOVE_MAX in verdict.reason_codes


def test_missing_loss_cap_reference_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(max_loss_cap_eur=0))
    assert REASON_LOSS_CAP_REFERENCE_MISSING in verdict.reason_codes


def test_reduce_only_unsupported_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(reduce_only=True))
    assert REASON_UNSUPPORTED_REDUCE_ONLY in verdict.reason_codes


def test_post_only_unsupported_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(post_only=True))
    assert REASON_UNSUPPORTED_POST_ONLY in verdict.reason_codes


def test_unsupported_time_in_force_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(time_in_force="FOK"))
    assert REASON_UNSUPPORTED_TIME_IN_FORCE in verdict.reason_codes


def test_missing_instrument_rules_fail_closed() -> None:
    rules = _valid_instrument_rules(metadata_verified_offline=False)
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(instrument_rules=rules))
    assert REASON_MISSING_INSTRUMENT_RULES in verdict.reason_codes


def test_live_environment_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(environment="live"))
    assert REASON_LIVE_ENVIRONMENT_REJECTED in verdict.reason_codes


def test_prod_environment_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(environment="production"))
    assert REASON_LIVE_ENVIRONMENT_REJECTED in verdict.reason_codes


def test_mainnet_environment_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(environment="mainnet"))
    assert REASON_LIVE_ENVIRONMENT_REJECTED in verdict.reason_codes


def test_missing_correlation_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(
        _valid_input(evidence_correlation_id="")
    )
    assert REASON_MISSING_CORRELATION in verdict.reason_codes


def test_unsafe_authority_flags_fail_closed() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(execute_authorized=True))
    assert REASON_UNSAFE_AUTHORITY_FLAGS in verdict.reason_codes
    assert "EXECUTION_FIELDS_NOT_DRY_ONLY" in verdict.reason_codes


def test_decimal_alignment_avoids_float_rounding() -> None:
    rules = _valid_instrument_rules(price_tick=Decimal("0.1"), quantity_step=Decimal("0.1"))
    ok = evaluate_order_capability_side_price_qty_rules(
        _valid_input(instrument_rules=rules, limit_price=1.3, quantity=0.1)
    )
    assert ok.verdict == SidePriceQtyVerdictKind.VALID_FOR_DRY_ORDER_CAPABILITY_PAYLOAD_ONLY
    bad = evaluate_order_capability_side_price_qty_rules(
        _valid_input(instrument_rules=rules, limit_price=1.31, quantity=0.1)
    )
    assert REASON_PRICE_TICK_MISMATCH in bad.reason_codes


def test_serialization_stable_secret_free() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input())
    data = serialize_order_capability_side_price_qty_verdict(verdict)
    for key in data:
        assert key.lower() not in FORBIDDEN_SERIALIZATION_KEYS
    for key in data["safety_flags"]:
        assert key.lower() not in FORBIDDEN_SERIALIZATION_KEYS


def test_deterministic_output_same_input() -> None:
    inp = _valid_input()
    first = evaluate_order_capability_side_price_qty_rules(inp)
    second = evaluate_order_capability_side_price_qty_rules(inp)
    assert first == second


def test_map_verdict_to_payload_builder_flag() -> None:
    valid = evaluate_order_capability_side_price_qty_rules(_valid_input())
    invalid = evaluate_order_capability_side_price_qty_rules(_valid_input(side="hold"))
    assert map_side_price_qty_verdict_to_payload_builder_flag(valid) is True
    assert map_side_price_qty_verdict_to_payload_builder_flag(invalid) is False


def test_validate_verdict_raises_on_invalid_flags() -> None:
    valid = evaluate_order_capability_side_price_qty_rules(_valid_input())
    bad_flags = SidePriceQtyVerdictKind.FAIL_CLOSED, valid.reason_codes, valid.normalized_side
    with pytest.raises(SidePriceQtyRulesError):
        validate_order_capability_side_price_qty_verdict(
            type(valid)(
                verdict=bad_flags[0],
                reason_codes=("UNSUPPORTED_SIDE",),
                normalized_side=None,
                computed_notional_eur=None,
                side_price_qty_rules_satisfied=True,
                safety_flags=valid.safety_flags,
            )
        )


def test_default_policy_factory() -> None:
    policy = default_order_capability_side_price_qty_policy()
    verdict = evaluate_order_capability_side_price_qty_rules(_valid_input(policy=policy))
    assert verdict.verdict == SidePriceQtyVerdictKind.VALID_FOR_DRY_ORDER_CAPABILITY_PAYLOAD_ONLY


def test_no_execution_risk_layer_imports() -> None:
    tree = ast.parse(CONTRACT_MODULE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("src.execution")
                assert not alias.name.startswith("src.risk_layer")
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("src.execution")
            assert not node.module.startswith("src.risk_layer")
