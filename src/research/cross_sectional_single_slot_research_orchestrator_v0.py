"""Cross-sectional single-slot research orchestrator v0.

Loads versioned bindings, validates PIT panel data, computes deterministic scores,
produces panel rankings and single-slot rotation events with flat-delay semantics.
Outputs canonical research inputs for existing backtest/robustness owners.

Research-only; no economic evaluation, runtime, orders, credentials, or network.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_ranking_semantics_binding_v0 import (
    RATIFIED_OPERATOR_BINDING_VALUES,
)
from src.research.cross_sectional_relative_strength_v0_score_v0 import (
    SCORE_FORMULA_VERSION,
    CrossSectionalScoreResultV0,
    compute_instrument_score_v0,
    rank_scores_deterministic_v0,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    InstrumentPanelSeriesV1,
    PanelBarV1,
    PanelValidationErrorCode,
    validate_panel_series_v1,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_SINGLE_SLOT_RESEARCH_ORCHESTRATOR_V0=true"
ORCHESTRATOR_VERSION = "cross_sectional_single_slot_research_orchestrator.v0"

FORBIDDEN_INSTRUMENT_TOKENS = frozenset({"btc", "xbt", "bitcoin"})


class SlotSide(str, Enum):
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"


class OrchestratorErrorCode(str, Enum):
    BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
    PANEL_VALIDATION_FAILED = "PANEL_VALIDATION_FAILED"
    INSUFFICIENT_ELIGIBLE_MEMBERS = "INSUFFICIENT_ELIGIBLE_MEMBERS"
    BITCOIN_INSTRUMENT_PRESENT = "BITCOIN_INSTRUMENT_PRESENT"
    STALE_BAR_EXCLUDED = "STALE_BAR_EXCLUDED"
    MISSING_BINDING = "MISSING_BINDING"
    UNKNOWN_INSTRUMENT = "UNKNOWN_INSTRUMENT"


@dataclass(frozen=True)
class SingleSlotSelectionEventV0:
    epoch_index: int
    timestamp_utc: str
    ranked_instrument_ids: tuple[str, ...]
    top_score: float | None
    selected_instrument_id: str | None
    slot_side: SlotSide
    pending_switch: bool
    eligible_member_count: int


@dataclass(frozen=True)
class OrchestratorEpochResultV0:
    epoch_index: int
    timestamp_utc: str
    scores: tuple[CrossSectionalScoreResultV0, ...]
    selection: SingleSlotSelectionEventV0
    error_codes: tuple[str, ...]


@dataclass(frozen=True)
class OrchestratorRunResultV0:
    orchestrator_version: str
    score_formula_version: str
    epochs: tuple[OrchestratorEpochResultV0, ...]
    final_slot_side: SlotSide
    final_instrument_id: str | None
    authority_effect: str
    runtime_effect: str
    order_effect: str


def _parse_close_series(bars: Sequence[PanelBarV1]) -> tuple[float, ...]:
    result: list[float] = []
    for bar in bars:
        try:
            result.append(float(bar.close))
        except (TypeError, ValueError):
            result.append(float("nan"))
    return tuple(result)


def _extract_numeric_binding(
    binding: Mapping[str, Any],
    key: str,
    *,
    default: int | float | str | None = None,
) -> int | float | str:
    numeric = binding.get("numeric_bindings", {})
    if not isinstance(numeric, Mapping):
        raise ValueError(OrchestratorErrorCode.MISSING_BINDING.value)
    field = numeric.get(key, {})
    if not isinstance(field, Mapping):
        raise ValueError(OrchestratorErrorCode.MISSING_BINDING.value)
    if field.get("status") != "BOUND":
        if default is not None:
            return default
        raise ValueError(OrchestratorErrorCode.BINDING_INCOMPLETE.value)
    value = field.get("value")
    if value is None:
        raise ValueError(OrchestratorErrorCode.MISSING_BINDING.value)
    return value


def _is_stale(
    bars: Sequence[PanelBarV1],
    *,
    epoch_index: int,
    reference_timestamp: str,
    max_bar_staleness_bars: int,
) -> bool:
    if epoch_index < 0:
        return True
    if epoch_index >= len(bars):
        staleness = epoch_index - len(bars) + 1
        return staleness > max_bar_staleness_bars
    if bars[epoch_index].timestamp_utc != reference_timestamp:
        return True
    return False


def _resolve_target_side(score: float | None) -> SlotSide:
    if score is None or not math.isfinite(score) or score == 0.0:
        return SlotSide.FLAT
    if score > 0:
        return SlotSide.LONG
    return SlotSide.SHORT


@dataclass
class _SlotState:
    current_side: SlotSide = SlotSide.FLAT
    current_instrument_id: str | None = None
    pending_target_side: SlotSide | None = None
    pending_target_instrument_id: str | None = None
    flat_epochs_remaining: int = 0


def _apply_rotation_state_machine(
    state: _SlotState,
    *,
    target_side: SlotSide,
    target_instrument_id: str | None,
    switch_entry_delay_epochs: int,
) -> tuple[SlotSide, str | None, bool]:
    """Apply flat-then-wait-then-enter rotation semantics."""
    pending_switch = False

    if (
        state.current_side == target_side
        and state.current_instrument_id == target_instrument_id
        and state.flat_epochs_remaining == 0
        and state.pending_target_side is None
    ):
        return state.current_side, state.current_instrument_id, False

    if state.flat_epochs_remaining > 0:
        state.flat_epochs_remaining -= 1
        state.current_side = SlotSide.FLAT
        state.current_instrument_id = None
        if state.flat_epochs_remaining == 0 and state.pending_target_side is not None:
            state.current_side = state.pending_target_side
            state.current_instrument_id = state.pending_target_instrument_id
            state.pending_target_side = None
            state.pending_target_instrument_id = None
        pending_switch = True
        return state.current_side, state.current_instrument_id, pending_switch

    same_position = (
        state.current_side == target_side and state.current_instrument_id == target_instrument_id
    )
    if same_position:
        return state.current_side, state.current_instrument_id, False

    if state.current_side != SlotSide.FLAT:
        state.pending_target_side = target_side
        state.pending_target_instrument_id = target_instrument_id
        state.flat_epochs_remaining = switch_entry_delay_epochs
        state.current_side = SlotSide.FLAT
        state.current_instrument_id = None
        pending_switch = True
        return state.current_side, state.current_instrument_id, pending_switch

    if target_side == SlotSide.FLAT:
        state.current_side = SlotSide.FLAT
        state.current_instrument_id = None
        state.pending_target_side = None
        state.pending_target_instrument_id = None
        return state.current_side, state.current_instrument_id, False

    state.current_side = target_side
    state.current_instrument_id = target_instrument_id
    return state.current_side, state.current_instrument_id, False


def run_cross_sectional_single_slot_orchestrator_v0(
    *,
    binding: Mapping[str, Any],
    panel_series: Sequence[InstrumentPanelSeriesV1],
    eligible_instrument_ids: Sequence[str] | None = None,
) -> OrchestratorRunResultV0:
    """Run deterministic single-slot panel orchestration over aligned panel series."""
    lookback_n = int(_extract_numeric_binding(binding, "lookback_N"))
    vol_window_v = int(_extract_numeric_binding(binding, "vol_window_V"))
    vol_epsilon = float(_extract_numeric_binding(binding, "vol_epsilon"))
    signal_lag_bars = int(_extract_numeric_binding(binding, "signal_lag_bars"))
    min_eligible = int(_extract_numeric_binding(binding, "min_eligible_members_for_rank"))
    switch_delay = int(_extract_numeric_binding(binding, "switch_entry_delay_epochs"))
    max_staleness = int(_extract_numeric_binding(binding, "max_bar_staleness_bars"))

    panel_validation = validate_panel_series_v1(
        panel_series,
        min_instruments=min_eligible,
        forbidden_instrument_substrings=FORBIDDEN_INSTRUMENT_TOKENS,
    )
    bitcoin_present = PanelValidationErrorCode.BITCOIN_INSTRUMENT_PRESENT.value in (
        panel_validation.error_codes
    )
    insufficient = PanelValidationErrorCode.INSUFFICIENT_INSTRUMENTS.value in (
        panel_validation.error_codes
    )
    alignment_failed = panel_validation.panel_alignment_check == "FAIL"
    if bitcoin_present or insufficient or alignment_failed:
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
        raise ValueError(OrchestratorErrorCode.UNKNOWN_INSTRUMENT.value)

    reference_series = max(series_by_id.values(), key=lambda s: len(s.bars))
    bar_count = len(reference_series.bars)
    closes_by_id = {iid: _parse_close_series(series.bars) for iid, series in series_by_id.items()}

    state = _SlotState()
    epoch_results: list[OrchestratorEpochResultV0] = []

    for epoch_index in range(bar_count):
        timestamp_utc = reference_series.bars[epoch_index].timestamp_utc
        error_codes: list[str] = []
        epoch_scores: list[CrossSectionalScoreResultV0] = []

        for instrument_id, closes in closes_by_id.items():
            series = series_by_id[instrument_id]
            if _is_stale(
                series.bars,
                epoch_index=epoch_index,
                reference_timestamp=timestamp_utc,
                max_bar_staleness_bars=max_staleness,
            ):
                error_codes.append(OrchestratorErrorCode.STALE_BAR_EXCLUDED.value)
                continue
            score_result = compute_instrument_score_v0(
                instrument_id,
                closes,
                lookback_n=lookback_n,
                vol_window_v=vol_window_v,
                vol_epsilon=vol_epsilon,
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
            error_codes.append(OrchestratorErrorCode.INSUFFICIENT_ELIGIBLE_MEMBERS.value)
        else:
            top = ranked[0]
            top_score = top.score
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
                scores=tuple(ranked),
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


def default_operator_binding_v0() -> Mapping[str, Any]:
    """Return binding dict with ratified operator numeric values for orchestrator tests."""
    from src.research.cross_sectional_ranking_semantics_binding_v0 import (
        apply_ratified_operator_bindings_v0,
        materialize_cross_sectional_ranking_semantics_binding_v0,
    )

    return apply_ratified_operator_bindings_v0(
        materialize_cross_sectional_ranking_semantics_binding_v0()
    )
