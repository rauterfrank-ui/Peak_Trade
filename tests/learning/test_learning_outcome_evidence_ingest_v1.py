"""Behavior tests for LEARNING_OUTCOME_EVIDENCE_INGEST_V1."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_LEARNING_STATE_RECORD,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import build_decision_event_v0
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.real_outcome_horizon_productive_host_v1 import (
    produce_real_outcome_horizon_evaluation_observation_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1 import (
    ingest_evaluation_bundle_into_learning_state_v1,
    latest_learning_state_for_scope_v1,
    reduce_learning_state_transition_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.account_identity_boundary_v1 import (
    build_account_identity_record_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    run_bridge_cycle_v1,
    run_bridge_cycles_from_mids_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_snapshot_from_canonical_bar_producer_v1 import (
    materialize_o4_n_bars_bar_evidence_snapshot_v1,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _decision, _identity, _snapshot
from tests.learning.test_ddo_n_bars_productive_upstream_auto_bind_v1 import (
    _producer_with_two_gapless_finalized_bars,
)


def _bundle(tmp_path: Path):
    decision = build_decision_event_v0(_decision())
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ingest.jsonl")
    ledger.append(decision)
    horizon = produce_real_outcome_horizon_evaluation_observation_v1(
        decision, _snapshot(), economic_score="LABEL_A"
    )
    bundle = evaluate_offline_bundle_v0(
        decision,
        horizon["evaluation_observation"],
        identity=_identity(),
        ledger=ledger,
    )
    return ledger, bundle, decision


def test_deterministic_state_transition_and_idempotency(tmp_path: Path) -> None:
    ledger, bundle, _decision = _bundle(tmp_path)
    scope = "ddo.lscope.test-scope-0001"
    first = ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id=scope,
        outcome=bundle["outcome_record"],
        attribution=bundle["attribution_record"],
        counterfactual=bundle["counterfactual_record"],
        event_time_utc="2026-09-01T15:00:00Z",
        correlation_id=str(bundle["outcome_record"]["record_id"]),
    )
    second = ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id=scope,
        outcome=bundle["outcome_record"],
        attribution=bundle["attribution_record"],
        counterfactual=bundle["counterfactual_record"],
        event_time_utc="2026-09-01T15:00:00Z",
        correlation_id=str(bundle["outcome_record"]["record_id"]),
    )
    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert first["learning_state_record"]["state_version"] == 1
    assert second["learning_state_record"]["state_version"] == 1
    assert first["learning_state_record"]["next_cycle_economic_score_label"] == "LABEL_A"
    rows = [r for r in ledger.read_all() if r["schema_name"] == SCHEMA_NAME_LEARNING_STATE_RECORD]
    assert len(rows) == 1


def test_out_of_order_fail_closed(tmp_path: Path) -> None:
    decision = build_decision_event_v0(_decision())
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ingest-ooo.jsonl")
    ledger.append(decision)
    horizon_late = produce_real_outcome_horizon_evaluation_observation_v1(
        decision, _snapshot(), economic_score="LABEL_LATE"
    )
    bundle_late = evaluate_offline_bundle_v0(
        decision,
        horizon_late["evaluation_observation"],
        identity=_identity(),
        ledger=ledger,
    )
    horizon_early = produce_real_outcome_horizon_evaluation_observation_v1(
        decision, _snapshot(), economic_score="LABEL_EARLY"
    )
    bundle_early = evaluate_offline_bundle_v0(
        decision,
        horizon_early["evaluation_observation"],
        identity=_identity(),
        ledger=None,
    )
    scope = "ddo.lscope.test-scope-0002"
    ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id=scope,
        outcome=bundle_late["outcome_record"],
        attribution=bundle_late["attribution_record"],
        counterfactual=bundle_late["counterfactual_record"],
        event_time_utc=str(bundle_late["outcome_record"]["event_time_utc"]),
        correlation_id=str(bundle_late["outcome_record"]["record_id"]),
    )
    prior = latest_learning_state_for_scope_v1(ledger, state_scope_id=scope)
    assert prior is not None
    early_time = str(bundle_early["outcome_record"]["event_time_utc"])
    prior_with_advanced_cursor = dict(prior)
    prior_with_advanced_cursor["last_event_time_utc"] = "2099-01-01T00:00:00Z"
    with pytest.raises(DdoValidationError, match="LEARNING_INGEST_OUT_OF_ORDER"):
        reduce_learning_state_transition_v1(
            state_scope_id=scope,
            bundle={
                "outcome": bundle_early["outcome_record"],
                "attribution": bundle_early["attribution_record"],
                "counterfactual": bundle_early["counterfactual_record"],
            },
            prior_state=prior_with_advanced_cursor,
            record_id="ls.test.outoforder0001",
            event_time_utc=early_time,
            correlation_id="ddo.corr.outoforder0001",
            cycle_id=None,
        )


def test_ledger_reopen_reconstructs_latest_learning_state(tmp_path: Path) -> None:
    ledger, bundle, _decision = _bundle(tmp_path)
    scope = "ddo.lscope.test-scope-reopen01"
    ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id=scope,
        outcome=bundle["outcome_record"],
        attribution=bundle["attribution_record"],
        counterfactual=bundle["counterfactual_record"],
        event_time_utc=str(bundle["outcome_record"]["event_time_utc"]),
        correlation_id=str(bundle["outcome_record"]["record_id"]),
    )
    ledger_path = tmp_path / "ingest.jsonl"
    reopened = AppendOnlyDdoLedgerV0(ledger_path)
    reconstructed = latest_learning_state_for_scope_v1(reopened, state_scope_id=scope)
    assert reconstructed is not None
    assert reconstructed["next_cycle_economic_score_label"] == "LABEL_A"


def test_productive_closed_loop_two_cycles_feedback(tmp_path: Path) -> None:
    account = build_account_identity_record_v1(
        account_identity="acct-closed-loop",
        venue="OKX",
        credential_ref_id="cred-closed-loop",
        account_scope="trading-only",
        expected_uid="acct-closed-loop",
    )
    t0 = 1_756_732_800.0
    common = dict(
        session_id="closed-loop-session",
        require_selection_binding=False,
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=account,
        ddo_n_bars_horizon_n_bars=2,
        ddo_n_bars_economic_score="LEARN_LABEL_01",
        ddo_n_bars_evaluation_identity=_identity(),
    )
    state, _ = run_bridge_cycles_from_mids_v1([3500.0], start_ts_unix=t0, **common)
    for mid, ts in [(3510.0, t0 + 3600.0), (3520.0, t0 + 7200.0), (3530.0, t0 + 10800.0)]:
        run_bridge_cycle_v1(
            state,
            mid_price=mid,
            event_ts_unix=ts,
            force_observation_event_time=ts,
            session_id=common["session_id"],
            ddo_durable_evidence_runtime_state_root=tmp_path,
            ddo_evidence_environment=ExecutionEnvironment.DEV,
            ddo_account_identity_record=account,
        )
    first_label = (state.last_ddo_learning_state or {}).get("next_cycle_economic_score_label")
    assert state.last_ddo_learning_outcome_ingest is not None
    assert state.last_ddo_learning_outcome_ingest.get("ok") is True
    assert first_label == "LEARN_LABEL_01"

    prior_version = int(state.last_ddo_learning_state["state_version"])
    run_bridge_cycle_v1(
        state,
        mid_price=3540.0,
        event_ts_unix=t0 + 14400.0,
        force_observation_event_time=t0 + 14400.0,
        session_id=common["session_id"],
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=account,
    )
    assert state.ddo_n_bars_economic_score == first_label
    assert state.last_ddo_learning_state is not None
    assert int(state.last_ddo_learning_state["state_version"]) >= prior_version
