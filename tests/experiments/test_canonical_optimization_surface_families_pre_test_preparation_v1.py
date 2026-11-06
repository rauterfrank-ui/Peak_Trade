"""Contract tests for optimization surface family pre-test preparation v1."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    SURFACE_ID as F5_FRESH_SURFACE_ID,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_SURFACE_ID,
)
from src.experiments.canonical_optimization_surface_families_pre_test_preparation_v1 import (
    BOUND_ORIGIN_MAIN_SHA,
    DECISION_CONFIG,
    EXTERNAL_EFFECT_AUTHORIZED,
    MV2_DOUBLE_PLAY_SOLE_TRADING_DECISION_AUTHORITY,
    NORMATIVE_SPEC,
    PRODUCTIVE_EFFECT,
    PreparationStatus,
    ResearchTestEntryGateV1,
    WORKPACKAGE_ID,
    assert_family_set_closed_v1,
    assert_f3_excluded_by_authority_boundary_v1,
    build_optimization_surface_family_matrix_v1,
    build_preparation_status_summary_v1,
    f5_subfamily_status_v1,
    list_authorized_optimization_surface_ids_v1,
    list_excluded_family_gate_ids_v1,
    list_owner_decision_required_family_gate_ids_v1,
    list_test_ready_surface_ids_v1,
    optimization_surface_family_records_v1,
    verify_test_ready_cross_surface_isolation_v1,
)
from src.research.linear_evidence.parameter_sensitivity_productive_contract_v0 import (
    ALLOWED_CALIBRATABLE_PARAMETERS,
    DIAGNOSTIC_ONLY_PARAMETERS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "experiments"
    / "canonical_optimization_surface_families_pre_test_preparation_v1.py"
)


def test_decision_config_aligns_with_matrix() -> None:
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["workpackage_id"] == WORKPACKAGE_ID
    assert decision["bound_origin_main_sha"] == BOUND_ORIGIN_MAIN_SHA
    assert decision["test_ready_surface_ids"] == list(list_test_ready_surface_ids_v1())
    assert decision["authorized_optimization_surface_ids"] == list(
        list_authorized_optimization_surface_ids_v1()
    )
    assert decision["owner_decision_required_family_gate_ids"] == list(
        list_owner_decision_required_family_gate_ids_v1()
    )
    assert decision["excluded_family_gate_ids"] == list(list_excluded_family_gate_ids_v1())
    assert decision["family_set_closed"] is True


def test_f1_f2_f5_fresh_status_and_isolation() -> None:
    summary = build_preparation_status_summary_v1()
    assert summary["f1_status"] == PreparationStatus.TEST_READY.value
    assert summary["f2_status"] == PreparationStatus.TEST_READY.value
    assert summary["f5_fresh_status"] == PreparationStatus.TEST_READY_SHADOW_RESEARCH.value
    isolation = verify_test_ready_cross_surface_isolation_v1()
    assert isolation["isolation_proven"] is True
    assert isolation["productive_effect"] == PRODUCTIVE_EFFECT
    assert isolation["external_effect_authorized"] is EXTERNAL_EFFECT_AUTHORIZED


def test_f3_excluded_and_f5_subfamilies_shadow_only() -> None:
    assert_f3_excluded_by_authority_boundary_v1()
    assert_family_set_closed_v1()
    f5 = f5_subfamily_status_v1()
    assert f5["F5-FRESH"] == PreparationStatus.TEST_READY_SHADOW_RESEARCH.value
    assert f5["F5-SURV"] == PreparationStatus.TEST_READY_PER_TOKEN_SHADOW_CALIBRATION_ONLY.value
    assert f5["F5-CAP"] == PreparationStatus.TEST_READY_PER_TOKEN_SHADOW_CALIBRATION_ONLY.value
    f3 = next(r for r in optimization_surface_family_records_v1() if r.family_gate_id == "F3")
    assert f3.preparation_status == PreparationStatus.EXCLUDED_BY_AUTHORITY_BOUNDARY
    assert f3.test_entry_gate == ResearchTestEntryGateV1.UNKNOWN_FAIL_CLOSED


def test_f2_allowed_parameters_match_productive_contract() -> None:
    assert ALLOWED_CALIBRATABLE_PARAMETERS == ("fee_bps", "slippage_bps")
    assert "signal_scale" in DIAGNOSTIC_ONLY_PARAMETERS


def test_matrix_covers_all_records_and_normative_spec_exists() -> None:
    matrix = build_optimization_surface_family_matrix_v1()
    assert matrix["workpackage_id"] == WORKPACKAGE_ID
    assert len(matrix["families"]) == len(optimization_surface_family_records_v1())
    assert (REPO_ROOT / NORMATIVE_SPEC).is_file()


def test_authorized_surface_ids_partition() -> None:
    assert list_test_ready_surface_ids_v1() == (F1_SURFACE_ID, F2_SURFACE_ID)
    assert list_authorized_optimization_surface_ids_v1() == (
        F1_SURFACE_ID,
        F2_SURFACE_ID,
        F5_FRESH_SURFACE_ID,
    )


def test_module_has_no_trading_hot_path_imports() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert "src.trading.master_v2.integrated_offline_trading_logic_replay_v1" not in imported
    assert "src.execution" not in imported


def test_global_safety_flags_unchanged() -> None:
    matrix = build_optimization_surface_family_matrix_v1()
    assert matrix["mv2_double_play_sole_trading_decision_authority"] is True
    assert matrix["productive_effect"] == "NONE"
    assert MV2_DOUBLE_PLAY_SOLE_TRADING_DECISION_AUTHORITY is True
