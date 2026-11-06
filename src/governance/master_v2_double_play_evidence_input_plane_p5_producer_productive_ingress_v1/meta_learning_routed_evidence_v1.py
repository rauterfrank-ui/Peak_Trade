"""P5 meta_learning_routed_evidence_v1 — governed producer artifact terminating at Component A."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.constants_v1 import (
    META_LEARNING_PRODUCER_ID,
    META_LEARNING_PRODUCER_VERSION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.p5_m4_m8_governed_binding_context_v1 import (
    SCHEMA_VERSION as BINDING_SCHEMA_VERSION,
    validate_p5_m4_m8_governed_evidence_binding_context_v1,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    SCHEMA_VERSION as M6_EVIDENCE_SCHEMA_VERSION,
    validate_meta_learning_evidence_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "meta_learning_routed_evidence_v1"
EVIDENCE_KIND: Final[str] = "meta_learning_routed_evidence_v1"
ROUTED_DOMAIN: Final[str] = "peak_trade.p5.meta_learning_routed_evidence.v1"

META_EVIDENCE_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False


class MetaLearningRoutedEvidenceError(ValueError):
    """Fail-closed meta-learning routed evidence build/validation."""


def derive_meta_learning_routed_evidence_id_v1(*, reproducibility_digest: str) -> str:
    return compute_content_sha256(
        {
            "domain": ROUTED_DOMAIN,
            "evidence_kind": EVIDENCE_KIND,
            "reproducibility_digest": reproducibility_digest,
        }
    )[:48]


def produce_meta_learning_routed_evidence_v1(
    *,
    meta_learning_evidence: Mapping[str, Any],
    binding_context: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    m6 = validate_meta_learning_evidence_v1(meta_learning_evidence)
    binding = validate_p5_m4_m8_governed_evidence_binding_context_v1(binding_context)
    if binding["source_lineage_schema"] != M6_EVIDENCE_SCHEMA_VERSION:
        raise MetaLearningRoutedEvidenceError("BINDING_SOURCE_SCHEMA_MISMATCH")
    m6_digest = str(m6.get("reproducibility_digest") or "")
    if binding["source_lineage_content_digest"] != m6_digest:
        raise MetaLearningRoutedEvidenceError("BINDING_M6_DIGEST_MISMATCH")
    m6_lineage_digest = str(m6.get("source_optimization_experiment_evidence_digest") or "")

    reproducibility_body = {
        "evidence_kind": EVIDENCE_KIND,
        "source_meta_learning_evidence_id": str(m6.get("meta_evidence_id") or ""),
        "source_meta_learning_reproducibility_digest": str(m6.get("reproducibility_digest") or ""),
        "binding_context_digest": str(binding["binding_digest"]),
        "producer_id": META_LEARNING_PRODUCER_ID,
    }
    reproducibility_digest = compute_content_sha256(reproducibility_body)
    routed_id = derive_meta_learning_routed_evidence_id_v1(
        reproducibility_digest=reproducibility_digest
    )

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": ROUTED_DOMAIN,
        "evidence_kind": EVIDENCE_KIND,
        "routed_evidence_id": routed_id,
        "producer_id": META_LEARNING_PRODUCER_ID,
        "producer_version": META_LEARNING_PRODUCER_VERSION,
        "source_meta_learning_evidence_schema_version": M6_EVIDENCE_SCHEMA_VERSION,
        "source_meta_learning_evidence_id": str(m6.get("meta_evidence_id") or ""),
        "source_meta_learning_reproducibility_digest": str(m6.get("reproducibility_digest") or ""),
        "source_optimization_experiment_evidence_digest": m6_lineage_digest,
        "binding_context_schema_version": BINDING_SCHEMA_VERSION,
        "binding_context_digest": str(binding["binding_digest"]),
        "binding_record_id": str(binding["binding_record_id"]),
        "instrument_ref": str(binding["instrument_ref"]),
        "observed_at": str(binding["observed_at"]),
        "market_observation_epoch": int(binding["market_observation_epoch"]),
        "typed_payload_digest": str(m6.get("reproducibility_digest") or ""),
        "reproducibility_digest": reproducibility_digest,
        "meta_evidence_authority": META_EVIDENCE_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "trading_selection_effect": "NONE",
        "provenance": {
            "market_context_content_digest": str(binding["market_context_content_digest"]),
            "market_context_id": str(binding["market_context_id"]),
            "meta_evidence_authority": META_EVIDENCE_AUTHORITY,
        },
    }
    payload["content_hash"] = compute_content_sha256(
        {k: v for k, v in payload.items() if k != "content_hash"}
    )
    return validate_meta_learning_routed_evidence_v1(payload)


def validate_meta_learning_routed_evidence_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    if not isinstance(payload, Mapping):
        raise MetaLearningRoutedEvidenceError("ROUTED_EVIDENCE_MUST_BE_MAPPING")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise MetaLearningRoutedEvidenceError("ROUTED_SCHEMA_MISMATCH")
    if payload.get("evidence_kind") != EVIDENCE_KIND:
        raise MetaLearningRoutedEvidenceError("EVIDENCE_KIND_MISMATCH")
    if payload.get("meta_evidence_authority") != META_EVIDENCE_AUTHORITY:
        raise MetaLearningRoutedEvidenceError("META_EVIDENCE_AUTHORITY_MUST_BE_NONE")
    if payload.get("external_effect_authorized") is not False:
        raise MetaLearningRoutedEvidenceError("EXTERNAL_EFFECT_MUST_BE_FALSE")
    digest = str(payload.get("reproducibility_digest") or "")
    if not is_valid_sha256_hex(digest):
        raise MetaLearningRoutedEvidenceError("REPRODUCIBILITY_DIGEST_INVALID")
    content = str(payload.get("content_hash") or "")
    if not is_valid_sha256_hex(content):
        raise MetaLearningRoutedEvidenceError("CONTENT_HASH_INVALID")
    if payload.get("producer_id") != META_LEARNING_PRODUCER_ID:
        raise MetaLearningRoutedEvidenceError("PRODUCER_ID_MISMATCH")
    return MappingProxyType(dict(payload))
