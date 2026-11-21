"""Precise original-case chronology before paired features, fits and Meta routing."""

from datetime import timedelta
import hashlib

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    phase_22_paired_market_research_v1 as paired,
)
from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
    build_independent_market_return_target_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    freeze_existing_market_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.independent_market_forecast_measurement_v1 import (
    calibrate_frozen_market_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    digest_v1,
    plain_v1,
)
from src.meta.learning_loop.paired_market_representation_meta_v1 import (
    route_paired_market_representation_v1,
)
from tests.learning.test_market_ols_exact_clock_admission_v1 import _observed_at, _stamp
from tests.learning.test_market_ols_next_forecast_v1 import (
    _representation_inputs,
    market_case,
    supplier,
    utc,
)
from tests.learning.test_mi_learning_exact_clock_admission_v1 import _remint

VARIANTS = (
    "plain",
    "zero_fraction",
    "utc_offset_zero",
    "holdout_at_cutoff",
    "missing_proxy",
    "pending",
    "fit_blocked",
    "late_label",
)


def _time(index, kind):
    freeze, owner = market_case(index)
    return freeze["context_package"]["as_of"] if kind == "context" else owner["evaluated_at_utc"]


def _job(
    root,
    index,
    *,
    evaluation=None,
    forecast_nanos=None,
    observed_nanos=None,
    pending=False,
    proxy=True,
    mark=None,
    max_end_age_seconds=None,
):
    def context_inputs(args, i):
        _representation_inputs(args, i, include_proxy=proxy)
        if observed_nanos is not None:
            _observed_at(observed_nanos, "Z")(args, i)

    freeze, owner = market_case(index, context_inputs=context_inputs, mark=mark)
    if max_end_age_seconds is not None:
        owner["request"]["max_end_age_seconds"] = max_end_age_seconds
        target = build_independent_market_return_target_v1(owner["request"])
        freeze["forecast_evidence"] = _remint(
            freeze["forecast_evidence"],
            bar_spec_ref=target["bar_spec_ref"],
            outcome_horizon_end_utc=target["return_end_close_time_utc"],
            provenance={
                **freeze["forecast_evidence"]["provenance"],
                "measured_return_target_v1": target,
            },
        )
        freeze["provider_admission"]["target_spec_digest"] = digest_v1(target)
    if forecast_nanos is not None:
        freeze["provider_admission"]["max_context_age_seconds"] = 1
        freeze["forecast_evidence"] = _remint(
            freeze["forecast_evidence"],
            forecast_created_at_utc=_stamp(
                freeze["forecast_evidence"]["forecast_created_at_utc"], forecast_nanos, "Z"
            ),
        )
    if evaluation is not None:
        owner["evaluated_at_utc"] = evaluation
    frozen = freeze_existing_market_forecast_v1(store_root=root, **freeze)
    if not pending:
        observation = supplier.materialize_independent_market_horizon_v1(**owner)
        calibrate_frozen_market_forecast_v1(
            store_root=root, frozen=frozen, market_observation=observation
        )
    return {"store_root": root, "job_key": frozen["job_key"]}


def _args(root, *, variant="plain", fault=None, nanos=1):
    jobs = []
    for index in range(8):
        changes = dict(proxy=variant != "missing_proxy", pending=variant == "pending")
        if variant == "fit_blocked":
            changes["mark"] = 100
        if fault in {"fit_label", "holdout_label"} and index == (5 if fault == "fit_label" else 7):
            changes["evaluation"] = _stamp(_time(index, "label"), nanos, "Z")
        if fault == "overlap" and index == 4:
            changes["evaluation"] = _stamp(_time(5, "context"), nanos, "Z")
        if fault == "overlap":
            # Same explicit freshness contract for all eight synthetic original jobs.
            changes["max_end_age_seconds"] = 2 * 86400
        if fault == "forecast" and index == 7:
            changes["forecast_nanos"] = nanos
        jobs.append(_job(root / str(index), index, **changes))
    args = dict(
        fit_jobs=jobs[:6],
        holdout_jobs=jobs[6:],
        fit_cutoff_utc=_time(5, "label"),
        evaluated_at_utc=_time(7, "label"),
        validation_fraction=0.25,
    )
    if variant == "zero_fraction":
        for key in ("fit_cutoff_utc", "evaluated_at_utc"):
            args[key] = _stamp(args[key], 0, "Z")
    if variant == "utc_offset_zero":
        for key in ("fit_cutoff_utc", "evaluated_at_utc"):
            args[key] = args[key].removesuffix("Z") + "+00:00"
    if variant == "holdout_at_cutoff":
        args["fit_cutoff_utc"] = _time(6, "context")
    if variant == "late_label":
        args["fit_cutoff_utc"] = utc(paired.instant_v1(_time(5, "label")) - timedelta(seconds=1))
    if fault == "holdout_split":
        args["fit_cutoff_utc"] = _stamp(_time(6, "context"), nanos, "Z")
    if fault == "fit_split":
        args["fit_cutoff_utc"] = _stamp(_time(5, "context"), nanos, "Z")
    if fault == "forecast":
        args["evaluated_at_utc"] = _time(7, "context")
    return args


def _packet(root, variant):
    args = _args(root, variant=variant)
    comparison = paired.compare_paired_market_b1_to_b0_v1(**args)
    handoff = route_paired_market_representation_v1(stored_comparison=comparison, **args)
    return plain_v1(
        {
            "comparison": comparison,
            "handoff": handoff,
            "cutoffs": {name: args[name] for name in ("fit_cutoff_utc", "evaluated_at_utc")},
        }
    )


def _files(root):
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


def _forbidden(*args, **kwargs):
    pytest.fail("Inconsistent original chronology reached paired features, fit or measurement")


@pytest.mark.parametrize("nanos", [1, 999])
@pytest.mark.parametrize("split", ["fit", "holdout"])
def test_late_original_label_remains_unavailable_before_features(
    tmp_path, monkeypatch, split, nanos
):
    args = _args(tmp_path, fault=f"{split}_label", nanos=nanos)
    before = _files(tmp_path)
    monkeypatch.setattr(paired, "_bind_features", _forbidden)
    monkeypatch.setattr(paired, "fit_ols_lstsq", _forbidden)
    result = paired.compare_paired_market_b1_to_b0_v1(**args)
    row = result["cases"][5 if split == "fit" else 7]
    assert result["status"] == "INSUFFICIENT_EVIDENCE"
    assert row["status"] == "LABEL_NOT_AVAILABLE_AT_CUTOFF"
    assert paired.TARGET not in row
    assert row["label_available_at"] == _stamp(
        _time(5 if split == "fit" else 7, "label"), nanos, "Z"
    )
    assert _files(tmp_path) == before


@pytest.mark.parametrize("nanos", [1, 999])
@pytest.mark.parametrize(
    ("fault", "reason"),
    [
        ("overlap", "PAIRED_CASE_OVERLAP"),
        ("holdout_split", "PAIRED_SPLIT_CONTEXT_CLOCK_INVALID"),
    ],
)
def test_precise_case_boundaries_stop_before_features(tmp_path, monkeypatch, fault, reason, nanos):
    args = _args(tmp_path, fault=fault, nanos=nanos)
    before = _files(tmp_path)
    monkeypatch.setattr(paired, "_bind_features", _forbidden)
    monkeypatch.setattr(paired, "fit_ols_lstsq", _forbidden)
    with pytest.raises(ValueError, match=reason):
        paired.compare_paired_market_b1_to_b0_v1(**args)
    assert _files(tmp_path) == before


@pytest.mark.parametrize("nanos", [1, 999])
def test_forecast_after_evaluation_stops_before_later_measurement(tmp_path, monkeypatch, nanos):
    args = _args(tmp_path, fault="forecast", nanos=nanos)
    read = paired.read_independent_market_calibration_v1
    last = args["holdout_jobs"][-1]["job_key"]

    def checked_read(**locator):
        if locator["job_key"] == last:
            _forbidden()
        return read(**locator)

    monkeypatch.setattr(paired, "read_independent_market_calibration_v1", checked_read)
    with pytest.raises(ValueError, match="PAIRED_FORECAST_CLOCK_INVALID"):
        paired.compare_paired_market_b1_to_b0_v1(**args)


@pytest.mark.parametrize("nanos", [1, 999])
def test_fit_context_before_fractional_cutoff_reaches_explicit_label_abstention(
    tmp_path, monkeypatch, nanos
):
    args = _args(tmp_path, fault="fit_split", nanos=nanos)
    monkeypatch.setattr(paired, "_bind_features", _forbidden)
    result = paired.compare_paired_market_b1_to_b0_v1(**args)
    assert result["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["cases"][5]["status"] == "LABEL_NOT_AVAILABLE_AT_CUTOFF"


def test_distinct_original_pending_instants_do_not_alias_the_display_time(tmp_path, monkeypatch):
    fit = [
        _job(tmp_path / f"fit-{nanos}", 0, observed_nanos=nanos, pending=True) for nanos in (1, 999)
    ]
    holdout = [_job(tmp_path / "holdout", 1, pending=True)]
    monkeypatch.setattr(paired, "_bind_features", _forbidden)
    result = paired.compare_paired_market_b1_to_b0_v1(
        fit_jobs=fit,
        holdout_jobs=holdout,
        fit_cutoff_utc=_time(0, "label"),
        evaluated_at_utc=_time(1, "label"),
        validation_fraction=0.25,
    )
    rows = result["cases"]
    assert result["status"] == "INSUFFICIENT_EVIDENCE"
    assert [row["status"] for row in rows] == ["MEASUREMENT_PENDING"] * 3
    assert rows[0]["context_as_of"] == rows[1]["context_as_of"]
    assert rows[0]["context_digest"] != rows[1]["context_digest"]
    repeated = paired.compare_paired_market_b1_to_b0_v1(
        fit_jobs=list(reversed(fit)),
        holdout_jobs=holdout,
        fit_cutoff_utc=_time(0, "label"),
        evaluated_at_utc=_time(1, "label"),
        validation_fraction=0.25,
    )
    assert repeated == result


@pytest.mark.parametrize("variant", VARIANTS)
def test_valid_original_comparison_and_meta_handoff_stay_connected(tmp_path, variant):
    packet = _packet(tmp_path, variant)
    measured = packet["comparison"]
    handoff = packet["handoff"]
    assert measured["independent_quality_proven"] is False
    assert handoff["productive_apply_authorized"] is False
    assert measured["fit_cutoff_utc"] == packet["cutoffs"]["fit_cutoff_utc"]
    assert measured["evaluated_at_utc"] == packet["cutoffs"]["evaluated_at_utc"]
    if variant in {"plain", "zero_fraction", "utc_offset_zero", "holdout_at_cutoff"}:
        assert measured["status"] == "MEASURED_CHRONOLOGICAL_HOLDOUT"
        assert handoff["status"] == "LEARNING_RESEARCH_PLAN_READY"
        assert handoff["routing_cycle"]["routing_result"]["optimization_consumer_invoked"] is False
    else:
        assert measured["status"] in {"INSUFFICIENT_EVIDENCE", "FIT_BLOCKED"}
        assert handoff["status"] == "UNRESOLVED_REPRESENTATION_QUESTION"
