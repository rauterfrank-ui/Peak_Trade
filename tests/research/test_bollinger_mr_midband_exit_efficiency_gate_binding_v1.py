"""Synthetic binding contracts for midband exit-efficiency gate open_side wiring.

No panel archive, no evaluation runner, no holdout. Proves the V3
``identical_arms_no_exit_divergence`` root cause: position-feedback capture
must patch the MV2 wiring_mod from-import alias (live bar-loop call site),
not only ``feedback_mod``.
"""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from src.backtest.backtest_engine_position_feedback_adapter_v1 import (
    LegacyRealisticBarLoopStateV1,
)
from src.backtest.engine import Trade
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.exit_efficiency_gate_v1 import (
    optional_treatment_exit_efficiency_gate,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.midband_exit_mechanism_v1 import (
    short_exit_mask_from_bars,
)


def _synthetic_short_midband_cross_bars() -> pd.DataFrame:
    """Deterministic bars with at least one SHORT midband cross after warmup."""
    idx = pd.date_range("2023-05-20", periods=40, freq="h", tz="UTC")
    # Flat warmup, then rise above middle, then drop through middle (short exit).
    close = [100.0] * 20 + [105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 109.0, 100.0]
    close = close + [100.0] * (40 - len(close))
    return pd.DataFrame(
        {
            "open": close,
            "high": [c + 1.0 for c in close],
            "low": [c - 1.0 for c in close],
            "close": close,
        },
        index=idx,
    )


def _open_short_loop_state(*, entry_ts: pd.Timestamp) -> LegacyRealisticBarLoopStateV1:
    return LegacyRealisticBarLoopStateV1(
        equity=10_000.0,
        current_trade=Trade(
            entry_time=entry_ts,
            entry_price=110.0,
            size=-1.0,
            stop_price=120.0,
        ),
    )


def test_feedback_mod_only_patch_leaves_wiring_mod_capture_unbound() -> None:
    """Historical collapse boundary: from-import alias is a separate binding."""
    import src.backtest.backtest_engine_position_feedback_adapter_v1 as feedback_mod
    import src.backtest.mv2_research_wiring_v1 as wiring_mod

    orig_wiring = wiring_mod.capture_backtest_engine_position_feedback_v1
    orig_feedback = feedback_mod.capture_backtest_engine_position_feedback_v1
    assert orig_wiring is orig_feedback

    def _feedback_only_patch(**kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("feedback_only_patch_must_not_be_reached_via_wiring_mod")

    feedback_mod.capture_backtest_engine_position_feedback_v1 = _feedback_only_patch
    try:
        assert wiring_mod.capture_backtest_engine_position_feedback_v1 is orig_wiring
        assert wiring_mod.capture_backtest_engine_position_feedback_v1 is not _feedback_only_patch
    finally:
        feedback_mod.capture_backtest_engine_position_feedback_v1 = orig_feedback


def test_gate_patches_wiring_mod_and_feedback_mod_capture_aliases() -> None:
    bars = _synthetic_short_midband_cross_bars()
    import src.backtest.backtest_engine_position_feedback_adapter_v1 as feedback_mod
    import src.backtest.mv2_research_wiring_v1 as wiring_mod

    before_w = wiring_mod.capture_backtest_engine_position_feedback_v1
    before_f = feedback_mod.capture_backtest_engine_position_feedback_v1
    with optional_treatment_exit_efficiency_gate(enabled=True, bars=bars):
        assert wiring_mod.capture_backtest_engine_position_feedback_v1 is not before_w
        assert feedback_mod.capture_backtest_engine_position_feedback_v1 is not before_f
        assert (
            wiring_mod.capture_backtest_engine_position_feedback_v1
            is feedback_mod.capture_backtest_engine_position_feedback_v1
        )
    assert wiring_mod.capture_backtest_engine_position_feedback_v1 is before_w
    assert feedback_mod.capture_backtest_engine_position_feedback_v1 is before_f


def test_synthetic_short_midband_exit_diverges_when_open_side_bound_via_wiring_capture(
    monkeypatch,
) -> None:
    """Baseline map stays flat; treatment forces cover (+1) on short midband cross."""
    import src.backtest.mv2_research_wiring_v1 as wiring_mod

    bars = _synthetic_short_midband_cross_bars()
    short_mask = short_exit_mask_from_bars(bars)
    trigger_positions = [i for i, v in enumerate(short_mask.tolist()) if v]
    assert trigger_positions, "fixture_must_contain_short_midband_cross"
    trigger_i = int(trigger_positions[0])
    trigger_ts = bars.index[trigger_i]
    entry_ts = bars.index[max(0, trigger_i - 3)]

    def _fake_bind_bar(
        *, bar, instrument_id, trading_epoch, profile_binding, research_execution_cost=None
    ):
        return ("context", "l1_status", True)

    def _fake_map(_evidence) -> int:
        return 0

    monkeypatch.setattr(wiring_mod, "bind_bar_for_mv2_wiring_v1", _fake_bind_bar)
    monkeypatch.setattr(wiring_mod, "map_decision_evidence_to_position_signal_v1", _fake_map)

    loop_state = _open_short_loop_state(entry_ts=entry_ts)
    evidence = SimpleNamespace(decision_outcome="hold")

    baseline_signal = wiring_mod.map_decision_evidence_to_position_signal_v1(evidence)
    assert baseline_signal == 0

    with optional_treatment_exit_efficiency_gate(enabled=True, bars=bars) as counters:
        # Live MV2 call site: wiring_mod.capture_... (not feedback_mod alone).
        wiring_mod.capture_backtest_engine_position_feedback_v1(
            state=loop_state,
            feedback_source_bar_epoch=trigger_i - 1,
        )
        wiring_mod.bind_bar_for_mv2_wiring_v1(
            bar=bars.iloc[trigger_i],
            instrument_id="x",
            trading_epoch=trigger_i,
            profile_binding=None,
        )
        treatment_signal = wiring_mod.map_decision_evidence_to_position_signal_v1(evidence)

    assert treatment_signal == 1
    assert treatment_signal != baseline_signal
    assert counters["exit_bars_observed"] >= 1
    assert counters["exits_forced_by_gate"] >= 1
    assert trigger_ts is not None
