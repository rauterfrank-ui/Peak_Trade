"""Loop-B durable MI store + Phase-10 multi-cycle durable replay integration."""

from __future__ import annotations

import hashlib
from pathlib import Path

from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    WORKING_TREE_CLEAN,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
from src.experiments.canonical_failure_memory_v1 import (
    CanonicalFailureMemoryRecordRequestV1,
    build_canonical_failure_memory_record_v1,
)
from src.experiments.canonical_unified_blueprint_mi_crossing_bounded_multi_cycle_offline_replay_v1 import (
    REPLAY_STATUS_COMPLETE,
    MiCrossingDeterministicMultiCycleOfflineReplayRequestV1,
    MiCrossingOfflineReplayCycleInputV1,
    run_mi_crossing_deterministic_multi_cycle_offline_replay_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    CAP23_SOLE_PRODUCTIVE_SELECTION_OWNER,
    MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_store_v1 import (
    MiOfflineDurableEvidenceStoreV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_orchestrator_v1 import (
    OfflineForecastScenarioV1,
    OfflineOrchestratorInputV1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state
from tests.learning.test_unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1 import (
    _directional_payload,
    _observation_for_n,
)


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _orchestrator_input(
    tmp_path: Path,
    *,
    info_ref: str,
    durable_store: Path | None = None,
    failure_store: Path | None = None,
    failure_request: CanonicalFailureMemoryRecordRequestV1 | None = None,
) -> OfflineOrchestratorInputV1:
    obs = _observation_for_n(n_bars=2)
    legacy_state = _learning_state(tmp_path)
    legacy = export_learning_evidence_from_state_v1(legacy_state)
    return OfflineOrchestratorInputV1(
        scenarios=[
            OfflineForecastScenarioV1(
                information_set_ref=info_ref,
                forecast_created_at_utc="2026-09-01T12:00:00Z",
                outcome_horizon_end_utc="2026-09-01T14:00:00Z",
                n_bars=2,
                bar_spec_ref=str(obs["bar_spec_ref"]),
                market_state_refs=[f"mi.state.{info_ref}"],
                forecast_model_ref="mi.model.offline.v1",
                probabilistic_payload=_directional_payload(),
                realized_direction="UP",
            )
        ],
        evaluation_observations_by_n_bars={2: obs},
        learning_state_record=legacy_state,
        m4_experiment_plane_request=_plane_request(legacy),
        run_mi_enriched_m4_closure=True,
        mi_offline_durable_evidence_store_root=durable_store,
        failure_memory_store_root=failure_store,
        failure_memory_request=failure_request,
    )


def _failure_request() -> CanonicalFailureMemoryRecordRequestV1:
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
    return CanonicalFailureMemoryRecordRequestV1(
        experiment_identity=identity,
        hypothesis_id="hyp.mi.loopb.v1",
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


def test_phase_10_multi_cycle_consumes_durable_mi_evidence(tmp_path: Path) -> None:
    durable_store = tmp_path / "mi_offline_durable"
    request = MiCrossingDeterministicMultiCycleOfflineReplayRequestV1(
        cycles=(
            MiCrossingOfflineReplayCycleInputV1(
                cycle_index=0,
                orchestrator_input=_orchestrator_input(
                    tmp_path,
                    info_ref="loopb.phase10.c0",
                    durable_store=durable_store,
                ),
                replay_seed=11,
            ),
            MiCrossingOfflineReplayCycleInputV1(
                cycle_index=1,
                orchestrator_input=_orchestrator_input(
                    tmp_path,
                    info_ref="loopb.phase10.c1",
                    durable_store=durable_store,
                ),
                replay_seed=11,
            ),
        )
    )
    first = run_mi_crossing_deterministic_multi_cycle_offline_replay_v1(request)
    second = run_mi_crossing_deterministic_multi_cycle_offline_replay_v1(request)
    assert first["status"] == REPLAY_STATUS_COMPLETE
    assert first["replay_identity"] == second["replay_identity"]
    assert first["cycles"][0]["cycle_body"]["mi_offline_durable_evidence_ids"]
    assert MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY is True
    assert CAP23_SOLE_PRODUCTIVE_SELECTION_OWNER is True

    store = MiOfflineDurableEvidenceStoreV1(durable_store)
    records = store.list_records()
    assert len(records) == 2
    for cycle in first["cycles"]:
        forecast_id = cycle["cycle_body"]["mi_lineage_refs"]["forecast_evidence_id"]
        loaded = store.get_by_forecast_evidence_id(str(forecast_id))
        assert loaded is not None
        assert (
            loaded["durable_evidence_id"] in cycle["cycle_body"]["mi_offline_durable_evidence_ids"]
        )
        assert loaded["n_bars"] == 2
        assert loaded["forecast_created_at_utc"] < loaded["outcome_horizon_end_utc"]


def test_failure_memory_reuse_preserved_with_durable_store(tmp_path: Path) -> None:
    durable_store = tmp_path / "mi_offline_durable"
    failure_store = tmp_path / "failure_memory"
    failure_request = _failure_request()
    result = run_mi_crossing_deterministic_multi_cycle_offline_replay_v1(
        MiCrossingDeterministicMultiCycleOfflineReplayRequestV1(
            cycles=(
                MiCrossingOfflineReplayCycleInputV1(
                    cycle_index=0,
                    orchestrator_input=_orchestrator_input(
                        tmp_path,
                        info_ref="loopb.fm.c0",
                        durable_store=durable_store,
                        failure_store=failure_store,
                        failure_request=failure_request,
                    ),
                    replay_seed=3,
                ),
                MiCrossingOfflineReplayCycleInputV1(
                    cycle_index=1,
                    orchestrator_input=_orchestrator_input(
                        tmp_path,
                        info_ref="loopb.fm.c1",
                        durable_store=durable_store,
                    ),
                    replay_seed=3,
                ),
            )
        )
    )
    assert result["status"] == REPLAY_STATUS_COMPLETE
    assert result["cycles"][0]["failure_memory_replay"]["deterministic_replay_equal"] is True
    fm = CanonicalFailureMemoryStoreV1(failure_store)
    replay = build_canonical_failure_memory_record_v1(failure_request)
    dup = fm.assess_duplicate(hypothesis_fingerprint=str(replay["hypothesis_fingerprint"]))
    assert dup["previously_rejected"] is True
