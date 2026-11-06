"""Retain actual supplier artifacts through the host without inventing score labels."""

from copy import deepcopy
import json
import math

import pytest

from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import build_decision_event_v0
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_runtime_productive_host_v1 import (
    produce_n_bars_evaluation_runtime_bundle_v1,
)
from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    mint_ddo_content_ref_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_productive_host_v1 import (
    produce_real_outcome_horizon_evaluation_observation_v1,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _decision, _identity, _snapshot


def _horizon(asset="ETH", start=100.0, end=110.0):
    canonical, native = f"{asset}-USD-SWAP-CANON", f"{asset}-USD-SWAP"
    snapshot = _snapshot()
    for bar, price in zip(snapshot["o4_bars"], (start, end)):
        bar.update(canonical_instrument_id=canonical, venue_instrument_id=native, close=price)
        bar["last_observation_identity"].update(
            canonical_instrument_id=canonical, venue_instrument_id=native, mark_price=price
        )
    before = deepcopy(snapshot)
    decision = build_decision_event_v0(_decision(selected_instrument_ref=canonical))
    result = produce_real_outcome_horizon_evaluation_observation_v1(decision, snapshot)
    assert snapshot == before
    return decision, result


@pytest.mark.parametrize(
    ("asset", "start", "end"), [("ETH", 100.0, 110.0), ("BTC", 50000.0, 55000.0), ("SUI", 1.0, 1.1)]
)
def test_supplier_measurement_reaches_runtime_for_each_asset_without_a_score_inference(
    asset, start, end
):
    decision, horizon = _horizon(asset, start, end)
    result = produce_n_bars_evaluation_runtime_bundle_v1(horizon, decision, _identity())
    restored = json.loads(json.dumps(result, allow_nan=False))
    assert result["measurement_artifacts_retained"] is True
    measurement = restored["measurement_evidence_artifact"]
    assert measurement["log_return"] == pytest.approx(math.log(end / start))
    assert measurement["start_price"] == start
    assert measurement["end_price"] == end
    assert measurement["actual_outcome_ref"] == result["actual_outcome_ref"]
    assert result["economic_score"] == "UNKNOWN"
    assert result["external_effect_authorized"] is False
    result["measurement_evidence_artifact"]["bar_identity_refs"][0] = "changed-output-copy"
    assert horizon["measurement_evidence_artifact"]["bar_identity_refs"][0] != "changed-output-copy"


def test_modified_measurement_is_rejected_before_evaluation(monkeypatch):
    decision, horizon = _horizon()
    horizon["measurement_evidence_artifact"]["end_price"] = 999.0

    def must_not_evaluate(*args, **kwargs):
        raise AssertionError("corrupt measurement reached evaluation/ledger")

    monkeypatch.setattr(
        "src.learning.deterministic_decision_outcome_v0.evaluation_runtime_productive_host_v1."
        "evaluate_offline_bundle_v0",
        must_not_evaluate,
    )
    with pytest.raises(DdoValidationError, match="CONTENT_REF_MISMATCH"):
        produce_n_bars_evaluation_runtime_bundle_v1(horizon, decision, _identity())


@pytest.mark.parametrize(
    "field,value", [("instrument_ref", "different.future"), ("outcome_scalar_kind", "ABS_RETURN")]
)
def test_rehashed_measurement_cannot_change_instrument_or_scalar_meaning(field, value):
    decision, horizon = _horizon()
    measurement = horizon["measurement_evidence_artifact"]
    measurement[field] = value
    measurement["actual_outcome_ref"] = mint_ddo_content_ref_v1(
        prefix="ddo.outcome.measure.",
        payload={k: v for k, v in measurement.items() if k != "actual_outcome_ref"},
    )
    horizon["evaluation_observation"]["actual_outcome_ref"] = measurement["actual_outcome_ref"]
    with pytest.raises(DdoValidationError, match="CONTEXT_MISMATCH|SCALAR_KIND_MISMATCH"):
        produce_n_bars_evaluation_runtime_bundle_v1(horizon, decision, _identity())


def test_rehashed_information_set_cannot_be_spliced_from_another_decision():
    decision, horizon = _horizon()
    info = horizon["evaluation_time_information_set_artifact"]
    info["decision_event_ref"] = "different-decision"
    info["evaluation_time_information_set_ref"] = mint_ddo_content_ref_v1(
        prefix="ddo.eval_info_set.",
        payload={k: v for k, v in info.items() if k != "evaluation_time_information_set_ref"},
    )
    horizon["evaluation_observation"]["evaluation_time_information_set_ref"] = info[
        "evaluation_time_information_set_ref"
    ]
    with pytest.raises(DdoValidationError, match="DECISION_MISMATCH"):
        produce_n_bars_evaluation_runtime_bundle_v1(horizon, decision, _identity())


def test_partial_artifact_pair_is_not_silently_treated_as_legacy():
    decision, horizon = _horizon()
    del horizon["evaluation_time_information_set_artifact"]
    with pytest.raises(DdoValidationError, match="ARTIFACTS_INCOMPLETE"):
        produce_n_bars_evaluation_runtime_bundle_v1(horizon, decision, _identity())


def test_legacy_reference_only_input_does_not_claim_measurement_retention():
    decision, horizon = _horizon()
    del horizon["measurement_evidence_artifact"]
    del horizon["evaluation_time_information_set_artifact"]
    result = produce_n_bars_evaluation_runtime_bundle_v1(horizon, decision, _identity())
    assert result["measurement_artifacts_retained"] is False
    assert result["measurement_evidence_artifact"] is None
    assert result["evaluation_time_information_set_artifact"] is None


def test_measurement_close_window_is_kept_distinct_from_the_horizon_grid_anchor():
    _decision_record, horizon = _horizon()
    measurement = horizon["measurement_evidence_artifact"]
    assert measurement["horizon_start_time_utc"] == "2026-09-01T12:00:00Z"
    assert measurement["bar_close_times_utc"] == [
        "2026-09-01T13:00:00Z",
        "2026-09-01T14:00:00Z",
    ]
    # Existing supplier measures first-close to last-close, not a decision-time PnL.
    assert measurement["start_price"] == 100.0
    assert measurement["end_price"] == 110.0
