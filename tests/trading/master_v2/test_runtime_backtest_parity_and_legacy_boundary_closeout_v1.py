"""Slice 4: runtime/backtest parity and legacy duplicate decision boundary closeout."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.ops.double_play.specialists import evaluate_double_play
from trading.master_v2.canonical_core_runtime_integration_bridge_v0 import (
    INTEGRATION_STATUS_BOUND_NOT_ACTIVATED,
    CanonicalCoreRuntimeIntegrationInputV0,
    build_integrated_offline_replay_input_from_harness_v0,
    run_canonical_core_runtime_integration_bridge_v0,
    serialize_canonical_decision_evidence_for_parity,
)
from trading.master_v2.evaluate_double_play_authority_boundary_v0 import (
    LEGACY_DUPLICATE_DECISION_PATH_AUTHORITY,
    OFFLINE_SCENARIO_REPLAY_AUTHORITY,
    OFFLINE_SCENARIO_REPLAY_CALLABLE,
    OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY,
    OPS_EVALUATE_DOUBLE_PLAY_CALLABLE,
    LegacyDuplicateDecisionPathSystemEvidenceBlockedError,
    assert_legacy_duplicate_decision_path_blocks_system_economic_evidence_v0,
    build_slice_4_legacy_boundary_status_fields_v0,
    classify_offline_scenario_replay_authority,
    classify_ops_evaluate_double_play_authority,
    declare_legacy_duplicate_decision_path_v0,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.legacy_runtime_entrypoint_guard_v0 import (
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    build_slice_d_status_fields_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_PATH_AUTHORITY,
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE,
    OfflineDoublePlayScenarioReplayInputV0,
    SYNTHETIC_FUTURES_INSTRUMENT,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
)
from tests.trading.master_v2.test_canonical_replay_input_builder_ssot_contract_v1 import (
    assert_exactly_one_authorized_src_wide_productive_direct_replay_input_constructor,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
OWNER_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
BRIDGE_MODULE = REPO_ROOT / "src/trading/master_v2/canonical_core_runtime_integration_bridge_v0.py"
MV2_MODULE = REPO_ROOT / "src/backtest/mv2_research_wiring_v1.py"
SCENARIO_MODULE = REPO_ROOT / "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
OPS_SPECIALISTS_MODULE = REPO_ROOT / "src/ops/double_play/specialists.py"
LEGACY_GUARD_MODULE = REPO_ROOT / "src/trading/master_v2/legacy_runtime_entrypoint_guard_v0.py"
MASTER_V2_ROOT = REPO_ROOT / "src/trading/master_v2"

_PUBLIC_BUILDER = "build_integrated_offline_replay_input_v1"
_ORCHESTRATOR = "run_integrated_offline_trading_logic_replay_v1"
_INPUT_TYPE = "IntegratedOfflineReplayInputV1"

_FORBIDDEN_PARTIAL_DECISION_CALLS = frozenset(
    {
        "evaluate_directional_assessment_v1",
        "evaluate_survival_assessment_v1",
        "evaluate_suitability_binding_v1",
        "evaluate_double_play_composition_matrix_v1",
        "evaluate_double_play_entry_exit_policy_v0",
        "generate_deterministic_scope_event",
    }
)


def _parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def _call_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            names.add(func.id)
        elif isinstance(func, ast.Attribute):
            names.add(func.attr)
    return names


def _imported_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[-1])
    return names


def _direct_input_constructions(tree: ast.AST) -> list[ast.Call]:
    hits: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == _INPUT_TYPE:
                hits.append(node)
            elif isinstance(func, ast.Attribute) and func.attr == _INPUT_TYPE:
                hits.append(node)
    return hits


def _harness_input() -> CanonicalCoreRuntimeIntegrationInputV0:
    return CanonicalCoreRuntimeIntegrationInputV0(
        run_id="slice4-parity-fixture",
        harness_instrument="PF_ETHUSD",
        market_type="futures",
    )


def test_backtest_and_runtime_bridge_use_same_canonical_builder() -> None:
    for path in (MV2_MODULE, BRIDGE_MODULE):
        tree = _parse(path)
        imported = _imported_names(tree)
        calls = _call_names(tree)
        assert _PUBLIC_BUILDER in imported
        assert _PUBLIC_BUILDER in calls
        assert _direct_input_constructions(tree) == []


def test_backtest_and_runtime_bridge_use_same_total_decision_owner() -> None:
    for path in (MV2_MODULE, BRIDGE_MODULE):
        tree = _parse(path)
        imported = _imported_names(tree)
        calls = _call_names(tree)
        assert _ORCHESTRATOR in imported
        assert _ORCHESTRATOR in calls


def test_identical_normalized_fixture_produces_identical_decision_evidence() -> None:
    harness = _harness_input()
    normalized, errors = build_integrated_offline_replay_input_from_harness_v0(harness)
    assert errors == ()
    assert normalized is not None

    # Backtest/MV2 consumption path once the fixture is normalized: total decision owner only.
    backtest_path = run_integrated_offline_trading_logic_replay_v1(normalized)
    bridge = run_canonical_core_runtime_integration_bridge_v0(harness)

    assert bridge.canonical_core_consumed is True
    assert bridge.replay_owner == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    assert bridge.decision_outcome == backtest_path.evidence.decision_outcome
    assert bridge.decision_semantic_digest == backtest_path.evidence.semantic_digest
    assert bridge.decision_semantic_digest
    assert serialize_canonical_decision_evidence_for_parity(backtest_path) == (
        serialize_canonical_decision_evidence_for_parity(
            run_integrated_offline_trading_logic_replay_v1(normalized)
        )
    )


def test_semantic_digest_matches_for_identical_normalized_fixture() -> None:
    harness = _harness_input()
    normalized, errors = build_integrated_offline_replay_input_from_harness_v0(harness)
    assert errors == ()
    assert normalized is not None
    backtest_path = run_integrated_offline_trading_logic_replay_v1(normalized)
    bridge = run_canonical_core_runtime_integration_bridge_v0(harness)
    assert bridge.decision_semantic_digest == backtest_path.evidence.semantic_digest
    assert backtest_path.evidence.instrument_id == normalized.instrument_id
    assert backtest_path.evidence.trading_epoch == normalized.trading_epoch
    assert tuple(normalized.component_versions.items())


def test_runtime_bridge_remains_bound_not_activated() -> None:
    result = run_canonical_core_runtime_integration_bridge_v0(_harness_input())
    assert result.integration_status == INTEGRATION_STATUS_BOUND_NOT_ACTIVATED
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "BOUND_NOT_ACTIVATED"
    fields = build_slice_d_status_fields_v0()
    assert fields["CANONICAL_RUNTIME_ENTRYPOINT_STATUS"] == "BOUND_NOT_ACTIVATED"


def test_runtime_bridge_has_zero_authority_and_order_effect() -> None:
    result = run_canonical_core_runtime_integration_bridge_v0(_harness_input())
    assert result.authority_effect == "NONE"
    assert result.runtime_effect == "NONE"
    assert result.order_effect == "NONE"
    assert result.execution_eligible is False
    assert result.legacy_decision_authority_active is False
    assert result.dual_authority_possible is False
    assert result.adapter_submission is False
    assert result.credentials_required is False


def test_runtime_bridge_does_not_duplicate_partial_decision_components() -> None:
    source = BRIDGE_MODULE.read_text(encoding="utf-8")
    for name in _FORBIDDEN_PARTIAL_DECISION_CALLS:
        assert name not in source
    assert _ORCHESTRATOR in source
    assert _PUBLIC_BUILDER in source


def test_offline_scenario_replay_is_non_authoritative() -> None:
    assert classify_offline_scenario_replay_authority() == "LEGACY_NON_AUTHORITATIVE"
    assert OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_PATH_AUTHORITY == OFFLINE_SCENARIO_REPLAY_AUTHORITY
    assert OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE is False
    marker = declare_legacy_duplicate_decision_path_v0(
        path_id=OFFLINE_SCENARIO_REPLAY_CALLABLE,
        system_economic_evidence_requested=False,
    )
    assert marker == LEGACY_DUPLICATE_DECISION_PATH_AUTHORITY
    result = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
            ticks=build_default_bull_bear_bull_scenario_ticks()[:3],
        )
    )
    assert result.replay_pass is True or result.fail_reasons is not None


def test_ops_evaluate_double_play_is_non_authoritative() -> None:
    assert classify_ops_evaluate_double_play_authority() == "LEGACY_NON_AUTHORITATIVE"
    decision = evaluate_double_play(context={})
    assert decision.details["path_authority"] == OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY
    assert decision.details["system_economic_evidence_admissible"] is False


def test_legacy_paths_cannot_produce_system_economic_evidence() -> None:
    with pytest.raises(
        LegacyDuplicateDecisionPathSystemEvidenceBlockedError,
        match="legacy_duplicate_decision_path_system_economic_evidence_blocked",
    ):
        assert_legacy_duplicate_decision_path_blocks_system_economic_evidence_v0(
            path_id=OFFLINE_SCENARIO_REPLAY_CALLABLE,
            system_economic_evidence_requested=True,
        )
    with pytest.raises(
        LegacyDuplicateDecisionPathSystemEvidenceBlockedError,
        match="legacy_duplicate_decision_path_system_economic_evidence_blocked",
    ):
        evaluate_double_play(context={"system_economic_evidence_requested": True})
    with pytest.raises(
        LegacyDuplicateDecisionPathSystemEvidenceBlockedError,
        match="legacy_duplicate_decision_path_system_economic_evidence_blocked",
    ):
        run_offline_double_play_scenario_replay_v0(
            OfflineDoublePlayScenarioReplayInputV0(
                selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
                ticks=build_default_bull_bear_bull_scenario_ticks()[:1],
            ),
            system_economic_evidence_requested=True,
        )


def test_productive_direct_replay_input_constructor_count_remains_one() -> None:
    # Reuse src-wide SSOT authority boundary (no divergent fixed-file allowlist).
    sole = assert_exactly_one_authorized_src_wide_productive_direct_replay_input_constructor()
    assert (
        sole.relative_path == "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
    )
    assert sole.enclosing_function == _PUBLIC_BUILDER
    owner_tree = _parse(OWNER_MODULE)
    assert len(_direct_input_constructions(owner_tree)) == 1
    for path in (MV2_MODULE, BRIDGE_MODULE):
        assert _direct_input_constructions(_parse(path)) == []


def test_classic_engine_decision_authority_bypass_count_remains_zero() -> None:
    """Slice-3 invariant: classic callers still guard; no new bypass introduced."""
    engine = (REPO_ROOT / "src/backtest/engine.py").read_text(encoding="utf-8")
    assert "declare_legacy_raw_signal_research_path_v1" in engine
    assert "LEGACY_NON_AUTHORITATIVE" in engine or "RAW_SIGNAL_RESEARCH" in engine
    tree = _parse(REPO_ROOT / "src/backtest/engine.py")
    imported = _imported_names(tree)
    assert _ORCHESTRATOR not in imported
    assert "evaluate_suitability_binding_v1" not in imported
    calls = _call_names(tree)
    assert "declare_legacy_raw_signal_research_path_v1" in calls


def test_legacy_runtime_guard_unchanged_blocking() -> None:
    text = LEGACY_GUARD_MODULE.read_text(encoding="utf-8")
    assert 'CANONICAL_RUNTIME_ENTRYPOINT_STATUS = "BOUND_NOT_ACTIVATED"' in text
    fields = build_slice_d_status_fields_v0()
    assert fields["LEGACY_RUNTIME_DECISION_AUTHORITY"] == "false"
    assert fields["LEGACY_RUNTIME_ORDER_EFFECT_POSSIBLE"] == "false"
    assert fields["CANONICAL_RUNTIME_ENTRYPOINT_STATUS"] == "BOUND_NOT_ACTIVATED"


def test_master_v2_still_does_not_import_backtest_signal_types() -> None:
    forbidden = {"StrategySignalBindingResultV1", "StrategySignalProvenanceV1"}
    for path in MASTER_V2_ROOT.rglob("*.py"):
        leaked = _imported_names(_parse(path)) & forbidden
        assert not leaked, f"{path.relative_to(REPO_ROOT)} imports {sorted(leaked)}"


def test_slice_4_legacy_boundary_status_fields() -> None:
    fields = build_slice_4_legacy_boundary_status_fields_v0()
    assert fields["OFFLINE_SCENARIO_REPLAY_AUTHORITY"] == "LEGACY_NON_AUTHORITATIVE"
    assert fields["OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY"] == "LEGACY_NON_AUTHORITATIVE"
    assert fields["LEGACY_SYSTEM_ECONOMIC_EVIDENCE_BLOCKED"] == "true"
    assert fields["CANONICAL_TOTAL_DECISION_OWNER"].endswith(
        "integrated_offline_trading_logic_replay_v1"
    )


def test_legacy_path_modules_declare_non_authoritative_markers() -> None:
    scenario_text = SCENARIO_MODULE.read_text(encoding="utf-8")
    specialists_text = OPS_SPECIALISTS_MODULE.read_text(encoding="utf-8")
    assert "LEGACY_NON_AUTHORITATIVE" in scenario_text
    assert "declare_legacy_duplicate_decision_path_v0" in scenario_text
    assert "declare_legacy_duplicate_decision_path_v0" in specialists_text
    assert OPS_EVALUATE_DOUBLE_PLAY_CALLABLE
