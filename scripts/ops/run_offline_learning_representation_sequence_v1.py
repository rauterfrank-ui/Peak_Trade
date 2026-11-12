"""Collect a finite prospective B0/B1 cohort and compare its original holdout."""

import argparse
from datetime import timedelta
from pathlib import Path
import re
import time

from scripts.ops import capture_offline_learning_representation_context_v1 as representation
from scripts.ops import run_offline_learning_mark_measurement_v1 as measurement
from scripts.ops.capture_offline_learning_mark_window_v1 import read_captured_mark_archive_v1
from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
    build_independent_market_return_target_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    _append,
    _lease,
    _read,
    freeze_existing_market_forecast_v1,
    read_frozen_market_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.independent_market_forecast_measurement_v1 import (
    read_independent_market_calibration_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    digest_v1,
    finite_v1,
    instant_v1,
    require_v1,
    seal_v1,
    strict_json_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    recorded_market_target_from_frozen_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.phase_22_paired_market_research_v1 import (
    compare_paired_market_b1_to_b0_v1,
)

PLAN_SCHEMA = "recorded_representation_successor_plan_v1"
LINK_SCHEMA = "recorded_representation_successor_link_v1"
COHORT_SCHEMA = "recorded_representation_cohort_plan_v1"


def _without_network(**kwargs):
    raise ValueError("ORIGINAL_REPRESENTATION_OUTCOME_ARCHIVE_REQUIRED")


def _freeze_benchmark(*, store_root, context, observation, request, plan):
    native = context["market_context"]
    target = build_independent_market_return_target_v1(request)
    forecast_at = plan["forecast_at_utc"]
    payload = {"mean_return": observation["measurement"]["log_return"], "std_return": 0.0}
    benchmark = {
        "method": "repeat_last_available_hourly_mark_log_return",
        "trained_model": False,
        "input_observation_digest": observation["exact_content_digest"],
        "representation_context_digest": context["exact_content_digest"],
        "payload": payload,
    }
    model_ref = "offline-previous-hour-return-benchmark:" + digest_v1(benchmark)
    forecast = mint_forecast_evidence_v1(
        information_set_ref=native["information_set_ref"],
        forecast_created_at_utc=forecast_at,
        outcome_horizon_end_utc=target["return_end_close_time_utc"],
        n_bars=target["n_bars"],
        bar_spec_ref=target["bar_spec_ref"],
        forecast_kind="RETURN_DISTRIBUTION_SUMMARY",
        probabilistic_payload=payload,
        market_state_refs=[native["context_id"]],
        forecast_model_ref=model_ref,
        support_disposition="SUFFICIENT_EVIDENCE",
        selected_instrument_ref=context["identity"]["instrument_ref"],
        provenance={"measured_return_target_v1": target, "offline_prospective_benchmark": True},
    )
    return freeze_existing_market_forecast_v1(
        store_root=store_root,
        context_package=context,
        forecast_evidence=forecast,
        original_probabilistic_payload=bytes_v1(payload),
        model_artifact_bytes=bytes_v1(benchmark),
        attempt_generation=plan["exact_content_digest"],
        provider_admission={
            "provider_ref": "explicit-previous-hour-offline-benchmark",
            "model_ref": model_ref,
            "feature_schema_ref": "previous-hourly-mark-close-log-return",
            "training_dataset_ref": observation["exact_content_digest"],
            "validation_ref": "comparison-baseline-only",
            "admitted_by_ref": "explicit-local-offline-prospective-case",
            "model_artifact_sha256": digest_v1(benchmark),
            "training_end": observation["evaluated_at_utc"],
            "available_at": context["as_of"],
            "context_package_digest": context["exact_content_digest"],
            "max_context_age_seconds": plan["inputs"]["forecast_context_max_age_seconds"],
            "target_spec_digest": digest_v1(target),
        },
    )


def prepare_recorded_representation_successor_v1(
    *,
    store_root,
    job_key,
    next_start_utc,
    repository_sha,
    trade_count,
    max_age_seconds_by_role,
    forecast_context_max_age_seconds,
    fetch=representation._public_get,
):
    """Acquire the next context only after reading back the preceding original outcome."""
    start = instant_v1(next_start_utc)
    require_v1(not (start.minute or start.second or start.microsecond), "HOURLY_GRID_REQUIRED")
    require_v1(re.fullmatch(r"[0-9a-f]{40}", repository_sha) is not None, "REPOSITORY_SHA_REQUIRED")
    require_v1(
        type(forecast_context_max_age_seconds) is int and forecast_context_max_age_seconds > 0,
        "EXPLICIT_FORECAST_CONTEXT_MAX_AGE_REQUIRED",
    )
    locator = {"store_root": store_root, "job_key": job_key}
    key = digest_v1(job_key)
    predecessor = Path(store_root) / ".intelligence-integration-v1" / key
    require_v1((predecessor / "calibration_ack.json").is_file(), "COMPLETED_PREDECESSOR_REQUIRED")
    packet = read_independent_market_calibration_v1(**locator)
    original = measurement.advance_recorded_market_measurement_v1(
        **locator, capture_window=_without_network
    )
    require_v1(
        original["status"] == "COMPLETED"
        and original["calibration_ack"] == packet["calibration_ack"],
        "REPRESENTATION_PREDECESSOR_READBACK_MISMATCH",
    )
    observation = packet["measurement_inputs"]["market_observation"]
    require_v1(
        instant_v1(observation["evaluated_at_utc"]) < start,
        "SUCCESSOR_MUST_FOLLOW_AVAILABLE_OUTCOME",
    )
    previous_target = recorded_market_target_from_frozen_v1(packet["frozen"])
    require_v1(previous_target["n_bars"] == 2, "TWO_HOUR_BENCHMARK_WINDOW_REQUIRED")
    previous_schedule = _read(predecessor / measurement.PLAN_FILE, measurement.SCHEMA)
    mark_root = predecessor / "recorded_outcome_archive"
    mark_archive = read_captured_mark_archive_v1(mark_root)
    request = {
        **previous_target["market_request"],
        "horizon_start_time_utc": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with _lease(store_root, key) as folder:
        context_root = folder / "recorded_representation_successor_context"
        link_path = folder / "recorded_representation_successor.json"
        plan_path = folder / "recorded_representation_successor_plan.json"
        now = instant_v1(measurement._utc_now())
        if not link_path.is_file():
            require_v1(now < start, "REPRESENTATION_SUCCESSOR_WINDOW_NOT_FUTURE")
        if context_root.is_dir():
            manifest = representation._read_capture(context_root)
            ohlcv_end = representation._utc_from_ms(manifest["plan"]["ohlcv_end_ms"])
        else:
            # Avoid the most recently closed minute, which may still be provisional.
            ohlcv_end = (now.replace(second=0, microsecond=0) - timedelta(minutes=1)).isoformat()
        context = representation.capture_representation_context_v1(
            output=context_root,
            mark_archive=mark_root,
            ohlcv_end_utc=ohlcv_end,
            trade_count=trade_count,
            max_age_seconds_by_role=max_age_seconds_by_role,
            fetch=fetch,
        )
        require_v1(
            context["identity"] == request["market_identity"], "REPRESENTATION_GENERATION_CHANGED"
        )
        inputs = {
            "previous_job_key": job_key,
            "previous_measurement_digest": observation["exact_content_digest"],
            "context_digest": context["exact_content_digest"],
            "request": request,
            "forecast_context_max_age_seconds": forecast_context_max_age_seconds,
            "repository_sha": repository_sha,
        }
        if plan_path.is_file():
            plan = _read(plan_path, PLAN_SCHEMA)
            require_v1(plan["inputs"] == inputs, "REPRESENTATION_SUCCESSOR_PLAN_CONFLICT")
        else:
            require_v1(not link_path.exists(), "REPRESENTATION_SUCCESSOR_PLAN_REQUIRED")
            forecast_at = measurement._utc_now()
            require_v1(
                instant_v1(context["as_of"]) <= instant_v1(forecast_at) < start,
                "REPRESENTATION_SUCCESSOR_WINDOW_NOT_FUTURE",
            )
            plan = seal_v1(
                {
                    "schema_version": PLAN_SCHEMA,
                    "authority": "NONE",
                    "inputs": inputs,
                    "forecast_at_utc": forecast_at,
                }
            )
            _append(plan_path, plan)
        require_v1(
            instant_v1(observation["evaluated_at_utc"])
            <= instant_v1(context["as_of"])
            <= instant_v1(plan["forecast_at_utc"])
            < start,
            "REPRESENTATION_SUCCESSOR_PLAN_CLOCK_MISMATCH",
        )
        if link_path.is_file():
            link = _read(link_path, LINK_SCHEMA)
            frozen = read_frozen_market_forecast_v1(store_root=store_root, job_key=link["job_key"])
            require_v1(
                link["plan_digest"] == plan["exact_content_digest"]
                and link["forecast_digest"] == frozen["exact_content_digest"]
                and frozen["job_key"]["attempt_generation"] == plan["exact_content_digest"],
                "REPRESENTATION_SUCCESSOR_READBACK_MISMATCH",
            )
        else:
            frozen = _freeze_benchmark(
                store_root=store_root,
                context=context,
                observation=observation,
                request=request,
                plan=plan,
            )
            _append(
                link_path,
                seal_v1(
                    {
                        "schema_version": LINK_SCHEMA,
                        "authority": "NONE",
                        "plan_digest": plan["exact_content_digest"],
                        "job_key": frozen["job_key"],
                        "forecast_digest": frozen["exact_content_digest"],
                    }
                ),
            )
        return measurement.schedule_recorded_market_measurement_v1(
            store_root=store_root,
            job_key=frozen["job_key"],
            binding_path=mark_archive.binding_path,
            binding_sha256=mark_archive.binding_sha256,
            repository_sha=repository_sha,
            capture_delay_seconds=previous_schedule["plan"]["capture_delay_seconds"],
        )


def run_representation_cohort_v1(
    *,
    store_root,
    seed_job_key,
    seed_context_root,
    next_starts_utc,
    fit_window_count,
    validation_fraction,
    repository_sha,
    forecast_context_max_age_seconds,
    wait,
):
    """Resume the declared cohort, preserving its split and the original case locators."""
    locator = {"store_root": store_root, "job_key": seed_job_key}
    seed = read_frozen_market_forecast_v1(**locator)
    seed_target = recorded_market_target_from_frozen_v1(seed)
    first_start = instant_v1(seed_target["horizon_start_time_utc"])
    starts = [first_start, *(instant_v1(value) for value in next_starts_utc)]
    validation_fraction = finite_v1(validation_fraction, "VALIDATION_FRACTION")
    require_v1(0 < validation_fraction < 1, "VALIDATION_FRACTION_DOMAIN")
    fit_training_count = round(fit_window_count * (1.0 - validation_fraction))
    require_v1(
        seed_target["n_bars"] == 2
        and 5 <= fit_window_count <= len(starts) - 2
        and 4 <= fit_training_count < fit_window_count
        and all(not (start.minute or start.second or start.microsecond) for start in starts)
        and all(later - earlier > timedelta(hours=2) for earlier, later in zip(starts, starts[1:])),
        "EXPLICIT_REPRESENTATION_SPLIT_AND_WINDOWS_REQUIRED",
    )
    require_v1(re.fullmatch(r"[0-9a-f]{40}", repository_sha) is not None, "REPOSITORY_SHA_REQUIRED")
    require_v1(
        type(forecast_context_max_age_seconds) is int and forecast_context_max_age_seconds > 0,
        "EXPLICIT_FORECAST_CONTEXT_MAX_AGE_REQUIRED",
    )
    seed_context_root = Path(seed_context_root)
    seed_context = representation.read_recorded_representation_context_v1(
        seed_context_root, cutoff_utc=measurement._utc_now()
    )
    require_v1(seed_context == seed["context_package"], "REPRESENTATION_SEED_CONTEXT_MISMATCH")
    source_plan = representation._read_capture(seed_context_root)["plan"]
    campaign_key = digest_v1({"schema_version": COHORT_SCHEMA, "seed_job_key": seed_job_key})
    cohort = seal_v1(
        {
            "schema_version": COHORT_SCHEMA,
            "authority": "NONE",
            "seed_job_key": seed_job_key,
            "seed_context_digest": seed_context["exact_content_digest"],
            "starts_utc": [start.isoformat() for start in starts],
            "fit_window_count": fit_window_count,
            "validation_fraction": validation_fraction,
            "repository_sha": repository_sha,
            "forecast_context_max_age_seconds": forecast_context_max_age_seconds,
        }
    )
    with _lease(store_root, campaign_key) as folder:
        _append(folder / "representation_cohort_plan.json", cohort)

    jobs, receipt_times = [], []
    job_key = seed_job_key
    for next_start in [*starts[1:], None]:
        last_status = None
        while True:
            result = measurement.advance_recorded_market_measurement_v1(
                store_root=store_root, job_key=job_key
            )
            status = result["status"]
            if status != last_status:
                print(
                    bytes_v1({"window": len(jobs) + 1, "job_key": job_key, **result}).decode(),
                    flush=True,
                )
                last_status = status
            if status != "WAITING" or not wait:
                break
            delay = instant_v1(result["capture_at_utc"]) - instant_v1(measurement._utc_now())
            time.sleep(max(1, min(delay.total_seconds(), 60)))
        if status != "COMPLETED":
            return 2 if status == "EXPIRED" else 0
        jobs.append({"store_root": store_root, "job_key": job_key})
        receipt_times.append(result["captured_at_utc"])
        if next_start is not None:
            schedule = prepare_recorded_representation_successor_v1(
                store_root=store_root,
                job_key=job_key,
                next_start_utc=next_start.isoformat(),
                repository_sha=repository_sha,
                trade_count=source_plan["trade_count"],
                max_age_seconds_by_role=source_plan["max_age_seconds_by_role"],
                forecast_context_max_age_seconds=forecast_context_max_age_seconds,
            )
            job_key = schedule["plan"]["job_key"]

    result = compare_paired_market_b1_to_b0_v1(
        fit_jobs=jobs[:fit_window_count],
        holdout_jobs=jobs[fit_window_count:],
        fit_cutoff_utc=receipt_times[fit_window_count - 1],
        evaluated_at_utc=receipt_times[-1],
        validation_fraction=validation_fraction,
    )
    with _lease(store_root, campaign_key) as folder:
        _append(folder / "paired_representation_comparison.json", result)
    print(bytes_v1(result).decode(), flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-root", required=True, type=Path)
    parser.add_argument("--seed-job-key-file", required=True, type=Path)
    parser.add_argument("--seed-context-root", required=True, type=Path)
    parser.add_argument("--next-start-utc", dest="next_starts_utc", required=True, action="append")
    parser.add_argument("--fit-window-count", required=True, type=int)
    parser.add_argument("--validation-fraction", required=True, type=float)
    parser.add_argument("--repository-sha", required=True)
    parser.add_argument("--forecast-context-max-age-seconds", required=True, type=int)
    parser.add_argument("--wait", action="store_true")
    args = vars(parser.parse_args())
    args["seed_job_key"] = strict_json_v1(args.pop("seed_job_key_file").read_bytes())
    return run_representation_cohort_v1(**args)


if __name__ == "__main__":
    raise SystemExit(main())
