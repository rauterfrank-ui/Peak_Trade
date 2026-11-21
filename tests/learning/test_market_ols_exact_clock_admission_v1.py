"""Native UTC fractions must survive the OLS training and inference admissions."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    market_ols_next_forecast_v1 as learner,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    freeze_existing_market_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.independent_market_forecast_measurement_v1 import (
    calibrate_frozen_market_forecast_v1,
)
from tests.learning.test_market_ols_next_forecast_v1 import (
    POLICY,
    market_case,
    next_forecast_args,
    setup_training,
    supplier,
    utc,
)


def _stamp(value, nanos, suffix):
    whole = learner.instant_v1(value).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{whole}.{nanos:09d}{suffix}"


def _observed_at(nanos, suffix):
    def change(args, index):
        args["request"] = replace(
            args["request"], observed_at=_stamp(args["request"].observed_at, nanos, suffix)
        )
        # Exercise the later OLS gate with an independently admissible source context.
        if nanos:
            args["policy"] = replace(
                args["policy"],
                max_age_seconds_by_role={
                    role: seconds + 1
                    for role, seconds in args["policy"].max_age_seconds_by_role.items()
                },
            )

    return change


def _original_label(root, nanos, suffix):
    freeze, owner = market_case(7)
    owner["evaluated_at_utc"] = _stamp(owner["evaluated_at_utc"], nanos, suffix)
    frozen = freeze_existing_market_forecast_v1(store_root=root, **freeze)
    observation = supplier.materialize_independent_market_horizon_v1(**owner)
    calibrate_frozen_market_forecast_v1(
        store_root=root, frozen=frozen, market_observation=observation
    )
    return {"store_root": root, "job_key": frozen["job_key"]}, owner["evaluated_at_utc"]


def _forbidden(*args, **kwargs):
    pytest.fail("Noncausal input reached the original fitter or feature consumer")


@pytest.mark.parametrize("suffix", ["Z", "+00:00"])
@pytest.mark.parametrize("fault", ["publication", "label_cutoff", "parent"])
def test_submicrosecond_training_lookahead_stops_before_fit(tmp_path, monkeypatch, fault, suffix):
    args = setup_training(tmp_path, count=9 if fault == "parent" else 8)
    model_before = None
    if fault == "publication":
        args.update(
            trained_as_of=_stamp(args["trained_as_of"], 2, suffix),
            available_at=_stamp(args["available_at"], 1, suffix),
        )
        reason = "MODEL_AVAILABILITY_BEFORE_TRAINING"
    elif fault == "label_cutoff":
        job, available = _original_label(tmp_path / "later-label", 1, suffix)
        args.update(
            evidence_jobs=[*args["evidence_jobs"][:-1], job],
            trained_as_of=_stamp(available, 0, suffix),
            available_at=_stamp(available, 0, suffix),
        )
        reason = "MODEL_LABEL_NOT_AVAILABLE_AT_CUTOFF"
    else:
        parent_cutoff = utc(
            learner.instant_v1(market_case(7)[1]["evaluated_at_utc"]) + timedelta(seconds=10)
        )
        parent = learner.train_market_ols_model_v1(
            **{
                **args,
                "evidence_jobs": args["evidence_jobs"][:-1],
                "trained_as_of": parent_cutoff,
                "available_at": _stamp(args["trained_as_of"], 1, suffix),
            }
        )
        path = learner._model_path(args["model_store_root"], parent["model_ref"])
        model_before = (path, path.read_bytes())
        args.update(
            trained_as_of=_stamp(args["trained_as_of"], 0, suffix),
            available_at=_stamp(args["available_at"], 0, suffix),
            parent_model_ref=parent["model_ref"],
        )
        reason = "MODEL_PARENT_KNOWLEDGE_LOOKAHEAD"
    monkeypatch.setattr(learner, "_fit_request", _forbidden)
    with pytest.raises(ValueError, match=reason):
        learner.train_market_ols_model_v1(**args)
    if model_before is None:
        assert not args["model_store_root"].exists()
    else:
        assert model_before[0].read_bytes() == model_before[1]
        assert len(list((args["model_store_root"] / "models").glob("*.json"))) == 1


@pytest.mark.parametrize(
    "fault,suffix",
    [
        ("publication", "Z"),
        ("publication", "+00:00"),
        ("context_order", "Z"),
        ("context_age", "Z"),
        ("label_age", "Z"),
    ],
)
def test_submicrosecond_forecast_admission_stops_before_features(
    tmp_path, monkeypatch, fault, suffix
):
    args = setup_training(tmp_path)
    context_nanos = 2 if fault == "context_order" else 1 if fault == "label_age" else 0
    freeze, owner = market_case(12, context_inputs=_observed_at(context_nanos, "Z"))
    context = freeze["context_package"]
    if fault == "publication":
        args["available_at"] = _stamp(context["as_of"], 1, suffix)
    elif fault == "label_age":
        last = market_case(7)[1]["evaluated_at_utc"]
        seconds = int(
            (learner.instant_v1(context["as_of"]) - learner.instant_v1(last)).total_seconds()
        )
        args["policy"] = replace(POLICY, max_training_evidence_age_seconds=seconds)
    model = learner.train_market_ols_model_v1(**args)
    forecast_args, _ = next_forecast_args(tmp_path, model)
    forecast_args.update(
        context_package=context,
        market_request=owner["request"],
        forecast_created_at=(
            _stamp(context["as_of"], 1, "Z")
            if fault in {"context_order", "context_age"}
            else context["as_of"]
        ),
    )
    reason = {
        "publication": "MODEL_FORECAST_KNOWLEDGE_LOOKAHEAD",
        "context_order": "MODEL_FORECAST_KNOWLEDGE_LOOKAHEAD",
        "context_age": "MODEL_FORECAST_CONTEXT_STALE",
        "label_age": "MODEL_TRAINING_EVIDENCE_STALE",
    }[fault]
    monkeypatch.setattr(learner, "_extract", _forbidden)
    with pytest.raises(ValueError, match=reason):
        learner.forecast_from_market_ols_model_v1(**forecast_args)
    assert not forecast_args["store_root"].exists()


@pytest.mark.parametrize("suffix", ["Z", "+00:00"])
def test_equal_label_cutoff_preserves_original_timestamp_and_cold_model(
    tmp_path, monkeypatch, suffix
):
    args = setup_training(tmp_path)
    job, available = _original_label(tmp_path / "equal-label", 1, suffix)
    args.update(
        evidence_jobs=[*args["evidence_jobs"][:-1], job],
        trained_as_of=available,
        available_at=available,
    )
    model = learner.train_market_ols_model_v1(**args)
    assert model["request"]["samples"][-1]["label_available_at"] == available
    assert model["request"]["trained_as_of"] == model["request"]["available_at"] == available
    monkeypatch.setattr(learner, "_fit_request", _forbidden)
    assert learner.train_market_ols_model_v1(**args) == model
    assert (
        learner.read_market_ols_model_v1(
            model_store_root=args["model_store_root"], model_ref=model["model_ref"]
        )
        == model
    )


@pytest.mark.parametrize("suffix", ["Z", "+00:00"])
@pytest.mark.parametrize("age_limit", [0, 10**20])
def test_equal_forecast_clocks_preserve_original_provider_and_cold_read(
    tmp_path, monkeypatch, suffix, age_limit
):
    args = setup_training(tmp_path)
    args["policy"] = replace(
        POLICY,
        max_context_age_seconds=age_limit,
        max_training_evidence_age_seconds=max(POLICY.max_training_evidence_age_seconds, age_limit),
    )
    freeze, owner = market_case(12, context_inputs=_observed_at(1, "Z"))
    args["available_at"] = _stamp(freeze["context_package"]["as_of"], 1, suffix)
    model = learner.train_market_ols_model_v1(**args)
    forecast_args, _ = next_forecast_args(tmp_path, model)
    forecast_args.update(
        context_package=freeze["context_package"],
        market_request=owner["request"],
        forecast_created_at=freeze["context_package"]["as_of"],
    )
    result = learner.forecast_from_market_ols_model_v1(**forecast_args)
    assert model["request"]["available_at"] == args["available_at"]
    assert (
        result["frozen"]["forecast_evidence"]["forecast_created_at_utc"]
        == freeze["context_package"]["as_of"]
    )
    for name in ["_extract", "_fit_request", "mint_forecast_evidence_v1"]:
        monkeypatch.setattr(learner, name, _forbidden)
    assert (
        learner.read_market_model_forecast_v1(
            model_store_root=args["model_store_root"],
            store_root=forecast_args["store_root"],
            job_key=result["frozen"]["job_key"],
        )
        == result
    )


@pytest.mark.parametrize(
    "model_ref",
    [
        "mi.market.ols.8bb95db2cad4898c132d83d8170e9682650d5bb767d7d1d440860bdf2145f89d",
        "mi.market.ols.48387d2737d05f6c41333b3499f1ee53aa75f96aee6b6dcf6b489bfbaa2cfdbc",
    ],
)
def test_original_archived_models_remain_readable_without_refitting(monkeypatch, model_ref):
    root = Path(__file__).resolve().parents[2]
    store = (
        root / "docs/ops/evidence/independent_market_ols_next_forecast_v1_2026_11_06/example/models"
    )
    path = store / "models" / (model_ref + ".json")
    before = path.read_bytes()
    original = learner.strict_json_v1(before)
    for name in [
        "fit_ols_lstsq",
        "_extract",
        "_fit_request",
        "read_independent_market_calibration_v1",
    ]:
        monkeypatch.setattr(learner, name, _forbidden)
    assert learner.read_market_ols_model_v1(model_store_root=store, model_ref=model_ref) == original
    assert path.read_bytes() == before
