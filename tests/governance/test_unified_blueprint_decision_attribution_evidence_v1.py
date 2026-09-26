"""Phase 14 decision attribution evidence — authority and fail-closed proofs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.governance.unified_blueprint_decision_attribution_evidence_v1 import (
    ATTRIBUTION_AUTHORITY,
    CAP23_SELECTION_OWNER_REF,
    COMPOSE_REFERENCES_DONT_DUPLICATE_OWNERSHIP,
    DECISION_AUTHORITY_DUPLICATED,
    DecisionAttributionDisposition,
    DecisionAttributionEvidenceRequestV1,
    NO_SELF_DEPLOY,
    OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE,
    OPTIMIZATION_PROMOTION_AUTHORITY,
    TRADING_DECISION_AUTHORITY_OWNER_REF,
    build_decision_attribution_evidence_v1,
    ingest_decision_attribution_to_learning_state_v1,
    replay_decision_attribution_evidence_v1,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_engine_v1 import (
    supply_n_bars_evaluation_observation_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.constants_v1 import (
    PRODUCTIVE_SELECTION_OWNER,
)
from trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1 import (
    LEARNING_CORE_MUTATION_AUTHORITY,
    OPTIMIZATION_CORE_MUTATION_AUTHORITY,
    TRADING_DECISION_AUTHORITY_OWNER,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _decision(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_name": "decision_event",
        "schema_version": "decision_event_v0",
        "record_id": "dec-p14-0001",
        "event_id": "evt-p14-0001",
        "correlation_id": "cor-p14-0001",
        "cycle_id": None,
        "event_time_utc": "2026-09-01T12:00:00Z",
        "decision_type": "NO_ENTRY",
        "decision_result": "NO_ACTION",
        "reason_codes": [],
        "hard_block_reasons": [],
        "decision_time_information_set_ref": "info-set-p14-1",
        "market_snapshot_ref": None,
        "feature_snapshot_ref": None,
        "data_quality_ref": None,
        "risk_snapshot_ref": None,
        "position_snapshot_ref": "sel-future-ref-1",
        "selected_instrument_ref": "sel-future-ref-1",
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
        "authority_owner": UNKNOWN,
        "producer_id": "offline-test-producer",
        "evidence_hash": UNKNOWN,
        "causal_parent_ids": [],
        "evidence_source_refs": ["src-evidence-p14-1"],
    }
    payload.update(overrides)
    return payload


def _identity(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "outcome_record_id": "out-p14-0001",
        "attribution_record_id": "attr-p14-0001",
        "counterfactual_record_id": "cf-p14-0001",
        "correlation_id": "cor-p14-0001",
        "event_time_utc": "2026-09-01T13:00:00Z",
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
    }
    payload.update(overrides)
    return payload


def _n_bars_supplier(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "horizon_start_time_utc": "2026-09-01T12:00:00Z",
        "instrument_ref": "inst:btc-usdt",
        "bar_spec_ref": "bar:1h",
        "n_bars": 2,
        "horizon_observation_status": "OK",
        "outcome_scalar_kind": "LOG_RETURN",
        "bar_close_times_utc": ["2026-09-01T13:00:00Z", "2026-09-01T14:00:00Z"],
        "bar_identity_refs": ["bar-close-1", "bar-close-2"],
        "evaluation_time_information_set_ref": "eval-info-set-p14-1",
        "actual_outcome_ref": "evidence/outcome-measurement-p14",
        "economic_score": "LABEL_OPAQUE_P14",
    }
    payload.update(overrides)
    return payload


def _attributed_bundle():
    decision = build_decision_event_v0(_decision())
    obs = supply_n_bars_evaluation_observation_v1(decision, _n_bars_supplier())
    req = DecisionAttributionEvidenceRequestV1(
        decision_event=decision,
        evaluation_observation=obs,
        evaluation_identity=_identity(),
        side_state_ref="side-state-ref-1",
        bull_bear_state_ref="bull-bear-ref-1",
    )
    return build_decision_attribution_evidence_v1(req), req, decision


def test_authority_invariants_preserved() -> None:
    assert COMPOSE_REFERENCES_DONT_DUPLICATE_OWNERSHIP is True
    assert ATTRIBUTION_AUTHORITY == "NONE"
    assert DECISION_AUTHORITY_DUPLICATED is False
    assert OPTIMIZATION_PROMOTION_AUTHORITY == "NONE"
    assert OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE is False
    assert NO_SELF_DEPLOY is True
    assert CAP23_SELECTION_OWNER_REF == PRODUCTIVE_SELECTION_OWNER
    assert TRADING_DECISION_AUTHORITY_OWNER_REF == TRADING_DECISION_AUTHORITY_OWNER
    assert OPTIMIZATION_CORE_MUTATION_AUTHORITY == "NONE"
    assert LEARNING_CORE_MUTATION_AUTHORITY == "NONE"


def test_n_bars_realized_outcome_attribution_composes_references_only() -> None:
    result, _, decision = _attributed_bundle()
    assert result.disposition == DecisionAttributionDisposition.ATTRIBUTED
    assert result.decision_attribution_evidence is not None
    ev = result.decision_attribution_evidence
    assert ev["compose_references_dont_duplicate_ownership"] is True
    assert ev["attribution_authority"] == "NONE"
    assert ev["decision_event_ref"] == decision["record_id"]
    assert ev["realized_outcome_ref"] == "evidence/outcome-measurement-p14"
    assert result.offline_evaluation_bundle is not None
    assert result.offline_evaluation_bundle["trading_core_reachable"] is False


def test_proposal_alone_cannot_authorize_trading() -> None:
    """Attribution evidence does not mint trading authority fields."""
    result, _, _ = _attributed_bundle()
    ev = result.decision_attribution_evidence
    assert ev is not None
    assert ev.get("promotion_authority", "NONE") == "NONE"
    assert ev.get("trading_decision_payload") is None


def test_missing_decision_ref_fail_closed() -> None:
    decision = build_decision_event_v0(_decision())
    obs = supply_n_bars_evaluation_observation_v1(decision, _n_bars_supplier())
    obs_bad = dict(obs)
    obs_bad["decision_event_ref"] = "dec-other"
    result = build_decision_attribution_evidence_v1(
        DecisionAttributionEvidenceRequestV1(
            decision_event=decision,
            evaluation_observation=obs_bad,
            evaluation_identity=_identity(),
        )
    )
    assert result.disposition == DecisionAttributionDisposition.REJECTED
    assert "DECISION_EVENT_REF_MISMATCH" in result.reason_codes


def test_horizon_lookahead_rejected() -> None:
    decision = build_decision_event_v0(_decision())
    with pytest.raises(Exception):
        supply_n_bars_evaluation_observation_v1(
            decision,
            _n_bars_supplier(horizon_start_time_utc="2026-09-01T11:00:00Z"),
        )


def test_replay_deterministic() -> None:
    result, req, _ = _attributed_bundle()
    assert replay_decision_attribution_evidence_v1(req, result)


def test_learning_ingest_evidence_only(tmp_path: Path) -> None:
    result, req, _ = _attributed_bundle()
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ledger.jsonl")
    bundle = result.offline_evaluation_bundle
    assert bundle is not None
    ledger.append(dict(req.decision_event))
    ledger.append(dict(bundle["outcome_record"]))
    ledger.append(dict(bundle["attribution_record"]))
    ledger.append(dict(bundle["counterfactual_record"]))
    ingest = ingest_decision_attribution_to_learning_state_v1(
        ledger=ledger,
        attribution_result=result,
        session_id="session-p14",
        event_time_utc="2026-09-01T13:00:00Z",
        correlation_id="cor-p14-0001",
    )
    assert ingest["ok"] is True
    assert ingest["external_effect_authorized"] is False
    state = ingest["learning_state_record"]
    assert state.get("can_auto_promote") is False
    assert state.get("can_mutate_core") is False


def test_side_state_and_cap23_remain_references() -> None:
    result, _, _ = _attributed_bundle()
    ev = result.decision_attribution_evidence
    assert ev is not None
    assert ev["side_state_ref"] == "side-state-ref-1"
    assert ev["cap23_selection_owner_ref"] == PRODUCTIVE_SELECTION_OWNER
    assert ev["selected_instrument_ref"] == "sel-future-ref-1"
