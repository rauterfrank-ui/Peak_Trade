"""Run a bounded sequence of prospective offline mark-return comparisons."""

import argparse
from datetime import timedelta
from pathlib import Path
import re
import time

from scripts.ops import run_offline_learning_mark_measurement_v1 as measurement
from scripts.ops.capture_offline_learning_mark_window_v1 import (
    _read_manifest,
    read_captured_mark_archive_v1,
)
from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
    build_independent_market_return_target_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
    ContextAdmissionPolicyV1,
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
    MarketIdentityV1,
    bytes_v1,
    digest_v1,
    instant_v1,
    require_v1,
    seal_v1,
    strict_json_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    compose_recorded_market_context_v1,
    measure_recorded_market_horizon_v1,
    recorded_market_target_from_frozen_v1,
)

PLAN_SCHEMA = "recorded_market_successor_plan_v1"
LINK_SCHEMA = "recorded_market_successor_link_v1"


def _freeze_benchmark(*, store_root, context, observation, request, plan):
    inputs = plan["inputs"]
    forecast_at = plan["forecast_at_utc"]
    observed_at = observation["evaluated_at_utc"]
    payload = {"mean_return": observation["measurement"]["log_return"], "std_return": 0.0}
    benchmark = {
        "method": "repeat_last_available_hourly_mark_log_return",
        "trained_model": False,
        "input_observation_digest": observation["exact_content_digest"],
        "capture_manifest_digest": inputs["capture_manifest_digest"],
        "payload": payload,
    }
    model_ref = "offline-previous-hour-return-benchmark:" + digest_v1(benchmark)
    target = build_independent_market_return_target_v1(request)
    native = context["market_context"]
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
        selected_instrument_ref=request["market_identity"]["instrument_ref"],
        provenance={
            "measured_return_target_v1": target,
            "offline_prospective_benchmark": True,
            "previous_measurement_digest": inputs["previous_measurement_digest"],
            "successor_plan_digest": plan["exact_content_digest"],
        },
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
            "training_end": observed_at,
            "available_at": forecast_at,
            "context_package_digest": context["exact_content_digest"],
            "max_context_age_seconds": 0,
            "target_spec_digest": digest_v1(target),
        },
    )


def prepare_recorded_market_successor_v1(
    *, store_root, job_key, next_start_utc, context_max_age_seconds, repository_sha
):
    """Freeze and schedule one successor from the previous job's original outcome archive."""
    start = instant_v1(next_start_utc)
    require_v1(not (start.minute or start.second or start.microsecond), "HOURLY_GRID_REQUIRED")
    next_start_utc = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    require_v1(
        type(context_max_age_seconds) is int and context_max_age_seconds > 0,
        "EXPLICIT_CONTEXT_MAX_AGE_REQUIRED",
    )
    require_v1(re.fullmatch(r"[0-9a-f]{40}", repository_sha) is not None, "REPOSITORY_SHA_REQUIRED")
    previous_key = digest_v1(job_key)
    folder = Path(store_root) / ".intelligence-integration-v1" / previous_key
    require_v1((folder / "calibration_ack.json").is_file(), "COMPLETED_PREDECESSOR_REQUIRED")
    packet = read_independent_market_calibration_v1(store_root=store_root, job_key=job_key)
    frozen = packet["frozen"]
    observation = packet["measurement_inputs"]["market_observation"]
    target = recorded_market_target_from_frozen_v1(frozen)
    require_v1(target["n_bars"] == 2, "TWO_HOUR_BENCHMARK_WINDOW_REQUIRED")
    observed_at = instant_v1(observation["evaluated_at_utc"])
    require_v1(observed_at < start, "SUCCESSOR_MUST_FOLLOW_AVAILABLE_OUTCOME")
    prior_schedule = _read(folder / measurement.PLAN_FILE, measurement.SCHEMA)
    prior_plan = prior_schedule["plan"]
    require_v1(
        prior_plan["job_key"] == dict(job_key)
        and prior_plan["forecast_digest"] == frozen["exact_content_digest"],
        "MEASUREMENT_SCHEDULE_FORECAST_MISMATCH",
    )
    measurement._validate_forecast_clock(frozen, target, prior_schedule["forecast_verified_at_utc"])
    due, expires = measurement._bounds(target, prior_plan["capture_delay_seconds"])
    archive_root = folder / "recorded_outcome_archive"
    manifest = _read_manifest(archive_root)
    require_v1(
        manifest["plan"]
        == {
            "start_utc": target["horizon_start_time_utc"],
            "hours": target["n_bars"],
            "binding_sha256": prior_plan["binding_sha256"],
            "repository_sha": prior_plan["repository_sha"],
        }
        and instant_v1(manifest["available_at_utc"]) == observed_at
        and due <= observed_at <= expires,
        "PREDECESSOR_CAPTURE_SCHEDULE_MISMATCH",
    )
    archive = read_captured_mark_archive_v1(archive_root)
    reproduced = measure_recorded_market_horizon_v1(
        archive=archive,
        request=target["market_request"],
        evaluated_at_utc=observation["evaluated_at_utc"],
    )
    require_v1(reproduced == observation, "PREDECESSOR_CAPTURE_OBSERVATION_MISMATCH")
    request = {**target["market_request"], "horizon_start_time_utc": next_start_utc}
    inputs = {
        "previous_job_key": dict(job_key),
        "previous_measurement_digest": observation["exact_content_digest"],
        "capture_manifest_digest": manifest["exact_content_digest"],
        "request": request,
        "context_max_age_seconds": context_max_age_seconds,
        "repository_sha": repository_sha,
    }
    with _lease(store_root, previous_key) as folder:
        plan_path = folder / "recorded_successor_plan.json"
        link_path = folder / "recorded_successor.json"
        now = measurement._utc_now()
        if not link_path.is_file():
            require_v1(observed_at <= instant_v1(now) < start, "SUCCESSOR_WINDOW_NOT_FUTURE")
        if plan_path.is_file():
            plan = _read(plan_path, PLAN_SCHEMA)
            require_v1(plan["inputs"] == inputs, "SUCCESSOR_PLAN_CONFLICT")
        else:
            require_v1(not link_path.exists(), "SUCCESSOR_PLAN_MISSING")
            plan = seal_v1(
                {
                    "schema_version": PLAN_SCHEMA,
                    "authority": "NONE",
                    "inputs": inputs,
                    "forecast_at_utc": now,
                }
            )
        require_v1(
            observed_at <= instant_v1(plan["forecast_at_utc"]) < start,
            "SUCCESSOR_PLAN_CLOCK_MISMATCH",
        )
        if link_path.is_file():
            link = _read(link_path, LINK_SCHEMA)
            require_v1(
                link["plan_digest"] == plan["exact_content_digest"], "SUCCESSOR_LINK_PLAN_MISMATCH"
            )
            successor = read_frozen_market_forecast_v1(
                store_root=store_root, job_key=link["job_key"]
            )
            require_v1(
                successor["exact_content_digest"] == link["forecast_digest"]
                and successor["job_key"]["attempt_generation"] == plan["exact_content_digest"],
                "SUCCESSOR_LINK_FORECAST_MISMATCH",
            )
        else:
            prior_open = instant_v1(target["horizon_start_time_utc"])
            context = compose_recorded_market_context_v1(
                archive=archive,
                identity=MarketIdentityV1(**request["market_identity"]),
                bar_open_utc=(prior_open + timedelta(hours=1)).isoformat(),
                observed_at=plan["forecast_at_utc"],
                policy=ContextAdmissionPolicyV1(
                    "prospective-offline-benchmark",
                    {"price_o4": context_max_age_seconds},
                    ("price_state_ref",),
                ),
            )
            require_v1(context["context_status"] == "VALID", "VALID_CONTEXT_REQUIRED")
            _append(plan_path, plan)
            successor = _freeze_benchmark(
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
                        "job_key": successor["job_key"],
                        "forecast_digest": successor["exact_content_digest"],
                    }
                ),
            )
        return measurement.schedule_recorded_market_measurement_v1(
            store_root=store_root,
            job_key=successor["job_key"],
            binding_path=archive.binding_path,
            binding_sha256=archive.binding_sha256,
            repository_sha=repository_sha,
            capture_delay_seconds=prior_plan["capture_delay_seconds"],
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-root", required=True, type=Path)
    parser.add_argument("--job-key-file", required=True, type=Path)
    parser.add_argument("--next-start-utc", required=True, action="append")
    parser.add_argument("--context-max-age-seconds", required=True, type=int)
    parser.add_argument("--repository-sha", required=True)
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args()
    starts = [instant_v1(value) for value in args.next_start_utc]
    require_v1(
        all(not (start.minute or start.second or start.microsecond) for start in starts)
        and all(later - earlier > timedelta(hours=2) for earlier, later in zip(starts, starts[1:])),
        "HOURLY_ORDERED_NON_OVERLAPPING_WINDOWS_REQUIRED",
    )
    job_key = strict_json_v1(args.job_key_file.read_bytes())
    for next_start in [*args.next_start_utc, None]:
        last_status = None
        while True:
            result = measurement.advance_recorded_market_measurement_v1(
                store_root=args.store_root, job_key=job_key
            )
            status = result["status"]
            if status != last_status:
                print(bytes_v1({"job_key": job_key, **result}).decode(), flush=True)
                last_status = status
            if status != "WAITING" or not args.wait:
                break
            delay = instant_v1(result["capture_at_utc"]) - instant_v1(measurement._utc_now())
            time.sleep(max(1, min(delay.total_seconds(), 60)))
        if status != "COMPLETED" or next_start is None:
            return 2 if status == "EXPIRED" else 0
        schedule = prepare_recorded_market_successor_v1(
            store_root=args.store_root,
            job_key=job_key,
            next_start_utc=next_start,
            context_max_age_seconds=args.context_max_age_seconds,
            repository_sha=args.repository_sha,
        )
        job_key = schedule["plan"]["job_key"]


if __name__ == "__main__":
    raise SystemExit(main())
