"""Phase 20 MARKET_CONTEXT → REALIZED_BEHAVIOR N_BARS join tests (AUTHORITY=NONE)."""

from __future__ import annotations

import math

import pytest

from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    run_offline_n_bars_horizon_pipeline_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    GovernedMarketContextInputsV1,
    compose_market_context_v1_from_governed_inputs,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1 import (
    RealizedBehaviorError,
    RealizedBehaviorJoinInputsV1,
    assert_realized_behavior_authority_invariants_v1,
    join_market_context_to_realized_behavior_v1,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import (
    _decision,
    _o4_bar,
    _snapshot,
)


def _minimal_market_context(
    *,
    observed_at: str = "2026-09-01T12:00:00Z",
    instrument_ref: str = "inst-eth-usdt-perp",
) -> dict:
    inputs = GovernedMarketContextInputsV1(
        observed_at=observed_at,
        instrument_ref=instrument_ref,
        information_set_identity_body={"pit": observed_at, "instrument": instrument_ref},
        provenance_refs=["mi.provenance.phase20.test"],
        feature_versions={"market_context_v1": "market_context_v1", "phase_20_test": "v1"},
    )
    return dict(compose_market_context_v1_from_governed_inputs(inputs))


def _context_for_observation(obs: dict, *, observed_at: str = "2026-09-01T12:00:00Z") -> dict:
    return _minimal_market_context(
        observed_at=observed_at,
        instrument_ref=str(obs["instrument_ref"]),
    )


def _pipeline() -> dict:
    decision = _decision()
    snap = _snapshot()
    snap["decision_event_ref"] = decision["record_id"]
    return run_offline_n_bars_horizon_pipeline_v1(
        decision,
        snap,
        outcome_scalar_kind="LOG_RETURN",
    )


def test_behavior_join_deterministic_replay() -> None:
    pipe = _pipeline()
    obs = pipe["evaluation_observation"]
    ctx = _context_for_observation(obs)
    meas = pipe["materialization"].measurement_evidence_artifact
    bars = _snapshot()["o4_bars"]

    first = join_market_context_to_realized_behavior_v1(
        RealizedBehaviorJoinInputsV1(
            market_context=ctx,
            evaluation_observation=obs,
            measurement_evidence=meas,
            o4_bars_for_path=bars,
        )
    )
    second = join_market_context_to_realized_behavior_v1(
        RealizedBehaviorJoinInputsV1(
            market_context=ctx,
            evaluation_observation=obs,
            measurement_evidence=meas,
            o4_bars_for_path=bars,
        )
    )
    assert first["behavior_id"] == second["behavior_id"]
    assert first["content_digest"] == second["content_digest"]


def test_forward_behavior_from_measurement() -> None:
    pipe = _pipeline()
    joined = join_market_context_to_realized_behavior_v1(
        RealizedBehaviorJoinInputsV1(
            market_context=_context_for_observation(pipe["evaluation_observation"]),
            evaluation_observation=pipe["evaluation_observation"],
            measurement_evidence=pipe["materialization"].measurement_evidence_artifact,
            o4_bars_for_path=_snapshot()["o4_bars"],
        )
    )
    fb = joined["forward_behavior"]
    assert fb["status"] == "PROVEN_TYPED"
    assert fb["forward_return"]["kind"] == "LOG_RETURN"
    assert math.isclose(float(fb["forward_return"]["value"]), math.log(110.0 / 100.0))


def test_excursion_close_path_and_classical_mfe_unresolved() -> None:
    pipe = _pipeline()
    joined = join_market_context_to_realized_behavior_v1(
        RealizedBehaviorJoinInputsV1(
            market_context=_context_for_observation(pipe["evaluation_observation"]),
            evaluation_observation=pipe["evaluation_observation"],
            measurement_evidence=pipe["materialization"].measurement_evidence_artifact,
            o4_bars_for_path=_snapshot()["o4_bars"],
        )
    )
    exc = joined["excursion"]
    assert exc["status"] == "PROVEN_TYPED"
    assert exc["classical_mfe_mae"]["status"] == "SEMANTICALLY_UNRESOLVED"


def test_realized_volatility_typed() -> None:
    pipe = _pipeline()
    joined = join_market_context_to_realized_behavior_v1(
        RealizedBehaviorJoinInputsV1(
            market_context=_context_for_observation(pipe["evaluation_observation"]),
            evaluation_observation=pipe["evaluation_observation"],
            measurement_evidence=pipe["materialization"].measurement_evidence_artifact,
            o4_bars_for_path=_snapshot()["o4_bars"],
        )
    )
    rv = joined["realized_volatility"]
    assert rv["status"] == "PROVEN_TYPED"
    assert rv["returns_count"] == 1


def test_transition_explicit_unresolved() -> None:
    pipe = _pipeline()
    joined = join_market_context_to_realized_behavior_v1(
        RealizedBehaviorJoinInputsV1(
            market_context=_context_for_observation(pipe["evaluation_observation"]),
            evaluation_observation=pipe["evaluation_observation"],
            measurement_evidence=pipe["materialization"].measurement_evidence_artifact,
            o4_bars_for_path=_snapshot()["o4_bars"],
        )
    )
    assert joined["transition"]["status"] == "SEMANTICALLY_UNRESOLVED"


def test_pit_rejects_context_after_horizon_start() -> None:
    pipe = _pipeline()
    ctx = _context_for_observation(
        pipe["evaluation_observation"], observed_at="2026-09-01T13:30:00Z"
    )
    with pytest.raises(RealizedBehaviorError, match="CONTEXT_OBSERVED_AFTER_HORIZON_START"):
        join_market_context_to_realized_behavior_v1(
            RealizedBehaviorJoinInputsV1(
                market_context=ctx,
                evaluation_observation=pipe["evaluation_observation"],
                measurement_evidence=pipe["materialization"].measurement_evidence_artifact,
                o4_bars_for_path=_snapshot()["o4_bars"],
            )
        )


def test_rejects_post_boundary_o4_observation() -> None:
    pipe = _pipeline()
    snap = _snapshot()
    leak_bar = _o4_bar(
        open_iso="2026-09-01T13:00:00Z",
        close_iso="2026-09-01T14:00:00Z",
        close_price=110.0,
        venue_event_time=9999999999.0,
    )
    snap["o4_bars"] = [snap["o4_bars"][0], leak_bar]
    with pytest.raises(RealizedBehaviorError, match="O4_BAR_POST_OUTCOME_BOUNDARY_LEAKAGE"):
        join_market_context_to_realized_behavior_v1(
            RealizedBehaviorJoinInputsV1(
                market_context=_context_for_observation(pipe["evaluation_observation"]),
                evaluation_observation=pipe["evaluation_observation"],
                measurement_evidence=pipe["materialization"].measurement_evidence_artifact,
                o4_bars_for_path=snap["o4_bars"],
            )
        )


def test_horizon_change_changes_behavior_id() -> None:
    pipe2 = _pipeline()
    snap3 = _snapshot(n_bars=3)
    snap3["decision_event_ref"] = _decision()["record_id"]
    snap3["o4_bars"] = [
        _o4_bar(
            open_iso="2026-09-01T12:00:00Z", close_iso="2026-09-01T13:00:00Z", close_price=100.0
        ),
        _o4_bar(
            open_iso="2026-09-01T13:00:00Z", close_iso="2026-09-01T14:00:00Z", close_price=105.0
        ),
        _o4_bar(
            open_iso="2026-09-01T14:00:00Z", close_iso="2026-09-01T15:00:00Z", close_price=110.0
        ),
    ]
    pipe3 = run_offline_n_bars_horizon_pipeline_v1(
        _decision(),
        snap3,
        outcome_scalar_kind="LOG_RETURN",
    )
    ctx = _context_for_observation(pipe2["evaluation_observation"])
    j2 = join_market_context_to_realized_behavior_v1(
        RealizedBehaviorJoinInputsV1(
            market_context=ctx,
            evaluation_observation=pipe2["evaluation_observation"],
            measurement_evidence=pipe2["materialization"].measurement_evidence_artifact,
            o4_bars_for_path=_snapshot()["o4_bars"],
        )
    )
    j3 = join_market_context_to_realized_behavior_v1(
        RealizedBehaviorJoinInputsV1(
            market_context=ctx,
            evaluation_observation=pipe3["evaluation_observation"],
            measurement_evidence=pipe3["materialization"].measurement_evidence_artifact,
            o4_bars_for_path=snap3["o4_bars"],
        )
    )
    assert j2["behavior_id"] != j3["behavior_id"]


def test_incomplete_horizon_explicit_missing_forward() -> None:
    decision = _decision()
    snap = _snapshot()
    snap["decision_event_ref"] = decision["record_id"]
    snap["o4_bars"][1]["finalization_state"] = "IN_PROGRESS_BAR"
    pipe = run_offline_n_bars_horizon_pipeline_v1(
        decision,
        snap,
        outcome_scalar_kind="LOG_RETURN",
    )
    joined = join_market_context_to_realized_behavior_v1(
        RealizedBehaviorJoinInputsV1(
            market_context=_context_for_observation(pipe["evaluation_observation"]),
            evaluation_observation=pipe["evaluation_observation"],
            measurement_evidence=None,
            o4_bars_for_path=snap["o4_bars"],
        )
    )
    assert joined["forward_behavior"]["status"] == "UNAVAILABLE"
    assert joined["quality_state"]["join_status"] == "OUTCOME_INCOMPLETE"


def test_authority_negative_invariants() -> None:
    inv = assert_realized_behavior_authority_invariants_v1()
    assert inv["REALIZED_BEHAVIOR_AUTHORITY"] == "NONE"
    assert inv["MARKET_CONTEXT_AUTHORITY"] == "NONE"
    assert inv["FORECAST_IS_NOT_DECISION"] is True
    assert inv["NO_SECOND_MARKET_TRUTH"] is True
