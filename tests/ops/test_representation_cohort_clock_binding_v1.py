"""Declared cohort clocks must bind original recorded jobs before a next consumer."""

from datetime import datetime, timedelta, timezone
import hashlib

import pytest

from scripts.ops import run_offline_learning_representation_sequence_v1 as cohort
from scripts.ops import route_offline_paired_market_representation_meta_v1 as meta
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    _append,
    _read,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.independent_market_forecast_measurement_v1 import (
    calibrate_frozen_market_forecast_v1,
    read_independent_market_calibration_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    digest_v1,
    instant_v1,
    seal_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    compose_recorded_market_context_v1,
    measure_recorded_market_horizon_v1,
)
from tests.learning.test_offline_recorded_market_replay_v1 import (
    CONTEXT_POLICY,
    IDENTITY,
    market_request,
    seed_frozen_forecast,
    utc,
    write_archive,
)

VARIANTS = ("plain", "zero_fraction", "utc_offset_zero")


def _stamp(value, nanos=0, suffix="Z"):
    return instant_v1(value).strftime("%Y-%m-%dT%H:%M:%S") + f".{nanos:09d}{suffix}"


def _case(root, variant="plain"):
    root.mkdir(parents=True)
    store = root / "store"
    first = datetime(2026, 10, 9, 6, tzinfo=timezone.utc)
    jobs, frozen_jobs, observations, starts = [], [], [], []
    previous = None
    for index in range(8):
        opened = first + timedelta(days=index)
        source = write_archive(
            root / f"source-{index}",
            opened=opened,
            received=opened + timedelta(hours=2, seconds=2),
            closes=(100 + index, 101 + index),
        )
        context = compose_recorded_market_context_v1(
            archive=source,
            identity=IDENTITY,
            policy=CONTEXT_POLICY,
            bar_open_utc=utc(opened + timedelta(hours=1)),
            observed_at=utc(opened + timedelta(hours=2, seconds=2)),
        )
        start = opened + timedelta(hours=3)
        request = market_request(start)
        if previous is None:
            frozen = seed_frozen_forecast(store, context, request)
        else:
            inputs = {
                "previous_job_key": previous["job_key"],
                "previous_measurement_digest": observations[-1]["exact_content_digest"],
                "context_digest": context["exact_content_digest"],
                "request": request,
                "forecast_context_max_age_seconds": 300,
                "repository_sha": "a" * 40,
            }
            plan = seal_v1(
                {
                    "schema_version": cohort.PLAN_SCHEMA,
                    "authority": "NONE",
                    "inputs": inputs,
                    "forecast_at_utc": context["as_of"],
                }
            )
            predecessor = store / ".intelligence-integration-v1" / digest_v1(previous["job_key"])
            _append(predecessor / "recorded_representation_successor_plan.json", plan)
            frozen = cohort._freeze_benchmark(
                store_root=store,
                context=context,
                observation=observations[-1],
                request=request,
                plan=plan,
            )
            _append(
                predecessor / "recorded_representation_successor.json",
                seal_v1(
                    {
                        "schema_version": cohort.LINK_SCHEMA,
                        "authority": "NONE",
                        "plan_digest": plan["exact_content_digest"],
                        "job_key": frozen["job_key"],
                        "forecast_digest": frozen["exact_content_digest"],
                    }
                ),
            )
        outcome = write_archive(
            root / f"outcome-{index}",
            opened=start,
            received=start + timedelta(hours=2, seconds=2),
            closes=(102 + index, 103 + index),
        )
        observation = measure_recorded_market_horizon_v1(
            archive=outcome,
            request=request,
            evaluated_at_utc=utc(start + timedelta(hours=2, seconds=2)),
        )
        calibrate_frozen_market_forecast_v1(
            store_root=store, frozen=frozen, market_observation=observation
        )
        jobs.append({"store_root": store, "job_key": frozen["job_key"]})
        frozen_jobs.append(frozen)
        observations.append(observation)
        starts.append(start.isoformat())
        previous = frozen
    if variant == "zero_fraction":
        starts = [_stamp(value) for value in starts]
    if variant == "utc_offset_zero":
        starts = [_stamp(value, suffix="+00:00") for value in starts]
    plan = seal_v1(
        {
            "schema_version": cohort.COHORT_SCHEMA,
            "authority": "NONE",
            "seed_job_key": jobs[0]["job_key"],
            "seed_context_digest": frozen_jobs[0]["context_package"]["exact_content_digest"],
            "starts_utc": starts,
            "fit_window_count": 6,
            "validation_fraction": 0.25,
            "repository_sha": "a" * 40,
            "forecast_context_max_age_seconds": 300,
        }
    )
    return store, plan, jobs


def _files(root):
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


def _verified_measurement(**locator):
    assert locator.pop("capture_window") is cohort._without_network
    packet = read_independent_market_calibration_v1(**locator)
    return {
        "status": "COMPLETED",
        "calibration_ack": packet["calibration_ack"],
        "captured_at_utc": packet["measurement_inputs"]["market_observation"]["evaluated_at_utc"],
    }


def _packet(store, plan, jobs):
    locators, receipts = meta._declared_cohort_jobs(store, plan)
    assert locators == jobs
    packets = [read_independent_market_calibration_v1(**locator) for locator in locators]
    successors = []
    for locator in locators[:-1]:
        folder = store / ".intelligence-integration-v1" / digest_v1(locator["job_key"])
        successors.append(
            {
                "plan": _read(
                    folder / "recorded_representation_successor_plan.json", cohort.PLAN_SCHEMA
                ),
                "link": _read(
                    folder / "recorded_representation_successor.json", cohort.LINK_SCHEMA
                ),
            }
        )
    return {
        "cohort_plan": plan,
        "original_packets": packets,
        "successors": successors,
        "job_keys": [locator["job_key"] for locator in locators],
        "receipt_times": receipts,
    }


def _forbidden(*args, **kwargs):
    pytest.fail("A contradictory declared clock reached the next original consumer")


class ReachedOriginalConsumer(Exception):
    pass


def _reached(*args, **kwargs):
    raise ReachedOriginalConsumer


def _invoke_producer(entry, root, store, plan, declared):
    if entry == "successor":
        return cohort.prepare_recorded_representation_successor_v1(
            store_root=store,
            job_key=plan["seed_job_key"],
            next_start_utc=declared,
            repository_sha="a" * 40,
            trade_count=2,
            max_age_seconds_by_role={"price_o4": 7200},
            forecast_context_max_age_seconds=300,
            fetch=_forbidden,
        )
    return cohort.run_representation_cohort_v1(
        store_root=store,
        seed_job_key=plan["seed_job_key"],
        seed_context_root=root / "unused",
        next_starts_utc=[declared, *plan["starts_utc"][2:]],
        fit_window_count=6,
        validation_fraction=0.25,
        repository_sha="a" * 40,
        forecast_context_max_age_seconds=300,
        wait=False,
    )


@pytest.mark.parametrize("entry", ["successor", "cohort"])
@pytest.mark.parametrize("nanos", [1, 999])
def test_fractional_hour_stops_before_original_reader_or_context(
    entry, nanos, tmp_path, monkeypatch
):
    store, plan, _ = _case(tmp_path / "originals")
    before = _files(tmp_path)
    monkeypatch.setattr(cohort, "read_independent_market_calibration_v1", _forbidden)
    monkeypatch.setattr(
        cohort.representation, "read_recorded_representation_context_v1", _forbidden
    )
    reason = (
        "HOURLY_GRID_REQUIRED"
        if entry == "successor"
        else "EXPLICIT_REPRESENTATION_SPLIT_AND_WINDOWS_REQUIRED"
    )
    with pytest.raises(ValueError, match=reason):
        _invoke_producer(entry, tmp_path, store, plan, _stamp(plan["starts_utc"][1], nanos))
    assert _files(tmp_path) == before


@pytest.mark.parametrize("entry", ["successor", "cohort"])
@pytest.mark.parametrize("variant", VARIANTS)
def test_equivalent_exact_hours_reach_the_existing_consumer(entry, variant, tmp_path, monkeypatch):
    store, plan, _ = _case(tmp_path / "originals", variant)
    before = _files(tmp_path)
    monkeypatch.setattr(cohort, "read_independent_market_calibration_v1", _reached)
    monkeypatch.setattr(cohort.representation, "read_recorded_representation_context_v1", _reached)
    with pytest.raises(ReachedOriginalConsumer):
        _invoke_producer(entry, tmp_path, store, plan, plan["starts_utc"][1])
    assert _files(tmp_path) == before


@pytest.mark.parametrize("boundary", ["forecast", "successor"])
@pytest.mark.parametrize("nanos", [1, 999])
def test_declared_start_cannot_alias_a_different_original_hour(
    boundary, nanos, tmp_path, monkeypatch
):
    store, original, jobs = _case(tmp_path / "originals")
    plan = {key: value for key, value in original.items() if key != "exact_content_digest"}
    plan["starts_utc"] = list(plan["starts_utc"])
    plan["starts_utc"][0 if boundary == "forecast" else 1] = _stamp(
        plan["starts_utc"][0 if boundary == "forecast" else 1], nanos
    )
    plan = seal_v1(plan)
    before = _files(tmp_path)
    if boundary == "forecast":
        monkeypatch.setattr(meta.measurement, "advance_recorded_market_measurement_v1", _forbidden)
        reason = "META_COHORT_ORIGINAL_FORECAST_MISMATCH"
    else:
        read = meta.read_frozen_market_forecast_v1

        def checked_read(**locator):
            if locator["job_key"] == jobs[1]["job_key"]:
                _forbidden()
            return read(**locator)

        monkeypatch.setattr(meta, "read_frozen_market_forecast_v1", checked_read)
        monkeypatch.setattr(
            meta.measurement, "advance_recorded_market_measurement_v1", _verified_measurement
        )
        reason = "META_COHORT_ORIGINAL_SUCCESSOR_MISMATCH"
    with pytest.raises(ValueError, match=reason):
        meta._declared_cohort_jobs(store, plan)
    assert _files(tmp_path) == before


@pytest.mark.parametrize("variant", VARIANTS)
def test_valid_stored_clock_forms_preserve_original_chain_and_receipts(
    variant, tmp_path, monkeypatch
):
    store, plan, jobs = _case(tmp_path / "originals", variant)
    before = _files(tmp_path)
    monkeypatch.setattr(
        meta.measurement, "advance_recorded_market_measurement_v1", _verified_measurement
    )
    packet = _packet(store, plan, jobs)
    assert packet["job_keys"] == [locator["job_key"] for locator in jobs]
    assert len(packet["receipt_times"]) == len(packet["original_packets"]) == 8
    assert len(packet["successors"]) == 7
    assert _files(tmp_path) == before
