"""Schedule and advance the public mark measurement for one frozen offline forecast."""

import argparse
from datetime import timedelta
from pathlib import Path
import re
import time

from scripts.ops.capture_offline_learning_mark_window_v1 import (
    _read_manifest,
    _utc_now,
    capture_public_mark_window_v1,
    read_captured_mark_archive_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    _append,
    _lease,
    _read,
    read_frozen_market_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    digest_v1,
    instant_v1,
    require_v1,
    seal_v1,
    strict_json_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    complete_recorded_market_forecast_v1,
    recorded_market_target_from_frozen_v1,
)
from src.research.offline_recorded_mark_horizon_source_v1 import (
    LEGACY_NATIVE_INSTRUMENT as NATIVE_INSTRUMENT,
)
from src.research.offline_recorded_mark_horizon_source_v1 import read_bound_json

SCHEMA = "scheduled_recorded_market_measurement_v1"
PLAN_FILE = "recorded_measurement_schedule.json"


def _bounds(target, delay):
    require_v1(2 <= target["n_bars"] <= 24, "EXPLICIT_BOUNDED_BAR_COUNT_REQUIRED")
    end = instant_v1(target["return_end_close_time_utc"])
    max_age = target["market_request"]["max_end_age_seconds"]
    require_v1(type(delay) is int and 0 <= delay <= max_age, "CAPTURE_DELAY_OUTSIDE_TARGET_POLICY")
    return end + timedelta(seconds=delay), end + timedelta(seconds=max_age)


def _validate_forecast_clock(frozen, target, verified_at):
    require_v1(
        instant_v1(frozen["forecast_evidence"]["forecast_created_at_utc"])
        <= instant_v1(verified_at)
        < instant_v1(target["horizon_start_time_utc"]),
        "FORECAST_NOT_OBSERVED_BEFORE_WINDOW",
    )


def schedule_recorded_market_measurement_v1(
    *, store_root, job_key, binding_path, binding_sha256, repository_sha, capture_delay_seconds
):
    """Bind one original forecast and verify its durable presence before the window."""
    frozen = read_frozen_market_forecast_v1(store_root=store_root, job_key=job_key)
    target = recorded_market_target_from_frozen_v1(frozen)
    _bounds(target, capture_delay_seconds)
    require_v1(re.fullmatch(r"[0-9a-f]{40}", repository_sha) is not None, "REPOSITORY_SHA_REQUIRED")
    binding_path = Path(binding_path).resolve()
    plan = {
        "job_key": dict(job_key),
        "forecast_digest": frozen["exact_content_digest"],
        "binding_path": str(binding_path),
        "binding_sha256": binding_sha256,
        "repository_sha": repository_sha,
        "capture_delay_seconds": capture_delay_seconds,
    }
    with _lease(store_root, digest_v1(job_key)) as folder:
        path = folder / PLAN_FILE
        if path.is_file():
            record = _read(path, SCHEMA)
            require_v1(record["plan"] == plan, "MEASUREMENT_SCHEDULE_CONFLICT")
            _validate_forecast_clock(frozen, target, record["forecast_verified_at_utc"])
            return record
        binding = read_bound_json(binding_path, binding_sha256)
        market = target["market_request"]["market_identity"]
        require_v1(
            isinstance(binding, dict)
            and (market["venue"], market["native_instrument_ref"]) == ("OKX", NATIVE_INSTRUMENT)
            and (
                binding.get("venue"),
                binding.get("canonical_instrument_id"),
                binding.get("native_instrument_id"),
            )
            == (market["venue"], market["instrument_ref"], market["native_instrument_ref"]),
            "MEASUREMENT_SCHEDULE_MARKET_MISMATCH",
        )
        verified_at = _utc_now()
        _validate_forecast_clock(frozen, target, verified_at)
        record = seal_v1(
            {
                "schema_version": SCHEMA,
                "authority": "NONE",
                "plan": plan,
                "forecast_verified_at_utc": verified_at,
            }
        )
        _append(path, record)
        return _read(path, SCHEMA)


def advance_recorded_market_measurement_v1(
    *, store_root, job_key, capture_window=capture_public_mark_window_v1
):
    """Capture only at the scheduled time, or resume an already captured outcome."""
    frozen = read_frozen_market_forecast_v1(store_root=store_root, job_key=job_key)
    target = recorded_market_target_from_frozen_v1(frozen)
    folder = Path(store_root) / ".intelligence-integration-v1" / digest_v1(job_key)
    schedule = _read(folder / PLAN_FILE, SCHEMA)
    plan = schedule["plan"]
    require_v1(
        plan["job_key"] == dict(job_key)
        and plan["forecast_digest"] == frozen["exact_content_digest"],
        "MEASUREMENT_SCHEDULE_FORECAST_MISMATCH",
    )
    _validate_forecast_clock(frozen, target, schedule["forecast_verified_at_utc"])
    due, expires = _bounds(target, plan["capture_delay_seconds"])
    outcome_root = folder / "recorded_outcome_archive"
    capture_plan = {
        "start_utc": target["horizon_start_time_utc"],
        "hours": target["n_bars"],
        "binding_sha256": plan["binding_sha256"],
        "repository_sha": plan["repository_sha"],
    }
    if not outcome_root.exists():
        now = instant_v1(_utc_now())
        if now < due:
            return {"status": "WAITING", "capture_at_utc": due.isoformat()}
        if now > expires:
            return {"status": "EXPIRED", "capture_deadline_utc": expires.isoformat()}
        capture_window(output=outcome_root, binding_path=Path(plan["binding_path"]), **capture_plan)

    manifest = _read_manifest(outcome_root)
    require_v1(manifest["plan"] == capture_plan, "MEASUREMENT_CAPTURE_PLAN_MISMATCH")
    captured_at = manifest["available_at_utc"]
    require_v1(
        due <= instant_v1(captured_at) <= min(expires, instant_v1(_utc_now())),
        "MEASUREMENT_CAPTURE_OUTSIDE_SCHEDULE",
    )
    ack = complete_recorded_market_forecast_v1(
        store_root=store_root,
        job_key=job_key,
        archive=read_captured_mark_archive_v1(outcome_root),
        evaluated_at_utc=captured_at,
    )
    return {"status": "COMPLETED", "captured_at_utc": captured_at, "calibration_ack": ack}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    schedule = commands.add_parser("schedule")
    advance = commands.add_parser("advance")
    for command in (schedule, advance):
        command.add_argument("--store-root", required=True, type=Path)
        command.add_argument("--job-key-file", required=True, type=Path)
    schedule.add_argument("--binding-path", required=True, type=Path)
    schedule.add_argument("--binding-sha256", required=True)
    schedule.add_argument("--repository-sha", required=True)
    schedule.add_argument("--capture-delay-seconds", required=True, type=int)
    advance.add_argument("--wait", action="store_true")
    args = vars(parser.parse_args())
    command = args.pop("command")
    args["job_key"] = strict_json_v1(args.pop("job_key_file").read_bytes())
    if command == "schedule":
        print(bytes_v1(schedule_recorded_market_measurement_v1(**args)).decode())
        return 0
    wait = args.pop("wait")
    while True:
        result = advance_recorded_market_measurement_v1(**args)
        if not wait or result["status"] != "WAITING":
            print(bytes_v1(result).decode())
            return 2 if result["status"] == "EXPIRED" else 0
        delay = (instant_v1(result["capture_at_utc"]) - instant_v1(_utc_now())).total_seconds()
        time.sleep(max(1, min(delay, 60)))


if __name__ == "__main__":
    raise SystemExit(main())
