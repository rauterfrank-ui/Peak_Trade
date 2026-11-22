"""Existing measured-return admission must keep the original declared clock precision."""

import math
import socket

import pytest

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    validate_n_bars_measurement_artifacts_v1,
)
from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    mint_ddo_content_ref_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    measured_return_calibration_v1 as adapter,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    plain_v1,
)
from tests.learning.test_measured_return_calibration_v1 import _case


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Measured-return tests must not open a network connection")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def declared_evaluation_case(*, evaluated_at, final_close="2026-09-01T14:00:00Z"):
    """Rebind serialized declarations with original APIs, not source authenticity.

    The ordinary O4 fixture supplies whole-hour closes. A declared later close is
    counterevidence: recomputing its hashes cannot make evaluation before that
    close temporally valid or certify a new fractional O4 source observation.
    """
    case = plain_v1(_case())
    obs = case["evaluation_observation"]
    obs["bar_close_times_utc"][-1] = final_close
    obs["evaluation_time_utc"] = evaluated_at
    measurement = case["measurement_evidence"]
    measurement.update(
        bar_close_times_utc=list(obs["bar_close_times_utc"]), evaluation_time_utc=evaluated_at
    )
    measurement.pop("actual_outcome_ref")
    measurement["actual_outcome_ref"] = mint_ddo_content_ref_v1(
        prefix="ddo.outcome.measure.", payload=measurement
    )
    obs["actual_outcome_ref"] = measurement["actual_outcome_ref"]
    info = case["evaluation_information_set"]
    info.update(
        bar_close_times_utc=list(obs["bar_close_times_utc"]),
        evaluation_boundary_time_utc=evaluated_at,
    )
    info.pop("evaluation_time_information_set_ref")
    info["evaluation_time_information_set_ref"] = mint_ddo_content_ref_v1(
        prefix="ddo.eval_info_set.", payload=info
    )
    obs["evaluation_time_information_set_ref"] = info["evaluation_time_information_set_ref"]
    forecast = case["forecast_evidence"]
    forecast["provenance"]["measured_return_target_v1"]["return_end_close_time_utc"] = final_close
    case["forecast_evidence"] = mint_forecast_evidence_v1(
        information_set_ref=forecast["information_set_ref"],
        forecast_created_at_utc=forecast["forecast_created_at_utc"],
        outcome_horizon_end_utc=final_close,
        n_bars=forecast["n_bars"],
        bar_spec_ref=forecast["bar_spec_ref"],
        forecast_kind=forecast["forecast_kind"],
        probabilistic_payload=forecast["probabilistic_payload"],
        market_state_refs=forecast["market_state_refs"],
        forecast_model_ref=forecast["forecast_model_ref"],
        support_disposition=forecast["support_disposition"],
        provenance=forecast["provenance"],
        decision_event_ref=forecast["decision_event_ref"],
        selected_instrument_ref=forecast["selected_instrument_ref"],
        outcome_binding_mode=forecast["outcome_binding_mode"],
        drift_assessment_refs=forecast["drift_assessment_refs"],
    )
    validate_n_bars_measurement_artifacts_v1(obs, measurement, info)
    return case


@pytest.mark.parametrize("fraction", ["000000001", "000000999"])
@pytest.mark.parametrize("boundary", ["late_forecast", "early_evaluation"])
@pytest.mark.parametrize("entrypoint", ["prepare", "persist"])
def test_inconsistent_original_clock_stops_before_calibration_and_store(
    tmp_path, monkeypatch, fraction, boundary, entrypoint
):
    if boundary == "late_forecast":
        case = _case(forecast_created_at_utc=f"2026-09-01T12:00:00.{fraction}Z")
    else:
        case = declared_evaluation_case(
            evaluated_at="2026-09-01T14:00:00Z",
            final_close=f"2026-09-01T14:00:00.{fraction}Z",
        )
    original = bytes_v1(case)
    calls = []
    calibrate = adapter.build_calibration_evidence_v1
    persist = adapter.persist_mi_offline_durable_evidence_v1

    def calibration(**kwargs):
        calls.append("calibration")
        return calibrate(**kwargs)

    def persistence(*args, **kwargs):
        calls.append("persistence")
        return persist(*args, **kwargs)

    monkeypatch.setattr(adapter, "build_calibration_evidence_v1", calibration)
    monkeypatch.setattr(adapter, "persist_mi_offline_durable_evidence_v1", persistence)
    store = tmp_path / "unwritten"
    with pytest.raises(adapter.MeasuredReturnCalibrationError, match="KNOWLEDGE_TIME_MISMATCH"):
        if entrypoint == "prepare":
            adapter.prepare_explicit_measured_return_v1(**case)
        else:
            adapter.calibrate_explicit_measured_return_v1(**case, durable_store_root=store)
    assert calls == []
    assert not store.exists()
    assert bytes_v1(case) == original


@pytest.mark.parametrize("end", [110.0, 90.0])
@pytest.mark.parametrize(
    "created_at",
    [
        "2026-09-01T11:59:59.999999999Z",
        "2026-09-01T12:00:00Z",
        "2026-09-01T12:00:00.000000000Z",
    ],
)
def test_valid_forecast_boundary_retains_original_return_and_durable_readback(
    tmp_path, end, created_at
):
    case = _case(end, forecast_created_at_utc=created_at)
    original = bytes_v1(case)
    result = adapter.calibrate_explicit_measured_return_v1(**case, durable_store_root=tmp_path)
    numeric = adapter.read_measured_return_calibration_v1(
        durable_store_root=tmp_path,
        durable_evidence_id=result["persistence"]["durable_evidence_id"],
        forecast_evidence_id=result["forecast_evidence_id"],
        actual_outcome_ref=result["actual_outcome_ref"],
    )
    assert numeric["realized_return"] == math.log(end / 100)
    assert numeric["error"] == math.log(end / 100) - 0.02
    assert numeric == result["calibration_evidence"]["calibration_result"]
    replay = adapter.calibrate_explicit_measured_return_v1(**case, durable_store_root=tmp_path)
    assert replay["persistence"]["persist_status"] == "IDEMPOTENT_REPLAY"
    assert replay["calibration_evidence"] == result["calibration_evidence"]
    assert result["source_authenticated"] is False
    assert result["productive_apply_authorized"] is False
    assert result["model_training_performed"] is False
    assert bytes_v1(case) == original


@pytest.mark.parametrize("fraction", ["", ".000000000", ".000000001", ".000000999"])
def test_evaluation_at_or_after_original_close_remains_admissible(tmp_path, fraction):
    case = declared_evaluation_case(evaluated_at=f"2026-09-01T14:00:00{fraction}Z")
    original = bytes_v1(case)
    result = adapter.calibrate_explicit_measured_return_v1(**case, durable_store_root=tmp_path)
    assert result["persistence"]["persist_status"] == "APPENDED"
    assert result["calibration_evidence"]["calibration_result"]["realized_return"] == math.log(1.1)
    assert bytes_v1(case) == original


@pytest.mark.parametrize(
    "created_at",
    [
        "2026-09-01T12:00:00+00:00",
        "2026-09-01T12:00:00+01:00",
        "2026-09-01T12:00:00",
        "2026-09-01T12:00:00.0000000001Z",
    ],
)
def test_original_ddo_utc_syntax_is_not_broadened(created_at):
    with pytest.raises(DdoValidationError):
        _case(forecast_created_at_utc=created_at)
