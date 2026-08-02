"""Single Selected Future policy descriptor and eligibility helpers."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from src.ops.single_selected_future_policy_v1.constants_v1 import (
    DATA_QUALITY_PASS,
    DEFAULT_HYSTERESIS_RANK_IMPROVEMENT,
    DEFAULT_MAX_RANKING_AGE_SECONDS,
    DEFAULT_MIN_DATA_QUALITY_STATUS,
    DEFAULT_MIN_HISTORY_SAMPLES,
    DEFAULT_MIN_HOLDING_PERIOD_SECONDS,
    DEFAULT_REFRESH_CADENCE_SECONDS,
    ELIGIBILITY_ELIGIBLE,
    MANUAL_OVERRIDE_ALLOWED,
    MAX_POSITIONS_EFFECTIVE,
    SELECTED_FUTURE_COUNT,
    SELECTION_POLICY_ID,
    SELECTION_POLICY_PROVENANCE,
    SELECTION_POLICY_VERSION,
    SINGLE_SELECTED_FUTURE,
)
from src.ops.single_selected_future_policy_v1.reason_codes_v1 import SelectionFailureCodeV1


def policy_descriptor_v1() -> dict[str, Any]:
    return {
        "selection_policy_id": SELECTION_POLICY_ID,
        "selection_policy_version": SELECTION_POLICY_VERSION,
        "selection_policy_provenance": SELECTION_POLICY_PROVENANCE,
        "selected_future_count": SELECTED_FUTURE_COUNT,
        "max_positions": MAX_POSITIONS_EFFECTIVE,
        "single_selected_future": SINGLE_SELECTED_FUTURE,
        "multi_future_runtime_authorized": False,
        "tie_break_order": (
            "ranking_rank_asc",
            "venue_native_id_asc",
            "canonical_instrument_id_asc",
        ),
        "refresh_cadence_seconds": DEFAULT_REFRESH_CADENCE_SECONDS,
        "min_holding_period_seconds": DEFAULT_MIN_HOLDING_PERIOD_SECONDS,
        "hysteresis_rank_improvement": DEFAULT_HYSTERESIS_RANK_IMPROVEMENT,
        "max_ranking_age_seconds": DEFAULT_MAX_RANKING_AGE_SECONDS,
        "min_history_samples": DEFAULT_MIN_HISTORY_SAMPLES,
        "min_data_quality_status": DEFAULT_MIN_DATA_QUALITY_STATUS,
        "manual_override_allowed": MANUAL_OVERRIDE_ALLOWED,
        "open_position_semantics": (
            "no_silent_instrument_switch",
            "no_alpha_authority_for_replacement",
            "risk_safety_exit_reconciliation_preserved",
            "replacement_only_as_persisted_pending_state",
        ),
        "dashboard_authority": False,
        "allowlist_selection_authority": False,
        "alpha_opens_positions": False,
        "fail_closed": True,
    }


def candidate_exclusion_codes_v1(
    candidate: Mapping[str, Any],
    *,
    instrument_status: Mapping[str, Any] | None,
    min_history_samples: int,
    min_data_quality_status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    eligibility = str(candidate.get("eligibility_status") or "")
    if eligibility != ELIGIBILITY_ELIGIBLE:
        codes.append(SelectionFailureCodeV1.NO_ELIGIBLE_SELECTION.value)

    dq = str(candidate.get("data_quality_status") or "")
    overlay = dict(instrument_status or {})
    if overlay:
        dq = str(overlay.get("data_quality_status") or dq)
        history = overlay.get("history_sample_count")
        mark_present = overlay.get("mark_price_present")
        trading_status = str(overlay.get("trading_status") or "").strip().lower()
        suspended = bool(overlay.get("suspended", False))
        data_loss = bool(overlay.get("data_loss", False))
        if mark_present is False:
            codes.append(SelectionFailureCodeV1.MARK_PRICE_MISSING.value)
        if suspended or trading_status in {"suspend", "suspended", "settle"}:
            codes.append(SelectionFailureCodeV1.INSTRUMENT_SUSPENDED.value)
        if history is not None and int(history) < int(min_history_samples):
            codes.append(SelectionFailureCodeV1.MINIMUM_HISTORY_FAILURE.value)
        if data_loss:
            codes.append(SelectionFailureCodeV1.DATA_LOSS.value)
        if overlay.get("instrument_valid") is False:
            codes.append(SelectionFailureCodeV1.INSTRUMENT_INVALID.value)

    required_dq = str(min_data_quality_status or DATA_QUALITY_PASS)
    if dq != required_dq:
        codes.append(SelectionFailureCodeV1.DATA_QUALITY_FAILURE.value)

    return tuple(sorted(set(codes)))


def is_selection_eligible_v1(exclusion_codes: Sequence[str]) -> bool:
    return len(tuple(exclusion_codes)) == 0


def soft_degradation_codes_v1(
    instrument_status: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    """Non-excluding degradation markers (instrument remains selectable)."""
    overlay = dict(instrument_status or {})
    if not overlay:
        return ()
    codes: list[str] = []
    if bool(overlay.get("degraded", False)):
        codes.append("SELECTED_DEGRADED_MARKER")
    if str(overlay.get("connectivity_status") or "").upper() == "DEGRADED":
        codes.append("CONNECTIVITY_DEGRADED")
    return tuple(sorted(set(codes)))


def rank_of_instrument_v1(
    ranked_candidates: list[Mapping[str, Any]],
    instrument_id: str,
) -> Optional[int]:
    for row in ranked_candidates:
        if str(row.get("canonical_instrument_id") or "") == instrument_id:
            return int(row.get("rank") or 0)
        if str(row.get("venue_native_id") or "") == instrument_id:
            return int(row.get("rank") or 0)
    return None
