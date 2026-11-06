"""Contract tests for cross_sectional_ranking_semantics_binding.v0 and validator v0."""

from __future__ import annotations

from copy import deepcopy

import pytest

from src.research.cross_sectional_ranking_semantics_binding_v0 import (
    SCHEMA_VERSION,
    materialize_cross_sectional_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_ranking_semantics_binding_validator_v0 import (
    REASON_ATOMIC_SIDE_SWITCH,
    REASON_BOTTOM1_SEMANTICS,
    REASON_DUAL_RANK_SEMANTICS,
    REASON_INCOMPLETE_BINDING_MARKED_COMPLETE,
    REASON_INSUFFICIENT_PANEL_WITHOUT_FLAT,
    REASON_MISSING_BAR_CARRY_FORWARD,
    REASON_MISSING_COST_MODEL_BINDING,
    REASON_MISSING_DATASET_MANIFEST,
    REASON_MISSING_DIGEST,
    REASON_MISSING_PERIOD_BINDING,
    REASON_MISSING_WAIT_EPOCH,
    REASON_NON_FINITE_SCORE_NOT_FLAT,
    REASON_NUMERIC_STRENGTH_THRESHOLD_ENABLED,
    REASON_ROUNDED_SCORE_TIE_BREAK,
    REASON_SAME_BAR_EXECUTION,
    REASON_SELECTED_MISSING_WITHOUT_FORCE_FLAT,
    REASON_SIDE_FLIP_WITHOUT_RECONCILED_FLAT,
    REASON_SIGNAL_LAG_BELOW_MINIMUM,
    REASON_SIGNAL_LAG_ZERO,
    REASON_UNSTABLE_TIE_BREAK,
    REASON_UNVERSIONED_UNIVERSE_BINDING,
    REASON_ZERO_SCORE_NOT_FLAT,
    ValidationVerdict,
    validate_cross_sectional_ranking_semantics_binding_v0,
)


def _materialized() -> dict:
    return materialize_cross_sectional_ranking_semantics_binding_v0()


def _mutated(**patches: object) -> dict:
    binding = deepcopy(_materialized())
    for path, value in patches.items():
        node = binding
        parts = path.split(".")
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = value
    return binding


def test_ratified_policy_classes_materialize_successfully() -> None:
    binding = _materialized()
    assert binding["schema_version"] == SCHEMA_VERSION
    assert binding["policy_classes"]["score_family_policy"] == (
        "volatility_normalized_fixed_lookback_return"
    )
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is True
    assert result.verdict == ValidationVerdict.ACCEPTED_INCOMPLETE


def test_fully_unbound_numeric_schema_is_valid_but_incomplete() -> None:
    binding = _materialized()
    status = binding["binding_status"]
    assert status["policy_classes_status"] == "BOUND"
    assert status["numeric_bindings_status"] == "REQUIRED_UNBOUND"
    assert status["overall_binding_status"] == "INCOMPLETE_FAIL_CLOSED"
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is True
    assert result.verdict == ValidationVerdict.ACCEPTED_INCOMPLETE


def test_sign_boundary_only_is_accepted() -> None:
    binding = _materialized()
    assert binding["threshold_semantics"]["threshold_policy"] == "sign_boundary_only"
    assert binding["numeric_bindings"]["min_abs_score_strength"]["status"] == "NOT_APPLICABLE"
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is True


def test_negative_top1_maps_to_short_same_instrument() -> None:
    binding = _materialized()
    direction = binding["direction_semantics"]
    assert direction["negative_top1_means"] == "SHORT_TOP1"
    assert direction["bottom1_selection_allowed"] is False
    assert direction["dual_rank_forbidden"] is True
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is True


def test_deterministic_tie_break_contract_is_accepted() -> None:
    binding = _materialized()
    tie = binding["tie_break_semantics"]
    assert tie["primary_order"] == "score_desc"
    assert tie["secondary_order"] == "instrument_id_asc"
    assert tie["score_representation"] == "unrounded_internal_score"
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is True


def test_selected_missing_force_flat_contract_is_accepted() -> None:
    binding = _materialized()
    missing = binding["missing_bar_semantics"]
    assert missing["selected_missing"] == "force_flat"
    assert missing["carry_forward"] is False
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is True


def test_reconciled_flat_wait_epoch_contract_is_accepted() -> None:
    binding = _materialized()
    switch = binding["switch_semantics"]
    assert switch["opposite_side_requires_reconciled_flat"] is True
    assert switch["flat_then_wait_one_epoch_then_enter"] is True
    assert switch["atomic_side_switch"] is False
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is True


@pytest.mark.parametrize(
    ("patch_path", "patch_value", "reason"),
    [
        ("direction_semantics.bottom1_selection_allowed", True, REASON_BOTTOM1_SEMANTICS),
        ("direction_semantics.dual_rank_forbidden", False, REASON_DUAL_RANK_SEMANTICS),
        (
            "direction_semantics.ascending_rank_for_short_selection_forbidden",
            False,
            REASON_DUAL_RANK_SEMANTICS,
        ),
        ("direction_semantics.selection_mode", "top_or_bottom", REASON_DUAL_RANK_SEMANTICS),
        ("direction_semantics.zero_score_target", "HOLD", REASON_ZERO_SCORE_NOT_FLAT),
        ("direction_semantics.non_finite_score_target", "HOLD", REASON_NON_FINITE_SCORE_NOT_FLAT),
        ("timing_semantics.same_bar_execution", True, REASON_SAME_BAR_EXECUTION),
        ("timing_semantics.minimum_signal_lag_bars", 0, REASON_SIGNAL_LAG_BELOW_MINIMUM),
        ("switch_semantics.atomic_side_switch", True, REASON_ATOMIC_SIDE_SWITCH),
        (
            "switch_semantics.opposite_side_requires_reconciled_flat",
            False,
            REASON_SIDE_FLIP_WITHOUT_RECONCILED_FLAT,
        ),
        ("switch_semantics.flat_then_wait_one_epoch_then_enter", False, REASON_MISSING_WAIT_EPOCH),
        ("missing_bar_semantics.carry_forward", True, REASON_MISSING_BAR_CARRY_FORWARD),
        (
            "missing_bar_semantics.selected_missing",
            "exclude",
            REASON_SELECTED_MISSING_WITHOUT_FORCE_FLAT,
        ),
        (
            "panel_semantics.insufficient_panel_action",
            "hold",
            REASON_INSUFFICIENT_PANEL_WITHOUT_FLAT,
        ),
        ("tie_break_semantics.primary_order", "score_asc", REASON_UNSTABLE_TIE_BREAK),
        (
            "tie_break_semantics.score_representation",
            "rounded_display_score",
            REASON_ROUNDED_SCORE_TIE_BREAK,
        ),
        (
            "threshold_semantics.threshold_policy",
            "fixed_policy_threshold",
            REASON_NUMERIC_STRENGTH_THRESHOLD_ENABLED,
        ),
        (
            "threshold_semantics.numeric_strength_threshold_initial",
            True,
            REASON_NUMERIC_STRENGTH_THRESHOLD_ENABLED,
        ),
    ],
)
def test_negative_policy_semantics_rejected(
    patch_path: str, patch_value: object, reason: str
) -> None:
    binding = _mutated(**{patch_path: patch_value})
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is False
    assert reason in result.fail_reasons


def test_bottom_1_semantics_rejected() -> None:
    binding = _mutated(**{"direction_semantics.bottom1_selection_allowed": True})
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert REASON_BOTTOM1_SEMANTICS in result.fail_reasons


def test_dual_rank_semantics_rejected() -> None:
    binding = _mutated(**{"direction_semantics.selection_mode": "dual_rank_top_bottom"})
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert REASON_DUAL_RANK_SEMANTICS in result.fail_reasons


def test_signal_lag_zero_rejected() -> None:
    binding = _mutated(
        **{
            "numeric_bindings.signal_lag_bars": {"status": "BOUND", "value": 0},
        }
    )
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is False
    assert REASON_SIGNAL_LAG_ZERO in result.fail_reasons


def test_numeric_strength_threshold_enabled_rejected() -> None:
    binding = _mutated(
        **{
            "numeric_bindings.min_abs_score_strength": {"status": "BOUND", "value": 0.1},
        }
    )
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is False
    assert REASON_NUMERIC_STRENGTH_THRESHOLD_ENABLED in result.fail_reasons


def test_unversioned_universe_binding_rejected() -> None:
    binding = _mutated(
        **{
            "external_bindings.pit_universe_manifest_ref": {"status": "BOUND", "ref": ""},
        }
    )
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is False
    assert REASON_UNVERSIONED_UNIVERSE_BINDING in result.fail_reasons


def test_missing_dataset_manifest_rejected() -> None:
    binding = _mutated(
        **{
            "external_bindings.panel_ohlcv_dataset_manifest_ref": {"status": "BOUND", "ref": ""},
        }
    )
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is False
    assert REASON_MISSING_DATASET_MANIFEST in result.fail_reasons


def test_missing_period_binding_rejected() -> None:
    binding = _mutated(
        **{
            "external_bindings.evaluation_period_binding": {"status": "BOUND", "ref": ""},
        }
    )
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is False
    assert REASON_MISSING_PERIOD_BINDING in result.fail_reasons


def test_missing_cost_model_binding_rejected() -> None:
    binding = _mutated(
        **{
            "external_bindings.fee_model_version": {"status": "BOUND", "ref": ""},
        }
    )
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is False
    assert REASON_MISSING_COST_MODEL_BINDING in result.fail_reasons


def test_missing_digest_rejected() -> None:
    binding = _mutated(
        **{
            "digest_bindings.implementation_digest": {"status": "BOUND", "ref": ""},
        }
    )
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is False
    assert REASON_MISSING_DIGEST in result.fail_reasons


def test_incomplete_binding_marked_complete_rejected() -> None:
    binding = _mutated(**{"binding_status.overall_binding_status": "COMPLETE"})
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is False
    assert REASON_INCOMPLETE_BINDING_MARKED_COMPLETE in result.fail_reasons


def test_bound_signal_lag_at_least_one_accepted() -> None:
    binding = _mutated(
        **{
            "numeric_bindings.signal_lag_bars": {"status": "BOUND", "value": 1},
        }
    )
    result = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    assert result.valid is True
