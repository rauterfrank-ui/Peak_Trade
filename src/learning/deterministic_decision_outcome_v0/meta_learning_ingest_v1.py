"""Meta-learning ingest v1 — project M5 optimization experiment evidence to meta evidence."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_meta_learning_v1 import (
    META_LEARNING_AUTHORITY as CANONICAL_ANALYZER_AUTHORITY,
    META_LEARNING_DOMAIN as CANONICAL_ANALYZER_DOMAIN,
    SCHEMA_VERSION as CANONICAL_ANALYZER_SCHEMA_VERSION,
)
from src.experiments.canonical_optimizable_envelope_v1 import SYNTHETIC_OFFLINE_SURFACE_ID
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    CLASS_CHALLENGER_EVIDENCE,
    CLASS_ECONOMIC_EVIDENCE,
    CLASS_FAILURE_EVIDENCE,
    CLASS_OOS_EVIDENCE,
    CLASS_ROBUSTNESS_EVIDENCE,
    CLASS_SEARCH_EVIDENCE,
    SCHEMA_VERSION as OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION,
    validate_optimization_experiment_evidence_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import OFFLINE_CONTEXT_KIND
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    CANONICAL_META_LEARNING_ANALYZER_REF,
    CANONICAL_META_LEARNING_ANALYZER_SCHEMA,
    EVIDENCE_CLASS_META_LEARNING,
    META_EVIDENCE_AUTHORITY,
    SCHEMA_VERSION as META_LEARNING_EVIDENCE_SCHEMA_VERSION,
    UNKNOWN_UNAVAILABLE,
    UNIVERSE_CLASS_SELF_LEARNING,
    derive_meta_evidence_id_v1,
    validate_meta_learning_evidence_v1,
)
from src.learning.deterministic_decision_outcome_v0.self_learning_optimization_return_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT,
    SCHEMA_VERSION as RETURN_INPUT_SCHEMA_VERSION,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "meta_learning_ingest_v1"
META_LEARNING_INGEST_DOMAIN: Final[str] = "peak_trade.learning.ddo.meta_learning_ingest.v1"

INGEST_STATUS_COMPLETE: Final[str] = "META_LEARNING_INGEST_COMPLETE"
INGEST_STATUS_REJECTED_ACK: Final[str] = "META_LEARNING_INGEST_REJECTED_RETURN_ACK"
INGEST_STATUS_REJECTED_STALE: Final[str] = "META_LEARNING_INGEST_REJECTED_STALE_CONTRACT"
INGEST_STATUS_REJECTED_OUT_OF_ORDER: Final[str] = "META_LEARNING_INGEST_REJECTED_OUT_OF_ORDER"
INGEST_STATUS_REJECTED_MALFORMED: Final[str] = "META_LEARNING_INGEST_REJECTED_MALFORMED"
INGEST_STATUS_REJECTED_AUTHORITY: Final[str] = "META_LEARNING_INGEST_REJECTED_AUTHORITY_BOUNDARY"

AUTHORIZED_PRODUCTIVE_SURFACES: Final[int] = 0
LEARNING_STATE_MUTATION_PERFORMED: Final[bool] = False
SEARCH_EXECUTION_PERFORMED: Final[bool] = False
CANONICAL_ANALYZER_INVOKED: Final[bool] = False

_LOGGER = logging.getLogger(__name__)


class MetaLearningIngestError(ValueError):
    """Fail-closed meta-learning ingest request error."""


@dataclass(frozen=True)
class MetaLearningIngestRequestV1:
    return_input_ack: Mapping[str, Any] | None
    optimization_experiment_evidence: Mapping[str, Any] | None
    expected_return_input_schema_version: str | None = RETURN_INPUT_SCHEMA_VERSION
    expected_optimization_evidence_schema_version: str | None = (
        OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION
    )
    expected_meta_evidence_schema_version: str | None = META_LEARNING_EVIDENCE_SCHEMA_VERSION
    requested_learning_state_mutation: bool = False
    requested_search_execution: bool = False
    requested_experiment_prioritization: bool = False
    requested_promotion: bool = False


def ingest_meta_learning_evidence_from_return_input_v1(
    request: MetaLearningIngestRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_learning_state_mutation:
        raise MetaLearningIngestError("LEARNING_STATE_MUTATION_FORBIDDEN")
    if request.requested_search_execution:
        raise MetaLearningIngestError("SEARCH_EXECUTION_FORBIDDEN")
    if request.requested_experiment_prioritization:
        raise MetaLearningIngestError("EXPERIMENT_PRIORITIZATION_FORBIDDEN")
    if request.requested_promotion:
        raise MetaLearningIngestError("PROMOTION_FORBIDDEN")

    if request.expected_return_input_schema_version != RETURN_INPUT_SCHEMA_VERSION:
        return _ingest_result(
            status=INGEST_STATUS_REJECTED_STALE,
            reason="RETURN_INPUT_SCHEMA_VERSION_MISMATCH",
            meta_evidence=None,
        )
    if request.expected_optimization_evidence_schema_version not in (
        None,
        OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION,
    ):
        return _ingest_result(
            status=INGEST_STATUS_REJECTED_STALE,
            reason="OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION_MISMATCH",
            meta_evidence=None,
        )

    if request.return_input_ack is None:
        return _ingest_result(
            status=INGEST_STATUS_REJECTED_ACK,
            reason="MISSING_RETURN_INPUT_ACK",
            meta_evidence=None,
        )
    ack = request.return_input_ack
    if ack.get("schema_version") != RETURN_INPUT_SCHEMA_VERSION:
        return _ingest_result(
            status=INGEST_STATUS_REJECTED_STALE,
            reason="RETURN_INPUT_ACK_SCHEMA_MISMATCH",
            meta_evidence=None,
        )
    if ack.get("status") != STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT:
        return _ingest_result(
            status=INGEST_STATUS_REJECTED_ACK,
            reason="RETURN_INPUT_NOT_ACCEPTED",
            meta_evidence=None,
        )

    if request.optimization_experiment_evidence is None:
        return _ingest_result(
            status=INGEST_STATUS_REJECTED_MALFORMED,
            reason="MISSING_OPTIMIZATION_EXPERIMENT_EVIDENCE",
            meta_evidence=None,
        )
    try:
        opt_evidence = validate_optimization_experiment_evidence_v1(
            request.optimization_experiment_evidence
        )
    except Exception as exc:
        _LOGGER.debug("optimization experiment evidence invalid: %s", exc)
        return _ingest_result(
            status=INGEST_STATUS_REJECTED_MALFORMED,
            reason="OPTIMIZATION_EXPERIMENT_EVIDENCE_INVALID",
            meta_evidence=None,
        )

    ack_digest = ack.get("optimization_experiment_evidence_digest")
    evidence_digest = opt_evidence.get("content_hash")
    if str(ack_digest) != str(evidence_digest):
        return _ingest_result(
            status=INGEST_STATUS_REJECTED_OUT_OF_ORDER,
            reason="ACK_EVIDENCE_DIGEST_MISMATCH",
            meta_evidence=None,
        )
    if ack.get("plane_identity") != opt_evidence.get("plane_identity"):
        return _ingest_result(
            status=INGEST_STATUS_REJECTED_OUT_OF_ORDER,
            reason="ACK_PLANE_IDENTITY_MISMATCH",
            meta_evidence=None,
        )

    meta_evidence = build_meta_learning_evidence_from_optimization_experiment_v1(opt_evidence)
    if request.expected_meta_evidence_schema_version != META_LEARNING_EVIDENCE_SCHEMA_VERSION:
        return _ingest_result(
            status=INGEST_STATUS_REJECTED_STALE,
            reason="META_LEARNING_EVIDENCE_SCHEMA_VERSION_MISMATCH",
            meta_evidence=meta_evidence,
        )

    return _ingest_result(
        status=INGEST_STATUS_COMPLETE,
        reason="META_LEARNING_EVIDENCE_PROJECTED_ONLY",
        meta_evidence=meta_evidence,
    )


def build_meta_learning_evidence_from_optimization_experiment_v1(
    optimization_experiment_evidence: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    evidence = validate_optimization_experiment_evidence_v1(optimization_experiment_evidence)
    slices = evidence["evidence_slices"]
    search = slices[CLASS_SEARCH_EVIDENCE]
    challenger = slices[CLASS_CHALLENGER_EVIDENCE]
    oos = slices[CLASS_OOS_EVIDENCE]
    robustness = slices[CLASS_ROBUSTNESS_EVIDENCE]
    failure = slices[CLASS_FAILURE_EVIDENCE]
    economic = slices[CLASS_ECONOMIC_EVIDENCE]
    version_bindings = dict(evidence["version_bindings"])

    experiment_id = search.get("experiment_id")
    source_experiment_ids: tuple[str, ...] = ()
    if isinstance(experiment_id, str) and experiment_id.strip():
        source_experiment_ids = (experiment_id.strip(),)

    source_envelope_versions = {
        "optimizable_envelope_schema_version": version_bindings.get(
            "optimizable_envelope_schema_version"
        ),
        "optimizable_envelope_contract_version": version_bindings.get(
            "optimizable_envelope_contract_version"
        ),
        "envelope_resolution_digest": evidence.get("envelope_resolution_digest"),
    }

    failure_count = int(failure.get("failure_evidence_count") or 0)
    disposition = challenger.get("overall_disposition")
    pattern = f"OFFLINE_CHALLENGER_DISPOSITION={disposition};FAILURE_EVIDENCE_COUNT={failure_count}"

    cost_slippage_failure_pattern: str | Mapping[str, Any]
    if failure_count > 0:
        cost_slippage_failure_pattern = {
            "failure_records_digest": failure.get("failure_records_digest"),
            "interpretation_authority": META_EVIDENCE_AUTHORITY,
        }
    else:
        cost_slippage_failure_pattern = UNKNOWN_UNAVAILABLE

    reproducibility_body = {
        "source_optimization_experiment_evidence_digest": str(evidence["content_hash"]),
        "source_experiment_ids": source_experiment_ids,
        "search_identity": search.get("search_identity"),
        "oos_integrity": oos.get("robustness_evidence_integrity"),
        "robustness_integrity": robustness.get("robustness_evidence_integrity"),
        "economic_lineage_digest": economic.get("source_learning_evidence_digest"),
        "failure_records_digest": failure.get("failure_records_digest"),
    }
    reproducibility_digest = compute_content_sha256(reproducibility_body)

    canonical: dict[str, Any] = {
        "schema_version": META_LEARNING_EVIDENCE_SCHEMA_VERSION,
        "domain": "peak_trade.learning.ddo.meta_learning_evidence.v1",
        "universe_class": UNIVERSE_CLASS_SELF_LEARNING,
        "evidence_class": EVIDENCE_CLASS_META_LEARNING,
        "meta_evidence_id": derive_meta_evidence_id_v1(
            reproducibility_digest=reproducibility_digest
        ),
        "source_experiment_ids": source_experiment_ids,
        "source_envelope_versions": source_envelope_versions,
        "observed_regime_or_context_ref": (
            f"{OFFLINE_CONTEXT_KIND}|surface={SYNTHETIC_OFFLINE_SURFACE_ID}"
        ),
        "optimization_family": UNKNOWN_UNAVAILABLE,
        "search_method": {
            "method_token": UNKNOWN_UNAVAILABLE,
            "advanced_search_schema_version": version_bindings.get(
                "advanced_search_schema_version"
            ),
        },
        "repeated_success_or_failure_pattern": pattern,
        "oos_robustness_pattern": {
            "oos_observation_kind": oos.get("observation_kind"),
            "robustness_suite_identity": robustness.get("robustness_suite_identity"),
            "robustness_evidence_integrity": robustness.get("robustness_evidence_integrity"),
        },
        "cost_slippage_failure_pattern": cost_slippage_failure_pattern,
        "predictive_evidence_features": UNKNOWN_UNAVAILABLE,
        "uncertainty": UNKNOWN_UNAVAILABLE,
        "support_count": len(source_experiment_ids),
        "provenance": {
            "source_optimization_experiment_evidence_record_id": evidence.get("record_id"),
            "source_plane_identity": evidence.get("plane_identity"),
            "return_loop_predecessor": "OPTIMIZATION_TO_SELF_LEARNING_M5_RETURN_LOOP_V1",
            "canonical_meta_learning_analyzer_ref": CANONICAL_META_LEARNING_ANALYZER_REF,
            "canonical_meta_learning_analyzer_schema": CANONICAL_META_LEARNING_ANALYZER_SCHEMA,
            "canonical_analyzer_authority": CANONICAL_ANALYZER_AUTHORITY,
            "canonical_analyzer_domain": CANONICAL_ANALYZER_DOMAIN,
            "canonical_analyzer_schema_version": CANONICAL_ANALYZER_SCHEMA_VERSION,
            "canonical_analyzer_invoked": CANONICAL_ANALYZER_INVOKED,
        },
        "reproducibility_digest": reproducibility_digest,
        "meta_evidence_authority": META_EVIDENCE_AUTHORITY,
        "source_optimization_experiment_evidence_record_id": evidence.get("record_id"),
        "source_optimization_experiment_evidence_digest": str(evidence["content_hash"]),
        "learning_state_mutation": False,
        "search_execution_performed": False,
        "promotion_performed": False,
        "external_effect_authorized": False,
        "proposal_not_authority": True,
    }
    return validate_meta_learning_evidence_v1(canonical)


def _ingest_result(
    *,
    status: str,
    reason: str,
    meta_evidence: Mapping[str, Any] | None,
) -> MappingProxyType[str, Any]:
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": META_LEARNING_INGEST_DOMAIN,
        "status": status,
        "reason": reason,
        "meta_learning_evidence": dict(meta_evidence) if meta_evidence is not None else None,
        "meta_evidence_authority": META_EVIDENCE_AUTHORITY,
        "learning_state_mutation_performed": LEARNING_STATE_MUTATION_PERFORMED,
        "search_execution_performed": SEARCH_EXECUTION_PERFORMED,
        "canonical_meta_learning_analyzer_invoked": CANONICAL_ANALYZER_INVOKED,
        "authorized_productive_surfaces": AUTHORIZED_PRODUCTIVE_SURFACES,
    }
    body["result_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "result_digest"}
    )
    return MappingProxyType(body)
