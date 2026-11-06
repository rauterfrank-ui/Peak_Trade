"""Focused regression tests for canonical SHORT binding miswiring repair v1.

Productive repair at FIRST_TRUE_MISWIRING_BOUNDARY:
  run_mv2_research_backtest_wiring_v1::BacktestEngine(use_execution_pipeline=True)
  + step_legacy_realistic_bar_v1(honor_mapped_short_entry=True)

No new direction authority. Master V2 / Double Play remain sole owners.
LIVE_AUTHORIZED=false; ORDERS=false.
"""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
import pytest

from src.backtest import mv2_research_wiring_v1 as wiring
from src.backtest.backtest_engine_position_feedback_adapter_v1 import (
    capture_backtest_engine_position_feedback_v1,
    finalize_legacy_realistic_bar_loop_v1,
    init_legacy_realistic_bar_loop_state_v1,
    step_legacy_realistic_bar_v1,
)
from src.backtest.cost_config_v0 import resolve_effective_backtest_cost_config
from src.backtest.engine import BacktestEngine
from src.backtest.strategy_signal_binding_v1 import ENGINE_SIGNAL_SOURCE_MV2_REPLAY
from src.trading.master_v2.double_play_composition_matrix_v1 import PositionManagementContext
from src.trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
    StrategySideAgreementV1,
    StrategySignalEncodingClassV1,
    StrategySuitabilityAgreementMaterialV1,
    compute_strategy_suitability_agreement_material_digest_v1,
)


def _cfg() -> Mapping[str, Any]:
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
        },
        "risk": {
            "risk_per_trade": 0.004,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
        "economic_evaluation_v1": {
            "strategy_params": {
                "fast_window": 2,
                "slow_window": 3,
            },
        },
    }


def _bars(n: int = 6, *, closes: list[float] | None = None) -> pd.DataFrame:
    idx = pd.date_range("2026-07-01", periods=n, freq="1h", tz="UTC")
    close = closes if closes is not None else [100.0 - float(i) for i in range(n)]
    assert len(close) == n
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": [v - 0.5 for v in close],
            "close": close,
            "mark_price": close,
            "index_price": [v - 0.1 for v in close],
            "best_bid": [v - 0.05 for v in close],
            "best_ask": [v + 0.05 for v in close],
            "spread": [0.1 for _ in close],
            "volume": [1000.0 for _ in close],
            "open_interest": [10000.0 for _ in close],
            "funding_rate": [0.0001 for _ in close],
            "volatility_estimate": [0.2 for _ in close],
            "is_final": [True for _ in close],
            "bar_interval": ["1m" for _ in close],
        },
        index=idx,
    )


def test_wiring_binds_short_capable_pipeline_consumer() -> None:
    from pathlib import Path

    text = Path(wiring.__file__).read_text(encoding="utf-8")
    assert text.count("use_execution_pipeline=True") >= 2
    assert "use_execution_pipeline=False" not in text
    assert text.count("honor_mapped_short_entry=True") >= 2


def test_honor_mapped_short_entry_opens_short_when_flat() -> None:
    cfg = _cfg()
    engine = BacktestEngine(
        use_execution_pipeline=True,
        risk_limits=wiring.build_mv2_research_risk_limits_v1(cfg),
    )
    engine.config = cfg
    cost = resolve_effective_backtest_cost_config(cfg)
    state = init_legacy_realistic_bar_loop_state_v1(engine, strategy_params={"stop_pct": 0.02})
    bars = _bars(3, closes=[100.0, 99.0, 98.0])
    state = step_legacy_realistic_bar_v1(
        engine,
        state,
        bar=bars.iloc[0],
        signal=0,
        symbol="inst-eth-usdt-perp",
        effective_cost=cost,
        honor_mapped_short_entry=True,
    )
    state = step_legacy_realistic_bar_v1(
        engine,
        state,
        bar=bars.iloc[1],
        signal=-1,
        symbol="inst-eth-usdt-perp",
        effective_cost=cost,
        honor_mapped_short_entry=True,
    )
    assert state.current_trade is not None, f"blocked={state.blocked_trades}"
    assert state.current_trade.size < 0.0
    feedback = capture_backtest_engine_position_feedback_v1(
        state=state,
        feedback_source_bar_epoch=1,
    )
    assert feedback.existing_position_side is ExistingPositionSide.SHORT
    assert feedback.position_management_context is PositionManagementContext.SHORT_POSITION
    assert feedback.side_state.name == "NEUTRAL_OBSERVE"


def test_default_stepper_still_noops_flat_minus_one() -> None:
    cfg = _cfg()
    engine = BacktestEngine(use_execution_pipeline=False)
    engine.config = cfg
    cost = resolve_effective_backtest_cost_config(cfg)
    state = init_legacy_realistic_bar_loop_state_v1(engine, strategy_params={"stop_pct": 0.02})
    bar = _bars(1).iloc[0]
    state = step_legacy_realistic_bar_v1(
        engine,
        state,
        bar=bar,
        signal=-1,
        symbol="inst-eth-usdt-perp",
        effective_cost=cost,
    )
    assert state.current_trade is None
    assert state.trades == []


def test_long_regression_still_opens_on_plus_one() -> None:
    cfg = _cfg()
    engine = BacktestEngine(
        use_execution_pipeline=True,
        risk_limits=wiring.build_mv2_research_risk_limits_v1(cfg),
    )
    engine.config = cfg
    cost = resolve_effective_backtest_cost_config(cfg)
    state = init_legacy_realistic_bar_loop_state_v1(engine, strategy_params={"stop_pct": 0.02})
    bars = _bars(3, closes=[100.0, 101.0, 102.0])
    state = step_legacy_realistic_bar_v1(
        engine,
        state,
        bar=bars.iloc[1],
        signal=1,
        symbol="inst-eth-usdt-perp",
        effective_cost=cost,
        honor_mapped_short_entry=True,
    )
    assert state.current_trade is not None
    assert state.current_trade.size > 0.0
    feedback = capture_backtest_engine_position_feedback_v1(
        state=state,
        feedback_source_bar_epoch=1,
    )
    assert feedback.existing_position_side is ExistingPositionSide.LONG


def test_short_roundtrip_finalize_preserves_short_accounting() -> None:
    cfg = _cfg()
    engine = BacktestEngine(
        use_execution_pipeline=True,
        risk_limits=wiring.build_mv2_research_risk_limits_v1(cfg),
    )
    engine.config = cfg
    cost = resolve_effective_backtest_cost_config(cfg)
    state = init_legacy_realistic_bar_loop_state_v1(engine, strategy_params={"stop_pct": 0.02})
    bars = _bars(4, closes=[100.0, 99.0, 98.0, 97.0])
    for i, signal in enumerate([0, -1, 0, 0]):
        state = step_legacy_realistic_bar_v1(
            engine,
            state,
            bar=bars.iloc[i],
            signal=signal,
            symbol="inst-eth-usdt-perp",
            effective_cost=cost,
            honor_mapped_short_entry=True,
        )
    assert state.current_trade is not None
    assert state.current_trade.size < 0.0
    result = finalize_legacy_realistic_bar_loop_v1(
        engine,
        state,
        df=bars,
        effective_cost=cost,
        symbol="inst-eth-usdt-perp",
    )
    assert result.stats["total_trades"] >= 1
    assert result.trades is not None
    assert float(result.trades.iloc[0]["size"]) < 0.0


def test_mv2_wiring_preserves_mapped_short_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    signals = [0, -1, -1, 0]
    call_idx = {"i": 0}

    def _forced_signal(_evidence: object) -> int:
        idx = call_idx["i"]
        call_idx["i"] += 1
        return signals[min(idx, len(signals) - 1)]

    monkeypatch.setattr(
        wiring,
        "map_decision_evidence_to_position_signal_v1",
        _forced_signal,
    )
    result = wiring.run_mv2_research_backtest_wiring_v1(
        bars=_bars(4, closes=[100.0, 99.0, 98.0, 97.0]),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        backtest_engine_signal_source=ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
    )
    assert list(result.signals.astype(int)) == signals
    assert result.backtest_result is not None
    assert int(result.backtest_result.stats["total_trades"]) >= 1
    trades = result.backtest_result.trades
    assert trades is not None and not trades.empty
    assert float(trades.iloc[0]["size"]) < 0.0


def test_mv2_wiring_long_regression(monkeypatch: pytest.MonkeyPatch) -> None:
    signals = [0, 1, 0, -1]
    call_idx = {"i": 0}

    def _forced_signal(_evidence: object) -> int:
        idx = call_idx["i"]
        call_idx["i"] += 1
        return signals[min(idx, len(signals) - 1)]

    monkeypatch.setattr(
        wiring,
        "map_decision_evidence_to_position_signal_v1",
        _forced_signal,
    )
    result = wiring.run_mv2_research_backtest_wiring_v1(
        bars=_bars(4, closes=[100.0, 101.0, 102.0, 103.0]),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        backtest_engine_signal_source=ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
    )
    assert list(result.signals.astype(int)) == signals
    assert result.backtest_result is not None
    assert int(result.backtest_result.stats["total_trades"]) >= 1
    trades = result.backtest_result.trades
    assert trades is not None and not trades.empty
    assert float(trades.iloc[0]["size"]) > 0.0


def test_entry_side_none_fail_closed() -> None:
    import hashlib

    def _digest(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    encoding = StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1
    entry_side = StrategyEntrySideCarrierV1.NONE
    params_digest = _digest("params")
    signal_digest = _digest("signal")
    digest = compute_strategy_suitability_agreement_material_digest_v1(
        encoding_class=encoding,
        configured_strategy_id="ma_crossover",
        executed_strategy_id="ma_crossover",
        strategy_version="v1",
        strategy_params_digest=params_digest,
        strategy_signal_digest=signal_digest,
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=0,
        cycle_signal_value=1,
        side_agreement=StrategySideAgreementV1.NEUTRAL,
        filter_pass=None,
        event_kind=StrategyAgreementEventKindV1.ENTRY,
        entry_side=entry_side,
    )
    material = StrategySuitabilityAgreementMaterialV1(
        encoding_class=encoding,
        configured_strategy_id="ma_crossover",
        executed_strategy_id="ma_crossover",
        strategy_version="v1",
        strategy_params_digest=params_digest,
        strategy_signal_digest=signal_digest,
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=0,
        cycle_signal_value=1,  # type: ignore[arg-type]
        side_agreement=StrategySideAgreementV1.NEUTRAL,
        filter_pass=None,
        event_kind=StrategyAgreementEventKindV1.ENTRY,
        material_digest=digest,
        entry_side=entry_side,
    )
    direction = wiring.resolve_agreement_bound_directional_cycle_v1(material)
    assert material.entry_side is StrategyEntrySideCarrierV1.NONE
    assert direction is None
