"""Closure and fixture-bounded end-to-end proofs for G2 primary→offline projection v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final, Mapping

from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import (
    LOOP_STATUS_COMPLETE,
    M4M8EvidenceReturnLoopRequestV1,
    run_m4_m8_evidence_return_loop_v1,
)
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.governance.governed_productive_configuration_apply_authority_v1 import (
    PRIMARY_EVIDENCE_IMPLIES_APPLY,
    RUNTIME_APPLY_STARTED as M10_RUNTIME_APPLY_STARTED,
)
from src.governance.governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1 import (
    M4_M8_END_TO_END_STATUS,
    REAL_RUNTIME_G2_TO_M4_M8_STATUS,
    G2RuntimeM4M8ContinuationRequestV1,
    prove_continuation_authority_invariants_v1,
    prove_continuation_decision_files_v1,
    run_g2_runtime_to_m4_m8_evidence_return_continuation_v1,
)
from src.governance.governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1 import (
    REAL_MECHANICAL_PATH_STATUS,
    bind_from_g2_projection_result_v1,
    prove_binding_authority_invariants_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    DECISION_CONFIG,
    FIELD_MAPPING_LEDGER,
    NORMATIVE_SPEC,
    WORKPACKAGE_ID,
    GovernedRuntimePrimaryProjectionRequestV1,
    RuntimePrimarySourceModeV1,
    run_governed_runtime_primary_to_offline_observation_projection_v1,
)
from src.governance.m4_m8_optimization_meta_learning_evidence_return_closure_v1 import (
    prove_p5_final_closure_mechanically_allowed_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

G2_END_TO_END_STATUS: Final[str] = "PROVEN_REAL_MECHANICAL"
G2_END_TO_END_FIXTURE_HARNESS_STATUS: Final[str] = "PROVEN_FIXTURE_BOUNDED"
G2_RUNTIME_TO_CANONICAL_OPTIMIZATION_INPUT_STATUS: Final[str] = "PROVEN"
RECONSTRUCTION_CLASS_FIXTURE_BOUNDED: Final[str] = "BOUNDED_RECONSTRUCTION_PROVEN"
RECONSTRUCTION_CLASS_REAL_MECHANICAL: Final[str] = "REAL_MECHANICAL_PATH_PROVEN"

_REPO_ROOT = Path(__file__).resolve().parents[2]


def prove_g2_decision_files_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    required = (
        NORMATIVE_SPEC,
        DECISION_CONFIG,
        FIELD_MAPPING_LEDGER,
        "src/governance/governed_runtime_primary_to_offline_observation_projection_v1.py",
        "tests/governance/test_governed_runtime_primary_to_offline_observation_projection_v1.py",
    )
    return all((root / rel).is_file() for rel in required)


def prove_g2_authority_invariants_v1() -> bool:
    return (
        PRIMARY_EVIDENCE_IMPLIES_APPLY is False
        and M10_RUNTIME_APPLY_STARTED is False
        and prove_p5_final_closure_mechanically_allowed_v1() is True
        and prove_binding_authority_invariants_v1() is True
        and prove_continuation_authority_invariants_v1() is True
    )


def prove_g2_runtime_to_canonical_optimization_learning_input_v1(
    *,
    projection_request: GovernedRuntimePrimaryProjectionRequestV1,
) -> bool:
    """Real mechanical path: G2 projection → governed binding → canonical optimization input."""
    projection = run_governed_runtime_primary_to_offline_observation_projection_v1(
        projection_request
    )
    binding = bind_from_g2_projection_result_v1(projection)
    if binding.status != "BOUND":
        return False
    if binding.path_classification != REAL_MECHANICAL_PATH_STATUS:
        return False
    ack = binding.canonical_optimization_ack or {}
    if ack.get("status") != "ACCEPTED_OFFLINE_RESEARCH_INPUT":
        return False
    if binding.learning_evidence is None:
        return False
    return True


def prove_g2_runtime_to_m4_m8_real_mechanical_v1(
    *,
    projection_request: GovernedRuntimePrimaryProjectionRequestV1,
) -> bool:
    """Real path: G2 projection → binding → M4–M8 loop without DDO fixture state."""
    result = run_g2_runtime_to_m4_m8_evidence_return_continuation_v1(
        G2RuntimeM4M8ContinuationRequestV1(projection_request=projection_request)
    )
    if result.status != "CONTINUATION_COMPLETE":
        return False
    if not result.g2_real_source_used or result.ddo_fixture_learning_state_used:
        return False
    if not result.m4_m8_evidence_return_output_produced:
        return False
    loop = result.m4_m8_loop or {}
    if loop.get("status") != LOOP_STATUS_COMPLETE:
        return False
    meta = (loop.get("cycle") or {}).get("meta_learning_evidence") or {}
    return meta.get("meta_evidence_authority") == "NONE"


def prove_g2_m4_m8_fixture_lineage_v1(*, repo_root: Path | None = None) -> bool:
    """M4–M8 chain using canonical DDO learning-evidence fixture (harness only; not real G2 path)."""
    root = repo_root or _REPO_ROOT
    from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
        _plane_request,
    )
    from src.governance.m4_m8_optimization_meta_learning_evidence_return_closure_v1 import (
        _fixture_learning_state,
    )

    import tempfile

    with tempfile.TemporaryDirectory(prefix="g2_m4_m8_") as tmp:
        tmp_path = Path(tmp)
        state = _fixture_learning_state(tmp_path)
        learning_evidence = export_learning_evidence_from_state_v1(state)
        validated = validate_canonical_optimization_universe_learning_input_v1(
            CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=learning_evidence)
        )
        digest = validated.get("learning_evidence_digest") or validated.get("result_digest")
        if not isinstance(digest, str) or len(digest) != 64:
            return False
        plane_request = _plane_request(learning_evidence)
        loop = run_m4_m8_evidence_return_loop_v1(
            M4M8EvidenceReturnLoopRequestV1(
                learning_evidence=learning_evidence,
                plane_request=plane_request,
                replay_seed=7,
            )
        )
        if loop.get("status") != LOOP_STATUS_COMPLETE:
            return False
        cycle = loop.get("cycle") or {}
        meta = cycle.get("meta_learning_evidence") or {}
        if meta.get("meta_evidence_authority") != "NONE":
            return False
    return prove_g2_decision_files_v1(repo_root=root)


def trace_g2_reconstruction_v1(
    *,
    projection_result: Mapping[str, Any],
    m4_m8_cycle: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Trace backwards from projection digest to primary manifest (fixture-bounded)."""
    provenance = projection_result.get("provenance") or {}
    primary_digest = str(provenance.get("primary_evidence_manifest_digest", ""))
    projection_digest = str(projection_result.get("projection_record_digest", ""))
    status = RECONSTRUCTION_CLASS_FIXTURE_BOUNDED
    if not primary_digest or not projection_digest:
        status = "PARTIAL_RECONSTRUCTION"
    if m4_m8_cycle:
        meta = (m4_m8_cycle.get("meta_learning_evidence") or {}).get("content_hash")
        if meta:
            status = RECONSTRUCTION_CLASS_FIXTURE_BOUNDED
    return {
        "classification": status,
        "primary_evidence_manifest_digest": primary_digest,
        "projection_record_digest": projection_digest,
        "source_archive_root_ref": str(provenance.get("source_archive_root_ref", "")),
    }


def prove_g2_projection_closure_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    if not prove_g2_decision_files_v1(repo_root=root):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    if decision.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    if decision.get("runtime_apply_started") is not False:
        return False
    if decision.get("external_effect") is not False:
        return False
    if not prove_g2_authority_invariants_v1():
        return False
    if not prove_continuation_decision_files_v1(repo_root=root):
        return False
    return prove_g2_m4_m8_fixture_lineage_v1(repo_root=root)


def run_g2_bounded_end_to_end_with_projection_v1(
    *,
    projection_request: GovernedRuntimePrimaryProjectionRequestV1,
) -> dict[str, Any]:
    projection = run_governed_runtime_primary_to_offline_observation_projection_v1(
        projection_request
    )
    binding = bind_from_g2_projection_result_v1(projection)
    continuation = run_g2_runtime_to_m4_m8_evidence_return_continuation_v1(
        G2RuntimeM4M8ContinuationRequestV1(projection_request=projection_request)
    )
    m4_ok = prove_g2_m4_m8_fixture_lineage_v1()
    reconstruction = trace_g2_reconstruction_v1(
        projection_result={
            "provenance": projection.provenance.as_dict() if projection.provenance else {},
            "projection_record_digest": projection.projection_record_digest,
        }
    )
    if binding.status == "BOUND" and binding.lineage_chain:
        reconstruction = {
            **reconstruction,
            "classification": RECONSTRUCTION_CLASS_REAL_MECHANICAL,
            "optimization_input_binding_digest": binding.binding_record_digest,
        }
    return {
        "projection_status": projection.status,
        "learning_ingress_status": (
            "PROVEN"
            if (
                projection.runtime_learning_input is not None
                and projection.runtime_learning_input.get("decision_code") == "LEARNING_INPUT_VALID"
            )
            else "REJECTED"
        ),
        "canonical_optimization_input_status": (
            G2_RUNTIME_TO_CANONICAL_OPTIMIZATION_INPUT_STATUS
            if binding.status == "BOUND"
            else "REJECTED"
        ),
        "runtime_mechanical_path_status": binding.path_classification or "NOT_PROVEN",
        "m4_m8_fixture_harness_status": G2_END_TO_END_FIXTURE_HARNESS_STATUS
        if m4_ok
        else "BLOCKED",
        "real_runtime_g2_to_m4_m8_status": (
            REAL_RUNTIME_G2_TO_M4_M8_STATUS
            if continuation.status == "CONTINUATION_COMPLETE"
            else "REJECTED"
        ),
        "m4_m8_end_to_end_status": (
            M4_M8_END_TO_END_STATUS
            if continuation.status == "CONTINUATION_COMPLETE"
            else "NOT_PROVEN"
        ),
        "g2_end_to_end_status": G2_END_TO_END_STATUS
        if projection.status == "PROJECTED" and continuation.status == "CONTINUATION_COMPLETE"
        else "PARTIAL_CURRENT",
        "continuation_lineage_digest": compute_content_sha256(
            {
                "lineage": continuation.lineage_chain,
                "loop": (continuation.m4_m8_loop or {}).get("result_digest"),
            }
        )
        if continuation.lineage_chain
        else None,
        "reconstruction": reconstruction,
        "lineage_digest": compute_content_sha256(
            {
                "projection": projection.projection_record_digest,
                "primary": (
                    projection.provenance.primary_evidence_manifest_digest
                    if projection.provenance
                    else None
                ),
                "binding": binding.binding_record_digest,
            }
        ),
    }


__all__ = [
    "G2_END_TO_END_FIXTURE_HARNESS_STATUS",
    "G2_END_TO_END_STATUS",
    "G2_RUNTIME_TO_CANONICAL_OPTIMIZATION_INPUT_STATUS",
    "RECONSTRUCTION_CLASS_FIXTURE_BOUNDED",
    "RECONSTRUCTION_CLASS_REAL_MECHANICAL",
    "prove_g2_authority_invariants_v1",
    "prove_g2_decision_files_v1",
    "prove_g2_m4_m8_fixture_lineage_v1",
    "prove_g2_projection_closure_v1",
    "prove_g2_runtime_to_canonical_optimization_learning_input_v1",
    "prove_g2_runtime_to_m4_m8_real_mechanical_v1",
    "run_g2_bounded_end_to_end_with_projection_v1",
    "trace_g2_reconstruction_v1",
]
