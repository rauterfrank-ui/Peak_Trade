"""Compare B1's OHLCV proxy with B0 on the same original market cases."""

import math
from pathlib import Path

from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
    build_independent_market_return_target_v1,
)
from src.research.linear_evidence.feature_matrix import build_feature_matrix_binding
from src.research.linear_evidence.fitters import fit_ols_lstsq

from .context_admission_v1 import replay_admitted_market_context_v1
from .forecast_measurement_integration_v1 import read_frozen_market_forecast_v1
from .incremental_information_set_v1 import (
    IncrementalInformationSetRequestV1,
    STAGE_B0,
    STAGE_B1,
    build_incremental_information_set_v1,
    project_market_context_to_stage_v1,
)
from .independent_market_forecast_measurement_v1 import read_independent_market_calibration_v1
from .integration_contracts_v1 import (
    assert_offline_v1,
    digest_v1,
    finite_v1,
    instant_v1,
    require_v1,
    seal_v1,
)
from .market_context_v1 import ContextFamilyPresence, MICROSTRUCTURE_KIND_PROXY_OHLCV
from .phase_22_incremental_research_evidence_v1 import build_incremental_comparison_evidence_v1

SCHEMA = "phase_22_paired_market_research_v1"
BASELINE_FEATURES = ("mark_price", "signed_flow_quote")
PROXY_FEATURE = "signed_return_volume_pressure"
TARGET = "realized_log_return"


def _read_case(locator, *, split, fit_cutoff, evaluated_at):
    require_v1(set(locator) == {"store_root", "job_key"}, "ORIGINAL_MARKET_JOB_LOCATOR_REQUIRED")
    frozen = read_frozen_market_forecast_v1(**locator)
    context = replay_admitted_market_context_v1(frozen["context_package"])
    forecast = frozen["forecast_evidence"]
    target = forecast["provenance"]["measured_return_target_v1"]
    request = target["market_request"]
    require_v1(
        build_independent_market_return_target_v1(request) == target
        and digest_v1(target) == locator["job_key"]["target_spec_digest"],
        "PAIRED_TARGET_MISMATCH",
    )
    as_of = instant_v1(context["as_of"])
    forecast_at = instant_v1(forecast["forecast_created_at_utc"])
    require_v1(
        as_of <= forecast_at <= min(instant_v1(request["horizon_start_time_utc"]), evaluated_at),
        "PAIRED_FORECAST_CLOCK_INVALID",
    )
    require_v1(
        (as_of < fit_cutoff if split == "FIT" else fit_cutoff <= as_of),
        "PAIRED_SPLIT_CONTEXT_CLOCK_INVALID",
    )
    row = {
        "job_key": locator["job_key"],
        "frozen_digest": frozen["exact_content_digest"],
        "context_digest": context["exact_content_digest"],
        "context_as_of": as_of.isoformat(timespec="microseconds"),
        "split": split,
        "label_available_at": None,
    }
    native = context["market_context"]
    present = ContextFamilyPresence.PRESENT.value
    baseline = all(
        native[name]["presence"] == present for name in ("price_state_ref", "flow_state_ref")
    )
    proxy = native["liquidity_microstructure_state_ref"]
    challenger = (
        baseline
        and proxy["presence"] == present
        and proxy.get("microstructure_kind") == MICROSTRUCTURE_KIND_PROXY_OHLCV
    )
    row["baseline_context_available"] = baseline
    row["challenger_context_available"] = challenger
    job_dir = (
        Path(locator["store_root"]) / ".intelligence-integration-v1" / digest_v1(locator["job_key"])
    )
    if not (job_dir / "calibration_ack.json").is_file():
        row["status"] = "MEASUREMENT_PENDING"
        return row, request, context
    packet = read_independent_market_calibration_v1(**locator)
    observation = packet["measurement_inputs"]["market_observation"]
    require_v1(observation["request"] == request, "PAIRED_MEASUREMENT_REQUEST_MISMATCH")
    available = instant_v1(observation["evaluated_at_utc"])
    cutoff = fit_cutoff if split == "FIT" else evaluated_at
    row["label_available_at"] = observation["evaluated_at_utc"]
    row["observation_digest"] = observation["exact_content_digest"]
    row["actual_outcome_ref"] = observation["measurement"]["actual_outcome_ref"]
    if available > cutoff:
        row["status"] = "LABEL_NOT_AVAILABLE_AT_CUTOFF"
    elif not baseline:
        row["status"] = "B0_CONTEXT_INCOMPLETE"
    elif proxy["presence"] != present:
        row["status"] = "B1_PROXY_MISSING"
    elif not challenger:
        row["status"] = "B1_PROXY_UNSUPPORTED"
    else:
        row["status"] = "PAIRED"
        row[TARGET] = finite_v1(observation["measurement"]["log_return"], TARGET)
    return row, request, context


def _bind_features(context, stages, price_unit):
    native = context["market_context"]
    projected = {
        stage: project_market_context_to_stage_v1(
            native, stage_id=stage, information_set_id=info["information_set_id"]
        )
        for stage, info in stages.items()
    }
    baseline, challenger = projected[STAGE_B0], projected[STAGE_B1]
    derivations = context["derivations"]
    price = derivations[baseline["price_state_ref"]["state_ref"]]
    flow = derivations[baseline["flow_state_ref"]["state_ref"]]
    proxy = derivations[challenger["liquidity_microstructure_state_ref"]["state_ref"]]
    require_v1(
        all(
            binding["units"].get("price") == price_unit
            for binding in context["source_bindings"]
            if binding["role"] in {"price_mark", "price_o4", "flow", "microstructure"}
        ),
        "PAIRED_FEATURE_PRICE_UNIT_MISMATCH",
    )
    mark = price["mark_px"] if price["fact_kind"] == "FinalizedPt1mMarkFactV1" else price["close"]
    return {
        "price_fact_kind": price["fact_kind"],
        "projected_context_refs": {stage: body["context_id"] for stage, body in projected.items()},
        "features": {
            "mark_price": finite_v1(float(mark), "mark_price"),
            "signed_flow_quote": finite_v1(float(flow["signed_net_notional"]), "signed_flow_quote"),
            PROXY_FEATURE: finite_v1(float(proxy["proxy_features"][PROXY_FEATURE]), PROXY_FEATURE),
        },
    }


def _fit(rows, feature_names, validation_fraction, market_digest):
    matrix_rows = [
        {"context_as_of": row["context_as_of"], TARGET: row[TARGET], **row["features"]}
        for row in rows
    ]
    x, y, binding = build_feature_matrix_binding(
        matrix_rows, feature_names=feature_names, target_name=TARGET, time_name="context_as_of"
    )
    require_v1(binding.n_samples == len(rows), "PAIRED_MATRIX_DROPPED_ROWS")
    fitted = fit_ols_lstsq(
        x,
        y,
        binding,
        validation_fraction=validation_fraction,
        instrument_universe_digest=market_digest,
        evidence_type="PairedB0B1MarketLogReturnResearchV1",
    )
    return {
        "status": fitted.status,
        "reason_codes": fitted.reason_codes,
        "coefficients": fitted.coefficients,
        "feature_matrix_digest": fitted.feature_matrix_digest,
        "target_digest": fitted.target_digest,
    }


def compare_paired_market_b1_to_b0_v1(
    *, fit_jobs, holdout_jobs, fit_cutoff_utc, evaluated_at_utc, validation_fraction
):
    """Fit both arms on the same pre-cutoff population and compare a later holdout."""
    assert_offline_v1()
    cutoff, evaluated = instant_v1(fit_cutoff_utc), instant_v1(evaluated_at_utc)
    fraction = finite_v1(validation_fraction, "VALIDATION_FRACTION")
    require_v1(
        bool(fit_jobs) and bool(holdout_jobs) and cutoff < evaluated and 0 < fraction < 1,
        "EXPLICIT_PAIRED_TIME_SPLIT_REQUIRED",
    )
    case_inputs = [
        _read_case(locator, split=split, fit_cutoff=cutoff, evaluated_at=evaluated)
        for split, locators in (("FIT", fit_jobs), ("HOLDOUT", holdout_jobs))
        for locator in locators
    ]
    case_inputs.sort(key=lambda case: case[0]["context_as_of"])
    rows = [row for row, _, _ in case_inputs]
    require_v1(
        len({digest_v1(row["job_key"]) for row in rows}) == len(rows), "PAIRED_DUPLICATE_JOB"
    )
    labels = [row["actual_outcome_ref"] for row in rows if "actual_outcome_ref" in row]
    require_v1(len(set(labels)) == len(labels), "PAIRED_DUPLICATE_OUTCOME")
    targets = [
        {k: v for k, v in request.items() if k != "horizon_start_time_utc"}
        for _, request, _ in case_inputs
    ]
    target = targets[0]
    require_v1(all(other == target for other in targets), "PAIRED_TARGET_CONTRACT_MISMATCH")
    for previous, current in zip(rows, rows[1:]):
        require_v1(
            previous["context_as_of"] < current["context_as_of"], "PAIRED_DUPLICATE_CASE_TIME"
        )
        if previous["status"] == current["status"] == "PAIRED":
            require_v1(
                instant_v1(previous["label_available_at"]) <= instant_v1(current["context_as_of"]),
                "PAIRED_CASE_OVERLAP",
            )

    result = {
        "schema_version": SCHEMA,
        "authority": "NONE",
        "status": "INSUFFICIENT_EVIDENCE",
        "target_contract": target,
        "fit_cutoff_utc": fit_cutoff_utc,
        "evaluated_at_utc": evaluated_at_utc,
        "validation_fraction": fraction,
        "declared_case_count": len(rows),
        "paired_case_count": sum(row["status"] == "PAIRED" for row in rows),
        "cases": rows,
        "stage_comparison": None,
        "independent_quality_proven": False,
        "productive_apply_authorized": False,
    }
    # This comparison requires identical coverage; any excluded case is explicit.
    fit_count = len(fit_jobs)
    training_count = max(1, min(fit_count - 1, int(round(fit_count * (1.0 - fraction)))))
    if result["paired_case_count"] != len(rows):
        result["reason"] = "DECLARED_CASES_INCOMPLETE"
        return seal_v1(result)
    if fit_count < 5 or training_count < 4:
        result["reason"] = "INSUFFICIENT_PRE_CUTOFF_ROWS"
        return seal_v1(result)

    feature_version_names = {
        STAGE_B0: ("price_state", "flow_state"),
        STAGE_B1: ("price_state", "flow_state", "liquidity_microstructure"),
    }
    provenance = ("mi.paired.population." + digest_v1([row["frozen_digest"] for row in rows]),)
    stages = {}
    for stage, names in feature_version_names.items():
        versions = [
            {name: context["market_context"]["feature_versions"][name] for name in names}
            for _, _, context in case_inputs
        ]
        require_v1(
            all(value == versions[0] for value in versions), "PAIRED_FEATURE_VERSION_MISMATCH"
        )
        stages[stage] = build_incremental_information_set_v1(
            IncrementalInformationSetRequestV1(
                stage_id=stage,
                horizon_identity=target,
                feature_versions=versions[0],
                provenance_refs=provenance,
                microstructure_kind=MICROSTRUCTURE_KIND_PROXY_OHLCV if stage == STAGE_B1 else None,
            )
        )
    for row, _, context in case_inputs:
        row.update(_bind_features(context, stages, target["price_unit"]))
    require_v1(
        len({row["price_fact_kind"] for row in rows}) == 1, "PAIRED_PRICE_FACT_KIND_MISMATCH"
    )
    result["feature_units"] = {
        "mark_price": target["price_unit"],
        "signed_flow_quote": {"price_unit": target["price_unit"], "size_unit": "BASE"},
        PROXY_FEATURE: "SIGNED_LOG1P_OF_BASE_VOLUME",
    }
    market_digest = digest_v1(target["market_identity"])
    fits = {
        STAGE_B0: _fit(rows[:fit_count], BASELINE_FEATURES, fraction, market_digest),
        STAGE_B1: _fit(
            rows[:fit_count], (*BASELINE_FEATURES, PROXY_FEATURE), fraction, market_digest
        ),
    }
    result["fits"] = fits
    if any(fit["status"] != "CALIBRATION_CANDIDATE" for fit in fits.values()):
        result["status"] = "FIT_BLOCKED"
        return seal_v1(result)
    holdout = rows[fit_count:]
    errors = {stage: [] for stage in fits}
    for row in holdout:
        row["holdout_errors"] = {}
        for stage, fit in fits.items():
            weights = fit["coefficients"]
            predicted = weights["intercept"] + sum(
                weight * row["features"][name]
                for name, weight in weights.items()
                if name != "intercept"
            )
            error = finite_v1(row[TARGET] - predicted, "PAIRED_HOLDOUT_ERROR")
            row["holdout_errors"][stage] = error
            errors[stage].append(error)
    rmse = {
        stage: math.sqrt(math.fsum(error * error for error in values) / len(holdout))
        for stage, values in errors.items()
    }
    result["status"] = "MEASURED_CHRONOLOGICAL_HOLDOUT"
    result["stage_comparison"] = build_incremental_comparison_evidence_v1(
        stage_id=STAGE_B1,
        predecessor_stage_id=STAGE_B0,
        stage_information_set_id=stages[STAGE_B1]["information_set_id"],
        predecessor_information_set_id=stages[STAGE_B0]["information_set_id"],
        stage_plane_identity=None,
        predecessor_plane_identity=None,
        challenger_delta=rmse[STAGE_B0] - rmse[STAGE_B1],
        walk_forward_summary={
            "kind": "SINGLE_CHRONOLOGICAL_HOLDOUT",
            "training_rows": training_count,
            "fit_validation_rows": fit_count - training_count,
            "holdout_rows": len(holdout),
        },
        calibration_summary={"metric": "RMSE", "unit": "LOG_RETURN", "rmse_by_stage": rmse},
        redundancy_summary=None,
    )
    return seal_v1(result)
