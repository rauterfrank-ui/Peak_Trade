"""Actual standing supervisor startup recovers original N1 consumer evidence."""

from dataclasses import replace
import json
from pathlib import Path

import pytest

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DuplicateLaneAssignmentWriterError,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1 import (
    addressing_join_v1 as addressing,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1 import (
    consumer_completion_v1 as completion,
)
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
    run_productive_full_autonomy_n5_runtime_orchestrator_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.startup_binding_v1 import (
    PostCloseStartupRecoveryRequestV1,
    recover_post_close_before_runtime_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    StandingSupervisorConfigV1,
    run_n1_standing_pre_external_supervisor_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops import test_productive_n1_post_close_continuation_v1 as source
from tests.ops import test_n1_standing_pre_external_runtime_supervisor_v1 as standing
from tests.ops.test_portfolio_budget_host_v1 import _fetch


@pytest.fixture
def startup_case(tmp_path, monkeypatch):
    state = tmp_path / "kill.json"
    state.write_text('{"state":"ACTIVE"}')
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(state))
    host_root = tmp_path / "private_store" / "portfolio_budget_host_v1"
    (tmp_path / "transition").mkdir()
    args, owner, writer, _ = source._fixture(
        tmp_path / "transition", monkeypatch, budget_root=host_root / "owner"
    )
    calls = []
    original_core = addressing.run_current_productive_master_v2_runtime_cycle_v1

    def counted(**kwargs):
        calls.append(kwargs["cycle_id"])
        return original_core(**kwargs)

    monkeypatch.setattr(addressing, "run_current_productive_master_v2_runtime_cycle_v1", counted)
    original_link = completion.os.link
    first = True

    def interrupted(src, dst, *a, **kw):
        nonlocal first
        if (
            first
            and Path(dst).parent.name == completion.DIRECTORY
            and not str(dst).endswith(".pending.json")
        ):
            first = False
            raise OSError("prepared original output; restart before publication")
        return original_link(src, dst, *a, **kw)

    monkeypatch.setattr(completion.os, "link", interrupted)
    with pytest.raises(OSError, match="restart before publication"):
        run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
    receipt = next(writer.state_root.glob("post_close/*.json"))
    record = json.loads(receipt.read_text())
    bound = BoundInstrumentV1(**record["bound_by_lane"]["LANE_1"])
    owner.close()
    writer.release()
    new_writer = source.sources._held_writer(args["topology_state_root_base"])
    args["lane_assignment_writer"] = new_writer
    host = PortfolioBudgetHostV1(
        root=host_root,
        private_rest_fetch=_fetch(uid="acct-1"),
        repository_sha=standing.OWNER_GO_BASELINE_SHA,
        session_id="after-restart",
        expected_account_identity="acct-1",
        durable_mode="recover",
    )
    try:
        yield args, host, bound, calls, receipt, state
    finally:
        host.close()
        new_writer.release()


def test_actual_supervisor_recovers_then_consumes_distinct_authorized_c1(
    startup_case, tmp_path, monkeypatch
):
    args, _host, bound, calls, receipt, state = startup_case
    before = list(calls)
    standing._seed_public_marks(tmp_path / "public_store")
    lane = source.sources.lane_state_root_for(
        topology_state_root_base=args["topology_state_root_base"], lane_id="LANE_1"
    )
    next_event = source.T0 + 120
    monkeypatch.setattr(source.market, "PREVIOUS_C1_VENUE_EVENT_TIME", next_event)
    g17 = {
        "LANE_1": source.market._memory_g17_producer(
            instrument_id=bound.instrument_id, venue_native_id=bound.venue_native_id
        )
    }
    config = StandingSupervisorConfigV1(
        public_store_root=tmp_path / "public_store",
        private_store_root=tmp_path / "private_store",
        lane_state_root=args["topology_state_root_base"],
        evidence_root=tmp_path / "supervisor_run",
        lock_root=tmp_path / "supervisor_lock",
        expected_account_identity="acct-1",
        venue_native_id=bound.venue_native_id,
        canonical_instrument_id=bound.instrument_id,
        kill_switch_state_path=str(state),
        wp02_productive_default_enabled=False,
    )
    auth = standing._continuous_auth(native_id=bound.venue_native_id, max_cycles=1)
    auth = replace(auth, expected_cursor_floor=standing._cursor_floor_or_zero(Path(lane)))
    clock = standing._FakeClock()
    observation = standing._observation_from_closes(
        closes=standing.strong_uptrend_closes_v1(count=128)[:106], event_ts=next_event, bound=bound
    )
    wp02_order = []

    def observe_wp02(_):
        wp02_order.append(json.loads(receipt.read_text())["phase"])
        assert calls == before

    result = run_n1_standing_pre_external_supervisor_v1(
        config=config,
        origin_main_sha=standing.OWNER_GO_BASELINE_SHA,
        bound=bound,
        authorization=auth,
        observation_source=standing.ScriptedContinuousObservationSourceV1([observation]),
        g17_producers=g17,
        f1_m9_cycle_evaluator=standing._f1_m9_evaluator_factory(tmp_path),
        repo_root=standing.REPO,
        public_rest_fetch=standing._public_rest_empty,
        private_rest_fetch=_fetch(uid="acct-1"),
        public_ws_messages=[],
        time_fn=clock.time,
        sleep_fn=clock.sleep,
        post_close_startup_recovery=PostCloseStartupRecoveryRequestV1(args),
        wp02_hook=observe_wp02,
    )
    assert result.ok
    recovery = result.trace.extra["post_close_startup_recovery"]
    assert recovery["phase"] == "ACKED" and not recovery["runtime_admission_granted"]
    assert recovery["budget_admitted"] is False
    assert result.trace.accepted_c1_count == result.trace.governed_cycle_count == 1
    assert result.trace.post_count == 0
    assert json.loads(receipt.read_text())["phase"] == "ACKED"
    assert calls.count("after-close:LANE_1:LANE_1") == before.count("after-close:LANE_1:LANE_1")
    assert len(calls) == len(before) + 1
    assert wp02_order == ["ACKED"]
    assert result.trace.observation_recovery_completed and not result.trace.recovery_completed


def test_startup_adapter_replays_without_a_new_core_call(startup_case):
    args, host, bound, calls, receipt, _state = startup_case
    before = list(calls)
    result = recover_post_close_before_runtime_v1(
        PostCloseStartupRecoveryRequestV1(args),
        current_bound=bound,
        budget_host=host,
        current_topology_root=args["topology_state_root_base"],
    )
    assert result["phase"] == "ACKED"
    assert calls == before
    assert host.owner.budget_state_v1().recovery_required
    assert not host.owner.budget_state_v1().admitted
    assert json.loads(receipt.read_text())["phase"] == "ACKED"


@pytest.mark.parametrize(
    "fault,reason",
    [
        ("root", "LANE_SCOPE_MISMATCH"),
        ("account", "BUDGET_SCOPE_MISMATCH"),
        ("budget-root", "BUDGET_SCOPE_MISMATCH"),
        ("generation", "TARGET_GENERATION_MISMATCH"),
        ("missing-receipt", "EXISTING_RECEIPT_REQUIRED"),
        ("membership-only", "ORIGINAL_CONTINUATION_REQUIRED"),
        ("receipt-integrity", "RECEIPT_INTEGRITY_INVALID"),
        ("missing-output", "CORE_OUTCOME_UNCERTAIN"),
        ("output-integrity", "CORE_OUTCOME_UNCERTAIN"),
        ("changed-invocation", "REPLAY_CONFLICT"),
    ],
)
def test_startup_refuses_foreign_or_uncertain_originals(startup_case, tmp_path, fault, reason):
    args, host, bound, calls, receipt, _state = startup_case
    topology = args["topology_state_root_base"]
    current_topology = topology
    if fault == "root":
        current_topology = tmp_path / "other-topology"
    elif fault == "account":
        host.expected_account_identity = "another-account"
    elif fault == "budget-root":
        host.root = tmp_path / "other-budget"
    elif fault == "generation":
        bound = replace(bound, selection_integrity_digest="0" * 64)
    elif fault == "missing-receipt":
        receipt.unlink()
    elif fault == "membership-only":
        record = json.loads(receipt.read_text())
        record["phase"] = "MEMBERSHIP_STORED"
        source.continuation._write_receipt(receipt, record)
    elif fault == "receipt-integrity":
        record = json.loads(receipt.read_text())
        record["content_digest"] = "0" * 64
        receipt.write_text(json.dumps(record))
    elif fault in {"missing-output", "output-integrity"}:
        pending = next(topology.glob("**/n1_consumer_completions_v1/*.pending.json"))
        if fault == "missing-output":
            pending.unlink()
        else:
            pending.write_text("{}")
    elif fault == "changed-invocation":
        args["cycle_id_prefix"] = "foreign-cycle"
    before = list(calls), receipt.read_bytes() if receipt.exists() else None
    with pytest.raises(ValueError, match=reason):
        recover_post_close_before_runtime_v1(
            PostCloseStartupRecoveryRequestV1(args),
            current_bound=bound,
            current_topology_root=current_topology,
            budget_host=host,
        )
    assert calls == before[0]
    assert (receipt.read_bytes() if receipt.exists() else None) == before[1]
    if host.owner is not None:
        assert host.owner.budget_state_v1().recovery_required
        assert not host.owner.budget_state_v1().admitted


@pytest.mark.parametrize("failure", ["pending-orders", "account-changed", "transport"])
def test_fresh_account_failure_keeps_ack_pending_then_recovers(startup_case, failure):
    args, host, bound, calls, receipt, _state = startup_case
    before = list(calls), receipt.read_bytes()
    if failure == "pending-orders":
        host.fetch = _fetch(uid="acct-1", pending=True)
    elif failure == "account-changed":
        host.fetch = _fetch(uid="other-account")
    else:

        def unavailable(*_):
            raise TimeoutError("account temporarily unavailable")

        host.fetch = unavailable
        host.retry_sleep = lambda _: None
    with pytest.raises((ValueError, TimeoutError)):
        recover_post_close_before_runtime_v1(
            PostCloseStartupRecoveryRequestV1(args),
            current_bound=bound,
            current_topology_root=args["topology_state_root_base"],
            budget_host=host,
        )
    assert (calls, receipt.read_bytes()) == before
    host.fetch = _fetch(uid="acct-1")
    result = recover_post_close_before_runtime_v1(
        PostCloseStartupRecoveryRequestV1(args),
        current_bound=bound,
        current_topology_root=args["topology_state_root_base"],
        budget_host=host,
    )
    assert result["phase"] == "ACKED" and calls == before[0]
    assert host.owner.budget_state_v1().recovery_required
    assert not host.owner.budget_state_v1().admitted


def test_startup_requires_original_writer_lock(startup_case):
    args, host, bound, calls, receipt, _state = startup_case
    before = list(calls), receipt.read_bytes()
    args["lane_assignment_writer"].release()
    with pytest.raises(DuplicateLaneAssignmentWriterError, match="WRITER_LOCK_NOT_HELD"):
        recover_post_close_before_runtime_v1(
            PostCloseStartupRecoveryRequestV1(args),
            current_bound=bound,
            current_topology_root=args["topology_state_root_base"],
            budget_host=host,
        )
    assert (calls, receipt.read_bytes()) == before
    assert host.owner is None


@pytest.mark.parametrize("fault", ["generation", "output-integrity"])
def test_actual_supervisor_stops_before_wp02_and_closes_owner_on_startup_failure(
    startup_case, tmp_path, fault
):
    args, host, bound, calls, receipt, state = startup_case
    if fault == "generation":
        bound = replace(bound, selection_integrity_digest="0" * 64)
    else:
        next(args["topology_state_root_base"].glob("**/*.pending.json")).write_text("{}")
    before = list(calls), receipt.read_bytes()
    wp02_calls = []
    config = StandingSupervisorConfigV1(
        public_store_root=tmp_path / "public_store",
        private_store_root=tmp_path / "private_store",
        lane_state_root=args["topology_state_root_base"],
        evidence_root=tmp_path / "failed-run",
        expected_account_identity="acct-1",
        venue_native_id=bound.venue_native_id,
        canonical_instrument_id=bound.instrument_id,
        kill_switch_state_path=str(state),
    )
    with pytest.raises(ValueError):
        run_n1_standing_pre_external_supervisor_v1(
            config=config,
            origin_main_sha=standing.OWNER_GO_BASELINE_SHA,
            bound=bound,
            authorization=standing._continuous_auth(native_id=bound.venue_native_id, max_cycles=1),
            observation_source=None,
            g17_producers={},
            f1_m9_cycle_evaluator=lambda _: None,
            public_rest_fetch=standing._public_rest_empty,
            private_rest_fetch=_fetch(uid="acct-1"),
            post_close_startup_recovery=PostCloseStartupRecoveryRequestV1(args),
            wp02_hook=lambda _: wp02_calls.append(True),
        )
    assert (calls, receipt.read_bytes()) == before
    assert wp02_calls == []
    # The supervisor's finally closes its real owner even when readback fails.
    original_bound = BoundInstrumentV1(**json.loads(receipt.read_text())["bound_by_lane"]["LANE_1"])
    host.observe_v1({"LANE_1": original_bound})
    assert host.owner.budget_state_v1().recovery_required
    assert not host.owner.budget_state_v1().admitted
