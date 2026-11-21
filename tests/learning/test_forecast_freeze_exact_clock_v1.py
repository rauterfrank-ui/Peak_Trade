"""Exact chronology before immutable forecast and measurement publication."""

from copy import deepcopy
from dataclasses import replace
import inspect
import json

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    forecast_measurement_integration_v1 as integration,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
    ContextAdmissionPolicyV1,
    FactAdmissionReceiptV1,
    compose_admitted_intelligence_context_v1,
    compose_admitted_market_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_existing_fact_materialization_v1 import (
    ExistingFactMaterializationRequestV1,
    GovernedCanonicalFactV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    IntelligenceIdentityV1,
    bytes_v1,
    plain_v1,
    digest_v1,
    instant_v1,
)
from tests.learning.test_independent_market_forecast_measurement_v1 import case as market_case
from tests.learning.test_intelligence_forecast_measurement_integration_v1 import setup

MODES = ("attributed", "market")
VARIANTS = ("plain", "provider_tie", "offset", "huge_age", "horizon_tie", "zero_fraction_end")


def _stamp(value, nanos, suffix="Z"):
    whole = instant_v1(value).replace(microsecond=0).isoformat(timespec="seconds")
    return whole.removesuffix("+00:00") + f".{nanos:09d}" + suffix


def _remint(args, **changes):
    forecast = dict(args["forecast_evidence"])
    forecast.update(changes)
    fields = inspect.signature(mint_forecast_evidence_v1).parameters
    args["forecast_evidence"] = plain_v1(
        mint_forecast_evidence_v1(**{key: forecast[key] for key in fields})
    )


def _case(mode, variant="plain", suffix="Z"):
    args = market_case()[1] if mode == "market" else setup()[0]
    args["forecast_evidence"] = plain_v1(args["forecast_evidence"])
    admission = args["provider_admission"]
    if variant in {"provider_tie", "offset"}:
        stamp = _stamp(admission["available_at"], 123456789, suffix)
        admission.update(training_end=stamp, available_at=stamp)
    if variant == "huge_age":
        admission["max_context_age_seconds"] = 10**20
    if variant == "horizon_tie":
        target = args["forecast_evidence"]["provenance"]["measured_return_target_v1"]
        admission["max_context_age_seconds"] = int(
            (
                instant_v1(target["horizon_start_time_utc"])
                - instant_v1(args["context_package"]["as_of"])
            ).total_seconds()
        )
        _remint(args, forecast_created_at_utc=target["horizon_start_time_utc"])
    if variant == "zero_fraction_end":
        _remint(
            args,
            outcome_horizon_end_utc=_stamp(args["forecast_evidence"]["outcome_horizon_end_utc"], 0),
        )
    return args


def _freeze(mode, root, args):
    freeze = (
        integration.freeze_existing_market_forecast_v1
        if mode == "market"
        else integration.freeze_existing_intelligence_forecast_v1
    )
    return freeze(store_root=root, **args)


def _forbidden(*args, **kwargs):
    pytest.fail("Contradictory chronology reached the original lease/write boundary")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize(
    "fault,reason",
    [
        ("training", "MODEL_KNOWLEDGE_LOOKAHEAD"),
        ("publication", "MODEL_KNOWLEDGE_LOOKAHEAD"),
        ("context", "FORECAST_KNOWLEDGE_LOOKAHEAD"),
        ("age", "PROVIDER_CONTEXT_STALE_AT_FORECAST"),
        ("horizon", "FORECAST_KNOWLEDGE_LOOKAHEAD"),
        ("end", "FORECAST_TARGET_TIME_MISMATCH"),
    ],
)
def test_fractional_freeze_contradictions_stop_before_any_store(
    tmp_path, monkeypatch, mode, fault, reason
):
    args = _case(mode)
    admission = args["provider_admission"]
    if fault == "training":
        admission["training_end"] = _stamp(admission["available_at"], 2)
        admission["available_at"] = _stamp(admission["available_at"], 1, "+00:00")
    elif fault == "publication":
        admission["available_at"] = _stamp(args["context_package"]["as_of"], 1)
    elif fault == "context":
        # Rebuild a later native context from the original admitted source bytes.
        if mode == "market":
            context_args = market_case()[0]
        else:
            original = args["context_package"]
            binding = original["source_bindings"][0]
            fact = GovernedCanonicalFactV1(
                binding["fact_kind"],
                binding["fact_digest"],
                binding["payload"],
                binding["producer_owner"],
            )
            context_args = dict(
                identity=IntelligenceIdentityV1(**original["identity"]),
                request=ExistingFactMaterializationRequestV1(
                    original["as_of"],
                    original["identity"]["instrument_ref"],
                    original["market_context"]["provenance_refs"],
                    price_mark_fact=fact,
                ),
                receipts_by_digest={
                    fact.fact_digest: FactAdmissionReceiptV1(
                        binding["source_ref"],
                        binding["dataset_generation"],
                        binding["original_payload_json"].encode(),
                        binding["known_at"],
                        binding["available_at"],
                        binding["units"],
                    )
                },
                policy=ContextAdmissionPolicyV1(**original["admission_policy"]),
            )
        context_args["request"] = replace(
            context_args["request"], observed_at=_stamp(args["context_package"]["as_of"], 1)
        )
        context_args["policy"] = replace(
            context_args["policy"],
            max_age_seconds_by_role={
                role: seconds + 1
                for role, seconds in context_args["policy"].max_age_seconds_by_role.items()
            },
        )
        compose = (
            compose_admitted_market_context_v1
            if mode == "market"
            else compose_admitted_intelligence_context_v1
        )
        context = compose(**context_args)
        args["context_package"] = context
        admission["context_package_digest"] = context["exact_content_digest"]
        _remint(
            args,
            information_set_ref=context["market_context"]["information_set_ref"],
            market_state_refs=[context["market_context"]["context_id"]],
        )
    elif fault == "age":
        _remint(args, forecast_created_at_utc=_stamp(args["context_package"]["as_of"], 1))
    elif fault == "horizon":
        target = args["forecast_evidence"]["provenance"]["measured_return_target_v1"]
        admission["max_context_age_seconds"] = 3600
        _remint(args, forecast_created_at_utc=_stamp(target["horizon_start_time_utc"], 1))
    else:
        _remint(
            args,
            outcome_horizon_end_utc=_stamp(args["forecast_evidence"]["outcome_horizon_end_utc"], 1),
        )
    monkeypatch.setattr(integration, "_lease", _forbidden)
    root = tmp_path / "never-created"
    with pytest.raises(ValueError, match=reason):
        _freeze(mode, root, args)
    assert not root.exists()


@pytest.mark.parametrize("suffix", ["Z", "+00:00"])
def test_measurement_after_evaluation_stops_before_lease(tmp_path, monkeypatch, suffix):
    args, measurement = setup()
    frozen = _freeze("attributed", tmp_path, args)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    available = _stamp(measurement["evaluation_observation"]["evaluation_time_utc"], 1, suffix)
    monkeypatch.setattr(integration, "_lease", _forbidden)
    with pytest.raises(ValueError, match="MEASUREMENT_NOT_AVAILABLE_AT_EVALUATION"):
        integration.calibrate_frozen_intelligence_forecast_v1(
            store_root=tmp_path,
            frozen=frozen,
            **measurement,
            measurement_generation=frozen["job_key"]["dataset_generation"],
            measurement_available_at=available,
        )
    assert {
        p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    } == before


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("variant", VARIANTS)
def test_valid_clocks_preserve_full_frozen_record_and_immutable_retry(
    tmp_path, monkeypatch, mode, variant
):
    args = _case(mode, variant, suffix="+00:00" if variant == "offset" else "Z")
    before = deepcopy(args)
    frozen = _freeze(mode, tmp_path, args)
    assert args == before
    assert frozen["provider_admission"] == args["provider_admission"]
    assert frozen["forecast_evidence"] == json.loads(bytes_v1(args["forecast_evidence"]))
    path = (
        tmp_path / ".intelligence-integration-v1" / digest_v1(frozen["job_key"]) / "forecast.json"
    )
    stored = path.read_bytes()
    assert json.loads(stored) == frozen
    assert _freeze(mode, tmp_path, args) == frozen
    assert path.read_bytes() == stored
    monkeypatch.setattr(integration, "_freeze_existing_forecast_v1", _forbidden)
    if mode == "market":
        assert (
            integration.read_frozen_market_forecast_v1(
                store_root=tmp_path, job_key=frozen["job_key"]
            )
            == frozen
        )
    else:
        assert integration._read(path, integration.FROZEN_SCHEMA) == frozen


@pytest.mark.parametrize("suffix", ["Z", "+00:00"])
def test_equal_measurement_availability_keeps_original_receipt_and_cold_read(
    tmp_path, monkeypatch, suffix
):
    args, measurement = setup()
    frozen = _freeze("attributed", tmp_path, args)
    available = _stamp(measurement["evaluation_observation"]["evaluation_time_utc"], 0, suffix)
    ack = integration.calibrate_frozen_intelligence_forecast_v1(
        store_root=tmp_path,
        frozen=frozen,
        **measurement,
        measurement_generation=frozen["job_key"]["dataset_generation"],
        measurement_available_at=available,
    )
    monkeypatch.setattr(integration, "calibrate_explicit_measured_return_v1", _forbidden)
    packet = integration.read_calibrated_intelligence_v1(
        store_root=tmp_path, job_key=frozen["job_key"]
    )
    assert packet["measurement_inputs"]["measurement_available_at"] == available
    assert packet["calibration_ack"] == ack
