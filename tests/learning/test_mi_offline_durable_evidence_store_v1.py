"""Contract tests for MI offline durable evidence store."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_persist_v1 import (
    PERSIST_STATUS_APPENDED,
    PERSIST_STATUS_IDEMPOTENT,
    MiOfflineDurableEvidencePersistRequestV1,
    persist_mi_offline_durable_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_record_v1 import (
    MiOfflineDurableEvidenceValidationError,
    build_mi_offline_durable_evidence_record_v1,
    validate_mi_offline_durable_evidence_record_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_store_v1 import (
    MiOfflineDurableEvidenceStoreV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_orchestrator_v1 import (
    OfflineForecastScenarioV1,
    OfflineOrchestratorInputV1,
    run_market_intelligence_offline_orchestrator_cycle_v1,
)
from tests.learning.test_unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1 import (
    _directional_payload,
    _observation_for_n,
)


def _scenario(*, info_ref: str) -> OfflineForecastScenarioV1:
    obs = _observation_for_n(n_bars=2)
    return OfflineForecastScenarioV1(
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


def _triad(tmp_path: Path, *, info_ref: str) -> tuple[dict, dict, dict]:
    obs = _observation_for_n(n_bars=2)
    result = run_market_intelligence_offline_orchestrator_cycle_v1(
        OfflineOrchestratorInputV1(
            scenarios=[_scenario(info_ref=info_ref)],
            evaluation_observations_by_n_bars={2: obs},
        )
    )
    return result["forecasts"][0], result["calibrations"][0], result["research_projections"][0]


def test_write_restart_read_replay_preserves_semantics(tmp_path: Path) -> None:
    forecast, calib, research = _triad(tmp_path, info_ref="durable.restart")
    store_root = tmp_path / "mi_offline_durable"
    first = persist_mi_offline_durable_evidence_v1(
        store_root,
        MiOfflineDurableEvidencePersistRequestV1(
            forecast_evidence=forecast,
            calibration_evidence=calib,
            research_evidence=research,
        ),
    )
    assert first["persist_status"] == PERSIST_STATUS_APPENDED
    restarted = MiOfflineDurableEvidenceStoreV1(store_root)
    loaded = restarted.get(str(first["durable_evidence_id"]))
    assert loaded["forecast_evidence_id"] == forecast["forecast_evidence_id"]
    assert loaded["research_evidence_id"] == research["research_evidence_id"]
    assert loaded["content_digest"] == first["content_digest"]
    assert loaded["forecast_evidence"]["content_digest"] == forecast["content_digest"]
    assert loaded["market_state_refs"] == forecast["market_state_refs"]
    assert loaded["outcome_horizon_end_utc"] == forecast["outcome_horizon_end_utc"]


def test_identical_input_deterministic_identity(tmp_path: Path) -> None:
    forecast, calib, research = _triad(tmp_path, info_ref="durable.ident")
    a = build_mi_offline_durable_evidence_record_v1(
        forecast_evidence=forecast,
        calibration_evidence=calib,
        research_evidence=research,
    )
    b = build_mi_offline_durable_evidence_record_v1(
        forecast_evidence=forecast,
        calibration_evidence=calib,
        research_evidence=research,
    )
    assert a["durable_evidence_id"] == b["durable_evidence_id"]
    assert a["content_digest"] == b["content_digest"]


def test_idempotent_append_and_divergent_fail_closed(tmp_path: Path) -> None:
    forecast, calib, research = _triad(tmp_path, info_ref="durable.idem")
    store_root = tmp_path / "store"
    request = MiOfflineDurableEvidencePersistRequestV1(
        forecast_evidence=forecast,
        calibration_evidence=calib,
        research_evidence=research,
    )
    first = persist_mi_offline_durable_evidence_v1(store_root, request)
    second = persist_mi_offline_durable_evidence_v1(store_root, request)
    assert second["persist_status"] == PERSIST_STATUS_IDEMPOTENT
    assert first["durable_evidence_id"] == second["durable_evidence_id"]
    assert first["deterministic_replay_equal"] is True

    store = MiOfflineDurableEvidenceStoreV1(store_root)
    mutated = dict(store.get(str(first["durable_evidence_id"])))
    mutated["provenance"] = {"tampered": True}
    with pytest.raises(MiOfflineDurableEvidenceValidationError):
        store.append(mutated)


def test_corrupt_and_stale_schema_fail_closed(tmp_path: Path) -> None:
    forecast, calib, research = _triad(tmp_path, info_ref="durable.corrupt")
    record = build_mi_offline_durable_evidence_record_v1(
        forecast_evidence=forecast,
        calibration_evidence=calib,
        research_evidence=research,
    )
    with pytest.raises(MiOfflineDurableEvidenceValidationError):
        validate_mi_offline_durable_evidence_record_v1(
            {**dict(record), "schema_version": "mi_offline_durable_evidence_record_v0"}
        )
    with pytest.raises(MiOfflineDurableEvidenceValidationError):
        validate_mi_offline_durable_evidence_record_v1({**dict(record), "content_digest": "0" * 64})

    store_root = tmp_path / "corrupt_store"
    persist_mi_offline_durable_evidence_v1(
        store_root,
        MiOfflineDurableEvidencePersistRequestV1(
            forecast_evidence=forecast,
            calibration_evidence=calib,
            research_evidence=research,
        ),
    )
    store = MiOfflineDurableEvidenceStoreV1(store_root)
    path = store._record_path(str(record["durable_evidence_id"]))
    broken = json.loads(path.read_text(encoding="utf-8"))
    broken["forecast_evidence"]["content_digest"] = "f" * 64
    path.write_text(json.dumps(broken), encoding="utf-8")
    with pytest.raises(MiOfflineDurableEvidenceValidationError):
        store.get(str(record["durable_evidence_id"]))


def test_canonical_list_ordering_deterministic(tmp_path: Path) -> None:
    store_root = tmp_path / "ordered"
    for label in ("z", "a", "m"):
        forecast, calib, research = _triad(tmp_path / label, info_ref=f"durable.order.{label}")
        persist_mi_offline_durable_evidence_v1(
            store_root,
            MiOfflineDurableEvidencePersistRequestV1(
                forecast_evidence=forecast,
                calibration_evidence=calib,
                research_evidence=research,
            ),
        )
    store = MiOfflineDurableEvidenceStoreV1(store_root)
    first = [r["durable_evidence_id"] for r in store.list_records()]
    second = [r["durable_evidence_id"] for r in store.list_records()]
    assert first == second
    assert first == sorted(first)


def test_orchestrator_persists_and_reloads_by_forecast_id(tmp_path: Path) -> None:
    obs = _observation_for_n(n_bars=2)
    store_root = tmp_path / "orch_store"
    result = run_market_intelligence_offline_orchestrator_cycle_v1(
        OfflineOrchestratorInputV1(
            scenarios=[_scenario(info_ref="durable.orch")],
            evaluation_observations_by_n_bars={2: obs},
            mi_offline_durable_evidence_store_root=store_root,
        )
    )
    traces = result["mi_offline_durable_evidence_persist"]
    assert len(traces) == 1
    assert traces[0]["persist_status"] == PERSIST_STATUS_APPENDED
    store = MiOfflineDurableEvidenceStoreV1(store_root)
    loaded = store.get_by_forecast_evidence_id(result["forecasts"][0]["forecast_evidence_id"])
    assert loaded is not None
    assert (
        loaded["research_evidence_id"] == result["research_projections"][0]["research_evidence_id"]
    )
