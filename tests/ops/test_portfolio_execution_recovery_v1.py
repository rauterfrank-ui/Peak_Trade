"""Exact execution/reservation correlation; all source ports are offline."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlsplit

import pytest

from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    FullCoreExchangeReconciliationIdentityV1 as Identity,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    fetch_okx_read_only_reconciliation_snapshot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from tests.ops.test_outer_entry_budget_policy_v1 import (
    _bound,
    _host_enter_cycle,
    _enter_replay,
    _injected,
    _balance_payload,
    Slot,
    join,
)
from tests.ops.test_portfolio_budget_host_v1 import _host, _fetch
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import EPOCH
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_ACCOUNT_SCOPE as ACCOUNT,
)

NOW = datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp()


def seed(root):
    host = _host(root, _fetch(uid=ACCOUNT), clock=lambda: NOW, expected_account=ACCOUNT)
    context = host.observe_v1({"LANE_1": _bound()})
    _, cycle, _ = _host_enter_cycle()
    replay = _enter_replay(cycle)
    result = join(
        replay=replay,
        bound_instrument=_bound(),
        decision_epoch=EPOCH,
        injected=_injected(payload=_balance_payload(avail_eq="1000.00")),
        portfolio_budget_owner=host.owner,
        portfolio_slot=Slot(
            slot_id="LANE_1", decision_id=str(replay.evidence.decision_id), cycle_id="execution"
        ),
        host_budget_recovery=context,
    )
    assert result.status == "PASS", result.first_blocker
    status, reasons, plan = try_bind_current_productive_venue_plan_v1(
        replay=result.replay,
        bound_instrument=_bound(),
        session_id="execution",
        run_id="execution",
        composed_epoch=EPOCH,
        execution_mode="LIVE",
    )
    assert status.value == "PASS", reasons
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        plan, admission_ref="execution", provenance_ref="execution", creation_epoch=EPOCH
    )
    rid = result.portfolio_reservation_id
    host.owner.commit_internal_pre_external_effect_v1(rid)
    host.owner.bind_execution_plan_v1(rid, envelope)
    identity = Identity(
        canonical_decision_id=str(replay.evidence.decision_id),
        decision_outcome="ENTER",
        selected_side=result.replay.intermediate.capital_risk_sizing_decision.selected_side,
        instrument_id=_bound().instrument_id,
        native_id=envelope.instrument_id,
        account_identity=ACCOUNT,
        execution_environment="LIVE",
        venue="OKX",
        venue_plan_identity="plan-execution",
        venue_plan_digest="plan-execution-digest",
        envelope_identity=envelope.envelope_id,
        envelope_digest=envelope.envelope_digest,
        final_quantity=envelope.quantity,
        quantity_unit=envelope.quantity_unit,
        order_type=envelope.order_type,
        order_price=envelope.price,
        clordid=envelope.client_order_id,
        exchange_ord_id=None,
        owner_go="test-existing-send-gate",
        atomic_consumption_key="test-existing-consume-key",
        submit_attempt_id="attempt-1",
        local_durable_state_version="v1",
    )
    return host, rid, identity, envelope


class ReadPort:
    def __init__(self, identity, *, state="canceled", filled="0", fault=None):
        self.identity = identity
        self.state = state
        self.filled = filled
        self.fault = fault
        self.calls = []

    def get(self, *, endpoint, **kwargs):
        self.calls.append(endpoint)
        path = urlsplit(endpoint).path
        row = {
            "instId": self.identity.native_id,
            "clOrdId": self.identity.clordid,
            "ordId": "order-1",
            "sz": self.identity.final_quantity,
            "accFillSz": self.filled,
            "state": self.state,
        }
        rows = [row] if path.endswith(("orders-history", "/order")) else []
        if path.endswith("/config"):
            rows = [{"uid": "foreign" if self.fault == "account" else ACCOUNT}]
        elif path.endswith("/fills") and Decimal(self.filled) > 0:
            rows = [{**row, "tradeId": "trade-1", "fillSz": self.filled, "fillPx": "10"}]
        if self.fault == "foreign-order" and rows and path.endswith("/order"):
            rows[0]["instId"] = "FOREIGN"
        payload = {"code": "0", "data": rows}
        return FreshPretradeGetTransportResultV1(
            get_performed=True,
            method="GET",
            endpoint="/wrong-scope"
            if self.fault == "wrong-endpoint" and path.endswith("orders-history")
            else endpoint,
            http_status=200,
            payload=payload,
            auth_header_sent=not (self.fault == "no-auth" and path.endswith("orders-history")),
            transport_class="OFFLINE_ACCOUNT_BOUND_TEST_PORT",
            venue_live_contact=False,
            historical_reuse=self.fault == "cached",
            error_class="",
        )


def test_durable_submit_link_prevents_resend_and_generic_release(tmp_path):
    host, rid, identity, envelope = seed(tmp_path)
    try:
        with pytest.raises(ValueError, match="IDENTITY_MISMATCH"):
            host.owner.mark_execution_submit_boundary_v1(
                rid, replace(identity, final_quantity="999")
            )
        host.owner.mark_execution_submit_boundary_v1(rid, identity)
        with pytest.raises(ValueError, match="REPLAY"):
            host.owner.mark_execution_submit_boundary_v1(rid, identity)
        assert host.owner.release_plan_failure_v1(rid).disposition.value == "FAIL_CLOSED"
        expected = host.owner.active_sum_v1()
    finally:
        host.close()
    restored = _host(tmp_path, _fetch(uid=ACCOUNT), clock=lambda: NOW, expected_account=ACCOUNT)
    try:
        context = restored.observe_v1({"LANE_1": _bound()})
        assert not context.execution_reconciliation[rid]["matched"]
        assert restored.owner.active_sum_v1() == expected
        assert restored.owner.execution_links_v1()[rid]["identity"] == identity.to_dict()
    finally:
        restored.close()


@pytest.mark.parametrize(
    "fault", [None, "account", "foreign-order", "cached", "position", "wrong-endpoint", "no-auth"]
)
def test_host_automatically_matches_cancel_without_fill_or_retains_uncertain_hold(tmp_path, fault):
    host, rid, identity, _ = seed(tmp_path)
    host.owner.mark_execution_submit_boundary_v1(rid, identity)
    held = host.owner.active_sum_v1()
    host.close()
    positions = (
        ()
        if fault != "position"
        else ({"instId": _bound().venue_native_id, "posSide": "net", "pos": "1"},)
    )
    host = _host(
        tmp_path,
        _fetch(uid=ACCOUNT, positions=positions),
        clock=lambda: NOW,
        expected_account=ACCOUNT,
    )
    host.reconciliation_transport = ReadPort(identity, fault=fault)
    try:
        if fault in {"account", "cached"}:
            with pytest.raises(ValueError, match="ACCOUNT_UNPROVEN"):
                host.observe_v1({"LANE_1": _bound()})
            assert host.owner.active_sum_v1() == held
        else:
            context = host.observe_v1({"LANE_1": _bound()})
            proof = context.execution_reconciliation[rid]
            assert proof["matched"] is (fault is None)
            assert proof["reservation_released"] is (fault is None)
            assert host.owner.active_sum_v1() == (0 if fault is None else held)
            assert host.owner.budget_state_v1().recovery_required
            assert all(
                _bound().venue_native_id in call
                for call in host.reconciliation_transport.calls
                if not call.endswith("config")
            )
    finally:
        host.close()


def test_filled_entry_requires_corresponding_position_and_retains_capital(tmp_path):
    host, rid, identity, _ = seed(tmp_path)
    host.owner.mark_execution_submit_boundary_v1(rid, identity)
    held = host.owner.active_sum_v1()
    qty = identity.final_quantity
    sign = "" if identity.selected_side.upper() in {"LONG", "ENTER_LONG"} else "-"
    host.fetch = _fetch(
        uid=ACCOUNT,
        positions=({"instId": identity.native_id, "posSide": "net", "pos": sign + qty},),
    )
    host.reconciliation_transport = ReadPort(identity, state="filled", filled=qty)
    try:
        context = host.observe_v1({"LANE_1": _bound()})
        assert context.execution_reconciliation[rid]["matched"]
        assert host.owner.active_sum_v1() == held
        host.fetch = _fetch(uid=ACCOUNT)
        context = host.observe_v1({"LANE_1": _bound()})
        assert not context.execution_reconciliation[rid]["matched"]
        assert host.owner.active_sum_v1() == held
    finally:
        host.close()


def test_known_open_order_is_not_new_entry_readiness(tmp_path):
    host, rid, identity, _ = seed(tmp_path)
    host.owner.mark_execution_submit_boundary_v1(rid, identity)
    host.reconciliation_transport = ReadPort(identity, state="live", filled="0")
    try:
        context = host.observe_v1({"LANE_1": _bound()})
        assert context.execution_reconciliation[rid]["matched"]
        assert not context.execution_reconciliation[rid]["decision"]["reconciliation_complete"]
        with pytest.raises(ValueError, match="EXECUTION_RECONCILIATION_UNRESOLVED"):
            context.recover_v1(host.owner, None)
        assert host.owner.budget_state_v1().recovery_required
        host.execution_environment = "SHADOW"
        with pytest.raises(ValueError, match="ENVIRONMENT_MISMATCH"):
            host.observe_v1({"LANE_1": _bound()})
    finally:
        host.close()


@pytest.mark.parametrize("storage_fault", [False, True])
def test_send_barrier_records_identity_before_transport_and_never_retries(
    tmp_path, monkeypatch, storage_fault
):
    from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
        attempt_envelope_bound_external_effect_send_v1,
    )
    from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
        _permit,
        _handle,
    )

    host, rid, identity, envelope = seed(tmp_path)
    calls = []

    class Transport:
        def post_trade_order(self, **kwargs):
            calls.append(kwargs)
            assert host.owner.execution_links_v1()[rid]["phase"] == "SUBMIT_MAY_HAVE_OCCURRED"
            raise RuntimeError("offline-transport-boundary")

    if storage_fault:

        def fail_save(*_):
            raise OSError("offline-disk-failure")

        monkeypatch.setattr(host.owner._store, "save", fail_save)
    kwargs = dict(
        envelope=envelope,
        permit=_permit(envelope),
        store_root=tmp_path / "send",
        transport=Transport(),
        handle=_handle(),
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_identity=identity,
    )
    try:
        with pytest.raises((RuntimeError, ValueError)):
            attempt_envelope_bound_external_effect_send_v1(**kwargs)
        assert len(calls) == (0 if storage_fault else 1)
        with pytest.raises((RuntimeError, ValueError)):
            attempt_envelope_bound_external_effect_send_v1(**kwargs)
        assert len(calls) == (0 if storage_fault else 1)
        assert host.owner.active_sum_v1() > 0
    finally:
        host.close()


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-1", "0"])
def test_existing_adjudicator_rejects_invalid_quantities(number):
    from tests.ops.test_full_core_exchange_reconciliation_v1 import _identity, _order_row
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
        OfflineExchangeFixtureV1,
        build_offline_exchange_reconciliation_snapshot_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
        adjudicate_full_core_exchange_reconciliation_v1,
        LocalSubmitOutcome,
    )

    identity = _identity()
    fixture = OfflineExchangeFixtureV1(
        order_history={"code": "0", "data": [_order_row(state="filled", sz=number, acc=number)]}
    )
    result = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity,
        snapshot=build_offline_exchange_reconciliation_snapshot_v1(
            identity=identity, fixture=fixture
        ),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_UNKNOWN,
    )
    assert result.outcome == "HALTED_UNRESOLVED"
    assert result.exposure_retained


def test_identical_fill_redelivery_is_counted_once():
    from tests.ops.test_full_core_exchange_reconciliation_v1 import _identity, _order_row
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
        OfflineExchangeFixtureV1,
        build_offline_exchange_reconciliation_snapshot_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
        adjudicate_full_core_exchange_reconciliation_v1,
        LocalSubmitOutcome,
    )

    identity = _identity()
    order = _order_row(state="filled", acc="10")
    fill = {
        "instId": identity.native_id,
        "clOrdId": identity.clordid,
        "ordId": "ord-1",
        "tradeId": "t1",
        "fillSz": "10",
        "fillPx": "2",
    }
    fixture = OfflineExchangeFixtureV1(
        order_history={"code": "0", "data": [order]}, fills={"code": "0", "data": [fill, fill]}
    )
    result = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity,
        snapshot=build_offline_exchange_reconciliation_snapshot_v1(
            identity=identity, fixture=fixture
        ),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_UNKNOWN,
    )
    assert result.outcome == "CONFIRMED_FILLED"
    assert result.cumulative_filled_qty == "10"


@pytest.mark.parametrize("filled", [False, True])
def test_physical_death_after_submit_barrier_reconciles_same_reservation(tmp_path, filled):
    import json
    import signal
    import subprocess
    import time
    from pathlib import Path

    code = """
import sys, time, json
from pathlib import Path
from tests.ops.test_portfolio_execution_recovery_v1 import seed
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.evidence_v1 import write_json
root = Path(sys.argv[1])
host, rid, identity, envelope = seed(root)
host.owner.mark_execution_submit_boundary_v1(rid, identity)
write_json(root / "checkpoint.json", {"rid": rid, "identity": identity.to_dict(), "sum": str(host.owner.active_sum_v1())})
while True:
    time.sleep(1)
"""
    repo = Path(__file__).resolve().parents[2]
    child = subprocess.Popen(
        [str(repo / "scripts/pt"), "-c", code, str(tmp_path)],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 15
        checkpoint = tmp_path / "checkpoint.json"
        while not checkpoint.exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert checkpoint.exists(), (
            child.stderr.read().decode() if child.poll() is not None else "checkpoint timeout"
        )
        child.send_signal(signal.SIGKILL)
        child.wait(timeout=5)
        expected = json.loads(checkpoint.read_text())
        raw = expected["identity"]
        raw.pop("contract_id")
        identity = Identity(**raw)
        sign = "" if identity.selected_side.upper() in {"LONG", "ENTER_LONG"} else "-"
        positions = (
            ()
            if not filled
            else (
                {
                    "instId": identity.native_id,
                    "posSide": "net",
                    "pos": sign + identity.final_quantity,
                },
            )
        )
        host = _host(
            tmp_path,
            _fetch(uid=ACCOUNT, positions=positions),
            clock=lambda: NOW,
            expected_account=ACCOUNT,
        )
        host.reconciliation_transport = ReadPort(
            identity,
            state="filled" if filled else "canceled",
            filled=identity.final_quantity if filled else "0",
        )
        try:
            context = host.observe_v1({"LANE_1": _bound()})
            proof = context.execution_reconciliation[expected["rid"]]
            assert proof["matched"]
            assert proof["reservation_released"] is not filled
            assert host.owner.active_sum_v1() == (Decimal(expected["sum"]) if filled else 0)
            assert host.owner.budget_state_v1().recovery_required
        finally:
            host.close()
        # A repeated restart cannot resurrect the released reservation or reset
        # the frozen submit barrier; no send port is involved in recovery.
        host = _host(
            tmp_path,
            _fetch(uid=ACCOUNT, positions=positions),
            clock=lambda: NOW,
            expected_account=ACCOUNT,
        )
        host.reconciliation_transport = ReadPort(
            identity,
            state="filled" if filled else "canceled",
            filled=identity.final_quantity if filled else "0",
        )
        try:
            host.observe_v1({"LANE_1": _bound()})
            assert host.owner.active_sum_v1() == (Decimal(expected["sum"]) if filled else 0)
            assert (
                host.owner.execution_links_v1()[expected["rid"]]["phase"]
                == "SUBMIT_MAY_HAVE_OCCURRED"
            )
        finally:
            host.close()
    finally:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=5)
        child.stderr.close()
