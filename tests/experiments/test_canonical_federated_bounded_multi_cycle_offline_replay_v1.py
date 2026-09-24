"""G4/G5 tests — federated M8 multi-cycle offline replay."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.experiments.canonical_federated_bounded_multi_cycle_offline_replay_v1 import (
    MINIMUM_CYCLE_COUNT,
    M4_PLANE_EXECUTION,
    REPLAY_STATUS_COMPLETE,
    REPLAY_STATUS_REJECTED_CYCLE_ORDER,
    FederatedDeterministicMultiCycleOfflineReplayRequestV1,
    FederatedOfflineMultiCycleReplayError,
    FederatedOfflineReplayCycleInputV1,
    run_federated_deterministic_multi_cycle_offline_replay_v1,
)
from src.experiments.canonical_federated_m5_m6_return_join_v1 import (
    FederatedM5M6ReturnJoinRequestV1,
    perform_federated_m5_m6_return_join_v1,
)
from src.experiments.canonical_federated_surface_optimization_experiment_evidence_projection_v1 import (
    bind_f1_surface_execution_projection_request_v1,
    build_federated_surface_optimization_experiment_evidence_projection_v1,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_SURFACE_ID,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    OptimizableEnvelopeResolveRequestV1,
    resolve_optimizable_envelope_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]
REPLAY_MODULE = (
    REPO_ROOT
    / "src"
    / "experiments"
    / "canonical_federated_bounded_multi_cycle_offline_replay_v1.py"
)


def _envelope_for(surface_id: str) -> tuple[str, str]:
    resolution = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=surface_id)
    )
    assert resolution["resolution"] == RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION
    return (
        str(resolution["envelope_identity"]),
        str(resolution["result_digest"]),
    )


def _federated_m5(*, execution_id: str) -> dict:
    env_id, env_digest = _envelope_for(F1_SURFACE_ID)
    native_digest = compute_content_sha256({"native": execution_id})
    f1_result = {
        "execution_id": execution_id,
        "repository_sha": "e" * 64,
        "candidate_domain_digest": compute_content_sha256({"domain": execution_id}),
        "input_evidence_manifest_digest": compute_content_sha256({"manifest": execution_id}),
    }
    req = bind_f1_surface_execution_projection_request_v1(
        f1_result,
        surface_native_evidence_ref=f"fixture/{execution_id}",
        surface_native_evidence_digest=native_digest,
        envelope_identity=env_id,
        envelope_resolution_digest=env_digest,
    )
    return dict(build_federated_surface_optimization_experiment_evidence_projection_v1(req))


def _two_cycle_request() -> FederatedDeterministicMultiCycleOfflineReplayRequestV1:
    ev0 = _federated_m5(execution_id="f1.cycle0.v1")
    ev1 = _federated_m5(execution_id="f1.cycle1.v1")
    return FederatedDeterministicMultiCycleOfflineReplayRequestV1(
        cycles=(
            FederatedOfflineReplayCycleInputV1(
                cycle_index=0,
                federated_optimization_experiment_evidence=ev0,
                replay_seed=7,
            ),
            FederatedOfflineReplayCycleInputV1(
                cycle_index=1,
                federated_optimization_experiment_evidence=ev1,
                replay_seed=7,
            ),
        )
    )


def test_replay_module_does_not_import_m4_plane() -> None:
    tree = ast.parse(REPLAY_MODULE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert "src.experiments.canonical_optimization_universe_experiment_plane_v1" not in imported


def test_two_cycle_federated_replay_closed_and_deterministic() -> None:
    first = run_federated_deterministic_multi_cycle_offline_replay_v1(_two_cycle_request())
    second = run_federated_deterministic_multi_cycle_offline_replay_v1(_two_cycle_request())
    assert first["status"] == REPLAY_STATUS_COMPLETE
    assert first["multi_cycle_loop_closed"] is True
    assert first["cycle_count"] == MINIMUM_CYCLE_COUNT
    assert first["m4_plane_execution"] is False
    assert M4_PLANE_EXECUTION is False
    assert first["replay_identity"] == second["replay_identity"]
    assert first["result_digest"] == second["result_digest"]
    cycle0 = first["cycles"][0]
    cycle1 = first["cycles"][1]
    assert cycle0["m4_plane_execution"] is False
    assert (
        cycle1["cycle_body"]["prior_feedback_decision_identity"]
        == cycle0["cycle_body"]["feedback_decision_identity"]
    )
    assert cycle1["cycle_body"]["cycle_n_plus_1_input_semantics"] is not None


def test_rejects_m4_plane_execution_flag() -> None:
    with pytest.raises(FederatedOfflineMultiCycleReplayError, match="M4_PLANE_EXECUTION_FORBIDDEN"):
        run_federated_deterministic_multi_cycle_offline_replay_v1(
            FederatedDeterministicMultiCycleOfflineReplayRequestV1(
                cycles=_two_cycle_request().cycles,
                requested_m4_plane_execution=True,
            )
        )


def test_rejects_out_of_order_cycle_indices() -> None:
    ev0 = _federated_m5(execution_id="f1.badorder0.v1")
    ev1 = _federated_m5(execution_id="f1.badorder1.v1")
    result = run_federated_deterministic_multi_cycle_offline_replay_v1(
        FederatedDeterministicMultiCycleOfflineReplayRequestV1(
            cycles=(
                FederatedOfflineReplayCycleInputV1(
                    cycle_index=0,
                    federated_optimization_experiment_evidence=ev0,
                    replay_seed=1,
                ),
                FederatedOfflineReplayCycleInputV1(
                    cycle_index=2,
                    federated_optimization_experiment_evidence=ev1,
                    replay_seed=1,
                ),
            )
        )
    )
    assert result["status"] == REPLAY_STATUS_REJECTED_CYCLE_ORDER


def test_duplicate_join_key_across_cycles_fails_on_second_cycle() -> None:
    ev = _federated_m5(execution_id="f1.duplicate.v1")
    request = FederatedDeterministicMultiCycleOfflineReplayRequestV1(
        cycles=(
            FederatedOfflineReplayCycleInputV1(
                cycle_index=0,
                federated_optimization_experiment_evidence=ev,
                replay_seed=3,
            ),
            FederatedOfflineReplayCycleInputV1(
                cycle_index=1,
                federated_optimization_experiment_evidence=ev,
                replay_seed=3,
            ),
        )
    )
    with pytest.raises(FederatedOfflineMultiCycleReplayError, match="RETURN_JOIN_NOT_COMPLETE"):
        run_federated_deterministic_multi_cycle_offline_replay_v1(request)
