"""Typed durable MI offline evidence envelope (forecast + calibration + research).

AUTHORITY=NONE. Offline research evidence only. Does not authorize promotion,
productive apply, market-fact ownership, or external effects.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    compute_content_hash_v0,
    is_valid_sha256_hex_v0,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.calibration_evidence_v1 import (
    CalibrationEvidenceValidationError,
    validate_calibration_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    STACK_DOMAIN,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    ForecastEvidenceValidationError,
    validate_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_research_evidence_v1 import (
    EVIDENCE_CLASS_MI_RESEARCH,
    MI_RESEARCH_AUTHORITY,
    SCHEMA_VERSION as RESEARCH_SCHEMA_VERSION,
)

SCHEMA_VERSION: Final[str] = "mi_offline_durable_evidence_record_v1"
EVIDENCE_CLASS_MI_OFFLINE_DURABLE: Final[str] = "MI_OFFLINE_DURABLE_EVIDENCE"
MI_OFFLINE_DURABLE_EVIDENCE_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False


class MiOfflineDurableEvidenceValidationError(ValueError):
    """Fail-closed durable MI offline evidence validation."""


def derive_mi_offline_durable_evidence_id_v1(*, content_digest: str) -> str:
    if not is_valid_sha256_hex_v0(content_digest):
        raise MiOfflineDurableEvidenceValidationError("DURABLE_CONTENT_DIGEST_INVALID")
    return f"mi.offline.durable.{content_digest[:48]}"


def validate_research_evidence_record_v1(
    research_evidence: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    raw = dict(research_evidence)
    if raw.get("schema_version") != RESEARCH_SCHEMA_VERSION:
        raise MiOfflineDurableEvidenceValidationError("RESEARCH_SCHEMA_MISMATCH")
    if raw.get("market_intelligence_research_authority") != MI_RESEARCH_AUTHORITY:
        raise MiOfflineDurableEvidenceValidationError("RESEARCH_AUTHORITY_MUST_BE_NONE")
    if raw.get("evidence_class") != EVIDENCE_CLASS_MI_RESEARCH:
        raise MiOfflineDurableEvidenceValidationError("RESEARCH_EVIDENCE_CLASS_MISMATCH")
    required = (
        "forecast_evidence_id",
        "calibration_evidence_id",
        "n_bars",
        "bar_spec_ref",
        "forecast_kind",
        "research_evidence_id",
        "content_digest",
    )
    for key in required:
        if key not in raw:
            raise MiOfflineDurableEvidenceValidationError("RESEARCH_EVIDENCE_FIELDS_MISSING")
    body = {
        key: raw[key]
        for key in (
            "schema_version",
            "domain",
            "forecast_evidence_id",
            "calibration_evidence_id",
            "n_bars",
            "bar_spec_ref",
            "forecast_kind",
            "evaluability",
            "drift_assessment_refs",
            "legacy_learning_evidence_ref",
            "market_intelligence_research_authority",
            "evidence_class",
            "productive_authority",
            "runtime_reachability",
            "can_auto_promote",
        )
        if key in raw
    }
    digest = compute_content_hash_v0(body)
    if raw.get("content_digest") != digest:
        raise MiOfflineDurableEvidenceValidationError("RESEARCH_CONTENT_DIGEST_MISMATCH")
    expected_id = f"mi.research.{digest[:48]}"
    if raw.get("research_evidence_id") != expected_id:
        raise MiOfflineDurableEvidenceValidationError("RESEARCH_EVIDENCE_ID_MISMATCH")
    return MappingProxyType(raw)


def build_mi_offline_durable_evidence_record_v1(
    *,
    forecast_evidence: Mapping[str, Any],
    calibration_evidence: Mapping[str, Any],
    research_evidence: Mapping[str, Any],
    provenance: Mapping[str, Any] | None = None,
) -> MappingProxyType[str, Any]:
    try:
        forecast = validate_forecast_evidence_v1(forecast_evidence)
    except (ForecastEvidenceValidationError, ValueError) as exc:
        raise MiOfflineDurableEvidenceValidationError(str(exc)) from exc
    try:
        calibration = validate_calibration_evidence_v1(calibration_evidence)
    except (CalibrationEvidenceValidationError, DdoValidationError, ValueError) as exc:
        raise MiOfflineDurableEvidenceValidationError(str(exc)) from exc
    research = validate_research_evidence_record_v1(research_evidence)

    if calibration.get("forecast_evidence_id") != forecast["forecast_evidence_id"]:
        raise MiOfflineDurableEvidenceValidationError("CALIBRATION_FORECAST_ID_MISMATCH")
    if research.get("forecast_evidence_id") != forecast["forecast_evidence_id"]:
        raise MiOfflineDurableEvidenceValidationError("RESEARCH_FORECAST_ID_MISMATCH")
    if research.get("calibration_evidence_id") != calibration["calibration_evidence_id"]:
        raise MiOfflineDurableEvidenceValidationError("RESEARCH_CALIBRATION_ID_MISMATCH")
    if forecast.get("forecast_evidence_authority") != "NONE":
        raise MiOfflineDurableEvidenceValidationError("FORECAST_AUTHORITY_MUST_BE_NONE")

    identity_body = {
        "schema_version": SCHEMA_VERSION,
        "domain": STACK_DOMAIN,
        "forecast_evidence_id": forecast["forecast_evidence_id"],
        "forecast_content_digest": forecast["content_digest"],
        "calibration_evidence_id": calibration["calibration_evidence_id"],
        "calibration_content_digest": calibration["content_digest"],
        "research_evidence_id": research["research_evidence_id"],
        "research_content_digest": research["content_digest"],
        "n_bars": forecast["n_bars"],
        "bar_spec_ref": forecast["bar_spec_ref"],
        "outcome_horizon_end_utc": forecast["outcome_horizon_end_utc"],
        "forecast_created_at_utc": forecast["forecast_created_at_utc"],
        "market_state_refs": list(forecast["market_state_refs"]),
        "evidence_class": EVIDENCE_CLASS_MI_OFFLINE_DURABLE,
        "mi_offline_durable_evidence_authority": MI_OFFLINE_DURABLE_EVIDENCE_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "productive_authority": "NONE",
        "can_auto_promote": False,
    }
    content_digest = compute_content_hash_v0(identity_body)
    durable_id = derive_mi_offline_durable_evidence_id_v1(content_digest=content_digest)
    record = {
        **identity_body,
        "durable_evidence_id": durable_id,
        "content_digest": content_digest,
        "forecast_evidence": dict(forecast),
        "calibration_evidence": dict(calibration),
        "research_evidence": dict(research),
        "provenance": dict(provenance or {}),
    }
    return MappingProxyType(record)


def validate_mi_offline_durable_evidence_record_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise MiOfflineDurableEvidenceValidationError("DURABLE_SCHEMA_MISMATCH")
    if (
        payload.get("mi_offline_durable_evidence_authority")
        != MI_OFFLINE_DURABLE_EVIDENCE_AUTHORITY
    ):
        raise MiOfflineDurableEvidenceValidationError("DURABLE_AUTHORITY_MUST_BE_NONE")
    rebuilt = build_mi_offline_durable_evidence_record_v1(
        forecast_evidence=payload.get("forecast_evidence") or {},
        calibration_evidence=payload.get("calibration_evidence") or {},
        research_evidence=payload.get("research_evidence") or {},
        provenance=payload.get("provenance")
        if isinstance(payload.get("provenance"), Mapping)
        else {},
    )
    if payload.get("durable_evidence_id") != rebuilt["durable_evidence_id"]:
        raise MiOfflineDurableEvidenceValidationError("DURABLE_EVIDENCE_ID_MISMATCH")
    if payload.get("content_digest") != rebuilt["content_digest"]:
        raise MiOfflineDurableEvidenceValidationError("DURABLE_CONTENT_DIGEST_MISMATCH")
    return rebuilt
