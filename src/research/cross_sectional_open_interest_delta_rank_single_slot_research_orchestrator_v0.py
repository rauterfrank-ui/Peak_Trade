"""Open-interest delta rank single-slot research orchestrator v0."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_open_interest_delta_rank_scoring_v0 import (
    SCORE_FORMULA_VERSION,
    OpenInterestDeltaLeg,
    OpenInterestDeltaScoreResultV0,
    compute_instrument_open_interest_delta_score_v0,
    select_open_interest_delta_extreme_single_leg_v0,
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
)
from src.research.pit_okx_pt1h_panel_open_interest_dataset_v1 import (
    InstrumentOpenInterestPanelSeriesV1,
    validate_open_interest_panel_series_v1,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    PanelValidationErrorCode,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_SINGLE_SLOT_RESEARCH_ORCHESTRATOR_V0=true"
)
ORCHESTRATOR_VERSION = (
    "cross_sectional_open_interest_delta_rank_single_slot_research_orchestrator.v0"
)

FORBIDDEN_INSTRUMENT_TOKENS = frozenset({"btc", "xbt", "bitcoin"})


class OpenInterestDeltaOrchestratorErrorCode(str, Enum):
    BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
    PANEL_VALIDATION_FAILED = "PANEL_VALIDATION_FAILED"
    INSUFFICIENT_ELIGIBLE_MEMBERS = "INSUFFICIENT_ELIGIBLE_MEMBERS"
    MISSING_OPEN_INTEREST = "MISSING_OPEN_INTEREST"
    INVALID_OPEN_INTEREST = "INVALID_OPEN_INTEREST"


def _leg_to_slot_side(leg: OpenInterestDeltaLeg) -> SlotSide:
    if leg is OpenInterestDeltaLeg.LONG_MIN_DELTA:
        return SlotSide.LONG
    if leg is OpenInterestDeltaLeg.SHORT_MAX_DELTA:
        return SlotSide.SHORT
    return SlotSide.FLAT


def _open_interest_values_from_series(
    series: InstrumentOpenInterestPanelSeriesV1,
) -> tuple[float | str | None, ...]:
    return tuple(bar.open_interest for bar in series.bars)


def run_cross_sectional_open_interest_delta_rank_orchestrator_v0(
    *,
    binding: Mapping[str, Any],
    open_interest_panel_series: Sequence[InstrumentOpenInterestPanelSeriesV1],
    eligible_instrument_ids: Sequence[str] | None = None,
) -> OrchestratorRunResultV0:
    lookback_k = int(_extract_numeric_binding(binding, "rank_lookback_k"))
    signal_lag_bars = int(_extract_numeric_binding(binding, "signal_lag_bars"))
    min_eligible = int(_extract_numeric_binding(binding, "min_eligible_members_for_rank"))
    switch_delay = int(_extract_numeric_binding(binding, "switch_entry_delay_epochs"))
    max_staleness = int(_extract_numeric_binding(binding, "max_bar_staleness_bars"))

    if len(open_interest_panel_series) < min_eligible:
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

    for series in open_interest_panel_series:
        lowered = series.instrument_id.lower()
        if any(token in lowered for token in FORBIDDEN_INSTRUMENT_TOKENS):
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

    reference_calendar = tuple(bar.timestamp_utc for bar in open_interest_panel_series[0].bars)
    for series in open_interest_panel_series:
        panel_validation = validate_open_interest_panel_series_v1(
            series,
            expected_timestamps=reference_calendar,
        )
        if (
            PanelValidationErrorCode.PANEL_ALIGNMENT_MISMATCH.value in panel_validation.error_codes
            or not panel_validation.valid
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

    series_by_id = {series.instrument_id: series for series in open_interest_panel_series}
    if eligible_instrument_ids is not None:
        allowed = set(eligible_instrument_ids)
        series_by_id = {iid: series for iid, series in series_by_id.items() if iid in allowed}

    if not series_by_id:
        raise ValueError(OpenInterestDeltaOrchestratorErrorCode.PANEL_VALIDATION_FAILED.value)

    reference_series = max(series_by_id.values(), key=lambda s: len(s.bars))
    bar_count = len(reference_series.bars)
    oi_by_id = {
        iid: _open_interest_values_from_series(series) for iid, series in series_by_id.items()
    }

    state = _SlotState()
    epoch_results: list[OrchestratorEpochResultV0] = []

    for epoch_index in range(bar_count):
        timestamp_utc = reference_series.bars[epoch_index].timestamp_utc
        error_codes: list[str] = []
        epoch_scores: list[OpenInterestDeltaScoreResultV0] = []

        for instrument_id, oi_values in oi_by_id.items():
            series = series_by_id[instrument_id]
            if _is_stale(
                series.bars,
                epoch_index=epoch_index,
                reference_timestamp=timestamp_utc,
                max_bar_staleness_bars=max_staleness,
            ):
                continue
            score_result = compute_instrument_open_interest_delta_score_v0(
                instrument_id,
                oi_values,
                open_interest_delta_lookback_k=lookback_k,
                signal_lag_bars=signal_lag_bars,
                epoch_index=epoch_index,
            )
            if score_result is not None and score_result.signal_eligible:
                epoch_scores.append(score_result)
            elif score_result is not None:
                error_codes.append(
                    OpenInterestDeltaOrchestratorErrorCode.MISSING_OPEN_INTEREST.value
                )

        selection_extreme = select_open_interest_delta_extreme_single_leg_v0(epoch_scores)
        ranked_ids = tuple(sorted(item.instrument_id for item in epoch_scores))

        if len(epoch_scores) < min_eligible or selection_extreme.leg is OpenInterestDeltaLeg.FLAT:
            target_side = SlotSide.FLAT
            target_instrument_id = None
            top_score = None
            error_codes.append(
                OpenInterestDeltaOrchestratorErrorCode.INSUFFICIENT_ELIGIBLE_MEMBERS.value
            )
        else:
            target_side = _leg_to_slot_side(selection_extreme.leg)
            target_instrument_id = selection_extreme.instrument_id
            top_score = (
                selection_extreme.min_open_interest_delta
                if selection_extreme.leg is OpenInterestDeltaLeg.LONG_MIN_DELTA
                else selection_extreme.max_open_interest_delta
            )

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
            eligible_member_count=len(epoch_scores),
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


def default_open_interest_delta_rank_operator_binding_v0() -> Mapping[str, Any]:
    def _bound(value: int) -> dict[str, Any]:
        return {"status": "BOUND", "value": value}

    return {
        "binding_version": "v0",
        "numeric_bindings": {
            "rank_lookback_k": _bound(4),
            "signal_lag_bars": _bound(1),
            "min_eligible_members_for_rank": _bound(5),
            "switch_entry_delay_epochs": _bound(1),
            "max_bar_staleness_bars": _bound(1),
            "rebalance_interval_bars": _bound(1),
        },
    }
