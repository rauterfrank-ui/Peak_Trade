"""Bounded numerical consumer probe; synthetic identity scaffold, no runtime join.

Run from repo root via scripts/pt with this file on stdin.
"""

import hashlib
import json
import math
import subprocess
from copy import deepcopy
from pathlib import Path

from src.experiments.canonical_robustness_suite_v1 import (
    RobustnessSuiteValidationError,
    build_canonical_robustness_evidence_v1,
    build_failure_records_for_failed_gates_v1,
    canonical_record_payload,
    canonical_robustness_policy_v1,
)
from tests.experiments.test_canonical_robustness_suite_v1 import _identity, _request

ROOT = Path.cwd()
OUT = ROOT / "docs/ops/evidence/measured_split_robustness_consumer_effect_v1_2026_11_04"
SOURCE = ROOT / "docs/ops/evidence/parameter_sensitivity_split_observation_v1_2026_11_04"
rows = json.loads((SOURCE / "captured_split_results.json").read_text())
grid = json.loads((SOURCE / "result_with_observer.json").read_text())


def dump(name, body):
    (OUT / name).write_text(json.dumps(body, indent=2, sort_keys=True, allow_nan=False) + "\n")


summary = []
for point in grid["points"]:
    assert point["evaluation_status"] == "EVALUATED"
    selected = [row for row in rows if row["parameter_set_id"] == point["parameter_set_id"]]
    assert [row["result_ref"] for row in selected] == [
        point["train_result_ref"],
        point["validation_result_ref"],
        point["out_of_sample_result_ref"],
    ]
    native_params = {
        key.removeprefix("strategy."): int(value)
        for key, value in point["parameter_values"].items()
    }
    # Remaining identity dimensions are explicit synthetic fixture scaffolding.
    # This numerical consumer test does not certify their source authenticity.
    identity = _identity(strategy_params=native_params, dataset_digest=point["data_digest"])
    split_metrics = {}
    for row in selected:
        split_name = "holdout" if row["split_name"] == "out_of_sample" else row["split_name"]
        # Known producer uses zero risk-free rate and sqrt(8760) annualization;
        # target policy declares MEAN_OVER_SAMPLE_STD_NO_ANNUALIZATION. This is
        # an explicit evidence-only dimensional conversion, not a global default.
        split_metrics[split_name] = {
            "sample_size": row["bar_count"],
            "sharpe": row["metrics"]["sharpe"] / math.sqrt(8760),
        }

    def evaluate(metrics):
        return build_canonical_robustness_evidence_v1(
            _request(
                identity=identity,
                observations={"split_metrics": metrics},
                parameter_region=native_params,
                regime="controlled_synthetic_hourly_simulator",
            )
        )

    def gate(record):
        return next(
            row for row in record["test_results"] if row["test_id"] == "TRAIN_VALIDATION_HOLDOUT"
        )

    actual = evaluate(split_metrics)
    assert (
        canonical_robustness_policy_v1()["annualization"] == "MEAN_OVER_SAMPLE_STD_NO_ANNUALIZATION"
    )
    assert gate(actual)["status"] == "PASS"
    assert actual["aggregate_status"] != "PASS"
    positive = deepcopy(split_metrics)
    positive["validation"]["sharpe"] = 100.0
    negative = deepcopy(split_metrics)
    negative["validation"]["sharpe"] = -100.0
    positive_result, negative_result = evaluate(positive), evaluate(negative)
    assert gate(positive_result)["status"] == gate(negative_result)["status"] == "PASS"
    assert (
        positive_result["integrity"]["content_sha256"]
        != negative_result["integrity"]["content_sha256"]
    )

    collapsed = deepcopy(split_metrics)
    collapsed["holdout"]["sharpe"] = 0.0
    collapsed_result = evaluate(collapsed)
    assert gate(collapsed_result)["status"] == "FAIL"
    failures = build_failure_records_for_failed_gates_v1(collapsed_result)
    assert any(row["failure_class"] == "REJECTED_OVERFIT" for row in failures)

    missing = deepcopy(split_metrics)
    del missing["validation"]
    missing_result = evaluate(missing)
    assert gate(missing_result)["status"] == "BLOCKED_MISSING_CAPABILITY"
    nonfinite = deepcopy(split_metrics)
    nonfinite["validation"]["sharpe"] = float("nan")
    try:
        evaluate(nonfinite)
    except RobustnessSuiteValidationError as exc:
        nonfinite_reason = str(exc)
    else:
        raise AssertionError("Nonfinite validation unexpectedly admitted")

    slow = native_params["slow_window"]
    dump(f"slow{slow}_actual.json", canonical_record_payload(actual))
    dump(f"slow{slow}_positive_validation_control.json", canonical_record_payload(positive_result))
    dump(f"slow{slow}_negative_validation_control.json", canonical_record_payload(negative_result))
    dump(f"slow{slow}_collapsed_holdout_control.json", canonical_record_payload(collapsed_result))
    dump(f"slow{slow}_missing_validation_control.json", canonical_record_payload(missing_result))
    dump(
        f"slow{slow}_collapsed_failure_records.json",
        [canonical_record_payload(row) for row in failures],
    )
    summary.append(
        {
            "source_parameter_set_id": point["parameter_set_id"],
            "native_parameters": native_params,
            "source_split_refs": [row["result_ref"] for row in selected],
            "converted_split_metrics": split_metrics,
            "actual_gate_status": gate(actual)["status"],
            "actual_aggregate_status": actual["aggregate_status"],
            "validation_plus_and_minus_100_gate": "PASS_BOTH_WITH_DISTINCT_BOUND_EVIDENCE",
            "collapsed_holdout_gate": "FAIL_WITH_REJECTED_OVERFIT_MEMORY",
            "missing_validation_gate": "BLOCKED_MISSING_CAPABILITY",
            "nonfinite_validation_denied": nonfinite_reason,
        }
    )

dump(
    "summary.json",
    {
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_split_file_sha256": hashlib.sha256(
            (SOURCE / "captured_split_results.json").read_bytes()
        ).hexdigest(),
        "source_grid_file_sha256": hashlib.sha256(
            (SOURCE / "result_with_observer.json").read_bytes()
        ).hexdigest(),
        "results": summary,
        "source_scope": "ACTUAL_SYNTHETIC_SIMULATOR_MEASUREMENTS_WITH_SYNTHETIC_IDENTITY_SCAFFOLD",
        "normalization": "KNOWN_ZERO_RF_HOURLY_SHARPE_DIVIDED_BY_SQRT_8760_FOR_DECLARED_NONANNUAL_POLICY",
        "authority": "NONE",
    },
)
print(json.dumps(summary))
