"""Advance occupied-lane MV2 state to layered LONG_ARMED for governed ENTER.

Origin/upscope use ``run_current_productive_master_v2_runtime_cycle_v1``;
ARM uses ``compose_occupied_lane_mv2_dp_durable_cycle_v1`` after cursor persist.
Does not call test ARM/ENTER seed helpers.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    OCCUPANCY_OCCUPIED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
    lane_state_root_for,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    INDEX_SOURCE_EXPLICIT_TEST_FIXTURE,
    build_provenance_from_resolved_cmc_mark_and_index_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_controlled_external_market_observation_v1 import (
    NATURAL_ENTER_MARK_INCREMENT_V1,
    governed_c1_aligned_g17_dk_producer_v1,
    governed_productive_c1_event_ts_unix_v1,
    natural_enter_long_closes_v1,
    strong_uptrend_closes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    persist_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.p5_10_productive_activation_and_binding_v1.productive_cycle_bind_seam_v1 import (
    ensure_productive_layered_core_episode_store_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_state import SideState

LANE_ID = "LANE_1"
SHORT_AFTER_ARM_TS_DELTA_V1 = 20.0


class LayeredLongMv2StateAdvanceError(RuntimeError):
    """Fail-closed MV2 state advance violation."""


@dataclass(frozen=True)
class LayeredLongMv2StateAdvanceForPreExternalV1:
    arm_cycle_id: str
    enter_closes: tuple[float, ...]
    enter_mark_px: float
    enter_event_ts_unix: float
    invoke_g17_producer: object
    arm_side_state: str
    arm_decision_outcome: str


def _lane_pair_v1(
    *, lane_state_root: Path, bound: BoundInstrumentV1
) -> tuple[IsolatedLaneSlotV1, BoundInstrumentV1]:
    root = lane_state_root_for(topology_state_root_base=Path(lane_state_root), lane_id=LANE_ID)
    slot = IsolatedLaneSlotV1(
        lane_id=LANE_ID,
        occupancy=OCCUPANCY_OCCUPIED,
        canonical_instrument_id=bound.instrument_id,
        lane_state_root=str(root),
        universe_snapshot_id=bound.universe_snapshot_id,
        ranking_snapshot_id=bound.ranking_snapshot_id,
        ranking_integrity_digest=bound.ranking_integrity_digest,
    )
    return slot, bound


def _provenance_v1(*, bound: BoundInstrumentV1, mark_px: float) -> object:
    index_px = float(mark_px) * 0.995
    return build_provenance_from_resolved_cmc_mark_and_index_v1(
        venue_native_id=str(bound.venue_native_id),
        mark_px=float(mark_px),
        index_px=index_px,
        index_source=INDEX_SOURCE_EXPLICIT_TEST_FIXTURE,
    )


def _offline_mv2_cycle_v1(
    *,
    bound: BoundInstrumentV1,
    cycle_id: str,
    g17_typed_vol_producer: object,
    closes: Sequence[float],
    mark_px: float,
    event_ts_unix: float,
    incoming_cursor: object | None = None,
) -> object:
    index_px = float(mark_px) * 0.995
    return run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id=cycle_id,
        observed_unix=float(event_ts_unix) + 100.0,
        mark_px=float(mark_px),
        index_px=index_px,
        bid_px=float(mark_px) - 0.5,
        ask_px=float(mark_px) + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=tuple(closes),
        last_finalized_event_ts_unix=float(event_ts_unix),
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        incoming_cursor=incoming_cursor,
        g17_typed_vol_producer=g17_typed_vol_producer,
        canonical_price_provenance=_provenance_v1(bound=bound, mark_px=float(mark_px)),
    )


def _compose_cycle_v1(
    *,
    pair: tuple[IsolatedLaneSlotV1, BoundInstrumentV1],
    g17_typed_vol_producer: object,
    closes: Sequence[float],
    mark_px: float,
    event_ts_unix: float,
    cycle_id_prefix: str,
) -> object:
    index_px = float(mark_px) * 0.995
    bound = pair[1]
    provenance = _provenance_v1(bound=bound, mark_px=float(mark_px))
    return compose_occupied_lane_mv2_dp_durable_cycle_v1(
        {LANE_ID: pair},
        cycle_id_prefix=cycle_id_prefix,
        observed_unix=float(event_ts_unix) + 1.0,
        mark_px=float(mark_px),
        index_px=index_px,
        bid_px=float(mark_px) - 0.5,
        ask_px=float(mark_px) + 0.5,
        volume=10.0,
        open_interest=20.0,
        funding_rate=0.0001,
        finalized_closes=tuple(closes),
        last_finalized_event_ts_unix=float(event_ts_unix),
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        g17_typed_vol_producers={LANE_ID: g17_typed_vol_producer},
        canonical_price_provenance=provenance,
    )[LANE_ID].cycle_result


def advance_layered_long_mv2_state_for_pre_external_v1(
    *,
    bound: BoundInstrumentV1,
    lane_state_root: Path,
    origin_main_sha: str = "",
    g17_evidence_root: Path | None = None,
) -> LayeredLongMv2StateAdvanceForPreExternalV1:
    """Run origin → upscope → arm chain; stop before governed ENTER cycle."""
    _ = origin_main_sha
    enter_ts = governed_productive_c1_event_ts_unix_v1()
    path = strong_uptrend_closes_v1()
    g17_root = g17_evidence_root or (Path(lane_state_root) / "g17-controlled")
    g17 = governed_c1_aligned_g17_dk_producer_v1(
        bound=bound,
        anchor_event_ts_unix=enter_ts,
        evidence_store_root=g17_root,
        mark_closes=path,
    )
    pair = _lane_pair_v1(lane_state_root=lane_state_root, bound=bound)
    store_root = Path(pair[0].lane_state_root)

    origin = _offline_mv2_cycle_v1(
        bound=bound,
        cycle_id="native-full-cycle-long-origin",
        g17_typed_vol_producer=g17,
        closes=path,
        mark_px=float(path[0]),
        event_ts_unix=enter_ts - 120.0,
    )
    upscope = _offline_mv2_cycle_v1(
        bound=bound,
        cycle_id="native-full-cycle-long-upscope",
        g17_typed_vol_producer=g17,
        closes=path,
        mark_px=float(path[-1]),
        event_ts_unix=enter_ts - 60.0,
        incoming_cursor=origin.outgoing_cursor,
    )
    if upscope.outgoing_cursor is None:
        raise LayeredLongMv2StateAdvanceError("UPSCOPE_OUTGOING_CURSOR_MISSING")

    arm_closes = natural_enter_long_closes_v1(path)
    arm_mark = float(arm_closes[-1])
    arm_ts = enter_ts

    persist_current_productive_sidestate_confirmation_cursor_v1(
        upscope.outgoing_cursor,
        store_root=store_root,
    )
    ensure_productive_layered_core_episode_store_v1(
        store_root=store_root,
        bound_instrument=bound,
        mark_price_m_t=arm_mark,
        finalized_closes=arm_closes,
        last_finalized_event_ts_unix=arm_ts,
        outgoing_cursor=upscope.outgoing_cursor,
    )

    arm = _compose_cycle_v1(
        pair=pair,
        g17_typed_vol_producer=g17,
        closes=arm_closes,
        mark_px=arm_mark,
        event_ts_unix=arm_ts,
        cycle_id_prefix="native-full-cycle-long-arm",
    )
    if arm.outgoing_cursor is None:
        raise LayeredLongMv2StateAdvanceError("ARM_OUTGOING_CURSOR_MISSING")
    side = arm.outgoing_cursor.side_state
    if side not in {
        SideState.LONG_ARMED,
        SideState.LONG_ARMED_NEUTRAL_START,
        SideState.LONG_ARMED_SWITCH_TERMINAL,
    }:
        raise LayeredLongMv2StateAdvanceError(f"ARM_SIDE_STATE_UNEXPECTED:{side}")
    if str(arm.decision_outcome) == "enter_long":
        raise LayeredLongMv2StateAdvanceError("ENTER_LONG_BEFORE_GOVERNED_CYCLE")

    enter_closes = tuple(list(arm_closes) + [arm_mark + NATURAL_ENTER_MARK_INCREMENT_V1])
    enter_mark = float(enter_closes[-1])
    enter_event_ts = arm_ts + SHORT_AFTER_ARM_TS_DELTA_V1
    invoke_g17 = governed_c1_aligned_g17_dk_producer_v1(
        bound=bound,
        anchor_event_ts_unix=enter_event_ts,
        evidence_store_root=g17_root / "invoke",
        mark_closes=enter_closes,
    )
    _ = origin
    return LayeredLongMv2StateAdvanceForPreExternalV1(
        arm_cycle_id=str(getattr(arm, "cycle_id", "") or "native-full-cycle-long-arm"),
        enter_closes=enter_closes,
        enter_mark_px=enter_mark,
        enter_event_ts_unix=enter_event_ts,
        invoke_g17_producer=invoke_g17,
        arm_side_state=str(side),
        arm_decision_outcome=str(arm.decision_outcome),
    )
