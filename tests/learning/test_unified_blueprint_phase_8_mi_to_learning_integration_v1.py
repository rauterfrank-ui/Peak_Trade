"""Phase 8 — typed MI forecast/outcome/calibration → learning export path."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

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
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_ingest_v1 import (
    MiLearningEvidenceIngestRequestV1,
    ingest_mi_learning_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_learning_export_v1 import (
    ROUTE_MI_TYPED_WITH_LEGACY,
    export_mi_learning_evidence_onto_learning_path_v1,
    route_learning_evidence_for_consumer_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_store_v1 import (
    MiLearningEvidenceStoreV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_to_learning_evidence_bridge_v1 import (
    MiToLearningBridgeError,
    compose_mi_to_learning_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_orchestrator_v1 import (
    OfflineForecastScenarioV1,
    OfflineOrchestratorInputV1,
    run_market_intelligence_offline_orchestrator_cycle_v1,
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


def _observation_for_n(*, n_bars: int) -> dict[str, Any]:
    snap = _snapshot(n_bars=n_bars) if n_bars != 3 else _snapshot_three_bars()
    decision = build_decision_event_v0(_decision())
    return produce_real_outcome_horizon_evaluation_observation_v1(
        decision, snap, economic_score="PHASE8_MI"
    )["evaluation_observation"]


def _mint_forecast(*, n_bars: int, bar_spec_ref: str) -> dict[str, Any]:
    return dict(
        mint_forecast_evidence_v1(
            information_set_ref="info.set.phase8",
            forecast_created_at_utc="2026-09-01T12:00:00Z",
            outcome_horizon_end_utc="2026-09-01T14:00:00Z"
            if n_bars == 2
            else "2026-09-01T15:00:00Z",
            n_bars=n_bars,
            bar_spec_ref=bar_spec_ref,
            forecast_kind="DIRECTIONAL_PROBABILITY",
            probabilistic_payload=_directional_payload(),
            market_state_refs=["mi.state.phase8"],
            forecast_model_ref="mi.model.offline.v1",
            support_disposition="SUFFICIENT_EVIDENCE",
            provenance={"source": "phase8-test"},
        )
    )


def test_forecast_identity_and_horizon_survive_join_and_export() -> None:
    obs = _observation_for_n(n_bars=2)
    forecast = _mint_forecast(n_bars=2, bar_spec_ref=str(obs["bar_spec_ref"]))
    mi_record = compose_mi_to_learning_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=obs,
        realized_direction="UP",
    )
    export = export_mi_learning_evidence_onto_learning_path_v1(mi_record)
    assert (
        export["mi_learning_evidence"]["forecast_evidence_id"] == forecast["forecast_evidence_id"]
    )
    assert export["mi_learning_evidence"]["n_bars"] == 2
    assert export["mi_learning_evidence"]["bar_spec_ref"] == obs["bar_spec_ref"]
    assert export["consumer_route"]["forecast_evidence_id"] == forecast["forecast_evidence_id"]


def test_wrong_horizon_fails_closed() -> None:
    obs = _observation_for_n(n_bars=3)
    forecast = _mint_forecast(n_bars=2, bar_spec_ref=str(obs["bar_spec_ref"]))
    with pytest.raises(MiToLearningBridgeError, match="FORECAST_N_BARS_MISMATCH"):
        compose_mi_to_learning_evidence_v1(
            forecast_evidence=forecast,
            evaluation_observation=obs,
            realized_direction="UP",
        )


def test_calibration_evidence_distinct_from_raw_forecast_and_outcome() -> None:
    obs = _observation_for_n(n_bars=2)
    forecast = _mint_forecast(n_bars=2, bar_spec_ref=str(obs["bar_spec_ref"]))
    mi_record = compose_mi_to_learning_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=obs,
        realized_direction="UP",
    )
    assert mi_record["calibration_evidence_id"].startswith("mi.calib.")
    assert mi_record["actual_outcome_ref"] == obs["actual_outcome_ref"]
    assert mi_record["calibration_evidence_digest"] != forecast["content_digest"]


def test_deterministic_mi_learning_evidence_and_export() -> None:
    obs = _observation_for_n(n_bars=2)
    forecast = _mint_forecast(n_bars=2, bar_spec_ref=str(obs["bar_spec_ref"]))
    first = compose_mi_to_learning_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=obs,
        realized_direction="UP",
    )
    second = compose_mi_to_learning_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=obs,
        realized_direction="UP",
    )
    assert first == second
    assert export_mi_learning_evidence_onto_learning_path_v1(first) == (
        export_mi_learning_evidence_onto_learning_path_v1(second)
    )


def test_learning_path_routes_legacy_and_mi_typed(tmp_path: Path) -> None:
    legacy = export_learning_evidence_from_state_v1(_learning_state(tmp_path))
    obs = _observation_for_n(n_bars=2)
    forecast = _mint_forecast(n_bars=2, bar_spec_ref=str(obs["bar_spec_ref"]))
    mi_record = compose_mi_to_learning_evidence_v1(
        forecast_evidence=forecast,
        evaluation_observation=obs,
        realized_direction="UP",
        legacy_learning_evidence_ref=str(legacy["record_id"]),
    )
    route = route_learning_evidence_for_consumer_v1(
        mi_learning_evidence=mi_record,
        legacy_learning_evidence=legacy,
    )
    assert route["consumer_route"] == ROUTE_MI_TYPED_WITH_LEGACY
    assert route["legacy_ddo_export_compatible"] is True
    assert route["productive_ddo_reducer_mutated"] is False


def test_persistence_restart_replay_and_idempotent_ingest(tmp_path: Path) -> None:
    store_root = tmp_path / "mi_learning_store"
    obs = _observation_for_n(n_bars=2)
    forecast = _mint_forecast(n_bars=2, bar_spec_ref=str(obs["bar_spec_ref"]))
    request = MiLearningEvidenceIngestRequestV1(
        forecast_evidence=forecast,
        evaluation_observation=obs,
        realized_direction="UP",
    )
    first = ingest_mi_learning_evidence_v1(store_root, request)
    second = ingest_mi_learning_evidence_v1(store_root, request)
    assert first["deterministic_replay_equal"] is True
    assert second["ingest_status"] == "IDEMPOTENT_REPLAY"
    assert first["mi_learning_evidence_id"] == second["mi_learning_evidence_id"]
    store = MiLearningEvidenceStoreV1(store_root)
    assert len(store.list_records()) == 1


def test_orchestrator_emits_mi_learning_exports(tmp_path: Path) -> None:
    obs2 = _observation_for_n(n_bars=2)
    cycle = run_market_intelligence_offline_orchestrator_cycle_v1(
        OfflineOrchestratorInputV1(
            scenarios=[
                OfflineForecastScenarioV1(
                    information_set_ref="info.set.orchestrator.phase8",
                    forecast_created_at_utc="2026-09-01T12:00:00Z",
                    outcome_horizon_end_utc="2026-09-01T14:00:00Z",
                    n_bars=2,
                    bar_spec_ref=str(obs2["bar_spec_ref"]),
                    market_state_refs=["mi.state.p8"],
                    forecast_model_ref="mi.model.v1",
                    probabilistic_payload=_directional_payload(),
                    realized_direction="UP",
                )
            ],
            evaluation_observations_by_n_bars={2: obs2},
            learning_state_record=_learning_state(tmp_path),
        )
    )
    assert len(cycle["mi_learning_evidence_exports"]) == 1
    export = cycle["mi_learning_evidence_exports"][0]
    assert (
        export["mi_learning_evidence"]["forecast_evidence_id"]
        == cycle["forecasts"][0]["forecast_evidence_id"]
    )
    assert export["promotion_authority_created"] is False


def test_productive_ddo_chain_unchanged(tmp_path: Path) -> None:
    decision = build_decision_event_v0(_decision())
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ddo-regression.jsonl")
    ledger.append(decision)
    horizon = produce_real_outcome_horizon_evaluation_observation_v1(
        decision, _snapshot(), economic_score="PHASE8_REGRESSION"
    )
    bundle = evaluate_offline_bundle_v0(
        decision,
        horizon["evaluation_observation"],
        identity=_identity(),
        ledger=ledger,
    )
    state = ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id="ddo.lscope.phase8-regression",
        outcome=bundle["outcome_record"],
        attribution=bundle["attribution_record"],
        counterfactual=bundle["counterfactual_record"],
        event_time_utc="2026-09-01T15:00:00Z",
        correlation_id=str(bundle["outcome_record"]["record_id"]),
    )
    assert state["learning_state_record"]["next_cycle_economic_score_label"] == "PHASE8_REGRESSION"
