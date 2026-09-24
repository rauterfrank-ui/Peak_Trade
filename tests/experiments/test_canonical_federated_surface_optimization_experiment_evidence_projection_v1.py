"""Contract tests for federated surface → M5 evidence projection v1."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_federated_surface_optimization_experiment_evidence_projection_v1 import (
    EXECUTOR_OWNER_F1,
    EXECUTOR_OWNER_F2,
    FederatedSurfaceEvidenceProjectionError,
    FederatedSurfaceEvidenceProjectionRequestV1,
    PROJECTION_BINDING_SURFACE_NATIVE_REF_ONLY,
    SCHEMA_VERSION as PROJECTION_SCHEMA_VERSION,
    SEMANTIC_STATUS_EXPLICIT_REF,
    SEMANTIC_STATUS_NOT_MAPPED,
    bind_f1_surface_execution_projection_request_v1,
    bind_f2_surface_execution_projection_request_v1,
    build_federated_surface_optimization_experiment_evidence_projection_v1,
    validate_federated_projected_optimization_experiment_evidence_v1,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_SURFACE_ID,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    CLASS_ECONOMIC_EVIDENCE,
    CLASS_SEARCH_EVIDENCE,
    REQUIRED_EVIDENCE_CLASSES,
    SCHEMA_VERSION as M5_SCHEMA_VERSION,
    validate_optimization_experiment_evidence_v1,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    OptimizableEnvelopeResolveRequestV1,
    resolve_optimizable_envelope_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECTION_MODULE = (
    REPO_ROOT
    / "src"
    / "experiments"
    / "canonical_federated_surface_optimization_experiment_evidence_projection_v1.py"
)
DECISION_PATH = (
    REPO_ROOT
    / "config"
    / "governance"
    / "federated_surface_optimization_experiment_evidence_projection_v1_decision_v1.json"
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


def _minimal_f1_result(*, execution_id: str = "f1.exec.test.v1") -> dict:
    return {
        "execution_id": execution_id,
        "repository_sha": "a" * 64,
        "candidate_domain_digest": compute_content_sha256({"domain": "f1-test"}),
        "input_evidence_manifest_digest": compute_content_sha256({"manifest": "f1-test"}),
    }


def test_decision_config_aligns_with_spec() -> None:
    decision = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    assert decision["plane_identity_on_federated_record_forbidden"] is True
    assert decision["m4_plane_re_execution_forbidden"] is True
    assert F1_SURFACE_ID in decision["authorized_projection_surface_ids"]
    assert F2_SURFACE_ID in decision["authorized_projection_surface_ids"]


def test_projection_module_does_not_import_m4_plane_executor() -> None:
    tree = ast.parse(PROJECTION_MODULE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert "src.experiments.canonical_optimization_universe_experiment_plane_v1" not in imported


def test_f1_projection_deterministic_and_m5_compatible() -> None:
    env_id, env_digest = _envelope_for(F1_SURFACE_ID)
    native_digest = compute_content_sha256({"native": "f1-artifacts"})
    req = bind_f1_surface_execution_projection_request_v1(
        _minimal_f1_result(),
        surface_native_evidence_ref="research://f1/output_evidence/test",
        surface_native_evidence_digest=native_digest,
        envelope_identity=env_id,
        envelope_resolution_digest=env_digest,
    )
    assert req.executor_semantic_owner == EXECUTOR_OWNER_F1
    first = build_federated_surface_optimization_experiment_evidence_projection_v1(req)
    second = build_federated_surface_optimization_experiment_evidence_projection_v1(req)
    assert first["content_hash"] == second["content_hash"]
    assert first["schema_version"] == M5_SCHEMA_VERSION
    assert "plane_identity" not in first
    assert first["federated_projection"] is True
    validate_optimization_experiment_evidence_v1(first)
    validate_federated_projected_optimization_experiment_evidence_v1(first)
    assert frozenset(first["evidence_slices"].keys()) == REQUIRED_EVIDENCE_CLASSES
    search = first["evidence_slices"][CLASS_SEARCH_EVIDENCE]
    assert search["semantic_status"] == SEMANTIC_STATUS_NOT_MAPPED
    assert search["projection_binding"] == PROJECTION_BINDING_SURFACE_NATIVE_REF_ONLY
    assert "candidate_experiment_id" not in first


def _minimal_f2_result(*, execution_digest: str | None = None) -> dict:
    execution_digest = execution_digest or compute_content_sha256({"f2": "execution"})
    bundle_body = {
        "schema_version": "f2_research_evidence_materialization_v1",
        "surface_id": F2_SURFACE_ID,
        "evidence_by_class": {"GRID_DIGEST": {"grid_digest": "stub"}},
    }
    bundle_digest = compute_content_sha256(bundle_body)
    return {
        "schema_version": "canonical_f2_research_backtest_cost_grid_research_execution_v1",
        "execution_digest": execution_digest,
        "parameter_sensitivity_result_digest": compute_content_sha256({"sensitivity": "stub"}),
        "required_evidence_materialization": {
            **bundle_body,
            "evidence_bundle_digest": bundle_digest,
        },
        "code_provenance": {
            "git_sha": "b" * 64,
            "working_tree_status": "CLEAN",
        },
    }


def test_f2_projection_from_execution_result_without_m4() -> None:
    f2_result = _minimal_f2_result()
    env_id, env_digest = _envelope_for(F2_SURFACE_ID)
    economic_digest = compute_content_sha256(
        {"economic": f2_result.get("parameter_sensitivity_result_digest")}
    )
    req = bind_f2_surface_execution_projection_request_v1(
        f2_result,
        surface_native_evidence_ref="f2://required_evidence_materialization",
        envelope_identity=env_id,
        envelope_resolution_digest=env_digest,
        explicit_slice_bindings={
            CLASS_ECONOMIC_EVIDENCE: {
                "surface_native_evidence_ref": "f2://economic_evaluation_binding",
                "surface_native_evidence_digest": economic_digest,
            }
        },
    )
    assert req.executor_semantic_owner == EXECUTOR_OWNER_F2
    evidence = build_federated_surface_optimization_experiment_evidence_projection_v1(req)
    assert evidence["provenance"]["m4_plane_execution"] is False
    assert evidence["provenance"]["executor_semantic_owner"] == EXECUTOR_OWNER_F2
    economic = evidence["evidence_slices"][CLASS_ECONOMIC_EVIDENCE]
    assert economic["semantic_status"] == SEMANTIC_STATUS_EXPLICIT_REF


def test_f1_f2_isolation_different_surface_execution_identity() -> None:
    env_f1, digest_f1 = _envelope_for(F1_SURFACE_ID)
    env_f2, digest_f2 = _envelope_for(F2_SURFACE_ID)
    native = compute_content_sha256({"x": "native"})
    f1 = build_federated_surface_optimization_experiment_evidence_projection_v1(
        bind_f1_surface_execution_projection_request_v1(
            _minimal_f1_result(execution_id="f1.a"),
            surface_native_evidence_ref="ref/f1",
            surface_native_evidence_digest=native,
            envelope_identity=env_f1,
            envelope_resolution_digest=digest_f1,
        )
    )
    f2 = build_federated_surface_optimization_experiment_evidence_projection_v1(
        FederatedSurfaceEvidenceProjectionRequestV1(
            surface_id=F2_SURFACE_ID,
            envelope_identity=env_f2,
            envelope_resolution_digest=digest_f2,
            surface_execution_digest=compute_content_sha256({"f2": "exec"}),
            surface_native_evidence_ref="ref/f2",
            surface_native_evidence_digest=native,
            executor_semantic_owner=EXECUTOR_OWNER_F2,
        )
    )
    assert f1["surface_execution_identity"] != f2["surface_execution_identity"]
    assert f1["record_id"] != f2["record_id"]


def test_cross_surface_envelope_mismatch_fail_closed() -> None:
    env_f2, digest_f2 = _envelope_for(F2_SURFACE_ID)
    native = compute_content_sha256({"x": "native"})
    with pytest.raises(FederatedSurfaceEvidenceProjectionError, match="ENVELOPE_IDENTITY_MISMATCH"):
        build_federated_surface_optimization_experiment_evidence_projection_v1(
            FederatedSurfaceEvidenceProjectionRequestV1(
                surface_id=F1_SURFACE_ID,
                envelope_identity=env_f2,
                envelope_resolution_digest=digest_f2,
                surface_execution_digest=compute_content_sha256({"bad": "cross"}),
                surface_native_evidence_ref="ref/bad",
                surface_native_evidence_digest=native,
                executor_semantic_owner=EXECUTOR_OWNER_F1,
            )
        )


def test_unknown_surface_fail_closed() -> None:
    env_id, env_digest = _envelope_for(F1_SURFACE_ID)
    with pytest.raises(FederatedSurfaceEvidenceProjectionError, match="SURFACE_NOT_AUTHORIZED"):
        build_federated_surface_optimization_experiment_evidence_projection_v1(
            FederatedSurfaceEvidenceProjectionRequestV1(
                surface_id="UNKNOWN_SURFACE_X",
                envelope_identity=env_id,
                envelope_resolution_digest=env_digest,
                surface_execution_digest=compute_content_sha256({"x": 1}),
                surface_native_evidence_ref="ref/x",
                surface_native_evidence_digest=compute_content_sha256({"d": 1}),
                executor_semantic_owner=EXECUTOR_OWNER_F1,
            )
        )


def test_malformed_missing_digest_fail_closed() -> None:
    env_id, env_digest = _envelope_for(F1_SURFACE_ID)
    with pytest.raises(FederatedSurfaceEvidenceProjectionError, match="SURFACE_EXECUTION_DIGEST"):
        build_federated_surface_optimization_experiment_evidence_projection_v1(
            FederatedSurfaceEvidenceProjectionRequestV1(
                surface_id=F1_SURFACE_ID,
                envelope_identity=env_id,
                envelope_resolution_digest=env_digest,
                surface_execution_digest="not-a-sha256",
                surface_native_evidence_ref="ref/x",
                surface_native_evidence_digest=compute_content_sha256({"d": 1}),
                executor_semantic_owner=EXECUTOR_OWNER_F1,
            )
        )


def test_f1_owner_mismatch_fail_closed() -> None:
    env_id, env_digest = _envelope_for(F1_SURFACE_ID)
    with pytest.raises(FederatedSurfaceEvidenceProjectionError, match="F1_EXECUTOR_OWNER_MISMATCH"):
        build_federated_surface_optimization_experiment_evidence_projection_v1(
            FederatedSurfaceEvidenceProjectionRequestV1(
                surface_id=F1_SURFACE_ID,
                envelope_identity=env_id,
                envelope_resolution_digest=env_digest,
                surface_execution_digest=compute_content_sha256({"x": 1}),
                surface_native_evidence_ref="ref/x",
                surface_native_evidence_digest=compute_content_sha256({"d": 1}),
                executor_semantic_owner=EXECUTOR_OWNER_F2,
            )
        )


def test_authority_invariants_on_record() -> None:
    env_id, env_digest = _envelope_for(F1_SURFACE_ID)
    evidence = build_federated_surface_optimization_experiment_evidence_projection_v1(
        bind_f1_surface_execution_projection_request_v1(
            _minimal_f1_result(),
            surface_native_evidence_ref="ref/f1",
            surface_native_evidence_digest=compute_content_sha256({"n": 1}),
            envelope_identity=env_id,
            envelope_resolution_digest=env_digest,
        )
    )
    assert evidence["optimization_productive_authority"] == "NONE"
    assert evidence["external_effect_authorized"] is False
    assert evidence["learning_state_mutation"] is False
    assert evidence["meta_learning_ingest"] is False
    assert evidence["proposal_not_authority"] is True


def test_federated_validator_rejects_plane_identity() -> None:
    env_id, env_digest = _envelope_for(F1_SURFACE_ID)
    evidence = dict(
        build_federated_surface_optimization_experiment_evidence_projection_v1(
            bind_f1_surface_execution_projection_request_v1(
                _minimal_f1_result(),
                surface_native_evidence_ref="ref/f1",
                surface_native_evidence_digest=compute_content_sha256({"n": 1}),
                envelope_identity=env_id,
                envelope_resolution_digest=env_digest,
            )
        )
    )
    evidence["plane_identity"] = "b" * 64
    with pytest.raises(
        FederatedSurfaceEvidenceProjectionError,
        match="PLANE_IDENTITY_FORBIDDEN",
    ):
        validate_federated_projected_optimization_experiment_evidence_v1(evidence)


def test_projection_schema_version_constant() -> None:
    assert PROJECTION_SCHEMA_VERSION.startswith("canonical_federated_surface_")
