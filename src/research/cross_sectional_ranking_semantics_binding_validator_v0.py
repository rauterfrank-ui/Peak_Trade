"""Fail-closed validator for cross_sectional_ranking_semantics_binding.v0.

Schema, contract, and binding-status validation only. Does not compute scores,
rank instruments, generate signals, load datasets, or invoke runtime paths.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from src.research.cross_sectional_ranking_semantics_binding_v0 import (
    DIGEST_BINDING_KEYS,
    DIRECTION_POLICY,
    EXTERNAL_BINDING_KEYS,
    HYPOTHESIS_ID,
    MINIMUM_SIGNAL_LAG_BARS,
    NUMERIC_BINDING_KEYS,
    SCHEMA_VERSION,
    SCORE_FAMILY_POLICY,
    BindingFieldStatus,
    materialize_cross_sectional_ranking_semantics_binding_v0,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_RANKING_SEMANTICS_BINDING_VALIDATOR_V0=true"

REASON_UNKNOWN_POLICY_ENUM = "UNKNOWN_POLICY_ENUM"
REASON_MISSING_RATIFIED_POLICY_FIELD = "MISSING_RATIFIED_POLICY_FIELD"
REASON_BOTTOM1_SEMANTICS = "BOTTOM1_SEMANTICS_REJECTED"
REASON_DUAL_RANK_SEMANTICS = "DUAL_RANK_SEMANTICS_REJECTED"
REASON_ZERO_SCORE_NOT_FLAT = "ZERO_SCORE_NOT_FLAT"
REASON_NON_FINITE_SCORE_NOT_FLAT = "NON_FINITE_SCORE_NOT_FLAT"
REASON_SAME_BAR_EXECUTION = "SAME_BAR_EXECUTION_REJECTED"
REASON_SIGNAL_LAG_ZERO = "SIGNAL_LAG_ZERO_REJECTED"
REASON_SIGNAL_LAG_BELOW_MINIMUM = "SIGNAL_LAG_BELOW_MINIMUM_REJECTED"
REASON_ATOMIC_SIDE_SWITCH = "ATOMIC_SIDE_SWITCH_REJECTED"
REASON_SIDE_FLIP_WITHOUT_RECONCILED_FLAT = "SIDE_FLIP_WITHOUT_RECONCILED_FLAT_REJECTED"
REASON_MISSING_WAIT_EPOCH = "MISSING_WAIT_EPOCH_REJECTED"
REASON_MISSING_BAR_CARRY_FORWARD = "MISSING_BAR_CARRY_FORWARD_REJECTED"
REASON_SELECTED_MISSING_WITHOUT_FORCE_FLAT = "SELECTED_MISSING_WITHOUT_FORCE_FLAT_REJECTED"
REASON_INSUFFICIENT_PANEL_WITHOUT_FLAT = "INSUFFICIENT_PANEL_WITHOUT_FLAT_REJECTED"
REASON_UNSTABLE_TIE_BREAK = "UNSTABLE_TIE_BREAK_REJECTED"
REASON_ROUNDED_SCORE_TIE_BREAK = "ROUNDED_SCORE_TIE_BREAK_REJECTED"
REASON_NUMERIC_STRENGTH_THRESHOLD_ENABLED = "NUMERIC_STRENGTH_THRESHOLD_ENABLED_REJECTED"
REASON_UNVERSIONED_UNIVERSE_BINDING = "UNVERSIONED_UNIVERSE_BINDING_REJECTED"
REASON_MISSING_DATASET_MANIFEST = "MISSING_DATASET_MANIFEST_REJECTED"
REASON_MISSING_PERIOD_BINDING = "MISSING_PERIOD_BINDING_REJECTED"
REASON_MISSING_COST_MODEL_BINDING = "MISSING_COST_MODEL_BINDING_REJECTED"
REASON_MISSING_DIGEST = "MISSING_DIGEST_REJECTED"
REASON_INCOMPLETE_BINDING_MARKED_COMPLETE = "INCOMPLETE_BINDING_MARKED_COMPLETE_REJECTED"
REASON_NON_FINITE_NUMERIC = "NON_FINITE_NUMERIC_REJECTED"
REASON_NON_POSITIVE_WINDOW = "NON_POSITIVE_WINDOW_OR_INTERVAL_REJECTED"
REASON_CONFLICTING_BINDING_STATUS = "CONFLICTING_BINDING_STATUS_REJECTED"
REASON_INVALID_SCHEMA_VERSION = "INVALID_SCHEMA_VERSION"
REASON_UNKNOWN_BINDING_FIELD_STATUS = "UNKNOWN_BINDING_FIELD_STATUS"
REASON_SWITCH_DELAY_TOO_SHORT = "SWITCH_ENTRY_DELAY_TOO_SHORT_REJECTED"
REASON_NEGATIVE_TOP1_SEMANTICS_MISMATCH = "NEGATIVE_TOP1_SEMANTICS_MISMATCH"

RATIFIED_POLICY_CLASS_VALUES = {
    "score_family_policy": {SCORE_FAMILY_POLICY},
    "direction_policy": {DIRECTION_POLICY},
    "signal_timing_policy": {"finalized_bar_close_epoch"},
    "rebalance_policy_class": {"fixed_N_bar_cadence"},
    "switch_policy": {"flat_then_wait_one_epoch_then_enter"},
    "cooldown_policy": {"no_cooldown"},
    "minimum_hold_policy": {"until_next_rebalance"},
    "panel_completeness_policy": {"per_instrument_eligibility_mask"},
    "missing_bar_policy": {"exclude_non_selected_instrument_for_epoch"},
    "tie_break_policy": {"score_desc_then_instrument_id_asc"},
    "threshold_policy": {"sign_boundary_only"},
}

POSITIVE_NUMERIC_KEYS = frozenset(
    {
        "lookback_N",
        "vol_window_V",
        "vol_epsilon",
        "rebalance_interval_bars",
        "signal_lag_bars",
        "min_eligible_members_for_rank",
        "switch_entry_delay_epochs",
        "max_bar_staleness_bars",
    }
)


class ValidationVerdict(str, Enum):
    ACCEPTED_INCOMPLETE = "ACCEPTED_INCOMPLETE"
    ACCEPTED_COMPLETE = "ACCEPTED_COMPLETE"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class CrossSectionalRankingSemanticsBindingValidationResult:
    verdict: ValidationVerdict
    valid: bool
    fail_reasons: tuple[str, ...]
    binding_status: Mapping[str, Any]


def _is_finite_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    return False


def _field_status(field: Mapping[str, Any]) -> str | None:
    status = field.get("status")
    return status if isinstance(status, str) else None


def _field_value(field: Mapping[str, Any]) -> Any:
    return field.get("value")


def _field_ref(field: Mapping[str, Any]) -> str:
    ref = field.get("ref", "")
    return ref if isinstance(ref, str) else ""


def _require_mapping(value: Any, path: str, reasons: list[str]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        reasons.append(f"{REASON_MISSING_RATIFIED_POLICY_FIELD}:{path}")
        return None
    return value


def _validate_binding_field(
    field: Any,
    *,
    path: str,
    reasons: list[str],
    allow_not_applicable: bool = False,
) -> Mapping[str, Any] | None:
    mapping = _require_mapping(field, path, reasons)
    if mapping is None:
        return None
    status = _field_status(mapping)
    allowed = {s.value for s in BindingFieldStatus}
    if status not in allowed:
        reasons.append(f"{REASON_UNKNOWN_BINDING_FIELD_STATUS}:{path}")
        return mapping
    if status == BindingFieldStatus.NOT_APPLICABLE.value and not allow_not_applicable:
        reasons.append(f"{REASON_CONFLICTING_BINDING_STATUS}:{path}")
    return mapping


def _validate_bound_numeric(
    key: str,
    field: Mapping[str, Any],
    reasons: list[str],
) -> None:
    status = _field_status(field)
    if status != BindingFieldStatus.BOUND.value:
        return
    value = _field_value(field)
    if key == "vol_return_method":
        if not isinstance(value, str) or not value.strip():
            reasons.append(f"{REASON_NON_FINITE_NUMERIC}:{key}")
        return
    if key == "min_abs_score_strength":
        reasons.append(REASON_NUMERIC_STRENGTH_THRESHOLD_ENABLED)
        return
    if not _is_finite_number(value):
        reasons.append(f"{REASON_NON_FINITE_NUMERIC}:{key}")
        return
    if key in POSITIVE_NUMERIC_KEYS and float(value) <= 0:
        reasons.append(f"{REASON_NON_POSITIVE_WINDOW}:{key}")
    if key == "signal_lag_bars" and float(value) < MINIMUM_SIGNAL_LAG_BARS:
        reasons.append(REASON_SIGNAL_LAG_BELOW_MINIMUM)
    if key == "switch_entry_delay_epochs" and float(value) < 1:
        reasons.append(REASON_SWITCH_DELAY_TOO_SHORT)


def _validate_bound_external(key: str, field: Mapping[str, Any], reasons: list[str]) -> None:
    status = _field_status(field)
    if status != BindingFieldStatus.BOUND.value:
        return
    ref = _field_ref(field)
    value = _field_value(field)
    token = ref or (value if isinstance(value, str) else "")
    if not token.strip():
        if key == "pit_universe_manifest_ref":
            reasons.append(REASON_UNVERSIONED_UNIVERSE_BINDING)
        elif key == "panel_ohlcv_dataset_manifest_ref":
            reasons.append(REASON_MISSING_DATASET_MANIFEST)
        elif key == "evaluation_period_binding":
            reasons.append(REASON_MISSING_PERIOD_BINDING)
        elif key.endswith("_model_version") or key == "execution_model_version":
            reasons.append(REASON_MISSING_COST_MODEL_BINDING)
        else:
            reasons.append(f"{REASON_MISSING_RATIFIED_POLICY_FIELD}:{key}")


def _validate_bound_digest(field: Mapping[str, Any], reasons: list[str]) -> None:
    if _field_status(field) != BindingFieldStatus.BOUND.value:
        return
    token = _field_ref(field) or _field_value(field)
    if not isinstance(token, str) or not token.strip():
        reasons.append(REASON_MISSING_DIGEST)


def _external_group_complete(external: Mapping[str, Any], keys: tuple[str, ...]) -> bool:
    return all(
        _field_status(external[k]) == BindingFieldStatus.BOUND.value
        and (_field_ref(external[k]) or _field_value(external[k]))
        for k in keys
        if k in external
    )


def validate_cross_sectional_ranking_semantics_binding_v0(
    binding: Mapping[str, Any],
) -> CrossSectionalRankingSemanticsBindingValidationResult:
    reasons: list[str] = []

    if binding.get("schema_version") != SCHEMA_VERSION:
        reasons.append(REASON_INVALID_SCHEMA_VERSION)
    if binding.get("hypothesis_id") != HYPOTHESIS_ID:
        reasons.append(f"{REASON_MISSING_RATIFIED_POLICY_FIELD}:hypothesis_id")

    policy_classes = _require_mapping(binding.get("policy_classes"), "policy_classes", reasons)
    if policy_classes is not None:
        for key, allowed in RATIFIED_POLICY_CLASS_VALUES.items():
            value = policy_classes.get(key)
            if value not in allowed:
                reasons.append(f"{REASON_UNKNOWN_POLICY_ENUM}:{key}={value!r}")

    direction = _require_mapping(binding.get("direction_semantics"), "direction_semantics", reasons)
    if direction is not None:
        if direction.get("bottom1_selection_allowed") is not False:
            reasons.append(REASON_BOTTOM1_SEMANTICS)
        if direction.get("dual_rank_forbidden") is not True:
            reasons.append(REASON_DUAL_RANK_SEMANTICS)
        if direction.get("ascending_rank_for_short_selection_forbidden") is not True:
            reasons.append(REASON_DUAL_RANK_SEMANTICS)
        if direction.get("selection_mode") != "single_top1_by_score_desc":
            reasons.append(REASON_DUAL_RANK_SEMANTICS)
        if direction.get("zero_score_target") != "FLAT":
            reasons.append(REASON_ZERO_SCORE_NOT_FLAT)
        if direction.get("non_finite_score_target") != "FLAT":
            reasons.append(REASON_NON_FINITE_SCORE_NOT_FLAT)
        if direction.get("negative_top1_means") != "SHORT_TOP1":
            reasons.append(REASON_NEGATIVE_TOP1_SEMANTICS_MISMATCH)

    timing = _require_mapping(binding.get("timing_semantics"), "timing_semantics", reasons)
    if timing is not None:
        if timing.get("same_bar_execution") is not False:
            reasons.append(REASON_SAME_BAR_EXECUTION)
        min_lag = timing.get("minimum_signal_lag_bars")
        if not isinstance(min_lag, int) or min_lag < MINIMUM_SIGNAL_LAG_BARS:
            reasons.append(REASON_SIGNAL_LAG_BELOW_MINIMUM)

    switch = _require_mapping(binding.get("switch_semantics"), "switch_semantics", reasons)
    if switch is not None:
        if switch.get("atomic_side_switch") is not False:
            reasons.append(REASON_ATOMIC_SIDE_SWITCH)
        if switch.get("opposite_side_requires_reconciled_flat") is not True:
            reasons.append(REASON_SIDE_FLIP_WITHOUT_RECONCILED_FLAT)
        if switch.get("flat_then_wait_one_epoch_then_enter") is not True:
            reasons.append(REASON_MISSING_WAIT_EPOCH)

    missing = _require_mapping(
        binding.get("missing_bar_semantics"), "missing_bar_semantics", reasons
    )
    if missing is not None:
        if missing.get("carry_forward") is not False:
            reasons.append(REASON_MISSING_BAR_CARRY_FORWARD)
        selected = missing.get("selected_missing")
        if selected not in {"force_flat", "FORCE_FLAT"}:
            reasons.append(REASON_SELECTED_MISSING_WITHOUT_FORCE_FLAT)

    panel = _require_mapping(binding.get("panel_semantics"), "panel_semantics", reasons)
    if panel is not None:
        if panel.get("insufficient_panel_action") != "flat":
            reasons.append(REASON_INSUFFICIENT_PANEL_WITHOUT_FLAT)

    tie_break = _require_mapping(binding.get("tie_break_semantics"), "tie_break_semantics", reasons)
    if tie_break is not None:
        if (
            tie_break.get("primary_order") != "score_desc"
            or tie_break.get("secondary_order") != "instrument_id_asc"
        ):
            reasons.append(REASON_UNSTABLE_TIE_BREAK)
        if tie_break.get("score_representation") != "unrounded_internal_score":
            reasons.append(REASON_ROUNDED_SCORE_TIE_BREAK)

    threshold = _require_mapping(binding.get("threshold_semantics"), "threshold_semantics", reasons)
    if threshold is not None:
        if threshold.get("threshold_policy") != "sign_boundary_only":
            reasons.append(REASON_NUMERIC_STRENGTH_THRESHOLD_ENABLED)
        if threshold.get("numeric_strength_threshold_initial") is not False:
            reasons.append(REASON_NUMERIC_STRENGTH_THRESHOLD_ENABLED)

    numeric = _require_mapping(binding.get("numeric_bindings"), "numeric_bindings", reasons)
    if numeric is not None:
        for key in NUMERIC_BINDING_KEYS:
            field = numeric.get(key)
            validated = _validate_binding_field(
                field,
                path=f"numeric_bindings.{key}",
                reasons=reasons,
                allow_not_applicable=(key == "min_abs_score_strength"),
            )
            if validated is None:
                continue
            status = _field_status(validated)
            if key == "min_abs_score_strength":
                if status == BindingFieldStatus.BOUND.value:
                    reasons.append(REASON_NUMERIC_STRENGTH_THRESHOLD_ENABLED)
                elif status not in {
                    BindingFieldStatus.NOT_APPLICABLE.value,
                    BindingFieldStatus.REQUIRED_UNBOUND.value,
                }:
                    reasons.append(REASON_NUMERIC_STRENGTH_THRESHOLD_ENABLED)
            if status == BindingFieldStatus.BOUND.value and key == "signal_lag_bars":
                value = _field_value(validated)
                if value == 0:
                    reasons.append(REASON_SIGNAL_LAG_ZERO)
            _validate_bound_numeric(key, validated, reasons)

    external = _require_mapping(binding.get("external_bindings"), "external_bindings", reasons)
    if external is not None:
        for key in EXTERNAL_BINDING_KEYS:
            field = external.get(key)
            validated = _validate_binding_field(
                field, path=f"external_bindings.{key}", reasons=reasons
            )
            if validated is not None:
                _validate_bound_external(key, validated, reasons)

    digest = _require_mapping(binding.get("digest_bindings"), "digest_bindings", reasons)
    if digest is not None:
        for key in DIGEST_BINDING_KEYS:
            field = digest.get(key)
            validated = _validate_binding_field(
                field, path=f"digest_bindings.{key}", reasons=reasons
            )
            if validated is not None:
                _validate_bound_digest(validated, reasons)

    binding_status = (
        _require_mapping(binding.get("binding_status"), "binding_status", reasons) or {}
    )

    numeric_complete = numeric is not None and all(
        _field_status(numeric[k]) == BindingFieldStatus.BOUND.value
        for k in NUMERIC_BINDING_KEYS
        if k != "min_abs_score_strength"
    )
    universe_complete = (
        external is not None
        and _field_status(external["pit_universe_manifest_ref"]) == BindingFieldStatus.BOUND.value
        and bool(
            _field_ref(external["pit_universe_manifest_ref"])
            or _field_value(external["pit_universe_manifest_ref"])
        )
    )
    dataset_complete = external is not None and _external_group_complete(
        external, ("panel_ohlcv_dataset_manifest_ref", "admissibility_manifest_ref")
    )
    period_complete = (
        external is not None
        and _field_status(external["evaluation_period_binding"]) == BindingFieldStatus.BOUND.value
        and bool(
            _field_ref(external["evaluation_period_binding"])
            or _field_value(external["evaluation_period_binding"])
        )
    )
    cost_complete = external is not None and _external_group_complete(
        external,
        (
            "fee_model_version",
            "slippage_model_version",
            "funding_model_version",
            "spread_model_version",
            "execution_model_version",
        ),
    )
    digest_complete = digest is not None and all(
        _field_status(digest[k]) == BindingFieldStatus.BOUND.value
        and bool(_field_ref(digest[k]) or _field_value(digest[k]))
        for k in DIGEST_BINDING_KEYS
    )

    overall = binding_status.get("overall_binding_status")
    if overall == "COMPLETE":
        if not all(
            [
                numeric_complete,
                universe_complete,
                dataset_complete,
                period_complete,
                cost_complete,
                digest_complete,
            ]
        ):
            reasons.append(REASON_INCOMPLETE_BINDING_MARKED_COMPLETE)

    if binding_status.get("policy_classes_status") != "BOUND":
        reasons.append(f"{REASON_CONFLICTING_BINDING_STATUS}:policy_classes_status")

    strength_field = numeric.get("min_abs_score_strength") if numeric else None
    if strength_field and _field_status(strength_field) == BindingFieldStatus.BOUND.value:
        reasons.append(REASON_NUMERIC_STRENGTH_THRESHOLD_ENABLED)

    unique_reasons = tuple(dict.fromkeys(reasons))
    if unique_reasons:
        return CrossSectionalRankingSemanticsBindingValidationResult(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=unique_reasons,
            binding_status=binding_status,
        )

    if (
        overall == "COMPLETE"
        and numeric_complete
        and universe_complete
        and dataset_complete
        and period_complete
        and cost_complete
        and digest_complete
    ):
        verdict = ValidationVerdict.ACCEPTED_COMPLETE
    else:
        verdict = ValidationVerdict.ACCEPTED_INCOMPLETE

    return CrossSectionalRankingSemanticsBindingValidationResult(
        verdict=verdict,
        valid=True,
        fail_reasons=(),
        binding_status=binding_status,
    )
