"""Original FUTURES budget, one-shot dispatch, and signed GET recovery at fake boundaries."""

from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_futures_simulated_dispatch_v1 as dispatch,
    current_productive_n1_venue_quantity_limit_admission_v1 as quantity,
    envelope_bound_external_effect_send_seam_v1 as seam,
    productive_read_only_get_transport_v1 as wire,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import TRADE_ORDER_PATH
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    OriginalPermitTransportAttemptV1,
    load_external_effect_durable_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    parse_exchange_reconciliation_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreNonNetworkingTestPostTransportV1,
    FullCoreProductiveHttpPostError,
    FullCoreTradeOrderPostResultV1,
    TRANSPORT_CLASS_NON_NETWORKING_TEST,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    open_k1_account_observation_source_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1 import rest_recovery_v1 as rest
from src.ops.portfolio_capital_reservation_budget_v1.absolute_movement_cost_v1 import (
    EntryPublicMarkSourceV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.ops.test_current_usdc_xperp_financial_admission_v1 import (
    ACCOUNT,
    EPOCH,
    NATIVE,
    instrument,
    join,
    prepare,
)
from tests.ops.test_execution_reconciliation_get_provenance_v1 import (
    SignedReconciliationHttpFixture,
)
from tests.ops.test_k1_account_observation_source_v1 import InjectedOpener, _FakeKeychainBackend


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    host, args, _ = prepare(tmp_path, monkeypatch, tier_evidence=True, public_movement_policy=True)
    gate = tmp_path / "filegate.json"
    StatePersistence(str(gate)).save(KillSwitchState.ACTIVE)
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(gate))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    monkeypatch.setattr(wire, "utc_now_iso_v1", lambda: EPOCH)
    monkeypatch.setattr(quantity, "utc_now_iso_v1", lambda: EPOCH)
    monkeypatch.setattr(rest, "time", SimpleNamespace(time=host.clock))
    public_instruments = "/api/v5/public/instruments"
    opener = InjectedOpener(
        account=ACCOUNT, public_paths=(rest.MARK_HISTORY_CANDLES_PATH, public_instruments)
    )
    original_fetch = opener.fetch
    state = {"fault": None, "configs": 0, "size_queries": 0}
    mandate_path = tmp_path / "mandate.json"

    def fetch(path, params):
        if path == rest.MARK_HISTORY_CANDLES_PATH:
            assert params == {"instId": NATIVE, "bar": "1m", "limit": "100"}
            latest = int(host.clock() * 1000) // 60_000 * 60_000 - 60_000
            mark = Decimal(str(args["replay"].intermediate.market_context.mark_price))
            rows = []
            for offset in range(61):
                px = str(mark + (offset % 2) * Decimal("50"))
                rows.append([str(latest - offset * 60_000), px, px, px, px, "1"])
            return dict(code="0", data=rows)
        if path == public_instruments:
            assert params == {"instType": "FUTURES", "instId": NATIVE}
            return dict(code="0", data=[instrument(settlement="USD")])
        if path == "/api/v5/account/max-size":
            assert params == {"instId": NATIVE, "tdMode": "cross"}
            state["size_queries"] += 1
            limit = "0" if state["fault"] == "quantity" and state["size_queries"] == 2 else "999"
            return dict(code="0", data=[dict(instId=NATIVE, maxBuy=limit, maxSell=limit)])
        payload = original_fetch(path, params)
        if path == "/api/v5/account/config":
            payload["data"][0].update(settleCcy="USDC", autoLoan=False)
            state["configs"] += 1
            if state["configs"] == 3:
                if state["fault"] == "kill":
                    StatePersistence(str(gate)).save(KillSwitchState.KILLED)
                elif state["fault"] == "kill-reactivated":
                    StatePersistence(str(gate)).save(KillSwitchState.KILLED)
                    StatePersistence(str(gate)).save(KillSwitchState.ACTIVE)
                elif state["fault"] == "revoked":
                    mandate_path.unlink()
        elif path == "/api/v5/account/balance":
            payload["data"][0]["details"] = [dict(ccy="USDC", availEq="1000", frozenBal="0")]
        return payload

    opener.fetch = fetch
    monkeypatch.setattr(wire, "build_opener", lambda *handlers: opener)
    try:
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="futures-dispatch-simulated",
            max_request_count=80,
            account_inventory_guard=True,
            inventory_inst_type="FUTURES",
            clock=host.clock,
            k1_lookup_backend=_FakeKeychainBackend(),
        ) as source:
            args["injected"] = replace(
                args["injected"],
                futures_financial_custody=host.capture_futures_financial_custody_v1(source),
                absolute_movement_cost_observation=None,
                entry_public_mark_source=EntryPublicMarkSourceV1(
                    tmp_path / "public-facts",
                    wire.FullCoreProductiveReadOnlyGetTransportV1(handle=None, max_request_count=1),
                ),
            )
            entry = join(**args)
            assert entry.status == "PASS", entry.reason_codes
            bound = args["bound_instrument"]
            status, reasons, plan = try_bind_current_productive_venue_plan_v1(
                replay=entry.replay,
                bound_instrument=bound,
                session_id=host.session_id,
                run_id=host.session_id,
                composed_epoch=EPOCH,
                execution_mode="INTERNAL_SIMULATED_EXECUTION",
            )
            assert status.value == "PASS", reasons
            rid = entry.portfolio_reservation_id
            envelope = bind_final_order_envelope_from_venue_plan_v1(
                plan,
                admission_ref=host.session_id,
                provenance_ref=host.session_id,
                creation_epoch=EPOCH,
            )
            owner = host.owner
            owner.commit_internal_pre_external_effect_v1(rid)
            owner.bind_execution_plan_v1(
                rid,
                envelope,
                canonical_intent=entry.replay.intermediate.canonical_order_intent,
                venue_plan=plan,
            )
            original = owner.execution_plan_context_v1(rid, envelope)
            send = tmp_path / "send"
            mandate = dict(
                schema=dispatch.MANDATE_SCHEMA,
                execution_environment=host.execution_environment,
                budget_owner_root=original.root,
                account_identity=ACCOUNT,
                reservation_id=rid,
                native_id=NATIVE,
                envelope_digest=envelope.envelope_digest,
                plan_origin_digest=original.plan_origin_digest,
                transport_store_root=str(send),
                filegate_state_path=str(gate),
                filegate_state_sha256=sha256(gate.read_bytes()).hexdigest(),
                expires_at_utc=(
                    datetime.fromisoformat(EPOCH.replace("Z", "+00:00")) + timedelta(seconds=4)
                ).isoformat(),
            )
            mandate_path.write_text(json.dumps(mandate))
            yield (
                host,
                bound,
                state,
                dict(
                    host=host,
                    account_source=source,
                    reservation_id=rid,
                    envelope=envelope,
                    plan_context=original,
                    mandate_path=mandate_path,
                    store_root=send,
                    simulated_transport=FullCoreNonNetworkingTestPostTransportV1(),
                ),
            )
    finally:
        host.close()


@pytest.mark.parametrize("fault", ["kill", "kill-reactivated", "revoked", "quantity", "expired"])
def test_futures_send_veto_preserves_original_hold(seeded, fault):
    host, _, state, args = seeded
    state["fault"] = fault
    before = host.owner.active_sum_v1()
    if fault == "expired":
        path = args["mandate_path"]
        mandate = json.loads(path.read_bytes())
        mandate["expires_at_utc"] = EPOCH
        path.write_text(json.dumps(mandate))
    reason = {
        "kill": "POST_SAFETY_DURABLE_VETO",
        "kill-reactivated": "POST_SAFETY_FILEGATE_REVISION_CHANGED",
        "revoked": "POST_AUTHORITY_FUTURES_MANDATE_DENIED",
        "quantity": "POST_QUANTITY_DENIED",
        "expired": "POST_AUTHORITY_FUTURES_MANDATE_DENIED",
    }[fault]
    with pytest.raises(
        (FullCoreProductiveHttpPostError, seam.FullCoreEnvelopeBoundSendSeamError), match=reason
    ):
        dispatch.dispatch_current_futures_simulated_entry_v1(**args)
    record = load_external_effect_durable_consume_v1(store_root=args["store_root"])["record"]
    if fault == "expired":
        assert record is None
        assert state["configs"] == 1
    else:
        assert record["transport_attempt"]["phase"] == "ABORTED"
        assert record["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
    assert args["simulated_transport"].post_count == 0
    assert host.owner.active_sum_v1() == before > 0


def _observe_after_restart(
    host, bound, identity, monkeypatch, fault, *, legacy_without_floor=False
):
    fake_venue = SignedReconciliationHttpFixture(identity)
    fake_venue.fault = fault
    monkeypatch.setattr(wire, "build_opener", lambda *handlers: fake_venue)
    with open_k1_account_observation_source_v1(
        expected_account_identity=ACCOUNT,
        session_id="futures-restart-simulated",
        max_request_count=26,
        account_inventory_guard=True,
        inventory_inst_type="FUTURES",
        clock=host.clock,
        k1_lookup_backend=_FakeKeychainBackend(),
    ) as source:
        reopened = PortfolioBudgetHostV1(
            root=host.root,
            private_rest_fetch=source,
            repository_sha=host.repository_sha,
            session_id=host.session_id,
            expected_account_identity=ACCOUNT,
            clock=host.clock,
            execution_environment="INTERNAL_SIMULATED_EXECUTION",
            reconciliation_transport=source.transport._transport,
        )
        try:
            context = reopened.observe_v1({"LANE_1": bound})
            assert reopened.owner.budget_state_v1().recovery_required
            assert source.transport._transport.methods_used == ["GET"] * 26
            rid = identity.portfolio_reservation_id
            if legacy_without_floor:
                # Emulate the previous writer's durable shape after a later
                # unknown read. The earlier matched fill remains in history.
                with reopened.owner._lock:
                    stored = reopened.owner._execution_links[rid]["reconciliation"]
                    stored.pop("confirmed_filled_qty_floor")
                    reopened.owner._persist_locked()
            return context.execution_reconciliation[rid], reopened.owner.active_sum_v1()
        finally:
            reopened.close()


@pytest.mark.parametrize("boundary", ["before-permit-consume", "before-transport"])
def test_futures_crash_at_original_boundaries_keeps_the_hold_for_read_only_recovery(
    seeded, monkeypatch, boundary
):
    class Crash(BaseException):
        pass

    def stop(*args, **kwargs):
        raise Crash(boundary)

    host, bound, _, args = seeded
    held = host.owner.active_sum_v1()
    with monkeypatch.context() as scoped:
        if boundary == "before-permit-consume":
            scoped.setattr(seam, "persist_external_effect_durable_consume_v1", stop)
        else:
            scoped.setattr(OriginalPermitTransportAttemptV1, "mark_socket_boundary_v1", stop)
        with pytest.raises(Crash, match=boundary):
            dispatch.dispatch_current_futures_simulated_entry_v1(**args)
    rid = args["reservation_id"]
    link = host.owner.execution_links_v1()[rid]
    assert link["phase"] == "SUBMIT_MAY_HAVE_OCCURRED"
    identity = parse_exchange_reconciliation_identity_v1(link["identity"])
    record = load_external_effect_durable_consume_v1(store_root=args["store_root"])["record"]
    if boundary == "before-permit-consume":
        assert record is None
    else:
        assert record["transport_attempt"]["phase"] == "PRE_SOCKET"
    with pytest.raises(ValueError, match="EXECUTION_SUBMIT_REPLAY_OR_UNBOUND"):
        dispatch.dispatch_current_futures_simulated_entry_v1(**args)
    host.close()
    result, actual = _observe_after_restart(host, bound, identity, monkeypatch, "missing-order")
    assert not result["matched"] and not result["reservation_released"]
    assert actual == held > 0
    assert args["simulated_transport"].post_count == 0


@pytest.mark.parametrize("unknown", [False, True])
def test_futures_dispatch_once_and_reconcile_original_order_after_restart(
    seeded, monkeypatch, unknown
):
    host, bound, _, args = seeded
    envelope, rid = args["envelope"], args["reservation_id"]
    held = host.owner.active_sum_v1()
    transport = args["simulated_transport"]
    transport.simulated_response = FullCoreTradeOrderPostResultV1(
        post_attempted=True,
        venue_live_contact=False,
        method="POST",
        endpoint=TRADE_ORDER_PATH,
        http_status=0 if unknown else 200,
        payload={}
        if unknown
        else {
            "code": "0",
            "data": [dict(sCode="0", clOrdId=envelope.client_order_id, ordId="venue-order")],
        },
        transport_class=TRANSPORT_CLASS_NON_NETWORKING_TEST,
        unknown_outcome=unknown,
    )
    result = dispatch.dispatch_current_futures_simulated_entry_v1(**args)
    assert result.mocked_post_count == 1 and result.real_post_count == 0
    assert result.unknown_outcome is unknown
    assert result.post_submit_join.fill_observed is False
    assert result.post_submit_join.typed_outcome == ("UNKNOWN" if unknown else "ACKNOWLEDGED")
    assert transport.last_payload == seam._payload_from_envelope_v1(envelope)
    assert host.owner.active_sum_v1() == held
    record = load_external_effect_durable_consume_v1(store_root=args["store_root"])["record"]
    identity = parse_exchange_reconciliation_identity_v1(record["execution_identity"])
    assert identity.native_id == NATIVE
    assert identity.identity_digest() == record["execution_identity_digest"]
    assert record["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
    assert record["durable_state"] == ("SENT_INITIATED" if unknown else "COMPLETED")
    with pytest.raises(ValueError, match="EXECUTION_SUBMIT_REPLAY_OR_UNBOUND"):
        dispatch.dispatch_current_futures_simulated_entry_v1(**args)
    assert transport.post_count == 1
    host.close()

    def observe_again(fault):
        result = _observe_after_restart(host, bound, identity, monkeypatch, fault)
        assert transport.post_count == 1
        return result

    if unknown:
        result, actual = observe_again("missing-order")
        assert not result["matched"] and actual == held
        result, actual = observe_again("canceled-after-partial")
        assert result["matched"] and not result["reservation_released"] and actual == held
        assert result["confirmed_filled_qty_floor"] == "1"
        result, actual = _observe_after_restart(
            host, bound, identity, monkeypatch, "missing-order", legacy_without_floor=True
        )
        assert not result["matched"] and actual == held
        result, actual = observe_again("healthy-canceled")
        assert not result["matched"] and not result["reservation_released"] and actual == held
        assert "EXECUTION_CONFIRMED_FILL_QUANTITY_REGRESSED" in result["reason_codes"]
        assert result["confirmed_filled_qty_floor"] == "1"
    else:
        result, actual = observe_again("healthy-canceled")
        assert result["matched"] and result["reservation_released"] and actual == 0
