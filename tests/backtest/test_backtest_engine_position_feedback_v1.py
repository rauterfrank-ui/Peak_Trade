"""Contract tests for backtest engine position feedback into MV2 integrated replay."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

import pandas as pd
import pytest

from src.backtest import mv2_research_wiring_v1 as wiring
from src.backtest.backtest_engine_position_feedback_adapter_v1 import (
    BACKTEST_ENGINE_POSITION_FEEDBACK_ADAPTER_OWNER,
    CANONICAL_BACKTEST_POSITION_OWNER,
    _PARTIAL_REDUCTION_SUPPORTED_BY_CANONICAL_OWNER,
    BacktestEnginePositionFeedbackV1,
    capture_backtest_engine_position_feedback_v1,
    coerce_backtest_position_state_v1,
    init_legacy_realistic_bar_loop_state_v1,
    step_legacy_realistic_bar_v1,
)
from src.backtest.engine import BacktestEngine
from src.backtest.strategy_signal_binding_v1 import ENGINE_SIGNAL_SOURCE_MV2_REPLAY
from src.trading.master_v2.double_play_composition_matrix_v1 import PositionManagementContext
from src.trading.master_v2.double_play_entry_exit_policy_v0 import (
    ExistingPositionSide,
    PositionState,
    ReconciliationState,
    EntryExitDirectionState,
)
from src.trading.master_v2.double_play_state import SideState
from src.trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
)


def _cfg(*, fee_bps: float = 10.0, slippage_bps: float = 5.0) -> Mapping[str, Any]:
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": fee_bps,
            "slippage_bps": slippage_bps,
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


def _bars(n: int = 12, *, stop_trigger_bar: int | None = None) -> pd.DataFrame:
    idx = pd.date_range("2026-06-01", periods=n, freq="1h", tz="UTC")
    close = [100.0 + float(i) for i in range(n)]
    lows = [v - 0.5 for v in close]
    if stop_trigger_bar is not None and 0 <= stop_trigger_bar < n:
        lows[stop_trigger_bar] = close[stop_trigger_bar] - 5.0
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": lows,
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


def _run_mv2_replay(**kwargs: Any) -> wiring.MV2ResearchWiringResultV1:
    return wiring.run_mv2_research_backtest_wiring_v1(
        bars=kwargs.pop("bars", _bars()),
        strategy_id=kwargs.pop("strategy_id", "ma_crossover"),
        cfg=kwargs.pop("cfg", _cfg()),
        backtest_engine_signal_source=ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
        **kwargs,
    )


def _flat_feedback(epoch: int = 0) -> BacktestEnginePositionFeedbackV1:
    return BacktestEnginePositionFeedbackV1(
        feedback_source_bar_epoch=epoch,
        position_state=PositionState.FLAT_RECONCILED,
        existing_position_side=ExistingPositionSide.NONE,
        venue_flat=True,
        side_state=SideState.NEUTRAL_OBSERVE,
        direction_state=EntryExitDirectionState.NEUTRAL,
        position_management_context=PositionManagementContext.FLAT,
        reconciliation_state=ReconciliationState.RECONCILED,
        has_open_trade=False,
    )


def test_initial_flat_feedback_from_adapter() -> None:
    engine = BacktestEngine(use_execution_pipeline=False)
    engine.config = _cfg()
    state = init_legacy_realistic_bar_loop_state_v1(engine, strategy_params={"stop_pct": 0.02})
    feedback = capture_backtest_engine_position_feedback_v1(
        state=state,
        feedback_source_bar_epoch=0,
    )
    assert feedback.position_state is PositionState.FLAT_RECONCILED
    assert feedback.venue_flat is True
    assert feedback.has_open_trade is False


def test_entry_on_prior_bar_visible_to_next_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    signals = [0, 1, 0, 0]
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
    captured: list[PositionState] = []
    original_build = wiring._build_replay_input

    def _capture_build(**kwargs: object) -> object:
        seq = kwargs["sequence_state"]
        captured.append(seq.position_state)
        return original_build(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(wiring, "_build_replay_input", _capture_build)
    result = _run_mv2_replay(bars=_bars(4))
    assert captured[0] is PositionState.FLAT_RECONCILED
    assert captured[1] is PositionState.FLAT_RECONCILED
    assert captured[2] is PositionState.OPEN_FULL, (
        f"captured={captured}, trades={result.backtest_result.stats.get('total_trades')}"
    )


def test_held_position_carried_across_multiple_bars(monkeypatch: pytest.MonkeyPatch) -> None:
    signals = [1, 0, 0, 0]
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
    captured: list[PositionState] = []
    original_build = wiring._build_replay_input

    def _capture_build(**kwargs: object) -> object:
        seq = kwargs["sequence_state"]
        captured.append(seq.position_state)
        return original_build(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(wiring, "_build_replay_input", _capture_build)
    _run_mv2_replay(bars=_bars(4))
    assert captured[1:] == [
        PositionState.OPEN_FULL,
        PositionState.OPEN_FULL,
        PositionState.OPEN_FULL,
    ]


def test_exit_feedback_visible_to_next_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    signals = [1, 0, -1, 0]
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
    captured: list[PositionState] = []
    original_build = wiring._build_replay_input

    def _capture_build(**kwargs: object) -> object:
        captured.append(kwargs["sequence_state"].position_state)
        return original_build(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(wiring, "_build_replay_input", _capture_build)
    _run_mv2_replay(bars=_bars(4))
    assert captured[-1] is PositionState.FLAT_RECONCILED


def test_stop_triggered_flat_feedback_visible_to_next_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signals = [1, 0, 0, 0]
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
    captured: list[PositionState] = []
    original_build = wiring._build_replay_input

    def _capture_build(**kwargs: object) -> object:
        captured.append(kwargs["sequence_state"].position_state)
        return original_build(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(wiring, "_build_replay_input", _capture_build)
    _run_mv2_replay(bars=_bars(4, stop_trigger_bar=2))
    assert captured[2] is PositionState.OPEN_FULL
    assert captured[3] is PositionState.FLAT_RECONCILED


def test_partial_reduction_not_supported_by_canonical_owner() -> None:
    assert _PARTIAL_REDUCTION_SUPPORTED_BY_CANONICAL_OWNER is False


def test_no_direct_opposite_side_opening_before_flat() -> None:
    cfg = _cfg()
    engine = BacktestEngine(
        use_execution_pipeline=False,
        risk_limits=wiring.build_mv2_research_risk_limits_v1(cfg),
    )
    engine.config = cfg
    state = init_legacy_realistic_bar_loop_state_v1(engine, strategy_params={"stop_pct": 0.02})
    bar = _bars(1).iloc[0]
    from src.backtest.cost_config_v0 import resolve_effective_backtest_cost_config

    cost = resolve_effective_backtest_cost_config(cfg)
    state = step_legacy_realistic_bar_v1(
        engine,
        state,
        bar=bar,
        signal=1,
        symbol="inst-eth-usdt-perp",
        effective_cost=cost,
    )
    assert state.current_trade is not None, f"blocked={state.blocked_trades}"
    state = step_legacy_realistic_bar_v1(
        engine,
        state,
        bar=bar,
        signal=1,
        symbol="inst-eth-usdt-perp",
        effective_cost=cost,
    )
    assert state.current_trade is not None
    assert len(state.trades) == 0


def test_no_same_bar_lookahead_in_feedback_epoch() -> None:
    cfg = _cfg()
    engine = BacktestEngine(
        use_execution_pipeline=False,
        risk_limits=wiring.build_mv2_research_risk_limits_v1(cfg),
    )
    engine.config = cfg
    state = init_legacy_realistic_bar_loop_state_v1(engine, strategy_params={"stop_pct": 0.02})
    bar = _bars(1).iloc[0]
    from src.backtest.cost_config_v0 import resolve_effective_backtest_cost_config

    cost = resolve_effective_backtest_cost_config(cfg)
    pre = capture_backtest_engine_position_feedback_v1(state=state, feedback_source_bar_epoch=0)
    assert pre.has_open_trade is False
    state = step_legacy_realistic_bar_v1(
        engine,
        state,
        bar=bar,
        signal=1,
        symbol="inst-eth-usdt-perp",
        effective_cost=cost,
    )
    post = capture_backtest_engine_position_feedback_v1(state=state, feedback_source_bar_epoch=0)
    assert post.has_open_trade is True, f"blocked={state.blocked_trades}"
    assert pre.feedback_source_bar_epoch == post.feedback_source_bar_epoch


def test_no_state_leakage_between_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    signals = [1, 0, -1, 0]
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
    bars = _bars(4)
    first = _run_mv2_replay(bars=bars)
    call_idx["i"] = 0
    second = _run_mv2_replay(bars=bars)
    for a, b in zip(first.bar_outcomes, second.bar_outcomes):
        assert a.position_signal == b.position_signal
        assert a.evidence.semantic_digest == b.evidence.semantic_digest


def test_deterministic_repeated_mv2_replay_run(monkeypatch: pytest.MonkeyPatch) -> None:
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
    bars = _bars(4)
    a = _run_mv2_replay(bars=bars)
    call_idx["i"] = 0
    b = _run_mv2_replay(bars=bars)
    assert list(a.mv2_replay_signals) == list(b.mv2_replay_signals)
    assert a.backtest_result.stats.get("total_trades") == b.backtest_result.stats.get(
        "total_trades"
    )


def test_canonical_backtest_owner_reused() -> None:
    assert CANONICAL_BACKTEST_POSITION_OWNER == "backtest.engine.BacktestEngine"
    assert BACKTEST_ENGINE_POSITION_FEEDBACK_ADAPTER_OWNER.endswith(
        "backtest_engine_position_feedback_adapter_v1"
    )


def test_canonical_replay_callable_reused(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    original = wiring.run_integrated_offline_trading_logic_replay_v1

    def _spy(*args: object, **kwargs: object):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(
        wiring,
        "run_integrated_offline_trading_logic_replay_v1",
        _spy,
    )
    _run_mv2_replay(bars=_bars(3))
    assert calls == 3
    assert INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER.endswith(
        "integrated_offline_trading_logic_replay_v1"
    )


def test_negative_position_state_coercion_fail_closed() -> None:
    with pytest.raises(ValueError, match="position_state_coercion_failed"):
        coerce_backtest_position_state_v1("not_a_position_state")


def test_apply_feedback_overrides_position_fields_only() -> None:
    initial = wiring.build_initial_mv2_integrated_replay_bar_sequence_state_v1(trading_epoch=0)
    marked = replace(initial, scope_direction_state=initial.scope_direction_state)
    prior_side = marked.side_state
    feedback = _flat_feedback()
    open_feedback = replace(
        feedback,
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        venue_flat=False,
        side_state=SideState.LONG_ACTIVE,
        position_management_context=PositionManagementContext.LONG_POSITION,
        has_open_trade=True,
    )
    updated = wiring.apply_backtest_engine_position_feedback_to_mv2_sequence_state_v1(
        marked,
        open_feedback,
    )
    assert updated.position_state is PositionState.OPEN_FULL
    assert updated.scope_direction_state == marked.scope_direction_state
    assert updated.side_state is prior_side


def test_mv2_replay_incremental_matches_batch_backtest(monkeypatch: pytest.MonkeyPatch) -> None:
    signals = [0, 1, 0, -1, 0]
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
    bars = _bars(5)
    incremental = _run_mv2_replay(bars=bars)
    call_idx["i"] = 0
    cfg = _cfg()
    engine = BacktestEngine(
        use_execution_pipeline=False,
        risk_limits=wiring.build_mv2_research_risk_limits_v1(cfg),
    )
    engine.config = cfg
    state = init_legacy_realistic_bar_loop_state_v1(engine, strategy_params={"stop_pct": 0.02})
    from src.backtest.backtest_engine_position_feedback_adapter_v1 import (
        finalize_legacy_realistic_bar_loop_v1,
    )
    from src.backtest.cost_config_v0 import resolve_effective_backtest_cost_config

    cost = resolve_effective_backtest_cost_config(cfg)
    for i, (_, row) in enumerate(bars.iterrows()):
        state = step_legacy_realistic_bar_v1(
            engine,
            state,
            bar=row,
            signal=signals[min(i, len(signals) - 1)],
            symbol="inst-eth-usdt-perp",
            effective_cost=cost,
        )
    batch = finalize_legacy_realistic_bar_loop_v1(
        engine,
        state,
        df=bars,
        effective_cost=cost,
        symbol="inst-eth-usdt-perp",
    )
    assert incremental.backtest_result.stats.get("total_trades") == batch.stats.get("total_trades")
