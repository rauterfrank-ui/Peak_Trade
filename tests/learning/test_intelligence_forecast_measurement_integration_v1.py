"""Exact original supplier → calibration → cold readback → separate typed SL/OPT."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta
import hashlib
import json
import math

import pytest

from tests.learning.test_intelligence_context_admission_v1 import inputs
from tests.learning.test_measured_return_calibration_v1 import _case
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
    compose_admitted_intelligence_context_v1,
    replay_admitted_intelligence_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    digest_v1,
    seal_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    freeze_existing_intelligence_forecast_v1,
    calibrate_frozen_intelligence_forecast_v1,
    handoff_calibrated_intelligence_evidence_v1,
    validate_forecast_numbers_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_store_v1 import (
    MiOfflineDurableEvidenceStoreV1,
)


def setup(*, mean=0.02, lane="LANE_1"):
    case = _case()
    forecast = case.pop("forecast_evidence")
    args = inputs()
    args["identity"] = replace(
        args["identity"],
        instrument_ref=forecast["selected_instrument_ref"],
        decision_event_ref=forecast["decision_event_ref"],
        lane_id=lane,
    )
    p = deepcopy(args["request"].price_mark_fact.payload)
    p["instrument"]["canonical_instrument_id"] = forecast["selected_instrument_ref"]
    as_of = datetime.fromisoformat(forecast["forecast_created_at_utc"].replace("Z", "+00:00"))
    event = as_of - timedelta(minutes=2)
    captured = (event + timedelta(seconds=61)).isoformat().replace("+00:00", "Z")
    p["interval_start_ms"] = int(event.timestamp() * 1000)
    p["timestamps"] = {
        "effective_at": event.isoformat().replace("+00:00", "Z"),
        "captured_at": captured,
    }
    from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest

    fact = replace(args["request"].price_mark_fact, payload=p, fact_digest=fact_digest(p))
    receipt = replace(
        next(iter(args["receipts_by_digest"].values())),
        payload_bytes=bytes_v1(p),
        known_at=captured,
        available_at=captured,
    )
    args["receipts_by_digest"] = {fact.fact_digest: receipt}
    args["request"] = replace(
        args["request"],
        observed_at=forecast["forecast_created_at_utc"],
        instrument_ref=forecast["selected_instrument_ref"],
        price_mark_fact=fact,
    )
    context = compose_admitted_intelligence_context_v1(**args)
    forecast = mint_forecast_evidence_v1(
        information_set_ref=context["market_context"]["information_set_ref"],
        forecast_created_at_utc=forecast["forecast_created_at_utc"],
        outcome_horizon_end_utc=forecast["outcome_horizon_end_utc"],
        n_bars=forecast["n_bars"],
        bar_spec_ref=forecast["bar_spec_ref"],
        forecast_kind=forecast["forecast_kind"],
        probabilistic_payload={"mean_return": mean, "std_return": 0.1},
        market_state_refs=[context["market_context"]["context_id"]],
        forecast_model_ref=forecast["forecast_model_ref"],
        support_disposition=forecast["support_disposition"],
        provenance=forecast["provenance"],
        selected_instrument_ref=forecast["selected_instrument_ref"],
        decision_event_ref=forecast["decision_event_ref"],
    )
    artifact = b"TEST_ONLY_SYNTHETIC_MODEL_ARTIFACT; NO INFERENCE"
    admission = {
        "provider_ref": "synthetic.provider",
        "max_context_age_seconds": 0,
        "model_ref": forecast["forecast_model_ref"],
        "feature_schema_ref": "features.test",
        "training_dataset_ref": "training.synthetic",
        "validation_ref": "validation.synthetic",
        "admitted_by_ref": "TEST_ONLY_SYNTHETIC_ADMISSION",
        "model_artifact_sha256": hashlib.sha256(artifact).hexdigest(),
        "training_end": "2026-05-01T00:00:00Z",
        "available_at": "2026-05-02T00:00:00Z",
        "context_package_digest": context["exact_content_digest"],
        "target_spec_digest": digest_v1(forecast["provenance"]["measured_return_target_v1"]),
    }
    return dict(
        context_package=context,
        forecast_evidence=forecast,
        original_probabilistic_payload=bytes_v1(forecast["probabilistic_payload"]),
        provider_admission=admission,
        model_artifact_bytes=artifact,
        attempt_generation="attempt.1",
    ), case


def measure(root, frozen, case):
    return calibrate_frozen_intelligence_forecast_v1(
        store_root=root,
        frozen=frozen,
        **case,
        measurement_generation=frozen["job_key"]["dataset_generation"],
        measurement_available_at=case["evaluation_observation"]["evaluation_time_utc"],
    )


def test_actual_original_numeric_readback_typed_handoffs_and_retry(tmp_path):
    args, case = setup()
    frozen = freeze_existing_intelligence_forecast_v1(store_root=tmp_path / "mi", **args)
    before = deepcopy(case)
    ack = measure(tmp_path / "mi", frozen, case)
    assert case == before
    assert ack["calibration_result"]["error"] == math.log(1.1) - 0.02
    assert measure(tmp_path / "mi", json.loads(bytes_v1(frozen)), case) == ack
    handoff = handoff_calibrated_intelligence_evidence_v1(
        store_root=tmp_path / "mi",
        learning_store_root=tmp_path / "sl",
        frozen=frozen,
        calibration_ack=ack,
    )
    assert (
        handoff["learning_export"]["consumer_route"]["consumer_route"]
        == "MI_TYPED_LEARNING_EVIDENCE_ONLY"
    )
    original = MiOfflineDurableEvidenceStoreV1(tmp_path / "mi").get(ack["durable_evidence_id"])
    assert (
        handoff["learning_export"]["mi_learning_evidence"]["calibration_evidence_id"]
        == original["calibration_evidence"]["calibration_evidence_id"]
    )
    assert handoff["optimization_intake_ack"]["optimization_productive_authority"] == "NONE"
    assert handoff["numeric_feature_consumption_proven"] is False
    assert handoff == handoff_calibrated_intelligence_evidence_v1(
        store_root=tmp_path / "mi",
        learning_store_root=tmp_path / "sl",
        frozen=frozen,
        calibration_ack=ack,
    )
    assert len(MiOfflineDurableEvidenceStoreV1(tmp_path / "mi").list_records()) == 1


def test_exact_payload_distinguishes_legacy_normalization_aliases(tmp_path):
    left, _ = setup(mean=0.10000000000001)
    right, _ = setup(mean=0.10000000000002)
    assert (
        left["forecast_evidence"]["forecast_evidence_id"]
        == right["forecast_evidence"]["forecast_evidence_id"]
    )
    freeze_existing_intelligence_forecast_v1(store_root=tmp_path, **left)
    with pytest.raises(ValueError, match="ATTACHMENT_CONFLICT"):
        freeze_existing_intelligence_forecast_v1(store_root=tmp_path, **right)


def test_equal_n_in_distinct_lanes_never_aliases_jobs(tmp_path):
    keys = []
    for lane in ("LANE_1", "LANE_2"):
        args, case = setup(lane=lane)
        frozen = freeze_existing_intelligence_forecast_v1(store_root=tmp_path, **args)
        keys.append(frozen["job_key"])
        measure(tmp_path, frozen, case)
    assert keys[0] != keys[1]
    assert (
        len(list((tmp_path / ".intelligence-integration-v1").glob("*/calibration_ack.json"))) == 2
    )


def test_tampered_refs_reject_even_though_old_native_digest_is_unchanged(tmp_path):
    args, _ = setup()
    native = dict(args["forecast_evidence"])
    old = native["content_digest"]
    native["decision_event_ref"] = "foreign.decision"
    args["forecast_evidence"] = native
    assert native["content_digest"] == old
    with pytest.raises(ValueError, match="DECISION_MISMATCH"):
        freeze_existing_intelligence_forecast_v1(store_root=tmp_path, **args)
    assert not (tmp_path / ".intelligence-integration-v1").exists()


def test_invalid_measurement_cannot_pin_prepared_input_or_write_original_store(tmp_path):
    args, case = setup()
    frozen = freeze_existing_intelligence_forecast_v1(store_root=tmp_path, **args)
    bad = deepcopy(case)
    bad["measurement_evidence"] = dict(bad["measurement_evidence"], log_return=999)
    with pytest.raises(Exception, match="CONTENT_REF_MISMATCH"):
        measure(tmp_path, frozen, bad)
    assert not list((tmp_path / ".intelligence-integration-v1").glob("*/measurement.json"))
    assert not MiOfflineDurableEvidenceStoreV1(tmp_path).list_records()
    measure(tmp_path, frozen, case)


def test_resealed_derived_value_is_recomputed_from_original_source(tmp_path):
    args, _ = setup()
    context = dict(args["context_package"])
    context.pop("exact_content_digest")
    context = deepcopy(context)
    next(iter(context["derivations"].values()))["mark_px"] = "999"
    args["context_package"] = seal_v1(context)
    with pytest.raises(ValueError, match="CONTEXT_REPLAY_MISMATCH"):
        freeze_existing_intelligence_forecast_v1(store_root=tmp_path, **args)


def test_post_store_pre_ack_recovery_reuses_original_numeric_record(tmp_path, monkeypatch):
    import src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 as module

    args, case = setup()
    frozen = freeze_existing_intelligence_forecast_v1(store_root=tmp_path, **args)
    append = module._append

    def interrupted(path, value):
        if path.name == "calibration_ack.json":
            raise RuntimeError("SIMULATED_INTERRUPTION")
        return append(path, value)

    with monkeypatch.context() as m:
        m.setattr(module, "_append", interrupted)
        with pytest.raises(RuntimeError, match="SIMULATED_INTERRUPTION"):
            measure(tmp_path, frozen, case)
    assert len(MiOfflineDurableEvidenceStoreV1(tmp_path).list_records()) == 1
    ack = measure(tmp_path, frozen, case)
    assert ack["calibration_result"]["error"] == math.log(1.1) - 0.02
    assert len(MiOfflineDurableEvidenceStoreV1(tmp_path).list_records()) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"p_up": -0.1, "p_down": 1.1, "p_flat": 0},
        {"p_up": True, "p_down": 0, "p_flat": 0},
        {"p_up": float("nan"), "p_down": 0, "p_flat": 0},
    ],
)
def test_sum_one_does_not_override_component_domain(payload):
    with pytest.raises(ValueError):
        validate_forecast_numbers_v1(
            {"forecast_kind": "DIRECTIONAL_PROBABILITY", "probabilistic_payload": payload}
        )


def test_fresh_process_reads_original_numbers_without_running_provider_or_calibration(tmp_path):
    import subprocess
    from pathlib import Path

    args, case = setup()
    frozen = freeze_existing_intelligence_forecast_v1(store_root=tmp_path, **args)
    ack = measure(tmp_path, frozen, case)
    launcher = Path(__file__).resolve().parents[2] / "scripts/pt"
    code = """import json,sys
import src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 as m
def forbidden(*args,**kwargs):raise RuntimeError("MUST_NOT_CALIBRATE")
m.calibrate_explicit_measured_return_v1=forbidden
x=m.read_calibrated_intelligence_v1(store_root=sys.argv[1],job_key=json.loads(sys.argv[2]))
print("READBACK_JSON="+json.dumps(x["calibration_ack"]["calibration_result"],sort_keys=True))
"""
    result = subprocess.run(
        [str(launcher), "-c", code, str(tmp_path), json.dumps(frozen["job_key"])],
        cwd=launcher.parents[1],
        capture_output=True,
        text=True,
        check=True,
    )
    line = next(l for l in result.stdout.splitlines() if l.startswith("READBACK_JSON="))
    assert json.loads(line.removeprefix("READBACK_JSON=")) == ack["calibration_result"]


def test_stale_forecast_context_and_foreign_learning_recipient_do_not_write(tmp_path):
    args, case = setup()
    bad = {**args, "provider_admission": deepcopy(args["provider_admission"])}
    # The original ForecastEvidence hash excludes this new admission policy.
    bad["provider_admission"]["max_context_age_seconds"] = None
    with pytest.raises(ValueError, match="FRESHNESS_POLICY_REQUIRED"):
        freeze_existing_intelligence_forecast_v1(store_root=tmp_path / "never", **bad)
    assert not (tmp_path / "never").exists()
    frozen = freeze_existing_intelligence_forecast_v1(store_root=tmp_path / "mi", **args)
    ack = measure(tmp_path / "mi", frozen, case)
    handoff_calibrated_intelligence_evidence_v1(
        store_root=tmp_path / "mi",
        learning_store_root=tmp_path / "sl",
        frozen=frozen,
        calibration_ack=ack,
    )
    with pytest.raises(ValueError, match="LEARNING_RECIPIENT_CONFLICT"):
        handoff_calibrated_intelligence_evidence_v1(
            store_root=tmp_path / "mi",
            learning_store_root=tmp_path / "foreign",
            frozen=frozen,
            calibration_ack=ack,
        )
    assert not (tmp_path / "foreign").exists()
