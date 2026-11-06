"""Stored producer observations and DecisionEvent parents must agree before Pending."""
from dataclasses import replace

import pytest

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    DdoCaptureBindingV0, SEAM_DOUBLE_PLAY_ENTRY_EXIT, observe_producer_result_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.ops.full_core_live_path_composition_root_v1.current_productive_pending_decision_context_v1 import pending_decision_context_from_invocation_v1
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.creation_v1 import maybe_create_natural_enter_pending_outcome_v1
from scripts.ops.pre_external_convergence_natural_enter_reporting_v1 import evaluate_natural_enter_reporting_v1
from types import SimpleNamespace
from tests.ops.test_pending_exact_decision_context_v1 import _invocation


def _setup(tmp_path):
    inv = _invocation()
    context = pending_decision_context_from_invocation_v1(inv)
    root = tmp_path / "lane"
    path = root / "LANE_1/ddo_learning_capture_v1.jsonl"
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=path)
    observed = observe_producer_result_v0(
        binding, seam_id=SEAM_DOUBLE_PLAY_ENTRY_EXIT,
        result=inv.cycle_result.replay.intermediate.entry_exit_decision,
        event_time_utc="2026-11-04T10:00:00Z", correlation_id="ddo.corr.test",
        cycle_id=context.cycle_id, repository_sha="85491657b",
    )
    assert observed["ok"]
    reporting = evaluate_natural_enter_reporting_v1(
        cycle_records=[SimpleNamespace(cycle_index=1, s5_disposition="PRE_EXTERNAL_EFFECT", pending_decision_context=context)],
        terminal_disposition="PRE_EXTERNAL_EFFECT", ddo_jsonl=path,
    )
    assert reporting.natural_pre_external_reached
    args = dict(lane_state_root=root, reporting=reporting, run_id="offline-parent-contract",
                evidence_root=tmp_path / "evidence", canonical_instrument_id=context.instrument_id,
                native_id=context.native_id, decision_timestamp_unix=context.decision_timestamp_unix,
                decision_reference_price=context.reference_price, market_context_ref=context.market_context_ref)
    return path, args


def _rewrite_records(path, mutate):
    records = [dict(rec) for rec in AppendOnlyDdoLedgerV0(path).read_all()]
    mutate(records)
    path.unlink()  # isolated test data only; exercise valid schema/chain with wrong semantic parent
    for record in records:
        record.pop("content_hash", None)
        AppendOnlyDdoLedgerV0(path).append(record)


def test_actual_capture_generic_unknown_parent_is_valid(tmp_path):
    path, args = _setup(tmp_path)
    parent = AppendOnlyDdoLedgerV0(path).get(args["reporting"].dpo["decision_event_ref"])
    assert parent["decision_type"] == "UNKNOWN"
    assert args["reporting"].dpo["execution_eligible"] == "false"
    out = maybe_create_natural_enter_pending_outcome_v1(**args)
    assert out.created
    assert out.record.market_context_ref == args["market_context_ref"]


@pytest.mark.parametrize("field,value", [
    ("cycle_id", "another-cycle"), ("correlation_id", "ddo.corr.other"),
    ("event_time_utc", "2026-11-04T09:00:00Z"), ("producer_id", "wrong-producer"),
    ("authority_owner", "wrong-owner"), ("decision_type", "NO_ENTRY"),
    ("decision_result", "NO_ACTION"),
])
def test_valid_ledger_with_foreign_or_contradictory_parent_is_rejected(tmp_path, field, value):
    path, args = _setup(tmp_path)
    parent_ref = args["reporting"].dpo["decision_event_ref"]
    def mutate(records):
        parent = next(rec for rec in records if rec["record_id"] == parent_ref)
        assert parent[field] != value
        parent[field] = value
    _rewrite_records(path, mutate)
    out = maybe_create_natural_enter_pending_outcome_v1(**args)
    assert out.reason == "PENDING_DECISION_LINEAGE_UNBOUND" and not out.created
    assert not list(path.parent.glob("*pending*"))


def test_missing_parent_is_rejected(tmp_path):
    path, args = _setup(tmp_path)
    path.rename(path.with_suffix(".original"))
    assert maybe_create_natural_enter_pending_outcome_v1(**args).reason == "PENDING_DECISION_LINEAGE_UNBOUND"


def test_corrupt_owner_ledger_is_rejected_without_repair(tmp_path):
    path, args = _setup(tmp_path)
    before = path.read_bytes()[:-1]
    path.write_bytes(before)
    assert maybe_create_natural_enter_pending_outcome_v1(**args).reason == "PENDING_DECISION_LINEAGE_UNBOUND"
    assert path.read_bytes() == before


@pytest.mark.parametrize("field,value", [("native_id", "other"), ("canonical_instrument_id", "other"),
    ("decision_reference_price", 999.0), ("decision_timestamp_unix", 1793786402.0), ("market_context_ref", "other")])
def test_context_cannot_be_paired_with_different_pending_inputs(tmp_path, field, value):
    _, args = _setup(tmp_path)
    args[field] = value
    assert maybe_create_natural_enter_pending_outcome_v1(**args).reason == "PENDING_DECISION_LINEAGE_UNBOUND"


def test_report_side_cannot_override_exact_producer(tmp_path):
    _, args = _setup(tmp_path)
    args["reporting"] = replace(args["reporting"], enter_side="SHORT")
    assert maybe_create_natural_enter_pending_outcome_v1(**args).reason == "PENDING_DECISION_LINEAGE_UNBOUND"
