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
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
)

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


def _policy(**overrides: object) -> sizing.CapitalRiskSizingPolicyV1:
    base: dict[str, object] = {
        "policy_version": "capital_risk_sizing_policy_v1",
        "total_capital_limit_usd": TOTAL_LIMIT_USD,
        "order_limit_usd": ORDER_LIMIT_USD,
        "daily_loss_limit_usd": DAILY_LOSS_LIMIT_USD,
        "max_positions": 1,
    }
    base.update(overrides)
    return sizing.CapitalRiskSizingPolicyV1(**base)  # type: ignore[arg-type]


def _instrument(**overrides: object) -> sizing.InstrumentQuantityConstraintsV1:
    base: dict[str, object] = {
        "instrument_id": "ETH-USD-PERP",
        "market_type": "futures",
        "contract_kind": "LINEAR",
        "contract_multiplier": Decimal("1"),
        "lot_size": Decimal("0.01"),
        "minimum_quantity": Decimal("0.01"),
        "maximum_quantity": Decimal("100"),
        "minimum_notional": Decimal("5"),
        "tick_size": Decimal("0.01"),
        "instrument_metadata_version": "futures_metadata_v1_test",
    }
    base.update(overrides)
    return sizing.InstrumentQuantityConstraintsV1(**base)  # type: ignore[arg-type]


def _evidence(**overrides: object) -> CanonicalTradingDecisionEvidenceV1:
    base: dict[str, object] = {
        "decision_id": "decision-001",
        "replay_id": "replay-001",
        "instrument_id": "ETH-USD-PERP",
        "trading_epoch": 1,
        "market_context_ref": "ctx",
        "scope_initialization_ref": "init",
        "scope_event_ref": "evt",
        "bull_assessment_ref": "bull",
        "bear_assessment_ref": "bear",
        "state_switch_ref": "sw",
        "bull_survival_ref": "bs",
        "bear_survival_ref": "brs",
        "bull_suitability_ref": "bsu",
        "bear_suitability_ref": "brsu",
        "composition_result_ref": "comp",
        "entry_exit_policy_ref": "eep",
        "current_scope_ref": "cs",
        "next_scope_ref": "ns",
        "previous_direction_state": "neutral",
        "next_direction_state": "long_active",
        "selected_side": "LONG",
        "selected_strategy_ref": "strat",
        "decision_outcome": "enter_long",
        "entry_or_exit_policy_ref": "eep",
        "reason_codes": (),
        "decision_precedence_trace": (),
        "component_versions": {},
        "policy_versions": {"capital_risk_sizing_policy_v1": "v1"},
        "config_digest": "cfg_digest_test",
        "implementation_digest": sizing.IMPLEMENTATION_DIGEST,
        "input_digest": "a" * 64,
        "semantic_digest": "",
    }
    base.update(overrides)
    return CanonicalTradingDecisionEvidenceV1(**base)  # type: ignore[arg-type]


def _context(**overrides: object) -> sizing.CapitalRiskSizingContextV1:
    instrument = _instrument()
    base: dict[str, object] = {
        "reference_price": Decimal("2000"),
        "protective_stop_price": Decimal("1900"),
        "stop_distance": None,
        "account_equity": TOTAL_LIMIT_USD,
        "already_committed_capital": Decimal("0"),
        "daily_loss_consumed": Decimal("0"),
        "current_reconciled_exposure": Decimal("0"),
        "reconciled_open_position_quantity": Decimal("0"),
        "current_open_positions_count": 0,
        "current_open_side": None,
        "reconciliation_status": "RECONCILED",
        "configured_quantity_cap": None,
        "leverage_ceiling": Decimal("5"),
        "instrument": instrument,
        "config_digest": "cfg_digest_test",
    }
    base.update(overrides)
    return sizing.CapitalRiskSizingContextV1(**base)  # type: ignore[arg-type]


def _evaluate_chain(**overrides: object) -> sizing.CapitalRiskSizingChainResultV1:
    ctx_overrides = {k: v for k, v in overrides.items() if k in _context().__dataclass_fields__}
    ev_overrides = {k: v for k, v in overrides.items() if k in _evidence().__dataclass_fields__}
    pol_overrides = {k: v for k, v in overrides.items() if k in _policy().__dataclass_fields__}
    return sizing.evaluate_quantity_chain_v1(
        _evidence(**ev_overrides),
        _context(**ctx_overrides),
        _policy(**pol_overrides),
    )


def _input(**overrides: object) -> sizing.CapitalRiskSizingInputV1:
    instrument = _instrument()
    base: dict[str, object] = {
        "decision_id": "decision-001",
        "instrument_id": instrument.instrument_id,
        "selected_side": "LONG",
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
        "input_digest": "a" * 64,
        "instrument": instrument,
        "decision_outcome": "enter_long",
    }
    base.update(overrides)
    return sizing.CapitalRiskSizingInputV1(**base)  # type: ignore[arg-type]


def _evaluate(**overrides: object) -> sizing.CapitalRiskSizingDecisionV1:
    return sizing.evaluate_capital_risk_sizing_v1(_input(**overrides))


# --- A. Happy Path ---


def test_a01_happy_path_long_passes() -> None:
    result = _evaluate_chain()
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert result.final_quantity > 0
    assert result.quantity_provenance is not None
    assert result.quantity_provenance.final_quantity == result.final_quantity


def test_a02_happy_path_short_symmetric_quantity() -> None:
    long_result = _evaluate_chain(
        selected_side="LONG",
        decision_outcome="enter_long",
        protective_stop_price=Decimal("1900"),
    )
    short_result = _evaluate_chain(
        selected_side="SHORT",
        decision_outcome="enter_short",
        protective_stop_price=Decimal("2100"),
    )
    assert long_result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert short_result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert long_result.final_quantity == short_result.final_quantity


def test_a03_deterministic_double_run() -> None:
    first = _evaluate_chain()
    second = _evaluate_chain()
    assert first == second


def test_a04_provenance_complete() -> None:
    result = _evaluate_chain()
    prov = result.quantity_provenance
    assert prov is not None
    assert prov.authority_effect == sizing.AUTHORITY_EFFECT_NONE
    assert prov.runtime_effect == sizing.RUNTIME_EFFECT_NONE
    assert prov.adapter_compatible is False
    assert len(prov.source_contract_refs) >= 3


# --- B. Monotonicity ---


def test_b01_smaller_risk_budget_does_not_increase_quantity() -> None:
    base = _evaluate_chain()
    reduced = _evaluate_chain(order_limit_usd=Decimal("20"))
    assert base.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert reduced.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert reduced.final_quantity <= base.final_quantity


def test_b02_smaller_capital_does_not_increase_quantity() -> None:
    base = _evaluate_chain(account_equity=TOTAL_LIMIT_USD)
    reduced = _evaluate_chain(account_equity=Decimal("100"))
    assert base.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert reduced.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert reduced.final_quantity <= base.final_quantity


def test_b03_larger_stop_distance_does_not_increase_quantity() -> None:
    base = _evaluate_chain(protective_stop_price=Decimal("1950"))
    wider = _evaluate_chain(protective_stop_price=Decimal("1800"))
    assert base.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert wider.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert wider.final_quantity <= base.final_quantity


def test_b04_larger_open_exposure_does_not_increase_quantity() -> None:
    base = _evaluate_chain(current_reconciled_exposure=Decimal("0"))
    exposed = _evaluate_chain(current_reconciled_exposure=Decimal("100"))
    assert base.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert exposed.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert exposed.final_quantity <= base.final_quantity


def test_b05_coarser_lot_size_does_not_increase_quantity() -> None:
    base = _evaluate_chain(
        order_limit_usd=Decimal("50"),
        instrument=_instrument(lot_size=Decimal("0.01")),
    )
    coarse = _evaluate_chain(
        order_limit_usd=Decimal("50"),
        instrument=_instrument(lot_size=Decimal("0.02")),
    )
    assert base.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert coarse.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert coarse.final_quantity <= base.final_quantity


def test_b06_monotone_chain_fields() -> None:
    result = _evaluate_chain()
    assert result.pre_sizing_risk is not None
    assert result.canonical_position_sizing is not None
    assert result.post_sizing_risk is not None
    pre = result.pre_sizing_risk.candidate_quantity_upper_bound
    bounded = result.canonical_position_sizing.bounded_quantity_before_rounding
    rounded = result.canonical_position_sizing.rounded_quantity
    final = result.post_sizing_risk.final_allowed_quantity
    assert pre >= bounded >= rounded >= final >= 0


# --- C. Rounding ---


def test_c01_rounding_is_floor_only() -> None:
    result = _evaluate(
        per_trade_risk_limit=Decimal("12.37"),
        scope_capital_limit=Decimal("500"),
    )
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    sizing_result = result.canonical_position_sizing
    assert sizing_result is not None
    assert result.final_quantity <= sizing_result.bounded_quantity_before_rounding
    assert result.final_quantity % _instrument().lot_size == 0


def test_c02_below_min_quantity_blocks_without_round_up() -> None:
    result = _evaluate_chain(
        order_limit_usd=Decimal("0.01"),
        instrument=_instrument(minimum_quantity=Decimal("1")),
    )
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert sizing.REASON_BELOW_MIN_QUANTITY in result.reason_codes


def test_c03_below_min_notional_blocks_without_round_up() -> None:
    result = _evaluate_chain(
        order_limit_usd=Decimal("20"),
        instrument=_instrument(minimum_quantity=Decimal("0.01"), minimum_notional=Decimal("25")),
    )
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert sizing.REASON_BELOW_MIN_NOTIONAL in result.reason_codes


# --- D. Fail-Closed ---


@pytest.mark.parametrize(
    "kwargs,expected_reason",
    [
        ({"protective_stop_price": None, "stop_distance": None}, sizing.REASON_INVALID_STOP_PRICE),
        ({"protective_stop_price": Decimal("2000")}, sizing.REASON_ZERO_RISK_DISTANCE),
        (
            {"selected_side": "LONG", "protective_stop_price": Decimal("2100")},
            sizing.REASON_INVALID_STOP_PRICE,
        ),
        (
            {"instrument": _instrument(instrument_metadata_version="")},
            sizing.REASON_MISSING_INSTRUMENT_METADATA,
        ),
        ({"reference_price": Decimal("NaN")}, sizing.REASON_NON_FINITE_INPUT),
        ({"account_equity": Decimal("-1")}, sizing.REASON_INVALID_CAPITAL_INPUT),
        ({"daily_loss_consumed": DAILY_LOSS_LIMIT_USD}, sizing.REASON_DAILY_LOSS_BUDGET_EXHAUSTED),
        ({"reconciliation_status": "UNKNOWN"}, sizing.REASON_RECONCILIATION_REQUIRED),
        ({"current_open_positions_count": 1}, sizing.REASON_MAX_POSITIONS_REACHED),
        (
            {
                "selected_side": "LONG",
                "current_open_side": "SHORT",
                "reconciled_open_position_quantity": Decimal("10"),
                "current_reconciled_exposure": Decimal("10"),
            },
            sizing.REASON_OPPOSITE_EXPOSURE_PRESENT,
        ),
        ({"instrument": _instrument(lot_size=Decimal("0"))}, sizing.REASON_INVALID_QUANTITY_STEP),
        (
            {"instrument": _instrument(contract_multiplier=Decimal("0"))},
            sizing.REASON_INVALID_CONTRACT_MULTIPLIER,
        ),
        ({"decision_outcome": "hold"}, sizing.REASON_NON_ENTRY_OUTCOME),
    ],
)
def test_d_fail_closed_cases(kwargs: dict[str, object], expected_reason: str) -> None:
    result = _evaluate_chain(**kwargs)
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert expected_reason in result.reason_codes


# --- E. Limits ---


def test_e01_total_limit_not_exceeded() -> None:
    result = _evaluate_chain()
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert result.post_sizing_risk is not None
    assert result.post_sizing_risk.exposure_after <= TOTAL_LIMIT_USD


def test_e02_order_limit_not_exceeded() -> None:
    result = _evaluate_chain()
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert result.post_sizing_risk is not None
    assert result.post_sizing_risk.resulting_notional <= ORDER_LIMIT_USD


def test_e03_daily_loss_limit_not_exceeded() -> None:
    result = _evaluate_chain()
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert result.post_sizing_risk is not None
    assert result.post_sizing_risk.resulting_max_loss <= DAILY_LOSS_LIMIT_USD


def test_e04_max_positions_one() -> None:
    result = _evaluate_chain(max_positions=1, current_open_positions_count=0)
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    blocked = _evaluate_chain(max_positions=1, current_open_positions_count=1)
    assert blocked.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED


# --- F. Entry / Reduce / Exit ---


def test_f01_reduce_bounded_by_open_position() -> None:
    result = _evaluate_chain(
        decision_outcome="reduce",
        reconciled_open_position_quantity=Decimal("0.05"),
        current_open_side="LONG",
        selected_side="LONG",
        current_open_positions_count=1,
        current_reconciled_exposure=Decimal("100"),
    )
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert result.final_quantity <= Decimal("0.05")


def test_f02_exit_requires_open_position() -> None:
    result = _evaluate_chain(
        decision_outcome="exit",
        reconciled_open_position_quantity=Decimal("0"),
    )
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert sizing.REASON_NO_OPEN_POSITION_FOR_REDUCE in result.reason_codes


def test_f03_reduce_exceeds_open_position_capped() -> None:
    result = _evaluate_chain(
        decision_outcome="reduce",
        reconciled_open_position_quantity=Decimal("0.02"),
        current_open_side="LONG",
        selected_side="LONG",
        current_open_positions_count=1,
        current_reconciled_exposure=Decimal("40"),
        order_limit_usd=Decimal("100"),
    )
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert result.final_quantity <= Decimal("0.02")


# --- G. Authority Safety ---


def test_g01_authority_flags_remain_none() -> None:
    result = _evaluate_chain()
    assert result.authority_effect == sizing.AUTHORITY_EFFECT_NONE
    assert result.runtime_effect == sizing.RUNTIME_EFFECT_NONE
    assert result.adapter_compatible is False


def test_g02_no_runtime_submission_imports() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_from = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert _FORBIDDEN_RUNTIME_MODULES.isdisjoint(imported_from)


def test_g03_bypass_scan_flags() -> None:
    scan = sizing.export_bypass_scan_v1()
    assert scan["DIRECT_DECISION_TO_QUANTITY_PATH_BLOCKED"] is True
    assert scan["QUANTITY_WITHOUT_PROVENANCE_BLOCKED"] is True
    assert scan["RISK_INCREASING_ROUNDING_BLOCKED"] is True
    assert scan["FORBIDDEN_RUNTIME_IMPORTS_IN_OWNER"] == []


# --- H. Futures-only ---


def test_h01_futures_metadata_required() -> None:
    result = _evaluate_chain(instrument=_instrument(market_type="spot"))
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert sizing.REASON_NON_FUTURES_INSTRUMENT in result.reason_codes


def test_h02_bitcoin_instrument_blocked() -> None:
    result = _evaluate_chain(
        instrument_id="XBT-USD-PERP",
        instrument=_instrument(instrument_id="XBT-USD-PERP"),
    )
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert sizing.REASON_BITCOIN_SPECIFIC_DIRECTION in result.reason_codes


def test_h03_inverse_contract_blocked() -> None:
    result = _evaluate_chain(instrument=_instrument(contract_kind="INVERSE"))
    assert result.outcome is sizing.CapitalRiskSizingOutcome.BLOCKED
    assert sizing.REASON_UNSUPPORTED_CONTRACT_KIND in result.reason_codes


# --- I. Legacy adapter ---


def test_i01_legacy_adapter_passes() -> None:
    result = _evaluate()
    assert result.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert result.final_quantity > 0


def test_i02_schema_contract_complete() -> None:
    schema = sizing.capital_risk_sizing_schema_v1()
    assert schema["contract_name"] == sizing.CONTRACT_NAME
    assert schema["invariants"]["futures_only"] is True
    assert schema["invariants"]["adapter_compatible"] is False


def test_i03_import_smoke() -> None:
    module = importlib.import_module("src.governance.capital_risk_sizing_v1")
    assert module.PACKAGE_MARKER == "CAPITAL_RISK_SIZING_V1=true"


def test_i04_deterministic_payload() -> None:
    payloads = []
    for _ in range(2):
        result = _evaluate_chain()
        payloads.append(
            json.dumps(
                {
                    "outcome": result.outcome.value,
                    "final_quantity": str(result.final_quantity),
                    "reason_codes": result.reason_codes,
                },
                sort_keys=True,
            )
        )
    assert payloads[0] == payloads[1]


def test_i05_public_api_has_no_forbidden_runtime_symbols() -> None:
    forbidden = {"submit", "execute", "place_order", "grant_permission"}
    public_names = {
        name
        for name, obj in inspect.getmembers(sizing)
        if not name.startswith("_") and (inspect.isfunction(obj) or inspect.isclass(obj))
    }
    assert forbidden.isdisjoint(public_names)
