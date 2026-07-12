"""Open-interest z-score reversion single-slot research orchestrator v0."""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_open_interest_zscore_reversion_scoring_v0 import (
    SCORE_FORMULA_VERSION,
    OpenInterestZscoreLeg,
    OpenInterestZscoreScoreResultV0,
    compute_instrument_open_interest_zscore_score_v0,
    compute_panel_oi_dispersion_snapshot_v0,
    select_open_interest_zscore_extreme_single_leg_v0,
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
    "CROSS_SECTIONAL_OPEN_INTEREST_ZSCORE_REVERSION_SINGLE_SLOT_RESEARCH_ORCHESTRATOR_V0=true"
)
ORCHESTRATOR_VERSION = (
    "cross_sectional_open_interest_zscore_reversion_single_slot_research_orchestrator.v0"
)

FORBIDDEN_INSTRUMENT_TOKENS = frozenset({"btc", "xbt", "bitcoin"})


class OpenInterestZscoreOrchestratorErrorCode(str, Enum):
    BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
    PANEL_VALIDATION_FAILED = "PANEL_VALIDATION_FAILED"
    INSUFFICIENT_ELIGIBLE_MEMBERS = "INSUFFICIENT_ELIGIBLE_MEMBERS"
    INSUFFICIENT_PANEL_DISPERSION = "INSUFFICIENT_PANEL_DISPERSION"
    MISSING_OPEN_INTEREST = "MISSING_OPEN_INTEREST"
    INVALID_OPEN_INTEREST = "INVALID_OPEN_INTEREST"
    RANK_LOOKBACK_FORBIDDEN = "RANK_LOOKBACK_FORBIDDEN"
    DELTA_LOOKBACK_FORBIDDEN = "DELTA_LOOKBACK_FORBIDDEN"


def _leg_to_slot_side(leg: OpenInterestZscoreLeg) -> SlotSide:
    if leg is OpenInterestZscoreLeg.LONG_MIN_ZSCORE:
        return SlotSide.LONG
    if leg is OpenInterestZscoreLeg.SHORT_MAX_ZSCORE:
        return SlotSide.SHORT
    return SlotSide.FLAT


def _open_interest_values_from_series(
    series: InstrumentOpenInterestPanelSeriesV1,
) -> tuple[float | str | None, ...]:
    return tuple(bar.open_interest for bar in series.bars)


def _panel_oi_level_snapshot(
    oi_by_id: Mapping[str, tuple[float | str | None, ...]],
    *,
    bar_index: int,
) -> tuple[tuple[str, float | str | None], ...]:
    snapshot: list[tuple[str, float | str | None]] = []
    for instrument_id in sorted(oi_by_id):
        values = oi_by_id[instrument_id]
        if bar_index < 0 or bar_index >= len(values):
            snapshot.append((instrument_id, None))
            continue
        snapshot.append((instrument_id, values[bar_index]))
    return tuple(snapshot)


def run_cross_sectional_open_interest_zscore_reversion_orchestrator_v0(
    *,
    binding: Mapping[str, Any],
    open_interest_panel_series: Sequence[InstrumentOpenInterestPanelSeriesV1],
    eligible_instrument_ids: Sequence[str] | None = None,
) -> OrchestratorRunResultV0:
    if "rank_lookback_k" in binding.get("numeric_bindings", {}):
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

    signal_lag_bars = int(_extract_numeric_binding(binding, "signal_lag_bars"))
    min_eligible = int(_extract_numeric_binding(binding, "min_eligible_members_for_rank"))
    min_abs_zscore = float(_extract_numeric_binding(binding, "min_abs_zscore_for_entry"))
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
        raise ValueError(OpenInterestZscoreOrchestratorErrorCode.PANEL_VALIDATION_FAILED.value)

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
        epoch_scores: list[OpenInterestZscoreScoreResultV0] = []

        lag_idx = epoch_index - signal_lag_bars
        panel_levels_lag = _panel_oi_level_snapshot(oi_by_id, bar_index=lag_idx)
        dispersion_snapshot = compute_panel_oi_dispersion_snapshot_v0(panel_levels_lag)
        dispersion_gate_passes = (
            dispersion_snapshot is not None and dispersion_snapshot.dispersion_gate_passes
        )
        if dispersion_snapshot is not None and not dispersion_gate_passes:
            error_codes.append(
                OpenInterestZscoreOrchestratorErrorCode.INSUFFICIENT_PANEL_DISPERSION.value
            )

        for instrument_id, series in series_by_id.items():
            if _is_stale(
                series.bars,
                epoch_index=epoch_index,
                reference_timestamp=timestamp_utc,
                max_bar_staleness_bars=max_staleness,
            ):
                continue
            score_result = compute_instrument_open_interest_zscore_score_v0(
                instrument_id,
                panel_levels_lag,
                signal_lag_bars=signal_lag_bars,
                epoch_index=epoch_index,
            )
            if score_result is not None and score_result.signal_eligible:
                epoch_scores.append(score_result)
            elif score_result is not None:
                error_codes.append(
                    OpenInterestZscoreOrchestratorErrorCode.MISSING_OPEN_INTEREST.value
                )

        selection_extreme = select_open_interest_zscore_extreme_single_leg_v0(
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

        if len(epoch_scores) < min_eligible or selection_extreme.leg is OpenInterestZscoreLeg.FLAT:
            target_side = SlotSide.FLAT
            target_instrument_id = None
            top_score = None
            error_codes.append(
                OpenInterestZscoreOrchestratorErrorCode.INSUFFICIENT_ELIGIBLE_MEMBERS.value
            )
        else:
            target_side = _leg_to_slot_side(selection_extreme.leg)
            target_instrument_id = selection_extreme.instrument_id
            top_score = (
                selection_extreme.min_zscore
                if selection_extreme.leg is OpenInterestZscoreLeg.LONG_MIN_ZSCORE
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


def default_open_interest_zscore_reversion_operator_binding_v0() -> Mapping[str, Any]:
    def _bound(value: int | float) -> dict[str, Any]:
        return {"status": "BOUND", "value": value}

    return {
        "binding_version": "v0",
        "numeric_bindings": {
            "signal_lag_bars": _bound(1),
            "min_eligible_members_for_rank": _bound(5),
            "min_abs_zscore_for_entry": _bound(1.0),
            "switch_entry_delay_epochs": _bound(1),
            "max_bar_staleness_bars": _bound(1),
            "rebalance_interval_bars": _bound(1),
        },
    }
