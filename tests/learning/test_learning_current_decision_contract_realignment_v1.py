"""Slice 1: Learning current decision contract realignment — join resolver v1."""

from __future__ import annotations

import ast
import copy
from pathlib import Path
from typing import Any

import pytest

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    LEARNING_PRODUCTIVE_AUTHORITY,
    PROMOTION_AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
)
from src.learning.deterministic_decision_outcome_v0.contract_registry_v0 import (
    CONTRACT_REGISTRY_V0,
)
from src.learning.deterministic_decision_outcome_v0.current_decision_learning_binding_v1 import (
    BINDING_ID,
    RESOLVER_ID,
    CurrentDecisionLearningBindingError,
    records_index_from_sequence_v1,
    resolve_current_double_play_decision_bundle_v1,
)
from src.learning.deterministic_decision_outcome_v0.double_play_observation_projection_v1 import (
    generic_decision_result_for_producer_outcome_v1,
    generic_decision_type_for_producer_outcome_v1,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.lineage_v0 import (
    verify_double_play_decision_triple_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitPolicyDecisionV0,
    serialize_entry_exit_policy_decision_canonical,
)
from tests.learning.test_ddo_current_double_play_decision_capture_parity_v1 import (
    FORBIDDEN_IMPORT_PREFIXES,
    TRADE_OUTCOMES,
    _capture,
    _decision_events,
    _enter_long,
    _enter_short,
    _exit_non_none,
    _hold,
    _observations,
    _reduce,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BINDING_PATH = (
    REPO_ROOT
    / "src/learning/deterministic_decision_outcome_v0/current_decision_learning_binding_v1.py"
)
AUTHORITY_PATH = REPO_ROOT / "src/learning/deterministic_decision_outcome_v0/authority_v0.py"


def _index_from_capture(binding) -> dict[str, dict[str, Any]]:
    return records_index_from_sequence_v1(tuple(binding.captured_records))


def _resolve_enter_long_binding():
    binding = _capture(_enter_long())
    events = _decision_events(binding)
    assert len(events) == 1
    de_ref = events[0]["record_id"]
    bundle = resolve_current_double_play_decision_bundle_v1(
        records_by_id=_index_from_capture(binding),
        decision_event_ref=de_ref,
    )
    return binding, de_ref, bundle


def test_registry_exposes_current_decision_learning_roles_v1() -> None:
    roles = CONTRACT_REGISTRY_V0["current_decision_learning_roles_v1"]
    assert roles["binding_id"] == BINDING_ID
    assert roles["resolver_id"] == RESOLVER_ID
    assert roles["decision_event_is_envelope_only"] is True


def test_t4_actionable_outcomes_preserved_in_observation_payload() -> None:
    cases = [
        (_enter_long(), DecisionOutcome.ENTER_LONG.value),
        (_enter_short(), DecisionOutcome.ENTER_SHORT.value),
        (_exit_non_none(), DecisionOutcome.EXIT.value),
        (_hold(), DecisionOutcome.HOLD.value),
        (_reduce(), DecisionOutcome.REDUCE.value),
    ]
    for decision, expected in cases:
        binding = _capture(decision)
        obs = _observations(binding)
        assert len(obs) == 1
        payload = obs[0]["producer_canonical_payload"]
        assert payload["decision_outcome"] == expected
        assert expected in TRADE_OUTCOMES


def test_t5_decision_event_unknown_does_not_reconstruct_semantics() -> None:
    binding, de_ref, bundle = _resolve_enter_long_binding()
    de = _decision_events(binding)[0]
    assert de["producer_id"] == "double_play_entry_exit_policy_v0"
    producer_outcome = str(
        _observations(binding)[0]["producer_canonical_payload"]["decision_outcome"]
    )
    mapped_type = generic_decision_type_for_producer_outcome_v1(producer_outcome)
    mapped_result = generic_decision_result_for_producer_outcome_v1(producer_outcome)
    if producer_outcome in {"enter_long", "enter_short", "exit", "hold", "reduce"}:
        assert mapped_type == UNKNOWN or mapped_result == UNKNOWN
    assert bundle.authoritative_decision_outcome == producer_outcome
    assert bundle.authoritative_decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert de_ref == bundle.decision_event_ref


def test_t6_deterministic_join_identity() -> None:
    binding, de_ref, bundle_a = _resolve_enter_long_binding()
    index = _index_from_capture(binding)
    bundle_b = resolve_current_double_play_decision_bundle_v1(
        records_by_id=index,
        decision_event_ref=de_ref,
    )
    assert bundle_a == bundle_b
    triple = verify_double_play_decision_triple_v1(
        existing_by_id=index,
        decision_event_ref=de_ref,
    )
    assert triple == bundle_a


def test_t7_missing_observation_fail_closed() -> None:
    binding, de_ref, _ = _resolve_enter_long_binding()
    index = _index_from_capture(binding)
    de_only = {de_ref: index[de_ref]}
    with pytest.raises(CurrentDecisionLearningBindingError) as exc:
        resolve_current_double_play_decision_bundle_v1(
            records_by_id=de_only,
            decision_event_ref=de_ref,
        )
    assert exc.value.failure_code == "SIBLING_OBSERVATION_ABSENT"


def test_t8_ambiguous_observation_fail_closed() -> None:
    binding, de_ref, _ = _resolve_enter_long_binding()
    index = _index_from_capture(binding)
    obs = [
        row
        for row in index.values()
        if row.get("schema_name") == "double_play_entry_exit_observation"
    ]
    dup = copy.deepcopy(obs[0])
    dup["record_id"] = "ddo.dpo.dup.ambiguous"
    index[dup["record_id"]] = dup
    with pytest.raises(CurrentDecisionLearningBindingError) as exc:
        resolve_current_double_play_decision_bundle_v1(
            records_by_id=index,
            decision_event_ref=de_ref,
        )
    assert exc.value.failure_code == "SIBLING_OBSERVATION_AMBIGUOUS"


def test_t9_semantic_digest_mismatch_fail_closed() -> None:
    binding, de_ref, _ = _resolve_enter_long_binding()
    index = _index_from_capture(binding)
    for row in index.values():
        if row.get("schema_name") == "double_play_entry_exit_observation":
            row["semantic_digest"] = "0" * 64
    with pytest.raises((CurrentDecisionLearningBindingError, DdoValidationError)):
        resolve_current_double_play_decision_bundle_v1(
            records_by_id=index,
            decision_event_ref=de_ref,
        )


def test_t10_binding_module_forbidden_imports() -> None:
    tree = ast.parse(BINDING_PATH.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module
            if any(mod.startswith(prefix) for prefix in FORBIDDEN_IMPORT_PREFIXES):
                hits.append(mod)
    assert hits == []


def test_t11_authority_v0_unchanged() -> None:
    assert RUNTIME_EFFECT == "NONE"
    assert PROMOTION_AUTHORITY_EFFECT == "NONE"
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    text = AUTHORITY_PATH.read_text(encoding="utf-8")
    assert "MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY" in text
    assert "CAPTURE_RUNTIME_EFFECT" in text


def test_producer_canonical_serialization_unchanged_enter_long() -> None:
    decision = _enter_long()
    raw = serialize_entry_exit_policy_decision_canonical(decision)
    assert isinstance(raw, str)
    assert "enter_long" in raw
    assert isinstance(decision, EntryExitPolicyDecisionV0)
