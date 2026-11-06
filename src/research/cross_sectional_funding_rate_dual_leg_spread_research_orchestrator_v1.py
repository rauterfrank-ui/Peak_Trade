"""Funding-rate dual-leg spread research orchestrator v1.

Deterministic simultaneous long-low / short-high funding level spread book with
switch-delay semantics. Material difference vs PR4925 single-slot delta rotation.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_funding_rate_dual_leg_spread_scoring_v1 import (
    SCORE_FORMULA_VERSION,
    DualLegSpreadTarget,
    compute_instrument_funding_level_score_v1,
    select_dual_leg_spread_v1,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    _extract_numeric_binding,
    _is_stale,
)
from src.research.pit_okx_pt1h_panel_funding_dataset_v1 import InstrumentFundingPanelSeriesV1
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    PanelValidationErrorCode,
    validate_panel_series_v1,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_DUAL_LEG_SPREAD_RESEARCH_ORCHESTRATOR_V1=true"
ORCHESTRATOR_VERSION = "cross_sectional_funding_rate_dual_leg_spread_research_orchestrator.v1"

FORBIDDEN_INSTRUMENT_TOKENS = frozenset({"btc", "xbt", "bitcoin"})


class DualLegOrchestratorErrorCode(str, Enum):
    BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
    PANEL_VALIDATION_FAILED = "PANEL_VALIDATION_FAILED"
    INSUFFICIENT_ELIGIBLE_MEMBERS = "INSUFFICIENT_ELIGIBLE_MEMBERS"
    MISSING_FUNDING_RATE = "MISSING_FUNDING_RATE"
    SPREAD_BELOW_THRESHOLD = "SPREAD_BELOW_THRESHOLD"


@dataclass(frozen=True)
class DualLegSelectionEventV1:
    epoch_index: int
    timestamp_utc: str
    ranked_instrument_ids: tuple[str, ...]
    spread_bps: float | None
    long_instrument_id: str | None
    short_instrument_id: str | None
    active: bool
    pending_switch: bool
    eligible_member_count: int


@dataclass(frozen=True)
class DualLegOrchestratorEpochResultV1:
    epoch_index: int
    timestamp_utc: str
    selection: DualLegSelectionEventV1
    error_codes: tuple[str, ...]


@dataclass(frozen=True)
class DualLegOrchestratorRunResultV1:
    orchestrator_version: str
    score_formula_version: str
    epochs: tuple[DualLegOrchestratorEpochResultV1, ...]
    final_long_instrument_id: str | None
    final_short_instrument_id: str | None
    final_active: bool
    authority_effect: str
    runtime_effect: str
    order_effect: str


@dataclass
class _DualLegState:
    current_long: str | None = None
    current_short: str | None = None
    active: bool = False
    pending_target_long: str | None = None
    pending_target_short: str | None = None
    pending_epochs_remaining: int = 0


def _funding_rates_from_series(series: InstrumentFundingPanelSeriesV1) -> tuple[float, ...]:
    return tuple(float(bar.funding_rate) for bar in series.bars)


def _apply_dual_leg_switch_state_machine(
    state: _DualLegState,
    *,
    target_active: bool,
    target_long: str | None,
    target_short: str | None,
    switch_entry_delay_epochs: int,
) -> tuple[bool, str | None, str | None, bool]:
    """Return (active, long_id, short_id, pending_switch)."""
    if not target_active:
        state.current_long = None
        state.current_short = None
        state.active = False
        state.pending_target_long = None
        state.pending_target_short = None
        state.pending_epochs_remaining = 0
        return False, None, None, False

    same_target = (
        target_long == state.current_long and target_short == state.current_short and state.active
    )
    if same_target:
        state.pending_target_long = None
        state.pending_target_short = None
        state.pending_epochs_remaining = 0
        return True, state.current_long, state.current_short, False

    target_changed = (
        target_long != state.current_long or target_short != state.current_short or not state.active
    )
    if target_changed:
        if (
            state.pending_target_long == target_long
            and state.pending_target_short == target_short
            and state.pending_epochs_remaining > 0
        ):
            state.pending_epochs_remaining -= 1
            if state.pending_epochs_remaining <= 0:
                state.current_long = target_long
                state.current_short = target_short
                state.active = True
                state.pending_target_long = None
                state.pending_target_short = None
                return True, target_long, target_short, False
            return False, None, None, True

        state.pending_target_long = target_long
        state.pending_target_short = target_short
        state.pending_epochs_remaining = switch_entry_delay_epochs
        state.current_long = None
        state.current_short = None
        state.active = False
        if switch_entry_delay_epochs <= 0:
            state.current_long = target_long
            state.current_short = target_short
            state.active = True
            state.pending_target_long = None
            state.pending_target_short = None
            return True, target_long, target_short, False
        return False, None, None, True

    return state.active, state.current_long, state.current_short, False


def run_cross_sectional_funding_rate_dual_leg_spread_orchestrator_v1(
    *,
    binding: Mapping[str, Any],
    funding_panel_series: Sequence[InstrumentFundingPanelSeriesV1],
    eligible_instrument_ids: Sequence[str] | None = None,
) -> DualLegOrchestratorRunResultV1:
    signal_lag_bars = int(_extract_numeric_binding(binding, "signal_lag_bars"))
    min_eligible = int(_extract_numeric_binding(binding, "min_eligible_members_for_rank"))
    switch_delay = int(_extract_numeric_binding(binding, "switch_entry_delay_epochs"))
    max_staleness = int(_extract_numeric_binding(binding, "max_bar_staleness_bars"))
    min_spread_bps = float(_extract_numeric_binding(binding, "min_spread_bps_for_entry"))

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
        return DualLegOrchestratorRunResultV1(
            orchestrator_version=ORCHESTRATOR_VERSION,
            score_formula_version=SCORE_FORMULA_VERSION,
            epochs=(),
            final_long_instrument_id=None,
            final_short_instrument_id=None,
            final_active=False,
            authority_effect="NONE",
            runtime_effect="NONE",
            order_effect="NONE",
        )

    series_by_id = {series.instrument_id: series for series in funding_panel_series}
    if eligible_instrument_ids is not None:
        allowed = set(eligible_instrument_ids)
        series_by_id = {iid: series for iid, series in series_by_id.items() if iid in allowed}

    if not series_by_id:
        raise ValueError(DualLegOrchestratorErrorCode.PANEL_VALIDATION_FAILED.value)

    reference_series = max(series_by_id.values(), key=lambda s: len(s.bars))
    bar_count = len(reference_series.bars)
    rates_by_id = {iid: _funding_rates_from_series(series) for iid, series in series_by_id.items()}

    state = _DualLegState()
    epoch_results: list[DualLegOrchestratorEpochResultV1] = []

    for epoch_index in range(bar_count):
        timestamp_utc = reference_series.bars[epoch_index].timestamp_utc
        error_codes: list[str] = []
        epoch_scores = []

        for instrument_id, rates in rates_by_id.items():
            series = series_by_id[instrument_id]
            if _is_stale(
                series.bars,
                epoch_index=epoch_index,
                reference_timestamp=timestamp_utc,
                max_bar_staleness_bars=max_staleness,
            ):
                continue
            score_result = compute_instrument_funding_level_score_v1(
                instrument_id,
                rates,
                signal_lag_bars=signal_lag_bars,
                epoch_index=epoch_index,
            )
            if score_result is not None and score_result.signal_eligible:
                epoch_scores.append(score_result)

        spread_selection = select_dual_leg_spread_v1(
            epoch_scores,
            min_spread_bps_for_entry=min_spread_bps,
        )
        ranked_ids = tuple(
            sorted(
                (item.instrument_id for item in epoch_scores),
                key=lambda iid: (
                    (rates_by_id[iid][epoch_index - signal_lag_bars], iid)
                    if epoch_index >= signal_lag_bars
                    else (float("inf"), iid)
                ),
            )
        )

        if len(epoch_scores) < min_eligible:
            target_active = False
            target_long = None
            target_short = None
            error_codes.append(DualLegOrchestratorErrorCode.INSUFFICIENT_ELIGIBLE_MEMBERS.value)
        elif spread_selection.target is DualLegSpreadTarget.FLAT:
            target_active = False
            target_long = None
            target_short = None
            if spread_selection.spread_bps is not None:
                error_codes.append(DualLegOrchestratorErrorCode.SPREAD_BELOW_THRESHOLD.value)
        else:
            target_active = True
            target_long = spread_selection.long_instrument_id
            target_short = spread_selection.short_instrument_id

        active, long_id, short_id, pending = _apply_dual_leg_switch_state_machine(
            state,
            target_active=target_active,
            target_long=target_long,
            target_short=target_short,
            switch_entry_delay_epochs=switch_delay,
        )

        selection = DualLegSelectionEventV1(
            epoch_index=epoch_index,
            timestamp_utc=timestamp_utc,
            ranked_instrument_ids=ranked_ids,
            spread_bps=spread_selection.spread_bps,
            long_instrument_id=long_id,
            short_instrument_id=short_id,
            active=active,
            pending_switch=pending,
            eligible_member_count=len(epoch_scores),
        )
        epoch_results.append(
            DualLegOrchestratorEpochResultV1(
                epoch_index=epoch_index,
                timestamp_utc=timestamp_utc,
                selection=selection,
                error_codes=tuple(sorted(set(error_codes))),
            )
        )

    return DualLegOrchestratorRunResultV1(
        orchestrator_version=ORCHESTRATOR_VERSION,
        score_formula_version=SCORE_FORMULA_VERSION,
        epochs=tuple(epoch_results),
        final_long_instrument_id=state.current_long,
        final_short_instrument_id=state.current_short,
        final_active=state.active,
        authority_effect="NONE",
        runtime_effect="NONE",
        order_effect="NONE",
    )


def default_dual_leg_spread_operator_binding_v1() -> Mapping[str, Any]:
    from src.research.cross_sectional_funding_rate_dual_leg_spread_ranking_semantics_binding_v1 import (
        apply_ratified_operator_bindings_v1,
        materialize_funding_rate_dual_leg_spread_ranking_semantics_binding_v1,
    )

    return apply_ratified_operator_bindings_v1(
        materialize_funding_rate_dual_leg_spread_ranking_semantics_binding_v1()
    )
