"""Archive-shaped fixtures for the offline learning-side market replay."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math

import pytest

from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
    REQUEST_SCHEMA,
    build_independent_market_return_target_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
    ContextAdmissionPolicyV1,
    replay_admitted_market_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    MarketIdentityV1,
    bytes_v1,
    digest_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    freeze_existing_market_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.independent_market_forecast_measurement_v1 import (
    read_independent_market_calibration_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_ols_next_forecast_v1 import (
    MarketOlsFeatureV1,
    MarketOlsPolicyV1,
    read_market_model_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_ols_store_training_v1 import (
    train_market_ols_model_from_store_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    RecordedMarkArchiveV1,
    complete_recorded_market_forecast_v1,
    compose_recorded_market_context_v1,
    forecast_from_recorded_market_context_v1,
    measure_recorded_market_horizon_v1,
)
from src.research.offline_recorded_mark_horizon_source_v1 import ENDPOINT

IDENTITY = MarketIdentityV1("archive.test", "OKX", "inst-eth-usdt-perp", "ETH-USDT-SWAP")
CONTEXT_POLICY = ContextAdmissionPolicyV1("explicit.test", {"price_o4": 7200}, ("price_state_ref",))


def utc(value):
    return value.isoformat().replace("+00:00", "Z")


def write_archive(root, *, opened, received, closes):
    root.mkdir()

    def write(name, value):
        data = json.dumps(value).encode("utf-8")
        path = root / name
        path.write_bytes(data)
        return path, hashlib.sha256(data).hexdigest()

    rows = []
    for hour, close in enumerate(closes):
        for minute in range(60):
            start = opened + timedelta(hours=hour, minutes=minute)
            rows.append([str(int(start.timestamp()) * 1000), *([str(close)] * 4), "1"])
    raw = write("raw.json", {"code": "0", "data": rows})
    log = write(
        "request_log.json",
        [
            {
                "raw_response_sha256": raw[1],
                "endpoint": ENDPOINT,
                "query_params": {"instId": IDENTITY.native_instrument_ref, "bar": "1m"},
                "http_status": 200,
                "okx_code": "0",
                "request_time_utc": utc(received - timedelta(seconds=1)),
                "response_time_utc": utc(received),
            }
        ],
    )
    binding = write(
        "binding.json",
        {
            "canonical_instrument_id": IDENTITY.instrument_ref,
            "native_instrument_id": IDENTITY.native_instrument_ref,
            "venue": IDENTITY.venue,
            "instrument_metadata": {
                "instId": IDENTITY.native_instrument_ref,
                "instType": "SWAP",
                "settleCcy": "USDT",
                "uly": "ETH-USDT",
            },
        },
    )
    return RecordedMarkArchiveV1(*raw, *log, *binding, "a" * 40)


def market_request(opened):
    return {
        "schema_version": REQUEST_SCHEMA,
        "market_identity": IDENTITY.payload(),
        "horizon_start_time_utc": utc(opened),
        "n_bars": 2,
        "o4_interval_id": "PT1H",
        "price_unit": "USDT per ETH",
        "price_family": "MARK_PRICE",
        "source_kind": "RECORDED_PUBLIC_MD",
        "max_end_age_seconds": 300,
        "expected_price_basis_kind": "O4_BAR_CLOSE_FINALIZED",
    }


def test_archived_consumers_bind_files_and_reject_early_reads(tmp_path):
    received = datetime(2026, 10, 9, 13, 3, 11, 123456, tzinfo=timezone.utc)
    opened = datetime(2026, 10, 9, 11, tzinfo=timezone.utc)
    archive = write_archive(tmp_path / "case", opened=opened, received=received, closes=(101, 102))
    context_args = {
        "archive": archive,
        "identity": IDENTITY,
        "bar_open_utc": utc(opened),
        "policy": CONTEXT_POLICY,
    }
    context = compose_recorded_market_context_v1(**context_args, observed_at=utc(received))
    assert replay_admitted_market_context_v1(context) == context
    assert context["source_bindings"][0]["captured_at"] == received.isoformat()
    request = market_request(opened)
    observation = measure_recorded_market_horizon_v1(
        archive=archive, request=request, evaluated_at_utc=utc(received)
    )
    assert observation["measurement"]["log_return"] == pytest.approx(math.log(102 / 101))
    assert observation["evaluated_at_utc"] == utc(received)

    archive.raw_path.unlink()
    earlier = "2026-10-09T13:03:11.123455999Z"
    with pytest.raises(ValueError, match="^ARCHIVE_RESPONSE_NOT_YET_AVAILABLE$"):
        compose_recorded_market_context_v1(**context_args, observed_at=earlier)
    with pytest.raises(ValueError, match="^ARCHIVE_RESPONSE_NOT_YET_AVAILABLE$"):
        measure_recorded_market_horizon_v1(
            archive=archive, request=request, evaluated_at_utc=earlier
        )


def seed_frozen_forecast(store_root, context, request):
    target = build_independent_market_return_target_v1(request)
    native = context["market_context"]
    model = b"archive-shaped fixture baseline"
    forecast = mint_forecast_evidence_v1(
        information_set_ref=native["information_set_ref"],
        forecast_created_at_utc=context["as_of"],
        outcome_horizon_end_utc=target["return_end_close_time_utc"],
        n_bars=target["n_bars"],
        bar_spec_ref=target["bar_spec_ref"],
        forecast_kind="RETURN_DISTRIBUTION_SUMMARY",
        probabilistic_payload={"mean_return": 0.0, "std_return": 0.1},
        market_state_refs=[native["context_id"]],
        forecast_model_ref="archive-fixture-baseline",
        support_disposition="SUFFICIENT_EVIDENCE",
        selected_instrument_ref=IDENTITY.instrument_ref,
        provenance={"measured_return_target_v1": target, "archive_fixture": True},
    )
    return freeze_existing_market_forecast_v1(
        store_root=store_root,
        context_package=context,
        forecast_evidence=forecast,
        original_probabilistic_payload=bytes_v1(forecast["probabilistic_payload"]),
        model_artifact_bytes=model,
        attempt_generation="archive-fixture-seed",
        provider_admission={
            "provider_ref": "archive-fixture-provider",
            "model_ref": forecast["forecast_model_ref"],
            "feature_schema_ref": "archive-fixture-feature",
            "training_dataset_ref": "archive-fixture-dataset",
            "validation_ref": "archive-fixture-validation",
            "admitted_by_ref": "archive-fixture-test",
            "model_artifact_sha256": hashlib.sha256(model).hexdigest(),
            "training_end": context["as_of"],
            "available_at": context["as_of"],
            "context_package_digest": context["exact_content_digest"],
            "max_context_age_seconds": 0,
            "target_spec_digest": digest_v1(target),
        },
    )


def test_archive_feedback_reads_frozen_target_and_reuses_stored_weights(tmp_path):
    origin = datetime(2026, 10, 1, 10, tzinfo=timezone.utc)
    evidence_store = tmp_path / "evidence"
    model_store = tmp_path / "models"
    for index in range(6):
        opened = origin + timedelta(days=index)
        context_at = opened + timedelta(hours=1, seconds=3)
        archive = write_archive(
            tmp_path / f"context-{index}", opened=opened, received=context_at, closes=(100 + index,)
        )
        context = compose_recorded_market_context_v1(
            archive=archive,
            identity=IDENTITY,
            bar_open_utc=utc(opened),
            observed_at=utc(context_at),
            policy=CONTEXT_POLICY,
        )
        horizon = opened + timedelta(hours=2)
        request = market_request(horizon)
        frozen = seed_frozen_forecast(evidence_store, context, request)
        receipt_at = horizon + timedelta(hours=2, seconds=3)
        outcome = write_archive(
            tmp_path / f"outcome-{index}",
            opened=horizon,
            received=receipt_at,
            closes=(100, 101 + index),
        )
        complete_recorded_market_forecast_v1(
            store_root=evidence_store,
            job_key=frozen["job_key"],
            archive=outcome,
            evaluated_at_utc=utc(receipt_at),
        )

    training = {
        "evidence_store_root": evidence_store,
        "market_request": request,
        "model_store_root": model_store,
        "features": [
            MarketOlsFeatureV1(
                "mark", "price_o4", 0, "FinalizedPt1hO4BarFactV1", "close", "USDT per ETH"
            )
        ],
        "policy": MarketOlsPolicyV1(0.25, 4, 2, 0, 2 * 86400),
        "trained_as_of": utc(receipt_at),
        "available_at": utc(receipt_at),
        "parent_model_ref": None,
    }
    model = train_market_ols_model_from_store_v1(**training)
    opened = origin + timedelta(days=6)
    context_at = opened + timedelta(hours=1, seconds=3)
    horizon = opened + timedelta(hours=2)
    archive = write_archive(
        tmp_path / "next-context", opened=opened, received=context_at, closes=(109,)
    )
    result = forecast_from_recorded_market_context_v1(
        archive=archive,
        bar_open_utc=utc(opened),
        observed_at=utc(context_at),
        context_policy=CONTEXT_POLICY,
        model_store_root=model_store,
        model_ref=model["model_ref"],
        store_root=evidence_store,
        market_request=market_request(horizon),
        forecast_created_at=utc(context_at),
        attempt_generation="archive-fixture-follow-up",
    )
    job = result["frozen"]["job_key"]
    expected = model["coefficients"]["intercept"] + model["coefficients"]["mark"] * 109
    assert result["provider"]["computed_payload"]["mean_return"] == expected
    assert (
        read_market_model_forecast_v1(
            model_store_root=model_store, store_root=evidence_store, job_key=job
        )
        == result
    )

    receipt_at = horizon + timedelta(hours=2, seconds=3)
    outcome = write_archive(
        tmp_path / "next-outcome", opened=horizon, received=receipt_at, closes=(100, 111)
    )
    args = {"store_root": evidence_store, "job_key": job, "archive": outcome}
    with pytest.raises(ValueError, match="^MARKET_FORECAST_MUST_BE_FROZEN_FIRST$"):
        complete_recorded_market_forecast_v1(
            store_root=evidence_store,
            job_key={**job, "attempt_generation": "unpublished"},
            archive=replace(outcome, request_log_path=tmp_path / "unavailable-log.json"),
            evaluated_at_utc=utc(receipt_at),
        )
    with pytest.raises(ValueError, match="^ARCHIVE_RESPONSE_NOT_YET_AVAILABLE$"):
        complete_recorded_market_forecast_v1(
            **args, evaluated_at_utc=utc(receipt_at - timedelta(seconds=1))
        )
    ack = complete_recorded_market_forecast_v1(**args, evaluated_at_utc=utc(receipt_at))
    assert ack["calibration_result"]["error"] == pytest.approx(math.log(111 / 100) - expected)
    assert complete_recorded_market_forecast_v1(**args, evaluated_at_utc=utc(receipt_at)) == ack
    assert (
        read_independent_market_calibration_v1(store_root=evidence_store, job_key=job)[
            "calibration_ack"
        ]
        == ack
    )
    assert train_market_ols_model_from_store_v1(**training) == model
    child = train_market_ols_model_from_store_v1(
        **{
            **training,
            "trained_as_of": utc(receipt_at),
            "available_at": utc(receipt_at),
            "parent_model_ref": model["model_ref"],
        }
    )
    assert len(child["request"]["samples"]) == 7
    assert child["request"]["samples"][-1]["job_key"] == job
