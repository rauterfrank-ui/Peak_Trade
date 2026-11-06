"""Orchestrate M4–M8 upstream artifacts → P5 producer artifacts (no trading authority)."""

from __future__ import annotations

from typing import Any, Mapping

from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.meta_learning_routed_evidence_v1 import (
    produce_meta_learning_routed_evidence_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.optimization_envelope_evidence_v1 import (
    produce_optimization_envelope_evidence_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.p5_m4_m8_governed_binding_context_v1 import (
    build_p5_m4_m8_governed_evidence_binding_context_v1,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    SCHEMA_VERSION as M5_SCHEMA_VERSION,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    SCHEMA_VERSION as M6_EVIDENCE_SCHEMA_VERSION,
)


def build_optimization_binding_context_v1(
    *,
    market_context: Mapping[str, Any],
    optimization_experiment_evidence: Mapping[str, Any],
    market_observation_epoch: int = 0,
) -> Mapping[str, Any]:
    m5_digest = str(optimization_experiment_evidence.get("content_hash") or "")
    return build_p5_m4_m8_governed_evidence_binding_context_v1(
        market_context=market_context,
        market_observation_epoch=market_observation_epoch,
        source_lineage_schema=M5_SCHEMA_VERSION,
        source_lineage_content_digest=m5_digest,
    )


def build_meta_learning_binding_context_v1(
    *,
    market_context: Mapping[str, Any],
    meta_learning_evidence: Mapping[str, Any],
    market_observation_epoch: int = 0,
) -> Mapping[str, Any]:
    m6_digest = str(meta_learning_evidence.get("reproducibility_digest") or "")
    return build_p5_m4_m8_governed_evidence_binding_context_v1(
        market_context=market_context,
        market_observation_epoch=market_observation_epoch,
        source_lineage_schema=M6_EVIDENCE_SCHEMA_VERSION,
        source_lineage_content_digest=m6_digest,
    )


def bridge_m5_to_optimization_envelope_evidence_v1(
    *,
    optimization_experiment_evidence: Mapping[str, Any],
    market_context: Mapping[str, Any],
    market_observation_epoch: int = 0,
) -> Mapping[str, Any]:
    binding = build_optimization_binding_context_v1(
        market_context=market_context,
        optimization_experiment_evidence=optimization_experiment_evidence,
        market_observation_epoch=market_observation_epoch,
    )
    return produce_optimization_envelope_evidence_v1(
        optimization_experiment_evidence=optimization_experiment_evidence,
        binding_context=binding,
    )


def bridge_m6_to_meta_learning_routed_evidence_v1(
    *,
    meta_learning_evidence: Mapping[str, Any],
    market_context: Mapping[str, Any],
    market_observation_epoch: int = 0,
) -> Mapping[str, Any]:
    binding = build_meta_learning_binding_context_v1(
        market_context=market_context,
        meta_learning_evidence=meta_learning_evidence,
        market_observation_epoch=market_observation_epoch,
    )
    return produce_meta_learning_routed_evidence_v1(
        meta_learning_evidence=meta_learning_evidence,
        binding_context=binding,
    )
