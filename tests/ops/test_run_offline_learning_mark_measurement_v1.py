"""Timed continuation over the original forecast and public capture stores."""

from datetime import datetime, timedelta, timezone
import json
import math

import pytest

from scripts.ops import capture_offline_learning_mark_window_v1 as capture
from scripts.ops import run_offline_learning_mark_measurement_v1 as scheduler
from scripts.ops import run_offline_learning_mark_sequence_v1 as sequence
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    read_frozen_market_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.independent_market_forecast_measurement_v1 import (
    read_independent_market_calibration_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    digest_v1,
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
    compose_recorded_market_context_v1,
    forecast_from_recorded_market_context_v1,
)
from tests.learning.test_offline_recorded_market_replay_v1 import (
    CONTEXT_POLICY,
    IDENTITY,
    market_request,
    seed_frozen_forecast,
    utc,
    write_archive,
)


@pytest.fixture
def scheduled_job(tmp_path, monkeypatch):
    opened = datetime(2026, 10, 9, 10, tzinfo=timezone.utc)
    received = opened + timedelta(hours=1, seconds=3)
    horizon = opened + timedelta(hours=2)
    source = write_archive(tmp_path / "context", opened=opened, received=received, closes=(100,))
    context = compose_recorded_market_context_v1(
        archive=source,
        identity=IDENTITY,
        bar_open_utc=utc(opened),
        observed_at=utc(received),
        policy=CONTEXT_POLICY,
    )
    store = tmp_path / "evidence"
    frozen = seed_frozen_forecast(store, context, market_request(horizon))
    clock = [received + timedelta(seconds=2)]
    monkeypatch.setattr(scheduler, "_utc_now", lambda: utc(clock[0]))
    monkeypatch.setattr(capture, "_utc_now", lambda: utc(clock[0]))
    inputs = {
        "store_root": store,
        "job_key": frozen["job_key"],
        "binding_path": source.binding_path,
        "binding_sha256": source.binding_sha256,
        "repository_sha": source.repository_sha,
        "capture_delay_seconds": 10,
    }
    return inputs, horizon, clock


def unexpected(*args, **kwargs):
    raise AssertionError("Unexpected capture or measurement")


def test_schedule_waits_then_resumes_timely_capture_after_restart(scheduled_job, monkeypatch):
    inputs, horizon, clock = scheduled_job
    registered = scheduler.schedule_recorded_market_measurement_v1(**inputs)
    assert registered == scheduler.schedule_recorded_market_measurement_v1(**inputs)
    with pytest.raises(ValueError, match="^MEASUREMENT_SCHEDULE_CONFLICT$"):
        scheduler.schedule_recorded_market_measurement_v1(**{**inputs, "capture_delay_seconds": 11})
    key = {name: inputs[name] for name in ("store_root", "job_key")}
    end = horizon + timedelta(hours=2)
    due = end + timedelta(seconds=10)
    clock[0] = due - timedelta(seconds=1)
    assert scheduler.advance_recorded_market_measurement_v1(**key, capture_window=unexpected) == {
        "status": "WAITING",
        "capture_at_utc": due.isoformat(),
    }

    clock[0] = due
    captured_pages = []

    def fetch(query):
        clock[0] += timedelta(seconds=1)
        captured_pages.append(query)
        rows = []
        for index in range(int(query["limit"])):
            opened = int(query["after"]) - 60_000 * (index + 1)
            price = "100" if opened < (horizon + timedelta(hours=1)).timestamp() * 1000 else "101"
            rows.append([str(opened), price, price, price, price, "1"])
        return 200, json.dumps({"code": "0", "data": rows}).encode()

    def interrupted(**kwargs):
        raise RuntimeError("interrupted after capture")

    with monkeypatch.context() as interrupted_process:
        interrupted_process.setattr(scheduler, "complete_recorded_market_forecast_v1", interrupted)
        with pytest.raises(RuntimeError, match="interrupted after capture"):
            scheduler.advance_recorded_market_measurement_v1(
                **key,
                capture_window=lambda **kwargs: capture.capture_public_mark_window_v1(
                    **kwargs, fetch_page=fetch
                ),
            )
    assert [page["limit"] for page in captured_pages] == ["100", "20"]
    captured_at = utc(clock[0])
    clock[0] = end + timedelta(minutes=6)
    result = scheduler.advance_recorded_market_measurement_v1(**key, capture_window=unexpected)
    assert result["status"] == "COMPLETED"
    assert result["captured_at_utc"] == captured_at
    assert result["calibration_ack"]["calibration_result"]["realized_return"] == pytest.approx(
        math.log(101 / 100)
    )
    assert (
        read_independent_market_calibration_v1(**key)["calibration_ack"]
        == result["calibration_ack"]
    )
    assert (
        scheduler.advance_recorded_market_measurement_v1(**key, capture_window=unexpected) == result
    )


def test_no_schedule_after_window_start_and_no_capture_after_expiry(scheduled_job):
    inputs, horizon, clock = scheduled_job
    clock[0] = horizon
    with pytest.raises(ValueError, match="^FORECAST_NOT_OBSERVED_BEFORE_WINDOW$"):
        scheduler.schedule_recorded_market_measurement_v1(**inputs)
    clock[0] = horizon - timedelta(seconds=1)
    scheduler.schedule_recorded_market_measurement_v1(**inputs)
    clock[0] = horizon + timedelta(hours=2, minutes=6)
    assert (
        scheduler.advance_recorded_market_measurement_v1(
            store_root=inputs["store_root"], job_key=inputs["job_key"], capture_window=unexpected
        )["status"]
        == "EXPIRED"
    )


def _complete_window(locator, horizon, clock, closes):
    clock[0] = horizon + timedelta(hours=2, seconds=10)
    second_hour_ms = int((horizon + timedelta(hours=1)).timestamp() * 1000)

    def fetch(query):
        clock[0] += timedelta(seconds=1)
        rows = []
        for index in range(int(query["limit"])):
            opened = int(query["after"]) - 60_000 * (index + 1)
            price = str(closes[int(opened >= second_hour_ms)])
            rows.append([str(opened), price, price, price, price, "1"])
        return 200, json.dumps({"code": "0", "data": rows}).encode()

    return scheduler.advance_recorded_market_measurement_v1(
        **locator,
        capture_window=lambda **kwargs: capture.capture_public_mark_window_v1(
            **kwargs, fetch_page=fetch
        ),
    )


def test_successor_retries_original_forecast_without_backdating(scheduled_job, monkeypatch):
    inputs, horizon, clock = scheduled_job
    scheduler.schedule_recorded_market_measurement_v1(**inputs)
    seed = {name: inputs[name] for name in ("store_root", "job_key")}
    following = horizon + timedelta(hours=3)
    args = {
        **seed,
        "next_start_utc": utc(following),
        "context_max_age_seconds": 3600,
        "repository_sha": "b" * 40,
    }
    with pytest.raises(ValueError, match="^COMPLETED_PREDECESSOR_REQUIRED$"):
        sequence.prepare_recorded_market_successor_v1(**args)
    result = _complete_window(seed, horizon, clock, (100, 101))
    with pytest.raises(ValueError, match="^SUCCESSOR_MUST_FOLLOW_AVAILABLE_OUTCOME$"):
        sequence.prepare_recorded_market_successor_v1(
            **{**args, "next_start_utc": utc(horizon + timedelta(hours=2))}
        )
    receipt_time = clock[0]
    clock[0] = following
    with pytest.raises(ValueError, match="^SUCCESSOR_WINDOW_NOT_FUTURE$"):
        sequence.prepare_recorded_market_successor_v1(**args)
    clock[0] = receipt_time + timedelta(seconds=1)
    initial_forecast_at = utc(clock[0])
    with monkeypatch.context() as crash:
        crash.setattr(scheduler, "schedule_recorded_market_measurement_v1", unexpected)
        with pytest.raises(AssertionError, match="Unexpected capture or measurement"):
            sequence.prepare_recorded_market_successor_v1(**args)

    clock[0] += timedelta(seconds=1)
    schedule = sequence.prepare_recorded_market_successor_v1(**args)
    next_job = {"store_root": seed["store_root"], "job_key": schedule["plan"]["job_key"]}
    frozen = read_frozen_market_forecast_v1(**next_job)
    forecast = frozen["forecast_evidence"]
    assert forecast["forecast_created_at_utc"] == initial_forecast_at
    assert schedule["forecast_verified_at_utc"] == utc(clock[0])
    assert schedule["plan"]["repository_sha"] == "b" * 40
    assert forecast["probabilistic_payload"] == {
        "mean_return": pytest.approx(math.log(101 / 100)),
        "std_return": 0.0,
    }
    assert (
        forecast["provenance"]["previous_measurement_digest"]
        == result["calibration_ack"]["market_observation_digest"]
    )
    assert frozen["context_package"]["as_of"] == initial_forecast_at
    assert frozen["context_package"]["source_bindings"][0]["payload"]["bar"]["close"] == 101.0
    with pytest.raises(ValueError, match="^SUCCESSOR_PLAN_CONFLICT$"):
        sequence.prepare_recorded_market_successor_v1(
            **{**args, "next_start_utc": utc(following + timedelta(hours=1))}
        )
    clock[0] = following
    assert sequence.prepare_recorded_market_successor_v1(**args) == schedule
    archive_root = (
        seed["store_root"]
        / ".intelligence-integration-v1"
        / digest_v1(seed["job_key"])
        / "recorded_outcome_archive"
    )
    page = capture.read_captured_mark_archive_v1(archive_root).raw_path
    page.write_bytes(page.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="^SOURCE_SHA256_MISMATCH$"):
        sequence.prepare_recorded_market_successor_v1(**args)


def test_four_scheduled_windows_train_and_feed_existing_ols_forecast(scheduled_job, tmp_path):
    inputs, horizon, clock = scheduled_job
    scheduler.schedule_recorded_market_measurement_v1(**inputs)
    store = inputs["store_root"]
    locator = {"store_root": store, "job_key": inputs["job_key"]}
    jobs, receipts = [], []
    model_store = tmp_path / "models"
    for index, close in enumerate((101, 104, 103, 108)):
        result = _complete_window(locator, horizon, clock, (100 + index, close))
        assert result["status"] == "COMPLETED"
        jobs.append(locator["job_key"])
        receipts.append(result["captured_at_utc"])
        horizon += timedelta(hours=3)
        if index < 3:
            successor = sequence.prepare_recorded_market_successor_v1(
                **locator,
                next_start_utc=utc(horizon),
                context_max_age_seconds=3600,
                repository_sha=inputs["repository_sha"],
            )
            locator["job_key"] = successor["plan"]["job_key"]

    request = market_request(horizon)
    training = {
        "evidence_store_root": store,
        "market_request": request,
        "model_store_root": model_store,
        "features": [
            MarketOlsFeatureV1(
                "mark", "price_o4", 0, "FinalizedPt1hO4BarFactV1", "close", "USDT per ETH"
            )
        ],
        "policy": MarketOlsPolicyV1(0.5, 2, 2, 0, 3600),
        "trained_as_of": receipts[-1],
        "available_at": receipts[-1],
        "parent_model_ref": None,
    }
    with pytest.raises(ValueError, match="^MODEL_INSUFFICIENT_VALIDATION_ROWS$"):
        train_market_ols_model_from_store_v1(**{**training, "trained_as_of": receipts[-2]})
    model = train_market_ols_model_from_store_v1(**training)
    samples = model["request"]["samples"]
    assert [row["job_key"] for row in samples] == jobs
    assert [row["label_available_at"] for row in samples] == receipts
    assert [row["features"]["mark"] for row in samples] == [100, 101, 104, 103]
    assert model["validation"]["training_rows"] == model["validation"]["validation_rows"] == 2

    archive = capture.read_captured_mark_archive_v1(
        store / ".intelligence-integration-v1" / digest_v1(jobs[-1]) / "recorded_outcome_archive"
    )
    result = forecast_from_recorded_market_context_v1(
        archive=archive,
        bar_open_utc=utc(horizon - timedelta(hours=2)),
        observed_at=receipts[-1],
        context_policy=CONTEXT_POLICY,
        model_store_root=model_store,
        model_ref=model["model_ref"],
        store_root=store,
        market_request=request,
        forecast_created_at=receipts[-1],
        attempt_generation="scheduled-fixture-ols-follow-up",
    )
    coefficients = model["coefficients"]
    expected = coefficients["intercept"] + 108 * coefficients["mark"]
    assert result["provider"]["computed_payload"]["mean_return"] == pytest.approx(expected)
    assert (
        read_market_model_forecast_v1(
            model_store_root=model_store, store_root=store, job_key=result["frozen"]["job_key"]
        )
        == result
    )
    assert train_market_ols_model_from_store_v1(**training) == model
