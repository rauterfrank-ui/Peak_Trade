"""G1/G5 tests — federated M5→M6 return join."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.experiments.canonical_federated_m5_m6_return_join_v1 import (
    JOIN_STATUS_COMPLETE,
    JOIN_STATUS_REJECTED_DUPLICATE,
    JOIN_STATUS_REJECTED_FOREIGN,
    JOIN_STATUS_REJECTED_IDENTITY,
    JOIN_STATUS_REJECTED_PLANE,
    FederatedM5M6ReturnJoinError,
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
from src.experiments.canonical_meta_learning_ingest_v1 import (
    INGEST_STATUS_COMPLETE,
    FederatedMetaLearningIngestRequestV1,
    ingest_meta_learning_evidence_from_federated_return_join_v1,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    build_optimization_experiment_evidence_from_plane_v1,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    OptimizableEnvelopeResolveRequestV1,
    resolve_optimizable_envelope_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
    run_optimization_universe_experiment_plane_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state

REPO_ROOT = Path(__file__).resolve().parents[2]
JOIN_MODULE = REPO_ROOT / "src" / "experiments" / "canonical_federated_m5_m6_return_join_v1.py"
DECISION_PATH = (
    REPO_ROOT
    / "config"
    / "governance"
    / "m5_m8_bounded_meta_return_and_replay_completion_v1_decision_v1.json"
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


def _federated_m5(*, execution_id: str = "f1.exec.join.v1") -> dict:
    env_id, env_digest = _envelope_for(F1_SURFACE_ID)
    native_digest = compute_content_sha256({"native": execution_id})
    f1_result = {
        "execution_id": execution_id,
        "repository_sha": "b" * 64,
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


def test_decision_config_m4_forbidden() -> None:
    decision = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    assert decision["m4_plane_re_execution_forbidden"] is True
    assert decision["join_key_field"] == "surface_execution_identity"


def test_join_module_does_not_import_m4_plane() -> None:
    tree = ast.parse(JOIN_MODULE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert "src.experiments.canonical_optimization_universe_experiment_plane_v1" not in imported


def test_federated_join_complete_and_deterministic() -> None:
    evidence = _federated_m5()
    first = perform_federated_m5_m6_return_join_v1(
        FederatedM5M6ReturnJoinRequestV1(optimization_experiment_evidence=evidence)
    )
    second = perform_federated_m5_m6_return_join_v1(
        FederatedM5M6ReturnJoinRequestV1(optimization_experiment_evidence=evidence)
    )
    assert first["status"] == JOIN_STATUS_COMPLETE
    assert first["return_join_identity"] == second["return_join_identity"]
    assert first["plane_identity"] is None
    assert first["m4_re_execution"] is False


def test_m6_ingest_from_federated_join_complete() -> None:
    evidence = _federated_m5()
    join = perform_federated_m5_m6_return_join_v1(
        FederatedM5M6ReturnJoinRequestV1(optimization_experiment_evidence=evidence)
    )
    ingest = ingest_meta_learning_evidence_from_federated_return_join_v1(
        FederatedMetaLearningIngestRequestV1(
            federated_return_join=join,
            optimization_experiment_evidence=evidence,
        )
    )
    assert ingest["status"] == INGEST_STATUS_COMPLETE
    meta = ingest["meta_learning_evidence"]
    assert (
        meta["provenance"]["source_surface_execution_identity"]
        == join["surface_execution_identity"]
    )
    assert meta["provenance"]["source_plane_identity"] is None
    assert meta["provenance"]["m4_plane_execution"] is False


def test_rejects_plane_based_m5_foreign_evidence(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    learning_evidence = export_learning_evidence_from_state_v1(state)
    plane = run_optimization_universe_experiment_plane_v1(_plane_request(learning_evidence))
    assert plane["status"] == PLANE_STATUS_COMPLETE
    plane_evidence = build_optimization_experiment_evidence_from_plane_v1(plane)
    result = perform_federated_m5_m6_return_join_v1(
        FederatedM5M6ReturnJoinRequestV1(optimization_experiment_evidence=plane_evidence)
    )
    assert result["status"] == JOIN_STATUS_REJECTED_PLANE


def test_rejects_duplicate_join_key() -> None:
    evidence = _federated_m5()
    join_key = str(evidence["surface_execution_identity"])
    first = perform_federated_m5_m6_return_join_v1(
        FederatedM5M6ReturnJoinRequestV1(optimization_experiment_evidence=evidence)
    )
    assert first["status"] == JOIN_STATUS_COMPLETE
    second = perform_federated_m5_m6_return_join_v1(
        FederatedM5M6ReturnJoinRequestV1(
            optimization_experiment_evidence=evidence,
            seen_surface_execution_identities=frozenset({join_key}),
        )
    )
    assert second["status"] == JOIN_STATUS_REJECTED_DUPLICATE


def test_rejects_identity_mismatch() -> None:
    evidence = _federated_m5()
    result = perform_federated_m5_m6_return_join_v1(
        FederatedM5M6ReturnJoinRequestV1(
            optimization_experiment_evidence=evidence,
            expected_surface_execution_identity="c" * 64,
        )
    )
    assert result["status"] == JOIN_STATUS_REJECTED_IDENTITY


def test_rejects_m4_re_execution_request() -> None:
    evidence = _federated_m5()
    with pytest.raises(FederatedM5M6ReturnJoinError, match="M4_RE_EXECUTION_FORBIDDEN"):
        perform_federated_m5_m6_return_join_v1(
            FederatedM5M6ReturnJoinRequestV1(
                optimization_experiment_evidence=evidence,
                requested_m4_re_execution=True,
            )
        )


def test_m6_rejects_digest_mismatch_after_join() -> None:
    evidence = _federated_m5()
    join = perform_federated_m5_m6_return_join_v1(
        FederatedM5M6ReturnJoinRequestV1(optimization_experiment_evidence=evidence)
    )
    tampered = dict(evidence)
    tampered["content_hash"] = "d" * 64
    from src.experiments.canonical_meta_learning_ingest_v1 import (
        INGEST_STATUS_REJECTED_OUT_OF_ORDER,
    )

    ingest = ingest_meta_learning_evidence_from_federated_return_join_v1(
        FederatedMetaLearningIngestRequestV1(
            federated_return_join=join,
            optimization_experiment_evidence=tampered,
        )
    )
    assert ingest["status"] == INGEST_STATUS_REJECTED_OUT_OF_ORDER


def test_foreign_malformed_evidence() -> None:
    result = perform_federated_m5_m6_return_join_v1(
        FederatedM5M6ReturnJoinRequestV1(
            optimization_experiment_evidence={"schema_version": "not-valid"}
        )
    )
    assert result["status"] == JOIN_STATUS_REJECTED_FOREIGN
