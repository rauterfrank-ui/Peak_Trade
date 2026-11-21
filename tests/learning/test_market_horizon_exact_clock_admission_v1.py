"""Original market receipts must be causal before return and calibration math."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import math

import pytest

from src.learning.deterministic_decision_outcome_v0 import independent_market_horizon_v1 as horizon
from src.learning.deterministic_decision_outcome_v0 import (
    n_bars_bar_evidence_supplier_v1 as supplier,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    independent_market_forecast_measurement_v1 as integration,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    freeze_existing_market_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    seal_v1,
)
from tests.learning.test_independent_market_forecast_measurement_v1 import case, remint, utc

VARIANTS = (
    "plain",
    "precise_receipts",
    "offset",
    "age_tie",
    "zero_age",
    "huge_age",
    "zero_grid",
    "reversed_receipts",
)


def _stamp(value, nanos, suffix="Z"):
    whole = datetime.fromisoformat(value.replace("Z", "+00:00")).replace(microsecond=0)
    return whole.isoformat(timespec="seconds").removesuffix("+00:00") + f".{nanos:09d}" + suffix


def _bar_close(receipt):
    return datetime.fromtimestamp(
        json.loads(receipt["original_bar_json"])["bar_close_time"], timezone.utc
    )


def _case(variant="plain", corrected=False):
    _, freeze, args, original = case(corrected=corrected)
    if variant == "precise_receipts":
        for receipt in args["source_receipts"]:
            stamp = _stamp(receipt["known_at_utc"], 123456789)
            receipt.update(known_at_utc=stamp, available_at_utc=stamp)
        args["evaluated_at_utc"] = _stamp(args["evaluated_at_utc"], 123456789)
    if variant == "offset":
        for receipt in args["source_receipts"]:
            for field in ("known_at_utc", "available_at_utc"):
                receipt[field] = receipt[field].replace("Z", "+00:00")
        args["evaluated_at_utc"] = args["evaluated_at_utc"].replace("Z", "+00:00")
    if variant == "age_tie":
        args["evaluated_at_utc"] = utc(
            _bar_close(args["source_receipts"][-1])
            + timedelta(seconds=args["request"]["max_end_age_seconds"])
        )
    if variant == "zero_age":
        for receipt in args["source_receipts"]:
            receipt.update(
                known_at_utc=utc(_bar_close(receipt)), available_at_utc=utc(_bar_close(receipt))
            )
        args["evaluated_at_utc"] = utc(_bar_close(args["source_receipts"][-1]))
        args["request"]["max_end_age_seconds"] = 0
    if variant == "huge_age":
        args["request"]["max_end_age_seconds"] = 10**20
    if variant == "zero_grid":
        args["request"]["horizon_start_time_utc"] = _stamp(
            args["request"]["horizon_start_time_utc"], 0
        )
    if variant == "reversed_receipts":
        args["source_receipts"].reverse()
    remint(freeze, args["request"])
    return freeze, args, original


def _contradict(args, fault, suffix):
    receipt = args["source_receipts"][-1]
    if fault == "knowledge":
        receipt["known_at_utc"] = _stamp(receipt["available_at_utc"], 2, suffix)
        receipt["available_at_utc"] = _stamp(receipt["available_at_utc"], 1, suffix)
    elif fault == "availability":
        receipt["available_at_utc"] = _stamp(args["evaluated_at_utc"], 1, suffix)
    else:
        boundary = utc(
            _bar_close(receipt) + timedelta(seconds=args["request"]["max_end_age_seconds"])
        )
        args["evaluated_at_utc"] = _stamp(boundary, 1, suffix)
    return "MARKET_MEASUREMENT_STALE" if fault == "age" else "MARKET_FINAL_VALUE_NOT_AVAILABLE"


def _forbidden(*args, **kwargs):
    pytest.fail("Contradictory market timing reached original return or calibration math")


@pytest.mark.parametrize("suffix", ["Z", "+00:00"])
@pytest.mark.parametrize("fault", ["knowledge", "availability", "age"])
def test_receipt_clock_contradictions_stop_before_native_return(monkeypatch, suffix, fault):
    _, args, _ = _case()
    reason = _contradict(args, fault, suffix)
    before = deepcopy(args)
    monkeypatch.setattr(horizon, "_materialize_canonical_n_bars_measurement_v1", _forbidden)
    with pytest.raises(ValueError, match=reason):
        supplier.materialize_independent_market_horizon_v1(**args)
    assert args == before


@pytest.mark.parametrize("entry", ["target", "measurement"])
def test_nanosecond_off_grid_request_is_not_rounded_into_an_hour(monkeypatch, entry):
    _, args, _ = _case()
    args["request"]["horizon_start_time_utc"] = _stamp(args["request"]["horizon_start_time_utc"], 1)
    monkeypatch.setattr(horizon, "_materialize_canonical_n_bars_measurement_v1", _forbidden)
    with pytest.raises(ValueError, match="MARKET_EXACT_BAR_GRID_REQUIRED"):
        if entry == "target":
            horizon.build_independent_market_return_target_v1(args["request"])
        else:
            supplier.materialize_independent_market_horizon_v1(**args)


@pytest.mark.parametrize("suffix", ["Z", "+00:00"])
@pytest.mark.parametrize("fault", ["knowledge", "availability", "age"])
def test_resealed_observation_rejects_before_calibration_or_attachment(
    tmp_path, monkeypatch, suffix, fault
):
    freeze, args, _ = _case()
    frozen = freeze_existing_market_forecast_v1(store_root=tmp_path, **freeze)
    observation = supplier.materialize_independent_market_horizon_v1(**args)
    changed = deepcopy(observation)
    reason = _contradict(changed, fault, suffix)
    changed.pop("exact_content_digest")
    changed = seal_v1(changed)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    monkeypatch.setattr(horizon, "_materialize_canonical_n_bars_measurement_v1", _forbidden)
    monkeypatch.setattr(integration, "_build_calibration_from_validated_join_v1", _forbidden)
    with pytest.raises(ValueError, match=reason):
        integration.calibrate_frozen_market_forecast_v1(
            store_root=tmp_path, frozen=frozen, market_observation=changed
        )
    assert {
        p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    } == before


@pytest.mark.parametrize("corrected", [False, True])
@pytest.mark.parametrize("variant", VARIANTS)
def test_valid_receipts_preserve_original_measurement_and_cold_read(
    tmp_path, monkeypatch, variant, corrected
):
    freeze, args, original = _case(variant, corrected)
    before = deepcopy(args)
    observation = supplier.materialize_independent_market_horizon_v1(**args)
    assert args == before
    assert observation["source_receipts"] == args["source_receipts"]
    assert observation["evaluated_at_utc"] == args["evaluated_at_utc"]
    assert observation["measurement"]["log_return"] == original["measurement"]["log_return"]
    assert (
        observation["measurement"]["evaluation_time_utc"]
        == observation["measurement"]["bar_close_times_utc"][-1]
    )
    assert not {"decision_event_ref", "lane_id", "epoch"} & set(observation["measurement"])
    assert (
        horizon.validate_independent_market_horizon_v1(json.loads(bytes_v1(observation)))
        == observation
    )
    frozen = freeze_existing_market_forecast_v1(store_root=tmp_path, **freeze)
    ack = integration.calibrate_frozen_market_forecast_v1(
        store_root=tmp_path, frozen=frozen, market_observation=observation
    )
    assert ack["calibration_result"]["error"] == math.log(120 / 110) - 0.02
    assert (
        integration.calibrate_frozen_market_forecast_v1(
            store_root=tmp_path, frozen=frozen, market_observation=observation
        )
        == ack
    )
    monkeypatch.setattr(horizon, "_materialize_market_horizon_v1", _forbidden)
    monkeypatch.setattr(integration, "_prepare", _forbidden)
    monkeypatch.setattr(integration, "_build_calibration_from_validated_join_v1", _forbidden)
    readback = integration.read_independent_market_calibration_v1(
        store_root=tmp_path, job_key=frozen["job_key"]
    )
    assert readback["measurement_inputs"]["market_observation"] == observation
    assert readback["calibration_ack"] == ack
