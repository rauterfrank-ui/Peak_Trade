"""Create a new, explicitly synthetic native-store/model witness directory once."""

from datetime import timedelta
import json
from pathlib import Path

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    market_ols_next_forecast_v1 as learner,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.independent_market_forecast_measurement_v1 import (
    calibrate_frozen_market_forecast_v1,
)
from src.learning.deterministic_decision_outcome_v0 import (
    n_bars_bar_evidence_supplier_v1 as supplier,
)
from tests.learning.test_market_ols_next_forecast_v1 import (
    setup_training,
    next_forecast_args,
    original_job,
    utc,
)


def write_example(root):
    root = Path(root)
    if root.exists():
        raise ValueError("Preserve the existing witness; choose a new output directory.")
    args = setup_training(root)
    first = learner.train_market_ols_model_v1(**args)
    forecast_args, owner = next_forecast_args(root, first)
    first_forecast = learner.forecast_from_market_ols_model_v1(**forecast_args)
    observation = supplier.materialize_independent_market_horizon_v1(**owner)
    ack = calibrate_frozen_market_forecast_v1(
        store_root=forecast_args["store_root"],
        frozen=first_forecast["frozen"],
        market_observation=observation,
    )
    more = [original_job(root / "mi", i, realized=0.01 + 0.001 * i) for i in range(8, 12)]
    computed_job = {
        "store_root": forecast_args["store_root"],
        "job_key": first_forecast["frozen"]["job_key"],
    }
    cutoff = utc(learner.instant_v1(owner["evaluated_at_utc"]) + timedelta(seconds=10))
    child = learner.train_market_ols_model_v1(
        **{
            **args,
            "evidence_jobs": args["evidence_jobs"] + more + [computed_job],
            "trained_as_of": cutoff,
            "available_at": cutoff,
            "parent_model_ref": first["model_ref"],
        }
    )
    common_args, _ = next_forecast_args(root, child, index=14)
    child_forecast = learner.forecast_from_market_ols_model_v1(**common_args)
    parent_forecast = learner.forecast_from_market_ols_model_v1(
        **{**common_args, "model_ref": first["model_ref"]}
    )
    cold = learner.read_market_model_forecast_v1(
        model_store_root=args["model_store_root"],
        store_root=common_args["store_root"],
        job_key=child_forecast["frozen"]["job_key"],
    )
    assert cold == child_forecast
    witness = {
        "source_class": "TEST_ONLY_SYNTHETIC_ORIGINAL_OWNERS",
        "model_v1_ref": first["model_ref"],
        "model_v2_ref": child["model_ref"],
        "v1_coefficients": first["coefficients"],
        "v2_coefficients": child["coefficients"],
        "v1_validation": first["validation"],
        "v2_validation": child["validation"],
        "first_computed_forecast": first_forecast,
        "later_original_calibration": ack["calibration_result"],
        "computed_forecast_outcome_consumed_by_child": any(
            s["job_key"] == computed_job["job_key"] for s in child["request"]["samples"]
        ),
        "same_future_context": {
            "features": child_forecast["provider"]["feature_values"],
            "parent_payload": parent_forecast["provider"]["computed_payload"],
            "child_payload": child_forecast["provider"]["computed_payload"],
        },
        "child_forecast": child_forecast,
        "cold_provider_exactly_equal": cold == child_forecast,
        "model_training_and_next_inference_performed": True,
        "natural_source_quality_proven": False,
        "double_play_benefit_proven": False,
        "continuous_host_or_five_lane_runtime_activated": False,
    }
    (root / "witness.json").write_text(json.dumps(witness, ensure_ascii=False, indent=2) + "\n")
    return witness


if __name__ == "__main__":
    import sys

    result = write_example(sys.argv[1])
    print(json.dumps(result["same_future_context"], ensure_ascii=False))
