"""Optimization experiment evidence v1 — typed M4 return payload (optimization universe).

Projects a completed M4 experiment-plane result into a versioned evidence record for
self-learning return-input validation. Does not mutate learning state or invoke meta-learning.
"""

from __future__ import annotations

import hashlib
import logging
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_advanced_search_v1 import (
    SCHEMA_VERSION as ADVANCED_SEARCH_SCHEMA_VERSION,
)
from src.experiments.canonical_champion_challenger_v1 import (
    SCHEMA_VERSION as CHAMPION_CHALLENGER_SCHEMA_VERSION,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    ENVELOPE_CONTRACT_VERSION,
    SCHEMA_VERSION as OPTIMIZABLE_ENVELOPE_SCHEMA_VERSION,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
    SCHEMA_VERSION as EXPERIMENT_PLANE_SCHEMA_VERSION,
)
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    SCHEMA_VERSION as OPTIMIZATION_LEARNING_INPUT_SCHEMA_VERSION,
)
from src.experiments.canonical_robustness_suite_v1 import (
    SCHEMA_VERSION as ROBUSTNESS_SUITE_SCHEMA_VERSION,
)
from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_VERSION_LEARNING_EVIDENCE_RECORD_V1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "canonical_optimization_experiment_evidence_v1"
OPTIMIZATION_EXPERIMENT_EVIDENCE_DOMAIN: Final[str] = (
    "peak_trade.optimization_experiment_evidence.v1"
)
DIGEST_ALGORITHM: Final[str] = "sha256"
UNIVERSE_CLASS_OPTIMIZATION: Final[str] = "OPTIMIZATION_UNIVERSE"
EVIDENCE_CLASS_OPTIMIZATION_EXPERIMENT: Final[str] = "OPTIMIZATION_EXPERIMENT_EVIDENCE"

CLASS_SEARCH_EVIDENCE: Final[str] = "SEARCH_EVIDENCE"
CLASS_CHALLENGER_EVIDENCE: Final[str] = "CHALLENGER_EVIDENCE"
CLASS_OOS_EVIDENCE: Final[str] = "OOS_EVIDENCE"
CLASS_ROBUSTNESS_EVIDENCE: Final[str] = "ROBUSTNESS_EVIDENCE"
CLASS_ECONOMIC_EVIDENCE: Final[str] = "ECONOMIC_EVIDENCE"
CLASS_FAILURE_EVIDENCE: Final[str] = "FAILURE_EVIDENCE"
CLASS_META_EVIDENCE_SOURCE_REF: Final[str] = "META_EVIDENCE_SOURCE_REF"

REQUIRED_EVIDENCE_CLASSES: Final[frozenset[str]] = frozenset(
    {
        CLASS_SEARCH_EVIDENCE,
        CLASS_CHALLENGER_EVIDENCE,
        CLASS_OOS_EVIDENCE,
        CLASS_ROBUSTNESS_EVIDENCE,
        CLASS_ECONOMIC_EVIDENCE,
        CLASS_FAILURE_EVIDENCE,
        CLASS_META_EVIDENCE_SOURCE_REF,
    }
)

OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
PROPOSAL_NOT_AUTHORITY: Final[bool] = True

_LOGGER = logging.getLogger(__name__)


class CanonicalOptimizationExperimentEvidenceError(ValueError):
    """Fail-closed optimization experiment evidence build/validation error."""


def _json_safe(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def derive_optimization_experiment_evidence_id_v1(*, plane_identity: str) -> str:
    digest = hashlib.sha256(plane_identity.encode("utf-8")).hexdigest()
    return f"opt.exp_ev.{digest[:40]}"


def build_optimization_experiment_evidence_from_plane_v1(
    plane_result: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    if plane_result.get("schema_version") != EXPERIMENT_PLANE_SCHEMA_VERSION:
        raise CanonicalOptimizationExperimentEvidenceError("PLANE_SCHEMA_VERSION_MISMATCH")
    if plane_result.get("status") != PLANE_STATUS_COMPLETE:
        raise CanonicalOptimizationExperimentEvidenceError("PLANE_STATUS_NOT_COMPLETE")
    chain = plane_result.get("chain")
    if not isinstance(chain, Mapping):
        raise CanonicalOptimizationExperimentEvidenceError("PLANE_CHAIN_MISSING")
    plane_identity = str(plane_result.get("plane_identity") or "")
    if not is_valid_sha256_hex(plane_identity):
        raise CanonicalOptimizationExperimentEvidenceError("PLANE_IDENTITY_INVALID")

    learning_input = chain.get("learning_input_validation")
    if not isinstance(learning_input, Mapping):
        raise CanonicalOptimizationExperimentEvidenceError("LEARNING_INPUT_VALIDATION_MISSING")
    learning_evidence_digest = learning_input.get("learning_evidence_digest")
    if not is_valid_sha256_hex(str(learning_evidence_digest or "")):
        raise CanonicalOptimizationExperimentEvidenceError("LEARNING_EVIDENCE_DIGEST_INVALID")

    offline_context = chain.get("offline_research_context")
    if not isinstance(offline_context, Mapping):
        raise CanonicalOptimizationExperimentEvidenceError("OFFLINE_CONTEXT_MISSING")
    envelope_resolution = offline_context.get("envelope_resolution")
    if not isinstance(envelope_resolution, Mapping):
        raise CanonicalOptimizationExperimentEvidenceError("ENVELOPE_RESOLUTION_MISSING")

    selected = chain.get("selected_candidate")
    challenger_eval = chain.get("challenger_evaluation")
    proposal = chain.get("proposal")
    failure_evidence = chain.get("failure_evidence")
    if not isinstance(selected, Mapping) or not isinstance(challenger_eval, Mapping):
        raise CanonicalOptimizationExperimentEvidenceError("CANDIDATE_OR_EVALUATION_MISSING")
    if not isinstance(proposal, Mapping):
        raise CanonicalOptimizationExperimentEvidenceError("PROPOSAL_MISSING")
    if failure_evidence is None:
        failure_evidence = []

    search_identity = str(chain.get("search_identity") or "")
    if not is_valid_sha256_hex(search_identity):
        raise CanonicalOptimizationExperimentEvidenceError("SEARCH_IDENTITY_INVALID")

    robustness_digest = chain.get("robustness_evidence_digest")
    if not isinstance(robustness_digest, Mapping):
        raise CanonicalOptimizationExperimentEvidenceError("ROBUSTNESS_EVIDENCE_DIGEST_MISSING")

    evidence_slices = {
        CLASS_SEARCH_EVIDENCE: {
            "search_identity": search_identity,
            "schema_version": ADVANCED_SEARCH_SCHEMA_VERSION,
            "candidate_ref": selected.get("candidate_ref"),
            "experiment_id": selected.get("experiment_id"),
        },
        CLASS_CHALLENGER_EVIDENCE: {
            "schema_version": CHAMPION_CHALLENGER_SCHEMA_VERSION,
            "evaluation_digest": compute_content_sha256(_json_safe(challenger_eval)),
            "overall_disposition": challenger_eval.get("overall_disposition"),
            "proposal_disposition": proposal.get("disposition"),
        },
        CLASS_OOS_EVIDENCE: {
            "schema_version": ROBUSTNESS_SUITE_SCHEMA_VERSION,
            "observation_kind": "OFFLINE_OOS_PROJECTION",
            "robustness_evidence_integrity": dict(robustness_digest),
        },
        CLASS_ROBUSTNESS_EVIDENCE: {
            "schema_version": ROBUSTNESS_SUITE_SCHEMA_VERSION,
            "robustness_suite_identity": proposal.get("robustness_suite_identity"),
            "robustness_evidence_integrity": dict(robustness_digest),
        },
        CLASS_ECONOMIC_EVIDENCE: {
            "evidence_kind": "OPAQUE_LINEAGE_REF_ONLY",
            "source_learning_evidence_digest": str(learning_evidence_digest),
            "numeric_calibration_authority": "NONE",
        },
        CLASS_FAILURE_EVIDENCE: {
            "failure_evidence_count": int(chain.get("failure_evidence_count") or 0),
            "failure_records_digest": compute_content_sha256(
                {"failure_evidence": _json_safe(list(failure_evidence))}
            ),
            "failure_records": _json_safe(list(failure_evidence)),
        },
        CLASS_META_EVIDENCE_SOURCE_REF: {
            "meta_learning_ingest_status": "NOT_INGESTED_M6_DEFERRED",
            "capability_ref": "peak_trade.canonical_meta_learning.v1",
            "schema_version": "canonical_meta_learning_v1",
        },
    }
    missing_classes = REQUIRED_EVIDENCE_CLASSES - frozenset(evidence_slices.keys())
    if missing_classes:
        raise CanonicalOptimizationExperimentEvidenceError("EVIDENCE_CLASS_MISSING")

    version_bindings = {
        "experiment_plane_schema_version": EXPERIMENT_PLANE_SCHEMA_VERSION,
        "optimization_learning_input_schema_version": OPTIMIZATION_LEARNING_INPUT_SCHEMA_VERSION,
        "learning_evidence_record_schema_version": SCHEMA_VERSION_LEARNING_EVIDENCE_RECORD_V1,
        "optimizable_envelope_schema_version": OPTIMIZABLE_ENVELOPE_SCHEMA_VERSION,
        "optimizable_envelope_contract_version": ENVELOPE_CONTRACT_VERSION,
        "advanced_search_schema_version": ADVANCED_SEARCH_SCHEMA_VERSION,
        "robustness_suite_schema_version": ROBUSTNESS_SUITE_SCHEMA_VERSION,
        "champion_challenger_schema_version": CHAMPION_CHALLENGER_SCHEMA_VERSION,
    }

    reproducibility_body = {
        "plane_identity": plane_identity,
        "learning_evidence_digest": str(learning_evidence_digest),
        "search_identity": search_identity,
        "candidate_ref": selected.get("candidate_ref"),
        "evidence_slices": evidence_slices,
        "version_bindings": version_bindings,
    }
    reproducibility_digest = compute_content_sha256(reproducibility_body)
    record_id = derive_optimization_experiment_evidence_id_v1(plane_identity=plane_identity)

    canonical: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": OPTIMIZATION_EXPERIMENT_EVIDENCE_DOMAIN,
        "record_id": record_id,
        "universe_class": UNIVERSE_CLASS_OPTIMIZATION,
        "evidence_class": EVIDENCE_CLASS_OPTIMIZATION_EXPERIMENT,
        "plane_identity": plane_identity,
        "source_plane_schema_version": EXPERIMENT_PLANE_SCHEMA_VERSION,
        "learning_evidence_digest": str(learning_evidence_digest),
        "envelope_resolution_digest": str(envelope_resolution.get("result_digest")),
        "template_identity_digest": chain.get("template_identity_digest"),
        "candidate_experiment_id": selected.get("experiment_id"),
        "candidate_ref": selected.get("candidate_ref"),
        "version_bindings": version_bindings,
        "evidence_slices": evidence_slices,
        "provenance": {
            "source": "canonical_optimization_universe_experiment_plane_v1",
            "plane_result_digest": plane_result.get("result_digest"),
            "offline_context_digest": offline_context.get("context_digest"),
            "decision_config_ref": plane_result.get("decision_config"),
        },
        "reproducibility_digest": reproducibility_digest,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "proposal_not_authority": PROPOSAL_NOT_AUTHORITY,
        "learning_state_mutation": False,
        "meta_learning_ingest": False,
    }
    canonical["content_hash"] = compute_content_sha256(
        _json_safe({key: value for key, value in canonical.items() if key != "content_hash"})
    )
    validated = validate_optimization_experiment_evidence_v1(canonical)
    _LOGGER.debug("built optimization experiment evidence id=%s", record_id)
    return validated


def validate_optimization_experiment_evidence_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    if not isinstance(payload, Mapping):
        raise CanonicalOptimizationExperimentEvidenceError("EVIDENCE_MUST_BE_MAPPING")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise CanonicalOptimizationExperimentEvidenceError("EVIDENCE_SCHEMA_VERSION_MISMATCH")
    if payload.get("universe_class") != UNIVERSE_CLASS_OPTIMIZATION:
        raise CanonicalOptimizationExperimentEvidenceError("UNIVERSE_CLASS_INVALID")
    if payload.get("evidence_class") != EVIDENCE_CLASS_OPTIMIZATION_EXPERIMENT:
        raise CanonicalOptimizationExperimentEvidenceError("EVIDENCE_CLASS_INVALID")
    if payload.get("optimization_productive_authority") != "NONE":
        raise CanonicalOptimizationExperimentEvidenceError("PRODUCTIVE_AUTHORITY_MUST_BE_NONE")
    for flag in ("learning_state_mutation", "meta_learning_ingest", "external_effect_authorized"):
        if payload.get(flag) is not False:
            raise CanonicalOptimizationExperimentEvidenceError(f"{flag.upper()}_MUST_BE_FALSE")
    digest = payload.get("reproducibility_digest")
    if not is_valid_sha256_hex(str(digest or "")):
        raise CanonicalOptimizationExperimentEvidenceError("REPRODUCIBILITY_DIGEST_INVALID")
    slices = payload.get("evidence_slices")
    if not isinstance(slices, Mapping):
        raise CanonicalOptimizationExperimentEvidenceError("EVIDENCE_SLICES_MISSING")
    if frozenset(slices.keys()) != REQUIRED_EVIDENCE_CLASSES:
        raise CanonicalOptimizationExperimentEvidenceError("EVIDENCE_SLICES_INCOMPLETE")
    return MappingProxyType(dict(payload))
