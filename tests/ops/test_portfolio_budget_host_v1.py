"""Host owner lifecycle using offline private GET and canonical producer ports."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from tests.ops.test_durable_portfolio_budget_recovery_v1 import (
    BINDINGS,
    BOUND,
    EPOCH,
    NOW,
    ACCOUNT,
    _produce,
    _reserve,
)
from tests.ops.test_okx_eea_private_account_state_runtime_v1 import _fixture_rest


def _fetch(*, uid=ACCOUNT, pending=False, positions=(), calls=None):
    def fetch(path, params):
        if calls is not None:
            calls.append((path, params))
        payload = _fixture_rest(path, params)
        if path.endswith("config"):
            payload["data"][0]["uid"] = uid
        elif path.endswith("positions"):
            payload["data"] = list(positions)
        elif path.endswith("orders-pending"):
            payload["data"] = payload["data"] if pending else []
        elif path.endswith("orders-history") or path.endswith("fills"):
            payload["data"] = []
        return payload

    return fetch


def _host(root, fetch=None, clock=lambda: NOW, expected_account=ACCOUNT):
    return PortfolioBudgetHostV1(
        root=root / "stable-host",
        private_rest_fetch=fetch or _fetch(),
        repository_sha="test-host-revision",
        session_id="host-session",
        expected_account_identity=expected_account,
        # Explicit synthetic first-bootstrap choice belongs to this fixture.
        durable_mode="recover" if (root / "stable-host").exists() else "create",
        clock=clock,
    )


def test_host_reopens_same_owner_and_automatically_readmits_retaining_holds(tmp_path):
    calls = []
    host = _host(tmp_path, _fetch(calls=calls))
    try:
        ctx = host.observe_v1(BINDINGS)
        assert host.owner.budget_state_v1().recovery_required
        ctx.recover_v1(host.owner, _produce(epoch=EPOCH))
        held = _reserve(host.owner)
        host.owner.commit_internal_pre_external_effect_v1(held.reservation.reservation_id)
        assert host.owner.active_sum_v1() == 60
        assert all("instId" not in params for _, params in calls)
        assert len(calls) == 6
    finally:
        host.close()
    host = _host(tmp_path)
    try:
        ctx = host.observe_v1(BINDINGS)
        assert host.owner.active_sum_v1() == 60
        assert host.owner.budget_state_v1().recovery_required
        ctx.recover_v1(host.owner, _produce(epoch=EPOCH))
        assert host.owner.budget_state_v1().admitted
        restored = _reserve(host.owner).reservation
        assert restored.reservation_id == held.reservation.reservation_id
        assert restored.amount == held.reservation.amount
        assert restored.state.value == "COMMITTED"
        assert host.owner.active_sum_v1() == 60
    finally:
        host.close()


@pytest.mark.parametrize("fault", ["uid", "pending", "stale", "foreign-position", "hedge"])
def test_host_fences_bad_refresh_and_recovers_with_new_facts_without_unlock(tmp_path, fault):
    host = _host(tmp_path)
    try:
        host.observe_v1(BINDINGS).recover_v1(host.owner, _produce(epoch=EPOCH))
        _reserve(host.owner)
        if fault == "uid":
            host.fetch = _fetch(uid="other")
        elif fault == "pending":
            host.fetch = _fetch(pending=True)
        elif fault == "stale":
            ticks = iter([NOW, NOW + 6])
            host.clock = lambda: next(ticks)
        else:
            rows = [
                {
                    "instId": "UNKNOWN" if fault == "foreign-position" else BOUND.venue_native_id,
                    "posSide": "net",
                    "pos": "1",
                }
            ]
            if fault == "hedge":
                rows *= 2
            host.fetch = _fetch(positions=rows)
        with pytest.raises(ValueError):
            host.observe_v1(BINDINGS).recover_v1(host.owner, _produce(epoch=EPOCH))
        assert host.owner.budget_state_v1().recovery_required
        assert host.owner.active_sum_v1() == 60
        host.fetch = _fetch()
        host.clock = lambda: NOW
        host.observe_v1(BINDINGS).recover_v1(host.owner, _produce(epoch=EPOCH))
        assert host.owner.budget_state_v1().admitted
        assert host.owner.active_sum_v1() == 60
    finally:
        host.close()


def test_missing_uid_and_damaged_existing_scope_never_create_empty_budget(tmp_path):
    host = _host(tmp_path, _fetch(uid=""))
    with pytest.raises(ValueError, match="ACCOUNT_UNPROVEN"):
        host.observe_v1(BINDINGS)
    assert not (tmp_path / "stable-host").exists()
    (tmp_path / "stable-host").mkdir()
    host.fetch = _fetch()
    with pytest.raises(ValueError, match="BOOTSTRAP_SCOPE_ALREADY_EXISTS"):
        host.observe_v1(BINDINGS)
    host.close()


def test_shared_host_refuses_second_writer_and_account_switch_after_restart(tmp_path):
    first, second = _host(tmp_path), _host(tmp_path)
    try:
        first.observe_v1(BINDINGS)
        with pytest.raises(ValueError):
            second.observe_v1(BINDINGS)
    finally:
        first.close()
        second.close()
    other = _host(tmp_path, _fetch(uid="other"))
    try:
        with pytest.raises(ValueError):
            other.observe_v1(BINDINGS)
    finally:
        other.close()


def test_actual_outer_entry_seam_recovers_host_before_reserving(tmp_path, monkeypatch):
    from tests.ops.test_outer_entry_budget_policy_v1 import (
        _bound,
        _host_enter_cycle,
        _enter_replay,
        _injected,
        _balance_payload,
        Slot,
        join,
    )
    from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import EPOCH as epoch
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        REUSED_BINDING_ACCOUNT_SCOPE,
    )

    now = datetime.fromisoformat(epoch.replace("Z", "+00:00")).timestamp()
    host = _host(
        tmp_path,
        _fetch(uid=REUSED_BINDING_ACCOUNT_SCOPE),
        clock=lambda: now,
        expected_account=REUSED_BINDING_ACCOUNT_SCOPE,
    )
    bindings = {"LANE_1": _bound()}
    _, cycle, _ = _host_enter_cycle()
    replay = _enter_replay(cycle)
    original = replay.evidence

    def no_dp(**kwargs):
        raise AssertionError("Outer policy must never rerun DoublePlay")

    monkeypatch.setattr(
        "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0",
        no_dp,
    )
    try:
        ctx = host.observe_v1(bindings)
        result = join(
            replay=replay,
            bound_instrument=_bound(),
            decision_epoch=epoch,
            injected=_injected(payload=_balance_payload(avail_eq="1000.00")),
            portfolio_budget_owner=host.owner,
            portfolio_slot=Slot(
                slot_id="LANE_1", decision_id=str(original.decision_id), cycle_id="host-entry"
            ),
            host_budget_recovery=ctx,
        )
        assert result.status == "PASS", result.first_blocker
        assert replay.evidence is original
        assert 0 < host.owner.active_sum_v1() <= Decimal("25")
        assert result.post_count == "0" and result.permit_created == "false"
    finally:
        host.close()


def test_actual_supervisor_passes_shared_host_through_s5_and_closes_it(tmp_path, monkeypatch):
    from tests.ops.test_n1_standing_pre_external_runtime_supervisor_v1 import (
        test_t_plus_01_supervisor_single_cycle,
    )
    import src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 as persistent

    calls = []
    original = persistent._t2_from_s7

    def track(**kwargs):
        calls.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(persistent, "_t2_from_s7", track)
    test_t_plus_01_supervisor_single_cycle(tmp_path)
    assert calls
    owner = calls[0]["portfolio_budget_owner"]
    assert owner is not None
    assert calls[0]["host_budget_recovery"].host.owner is owner
    assert calls[0]["host_budget_recovery"].host.closed
    assert (
        calls[0]["host_budget_recovery"].host.root
        == tmp_path / "private_store" / "portfolio_budget_host_v1"
    )
    assert all(
        k not in calls[0]["s7_base"]
        for k in (
            "portfolio_budget_owner",
            "host_budget_recovery",
            "entry_budget_policy",
        )
    )
    assert (
        tmp_path / "private_store" / "portfolio_budget_host_v1" / "owner" / "reservations.sqlite3"
    ).is_file()


def test_transient_private_transport_uses_existing_bounded_retry_and_keeps_owner(tmp_path):
    host = _host(tmp_path)
    host.retry_sleep = lambda _: None
    try:
        host.observe_v1(BINDINGS).recover_v1(host.owner, _produce(epoch=EPOCH))
        _reserve(host.owner)
        original_owner = host.owner
        healthy_fetch = _fetch()
        attempts = []

        def flaky(path, params):
            if len(attempts) < 2:
                attempts.append(path)
                raise ConnectionError("offline-fault")
            return healthy_fetch(path, params)

        host.fetch = flaky
        host.observe_v1(BINDINGS).recover_v1(host.owner, _produce(epoch=EPOCH))
        assert host.owner is original_owner
        assert host.transport_retry_count == 2
        assert host.owner.active_sum_v1() == 60
        assert host.owner.budget_state_v1().admitted

        def always_down(*_):
            raise TimeoutError("offline-fault")

        host.fetch = always_down
        with pytest.raises(TimeoutError):
            host.observe_v1(BINDINGS)
        assert host.transport_retry_count == 5  # two earlier + existing three-retry limit
        assert host.owner.budget_state_v1().recovery_required
        assert host.owner.active_sum_v1() == 60
    finally:
        host.close()


@pytest.mark.parametrize(
    "pos_side,quantity,expected",
    [("long", "2", "long"), ("short", "2", "short"), ("net", "-2", "short")],
)
def test_cold_and_warm_host_never_override_real_position_with_flat_default(
    tmp_path, monkeypatch, pos_side, quantity, expected
):
    from types import SimpleNamespace
    import src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 as persistent
    from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
        _bound_lane_1,
        _lane_g17,
        _observation_from_closes,
        strong_uptrend_closes_v1,
    )

    bound = _bound_lane_1()
    pairs = persistent.build_s8_occupied_lane_pairs_v1(
        lane_state_root=tmp_path / "lanes", bound=bound
    )
    g17 = _lane_g17(pairs)
    obs = _observation_from_closes(
        closes=strong_uptrend_closes_v1(count=106), event_ts=NOW, bound=bound
    )
    host = _host(
        tmp_path,
        _fetch(
            positions=({"instId": bound.venue_native_id, "pos": quantity, "posSide": pos_side},)
        ),
    )
    cold, warm, dispatch = [], [], []
    monkeypatch.setattr(
        persistent,
        "compose_occupied_lane_mv2_dp_durable_cycle_v1",
        lambda pairs, **kw: cold.append(kw),
    )
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class CapturedCycleResult:
        pending_decision_context: object = None

    def capture_warm(**kwargs):
        warm.append(kwargs)
        return CapturedCycleResult()

    monkeypatch.setattr(persistent, "run_current_productive_governed_cycle_v1", capture_warm)
    original = persistent._t2_from_s7

    def capture(**kwargs):
        dispatch.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(persistent, "_t2_from_s7", capture)
    try:
        ctx = host.observe_v1({"LANE_1": bound})
        from dataclasses import replace

        with pytest.raises(ValueError, match="POSITION_BINDING_MISMATCH"):
            ctx.position_side_v1(replace(bound, instrument_id="unknown"))
        persistent.bootstrap_s8_lane_via_s7_compose_v1(
            composed_pairs=pairs,
            origin_main_sha="test",
            g17_producers=g17,
            candles_payload=obs.candles_payload,
            mark_price_payload=obs.mark_price_payload,
            index_tickers_payload=obs.index_tickers_payload,
            venue_native_id=bound.venue_native_id,
            host_budget_recovery=ctx,
        )
        runner = persistent.make_n1_occupied_lane_s5_runner_v1(
            composed_pairs=pairs,
            g17_producers=g17,
            cycle_id_prefix_base="host-position",
            portfolio_budget_host=host,
        )
        runner(
            authorization=SimpleNamespace(native_id=bound.venue_native_id),
            origin_main_sha="test",
            cursor_store_root=Path(pairs["LANE_1"][0].lane_state_root),
            lock_root=tmp_path / "locks",
            evidence_root=tmp_path / "cycle",
            candles_payload=obs.candles_payload,
            mark_price_payload=obs.mark_price_payload,
            index_tickers_payload=obs.index_tickers_payload,
            occupancy_payloads={"POSITIONS": {"code": "0", "data": []}},
        )
        assert cold[0]["venue_flat"] is False
        assert cold[0]["existing_position_side"].value == expected
        assert dispatch[0]["s7_base"]["venue_flat"] is False
        assert dispatch[0]["s7_base"]["existing_position_side"].value == expected
        assert warm[0]["occupancy_payloads"]["POSITIONS"]["data"][0]["pos"] == quantity
    finally:
        host.close()


def test_host_sigkill_restores_real_entry_frozen_sizing_and_obligations(tmp_path):
    import subprocess
    import signal
    import time
    from pathlib import Path
    import json
    from tests.ops.test_outer_entry_budget_policy_v1 import _bound
    from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import EPOCH as epoch
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        REUSED_BINDING_ACCOUNT_SCOPE,
    )

    checkpoint = tmp_path / "checkpoint.json"
    code = """
import sys, json, time
from pathlib import Path
from datetime import datetime
from tests.ops.test_portfolio_budget_host_v1 import _host, _fetch
from tests.ops.test_outer_entry_budget_policy_v1 import _bound, _host_enter_cycle, _enter_replay, _injected, _balance_payload, Slot, join
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import EPOCH
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import REUSED_BINDING_ACCOUNT_SCOPE
root = Path(sys.argv[1])
now = datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp()
host = _host(root, _fetch(uid=REUSED_BINDING_ACCOUNT_SCOPE), clock=lambda: now, expected_account=REUSED_BINDING_ACCOUNT_SCOPE)
ctx = host.observe_v1({"LANE_1": _bound()})
_, cycle, _ = _host_enter_cycle()
replay = _enter_replay(cycle)
result = join(replay=replay, bound_instrument=_bound(), decision_epoch=EPOCH,
    injected=_injected(payload=_balance_payload(avail_eq="1000.00")),
    portfolio_budget_owner=host.owner,
    portfolio_slot=Slot(slot_id="LANE_1", decision_id=str(replay.evidence.decision_id), cycle_id="host-crash"),
    host_budget_recovery=ctx)
assert result.status == "PASS", result.first_blocker
host.owner.commit_internal_pre_external_effect_v1(result.portfolio_reservation_id)
import sqlite3
with sqlite3.connect(host.root / "owner" / "reservations.sqlite3") as db:
    payload = json.loads(db.execute("SELECT payload FROM states ORDER BY seq DESC LIMIT 1").fetchone()[0])
Path(sys.argv[2]).write_text(json.dumps({"sum": str(host.owner.active_sum_v1()), "reservation_id": result.portfolio_reservation_id, "sizing": payload["sizing_bindings"]}))
while True:
    time.sleep(1)
"""
    proc = subprocess.Popen(
        ["./scripts/pt", "-c", code, str(tmp_path), str(checkpoint)],
        cwd=Path(__file__).resolve().parents[2],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 20
        while not checkpoint.exists() and proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert checkpoint.exists(), (
            proc.stderr.read().decode() if proc.poll() is not None else "checkpoint timeout"
        )
        proc.send_signal(signal.SIGKILL)
        proc.wait(timeout=5)
        expected = json.loads(checkpoint.read_text())
        now = datetime.fromisoformat(epoch.replace("Z", "+00:00")).timestamp()
        host = _host(
            tmp_path,
            _fetch(uid=REUSED_BINDING_ACCOUNT_SCOPE),
            clock=lambda: now,
            expected_account=REUSED_BINDING_ACCOUNT_SCOPE,
        )
        try:
            host.observe_v1({"LANE_1": _bound()})
            assert host.owner.budget_state_v1().recovery_required
            assert host.owner.active_sum_v1() == Decimal(expected["sum"])
            assert host.owner.stored_reservation_count_v1() == 1
            # A frozen canonical sizing record is part of the recovered history.
            persisted = host.root / "owner" / "reservations.sqlite3"
            import sqlite3

            with sqlite3.connect(persisted) as connection:
                payload = json.loads(
                    connection.execute(
                        "SELECT payload FROM states ORDER BY seq DESC LIMIT 1"
                    ).fetchone()[0]
                )
            assert expected["reservation_id"] in json.dumps(payload)
            assert "sizing_bindings" in payload
            assert payload["sizing_bindings"] == expected["sizing"]
            from tests.ops.test_outer_entry_budget_policy_v1 import (
                _host_enter_cycle,
                _enter_replay,
                _injected,
                _balance_payload,
                Slot,
                join,
            )

            _, cycle, _ = _host_enter_cycle()
            replay = _enter_replay(cycle)
            result = join(
                replay=replay,
                bound_instrument=_bound(),
                decision_epoch=epoch,
                injected=_injected(payload=_balance_payload(avail_eq="1000.00")),
                portfolio_budget_owner=host.owner,
                portfolio_slot=Slot(
                    slot_id="LANE_1",
                    decision_id=str(replay.evidence.decision_id),
                    cycle_id="host-crash",
                ),
                host_budget_recovery=host.observe_v1({"LANE_1": _bound()}),
            )
            assert result.status == "PASS", result.first_blocker
            assert result.portfolio_reservation_id == expected["reservation_id"]
            assert result.portfolio_reservation_disposition == "IDEMPOTENT_REPLAY"
            assert host.owner.active_sum_v1() == Decimal(expected["sum"])
        finally:
            host.close()
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5)
        proc.stderr.close()
