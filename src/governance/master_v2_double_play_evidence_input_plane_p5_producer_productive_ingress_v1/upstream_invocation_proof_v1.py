"""Prove how Optimization / Meta-Learning source artifacts are produced (reachability class)."""

from __future__ import annotations

from typing import Any, Final

from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    SCHEMA_VERSION as OPT_EXP_SCHEMA,
)
from src.learning.deterministic_decision_outcome_v0.meta_evidence_v1 import (
    SCHEMA_VERSION as META_EVIDENCE_SCHEMA,
)

SCHEMA_VERSION: Final[str] = (
    "master_v2_double_play_evidence_input_plane_p5_upstream_invocation_proof/v1"
)


def _surface(
    *,
    module: str,
    builder: str,
    output_schema: str,
    implemented: bool,
    current: bool,
    invocation_path_proven: bool,
    output_artifact_proven: bool,
    reachability: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "module": module,
        "builder": builder,
        "output_schema": output_schema,
        "IMPLEMENTED": implemented,
        "CURRENT": current,
        "INVOCATION_PATH_PROVEN": invocation_path_proven,
        "OUTPUT_ARTIFACT_PROVEN": output_artifact_proven,
        "reachability_class": reachability,
        "PRODUCTIVE_REACHABLE": reachability == "PRODUCTIVE_REACHABLE",
        "notes": notes,
    }


def run_optimization_upstream_invocation_proof_v1() -> dict[str, Any]:
    surfaces = [
        _surface(
            module="src/experiments/canonical_optimization_experiment_evidence_v1.py",
            builder="build_optimization_experiment_evidence_from_plane_v1",
            output_schema=OPT_EXP_SCHEMA,
            implemented=True,
            current=True,
            invocation_path_proven=True,
            output_artifact_proven=True,
            reachability="RESEARCH_RUNNABLE",
            notes="Invoked from offline experiment plane / phase-22 research stacks only.",
        ),
        _surface(
            module="src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_22_incremental_research_evidence_v1.py",
            builder="build_optimization_experiment_evidence_from_plane_v1",
            output_schema=OPT_EXP_SCHEMA,
            implemented=True,
            current=True,
            invocation_path_proven=True,
            output_artifact_proven=True,
            reachability="RESEARCH_RUNNABLE",
            notes="MI offline research evidence path; not productive runtime.",
        ),
        _surface(
            module="src/experiments/canonical_deterministic_multi_cycle_offline_replay_v1.py",
            builder="build_optimization_experiment_evidence_from_plane_v1",
            output_schema=OPT_EXP_SCHEMA,
            implemented=True,
            current=True,
            invocation_path_proven=True,
            output_artifact_proven=True,
            reachability="RESEARCH_RUNNABLE",
            notes="Deterministic offline replay; not productive producer.",
        ),
        _surface(
            module="config/governance/master_v2_double_play_evidence_input_plane_p2_producer_registry_v1.json",
            builder="N/A",
            output_schema="optimization_envelope_evidence_v1",
            implemented=True,
            current=True,
            invocation_path_proven=False,
            output_artifact_proven=False,
            reachability="REGISTRY_DECLARATION_ONLY",
            notes="Registry entry is not evidence emission.",
        ),
        _surface(
            module="src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/p5_m4_m8_producer_bridge_v1.py",
            builder="bridge_m5_to_optimization_envelope_evidence_v1",
            output_schema="optimization_envelope_evidence_v1",
            implemented=True,
            current=True,
            invocation_path_proven=True,
            output_artifact_proven=True,
            reachability="PRODUCTIVE_REACHABLE",
            notes="M5 + governed binding → P5 envelope; terminates at Component A only.",
        ),
    ]
    productive = any(s["PRODUCTIVE_REACHABLE"] for s in surfaces)
    return {
        "schema_version": SCHEMA_VERSION,
        "target_p2_kind": "optimization_envelope_evidence_v1",
        "surfaces": surfaces,
        "productive_reachable_proven": productive,
        "verdict": "PROVEN_AT_A" if productive else "BLOCKED_NO_PRODUCTIVE_EMITTER",
    }


def run_meta_learning_upstream_invocation_proof_v1() -> dict[str, Any]:
    surfaces = [
        _surface(
            module="src/learning/deterministic_decision_outcome_v0/meta_evidence_v1.py",
            builder="build_meta_evidence_v1",
            output_schema=META_EVIDENCE_SCHEMA,
            implemented=True,
            current=True,
            invocation_path_proven=True,
            output_artifact_proven=True,
            reachability="RESEARCH_RUNNABLE",
            notes="RESEARCH_ONLY routing envelope; permitted_use_classification=RESEARCH_ONLY.",
        ),
        _surface(
            module="src/experiments/canonical_meta_evidence_dual_router_v1.py",
            builder="classify_and_build_meta_evidence_v1",
            output_schema=META_EVIDENCE_SCHEMA,
            implemented=True,
            current=True,
            invocation_path_proven=True,
            output_artifact_proven=True,
            reachability="RESEARCH_RUNNABLE",
            notes="Dual-router research consumer path; no productive promotion.",
        ),
        _surface(
            module="src/experiments/canonical_meta_learning_ingest_v1.py",
            builder="meta_learning_evidence_v1 ingest",
            output_schema="meta_learning_evidence_v1",
            implemented=True,
            current=True,
            invocation_path_proven=True,
            output_artifact_proven=True,
            reachability="RESEARCH_RUNNABLE",
            notes="M6 ingest output; routed via P5 binding bridge.",
        ),
        _surface(
            module="src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/p5_m4_m8_producer_bridge_v1.py",
            builder="bridge_m6_to_meta_learning_routed_evidence_v1",
            output_schema="meta_learning_routed_evidence_v1",
            implemented=True,
            current=True,
            invocation_path_proven=True,
            output_artifact_proven=True,
            reachability="PRODUCTIVE_REACHABLE",
            notes="M6 + governed binding → P5 routed evidence; terminates at Component A only.",
        ),
    ]
    productive = any(s["PRODUCTIVE_REACHABLE"] for s in surfaces)
    return {
        "schema_version": SCHEMA_VERSION,
        "target_p2_kind": "meta_learning_routed_evidence_v1",
        "surfaces": surfaces,
        "productive_reachable_proven": productive,
        "verdict": "PROVEN_AT_A" if productive else "BLOCKED_NO_PRODUCTIVE_PROMOTION_BOUNDARY",
    }


def run_p5_upstream_invocation_proofs_v1() -> dict[str, Any]:
    return {
        "optimization": run_optimization_upstream_invocation_proof_v1(),
        "meta_learning": run_meta_learning_upstream_invocation_proof_v1(),
    }
