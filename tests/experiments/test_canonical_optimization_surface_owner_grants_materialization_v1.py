"""Owner grants materialization v1 contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.experiments.canonical_f3_strategy_hyperparameter_optimizable_surface_exclusion_v1 import (
    GLOBAL_F3_OPTIMIZABLE_SURFACE_AUTHORIZED,
    assert_global_f3_surface_not_authorized_v1,
)
from src.experiments.canonical_f5_shadow_per_token_calibration_test_entry_v1 import (
    OPTIMIZER_ENVELOPE_AUTHORIZED,
    build_shadow_calibration_registry_v1,
    shadow_per_token_calibration_entries_v1,
)
from src.experiments.canonical_optimization_surface_families_pre_test_preparation_v1 import (
    PreparationStatus,
    assert_family_set_closed_v1,
    assert_f3_excluded_by_authority_boundary_v1,
    build_preparation_status_summary_v1,
    list_authorized_optimization_surface_ids_v1,
    list_unclassified_current_family_gate_ids_v1,
    verify_test_ready_cross_surface_isolation_v1,
)
from src.experiments.canonical_optimization_surface_owner_grants_materialization_v1 import (
    DECISION_CONFIG,
    WORKPACKAGE_ID,
    build_owner_decisions_materialized_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_owner_grants_decision_config_present() -> None:
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["workpackage_id"] == WORKPACKAGE_ID
    assert decision["owner_decisions"]["D4_F3"]["global_f3_optimizable_surface_authorized"] is False
    assert len(decision["authorized_optimization_surface_ids"]) == 3


def test_materialized_owner_decisions_align_with_registry() -> None:
    payload = build_owner_decisions_materialized_v1()
    assert payload["global_f3_optimizable_surface_authorized"] is False
    assert len(payload["authorized_surface_ids"]) == 3
    assert payload["d2_d3_shadow_registry"]["optimizer_envelope_authorized"] is False


def test_shadow_per_token_registry_counts() -> None:
    registry = build_shadow_calibration_registry_v1()
    assert registry["survival_token_count"] == 10
    assert registry["capital_token_count"] == 7
    assert len(shadow_per_token_calibration_entries_v1()) == 17
    assert OPTIMIZER_ENVELOPE_AUTHORIZED is False


def test_f3_global_exclusion_fail_closed() -> None:
    assert GLOBAL_F3_OPTIMIZABLE_SURFACE_AUTHORIZED is False
    assert_f3_excluded_by_authority_boundary_v1()
    try:
        assert_global_f3_surface_not_authorized_v1(
            surface_id="F3_STRATEGY_HYPERPARAMETER_OPTIMIZATION_V1"
        )
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_family_set_closed_and_isolated() -> None:
    assert list_unclassified_current_family_gate_ids_v1() == ()
    assert_family_set_closed_v1()
    summary = build_preparation_status_summary_v1()
    assert summary["f1_status"] == PreparationStatus.TEST_READY.value
    assert summary["f2_status"] == PreparationStatus.TEST_READY.value
    assert summary["f5_fresh_status"] == PreparationStatus.TEST_READY_SHADOW_RESEARCH.value
    assert summary["f3_status"] == PreparationStatus.EXCLUDED_BY_AUTHORITY_BOUNDARY.value
    assert summary["family_set_closed"] is True
    assert len(list_authorized_optimization_surface_ids_v1()) == 3
    isolation = verify_test_ready_cross_surface_isolation_v1()
    assert isolation["isolation_proven"] is True
