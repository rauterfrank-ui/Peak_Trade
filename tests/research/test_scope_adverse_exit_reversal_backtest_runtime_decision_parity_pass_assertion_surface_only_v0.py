from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from scripts.research.adverse_exit_and_reversal_preparation_backtest_parity_narrow_rewire_v0 import (
    BACKTEST_CONSUMER,
    INTEGRATED_REPLAY_PATH,
    REVERSAL_ADAPTER_PATH,
    SCOPE_ADAPTER_PATH,
    evaluate_adverse_exit_integrated_backtest_parity_fixtures_v0,
    evaluate_reversal_preparation_integrated_backtest_parity_fixtures_v0,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    CanonicalScopeEventType,
    ScopeDirectionState,
)
from trading.master_v2.directional_assessment_v1 import mirror_price_path_for_short
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionStatus,
    PositionManagementContext,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
    ExitClass,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    resolve_integrated_reversal_preparation_entry_exit_binding_v0,
    resolve_integrated_scope_adverse_exit_signal_v0,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    evaluate_reversal_preparation_matrix_v0,
)
from trading.master_v2.reversal_preparation_scenario_binding_adapter_v0 import (
    REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER,
    reversal_preparation_decision_is_reduce_only_preparation_v0,
)
from trading.master_v2.scope_event_generator_scenario_binding_adapter_v0 import (
    CANONICAL_SCOPE_EVENT_GENERATOR_OWNER,
    SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER,
    derive_scope_adverse_exit_signal_v0,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _market_context,
    _replay_input,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "docs/research/scope_adverse_exit_reversal_backtest_runtime_decision_parity_pass_assertion_surface_only_v0.json"
)
ASSESSMENT_CONTRACT = (
    ROOT
    / "docs/research/adverse_exit_and_reversal_preparation_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
NARROW_REWIRE_CONTRACT = (
    ROOT
    / "docs/research/adverse_exit_and_reversal_preparation_backtest_parity_narrow_rewire_v0.json"
)
BACKTEST_WIRING = ROOT / BACKTEST_CONSUMER
INTEGRATED_REPLAY = ROOT / INTEGRATED_REPLAY_PATH


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _long_adverse_replay_input():
    return _replay_input(
        canonical_market_context=_market_context(mark_price=100.0),
        price_path=(100.0, 96.0),
        current_price=96.0,
        scope_direction_state=ScopeDirectionState.LONG,
        position_management_context=PositionManagementContext.LONG_POSITION,
        existing_position_side=ExistingPositionSide.LONG,
        position_state=PositionState.OPEN_FULL,
        side_state=SideState.LONG_ACTIVE,
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        venue_flat=False,
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        up_distance=2.0,
        adverse_exit_distance=2.0,
        reversal_distance=4.0,
    )


def test_contract_declares_surface_only_parity_pass() -> None:
    data = load_contract()
    assert (
        data["assertion_id"]
        == "SCOPE_ADVERSE_EXIT_REVERSAL_BACKTEST_RUNTIME_DECISION_PARITY_PASS_ASSERTION_SURFACE_ONLY_V0"
    )
    assert data["assertion_scope"] == "SCOPE_ADVERSE_EXIT_AND_REVERSAL_PREPARATION_SURFACE_ONLY"
    assert data["ADVERSE_SCOPE_EXIT_BACKTEST_PARITY_STATUS"] == "WIRED"
    assert data["REVERSAL_PREPARATION_BACKTEST_PARITY_STATUS"] == "WIRED"
    assert data["SCOPE_EXIT_REVERSAL_BACKTEST_PARITY_PASS"] is True
    assert data["SCOPE_EXIT_REVERSAL_BACKTEST_RUNTIME_DECISION_PARITY_PASS"] is True
    assert (
        data["BACKTEST_RUNTIME_DECISION_PARITY_PASS_ASSERTION_SCOPE"]
        == "SCOPE_ADVERSE_EXIT_AND_REVERSAL_PREPARATION_SURFACE_ONLY"
    )
    assert (
        data["verdict"]
        == "PASS_SCOPE_ADVERSE_EXIT_REVERSAL_BACKTEST_RUNTIME_DECISION_PARITY_PASS_ASSERTION_SURFACE_ONLY_V0"
    )


def test_contract_preserves_whole_system_fail_closed_flags() -> None:
    data = load_contract()
    assert data["BACKTEST_RUNTIME_DECISION_PARITY_PASS"] is False
    assert data["FULL_CANONICAL_CHAIN_WIRED"] is False
    assert data["SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE"] is False
    assert data["RUNTIME_REWIRE_ADMISSIBLE"] is False
    assert data["authority_effect"] == "NONE"
    assert data["runtime_effect"] == "NONE"
    assert data["futures_only"] is True
    assert data["bitcoin_direction_allowed"] is False


def test_contract_binds_required_evidence_references() -> None:
    data = load_contract()
    assessment = json.loads(ASSESSMENT_CONTRACT.read_text(encoding="utf-8"))
    narrow_rewire = json.loads(NARROW_REWIRE_CONTRACT.read_text(encoding="utf-8"))

    assert data["canonical_owner"] == INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER
    assert data["direct_reference_count"] == 16
    assert data["direct_reference_count"] == assessment["backtest_direct_reference_count"]
    assert data["assessment_source_pr"] == 5060
    assert data["narrow_rewire_review_source_pr"] == 5061
    assert data["narrow_rewire_classification"] == "NARROW_INTEGRATED_CONSUMER_BINDING"
    assert data["narrow_rewire_classification"] == narrow_rewire["narrow_rewire_decision"]["mode"]
    assert (ROOT / data["assessment_contract_ref"]).is_file()
    assert (ROOT / data["narrow_rewire_review_contract_ref"]).is_file()
    assert all((ROOT / path).is_file() for path in data["backtest_consumer_paths"])
    assert all((ROOT / ref).is_file() for ref in data["deterministic_test_refs"])


def test_contract_decision_precedence_flags() -> None:
    data = load_contract()
    precedence = data["decision_precedence_evidence"]
    assert precedence["exit_before_opposite_side"] is True
    assert precedence["opposite_side_requires_reconciled_flat"] is True
    assert precedence["position_flip_allowed"] is False
    assert precedence["reduce_only_exit_preserved"] is True


def test_source_evidence_review_metadata_recorded_without_ci_archive_dependency() -> None:
    data = load_contract()
    narrow_rewire = json.loads(NARROW_REWIRE_CONTRACT.read_text(encoding="utf-8"))

    assert data["source_manifest_verify_rc"] == 0
    assert narrow_rewire["source_evidence_manifest_verify_rc"] == 0
    assert data["source_evidence_provenance_mode"] == "OPERATOR_DURABLE_ARCHIVE_REVIEW_TIME_ONLY"
    assert len(data["source_evidence_dirs"]) == 2
    assert set(data["source_manifest_digests"]) == {
        Path(evidence_dir).name for evidence_dir in data["source_evidence_dirs"]
    }
    for contract_ref in data["source_evidence_contract_refs"]:
        assert (ROOT / contract_ref).is_file()
    assert data["assessment_contract_ref"] in data["source_evidence_contract_refs"]
    assert data["narrow_rewire_review_contract_ref"] in data["source_evidence_contract_refs"]


def test_implementation_digests_match_origin_main_baseline() -> None:
    data = load_contract()
    for rel_path, expected_digest in data["implementation_digests"].items():
        actual = _sha256_file(ROOT / rel_path)
        assert actual == expected_digest, f"digest drift for {rel_path}"


def test_source_manifest_digests_are_stable_review_metadata() -> None:
    data = load_contract()
    for bundle_key, digest in data["source_manifest_digests"].items():
        assert bundle_key.endswith("Z")
        assert len(digest) == 64
        assert all(char in "0123456789abcdef" for char in digest)
        matching_dir = next(
            evidence_dir
            for evidence_dir in data["source_evidence_dirs"]
            if bundle_key in evidence_dir
        )
        assert matching_dir.endswith(bundle_key)


def test_backtest_consumer_routes_through_canonical_integrated_replay() -> None:
    data = load_contract()
    replay_text = INTEGRATED_REPLAY.read_text(encoding="utf-8")
    backtest_text = BACKTEST_WIRING.read_text(encoding="utf-8")

    assert "resolve_integrated_scope_adverse_exit_signal_v0" in replay_text
    assert "resolve_integrated_reversal_preparation_entry_exit_binding_v0" in replay_text
    assert "run_integrated_offline_trading_logic_replay_v1" in backtest_text
    assert data["backtest_consumer_paths"][0].endswith("mv2_research_wiring_v1.py")
    assert data["canonical_adverse_exit_owner"] == CANONICAL_SCOPE_EVENT_GENERATOR_OWNER
    assert (
        data["canonical_scope_adapter_owner"]
        == SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert (
        data["canonical_reversal_preparation_adapter_owner"]
        == REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert (ROOT / SCOPE_ADAPTER_PATH).is_file()
    assert (ROOT / REVERSAL_ADAPTER_PATH).is_file()


def test_mirrored_adverse_exit_and_reversal_preparation_parity() -> None:
    data = load_contract()
    long_result, short_result = evaluate_adverse_exit_integrated_backtest_parity_fixtures_v0()
    for result in (long_result, short_result):
        assert result.intermediate is not None
        scope = result.intermediate.scope_event
        assert "adverse_exit" in scope.matched_conditions
        assert scope.event_type in (
            CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE,
            CanonicalScopeEventType.DOWNSCOPE_CANDIDATE,
            CanonicalScopeEventType.DOWNSCOPE_CONFIRMED,
        )
        derived = resolve_integrated_scope_adverse_exit_signal_v0(
            scope,
            PolicySignalV0(triggered=False),
        )
        assert derived.triggered is True

    long_decision, short_decision = (
        evaluate_reversal_preparation_integrated_backtest_parity_fixtures_v0()
    )
    for decision in (long_decision, short_decision):
        assert decision.exit_class is ExitClass.REVERSAL_PREPARATION_EXIT
        assert reversal_preparation_decision_is_reduce_only_preparation_v0(decision)

    long_path = (100.0, 96.0)
    short_path = mirror_price_path_for_short(long_path, reference=100.0)
    long_inp = _long_adverse_replay_input()
    short_inp = replace(
        long_inp,
        scope_direction_state=ScopeDirectionState.SHORT,
        position_management_context=PositionManagementContext.SHORT_POSITION,
        existing_position_side=ExistingPositionSide.SHORT,
        side_state=SideState.SHORT_ACTIVE,
        direction_state=EntryExitDirectionState.SHORT_ACTIVE,
        price_path=short_path,
        current_price=float(short_path[-1]),
    )
    long_scope = run_integrated_offline_trading_logic_replay_v1(long_inp).intermediate.scope_event
    short_scope = run_integrated_offline_trading_logic_replay_v1(short_inp).intermediate.scope_event
    assert derive_scope_adverse_exit_signal_v0(long_scope).triggered is True
    assert derive_scope_adverse_exit_signal_v0(short_scope).triggered is True
    assert data["mirrored_behavior_verified"] is True
    assert data["bypass_authority_excluded"] is True


def test_exit_before_opposite_side_and_reconciled_flat_precedence() -> None:
    long_inp = _long_adverse_replay_input()
    matrix = evaluate_reversal_preparation_matrix_v0(
        instrument_id=long_inp.instrument_id,
        trading_epoch=long_inp.trading_epoch,
        context_reference=f"{long_inp.context_reference}-precedence",
    )
    projected, _, _, _ = resolve_integrated_reversal_preparation_entry_exit_binding_v0(
        matrix,
        long_inp,
    )
    assert projected.composition_status is CompositionStatus.REVERSAL_PREPARATION
    replay = run_integrated_offline_trading_logic_replay_v1(long_inp)
    assert replay.intermediate is not None
    adverse_signal = resolve_integrated_scope_adverse_exit_signal_v0(
        replay.intermediate.scope_event,
        PolicySignalV0(triggered=False),
    )
    assert adverse_signal.triggered is True
    assert replay.intermediate.entry_exit_decision.exit_class in (
        ExitClass.ADVERSE_SCOPE_EXIT,
        ExitClass.REVERSAL_PREPARATION_EXIT,
    )
    assert replay.intermediate.entry_exit_decision.decision_outcome not in (
        DecisionOutcome.ENTER_LONG,
        DecisionOutcome.ENTER_SHORT,
    )

    inp = _replay_input(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        side_state=SideState.SHORT_ARMED,
        direction_state=EntryExitDirectionState.SHORT_ARMED,
        reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED,
        venue_flat=False,
        scope_direction_state=ScopeDirectionState.SHORT,
    )
    result = run_integrated_offline_trading_logic_replay_v1(inp)
    assert result.intermediate is not None
    assert result.intermediate.entry_exit_decision.decision_outcome != DecisionOutcome.ENTER_SHORT


def test_position_flip_not_allowed_and_reduce_only_preserved() -> None:
    long_decision, short_decision = (
        evaluate_reversal_preparation_integrated_backtest_parity_fixtures_v0()
    )
    for decision in (long_decision, short_decision):
        assert decision.position_flip_allowed is False
        assert decision.reduce_only is True
        assert reversal_preparation_decision_is_reduce_only_preparation_v0(decision)
        assert decision.decision_outcome not in (
            DecisionOutcome.ENTER_LONG,
            DecisionOutcome.ENTER_SHORT,
        )


def test_no_parallel_ssot_imports_in_integrated_replay_negative() -> None:
    tree = ast.parse(INTEGRATED_REPLAY.read_text(encoding="utf-8"))
    defined_generators = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and "generate_deterministic_scope_event" in node.name
    }
    assert defined_generators == set()
    source = INTEGRATED_REPLAY.read_text(encoding="utf-8")
    assert "class ScopeEventGenerator" not in source


def test_next_parity_surface_is_flat_before_opposite_side_assessment() -> None:
    data = load_contract()
    assert (
        data["next_parity_surface"]
        == "FLAT_BEFORE_OPPOSITE_SIDE_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0"
    )


def test_limitations_and_non_claims_documented() -> None:
    data = load_contract()
    limitations = data["limitations_and_non_claims"]
    assert any("whole-system" in item for item in limitations)
    assert any("FULL_CANONICAL_CHAIN_WIRED" in item for item in limitations)
    assert any("reference count" in item for item in limitations)
