"""Funding-rate dispersion z-score reversion single-slot research orchestrator v0."""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_funding_rate_dispersion_zscore_reversion_scoring_v0 import (
    SCORE_FORMULA_VERSION,
    FundingZscoreLeg,
    FundingZscoreScoreResultV0,
    compute_instrument_funding_zscore_score_v0,
    compute_panel_dispersion_snapshot_v0,
    select_funding_zscore_extreme_single_leg_v0,
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
from src.research.pit_okx_pt1h_panel_funding_dataset_v1 import InstrumentFundingPanelSeriesV1
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    PanelValidationErrorCode,
    validate_panel_series_v1,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUNDING_RATE_DISPERSION_ZSCORE_REVERSION_"
    "SINGLE_SLOT_RESEARCH_ORCHESTRATOR_V0=true"
)
ORCHESTRATOR_VERSION = (
    "cross_sectional_funding_rate_dispersion_zscore_reversion_single_slot_research_orchestrator.v0"
)

FORBIDDEN_INSTRUMENT_TOKENS = frozenset({"btc", "xbt", "bitcoin"})


class FundingZscoreOrchestratorErrorCode(str, Enum):
    BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
    PANEL_VALIDATION_FAILED = "PANEL_VALIDATION_FAILED"
    INSUFFICIENT_ELIGIBLE_MEMBERS = "INSUFFICIENT_ELIGIBLE_MEMBERS"
    INSUFFICIENT_PANEL_DISPERSION = "INSUFFICIENT_PANEL_DISPERSION"
    MISSING_FUNDING_RATE = "MISSING_FUNDING_RATE"
    INVALID_FUNDING_RATE = "INVALID_FUNDING_RATE"


def _leg_to_slot_side(leg: FundingZscoreLeg) -> SlotSide:
    if leg is FundingZscoreLeg.LONG_MIN_ZSCORE:
        return SlotSide.LONG
    if leg is FundingZscoreLeg.SHORT_MAX_ZSCORE:
        return SlotSide.SHORT
    return SlotSide.FLAT


def _funding_rates_from_series(series: InstrumentFundingPanelSeriesV1) -> tuple[float, ...]:
    return tuple(float(bar.funding_rate) for bar in series.bars)


def _panel_rate_snapshot(
    rates_by_id: Mapping[str, tuple[float, ...]],
    *,
    bar_index: int,
) -> tuple[tuple[str, float | None], ...]:
    snapshot: list[tuple[str, float | None]] = []
    for instrument_id, rates in sorted(rates_by_id.items()):
        if bar_index < 0 or bar_index >= len(rates):
            snapshot.append((instrument_id, None))
            continue
        rate = rates[bar_index]
        snapshot.append((instrument_id, rate))
    return tuple(snapshot)


def run_cross_sectional_funding_rate_dispersion_zscore_reversion_orchestrator_v0(
    *,
    binding: Mapping[str, Any],
    funding_panel_series: Sequence[InstrumentFundingPanelSeriesV1],
    eligible_instrument_ids: Sequence[str] | None = None,
) -> OrchestratorRunResultV0:
    signal_lag_bars = int(_extract_numeric_binding(binding, "signal_lag_bars"))
    min_eligible = int(_extract_numeric_binding(binding, "min_eligible_members"))
    min_panel_dispersion = float(_extract_numeric_binding(binding, "min_panel_funding_dispersion"))
    min_abs_zscore = float(_extract_numeric_binding(binding, "min_abs_zscore_for_entry"))
    switch_delay = int(_extract_numeric_binding(binding, "switch_entry_delay_epochs"))
    max_staleness = int(_extract_numeric_binding(binding, "max_bar_staleness_bars"))

    ohlcv_series = [
        type(
            "OhlcvProxy",
            (),
            {
                "instrument_id": item.instrument_id,
                "native_instrument_id": item.native_instrument_id,
                "bars": item.bars,
                "series_digest": item.series_digest,
            },
        )()
        for item in funding_panel_series
    ]
    panel_validation = validate_panel_series_v1(
        ohlcv_series,
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

    series_by_id = {series.instrument_id: series for series in funding_panel_series}
    if eligible_instrument_ids is not None:
        allowed = set(eligible_instrument_ids)
        series_by_id = {iid: series for iid, series in series_by_id.items() if iid in allowed}

    if not series_by_id:
        raise ValueError(FundingZscoreOrchestratorErrorCode.PANEL_VALIDATION_FAILED.value)

    reference_series = max(series_by_id.values(), key=lambda s: len(s.bars))
    bar_count = len(reference_series.bars)
    rates_by_id = {iid: _funding_rates_from_series(series) for iid, series in series_by_id.items()}

    state = _SlotState()
    epoch_results: list[OrchestratorEpochResultV0] = []

    for epoch_index in range(bar_count):
        timestamp_utc = reference_series.bars[epoch_index].timestamp_utc
        error_codes: list[str] = []
        epoch_scores: list[FundingZscoreScoreResultV0] = []

        lag_idx = epoch_index - signal_lag_bars
        panel_rates_lag = _panel_rate_snapshot(rates_by_id, bar_index=lag_idx)
        dispersion_snapshot = compute_panel_dispersion_snapshot_v0(
            panel_rates_lag,
            min_panel_funding_dispersion=min_panel_dispersion,
        )
        dispersion_gate_passes = (
            dispersion_snapshot is not None and dispersion_snapshot.dispersion_gate_passes
        )
        if dispersion_snapshot is not None and not dispersion_gate_passes:
            error_codes.append(
                FundingZscoreOrchestratorErrorCode.INSUFFICIENT_PANEL_DISPERSION.value
            )

        for instrument_id, series in series_by_id.items():
            if _is_stale(
                series.bars,
                epoch_index=epoch_index,
                reference_timestamp=timestamp_utc,
                max_bar_staleness_bars=max_staleness,
            ):
                continue
            score_result = compute_instrument_funding_zscore_score_v0(
                instrument_id,
                panel_rates_lag,
                signal_lag_bars=signal_lag_bars,
                min_panel_funding_dispersion=min_panel_dispersion,
                epoch_index=epoch_index,
            )
            if score_result is not None and score_result.signal_eligible:
                epoch_scores.append(score_result)
            elif score_result is not None:
                error_codes.append(FundingZscoreOrchestratorErrorCode.MISSING_FUNDING_RATE.value)

        selection_extreme = select_funding_zscore_extreme_single_leg_v0(
            epoch_scores,
            min_abs_zscore_for_entry=min_abs_zscore,
            panel_dispersion_gate_passes=dispersion_gate_passes,
        )
        ranked_ids = tuple(
            sorted(
                (item.instrument_id for item in epoch_scores),
                key=lambda iid: (
                    abs(
                        next(score.z_score for score in epoch_scores if score.instrument_id == iid)
                    ),
                    iid,
                ),
            )
        )

        if len(epoch_scores) < min_eligible or selection_extreme.leg is FundingZscoreLeg.FLAT:
            target_side = SlotSide.FLAT
            target_instrument_id = None
            top_score = None
            error_codes.append(
                FundingZscoreOrchestratorErrorCode.INSUFFICIENT_ELIGIBLE_MEMBERS.value
            )
        else:
            target_side = _leg_to_slot_side(selection_extreme.leg)
            target_instrument_id = selection_extreme.instrument_id
            top_score = (
                selection_extreme.min_zscore
                if selection_extreme.leg is FundingZscoreLeg.LONG_MIN_ZSCORE
                else selection_extreme.max_zscore
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


def default_funding_dispersion_zscore_reversion_operator_binding_v0() -> Mapping[str, Any]:
    from src.research.cross_sectional_funding_rate_dispersion_zscore_reversion_ranking_semantics_binding_v0 import (
        apply_ratified_operator_bindings_v0,
        materialize_funding_rate_dispersion_zscore_reversion_ranking_semantics_binding_v0,
    )

    return apply_ratified_operator_bindings_v0(
        materialize_funding_rate_dispersion_zscore_reversion_ranking_semantics_binding_v0()
    )
