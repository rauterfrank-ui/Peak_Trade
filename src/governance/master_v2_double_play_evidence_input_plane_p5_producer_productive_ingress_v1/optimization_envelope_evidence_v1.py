"""P5 optimization_envelope_evidence_v1 — governed producer artifact terminating at Component A."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    SCHEMA_VERSION as M5_SCHEMA_VERSION,
    validate_optimization_experiment_evidence_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.constants_v1 import (
    OPTIMIZATION_PRODUCER_ID,
    OPTIMIZATION_PRODUCER_VERSION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.p5_m4_m8_governed_binding_context_v1 import (
    SCHEMA_VERSION as BINDING_SCHEMA_VERSION,
    validate_p5_m4_m8_governed_evidence_binding_context_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "optimization_envelope_evidence_v1"
EVIDENCE_KIND: Final[str] = "optimization_envelope_evidence_v1"
ENVELOPE_DOMAIN: Final[str] = "peak_trade.p5.optimization_envelope_evidence.v1"

OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False


class OptimizationEnvelopeEvidenceError(ValueError):
    """Fail-closed optimization envelope evidence build/validation."""


def derive_optimization_envelope_evidence_id_v1(*, reproducibility_digest: str) -> str:
    return compute_content_sha256(
        {
            "domain": ENVELOPE_DOMAIN,
            "evidence_kind": EVIDENCE_KIND,
            "reproducibility_digest": reproducibility_digest,
        }
    )[:48]


def produce_optimization_envelope_evidence_v1(
    *,
    optimization_experiment_evidence: Mapping[str, Any],
    binding_context: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    m5 = validate_optimization_experiment_evidence_v1(optimization_experiment_evidence)
    binding = validate_p5_m4_m8_governed_evidence_binding_context_v1(binding_context)
    if binding["source_lineage_schema"] != M5_SCHEMA_VERSION:
        raise OptimizationEnvelopeEvidenceError("BINDING_SOURCE_SCHEMA_MISMATCH")
    m5_digest = str(m5.get("content_hash") or "")
    if binding["source_lineage_content_digest"] != m5_digest:
        raise OptimizationEnvelopeEvidenceError("BINDING_LINEAGE_DIGEST_MISMATCH")

    reproducibility_body = {
        "evidence_kind": EVIDENCE_KIND,
        "source_optimization_experiment_evidence_digest": m5_digest,
        "source_plane_identity": str(m5.get("plane_identity") or ""),
        "binding_context_digest": str(binding["binding_digest"]),
        "binding_record_id": str(binding["binding_record_id"]),
        "producer_id": OPTIMIZATION_PRODUCER_ID,
    }
    reproducibility_digest = compute_content_sha256(reproducibility_body)
    envelope_id = derive_optimization_envelope_evidence_id_v1(
        reproducibility_digest=reproducibility_digest
    )

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": ENVELOPE_DOMAIN,
        "evidence_kind": EVIDENCE_KIND,
        "envelope_evidence_id": envelope_id,
        "producer_id": OPTIMIZATION_PRODUCER_ID,
        "producer_version": OPTIMIZATION_PRODUCER_VERSION,
        "source_optimization_experiment_evidence_schema_version": M5_SCHEMA_VERSION,
        "source_optimization_experiment_evidence_digest": m5_digest,
        "source_plane_identity": str(m5.get("plane_identity") or ""),
        "binding_context_schema_version": BINDING_SCHEMA_VERSION,
        "binding_context_digest": str(binding["binding_digest"]),
        "binding_record_id": str(binding["binding_record_id"]),
        "instrument_ref": str(binding["instrument_ref"]),
        "observed_at": str(binding["observed_at"]),
        "market_observation_epoch": int(binding["market_observation_epoch"]),
        "typed_payload_digest": str(m5.get("reproducibility_digest") or ""),
        "reproducibility_digest": reproducibility_digest,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "trading_selection_effect": "NONE",
        "provenance": {
            "m5_record_id": str(m5.get("record_id") or ""),
            "market_context_content_digest": str(binding["market_context_content_digest"]),
            "market_context_id": str(binding["market_context_id"]),
        },
    }
    payload["content_hash"] = compute_content_sha256(
        {k: v for k, v in payload.items() if k != "content_hash"}
    )
    return validate_optimization_envelope_evidence_v1(payload)


def validate_optimization_envelope_evidence_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    if not isinstance(payload, Mapping):
        raise OptimizationEnvelopeEvidenceError("ENVELOPE_EVIDENCE_MUST_BE_MAPPING")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise OptimizationEnvelopeEvidenceError("ENVELOPE_SCHEMA_MISMATCH")
    if payload.get("evidence_kind") != EVIDENCE_KIND:
        raise OptimizationEnvelopeEvidenceError("EVIDENCE_KIND_MISMATCH")
    if payload.get("optimization_productive_authority") != OPTIMIZATION_PRODUCTIVE_AUTHORITY:
        raise OptimizationEnvelopeEvidenceError("PRODUCTIVE_AUTHORITY_MUST_BE_NONE")
    if payload.get("external_effect_authorized") is not False:
        raise OptimizationEnvelopeEvidenceError("EXTERNAL_EFFECT_MUST_BE_FALSE")
    digest = str(payload.get("reproducibility_digest") or "")
    if not is_valid_sha256_hex(digest):
        raise OptimizationEnvelopeEvidenceError("REPRODUCIBILITY_DIGEST_INVALID")
    content = str(payload.get("content_hash") or "")
    if not is_valid_sha256_hex(content):
        raise OptimizationEnvelopeEvidenceError("CONTENT_HASH_INVALID")
    if payload.get("producer_id") != OPTIMIZATION_PRODUCER_ID:
        raise OptimizationEnvelopeEvidenceError("PRODUCER_ID_MISMATCH")
    return MappingProxyType(dict(payload))
