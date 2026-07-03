"""Funding-rate delta momentum single-slot research orchestrator v0."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_funding_rate_delta_momentum_scoring_v0 import (
    SCORE_FORMULA_VERSION,
    FundingDeltaLeg,
    FundingDeltaScoreResultV0,
    compute_instrument_funding_delta_score_v0,
    select_funding_delta_extreme_single_leg_v0,
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
    "CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_SINGLE_SLOT_RESEARCH_ORCHESTRATOR_V0=true"
)
ORCHESTRATOR_VERSION = (
    "cross_sectional_funding_rate_delta_momentum_single_slot_research_orchestrator.v0"
)

FORBIDDEN_INSTRUMENT_TOKENS = frozenset({"btc", "xbt", "bitcoin"})


class FundingDeltaOrchestratorErrorCode(str, Enum):
    BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
    PANEL_VALIDATION_FAILED = "PANEL_VALIDATION_FAILED"
    INSUFFICIENT_ELIGIBLE_MEMBERS = "INSUFFICIENT_ELIGIBLE_MEMBERS"
    MISSING_FUNDING_RATE = "MISSING_FUNDING_RATE"
    INVALID_FUNDING_RATE = "INVALID_FUNDING_RATE"


def _leg_to_slot_side(leg: FundingDeltaLeg) -> SlotSide:
    if leg is FundingDeltaLeg.LONG_MIN_DELTA:
        return SlotSide.LONG
    if leg is FundingDeltaLeg.SHORT_MAX_DELTA:
        return SlotSide.SHORT
    return SlotSide.FLAT


def _funding_rates_from_series(series: InstrumentFundingPanelSeriesV1) -> tuple[float, ...]:
    return tuple(float(bar.funding_rate) for bar in series.bars)


def run_cross_sectional_funding_rate_delta_momentum_orchestrator_v0(
    *,
    binding: Mapping[str, Any],
    funding_panel_series: Sequence[InstrumentFundingPanelSeriesV1],
    eligible_instrument_ids: Sequence[str] | None = None,
) -> OrchestratorRunResultV0:
    lookback_k = int(_extract_numeric_binding(binding, "funding_delta_lookback_k"))
    signal_lag_bars = int(_extract_numeric_binding(binding, "signal_lag_bars"))
    min_eligible = int(_extract_numeric_binding(binding, "min_eligible_members_for_rank"))
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
        raise ValueError(FundingDeltaOrchestratorErrorCode.PANEL_VALIDATION_FAILED.value)

    reference_series = max(series_by_id.values(), key=lambda s: len(s.bars))
    bar_count = len(reference_series.bars)
    rates_by_id = {iid: _funding_rates_from_series(series) for iid, series in series_by_id.items()}

    state = _SlotState()
    epoch_results: list[OrchestratorEpochResultV0] = []

    for epoch_index in range(bar_count):
        timestamp_utc = reference_series.bars[epoch_index].timestamp_utc
        error_codes: list[str] = []
        epoch_scores: list[FundingDeltaScoreResultV0] = []

        for instrument_id, rates in rates_by_id.items():
            series = series_by_id[instrument_id]
            if _is_stale(
                series.bars,
                epoch_index=epoch_index,
                reference_timestamp=timestamp_utc,
                max_bar_staleness_bars=max_staleness,
            ):
                continue
            score_result = compute_instrument_funding_delta_score_v0(
                instrument_id,
                rates,
                funding_delta_lookback_k=lookback_k,
                signal_lag_bars=signal_lag_bars,
                epoch_index=epoch_index,
            )
            if score_result is not None:
                epoch_scores.append(score_result)

        selection_extreme = select_funding_delta_extreme_single_leg_v0(epoch_scores)
        ranked_ids = tuple(
            sorted(
                (item.instrument_id for item in epoch_scores),
                key=lambda iid: (
                    rates_by_id[iid][epoch_index - signal_lag_bars]
                    - rates_by_id[iid][epoch_index - signal_lag_bars - lookback_k]
                    if epoch_index >= signal_lag_bars + lookback_k
                    else float("inf"),
                    iid,
                ),
            )
        )

        if len(epoch_scores) < min_eligible or selection_extreme.leg is FundingDeltaLeg.FLAT:
            target_side = SlotSide.FLAT
            target_instrument_id = None
            top_score = None
            error_codes.append(
                FundingDeltaOrchestratorErrorCode.INSUFFICIENT_ELIGIBLE_MEMBERS.value
            )
        else:
            target_side = _leg_to_slot_side(selection_extreme.leg)
            target_instrument_id = selection_extreme.instrument_id
            top_score = (
                selection_extreme.min_funding_delta
                if selection_extreme.leg is FundingDeltaLeg.LONG_MIN_DELTA
                else selection_extreme.max_funding_delta
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


def default_funding_delta_momentum_operator_binding_v0() -> Mapping[str, Any]:
    from src.research.cross_sectional_funding_rate_delta_momentum_ranking_semantics_binding_v0 import (
        apply_ratified_operator_bindings_v0,
        materialize_funding_rate_delta_momentum_ranking_semantics_binding_v0,
    )

    return apply_ratified_operator_bindings_v0(
        materialize_funding_rate_delta_momentum_ranking_semantics_binding_v0()
    )
