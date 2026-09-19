"""Downstream consumer realignment to CURRENT decision learning binding v1."""

from __future__ import annotations

from typing import Any

import pytest

from src.learning.deterministic_decision_outcome_v0.challenger_v0 import (
    compare_shadow_challenger_v0,
)
from src.learning.deterministic_decision_outcome_v0.current_decision_consumer_v1 import (
    build_decision_time_evaluation_observation_v1,
)
from src.learning.deterministic_decision_outcome_v0.current_decision_learning_binding_v1 import (
    records_index_from_sequence_v1,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN, VALIDATION_GATE_IDS_V0
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.learning_records_v0 import (
    validate_candidate_artifact_v0,
)
from src.learning.deterministic_decision_outcome_v0.replay_evaluator_v0 import (
    classify_current_double_play_decision_bundle_v0,
    classify_decision_event_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from tests.learning.test_ddo_current_double_play_decision_capture_parity_v1 import (
    _capture,
    _decision_events,
    _enter_long,
    _hold,
)
from tests.learning.test_deterministic_decision_outcome_learning_validation_shadow_v0 import (
    _artifacts,
    _candidate,
    _hypothesis,
    _identity,
)
from tests.learning.test_learning_current_decision_contract_realignment_v1 import (
    _index_from_capture,
)
from src.learning.deterministic_decision_outcome_v0.validation_pack_engine_v0 import (
    evaluate_validation_evidence_pack_v0,
)


def _dp_capture_index():
    binding = _capture(_enter_long())
    index = _index_from_capture(binding)
    events = _decision_events(binding)
    assert len(events) == 1
    return binding, index, events[0]


def _evaluation_identity(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "outcome_record_id": "out-dp-eval-0001",
        "attribution_record_id": "attr-dp-eval-0001",
        "counterfactual_record_id": "cf-dp-eval-0001",
        "correlation_id": "cor-dp-eval-0001",
        "event_time_utc": "2026-09-05T12:05:00Z",
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
    }
    payload.update(overrides)
    return payload


def test_evaluate_offline_bundle_uses_authoritative_outcome_not_envelope() -> None:
    _, index, de = _dp_capture_index()
    decision = build_decision_event_v0(de)
    obs = build_decision_time_evaluation_observation_v1(
        decision_event_ref=str(de["record_id"]),
        evaluation_time_utc="2026-09-05T12:05:00Z",
    )
    bundle = evaluate_offline_bundle_v0(
        decision,
        obs,
        identity=_evaluation_identity(),
        records_by_id=index,
    )
    assert bundle["outcome_record"]["decision_score"] == DecisionOutcome.ENTER_LONG.value
    dp_replay = bundle["replay"]["current_double_play_decision"]
    assert dp_replay["authoritative_decision_outcome"] == DecisionOutcome.ENTER_LONG.value
    envelope = classify_decision_event_v0(decision)
    assert envelope["decision_type"] == UNKNOWN or envelope["decision_result"] == UNKNOWN


def test_evaluate_double_play_without_records_index_fail_closed() -> None:
    _, _, de = _dp_capture_index()
    decision = build_decision_event_v0(de)
    obs = build_decision_time_evaluation_observation_v1(
        decision_event_ref=str(de["record_id"]),
        evaluation_time_utc="2026-09-05T12:05:00Z",
    )
    with pytest.raises(
        DdoValidationError, match="DOUBLE_PLAY_SEMANTIC_EVAL_REQUIRES_RECORDS_INDEX"
    ):
        evaluate_offline_bundle_v0(decision, obs, identity=_evaluation_identity())


def test_classify_current_double_play_bundle_matches_resolver() -> None:
    _, index, de = _dp_capture_index()
    left = classify_current_double_play_decision_bundle_v0(
        records_by_id=index,
        decision_event_ref=str(de["record_id"]),
    )
    right = classify_current_double_play_decision_bundle_v0(
        records_by_id=index,
        decision_event_ref=str(de["record_id"]),
    )
    assert left == right
    assert left["authoritative_decision_outcome"] == DecisionOutcome.ENTER_LONG.value


def test_challenger_prefers_authoritative_outcome_over_collapsed_envelope() -> None:
    binding_a = _capture(_enter_long())
    binding_b = _capture(_hold())
    index_a = records_index_from_sequence_v1(tuple(binding_a.captured_records))
    index_b = records_index_from_sequence_v1(tuple(binding_b.captured_records))
    de_a = _decision_events(binding_a)[0]
    de_b = _decision_events(binding_b)[0]
    incumbent = _candidate(record_id="cand-dp-incumbent", intended_scope="incumbent")
    candidate = _candidate(record_id="cand-dp-challenger", intended_scope="challenger")
    evaluated = evaluate_validation_evidence_pack_v0(
        candidate=candidate,
        artifacts=_artifacts(),
        identity=_identity(),
        incumbent=incumbent,
    )
    comparison = compare_shadow_challenger_v0(
        incumbent=incumbent,
        candidate=candidate,
        evidence_pack=evaluated["validation_evidence_pack"],
        incumbent_decisions=[de_a],
        candidate_decisions=[de_b],
        incumbent_records_by_id=index_a,
        candidate_records_by_id=index_b,
        incumbent_gates={gate: "PASS" for gate in VALIDATION_GATE_IDS_V0},
    )
    by_id = {row["record_id"]: row for row in comparison["decision_deltas"]}
    assert by_id[str(de_a["record_id"])]["incumbent_authoritative_decision_outcome"] == (
        DecisionOutcome.ENTER_LONG.value
    )
    assert by_id[str(de_b["record_id"])]["candidate_authoritative_decision_outcome"] == (
        DecisionOutcome.HOLD.value
    )


def test_challenger_generic_envelope_path_unchanged_without_records_index() -> None:
    incumbent = validate_candidate_artifact_v0(
        _candidate(record_id="cand-dp-incumbent-2", intended_scope="incumbent")
    )
    candidate = validate_candidate_artifact_v0(_candidate())
    evaluated = evaluate_validation_evidence_pack_v0(
        candidate=candidate,
        artifacts=_artifacts(),
        identity=_identity(),
        incumbent=incumbent,
    )
    comparison = compare_shadow_challenger_v0(
        incumbent=incumbent,
        candidate=candidate,
        evidence_pack=evaluated["validation_evidence_pack"],
        incumbent_decisions=[
            {
                "record_id": "dec-generic-1",
                "decision_type": "NO_ENTRY",
                "decision_result": "NO_ACTION",
            }
        ],
        candidate_decisions=[
            {
                "record_id": "dec-generic-1",
                "decision_type": "STALE_BLOCK",
                "decision_result": "NO_ACTION",
            }
        ],
        incumbent_gates={gate: "PASS" for gate in VALIDATION_GATE_IDS_V0},
    )
    delta = comparison["decision_deltas"][0]
    assert delta["incumbent_decision_type"] == "NO_ENTRY"
    assert delta["candidate_decision_type"] == "STALE_BLOCK"
    assert delta["incumbent_authoritative_decision_outcome"] == UNKNOWN
