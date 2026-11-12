"""Freeze exact existing forecasts, then compose original N_BARS/MI/SL owners.

No model is chosen or inferred, no new outcome queue, no score/target conversion.
Attachments are evidence for the original stores, not a second learning/fact SSOT.
"""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .context_admission_v1 import (
    replay_admitted_intelligence_context_v1,
    replay_admitted_market_context_v1,
)
from .integration_contracts_v1 import (
    assert_offline_v1,
    bytes_v1,
    digest_v1,
    finite_v1,
    instant_v1,
    plain_v1,
    require_v1,
    seal_v1,
    strict_json_v1,
    text_v1,
    validate_seal_v1,
)
from .forecast_evidence_v1 import validate_forecast_evidence_v1
from .measured_return_calibration_v1 import (
    calibrate_explicit_measured_return_v1,
    read_measured_return_calibration_v1,
    prepare_explicit_measured_return_v1,
)
from .mi_offline_durable_evidence_store_v1 import MiOfflineDurableEvidenceStoreV1

FROZEN_SCHEMA = "exact_intelligence_forecast_binding_v1"
ACK_SCHEMA = "exact_intelligence_calibration_readback_v1"
MARKET_FROZEN_SCHEMA = "exact_independent_market_forecast_binding_v1"


def validate_forecast_numbers_v1(forecast: Mapping[str, Any]) -> None:
    kind = forecast["forecast_kind"]
    payload = forecast["probabilistic_payload"]
    if kind == "DIRECTIONAL_PROBABILITY":
        values = [finite_v1(payload[k], k) for k in ("p_up", "p_down", "p_flat")]
        require_v1(all(0 <= p <= 1 for p in values), "PROBABILITY_COMPONENT_DOMAIN")
        require_v1(abs(sum(values) - 1) <= 1e-9, "PROBABILITY_SUM")
    elif kind == "RETURN_DISTRIBUTION_SUMMARY":
        finite_v1(payload["mean_return"], "MEAN_RETURN")
        require_v1(finite_v1(payload["std_return"], "STD_RETURN") >= 0, "NONNEGATIVE_STD")
    else:
        require_v1(False, "FORECAST_KIND_NEEDS_EXPLICIT_MEASUREMENT_ADAPTER")


@contextmanager
def _lease(root, key):
    folder = Path(root) / ".intelligence-integration-v1" / key
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "lease").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield folder
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _append(path, value):
    """Publish complete bytes once; exact retry succeeds, divergent reuse rejects."""
    data = bytes_v1(value)
    if path.exists():
        require_v1(path.read_bytes() == data, "IMMUTABLE_ATTACHMENT_CONFLICT")
        return
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".prepared-")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(name, path)
        except FileExistsError:
            require_v1(path.read_bytes() == data, "IMMUTABLE_ATTACHMENT_CONFLICT")
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        os.unlink(name)


def _read(path, schema):
    return validate_seal_v1(strict_json_v1(path.read_bytes()), schema)


def freeze_existing_intelligence_forecast_v1(
    *,
    store_root: Path | str,
    context_package: Mapping[str, Any],
    forecast_evidence: Mapping[str, Any],
    original_probabilistic_payload: bytes,
    provider_admission: Mapping[str, Any],
    model_artifact_bytes: bytes,
    attempt_generation: str,
) -> dict[str, Any]:
    return _freeze_existing_forecast_v1(
        store_root=store_root,
        context_package=context_package,
        forecast_evidence=forecast_evidence,
        original_probabilistic_payload=original_probabilistic_payload,
        provider_admission=provider_admission,
        model_artifact_bytes=model_artifact_bytes,
        attempt_generation=attempt_generation,
        market_only=False,
    )


def freeze_existing_market_forecast_v1(
    *,
    store_root: Path | str,
    context_package: Mapping[str, Any],
    forecast_evidence: Mapping[str, Any],
    original_probabilistic_payload: bytes,
    provider_admission: Mapping[str, Any],
    model_artifact_bytes: bytes,
    attempt_generation: str,
) -> dict[str, Any]:
    return _freeze_existing_forecast_v1(
        store_root=store_root,
        context_package=context_package,
        forecast_evidence=forecast_evidence,
        original_probabilistic_payload=original_probabilistic_payload,
        provider_admission=provider_admission,
        model_artifact_bytes=model_artifact_bytes,
        attempt_generation=attempt_generation,
        market_only=True,
    )


def read_frozen_market_forecast_v1(
    *, store_root: Path | str, job_key: Mapping[str, Any]
) -> dict[str, Any]:
    """Read the immutable forecast while its outcome can still be pending."""
    assert_offline_v1()
    require_v1(job_key.get("identity_kind") == "MARKET_ONLY_V1", "MARKET_JOB_REQUIRED")
    path = Path(store_root) / ".intelligence-integration-v1" / digest_v1(job_key) / "forecast.json"
    require_v1(path.is_file(), "MARKET_FORECAST_MUST_BE_FROZEN_FIRST")
    frozen = _read(path, MARKET_FROZEN_SCHEMA)
    require_v1(frozen["job_key"] == dict(job_key), "READBACK_JOB_MISMATCH")
    return frozen


def _freeze_existing_forecast_v1(
    *,
    store_root: Path | str,
    context_package: Mapping[str, Any],
    forecast_evidence: Mapping[str, Any],
    original_probabilistic_payload: bytes,
    provider_admission: Mapping[str, Any],
    model_artifact_bytes: bytes,
    attempt_generation: str,
    market_only: bool,
) -> dict[str, Any]:
    """Freeze already supplied evidence; this function does not execute model inference."""
    assert_offline_v1()
    replay_context = (
        replay_admitted_market_context_v1
        if market_only
        else replay_admitted_intelligence_context_v1
    )
    context = replay_context(context_package)
    require_v1(context["context_status"] == "VALID", "VALID_CONTEXT_REQUIRED")
    forecast = plain_v1(validate_forecast_evidence_v1(forecast_evidence))
    validate_forecast_numbers_v1(forecast)
    require_v1(
        forecast["forecast_kind"] == "RETURN_DISTRIBUTION_SUMMARY", "EXPLICIT_RETURN_ADAPTER_ONLY"
    )
    require_v1(
        forecast["support_disposition"] == "SUFFICIENT_EVIDENCE", "INSUFFICIENT_FORECAST_SUPPORT"
    )
    identity = context["identity"]
    require_v1(
        forecast["selected_instrument_ref"] == identity["instrument_ref"],
        "FORECAST_INSTRUMENT_MISMATCH",
    )
    if market_only:
        require_v1(
            forecast.get("decision_event_ref") is None, "MARKET_FORECAST_MUST_NOT_HAVE_DECISION"
        )
    else:
        require_v1(
            forecast["decision_event_ref"] == identity["decision_event_ref"],
            "FORECAST_DECISION_MISMATCH",
        )
    native = context["market_context"]
    require_v1(
        forecast["information_set_ref"] == native["information_set_ref"],
        "FORECAST_INFORMATION_SET_MISMATCH",
    )
    require_v1(
        native["context_id"] in forecast["market_state_refs"], "FORECAST_CONTEXT_REF_REQUIRED"
    )
    require_v1(
        bytes_v1(strict_json_v1(original_probabilistic_payload))
        == bytes_v1(forecast["probabilistic_payload"]),
        "ORIGINAL_FORECAST_PAYLOAD_MISMATCH",
    )
    admission = plain_v1(provider_admission)
    for key in (
        "provider_ref",
        "model_ref",
        "feature_schema_ref",
        "training_dataset_ref",
        "validation_ref",
        "admitted_by_ref",
    ):
        text_v1(admission.get(key), key)
    require_v1(admission["model_ref"] == forecast["forecast_model_ref"], "PROVIDER_MODEL_MISMATCH")
    require_v1(
        hashlib.sha256(model_artifact_bytes).hexdigest() == admission.get("model_artifact_sha256"),
        "MODEL_ARTIFACT_MISMATCH",
    )
    require_v1(
        instant_v1(admission["training_end"])
        <= instant_v1(admission["available_at"])
        <= instant_v1(context["as_of"]),
        "MODEL_KNOWLEDGE_LOOKAHEAD",
    )
    require_v1(
        admission.get("context_package_digest") == context["exact_content_digest"],
        "PROVIDER_CONTEXT_MISMATCH",
    )
    context_age_limit = admission.get("max_context_age_seconds")
    require_v1(
        type(context_age_limit) is int and context_age_limit >= 0,
        "PROVIDER_CONTEXT_FRESHNESS_POLICY_REQUIRED",
    )
    require_v1(
        (
            instant_v1(forecast["forecast_created_at_utc"]) - instant_v1(context["as_of"])
        ).total_seconds()
        <= context_age_limit,
        "PROVIDER_CONTEXT_STALE_AT_FORECAST",
    )
    target = forecast["provenance"].get("measured_return_target_v1")
    require_v1(
        isinstance(target, Mapping) and target.get("outcome_scalar_kind") == "LOG_RETURN",
        "EXPLICIT_LOG_RETURN_TARGET_REQUIRED",
    )
    require_v1(admission.get("target_spec_digest") == digest_v1(target), "PROVIDER_TARGET_MISMATCH")
    require_v1(
        instant_v1(context["as_of"])
        <= instant_v1(forecast["forecast_created_at_utc"])
        <= instant_v1(target["horizon_start_time_utc"]),
        "FORECAST_KNOWLEDGE_LOOKAHEAD",
    )
    require_v1(
        target["instrument_ref"] == identity["instrument_ref"]
        and target["bar_spec_ref"] == forecast["bar_spec_ref"]
        and target["n_bars"] == forecast["n_bars"],
        "FORECAST_TARGET_IDENTITY_MISMATCH",
    )
    require_v1(
        instant_v1(target["return_start_close_time_utc"])
        >= instant_v1(target["horizon_start_time_utc"])
        and instant_v1(target["return_end_close_time_utc"])
        == instant_v1(forecast["outcome_horizon_end_utc"]),
        "FORECAST_TARGET_TIME_MISMATCH",
    )
    require_v1(forecast["outcome_binding_mode"] == "ACTUAL", "ACTUAL_TARGET_REQUIRED")
    if market_only:
        from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
            build_independent_market_return_target_v1,
        )

        request = target["market_request"]
        require_v1(
            request["market_identity"] == identity, "MARKET_FORECAST_SOURCE_IDENTITY_MISMATCH"
        )
        require_v1(
            bytes_v1(build_independent_market_return_target_v1(request)) == bytes_v1(target),
            "MARKET_FORECAST_TARGET_MISMATCH",
        )
        require_v1(
            (forecast["provenance"].get("TEST_ONLY_SYNTHETIC") is True)
            == (request["source_kind"] == "SYNTHETIC_OFFLINE"),
            "MARKET_FORECAST_SOURCE_KIND_MISMATCH",
        )
        for source in context["source_bindings"]:
            if source["role"] in {"price_mark", "price_o4"}:
                require_v1(
                    source["units"].get("price") == request["price_unit"],
                    "MARKET_CONTEXT_MEASUREMENT_PRICE_UNIT_MISMATCH",
                )
    text_v1(attempt_generation, "ATTEMPT_GENERATION")
    job = {
        **identity,
        "information_set_ref": forecast["information_set_ref"],
        "target_spec_digest": digest_v1(target),
        "n_bars": forecast["n_bars"],
        "bar_spec_ref": forecast["bar_spec_ref"],
        "forecast_model_ref": forecast["forecast_model_ref"],
        "attempt_generation": attempt_generation,
    }
    if market_only:
        job["identity_kind"] = "MARKET_ONLY_V1"
    record = seal_v1(
        {
            "schema_version": MARKET_FROZEN_SCHEMA if market_only else FROZEN_SCHEMA,
            "authority": "NONE",
            "job_key": job,
            "context_package": context,
            "forecast_evidence": forecast,
            "provider_admission": admission,
            "original_probabilistic_payload_json": original_probabilistic_payload.decode("utf-8"),
            "original_probabilistic_payload_sha256": hashlib.sha256(
                original_probabilistic_payload
            ).hexdigest(),
            "model_inference_performed": False,
            "numeric_feature_consumption_proven": False,
            "source_authenticated": False,
            "productive_apply_authorized": False,
        }
    )
    key = digest_v1(job)
    with _lease(store_root, key) as folder:
        _append(folder / "forecast.json", record)
    return record


def calibrate_frozen_intelligence_forecast_v1(
    *,
    store_root: Path | str,
    frozen: Mapping[str, Any],
    evaluation_observation: Mapping[str, Any],
    measurement_evidence: Mapping[str, Any],
    evaluation_information_set: Mapping[str, Any],
    measurement_generation: str,
    measurement_available_at: str,
) -> dict[str, Any]:
    """Original measurement/calibration/store, followed by exact cold numeric readback."""
    assert_offline_v1()
    binding = validate_seal_v1(frozen, FROZEN_SCHEMA)
    require_v1(
        binding["job_key"]["dataset_generation"] == measurement_generation,
        "MEASUREMENT_GENERATION_MISMATCH",
    )
    available = instant_v1(measurement_available_at)
    require_v1(
        instant_v1(binding["forecast_evidence"]["outcome_horizon_end_utc"])
        <= available
        <= instant_v1(evaluation_observation["evaluation_time_utc"]),
        "MEASUREMENT_NOT_AVAILABLE_AT_EVALUATION",
    )
    key = digest_v1(binding["job_key"])
    original_inputs = seal_v1(
        {
            "schema_version": "exact_intelligence_measurement_inputs_v1",
            "authority": "NONE",
            "frozen_digest": binding["exact_content_digest"],
            "evaluation_observation": evaluation_observation,
            "measurement_evidence": measurement_evidence,
            "evaluation_information_set": evaluation_information_set,
            "measurement_generation": measurement_generation,
            "measurement_available_at": measurement_available_at,
        }
    )
    with _lease(store_root, key) as folder:
        require_v1((folder / "forecast.json").exists(), "FORECAST_MUST_BE_FROZEN_FIRST")
        require_v1(
            bytes_v1(_read(folder / "forecast.json", FROZEN_SCHEMA)) == bytes_v1(binding),
            "FROZEN_FORECAST_CHANGED",
        )
        prepare_explicit_measured_return_v1(
            forecast_evidence=binding["forecast_evidence"],
            evaluation_observation=evaluation_observation,
            measurement_evidence=measurement_evidence,
            evaluation_information_set=evaluation_information_set,
        )
        _append(folder / "measurement.json", original_inputs)
        if (folder / "calibration_ack.json").exists():
            ack = _read(folder / "calibration_ack.json", ACK_SCHEMA)
            require_v1(
                ack["measurement_inputs_digest"] == original_inputs["exact_content_digest"],
                "MEASUREMENT_ACK_MISMATCH",
            )
            _readback(store_root, ack)
            return ack
        result = calibrate_explicit_measured_return_v1(
            forecast_evidence=binding["forecast_evidence"],
            evaluation_observation=evaluation_observation,
            measurement_evidence=measurement_evidence,
            evaluation_information_set=evaluation_information_set,
            durable_store_root=store_root,
        )
        record = MiOfflineDurableEvidenceStoreV1(store_root).get(
            result["persistence"]["durable_evidence_id"]
        )
        ack = seal_v1(
            {
                "schema_version": ACK_SCHEMA,
                "authority": "NONE",
                "job_key": binding["job_key"],
                "frozen_digest": binding["exact_content_digest"],
                "measurement_inputs_digest": original_inputs["exact_content_digest"],
                "durable_evidence_id": result["persistence"]["durable_evidence_id"],
                "original_record_exact_digest": digest_v1(record),
                "forecast_evidence_id": result["forecast_evidence_id"],
                "actual_outcome_ref": result["actual_outcome_ref"],
                "calibration_result": result["calibration_evidence"]["calibration_result"],
                "method_formula": "realized_return - mean_return",
                "distribution_calibration_proven": False,
                "source_authenticated": False,
                "productive_apply_authorized": False,
            }
        )
        _readback(store_root, ack)
        _append(folder / "calibration_ack.json", ack)
        return ack


def _readback(root, ack):
    record = MiOfflineDurableEvidenceStoreV1(root).get(ack["durable_evidence_id"])
    require_v1(
        digest_v1(record) == ack["original_record_exact_digest"], "ORIGINAL_TRIAD_BYTES_CHANGED"
    )
    numeric = read_measured_return_calibration_v1(
        durable_store_root=root,
        durable_evidence_id=ack["durable_evidence_id"],
        forecast_evidence_id=ack["forecast_evidence_id"],
        actual_outcome_ref=ack["actual_outcome_ref"],
    )
    require_v1(
        bytes_v1(numeric) == bytes_v1(ack["calibration_result"]), "NUMERIC_READBACK_MISMATCH"
    )
    return record


def handoff_calibrated_intelligence_evidence_v1(
    *,
    store_root: Path | str,
    learning_store_root: Path | str,
    frozen: Mapping[str, Any],
    calibration_ack: Mapping[str, Any],
) -> dict[str, Any]:
    """Separate typed Learning persistence and original OPT intake, never a PnL label."""
    from .mi_to_learning_evidence_bridge_v1 import compose_mi_to_learning_evidence_v1
    from .mi_learning_evidence_store_v1 import MiLearningEvidenceStoreV1
    from .mi_learning_evidence_learning_export_v1 import (
        export_mi_learning_evidence_onto_learning_path_v1,
    )
    from .mi_optimization_research_input_v1 import (
        MarketIntelligenceOptimizationResearchInputRequestV1,
        validate_market_intelligence_optimization_research_input_v1,
        STATUS_ACCEPTED,
    )

    assert_offline_v1()
    binding = validate_seal_v1(frozen, FROZEN_SCHEMA)
    ack = validate_seal_v1(calibration_ack, ACK_SCHEMA)
    require_v1(
        ack["frozen_digest"] == binding["exact_content_digest"]
        and ack["job_key"] == binding["job_key"],
        "HANDOFF_PARENT_MISMATCH",
    )
    with _lease(store_root, digest_v1(binding["job_key"])) as folder:
        if (folder / "learning_opt_ack.json").exists():
            previous = _read(
                folder / "learning_opt_ack.json", "exact_intelligence_learning_opt_handoff_v1"
            )
            require_v1(
                previous["learning_store_root"] == str(Path(learning_store_root).resolve()),
                "LEARNING_RECIPIENT_CONFLICT",
            )
        require_v1(
            bytes_v1(_read(folder / "forecast.json", FROZEN_SCHEMA)) == bytes_v1(binding),
            "FROZEN_FORECAST_CHANGED",
        )
        require_v1(
            bytes_v1(_read(folder / "calibration_ack.json", ACK_SCHEMA)) == bytes_v1(ack),
            "CALIBRATION_ACK_CHANGED",
        )
        record = _readback(store_root, ack)
        measured = _read(folder / "measurement.json", "exact_intelligence_measurement_inputs_v1")
        require_v1(
            measured["exact_content_digest"] == ack["measurement_inputs_digest"],
            "MEASUREMENT_ACK_MISMATCH",
        )
        learning = compose_mi_to_learning_evidence_v1(
            forecast_evidence=record["forecast_evidence"],
            evaluation_observation=measured["evaluation_observation"],
            realized_scalar=measured["measurement_evidence"]["log_return"],
            calibration_evidence=record["calibration_evidence"],
            provenance={"exact_calibration_readback_digest": ack["exact_content_digest"]},
        )
        learning_owner = MiLearningEvidenceStoreV1(learning_store_root)
        learning_owner.append(learning)
        readback = MiLearningEvidenceStoreV1(learning_store_root).get(
            learning["mi_learning_evidence_id"]
        )
        require_v1(bytes_v1(readback) == bytes_v1(learning), "LEARNING_READBACK_MISMATCH")
        exported = export_mi_learning_evidence_onto_learning_path_v1(readback)
        opt = validate_market_intelligence_optimization_research_input_v1(
            MarketIntelligenceOptimizationResearchInputRequestV1(
                market_intelligence_research_evidence=record["research_evidence"]
            )
        )
        require_v1(opt["status"] == STATUS_ACCEPTED, "OPT_TYPED_INTAKE_REJECTED")
        result = seal_v1(
            {
                "schema_version": "exact_intelligence_learning_opt_handoff_v1",
                "authority": "NONE",
                "calibration_ack_digest": ack["exact_content_digest"],
                "learning_store_root": str(Path(learning_store_root).resolve()),
                "learning_export": exported,
                "optimization_intake_ack": opt,
                "research_evidence": record["research_evidence"],
                "numeric_feature_consumption_proven": False,
                "productive_apply_authorized": False,
            }
        )
        _append(folder / "learning_opt_ack.json", result)
        return result


def read_calibrated_intelligence_v1(
    *, store_root: Path | str, job_key: Mapping[str, Any]
) -> dict[str, Any]:
    """Cold evidence read; never executes provider, engine, evaluator or calibration."""
    assert_offline_v1()
    require_v1(
        (Path(store_root) / ".intelligence-integration-v1" / digest_v1(job_key)).is_dir(),
        "ORIGINAL_JOB_NOT_FOUND",
    )
    with _lease(store_root, digest_v1(job_key)) as folder:
        frozen = _read(folder / "forecast.json", FROZEN_SCHEMA)
        ack = _read(folder / "calibration_ack.json", ACK_SCHEMA)
        measured = _read(folder / "measurement.json", "exact_intelligence_measurement_inputs_v1")
        require_v1(frozen["job_key"] == dict(job_key) == ack["job_key"], "READBACK_JOB_MISMATCH")
        require_v1(
            ack["frozen_digest"] == frozen["exact_content_digest"] == measured["frozen_digest"],
            "READBACK_FORECAST_MISMATCH",
        )
        require_v1(
            ack["measurement_inputs_digest"] == measured["exact_content_digest"],
            "READBACK_MEASUREMENT_MISMATCH",
        )
        record = _readback(store_root, ack)
        return {
            "frozen": frozen,
            "calibration_ack": ack,
            "measurement_inputs": measured,
            "original_record": plain_v1(record),
        }
