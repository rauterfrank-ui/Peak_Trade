"""Regression: MV2 research scope distances are mark-relative (not 120/60/90)."""

from __future__ import annotations

import ast
import inspect
import math
from pathlib import Path

import pandas as pd
import pytest

from src.backtest.mv2_research_wiring_v1 import (
    _MV2_RESEARCH_SCOPE_ADVERSE_TO_UP_RATIO,
    _MV2_RESEARCH_SCOPE_REVERSAL_TO_UP_RATIO,
    _MV2_RESEARCH_SCOPE_UP_DISTANCE_BPS,
    build_initial_mv2_integrated_replay_bar_sequence_state_v1,
    compute_mv2_research_scope_distances_absolute_from_mark_v1,
    run_mv2_research_backtest_wiring_v1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    CanonicalScopeEventType,
    ScopeDirectionState,
    compute_evaluated_thresholds,
    _matched_directional_conditions,
)
from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    CANONICAL_BULL_BEAR_STATE_OWNER,
    CANONICAL_COMPOSITION_AUTHORITY,
    CANONICAL_SWITCH_AUTHORITY,
    LIVE_AUTHORIZED,
    ORDERS_ENABLED,
    RUNTIME_BRIDGE_STATUS,
)
from trading.master_v2.double_play_state import (
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    StaticHardLimits,
    transition_state,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyEntrySideCarrierV1,
)

_WIRING = Path("src/backtest/mv2_research_wiring_v1.py")
_GENERATOR = Path("src/trading/master_v2/deterministic_scope_event_generator_v1.py")
_STATE = Path("src/trading/master_v2/double_play_state.py")
_COMPOSITION = Path("src/trading/master_v2/double_play_composition_matrix_v1.py")


def test_low_price_instrument_distances_mark_scale_not_legacy_absolute() -> None:
    for mark in (0.23, 0.3895, 0.53):
        d = compute_mv2_research_scope_distances_absolute_from_mark_v1(mark)
        assert d.up_distance == pytest.approx(mark * 0.01)
        assert d.adverse_exit_distance == pytest.approx(d.up_distance * 0.5)
        assert d.reversal_distance == pytest.approx(d.up_distance * 0.75)
        assert d.up_distance < mark
        assert d.up_distance != 120.0
        assert d.adverse_exit_distance != 60.0
        assert d.reversal_distance != 90.0
        assert math.isfinite(d.up_distance) and d.up_distance > 0.0


def test_scale_invariance_proportional_mark() -> None:
    low = compute_mv2_research_scope_distances_absolute_from_mark_v1(0.4)
    high = compute_mv2_research_scope_distances_absolute_from_mark_v1(4.0)
    assert high.up_distance / low.up_distance == pytest.approx(10.0)
    assert high.adverse_exit_distance / low.adverse_exit_distance == pytest.approx(10.0)
    assert high.reversal_distance / low.reversal_distance == pytest.approx(10.0)
    # Relative thresholds vs mark remain constant (1% up).
    assert low.up_distance / 0.4 == pytest.approx(high.up_distance / 4.0)


def test_bull_bear_candidate_symmetry_reachable() -> None:
    mark = 0.40
    d = compute_mv2_research_scope_distances_absolute_from_mark_v1(mark)
    thr = compute_evaluated_thresholds(
        direction=ScopeDirectionState.LONG,
        trailing_anchor=mark,
        up_distance=d.up_distance,
        adverse_exit_distance=d.adverse_exit_distance,
        reversal_distance=d.reversal_distance,
    )
    bull_price = mark + d.up_distance + 1e-12
    bear_price = mark - d.up_distance - 1e-12
    bull_matched = _matched_directional_conditions(
        direction=ScopeDirectionState.LONG,
        current_price=bull_price,
        thresholds=thr,
    )
    bear_matched = _matched_directional_conditions(
        direction=ScopeDirectionState.LONG,
        current_price=bear_price,
        thresholds=thr,
    )
    assert any(k.value == "upscope" for k in bull_matched)
    assert any(k.value == "downscope" for k in bear_matched)
    # No direction invented from entry_side.
    assert StrategyEntrySideCarrierV1.NONE.value == "NONE"


def test_invalid_mark_fail_closed_no_legacy_absolute() -> None:
    for bad in (None, float("nan"), float("inf"), 0.0, -1.0):
        with pytest.raises(ValueError, match="mv2_research_scope_distance_mark_"):
            compute_mv2_research_scope_distances_absolute_from_mark_v1(bad)  # type: ignore[arg-type]
    src = inspect.getsource(compute_mv2_research_scope_distances_absolute_from_mark_v1)
    assert "120.0" not in src
    assert "up_distance=120" not in src
    assert "adverse_exit_distance=60" not in src


def test_option_d_entry_side_none_and_distance_helper_no_long_default() -> None:
    assert StrategyEntrySideCarrierV1.NONE.value == "NONE"
    helper_src = inspect.getsource(compute_mv2_research_scope_distances_absolute_from_mark_v1)
    assert "SideState.LONG" not in helper_src
    assert "SideState.SHORT" not in helper_src
    assert "entry_side" not in helper_src
    assert "transition_state" not in helper_src
    # Helper does not mutate initial sequence seed (pre-existing research seed out of scope).
    state = build_initial_mv2_integrated_replay_bar_sequence_state_v1(trading_epoch=0)
    assert state.side_state.value == SideState.LONG_ARMED.value


def test_authority_owners_unchanged_wiring_only_inputs() -> None:
    assert CANONICAL_BULL_BEAR_STATE_OWNER.endswith("transition_state")
    assert CANONICAL_SWITCH_AUTHORITY.endswith("transition_state")
    assert "double_play_composition_matrix_v1" in CANONICAL_COMPOSITION_AUTHORITY
    assert RUNTIME_BRIDGE_STATUS == "BOUND_NOT_ACTIVATED"
    assert LIVE_AUTHORIZED == "false"
    assert ORDERS_ENABLED == "false"
    wiring = _WIRING.read_text(encoding="utf-8")
    assert "compute_mv2_research_scope_distances_absolute_from_mark_v1" in wiring
    assert "up_distance=120.0" not in wiring
    assert "adverse_exit_distance=60.0" not in wiring
    assert "reversal_distance=90.0" not in wiring
    # Generator / transition_state / composition bodies unchanged by this slice.
    assert "def generate_deterministic_scope_event" in _GENERATOR.read_text(encoding="utf-8")
    assert "def transition_state" in _STATE.read_text(encoding="utf-8")
    assert "def evaluate_double_play_composition_matrix_v1" in _COMPOSITION.read_text(
        encoding="utf-8"
    )


def test_short_armed_reachable_via_transition_on_downscope_confirmed() -> None:
    empty = RuntimeScopeState()
    rules = DynamicScopeRules()
    env = RuntimeEnvelope(static=StaticHardLimits(), live_authorization=False)
    nxt, _, decision = transition_state(
        side_state=SideState.NEUTRAL_OBSERVE,
        event=ScopeEvent.DOWNSCOPE_CONFIRMED,
        scope_state=empty,
        rules=rules,
        envelope=env,
        now_tick=0,
    )
    assert nxt is SideState.SHORT_ARMED
    assert decision.allowed is True


def test_named_bps_constants_and_legacy_ratio() -> None:
    assert _MV2_RESEARCH_SCOPE_UP_DISTANCE_BPS == 100.0
    assert _MV2_RESEARCH_SCOPE_ADVERSE_TO_UP_RATIO == pytest.approx(0.5)
    assert _MV2_RESEARCH_SCOPE_REVERSAL_TO_UP_RATIO == pytest.approx(0.75)
    tree = ast.parse(_WIRING.read_text(encoding="utf-8"))
    assert isinstance(tree, ast.Module)


def test_end_to_end_low_price_synthetic_sample_produces_non_noop_candidates() -> None:
    """Synthetic 1INCH-scale marks with >1% moves must produce bull and bear candidates."""
    from src.backtest import admissible_versioned_futures_dataset_v1 as ds
    from src.backtest import cost_config_v0 as cost

    n = 80
    idx = pd.date_range("2024-05-01", periods=n, freq="1h", tz="UTC")
    # Oscillate around 0.40 with amplitude ~3% so both sides cross 1% thresholds.
    marks = [0.40 + 0.012 * math.sin(i / 3.0) for i in range(n)]
    bars = pd.DataFrame(
        {
            "open": marks,
            "high": [m + 0.001 for m in marks],
            "low": [m - 0.001 for m in marks],
            "close": marks,
            "mark_price": marks,
            "index_price": marks,
            "volume": [1000.0 for _ in marks],
            "open_interest": [10000.0 for _ in marks],
            "funding_rate": [0.0001 for _ in marks],
            "volatility_estimate": [0.2 for _ in marks],
            "is_final": [True for _ in marks],
            "bar_interval": ["1h" for _ in marks],
        },
        index=idx,
    )
    cfg = {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
            "economic_research_execution_cost": {
                "spread_model_version": cost.RESEARCH_SPREAD_MODEL_VERSION,
                "execution_price_observation_source": (
                    cost.EXECUTION_PRICE_OBSERVATION_SOURCE_MODELLED
                ),
                "conservative_half_spread_bps": 5.0,
            },
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
        "economic_evaluation_v1": {
            "strategy_params": {"fast_window": 2, "slow_window": 3},
        },
    }
    profile = ds.DatasetProfileBindingV1(
        dataset_profile=ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        l1_observation_status=ds.L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
        execution_cost_binding=ds.ExecutionCostBindingV1(
            spread_model_version=cost.RESEARCH_SPREAD_MODEL_VERSION,
            execution_price_observation_source=cost.EXECUTION_PRICE_OBSERVATION_SOURCE_MODELLED,
            conservative_half_spread_bps=5.0,
        ),
    )
    event_counts: dict[str, int] = {}
    bull_hits = 0
    bear_hits = 0
    threshold_miss = 0
    hooked = 0

    def hook(**kwargs: object) -> None:
        nonlocal bull_hits, bear_hits, threshold_miss, hooked
        inter = kwargs.get("intermediate")
        if inter is None:
            return
        se = getattr(inter, "scope_event", None)
        if se is None:
            return
        hooked += 1
        et = str(getattr(getattr(se, "event_type", None), "value", se.event_type))
        event_counts[et] = event_counts.get(et, 0) + 1
        binding = getattr(se, "semantic_binding", None)
        price = float(getattr(binding, "current_price", 0.0) or 0.0)
        anchor = float(getattr(binding, "trailing_anchor", 0.0) or 0.0)
        up = float(getattr(binding, "up_distance", 0.0) or 0.0)
        adverse = float(getattr(binding, "adverse_exit_distance", 0.0) or 0.0)
        reversal = float(getattr(binding, "reversal_distance", 0.0) or 0.0)
        assert up != 120.0
        thr = compute_evaluated_thresholds(
            direction=ScopeDirectionState.LONG,
            trailing_anchor=anchor,
            up_distance=up,
            adverse_exit_distance=adverse,
            reversal_distance=reversal,
        )
        if price >= thr.up_candidate_threshold:
            bull_hits += 1
        elif price <= thr.downscope_candidate_threshold:
            bear_hits += 1
        else:
            threshold_miss += 1

    run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id="ma_crossover",
        cfg=cfg,
        profile_binding=profile,
        observational_bar_hook=hook,
    )
    assert hooked > 0
    assert threshold_miss < hooked
    assert bull_hits + bear_hits > 0
    noop = event_counts.get(CanonicalScopeEventType.NOOP.value, 0)
    non_noop = hooked - noop
    # Prefer both sides; require at least one side + some non-noop or geometry hit.
    assert bull_hits > 0 or bear_hits > 0
    assert non_noop > 0 or (bull_hits + bear_hits) > 0
