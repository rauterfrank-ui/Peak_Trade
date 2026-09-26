"""MI-enriched M4 intake v1 — typed MI research input into canonical experiment plane.

Validates MARKET_INTELLIGENCE_OPTIMIZATION_RESEARCH_INPUT_V1 (and optional Phase-8 MI
learning export references), requires canonical DDO learning evidence for the existing
M4 plane, runs run_optimization_universe_experiment_plane_v1, and attaches auditable
MI lineage to the plane chain. Does not authorize promotion, productive apply, or
external effects.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    build_optimization_experiment_evidence_from_plane_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    DECISION_CONFIG as PLANE_DECISION_CONFIG,
    EXPERIMENT_PLANE_DOMAIN,
    NORMATIVE_SPEC as PLANE_NORMATIVE_SPEC,
    PLANE_STATUS_COMPLETE,
    SCHEMA_VERSION as PLANE_SCHEMA_VERSION,
    OptimizationUniverseExperimentPlaneRequestV1,
    run_optimization_universe_experiment_plane_v1,
)
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_optimization_research_input_v1 import (
    STATUS_ACCEPTED as MI_OPT_INPUT_ACCEPTED,
    MarketIntelligenceOptimizationResearchInputError,
    MarketIntelligenceOptimizationResearchInputRequestV1,
    SCHEMA_VERSION as MI_OPT_INPUT_SCHEMA_VERSION,
    validate_market_intelligence_optimization_research_input_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_research_evidence_v1 import (
    EVIDENCE_CLASS_MI_RESEARCH,
    SCHEMA_VERSION as MI_RESEARCH_SCHEMA_VERSION,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "canonical_optimization_universe_mi_enriched_m4_intake_v1"
INTAKE_DOMAIN: Final[str] = "peak_trade.canonical_optimization_universe_mi_enriched_m4_intake.v1"

INTAKE_STATUS_ACCEPTED: Final[str] = "MI_ENRICHED_M4_INTAKE_ACCEPTED"
INTAKE_STATUS_REJECTED_MI_INPUT: Final[str] = "MI_ENRICHED_M4_INTAKE_REJECTED_MI_INPUT"
INTAKE_STATUS_REJECTED_LEARNING_INPUT: Final[str] = "MI_ENRICHED_M4_INTAKE_REJECTED_LEARNING_INPUT"
INTAKE_STATUS_REJECTED_PLANE: Final[str] = "MI_ENRICHED_M4_INTAKE_REJECTED_PLANE"
INTAKE_STATUS_REJECTED_AUTHORITY: Final[str] = "MI_ENRICHED_M4_INTAKE_REJECTED_AUTHORITY"
INTAKE_STATUS_REJECTED_MISMATCH: Final[str] = "MI_ENRICHED_M4_INTAKE_REJECTED_LEARNING_MISMATCH"

OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
PROMOTION_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False

_LOGGER = logging.getLogger(__name__)


class MiEnrichedM4IntakeError(ValueError):
    """Fail-closed MI-enriched M4 intake error."""


@dataclass(frozen=True)
class MiEnrichedM4IntakeRequestV1:
    market_intelligence_research_evidence: Mapping[str, Any]
    plane_request: OptimizationUniverseExperimentPlaneRequestV1
    legacy_learning_evidence: Mapping[str, Any] | None = None
    mi_learning_evidence_export: Mapping[str, Any] | None = None
    requested_productive_join: bool = False
    requested_mv2_dp_binding: bool = False
    requested_cap23_binding: bool = False


@dataclass(frozen=True)
class MiEnrichedM4ClosureRequestV1:
    """Orchestrator-friendly closure: intake + plane + optimization experiment evidence."""

    intake_request: MiEnrichedM4IntakeRequestV1


def _json_safe(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _recompute_plane_result_digest(plane_body: dict[str, Any]) -> str:
    digest_body = _json_safe(
        {key: value for key, value in plane_body.items() if key != "result_digest"}
    )
    return compute_content_sha256(digest_body)


def build_mi_lineage_refs_v1(
    *,
    mi_research_evidence: Mapping[str, Any],
    mi_optimization_research_input_ack: Mapping[str, Any],
    mi_learning_evidence_export: Mapping[str, Any] | None,
) -> MappingProxyType[str, Any]:
    mi_record = None
    if mi_learning_evidence_export is not None:
        mi_record = mi_learning_evidence_export.get("mi_learning_evidence")
    lineage: dict[str, Any] = {
        "mi_optimization_research_input_schema_version": MI_OPT_INPUT_SCHEMA_VERSION,
        "mi_optimization_research_input_result_digest": mi_optimization_research_input_ack.get(
            "result_digest"
        ),
        "mi_research_evidence_schema_version": mi_research_evidence.get("schema_version"),
        "research_evidence_id": mi_research_evidence.get("research_evidence_id"),
        "mi_research_content_digest": mi_research_evidence.get("content_digest"),
        "forecast_evidence_id": mi_research_evidence.get("forecast_evidence_id"),
        "calibration_evidence_id": mi_research_evidence.get("calibration_evidence_id"),
        "legacy_learning_evidence_ref": mi_research_evidence.get("legacy_learning_evidence_ref"),
        "drift_assessment_refs": mi_research_evidence.get("drift_assessment_refs"),
        "mi_learning_evidence_export_schema_version": None,
        "mi_learning_evidence_id": None,
        "forecast_outcome_join_digest": None,
        "temporal_integrity_digest": None,
        "mi_learning_reproducibility_digest": None,
        "mi_learning_content_hash": None,
    }
    if mi_learning_evidence_export is not None:
        lineage["mi_learning_evidence_export_schema_version"] = mi_learning_evidence_export.get(
            "schema_version"
        )
    if isinstance(mi_record, Mapping):
        lineage["mi_learning_evidence_id"] = mi_record.get("mi_learning_evidence_id")
        lineage["forecast_outcome_join_digest"] = mi_record.get("forecast_outcome_join_digest")
        lineage["temporal_integrity_digest"] = mi_record.get("temporal_integrity_digest")
        lineage["mi_learning_reproducibility_digest"] = mi_record.get("reproducibility_digest")
        lineage["mi_learning_content_hash"] = mi_record.get("content_hash")
    lineage["lineage_digest"] = compute_content_sha256(
        _json_safe({key: value for key, value in lineage.items() if key != "lineage_digest"})
    )
    return MappingProxyType(lineage)


def _attach_mi_lineage_to_plane(
    plane: Mapping[str, Any],
    *,
    intake_record: Mapping[str, Any],
    mi_lineage: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    body = dict(plane)
    chain_raw = body.get("chain")
    chain = dict(chain_raw) if isinstance(chain_raw, Mapping) else {}
    chain["mi_enriched_m4_intake"] = dict(intake_record)
    chain["mi_lineage_refs"] = dict(mi_lineage)
    body["chain"] = chain
    body["result_digest"] = _recompute_plane_result_digest(body)
    return MappingProxyType(body)


def validate_mi_enriched_m4_intake_v1(
    request: MiEnrichedM4IntakeRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_productive_join:
        raise MiEnrichedM4IntakeError("PRODUCTIVE_JOIN_FORBIDDEN")
    if request.requested_mv2_dp_binding or request.requested_cap23_binding:
        raise MiEnrichedM4IntakeError("TRADING_BINDING_FORBIDDEN")

    mi_research = request.market_intelligence_research_evidence
    if mi_research.get("schema_version") != MI_RESEARCH_SCHEMA_VERSION:
        return _intake_payload(
            status=INTAKE_STATUS_REJECTED_MI_INPUT,
            reason="MI_RESEARCH_SCHEMA_MISMATCH",
            mi_ack=None,
            learning_ack=None,
        )
    if mi_research.get("evidence_class") != EVIDENCE_CLASS_MI_RESEARCH:
        return _intake_payload(
            status=INTAKE_STATUS_REJECTED_MI_INPUT,
            reason="MI_RESEARCH_EVIDENCE_CLASS_INVALID",
            mi_ack=None,
            learning_ack=None,
        )

    legacy = request.legacy_learning_evidence
    if legacy is None:
        return _intake_payload(
            status=INTAKE_STATUS_REJECTED_LEARNING_INPUT,
            reason="LEGACY_LEARNING_EVIDENCE_REQUIRED_FOR_M4",
            mi_ack=None,
            learning_ack=None,
        )

    try:
        mi_ack = validate_market_intelligence_optimization_research_input_v1(
            MarketIntelligenceOptimizationResearchInputRequestV1(
                market_intelligence_research_evidence=mi_research,
                legacy_learning_evidence=legacy,
            )
        )
    except MarketIntelligenceOptimizationResearchInputError as exc:
        return _intake_payload(
            status=INTAKE_STATUS_REJECTED_AUTHORITY,
            reason=str(exc),
            mi_ack=None,
            learning_ack=None,
        )

    if mi_ack.get("status") != MI_OPT_INPUT_ACCEPTED:
        return _intake_payload(
            status=INTAKE_STATUS_REJECTED_MI_INPUT,
            reason=str(mi_ack.get("reason") or "MI_OPT_INPUT_REJECTED"),
            mi_ack=dict(mi_ack),
            learning_ack=None,
        )

    learning_ack = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=legacy)
    )
    if learning_ack.get("status") != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT:
        return _intake_payload(
            status=INTAKE_STATUS_REJECTED_LEARNING_INPUT,
            reason=str(learning_ack.get("reason") or "LEARNING_INPUT_REJECTED"),
            mi_ack=dict(mi_ack),
            learning_ack=dict(learning_ack),
        )

    plane_learning = request.plane_request.learning_evidence
    plane_digest = str(learning_ack.get("learning_evidence_digest") or "")
    if plane_learning is not legacy:
        try:
            plane_ack = validate_canonical_optimization_universe_learning_input_v1(
                CanonicalOptimizationUniverseLearningInputRequestV1(
                    learning_evidence=plane_learning
                )
            )
        except Exception:
            plane_ack = None
        plane_plane_digest = (
            str(plane_ack.get("learning_evidence_digest") or "")
            if isinstance(plane_ack, Mapping)
            else ""
        )
        if plane_plane_digest != plane_digest:
            return _intake_payload(
                status=INTAKE_STATUS_REJECTED_MISMATCH,
                reason="PLANE_LEARNING_EVIDENCE_DIGEST_MISMATCH",
                mi_ack=dict(mi_ack),
                learning_ack=dict(learning_ack),
            )

    mi_lineage = build_mi_lineage_refs_v1(
        mi_research_evidence=mi_research,
        mi_optimization_research_input_ack=mi_ack,
        mi_learning_evidence_export=request.mi_learning_evidence_export,
    )
    return _intake_payload(
        status=INTAKE_STATUS_ACCEPTED,
        reason="MI_ENRICHED_OFFLINE_RESEARCH_INTAKE",
        mi_ack=dict(mi_ack),
        learning_ack=dict(learning_ack),
        mi_lineage=mi_lineage,
    )


def run_mi_enriched_optimization_universe_experiment_plane_v1(
    request: MiEnrichedM4IntakeRequestV1,
) -> MappingProxyType[str, Any]:
    intake = validate_mi_enriched_m4_intake_v1(request)
    if intake["status"] != INTAKE_STATUS_ACCEPTED:
        return MappingProxyType(
            {
                "schema_version": PLANE_SCHEMA_VERSION,
                "domain": EXPERIMENT_PLANE_DOMAIN,
                "status": INTAKE_STATUS_REJECTED_MI_INPUT,
                "reason": intake["reason"],
                "mi_enriched_intake": dict(intake),
                "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
                "promotion_authority": PROMOTION_AUTHORITY,
                "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
                "chain": None,
                "normative_spec": PLANE_NORMATIVE_SPEC,
                "decision_config": PLANE_DECISION_CONFIG,
                "result_digest": compute_content_sha256(
                    {
                        "status": intake["status"],
                        "reason": intake["reason"],
                        "intake_digest": intake.get("intake_digest"),
                    }
                ),
            }
        )

    plane = run_optimization_universe_experiment_plane_v1(request.plane_request)
    mi_lineage = intake.get("mi_lineage_refs")
    if plane.get("status") != PLANE_STATUS_COMPLETE or not isinstance(mi_lineage, Mapping):
        return MappingProxyType(dict(plane))

    return _attach_mi_lineage_to_plane(
        plane,
        intake_record=intake,
        mi_lineage=mi_lineage,
    )


def run_mi_enriched_m4_optimization_closure_v1(
    request: MiEnrichedM4ClosureRequestV1,
) -> MappingProxyType[str, Any]:
    plane = run_mi_enriched_optimization_universe_experiment_plane_v1(request.intake_request)
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": INTAKE_DOMAIN,
        "plane_result": dict(plane),
        "optimization_experiment_evidence": None,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "promotion_authority": PROMOTION_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
    }
    if plane.get("status") == PLANE_STATUS_COMPLETE:
        opt_evidence = build_optimization_experiment_evidence_from_plane_v1(plane)
        body["optimization_experiment_evidence"] = dict(opt_evidence)
    body["closure_digest"] = compute_content_sha256(
        _json_safe({key: value for key, value in body.items() if key != "closure_digest"})
    )
    return MappingProxyType(body)


def _intake_payload(
    *,
    status: str,
    reason: str,
    mi_ack: Mapping[str, Any] | None,
    learning_ack: Mapping[str, Any] | None,
    mi_lineage: Mapping[str, Any] | None = None,
) -> MappingProxyType[str, Any]:
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": INTAKE_DOMAIN,
        "status": status,
        "reason": reason,
        "mi_optimization_research_input_ack": mi_ack,
        "legacy_learning_input_ack": learning_ack,
        "mi_lineage_refs": dict(mi_lineage) if isinstance(mi_lineage, Mapping) else None,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "promotion_authority": PROMOTION_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
    }
    digest_src = {key: value for key, value in body.items() if key != "intake_digest"}
    body["intake_digest"] = compute_content_sha256(_json_safe(digest_src))
    if mi_lineage is not None:
        lineage_digest = mi_lineage.get("lineage_digest")
        if is_valid_sha256_hex(str(lineage_digest or "")):
            body["mi_lineage_digest"] = lineage_digest
    return MappingProxyType(body)
