"""Contract tests for offline capital risk sizing mathematics v1 (RUNBOOK STEP 29P)."""

from __future__ import annotations

import ast
import importlib
import inspect
import json
from decimal import Decimal
from pathlib import Path

import pytest

import src.governance.capital_risk_sizing_v1 as sizing

MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "src" / "governance" / "capital_risk_sizing_v1.py"
)

_FORBIDDEN_RUNTIME_MODULES = frozenset(
    {
        "src.execution.orchestrator",
        "src.execution.pipeline",
        "src.live.orders",
        "src.execution.adapters.base_v1",
        "src.orders.base",
    }
)

TOTAL_LIMIT_USD = Decimal("500")
ORDER_LIMIT_USD = Decimal("25")
DAILY_LOSS_LIMIT_USD = Decimal("25")


def _instrument(**overrides: object) -> sizing.InstrumentQuantityConstraintsV1:
    base: dict[str, object] = {
        "instrument_id": "ETH-USD-PERP",
        "market_type": "futures",
        "contract_kind": "LINEAR",
        "contract_multiplier": Decimal("1"),
        "quantity_step": Decimal("0.01"),
        "minimum_quantity": Decimal("0.01"),
        "maximum_quantity": Decimal("100"),
        "minimum_notional": Decimal("5"),
        "instrument_metadata_version": "futures_metadata_v1_test",
    }
    base.update(overrides)
    return sizing.InstrumentQuantityConstraintsV1(**base)  # type: ignore[arg-type]


def _input(**overrides: object) -> sizing.CapitalRiskSizingInputV1:
    instrument = _instrument()
    base: dict[str, object] = {
        "decision_id": "decision-001",
        "instrument_id": instrument.instrument_id,
        "selected_side": sizing.SelectedSide.LONG.value,
        "reference_price": Decimal("2000"),
        "protective_stop_price": Decimal("1900"),
        "stop_distance": None,
        "account_equity": TOTAL_LIMIT_USD,
        "scope_capital_limit": ORDER_LIMIT_USD,
        "per_trade_risk_limit": ORDER_LIMIT_USD,
        "total_capital_limit": TOTAL_LIMIT_USD,
        "daily_loss_remaining_budget": DAILY_LOSS_LIMIT_USD,
        "current_reconciled_exposure": Decimal("0"),
        "maximum_positions": 1,
        "current_open_positions_count": 0,
        "current_open_side": None,
        "configured_quantity_cap": None,
        "leverage_ceiling": Decimal("5"),
        "reconciliation_status": "RECONCILED",
        "policy_version": "capital_risk_sizing_policy_v1",
        "config_digest": "cfg_digest_test",
        "input_digest": "input_digest_test",
        "instrument": instrument,
    }
    base.update(overrides)
    return sizing.CapitalRiskSizingInputV1(**base)  # type: ignore[arg-type]


def _evaluate(**overrides: object) -> sizing.CapitalRiskSizingDecisionV1:
    return sizing.evaluate_capital_risk_sizing_v1(_input(**overrides))


# --- A. Happy Path ---


def test_a01_happy_path_long_passes() -> None:
    result = _evaluate()
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert result.final_quantity > 0
    assert result.quantity_provenance is not None
    assert result.quantity_provenance.final_quantity == result.final_quantity


def test_a02_happy_path_short_symmetric_quantity() -> None:
    long_result = _evaluate(
        selected_side=sizing.SelectedSide.LONG.value,
        protective_stop_price=Decimal("1900"),
    )
    short_result = _evaluate(
        selected_side=sizing.SelectedSide.SHORT.value,
        protective_stop_price=Decimal("2100"),
    )
    assert long_result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert short_result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert long_result.final_quantity == short_result.final_quantity


def test_a03_deterministic_double_run() -> None:
    first = _evaluate()
    second = _evaluate()
    assert first == second


def test_a04_stable_output_digest() -> None:
    first = _evaluate()
    second = _evaluate()
    assert first.quantity_provenance is not None
    assert second.quantity_provenance is not None
    assert first.quantity_provenance.output_digest == second.quantity_provenance.output_digest


# --- B. Monotonicity ---


def test_b01_smaller_risk_budget_does_not_increase_quantity() -> None:
    base = _evaluate(per_trade_risk_limit=ORDER_LIMIT_USD)
    reduced = _evaluate(per_trade_risk_limit=Decimal("10"))
    assert base.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert reduced.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert reduced.final_quantity <= base.final_quantity


def test_b02_smaller_capital_envelope_does_not_increase_quantity() -> None:
    base = _evaluate(scope_capital_limit=ORDER_LIMIT_USD)
    reduced = _evaluate(scope_capital_limit=Decimal("20"))
    assert base.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert reduced.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert reduced.final_quantity <= base.final_quantity


def test_b03_larger_stop_distance_does_not_increase_quantity() -> None:
    base = _evaluate(protective_stop_price=Decimal("1950"))
    wider = _evaluate(protective_stop_price=Decimal("1800"))
    assert base.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert wider.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert wider.final_quantity <= base.final_quantity


def test_b04_larger_contract_multiplier_does_not_increase_quantity() -> None:
    base = _evaluate()
    reduced = _evaluate(
        instrument=_instrument(contract_multiplier=Decimal("1.2")),
    )
    assert base.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert reduced.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert reduced.final_quantity <= base.final_quantity


def test_b05_larger_open_exposure_does_not_increase_quantity() -> None:
    base = _evaluate(current_reconciled_exposure=Decimal("0"))
    exposed = _evaluate(current_reconciled_exposure=Decimal("100"))
    assert base.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert exposed.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert exposed.final_quantity <= base.final_quantity


def test_b06_stricter_venue_max_does_not_increase_quantity() -> None:
    base = _evaluate(configured_quantity_cap=Decimal("1"))
    capped = _evaluate(configured_quantity_cap=Decimal("0.05"))
    assert base.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert capped.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert capped.final_quantity <= base.final_quantity


def test_b07_coarser_quantity_step_does_not_increase_quantity() -> None:
    base = _evaluate(
        scope_capital_limit=Decimal("100"),
        instrument=_instrument(quantity_step=Decimal("0.01")),
    )
    coarse = _evaluate(
        scope_capital_limit=Decimal("100"),
        instrument=_instrument(quantity_step=Decimal("0.02")),
    )
    assert base.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert coarse.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert coarse.final_quantity <= base.final_quantity


# --- C. Rounding ---


def test_c01_rounding_is_floor_only() -> None:
    result = _evaluate(
        per_trade_risk_limit=Decimal("12.37"),
        scope_capital_limit=Decimal("500"),
    )
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert result.canonical_sizing is not None
    assert result.final_quantity <= result.canonical_sizing.candidate_quantity
    step = _instrument().quantity_step
    assert result.final_quantity % step == 0


def test_c02_rounding_does_not_increase_risk() -> None:
    result = _evaluate()
    assert result.quantity_provenance is not None
    assert (
        result.quantity_provenance.rounded_quantity <= result.quantity_provenance.pre_round_quantity
    )


def test_c03_below_min_quantity_blocks_without_round_up() -> None:
    result = _evaluate(
        per_trade_risk_limit=Decimal("0.01"),
        instrument=_instrument(minimum_quantity=Decimal("1")),
    )
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert sizing.REASON_BELOW_MIN_QUANTITY in result.reason_codes


def test_c04_below_min_notional_blocks_without_round_up() -> None:
    result = _evaluate(
        instrument=_instrument(minimum_quantity=Decimal("0.01"), minimum_notional=Decimal("25")),
    )
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert sizing.REASON_BELOW_MIN_NOTIONAL in result.reason_codes


def test_c05_no_automatic_increase_to_minimum() -> None:
    result = _evaluate(
        per_trade_risk_limit=Decimal("0.5"),
        instrument=_instrument(minimum_quantity=Decimal("10"), minimum_notional=Decimal("1")),
    )
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert result.final_quantity < Decimal("10")


# --- D. Fail-Closed ---


@pytest.mark.parametrize(
    "kwargs,expected_reason",
    [
        ({"protective_stop_price": None, "stop_distance": None}, sizing.REASON_INVALID_STOP_PRICE),
        ({"protective_stop_price": Decimal("2000")}, sizing.REASON_ZERO_RISK_DISTANCE),
        (
            {
                "selected_side": sizing.SelectedSide.LONG.value,
                "protective_stop_price": Decimal("2100"),
            },
            sizing.REASON_INVALID_STOP_PRICE,
        ),
        (
            {"instrument": _instrument(instrument_metadata_version="")},
            sizing.REASON_MISSING_INSTRUMENT_METADATA,
        ),
        ({"reference_price": Decimal("NaN")}, sizing.REASON_NON_FINITE_INPUT),
        ({"account_equity": Decimal("-1")}, sizing.REASON_INVALID_CAPITAL_INPUT),
        ({"scope_capital_limit": Decimal("0")}, sizing.REASON_INVALID_CAPITAL_INPUT),
        ({"daily_loss_remaining_budget": Decimal("0")}, sizing.REASON_DAILY_LOSS_BUDGET_EXHAUSTED),
        ({"reconciliation_status": "UNKNOWN"}, sizing.REASON_RECONCILIATION_REQUIRED),
        ({"current_open_positions_count": 1}, sizing.REASON_MAX_POSITIONS_REACHED),
        (
            {
                "selected_side": sizing.SelectedSide.LONG.value,
                "current_open_side": sizing.SelectedSide.SHORT.value,
                "current_reconciled_exposure": Decimal("10"),
            },
            sizing.REASON_OPPOSITE_EXPOSURE_PRESENT,
        ),
        (
            {"instrument": _instrument(quantity_step=Decimal("0"))},
            sizing.REASON_INVALID_QUANTITY_STEP,
        ),
        (
            {"instrument": _instrument(contract_multiplier=Decimal("0"))},
            sizing.REASON_INVALID_CONTRACT_MULTIPLIER,
        ),
    ],
)
def test_d_fail_closed_cases(kwargs: dict[str, object], expected_reason: str) -> None:
    result = _evaluate(**kwargs)
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert expected_reason in result.reason_codes


# --- E. Limits ---


def test_e01_total_limit_not_exceeded() -> None:
    result = _evaluate()
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert result.post_sizing_risk is not None
    assert result.post_sizing_risk.projected_exposure <= TOTAL_LIMIT_USD


def test_e02_order_limit_not_exceeded() -> None:
    result = _evaluate()
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert result.post_sizing_risk is not None
    assert result.post_sizing_risk.projected_notional <= ORDER_LIMIT_USD


def test_e03_daily_loss_limit_not_exceeded() -> None:
    result = _evaluate()
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert result.post_sizing_risk is not None
    assert result.post_sizing_risk.projected_daily_loss_impact <= DAILY_LOSS_LIMIT_USD


def test_e04_max_positions_one() -> None:
    result = _evaluate(maximum_positions=1, current_open_positions_count=0)
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    blocked = _evaluate(maximum_positions=1, current_open_positions_count=1)
    assert blocked.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED


# --- F. Authority Safety ---


def test_f01_authority_flags_remain_false() -> None:
    result = _evaluate()
    assert result.execution_eligible is False
    assert result.adapter_compatible is False
    assert result.order_intent_bound is False
    assert result.authority_effect == sizing.AUTHORITY_EFFECT_NONE
    assert result.runtime_effect == sizing.RUNTIME_EFFECT_NONE
    assert result.quantity_provenance is not None
    assert result.quantity_provenance.execution_eligible is False


def test_f02_no_runtime_submission_imports() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_from = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert _FORBIDDEN_RUNTIME_MODULES.isdisjoint(imported_from)


def test_f03_no_network_clock_or_random_dependency() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "random" not in imported
    assert "time" not in imported
    assert "socket" not in imported
    assert "requests" not in imported


# --- G. Futures-only ---


def test_g01_futures_metadata_required() -> None:
    result = _evaluate(instrument=_instrument(market_type="spot"))
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert sizing.REASON_NON_FUTURES_INSTRUMENT in result.reason_codes


def test_g02_bitcoin_instrument_blocked() -> None:
    result = _evaluate(
        instrument_id="XBT-USD-PERP",
        instrument=_instrument(instrument_id="XBT-USD-PERP"),
    )
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert sizing.REASON_BITCOIN_SPECIFIC_DIRECTION in result.reason_codes


def test_g03_inverse_contract_blocked() -> None:
    result = _evaluate(instrument=_instrument(contract_kind="INVERSE"))
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert sizing.REASON_UNSUPPORTED_CONTRACT_KIND in result.reason_codes


# --- H. Boundary / schema ---


def test_h01_final_quantity_le_candidate() -> None:
    result = _evaluate()
    assert result.canonical_sizing is not None
    assert result.final_quantity <= result.canonical_sizing.candidate_quantity


def test_h02_schema_contract_complete() -> None:
    schema = sizing.capital_risk_sizing_schema_v1()
    assert schema["contract_name"] == sizing.CONTRACT_NAME
    assert schema["invariants"]["futures_only"] is True
    assert schema["invariants"]["execution_eligible"] is False


def test_h03_import_smoke() -> None:
    module = importlib.import_module("src.governance.capital_risk_sizing_v1")
    assert module.PACKAGE_MARKER == "CAPITAL_RISK_SIZING_V1=true"


def test_h04_deterministic_double_run_payload() -> None:
    payloads = []
    for _ in range(2):
        result = _evaluate()
        assert result.quantity_provenance is not None
        payloads.append(
            json.dumps(
                {
                    "outcome": result.outcome.value,
                    "final_quantity": str(result.final_quantity),
                    "output_digest": result.quantity_provenance.output_digest,
                    "reason_codes": result.reason_codes,
                },
                sort_keys=True,
            )
        )
    assert payloads[0] == payloads[1]


def test_h05_public_api_has_no_forbidden_runtime_symbols() -> None:
    forbidden = {"submit", "execute", "place_order", "grant_permission"}
    public_names = {
        name
        for name, obj in inspect.getmembers(sizing)
        if not name.startswith("_") and (inspect.isfunction(obj) or inspect.isclass(obj))
    }
    assert forbidden.isdisjoint(public_names)
