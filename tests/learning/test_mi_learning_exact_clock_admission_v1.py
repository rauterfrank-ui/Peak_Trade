"""Native outcome identity and typed learning chronology before calculation/write."""

from copy import deepcopy
from datetime import datetime, timedelta
import inspect
import json

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    calibration_evidence_v1 as calibration,
    forecast_outcome_join_v1 as joiner,
    mi_to_learning_evidence_bridge_v1 as bridge,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    plain_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_ingest_v1 import (
    MiLearningEvidenceIngestRequestV1,
    ingest_mi_learning_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_learning_export_v1 import (
    export_mi_learning_evidence_onto_learning_path_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_store_v1 import (
    MiLearningEvidenceStoreV1,
)
from tests.learning.test_unified_blueprint_phase_8_mi_to_learning_integration_v1 import (
    _mint_forecast,
    _observation_for_n,
)

VARIANTS = ("plain", "zero_fraction", "later_evaluation", "missing", "insufficient", "supplied")


def _stamp(value, nanos):
    return value.removesuffix("Z").split(".", 1)[0] + f".{nanos:09d}Z"


def _remint(forecast, **changes):
    raw = {**forecast, **changes}
    fields = inspect.signature(mint_forecast_evidence_v1).parameters
    return plain_v1(mint_forecast_evidence_v1(**{field: raw.get(field) for field in fields}))


def _case(n_bars=2, variant="plain"):
    observation = plain_v1(_observation_for_n(n_bars=n_bars))
    forecast = plain_v1(_mint_forecast(n_bars=n_bars, bar_spec_ref=observation["bar_spec_ref"]))
    if variant == "zero_fraction":
        forecast = _remint(
            forecast, outcome_horizon_end_utc=_stamp(forecast["outcome_horizon_end_utc"], 0)
        )
    if variant == "later_evaluation":
        later = datetime.fromisoformat(
            observation["evaluation_time_utc"].replace("Z", "+00:00")
        ) + timedelta(hours=2)
        observation["evaluation_time_utc"] = later.isoformat().replace("+00:00", "Z")
    if variant == "missing":
        observation = None
    if variant == "insufficient":
        forecast = _remint(forecast, support_disposition="INSUFFICIENT_EVIDENCE")
    args = dict(
        forecast_evidence=forecast, evaluation_observation=observation, realized_direction="UP"
    )
    original_calibration = calibration.build_calibration_evidence_v1(
        **args,
        provenance={"original.source": "synthetic.native.calibration"}
        if variant == "supplied"
        else None,
    )
    if variant == "supplied":
        args["calibration_evidence"] = plain_v1(original_calibration)
    return args, plain_v1(original_calibration)


def _forbidden(*args, **kwargs):
    pytest.fail("Inconsistent MI timing reached the original next consumer")


def _invoke(entry, args, root):
    if entry == "join":
        return joiner.join_forecast_to_n_bars_outcome_v1(
            forecast_evidence=args["forecast_evidence"],
            evaluation_observation=args["evaluation_observation"],
        )
    if entry == "calibration":
        return calibration.build_calibration_evidence_v1(**args)
    if entry == "bridge":
        return bridge.compose_mi_to_learning_evidence_v1(**args)
    return ingest_mi_learning_evidence_v1(root, MiLearningEvidenceIngestRequestV1(**args))


@pytest.mark.parametrize("entry", ["join", "calibration", "bridge", "ingest"])
@pytest.mark.parametrize("nanos", [1, 999])
def test_fractional_forecast_end_cannot_alias_original_last_close(
    tmp_path, monkeypatch, entry, nanos
):
    # Later evaluation remains legal, but cannot replace the actual last-close target.
    args, _ = _case(variant="later_evaluation")
    args["forecast_evidence"] = _remint(
        args["forecast_evidence"],
        outcome_horizon_end_utc=_stamp(args["forecast_evidence"]["outcome_horizon_end_utc"], nanos),
    )
    before = deepcopy(args)
    monkeypatch.setattr(calibration, "_build_calibration_from_validated_join_v1", _forbidden)
    monkeypatch.setattr(MiLearningEvidenceStoreV1, "append", _forbidden)
    root = tmp_path / "never-created"
    with pytest.raises(ValueError, match="FORECAST_OUTCOME_HORIZON_END_MISMATCH"):
        _invoke(entry, args, root)
    assert args == before
    assert not root.exists()


@pytest.mark.parametrize("entry", ["bridge", "ingest"])
@pytest.mark.parametrize("nanos", [1, 999])
def test_fractional_forecast_after_horizon_start_stops_before_join(
    tmp_path, monkeypatch, entry, nanos
):
    args, _ = _case()
    args["forecast_evidence"] = _remint(
        args["forecast_evidence"],
        forecast_created_at_utc=_stamp(
            args["evaluation_observation"]["horizon_start_time_utc"], nanos
        ),
    )
    before = deepcopy(args)
    monkeypatch.setattr(bridge, "join_forecast_to_n_bars_outcome_v1", _forbidden)
    monkeypatch.setattr(MiLearningEvidenceStoreV1, "append", _forbidden)
    root = tmp_path / "never-created"
    with pytest.raises(ValueError, match="HORIZON_START_BEFORE_FORECAST"):
        _invoke(entry, args, root)
    assert args == before
    assert not root.exists()


@pytest.mark.parametrize("n_bars", [2, 3])
@pytest.mark.parametrize("variant", VARIANTS)
def test_valid_native_packets_keep_calibration_export_and_cold_store(
    tmp_path, monkeypatch, n_bars, variant
):
    args, original_calibration = _case(n_bars, variant)
    before = deepcopy(args)
    record = bridge.compose_mi_to_learning_evidence_v1(**args)
    assert args == before
    assert record["calibration_evidence_id"] == original_calibration["calibration_evidence_id"]
    assert record["calibration_evidence_digest"] == original_calibration["content_digest"]
    assert record["forecast_created_at_utc"] == args["forecast_evidence"]["forecast_created_at_utc"]
    assert record["outcome_horizon_end_utc"] == args["forecast_evidence"]["outcome_horizon_end_utc"]
    assert record["evaluability"] == (
        "NOT_EVALUABLE"
        if variant == "missing"
        else "INSUFFICIENT_EVIDENCE"
        if variant == "insufficient"
        else "SUFFICIENT_EVIDENCE"
    )
    store = MiLearningEvidenceStoreV1(tmp_path)
    assert store.append(record) == record
    original_bytes = {
        p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    }
    assert store.append(record) == record
    assert {
        p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    } == original_bytes
    monkeypatch.setattr(bridge, "compose_mi_to_learning_evidence_v1", _forbidden)
    monkeypatch.setattr(calibration, "build_calibration_evidence_v1", _forbidden)
    cold = MiLearningEvidenceStoreV1(tmp_path).get(record["mi_learning_evidence_id"])
    assert cold == json.loads(bytes_v1(record))
    exported = export_mi_learning_evidence_onto_learning_path_v1(cold)
    assert exported["mi_learning_evidence"] == cold
    assert exported["promotion_authority_created"] is False
    assert exported["consumer_route"]["productive_ddo_reducer_mutated"] is False
