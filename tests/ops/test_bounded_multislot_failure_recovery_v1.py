"""Connected original multi-slot holds under shared failure and cold recovery."""

from dataclasses import replace
from datetime import datetime, timezone
import json
import subprocess
from pathlib import Path

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    invoke_join_v1 as n1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1 import (
    addressing_join_v1 as s7,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    PortfolioBudgetHostV1,
    HostBudgetRecoveryContextV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
)
from tests.ops.test_bounded_multislot_connected_cycle_v1 import connected, ports
from tests.ops.test_bounded_multislot_entry_budget_v1 import policy
from tests.ops.test_portfolio_budget_host_v1 import _fetch
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_aligned_g17_dk_producer_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PortfolioTruthSnapshotV1
from tests.ops.test_current_mf_n5_instrument_runtime_identity_closure_v1 import _positions_payload


def seed(tmp_path, monkeypatch, count=5):
    outputs = []
    original = HostBudgetRecoveryContextV1.recover_v1

    def observe(context, owner, output):
        result = original(context, owner, output)
        outputs.append(output)
        return result

    monkeypatch.setattr(HostBudgetRecoveryContextV1, "recover_v1", observe)
    pairs, _, kwargs, host = connected(tmp_path, count)
    results = n1.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
    assert all(r.governed_cycle_result.final_order_envelope is not None for r in results.values())
    assert len(outputs) == count
    return pairs, kwargs, host, outputs[-1], results


def reopen(host, *, fetch=None):
    return PortfolioBudgetHostV1(
        root=host.root,
        private_rest_fetch=fetch or host.fetch,
        repository_sha=host.repository_sha,
        session_id=host.session_id + ":reopen",
        expected_account_identity=host.expected_account_identity,
        durable_mode="recover",
        clock=host.clock,
        execution_environment="INTERNAL_SIMULATED_EXECUTION",
        entry_budget_policy=policy(),
    )


@pytest.mark.parametrize("fault", ["foreign-open-position", "stale-portfolio"])
def test_unowned_position_or_unhealthy_shared_truth_fences_original_owner_before_core(
    tmp_path, monkeypatch, fault
):
    pairs, kwargs, host, output, results = seed(tmp_path, monkeypatch)
    held, links = host.owner.active_sum_v1(), host.owner.execution_links_v1()
    kwargs = dict(kwargs)
    kwargs["cycle_id_prefix"] = "bad-shared-truth"
    if fault == "foreign-open-position":
        kwargs["occupancy_payloads"] = _positions_payload(("UNOWNED-USDT-SWAP", "net", 1))
    else:
        kwargs["observed_portfolio"] = PortfolioTruthSnapshotV1(stale=True)
    calls = []

    def forbidden(**kw):
        calls.append(True)
        raise AssertionError("No Core before shared truth admission")

    monkeypatch.setattr(s7, "run_current_productive_master_v2_runtime_cycle_v1", forbidden)
    try:
        with pytest.raises(ValueError):
            n1.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
        assert calls == []
        assert not host.owner.budget_state_v1().admitted
        assert host.owner.active_sum_v1() == held and host.owner.execution_links_v1() == links
    finally:
        host.close()


@pytest.mark.parametrize("count", [2, 5])
@pytest.mark.parametrize("fault", ["pending", "account", "stale"])
def test_shared_account_failure_fences_all_holds_then_original_fresh_facts_recover(
    tmp_path, monkeypatch, count, fault
):
    pairs, kwargs, host, output, results = seed(tmp_path, monkeypatch, count)
    owner = host.owner
    bindings = {lane: bound for lane, (_, bound) in pairs.items()}
    before, held = owner.execution_links_v1(), owner.active_sum_v1()
    cursors = {
        lane: load_current_productive_sidestate_confirmation_cursor_v1(
            Path(pair[0].lane_state_root)
        )
        for lane, pair in pairs.items()
    }
    try:
        if fault == "pending":
            host.fetch = _fetch(uid=host.account, pending=True)
        elif fault == "account":
            host.fetch = _fetch(uid="foreign-account")
        else:
            now = host.clock()
            ticks = iter(range(100))
            host.clock = lambda: now + 60 * next(ticks)
        with pytest.raises(ValueError):
            host.observe_v1(bindings).recover_v1(owner, output)
        assert not owner.budget_state_v1().admitted
        assert owner.active_sum_v1() == held > 0
        assert owner.execution_links_v1() == before
        for lane, pair in pairs.items():
            assert (
                load_current_productive_sidestate_confirmation_cursor_v1(
                    Path(pair[0].lane_state_root)
                )
                == cursors[lane]
            )
        # Restore explicit original synthetic account observations, no unlock.
        host.fetch = _fetch(uid=host.account)
        now = kwargs["observed_unix"]
        host.clock = lambda: now
        host.observe_v1(bindings).recover_v1(owner, output)
        assert owner.budget_state_v1().admitted
        assert owner.active_sum_v1() == held and owner.execution_links_v1() == before
        host.close()
        cold = reopen(host)
        try:
            context = cold.observe_v1(bindings)
            assert not cold.owner.budget_state_v1().admitted
            assert cold.owner.budget_state_v1().recovery_required
            assert cold.owner.active_sum_v1() == held
            assert cold.owner.execution_links_v1() == before
            context.recover_v1(cold.owner, output)
            assert cold.owner.budget_state_v1().admitted
            assert cold.owner.entry_budget_policy_v1() == policy()
            assert cold.owner.active_sum_v1() == held
            assert cold.owner.stored_reservation_count_v1() == count
        finally:
            cold.close()
    finally:
        host.close()


@pytest.mark.parametrize("failing_lane", ["LANE_1", "LANE_3"])
def test_real_s7_failure_fences_shared_owner_and_retains_other_slot_holds(
    tmp_path, monkeypatch, failing_lane
):
    pairs, kwargs, host, output, results = seed(tmp_path, monkeypatch)
    owner = host.owner
    links, held = owner.execution_links_v1(), owner.active_sum_v1()
    original = s7.run_current_productive_master_v2_runtime_cycle_v1
    calls = []

    def unavailable(**kw):
        calls.append(kw["bound_instrument"].instrument_id)
        if kw["bound_instrument"] == pairs[failing_lane][1]:
            raise OSError("SYNTHETIC_SLOT_CORE_PUBLICATION_FAILURE")
        return original(**kw)

    monkeypatch.setattr(s7, "run_current_productive_master_v2_runtime_cycle_v1", unavailable)
    event = kwargs["last_finalized_event_ts_unix"] + 60
    next_kwargs = dict(kwargs)
    payloads, producers = {}, {}
    epoch = datetime.fromtimestamp(event + 1, timezone.utc).isoformat().replace("+00:00", "Z")
    for lane, (_, bound) in pairs.items():
        old = kwargs["candles_payload_by_lane"][lane]
        closes = tuple(float(row[4]) for row in old["data"])
        payloads[lane] = {
            **old,
            "data": [
                [str(int((event - (len(closes) - 1 - i) * 60) * 1000)), *row[1:]]
                for i, row in enumerate(old["data"])
            ],
        }
        producers[lane] = governed_c1_aligned_g17_dk_producer_v1(
            bound=bound,
            anchor_event_ts_unix=event,
            evidence_store_root=tmp_path / "next-g17" / lane,
            mark_closes=closes,
        )
    next_kwargs.update(
        cycle_id_prefix="failed-next",
        observed_unix=event + 1,
        last_finalized_event_ts_unix=event,
        candles_payload_by_lane=payloads,
        g17_typed_vol_producers=producers,
        live_29p_injected_by_lane={
            lane: ports(bound, epoch, "failed-next:" + lane) for lane, (_, bound) in pairs.items()
        },
    )
    try:
        failed = n1.invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **next_kwargs)
        assert failed[failing_lane].governed_cycle_result.disposition == "FAIL_CLOSED"
        assert all(
            result.governed_cycle_result.final_order_envelope is None for result in failed.values()
        )
        assert calls and pairs[failing_lane][1].instrument_id in calls
        assert not owner.budget_state_v1().admitted
        assert owner.active_sum_v1() == held and owner.execution_links_v1() == links
        assert owner.stored_reservation_count_v1() == 5
        for lane, result in results.items():
            cycle = result.governed_cycle_result
            rid = cycle.extra["PORTFOLIO_RESERVATION_ID"]
            with pytest.raises(ValueError, match="OWNER_FENCED"):
                owner.inspect_execution_submit_context_v1(rid, cycle.final_order_envelope, None)
    finally:
        host.close()


@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_damaged_shared_store_never_bootstraps_empty_replacement(tmp_path, monkeypatch, damage):
    pairs, kwargs, host, output, results = seed(tmp_path, monkeypatch)
    owner_root = Path(host.owner.durable_scope_identity_v1()["root"])
    held = host.owner.active_sum_v1()
    host.close()
    files = list(owner_root.glob("reservations.sqlite3"))
    assert files, list(owner_root.rglob("*"))
    path = files[0]
    original = path.read_bytes()
    if damage == "missing":
        path.unlink()
    else:
        path.write_bytes(b"broken-sqlite")
    cold = reopen(host)
    try:
        with pytest.raises(ValueError):
            cold.observe_v1({lane: bound for lane, (_, bound) in pairs.items()})
        assert cold.owner is None
        assert held > 0
        assert not path.exists() if damage == "missing" else path.read_bytes() == b"broken-sqlite"
    finally:
        cold.close()


@pytest.mark.parametrize("count", [2, 5])
def test_process_termination_releases_writer_but_never_capital_admission(
    tmp_path, monkeypatch, count
):
    pairs, kwargs, host, output, results = seed(tmp_path, monkeypatch, count)
    owner_root = host.owner.durable_scope_identity_v1()["root"]
    held = str(host.owner.active_sum_v1())
    links = host.owner.execution_links_v1()
    account = host.account
    host.close()
    bindings = {lane: bound.to_dict() for lane, (_, bound) in pairs.items()}
    code = """
import json, os, socket, sys
from pathlib import Path
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import PortfolioCapitalReservationBudgetOwnerV1
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
def forbidden(*a, **kw): raise AssertionError('No child network')
socket.socket.connect = forbidden
owner = PortfolioCapitalReservationBudgetOwnerV1(durable_root=Path(sys.argv[1]), durable_account_identity=sys.argv[2], durable_mode='recover', durable_lane_bindings={k:BoundInstrumentV1(**v) for k,v in json.loads(sys.argv[3]).items()})
state = owner.budget_state_v1()
print(json.dumps(dict(admitted=state.admitted, recovery_required=state.recovery_required, held=str(owner.active_sum_v1()), links=owner.execution_links_v1(), policy=owner.entry_budget_policy_v1().to_dict_v1())), flush=True)
if sys.argv[4]=='terminate': os._exit(23)
owner.close()
"""
    for action in ("terminate", "reopen"):
        child = subprocess.run(
            ["./scripts/pt", "-c", code, owner_root, account, json.dumps(bindings), action],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert child.returncode == (23 if action == "terminate" else 0), child.stderr
        observed = json.loads(child.stdout.splitlines()[-1])
        assert not observed["admitted"] and observed["recovery_required"]
        assert observed["held"] == held and observed["links"] == links
        assert observed["policy"] == policy().to_dict_v1()
