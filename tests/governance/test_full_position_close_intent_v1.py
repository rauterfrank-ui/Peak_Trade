"""Full-close quantity and canonical intent without entry-budget substitution."""

from dataclasses import replace
from decimal import Decimal

import pytest

from src.governance.capital_risk_sizing_v1 import evaluate_full_position_close_quantity_v1
from src.governance.canonical_order_intent_v1 import (
    build_canonical_full_close_intent_v1,
    validate_canonical_order_intent_v1,
    transform_canonical_order_intent_v1_to_adapter_order_intent_v1,
)
from tests.governance.test_canonical_order_intent_v1 import _instrument


def _close(**changes):
    args = dict(
        decision_id="exit-decision",
        instrument_id="ETH-USD-PERP",
        trading_epoch="7",
        decision_outcome="exit",
        position_side="LONG",
        open_quantity=Decimal("1.23"),
        position_snapshot_ref="position-snapshot",
        binding_ref="lane-generation-binding",
        reconciliation_status="RECONCILED",
        instrument=_instrument(),
    )
    args.update(changes)
    return evaluate_full_position_close_quantity_v1(**args)


@pytest.mark.parametrize("side,order_side", [("LONG", "sell"), ("SHORT", "buy")])
def test_exit_closes_exactly_the_whole_remaining_position_without_entry_sizing(side, order_side):
    close = _close(position_side=side)
    assert close.outcome.value == "PASS"
    assert close.final_quantity == Decimal("1.23")
    built = build_canonical_full_close_intent_v1(
        close=close, intent_id="close-1", canonical_trading_logic_version="test"
    )
    assert built.intent is not None, built.reason_codes
    intent = built.intent
    assert intent.quantity == close.open_quantity
    assert intent.reduce_only and intent.position_effect == "CLOSE_ONLY"
    assert validate_canonical_order_intent_v1(intent).validation_status == "VALID"
    transformed = transform_canonical_order_intent_v1_to_adapter_order_intent_v1(intent)
    assert transformed.adapter_intent is not None, transformed.reason_codes
    assert transformed.adapter_intent.side == order_side
    assert transformed.adapter_intent.reduce_only is True
    assert not intent.submission_authorized and not intent.execution_eligible
    assert intent.authority_effect == "NONE"


@pytest.mark.parametrize(
    "changes",
    [
        {"open_quantity": Decimal("0")},
        {"open_quantity": Decimal("NaN")},
        {"open_quantity": Decimal("-1")},
        {"open_quantity": Decimal("1.234")},
        {"position_side": "NONE"},
        {"reconciliation_status": "UNKNOWN"},
        {"decision_outcome": "reduce"},
        {"binding_ref": ""},
        {"instrument": _instrument(maximum_quantity=Decimal("1"))},
        {"instrument": _instrument(contract_kind="INVERSE")},
    ],
)
def test_unresolved_or_non_executable_close_never_rounds_into_a_partial_exit(changes):
    close = _close(**changes)
    assert close.outcome.value == "BLOCKED"
    assert close.final_quantity == 0
    built = build_canonical_full_close_intent_v1(
        close=close, intent_id="close-1", canonical_trading_logic_version="test"
    )
    assert built.intent is None


def test_tampered_close_assessment_cannot_create_an_intent():
    close = replace(_close(), final_quantity=Decimal("2"))
    built = build_canonical_full_close_intent_v1(
        close=close, intent_id="close-1", canonical_trading_logic_version="test"
    )
    assert built.intent is None


def test_close_assessment_and_intent_are_deterministic():
    first, second = _close(), _close()
    assert first == second
    assert (
        first.quantity_provenance.source_contract_refs[0]
        == "full_confirmed_remaining_position_close.v1"
    )
    assert first.final_quantity == first.open_quantity
