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
from typing import Any, Mapping, Sequence, Union

from src.research.cross_sectional_ranking_semantics_binding_v0 import (
    RATIFIED_OPERATOR_BINDING_VALUES,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_score_v0 import (
    SCORE_FORMULA_VERSION as LEAD_LAG_SCORE_FORMULA_VERSION,
    LeadLagDiffusionScoreResultV0,
    compute_instrument_diffusion_score_v0,
    compute_panel_median_lagged_return_v0,
    rank_scores_deterministic_v0 as rank_lead_lag_scores_deterministic_v0,
)
from src.research.cross_sectional_relative_strength_v0_score_v0 import (
    SCORE_FORMULA_VERSION,
    CrossSectionalScoreResultV0,
    compute_instrument_score_v0,
    rank_scores_deterministic_v0,
)

SCORE_FAMILY_RELATIVE_STRENGTH = SCORE_FORMULA_VERSION
SCORE_FAMILY_LEAD_LAG_DIFFUSION = LEAD_LAG_SCORE_FORMULA_VERSION
ScoreResultV0 = Union[CrossSectionalScoreResultV0, LeadLagDiffusionScoreResultV0]
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
    UNKNOWN_SCORE_FAMILY = "UNKNOWN_SCORE_FAMILY"


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
    scores: tuple[ScoreResultV0, ...]
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


def _resolve_score_formula_version(binding: Mapping[str, Any]) -> str:
    explicit = binding.get("score_formula_version")
    if isinstance(explicit, str) and explicit:
        return explicit
    policy_classes = binding.get("policy_classes", {})
    if isinstance(policy_classes, Mapping):
        family = policy_classes.get("score_family_policy")
        if isinstance(family, str) and family:
            return family
    return SCORE_FORMULA_VERSION


def _compute_relative_strength_epoch_scores_v0(
    *,
    closes_by_id: dict[str, tuple[float, ...]],
    series_by_id: dict[str, InstrumentPanelSeriesV1],
    epoch_index: int,
    timestamp_utc: str,
    lookback_n: int,
    vol_window_v: int,
    vol_epsilon: float,
    signal_lag_bars: int,
    max_staleness: int,
) -> tuple[list[CrossSectionalScoreResultV0], list[str]]:
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
    return epoch_scores, error_codes


def _compute_lead_lag_epoch_scores_v0(
    *,
    closes_by_id: dict[str, tuple[float, ...]],
    series_by_id: dict[str, InstrumentPanelSeriesV1],
    epoch_index: int,
    timestamp_utc: str,
    lag_window_l: int,
    signal_lag_bars: int,
    max_staleness: int,
) -> tuple[list[LeadLagDiffusionScoreResultV0], list[str]]:
    error_codes: list[str] = []
    active_closes: dict[str, tuple[float, ...]] = {}
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
        active_closes[instrument_id] = closes

    panel = compute_panel_median_lagged_return_v0(
        active_closes,
        lag_window_l=lag_window_l,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    if panel is None:
        return [], error_codes

    panel_median_return, _ = panel
    epoch_scores: list[LeadLagDiffusionScoreResultV0] = []
    for instrument_id, closes in active_closes.items():
        score_result = compute_instrument_diffusion_score_v0(
            instrument_id,
            closes,
            lag_window_l=lag_window_l,
            signal_lag_bars=signal_lag_bars,
            epoch_index=epoch_index,
            panel_median_return=panel_median_return,
        )
        if score_result is not None:
            epoch_scores.append(score_result)
    return epoch_scores, error_codes


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
    score_formula_version: str | None = None,
) -> OrchestratorRunResultV0:
    """Run deterministic single-slot panel orchestration over aligned panel series."""
    resolved_score_family = score_formula_version or _resolve_score_formula_version(binding)
    min_eligible = int(_extract_numeric_binding(binding, "min_eligible_members_for_rank"))
    switch_delay = int(_extract_numeric_binding(binding, "switch_entry_delay_epochs"))
    max_staleness = int(_extract_numeric_binding(binding, "max_bar_staleness_bars"))
    signal_lag_bars = int(_extract_numeric_binding(binding, "signal_lag_bars"))
    lookback_n = 0
    vol_window_v = 0
    vol_epsilon = 0.0
    lag_window_l = 0
    if resolved_score_family == SCORE_FAMILY_RELATIVE_STRENGTH:
        lookback_n = int(_extract_numeric_binding(binding, "lookback_N"))
        vol_window_v = int(_extract_numeric_binding(binding, "vol_window_V"))
        vol_epsilon = float(_extract_numeric_binding(binding, "vol_epsilon"))
    elif resolved_score_family == SCORE_FAMILY_LEAD_LAG_DIFFUSION:
        lag_window_l = int(_extract_numeric_binding(binding, "lag_window_L"))
    else:
        raise ValueError(OrchestratorErrorCode.UNKNOWN_SCORE_FAMILY.value)

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
            score_formula_version=resolved_score_family,
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
        if resolved_score_family == SCORE_FAMILY_RELATIVE_STRENGTH:
            epoch_scores, error_codes = _compute_relative_strength_epoch_scores_v0(
                closes_by_id=closes_by_id,
                series_by_id=series_by_id,
                epoch_index=epoch_index,
                timestamp_utc=timestamp_utc,
                lookback_n=lookback_n,
                vol_window_v=vol_window_v,
                vol_epsilon=vol_epsilon,
                signal_lag_bars=signal_lag_bars,
                max_staleness=max_staleness,
            )
            ranked = rank_scores_deterministic_v0(epoch_scores)
        else:
            epoch_scores, error_codes = _compute_lead_lag_epoch_scores_v0(
                closes_by_id=closes_by_id,
                series_by_id=series_by_id,
                epoch_index=epoch_index,
                timestamp_utc=timestamp_utc,
                lag_window_l=lag_window_l,
                signal_lag_bars=signal_lag_bars,
                max_staleness=max_staleness,
            )
            ranked = rank_lead_lag_scores_deterministic_v0(epoch_scores)
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
        score_formula_version=resolved_score_family,
        epochs=tuple(epoch_results),
        final_slot_side=state.current_side,
        final_instrument_id=state.current_instrument_id,
        authority_effect="NONE",
        runtime_effect="NONE",
        order_effect="NONE",
    )


def _bound_numeric(value: int | float | str) -> dict[str, Any]:
    return {"status": "BOUND", "value": value}


def default_lead_lag_operator_binding_v0(
    versioned_binding: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    """Map ratified lead-lag hypothesis binding to orchestrator numeric bindings."""
    if versioned_binding is None:
        from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (
            materialize_versioned_hypothesis_binding_v0,
        )

        versioned_binding = materialize_versioned_hypothesis_binding_v0()

    parameter_binding = versioned_binding["parameter_binding"]
    selection_binding = versioned_binding["binding"]["selection_hold_exit_rotation_binding"]
    return {
        "score_formula_version": versioned_binding["score_family_policy"],
        "numeric_bindings": {
            "lag_window_L": _bound_numeric(parameter_binding["lag_window_L"]),
            "signal_lag_bars": _bound_numeric(parameter_binding["signal_lag_bars"]),
            "min_eligible_members_for_rank": _bound_numeric(
                parameter_binding["min_eligible_members_for_rank"]
            ),
            "switch_entry_delay_epochs": _bound_numeric(
                selection_binding["switch_entry_delay_epochs"]
            ),
            "max_bar_staleness_bars": _bound_numeric(parameter_binding["max_bar_staleness_bars"]),
        },
    }


def default_operator_binding_v0() -> Mapping[str, Any]:
    """Return binding dict with ratified operator numeric values for orchestrator tests."""
    from src.research.cross_sectional_ranking_semantics_binding_v0 import (
        apply_ratified_operator_bindings_v0,
        materialize_cross_sectional_ranking_semantics_binding_v0,
    )

    binding = apply_ratified_operator_bindings_v0(
        materialize_cross_sectional_ranking_semantics_binding_v0()
    )
    return {
        **binding,
        "score_formula_version": SCORE_FORMULA_VERSION,
    }
