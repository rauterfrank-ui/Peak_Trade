from __future__ import annotations

import ast
import json
from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.double_play_composition_narrow_reuse_first_rewire_v0 import (
    CHAINED_CONTRACT_TEST_PATH,
    REUSED_CANONICAL_OWNER,
    REUSED_SCENARIO_MATRIX_ADAPTER_OWNER,
    SCENARIO_MATRIX_PARITY_CONTRACT_TEST_PATH,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_double_play_composition_parity_fixtures_v0,
)
from trading.master_v2.directional_assessment_v1 import (
    DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    DirectionalAssessmentSide,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionConflictStatus,
    CompositionSelectedSide,
    CompositionStatus,
)
from trading.master_v2.double_play_composition_scenario_matrix_adapter_v0 import (
    CANONICAL_DOUBLE_PLAY_COMPOSITION_OWNER,
    DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_OWNER,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
)
from trading.master_v2.survival_suitability_scenario_binding_adapter_v0 import (
    SURVIVAL_SUITABILITY_SCENARIO_BINDING_ADAPTER_OWNER,
    apply_canonical_survival_suitability_pre_matrix_gates_v0,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _replay_input

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "docs"
    / "research"
    / "double_play_composition_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
INTEGRATED_REPLAY = ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
OFFLINE_REPLAY = ROOT / "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
COMPOSITION_MATRIX = ROOT / "src/trading/master_v2/double_play_composition_matrix_v1.py"
SCENARIO_ADAPTER = (
    ROOT / "src/trading/master_v2/double_play_composition_scenario_matrix_adapter_v0.py"
)
DIRECTIONAL_ASSESSMENT = ROOT / "src/trading/master_v2/directional_assessment_v1.py"
BACKTEST_WIRING = ROOT / "src/backtest/mv2_research_wiring_v1.py"
SURVIVAL_SUITABILITY_CONTRACT = (
    ROOT
    / "docs/research/survival_and_suitability_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
FLAT_BEFORE_CONTRACT = (
    ROOT
    / "docs/research/flat_before_opposite_side_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
BULL_BEAR_CONTRACT = (
    ROOT
    / "docs/research/bull_bear_state_switch_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
ADVERSE_EXIT_CONTRACT = (
    ROOT
    / "docs/research/adverse_exit_and_reversal_preparation_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _composition_surface(inventory: dict) -> dict:
    return next(s for s in inventory["surfaces"] if s["surface_id"] == SURFACE_ID)


def test_contract_is_authority_neutral_and_no_runtime() -> None:
    data = load_contract()
    assert data["authority_effect"] == "NONE"
    assert data["runtime_effect"] == "NONE"
    assert data["orders_allowed"] is False
    assert data["scheduler_runtime_allowed"] is False
    assert data["live_authorized"] is False
    assert data["shadow_authorized"] is False
    assert data["paper_authorized"] is False
    assert data["testnet_authorized"] is False
    assert data["futures_only"] is True
    assert data["bitcoin_direction_allowed"] is False


def test_contract_surface_flags_assessed_and_pass() -> None:
    data = load_contract()
    assert data["double_play_composition_backtest_parity_status"] == "ASSESSED"
    assert data["double_play_composition_backtest_parity_pass"] is True
    assert data["double_play_canonical_owner_reused"] is True
    assert data["separate_backtest_composition_logic_found"] is False
    assert data["narrow_rewire_required"] is False
    assert data["narrow_rewire_implemented"] is False
    assert data["both_sides_confirmed_chop_guard_block"] is True
    assert data["survival_suitability_pre_composition_gates"] is True
    assert data["existing_position_management_continues"] is True
    assert data["no_implicit_scoring_override"] is True
    assert data["long_short_symmetry_pass"] is True
    assert data["canonical_owner_identified"] is True
    assert data["full_canonical_chain_wired"] is False
    assert data["backtest_runtime_decision_parity_pass"] is False
    assert data["system_economic_evidence_admissible"] is False
    assert data["runtime_rewire_admissible"] is False


def test_contract_binds_expected_owners_and_call_paths() -> None:
    data = load_contract()
    assert data["canonical_composition_matrix_owner"] == CANONICAL_DOUBLE_PLAY_COMPOSITION_OWNER
    assert (
        data["canonical_scenario_matrix_adapter_owner"]
        == DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_OWNER
    )
    assert (
        data["canonical_survival_suitability_adapter_owner"]
        == SURVIVAL_SUITABILITY_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert (
        data["canonical_integrated_replay_owner"] == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    )
    assert "mv2_research_wiring_v1" in data["backtest_call_path"]
    assert "evaluate_double_play_composition_matrix_v1" in data["backtest_call_path"]
    assert (
        "compose_double_play_scenario_via_canonical_matrix_v0" in data["offline_replay_call_path"]
    )
    assert data["assessment_status"] == "WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE"


def test_narrow_rewire_not_required_in_wired_assessment_slice() -> None:
    data = load_contract()
    decision = data["narrow_rewire_decision"]
    assert decision["mode"] == "ASSERTION_SURFACE_ONLY"
    assert decision["rewire_implemented"] is False
    assert decision["rewire_required"] is False
    assert decision["admissible_next_slice_if_gap_confirmed"] == "NONE"


def test_inventory_pins_double_play_composition_backtest_binding_to_parity_contract() -> None:
    inventory = build_inventory(ROOT)
    surface = _composition_surface(inventory)
    pinned_paths = {hit["path"] for hit in surface["backtest_binding_candidates"][:5]}
    assert SCENARIO_MATRIX_PARITY_CONTRACT_TEST_PATH in pinned_paths
    assert CHAINED_CONTRACT_TEST_PATH in pinned_paths


def test_trace_matrix_confirms_double_play_composition_offline_parity_bound() -> None:
    inventory = build_inventory(ROOT)
    matrix = build_trace_matrix(inventory)
    edge = next(edge for edge in matrix["trace_edges"] if edge["surface_id"] == SURFACE_ID)
    assert edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    assert load_contract()["trace_rewire_bound"] is True


def test_prior_narrow_rewire_binding_reaches_canonical_owners() -> None:
    result = evaluate_double_play_composition_parity_fixtures_v0()
    assert result.composition_status is CompositionStatus.CHOP_GUARD_BLOCK
    assert result.conflict_status is CompositionConflictStatus.BOTH_SIDES_CONFIRMED
    assert result.selected_side is CompositionSelectedSide.NONE

    rewire = build_rewire_binding(ROOT)
    binding = rewire["rewire_binding"]
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["reused_canonical_owner"] == REUSED_CANONICAL_OWNER
    assert binding["reused_scenario_matrix_adapter_owner"] == REUSED_SCENARIO_MATRIX_ADAPTER_OWNER


def test_integrated_replay_and_backtest_call_canonical_composition_matrix() -> None:
    replay_source = INTEGRATED_REPLAY.read_text(encoding="utf-8")
    backtest_source = BACKTEST_WIRING.read_text(encoding="utf-8")
    matrix_source = COMPOSITION_MATRIX.read_text(encoding="utf-8")

    assert (
        "evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1" in replay_source
    )
    assert "evaluate_directional_assessment_with_confirmation_progress_v1" in (
        Path(
            "src/trading/master_v2/directional_assessment_confirmation_integration_v1.py"
        ).read_text(encoding="utf-8")
    )
    assert "evaluate_survival_assessment_v1" in replay_source
    assert "evaluate_suitability_binding_v1" in replay_source
    assert "evaluate_double_play_composition_matrix_v1" in replay_source
    assert "run_integrated_offline_trading_logic_replay_v1" in backtest_source
    assert "both_sides_confirmed" in matrix_source
    assert "chop_guard_block" in matrix_source
    assert "no_new_entry" in matrix_source
    assert "existing_position_management_continues" in matrix_source


def test_offline_replay_routes_through_composition_matrix_adapter() -> None:
    offline_source = OFFLINE_REPLAY.read_text(encoding="utf-8")
    adapter_source = SCENARIO_ADAPTER.read_text(encoding="utf-8")
    tree = ast.parse(offline_source)
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "compose_double_play_scenario_via_canonical_matrix_v0"
    }
    assert "compose_double_play_scenario_via_canonical_matrix_v0" in calls
    assert "apply_canonical_survival_suitability_pre_matrix_gates_v0" in adapter_source
    assert "evaluate_double_play_composition_matrix_v1" in adapter_source
    assert OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER.endswith(
        "offline_double_play_scenario_replay_v0"
    )


def test_no_separate_backtest_compose_double_play_decision() -> None:
    backtest_source = BACKTEST_WIRING.read_text(encoding="utf-8")
    assert "compose_double_play_decision" not in backtest_source
    assert "evaluate_double_play_composition_matrix_v1" not in backtest_source


def test_bull_bear_assessment_uses_shared_directional_contract() -> None:
    replay_source = INTEGRATED_REPLAY.read_text(encoding="utf-8")
    directional_source = DIRECTIONAL_ASSESSMENT.read_text(encoding="utf-8")
    assert "DirectionalAssessmentSide.LONG" in replay_source
    assert "DirectionalAssessmentSide.SHORT" in replay_source
    assert (
        "evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1" in replay_source
    )
    assert "evaluate_directional_assessment_with_confirmation_progress_v1" in (
        Path(
            "src/trading/master_v2/directional_assessment_confirmation_integration_v1.py"
        ).read_text(encoding="utf-8")
    )
    assert DirectionalAssessmentSide.LONG.value in directional_source
    assert DirectionalAssessmentSide.SHORT.value in directional_source
    assert DIRECTIONAL_ASSESSMENT_POLICY_VERSION


def test_survival_suitability_pre_matrix_gates_present() -> None:
    adapter_source = SCENARIO_ADAPTER.read_text(encoding="utf-8")
    assert "apply_canonical_survival_suitability_pre_matrix_gates_v0" in adapter_source
    assert apply_canonical_survival_suitability_pre_matrix_gates_v0.__name__


def test_integrated_replay_consumes_composition_matrix() -> None:
    result = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    assert result.intermediate is not None
    assert result.intermediate.composition_result.composition_status in CompositionStatus
    assert result.intermediate.composition_result.authority_effect == "NONE"
    assert result.intermediate.composition_result.runtime_effect == "NONE"
    assert result.intermediate.composition_result.order_effect == "NONE"


def test_gap_review_and_source_evidence_refs() -> None:
    data = load_contract()
    findings = data["gap_review_findings"]
    assert findings["bypass_path_reproducible"] is False
    assert findings["separate_backtest_composition_logic_reproducible"] is False
    assert findings["integrated_replay_calls_canonical_composition_matrix"] is True
    assert findings["scenario_replay_composition_matrix_adapter_bound"] is True
    assert findings["legacy_compose_double_play_decision_not_in_backtest_chain"] is True
    assert data["source_manifest_verify_rc"] == 0
    assert SURVIVAL_SUITABILITY_CONTRACT.is_file()
    assert FLAT_BEFORE_CONTRACT.is_file()
    assert BULL_BEAR_CONTRACT.is_file()
    assert ADVERSE_EXIT_CONTRACT.is_file()
    assert (
        "docs/research/survival_and_suitability_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
        in data["source_evidence_contract_refs"]
    )
