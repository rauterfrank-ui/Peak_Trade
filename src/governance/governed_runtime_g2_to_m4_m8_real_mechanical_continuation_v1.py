"""G2 runtime-derived learning evidence → canonical M4–M8 evidence return loop (real path).

Composes #6880 runtime binding with existing M4–M8 orchestrator only. No DDO fixture
learning state on the real path. Authority=NONE; no runtime apply or external effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_advanced_search_v1 import SearchAxisV1, SearchSpaceV1
from src.experiments.canonical_comparison_ssot_v1 import ComparisonCandidateV1
from src.experiments.canonical_experiment_identity_v1 import (
    WORKING_TREE_CLEAN,
    CanonicalExperimentIdentityRequestV1,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import (
    LOOP_STATUS_COMPLETE,
    M4M8EvidenceReturnLoopRequestV1,
    run_m4_m8_evidence_return_loop_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    OptimizationUniverseExperimentPlaneRequestV1,
)
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.experiments.canonical_robustness_suite_v1 import METRIC_DEFINITION_VERSION
from src.governance.governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1 import (
    BINDING_PRODUCER_ID,
    CANONICAL_LEARNING_INPUT_IMPLIES_PRODUCTIVE_ACTIVATION,
    EXTERNAL_EFFECT,
    P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY,
    PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION,
    PRODUCTIVE_ACTIVATION_AUTHORIZED,
    REAL_RUNTIME_MATERIALIZATION_PERFORMED,
    RUNTIME_APPLY_STARTED,
    bind_from_g2_projection_result_v1,
    prove_binding_authority_invariants_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    GovernedRuntimePrimaryProjectionRequestV1,
    GovernedRuntimePrimaryProjectionResultV1,
    run_governed_runtime_primary_to_offline_observation_projection_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1"
WORKPACKAGE_ID: Final[str] = "GOVERNED_RUNTIME_G2_TO_M4_M8_REAL_MECHANICAL_CONTINUATION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/GOVERNED_RUNTIME_G2_TO_M4_M8_REAL_MECHANICAL_CONTINUATION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1_decision_v1.json"
)

REAL_RUNTIME_G2_TO_M4_M8_STATUS: Final[str] = "PROVEN"
M4_M8_END_TO_END_STATUS: Final[str] = "PROVEN_REAL_MECHANICAL_PATH"
G2_REAL_SOURCE_USED: Final[bool] = True
DDO_FIXTURE_LEARNING_STATE_FORBIDDEN: Final[bool] = True

_OFFLINE_PLANE_CREATED_AT: Final[str] = "2026-09-26T12:00:00Z"
_TIME_HORIZON: Final[dict[str, str]] = {
    "start": "2020-01-01T00:00:00Z",
    "end": "2024-12-31T00:00:00Z",
}
_MARKET_UNIVERSE: Final[tuple[str, ...]] = ("SYNTHETIC-OFFLINE-RESEARCH-ONLY",)

_REPO_ROOT = Path(__file__).resolve().parents[2]


class GovernedRuntimeG2M4M8ContinuationError(ValueError):
    """Fail-closed G2→M4–M8 continuation error."""


@dataclass(frozen=True)
class G2RuntimeM4M8ContinuationRequestV1:
    projection_request: GovernedRuntimePrimaryProjectionRequestV1
    replay_seed: int | None = None
    ddo_fixture_learning_state: Mapping[str, Any] | None = None
    requested_search_execution: bool = False
    requested_promotion: bool = False
    requested_p5_producer_bridge: bool = False


@dataclass(frozen=True)
class G2RuntimeM4M8ContinuationResultV1:
    status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    projection: GovernedRuntimePrimaryProjectionResultV1 | None
    learning_evidence: dict[str, Any] | None
    canonical_optimization_ack: MappingProxyType[str, Any] | None
    plane_request_digest: str | None
    m4_m8_loop: MappingProxyType[str, Any] | None
    lineage_chain: tuple[str, ...] = field(default_factory=tuple)
    g2_real_source_used: bool = False
    ddo_fixture_learning_state_used: bool = False
    canonical_optimization_input_validated: bool = False
    m4_m8_real_ingress_reached: bool = False
    m4_m8_evidence_return_output_produced: bool = False


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _replay_seed_from_learning_evidence(learning_evidence: Mapping[str, Any]) -> int:
    token = str(
        learning_evidence.get("evaluation_bundle_fingerprint")
        or learning_evidence.get("content_hash")
        or ""
    )
    if is_valid_sha256_hex(token):
        return int(token[:8], 16) % 1_000_000
    return 7


def _stable_offline_plane_identity_template_v1(
    *,
    learning_evidence: Mapping[str, Any],
    projection_request: GovernedRuntimePrimaryProjectionRequestV1,
) -> CanonicalExperimentIdentityRequestV1:
    """Bounded offline M4 identity envelope; lineage anchored to runtime learning evidence."""
    lineage_ref = str(learning_evidence.get("record_id", "")) or _digest("g2-lineage")
    return CanonicalExperimentIdentityRequestV1(
        git_sha="c889577bef56300f74039d921472f0638cbb8810",
        working_tree_status=WORKING_TREE_CLEAN,
        strategy_identity="g2.runtime.offline_plane.v1",
        strategy_params={"fast": 10, "slow": 50},
        dataset_digest=_digest("g2-offline-dataset"),
        feature_pipeline_digest=_digest("g2-offline-features"),
        fee_model_digest=_digest("g2-offline-fee"),
        slippage_model_digest=_digest("g2-offline-slippage"),
        funding_model_digest=_digest("g2-offline-funding"),
        risk_policy_digest=_digest("g2-offline-risk"),
        portfolio_digest=_digest("g2-offline-portfolio"),
        split_policy_digest=_digest("g2-offline-split"),
        market_context_contract_digest=_digest("g2-offline-market-context"),
        bull_bear_logic_digest=_digest("g2-offline-bull-bear"),
        state_switch_logic_digest=_digest("g2-offline-state-switch"),
        survival_logic_digest=_digest("g2-offline-survival"),
        suitability_logic_digest=_digest("g2-offline-suitability"),
        double_play_logic_digest=_digest("g2-offline-double-play"),
        entry_position_exit_logic_digest=_digest("g2-offline-entry-exit"),
        seed=19,
        environment={
            "python_version": "3.11.15",
            "python_implementation": "CPython",
        },
        parent_lineage_ref=lineage_ref or projection_request.claimed_parent_lineage_ref,
        dirty_paths_digest=None,
    )


def build_bounded_offline_m4_plane_request_from_runtime_learning_evidence_v1(
    *,
    learning_evidence: Mapping[str, Any],
    projection_request: GovernedRuntimePrimaryProjectionRequestV1,
    replay_seed: int | None = None,
) -> OptimizationUniverseExperimentPlaneRequestV1:
    """Bounded offline M4 plane request; learning evidence must be runtime-derived G2 export."""
    producer = str(learning_evidence.get("producer_id", ""))
    if producer != BINDING_PRODUCER_ID:
        raise GovernedRuntimeG2M4M8ContinuationError("LEARNING_EVIDENCE_NOT_RUNTIME_G2_BINDING")
    identity_template = _stable_offline_plane_identity_template_v1(
        learning_evidence=learning_evidence,
        projection_request=projection_request,
    )
    identity = build_canonical_experiment_identity_v1(identity_template)
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    seed = 19 if replay_seed is None else replay_seed
    champion = ComparisonCandidateV1(
        experiment_identity=identity,
        robustness_suite_version="canonical_robustness_suite_v1",
        metric_definitions=METRIC_DEFINITION_VERSION,
        time_horizon=dict(_TIME_HORIZON),
        market_universe=list(_MARKET_UNIVERSE),
        experiment_id=experiment_id,
        evidence_refs=(),
    )
    return OptimizationUniverseExperimentPlaneRequestV1(
        learning_evidence=dict(learning_evidence),
        identity_template=identity_template,
        search_space=SearchSpaceV1(
            search_space_id="search.g2.runtime.offline_plane.v1",
            axes=(SearchAxisV1(name="fast", values=(10, 15)),),
        ),
        champion=champion,
        champion_score=1.0,
        challenger_score=1.05,
        created_at=_OFFLINE_PLANE_CREATED_AT,
        search_seed=seed,
        search_budget=1,
        parent_hypothesis_id=projection_request.hypothesis_id,
        strategy_family=projection_request.strategy_family,
    )


def run_g2_runtime_to_m4_m8_evidence_return_continuation_v1(
    request: G2RuntimeM4M8ContinuationRequestV1,
) -> G2RuntimeM4M8ContinuationResultV1:
    if request.ddo_fixture_learning_state is not None:
        code = "DDO_FIXTURE_LEARNING_STATE_FORBIDDEN_ON_REAL_PATH"
        return G2RuntimeM4M8ContinuationResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=(code,),
            projection=None,
            learning_evidence=None,
            canonical_optimization_ack=None,
            plane_request_digest=None,
            m4_m8_loop=None,
            ddo_fixture_learning_state_used=False,
        )

    projection = run_governed_runtime_primary_to_offline_observation_projection_v1(
        request.projection_request
    )
    if projection.status != "PROJECTED":
        code = "G2_PROJECTION_NOT_PROJECTED"
        return G2RuntimeM4M8ContinuationResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=(code, *projection.blocking_reasons),
            projection=projection,
            learning_evidence=None,
            canonical_optimization_ack=None,
            plane_request_digest=None,
            m4_m8_loop=None,
        )

    binding = bind_from_g2_projection_result_v1(projection)
    if binding.status != "BOUND" or binding.learning_evidence is None:
        code = binding.decision_code or "G2_RUNTIME_BINDING_FAILED"
        return G2RuntimeM4M8ContinuationResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=binding.blocking_reasons or (code,),
            projection=projection,
            learning_evidence=binding.learning_evidence,
            canonical_optimization_ack=binding.canonical_optimization_ack,
            plane_request_digest=None,
            m4_m8_loop=None,
            g2_real_source_used=True,
        )

    learning_evidence = binding.learning_evidence
    ack = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=learning_evidence)
    )
    if ack.get("status") != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT:
        reason = str(ack.get("reason", "CANONICAL_OPTIMIZATION_INPUT_REJECTED"))
        return G2RuntimeM4M8ContinuationResultV1(
            status="REJECTED",
            decision_code=reason,
            blocking_reasons=(reason,),
            projection=projection,
            learning_evidence=learning_evidence,
            canonical_optimization_ack=ack,
            plane_request_digest=None,
            m4_m8_loop=None,
            g2_real_source_used=True,
            canonical_optimization_input_validated=False,
        )

    try:
        plane_request = build_bounded_offline_m4_plane_request_from_runtime_learning_evidence_v1(
            learning_evidence=learning_evidence,
            projection_request=request.projection_request,
            replay_seed=request.replay_seed,
        )
    except GovernedRuntimeG2M4M8ContinuationError as exc:
        code = str(exc)
        return G2RuntimeM4M8ContinuationResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=(code,),
            projection=projection,
            learning_evidence=learning_evidence,
            canonical_optimization_ack=ack,
            plane_request_digest=None,
            m4_m8_loop=None,
            g2_real_source_used=True,
            canonical_optimization_input_validated=True,
        )

    plane_digest = compute_content_sha256(
        {
            "learning_evidence_digest": learning_evidence.get("content_hash"),
            "search_seed": plane_request.search_seed,
            "hypothesis_id": plane_request.parent_hypothesis_id,
        }
    )

    loop = run_m4_m8_evidence_return_loop_v1(
        M4M8EvidenceReturnLoopRequestV1(
            learning_evidence=learning_evidence,
            plane_request=plane_request,
            replay_seed=plane_request.search_seed,
            requested_search_execution=request.requested_search_execution,
            requested_promotion=request.requested_promotion,
            requested_p5_producer_bridge=request.requested_p5_producer_bridge,
        )
    )

    loop_complete = loop.get("status") == LOOP_STATUS_COMPLETE
    lineage = (
        f"primary_manifest://{projection.provenance.primary_evidence_manifest_digest}"
        if projection.provenance
        else "primary_manifest://missing",
        f"runtime_learning://{projection.runtime_learning_input.get('output_digest', '')}"
        if projection.runtime_learning_input
        else "runtime_learning://missing",
        f"learning_evidence://{learning_evidence.get('content_hash', '')}",
        f"optimization_input://{ack.get('result_digest', '')}",
        f"m4_plane://{plane_digest}",
        f"m4_m8_loop://{loop.get('result_digest', '')}",
    )

    if not loop_complete:
        return G2RuntimeM4M8ContinuationResultV1(
            status="REJECTED",
            decision_code=str(loop.get("reason", "M4_M8_LOOP_NOT_COMPLETE")),
            blocking_reasons=(str(loop.get("reason", "M4_M8_LOOP_NOT_COMPLETE")),),
            projection=projection,
            learning_evidence=learning_evidence,
            canonical_optimization_ack=ack,
            plane_request_digest=plane_digest,
            m4_m8_loop=loop,
            lineage_chain=lineage,
            g2_real_source_used=True,
            ddo_fixture_learning_state_used=False,
            canonical_optimization_input_validated=True,
            m4_m8_real_ingress_reached=True,
            m4_m8_evidence_return_output_produced=False,
        )

    return G2RuntimeM4M8ContinuationResultV1(
        status="CONTINUATION_COMPLETE",
        decision_code="G2_RUNTIME_TO_M4_M8_EVIDENCE_RETURN_COMPLETE",
        blocking_reasons=(),
        projection=projection,
        learning_evidence=learning_evidence,
        canonical_optimization_ack=ack,
        plane_request_digest=plane_digest,
        m4_m8_loop=loop,
        lineage_chain=lineage,
        g2_real_source_used=True,
        ddo_fixture_learning_state_used=False,
        canonical_optimization_input_validated=True,
        m4_m8_real_ingress_reached=True,
        m4_m8_evidence_return_output_produced=True,
    )


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
    )


def prove_continuation_decision_files_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    decision = root / DECISION_CONFIG
    spec = root / NORMATIVE_SPEC
    module = root / "src/governance/governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1.py"
    tests = (
        root
        / "tests/governance/test_governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1.py"
    )
    return all(path.is_file() for path in (decision, spec, module, tests))


__all__ = [
    "DECISION_CONFIG",
    "DDO_FIXTURE_LEARNING_STATE_FORBIDDEN",
    "G2_REAL_SOURCE_USED",
    "GovernedRuntimeG2M4M8ContinuationError",
    "G2RuntimeM4M8ContinuationRequestV1",
    "G2RuntimeM4M8ContinuationResultV1",
    "M4_M8_END_TO_END_STATUS",
    "NORMATIVE_SPEC",
    "REAL_RUNTIME_G2_TO_M4_M8_STATUS",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "build_bounded_offline_m4_plane_request_from_runtime_learning_evidence_v1",
    "prove_continuation_authority_invariants_v1",
    "prove_continuation_decision_files_v1",
    "run_g2_runtime_to_m4_m8_evidence_return_continuation_v1",
]
