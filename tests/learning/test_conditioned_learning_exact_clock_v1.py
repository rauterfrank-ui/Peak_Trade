"""Original context → behavior → conditioned-learning chronology, offline only."""

from copy import deepcopy
from dataclasses import asdict
import math

import pytest

from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    derive_o4_instrument_ref_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    loop_a_conditioned_learning_evidence_v1 as conditioned,
    realized_behavior_v1 as behavior,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    plain_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    GovernedMarketContextInputsV1,
    MarketContextValidationError,
    compose_market_context_v1_from_governed_inputs,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_ingest_v1 import (
    INGEST_ID,
    MiLearningEvidenceIngestRequestV1,
    ingest_mi_learning_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_learning_export_v1 import (
    export_mi_learning_evidence_onto_learning_path_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_store_v1 import (
    MiLearningEvidenceStoreV1,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _snapshot
from tests.learning.test_market_context_realized_behavior_join_v1 import _pipeline
from tests.learning.test_mi_learning_exact_clock_admission_v1 import _remint, _stamp
from tests.learning.test_unified_blueprint_phase_8_mi_to_learning_integration_v1 import (
    _mint_forecast,
)

START = "2026-09-01T12:00:00Z"
BEFORE = "2026-09-01T11:59:59Z"
FAMILIES = (
    "price_state",
    "flow_state",
    "liquidity_microstructure_state",
    "derivatives_state",
    "volatility_state",
    "cross_market_state",
    "quality_state",
)
VARIANTS = (
    "plain",
    "zero_fraction",
    "fractional",
    "later_evaluation",
    "missing",
    "insufficient",
    "o4_utc_string",
    "o4_numeric_fraction",
)


def _context(observed_at=START, *, family="price_state", pit=None):
    bar = _snapshot()["o4_bars"][0]
    instrument_ref = derive_o4_instrument_ref_v1(
        bar["canonical_instrument_id"], bar["venue"], bar["venue_instrument_id"]
    )
    slot = {
        "state_ref": "fact.synthetic.original",
        "pit_observed_at_utc": observed_at if pit is None else pit,
        "producer_owner": "ops.peak_trade_public_market_data_runtime_v1",
        "producer_ownership": "GOVERNED",
        "feature_version": "v1",
    }
    if family == "liquidity_microstructure_state":
        slot["microstructure_kind"] = "PROXY_OHLCV"
    if family == "cross_market_state":
        slot["cross_market_authority"] = "CONTEXT_ONLY"
    return plain_v1(
        compose_market_context_v1_from_governed_inputs(
            GovernedMarketContextInputsV1(
                observed_at=observed_at,
                instrument_ref=instrument_ref,
                information_set_identity_body={"pit": observed_at, "source": "synthetic"},
                provenance_refs=["mi.provenance.synthetic.original"],
                feature_versions={"market_context_v1": "v1"},
                **{family: slot},
            )
        )
    )


def _behavior_inputs():
    pipe = _pipeline()
    return {
        "market_context": _context(),
        "evaluation_observation": plain_v1(pipe["evaluation_observation"]),
        "measurement_evidence": plain_v1(pipe["materialization"].measurement_evidence_artifact),
        "o4_bars_for_path": _snapshot()["o4_bars"],
    }


def _case(variant="plain"):
    args = _behavior_inputs()
    obs = args["evaluation_observation"]
    forecast = plain_v1(_mint_forecast(n_bars=2, bar_spec_ref=obs["bar_spec_ref"]))
    if variant == "zero_fraction":
        args["market_context"] = _context(_stamp(START, 0))
    if variant == "fractional":
        args["market_context"] = _context(_stamp(BEFORE, 1))
        forecast = _remint(forecast, forecast_created_at_utc=_stamp(BEFORE, 2))
    if variant in {"later_evaluation", "o4_numeric_fraction"}:
        eval_time = (
            "2026-09-01T16:00:00Z"
            if variant == "later_evaluation"
            else "2026-09-01T14:00:00.000001Z"
        )
        obs["evaluation_time_utc"] = eval_time
        # Omitting an optional measurement does not invent a replacement measurement.
        args["measurement_evidence"] = None
        if variant == "o4_numeric_fraction":
            bar = args["o4_bars_for_path"][-1]
            bar["last_observation_identity"]["venue_event_time"] += 0.000001
    if variant == "o4_utc_string":
        for bar, close in zip(args["o4_bars_for_path"], obs["bar_close_times_utc"]):
            bar["last_observation_identity"]["venue_event_time"] = close
    if variant == "insufficient":
        forecast = _remint(forecast, support_disposition="INSUFFICIENT_EVIDENCE")
    realized = plain_v1(
        behavior.join_market_context_to_realized_behavior_v1(
            behavior.RealizedBehaviorJoinInputsV1(**args)
        )
    )
    return conditioned.ConditionedLearningComposeInputsV1(
        forecast_evidence=forecast,
        evaluation_observation=None if variant == "missing" else obs,
        market_context=args["market_context"],
        realized_behavior=None if variant == "missing" else realized,
        realized_direction="UP",
    )


def _packet(variant):
    inputs = _case(variant)
    record = conditioned.compose_conditioned_mi_learning_evidence_v1(
        inputs, provenance={"ingest_id": INGEST_ID}
    )
    return plain_v1(
        {
            "inputs": asdict(inputs),
            "record": record,
            "export": export_mi_learning_evidence_onto_learning_path_v1(record),
        }
    )


def _forbidden(*args, **kwargs):
    pytest.fail("Invalid original chronology reached the next calculation or writer")


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("nanos", [1, 999])
def test_context_family_cannot_supply_future_information(family, nanos):
    with pytest.raises(MarketContextValidationError, match="PIT_LOOKAHEAD_FORBIDDEN"):
        _context(family=family, pit=_stamp(START, nanos))


@pytest.mark.parametrize("nanos", [1, 999])
@pytest.mark.parametrize(
    ("seam", "reason"),
    [
        ("context", "CONTEXT_OBSERVED_AFTER_HORIZON_START"),
        ("last_close", "EVAL_TIME_BEFORE_LAST_BAR_CLOSE"),
        ("o4", "O4_BAR_POST_OUTCOME_BOUNDARY_LEAKAGE"),
    ],
)
def test_behavior_chronology_stops_before_derivation(monkeypatch, seam, reason, nanos):
    args = _behavior_inputs()
    if seam == "context":
        args["market_context"] = _context(_stamp(START, nanos))
    elif seam == "last_close":
        args["measurement_evidence"] = None
        obs = args["evaluation_observation"]
        obs["bar_close_times_utc"][-1] = _stamp(obs["evaluation_time_utc"], nanos)
    else:
        bar = args["o4_bars_for_path"][-1]
        bar["last_observation_identity"]["venue_event_time"] = _stamp(
            args["evaluation_observation"]["evaluation_time_utc"], nanos
        )
    before = deepcopy(args)
    monkeypatch.setattr(behavior, "_materialize_forward_behavior_v1", _forbidden)
    with pytest.raises(behavior.RealizedBehaviorError, match=reason):
        behavior.join_market_context_to_realized_behavior_v1(
            behavior.RealizedBehaviorJoinInputsV1(**args)
        )
    assert args == before


@pytest.mark.parametrize("entry", ["compose", "ingest"])
@pytest.mark.parametrize(
    ("missing", "nanos"), [(False, 1), (False, 999), (True, 1), (True, 999), (True, 10**9)]
)
def test_future_conditioning_stops_before_original_bridge_or_store(
    tmp_path, monkeypatch, entry, missing, nanos
):
    args = _behavior_inputs()
    observed_at = START if nanos == 10**9 else _stamp(BEFORE, nanos)
    args["market_context"] = _context(observed_at)
    realized = plain_v1(
        behavior.join_market_context_to_realized_behavior_v1(
            behavior.RealizedBehaviorJoinInputsV1(**args)
        )
    )
    forecast = _remint(
        _mint_forecast(n_bars=2, bar_spec_ref=args["evaluation_observation"]["bar_spec_ref"]),
        forecast_created_at_utc=BEFORE,
    )
    inputs = conditioned.ConditionedLearningComposeInputsV1(
        forecast_evidence=forecast,
        evaluation_observation=None if missing else args["evaluation_observation"],
        market_context=args["market_context"],
        realized_behavior=None if missing else realized,
        realized_direction="UP",
    )
    before = deepcopy(asdict(inputs))
    monkeypatch.setattr(conditioned, "compose_mi_to_learning_evidence_v1", _forbidden)
    monkeypatch.setattr(MiLearningEvidenceStoreV1, "append", _forbidden)
    root = tmp_path / "never-created"
    with pytest.raises(
        conditioned.LoopAConditionedLearningError, match="MARKET_CONTEXT_AFTER_FORECAST"
    ):
        if entry == "compose":
            conditioned.compose_conditioned_mi_learning_evidence_v1(inputs)
        else:
            ingest_mi_learning_evidence_v1(
                root, MiLearningEvidenceIngestRequestV1(**asdict(inputs))
            )
    assert asdict(inputs) == before
    assert not root.exists()


@pytest.mark.parametrize("variant", VARIANTS)
def test_valid_conditioned_packets_keep_original_store_and_export(tmp_path, monkeypatch, variant):
    packet = _packet(variant)
    inputs = packet["inputs"]
    before = deepcopy(inputs)
    first = ingest_mi_learning_evidence_v1(tmp_path, MiLearningEvidenceIngestRequestV1(**inputs))
    second = ingest_mi_learning_evidence_v1(tmp_path, MiLearningEvidenceIngestRequestV1(**inputs))
    assert first["ingest_status"] == "APPENDED"
    assert second["ingest_status"] == "IDEMPOTENT_REPLAY"
    assert inputs == before
    monkeypatch.setattr(conditioned, "compose_mi_to_learning_evidence_v1", _forbidden)
    monkeypatch.setattr(behavior, "_materialize_forward_behavior_v1", _forbidden)
    loaded = MiLearningEvidenceStoreV1(tmp_path).get(first["mi_learning_evidence_id"])
    assert bytes_v1(loaded) == bytes_v1(packet["record"])
    exported = export_mi_learning_evidence_onto_learning_path_v1(loaded)
    assert bytes_v1(exported) == bytes_v1(packet["export"])
    assert exported["promotion_authority_created"] is False
    assert loaded["behavior_semantics_snapshot"]["transition_status"] == "SEMANTICALLY_UNRESOLVED"
    assert (
        loaded["behavior_semantics_snapshot"]["classical_mfe_mae_status"]
        == "SEMANTICALLY_UNRESOLVED"
    )
    if variant == "missing":
        assert loaded["evaluability"] == "NOT_EVALUABLE"
        assert loaded["realized_behavior_ref"] == "mi.realized_behavior.explicit_missing"
    if variant == "insufficient":
        assert loaded["evaluability"] == "INSUFFICIENT_EVIDENCE"


def test_numeric_o4_seconds_before_fractional_boundary_remain_admissible():
    args = _behavior_inputs()
    args["measurement_evidence"] = None
    args["evaluation_observation"]["evaluation_time_utc"] = "2026-09-01T14:00:00.000000500Z"
    bar = args["o4_bars_for_path"][-1]
    identity = bar["last_observation_identity"]
    identity["venue_event_time"] = math.nextafter(identity["venue_event_time"], math.inf)
    joined = behavior.join_market_context_to_realized_behavior_v1(
        behavior.RealizedBehaviorJoinInputsV1(**args)
    )
    assert joined["forward_behavior"]["status"] == "UNAVAILABLE"
    assert joined["outcome_window"]["evaluation_time_utc"] == "2026-09-01T14:00:00.000000500Z"


@pytest.mark.parametrize("event_time", [math.nan, math.inf, -math.inf])
def test_nonfinite_o4_seconds_cannot_bypass_the_boundary(monkeypatch, event_time):
    args = _behavior_inputs()
    args["o4_bars_for_path"][-1]["last_observation_identity"]["venue_event_time"] = event_time
    monkeypatch.setattr(behavior, "_materialize_forward_behavior_v1", _forbidden)
    with pytest.raises(behavior.RealizedBehaviorError, match="O4_BAR_PIT_TIME_INVALID"):
        behavior.join_market_context_to_realized_behavior_v1(
            behavior.RealizedBehaviorJoinInputsV1(**args)
        )
