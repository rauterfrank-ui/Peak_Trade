"""Fit from a declared prospective mark cohort and measure its next OLS forecast."""

import argparse
from datetime import timedelta
from pathlib import Path
import re
import time

from scripts.ops import run_offline_learning_mark_measurement_v1 as measurement
from scripts.ops import run_offline_learning_mark_sequence_v1 as sequence
from scripts.ops.capture_offline_learning_mark_window_v1 import (
    _read_manifest,
    read_captured_mark_archive_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
    ContextAdmissionPolicyV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    _append,
    _lease,
    _read,
    read_frozen_market_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.independent_market_forecast_measurement_v1 import (
    read_independent_market_calibration_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    digest_v1,
    instant_v1,
    require_v1,
    seal_v1,
    strict_json_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_ols_next_forecast_v1 import (
    read_market_model_forecast_v1,
    read_market_ols_model_v1,
    train_market_ols_model_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    forecast_from_recorded_market_context_v1,
    recorded_market_target_from_frozen_v1,
)

FIT_SCHEMA = "recorded_market_ols_follow_up_fit_v1"
PLAN_SCHEMA = "recorded_market_ols_follow_up_plan_v1"
LINK_SCHEMA = "recorded_market_ols_follow_up_link_v1"


def _job_folder(store_root, job_key):
    return Path(store_root) / ".intelligence-integration-v1" / digest_v1(job_key)


def _no_capture(**kwargs):
    raise ValueError("ORIGINAL_COHORT_ARCHIVE_REQUIRED")


def _read_cohort(store_root, job_key, starts):
    samples = []
    successor_digest = None
    for index, start in enumerate(starts):
        locator = {"store_root": store_root, "job_key": job_key}
        frozen = read_frozen_market_forecast_v1(**locator)
        target = recorded_market_target_from_frozen_v1(frozen)
        require_v1(
            instant_v1(target["horizon_start_time_utc"]) == start and target["n_bars"] == 2,
            "COHORT_ORIGINAL_TARGET_MISMATCH",
        )
        if successor_digest is not None:
            require_v1(
                frozen["exact_content_digest"] == successor_digest,
                "COHORT_SUCCESSOR_FORECAST_MISMATCH",
            )
        folder = _job_folder(store_root, job_key)
        if not (folder / "calibration_ack.json").is_file():
            return {"status": "WAITING_FOR_COHORT", "completed_samples": index}
        packet = read_independent_market_calibration_v1(**locator)
        verified = measurement.advance_recorded_market_measurement_v1(
            **locator, capture_window=_no_capture
        )
        require_v1(
            verified["status"] == "COMPLETED"
            and verified["calibration_ack"] == packet["calibration_ack"],
            "COHORT_SCHEDULED_MEASUREMENT_MISMATCH",
        )
        archive_root = folder / "recorded_outcome_archive"
        observation = packet["measurement_inputs"]["market_observation"]
        samples.append(
            {
                "job_key": job_key,
                "observation_digest": observation["exact_content_digest"],
                "label_available_at": observation["evaluated_at_utc"],
            }
        )
        if index == len(starts) - 1:
            schedule = _read(folder / measurement.PLAN_FILE, measurement.SCHEMA)
            return {
                "samples": samples,
                "last_archive": read_captured_mark_archive_v1(archive_root),
                "last_target": target,
                "capture_delay_seconds": schedule["plan"]["capture_delay_seconds"],
            }
        link_path = folder / "recorded_successor.json"
        if not link_path.is_file():
            return {"status": "WAITING_FOR_COHORT", "completed_samples": index + 1}
        link = _read(link_path, sequence.LINK_SCHEMA)
        plan = _read(folder / "recorded_successor_plan.json", sequence.PLAN_SCHEMA)
        inputs = plan["inputs"]
        require_v1(
            link["plan_digest"] == plan["exact_content_digest"]
            and inputs["previous_job_key"] == job_key
            and inputs["previous_measurement_digest"] == observation["exact_content_digest"]
            and inputs["capture_manifest_digest"]
            == _read_manifest(archive_root)["exact_content_digest"]
            and instant_v1(inputs["request"]["horizon_start_time_utc"]) == starts[index + 1]
            and link["job_key"]["attempt_generation"] == plan["exact_content_digest"],
            "COHORT_SUCCESSOR_PLAN_MISMATCH",
        )
        job_key = link["job_key"]
        successor_digest = link["forecast_digest"]


def prepare_recorded_market_ols_follow_up_v1(
    *,
    store_root,
    model_store_root,
    seed_job_key,
    sample_starts_utc,
    model_available_at_utc,
    next_start_utc,
    context_max_age_seconds,
    repository_sha,
    training,
):
    """Schedule one genuinely future forecast after the named cohort has completed."""
    starts = [instant_v1(value) for value in sample_starts_utc]
    next_start = instant_v1(next_start_utc)
    release = instant_v1(model_available_at_utc)
    require_v1(
        len(starts) >= 4
        and all(
            not (stamp.minute or stamp.second or stamp.microsecond)
            for stamp in [*starts, next_start]
        )
        and all(later - earlier > timedelta(hours=2) for earlier, later in zip(starts, starts[1:]))
        and starts[-1] + timedelta(hours=2) < release < next_start,
        "EXPLICIT_CAUSAL_COHORT_AND_RELEASE_REQUIRED",
    )
    require_v1(
        type(context_max_age_seconds) is int and context_max_age_seconds > 0,
        "EXPLICIT_CONTEXT_MAX_AGE_REQUIRED",
    )
    require_v1(re.fullmatch(r"[0-9a-f]{40}", repository_sha) is not None, "REPOSITORY_SHA_REQUIRED")
    require_v1(
        set(training) == {"features", "policy", "parent_model_ref"},
        "EXPLICIT_OLS_TRAINING_REQUIRED",
    )
    cohort = _read_cohort(store_root, seed_job_key, starts)
    if "status" in cohort:
        require_v1(
            instant_v1(measurement._utc_now()) < release, "COHORT_NOT_READY_BY_MODEL_RELEASE"
        )
        return cohort

    samples, archive = cohort["samples"], cohort["last_archive"]
    last_receipt = samples[-1]["label_available_at"]
    release_at = release.isoformat().replace("+00:00", "Z")
    require_v1(instant_v1(last_receipt) < release, "COHORT_NOT_READY_BY_MODEL_RELEASE")
    request = {
        **cohort["last_target"]["market_request"],
        "horizon_start_time_utc": next_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    inputs = {
        "samples": samples,
        "training": training,
        "model_available_at_utc": release_at,
        "model_store_root": str(Path(model_store_root).resolve()),
        "next_request": request,
        "context_max_age_seconds": context_max_age_seconds,
        "repository_sha": repository_sha,
    }
    key = digest_v1({"schema_version": FIT_SCHEMA, "seed_job_key": seed_job_key})
    with _lease(store_root, key) as folder:
        fit_path = folder / "recorded_ols_fit.json"
        if fit_path.is_file():
            fit = _read(fit_path, FIT_SCHEMA)
            require_v1(fit["inputs"] == inputs, "OLS_FOLLOW_UP_INPUT_CONFLICT")
        else:
            require_v1(instant_v1(measurement._utc_now()) < release, "MODEL_RELEASE_ALREADY_PASSED")
            model = train_market_ols_model_v1(
                model_store_root=model_store_root,
                evidence_jobs=[
                    {"store_root": store_root, "job_key": sample["job_key"]} for sample in samples
                ],
                trained_as_of=last_receipt,
                available_at=release_at,
                **training,
            )
            verified_at = measurement._utc_now()
            require_v1(instant_v1(verified_at) <= release, "MODEL_NOT_VERIFIED_BY_RELEASE")
            fit = seal_v1(
                {
                    "schema_version": FIT_SCHEMA,
                    "authority": "NONE",
                    "inputs": inputs,
                    "model_ref": model["model_ref"],
                    "model_digest": model["exact_content_digest"],
                    "verified_at_utc": verified_at,
                }
            )
            _append(fit_path, fit)
        model = read_market_ols_model_v1(
            model_store_root=model_store_root, model_ref=fit["model_ref"]
        )
        require_v1(
            model["exact_content_digest"] == fit["model_digest"]
            and instant_v1(last_receipt) <= instant_v1(fit["verified_at_utc"]) <= release,
            "OLS_FOLLOW_UP_MODEL_READBACK_MISMATCH",
        )
        now = measurement._utc_now()
        if instant_v1(now) < release:
            return {
                "status": "WAITING_FOR_MODEL_RELEASE",
                "model_ref": model["model_ref"],
                "release_at_utc": release_at,
            }

        plan_path = folder / "recorded_ols_plan.json"
        link_path = folder / "recorded_ols_forecast.json"
        if not link_path.is_file():
            require_v1(instant_v1(now) < next_start, "OLS_FOLLOW_UP_WINDOW_NOT_FUTURE")
        if plan_path.is_file():
            plan = _read(plan_path, PLAN_SCHEMA)
        else:
            require_v1(not link_path.exists(), "OLS_FOLLOW_UP_PLAN_REQUIRED")
            plan = seal_v1(
                {
                    "schema_version": PLAN_SCHEMA,
                    "authority": "NONE",
                    "fit_digest": fit["exact_content_digest"],
                    "forecast_at_utc": now,
                }
            )
            _append(plan_path, plan)
        forecast_at = plan["forecast_at_utc"]
        require_v1(
            plan["fit_digest"] == fit["exact_content_digest"]
            and release <= instant_v1(forecast_at) <= instant_v1(now)
            and instant_v1(forecast_at) < next_start,
            "OLS_FOLLOW_UP_PLAN_CLOCK_MISMATCH",
        )
        if link_path.is_file():
            link = _read(link_path, LINK_SCHEMA)
            forecast = read_market_model_forecast_v1(
                model_store_root=model_store_root, store_root=store_root, job_key=link["job_key"]
            )
            require_v1(
                link["plan_digest"] == plan["exact_content_digest"]
                and link["forecast_digest"] == forecast["frozen"]["exact_content_digest"]
                and forecast["provider"]["computation"]["requested_attempt_generation"]
                == plan["exact_content_digest"],
                "OLS_FOLLOW_UP_FORECAST_READBACK_MISMATCH",
            )
        else:
            last_bar_open = instant_v1(
                cohort["last_target"]["return_end_close_time_utc"]
            ) - timedelta(hours=1)
            forecast = forecast_from_recorded_market_context_v1(
                archive=archive,
                bar_open_utc=last_bar_open.isoformat(),
                observed_at=forecast_at,
                context_policy=ContextAdmissionPolicyV1(
                    "prospective-offline-ols-follow-up",
                    {"price_o4": context_max_age_seconds},
                    ("price_state_ref",),
                ),
                model_store_root=model_store_root,
                model_ref=model["model_ref"],
                store_root=store_root,
                market_request=request,
                forecast_created_at=forecast_at,
                attempt_generation=plan["exact_content_digest"],
            )
            _append(
                link_path,
                seal_v1(
                    {
                        "schema_version": LINK_SCHEMA,
                        "authority": "NONE",
                        "plan_digest": plan["exact_content_digest"],
                        "job_key": forecast["frozen"]["job_key"],
                        "forecast_digest": forecast["frozen"]["exact_content_digest"],
                    }
                ),
            )
        schedule = measurement.schedule_recorded_market_measurement_v1(
            store_root=store_root,
            job_key=forecast["frozen"]["job_key"],
            binding_path=archive.binding_path,
            binding_sha256=archive.binding_sha256,
            repository_sha=repository_sha,
            capture_delay_seconds=cohort["capture_delay_seconds"],
        )
        return {
            "status": "FORECAST_SCHEDULED",
            "job_key": schedule["plan"]["job_key"],
            "schedule": schedule,
            "fit": fit,
            "validation": model["validation"],
            "provider": forecast["provider"],
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-root", required=True, type=Path)
    parser.add_argument("--model-store-root", required=True, type=Path)
    parser.add_argument("--seed-job-key-file", required=True, type=Path)
    parser.add_argument(
        "--sample-start-utc", dest="sample_starts_utc", required=True, action="append"
    )
    parser.add_argument("--model-available-at-utc", required=True)
    parser.add_argument("--next-start-utc", required=True)
    parser.add_argument("--context-max-age-seconds", required=True, type=int)
    parser.add_argument("--repository-sha", required=True)
    parser.add_argument("--training-file", required=True, type=Path)
    parser.add_argument("--wait", action="store_true")
    args = vars(parser.parse_args())
    wait = args.pop("wait")
    args["seed_job_key"] = strict_json_v1(args.pop("seed_job_key_file").read_bytes())
    args["training"] = strict_json_v1(args.pop("training_file").read_bytes())
    previous = None
    while True:
        result = prepare_recorded_market_ols_follow_up_v1(**args)
        if result != previous:
            print(bytes_v1(result).decode(), flush=True)
            previous = result
        if not wait:
            return 0
        if result["status"] == "FORECAST_SCHEDULED":
            break
        time.sleep(30)

    previous = None
    while True:
        measurement_result = measurement.advance_recorded_market_measurement_v1(
            store_root=args["store_root"], job_key=result["job_key"]
        )
        if measurement_result != previous:
            print(bytes_v1(measurement_result).decode(), flush=True)
            previous = measurement_result
        if measurement_result["status"] != "WAITING":
            return 2 if measurement_result["status"] == "EXPIRED" else 0
        time.sleep(30)


if __name__ == "__main__":
    raise SystemExit(main())
