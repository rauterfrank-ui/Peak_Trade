"""Deterministic CURRENT productive MV2+Double-Play natural ENTER fixtures.

Encodes bilateral first-class Long/Short entry under CURRENT semantics:

  Long (oneshot/naked): UPSCOPE_CONFIRMED may ENTER_LONG same cycle.
  Long (layered compose): confirm cycle may ARM only; ENTER_LONG on later cycle.
  Short: DOWNSCOPE_CONFIRMED arms (may REDUCE same cycle); ENTER_SHORT later
         under SHORT-oriented geometry.

Identical cycle timing is NOT required.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    bind_occupied_lane_governed_cycle_store_roots_v1,
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    OCCUPANCY_OCCUPIED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
    lane_state_root_for,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    persist_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    _lane_pair_v1,
)
from src.ops.p5_10_productive_activation_and_binding_v1.productive_cycle_bind_seam_v1 import (
    ensure_productive_layered_core_episode_store_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    EntryExitDirectionState,
    ExistingPositionSide,
)
from trading.master_v2.double_play_state import SideState
from trading.market_state.directional_confirmation_progress_v1 import (
    ConfirmationAssessmentStateV1,
)

NATURAL_ENTER_MARK_INCREMENT_V1 = 5.0
NATURAL_ENTER_UPSCOPE_CONFIRM_TS_UNIX_V1 = 1_700_000_080.0
NATURAL_ENTER_DOWNSCOPE_CONFIRM_TS_UNIX_V1 = 1_700_000_080.0
NATURAL_ENTER_SHORT_AFTER_ARM_TS_DELTA_V1 = 20.0

CANONICAL_BULL_BEAR_SYMMETRY_INVARIANT_V1 = (
    "Both Bull/Long and Bear/Short are first-class opposing layers on the SAME "
    "selected future inside ONE MV2+Double-Play decision universe. Only one side "
    "may be active at a time. Normal directional/regime change uses State Switch, "
    "not Kill-All. Both directions must be naturally armable and enterable under "
    "their respective CURRENT scope orientations. Identical cycle timing is NOT "
    "required."
)

# CURRENT Decision-SSOT authority chain (trading semantic layers).
# Authority: trading.master_v2.integrated_offline_trading_logic_replay_v1 module docstring
# + V32_CURRENT_MV2_DP_CONCEPT_ALIGNMENT_V1 (CURRENT_MV2_DP_DECISION_SSOT).
# Distinct from naked L1–L10 mechanical articulation (P5; not parallel decision SSOT).
CURRENT_CANONICAL_DECISION_SSOT_LAYER_ORDER_V1: tuple[str, ...] = (
    "C1_OBSERVATION_ACCEPTANCE",
    "C2_CONFIRMATION_PROGRESS",
    "C3_DIRECTIONAL_ASSESSMENT_STATUS",
    "SURVIVAL_DOMAIN",
    "SUITABILITY_DOMAIN",
    "COMPOSITION_CONFIRMED_ADMISSIBILITY",
    "DOUBLE_PLAY_STATE_TRANSITION",
    "ENTRY_EXIT_POLICY",
)
CURRENT_CANONICAL_DECISION_SSOT_LAYER_COUNT_V1 = len(CURRENT_CANONICAL_DECISION_SSOT_LAYER_ORDER_V1)
# Within-cycle Dynamic Scope predecessor bound by V32 (same replay; not a 9th SSOT layer).
CURRENT_V32_DYNAMIC_SCOPE_EVENT_OWNER_V1 = "generate_deterministic_scope_event"
# Mechanical L1–L10 count (evidence); NOT Decision-SSOT.
NAKED_LAYERED_CORE_L1_L10_COUNT_V1 = 10
LAYER_COUNT_MATCH_STATUS_V1 = "DIFFERENT_BUT_EXPLAINED"


def assert_complete_decision_ssot_layer_trace_v1(
    cycle: Any,
    *,
    expected_selected_side: str,
) -> tuple[str, ...]:
    """Prove one productive cycle traversed the CURRENT Decision-SSOT layer stack.

    ``expected_selected_side`` must be ``\"LONG\"`` or ``\"SHORT\"`` (explicit; no default).
    """
    side = str(expected_selected_side or "").strip().upper()
    if side not in {"LONG", "SHORT"}:
        raise AssertionError("expected_selected_side must be LONG or SHORT")
    assert cycle.replay is not None and cycle.replay.replay_pass is True
    intermediate = cycle.replay.intermediate
    assert intermediate is not None

    # V32 Dynamic Scope owner present in-cycle (geometry; not trade recommendation).
    assert intermediate.scope_event is not None
    assert intermediate.scope_event.event_type is not None

    carrier = intermediate.directional_confirmation_progress_after
    assert carrier is not None  # C1/C2 durable side carrier after cycle

    if side == "LONG":
        assert intermediate.bull_assessment is not None
        assert intermediate.bull_assessment.status is not None  # C3
        assert intermediate.bull_survival is not None
        assert intermediate.bull_suitability is not None
        assert intermediate.bear_assessment is None
        assert intermediate.composition_result.composition_status is CompositionStatus.LONG_SELECTED
        assert carrier.bull_confirmation_state.assessment_state is (
            ConfirmationAssessmentStateV1.CONFIRMED
        )
        assert carrier.bull_confirmation_state.distinct_confirmation_observation_count >= 2
    else:
        assert intermediate.bear_assessment is not None
        assert intermediate.bear_assessment.status is not None
        assert intermediate.bear_survival is not None
        assert intermediate.bear_suitability is not None
        assert intermediate.bull_assessment is None
        assert (
            intermediate.composition_result.composition_status is CompositionStatus.SHORT_SELECTED
        )
        assert carrier.bear_confirmation_state.assessment_state is (
            ConfirmationAssessmentStateV1.CONFIRMED
        )
        assert carrier.bear_confirmation_state.distinct_confirmation_observation_count >= 2

    assert intermediate.state_switch is not None
    assert intermediate.transition_decision is not None
    assert intermediate.entry_exit_decision is not None
    return CURRENT_CANONICAL_DECISION_SSOT_LAYER_ORDER_V1


def governed_c1_candles_payload_from_enter_closes_v1(
    *,
    enter_closes: Sequence[float],
    last_event_ts_unix: float,
) -> dict[str, object]:
    """C1 payload whose extracted closes match the natural-enter price path."""
    last_ms = int(float(last_event_ts_unix) * 1000)
    rows: list[list[str]] = []
    for index, close_px in enumerate(enter_closes):
        ts = str(last_ms - (len(enter_closes) - 1 - index) * 60_000)
        px = f"{float(close_px):.4f}"
        rows.append([ts, px, px, px, px, "10", "100", "USDT", "1"])
    return {"code": "0", "data": rows}


def governed_productive_c1_event_ts_unix_v1(*, offset_seconds: float = 120.0) -> float:
    """C1 observation time satisfying ``PREVIOUS_C1_VENUE_EVENT_TIME`` gate for governed cycles."""
    from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
        PREVIOUS_C1_VENUE_EVENT_TIME,
    )

    return float(PREVIOUS_C1_VENUE_EVENT_TIME) + float(offset_seconds)


def strong_uptrend_closes_v1(
    *, count: int = 64, base: float = 1000.0, step: float = 10.0
) -> tuple[float, ...]:
    return tuple(base + float(index) * step for index in range(count))


def strong_downtrend_closes_v1(
    *, count: int = 64, base: float = 1630.0, step: float = 10.0
) -> tuple[float, ...]:
    return tuple(base - float(index) * step for index in range(count))


def natural_enter_long_closes_v1(
    uptrend: tuple[float, ...] | None = None,
    *,
    mark_increment: float = NATURAL_ENTER_MARK_INCREMENT_V1,
) -> tuple[float, ...]:
    path = uptrend if uptrend is not None else strong_uptrend_closes_v1()
    return tuple(list(path) + [float(path[-1]) + float(mark_increment)])


def natural_enter_short_arm_closes_v1(
    downtrend: tuple[float, ...] | None = None,
    *,
    mark_decrement: float = NATURAL_ENTER_MARK_INCREMENT_V1,
) -> tuple[float, ...]:
    path = downtrend if downtrend is not None else strong_downtrend_closes_v1()
    return tuple(list(path) + [float(path[-1]) - float(mark_decrement)])


def natural_enter_short_after_arm_closes_v1(
    arm_closes: Sequence[float],
    *,
    mark_decrement: float = NATURAL_ENTER_MARK_INCREMENT_V1,
) -> tuple[float, ...]:
    return tuple(list(arm_closes) + [float(arm_closes[-1]) - float(mark_decrement)])


def run_upscope_candidate_progress_cycles_v1(
    *,
    bound: BoundInstrumentV1,
    g17_typed_vol_producer: object,
    uptrend: tuple[float, ...] | None = None,
) -> tuple[Any, Any, tuple[float, ...]]:
    """Origin + UPSCOPE_CANDIDATE cycle (cap61 bull candidate, scope candidate)."""
    from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
        _cycle,
    )

    path = uptrend if uptrend is not None else strong_uptrend_closes_v1()
    origin = _cycle(
        cycle_id="natural-enter-origin",
        bound_instrument=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        mark_px=float(path[0]),
        event_ts_unix=1_700_000_000.0,
        closes=path,
    )
    upscope_candidate = _cycle(
        cycle_id="natural-enter-upscope-candidate",
        bound_instrument=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        incoming_cursor=origin.outgoing_cursor,
        mark_px=float(path[-1]),
        event_ts_unix=1_700_000_060.0,
        closes=path,
    )
    return origin, upscope_candidate, path


def run_downscope_candidate_progress_cycles_v1(
    *,
    bound: BoundInstrumentV1,
    g17_typed_vol_producer: object,
    downtrend: tuple[float, ...] | None = None,
) -> tuple[Any, Any, tuple[float, ...]]:
    """Origin + DOWNSCOPE_CANDIDATE under NEUTRAL / LONG-oriented geometry."""
    from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
        _cycle,
    )

    path = downtrend if downtrend is not None else strong_downtrend_closes_v1()
    origin = _cycle(
        cycle_id="natural-short-origin",
        bound_instrument=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        mark_px=float(path[0]),
        event_ts_unix=1_700_000_000.0,
        closes=path,
    )
    downscope_candidate = _cycle(
        cycle_id="natural-short-downscope-candidate",
        bound_instrument=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        incoming_cursor=origin.outgoing_cursor,
        mark_px=float(path[-1]),
        event_ts_unix=1_700_000_060.0,
        closes=path,
    )
    return origin, downscope_candidate, path


def run_natural_enter_long_cycle_v1(
    *,
    upscope_candidate_cycle: Any,
    bound: BoundInstrumentV1,
    g17_typed_vol_producer: object,
    uptrend: tuple[float, ...] | None = None,
    mark_increment: float = NATURAL_ENTER_MARK_INCREMENT_V1,
    event_ts_unix: float = NATURAL_ENTER_UPSCOPE_CONFIRM_TS_UNIX_V1,
    cycle_id: str = "natural-enter-long",
) -> tuple[Any, tuple[float, ...], float]:
    """UPSCOPE_CONFIRMED + C3 CONFIRMED + ``enter_long`` on one productive oneshot cycle."""
    from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
        _cycle,
    )

    path = uptrend if uptrend is not None else strong_uptrend_closes_v1()
    enter_closes = natural_enter_long_closes_v1(path, mark_increment=mark_increment)
    mark_px = float(enter_closes[-1])
    enter_cycle = _cycle(
        cycle_id=str(cycle_id),
        bound_instrument=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        incoming_cursor=upscope_candidate_cycle.outgoing_cursor,
        closes=enter_closes,
        mark_px=mark_px,
        event_ts_unix=float(event_ts_unix),
    )
    return enter_cycle, enter_closes, mark_px


def run_natural_short_arm_cycle_v1(
    *,
    downscope_candidate_cycle: Any,
    bound: BoundInstrumentV1,
    g17_typed_vol_producer: object,
    downtrend: tuple[float, ...] | None = None,
    mark_decrement: float = NATURAL_ENTER_MARK_INCREMENT_V1,
    event_ts_unix: float = NATURAL_ENTER_DOWNSCOPE_CONFIRM_TS_UNIX_V1,
    cycle_id: str = "natural-short-arm",
) -> tuple[Any, tuple[float, ...], float]:
    """DOWNSCOPE_CONFIRMED arm cycle — ENTER_SHORT not required on this cycle."""
    from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
        _cycle,
    )

    path = downtrend if downtrend is not None else strong_downtrend_closes_v1()
    arm_closes = natural_enter_short_arm_closes_v1(path, mark_decrement=mark_decrement)
    mark_px = float(arm_closes[-1])
    arm_cycle = _cycle(
        cycle_id=str(cycle_id),
        bound_instrument=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        incoming_cursor=downscope_candidate_cycle.outgoing_cursor,
        closes=arm_closes,
        mark_px=mark_px,
        event_ts_unix=float(event_ts_unix),
    )
    return arm_cycle, arm_closes, mark_px


def run_natural_enter_short_after_arm_cycle_v1(
    *,
    arm_cycle: Any,
    bound: BoundInstrumentV1,
    g17_typed_vol_producer: object,
    arm_closes: Sequence[float],
    mark_decrement: float = NATURAL_ENTER_MARK_INCREMENT_V1,
    event_ts_unix: float | None = None,
    cycle_id: str = "natural-enter-short",
) -> tuple[Any, tuple[float, ...], float]:
    """Subsequent SHORT-oriented cycle producing ``enter_short``."""
    from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
        _cycle,
    )

    enter_closes = natural_enter_short_after_arm_closes_v1(
        arm_closes, mark_decrement=mark_decrement
    )
    mark_px = float(enter_closes[-1])
    if event_ts_unix is None:
        event_ts_unix = (
            NATURAL_ENTER_DOWNSCOPE_CONFIRM_TS_UNIX_V1 + NATURAL_ENTER_SHORT_AFTER_ARM_TS_DELTA_V1
        )
    enter_cycle = _cycle(
        cycle_id=str(cycle_id),
        bound_instrument=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        incoming_cursor=arm_cycle.outgoing_cursor,
        closes=enter_closes,
        mark_px=mark_px,
        event_ts_unix=float(event_ts_unix),
    )
    return enter_cycle, enter_closes, mark_px


def assert_natural_enter_long_cycle_v1(cycle: Any) -> None:
    assert str(cycle.decision_outcome) == "enter_long"
    assert_complete_decision_ssot_layer_trace_v1(cycle, expected_selected_side="LONG")
    intermediate = cycle.replay.intermediate
    ee = intermediate.entry_exit_decision
    assert ee.previous_direction_state is EntryExitDirectionState.LONG_ARMED
    assert "entry_long_eligible" in ee.reason_codes
    assert cycle.outgoing_cursor is not None
    assert cycle.outgoing_cursor.side_state in {
        SideState.LONG_ARMED,
        SideState.LONG_ARMED_NEUTRAL_START,
        SideState.LONG_ARMED_SWITCH_TERMINAL,
        SideState.LONG_ACTIVE,
    }


def assert_natural_short_arm_cycle_v1(cycle: Any) -> None:
    """Arm cycle: SHORT_ARMED* + SHORT_SELECTED; ENTER_SHORT not required."""
    assert_complete_decision_ssot_layer_trace_v1(cycle, expected_selected_side="SHORT")
    intermediate = cycle.replay.intermediate
    # DOWNSCOPE_CONFIRMED may coexist with adverse_exit (geometry + precedence).
    assert intermediate.scope_event is not None
    assert cycle.outgoing_cursor is not None
    assert cycle.outgoing_cursor.side_state in {
        SideState.SHORT_ARMED,
        SideState.SHORT_ARMED_NEUTRAL_START,
        SideState.SHORT_ARMED_SWITCH_TERMINAL,
    }
    assert str(cycle.decision_outcome) != "enter_long"
    # Same-cycle ENTER_SHORT is not required (adverse/mandatory-exit may REDUCE).


def assert_natural_enter_short_cycle_v1(cycle: Any) -> None:
    assert str(cycle.decision_outcome) == "enter_short"
    assert_complete_decision_ssot_layer_trace_v1(cycle, expected_selected_side="SHORT")
    intermediate = cycle.replay.intermediate
    ee = intermediate.entry_exit_decision
    assert ee.previous_direction_state is EntryExitDirectionState.SHORT_ARMED
    assert "entry_short_eligible" in ee.reason_codes
    assert cycle.outgoing_cursor is not None
    assert cycle.outgoing_cursor.side_state in {
        SideState.SHORT_ARMED,
        SideState.SHORT_ARMED_NEUTRAL_START,
        SideState.SHORT_ARMED_SWITCH_TERMINAL,
        SideState.SHORT_ACTIVE,
    }


def seed_lane_cursor_for_natural_enter_invoke_v1(
    *,
    lane_store_root: Path,
    bound: BoundInstrumentV1,
    prior_cycle: Any,
    enter_closes: tuple[float, ...],
    mark_px: float,
    event_ts_unix: float,
) -> None:
    """Persist prior-cycle cursor + P5 episode so the next governed cycle can ENTER."""
    lane_store_root.mkdir(parents=True, exist_ok=True)
    cursor = prior_cycle.outgoing_cursor
    persist_current_productive_sidestate_confirmation_cursor_v1(cursor, store_root=lane_store_root)
    ensure_productive_layered_core_episode_store_v1(
        store_root=lane_store_root,
        bound_instrument=bound,
        mark_price_m_t=float(mark_px),
        finalized_closes=enter_closes,
        last_finalized_event_ts_unix=float(event_ts_unix),
        outgoing_cursor=cursor,
    )


def seed_lane_cursor_for_natural_enter_consumer_v1(
    *,
    topology_root: Path,
    bound: BoundInstrumentV1,
    prior_cycle: Any,
    enter_closes: tuple[float, ...],
    mark_px: float,
    event_ts_unix: float,
) -> tuple[IsolatedLaneSlotV1, BoundInstrumentV1]:
    lane_id = "LANE_1"
    root = lane_state_root_for(topology_state_root_base=topology_root, lane_id=lane_id)
    slot = IsolatedLaneSlotV1(
        lane_id=lane_id,
        occupancy=OCCUPANCY_OCCUPIED,
        canonical_instrument_id=bound.instrument_id,
        lane_state_root=root,
        universe_snapshot_id=bound.universe_snapshot_id,
        ranking_snapshot_id=bound.ranking_snapshot_id,
        ranking_integrity_digest=bound.ranking_integrity_digest,
    )
    pairs = {lane_id: (slot, bound)}
    addressed = bind_occupied_lane_governed_cycle_store_roots_v1(pairs)
    store_root = Path(addressed[lane_id][0])
    seed_lane_cursor_for_natural_enter_invoke_v1(
        lane_store_root=store_root,
        bound=bound,
        prior_cycle=prior_cycle,
        enter_closes=enter_closes,
        mark_px=mark_px,
        event_ts_unix=event_ts_unix,
    )
    return slot, bound


def _compose_layered_lane_cycle_v1(
    *,
    pair: tuple[IsolatedLaneSlotV1, BoundInstrumentV1],
    g17_typed_vol_producer: object,
    closes: Sequence[float],
    mark_px: float,
    event_ts_unix: float,
    cycle_id_prefix: str,
) -> Any:
    return compose_occupied_lane_mv2_dp_durable_cycle_v1(
        {"LANE_1": pair},
        cycle_id_prefix=cycle_id_prefix,
        observed_unix=float(event_ts_unix) + 1.0,
        mark_px=float(mark_px),
        index_px=float(mark_px),
        bid_px=float(mark_px) - 0.5,
        ask_px=float(mark_px) + 0.5,
        volume=10.0,
        open_interest=20.0,
        funding_rate=0.0001,
        finalized_closes=tuple(closes),
        last_finalized_event_ts_unix=float(event_ts_unix),
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        g17_typed_vol_producers={"LANE_1": g17_typed_vol_producer},
    )["LANE_1"].cycle_result


def run_natural_enter_long_sequence_for_bound_v1(
    *,
    bound: BoundInstrumentV1,
    g17_typed_vol_producer: object,
) -> tuple[Any, Any, Any, tuple[float, ...], float]:
    _origin, upscope_candidate, path = run_upscope_candidate_progress_cycles_v1(
        bound=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
    )
    enter_cycle, enter_closes, mark_px = run_natural_enter_long_cycle_v1(
        upscope_candidate_cycle=upscope_candidate,
        bound=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        uptrend=path,
    )
    assert_natural_enter_long_cycle_v1(enter_cycle)
    return _origin, upscope_candidate, enter_cycle, enter_closes, mark_px


def run_natural_enter_short_sequence_for_bound_v1(
    *,
    bound: BoundInstrumentV1,
    g17_typed_vol_producer: object,
) -> tuple[Any, Any, Any, Any, tuple[float, ...], tuple[float, ...], float]:
    """Multi-cycle Short: arm on DOWNSCOPE_CONFIRMED, ENTER_SHORT on later cycle."""
    _origin, downscope_candidate, path = run_downscope_candidate_progress_cycles_v1(
        bound=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
    )
    arm_cycle, arm_closes, _arm_mark = run_natural_short_arm_cycle_v1(
        downscope_candidate_cycle=downscope_candidate,
        bound=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        downtrend=path,
    )
    assert_natural_short_arm_cycle_v1(arm_cycle)
    enter_cycle, enter_closes, mark_px = run_natural_enter_short_after_arm_cycle_v1(
        arm_cycle=arm_cycle,
        bound=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        arm_closes=arm_closes,
    )
    assert_natural_enter_short_cycle_v1(enter_cycle)
    return (
        _origin,
        downscope_candidate,
        arm_cycle,
        enter_cycle,
        arm_closes,
        enter_closes,
        mark_px,
    )


def run_layered_long_arm_then_enter_for_pre_external_v1(
    *,
    bound: BoundInstrumentV1,
    g17_typed_vol_producer: object,
    lane_state_root: Path,
) -> tuple[Any, Any, tuple[float, ...], float, float]:
    """Layered compose: arm under UPSCOPE confirm, then ENTER_LONG on next cycle.

    Returns (arm_cycle, enter_cycle, enter_closes, mark_px, enter_event_ts) where
    ``enter_closes``/``mark_px``/``enter_event_ts`` are the ENTER cycle inputs.
    Seeds lane store through the arm cycle so a single subsequent governed invoke
    can consume the ARMED cursor.
    """
    enter_ts = governed_productive_c1_event_ts_unix_v1()
    path = strong_uptrend_closes_v1()
    from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
        _cycle,
    )

    origin = _cycle(
        cycle_id="layered-long-origin",
        bound_instrument=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        mark_px=float(path[0]),
        event_ts_unix=enter_ts - 120.0,
        closes=path,
    )
    upscope_candidate = _cycle(
        cycle_id="layered-long-upscope-candidate",
        bound_instrument=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        incoming_cursor=origin.outgoing_cursor,
        mark_px=float(path[-1]),
        event_ts_unix=enter_ts - 60.0,
        closes=path,
    )
    arm_closes = natural_enter_long_closes_v1(path)
    arm_mark = float(arm_closes[-1])
    arm_ts = enter_ts

    pair = _lane_pair_v1(lane_state_root=lane_state_root, bound=bound)
    store_root = Path(pair[0].lane_state_root)
    persist_current_productive_sidestate_confirmation_cursor_v1(
        upscope_candidate.outgoing_cursor,
        store_root=store_root,
    )
    ensure_productive_layered_core_episode_store_v1(
        store_root=store_root,
        bound_instrument=bound,
        mark_price_m_t=arm_mark,
        finalized_closes=arm_closes,
        last_finalized_event_ts_unix=arm_ts,
        outgoing_cursor=upscope_candidate.outgoing_cursor,
    )

    arm_cycle = _compose_layered_lane_cycle_v1(
        pair=pair,
        g17_typed_vol_producer=g17_typed_vol_producer,
        closes=arm_closes,
        mark_px=arm_mark,
        event_ts_unix=arm_ts,
        cycle_id_prefix="layered-long-arm",
    )
    assert arm_cycle.outgoing_cursor is not None
    assert arm_cycle.outgoing_cursor.side_state in {
        SideState.LONG_ARMED,
        SideState.LONG_ARMED_NEUTRAL_START,
        SideState.LONG_ARMED_SWITCH_TERMINAL,
    }
    assert str(arm_cycle.decision_outcome) != "enter_short"

    enter_closes = tuple(list(arm_closes) + [arm_mark + NATURAL_ENTER_MARK_INCREMENT_V1])
    enter_mark = float(enter_closes[-1])
    enter_event_ts = arm_ts + NATURAL_ENTER_SHORT_AFTER_ARM_TS_DELTA_V1
    enter_cycle = _compose_layered_lane_cycle_v1(
        pair=pair,
        g17_typed_vol_producer=g17_typed_vol_producer,
        closes=enter_closes,
        mark_px=enter_mark,
        event_ts_unix=enter_event_ts,
        cycle_id_prefix="layered-long-enter",
    )
    assert_natural_enter_long_cycle_v1(enter_cycle)
    return arm_cycle, enter_cycle, enter_closes, enter_mark, enter_event_ts


def prepare_layered_long_armed_seed_for_pre_external_invoke_v1(
    *,
    bound: BoundInstrumentV1,
    g17_typed_vol_producer: object,
    lane_state_root: Path,
) -> tuple[Any, tuple[float, ...], float, float]:
    """Stop after layered ARM; leave store ready for one governed ENTER cycle."""
    enter_ts = governed_productive_c1_event_ts_unix_v1()
    path = strong_uptrend_closes_v1()
    from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
        _cycle,
    )

    origin = _cycle(
        cycle_id="preext-long-origin",
        bound_instrument=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        mark_px=float(path[0]),
        event_ts_unix=enter_ts - 120.0,
        closes=path,
    )
    upscope_candidate = _cycle(
        cycle_id="preext-long-upscope-candidate",
        bound_instrument=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        incoming_cursor=origin.outgoing_cursor,
        mark_px=float(path[-1]),
        event_ts_unix=enter_ts - 60.0,
        closes=path,
    )
    arm_closes = natural_enter_long_closes_v1(path)
    arm_mark = float(arm_closes[-1])
    arm_ts = enter_ts

    pair = _lane_pair_v1(lane_state_root=lane_state_root, bound=bound)
    store_root = Path(pair[0].lane_state_root)
    persist_current_productive_sidestate_confirmation_cursor_v1(
        upscope_candidate.outgoing_cursor,
        store_root=store_root,
    )
    ensure_productive_layered_core_episode_store_v1(
        store_root=store_root,
        bound_instrument=bound,
        mark_price_m_t=arm_mark,
        finalized_closes=arm_closes,
        last_finalized_event_ts_unix=arm_ts,
        outgoing_cursor=upscope_candidate.outgoing_cursor,
    )
    arm_cycle = _compose_layered_lane_cycle_v1(
        pair=pair,
        g17_typed_vol_producer=g17_typed_vol_producer,
        closes=arm_closes,
        mark_px=arm_mark,
        event_ts_unix=arm_ts,
        cycle_id_prefix="preext-long-arm",
    )
    assert arm_cycle.outgoing_cursor is not None
    assert arm_cycle.outgoing_cursor.side_state in {
        SideState.LONG_ARMED,
        SideState.LONG_ARMED_NEUTRAL_START,
        SideState.LONG_ARMED_SWITCH_TERMINAL,
    }
    assert str(arm_cycle.decision_outcome) != "enter_long"

    enter_closes = tuple(list(arm_closes) + [arm_mark + NATURAL_ENTER_MARK_INCREMENT_V1])
    enter_mark = float(enter_closes[-1])
    enter_event_ts = arm_ts + NATURAL_ENTER_SHORT_AFTER_ARM_TS_DELTA_V1
    return arm_cycle, enter_closes, enter_mark, enter_event_ts


def run_natural_enter_long_sequence_for_governed_pre_external_v1(
    *,
    bound: BoundInstrumentV1,
    g17_typed_vol_producer: object,
) -> tuple[Any, Any, Any, tuple[float, ...], float, float]:
    """Oneshot natural long with C1-gate-aligned event times (legacy helper)."""
    enter_ts = governed_productive_c1_event_ts_unix_v1()
    path = strong_uptrend_closes_v1()
    from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
        _cycle,
    )

    origin = _cycle(
        cycle_id="natural-enter-origin-governed-c1",
        bound_instrument=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        mark_px=float(path[0]),
        event_ts_unix=enter_ts - 120.0,
        closes=path,
    )
    upscope_candidate = _cycle(
        cycle_id="natural-enter-upscope-candidate-governed-c1",
        bound_instrument=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        incoming_cursor=origin.outgoing_cursor,
        mark_px=float(path[-1]),
        event_ts_unix=enter_ts - 60.0,
        closes=path,
    )
    enter_cycle, enter_closes, mark_px = run_natural_enter_long_cycle_v1(
        upscope_candidate_cycle=upscope_candidate,
        bound=bound,
        g17_typed_vol_producer=g17_typed_vol_producer,
        uptrend=path,
        event_ts_unix=enter_ts,
    )
    assert_natural_enter_long_cycle_v1(enter_cycle)
    return origin, upscope_candidate, enter_cycle, enter_closes, mark_px, enter_ts
