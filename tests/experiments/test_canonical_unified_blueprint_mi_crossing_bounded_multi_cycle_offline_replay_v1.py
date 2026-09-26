"""Tests for Unified Blueprint Phase 10 MI-crossing bounded multi-cycle offline replay."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.experiments.canonical_unified_blueprint_mi_crossing_bounded_multi_cycle_offline_replay_v1 import (
    AUTHORIZED_PRODUCTIVE_SURFACES,
    BOUND_CONTRACT_VERSIONS,
    LEARNING_STATE_MUTATION_PERFORMED,
    META_EVIDENCE_AUTHORITY,
    MINIMUM_CYCLE_COUNT,
    MiCrossingOfflineMultiCycleReplayError,
    MiCrossingOfflineReplayCycleInputV1,
    MiCrossingDeterministicMultiCycleOfflineReplayRequestV1,
    REPLAY_STATUS_COMPLETE,
    REPLAY_STATUS_REJECTED_CYCLE_ORDER,
    REPLAY_STATUS_REJECTED_STALE,
    SEARCH_EXECUTED,
    run_mi_crossing_deterministic_multi_cycle_offline_replay_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_orchestrator_v1 import (
    OfflineForecastScenarioV1,
    OfflineOrchestratorInputV1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state
from tests.learning.test_unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1 import (
    _directional_payload,
    _observation_for_n,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "experiments"
    / "canonical_unified_blueprint_mi_crossing_bounded_multi_cycle_offline_replay_v1.py"
)


def _scenario(*, info_ref: str) -> OfflineForecastScenarioV1:
    obs = _observation_for_n(n_bars=2)
    return OfflineForecastScenarioV1(
        information_set_ref=info_ref,
        forecast_created_at_utc="2026-09-01T12:00:00Z",
        outcome_horizon_end_utc="2026-09-01T14:00:00Z",
        n_bars=2,
        bar_spec_ref=str(obs["bar_spec_ref"]),
        market_state_refs=[f"mi.state.{info_ref}"],
        forecast_model_ref="mi.model.offline.v1",
        probabilistic_payload=_directional_payload(),
        realized_direction="UP",
    )


def _orchestrator_input(tmp_path: Path, *, info_ref: str) -> OfflineOrchestratorInputV1:
    obs = _observation_for_n(n_bars=2)
    legacy_state = _learning_state(tmp_path)
    legacy = export_learning_evidence_from_state_v1(legacy_state)
    return OfflineOrchestratorInputV1(
        scenarios=[_scenario(info_ref=info_ref)],
        evaluation_observations_by_n_bars={2: obs},
        learning_state_record=legacy_state,
        m4_experiment_plane_request=_plane_request(legacy),
        run_mi_enriched_m4_closure=True,
    )


def _two_cycle_request(tmp_path: Path) -> MiCrossingDeterministicMultiCycleOfflineReplayRequestV1:
    return MiCrossingDeterministicMultiCycleOfflineReplayRequestV1(
        cycles=(
            MiCrossingOfflineReplayCycleInputV1(
                cycle_index=0,
                orchestrator_input=_orchestrator_input(tmp_path, info_ref="phase10.cycle0"),
                replay_seed=42,
            ),
            MiCrossingOfflineReplayCycleInputV1(
                cycle_index=1,
                orchestrator_input=_orchestrator_input(tmp_path, info_ref="phase10.cycle1"),
                replay_seed=42,
            ),
        )
    )


def test_two_cycle_mi_crossing_replay_closed_and_deterministic(tmp_path: Path) -> None:
    first = run_mi_crossing_deterministic_multi_cycle_offline_replay_v1(
        _two_cycle_request(tmp_path)
    )
    second = run_mi_crossing_deterministic_multi_cycle_offline_replay_v1(
        _two_cycle_request(tmp_path)
    )
    assert first["status"] == REPLAY_STATUS_COMPLETE
    assert first["multi_cycle_loop_closed"] is True
    assert first["cycle_count"] == MINIMUM_CYCLE_COUNT
    assert first["replay_identity"] == second["replay_identity"]
    assert first["result_digest"] == second["result_digest"]
    assert first["search_executed"] is False
    assert SEARCH_EXECUTED is False
    assert first["learning_state_mutation_performed"] is False
    assert LEARNING_STATE_MUTATION_PERFORMED is False
    assert first["authorized_productive_surfaces"] == 0
    assert first["meta_evidence_authority"] == META_EVIDENCE_AUTHORITY == "NONE"

    cycle0 = first["cycles"][0]
    cycle1 = first["cycles"][1]
    assert cycle0["cycle_index"] == 0
    assert cycle1["cycle_index"] == 1
    assert cycle0["mi_crossing_replay_performed"] is True
    assert cycle0["cycle_body"]["mi_lineage_refs"]["forecast_evidence_id"]
    assert (
        cycle0["cycle_body"]["mi_lineage_refs"]["forecast_evidence_id"]
        != cycle1["cycle_body"]["mi_lineage_refs"]["forecast_evidence_id"]
    )
    assert (
        cycle1["cycle_body"]["prior_feedback_decision_identity"]
        == cycle0["cycle_body"]["feedback_decision_identity"]
    )
    assert cycle1["cycle_body"]["cycle_n_plus_1_input_semantics"] is not None


def test_rejects_stale_contract_version(tmp_path: Path) -> None:
    stale = dict(BOUND_CONTRACT_VERSIONS)
    stale["m10_mi_crossing_replay"] = (
        "canonical_unified_blueprint_mi_crossing_bounded_multi_cycle_offline_replay_v0"
    )
    result = run_mi_crossing_deterministic_multi_cycle_offline_replay_v1(
        MiCrossingDeterministicMultiCycleOfflineReplayRequestV1(
            cycles=_two_cycle_request(tmp_path).cycles,
            expected_contract_versions=stale,
        )
    )
    assert result["status"] == REPLAY_STATUS_REJECTED_STALE


def test_rejects_out_of_order_cycle_indices(tmp_path: Path) -> None:
    orch = _orchestrator_input(tmp_path, info_ref="phase10.oof")
    result = run_mi_crossing_deterministic_multi_cycle_offline_replay_v1(
        MiCrossingDeterministicMultiCycleOfflineReplayRequestV1(
            cycles=(
                MiCrossingOfflineReplayCycleInputV1(1, orch, 42),
                MiCrossingOfflineReplayCycleInputV1(0, orch, 42),
            )
        )
    )
    assert result["status"] == REPLAY_STATUS_REJECTED_CYCLE_ORDER


def test_forbidden_search_execution_request() -> None:
    with pytest.raises(MiCrossingOfflineMultiCycleReplayError):
        run_mi_crossing_deterministic_multi_cycle_offline_replay_v1(
            MiCrossingDeterministicMultiCycleOfflineReplayRequestV1(
                cycles=(),
                requested_search_execution=True,
            )
        )


def test_forbidden_promotion_request() -> None:
    with pytest.raises(MiCrossingOfflineMultiCycleReplayError):
        run_mi_crossing_deterministic_multi_cycle_offline_replay_v1(
            MiCrossingDeterministicMultiCycleOfflineReplayRequestV1(
                cycles=(),
                requested_promotion=True,
            )
        )


def test_forbidden_graph_disjoint() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = {
        "src.governance.promotion_loop.engine",
        "src.execution",
        "src.trading",
        "src.trading.master_v2",
    }
    assert forbidden.isdisjoint(imported)
    assert AUTHORIZED_PRODUCTIVE_SURFACES == 0
