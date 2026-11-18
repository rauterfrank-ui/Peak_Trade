"""Run the flat LANE_1 entry decision on venue Marks in isolated offline state."""

from __future__ import annotations

import fcntl
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_core_entry_assessment_frame_v1 import (
    read_current_core_entry_assessment_frame_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_candidate_input_gate_v1 import (
    finalized_candidate_candle_history_rejection_codes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_reconciliation_admission_v1 import (
    ProductiveMasterV2ReconciliationAdmissionContextV1,
    ProductiveMasterV2ReconciliationAdmissionV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    CurrentProductiveMasterV2CycleResultV1,
    extract_finalized_candle_closes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    build_s8_occupied_lane_pairs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
    parse_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome, ExistingPositionSide


LANE_ID = "LANE_1"
ENTRY_MARK_STATE_DIRECTORY = "flat-entry-mark-v2"
ENTRY_OUTCOMES = {DecisionOutcome.ENTER_LONG.value, DecisionOutcome.ENTER_SHORT.value}
BAR_SECONDS = 60


@dataclass(frozen=True)
class FirstEntryMarkCycleV2:
    mark_event_unix: float
    candle_open_unix: float
    cycle: CurrentProductiveMasterV2CycleResultV1 | None
    status: str


def run_first_entry_mark_cycle_v2(
    *,
    offline_state_root: Path,
    bound: BoundInstrumentV1,
    cycle_id: str,
    observed_unix: float,
    candles_payload: Mapping[str, Any],
    mark_price_payload: Mapping[str, Any],
    index_tickers_payload: Mapping[str, Any] | None,
    mark_acquired_at_utc: str,
    bid_px: float,
    ask_px: float,
    volume: float,
    open_interest: float,
    funding_rate: float,
    venue_flat: bool,
    g17_producer: CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    reconciliation: ProductiveMasterV2ReconciliationAdmissionV1,
) -> FirstEntryMarkCycleV2:
    """Take one fresh Mark through the existing Core and durable entry cursor.

    The caller supplies a finalized 1m window as feature context, a current
    Mark and the same typed G17 and reconciliation inputs as the original
    entry decision. The state directory belongs to this offline run. After an
    ENTER, downstream fill/position ownership is outside this entry clock.
    """
    if venue_flat is not True:
        raise ValueError("FIRST_ENTRY_MARK_REQUIRES_FLAT_POSITION")
    if (
        reconciliation.context_class
        is ProductiveMasterV2ReconciliationAdmissionContextV1.PRODUCTIVE_UPSTREAM_GATE
    ):
        raise ValueError("FIRST_ENTRY_MARK_REQUIRES_OFFLINE_RECONCILIATION")
    reconciliation.validate_for_productive_master_v2_entry_v1(instrument_id=bound.instrument_id)
    history_codes = finalized_candidate_candle_history_rejection_codes_v1(candles_payload)
    if history_codes:
        raise ValueError("FIRST_ENTRY_MARK_HISTORY:" + ",".join(history_codes))
    closes, candle_open = extract_finalized_candle_closes_v1(candles_payload)
    if candle_open is None:
        raise ValueError("FIRST_ENTRY_MARK_FINALIZED_CANDLE_REQUIRED")
    provenance = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
        mark_price_payload=mark_price_payload,
        venue_native_id=bound.venue_native_id,
        index_from_index_tickers=index_tickers_payload,
        mark_acquired_at_utc=mark_acquired_at_utc,
    )
    mark_event = provenance.require_current_mark_clock_v1(observed_unix=observed_unix)
    if mark_event < candle_open + BAR_SECONDS:
        raise ValueError("FIRST_ENTRY_MARK_PRECEDES_CANDLE_CLOSE")

    pairs = build_s8_occupied_lane_pairs_v1(
        lane_state_root=Path(offline_state_root).resolve() / ENTRY_MARK_STATE_DIRECTORY,
        bound=bound,
    )
    lane_root = Path(pairs[LANE_ID][0].lane_state_root)
    lane_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (lane_root / "first_entry_mark_v2.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        prior = load_current_productive_sidestate_confirmation_cursor_v1(lane_root)
        if prior is not None:
            cursor = parse_current_productive_sidestate_confirmation_cursor_v1(prior)
            if (cursor.instrument_id, cursor.venue_native_id) != (
                bound.instrument_id,
                bound.venue_native_id,
            ):
                raise ValueError("FIRST_ENTRY_MARK_CURSOR_BINDING_MISMATCH")
            frame = read_current_core_entry_assessment_frame_v1(cursor)
            accepted = cursor.cap61_confirmation_state.observation_acceptance_state
            last = accepted.last_accepted_observation_identity
            market_ref = cursor.entry_assessment_frame.get("market_context")
            if market_ref is None:
                raise ValueError("FIRST_ENTRY_MARK_CURSOR_CLOCK_MISMATCH")
            market = json.loads(market_ref["canonical"])
            if (
                last is None
                or last.venue_event_time
                != datetime.fromisoformat(
                    market["market_event_time"].replace("Z", "+00:00")
                ).timestamp()
            ):
                raise ValueError("FIRST_ENTRY_MARK_CURSOR_CLOCK_MISMATCH")
            if frame["entry"]["decision_outcome"] in ENTRY_OUTCOMES:
                return FirstEntryMarkCycleV2(mark_event, candle_open, None, "ENTRY_ALREADY_DECIDED")
            if mark_event <= last.venue_event_time:
                return FirstEntryMarkCycleV2(mark_event, candle_open, None, "WAITING_FOR_NEW_MARK")

        # In the original Core call this argument feeds capability C1 (the
        # distinct-observation acceptor). Its identity is the venue Mark here.
        # The finalized bar/price series retains its separate input and clock.
        invocation = compose_occupied_lane_mv2_dp_durable_cycle_v1(
            pairs,
            cycle_id_prefix=cycle_id,
            observed_unix=observed_unix,
            mark_px=provenance.mark_px,
            index_px=provenance.index_px,
            bid_px=bid_px,
            ask_px=ask_px,
            volume=volume,
            open_interest=open_interest,
            funding_rate=funding_rate,
            finalized_closes=closes,
            last_finalized_event_ts_unix=candle_open,
            accepted_c1_venue_event_time_unix=mark_event,
            venue_flat=True,
            existing_position_side=ExistingPositionSide.NONE,
            g17_typed_vol_producers={LANE_ID: g17_producer},
            canonical_price_provenance=provenance,
            master_v2_reconciliation_admission=reconciliation,
        )[LANE_ID]
        cycle = invocation.cycle_result
        status = "BLOCKED"
        if cycle.replay_pass == "true":
            status = "ENTRY_DECIDED" if cycle.decision_outcome in ENTRY_OUTCOMES else "EVALUATED"
        return FirstEntryMarkCycleV2(mark_event, candle_open, cycle, status)
