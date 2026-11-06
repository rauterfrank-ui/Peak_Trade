"""Explicit first-close/last-close LOG_RETURN measurement -> existing MI calibration.

New additive adapter for an evidenced missing handoff, not a claim of recovered
historical bytes. No implicit target conversion, directional label, training,
productive state write, source authentication or trading authority.
"""

from __future__ import annotations

from datetime import datetime
import math
from pathlib import Path
from typing import Any, Mapping

from src.learning.deterministic_decision_outcome_v0.evaluation_observation_v0 import (
    validate_evaluation_observation_v0,
)
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    validate_n_bars_measurement_artifacts_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    validate_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.calibration_evidence_v1 import (
    build_calibration_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_research_evidence_v1 import (
    project_market_intelligence_research_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_persist_v1 import (
    MiOfflineDurableEvidencePersistRequestV1,
    persist_mi_offline_durable_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_store_v1 import (
    MiOfflineDurableEvidenceStoreV1,
)
from src.experiments.canonical_advanced_search_v1 import canonical_record_payload_v1
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256


class MeasuredReturnCalibrationError(ValueError):
    """Unspecified target semantics or mismatched measurement cannot yield a label."""


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def prepare_explicit_measured_return_v1(
    *,
    forecast_evidence: Mapping[str, Any],
    evaluation_observation: Mapping[str, Any],
    measurement_evidence: Mapping[str, Any],
    evaluation_information_set: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Require the exact target in forecast provenance before consuming the real scalar.

    Target is only the supplier's first finalized close to last finalized close
    LOG_RETURN, not decision-price-to-close, mark-to-last or simple return. This
    declaration must already be part of the forecast's content digest; the adapter
    cannot relabel an existing unspecified forecast to make a join succeed.
    """
    forecast = validate_forecast_evidence_v1(forecast_evidence)
    observation = validate_evaluation_observation_v0(evaluation_observation)
    validate_n_bars_measurement_artifacts_v1(
        observation, measurement_evidence, evaluation_information_set
    )
    if (
        observation["horizon_observation_status"] != "OK"
        or observation["outcome_scalar_kind"] != "LOG_RETURN"
    ):
        raise MeasuredReturnCalibrationError("COMPLETE_LOG_RETURN_MEASUREMENT_REQUIRED")
    if forecast["forecast_kind"] != "RETURN_DISTRIBUTION_SUMMARY":
        raise MeasuredReturnCalibrationError("EXPLICIT_RETURN_FORECAST_REQUIRED")
    for field in ("mean_return", "std_return"):
        parameter = forecast["probabilistic_payload"][field]
        if (
            isinstance(parameter, bool)
            or not isinstance(parameter, (int, float))
            or not math.isfinite(parameter)
        ):
            raise MeasuredReturnCalibrationError("FINITE_NUMERIC_FORECAST_REQUIRED")
    if forecast["probabilistic_payload"]["std_return"] < 0:
        raise MeasuredReturnCalibrationError("NONNEGATIVE_RETURN_STD_REQUIRED")
    closes = observation["bar_close_times_utc"]
    expected_target = {
        "schema_version": "measured_return_forecast_target_v1",
        "price_basis_kind": measurement_evidence["price_basis_kind"],
        "outcome_scalar_kind": "LOG_RETURN",
        "instrument_ref": observation["instrument_ref"],
        "bar_spec_ref": observation["bar_spec_ref"],
        "n_bars": observation["n_bars"],
        "horizon_start_time_utc": observation["horizon_start_time_utc"],
        "return_start_close_time_utc": closes[0],
        "return_end_close_time_utc": closes[-1],
    }
    if dict(forecast["provenance"].get("measured_return_target_v1", {})) != expected_target:
        raise MeasuredReturnCalibrationError("FORECAST_MEASUREMENT_TARGET_MISMATCH")
    if (
        forecast.get("selected_instrument_ref") != observation["instrument_ref"]
        or forecast.get("decision_event_ref") != observation["decision_event_ref"]
    ):
        raise MeasuredReturnCalibrationError("FORECAST_MEASUREMENT_ENTITY_MISMATCH")
    if forecast["outcome_binding_mode"] != "ACTUAL":
        raise MeasuredReturnCalibrationError("MODELLED_FORECAST_IS_NOT_ACTUAL_OUTCOME")
    if _instant(forecast["forecast_created_at_utc"]) > _instant(
        observation["horizon_start_time_utc"]
    ) or _instant(observation["evaluation_time_utc"]) < _instant(closes[-1]):
        raise MeasuredReturnCalibrationError("FORECAST_MEASUREMENT_KNOWLEDGE_TIME_MISMATCH")
    value = measurement_evidence.get("log_return")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise MeasuredReturnCalibrationError("FINITE_MEASURED_RETURN_REQUIRED")
    calibration = build_calibration_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=observation,
        realized_scalar=value,
        provenance={
            "measurement_ref": observation["actual_outcome_ref"],
            "target": expected_target,
        },
    )
    projection = project_market_intelligence_research_evidence_v1(
        forecast_evidence=forecast,
        calibration_evidence=calibration,
    )
    return {
        "forecast": forecast,
        "observation": observation,
        "calibration": calibration,
        "projection": projection,
        "target": expected_target,
    }


def calibrate_explicit_measured_return_v1(
    *,
    forecast_evidence: Mapping[str, Any],
    evaluation_observation: Mapping[str, Any],
    measurement_evidence: Mapping[str, Any],
    evaluation_information_set: Mapping[str, Any],
    durable_store_root: Path | str,
) -> Mapping[str, Any]:
    """Validate before writing, then reuse the original MI persistence owner."""
    prepared = prepare_explicit_measured_return_v1(
        forecast_evidence=forecast_evidence,
        evaluation_observation=evaluation_observation,
        measurement_evidence=measurement_evidence,
        evaluation_information_set=evaluation_information_set,
    )
    forecast = prepared["forecast"]
    observation = prepared["observation"]
    calibration = prepared["calibration"]
    projection = prepared["projection"]
    expected_target = prepared["target"]
    persisted = persist_mi_offline_durable_evidence_v1(
        durable_store_root,
        MiOfflineDurableEvidencePersistRequestV1(
            forecast_evidence=forecast,
            calibration_evidence=calibration,
            research_evidence=projection,
            provenance={"measurement_ref": observation["actual_outcome_ref"]},
        ),
    )
    body = {
        "schema_version": "measured_return_calibration_binding_v1",
        "forecast_evidence_id": forecast["forecast_evidence_id"],
        "actual_outcome_ref": observation["actual_outcome_ref"],
        "target": expected_target,
        "calibration_evidence": canonical_record_payload_v1(calibration),
        "research_evidence": canonical_record_payload_v1(projection),
        "persistence": persisted,
        "source_authenticated": False,
        "productive_apply_authorized": False,
        "model_training_performed": False,
    }
    body["content_digest"] = compute_content_sha256(body)
    return body


def read_measured_return_calibration_v1(
    *,
    durable_store_root: Path | str,
    durable_evidence_id: str,
    forecast_evidence_id: str,
    actual_outcome_ref: str,
) -> Mapping[str, Any]:
    """Load numerical calibration from the existing durable owner, not its ID projection."""
    record = MiOfflineDurableEvidenceStoreV1(durable_store_root).get(durable_evidence_id)
    # The durable owner validates the full triad and its identities/content digest.
    forecast = record["forecast_evidence"]
    calibration = record["calibration_evidence"]
    if (
        forecast["forecast_evidence_id"] != forecast_evidence_id
        or calibration["actual_outcome_ref"] != actual_outcome_ref
    ):
        raise MeasuredReturnCalibrationError("DURABLE_CALIBRATION_ENTITY_MISMATCH")
    if calibration["calibration_method"] != "RETURN_ERROR_V1":
        raise MeasuredReturnCalibrationError("DURABLE_RETURN_ERROR_REQUIRED")
    return canonical_record_payload_v1(calibration["calibration_result"])
