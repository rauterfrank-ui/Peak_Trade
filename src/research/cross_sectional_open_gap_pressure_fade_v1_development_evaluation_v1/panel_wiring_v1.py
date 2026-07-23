"""Panel wiring: bind open-gap score/selection into canonical single-slot backtest owner.

Does not invent metrics. Maps rank intents into OrchestratorRunResultV0 so
``run_single_slot_panel_backtest_v0`` remains the sole trade/PnL metrics path.
This module is infrastructure wiring only.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from src.research.cross_sectional_open_gap_pressure_fade_v1_development_evaluation_v1.constants_v1 import (
    DEFAULT_LOOKBACK_N,
    DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK,
    DEFAULT_REBALANCE_INTERVAL_BARS,
    DEFAULT_SIGNAL_LAG_BARS,
    SCORE_FORMULA_VERSION,
)
from src.research.cross_sectional_open_gap_pressure_fade_v1_selection_v1 import (
    RankIntentSideV1,
    select_single_top1_rank_intent_v1,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    ORCHESTRATOR_VERSION,
    OrchestratorEpochResultV0,
    OrchestratorRunResultV0,
    SingleSlotSelectionEventV0,
    SlotSide,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1


def _intent_side_to_slot(side: RankIntentSideV1) -> SlotSide:
    if side == RankIntentSideV1.LONG_TOP1:
        return SlotSide.LONG
    if side == RankIntentSideV1.SHORT_TOP1:
        return SlotSide.SHORT
    return SlotSide.FLAT


def _open_close_by_instrument(
    panel_series: Sequence[InstrumentPanelSeriesV1], *, bar_count: int
) -> dict[str, dict[str, tuple[float, ...]]]:
    out: dict[str, dict[str, tuple[float, ...]]] = {}
    for series in panel_series:
        opens: list[float] = []
        closes: list[float] = []
        for bar in series.bars[:bar_count]:
            try:
                opens.append(float(bar.open))
            except (TypeError, ValueError):
                opens.append(float("nan"))
            try:
                closes.append(float(bar.close))
            except (TypeError, ValueError):
                closes.append(float("nan"))
        out[series.instrument_id] = {
            "open": tuple(opens),
            "close": tuple(closes),
        }
    return out


def wire_selection_intents_to_orchestrator_result_v1(
    panel_series: Sequence[InstrumentPanelSeriesV1],
    *,
    lookback_n: int = DEFAULT_LOOKBACK_N,
    signal_lag_bars: int = DEFAULT_SIGNAL_LAG_BARS,
    rebalance_interval_bars: int = DEFAULT_REBALANCE_INTERVAL_BARS,
    min_eligible_members_for_rank: int = DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK,
) -> OrchestratorRunResultV0:
    """Deterministic wiring from CS open-gap fade v1 selection into orchestrator epochs."""
    if not panel_series:
        return OrchestratorRunResultV0(
            orchestrator_version=ORCHESTRATOR_VERSION,
            score_formula_version=SCORE_FORMULA_VERSION,
            epochs=(),
            final_slot_side=SlotSide.FLAT,
            final_instrument_id=None,
            authority_effect="NONE",
            runtime_effect="NONE",
            order_effect="NONE",
        )

    series_by_id = {s.instrument_id: s for s in panel_series}
    reference = max(series_by_id.values(), key=lambda s: len(s.bars))
    bar_count = len(reference.bars)
    panel_by_id = _open_close_by_instrument(panel_series, bar_count=bar_count)

    epochs: list[OrchestratorEpochResultV0] = []
    prior = None
    final_side = SlotSide.FLAT
    final_instrument: str | None = None
    for epoch_index in range(bar_count):
        ts = reference.bars[epoch_index].timestamp_utc
        intent = select_single_top1_rank_intent_v1(
            panel_by_id,
            epoch_index=epoch_index,
            lookback_n=lookback_n,
            signal_lag_bars=signal_lag_bars,
            min_eligible_members_for_rank=min_eligible_members_for_rank,
            rebalance_interval_bars=rebalance_interval_bars,
            prior_intent=prior,
        )
        prior = intent
        slot_side = _intent_side_to_slot(intent.intent_side)
        selected = intent.selected_instrument_id
        final_side = slot_side
        final_instrument = selected
        selection = SingleSlotSelectionEventV0(
            epoch_index=epoch_index,
            timestamp_utc=ts,
            ranked_instrument_ids=intent.ranked_instrument_ids,
            top_score=intent.top_score,
            selected_instrument_id=selected,
            slot_side=slot_side,
            pending_switch=False,
            eligible_member_count=intent.eligible_member_count,
        )
        epochs.append(
            OrchestratorEpochResultV0(
                epoch_index=epoch_index,
                timestamp_utc=ts,
                scores=(),
                selection=selection,
                error_codes=("INSUFFICIENT_ELIGIBLE_MEMBERS",)
                if intent.insufficient_universe
                else (),
            )
        )

    return OrchestratorRunResultV0(
        orchestrator_version=ORCHESTRATOR_VERSION,
        score_formula_version=SCORE_FORMULA_VERSION,
        epochs=tuple(epochs),
        final_slot_side=final_side,
        final_instrument_id=final_instrument,
        authority_effect="NONE",
        runtime_effect="NONE",
        order_effect="NONE",
    )


def cost_binding_for_canonical_backtest(
    cost_execution_binding: Mapping[str, object],
) -> Mapping[str, object]:
    """Pass-through helper documenting reuse of canonical backtest cost binding shape."""
    return cost_execution_binding
