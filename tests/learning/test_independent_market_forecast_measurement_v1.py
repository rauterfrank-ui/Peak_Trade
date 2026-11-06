"""Actual offline market → native measurement → calibration, without a decision."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import inspect

import pytest

from src.learning.deterministic_decision_outcome_v0 import (
    n_bars_bar_evidence_supplier_v1 as supplier,
)
from src.learning.deterministic_decision_outcome_v0 import independent_market_horizon_v1 as horizon
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    independent_market_forecast_measurement_v1 as integration,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
    compose_admitted_market_context_v1,
    replay_admitted_market_context_v1,
    compose_admitted_intelligence_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    freeze_existing_market_forecast_v1,
    freeze_existing_intelligence_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    IntelligenceIdentityV1,
    MarketIdentityV1,
    bytes_v1,
    digest_v1,
    seal_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from tests.learning.test_intelligence_context_admission_v1 import inputs

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "docs/ops/evidence/iu_sl_opt_concrete_origin_trace_2026_11_05/originals/mi_original_measurement.json"
)


def utc(dt):
    return dt.isoformat().replace("+00:00", "Z")


def case(*, generation="market.synthetic.1", corrected=False):
    raw = json.loads(SOURCE.read_text())
    assert hashlib.sha256(raw["original_utf8"].encode()).hexdigest() == raw["sha256"]
    original = json.loads(raw["original_utf8"])
    bars = deepcopy(original["snapshot"]["o4_bars"])
    first = bars[0]
    identity = MarketIdentityV1(
        generation, first["venue"], first["canonical_instrument_id"], first["venue_instrument_id"]
    )
    start = datetime.fromtimestamp(first["bar_open_time"], timezone.utc)
    as_of = start - timedelta(minutes=1)
    args = inputs()
    payload = deepcopy(args["request"].price_mark_fact.payload)
    payload["instrument"] = {
        "canonical_instrument_id": identity.instrument_ref,
        "venue": identity.venue,
        "venue_native_id": identity.native_instrument_ref,
    }
    event = start - timedelta(minutes=3)
    captured = utc(event + timedelta(seconds=61))
    payload["interval_start_ms"] = int(event.timestamp() * 1000)
    payload["timestamps"] = {"effective_at": utc(event), "captured_at": captured}
    fact = replace(
        args["request"].price_mark_fact, payload=payload, fact_digest=fact_digest(payload)
    )
    receipt = replace(
        next(iter(args["receipts_by_digest"].values())),
        dataset_generation=generation,
        payload_bytes=bytes_v1(payload),
        known_at=captured,
        available_at=captured,
        units={"price": "USDT_PER_ETH"},
    )
    context_args = {
        **args,
        "identity": identity,
        "request": replace(
            args["request"],
            observed_at=utc(as_of),
            instrument_ref=identity.instrument_ref,
            price_mark_fact=fact,
        ),
        "receipts_by_digest": {fact.fact_digest: receipt},
    }
    context = compose_admitted_market_context_v1(**context_args)
    if corrected:
        bars[-1]["revision"] = 1
        bars[-1]["finalization_state"] = bars[-1]["quality_state"] = "CORRECTED_BAR"
    request = {
        "schema_version": horizon.REQUEST_SCHEMA,
        "market_identity": identity.payload(),
        "horizon_start_time_utc": utc(start),
        "n_bars": len(bars),
        "o4_interval_id": "PT1H",
        "price_unit": "USDT_PER_ETH",
        "price_family": "MARK_PRICE",
        "source_kind": "SYNTHETIC_OFFLINE",
        "max_end_age_seconds": 1800,
        "expected_price_basis_kind": "O4_BAR_CLOSE_CORRECTED"
        if corrected
        else "O4_BAR_CLOSE_FINALIZED",
    }
    receipts = []
    for i, bar in enumerate(bars):
        text = bytes_v1(bar).decode()
        available = datetime.fromtimestamp(bar["bar_close_time"] + 1, timezone.utc)
        receipts.append(
            {
                "source_ref": f"TEST_ONLY_SYNTHETIC:preserved-e6-bar:{i}",
                "dataset_generation": generation,
                "source_kind": request["source_kind"],
                "price_unit": request["price_unit"],
                "price_family": request["price_family"],
                "original_bar_json": text,
                "original_bar_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "known_at_utc": utc(available),
                "available_at_utc": utc(available),
            }
        )
    target = horizon.build_independent_market_return_target_v1(request)
    forecast = mint_forecast_evidence_v1(
        information_set_ref=context["market_context"]["information_set_ref"],
        forecast_created_at_utc=utc(as_of),
        outcome_horizon_end_utc=target["return_end_close_time_utc"],
        n_bars=request["n_bars"],
        bar_spec_ref=target["bar_spec_ref"],
        forecast_kind="RETURN_DISTRIBUTION_SUMMARY",
        probabilistic_payload={"mean_return": 0.02, "std_return": 0.1},
        market_state_refs=[context["market_context"]["context_id"]],
        forecast_model_ref="TEST_ONLY_SUPPLIED_MODEL",
        support_disposition="SUFFICIENT_EVIDENCE",
        selected_instrument_ref=identity.instrument_ref,
        provenance={"TEST_ONLY_SYNTHETIC": True, "measured_return_target_v1": target},
    )
    artifact = b"TEST_ONLY_SYNTHETIC_MODEL_ARTIFACT; NO INFERENCE"
    freeze_args = {
        "context_package": context,
        "forecast_evidence": dict(forecast),
        "original_probabilistic_payload": bytes_v1(forecast["probabilistic_payload"]),
        "model_artifact_bytes": artifact,
        "attempt_generation": "attempt.1",
        "provider_admission": {
            "provider_ref": "TEST_ONLY_PROVIDER",
            "model_ref": forecast["forecast_model_ref"],
            "feature_schema_ref": "features.test",
            "training_dataset_ref": "training.synthetic",
            "validation_ref": "validation.synthetic",
            "admitted_by_ref": "TEST_ONLY_ADMISSION",
            "model_artifact_sha256": hashlib.sha256(artifact).hexdigest(),
            "training_end": "2026-05-01T00:00:00Z",
            "available_at": "2026-05-02T00:00:00Z",
            "context_package_digest": context["exact_content_digest"],
            "max_context_age_seconds": 0,
            "target_spec_digest": digest_v1(target),
        },
    }
    owner_args = {
        "request": request,
        "source_receipts": receipts,
        "evaluated_at_utc": utc(
            datetime.fromtimestamp(bars[-1]["bar_close_time"] + 2, timezone.utc)
        ),
    }
    return context_args, freeze_args, owner_args, original


def forbidden(*args, **kwargs):
    raise AssertionError("FORBIDDEN_DECISION_OR_RECOMPUTATION")


def test_complete_without_decision_original_measurement_and_cold_retry(tmp_path, monkeypatch):
    context_args, freeze_args, owner_args, original = case()
    monkeypatch.setattr(supplier, "validate_decision_event_v0", forbidden)
    before = deepcopy(owner_args)
    observation = supplier.materialize_independent_market_horizon_v1(**owner_args)
    assert owner_args == before
    assert observation["measurement"] == original["measurement"]
    assert (
        replay_admitted_market_context_v1(freeze_args["context_package"])
        == freeze_args["context_package"]
    )
    frozen = freeze_existing_market_forecast_v1(store_root=tmp_path, **freeze_args)
    assert not {"decision_event_ref", "lane_id", "epoch"} & set(frozen["job_key"])
    assert frozen["forecast_evidence"]["decision_event_ref"] is None
    ack = integration.calibrate_frozen_market_forecast_v1(
        store_root=tmp_path, frozen=frozen, market_observation=observation
    )
    assert ack["calibration_result"]["error"] == math.log(120 / 110) - 0.02
    assert ack["calibration_result"]["realized_return"] == original["measurement"]["log_return"]
    assert (
        integration.calibrate_frozen_market_forecast_v1(
            store_root=tmp_path, frozen=frozen, market_observation=observation
        )
        == ack
    )
    monkeypatch.setattr(integration, "_prepare", forbidden)
    monkeypatch.setattr(horizon, "_materialize_market_horizon_v1", forbidden)
    packet = integration.read_independent_market_calibration_v1(
        store_root=tmp_path, job_key=frozen["job_key"]
    )
    assert packet["calibration_ack"] == ack
    assert (
        packet["original_record"]["calibration_evidence"]["calibration_result"]
        == ack["calibration_result"]
    )


def mutate_bar(args, field, value):
    receipt = args["source_receipts"][-1]
    bar = json.loads(receipt["original_bar_json"])
    bar[field] = value
    receipt["original_bar_json"] = json.dumps(bar, sort_keys=True)
    receipt["original_bar_sha256"] = hashlib.sha256(
        receipt["original_bar_json"].encode()
    ).hexdigest()


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("close", True, "MARKET_FINITE_SOURCE_NUMBER"),
        ("close", 0, "MARKET_POSITIVE_CLOSE"),
        ("close", float("nan"), "NONFINITE_SOURCE_NUMBER"),
        ("venue", "foreign", "MARKET_SOURCE_ENTITY_MISMATCH"),
        ("venue_instrument_id", "foreign", "MARKET_SOURCE_ENTITY_MISMATCH"),
        ("canonical_instrument_id", "foreign", "MARKET_SOURCE_ENTITY_MISMATCH"),
        ("quality_state", "STALE_BAR", "MARKET_FINALIZED_COMPLETE_BAR"),
        ("finalization_state", "IN_PROGRESS_BAR", "MARKET_FINALIZED_COMPLETE_BAR"),
        ("bar_open_time", 0, "MARKET_OBSERVATION_OUTSIDE_BAR|MARKET_EXACT_HORIZON_GRID"),
        ("bar_close_time", 0, "MARKET_OBSERVATION_OUTSIDE_BAR|MARKET_EXACT_HORIZON_GRID"),
        ("interval", "PT1M", "MARKET_SOURCE_INTERVAL_MISMATCH"),
        ("revision", True, "MARKET_REVISION_REQUIRED"),
        ("config_digest", "foreign", "O4_PROVENANCE_CONFIG_DIGEST_MISMATCH"),
        ("session_id", None, "MARKET_SOURCE_PROVENANCE_REQUIRED"),
        ("repository_sha", "", "MARKET_SOURCE_PROVENANCE_REQUIRED"),
    ],
)
def test_bad_original_bar_never_becomes_measurement(field, value, reason):
    _, _, args, _ = case()
    mutate_bar(args, field, value)
    with pytest.raises((ValueError, DdoValidationError), match=reason):
        supplier.materialize_independent_market_horizon_v1(**args)


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("dataset_generation", "foreign", "MARKET_SOURCE_GENERATION_MISMATCH"),
        ("source_kind", "RECORDED_PUBLIC_MD", "MARKET_SOURCE_KIND_MISMATCH"),
        ("price_unit", "CONTRACTS", "MARKET_SOURCE_PRICE_UNIT"),
        ("price_family", "LAST_PRICE", "MARKET_SOURCE_PRICE_UNIT"),
        ("known_at_utc", "2026-01-01T00:00:00Z", "MARKET_FINAL_VALUE_NOT_AVAILABLE"),
        ("available_at_utc", "2027-01-01T00:00:00Z", "MARKET_FINAL_VALUE_NOT_AVAILABLE"),
        ("original_bar_sha256", "0" * 64, "MARKET_ORIGINAL_SOURCE_BYTES_CHANGED"),
        ("source_ref", "", "MARKET_SOURCE_REF_REQUIRED"),
    ],
)
def test_receipt_identity_time_units_and_bytes(field, value, reason):
    _, _, args, _ = case()
    args["source_receipts"][-1][field] = value
    with pytest.raises(ValueError, match=reason):
        supplier.materialize_independent_market_horizon_v1(**args)


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("n_bars", 1, "MARKET_RETURN_NEEDS_AT_LEAST_TWO_CLOSES"),
        ("n_bars", True, "MARKET_RETURN_NEEDS_AT_LEAST_TWO_CLOSES"),
        ("max_end_age_seconds", False, "MARKET_FRESHNESS_POLICY_REQUIRED"),
        ("max_end_age_seconds", 0, "MARKET_MEASUREMENT_STALE"),
        ("horizon_start_time_utc", "2026-09-17T07:00:01Z", "MARKET_EXACT_BAR_GRID_REQUIRED"),
        (
            "expected_price_basis_kind",
            "O4_BAR_CLOSE_CORRECTED",
            "MARKET_PRICE_BASIS_GENERATION_MISMATCH",
        ),
    ],
)
def test_explicit_request_and_no_defaults(field, value, reason):
    _, _, args, _ = case()
    args["request"][field] = value
    with pytest.raises(ValueError, match=reason):
        supplier.materialize_independent_market_horizon_v1(**args)


def test_incomplete_duplicate_and_forbidden_trading_identity():
    _, _, args, _ = case()
    for receipts in [args["source_receipts"][:1], [args["source_receipts"][0]] * 2]:
        with pytest.raises(
            ValueError, match="MARKET_COMPLETE_SOURCE_RECEIPTS|MARKET_DUPLICATE_SOURCE_REF"
        ):
            supplier.materialize_independent_market_horizon_v1(
                **{**args, "source_receipts": receipts}
            )
    args["request"]["market_identity"]["decision_event_ref"] = "not-a-market-identity"
    with pytest.raises(ValueError, match="MARKET_IDENTITY_FIELDS"):
        supplier.materialize_independent_market_horizon_v1(**args)


def test_forged_record_and_changed_retry_cannot_replace_original(tmp_path):
    _, freeze_args, args, _ = case()
    frozen = freeze_existing_market_forecast_v1(store_root=tmp_path, **freeze_args)
    observation = supplier.materialize_independent_market_horizon_v1(**args)
    forged = deepcopy(observation)
    forged["measurement"]["log_return"] = 999
    forged.pop("exact_content_digest")
    forged = seal_v1(forged)
    with pytest.raises(ValueError, match="MARKET_OBSERVATION_CONTENT_MISMATCH"):
        integration.calibrate_frozen_market_forecast_v1(
            store_root=tmp_path, frozen=frozen, market_observation=forged
        )
    assert not list(tmp_path.rglob("calibration_ack.json"))
    ack = integration.calibrate_frozen_market_forecast_v1(
        store_root=tmp_path, frozen=frozen, market_observation=observation
    )
    later = {
        **args,
        "evaluated_at_utc": utc(
            datetime.fromisoformat(args["evaluated_at_utc"].replace("Z", "+00:00"))
            + timedelta(seconds=1)
        ),
    }
    changed = supplier.materialize_independent_market_horizon_v1(**later)
    with pytest.raises(ValueError, match="IMMUTABLE_ATTACHMENT_CONFLICT"):
        integration.calibrate_frozen_market_forecast_v1(
            store_root=tmp_path, frozen=frozen, market_observation=changed
        )
    assert (
        integration.read_independent_market_calibration_v1(
            store_root=tmp_path, job_key=frozen["job_key"]
        )["calibration_ack"]
        == ack
    )


def test_source_generations_and_correction_are_separate_jobs(tmp_path):
    keys = []
    for generation, corrected in [("original.gen", False), ("corrected.gen", True)]:
        _, freeze_args, args, _ = case(generation=generation, corrected=corrected)
        frozen = freeze_existing_market_forecast_v1(store_root=tmp_path, **freeze_args)
        observation = supplier.materialize_independent_market_horizon_v1(**args)
        integration.calibrate_frozen_market_forecast_v1(
            store_root=tmp_path, frozen=frozen, market_observation=observation
        )
        keys.append(frozen["job_key"])
    assert keys[0] != keys[1]
    assert len(list(tmp_path.rglob("calibration_ack.json"))) == 2


def test_legacy_apis_keep_their_decision_requirement(tmp_path):
    context_args, freeze_args, _, _ = case()
    with pytest.raises(ValueError, match="DDO_CONTEXT_IDENTITY_REQUIRED"):
        compose_admitted_intelligence_context_v1(**context_args)
    with pytest.raises(ValueError, match="INTEGRATION_SCHEMA_MISMATCH"):
        freeze_existing_intelligence_forecast_v1(store_root=tmp_path, **freeze_args)


def test_fresh_process_reads_original_numbers_without_recomputation(tmp_path):
    _, freeze_args, args, _ = case()
    frozen = freeze_existing_market_forecast_v1(store_root=tmp_path, **freeze_args)
    observation = supplier.materialize_independent_market_horizon_v1(**args)
    ack = integration.calibrate_frozen_market_forecast_v1(
        store_root=tmp_path, frozen=frozen, market_observation=observation
    )
    code = f"""
import json
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import independent_market_forecast_measurement_v1 as m
def forbidden(*args, **kwargs): raise AssertionError("NO_RECOMPUTATION")
m._prepare = forbidden
m._build_calibration_from_validated_join_v1 = forbidden
packet=m.read_independent_market_calibration_v1(store_root={str(tmp_path)!r}, job_key=json.loads({json.dumps(frozen["job_key"])!r}))
print(json.dumps(packet['calibration_ack']))
"""
    completed = subprocess.run(
        [str(ROOT / "scripts/pt"), "-"],
        input=code,
        text=True,
        capture_output=True,
        check=True,
        cwd=ROOT,
    )
    assert json.loads(completed.stdout) == ack


def remint(freeze_args, request):
    target = horizon.build_independent_market_return_target_v1(request)
    old = freeze_args["forecast_evidence"]
    kwargs = {
        name: old[name]
        for name in inspect.signature(mint_forecast_evidence_v1).parameters
        if name in old
    }
    kwargs.update(
        n_bars=target["n_bars"],
        outcome_horizon_end_utc=target["return_end_close_time_utc"],
        provenance={"TEST_ONLY_SYNTHETIC": True, "measured_return_target_v1": target},
    )
    freeze_args["forecast_evidence"] = dict(mint_forecast_evidence_v1(**kwargs))
    freeze_args["provider_admission"]["target_spec_digest"] = digest_v1(target)


def test_explicit_three_closes_are_two_intervals_and_distinct_horizon(tmp_path):
    _, freeze_args, args, _ = case()
    first_key = freeze_existing_market_forecast_v1(store_root=tmp_path, **freeze_args)["job_key"]
    third = deepcopy(args["source_receipts"][-1])
    bar = json.loads(third["original_bar_json"])
    bar["bar_open_time"] += 3600
    bar["bar_close_time"] += 3600
    bar["last_observation_identity"]["venue_event_time"] += 3600
    bar["close"] = bar["last_observation_identity"]["mark_price"] = 132.0
    third.update(
        source_ref="TEST_ONLY_SYNTHETIC:third-bar",
        original_bar_json=bytes_v1(bar).decode(),
        original_bar_sha256=hashlib.sha256(bytes_v1(bar)).hexdigest(),
        known_at_utc=utc(datetime.fromtimestamp(bar["bar_close_time"] + 1, timezone.utc)),
        available_at_utc=utc(datetime.fromtimestamp(bar["bar_close_time"] + 1, timezone.utc)),
    )
    args["source_receipts"].append(third)
    args["request"]["n_bars"] = 3
    args["evaluated_at_utc"] = utc(datetime.fromtimestamp(bar["bar_close_time"] + 2, timezone.utc))
    remint(freeze_args, args["request"])
    frozen = freeze_existing_market_forecast_v1(store_root=tmp_path, **freeze_args)
    assert frozen["job_key"] != first_key
    observation = supplier.materialize_independent_market_horizon_v1(**args)
    assert len(observation["measurement"]["bar_close_times_utc"]) == 3
    assert observation["measurement"]["log_return"] == math.log(132 / 110)
    ack = integration.calibrate_frozen_market_forecast_v1(
        store_root=tmp_path, frozen=frozen, market_observation=observation
    )
    assert ack["calibration_result"]["error"] == math.log(132 / 110) - 0.02


def test_source_generation_target_and_context_units_cannot_be_relabelled(tmp_path):
    _, freeze_args, args, _ = case()
    frozen = freeze_existing_market_forecast_v1(store_root=tmp_path, **freeze_args)
    args["request"]["market_identity"]["dataset_generation"] = "foreign.generation"
    for receipt in args["source_receipts"]:
        receipt["dataset_generation"] = "foreign.generation"
    foreign = supplier.materialize_independent_market_horizon_v1(**args)
    with pytest.raises(ValueError, match="MARKET_MEASUREMENT_SOURCE_IDENTITY_MISMATCH"):
        integration.calibrate_frozen_market_forecast_v1(
            store_root=tmp_path, frozen=frozen, market_observation=foreign
        )
    _, freeze_args, args, _ = case()
    args["request"]["price_unit"] = "FOREIGN_UNIT"
    remint(freeze_args, args["request"])
    with pytest.raises(ValueError, match="MARKET_CONTEXT_MEASUREMENT_PRICE_UNIT_MISMATCH"):
        freeze_existing_market_forecast_v1(store_root=tmp_path / "foreign-unit", **freeze_args)
    assert not (tmp_path / "foreign-unit").exists()


def test_received_generation_detached_and_before_freeze_calibration_blocked(tmp_path):
    _, freeze_args, args, _ = case()
    observation = supplier.materialize_independent_market_horizon_v1(**args)
    original = deepcopy(observation)
    args["request"]["market_identity"]["dataset_generation"] = "caller.later"
    args["source_receipts"][0]["price_unit"] = "caller.later"
    assert observation == original
    assert horizon.validate_independent_market_horizon_v1(observation) == observation
    first = tmp_path / "original"
    frozen = freeze_existing_market_forecast_v1(store_root=first, **freeze_args)
    with pytest.raises(ValueError, match="MARKET_FORECAST_MUST_BE_FROZEN_FIRST"):
        integration.calibrate_frozen_market_forecast_v1(
            store_root=tmp_path / "unfrozen", frozen=frozen, market_observation=observation
        )
    assert not (tmp_path / "unfrozen").exists()


def test_market_path_cannot_acquire_a_decision_or_change_source_class(tmp_path):
    _, freeze_args, args, _ = case()
    freeze_args["forecast_evidence"]["decision_event_ref"] = "FAKE_DECISION_IS_NOT_ALLOWED"
    with pytest.raises(ValueError, match="MARKET_FORECAST_MUST_NOT_HAVE_DECISION"):
        freeze_existing_market_forecast_v1(store_root=tmp_path, **freeze_args)
    _, freeze_args, args, _ = case()
    args["request"]["source_kind"] = "RECORDED_PUBLIC_MD"
    remint(freeze_args, args["request"])
    with pytest.raises(ValueError, match="MARKET_FORECAST_SOURCE_KIND_MISMATCH"):
        freeze_existing_market_forecast_v1(store_root=tmp_path, **freeze_args)
    assert not tmp_path.joinpath(".intelligence-integration-v1").exists()


def test_existing_attributed_identity_subtypes_remain_accepted():
    class ExistingIdentitySubtype(IntelligenceIdentityV1):
        pass

    args = inputs()
    args["identity"] = ExistingIdentitySubtype(**args["identity"].payload())
    context = compose_admitted_intelligence_context_v1(**args)
    assert context["identity"] == args["identity"].payload()
