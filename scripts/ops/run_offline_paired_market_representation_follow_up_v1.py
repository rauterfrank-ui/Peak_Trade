"""Run the stored B1 representation question on a new prospective cohort."""

import argparse
from datetime import timedelta
from pathlib import Path
import re

from scripts.ops import capture_offline_learning_representation_context_v1 as representation
from scripts.ops import route_offline_paired_market_representation_meta_v1 as meta
from scripts.ops import run_offline_learning_mark_measurement_v1 as measurement
from scripts.ops import run_offline_learning_representation_sequence_v1 as cohort
from src.experiments.canonical_learning_representation_research_adaptation_plan_v1 import (
    RepresentationResearchPurpose,
    validate_learning_representation_research_adaptation_plan_v1,
)
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
from src.meta.learning_loop.paired_market_representation_meta_v1 import MEASURED_PATTERN

PLAN_SCHEMA = "recorded_paired_market_representation_follow_up_plan_v1"
RECEIPT_SCHEMA = "recorded_paired_market_representation_follow_up_receipt_v1"


def _campaign_key(seed_job_key):
    return digest_v1({"schema_version": cohort.COHORT_SCHEMA, "seed_job_key": seed_job_key})


def read_representation_research_parent_v1(*, store_root, seed_job_key):
    """Check that an already durable Meta decision can drive this research question."""
    assert_offline_v1()
    folder = Path(store_root) / ".intelligence-integration-v1" / _campaign_key(seed_job_key)
    plan = _read(folder / "representation_cohort_plan.json", cohort.COHORT_SCHEMA)
    require_v1(plan["seed_job_key"] == seed_job_key, "RESEARCH_PARENT_SEED_MISMATCH")
    if not (folder / "paired_representation_comparison.json").is_file():
        return {"status": "WAITING_FOR_PARENT_COMPARISON"}
    path = folder / "paired_representation_meta.json"
    if not path.is_file():
        return {"status": "WAITING_FOR_PARENT_META_HANDOFF"}
    stored = _read(path, meta.SCHEMA)
    require_v1(
        stored
        == meta.route_recorded_representation_cohort_v1(
            store_root=store_root, seed_job_key=seed_job_key
        ),
        "RESEARCH_PARENT_META_READBACK_MISMATCH",
    )
    if stored["status"] == "UNRESOLVED_REPRESENTATION_QUESTION":
        return {
            "status": "PARENT_RESEARCH_UNRESOLVED",
            "parent_meta_receipt_digest": stored["exact_content_digest"],
        }
    handoff = stored["handoff"]
    evidence = handoff["evidence"]
    research_plan = validate_learning_representation_research_adaptation_plan_v1(
        handoff["research_plan"]
    )
    require_v1(
        stored["status"] == "LEARNING_RESEARCH_PLAN_READY"
        and research_plan["research_purpose"]
        == RepresentationResearchPurpose.INVESTIGATE_FEATURE_USEFULNESS.value
        and research_plan["evaluation_fixture_label"] == MEASURED_PATTERN
        and research_plan["learning_representation_lineage_ref"]
        == evidence["representation_lineage_ref"],
        "RESEARCH_PARENT_PURPOSE_MISMATCH",
    )
    return {
        "status": "RESEARCH_PARENT_READY",
        "meta_receipt": stored,
        "cohort_plan": plan,
        "research_plan": research_plan,
        "evidence": evidence,
    }


def _declare_follow_up(
    *, parent, store_root, seed_job_key, seed_context_root, next_starts_utc, repository_sha
):
    frozen = read_frozen_market_forecast_v1(store_root=store_root, job_key=seed_job_key)
    target = recorded_market_target_from_frozen_v1(frozen)
    first_start = instant_v1(target["horizon_start_time_utc"])
    starts = [first_start, *(instant_v1(value) for value in next_starts_utc)]
    parent_plan = parent["cohort_plan"]
    require_v1(
        len(starts) == len(parent_plan["starts_utc"])
        and all(not (start.minute or start.second or start.microsecond) for start in starts)
        and all(later - earlier > timedelta(hours=2) for earlier, later in zip(starts, starts[1:])),
        "RESEARCH_FOLLOW_UP_WINDOW_CONTRACT_MISMATCH",
    )
    require_v1(re.fullmatch(r"[0-9a-f]{40}", repository_sha) is not None, "REPOSITORY_SHA_REQUIRED")
    evidence = parent["evidence"]
    request = target["market_request"]
    require_v1(
        {name: value for name, value in request.items() if name != "horizon_start_time_utc"}
        == evidence["target_contract"],
        "RESEARCH_FOLLOW_UP_TARGET_CONTRACT_MISMATCH",
    )
    parent_cutoff = instant_v1(evidence["evaluated_at_utc"])
    require_v1(
        parent_cutoff < instant_v1(frozen["context_package"]["as_of"]) < first_start,
        "RESEARCH_FOLLOW_UP_REQUIRES_LATER_ORIGINAL_CONTEXT",
    )
    seed_context = representation.read_recorded_representation_context_v1(
        seed_context_root, cutoff_utc=measurement._utc_now()
    )
    require_v1(seed_context == frozen["context_package"], "REPRESENTATION_SEED_CONTEXT_MISMATCH")
    job_dir = Path(store_root) / ".intelligence-integration-v1" / digest_v1(seed_job_key)
    schedule = _read(job_dir / measurement.PLAN_FILE, measurement.SCHEMA)
    require_v1(
        schedule["plan"]["job_key"] == seed_job_key
        and schedule["plan"]["forecast_digest"] == frozen["exact_content_digest"],
        "RESEARCH_FOLLOW_UP_SEED_SCHEDULE_MISMATCH",
    )
    measurement._validate_forecast_clock(frozen, target, schedule["forecast_verified_at_utc"])
    inputs = {
        "parent_meta_receipt_digest": parent["meta_receipt"]["exact_content_digest"],
        "parent_research_plan_identity": parent["research_plan"]["plan_identity"],
        "parent_representation_lineage_ref": evidence["representation_lineage_ref"],
        "seed_job_key": seed_job_key,
        "seed_context_root": str(Path(seed_context_root).resolve()),
        "seed_schedule_digest": schedule["exact_content_digest"],
        "starts_utc": [start.isoformat() for start in starts],
        "fit_window_count": parent_plan["fit_window_count"],
        "validation_fraction": parent_plan["validation_fraction"],
        "forecast_context_max_age_seconds": parent_plan["forecast_context_max_age_seconds"],
        "repository_sha": repository_sha,
    }
    with _lease(store_root, _campaign_key(seed_job_key)) as folder:
        path = folder / "paired_representation_follow_up_plan.json"
        if path.is_file():
            plan = _read(path, PLAN_SCHEMA)
            require_v1(plan["inputs"] == inputs, "RESEARCH_FOLLOW_UP_PLAN_CONFLICT")
        else:
            now = measurement._utc_now()
            require_v1(
                instant_v1(schedule["forecast_verified_at_utc"]) <= instant_v1(now) < first_start,
                "RESEARCH_FOLLOW_UP_MUST_BE_DECLARED_BEFORE_WINDOW",
            )
            require_v1(
                not (folder / "representation_cohort_plan.json").exists(),
                "RESEARCH_FOLLOW_UP_REQUIRES_UNSTARTED_COHORT",
            )
            plan = seal_v1(
                {
                    "schema_version": PLAN_SCHEMA,
                    "authority": "NONE",
                    "inputs": inputs,
                    "declared_at_utc": now,
                }
            )
            _append(path, plan)
    require_v1(
        instant_v1(schedule["forecast_verified_at_utc"])
        <= instant_v1(plan["declared_at_utc"])
        < first_start,
        "RESEARCH_FOLLOW_UP_PLAN_CLOCK_MISMATCH",
    )
    return plan


def run_paired_representation_follow_up_v1(
    *,
    parent_store_root,
    parent_seed_job_key,
    store_root,
    seed_job_key,
    seed_context_root,
    next_starts_utc,
    repository_sha,
    wait,
):
    """Consume the original research plan and persist the later measured answer."""
    parent = read_representation_research_parent_v1(
        store_root=parent_store_root, seed_job_key=parent_seed_job_key
    )
    if parent["status"] != "RESEARCH_PARENT_READY":
        return parent
    plan = _declare_follow_up(
        parent=parent,
        store_root=store_root,
        seed_job_key=seed_job_key,
        seed_context_root=seed_context_root,
        next_starts_utc=next_starts_utc,
        repository_sha=repository_sha,
    )
    inputs = plan["inputs"]
    exit_code = cohort.run_representation_cohort_v1(
        store_root=store_root,
        seed_job_key=inputs["seed_job_key"],
        seed_context_root=inputs["seed_context_root"],
        next_starts_utc=inputs["starts_utc"][1:],
        fit_window_count=inputs["fit_window_count"],
        validation_fraction=inputs["validation_fraction"],
        forecast_context_max_age_seconds=inputs["forecast_context_max_age_seconds"],
        repository_sha=inputs["repository_sha"],
        wait=wait,
    )
    if exit_code == 2:
        return {
            "status": "FOLLOW_UP_MEASUREMENT_EXPIRED",
            "follow_up_plan_digest": plan["exact_content_digest"],
        }
    result = meta.route_recorded_representation_cohort_v1(
        store_root=store_root, seed_job_key=seed_job_key
    )
    if result["status"] == "WAITING_FOR_COMPARISON":
        return {
            "status": "WAITING_FOR_FOLLOW_UP_COMPARISON",
            "follow_up_plan_digest": plan["exact_content_digest"],
        }
    answer = result["handoff"]["evidence"]
    measured = result["status"] == "LEARNING_RESEARCH_PLAN_READY"
    receipt = seal_v1(
        {
            "schema_version": RECEIPT_SCHEMA,
            "authority": "NONE",
            "status": "FOLLOW_UP_REMEASURED" if measured else "FOLLOW_UP_UNRESOLVED",
            "follow_up_plan_digest": plan["exact_content_digest"],
            "parent_meta_receipt_digest": inputs["parent_meta_receipt_digest"],
            "parent_research_plan_identity": inputs["parent_research_plan_identity"],
            "parent_comparison_digest": parent["meta_receipt"]["comparison_digest"],
            "follow_up_comparison_digest": result["comparison_digest"],
            "follow_up_meta_receipt_digest": result["exact_content_digest"],
            "parent_measurement": parent["evidence"]["measurement"],
            "follow_up_measurement": answer["measurement"],
            "follow_up_comparison_status": answer["comparison_status"],
            "independent_quality_proven": False,
            "productive_apply_authorized": False,
        }
    )
    with _lease(store_root, _campaign_key(seed_job_key)) as folder:
        output = folder / "paired_representation_follow_up_receipt.json"
        _append(output, receipt)
        return _read(output, RECEIPT_SCHEMA)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-store-root", required=True, type=Path)
    parser.add_argument("--parent-seed-job-key-file", required=True, type=Path)
    parser.add_argument("--store-root", required=True, type=Path)
    parser.add_argument("--seed-job-key-file", required=True, type=Path)
    parser.add_argument("--seed-context-root", required=True, type=Path)
    parser.add_argument("--next-start-utc", dest="next_starts_utc", required=True, action="append")
    parser.add_argument("--repository-sha", required=True)
    parser.add_argument("--wait", action="store_true")
    args = vars(parser.parse_args())
    args["seed_job_key"] = strict_json_v1(args.pop("seed_job_key_file").read_bytes())
    args["parent_seed_job_key"] = strict_json_v1(args.pop("parent_seed_job_key_file").read_bytes())
    result = run_paired_representation_follow_up_v1(**args)
    print(bytes_v1(result).decode())
    return 2 if result["status"] == "FOLLOW_UP_MEASUREMENT_EXPIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
