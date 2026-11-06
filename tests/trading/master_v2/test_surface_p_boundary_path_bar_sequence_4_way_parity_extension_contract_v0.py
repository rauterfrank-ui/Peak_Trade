"""Surface P boundary-path bar-sequence 4-way parity extension contract (offline only)."""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    ALLOWED_SLICE_CHANGED_PATH_PREFIXES,
    parity_surface_assessments_v0,
    scan_changed_paths_for_forbidden_runtime_v0,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    RUNTIME_REFERENCE_INTEGRATION_STATUS_V0,
    SURFACE_P_BAR_SEQUENCE_FIXTURE_COUNT,
    SURFACE_P_BOUNDARY_PATH_BAR_SEQUENCE_4_WAY_PARITY_EXTENSION_SLICE_ID,
    SURFACE_P_BOUNDARY_PATH_FIXTURE_COUNT,
    SURFACE_P_BOUNDARY_PATH_KINDS,
    SURFACE_P_CORE_BAR_SEQUENCE_FIXTURE_COUNT,
    evaluate_surface_p_full_bar_sequence_four_way_parity_v0,
    scan_changed_paths_for_forbidden_runtime_v0 as harness_scan_forbidden,
    surface_p_bar_sequence_fixtures_v0,
    surface_p_boundary_path_fixtures_v0,
    surface_p_core_bar_sequence_fixtures_v0,
)
from trading.master_v2.runtime_bridge_pre_activation_gate_v0 import (
    current_head_default_gate_input_v0,
    evaluate_runtime_bridge_pre_activation_gate_v0,
)
from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
    evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

_SLICE_SOURCE_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    REPO_ROOT / "scripts/ops/run_surface_p_boundary_path_bar_sequence_4_way_parity_extension_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_surface_p_boundary_path_bar_sequence_4_way_parity_extension_contract_v0.py",
)


def _scan_forbidden_imports(path: Path, forbidden_tokens: frozenset[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in forbidden_tokens):
                    hits.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden_tokens):
                hits.append(node.module)
    return hits


def test_slice_constants_v0() -> None:
    assert (
        SURFACE_P_BOUNDARY_PATH_BAR_SEQUENCE_4_WAY_PARITY_EXTENSION_SLICE_ID
        == "SURFACE_P_BOUNDARY_PATH_BAR_SEQUENCE_4_WAY_PARITY_EXTENSION_V0"
    )
    assert RUNTIME_REFERENCE_INTEGRATION_STATUS_V0 == "BOUND_NOT_ACTIVATED"


def test_boundary_path_fixtures_defined_v0() -> None:
    boundary = surface_p_boundary_path_fixtures_v0()
    assert len(boundary) == SURFACE_P_BOUNDARY_PATH_FIXTURE_COUNT
    assert {item.path_kind for item in boundary} == set(SURFACE_P_BOUNDARY_PATH_KINDS)
    all_fixtures = surface_p_bar_sequence_fixtures_v0()
    assert len(all_fixtures) == SURFACE_P_BAR_SEQUENCE_FIXTURE_COUNT
    assert (
        len(surface_p_core_bar_sequence_fixtures_v0()) == SURFACE_P_CORE_BAR_SEQUENCE_FIXTURE_COUNT
    )


def test_boundary_path_four_way_parity_complete_v0() -> None:
    assessment = evaluate_surface_p_full_bar_sequence_four_way_parity_v0()
    assert assessment.fixtures_complete is True
    assert assessment.core_fixtures_complete is True
    assert assessment.boundary_path_fixtures_complete is True
    assert assessment.boundary_fixtures_added == (
        "safety_kernel_boundary",
        "killswitch_boundary",
        "reconciliation_unknown_outcome_boundary",
        "promotion_gate_boundary",
        "ai_observability_boundary",
        "feedback_learning_boundary",
    )
    boundary_assessments = assessment.fixture_assessments[
        SURFACE_P_CORE_BAR_SEQUENCE_FIXTURE_COUNT:
    ]
    assert len(boundary_assessments) == SURFACE_P_BOUNDARY_PATH_FIXTURE_COUNT
    for item in boundary_assessments:
        assert item.four_way_fixture_parity_bound is True
        assert item.runtime_reference_lane_bound is True
        assert item.runtime_reference_non_authority_confirmed is True


def test_surface_p_registry_pass_with_runtime_activation_pending_v0() -> None:
    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    assert surface_p.parity_status == "PASS"
    assert surface_p.missing_binding_if_any == ""
    semantic = evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0()
    assert semantic.surface_p_overall_status == "PARTIAL_RUNTIME_ACTIVATION_PENDING"
    assert semantic.runtime_bridge_activated is False
    assert RUNTIME_REFERENCE_INTEGRATION_STATUS_V0 == "BOUND_NOT_ACTIVATED"


def test_runtime_bridge_pre_activation_gate_still_blocked_v0() -> None:
    gate = evaluate_runtime_bridge_pre_activation_gate_v0(current_head_default_gate_input_v0())
    assert gate.runtime_bridge_pre_activation_gate_status == "FAIL"
    assert gate.runtime_bridge_activation_admissible is False
    assert gate.authority_effect == "NONE"


def test_forbidden_runtime_paths_guard_v0() -> None:
    ok, violations = scan_changed_paths_for_forbidden_runtime_v0(
        ALLOWED_SLICE_CHANGED_PATH_PREFIXES
    )
    assert ok is True
    assert violations == ()
    ok_h, violations_h = harness_scan_forbidden(ALLOWED_SLICE_CHANGED_PATH_PREFIXES)
    assert ok_h is True
    assert violations_h == ()


def test_slice_sources_exclude_execution_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "execution",
            "scheduler",
            "credentials",
            "live_runtime",
            "testnet",
            "shadow",
            "paper_lane",
        }
    )
    for path in _SLICE_SOURCE_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"
