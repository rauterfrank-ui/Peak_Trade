"""Track D03 — offline MI forecast/calibration stack contract tests."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    WORKING_TREE_CLEAN,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
from src.experiments.canonical_failure_memory_v1 import (
    CanonicalFailureMemoryRecordRequestV1,
    build_canonical_failure_memory_record_v1,
    derive_experiment_id_v1,
)
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    CanonicalOptimizationUniverseLearningInputRequestV1,
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import build_decision_event_v0
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1 import (
    ingest_evaluation_bundle_into_learning_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_productive_host_v1 import (
    produce_real_outcome_horizon_evaluation_observation_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.calibration_evidence_v1 import (
    build_calibration_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    CAP23_SOLE_PRODUCTIVE_SELECTION_OWNER,
    GLOBAL_MARKET_INTELLIGENCE_DEFAULT_N,
    MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY,
    NO_AUTOMATIC_PROMOTION,
    PRODUCTIVE_DDO_FEEDBACK_SEAM_UNCHANGED,
    PRODUCTIVE_PROMOTION_OPENED,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    ForecastEvidenceValidationError,
    mint_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_outcome_join_v1 import (
    assert_n_bars_observation_unmodified_v1,
    join_forecast_to_n_bars_outcome_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_optimization_research_input_v1 import (
    MarketIntelligenceOptimizationResearchInputError,
    MarketIntelligenceOptimizationResearchInputRequestV1,
    STATUS_ACCEPTED,
    validate_market_intelligence_optimization_research_input_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_orchestrator_v1 import (
    OfflineForecastScenarioV1,
    OfflineOrchestratorInputV1,
    run_market_intelligence_offline_orchestrator_cycle_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.support_disposition_v1 import (
    SUPPORT_INSUFFICIENT_EVIDENCE,
    SUPPORT_NOT_EVALUABLE,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import (
    _decision,
    _identity,
    _o4_bar,
    _snapshot,
)
from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    O4_SNAPSHOT_SCHEMA_NAME,
    O4_SNAPSHOT_SCHEMA_VERSION,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _directional_payload() -> dict[str, float]:
    return {"p_up": 0.5, "p_down": 0.3, "p_flat": 0.2}


def _snapshot_three_bars() -> dict[str, Any]:
    return {
        "schema_name": O4_SNAPSHOT_SCHEMA_NAME,
        "schema_version": O4_SNAPSHOT_SCHEMA_VERSION,
        "decision_event_ref": "dec-chain-0001",
        "horizon_start_time_utc": "2026-09-01T12:00:00Z",
        "n_bars": 3,
        "o4_interval_id": "PT1H",
        "o4_bars": [
            _o4_bar(
                open_iso="2026-09-01T12:00:00Z",
                close_iso="2026-09-01T13:00:00Z",
                close_price=100.0,
            ),
            _o4_bar(
                open_iso="2026-09-01T13:00:00Z",
                close_iso="2026-09-01T14:00:00Z",
                close_price=105.0,
            ),
            _o4_bar(
                open_iso="2026-09-01T14:00:00Z",
                close_iso="2026-09-01T15:00:00Z",
                close_price=110.0,
            ),
        ],
    }


def _mint_forecast(
    *,
    n_bars: int,
    created: str,
    horizon_end: str,
    info_set: str,
    bar_spec_ref: str | None = None,
) -> dict[str, Any]:
    obs = _observation_for_n(n_bars=n_bars)
    resolved_bar_spec = bar_spec_ref or str(obs["bar_spec_ref"])
    return dict(
        mint_forecast_evidence_v1(
            information_set_ref=info_set,
            forecast_created_at_utc=created,
            outcome_horizon_end_utc=horizon_end,
            n_bars=n_bars,
            bar_spec_ref=resolved_bar_spec,
            forecast_kind="DIRECTIONAL_PROBABILITY",
            probabilistic_payload=_directional_payload(),
            market_state_refs=[f"mi.state.{n_bars}"],
            forecast_model_ref="mi.model.offline.v1",
            support_disposition="SUFFICIENT_EVIDENCE",
            provenance={"source": "test"},
        )
    )


def _observation_for_n(*, n_bars: int) -> dict[str, Any]:
    snap = _snapshot(n_bars=n_bars) if n_bars != 3 else _snapshot_three_bars()
    decision = build_decision_event_v0(_decision())
    return produce_real_outcome_horizon_evaluation_observation_v1(
        decision, snap, economic_score="MI_TEST"
    )["evaluation_observation"]


def test_forecast_created_before_outcome_boundary_and_explicit_horizon() -> None:
    forecast = _mint_forecast(
        n_bars=2,
        created="2026-09-01T12:00:00Z",
        horizon_end="2026-09-01T14:00:00Z",
        info_set="info.set.0001",
    )
    assert forecast["n_bars"] == 2
    assert forecast["bar_spec_ref"].startswith("ddo.o4.barspec.")
    assert forecast["information_set_ref"] == "info.set.0001"
    with pytest.raises(ForecastEvidenceValidationError):
        mint_forecast_evidence_v1(
            information_set_ref="info.set.bad",
            forecast_created_at_utc="2026-09-01T15:00:00Z",
            outcome_horizon_end_utc="2026-09-01T14:00:00Z",
            n_bars=2,
            bar_spec_ref="bar.spec.pt1h.v1",
            forecast_kind="DIRECTIONAL_PROBABILITY",
            probabilistic_payload=_directional_payload(),
            market_state_refs=["mi.state.1"],
            forecast_model_ref="mi.model.offline.v1",
            support_disposition="SUFFICIENT_EVIDENCE",
            provenance={"source": "test"},
        )


def test_different_n_produces_different_evidence_identity() -> None:
    f1 = _mint_forecast(
        n_bars=2,
        created="2026-09-01T12:00:00Z",
        horizon_end="2026-09-01T14:00:00Z",
        info_set="info.set.shared",
    )
    f2 = _mint_forecast(
        n_bars=3,
        created="2026-09-01T12:00:00Z",
        horizon_end="2026-09-01T15:00:00Z",
        info_set="info.set.shared",
    )
    assert f1["forecast_evidence_id"] != f2["forecast_evidence_id"]
    assert f1["n_bars"] == 2 and f2["n_bars"] == 3


def test_join_does_not_mutate_n_bars_observation() -> None:
    forecast = _mint_forecast(
        n_bars=2,
        created="2026-09-01T12:00:00Z",
        horizon_end="2026-09-01T14:00:00Z",
        info_set="info.set.join",
    )
    obs = _observation_for_n(n_bars=2)
    before = dict(obs)
    join = join_forecast_to_n_bars_outcome_v1(
        forecast_evidence=forecast, evaluation_observation=obs
    )
    assert join["join_status"] == "JOINED"
    assert_n_bars_observation_unmodified_v1(before, obs)


def test_calibration_references_exact_forecast_and_outcome() -> None:
    forecast = _mint_forecast(
        n_bars=2,
        created="2026-09-01T12:00:00Z",
        horizon_end="2026-09-01T14:00:00Z",
        info_set="info.set.calib",
    )
    obs = _observation_for_n(n_bars=2)
    calib = build_calibration_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=obs,
        realized_direction="UP",
    )
    assert calib["forecast_evidence_id"] == forecast["forecast_evidence_id"]
    assert calib["actual_outcome_ref"] == obs["actual_outcome_ref"]


def test_missing_outcome_is_not_evaluable() -> None:
    forecast = _mint_forecast(
        n_bars=2,
        created="2026-09-01T12:00:00Z",
        horizon_end="2026-09-01T14:00:00Z",
        info_set="info.set.missing",
    )
    calib = build_calibration_evidence_v1(forecast_evidence=forecast, evaluation_observation=None)
    assert calib["evaluability"] == SUPPORT_NOT_EVALUABLE


def test_insufficient_support_abstains_without_fabricated_confidence() -> None:
    forecast = dict(
        mint_forecast_evidence_v1(
            information_set_ref="info.set.insufficient",
            forecast_created_at_utc="2026-09-01T12:00:00Z",
            outcome_horizon_end_utc="2026-09-01T14:00:00Z",
            n_bars=2,
            bar_spec_ref=str(_observation_for_n(n_bars=2)["bar_spec_ref"]),
            forecast_kind="DIRECTIONAL_PROBABILITY",
            probabilistic_payload=_directional_payload(),
            market_state_refs=["mi.state.insufficient"],
            forecast_model_ref="mi.model.offline.v1",
            support_disposition=SUPPORT_INSUFFICIENT_EVIDENCE,
            provenance={"source": "test"},
        )
    )
    obs = _observation_for_n(n_bars=2)
    calib = build_calibration_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=obs,
        support_disposition=SUPPORT_INSUFFICIENT_EVIDENCE,
    )
    assert calib["evaluability"] == SUPPORT_INSUFFICIENT_EVIDENCE
    assert "confidence" not in calib["calibration_result"]


def test_no_numeric_calibration_in_opaque_economic_score_seam(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    label_before = state["next_cycle_economic_score_label"]
    export = export_learning_evidence_from_state_v1(state)
    forecast = _mint_forecast(
        n_bars=2,
        created="2026-09-01T12:00:00Z",
        horizon_end="2026-09-01T14:00:00Z",
        info_set="info.set.seam",
    )
    calib = build_calibration_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=_observation_for_n(n_bars=2),
        realized_direction="UP",
    )
    assert state["next_cycle_economic_score_label"] == label_before
    assert export["economic_score_label"] == label_before
    assert isinstance(calib["calibration_result"].get("score"), float)


def test_legacy_learning_consumers_remain_compatible(tmp_path: Path) -> None:
    evidence = export_learning_evidence_from_state_v1(_learning_state(tmp_path))
    ack = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=evidence)
    )
    assert ack["status"] == STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT


def test_offline_orchestrator_multi_horizon_and_optimization_intake(tmp_path: Path) -> None:
    obs2 = _observation_for_n(n_bars=2)
    obs3 = _observation_for_n(n_bars=3)
    cycle = run_market_intelligence_offline_orchestrator_cycle_v1(
        OfflineOrchestratorInputV1(
            scenarios=[
                OfflineForecastScenarioV1(
                    information_set_ref="info.set.n2.horizon",
                    forecast_created_at_utc="2026-09-01T12:00:00Z",
                    outcome_horizon_end_utc="2026-09-01T14:00:00Z",
                    n_bars=2,
                    bar_spec_ref=str(obs2["bar_spec_ref"]),
                    market_state_refs=["mi.state.n2"],
                    forecast_model_ref="mi.model.v1",
                    probabilistic_payload=_directional_payload(),
                    realized_direction="UP",
                ),
                OfflineForecastScenarioV1(
                    information_set_ref="info.set.n3.horizon",
                    forecast_created_at_utc="2026-09-01T12:00:00Z",
                    outcome_horizon_end_utc="2026-09-01T15:00:00Z",
                    n_bars=3,
                    bar_spec_ref=str(obs3["bar_spec_ref"]),
                    market_state_refs=["mi.state.n3"],
                    forecast_model_ref="mi.model.v1",
                    probabilistic_payload=_directional_payload(),
                    realized_direction="DOWN",
                ),
            ],
            evaluation_observations_by_n_bars={2: obs2, 3: obs3},
            learning_state_record=_learning_state(tmp_path),
        )
    )
    assert len(cycle["forecasts"]) == 2
    assert (
        cycle["forecasts"][0]["forecast_evidence_id"]
        != cycle["forecasts"][1]["forecast_evidence_id"]
    )
    assert cycle["optimization_research_input_acks"][0]["status"] == STATUS_ACCEPTED
    assert cycle["runtime_reachability"] is False
    with pytest.raises(MarketIntelligenceOptimizationResearchInputError):
        validate_market_intelligence_optimization_research_input_v1(
            MarketIntelligenceOptimizationResearchInputRequestV1(
                market_intelligence_research_evidence=cycle["research_projections"][0],
                requested_mv2_dp_binding=True,
            )
        )


def test_failure_memory_reuse_deterministic_replay(tmp_path: Path) -> None:
    identity = build_canonical_experiment_identity_v1(
        CanonicalExperimentIdentityRequestV1(
            git_sha="e10f32f56fad0576cd250958401d13f044c5920d",
            working_tree_status=WORKING_TREE_CLEAN,
            strategy_identity="ma_crossover.v1",
            strategy_params={"slow": 50, "fast": 10},
            dataset_digest=_digest("dataset"),
            feature_pipeline_digest=_digest("features"),
            fee_model_digest=_digest("fee"),
            slippage_model_digest=_digest("slippage"),
            funding_model_digest=_digest("funding"),
            risk_policy_digest=_digest("risk"),
            portfolio_digest=_digest("portfolio"),
            split_policy_digest=_digest("split"),
            market_context_contract_digest=_digest("market-context"),
            bull_bear_logic_digest=_digest("bull-bear"),
            state_switch_logic_digest=_digest("state-switch"),
            survival_logic_digest=_digest("survival"),
            suitability_logic_digest=_digest("suitability"),
            double_play_logic_digest=_digest("double-play"),
            entry_position_exit_logic_digest=_digest("entry-position-exit"),
            seed=7,
            environment={"python_version": "3.11.15", "python_implementation": "CPython"},
            parent_lineage_ref=None,
            dirty_paths_digest=None,
        )
    )
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    request = CanonicalFailureMemoryRecordRequestV1(
        experiment_identity=identity,
        hypothesis_id="hyp.mi.offline.v1",
        failure_class="REJECTED_OVERFIT",
        failed_gate="OVERFIT_GATE",
        rejection_reason="REJECTED_OVERFIT",
        regime="high_vol",
        parameter_region={"fast": 10, "slow": 50},
        cost_sensitivity={"fee_stress": 0.25},
        instability_indicators={"unstable": True},
        evidence_refs=[
            {
                "kind": "EXPERIMENT_RECORD",
                "ref": experiment_id,
                "digest": _digest("experiment-record"),
            }
        ],
        created_at="2026-09-26T10:00:00Z",
        robustness_policy_digest=_digest("robustness-policy"),
    )
    store_root = tmp_path / "failure_memory"
    cycle = run_market_intelligence_offline_orchestrator_cycle_v1(
        OfflineOrchestratorInputV1(
            scenarios=[
                OfflineForecastScenarioV1(
                    information_set_ref="info.set.fm.horizon",
                    forecast_created_at_utc="2026-09-01T12:00:00Z",
                    outcome_horizon_end_utc="2026-09-01T14:00:00Z",
                    n_bars=2,
                    bar_spec_ref=str(_observation_for_n(n_bars=2)["bar_spec_ref"]),
                    market_state_refs=["mi.state.fm"],
                    forecast_model_ref="mi.model.v1",
                    probabilistic_payload=_directional_payload(),
                )
            ],
            evaluation_observations_by_n_bars={},
            failure_memory_store_root=store_root,
            failure_memory_request=request,
        )
    )
    trace = cycle["failure_memory_replay"]
    assert trace is not None
    assert trace["deterministic_replay_equal"] is True
    assert trace["append_count"] == 1
    store = CanonicalFailureMemoryStoreV1(store_root)
    replay = build_canonical_failure_memory_record_v1(request)
    dup = store.assess_duplicate(hypothesis_fingerprint=str(replay["hypothesis_fingerprint"]))
    assert dup["previously_rejected"] is True


def test_safety_pins_and_global_default_n() -> None:
    assert GLOBAL_MARKET_INTELLIGENCE_DEFAULT_N is None
    assert MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY is True
    assert CAP23_SOLE_PRODUCTIVE_SELECTION_OWNER is True
    assert PRODUCTIVE_DDO_FEEDBACK_SEAM_UNCHANGED is True
    assert PRODUCTIVE_PROMOTION_OPENED is False
    assert NO_AUTOMATIC_PROMOTION is True


def test_existing_n_bars_chain_still_evaluates(tmp_path: Path) -> None:
    decision = build_decision_event_v0(_decision())
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "nbars.jsonl")
    ledger.append(decision)
    horizon = produce_real_outcome_horizon_evaluation_observation_v1(
        decision, _snapshot(), economic_score="CHAIN_OK"
    )
    bundle = evaluate_offline_bundle_v0(
        decision,
        horizon["evaluation_observation"],
        identity=_identity(),
        ledger=ledger,
    )
    state = ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id="ddo.lscope.mi-regression",
        outcome=bundle["outcome_record"],
        attribution=bundle["attribution_record"],
        counterfactual=bundle["counterfactual_record"],
        event_time_utc="2026-09-01T15:00:00Z",
        correlation_id=str(bundle["outcome_record"]["record_id"]),
    )
    assert state["learning_state_record"]["next_cycle_economic_score_label"] == "CHAIN_OK"
