"""Exact clocks before archived measurement consumers and capture publication."""

from datetime import datetime, timedelta, timezone
import json

import pytest

from scripts.ops import capture_offline_learning_mark_window_v1 as capture
from scripts.ops import run_offline_learning_mark_measurement_v1 as scheduler
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    read_frozen_market_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    compose_recorded_market_context_v1,
)
from tests.learning.test_offline_recorded_market_replay_v1 import (
    CONTEXT_POLICY,
    IDENTITY,
    market_request,
    seed_frozen_forecast,
    utc,
    write_archive,
)
from tests.ops.test_capture_offline_learning_mark_window_v1 import capture_args, mark_page
from tests.ops.test_representation_cohort_clock_binding_v1 import _files, _stamp


def _forbidden(*args, **kwargs):
    pytest.fail("Inconsistent original clock reached capture, measurement or publication")


@pytest.fixture
def job(tmp_path, monkeypatch):
    def make(context_nanos=0):
        opened = datetime(2026, 10, 9, 10, tzinfo=timezone.utc)
        received = opened + timedelta(hours=1, seconds=3)
        source = write_archive(tmp_path / "source", opened=opened, received=received, closes=(100,))
        context = compose_recorded_market_context_v1(
            archive=source,
            identity=IDENTITY,
            bar_open_utc=utc(opened),
            observed_at=_stamp(utc(received), context_nanos),
            policy=CONTEXT_POLICY,
        )
        horizon = opened + timedelta(hours=2)
        store = tmp_path / "store"
        frozen = seed_frozen_forecast(store, context, market_request(horizon))
        verified = utc(received + timedelta(seconds=2))
        monkeypatch.setattr(scheduler, "_utc_now", lambda: verified)
        monkeypatch.setattr(capture, "HTTPSConnection", _forbidden)
        inputs = dict(
            store_root=store,
            job_key=frozen["job_key"],
            binding_path=source.binding_path,
            binding_sha256=source.binding_sha256,
            repository_sha="a" * 40,
            capture_delay_seconds=10,
        )
        return inputs, horizon, frozen

    return make


def _archive(inputs, horizon, when, monkeypatch):
    schedule = scheduler.schedule_recorded_market_measurement_v1(**inputs)
    locator = {k: inputs[k] for k in ("store_root", "job_key")}
    root = (
        inputs["store_root"]
        / ".intelligence-integration-v1"
        / scheduler.digest_v1(inputs["job_key"])
        / "recorded_outcome_archive"
    )
    monkeypatch.setattr(capture, "_utc_now", lambda: when)
    capture.capture_public_mark_window_v1(
        output=root,
        start_utc=utc(horizon),
        hours=2,
        binding_path=inputs["binding_path"],
        binding_sha256=inputs["binding_sha256"],
        repository_sha=inputs["repository_sha"],
        fetch_page=mark_page,
    )
    return locator, schedule


@pytest.mark.parametrize("nanos", [1, 999])
def test_verification_before_original_forecast_stops_before_writer(
    job, nanos, tmp_path, monkeypatch
):
    inputs, _, frozen = job(nanos)
    monkeypatch.setattr(scheduler, "_utc_now", lambda: _stamp(frozen["context_package"]["as_of"]))
    monkeypatch.setattr(scheduler, "_append", _forbidden)
    before = _files(tmp_path)
    with pytest.raises(ValueError, match="^FORECAST_NOT_OBSERVED_BEFORE_WINDOW$"):
        scheduler.schedule_recorded_market_measurement_v1(**inputs)
    assert _files(tmp_path) == before


@pytest.mark.parametrize("nanos", [1, 999])
def test_expired_instant_never_starts_capture(job, nanos, tmp_path, monkeypatch):
    inputs, horizon, _ = job()
    scheduler.schedule_recorded_market_measurement_v1(**inputs)
    expired = utc(horizon + timedelta(hours=2, seconds=300))
    monkeypatch.setattr(scheduler, "_utc_now", lambda: _stamp(expired, nanos))
    before = _files(tmp_path)
    result = scheduler.advance_recorded_market_measurement_v1(
        **{k: inputs[k] for k in ("store_root", "job_key")}, capture_window=_forbidden
    )
    assert result["status"] == "EXPIRED"
    assert _files(tmp_path) == before


@pytest.mark.parametrize("fault", ["late", "future"])
@pytest.mark.parametrize("nanos", [1, 999])
def test_archived_receipt_clock_rejects_before_original_measurement(
    job, fault, nanos, tmp_path, monkeypatch
):
    inputs, horizon, _ = job()
    base = horizon + timedelta(hours=2, seconds=300 if fault == "late" else 20)
    locator, _ = _archive(inputs, horizon, _stamp(utc(base), nanos), monkeypatch)
    now = utc(base + timedelta(seconds=2)) if fault == "late" else utc(base)
    monkeypatch.setattr(scheduler, "_utc_now", lambda: now)
    monkeypatch.setattr(scheduler, "complete_recorded_market_forecast_v1", _forbidden)
    before = _files(tmp_path)
    with pytest.raises(ValueError, match="^MEASUREMENT_CAPTURE_OUTSIDE_SCHEDULE$"):
        scheduler.advance_recorded_market_measurement_v1(**locator, capture_window=_forbidden)
    assert _files(tmp_path) == before


@pytest.mark.parametrize("seconds", [10, 300])
@pytest.mark.parametrize("suffix", ["plain", "Z", "+00:00"])
def test_inclusive_capture_boundaries_remain_readable_after_restart(
    job, seconds, suffix, tmp_path, monkeypatch
):
    inputs, horizon, _ = job()
    when = utc(horizon + timedelta(hours=2, seconds=seconds))
    if suffix != "plain":
        when = _stamp(when, suffix=suffix)
    locator, _ = _archive(inputs, horizon, when, monkeypatch)
    monkeypatch.setattr(scheduler, "_utc_now", lambda: utc(horizon + timedelta(hours=3)))
    result = scheduler.advance_recorded_market_measurement_v1(**locator, capture_window=_forbidden)
    assert result["status"] == "COMPLETED" and result["captured_at_utc"] == when
    before = _files(tmp_path)
    assert (
        scheduler.advance_recorded_market_measurement_v1(**locator, capture_window=_forbidden)
        == result
    )
    assert _files(tmp_path) == before


@pytest.mark.parametrize("nanos", [1, 999])
def test_capture_raw_hourly_grid_rejects_before_binding_read(
    capture_args, nanos, tmp_path, monkeypatch
):
    args = {**capture_args, "start_utc": _stamp(capture_args["start_utc"], nanos)}
    before = _files(tmp_path)
    original = type(args["binding_path"]).read_bytes

    def checked_read(path):
        if path == args["binding_path"]:
            _forbidden()
        return original(path)

    with monkeypatch.context() as patch:
        patch.setattr(type(args["binding_path"]), "read_bytes", checked_read)
        with pytest.raises(ValueError, match="^EXPLICIT_HOURLY_GRID_REQUIRED$"):
            capture.capture_public_mark_window_v1(**args, fetch_page=_forbidden)
    assert _files(tmp_path) == before


@pytest.mark.parametrize("nanos", [1, 999])
def test_response_cannot_precede_its_request_before_page_write(capture_args, nanos, monkeypatch):
    args = {**capture_args, "hours": 1}
    base = "2026-10-09T13:00:05Z"
    times = iter([base, _stamp(base, nanos), base])
    monkeypatch.setattr(capture, "_utc_now", lambda: next(times))
    monkeypatch.setattr(capture, "_write", _forbidden)
    with pytest.raises(ValueError, match="^CAPTURE_RESPONSE_BEFORE_REQUEST$"):
        capture.capture_public_mark_window_v1(**args, fetch_page=mark_page)
    assert not args["output"].exists()


@pytest.mark.parametrize("nanos", [1, 999])
def test_availability_is_latest_original_instant_not_lexical_max(capture_args, nanos, monkeypatch):
    base = "2026-10-09T13:00:05Z"
    latest = _stamp(base, nanos)
    times = iter([base, base, base, base, latest])
    monkeypatch.setattr(capture, "_utc_now", lambda: next(times, latest))
    manifest = capture.capture_public_mark_window_v1(**capture_args, fetch_page=mark_page)
    assert manifest["available_at_utc"] == latest
    log = json.loads((capture_args["output"] / "request_log.json").read_bytes())
    assert log[-1]["response_time_utc"] == latest
