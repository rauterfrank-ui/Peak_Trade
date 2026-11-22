"""Meta-learning evidence v1 — typed evidence about optimization process (self-learning side).

Separate namespace from optimization experiment evidence and learning_state_record_v0.
Does not authorize trading, search, promotion, or runtime mutation.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    compute_content_hash_v0,
    is_valid_sha256_hex_v0,
)

SCHEMA_VERSION: Final[str] = "meta_learning_evidence_v1"
META_LEARNING_EVIDENCE_DOMAIN: Final[str] = "peak_trade.learning.ddo.meta_learning_evidence.v1"
UNIVERSE_CLASS_SELF_LEARNING: Final[str] = "SELF_LEARNING_UNIVERSE"
EVIDENCE_CLASS_META_LEARNING: Final[str] = "META_LEARNING_EVIDENCE"
UNKNOWN_UNAVAILABLE: Final[str] = "UNKNOWN_UNAVAILABLE"

META_EVIDENCE_AUTHORITY: Final[str] = "NONE"
LEARNING_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
PROPOSAL_NOT_AUTHORITY: Final[bool] = True

CANONICAL_META_LEARNING_ANALYZER_REF: Final[str] = "peak_trade.canonical_meta_learning.v1"
CANONICAL_META_LEARNING_ANALYZER_SCHEMA: Final[str] = "canonical_meta_learning_v1"

_REQUIRED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "domain",
        "meta_evidence_id",
        "source_experiment_ids",
        "source_envelope_versions",
        "observed_regime_or_context_ref",
        "optimization_family",
        "search_method",
        "repeated_success_or_failure_pattern",
        "oos_robustness_pattern",
        "cost_slippage_failure_pattern",
        "predictive_evidence_features",
        "uncertainty",
        "support_count",
        "provenance",
        "reproducibility_digest",
        "meta_evidence_authority",
        "source_optimization_experiment_evidence_record_id",
        "source_optimization_experiment_evidence_digest",
    }
)


class MetaLearningEvidenceValidationError(ValueError):
    """Fail-closed meta-learning evidence validation error."""


def derive_meta_evidence_id_v1(*, reproducibility_digest: str) -> str:
    return compute_content_hash_v0(
        {
            "digest_domain": f"{META_LEARNING_EVIDENCE_DOMAIN}.meta_evidence_id",
            "reproducibility_digest": reproducibility_digest,
            "schema_version": SCHEMA_VERSION,
        }
    )


def validate_meta_learning_evidence_v1(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    if not isinstance(payload, Mapping):
        raise MetaLearningEvidenceValidationError("META_LEARNING_EVIDENCE_MUST_BE_MAPPING")
    missing = _REQUIRED_FIELDS - frozenset(payload.keys())
    if missing:
        raise MetaLearningEvidenceValidationError("META_LEARNING_EVIDENCE_FIELDS_MISSING")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise MetaLearningEvidenceValidationError("META_LEARNING_EVIDENCE_SCHEMA_MISMATCH")
    if payload.get("meta_evidence_authority") != META_EVIDENCE_AUTHORITY:
        raise MetaLearningEvidenceValidationError("META_EVIDENCE_AUTHORITY_MUST_BE_NONE")
    digest = payload.get("reproducibility_digest")
    if not is_valid_sha256_hex_v0(str(digest or "")):
        raise MetaLearningEvidenceValidationError("REPRODUCIBILITY_DIGEST_INVALID")
    meta_id = payload.get("meta_evidence_id")
    if meta_id != derive_meta_evidence_id_v1(reproducibility_digest=str(digest)):
        raise MetaLearningEvidenceValidationError("META_EVIDENCE_ID_MISMATCH")
    support_count = payload.get("support_count")
    if isinstance(support_count, bool) or not isinstance(support_count, int) or support_count < 0:
        raise MetaLearningEvidenceValidationError("SUPPORT_COUNT_INVALID")
    source_ids = payload.get("source_experiment_ids")
    if not isinstance(source_ids, (list, tuple)):
        raise MetaLearningEvidenceValidationError("SOURCE_EXPERIMENT_IDS_INVALID")
    if support_count != len(source_ids):
        raise MetaLearningEvidenceValidationError("SUPPORT_COUNT_SOURCE_MISMATCH")
    for flag_name in (
        "learning_state_mutation",
        "search_execution_performed",
        "promotion_performed",
    ):
        if payload.get(flag_name) is True:
            raise MetaLearningEvidenceValidationError(f"{flag_name.upper()}_FORBIDDEN_TRUE")
    if payload.get("domain") != META_LEARNING_EVIDENCE_DOMAIN:
        raise MetaLearningEvidenceValidationError("META_LEARNING_EVIDENCE_DOMAIN_MISMATCH")
    declarations = {
        "universe_class": UNIVERSE_CLASS_SELF_LEARNING,
        "evidence_class": EVIDENCE_CLASS_META_LEARNING,
        "learning_state_mutation": False,
        "search_execution_performed": False,
        "promotion_performed": False,
        "external_effect_authorized": False,
        "proposal_not_authority": True,
    }
    for field, expected in declarations.items():
        supplied = payload.get(field)
        if supplied is not None and (type(supplied) is not type(expected) or supplied != expected):
            raise MetaLearningEvidenceValidationError(f"META_LEARNING_DECLARATION_INVALID:{field}")
    return MappingProxyType(dict(payload))
