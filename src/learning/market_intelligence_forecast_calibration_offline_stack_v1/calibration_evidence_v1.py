"""Governed CalibrationEvidence v1 — separate from productive learning-state reducer."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import require_mapping
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import is_valid_sha256_hex_v0
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    STACK_DOMAIN,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    validate_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_outcome_join_v1 import (
    join_forecast_to_n_bars_outcome_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.probabilistic_forecast_payload_v1 import (
    FORECAST_KIND_DIRECTIONAL_PROBABILITY,
    FORECAST_KIND_RETURN_DISTRIBUTION_SUMMARY,
    FORECAST_KIND_THRESHOLD_EVENT_PROBABILITY,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.support_disposition_v1 import (
    EVALUABILITY_INSUFFICIENT,
    EVALUABILITY_NOT_EVALUABLE,
    EVALUABILITY_SUFFICIENT,
    require_support_disposition,
)

SCHEMA_VERSION: Final[str] = "calibration_evidence_v1"
CALIBRATION_EVIDENCE_AUTHORITY: Final[str] = "NONE"
EVIDENCE_CLASS_CALIBRATION: Final[str] = "CALIBRATION_EVIDENCE"

METHOD_BRIER_SCORE: Final[str] = "BRIER_SCORE_V1"
METHOD_RETURN_ERROR: Final[str] = "RETURN_ERROR_V1"
METHOD_THRESHOLD_HIT: Final[str] = "THRESHOLD_HIT_V1"


def _canonicalize_numeric_tree(value: Any) -> Any:
    if isinstance(value, float):
        return format(value, ".12g")
    if isinstance(value, Mapping):
        return {str(k): _canonicalize_numeric_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_canonicalize_numeric_tree(v) for v in value]
    return value


def _calibration_digest(body: Mapping[str, Any]) -> str:
    return compute_content_sha256(_canonicalize_numeric_tree(dict(body)))


class CalibrationEvidenceValidationError(ValueError):
    """Fail-closed calibration evidence validation."""


def derive_calibration_evidence_id_v1(*, body: Mapping[str, Any]) -> str:
    digest = _calibration_digest(body)
    return f"mi.calib.{digest[:48]}"


def _score_directional(*, payload: Mapping[str, Any], realized_direction: str) -> dict[str, Any]:
    probs = payload
    realized = realized_direction.upper()
    if realized not in {"UP", "DOWN", "FLAT"}:
        raise CalibrationEvidenceValidationError("REALIZED_DIRECTION_INVALID")
    key = {"UP": "p_up", "DOWN": "p_down", "FLAT": "p_flat"}[realized]
    return {
        "method": METHOD_BRIER_SCORE,
        "score": 1.0 - float(probs[key]),
        "realized_direction": realized,
    }


def build_calibration_evidence_v1(
    *,
    forecast_evidence: Mapping[str, Any],
    evaluation_observation: Mapping[str, Any] | None,
    realized_scalar: float | None = None,
    realized_direction: str | None = None,
    threshold_hit: bool | None = None,
    support_disposition: str | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> MappingProxyType[str, Any]:
    forecast = validate_forecast_evidence_v1(forecast_evidence)
    join = join_forecast_to_n_bars_outcome_v1(
        forecast_evidence=forecast,
        evaluation_observation=evaluation_observation,
    )

    if join["join_status"] != "JOINED":
        body = {
            "domain": STACK_DOMAIN,
            "schema_version": SCHEMA_VERSION,
            "forecast_evidence_id": forecast["forecast_evidence_id"],
            "actual_outcome_ref": None,
            "n_bars": forecast["n_bars"],
            "bar_spec_ref": forecast["bar_spec_ref"],
            "forecast_kind": forecast["forecast_kind"],
            "evaluability": EVALUABILITY_NOT_EVALUABLE,
            "calibration_method": "NONE",
            "calibration_result": {},
        }
        calib_id = derive_calibration_evidence_id_v1(body=body)
        return MappingProxyType(
            {
                **body,
                "calibration_evidence_id": calib_id,
                "calibration_evidence_authority": CALIBRATION_EVIDENCE_AUTHORITY,
                "evidence_class": EVIDENCE_CLASS_CALIBRATION,
                "content_digest": _calibration_digest(
                    {**body, "calibration_evidence_id": calib_id}
                ),
            }
        )

    disposition = require_support_disposition(
        support_disposition or forecast["support_disposition"],
        "support_disposition",
    )
    if disposition == EVALUABILITY_INSUFFICIENT:
        body = {
            "domain": STACK_DOMAIN,
            "schema_version": SCHEMA_VERSION,
            "forecast_evidence_id": forecast["forecast_evidence_id"],
            "actual_outcome_ref": join["actual_outcome_ref"],
            "n_bars": forecast["n_bars"],
            "bar_spec_ref": forecast["bar_spec_ref"],
            "forecast_kind": forecast["forecast_kind"],
            "evaluability": EVALUABILITY_INSUFFICIENT,
            "calibration_method": "NONE",
            "calibration_result": {"reason": "INSUFFICIENT_SUPPORT"},
        }
        calib_id = derive_calibration_evidence_id_v1(body=body)
        return MappingProxyType(
            {
                **body,
                "calibration_evidence_id": calib_id,
                "calibration_evidence_authority": CALIBRATION_EVIDENCE_AUTHORITY,
                "evidence_class": EVIDENCE_CLASS_CALIBRATION,
                "content_digest": _calibration_digest(
                    {**body, "calibration_evidence_id": calib_id}
                ),
            }
        )

    kind = str(forecast["forecast_kind"])
    payload = require_mapping(forecast["probabilistic_payload"], "probabilistic_payload")
    calibration_result: dict[str, Any]
    method: str
    if kind == FORECAST_KIND_DIRECTIONAL_PROBABILITY:
        if realized_direction is None:
            raise CalibrationEvidenceValidationError("REALIZED_DIRECTION_REQUIRED")
        calibration_result = _score_directional(
            payload=payload, realized_direction=realized_direction
        )
        method = METHOD_BRIER_SCORE
    elif kind == FORECAST_KIND_RETURN_DISTRIBUTION_SUMMARY:
        if realized_scalar is None:
            raise CalibrationEvidenceValidationError("REALIZED_SCALAR_REQUIRED")
        expected = float(payload["mean_return"])
        calibration_result = {
            "method": METHOD_RETURN_ERROR,
            "error": realized_scalar - expected,
            "realized_return": realized_scalar,
        }
        method = METHOD_RETURN_ERROR
    elif kind == FORECAST_KIND_THRESHOLD_EVENT_PROBABILITY:
        if threshold_hit is None:
            raise CalibrationEvidenceValidationError("THRESHOLD_HIT_REQUIRED")
        calibration_result = {
            "method": METHOD_THRESHOLD_HIT,
            "threshold_hit": threshold_hit,
            "p_event": float(payload["p_event"]),
        }
        method = METHOD_THRESHOLD_HIT
    else:
        raise CalibrationEvidenceValidationError("FORECAST_KIND_NOT_CALIBRATABLE_V1")

    body = {
        "domain": STACK_DOMAIN,
        "schema_version": SCHEMA_VERSION,
        "forecast_evidence_id": forecast["forecast_evidence_id"],
        "actual_outcome_ref": join["actual_outcome_ref"],
        "n_bars": forecast["n_bars"],
        "bar_spec_ref": forecast["bar_spec_ref"],
        "forecast_kind": kind,
        "evaluability": EVALUABILITY_SUFFICIENT,
        "calibration_method": method,
        "calibration_result": calibration_result,
        "provenance": dict(provenance or {}),
    }
    calib_id = derive_calibration_evidence_id_v1(body=body)
    digest = _calibration_digest({**body, "calibration_evidence_id": calib_id})
    if not is_valid_sha256_hex_v0(digest):
        raise DdoValidationError("CALIBRATION_DIGEST_INVALID")
    return MappingProxyType(
        {
            **body,
            "calibration_evidence_id": calib_id,
            "calibration_evidence_authority": CALIBRATION_EVIDENCE_AUTHORITY,
            "evidence_class": EVIDENCE_CLASS_CALIBRATION,
            "content_digest": digest,
        }
    )


def validate_calibration_evidence_v1(
    calibration_evidence: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    """Fail-closed revalidation of an existing CalibrationEvidence record."""
    raw = require_mapping(calibration_evidence, "calibration_evidence")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise CalibrationEvidenceValidationError("CALIBRATION_SCHEMA_MISMATCH")
    if raw.get("calibration_evidence_authority") != CALIBRATION_EVIDENCE_AUTHORITY:
        raise CalibrationEvidenceValidationError("CALIBRATION_AUTHORITY_MUST_BE_NONE")
    if raw.get("evidence_class") != EVIDENCE_CLASS_CALIBRATION:
        raise CalibrationEvidenceValidationError("CALIBRATION_EVIDENCE_CLASS_MISMATCH")
    required = (
        "domain",
        "forecast_evidence_id",
        "n_bars",
        "bar_spec_ref",
        "forecast_kind",
        "evaluability",
        "calibration_method",
        "calibration_result",
        "calibration_evidence_id",
        "content_digest",
    )
    missing = [key for key in required if key not in raw]
    if missing:
        raise CalibrationEvidenceValidationError("CALIBRATION_EVIDENCE_FIELDS_MISSING")
    body_for_id: dict[str, Any] = {
        "domain": raw["domain"],
        "schema_version": raw["schema_version"],
        "forecast_evidence_id": raw["forecast_evidence_id"],
        "actual_outcome_ref": raw.get("actual_outcome_ref"),
        "n_bars": raw["n_bars"],
        "bar_spec_ref": raw["bar_spec_ref"],
        "forecast_kind": raw["forecast_kind"],
        "evaluability": raw["evaluability"],
        "calibration_method": raw["calibration_method"],
        "calibration_result": raw["calibration_result"],
    }
    if "provenance" in raw:
        body_for_id["provenance"] = raw["provenance"]
    expected_id = derive_calibration_evidence_id_v1(body=body_for_id)
    if raw.get("calibration_evidence_id") != expected_id:
        raise CalibrationEvidenceValidationError("CALIBRATION_EVIDENCE_ID_MISMATCH")
    expected_digest = _calibration_digest({**body_for_id, "calibration_evidence_id": expected_id})
    if raw.get("content_digest") != expected_digest:
        raise CalibrationEvidenceValidationError("CALIBRATION_CONTENT_DIGEST_MISMATCH")
    if not is_valid_sha256_hex_v0(str(raw["content_digest"])):
        raise DdoValidationError("CALIBRATION_DIGEST_INVALID")
    return MappingProxyType(dict(raw))
