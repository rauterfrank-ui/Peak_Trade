"""Tests for learning evidence export v1."""

from __future__ import annotations

from pathlib import Path

from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import build_decision_event_v0
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    EXPORT_ID,
    export_learning_evidence_from_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1 import (
    ingest_evaluation_bundle_into_learning_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_productive_host_v1 import (
    produce_real_outcome_horizon_evaluation_observation_v1,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _decision, _identity, _snapshot


def _learning_state(tmp_path: Path):
    decision = build_decision_event_v0(_decision())
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "lev.jsonl")
    ledger.append(decision)
    horizon = produce_real_outcome_horizon_evaluation_observation_v1(
        decision, _snapshot(), economic_score="LABEL_EXPORT"
    )
    bundle = evaluate_offline_bundle_v0(
        decision,
        horizon["evaluation_observation"],
        identity=_identity(),
        ledger=ledger,
    )
    state = ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id="ddo.lscope.export-test",
        outcome=bundle["outcome_record"],
        attribution=bundle["attribution_record"],
        counterfactual=bundle["counterfactual_record"],
        event_time_utc="2026-09-01T15:00:00Z",
        correlation_id=str(bundle["outcome_record"]["record_id"]),
    )
    return state["learning_state_record"]


def test_export_is_deterministic_and_preserves_opaque_tokens(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    first = export_learning_evidence_from_state_v1(state)
    second = export_learning_evidence_from_state_v1(state)
    assert first == second
    assert first["producer_id"] == EXPORT_ID
    assert first["economic_score_label"] == "LABEL_EXPORT"
    assert first["universe_class"] == "SELF_LEARNING_UNIVERSE"
    assert first["evidence_class"] == "LEARNING_EVIDENCE"
    assert first["productive_authority"] == "NONE"
    assert first["can_deploy"] is False
    assert first["source_learning_state_record_ref"] == state["record_id"]


def test_export_record_id_stable_for_same_state(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    a = export_learning_evidence_from_state_v1(state)
    b = export_learning_evidence_from_state_v1(state, event_time_utc="2026-09-01T16:00:00Z")
    assert a["record_id"] == b["record_id"]
