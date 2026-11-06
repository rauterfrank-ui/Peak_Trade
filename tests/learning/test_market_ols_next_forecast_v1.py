"""Actual original market jobs → fitted numeric model → next forecast/calibration."""

from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
import hashlib
import json
import math
from pathlib import Path
import subprocess

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    market_ols_next_forecast_v1 as learner,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
    compose_admitted_market_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    freeze_existing_market_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.independent_market_forecast_measurement_v1 import (
    calibrate_frozen_market_forecast_v1,
    read_independent_market_calibration_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    digest_v1,
    seal_v1,
)
from src.learning.deterministic_decision_outcome_v0 import (
    n_bars_bar_evidence_supplier_v1 as supplier,
)
from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
    build_independent_market_return_target_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from tests.learning.test_independent_market_forecast_measurement_v1 import case, utc

FEATURE = learner.MarketOlsFeatureV1(
    "mark", "price_mark", 0, "FinalizedPt1mMarkFactV1", "mark_px", "USDT_PER_ETH"
)
POLICY = learner.MarketOlsPolicyV1(0.25, 4, 2, 0, 10 * 86400)


def market_case(index, *, mark=None, realized=None, generation="market.synthetic.1"):
    args, freeze, owner, _ = case(generation=generation)
    offset = timedelta(days=index)
    price = 100 + index if mark is None else mark
    if realized is None:
        realized = 0.001 + 0.0001 * index + (0.00005 if index % 2 else -0.00005)
    p = deepcopy(args["request"].price_mark_fact.payload)
    p["mark_px"] = str(price)
    p["interval_start_ms"] += int(offset.total_seconds() * 1000)
    for key in ["effective_at", "captured_at"]:
        p["timestamps"][key] = utc(learner.instant_v1(p["timestamps"][key]) + offset)
    fact = replace(args["request"].price_mark_fact, payload=p, fact_digest=fact_digest(p))
    receipt = replace(
        next(iter(args["receipts_by_digest"].values())),
        payload_bytes=bytes_v1(p),
        known_at=p["timestamps"]["captured_at"],
        available_at=p["timestamps"]["captured_at"],
    )
    args["receipts_by_digest"] = {fact.fact_digest: receipt}
    args["request"] = replace(
        args["request"],
        observed_at=utc(learner.instant_v1(args["request"].observed_at) + offset),
        price_mark_fact=fact,
    )
    context = compose_admitted_market_context_v1(**args)
    request = owner["request"]
    request["horizon_start_time_utc"] = utc(
        learner.instant_v1(request["horizon_start_time_utc"]) + offset
    )
    for i, source in enumerate(owner["source_receipts"]):
        bar = json.loads(source["original_bar_json"])
        for key in ["bar_close_time", "bar_open_time"]:
            bar[key] += offset.total_seconds()
        bar["last_observation_identity"]["venue_event_time"] += offset.total_seconds()
        close = 110.0 if i == 0 else 110.0 * math.exp(realized)
        bar["close"] = bar["last_observation_identity"]["mark_price"] = close
        source["original_bar_json"] = bytes_v1(bar).decode()
        source["original_bar_sha256"] = hashlib.sha256(
            source["original_bar_json"].encode()
        ).hexdigest()
        for key in ["known_at_utc", "available_at_utc"]:
            source[key] = utc(learner.instant_v1(source[key]) + offset)
    owner["evaluated_at_utc"] = utc(learner.instant_v1(owner["evaluated_at_utc"]) + offset)
    target = build_independent_market_return_target_v1(request)
    forecast = mint_forecast_evidence_v1(
        information_set_ref=context["market_context"]["information_set_ref"],
        forecast_created_at_utc=context["as_of"],
        outcome_horizon_end_utc=target["return_end_close_time_utc"],
        n_bars=request["n_bars"],
        bar_spec_ref=target["bar_spec_ref"],
        forecast_kind="RETURN_DISTRIBUTION_SUMMARY",
        probabilistic_payload={"mean_return": 0.02, "std_return": 0.1},
        market_state_refs=[context["market_context"]["context_id"]],
        forecast_model_ref="TEST_ONLY_SUPPLIED_MODEL",
        support_disposition="SUFFICIENT_EVIDENCE",
        selected_instrument_ref=context["identity"]["instrument_ref"],
        provenance={"TEST_ONLY_SYNTHETIC": True, "measured_return_target_v1": target},
    )
    freeze["context_package"], freeze["forecast_evidence"] = context, dict(forecast)
    freeze["original_probabilistic_payload"] = bytes_v1(forecast["probabilistic_payload"])
    freeze["provider_admission"].update(
        context_package_digest=context["exact_content_digest"], target_spec_digest=digest_v1(target)
    )
    return freeze, owner


def original_job(root, index, **kwargs):
    freeze, owner = market_case(index, **kwargs)
    frozen = freeze_existing_market_forecast_v1(store_root=root, **freeze)
    observation = supplier.materialize_independent_market_horizon_v1(**owner)
    calibrate_frozen_market_forecast_v1(
        store_root=root, frozen=frozen, market_observation=observation
    )
    return {"store_root": root, "job_key": frozen["job_key"]}


def setup_training(tmp_path, count=8, **kwargs):
    jobs = [original_job(tmp_path / "mi", i, **kwargs) for i in range(count)]
    last = market_case(count - 1)[1]["evaluated_at_utc"]
    cutoff = utc(learner.instant_v1(last) + timedelta(seconds=10))
    return dict(
        model_store_root=tmp_path / "models",
        evidence_jobs=jobs,
        features=[FEATURE],
        policy=POLICY,
        trained_as_of=cutoff,
        available_at=cutoff,
        parent_model_ref=None,
    )


def next_forecast_args(tmp_path, model, index=12):
    freeze, owner = market_case(index)
    return dict(
        model_store_root=tmp_path / "models",
        model_ref=model["model_ref"],
        store_root=tmp_path / "next-mi",
        context_package=freeze["context_package"],
        market_request=owner["request"],
        forecast_created_at=freeze["context_package"]["as_of"],
        attempt_generation="next.1",
    ), owner


def forbidden(*args, **kwargs):
    raise AssertionError("FIT_OR_FORECAST_RECOMPUTATION_FORBIDDEN")


def test_original_numeric_training_next_inference_measurement_and_child(tmp_path):
    args = setup_training(tmp_path)
    model = learner.train_market_ols_model_v1(**args)
    assert model["model_version"] == 1
    assert model["coefficients"]["mark"] == pytest.approx(0.0001, abs=1e-5)
    assert model["validation"]["training_rows"] == 6
    forecast_args, owner = next_forecast_args(tmp_path, model)
    result = learner.forecast_from_market_ols_model_v1(**forecast_args)
    frozen = result["frozen"]
    expected = model["coefficients"]["intercept"] + model["coefficients"]["mark"] * 112
    assert frozen["forecast_evidence"]["probabilistic_payload"]["mean_return"] == expected
    assert result["provider"]["model_inference_performed"] is True
    assert frozen["model_inference_performed"] is False
    observation = supplier.materialize_independent_market_horizon_v1(**owner)
    ack = calibrate_frozen_market_forecast_v1(
        store_root=forecast_args["store_root"], frozen=frozen, market_observation=observation
    )
    assert ack["calibration_result"]["error"] == observation["measurement"]["log_return"] - expected
    assert (
        read_independent_market_calibration_v1(
            store_root=forecast_args["store_root"], job_key=frozen["job_key"]
        )["calibration_ack"]
        == ack
    )
    # Add actual completed jobs, including the forecast produced from stored weights.
    added = [original_job(tmp_path / "mi", i, realized=0.01 + 0.001 * i) for i in range(8, 12)]
    cutoff = utc(learner.instant_v1(owner["evaluated_at_utc"]) + timedelta(seconds=10))
    child = learner.train_market_ols_model_v1(
        **{
            **args,
            "evidence_jobs": args["evidence_jobs"]
            + added
            + [{"store_root": forecast_args["store_root"], "job_key": frozen["job_key"]}],
            "trained_as_of": cutoff,
            "available_at": cutoff,
            "parent_model_ref": model["model_ref"],
        }
    )
    assert child["model_version"] == 2
    assert child["request"]["parent_model_ref"] == model["model_ref"]
    # Same future context, different stored model -> different numeric forecast.
    next_args, _ = next_forecast_args(tmp_path, child, index=14)
    child_result = learner.forecast_from_market_ols_model_v1(**next_args)
    parent_result = learner.forecast_from_market_ols_model_v1(
        **{**next_args, "model_ref": model["model_ref"]}
    )
    assert child_result["provider"]["feature_values"] == parent_result["provider"]["feature_values"]
    assert (
        child_result["provider"]["computed_payload"]["mean_return"]
        != parent_result["provider"]["computed_payload"]["mean_return"]
    )


def test_exact_retry_and_cold_model_read_never_refit(tmp_path, monkeypatch):
    args = setup_training(tmp_path)
    model = learner.train_market_ols_model_v1(**args)
    monkeypatch.setattr(learner, "fit_ols_lstsq", forbidden)
    assert learner.train_market_ols_model_v1(**args) == model
    assert (
        learner.read_market_ols_model_v1(
            model_store_root=args["model_store_root"], model_ref=model["model_ref"]
        )
        == model
    )
    assert len(list((args["model_store_root"] / "models").glob("*.json"))) == 1


def test_cold_provider_read_never_infers_or_reads_training_source(tmp_path, monkeypatch):
    args = setup_training(tmp_path)
    model = learner.train_market_ols_model_v1(**args)
    forecast_args, _ = next_forecast_args(tmp_path, model)
    result = learner.forecast_from_market_ols_model_v1(**forecast_args)
    for name in [
        "fit_ols_lstsq",
        "_extract",
        "mint_forecast_evidence_v1",
        "read_independent_market_calibration_v1",
    ]:
        monkeypatch.setattr(learner, name, forbidden)
    assert (
        learner.read_market_model_forecast_v1(
            model_store_root=args["model_store_root"],
            store_root=forecast_args["store_root"],
            job_key=result["frozen"]["job_key"],
        )
        == result
    )


def test_future_label_is_rejected_before_model_store_write(tmp_path):
    args = setup_training(tmp_path)
    cutoff = utc(learner.instant_v1(args["trained_as_of"]) - timedelta(seconds=11))
    with pytest.raises(ValueError, match="LABEL_NOT_AVAILABLE_AT_CUTOFF"):
        learner.train_market_ols_model_v1(
            **{**args, "trained_as_of": cutoff, "available_at": cutoff}
        )
    assert not args["model_store_root"].exists()


def test_same_original_outcome_in_different_forecasts_cannot_double_learn(tmp_path):
    args = setup_training(tmp_path)
    alternate = original_job(tmp_path / "mi", 0, mark=150)
    with pytest.raises(ValueError, match="DUPLICATE_EVIDENCE"):
        learner.train_market_ols_model_v1(
            **{**args, "evidence_jobs": args["evidence_jobs"] + [alternate]}
        )
    assert not args["model_store_root"].exists()


def test_model_cannot_cross_to_replacement_instrument_or_horizon(tmp_path):
    args = setup_training(tmp_path)
    model = learner.train_market_ols_model_v1(**args)
    next_args, _ = next_forecast_args(tmp_path, model)
    for change in ["instrument", "horizon"]:
        request = deepcopy(next_args["market_request"])
        if change == "instrument":
            request["market_identity"]["instrument_ref"] = "foreign.instrument"
            request["market_identity"]["native_instrument_ref"] = "FOREIGN-SWAP"
        else:
            request["n_bars"] += 1
        with pytest.raises(ValueError, match="MODEL_FORECAST_TARGET_OR_MARKET_MISMATCH"):
            learner.forecast_from_market_ols_model_v1(**{**next_args, "market_request": request})
    assert not next_args["store_root"].exists()


def test_parent_update_requires_new_evidence_and_preserves_old_bytes(tmp_path):
    args = setup_training(tmp_path)
    model = learner.train_market_ols_model_v1(**args)
    path = learner._model_path(args["model_store_root"], model["model_ref"])
    before = path.read_bytes()
    with pytest.raises(ValueError, match="REQUIRES_NEW_CUMULATIVE_EVIDENCE"):
        learner.train_market_ols_model_v1(**{**args, "parent_model_ref": model["model_ref"]})
    assert path.read_bytes() == before


def test_interrupted_artifact_to_receipt_recovers_without_refit(tmp_path, monkeypatch):
    args = setup_training(tmp_path)
    append = learner._append

    def interrupted(path, value):
        if path.name == "model_receipt.json":
            raise RuntimeError("SIMULATED_INTERRUPTED_RECEIPT")
        return append(path, value)

    monkeypatch.setattr(learner, "_append", interrupted)
    with pytest.raises(RuntimeError, match="SIMULATED_INTERRUPTED_RECEIPT"):
        learner.train_market_ols_model_v1(**args)
    paths = list((args["model_store_root"] / "models").glob("*.json"))
    assert len(paths) == 1
    before = paths[0].read_bytes()
    monkeypatch.setattr(learner, "_append", append)
    monkeypatch.setattr(learner, "fit_ols_lstsq", forbidden)
    recovered = learner.train_market_ols_model_v1(**args)
    assert recovered["model_ref"] == paths[0].stem
    assert paths[0].read_bytes() == before


def test_resealed_weight_tamper_cannot_keep_original_model_identity(tmp_path):
    args = setup_training(tmp_path)
    model = learner.train_market_ols_model_v1(**args)
    path = learner._model_path(args["model_store_root"], model["model_ref"])
    changed = deepcopy(model)
    changed.pop("exact_content_digest")
    changed["coefficients"]["mark"] += 1.0
    path.write_bytes(bytes_v1(seal_v1(changed)))
    with pytest.raises(ValueError, match="MODEL_NUMERIC_CONTENT_MISMATCH"):
        learner.read_market_ols_model_v1(
            model_store_root=args["model_store_root"], model_ref=model["model_ref"]
        )


def test_model_cold_read_in_fresh_process(tmp_path):
    args = setup_training(tmp_path)
    model = learner.train_market_ols_model_v1(**args)
    root = Path(__file__).resolve().parents[2]
    code = "from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import market_ols_next_forecast_v1 as m\nimport sys,json\nm.fit_ols_lstsq=lambda *a,**k: (_ for _ in ()).throw(AssertionError('REFIT_FORBIDDEN'))\nx=m.read_market_ols_model_v1(model_store_root=sys.argv[1],model_ref=sys.argv[2])\nprint(json.dumps(x))\n"
    completed = subprocess.run(
        [str(root / "scripts/pt"), "-", str(args["model_store_root"]), model["model_ref"]],
        input=code,
        text=True,
        cwd=root,
        capture_output=True,
        check=True,
    )
    assert json.loads(completed.stdout) == model


def test_resealed_forecast_numbers_cannot_keep_original_computation_job(tmp_path):
    args = setup_training(tmp_path)
    model = learner.train_market_ols_model_v1(**args)
    forecast_args, _ = next_forecast_args(tmp_path, model)
    result = learner.forecast_from_market_ols_model_v1(**forecast_args)
    job_key = result["frozen"]["job_key"]
    folder = forecast_args["store_root"] / ".intelligence-integration-v1" / digest_v1(job_key)
    receipt, frozen = deepcopy(result["provider"]), deepcopy(result["frozen"])
    receipt.pop("exact_content_digest")
    frozen.pop("exact_content_digest")
    receipt["computed_payload"]["mean_return"] += 1
    receipt["computation"]["computed_payload"]["mean_return"] += 1
    frozen["forecast_evidence"]["probabilistic_payload"] = receipt["computed_payload"]
    frozen["forecast_evidence"]["provenance"]["model_computation_digest"] = digest_v1(
        receipt["computation"]
    )
    frozen = seal_v1(frozen)
    receipt["frozen_digest"] = frozen["exact_content_digest"]
    (folder / "forecast.json").write_bytes(bytes_v1(frozen))
    (folder / "model_inference.json").write_bytes(bytes_v1(seal_v1(receipt)))
    with pytest.raises(ValueError, match="MODEL_PROVIDER_COMPUTATION_IDENTITY_MISMATCH"):
        learner.read_market_model_forecast_v1(
            model_store_root=args["model_store_root"],
            store_root=forecast_args["store_root"],
            job_key=job_key,
        )
