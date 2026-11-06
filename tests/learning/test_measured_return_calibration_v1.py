"""Measured supplier scalar reaches existing MI calibration without caller-made labels."""

from copy import deepcopy
import json
import math

import pytest
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    run_offline_n_bars_horizon_pipeline_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.measured_return_calibration_v1 import (
    MeasuredReturnCalibrationError,
    calibrate_explicit_measured_return_v1,
    read_measured_return_calibration_v1,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _snapshot, _decision


def _case(end=110.0, **overrides):
    snapshot = _snapshot()
    snapshot["o4_bars"][-1]["close"] = end
    pipe = run_offline_n_bars_horizon_pipeline_v1(
        _decision(), snapshot, outcome_scalar_kind="LOG_RETURN"
    )
    obs = pipe["evaluation_observation"]
    material = pipe["materialization"]
    measurement = material.measurement_evidence_artifact
    target = {
        "schema_version": "measured_return_forecast_target_v1",
        "price_basis_kind": measurement["price_basis_kind"],
        "outcome_scalar_kind": "LOG_RETURN",
        "instrument_ref": obs["instrument_ref"],
        "bar_spec_ref": obs["bar_spec_ref"],
        "n_bars": obs["n_bars"],
        "horizon_start_time_utc": obs["horizon_start_time_utc"],
        "return_start_close_time_utc": obs["bar_close_times_utc"][0],
        "return_end_close_time_utc": obs["bar_close_times_utc"][-1],
    }
    payload = dict(
        information_set_ref="forecast.info.TEST_ONLY_SYNTHETIC",
        forecast_created_at_utc="2026-09-01T12:00:00Z",
        outcome_horizon_end_utc="2026-09-01T14:00:00Z",
        n_bars=2,
        bar_spec_ref=obs["bar_spec_ref"],
        forecast_kind="RETURN_DISTRIBUTION_SUMMARY",
        probabilistic_payload={"mean_return": 0.02, "std_return": 0.1},
        market_state_refs=["market.state.TEST_ONLY_SYNTHETIC"],
        forecast_model_ref="forecast.model.TEST_ONLY_SYNTHETIC",
        support_disposition="SUFFICIENT_EVIDENCE",
        provenance={"TEST_ONLY_SYNTHETIC": True, "measured_return_target_v1": target},
        selected_instrument_ref=obs["instrument_ref"],
        decision_event_ref=obs["decision_event_ref"],
    )
    payload.update(overrides)
    forecast = mint_forecast_evidence_v1(**payload)
    return dict(
        forecast_evidence=forecast,
        evaluation_observation=obs,
        measurement_evidence=measurement,
        evaluation_information_set=material.evaluation_time_information_set_artifact,
    )


def test_measured_return_intervention_reaches_calibration_and_durable_numeric_reader(tmp_path):
    outputs = []
    for end in (110.0, 90.0):
        inputs = _case(end)
        before = deepcopy(dict(inputs["evaluation_observation"]))
        result = calibrate_explicit_measured_return_v1(
            **inputs, durable_store_root=tmp_path / str(end)
        )
        assert inputs["evaluation_observation"] == before
        numeric = result["calibration_evidence"]["calibration_result"]
        assert numeric["realized_return"] == math.log(end / 100)
        assert numeric["error"] == math.log(end / 100) - 0.02
        assert result["source_authenticated"] is False
        assert result["model_training_performed"] is False
        readback = read_measured_return_calibration_v1(
            durable_store_root=tmp_path / str(end),
            durable_evidence_id=result["persistence"]["durable_evidence_id"],
            forecast_evidence_id=result["forecast_evidence_id"],
            actual_outcome_ref=result["actual_outcome_ref"],
        )
        assert readback == numeric
        replay = calibrate_explicit_measured_return_v1(
            **inputs, durable_store_root=tmp_path / str(end)
        )
        assert replay["persistence"]["persist_status"] == "IDEMPOTENT_REPLAY"
        outputs.append(result)
    assert outputs[0]["forecast_evidence_id"] == outputs[1]["forecast_evidence_id"]
    assert (
        outputs[0]["calibration_evidence"]["calibration_result"]
        != outputs[1]["calibration_evidence"]["calibration_result"]
    )
    (tmp_path / "measured_return_intervention.json").write_text(
        json.dumps(outputs, indent=2) + "\n"
    )


@pytest.mark.parametrize(
    "kind",
    [
        "unspecified_target",
        "wrong_instrument",
        "wrong_decision",
        "late_forecast",
        "simple_return",
        "directional",
        "modelled",
    ],
)
def test_incompatible_forecast_target_is_rejected_before_persistence(tmp_path, kind):
    kwargs = {}
    if kind == "unspecified_target":
        kwargs["provenance"] = {"TEST_ONLY_SYNTHETIC": True}
    elif kind == "wrong_instrument":
        kwargs["selected_instrument_ref"] = "other.instrument"
    elif kind == "wrong_decision":
        kwargs["decision_event_ref"] = "other.decision"
    elif kind == "late_forecast":
        kwargs["forecast_created_at_utc"] = "2026-09-01T12:30:00Z"
    elif kind == "simple_return":
        original = _case()["forecast_evidence"]
        target = dict(original["provenance"]["measured_return_target_v1"])
        target["outcome_scalar_kind"] = "SIMPLE_RETURN"
        kwargs["provenance"] = {"measured_return_target_v1": target}
    elif kind == "directional":
        kwargs.update(
            forecast_kind="DIRECTIONAL_PROBABILITY",
            probabilistic_payload={"p_up": 0.5, "p_down": 0.3, "p_flat": 0.2},
        )
    elif kind == "modelled":
        kwargs["outcome_binding_mode"] = "MODELLED_COUNTERFACTUAL"
    inputs = _case(**kwargs)
    store = tmp_path / "not_created"
    with pytest.raises(MeasuredReturnCalibrationError):
        calibrate_explicit_measured_return_v1(**inputs, durable_store_root=store)
    assert not store.exists()


def test_measurement_tampering_cannot_become_a_calibration(tmp_path):
    inputs = _case()
    inputs["measurement_evidence"] = dict(inputs["measurement_evidence"], log_return=999.0)
    with pytest.raises(DdoValidationError, match="CONTENT_REF_MISMATCH"):
        calibrate_explicit_measured_return_v1(**inputs, durable_store_root=tmp_path / "unwritten")
    assert not (tmp_path / "unwritten").exists()


def test_durable_numeric_read_rejects_wrong_outcome_identity(tmp_path):
    inputs = _case()
    result = calibrate_explicit_measured_return_v1(**inputs, durable_store_root=tmp_path)
    with pytest.raises(MeasuredReturnCalibrationError, match="ENTITY_MISMATCH"):
        read_measured_return_calibration_v1(
            durable_store_root=tmp_path,
            durable_evidence_id=result["persistence"]["durable_evidence_id"],
            forecast_evidence_id=result["forecast_evidence_id"],
            actual_outcome_ref="other.outcome",
        )


@pytest.mark.parametrize("mean,std", [(float("nan"), 0.1), (0.02, -0.1), (True, 0.1)])
def test_invalid_numeric_forecast_cannot_create_durable_calibration(tmp_path, mean, std):
    inputs = _case(probabilistic_payload={"mean_return": mean, "std_return": std})
    with pytest.raises(MeasuredReturnCalibrationError):
        calibrate_explicit_measured_return_v1(**inputs, durable_store_root=tmp_path / "unwritten")
    assert not (tmp_path / "unwritten").exists()
