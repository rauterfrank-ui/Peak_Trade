"""Decision-free offline market measurement → original calibration/store/readback.

Uses the original supplier's new market entry and the original calibration math.
No DDO observation, dummy decision, lane, model trainer or runtime hook is created.
"""

from __future__ import annotations

from pathlib import Path

from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
    OBSERVATION_SCHEMA,
    build_independent_market_return_target_v1,
    validate_independent_market_horizon_v1,
)
from .calibration_evidence_v1 import _build_calibration_from_validated_join_v1
from .forecast_evidence_v1 import validate_forecast_evidence_v1
from .forecast_measurement_integration_v1 import (
    MARKET_FROZEN_SCHEMA,
    _lease,
    _append,
    _read,
    _readback,
    validate_forecast_numbers_v1,
)
from .integration_contracts_v1 import (
    assert_offline_v1,
    bytes_v1,
    digest_v1,
    require_v1,
    seal_v1,
    validate_seal_v1,
)
from .mi_offline_durable_evidence_persist_v1 import (
    MiOfflineDurableEvidencePersistRequestV1,
    persist_mi_offline_durable_evidence_v1,
)
from .mi_offline_durable_evidence_store_v1 import MiOfflineDurableEvidenceStoreV1
from .mi_research_evidence_v1 import project_market_intelligence_research_evidence_v1

MARKET_ACK_SCHEMA = "exact_independent_market_calibration_readback_v1"
MARKET_INPUT_SCHEMA = "exact_independent_market_measurement_inputs_v1"


def _prepare(frozen, market_observation):
    binding = validate_seal_v1(frozen, MARKET_FROZEN_SCHEMA)
    forecast = validate_forecast_evidence_v1(binding["forecast_evidence"])
    validate_forecast_numbers_v1(forecast)
    observation = validate_independent_market_horizon_v1(market_observation)
    request = observation["request"]
    identity = binding["context_package"]["identity"]
    require_v1(
        request["market_identity"] == identity, "MARKET_MEASUREMENT_SOURCE_IDENTITY_MISMATCH"
    )
    target = build_independent_market_return_target_v1(request)
    require_v1(
        bytes_v1(target) == bytes_v1(forecast["provenance"].get("measured_return_target_v1")),
        "MARKET_MEASUREMENT_TARGET_MISMATCH",
    )
    require_v1(
        forecast.get("decision_event_ref") is None
        and binding["job_key"]["identity_kind"] == "MARKET_ONLY_V1",
        "MARKET_ATTRIBUTION_FORBIDDEN",
    )
    require_v1(
        forecast["selected_instrument_ref"] == identity["instrument_ref"],
        "MARKET_FORECAST_ENTITY_MISMATCH",
    )
    measurement = observation["measurement"]
    require_v1(
        measurement["instrument_ref"] == target["measurement_instrument_ref"]
        and measurement["bar_spec_ref"] == forecast["bar_spec_ref"],
        "MARKET_OPAQUE_MEASUREMENT_BINDING_MISMATCH",
    )
    require_v1(
        measurement["bar_close_times_utc"][0] == target["return_start_close_time_utc"]
        and measurement["bar_close_times_utc"][-1] == target["return_end_close_time_utc"],
        "MARKET_MEASUREMENT_ANCHOR_MISMATCH",
    )
    # Only this validated market join reaches the shared original error calculation.
    calibration = _build_calibration_from_validated_join_v1(
        forecast=forecast,
        join={"join_status": "JOINED", "actual_outcome_ref": measurement["actual_outcome_ref"]},
        realized_scalar=measurement["log_return"],
        provenance={
            "measurement_ref": measurement["actual_outcome_ref"],
            "market_observation_digest": observation["exact_content_digest"],
            "target": target,
        },
    )
    projection = project_market_intelligence_research_evidence_v1(
        forecast_evidence=forecast,
        calibration_evidence=calibration,
    )
    return binding, forecast, observation, calibration, projection


def calibrate_frozen_market_forecast_v1(*, store_root, frozen, market_observation):
    """Validate all inputs before publishing to the existing durable MI owner."""
    assert_offline_v1()
    key = digest_v1(frozen["job_key"])
    original = Path(store_root) / ".intelligence-integration-v1" / key / "forecast.json"
    require_v1(original.is_file(), "MARKET_FORECAST_MUST_BE_FROZEN_FIRST")
    binding, forecast, observation, calibration, projection = _prepare(frozen, market_observation)
    inputs = seal_v1(
        {
            "schema_version": MARKET_INPUT_SCHEMA,
            "authority": "NONE",
            "frozen_digest": binding["exact_content_digest"],
            "market_observation": observation,
        }
    )
    with _lease(store_root, digest_v1(binding["job_key"])) as folder:
        require_v1(
            bytes_v1(_read(folder / "forecast.json", MARKET_FROZEN_SCHEMA)) == bytes_v1(binding),
            "FROZEN_FORECAST_CHANGED",
        )
        _append(folder / "measurement.json", inputs)
        if (folder / "calibration_ack.json").exists():
            ack = _read(folder / "calibration_ack.json", MARKET_ACK_SCHEMA)
            require_v1(
                ack["measurement_inputs_digest"] == inputs["exact_content_digest"],
                "MEASUREMENT_ACK_MISMATCH",
            )
            _readback(store_root, ack)
            return ack
        persistence = persist_mi_offline_durable_evidence_v1(
            store_root,
            MiOfflineDurableEvidencePersistRequestV1(
                forecast_evidence=forecast,
                calibration_evidence=calibration,
                research_evidence=projection,
                provenance={
                    "measurement_ref": observation["measurement"]["actual_outcome_ref"],
                    "market_observation_digest": observation["exact_content_digest"],
                },
            ),
        )
        record = MiOfflineDurableEvidenceStoreV1(store_root).get(persistence["durable_evidence_id"])
        ack = seal_v1(
            {
                "schema_version": MARKET_ACK_SCHEMA,
                "authority": "NONE",
                "job_key": binding["job_key"],
                "frozen_digest": binding["exact_content_digest"],
                "measurement_inputs_digest": inputs["exact_content_digest"],
                "market_observation_digest": observation["exact_content_digest"],
                "durable_evidence_id": persistence["durable_evidence_id"],
                "original_record_exact_digest": digest_v1(record),
                "forecast_evidence_id": forecast["forecast_evidence_id"],
                "actual_outcome_ref": observation["measurement"]["actual_outcome_ref"],
                "calibration_result": record["calibration_evidence"]["calibration_result"],
                "distribution_calibration_proven": False,
                "model_training_performed": False,
                "source_authenticated": False,
                "productive_apply_authorized": False,
            }
        )
        _readback(store_root, ack)
        _append(folder / "calibration_ack.json", ack)
        return ack


def read_independent_market_calibration_v1(*, store_root, job_key):
    """Cold exact read: no supplier, calibration, provider, engine or inference call."""
    assert_offline_v1()
    require_v1(job_key.get("identity_kind") == "MARKET_ONLY_V1", "MARKET_JOB_REQUIRED")
    folder = Path(store_root) / ".intelligence-integration-v1" / digest_v1(job_key)
    require_v1(folder.is_dir(), "ORIGINAL_MARKET_JOB_NOT_FOUND")
    with _lease(store_root, digest_v1(job_key)) as folder:
        frozen = _read(folder / "forecast.json", MARKET_FROZEN_SCHEMA)
        ack = _read(folder / "calibration_ack.json", MARKET_ACK_SCHEMA)
        inputs = _read(folder / "measurement.json", MARKET_INPUT_SCHEMA)
        observation = validate_seal_v1(inputs["market_observation"], OBSERVATION_SCHEMA)
        require_v1(frozen["job_key"] == dict(job_key) == ack["job_key"], "READBACK_JOB_MISMATCH")
        require_v1(
            ack["frozen_digest"] == frozen["exact_content_digest"] == inputs["frozen_digest"],
            "READBACK_FORECAST_MISMATCH",
        )
        require_v1(
            ack["measurement_inputs_digest"] == inputs["exact_content_digest"]
            and ack["market_observation_digest"] == observation["exact_content_digest"],
            "READBACK_MEASUREMENT_MISMATCH",
        )
        require_v1(
            ack["actual_outcome_ref"] == observation["measurement"]["actual_outcome_ref"],
            "READBACK_OUTCOME_MISMATCH",
        )
        record = _readback(store_root, ack)
        require_v1(
            bytes_v1(record["forecast_evidence"]) == bytes_v1(frozen["forecast_evidence"]),
            "READBACK_ORIGINAL_FORECAST_MISMATCH",
        )
        return {
            "frozen": frozen,
            "calibration_ack": ack,
            "measurement_inputs": inputs,
            "original_record": record,
        }
