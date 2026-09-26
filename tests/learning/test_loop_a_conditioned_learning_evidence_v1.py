"""Phase 21 Loop A conditioned Learning evidence integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import build_decision_event_v0
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_productive_host_v1 import (
    produce_real_outcome_horizon_evaluation_observation_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.loop_a_conditioned_learning_evidence_v1 import (
    ConditionedLearningComposeInputsV1,
    LoopAConditionedLearningError,
    assert_loop_a_authority_invariants_v1,
    compose_conditioned_mi_learning_evidence_v1,
    run_loop_a_conditioned_learning_cycle_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_record_v1 import (
    CONDITIONED_BINDING_SCHEMA,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_optimization_research_input_v1 import (
    MarketIntelligenceOptimizationResearchInputError,
    MarketIntelligenceOptimizationResearchInputRequestV1,
    validate_market_intelligence_optimization_research_input_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1 import (
    RealizedBehaviorJoinInputsV1,
    join_market_context_to_realized_behavior_v1,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _decision, _snapshot
from tests.learning.test_market_context_realized_behavior_join_v1 import _context_for_observation
from tests.learning.test_unified_blueprint_phase_8_mi_to_learning_integration_v1 import (
    _directional_payload,
    _mint_forecast,
    _observation_for_n,
)


def _realized_behavior(*, obs: dict, ctx: dict) -> dict:
    pipe_obs = obs
    from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
        run_offline_n_bars_horizon_pipeline_v1,
    )

    decision = build_decision_event_v0(_decision())
    snap = _snapshot()
    snap["decision_event_ref"] = decision["record_id"]
    pipe = run_offline_n_bars_horizon_pipeline_v1(decision, snap, outcome_scalar_kind="LOG_RETURN")
    return dict(
        join_market_context_to_realized_behavior_v1(
            RealizedBehaviorJoinInputsV1(
                market_context=ctx,
                evaluation_observation=pipe["evaluation_observation"],
                measurement_evidence=pipe["materialization"].measurement_evidence_artifact,
                o4_bars_for_path=snap["o4_bars"],
            )
        )
    )


def test_conditioned_evidence_binds_context_and_behavior() -> None:
    obs = _observation_for_n(n_bars=2)
    ctx = _context_for_observation(obs)
    rb = _realized_behavior(obs=obs, ctx=ctx)
    forecast = _mint_forecast(n_bars=2, bar_spec_ref=str(obs["bar_spec_ref"]))
    record = compose_conditioned_mi_learning_evidence_v1(
        ConditionedLearningComposeInputsV1(
            forecast_evidence=forecast,
            evaluation_observation=obs,
            market_context=ctx,
            realized_behavior=rb,
            realized_direction="UP",
        )
    )
    assert record["conditioned_binding_schema"] == CONDITIONED_BINDING_SCHEMA
    assert record["market_context_ref"] == ctx["context_id"]
    assert record["realized_behavior_ref"] == rb["behavior_id"]
    snap = record["behavior_semantics_snapshot"]
    assert snap["transition_status"] == "SEMANTICALLY_UNRESOLVED"
    assert snap["classical_mfe_mae_status"] == "SEMANTICALLY_UNRESOLVED"


def test_deterministic_conditioned_evidence_identity() -> None:
    obs = _observation_for_n(n_bars=2)
    ctx = _context_for_observation(obs)
    rb = _realized_behavior(obs=obs, ctx=ctx)
    forecast = _mint_forecast(n_bars=2, bar_spec_ref=str(obs["bar_spec_ref"]))
    inputs = ConditionedLearningComposeInputsV1(
        forecast_evidence=forecast,
        evaluation_observation=obs,
        market_context=ctx,
        realized_behavior=rb,
        realized_direction="UP",
    )
    first = compose_conditioned_mi_learning_evidence_v1(inputs)
    second = compose_conditioned_mi_learning_evidence_v1(inputs)
    assert first["mi_learning_evidence_id"] == second["mi_learning_evidence_id"]


def test_loop_a_writer_reader_persistence(tmp_path: Path) -> None:
    obs = _observation_for_n(n_bars=2)
    ctx = _context_for_observation(obs)
    rb = _realized_behavior(obs=obs, ctx=ctx)
    forecast = _mint_forecast(n_bars=2, bar_spec_ref=str(obs["bar_spec_ref"]))
    cycle = run_loop_a_conditioned_learning_cycle_v1(
        store_root=tmp_path / "loop_a_store",
        inputs=ConditionedLearningComposeInputsV1(
            forecast_evidence=forecast,
            evaluation_observation=obs,
            market_context=ctx,
            realized_behavior=rb,
            realized_direction="UP",
        ),
    )
    assert cycle["loop_a_proven"] is True
    assert cycle["persistence_proven"] is True
    assert cycle["export_retrieval_proven"] is True
    assert cycle["learning_export"]["promotion_authority_created"] is False


def test_horizon_mismatch_fails_closed() -> None:
    obs = _observation_for_n(n_bars=3)
    ctx = _context_for_observation(obs)
    rb = _realized_behavior(obs=obs, ctx=ctx)
    forecast = _mint_forecast(n_bars=2, bar_spec_ref=str(obs["bar_spec_ref"]))
    with pytest.raises(LoopAConditionedLearningError, match="FORECAST_N_BARS_MISMATCH"):
        compose_conditioned_mi_learning_evidence_v1(
            ConditionedLearningComposeInputsV1(
                forecast_evidence=forecast,
                evaluation_observation=obs,
                market_context=ctx,
                realized_behavior=rb,
            )
        )


def test_missing_forecast_abstention_path_explicit() -> None:
    ctx = _context_for_observation(
        {"instrument_ref": "inst-eth-usdt-perp", "n_bars": 2, "bar_spec_ref": "PT1H"},
        observed_at="2026-09-01T12:00:00Z",
    )
    forecast = dict(
        mint_forecast_evidence_v1(
            information_set_ref="info.set.phase21",
            forecast_created_at_utc="2026-09-01T12:00:00Z",
            outcome_horizon_end_utc="2026-09-01T14:00:00Z",
            n_bars=2,
            bar_spec_ref="PT1H",
            forecast_kind="DIRECTIONAL_PROBABILITY",
            probabilistic_payload=_directional_payload(),
            market_state_refs=["mi.state.p21"],
            forecast_model_ref="mi.model.v1",
            support_disposition="INSUFFICIENT_EVIDENCE",
            provenance={"source": "phase21-test"},
        )
    )
    record = compose_conditioned_mi_learning_evidence_v1(
        ConditionedLearningComposeInputsV1(
            forecast_evidence=forecast,
            evaluation_observation=None,
            market_context=ctx,
            realized_behavior=None,
        )
    )
    assert record["horizon_observation_status"] == "OUTCOME_MISSING"


def test_optimization_boundary_unchanged_productive_join_forbidden() -> None:
    with pytest.raises(MarketIntelligenceOptimizationResearchInputError):
        validate_market_intelligence_optimization_research_input_v1(
            MarketIntelligenceOptimizationResearchInputRequestV1(
                market_intelligence_research_evidence=None,
                requested_productive_join=True,
            )
        )


def test_authority_negative_invariants() -> None:
    inv = assert_loop_a_authority_invariants_v1()
    assert inv["LEARNING_TRADING_AUTHORITY"] == "NONE"
    assert inv["LEARNING_PROMOTION_AUTHORITY"] == "NONE"
    assert inv["LEARNING_DIRECT_PRODUCTIVE_WRITE"] == "FORBIDDEN"
    assert inv["FORECAST_IS_NOT_DECISION"] is True
