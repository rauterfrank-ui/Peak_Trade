"""Phase 8 bridge: MI forecast + N_BARS outcome + calibration → typed MI learning evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import require_event_time_utc
from src.learning.deterministic_decision_outcome_v0.evaluation_observation_v0 import (
    validate_evaluation_observation_v0,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.calibration_evidence_v1 import (
    build_calibration_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    STACK_DOMAIN,
    WORKPACKAGE_ID,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    validate_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_outcome_join_v1 import (
    ForecastOutcomeJoinError,
    assert_n_bars_observation_unmodified_v1,
    join_forecast_to_n_bars_outcome_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_record_v1 import (
    EVIDENCE_CLASS_MI_LEARNING,
    MI_LEARNING_EVIDENCE_AUTHORITY,
    OUTCOME_FINALIZATION_FINALIZED,
    OUTCOME_FINALIZATION_INCOMPLETE,
    compute_mi_learning_reproducibility_digest_v1,
    derive_mi_learning_evidence_id_v1,
)

BRIDGE_ID: Final[str] = "peak_trade.learning.market_intelligence_mi_to_learning_evidence_bridge_v1"
BRIDGE_SCHEMA: Final[str] = "mi_to_learning_evidence_bridge_v1"


class MiToLearningBridgeError(ValueError):
    """Fail-closed MI→Learning bridge error."""


def _parse_utc(value: str) -> datetime:
    text = require_event_time_utc(value, "utc")
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _assert_temporal_integrity_v1(
    *,
    forecast: Mapping[str, Any],
    observation: Mapping[str, Any] | None,
) -> str:
    created = _parse_utc(str(forecast["forecast_created_at_utc"]))
    horizon_end = _parse_utc(str(forecast["outcome_horizon_end_utc"]))
    if created >= horizon_end:
        raise MiToLearningBridgeError("FORECAST_LOOKAHEAD_HORIZON_BOUNDARY")
    body: dict[str, Any] = {
        "forecast_created_at_utc": forecast["forecast_created_at_utc"],
        "outcome_horizon_end_utc": forecast["outcome_horizon_end_utc"],
        "observation_present": observation is not None,
    }
    if observation is not None:
        eval_time = observation.get("evaluation_time_utc")
        if eval_time is not None:
            eval_dt = _parse_utc(str(eval_time))
            if eval_dt < horizon_end:
                raise MiToLearningBridgeError("EVALUATION_TIME_BEFORE_HORIZON_END")
            body["evaluation_time_utc"] = eval_time
        horizon_start = observation.get("horizon_start_time_utc")
        if horizon_start is not None:
            if _parse_utc(str(horizon_start)) < created:
                raise MiToLearningBridgeError("HORIZON_START_BEFORE_FORECAST")
            body["horizon_start_time_utc"] = horizon_start
    return compute_content_hash_v0(body)


def _assert_instrument_alignment_v1(
    *,
    forecast: Mapping[str, Any],
    observation: Mapping[str, Any] | None,
) -> tuple[str | None, str | None]:
    selected = forecast.get("selected_instrument_ref")
    instrument = observation.get("instrument_ref") if observation is not None else None
    if selected is not None and instrument is not None and str(selected) != str(instrument):
        raise MiToLearningBridgeError("FORECAST_INSTRUMENT_MISMATCH")
    return (
        str(selected) if selected is not None else None,
        str(instrument) if instrument is not None else None,
    )


def compose_mi_to_learning_evidence_v1(
    *,
    forecast_evidence: Mapping[str, Any],
    evaluation_observation: Mapping[str, Any] | None,
    realized_direction: str | None = None,
    realized_scalar: float | None = None,
    legacy_learning_evidence_ref: str | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> MappingProxyType[str, Any]:
    forecast = validate_forecast_evidence_v1(forecast_evidence)
    observation = (
        validate_evaluation_observation_v0(evaluation_observation)
        if evaluation_observation is not None
        else None
    )
    temporal_digest = _assert_temporal_integrity_v1(forecast=forecast, observation=observation)
    selected_instrument_ref, instrument_ref = _assert_instrument_alignment_v1(
        forecast=forecast, observation=observation
    )

    obs_before = dict(observation) if observation is not None else None
    try:
        join = join_forecast_to_n_bars_outcome_v1(
            forecast_evidence=forecast,
            evaluation_observation=observation,
        )
    except ForecastOutcomeJoinError as exc:
        raise MiToLearningBridgeError(str(exc)) from exc

    if join["join_status"] != "JOINED":
        calib = build_calibration_evidence_v1(
            forecast_evidence=forecast,
            evaluation_observation=None,
        )
        body = {
            "schema_version": "mi_learning_evidence_record_v1",
            "domain": STACK_DOMAIN,
            "forecast_evidence_id": forecast["forecast_evidence_id"],
            "calibration_evidence_id": calib["calibration_evidence_id"],
            "forecast_outcome_join_digest": compute_content_hash_v0(dict(join)),
            "information_set_ref": forecast["information_set_ref"],
            "forecast_created_at_utc": forecast["forecast_created_at_utc"],
            "outcome_horizon_end_utc": forecast["outcome_horizon_end_utc"],
            "n_bars": forecast["n_bars"],
            "bar_spec_ref": forecast["bar_spec_ref"],
            "evaluation_observation_ref": None,
            "actual_outcome_ref": None,
            "horizon_observation_status": "OUTCOME_MISSING",
            "outcome_finalization_status": OUTCOME_FINALIZATION_INCOMPLETE,
            "evaluability": calib["evaluability"],
            "calibration_method": calib["calibration_method"],
            "calibration_evidence_digest": calib["content_digest"],
            "temporal_integrity_digest": temporal_digest,
            "selected_instrument_ref": selected_instrument_ref,
            "instrument_ref": instrument_ref,
            "legacy_learning_evidence_ref": legacy_learning_evidence_ref,
            "provenance": {
                "bridge_id": BRIDGE_ID,
                "workpackage_id": WORKPACKAGE_ID,
                **dict(provenance or {}),
            },
            "evidence_class": EVIDENCE_CLASS_MI_LEARNING,
            "mi_learning_evidence_authority": MI_LEARNING_EVIDENCE_AUTHORITY,
            "productive_ddo_reducer_mutated": False,
            "forecast_is_not_decision": True,
        }
        digest = compute_mi_learning_reproducibility_digest_v1(body)
        body["reproducibility_digest"] = digest
        body["mi_learning_evidence_id"] = derive_mi_learning_evidence_id_v1(
            reproducibility_digest=digest
        )
        from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_record_v1 import (
            validate_mi_learning_evidence_record_v1,
        )

        return validate_mi_learning_evidence_record_v1(body)

    assert observation is not None
    status = str(observation.get("horizon_observation_status") or "")
    if status != "OK":
        raise MiToLearningBridgeError("HORIZON_OBSERVATION_NOT_FINALIZED")

    calib = build_calibration_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=observation,
        realized_direction=realized_direction,
        realized_scalar=realized_scalar,
    )
    if obs_before is not None:
        assert_n_bars_observation_unmodified_v1(obs_before, observation)

    join_digest = str(join.get("join_digest") or compute_content_hash_v0(dict(join)))
    eval_ref = str(
        join.get("evaluation_observation_ref")
        or observation.get("record_id")
        or observation["actual_outcome_ref"]
    )
    body = {
        "schema_version": "mi_learning_evidence_record_v1",
        "domain": STACK_DOMAIN,
        "forecast_evidence_id": forecast["forecast_evidence_id"],
        "calibration_evidence_id": calib["calibration_evidence_id"],
        "forecast_outcome_join_digest": join_digest,
        "information_set_ref": forecast["information_set_ref"],
        "forecast_created_at_utc": forecast["forecast_created_at_utc"],
        "outcome_horizon_end_utc": forecast["outcome_horizon_end_utc"],
        "n_bars": forecast["n_bars"],
        "bar_spec_ref": forecast["bar_spec_ref"],
        "evaluation_observation_ref": eval_ref,
        "actual_outcome_ref": str(join["actual_outcome_ref"]),
        "horizon_observation_status": status,
        "outcome_finalization_status": OUTCOME_FINALIZATION_FINALIZED,
        "evaluability": calib["evaluability"],
        "calibration_method": calib["calibration_method"],
        "calibration_evidence_digest": calib["content_digest"],
        "temporal_integrity_digest": temporal_digest,
        "selected_instrument_ref": selected_instrument_ref,
        "instrument_ref": instrument_ref,
        "legacy_learning_evidence_ref": legacy_learning_evidence_ref,
        "provenance": {
            "bridge_id": BRIDGE_ID,
            "workpackage_id": WORKPACKAGE_ID,
            **dict(provenance or {}),
        },
        "evidence_class": EVIDENCE_CLASS_MI_LEARNING,
        "mi_learning_evidence_authority": MI_LEARNING_EVIDENCE_AUTHORITY,
        "productive_ddo_reducer_mutated": False,
        "forecast_is_not_decision": True,
    }
    digest = compute_mi_learning_reproducibility_digest_v1(body)
    body["reproducibility_digest"] = digest
    body["mi_learning_evidence_id"] = derive_mi_learning_evidence_id_v1(
        reproducibility_digest=digest
    )
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_record_v1 import (
        validate_mi_learning_evidence_record_v1,
    )

    return validate_mi_learning_evidence_record_v1(body)
