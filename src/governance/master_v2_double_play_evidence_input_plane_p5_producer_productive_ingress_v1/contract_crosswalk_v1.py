"""Field-by-field P5 contract crosswalks (Optimization / Meta-Learning) — read-only."""

from __future__ import annotations

from typing import Any, Final, Literal

from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    SCHEMA_VERSION as M5_SCHEMA,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    BoundedL6EvidenceKindV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.meta_learning_routed_evidence_v1 import (
    SCHEMA_VERSION as META_ROUTED_SCHEMA,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.optimization_envelope_evidence_v1 import (
    SCHEMA_VERSION as OPT_ENVELOPE_SCHEMA,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.p5_m4_m8_governed_binding_context_v1 import (
    SCHEMA_VERSION as BINDING_SCHEMA,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    SCHEMA_VERSION as M6_SCHEMA,
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
    """Crosswalk P2 optimization_envelope_evidence_v1 via M5 + governed binding context."""
    fields: list[dict[str, Any]] = [
        _entry(
            target_field="target_schema_validator",
            classification="EXACT_SOURCE",
            source_artifact=OPT_ENVELOPE_SCHEMA,
            source_field="validate_optimization_envelope_evidence_v1",
            source_authority="P5_PRODUCER_CLOSURE",
            transformation="validate_module",
            lossiness="NONE",
            reason="Governed P5 producer artifact validator on CURRENT main.",
        ),
        _entry(
            target_field="evidence_kind",
            classification="EXACT_SOURCE",
            source_artifact=OPT_ENVELOPE_SCHEMA,
            source_field="evidence_kind",
            source_authority="P5_PRODUCER_CLOSURE",
            transformation="identity",
            lossiness="NONE",
            reason=f"Producer emits {P2_OPT_KIND}; does not equate raw {M5_SCHEMA}.",
        ),
        _entry(
            target_field="instrument.instrument_id",
            classification="MECHANICAL_TRANSFORM",
            source_artifact=BINDING_SCHEMA,
            source_field="instrument_ref",
            source_authority="MARKET_CONTEXT_V1_BINDING",
            transformation="instrument_binding_from_ref_v1",
            lossiness="NONE",
            reason="Instrument sourced from authoritative market_context_v1 via binding context.",
        ),
        _entry(
            target_field="market_observation_epoch",
            classification="EXACT_SOURCE",
            source_artifact=BINDING_SCHEMA,
            source_field="market_observation_epoch",
            source_authority="GOVERNED_BINDING_CONTEXT",
            transformation="identity",
            lossiness="NONE",
            reason="Epoch supplied in binding context; not inferred from M5 plane_identity.",
        ),
        _entry(
            target_field="observed_at_unix",
            classification="MECHANICAL_TRANSFORM",
            source_artifact=BINDING_SCHEMA,
            source_field="observed_at",
            source_authority="MARKET_CONTEXT_V1_BINDING",
            transformation="parse_iso8601_utc_to_unix",
            lossiness="NONE",
            reason="Timestamp from market_context_v1 observed_at only.",
        ),
        _entry(
            target_field="source_evidence_digest",
            classification="EXACT_SOURCE",
            source_artifact=OPT_ENVELOPE_SCHEMA,
            source_field="content_hash",
            source_authority="P5_PRODUCER_CLOSURE",
            transformation="identity",
            lossiness="NONE",
            reason="P5 envelope content_hash is A intake source digest.",
        ),
        _entry(
            target_field="typed_payload_semantics",
            classification="MECHANICAL_TRANSFORM",
            source_artifact=M5_SCHEMA,
            source_field="reproducibility_digest",
            source_authority="RESEARCH_OPTIMIZATION_EXPERIMENT",
            transformation="opaque_digest_ref_only",
            lossiness="NONE",
            reason="M5 research slices referenced by digest; no trading semantics added.",
        ),
        _entry(
            target_field="producer_id",
            classification="EXACT_SOURCE",
            source_artifact=OPT_ENVELOPE_SCHEMA,
            source_field="producer_id",
            source_authority="P2_REGISTRY_ALIGNED",
            transformation="identity",
            lossiness="NONE",
            reason="Producer id matches P2 registry optimization.envelope_evidence.producer.",
        ),
        _entry(
            target_field="m5_lineage_lock",
            classification="EXACT_SOURCE",
            source_artifact=M5_SCHEMA,
            source_field="content_hash",
            source_authority="RESEARCH_OPTIMIZATION_EXPERIMENT",
            transformation="binding_context.source_lineage_content_digest",
            lossiness="NONE",
            reason="Binding context locks M5 content_hash before envelope emission.",
        ),
    ]
    summary = _summarize(fields)
    return {
        "schema_version": SCHEMA_VERSION,
        "target_evidence_kind": P2_OPT_KIND,
        "target_contract": "EvidenceIntakeRecordV1 + CanonicalMasterV2EvidenceEnvelopeV1 (P1/P2 A intake)",
        "candidate_source_artifacts": [M5_SCHEMA, OPT_ENVELOPE_SCHEMA, BINDING_SCHEMA],
        "owner_schema_equivalence_declared": False,
        "fields": fields,
        **summary,
        "verdict": "BLOCKED" if not summary["producer_bridge_allowed"] else "MECHANICALLY_ALLOWED",
        "earliest_blocker": summary["first_blocking_reason"],
    }


def run_meta_learning_contract_crosswalk_v1() -> dict[str, Any]:
    """Crosswalk meta_learning_routed_evidence_v1 via M6 meta_learning_evidence_v1 + binding."""
    fields: list[dict[str, Any]] = [
        _entry(
            target_field="evidence_kind",
            classification="EXACT_SOURCE",
            source_artifact=META_ROUTED_SCHEMA,
            source_field="evidence_kind",
            source_authority="P5_PRODUCER_CLOSURE",
            transformation="identity",
            lossiness="NONE",
            reason=f"Producer emits {P2_META_KIND}; meta_evidence_v1 is not equated.",
        ),
        _entry(
            target_field="instrument.instrument_id",
            classification="MECHANICAL_TRANSFORM",
            source_artifact=BINDING_SCHEMA,
            source_field="instrument_ref",
            source_authority="MARKET_CONTEXT_V1_BINDING",
            transformation="instrument_binding_from_ref_v1",
            lossiness="NONE",
            reason="Instrument from market_context_v1 binding; not from observed_regime_or_context_ref.",
        ),
        _entry(
            target_field="market_observation_epoch",
            classification="EXACT_SOURCE",
            source_artifact=BINDING_SCHEMA,
            source_field="market_observation_epoch",
            source_authority="GOVERNED_BINDING_CONTEXT",
            transformation="identity",
            lossiness="NONE",
            reason="Epoch from binding context.",
        ),
        _entry(
            target_field="observed_at_unix",
            classification="MECHANICAL_TRANSFORM",
            source_artifact=BINDING_SCHEMA,
            source_field="observed_at",
            source_authority="MARKET_CONTEXT_V1_BINDING",
            transformation="parse_iso8601_utc_to_unix",
            lossiness="NONE",
            reason="Timestamp from market_context_v1 observed_at only.",
        ),
        _entry(
            target_field="freshness_horizon_seconds",
            classification="EXACT_SOURCE",
            source_artifact=BINDING_SCHEMA,
            source_field="freshness_horizon_seconds",
            source_authority="GOVERNED_BINDING_CONTEXT",
            transformation="identity",
            lossiness="NONE",
            reason="Freshness horizon carried from binding context defaults.",
        ),
        _entry(
            target_field="source_evidence_digest",
            classification="EXACT_SOURCE",
            source_artifact=META_ROUTED_SCHEMA,
            source_field="content_hash",
            source_authority="P5_PRODUCER_CLOSURE",
            transformation="identity",
            lossiness="NONE",
            reason="Routed envelope content_hash is A intake source digest.",
        ),
        _entry(
            target_field="envelope_id",
            classification="EXACT_SOURCE",
            source_artifact=META_ROUTED_SCHEMA,
            source_field="routed_evidence_id",
            source_authority="P5_PRODUCER_CLOSURE",
            transformation="identity",
            lossiness="NONE",
            reason="Deterministic routed evidence id from reproducibility digest.",
        ),
        _entry(
            target_field="producer_id",
            classification="EXACT_SOURCE",
            source_artifact=META_ROUTED_SCHEMA,
            source_field="producer_id",
            source_authority="P2_REGISTRY_ALIGNED",
            transformation="identity",
            lossiness="NONE",
            reason="Producer id matches P2 registry meta_learning.routed_evidence.producer.",
        ),
        _entry(
            target_field="binding_context.instrument_epoch",
            classification="EXACT_SOURCE",
            source_artifact=BINDING_SCHEMA,
            source_field="binding_digest",
            source_authority="GOVERNED_BINDING_CONTEXT",
            transformation="identity",
            reason="Binding digest locks M6 reproducibility_digest lineage.",
            lossiness="NONE",
        ),
        _entry(
            target_field="m6_lineage_lock",
            classification="EXACT_SOURCE",
            source_artifact=M6_SCHEMA,
            source_field="reproducibility_digest",
            source_authority="META_LEARNING_RESEARCH",
            transformation="binding_context.source_lineage_content_digest",
            lossiness="NONE",
            reason="Binding context locks M6 reproducibility_digest before routed emission.",
        ),
    ]
    summary = _summarize(fields)
    return {
        "schema_version": SCHEMA_VERSION,
        "target_evidence_kind": P2_META_KIND,
        "target_contract": "EvidenceIntakeRecordV1 + explicit promotion/binding boundary",
        "candidate_source_artifacts": [M6_SCHEMA, META_ROUTED_SCHEMA, BINDING_SCHEMA],
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
