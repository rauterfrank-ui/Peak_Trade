"""Read a completed offline representation cohort and persist its Meta handoff."""

import argparse
from pathlib import Path

from scripts.ops import run_offline_learning_mark_measurement_v1 as measurement
from scripts.ops import run_offline_learning_representation_sequence_v1 as cohort
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    _append,
    _lease,
    _read,
    read_frozen_market_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    assert_offline_v1,
    bytes_v1,
    digest_v1,
    instant_v1,
    require_v1,
    seal_v1,
    strict_json_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    recorded_market_target_from_frozen_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.phase_22_paired_market_research_v1 import (
    SCHEMA as COMPARISON_SCHEMA,
)
from src.meta.learning_loop.paired_market_representation_meta_v1 import (
    route_paired_market_representation_v1,
)

SCHEMA = "recorded_representation_cohort_meta_receipt_v1"


def _declared_cohort_jobs(store_root, plan):
    job_key = plan["seed_job_key"]
    context_digest = plan["seed_context_digest"]
    forecast_digest = None
    locators, receipts = [], []
    starts = plan["starts_utc"]
    for index, start in enumerate(starts):
        locator = {"store_root": store_root, "job_key": job_key}
        folder = Path(store_root) / ".intelligence-integration-v1" / digest_v1(job_key)
        frozen = read_frozen_market_forecast_v1(**locator)
        target = recorded_market_target_from_frozen_v1(frozen)
        require_v1(
            instant_v1(target["horizon_start_time_utc"]) == instant_v1(start)
            and frozen["context_package"]["exact_content_digest"] == context_digest
            and (forecast_digest is None or frozen["exact_content_digest"] == forecast_digest),
            "META_COHORT_ORIGINAL_FORECAST_MISMATCH",
        )
        require_v1((folder / "calibration_ack.json").is_file(), "META_COHORT_MEASUREMENT_REQUIRED")
        result = measurement.advance_recorded_market_measurement_v1(
            **locator, capture_window=cohort._without_network
        )
        require_v1(result["status"] == "COMPLETED", "META_COHORT_MEASUREMENT_REQUIRED")
        locators.append(locator)
        receipts.append(result["captured_at_utc"])
        if index < len(starts) - 1:
            successor = _read(
                folder / "recorded_representation_successor_plan.json", cohort.PLAN_SCHEMA
            )
            link = _read(folder / "recorded_representation_successor.json", cohort.LINK_SCHEMA)
            inputs = successor["inputs"]
            require_v1(
                inputs["previous_job_key"] == job_key
                and inputs["previous_measurement_digest"]
                == result["calibration_ack"]["market_observation_digest"]
                and instant_v1(inputs["request"]["horizon_start_time_utc"])
                == instant_v1(starts[index + 1])
                and link["plan_digest"] == successor["exact_content_digest"]
                and link["job_key"]["attempt_generation"] == successor["exact_content_digest"],
                "META_COHORT_ORIGINAL_SUCCESSOR_MISMATCH",
            )
            job_key = link["job_key"]
            context_digest = inputs["context_digest"]
            forecast_digest = link["forecast_digest"]
    return locators, receipts


def route_recorded_representation_cohort_v1(*, store_root, seed_job_key):
    """Only the immutable cohort's exact stored comparison enters the Meta route."""
    assert_offline_v1()
    key = digest_v1({"schema_version": cohort.COHORT_SCHEMA, "seed_job_key": seed_job_key})
    folder = Path(store_root) / ".intelligence-integration-v1" / key
    plan = _read(folder / "representation_cohort_plan.json", cohort.COHORT_SCHEMA)
    require_v1(plan["seed_job_key"] == seed_job_key, "META_COHORT_SEED_MISMATCH")
    path = folder / "paired_representation_comparison.json"
    if not path.is_file():
        return {
            "status": "WAITING_FOR_COMPARISON",
            "cohort_plan_digest": plan["exact_content_digest"],
        }
    stored = _read(path, COMPARISON_SCHEMA)
    fit_count = plan["fit_window_count"]
    require_v1(
        type(fit_count) is int and 5 <= fit_count <= len(plan["starts_utc"]) - 2,
        "META_COHORT_SPLIT_MISMATCH",
    )
    jobs, receipts = _declared_cohort_jobs(store_root, plan)
    handoff = route_paired_market_representation_v1(
        stored_comparison=stored,
        fit_jobs=jobs[:fit_count],
        holdout_jobs=jobs[fit_count:],
        fit_cutoff_utc=receipts[fit_count - 1],
        evaluated_at_utc=receipts[-1],
        validation_fraction=plan["validation_fraction"],
    )
    receipt = seal_v1(
        {
            "schema_version": SCHEMA,
            "authority": "NONE",
            "status": handoff["status"],
            "cohort_plan_digest": plan["exact_content_digest"],
            "comparison_digest": stored["exact_content_digest"],
            "handoff": handoff,
        }
    )
    with _lease(store_root, key) as locked:
        output = locked / "paired_representation_meta.json"
        _append(output, receipt)
        return _read(output, SCHEMA)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-root", required=True, type=Path)
    parser.add_argument("--seed-job-key-file", required=True, type=Path)
    args = parser.parse_args()
    receipt = route_recorded_representation_cohort_v1(
        store_root=args.store_root,
        seed_job_key=strict_json_v1(args.seed_job_key_file.read_bytes()),
    )
    print(bytes_v1(receipt).decode())


if __name__ == "__main__":
    main()
