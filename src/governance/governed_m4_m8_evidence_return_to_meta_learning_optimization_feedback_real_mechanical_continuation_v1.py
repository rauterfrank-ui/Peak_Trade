"""Real M4–M8 evidence-return output → meta-learning ingest → optimization feedback (real path).

Composes the proven G2→M4–M8 continuation and fail-closed validates that the cycle output
reaches canonical M6 ingest and M7 bounded research feedback with runtime-derived lineage.
No DDO fixture substitution; no productive authority; no runtime apply.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_meta_learning_ingest_v1 import INGEST_STATUS_COMPLETE
from src.experiments.canonical_meta_to_optimization_feedback_v1 import (
    MetaToOptimizationFeedbackInputRequestV1,
    SCHEMA_VERSION as M7_FEEDBACK_SCHEMA_VERSION,
    validate_meta_to_optimization_feedback_input_v1,
)
from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import LOOP_STATUS_COMPLETE
from src.experiments.canonical_self_learning_optimization_return_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT,
)
from src.governance.governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1 import (
    G2RuntimeM4M8ContinuationRequestV1,
    run_g2_runtime_to_m4_m8_evidence_return_continuation_v1,
)
from src.governance.governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1 import (
    BINDING_PRODUCER_ID,
    CANONICAL_LEARNING_INPUT_IMPLIES_PRODUCTIVE_ACTIVATION,
    EXTERNAL_EFFECT,
    P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY,
    PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION,
    PRODUCTIVE_ACTIVATION_AUTHORIZED,
    REAL_RUNTIME_MATERIALIZATION_PERFORMED,
    RUNTIME_APPLY_STARTED,
    prove_binding_authority_invariants_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    GovernedRuntimePrimaryProjectionRequestV1,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    META_EVIDENCE_AUTHORITY,
    validate_meta_learning_evidence_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = (
    "governed_m4_m8_evidence_return_to_meta_learning_optimization_feedback_real_mechanical_continuation_v1"
)
WORKPACKAGE_ID: Final[str] = (
    "GOVERNED_M4_M8_EVIDENCE_RETURN_TO_META_LEARNING_OPTIMIZATION_FEEDBACK_REAL_MECHANICAL_CONTINUATION_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/"
    "GOVERNED_M4_M8_EVIDENCE_RETURN_TO_META_LEARNING_OPTIMIZATION_FEEDBACK_REAL_MECHANICAL_CONTINUATION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "governed_m4_m8_evidence_return_to_meta_learning_optimization_feedback_real_mechanical_continuation_v1_decision_v1.json"
)

REAL_M4_M8_TO_META_LEARNING_STATUS: Final[str] = "PROVEN_REAL_MECHANICAL_PATH"
REAL_META_LEARNING_TO_OPTIMIZATION_FEEDBACK_STATUS: Final[str] = "PROVEN_REAL_MECHANICAL_PATH"
REAL_FEEDBACK_END_TO_END_STATUS: Final[str] = "PROVEN_REAL_MECHANICAL_PATH"
CLOSED_MECHANICAL_LEARNING_LOOP: Final[bool] = True
CLOSED_PRODUCTIVE_OPTIMIZATION_LOOP: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]


class GovernedM4M8MetaOptimizationFeedbackContinuationError(ValueError):
    """Fail-closed real M4–M8 → meta-learning → optimization feedback error."""


@dataclass(frozen=True)
class M4M8MetaOptimizationFeedbackContinuationRequestV1:
    projection_request: GovernedRuntimePrimaryProjectionRequestV1
    replay_seed: int | None = None
    ddo_fixture_learning_state: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class M4M8MetaOptimizationFeedbackContinuationResultV1:
    status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    g2_m4_m8_status: str
    meta_learning_evidence: dict[str, Any] | None
    bounded_research_feedback_decision: dict[str, Any] | None
    lineage_chain: tuple[str, ...] = field(default_factory=tuple)
    g2_real_source_used: bool = False
    ddo_fixture_learning_state_used: bool = False
    m4_m8_real_output_used: bool = False
    meta_learning_real_ingress_reached: bool = False
    optimization_feedback_real_ingress_reached: bool = False
    feedback_output_produced: bool = False


def validate_real_m4_m8_cycle_meta_optimization_feedback_join_v1(
    *,
    learning_evidence: Mapping[str, Any],
    m4_m8_loop: Mapping[str, Any],
    require_runtime_g2_producer: bool = True,
) -> tuple[str, ...]:
    """Fail-closed lineage join from runtime learning evidence to M6/M7 cycle artifacts."""
    reasons: list[str] = []
    if m4_m8_loop.get("status") != LOOP_STATUS_COMPLETE:
        reasons.append("M4_M8_LOOP_NOT_COMPLETE")
        return tuple(reasons)

    if require_runtime_g2_producer:
        producer = str(learning_evidence.get("producer_id", ""))
        if producer != BINDING_PRODUCER_ID:
            reasons.append("LEARNING_EVIDENCE_NOT_RUNTIME_G2_BINDING")

    learning_digest = str(learning_evidence.get("content_hash", ""))
    if not is_valid_sha256_hex(learning_digest):
        reasons.append("LEARNING_EVIDENCE_DIGEST_INVALID")

    cycle = m4_m8_loop.get("cycle") or {}
    learning_input = cycle.get("learning_input_validation") or {}
    cycle_body = cycle.get("cycle_body") or {}
    if learning_input.get("learning_evidence_digest") != learning_digest:
        reasons.append("LEARNING_EVIDENCE_DIGEST_LINEAGE_MISMATCH")
    if cycle_body.get("learning_evidence_digest") != learning_digest:
        reasons.append("CYCLE_BODY_LEARNING_EVIDENCE_DIGEST_MISMATCH")

    return_ack = cycle.get("return_input_ack") or {}
    if return_ack.get("status") != STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT:
        reasons.append("M5_RETURN_ACK_NOT_ACCEPTED")
    plane = cycle.get("experiment_plane_result") or {}
    plane_identity = str(plane.get("plane_identity", ""))
    if plane_identity and return_ack.get("plane_identity") != plane_identity:
        reasons.append("PLANE_IDENTITY_RETURN_ACK_MISMATCH")

    ingest = cycle.get("meta_learning_ingest") or {}
    if ingest.get("status") != INGEST_STATUS_COMPLETE:
        reasons.append("M6_META_LEARNING_INGEST_NOT_COMPLETE")

    meta = cycle.get("meta_learning_evidence") or {}
    if not meta:
        reasons.append("M6_META_LEARNING_EVIDENCE_MISSING")
    else:
        try:
            validate_meta_learning_evidence_v1(meta)
        except ValueError:
            reasons.append("M6_META_LEARNING_EVIDENCE_MALFORMED")
        if meta.get("meta_evidence_authority") != META_EVIDENCE_AUTHORITY:
            reasons.append("M6_META_EVIDENCE_AUTHORITY_ESCALATION")
        opt_digest = (cycle.get("optimization_experiment_evidence") or {}).get("content_hash")
        if meta.get("source_optimization_experiment_evidence_digest") != opt_digest:
            reasons.append("M6_SOURCE_OPTIMIZATION_EVIDENCE_DIGEST_MISMATCH")

    feedback = cycle.get("bounded_research_feedback_decision") or {}
    if feedback.get("schema_version") != M7_FEEDBACK_SCHEMA_VERSION:
        reasons.append("M7_FEEDBACK_SCHEMA_STALE")
    if not feedback.get("feedback_decision_identity"):
        reasons.append("M7_FEEDBACK_DECISION_IDENTITY_MISSING")

    if meta and not reasons:
        revalidated = validate_meta_to_optimization_feedback_input_v1(
            MetaToOptimizationFeedbackInputRequestV1(
                meta_learning_evidence=meta,
                expected_meta_evidence_id=str(meta.get("meta_evidence_id")),
            )
        )
        if revalidated.get("feedback_decision_identity") != feedback.get(
            "feedback_decision_identity"
        ):
            reasons.append("M7_FEEDBACK_REVALIDATION_IDENTITY_MISMATCH")

    return tuple(reasons)


def run_real_runtime_g2_to_meta_learning_optimization_feedback_continuation_v1(
    request: M4M8MetaOptimizationFeedbackContinuationRequestV1,
) -> M4M8MetaOptimizationFeedbackContinuationResultV1:
    g2_request = G2RuntimeM4M8ContinuationRequestV1(
        projection_request=request.projection_request,
        replay_seed=request.replay_seed,
        ddo_fixture_learning_state=request.ddo_fixture_learning_state,
    )
    g2_result = run_g2_runtime_to_m4_m8_evidence_return_continuation_v1(g2_request)
    base_lineage = g2_result.lineage_chain

    if g2_result.status != "CONTINUATION_COMPLETE":
        return M4M8MetaOptimizationFeedbackContinuationResultV1(
            status="REJECTED",
            decision_code=g2_result.decision_code,
            blocking_reasons=g2_result.blocking_reasons,
            g2_m4_m8_status=g2_result.status,
            meta_learning_evidence=None,
            bounded_research_feedback_decision=None,
            lineage_chain=base_lineage,
            g2_real_source_used=g2_result.g2_real_source_used,
            ddo_fixture_learning_state_used=g2_result.ddo_fixture_learning_state_used,
            m4_m8_real_output_used=g2_result.m4_m8_evidence_return_output_produced,
        )

    learning_evidence = g2_result.learning_evidence or {}
    loop = dict(g2_result.m4_m8_loop or {})
    join_reasons = validate_real_m4_m8_cycle_meta_optimization_feedback_join_v1(
        learning_evidence=learning_evidence,
        m4_m8_loop=loop,
        require_runtime_g2_producer=True,
    )
    if join_reasons:
        code = join_reasons[0]
        return M4M8MetaOptimizationFeedbackContinuationResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=join_reasons,
            g2_m4_m8_status=g2_result.status,
            meta_learning_evidence=(loop.get("cycle") or {}).get("meta_learning_evidence"),
            bounded_research_feedback_decision=(loop.get("cycle") or {}).get(
                "bounded_research_feedback_decision"
            ),
            lineage_chain=base_lineage,
            g2_real_source_used=True,
            ddo_fixture_learning_state_used=False,
            m4_m8_real_output_used=True,
            meta_learning_real_ingress_reached=INGEST_STATUS_COMPLETE
            == ((loop.get("cycle") or {}).get("meta_learning_ingest") or {}).get("status"),
        )

    cycle = loop.get("cycle") or {}
    meta = dict(cycle.get("meta_learning_evidence") or {})
    feedback = dict(cycle.get("bounded_research_feedback_decision") or {})
    extended_lineage = (
        *base_lineage,
        f"meta_learning_evidence://{meta.get('content_hash', '')}",
        f"optimization_feedback://{feedback.get('feedback_decision_identity', '')}",
    )
    return M4M8MetaOptimizationFeedbackContinuationResultV1(
        status="CONTINUATION_COMPLETE",
        decision_code="REAL_M4_M8_META_OPTIMIZATION_FEEDBACK_CONTINUATION_COMPLETE",
        blocking_reasons=(),
        g2_m4_m8_status=g2_result.status,
        meta_learning_evidence=meta,
        bounded_research_feedback_decision=feedback,
        lineage_chain=extended_lineage,
        g2_real_source_used=True,
        ddo_fixture_learning_state_used=False,
        m4_m8_real_output_used=True,
        meta_learning_real_ingress_reached=True,
        optimization_feedback_real_ingress_reached=True,
        feedback_output_produced=True,
    )


def prove_real_meta_optimization_feedback_continuation_v1(
    *,
    projection_request: GovernedRuntimePrimaryProjectionRequestV1,
) -> bool:
    result = run_real_runtime_g2_to_meta_learning_optimization_feedback_continuation_v1(
        M4M8MetaOptimizationFeedbackContinuationRequestV1(projection_request=projection_request)
    )
    if result.status != "CONTINUATION_COMPLETE":
        return False
    if not (
        result.g2_real_source_used
        and not result.ddo_fixture_learning_state_used
        and result.m4_m8_real_output_used
        and result.meta_learning_real_ingress_reached
        and result.optimization_feedback_real_ingress_reached
        and result.feedback_output_produced
    ):
        return False
    meta = result.meta_learning_evidence or {}
    return meta.get("meta_evidence_authority") == META_EVIDENCE_AUTHORITY


def prove_continuation_authority_invariants_v1() -> bool:
    return (
        prove_binding_authority_invariants_v1()
        and PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION is False
        and P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY is False
        and CANONICAL_LEARNING_INPUT_IMPLIES_PRODUCTIVE_ACTIVATION is False
        and RUNTIME_APPLY_STARTED is False
        and REAL_RUNTIME_MATERIALIZATION_PERFORMED is False
        and PRODUCTIVE_ACTIVATION_AUTHORIZED is False
        and EXTERNAL_EFFECT is False
        and CLOSED_PRODUCTIVE_OPTIMIZATION_LOOP is False
    )


def prove_continuation_decision_files_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    paths = (
        DECISION_CONFIG,
        NORMATIVE_SPEC,
        "src/governance/"
        "governed_m4_m8_evidence_return_to_meta_learning_optimization_feedback_real_mechanical_continuation_v1.py",
        "tests/governance/"
        "test_governed_m4_m8_evidence_return_to_meta_learning_optimization_feedback_real_mechanical_continuation_v1.py",
    )
    return all((root / rel).is_file() for rel in paths)


def continuation_lineage_digest_v1(*, lineage_chain: tuple[str, ...]) -> str:
    return compute_content_sha256({"lineage": list(lineage_chain)})


__all__ = [
    "CLOSED_MECHANICAL_LEARNING_LOOP",
    "CLOSED_PRODUCTIVE_OPTIMIZATION_LOOP",
    "DECISION_CONFIG",
    "GovernedM4M8MetaOptimizationFeedbackContinuationError",
    "M4M8MetaOptimizationFeedbackContinuationRequestV1",
    "M4M8MetaOptimizationFeedbackContinuationResultV1",
    "NORMATIVE_SPEC",
    "REAL_FEEDBACK_END_TO_END_STATUS",
    "REAL_M4_M8_TO_META_LEARNING_STATUS",
    "REAL_META_LEARNING_TO_OPTIMIZATION_FEEDBACK_STATUS",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "continuation_lineage_digest_v1",
    "prove_continuation_authority_invariants_v1",
    "prove_continuation_decision_files_v1",
    "prove_real_meta_optimization_feedback_continuation_v1",
    "run_real_runtime_g2_to_meta_learning_optimization_feedback_continuation_v1",
    "validate_real_m4_m8_cycle_meta_optimization_feedback_join_v1",
]
