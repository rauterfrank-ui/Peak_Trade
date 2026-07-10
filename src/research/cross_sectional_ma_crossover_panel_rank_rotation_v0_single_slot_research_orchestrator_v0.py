"""MA-crossover panel rank-rotation single-slot research orchestrator v0.

Deterministic top-1 MA-crossover score ranking with flat-delay rotation semantics.
Reuses rotation state machine from cross_sectional_single_slot_research_orchestrator_v0.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_ranking_semantics_binding_v0 import (
    apply_ratified_operator_bindings_v0,
    materialize_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_score_v0 import (
    SCORE_FORMULA_VERSION,
    MaCrossoverPanelScoreResultV0,
    compute_instrument_score_v0,
    rank_scores_deterministic_v0,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    OrchestratorEpochResultV0,
    OrchestratorRunResultV0,
    SingleSlotSelectionEventV0,
    SlotSide,
    _SlotState,
    _apply_rotation_state_machine,
    _extract_numeric_binding,
    _is_stale,
    _parse_close_series,
    _resolve_target_side,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    InstrumentPanelSeriesV1,
    PanelValidationErrorCode,
    validate_panel_series_v1,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_SINGLE_SLOT_RESEARCH_ORCHESTRATOR_V0=true"
)
ORCHESTRATOR_VERSION = (
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_single_slot_research_orchestrator.v0"
)

FORBIDDEN_INSTRUMENT_TOKENS = frozenset({"btc", "xbt", "bitcoin"})


def run_ma_crossover_panel_rank_rotation_orchestrator_v0(
    *,
    binding: Mapping[str, Any],
    panel_series: Sequence[InstrumentPanelSeriesV1],
    eligible_instrument_ids: Sequence[str] | None = None,
) -> OrchestratorRunResultV0:
    """Run deterministic MA-crossover single-slot panel orchestration."""
    fast_window = int(_extract_numeric_binding(binding, "fast_window"))
    slow_window = int(_extract_numeric_binding(binding, "slow_window"))
    signal_lag_bars = int(_extract_numeric_binding(binding, "signal_lag_bars"))
    min_eligible = int(_extract_numeric_binding(binding, "min_eligible_members_for_rank"))
    switch_delay = int(_extract_numeric_binding(binding, "switch_entry_delay_epochs"))
    max_staleness = int(_extract_numeric_binding(binding, "max_bar_staleness_bars"))

    panel_validation = validate_panel_series_v1(
        panel_series,
        min_instruments=min_eligible,
        forbidden_instrument_substrings=FORBIDDEN_INSTRUMENT_TOKENS,
    )
    if (
        PanelValidationErrorCode.BITCOIN_INSTRUMENT_PRESENT.value in panel_validation.error_codes
        or PanelValidationErrorCode.INSUFFICIENT_INSTRUMENTS.value in panel_validation.error_codes
        or panel_validation.panel_alignment_check == "FAIL"
    ):
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

    series_by_id = {series.instrument_id: series for series in panel_series}
    if eligible_instrument_ids is not None:
        allowed = set(eligible_instrument_ids)
        series_by_id = {iid: series for iid, series in series_by_id.items() if iid in allowed}

    if not series_by_id:
        raise ValueError("UNKNOWN_INSTRUMENT")

    reference_series = max(series_by_id.values(), key=lambda s: len(s.bars))
    bar_count = len(reference_series.bars)
    closes_by_id = {iid: _parse_close_series(series.bars) for iid, series in series_by_id.items()}

    state = _SlotState()
    epoch_results: list[OrchestratorEpochResultV0] = []

    for epoch_index in range(bar_count):
        timestamp_utc = reference_series.bars[epoch_index].timestamp_utc
        error_codes: list[str] = []
        epoch_scores: list[MaCrossoverPanelScoreResultV0] = []

        for instrument_id, closes in closes_by_id.items():
            series = series_by_id[instrument_id]
            if _is_stale(
                series.bars,
                epoch_index=epoch_index,
                reference_timestamp=timestamp_utc,
                max_bar_staleness_bars=max_staleness,
            ):
                error_codes.append("STALE_BAR_EXCLUDED")
                continue
            score_result = compute_instrument_score_v0(
                instrument_id,
                closes,
                fast_window=fast_window,
                slow_window=slow_window,
                signal_lag_bars=signal_lag_bars,
                epoch_index=epoch_index,
            )
            if score_result is not None:
                epoch_scores.append(score_result)

        ranked = rank_scores_deterministic_v0(epoch_scores)
        ranked_ids = tuple(item.instrument_id for item in ranked)

        if len(ranked) < min_eligible:
            target_side = SlotSide.FLAT
            target_instrument_id = None
            top_score = None
            error_codes.append("INSUFFICIENT_ELIGIBLE_MEMBERS")
        else:
            top = ranked[0]
            top_score = top.score
            if not math.isfinite(top_score):
                target_side = SlotSide.FLAT
                target_instrument_id = None
            else:
                target_side = _resolve_target_side(top_score)
                target_instrument_id = top.instrument_id if target_side != SlotSide.FLAT else None

        slot_side, selected_id, pending = _apply_rotation_state_machine(
            state,
            target_side=target_side,
            target_instrument_id=target_instrument_id,
            switch_entry_delay_epochs=switch_delay,
        )

        selection = SingleSlotSelectionEventV0(
            epoch_index=epoch_index,
            timestamp_utc=timestamp_utc,
            ranked_instrument_ids=ranked_ids,
            top_score=top_score,
            selected_instrument_id=selected_id,
            slot_side=slot_side,
            pending_switch=pending,
            eligible_member_count=len(ranked),
        )
        epoch_results.append(
            OrchestratorEpochResultV0(
                epoch_index=epoch_index,
                timestamp_utc=timestamp_utc,
                scores=tuple(),
                selection=selection,
                error_codes=tuple(sorted(set(error_codes))),
            )
        )

    return OrchestratorRunResultV0(
        orchestrator_version=ORCHESTRATOR_VERSION,
        score_formula_version=SCORE_FORMULA_VERSION,
        epochs=tuple(epoch_results),
        final_slot_side=state.current_side,
        final_instrument_id=state.current_instrument_id,
        authority_effect="NONE",
        runtime_effect="NONE",
        order_effect="NONE",
    )


def default_ma_crossover_operator_binding_v0() -> Mapping[str, Any]:
    return apply_ratified_operator_bindings_v0(
        materialize_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0()
    )
