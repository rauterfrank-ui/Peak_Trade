"""Reconciliation / Unknown Outcome binding parity: integrated vs scenario replay (offline only)."""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
    ExistingPositionSide,
    PositionState,
    ReconciliationState,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    assert_reconciliation_unknown_outcome_non_authority_boundary_v0,
    assert_scenario_replay_zero_order_boundary_v0,
    canonical_owner_refs_v0,
    extract_integrated_parity_envelope_v0,
    extract_scenario_replay_tick_reconciliation_unknown_outcome_envelope_v0,
    scan_changed_paths_for_forbidden_runtime_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    OfflineDoublePlayScenarioReplayInputV0,
    SYNTHETIC_FUTURES_INSTRUMENT,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
)
from trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0 import (
    ENTRY_EXIT_POLICY_OWNER,
    RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE,
    RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    RUNTIME_STATE_RECONCILIATION_OWNER,
    ReconciliationUnknownOutcomeOfflineReplayContextV0,
    bind_reconciliation_unknown_outcome_offline_replay_evidence_v0,
    evaluate_offline_reconciliation_unknown_outcome_boundary_v0,
    evaluate_scenario_reconciliation_unknown_outcome_v0,
    reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0,
    system_economic_evidence_admissible_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run

REPO_ROOT = Path(__file__).resolve().parents[3]
_INSTRUMENT = SYNTHETIC_FUTURES_INSTRUMENT
_EPOCH = 48
_CONTEXT = "reconciliation-unknown-outcome-offline-replay-binding-parity-v0"

_SLICE_CHANGED_FILES = (
    "src/trading/master_v2/reconciliation_unknown_outcome_offline_replay_binding_adapter_v0.py",
    "src/trading/master_v2/canonical_trading_decision_evidence_v1.py",
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_v0.py",
    "tests/trading/master_v2/test_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_contract_v0.py",
)

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/reconciliation_unknown_outcome_offline_replay_binding_adapter_v0.py",
    REPO_ROOT
    / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    REPO_ROOT
    / "scripts/ops/run_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_contract_v0.py",
)

ALLOWED_SLICE_CHANGED_PATH_PREFIXES = _SLICE_CHANGED_FILES


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


def _base_evidence(*, decision_outcome: str = DecisionOutcome.OBSERVE.value):
    return build_scenario_tick_decision_evidence_v0(
        decision_id=f"{_CONTEXT}-decision",
        replay_id=f"{_CONTEXT}-replay",
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        composition_result_id=f"{_CONTEXT}-composition",
        entry_exit_policy_ref=f"{_CONTEXT}-policy",
        selected_side="long",
        decision_outcome=decision_outcome,
        reason_codes=("PASS",),
        decision_precedence_trace=("observe",),
        config_digest="config",
        implementation_digest="impl",
    )


def test_owner_constants_and_canonical_reuse_v0() -> None:
    refs = canonical_owner_refs_v0()
    assert refs["runtime_state_reconciliation"] == RUNTIME_STATE_RECONCILIATION_OWNER
    assert refs["reconciliation_entry_exit_policy"] == ENTRY_EXIT_POLICY_OWNER
    assert (
        refs["reconciliation_unknown_outcome_offline_replay_binding_adapter"]
        == RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
    )
    assert refs["scenario_replay"] == OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER


def test_forbidden_runtime_paths_guard_v0() -> None:
    ok, violations = scan_changed_paths_for_forbidden_runtime_v0(
        ALLOWED_SLICE_CHANGED_PATH_PREFIXES
    )
    assert ok is True
    assert violations == ()


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
            "live.orders",
            "risk_layer.kill_switch.core",
        }
    )
    for path in _FORBIDDEN_IMPORT_SCAN_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"


def test_integrated_replay_reconciliation_unknown_outcome_bound_v0() -> None:
    integrated = _run(
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    assert (
        integrated.evidence.reconciliation_unknown_outcome_effect
        == RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE
    )
    assert integrated.evidence.reconciliation_unknown_outcome_ref
    env = extract_integrated_parity_envelope_v0(integrated)
    assert_reconciliation_unknown_outcome_non_authority_boundary_v0(env)


def test_submission_unknown_blocks_new_exposure_offline_evidence_v0() -> None:
    evidence = _base_evidence(decision_outcome=DecisionOutcome.ENTER_LONG.value)
    binding = bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
        evidence,
        context=ReconciliationUnknownOutcomeOfflineReplayContextV0(
            position_state=PositionState.SUBMISSION_UNKNOWN,
        ),
    )
    assert binding.boundary.submission_unknown_blocks_new_exposure is True
    assert "submission_unknown_blocks_new_exposure" in binding.boundary.hard_block_reasons
    assert reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0(binding)


def test_unresolved_reduce_blocks_opposite_side_entry_offline_evidence_v0() -> None:
    evidence = _base_evidence(decision_outcome=DecisionOutcome.ENTER_SHORT.value)
    binding = bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
        evidence,
        context=ReconciliationUnknownOutcomeOfflineReplayContextV0(
            position_state=PositionState.REDUCING_PARTIAL,
            existing_position_side=ExistingPositionSide.LONG,
        ),
    )
    assert binding.boundary.unresolved_reduce_blocks_opposite_side is True
    assert "unresolved_reduce_blocks_opposite_side_entry" in binding.boundary.hard_block_reasons


def test_reconciliation_required_maps_to_reconcile_only_offline_evidence_v0() -> None:
    evidence = _base_evidence(decision_outcome=DecisionOutcome.ENTER_LONG.value)
    binding = bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
        evidence,
        context=ReconciliationUnknownOutcomeOfflineReplayContextV0(
            reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED,
        ),
    )
    assert binding.boundary.reconciliation_required_maps_to_reconcile_only is True
    assert "reconciliation_required_blocks_new_exposure" in binding.boundary.hard_block_reasons


def test_reconciled_flat_required_before_opposite_side_offline_evidence_v0() -> None:
    evidence = _base_evidence(decision_outcome=DecisionOutcome.ENTER_SHORT.value)
    binding = bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
        evidence,
        context=ReconciliationUnknownOutcomeOfflineReplayContextV0(
            position_state=PositionState.EXIT_PENDING,
            existing_position_side=ExistingPositionSide.LONG,
        ),
    )
    assert binding.boundary.reconciled_flat_required_before_opposite_side is True


def test_unknown_outcome_never_auto_resubmits_offline_evidence_v0() -> None:
    evidence = _base_evidence(decision_outcome=DecisionOutcome.ENTER_LONG.value)
    binding = bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
        evidence,
        context=ReconciliationUnknownOutcomeOfflineReplayContextV0(
            position_state=PositionState.SUBMISSION_UNKNOWN,
        ),
    )
    assert binding.boundary.unknown_outcome_never_auto_resubmits is True
    assert binding.boundary.no_auto_resubmit is True
    assert "unknown_outcome_no_auto_resubmit" in binding.boundary.hard_block_reasons


def test_venue_flat_alone_insufficient_when_snapshots_unresolved_offline_evidence_v0() -> None:
    evidence = _base_evidence(decision_outcome=DecisionOutcome.ENTER_LONG.value)
    binding = bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
        evidence,
        context=ReconciliationUnknownOutcomeOfflineReplayContextV0(
            position_state=PositionState.RECONCILIATION_REQUIRED,
            venue_flat=True,
            intent_snapshot_unresolved=True,
            order_snapshot_unresolved=True,
        ),
    )
    assert binding.boundary.venue_flat_alone_insufficient is True
    assert "venue_flat_alone_insufficient" in binding.boundary.hard_block_reasons


def test_adapter_issues_no_runtime_permission_or_order_authority_v0() -> None:
    boundary = evaluate_offline_reconciliation_unknown_outcome_boundary_v0(
        ReconciliationUnknownOutcomeOfflineReplayContextV0(
            position_state=PositionState.SUBMISSION_UNKNOWN,
        ),
    )
    assert boundary.runtime_authority_effect == "NONE"
    assert boundary.order_effect == "NONE"
    assert boundary.credential_effect == "NONE"
    evidence = _base_evidence()
    binding = bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
        evidence,
        context=ReconciliationUnknownOutcomeOfflineReplayContextV0(),
    )
    assert not binding.evidence.execution_eligible
    assert not binding.evidence.adapter_compatible
    assert binding.evidence.order_effect == "NONE"
    assert not system_economic_evidence_admissible_v0(binding)


def test_scenario_replay_tick_reconciliation_unknown_outcome_binding_v0() -> None:
    result = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=_INSTRUMENT,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            source_revision="reconciliation-unknown-outcome-binding-parity-v0",
        )
    )
    assert result.replay_pass, result.fail_reasons
    assert_scenario_replay_zero_order_boundary_v0(result)

    bound_ticks = 0
    for tick in result.tick_records:
        env = extract_scenario_replay_tick_reconciliation_unknown_outcome_envelope_v0(tick)
        assert_reconciliation_unknown_outcome_non_authority_boundary_v0(env)
        if (
            tick.reconciliation_unknown_outcome_effect
            == RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE
        ):
            bound_ticks += 1
            assert tick.reconciliation_unknown_outcome_ref
    assert bound_ticks == len(result.tick_records)


def test_scenario_fixture_reconciliation_unknown_outcome_binding_v0() -> None:
    evidence = _base_evidence(decision_outcome=DecisionOutcome.ENTER_LONG.value)
    binding = evaluate_scenario_reconciliation_unknown_outcome_v0(
        evidence,
        context=ReconciliationUnknownOutcomeOfflineReplayContextV0(),
    )
    assert binding.binding_applied is True
    assert (
        binding.reconciliation_unknown_outcome_effect
        == RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE
    )
    assert binding.reconciliation_unknown_outcome_ref
    assert reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0(binding)


def test_integrated_submission_unknown_reconcile_only_parity_v0() -> None:
    result = _run(position_state=PositionState.SUBMISSION_UNKNOWN)
    assert result.evidence.decision_outcome == DecisionOutcome.RECONCILE_ONLY.value
    assert result.evidence.reconciliation_unknown_outcome_ref
    assert (
        result.evidence.reconciliation_unknown_outcome_effect
        == RECONCILIATION_UNKNOWN_OUTCOME_EFFECT_BOUND_OFFLINE
    )


def test_pr4954_safety_kernel_binding_suite_still_passes_v0() -> None:
    from tests.trading.master_v2 import (
        test_safety_kernel_offline_replay_binding_parity_rewire_contract_v0 as pr4954,
    )

    pr4954.test_owner_constants_and_canonical_reuse_v0()
    pr4954.test_unknown_outcome_never_auto_resubmits_offline_evidence_v0()
    pr4954.test_scenario_fixture_safety_kernel_binding_v0()


def test_prometheus_client_importable_v0() -> None:
    assert importlib.util.find_spec("prometheus_client") is not None
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import prometheus_client; print('PROMETHEUS_CLIENT_IMPORTABLE=true')",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "PROMETHEUS_CLIENT_IMPORTABLE=true" in proc.stdout
