from __future__ import annotations

import ast
import json
from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import build_trace_matrix
from scripts.research.survival_suitability_narrow_reuse_first_rewire_v0 import (
    CHAINED_CONTRACT_TEST_PATH,
    REUSED_SCENARIO_BINDING_ADAPTER_OWNER,
    REUSED_SUITABILITY_BINDING_OWNER,
    REUSED_SURVIVAL_ASSESSMENT_OWNER,
    SCENARIO_REPLAY_CONTRACT_TEST_PATH,
    SURFACE_ID,
    build_rewire_binding,
    evaluate_survival_suitability_parity_fixtures_v0,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
)
from trading.master_v2.survival_assessment_v1 import (
    SURVIVAL_ASSESSMENT_POLICY_VERSION,
    SurvivalAssessmentStatus,
    SurvivalMetricInputsV1,
    SurvivalSubcheckResultV1,
    SurvivalSubcheckStatus,
    aggregate_survival_status,
)
from trading.master_v2.survival_suitability_scenario_binding_adapter_v0 import (
    CANONICAL_SUITABILITY_BINDING_OWNER,
    CANONICAL_SURVIVAL_ASSESSMENT_OWNER,
    SURVIVAL_SUITABILITY_SCENARIO_BINDING_ADAPTER_OWNER,
    ScenarioSurvivalSuitabilityOverridesV0,
    evaluate_scenario_survival_suitability_v0,
)
from trading.master_v2.suitability_binding_v1 import (
    SUITABILITY_RANKING_POLICY_VERSION,
    SuitabilityBindingStatus,
    SuitabilityRegimeStatus,
    SuitabilityStrategyEntryV1,
    SuitabilityStrategyRegistryV1,
    evaluate_suitability_binding_v1,
    select_strategy_deterministic,
)
from trading.master_v2.double_play_state import SideState
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _replay_input

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "docs"
    / "research"
    / "survival_and_suitability_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
INTEGRATED_REPLAY = ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
OFFLINE_REPLAY = ROOT / "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
SURVIVAL_ASSESSMENT = ROOT / "src/trading/master_v2/survival_assessment_v1.py"
SUITABILITY_BINDING = ROOT / "src/trading/master_v2/suitability_binding_v1.py"
SCENARIO_ADAPTER = (
    ROOT / "src/trading/master_v2/survival_suitability_scenario_binding_adapter_v0.py"
)
BACKTEST_WIRING = ROOT / "src/backtest/mv2_research_wiring_v1.py"
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

_REQUIRED_SUBCHECKS = (
    "DATA_COMPLETENESS_CHECK",
    "COST_SURVIVAL_CHECK",
    "VOLATILITY_SURVIVAL_CHECK",
    "SEQUENCE_SURVIVAL_CHECK",
    "DRAWDOWN_SURVIVAL_CHECK",
    "LIQUIDATION_BUFFER_CHECK",
)


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _survival_surface(inventory: dict) -> dict:
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


def test_contract_surface_flags_wired_and_pass() -> None:
    data = load_contract()
    assert data["survival_backtest_parity_status"] == "WIRED"
    assert data["survival_backtest_parity_pass"] is True
    assert data["suitability_backtest_parity_status"] == "WIRED"
    assert data["suitability_backtest_parity_pass"] is True
    assert data["survival_required_unknown_blocks"] is True
    assert data["survival_any_hard_fail_fails"] is True
    assert data["survival_all_required_pass_required"] is True
    assert data["unknown_regime_blocks_new_entry"] is True
    assert data["no_implicit_strategy_selection_by_list_order"] is True
    assert data["no_fallback_strategy"] is True
    assert data["stable_tie_break_policy_bound"] is True
    assert data["canonical_owner_identified"] is True
    assert data["rewire_required"] is False
    assert data["full_canonical_chain_wired"] is False
    assert data["backtest_runtime_decision_parity_pass"] is False
    assert data["system_economic_evidence_admissible"] is False
    assert data["runtime_rewire_admissible"] is False


def test_contract_binds_expected_owners_and_call_paths() -> None:
    data = load_contract()
    assert data["canonical_survival_assessment_owner"] == CANONICAL_SURVIVAL_ASSESSMENT_OWNER
    assert data["canonical_suitability_binding_owner"] == CANONICAL_SUITABILITY_BINDING_OWNER
    assert (
        data["canonical_survival_suitability_adapter_owner"]
        == SURVIVAL_SUITABILITY_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert (
        data["canonical_integrated_replay_owner"] == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    )
    assert "mv2_research_wiring_v1" in data["backtest_call_path"]
    assert "evaluate_survival_assessment_v1" in data["backtest_call_path"]
    assert "evaluate_suitability_binding_v1" in data["backtest_call_path"]
    assert (
        "compose_double_play_scenario_via_canonical_matrix_v0" in data["offline_replay_call_path"]
    )
    assert data["assessment_status"] == "WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE"
    assert tuple(data["survival_subchecks_wired"]) == _REQUIRED_SUBCHECKS


def test_narrow_rewire_not_required_in_wired_assessment_slice() -> None:
    data = load_contract()
    decision = data["narrow_rewire_decision"]
    assert decision["mode"] == "ASSERTION_SURFACE_ONLY"
    assert decision["rewire_implemented"] is False
    assert decision["rewire_required"] is False
    assert decision["admissible_next_slice_if_gap_confirmed"] == "NONE"


def test_inventory_pins_survival_suitability_backtest_binding_to_parity_contract() -> None:
    inventory = build_inventory(ROOT)
    surface = _survival_surface(inventory)
    pinned_paths = {hit["path"] for hit in surface["backtest_binding_candidates"][:5]}
    assert SCENARIO_REPLAY_CONTRACT_TEST_PATH in pinned_paths
    assert CHAINED_CONTRACT_TEST_PATH in pinned_paths


def test_trace_matrix_confirms_survival_suitability_offline_parity_bound() -> None:
    inventory = build_inventory(ROOT)
    matrix = build_trace_matrix(inventory)
    survival_edge = next(edge for edge in matrix["trace_edges"] if edge["surface_id"] == SURFACE_ID)
    assert survival_edge["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    assert load_contract()["trace_rewire_bound"] is True


def test_prior_narrow_rewire_binding_reaches_canonical_owners() -> None:
    result = evaluate_survival_suitability_parity_fixtures_v0()
    assert result.bull_survival.status is SurvivalAssessmentStatus.PASS
    assert result.bull_suitability.status is SuitabilityBindingStatus.PASS

    rewire = build_rewire_binding(ROOT)
    binding = rewire["rewire_binding"]
    assert binding["functional_rewire_performed"] is True
    assert binding["new_parallel_owner_created"] is False
    assert binding["reused_survival_assessment_owner"] == REUSED_SURVIVAL_ASSESSMENT_OWNER
    assert binding["reused_suitability_binding_owner"] == REUSED_SUITABILITY_BINDING_OWNER
    assert binding["reused_scenario_binding_adapter_owner"] == REUSED_SCENARIO_BINDING_ADAPTER_OWNER


def test_integrated_replay_and_backtest_call_canonical_survival_suitability() -> None:
    replay_source = INTEGRATED_REPLAY.read_text(encoding="utf-8")
    backtest_source = BACKTEST_WIRING.read_text(encoding="utf-8")
    survival_source = SURVIVAL_ASSESSMENT.read_text(encoding="utf-8")

    assert "evaluate_survival_assessment_v1" in replay_source
    assert "evaluate_suitability_binding_v1" in replay_source
    assert "run_integrated_offline_trading_logic_replay_v1" in backtest_source
    assert "aggregate_survival_status" in survival_source
    for subcheck in (
        "data_completeness_check",
        "cost_survival_check",
        "volatility_survival_check",
        "sequence_survival_check",
        "drawdown_survival_check",
        "liquidation_buffer_check",
    ):
        assert subcheck in survival_source


def test_offline_replay_routes_through_survival_suitability_adapter() -> None:
    offline_source = OFFLINE_REPLAY.read_text(encoding="utf-8")
    matrix_adapter = (
        ROOT / "src/trading/master_v2/double_play_composition_scenario_matrix_adapter_v0.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(offline_source)
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "compose_double_play_scenario_via_canonical_matrix_v0"
    }
    assert "compose_double_play_scenario_via_canonical_matrix_v0" in calls
    assert "apply_canonical_survival_suitability_pre_matrix_gates_v0" in matrix_adapter
    assert OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER.endswith(
        "offline_double_play_scenario_replay_v0"
    )
    assert SCENARIO_ADAPTER.is_file()


def test_survival_aggregation_negative_paths() -> None:
    required = tuple(
        SurvivalSubcheckResultV1(
            name=name.lower(), status=SurvivalSubcheckStatus.PASS, reason_code="ok"
        )
        for name in _REQUIRED_SUBCHECKS
    )
    assert aggregate_survival_status(required) is SurvivalAssessmentStatus.PASS

    hard_fail = tuple(
        SurvivalSubcheckResultV1(
            name=name.lower(),
            status=SurvivalSubcheckStatus.FAIL
            if name == "DATA_COMPLETENESS_CHECK"
            else SurvivalSubcheckStatus.PASS,
            reason_code="fail" if name == "DATA_COMPLETENESS_CHECK" else "ok",
        )
        for name in _REQUIRED_SUBCHECKS
    )
    assert aggregate_survival_status(hard_fail) is SurvivalAssessmentStatus.FAIL

    unknown = tuple(
        SurvivalSubcheckResultV1(
            name=name.lower(),
            status=SurvivalSubcheckStatus.UNKNOWN
            if name == "SEQUENCE_SURVIVAL_CHECK"
            else SurvivalSubcheckStatus.PASS,
            reason_code="unknown" if name == "SEQUENCE_SURVIVAL_CHECK" else "ok",
        )
        for name in _REQUIRED_SUBCHECKS
    )
    assert aggregate_survival_status(unknown) is SurvivalAssessmentStatus.BLOCKED


def test_suitability_unknown_regime_blocks_entry() -> None:
    from tests.trading.master_v2.test_suitability_binding_v1 import (
        _binding_input,
        _ranking_policy,
    )

    blocked = evaluate_suitability_binding_v1(
        _binding_input(
            regime_id="unknown_regime",
            regime_status=SuitabilityRegimeStatus.UNKNOWN,
        ),
        _ranking_policy(),
    )
    assert blocked.status is SuitabilityBindingStatus.BLOCKED
    assert blocked.selected_strategy_id is None


def test_deterministic_strategy_selection_independent_of_list_order() -> None:
    from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentSide
    from trading.master_v2.suitability_binding_v1 import SuitabilityRankingPolicyV1

    policy = SuitabilityRankingPolicyV1(
        policy_version=SUITABILITY_RANKING_POLICY_VERSION,
        tie_break_field="strategy_id",
        validity_epochs=3,
        no_match_status=SuitabilityBindingStatus.FAIL,
    )
    entries_a = (
        SuitabilityStrategyEntryV1(
            strategy_id="beta",
            priority_rank=1,
            supported_sides=(DirectionalAssessmentSide.LONG,),
            supported_regime_ids=("trend_up",),
        ),
        SuitabilityStrategyEntryV1(
            strategy_id="alpha",
            priority_rank=1,
            supported_sides=(DirectionalAssessmentSide.LONG,),
            supported_regime_ids=("trend_up",),
        ),
    )
    entries_b = tuple(reversed(entries_a))
    selected_a, _ = select_strategy_deterministic(entries_a, policy=policy)
    selected_b, _ = select_strategy_deterministic(entries_b, policy=policy)
    assert selected_a == selected_b == "alpha"


def test_scenario_negative_paths_block_on_survival_fail_and_unknown_regime() -> None:
    survival_fail = evaluate_scenario_survival_suitability_v0(
        instrument_id="SYNTHETIC:ETH-USDT-PERP",
        trading_epoch=61,
        side_st=SideState.LONG_ACTIVE,
        overrides=ScenarioSurvivalSuitabilityOverridesV0(
            bull_survival_status=SurvivalAssessmentStatus.FAIL,
        ),
    )
    assert survival_fail.bull_survival.status is SurvivalAssessmentStatus.FAIL

    unknown_regime = evaluate_scenario_survival_suitability_v0(
        instrument_id="SYNTHETIC:ETH-USDT-PERP",
        trading_epoch=61,
        side_st=SideState.LONG_ACTIVE,
        overrides=ScenarioSurvivalSuitabilityOverridesV0(
            regime_status=SuitabilityRegimeStatus.UNKNOWN,
        ),
    )
    assert unknown_regime.bull_suitability.status is SuitabilityBindingStatus.BLOCKED


def test_integrated_replay_consumes_survival_and_suitability() -> None:
    result = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    assert result.intermediate is not None
    assert result.intermediate.bull_survival.status in {
        SurvivalAssessmentStatus.PASS,
        SurvivalAssessmentStatus.BLOCKED,
        SurvivalAssessmentStatus.FAIL,
    }
    assert result.intermediate.bull_suitability.status in {
        SuitabilityBindingStatus.PASS,
        SuitabilityBindingStatus.BLOCKED,
        SuitabilityBindingStatus.FAIL,
    }


def test_gap_review_and_source_evidence_refs() -> None:
    data = load_contract()
    findings = data["gap_review_findings"]
    assert findings["bypass_path_reproducible"] is False
    assert findings["separate_backtest_survival_owner_reproducible"] is False
    assert findings["separate_backtest_suitability_owner_reproducible"] is False
    assert findings["integrated_replay_calls_canonical_survival_and_suitability"] is True
    assert findings["scenario_replay_survival_suitability_adapter_bound"] is True
    assert data["source_manifest_verify_rc"] == 0
    assert FLAT_BEFORE_CONTRACT.is_file()
    assert BULL_BEAR_CONTRACT.is_file()
    assert ADVERSE_EXIT_CONTRACT.is_file()
    assert (
        "docs/research/flat_before_opposite_side_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
        in data["source_evidence_contract_refs"]
    )


def test_stable_tie_break_policy_version_bound() -> None:
    data = load_contract()
    assert data["stable_tie_break_policy_bound"] is True
    assert SURVIVAL_ASSESSMENT_POLICY_VERSION
    assert SUITABILITY_RANKING_POLICY_VERSION
    suitability_source = SUITABILITY_BINDING.read_text(encoding="utf-8")
    assert "tie_break_field" in suitability_source
    assert "priority_rank" in suitability_source
