"""MV2 research wiring v1: backtest boundary chain integration."""

from __future__ import annotations

import json
from pathlib import Path

from src.backtest.mv2_research_wiring_v1 import (
    CanonicalOrderIntentBacktestStateFileBindingConfigV1,
    CapitalRiskSizingBacktestStateFileBindingConfigV1,
    KillSwitchBacktestStateFileBindingConfigV1,
    ReconciliationBacktestStateFileBindingConfigV1,
    SafetyKernelBacktestStateFileBindingConfigV1,
    run_mv2_research_backtest_wiring_v1,
)
from meta.learning_loop.runtime_state_reconciliation_v1 import RECONCILIATION_CONTRACT_VERSION
from src.governance.canonical_order_intent_v1 import (
    CONTRACT_VERSION as CANONICAL_ORDER_INTENT_CONTRACT_VERSION,
)
from src.governance.capital_risk_sizing_v1 import (
    CONTRACT_VERSION as CAPITAL_RISK_SIZING_CONTRACT_VERSION,
)
from src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1 import (
    KILL_SWITCH_CONTRACT_DIGEST,
)
from src.meta.learning_loop.runtime_eligibility_v1 import (
    CONTRACT_NAME as RUNTIME_ELIGIBILITY_CONTRACT_NAME,
)
from trading.master_v2.canonical_order_intent_boundary_backtest_state_file_binding_adapter_v0 import (
    CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0,
)
from trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0 as sizing_digest,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
)
from trading.master_v2.killswitch_boundary_backtest_state_file_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0 as killswitch_digest,
)
from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KillSwitchBoundaryMode,
)
from trading.master_v2.reconciliation_boundary_backtest_state_file_binding_adapter_v0 import (
    RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0 as reconciliation_digest,
)
from trading.master_v2.safety_kernel_boundary_backtest_state_file_binding_adapter_v0 import (
    SAFETY_KERNEL_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0 as safety_kernel_digest,
)
from tests.backtest.test_mv2_research_wiring_v1 import _bars, _cfg


def _sizing_payload() -> dict[str, object]:
    base = {
        "schema_version": CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "instrument_id": "inst-eth-usdt-perp",
        "reference_price": "3500",
        "protective_stop_price": "3400",
        "account_equity": "10000",
        "scope_capital_limit": "500",
        "per_trade_risk_limit": "25",
        "total_capital_limit": "500",
        "daily_loss_remaining_budget": "25",
        "current_reconciled_exposure": "0",
        "lot_size": "0.01",
        "minimum_quantity": "0.01",
        "maximum_quantity": "100",
        "minimum_notional": "5",
        "tick_size": "0.01",
        "capital_risk_sizing_owner_digest_ref": CAPITAL_RISK_SIZING_CONTRACT_VERSION,
    }
    return {**base, "state_file_digest_ref": sizing_digest(base)}


def _order_intent_payload() -> dict[str, object]:
    base = {
        "schema_version": CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "instrument_id": "inst-eth-usdt-perp",
        "reference_price": "3500",
        "protective_stop_price": "3400",
        "account_equity": "10000",
        "scope_capital_limit": "500",
        "per_trade_risk_limit": "25",
        "total_capital_limit": "500",
        "daily_loss_remaining_budget": "25",
        "current_reconciled_exposure": "0",
        "lot_size": "0.01",
        "minimum_quantity": "0.01",
        "maximum_quantity": "100",
        "minimum_notional": "5",
        "tick_size": "0.01",
        "canonical_order_intent_owner_digest_ref": CANONICAL_ORDER_INTENT_CONTRACT_VERSION,
    }
    return {
        **base,
        "state_file_digest_ref": compute_backtest_state_file_digest_from_payload_v0(base),
    }


def test_mv2_wiring_reuses_existing_backtest_matrix_v0() -> None:
    from tests.backtest import test_mv2_research_wiring_v1 as core

    core.test_matrix_23_end_to_end_returns_signal_series()


def test_mv2_wiring_canonical_order_intent_chain_v0(tmp_path: Path) -> None:
    sizing_payload = _sizing_payload()
    sizing_path = tmp_path / "capital_risk_sizing_backtest_state.json"
    sizing_path.write_text(json.dumps(sizing_payload, indent=2), encoding="utf-8")

    intent_payload = _order_intent_payload()
    intent_path = tmp_path / "canonical_order_intent_backtest_state.json"
    intent_path.write_text(json.dumps(intent_payload, indent=2), encoding="utf-8")

    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        capital_risk_sizing_state_file_binding=CapitalRiskSizingBacktestStateFileBindingConfigV1(
            state_file_path=sizing_path,
            expected_state_file_digest_ref=str(sizing_payload["state_file_digest_ref"]),
        ),
        canonical_order_intent_state_file_binding=CanonicalOrderIntentBacktestStateFileBindingConfigV1(
            state_file_path=intent_path,
            expected_state_file_digest_ref=str(intent_payload["state_file_digest_ref"]),
        ),
    )
    assert all(
        o.capital_risk_sizing_backtest_state_file_evidence is not None for o in result.bar_outcomes
    )
    assert all(
        o.canonical_order_intent_backtest_state_file_evidence is not None
        for o in result.bar_outcomes
    )


def _safety_kernel_payload() -> dict[str, object]:
    base = {
        "schema_version": SAFETY_KERNEL_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "safety_mode": SafetyMode.NORMAL.value,
        "safety_exit_signal_triggered": False,
        "safety_exit_signal_reason_code": "",
        "reconciliation_state": ReconciliationState.RECONCILED.value,
        "position_state": PositionState.FLAT_RECONCILED.value,
        "trading_gate": TradingGate.ENTRY_ALLOWED.value,
        "killswitch_blocked": False,
        "safety_decision_allowed": True,
        "safety_kernel_owner_digest_ref": RUNTIME_ELIGIBILITY_CONTRACT_NAME,
        "killswitch_fencing_digest_ref": KILL_SWITCH_CONTRACT_DIGEST,
    }
    return {**base, "state_file_digest_ref": safety_kernel_digest(base)}


def test_mv2_wiring_safety_kernel_chain_v0(tmp_path: Path) -> None:
    payload = _safety_kernel_payload()
    state_path = tmp_path / "safety_kernel_backtest_state.json"
    state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        safety_kernel_state_file_binding=SafetyKernelBacktestStateFileBindingConfigV1(
            state_file_path=state_path,
            expected_state_file_digest_ref=str(payload["state_file_digest_ref"]),
        ),
    )
    assert all(
        o.safety_kernel_backtest_state_file_evidence is not None for o in result.bar_outcomes
    )


def _killswitch_payload() -> dict[str, object]:
    base = {
        "schema_version": KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "killswitch_boundary_mode": KillSwitchBoundaryMode.BLOCK_NEW.value,
        "fencing_digest_ref": KILL_SWITCH_CONTRACT_DIGEST,
        "prior_killswitch_active": False,
    }
    return {**base, "state_file_digest_ref": killswitch_digest(base)}


def test_mv2_wiring_killswitch_boundary_chain_v0(tmp_path: Path) -> None:
    payload = _killswitch_payload()
    state_path = tmp_path / "killswitch_backtest_state.json"
    state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        killswitch_state_file_binding=KillSwitchBacktestStateFileBindingConfigV1(
            state_file_path=state_path,
            expected_state_file_digest_ref=str(payload["state_file_digest_ref"]),
        ),
    )
    assert all(o.killswitch_backtest_state_file_evidence is not None for o in result.bar_outcomes)
    sample = result.bar_outcomes[0].killswitch_backtest_state_file_evidence
    assert sample is not None
    assert sample.killswitch_boundary_represented_in_backtest is True
    assert sample.block_new_represented_in_backtest is True


def _reconciliation_payload() -> dict[str, object]:
    base = {
        "schema_version": RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "reconciliation_state": ReconciliationState.RECONCILIATION_REQUIRED.value,
        "position_state": PositionState.FLAT_RECONCILED.value,
        "venue_flat": True,
        "existing_position_side": "none",
        "intent_snapshot_unresolved": False,
        "order_snapshot_unresolved": False,
        "fill_snapshot_unresolved": False,
        "reconciliation_owner_digest_ref": RECONCILIATION_CONTRACT_VERSION,
    }
    return {**base, "state_file_digest_ref": reconciliation_digest(base)}


def test_mv2_wiring_reconciliation_unknown_outcome_chain_v0(tmp_path: Path) -> None:
    payload = _reconciliation_payload()
    state_path = tmp_path / "reconciliation_backtest_state.json"
    state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        reconciliation_state_file_binding=ReconciliationBacktestStateFileBindingConfigV1(
            state_file_path=state_path,
            expected_state_file_digest_ref=str(payload["state_file_digest_ref"]),
        ),
    )
    assert all(
        o.reconciliation_backtest_state_file_evidence is not None for o in result.bar_outcomes
    )
    sample = result.bar_outcomes[0].reconciliation_backtest_state_file_evidence
    assert sample is not None
    assert sample.reconciliation_semantics_represented_in_backtest is True
    assert sample.reconciliation_failure_blocks_new_exposure_represented_in_backtest is True
