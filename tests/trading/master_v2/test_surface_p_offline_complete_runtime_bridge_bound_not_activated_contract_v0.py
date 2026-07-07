"""Surface P offline-complete vs runtime-bridge-bound-not-activated contract tests."""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.ai_observability_boundary_offline_replay_binding_adapter_v0 import (
    AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED,
    ORDER_EFFECT_NONE,
    RUNTIME_AUTHORITY_EFFECT_NONE,
)
from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    ALLOWED_SLICE_CHANGED_PATH_PREFIXES,
    parity_gap_records_v0,
    parity_surface_assessments_v0,
    render_parity_gap_matrix_json_v0,
    scan_changed_paths_for_forbidden_runtime_v0,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    RUNTIME_REFERENCE_INTEGRATION_STATUS_V0,
    evaluate_surface_p_full_bar_sequence_four_way_parity_v0,
)
from trading.master_v2.legacy_runtime_entrypoint_guard_v0 import (
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
)
from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
    CONTRACT_SLICE_ID,
    PACKAGE_MARKER,
    evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0,
    surface_p_offline_parity_complete_runtime_activation_pending_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

_SLICE_SOURCE_PATHS = tuple(
    REPO_ROOT / p
    for p in ALLOWED_SLICE_CHANGED_PATH_PREFIXES
    if p.endswith(".py") and "surface_p_offline_complete_runtime_bridge" in p
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


def test_contract_constants_v0() -> None:
    assert (
        CONTRACT_SLICE_ID
        == "SURFACE_P_OFFLINE_COMPLETE_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED_FAIL_CLOSED_CONTRACT_V0"
    )
    assert PACKAGE_MARKER.endswith("=true")


def test_offline_four_way_parity_complete_runtime_bridge_bound_not_activated_v0() -> None:
    bar = evaluate_surface_p_full_bar_sequence_four_way_parity_v0()
    assert bar.fixtures_complete is True
    assert bar.runtime_bridge_status == "BOUND_NOT_ACTIVATED"
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "BOUND_NOT_ACTIVATED"
    assert RUNTIME_REFERENCE_INTEGRATION_STATUS_V0 == "BOUND_NOT_ACTIVATED"


def test_surface_p_semantic_split_v0() -> None:
    semantic = evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0()
    assert semantic.surface_p_offline_parity_status == "COMPLETE"
    assert semantic.surface_p_runtime_bridge_binding_status == "BOUND_NOT_ACTIVATED"
    assert semantic.surface_p_runtime_activation_status == "NOT_ACTIVATED_POLICY_BLOCKED"
    assert semantic.surface_p_overall_status == "PARTIAL_RUNTIME_ACTIVATION_PENDING"
    assert semantic.offline_economic_evidence_blocked_by_runtime_activation is False
    assert semantic.runtime_authority_blocked_by_runtime_activation is True
    assert surface_p_offline_parity_complete_runtime_activation_pending_v0(semantic) is True


def test_runtime_and_order_authority_remain_false_v0() -> None:
    semantic = evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0()
    assert semantic.runtime_authority_granted is False
    assert semantic.order_authority_granted is False
    assert semantic.scheduler_authority_granted is False
    assert semantic.shadow_paper_testnet_live_authority_granted is False
    assert semantic.runtime_bridge_activated is False


def test_ai_observability_no_authority_boundary_v0() -> None:
    semantic = evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0()
    assert semantic.ai_observability_boundary_documented is True
    assert (
        semantic.ai_observability_boundary_documented == AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED
    )
    assert semantic.ai_layer_authority_effect == "NONE"
    assert semantic.ai_layer_order_effect == ORDER_EFFECT_NONE
    assert semantic.ai_layer_runtime_effect == RUNTIME_AUTHORITY_EFFECT_NONE


def test_surface_p_not_counted_as_offline_parity_gap_when_activation_pending_v0() -> None:
    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    assert surface_p.parity_status == "PARTIAL"
    gap_record_ids = {record["surface_id"] for record in parity_gap_records_v0()}
    assert "P" not in gap_record_ids


def test_parity_matrix_json_includes_surface_p_semantic_v0() -> None:
    import json

    payload = json.loads(render_parity_gap_matrix_json_v0())
    assert payload["surface_p_semantic"]["surface_p_offline_parity_status"] == "COMPLETE"
    assert (
        payload["surface_p_semantic"]["surface_p_overall_status"]
        == "PARTIAL_RUNTIME_ACTIVATION_PENDING"
    )
    surface_p = next(item for item in payload["surfaces"] if item["surface_id"] == "P")
    assert surface_p["matrix_status"] == "PARTIAL_RUNTIME_ACTIVATION_PENDING"
    assert surface_p["surface_p_semantic"]["runtime_bridge_activated"] is False


def test_forbidden_runtime_paths_guard_v0() -> None:
    ok, violations = scan_changed_paths_for_forbidden_runtime_v0(
        ALLOWED_SLICE_CHANGED_PATH_PREFIXES
    )
    assert ok is True
    assert violations == ()


def test_slice_sources_exclude_runtime_imports_v0() -> None:
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
