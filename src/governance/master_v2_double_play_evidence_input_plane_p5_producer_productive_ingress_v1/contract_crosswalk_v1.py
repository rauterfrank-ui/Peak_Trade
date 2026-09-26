"""Field-by-field P5 contract crosswalks (Optimization / Meta-Learning) — read-only."""

from __future__ import annotations

from typing import Any, Final, Literal

from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    SCHEMA_VERSION as OPT_EXP_SCHEMA,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    SCHEMA_VERSION as OPT_ENVELOPE_SCHEMA,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    BoundedL6EvidenceKindV1,
)
from src.learning.deterministic_decision_outcome_v0.meta_evidence_v1 import (
    SCHEMA_VERSION as META_EVIDENCE_SCHEMA,
)

FieldClassification = Literal[
    "EXACT_SOURCE",
    "MECHANICAL_TRANSFORM",
    "SEMANTIC_TRANSFORM_REQUIRED",
    "MISSING",
    "CONFLICTING",
]

SCHEMA_VERSION: Final[str] = "master_v2_double_play_evidence_input_plane_p5_contract_crosswalk/v1"
P2_OPT_KIND: Final[str] = BoundedL6EvidenceKindV1.OPTIMIZATION_ENVELOPE_EVIDENCE_V1.value
P2_META_KIND: Final[str] = BoundedL6EvidenceKindV1.META_LEARNING_ROUTED_EVIDENCE_V1.value

_MANDATORY_OK: Final[frozenset[str]] = frozenset({"EXACT_SOURCE", "MECHANICAL_TRANSFORM"})


def _entry(
    *,
    target_field: str,
    classification: FieldClassification,
    source_artifact: str,
    source_field: str | None,
    source_authority: str,
    transformation: str | None,
    lossiness: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "target_field": target_field,
        "classification": classification,
        "source_artifact": source_artifact,
        "source_field": source_field,
        "source_authority": source_authority,
        "transformation": transformation,
        "lossiness": lossiness,
        "reason": reason,
    }


def _summarize(fields: list[dict[str, Any]]) -> dict[str, Any]:
    first_block = next(
        (f for f in fields if f["classification"] not in _MANDATORY_OK),
        None,
    )
    producer_allowed = first_block is None
    return {
        "mandatory_field_count": len(fields),
        "producer_bridge_allowed": producer_allowed,
        "first_blocking_field": first_block["target_field"] if first_block else None,
        "first_blocking_classification": first_block["classification"] if first_block else None,
        "first_blocking_reason": first_block["reason"] if first_block else None,
    }


def run_optimization_contract_crosswalk_v1() -> dict[str, Any]:
    """Crosswalk P2 optimization_envelope_evidence_v1 intake vs CURRENT Optimization outputs."""
    exp = OPT_EXP_SCHEMA
    env = OPT_ENVELOPE_SCHEMA
    fields: list[dict[str, Any]] = [
        _entry(
            target_field="target_schema_validator",
            classification="MISSING",
            source_artifact=exp,
            source_field=None,
            source_authority="NONE",
            transformation=None,
            lossiness="TOTAL",
            reason=(
                "No repository module validates or emits schema optimization_envelope_evidence_v1; "
                "P2 registry kind exists without governed artifact contract."
            ),
        ),
        _entry(
            target_field="evidence_kind",
            classification="CONFLICTING",
            source_artifact=exp,
            source_field="schema_version",
            source_authority="RESEARCH_OPTIMIZATION_EXPERIMENT",
            transformation=None,
            lossiness="TOTAL",
            reason=(f"Source schema {exp} is OPTIMIZATION_EXPERIMENT evidence, not {P2_OPT_KIND}."),
        ),
        _entry(
            target_field="evidence_kind",
            classification="CONFLICTING",
            source_artifact=env,
            source_field="schema_version",
            source_authority="RESEARCH_ENVELOPE_RESOLVER",
            transformation=None,
            lossiness="TOTAL",
            reason=(
                f"Source schema {env} is optimizable-surface envelope metadata, not {P2_OPT_KIND}."
            ),
        ),
        _entry(
            target_field="instrument.instrument_id",
            classification="MISSING",
            source_artifact=exp,
            source_field=None,
            source_authority="RESEARCH_OPTIMIZATION_EXPERIMENT",
            transformation=None,
            lossiness="TOTAL",
            reason="canonical_optimization_experiment_evidence_v1 has no InstrumentBindingV1 fields.",
        ),
        _entry(
            target_field="instrument.instrument_id",
            classification="MISSING",
            source_artifact=env,
            source_field="surface_id",
            source_authority="RESEARCH_ENVELOPE_RESOLVER",
            transformation=None,
            lossiness="TOTAL",
            reason="surface_id is optimization-surface identity, not trading instrument_id.",
        ),
        _entry(
            target_field="market_observation_epoch",
            classification="MISSING",
            source_artifact=exp,
            source_field=None,
            source_authority="RESEARCH_OPTIMIZATION_EXPERIMENT",
            transformation=None,
            lossiness="TOTAL",
            reason="Experiment evidence carries plane_identity only; no market_observation_epoch.",
        ),
        _entry(
            target_field="observed_at_unix",
            classification="MISSING",
            source_artifact=exp,
            source_field=None,
            source_authority="RESEARCH_OPTIMIZATION_EXPERIMENT",
            transformation=None,
            lossiness="TOTAL",
            reason="No authoritative observation timestamp on experiment evidence (wall-clock forbidden).",
        ),
        _entry(
            target_field="source_evidence_digest",
            classification="MECHANICAL_TRANSFORM",
            source_artifact=exp,
            source_field="reproducibility_digest",
            source_authority="RESEARCH_OPTIMIZATION_EXPERIMENT",
            transformation="copy_sha256_hex",
            lossiness="NONE",
            reason="Digest exists but remaining intake fields block bridge.",
        ),
        _entry(
            target_field="typed_payload_semantics",
            classification="SEMANTIC_TRANSFORM_REQUIRED",
            source_artifact=exp,
            source_field="evidence_slices",
            source_authority="RESEARCH_OPTIMIZATION_EXPERIMENT",
            transformation=None,
            lossiness="HIGH",
            reason=(
                "evidence_slices encode M4 search/challenger/OOS research classes; "
                "not a governed optimization_envelope_evidence_v1 payload."
            ),
        ),
        _entry(
            target_field="typed_payload_semantics",
            classification="SEMANTIC_TRANSFORM_REQUIRED",
            source_artifact=env,
            source_field="allowed_value_or_policy_domain",
            source_authority="RESEARCH_ENVELOPE_RESOLVER",
            transformation=None,
            lossiness="HIGH",
            reason="Optimizable envelope policy domain ≠ P2 optimization envelope evidence semantics.",
        ),
        _entry(
            target_field="producer_id",
            classification="MISSING",
            source_artifact=exp,
            source_field=None,
            source_authority="P2_REGISTRY_ONLY",
            transformation=None,
            lossiness="TOTAL",
            reason="Registry declares producer; no CURRENT module emits productive optimization envelope evidence.",
        ),
    ]
    summary = _summarize(fields)
    return {
        "schema_version": SCHEMA_VERSION,
        "target_evidence_kind": P2_OPT_KIND,
        "target_contract": "EvidenceIntakeRecordV1 + CanonicalMasterV2EvidenceEnvelopeV1 (P1/P2 A intake)",
        "candidate_source_artifacts": [exp, env],
        "owner_schema_equivalence_declared": False,
        "fields": fields,
        **summary,
        "verdict": "BLOCKED" if not summary["producer_bridge_allowed"] else "MECHANICALLY_ALLOWED",
        "earliest_blocker": summary["first_blocking_reason"],
    }


def run_meta_learning_contract_crosswalk_v1() -> dict[str, Any]:
    """Crosswalk meta_learning_routed_evidence_v1 vs meta_evidence_v1 (+ nested lineage)."""
    meta = META_EVIDENCE_SCHEMA
    nested = "meta_learning_evidence_v1"
    fields: list[dict[str, Any]] = [
        _entry(
            target_field="evidence_kind",
            classification="CONFLICTING",
            source_artifact=meta,
            source_field="schema_version",
            source_authority="RESEARCH_ONLY_ROUTING",
            transformation=None,
            lossiness="TOTAL",
            reason=f"Source {meta} ≠ target {P2_META_KIND}; schemas are not equated.",
        ),
        _entry(
            target_field="permitted_use",
            classification="CONFLICTING",
            source_artifact=meta,
            source_field="permitted_use_classification",
            source_authority="RESEARCH_ONLY_ROUTING",
            transformation=None,
            lossiness="TOTAL",
            reason="meta_evidence_v1 is RESEARCH_ONLY; productive promotion requires separate binding boundary.",
        ),
        _entry(
            target_field="instrument.instrument_id",
            classification="MISSING",
            source_artifact=meta,
            source_field=None,
            source_authority="RESEARCH_ONLY_ROUTING",
            transformation=None,
            lossiness="TOTAL",
            reason="meta_evidence_v1 carries no instrument_id.",
        ),
        _entry(
            target_field="instrument.instrument_id",
            classification="MISSING",
            source_artifact=nested,
            source_field="observed_regime_or_context_ref",
            source_authority="META_LEARNING_RESEARCH",
            transformation=None,
            lossiness="TOTAL",
            reason="observed_regime_or_context_ref is opaque regime ref, not InstrumentBindingV1.",
        ),
        _entry(
            target_field="market_observation_epoch",
            classification="MISSING",
            source_artifact=meta,
            source_field=None,
            source_authority="RESEARCH_ONLY_ROUTING",
            transformation=None,
            lossiness="TOTAL",
            reason="No market_observation_epoch in meta_evidence_v1 or nested meta_learning_evidence_v1.",
        ),
        _entry(
            target_field="observed_at_unix",
            classification="MISSING",
            source_artifact=meta,
            source_field=None,
            source_authority="RESEARCH_ONLY_ROUTING",
            transformation=None,
            lossiness="TOTAL",
            reason="No authoritative produced_at/observed_at; wall-clock fill forbidden.",
        ),
        _entry(
            target_field="freshness_horizon_seconds",
            classification="MISSING",
            source_artifact=meta,
            source_field=None,
            source_authority="RESEARCH_ONLY_ROUTING",
            transformation=None,
            lossiness="TOTAL",
            reason="No freshness basis in research routing envelope.",
        ),
        _entry(
            target_field="source_evidence_digest",
            classification="EXACT_SOURCE",
            source_artifact=meta,
            source_field="content_digest",
            source_authority="RESEARCH_ONLY_ROUTING",
            transformation="identity",
            lossiness="NONE",
            reason="Digest present on meta_evidence_v1 but identity fields still block promotion.",
        ),
        _entry(
            target_field="envelope_id",
            classification="MECHANICAL_TRANSFORM",
            source_artifact=meta,
            source_field="meta_evidence_record_id",
            source_authority="RESEARCH_ONLY_ROUTING",
            transformation="copy_string",
            lossiness="LOW",
            reason="Record id exists; does not satisfy instrument/epoch requirements for A intake.",
        ),
        _entry(
            target_field="producer_id",
            classification="MISSING",
            source_artifact=meta,
            source_field=None,
            source_authority="P2_REGISTRY_ONLY",
            transformation=None,
            lossiness="TOTAL",
            reason="P2 registry producer id is not emitted by research meta_evidence builder.",
        ),
        _entry(
            target_field="binding_context.instrument_epoch",
            classification="MISSING",
            source_artifact="authoritative_binding_context",
            source_field=None,
            source_authority="NONE_ON_CURRENT_MAIN",
            transformation=None,
            lossiness="TOTAL",
            reason=(
                "No CURRENT governed binding context pairs completed meta_evidence_v1 with "
                "InstrumentBindingV1 and market_observation_epoch without fabrication."
            ),
        ),
    ]
    summary = _summarize(fields)
    return {
        "schema_version": SCHEMA_VERSION,
        "target_evidence_kind": P2_META_KIND,
        "target_contract": "EvidenceIntakeRecordV1 + explicit promotion/binding boundary",
        "candidate_source_artifacts": [meta, nested],
        "meta_evidence_v1_equated_to_target": False,
        "fields": fields,
        **summary,
        "verdict": "BLOCKED" if not summary["producer_bridge_allowed"] else "MECHANICALLY_ALLOWED",
        "earliest_blocker": summary["first_blocking_reason"],
    }


def run_p5_contract_crosswalks_v1() -> dict[str, Any]:
    return {
        "optimization": run_optimization_contract_crosswalk_v1(),
        "meta_learning": run_meta_learning_contract_crosswalk_v1(),
    }
