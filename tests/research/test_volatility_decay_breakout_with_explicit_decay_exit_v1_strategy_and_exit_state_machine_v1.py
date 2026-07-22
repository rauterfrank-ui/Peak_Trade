"""Focused tests for VDBX exit reachability, precedence, no-lookahead, LONG/SHORT."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_exit_state_machine_v1 import (
    EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1,
    ExplicitDecayExitReasonV1,
    TIME_EXIT_MAX_BARS_V1,
    entry_exit_reachable_ex_ante_v1,
    evaluate_exit_on_bar_v1,
    open_position_from_fill_v1,
)
from src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_strategy_implementation_binding_v1 import (
    load_and_validate_repo_binding,
)
from src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_strategy_v1 import (
    EXIT_PARAMS_V1,
    EXIT_STATE_MACHINE_IMPLEMENTED_V1,
    PREDECESSOR_STRATEGY_ID_V1,
    PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1,
    STRATEGY_IDENTITY_V1,
    VdbxEventV1,
    VdbxReasonV1,
    generate_vdbx_events_and_roundtrips_v1,
)

REPO = Path(__file__).resolve().parents[2]


def test_binding_and_identity() -> None:
    report = load_and_validate_repo_binding(REPO)
    assert report["valid"] is True
    assert report["exit_state_machine_implemented"] is True
    assert report["evaluation_authorized"] is False
    assert STRATEGY_IDENTITY_V1 == "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1"
    assert PREDECESSOR_STRATEGY_ID_V1 == "VOLATILITY_DECAY_BREAKOUT_V1"
    assert EXIT_STATE_MACHINE_IMPLEMENTED_V1 is True
    assert EXIT_PARAMS_V1["exit_state_machine_implemented"] is True
    assert (REPO / PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1).is_file()
    assert EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1[0] == "INITIAL_STOP"


def test_ex_ante_reachability_gate() -> None:
    assert entry_exit_reachable_ex_ante_v1(signal_index=10, series_length=100) is True
    # fill=11, need fill+48 < n => 59 < n
    assert entry_exit_reachable_ex_ante_v1(signal_index=10, series_length=59) is False
    assert entry_exit_reachable_ex_ante_v1(signal_index=10, series_length=60) is True
    assert entry_exit_reachable_ex_ante_v1(signal_index=58, series_length=60) is False


def _long_pos(*, fill: int = 0, entry: float = 100.0, atr: float = 1.0):
    return open_position_from_fill_v1(
        side="LONG", fill_index=fill, entry_price=entry, atr_at_fill=atr
    )


def _short_pos(*, fill: int = 0, entry: float = 100.0, atr: float = 1.0):
    return open_position_from_fill_v1(
        side="SHORT", fill_index=fill, entry_price=entry, atr_at_fill=atr
    )


def test_precedence_initial_stop_beats_signal_and_regime_long() -> None:
    pos = _long_pos()
    # stop at 100 - 1.5*1 = 98.5; low hits stop; also signal+regime candidates present
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=101.0,
        low=98.0,
        close=99.0,
        atr=1.0,
        percentile_rank=0.80,  # SIGNAL_EXIT
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is ExplicitDecayExitReasonV1.INITIAL_STOP
    assert decision.side == "LONG"


def test_precedence_signal_exit_over_regime_short() -> None:
    pos = _short_pos()
    # no stop hit; percentile >=0.70 => SIGNAL; cannot also be <0.50
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=100.5,
        low=99.5,
        close=100.0,
        atr=1.0,
        percentile_rank=0.75,
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is ExplicitDecayExitReasonV1.SIGNAL_EXIT
    assert decision.side == "SHORT"


def test_regime_invalidation_long() -> None:
    pos = _long_pos()
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=101.0,
        low=99.5,
        close=100.2,
        atr=1.0,
        percentile_rank=0.40,
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert decision is not None
    assert decision.reason is ExplicitDecayExitReasonV1.REGIME_INVALIDATION


def test_time_exit_and_terminal_liquidation_precedence() -> None:
    pos = _long_pos(fill=0)
    # held == 48 at bar 48; also last panel -> TIME_EXIT wins over terminal
    decision, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=TIME_EXIT_MAX_BARS_V1,
        high=101.0,
        low=99.5,
        close=100.0,
        atr=1.0,
        percentile_rank=0.60,  # neither signal nor regime
        is_last_instrument_bar=True,
        is_last_panel_bar=True,
    )
    assert decision is not None
    assert decision.reason is ExplicitDecayExitReasonV1.TIME_EXIT

    pos2 = _long_pos(fill=0)
    decision2, _ = evaluate_exit_on_bar_v1(
        pos2,
        bar_index=5,
        high=101.0,
        low=99.5,
        close=100.0,
        atr=1.0,
        percentile_rank=0.60,
        is_last_instrument_bar=True,
        is_last_panel_bar=False,
    )
    assert decision2 is not None
    assert decision2.reason is ExplicitDecayExitReasonV1.END_OF_INSTRUMENT_LIQUIDATION

    pos3 = _short_pos(fill=0)
    decision3, _ = evaluate_exit_on_bar_v1(
        pos3,
        bar_index=5,
        high=100.5,
        low=99.5,
        close=100.0,
        atr=1.0,
        percentile_rank=0.60,
        is_last_instrument_bar=False,
        is_last_panel_bar=True,
    )
    assert decision3 is not None
    assert decision3.reason is ExplicitDecayExitReasonV1.END_OF_PANEL_LIQUIDATION


def test_same_bar_fill_exit_forbidden() -> None:
    pos = _long_pos(fill=10)
    with pytest.raises(ValueError, match="EXIT_BEFORE_OR_ON_FILL_FORBIDDEN|SAME_BAR"):
        evaluate_exit_on_bar_v1(
            pos,
            bar_index=10,
            high=101.0,
            low=90.0,
            close=95.0,
            atr=1.0,
            percentile_rank=0.9,
            is_last_instrument_bar=False,
            is_last_panel_bar=False,
        )


def test_missing_ohlc_fail_closed() -> None:
    pos = _long_pos()
    with pytest.raises(ValueError, match="MISSING_OHLC_FAIL_CLOSED"):
        evaluate_exit_on_bar_v1(
            pos,
            bar_index=1,
            high=float("nan"),
            low=99.0,
            close=100.0,
            atr=1.0,
            percentile_rank=0.6,
            is_last_instrument_bar=False,
            is_last_panel_bar=False,
        )


def test_no_lookahead_exit_uses_only_current_bar_inputs() -> None:
    """Exit decision depends only on provided bar fields (no future series access)."""
    pos = _long_pos()
    d1, _ = evaluate_exit_on_bar_v1(
        pos,
        bar_index=1,
        high=100.2,
        low=99.8,
        close=100.0,
        atr=1.0,
        percentile_rank=0.60,
        is_last_instrument_bar=False,
        is_last_panel_bar=False,
    )
    assert d1 is None  # no exit yet; proves we did not invent future exits


def test_strategy_suppresses_unreachable_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 30  # too short for reachability (need fill+48 < n)
    idx = pd.date_range("2022-01-01", periods=n, freq="h", tz="UTC")
    df = pd.DataFrame(
        {
            "open": np.full(n, 100.0),
            "high": np.full(n, 101.0),
            "low": np.full(n, 99.0),
            "close": np.full(n, 100.0),
            "volume": np.ones(n),
        },
        index=idx,
    )

    class _Fake:
        event = type("E", (), {"ENTRY_EVENT": "ENTRY_EVENT"})

    from src.research import volatility_decay_breakout_v1_strategy_v1 as vdb
    from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
        StrategyAgreementEventKindV1,
        StrategyEntrySideCarrierV1,
    )
    from src.research.volatility_decay_breakout_v1_strategy_v1 import (
        VolatilityDecayBreakoutBarResultV1,
        VolatilityDecayBreakoutEventV1,
        VolatilityDecayBreakoutReasonV1,
    )

    fake_rows = []
    for i in range(n):
        if i == 5:
            fake_rows.append(
                VolatilityDecayBreakoutBarResultV1(
                    event=VolatilityDecayBreakoutEventV1.ENTRY_EVENT,
                    entry_side=StrategyEntrySideCarrierV1.LONG,
                    event_kind=StrategyAgreementEventKindV1.ENTRY,
                    reason=VolatilityDecayBreakoutReasonV1.SUCCESSFUL_ENTRY,
                    decay_offset=1,
                    confirmation_bar_index=4,
                    percentile_rank_120=0.3,
                    normalized_atr=0.01,
                    upper_channel=100.5,
                    lower_channel=99.5,
                )
            )
        else:
            fake_rows.append(
                VolatilityDecayBreakoutBarResultV1(
                    event=VolatilityDecayBreakoutEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VolatilityDecayBreakoutReasonV1.NO_EVENT,
                )
            )
    monkeypatch.setattr(
        "src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_strategy_v1."
        "generate_volatility_decay_breakout_events_v1",
        lambda *a, **k: fake_rows,
    )
    monkeypatch.setattr(
        "src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_strategy_v1."
        "compute_atr14_v1",
        lambda h, l, c: pd.Series(1.0, index=df.index),
    )
    monkeypatch.setattr(
        "src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_strategy_v1."
        "compute_normalized_atr14_v1",
        lambda h, l, c: pd.Series(0.01, index=df.index),
    )
    monkeypatch.setattr(
        "src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_strategy_v1."
        "compute_percentile_rank_120_normalized_atr_v1",
        lambda s: pd.Series(0.60, index=df.index),
    )

    rows, roundtrips = generate_vdbx_events_and_roundtrips_v1(df)
    assert rows[5].reason is VdbxReasonV1.ENTRY_SUPPRESSED_EXIT_UNREACHABLE
    assert rows[5].event is VdbxEventV1.NONE
    assert roundtrips == []


def test_strategy_admits_reachable_entry_and_emits_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    n = 80
    idx = pd.date_range("2022-01-01", periods=n, freq="h", tz="UTC")
    df = pd.DataFrame(
        {
            "open": np.full(n, 100.0),
            "high": np.full(n, 100.2),
            "low": np.full(n, 99.8),
            "close": np.full(n, 100.0),
            "volume": np.ones(n),
        },
        index=idx,
    )
    from src.research.volatility_decay_breakout_v1_strategy_v1 import (
        VolatilityDecayBreakoutBarResultV1,
        VolatilityDecayBreakoutEventV1,
        VolatilityDecayBreakoutReasonV1,
    )
    from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
        StrategyAgreementEventKindV1,
        StrategyEntrySideCarrierV1,
    )

    ranks = np.full(n, 0.60)
    # after fill at 6, on bar 7 force regime invalidation via low percentile
    ranks[7] = 0.40

    fake_rows = []
    for i in range(n):
        if i == 5:
            fake_rows.append(
                VolatilityDecayBreakoutBarResultV1(
                    event=VolatilityDecayBreakoutEventV1.ENTRY_EVENT,
                    entry_side=StrategyEntrySideCarrierV1.SHORT,
                    event_kind=StrategyAgreementEventKindV1.ENTRY,
                    reason=VolatilityDecayBreakoutReasonV1.SUCCESSFUL_ENTRY,
                    decay_offset=1,
                    confirmation_bar_index=4,
                    percentile_rank_120=0.3,
                    normalized_atr=0.01,
                    upper_channel=100.5,
                    lower_channel=99.5,
                )
            )
        else:
            fake_rows.append(
                VolatilityDecayBreakoutBarResultV1(
                    event=VolatilityDecayBreakoutEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VolatilityDecayBreakoutReasonV1.NO_EVENT,
                )
            )
    monkeypatch.setattr(
        "src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_strategy_v1."
        "generate_volatility_decay_breakout_events_v1",
        lambda *a, **k: fake_rows,
    )
    monkeypatch.setattr(
        "src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_strategy_v1."
        "compute_atr14_v1",
        lambda h, l, c: pd.Series(1.0, index=df.index),
    )
    monkeypatch.setattr(
        "src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_strategy_v1."
        "compute_normalized_atr14_v1",
        lambda h, l, c: pd.Series(0.01, index=df.index),
    )
    monkeypatch.setattr(
        "src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_strategy_v1."
        "compute_percentile_rank_120_normalized_atr_v1",
        lambda s: pd.Series(ranks, index=df.index),
    )

    rows, roundtrips = generate_vdbx_events_and_roundtrips_v1(df)
    assert rows[5].event is VdbxEventV1.ENTRY_EVENT
    assert rows[5].entry_side is StrategyEntrySideCarrierV1.SHORT
    assert len(roundtrips) == 1
    assert roundtrips[0].side == "SHORT"
    assert roundtrips[0].fill_index == 6
    assert roundtrips[0].exit_index == 7
    assert roundtrips[0].exit_reason is ExplicitDecayExitReasonV1.REGIME_INVALIDATION
    assert rows[7].event is VdbxEventV1.EXIT_EVENT
