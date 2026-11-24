"""Original entry and session expiry: fake signed HTTP, no real credentials."""

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal
import json
from types import SimpleNamespace
from urllib.parse import urlsplit, parse_qs

import pytest

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.btc_demo_entry_submit_v1 import btc_demo_entry_reader_v1
from src.ops.btc_demo_session_close_v1 import (
    BOUNDED_SESSION_CLOSE,
    prepare_btc_demo_session_close_v1,
)
from src.ops.btc_demo_session_close_submit_v1 import execute_btc_demo_session_close_v1
from src.ops.full_core_live_path_composition_root_v1 import (
    pretrade_acquisition_v1,
    productive_read_only_get_transport_v1 as wire,
    external_effect_permit_durable_consume_v1 as durable,
)
from src.ops.gates.risk_gate import canonical_kill_switch_state_path
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    K1AccountObservationSourceV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    AuthenticatedEntryEpisodeRequestV1,
)
from tests.ops.test_btc_testnet_original_execution_receipt_v1 import (
    original_testnet_entry as original_testnet_entry,
    demo_entry as demo_entry,
    entry_send as entry_send,
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network
from tests.ops.test_current_productive_shared_post_owner_authority_v1 import (
    signed_post_authorization,
)
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    MockCurrentProductive29PIntegrityBackendV1,
)
from tests.ops.test_inspect_btc_demo_account_v1 import Response


def switch_original_demo_position(world, monkeypatch, root, index, recover_at_expiry=False):
    """Original Core seal, actual fake POST timeout, signed GET settlement."""
    from dataclasses import asdict
    from base64 import b64encode
    import hmac
    from tests.ops.test_btc_testnet_original_net_reversal_v1 import reversal_inputs
    from tests.ops.test_btc_testnet_original_net_submit_v1 import submit_unknown
    from tests.ops.test_authenticated_net_reversal_booking_v1 import SignedNetReversalGetFixture
    from tests.ops.test_portfolio_budget_host_v1 import _fetch
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        invoke_occupied_lane_governed_cycle_n1_consumer_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_double_play_reversal_v1 import (
        read_retained_net_reversal_post_context_v1,
        recover_submitted_net_reversal_v1,
    )

    root.mkdir()
    pairs, kwargs, _ = reversal_inputs(world, monkeypatch)
    kwargs["cycle_id_prefix"] += "-session-" + str(index)
    governed = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)[
        "LANE_3"
    ].governed_cycle_result
    assert governed.position_management_reversal is not None, governed.first_genuine_blocker
    host, pair = world["host"], pairs["LANE_3"]
    host.execution_incident_state_path = canonical_kill_switch_state_path()
    entry = AuthenticatedEntryEpisodeRequestV1(world["proof_root"], world["proof"])
    context = read_retained_net_reversal_post_context_v1(
        lane_pair=pair, recovery=world["context"], authenticated_entry=entry
    )
    monkeypatch.setattr(durable, "_utc_now_iso_v1", world["now"].isoformat)
    submit_unknown((world, pair, entry, context), root)
    old = world["context"].occupancy_payloads["POSITIONS"]["data"][0]
    data = dict(
        observed_at=(world["now"] + timedelta(seconds=1)).isoformat(),
        socket_ms=int(world["now"].timestamp() * 1000),
        envelope=asdict(context.envelope),
        account=host.account,
        closing_size=str(abs(context.reversal.current_contracts)),
        old_position_id=old["posId"],
        old_created_ms=old["cTime"],
        old_position_fee=old["fee"],
        position_id=str(8924 + index),
        venue_order_id=str(91235 + index),
        closing_trade_id=str(123 + index * 2),
        opening_trade_id=str(124 + index * 2),
    )
    if recover_at_expiry:
        started = world["host"].owner._bounded_demo_session_control["registration"][
            "started_at_utc"
        ]
        data["observed_at"] = (
            datetime.fromisoformat(started) + timedelta(seconds=3600)
        ).isoformat()
        monkeypatch.setattr(pretrade_acquisition_v1, "utc_now_iso_v1", lambda: data["observed_at"])

    class DemoNetGets(SignedNetReversalGetFixture):
        def position(self):
            return dict(
                super().position(),
                instType="FUTURES",
                ccy="USDC",
                avgPx=str(context.reversal.reference_mark),
            )

        def body(self, path, query):
            if path.endswith("/config"):
                rows = world["payloads"]["account"]["data"]
            elif path.endswith("/balance"):
                rows = _fetch(uid=host.account)(path, query)["data"]
            elif path.endswith("/positions"):
                rows = [self.position()]
            elif (
                path.endswith(("/orders-pending", "/orders-algo-pending")) or "/tradingBot/" in path
            ):
                rows = []
            elif path.endswith(("/orders-history", "/fills")) and "instId" not in query:
                rows = []
            else:
                rows = super().body(path, query)
            for row in rows:
                if "instType" in row:
                    row["instType"] = "FUTURES"
                for key in ("ccy", "feeCcy"):
                    if key in row:
                        row[key] = "USDC"
                for key in ("avgPx", "fillPx", "markPx"):
                    if key in row:
                        row[key] = str(context.reversal.reference_mark)
                if "settledPnl" in row:
                    row["settledPnl"] = "0"
            return rows

        @contextmanager
        def open(self, request, timeout):
            url = urlsplit(request.full_url)
            assert (
                request.get_method() == "GET" and request.get_header("X-simulated-trading") == "1"
            )
            timestamp = request.get_header("Ok-access-timestamp")
            endpoint = url.path + ("?" + url.query if url.query else "")
            assert request.get_header("Ok-access-sign").encode() == b64encode(
                hmac.digest(b"fixture-secret", f"{timestamp}GET{endpoint}".encode(), "sha256")
            )
            raw = json.dumps(dict(code="0", data=self.body(url.path, parse_qs(url.query)))).encode()
            yield SimpleNamespace(status=200, url=request.full_url, read=lambda: raw)

    gets = DemoNetGets(data, "complete")
    monkeypatch.setattr(wire, "build_opener", lambda *_: gets)
    monkeypatch.setattr(wire, "utc_now_iso_v1", gets.clock.isoformat)
    host.clock = gets.clock.timestamp
    host.reconciliation_transport = wire.FullCoreProductiveReadOnlyGetTransportV1(
        handle=host.reconciliation_transport._handle,
        execution_environment="TESTNET",
        max_request_count=200,
    )
    result = recover_submitted_net_reversal_v1(
        lane_pair=pair, get_budget_host=lambda: host, proof_root=world["proof_root"]
    )
    assert result.booking_digest, result.reconciliation_blocker
    source = K1AccountObservationSourceV1(
        credential=host.reconciliation_transport._handle,
        transport=host.reconciliation_transport,
        expected_account_identity=host.account,
        session_id=host.session_id,
        clock=host.clock,
        account_inventory_guard=True,
        inventory_inst_type="FUTURES",
    )
    host.fetch = source
    recovery, proofs = host.observe_authenticated_execution_reconciliation_v1(
        {"LANE_3": world["bound"]}, proof_root=world["proof_root"]
    )
    episode = recovery.bind_current_authenticated_entry_episode_v1(
        lane_id="LANE_3",
        proof_root=world["proof_root"],
        proof=proofs[world["rid"]],
        config_digest=world["episode"].binding.config_digest,
    )
    world.update(context=recovery, proof=proofs[world["rid"]], episode=episode, now=gets.clock)


@pytest.fixture
def expired_position(original_testnet_entry, monkeypatch, request, tmp_path):
    world = original_testnet_entry
    variant = getattr(request, "param", 0)
    count, late = variant if type(variant) is tuple else (variant, False)
    for index in range(count):
        switch_original_demo_position(
            world,
            monkeypatch,
            tmp_path / ("switch-" + str(index)),
            index,
            recover_at_expiry=late and index == count - 1,
        )
    host = world["host"]
    registration = host.owner._bounded_demo_session_control["registration"]
    now = datetime.fromisoformat(registration["started_at_utc"]) + timedelta(seconds=3600)
    monkeypatch.setattr(pretrade_acquisition_v1, "utc_now_iso_v1", now.isoformat)
    from src.ops import btc_demo_session_close_v1 as close_owner

    monkeypatch.setattr(close_owner, "utc_now_iso_v1", now.isoformat)
    monkeypatch.setattr(wire, "utc_now_iso_v1", now.isoformat)
    monkeypatch.setattr(durable, "_utc_now_iso_v1", now.isoformat)
    host.clock = now.timestamp
    handle = host.reconciliation_transport._handle
    host.reconciliation_transport = wire.FullCoreProductiveReadOnlyGetTransportV1(
        handle=handle, execution_environment="TESTNET", max_request_count=200
    )
    account_source = K1AccountObservationSourceV1(
        credential=handle,
        transport=host.reconciliation_transport,
        expected_account_identity=host.account,
        session_id=host.session_id,
        clock=host.clock,
        account_inventory_guard=True,
        inventory_inst_type="FUTURES",
    )
    host.fetch = account_source
    host.execution_incident_state_path = canonical_kill_switch_state_path()
    recovery, proofs = host.observe_authenticated_execution_reconciliation_v1(
        {"LANE_3": world["bound"]}, proof_root=world["proof_root"]
    )
    request = AuthenticatedEntryEpisodeRequestV1(world["proof_root"], proofs[world["rid"]])

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now if tz is None else now.astimezone(tz)

    monkeypatch.setattr(demo, "datetime", Clock)
    quote_faults = {}

    class QuoteGets:
        def open(self, request, timeout):
            path = urlsplit(request.full_url).path
            key = {
                "/api/v5/account/config": "account",
                "/api/v5/account/instruments": "instruments",
                "/api/v5/account/trade-fee": "fees",
                "/api/v5/market/books": "book",
            }[path]
            rows = deepcopy(world["payloads"][key]["data"])
            if key in {"fees", "book"}:
                rows[0]["ts"] = str(int(now.timestamp() * 1000))
                if quote_faults.get("fault") == "stale":
                    rows[0]["ts"] = str(int((now.timestamp() - 30) * 1000))
            if key == "book":
                mark = Decimal(world["context"].occupancy_payloads["POSITIONS"]["data"][0]["avgPx"])
                rows[0].update(
                    asks=[
                        [str(mark + Decimal("0.1")), "0.0002"],
                        [str(mark + Decimal("0.2")), "1000"],
                    ],
                    bids=[
                        [str(mark - Decimal("0.1")), "0.0002"],
                        [str(mark - Decimal("0.2")), "1000"],
                    ],
                )
                if quote_faults.get("fault") == "depth":
                    for side in ("asks", "bids"):
                        for level in rows[0][side]:
                            level[1] = "0.00000001"
            return Response(request.full_url, rows)

    monkeypatch.setattr(demo, "build_opener", lambda *_: QuoteGets())
    reads = btc_demo_entry_reader_v1(signing_handle=handle)
    try:
        yield SimpleNamespace(
            world=world,
            host=host,
            now=now,
            recovery=recovery,
            entry_request=request,
            reads=reads,
            signing_handle=handle,
            quote_faults=quote_faults,
        )
    finally:
        account_source.close()


def send_close(expired_position, tmp_path, post_outcome="ack"):
    case = expired_position
    owner = case.host.owner
    before = owner.local_commitment_readback_v1().commitments
    context = prepare_btc_demo_session_close_v1(
        recovery=case.recovery, entry_request=case.entry_request, reads=case.reads
    )
    assert context.envelope.path_kind == BOUNDED_SESSION_CLOSE
    assert context.envelope.reduce_only and context.envelope.pos_side == "net"
    assert Decimal(context.envelope.quantity) == abs(Decimal(context.plan["position"]["pos"]))
    assert Decimal(context.plan["quote"]["estimated_fee_usdc"]) > 0
    assert owner._bounded_demo_session_control["phase"] == "RUNNING"
    auth, _ = signed_post_authorization(
        tmp_path,
        context.envelope,
        account=case.host.account,
        action=BOUNDED_SESSION_CLOSE,
        execution_environment="TESTNET",
    )
    calls = []

    class Post:
        @contextmanager
        def open(self, request, timeout):
            assert request.full_url == "https://eea.okx.com/api/v5/trade/order"
            assert request.get_header("X-simulated-trading") == "1"
            body = json.loads(request.data)
            assert body["reduceOnly"] is True and body["posSide"] == "net"
            calls.append(body)
            if post_outcome == "timeout":
                raise TimeoutError("offline uncertainty at the original socket boundary")
            yield SimpleNamespace(
                status=200,
                url=request.full_url,
                read=lambda: json.dumps(
                    dict(
                        code="0",
                        data=[
                            dict(sCode="0", clOrdId=context.envelope.client_order_id, ordId="99912")
                        ],
                    )
                ).encode(),
            )

    args = dict(
        context=context,
        authorization=auth,
        signing_handle=case.signing_handle,
        baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        perform_real_venue_post=True,
        execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
            origin_main=case.host.repository_sha, head=case.host.repository_sha, drift=""
        ),
        opener_factory=Post,
    )
    result = execute_btc_demo_session_close_v1(**args)
    assert result.post_attempted and len(calls) == 1
    assert result.unknown_outcome is (post_outcome == "timeout")
    assert owner._bounded_demo_session_control["phase"] == "CLOSING"
    assert owner.local_commitment_readback_v1().commitments == before
    with pytest.raises(ValueError, match="ALREADY_CONSUMED"):
        execute_btc_demo_session_close_v1(**args)
    assert len(calls) == 1
    return context


@pytest.mark.parametrize("entry_send", ["bounded-session"], indirect=True)
def test_session_close_is_distinct_reduce_only_and_keeps_original_hold_until_confirmation(
    expired_position, tmp_path
):
    send_close(expired_position, tmp_path)


def final_gets(case, context, monkeypatch, fault=None):
    from base64 import b64encode
    import hmac
    from tests.ops.test_portfolio_budget_host_v1 import _fetch
    from src.ops import btc_demo_session_close_reconciliation_v1 as close_reconciliation

    now = case.now + timedelta(seconds=1)
    monkeypatch.setattr(wire, "utc_now_iso_v1", now.isoformat)
    monkeypatch.setattr(close_reconciliation, "utc_now_iso_v1", now.isoformat)
    case.host.clock = now.timestamp
    case.host.fetch.clock = now.timestamp
    stamp = int(now.timestamp() * 1000)
    envelope, position = context.envelope, context.plan["position"]
    order = dict(
        instId=envelope.instrument_id,
        instType="FUTURES",
        clOrdId=envelope.client_order_id,
        ordId="99912",
        sz=envelope.quantity,
        accFillSz=envelope.quantity,
        state="filled",
        side=envelope.side,
        posSide="net",
        tdMode="cross",
        ordType="market",
        reduceOnly=True,
        uTime=str(stamp - 100),
    )
    fill = dict(
        order,
        tradeId="99913",
        billId="99914",
        fillSz=envelope.quantity,
        fillPx="100000",
        fillTime=str(stamp - 200),
        fee="-0.02",
        feeCcy="USDC",
        fillPnl="0.20",
    )
    history = dict(
        instId=envelope.instrument_id,
        instType="FUTURES",
        posId=position["posId"],
        cTime=position["cTime"],
        uTime=str(stamp - 100),
        direction="long" if Decimal(position["pos"]) > 0 else "short",
        posSide="net",
        mgnMode="cross",
        ccy="USDC",
        type="2",
        openMaxPos=envelope.quantity,
        closeTotalPos=envelope.quantity,
        pnl="0.20",
        fee=str(Decimal(position["fee"]) - Decimal("0.02")),
        fundingFee="-0.01",
        settledPnl="0",
        liqPenalty="0",
        realizedPnl=str(Decimal("0.17") + Decimal(position["fee"])),
    )
    calls = []

    class Gets:
        @contextmanager
        def open(self, request, timeout):
            url = urlsplit(request.full_url)
            assert request.get_method() == "GET" and url.hostname == "eea.okx.com"
            assert request.get_header("X-simulated-trading") == "1"
            timestamp = request.get_header("Ok-access-timestamp")
            endpoint = url.path + ("?" + url.query if url.query else "")
            assert request.get_header("Ok-access-sign").encode() == b64encode(
                hmac.digest(b"fixture-secret", f"{timestamp}GET{endpoint}".encode(), "sha256")
            )
            calls.append(endpoint)
            path = url.path
            if "after" in parse_qs(url.query):
                rows = []
            elif path.endswith("/config"):
                rows = case.world["payloads"]["account"]["data"]
            elif path.endswith("/balance"):
                rows = _fetch(uid=case.host.account)(path, {})["data"]
                rows[0]["details"] = [{**row, "ccy": "USDC"} for row in rows[0]["details"]]
            elif path.endswith("/positions"):
                rows = [] if fault != "nonflat" else [position]
            elif path.endswith("/positions-history"):
                rows = [dict(history, realizedPnl="0.99")] if fault == "cash" else [history]
            elif path.endswith("/fills"):
                rows = [] if fault == "missing-fill" else [fill]
            elif path.endswith(("/orders-history", "/order")):
                rows = (
                    [
                        dict(
                            order,
                            state="partially_filled",
                            accFillSz=str(Decimal(envelope.quantity) / 2),
                        )
                    ]
                    if fault == "partial"
                    else [order]
                )
            elif path.endswith("/orders-pending"):
                rows = [order] if fault == "pending" else []
            else:
                assert path.endswith("/orders-algo-pending") or "/tradingBot/" in path
                rows = []
            raw = json.dumps(dict(code="0", data=rows)).encode()
            yield SimpleNamespace(status=200, url=request.full_url, read=lambda: raw)

    monkeypatch.setattr(wire, "build_opener", lambda *_: Gets())
    return calls


@pytest.mark.parametrize("entry_send", ["bounded-session"], indirect=True)
@pytest.mark.parametrize("expired_position", [0, 1, 2, (1, True)], indirect=True)
@pytest.mark.parametrize("post_outcome", ["ack", "timeout"])
def test_confirmed_session_close_books_cash_releases_once_and_cold_reproves(
    expired_position, tmp_path, monkeypatch, post_outcome
):
    from src.ops.btc_demo_session_close_reconciliation_v1 import reconcile_btc_demo_session_close_v1
    from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3

    case = expired_position
    context = send_close(case, tmp_path, post_outcome)
    allocation = case.host.owner.risk_snapshot_v1()["state"]["slot_capital_allocation"]
    calls = final_gets(case, context, monkeypatch)
    receipt = reconcile_btc_demo_session_close_v1(host=case.host)
    reversals = case.host.owner._live_net_reversal_bookings.get(case.world["rid"], ())
    assert Decimal(receipt["net_result_usdc"]) == Decimal("0.16" if not reversals else "0.17")
    assert Decimal(receipt["previously_booked_opening_fee_usdc"]) == Decimal(
        "0" if not reversals else "-0.02"
    )
    assert case.host.owner.active_sum_v1() == 0
    assert case.host.owner._bounded_demo_session_control["phase"] == "CLOSED"
    before = list(calls)
    assert reconcile_btc_demo_session_close_v1(host=case.host) == receipt
    assert calls == before
    owner = case.host.owner
    root = owner._store.root
    owner.close()
    cold = BtcDemoBudgetOwnerV3(
        durable_root=root,
        durable_account_identity=case.host.account,
        durable_mode="recover",
        durable_lane_bindings={"LANE_3": case.world["bound"]},
    )
    try:
        assert cold.active_sum_v1() == 0
        assert cold._bounded_demo_session_control["close_receipt"] == receipt
        assert cold.risk_snapshot_v1()["state"]["slot_capital_allocation"] == allocation
        summary = cold.bounded_demo_session_result_v1()
        assert Decimal(summary["initial_usdc"]) == 25
        expected = (
            Decimal("25")
            + Decimal(receipt["net_result_usdc"])
            + sum((Decimal(row["net_result_usdc"]) for row in reversals), Decimal(0))
        )
        assert Decimal(summary["final_session_basis_usdc"]) == expected
        assert (
            expected
            == {0: Decimal("25.16"), 1: Decimal("25.31"), 2: Decimal("25.46")}[len(reversals)]
        )
        assert summary["reversal_count"] == len(reversals)
    finally:
        cold.close()


@pytest.mark.parametrize("entry_send", ["bounded-session"], indirect=True)
@pytest.mark.parametrize("fault", ["nonflat", "cash", "missing-fill", "partial", "pending"])
def test_unconfirmed_close_never_books_or_releases(expired_position, tmp_path, monkeypatch, fault):
    from src.ops.btc_demo_session_close_reconciliation_v1 import reconcile_btc_demo_session_close_v1

    case = expired_position
    context = send_close(case, tmp_path)
    before = case.host.owner.local_commitment_readback_v1().commitments
    head = case.host.owner._store.head
    final_gets(case, context, monkeypatch, fault)
    with pytest.raises((ValueError, RuntimeError)):
        reconcile_btc_demo_session_close_v1(host=case.host)
    assert case.host.owner.local_commitment_readback_v1().commitments == before
    assert case.host.owner._store.head == head
    assert case.host.owner._bounded_demo_session_control["phase"] == "CLOSING"


@pytest.mark.parametrize("entry_send", ["bounded-session"], indirect=True)
@pytest.mark.parametrize("fault", ["depth", "stale", "early"])
def test_close_preparation_requires_deadline_current_depth_and_fees(
    expired_position, monkeypatch, fault
):
    from src.ops import btc_demo_session_close_v1 as close_owner

    case = expired_position
    head = case.host.owner._store.head
    held = case.host.owner.local_commitment_readback_v1().commitments
    if fault == "early":
        monkeypatch.setattr(
            close_owner, "utc_now_iso_v1", (case.now - timedelta(seconds=1)).isoformat
        )
    else:
        case.quote_faults["fault"] = fault
    with pytest.raises((ValueError, RuntimeError)):
        prepare_btc_demo_session_close_v1(
            recovery=case.recovery, entry_request=case.entry_request, reads=case.reads
        )
    assert case.host.owner._store.head == head
    assert case.host.owner.local_commitment_readback_v1().commitments == held


@pytest.mark.parametrize("entry_send", ["bounded-session"], indirect=True)
def test_cold_recovery_after_unknown_close_keeps_hold_until_authenticated_settlement(
    expired_position, tmp_path, monkeypatch
):
    from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3
    from src.ops.btc_demo_session_close_reconciliation_v1 import reconcile_btc_demo_session_close_v1

    case = expired_position
    context = send_close(case, tmp_path, "timeout")
    old = case.host.owner
    held = old.local_commitment_readback_v1().commitments
    old.close()
    cold = BtcDemoBudgetOwnerV3(
        durable_root=old._store.root,
        durable_account_identity=case.host.account,
        durable_mode="recover",
        durable_lane_bindings={"LANE_3": case.world["bound"]},
    )
    case.host.owner = cold
    assert cold._bounded_demo_session_control["phase"] == "CLOSING"
    assert cold.local_commitment_readback_v1().commitments == held
    with pytest.raises(ValueError, match="NEW_RISK_WINDOW_CLOSED"):
        cold.require_bounded_demo_risk_window_v1()
    final_gets(case, context, monkeypatch)
    receipt = reconcile_btc_demo_session_close_v1(host=case.host)
    assert Decimal(receipt["net_result_usdc"]) == Decimal("0.16")
    assert cold.active_sum_v1() == 0


@pytest.mark.parametrize("entry_send", ["bounded-session"], indirect=True)
def test_final_source_loss_fences_session_result_after_confirmation(
    expired_position, tmp_path, monkeypatch
):
    from src.ops.btc_demo_session_close_reconciliation_v1 import reconcile_btc_demo_session_close_v1

    case = expired_position
    context = send_close(case, tmp_path)
    final_gets(case, context, monkeypatch)
    reconcile_btc_demo_session_close_v1(host=case.host)
    proof = context.store_root_v1() / "confirmed-close-originals.json"
    body = json.loads(proof.read_bytes())
    body["history_get"]["body"] = '{"code":"0","data":[]}'
    proof.write_text(json.dumps(body))
    with pytest.raises((ValueError, RuntimeError)):
        case.host.owner.bounded_demo_session_result_v1()


@pytest.mark.parametrize("entry_send", ["bounded-session"], indirect=True)
@pytest.mark.parametrize("fault", ["live-grant", "foreign-signer", "late-revocation"])
def test_close_authority_is_testnet_scoped_and_rechecked_at_socket(
    expired_position, tmp_path, monkeypatch, fault
):
    from tests.ops.test_current_productive_shared_post_owner_authority_v1 import revoke
    from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
        bind_already_held_k1_venue_auth_session_v1,
        release_k1_venue_auth_session_v1,
    )

    case = expired_position
    context = prepare_btc_demo_session_close_v1(
        recovery=case.recovery, entry_request=case.entry_request, reads=case.reads
    )
    auth, key = signed_post_authorization(
        tmp_path,
        context.envelope,
        account=case.host.account,
        action=BOUNDED_SESSION_CLOSE,
        execution_environment="LIVE" if fault == "live-grant" else "TESTNET",
    )
    held = case.host.owner.local_commitment_readback_v1().commitments
    calls = []

    class ForbiddenPost:
        def open(self, request, timeout):
            calls.append(request)
            raise AssertionError("No socket may open")

    def opener():
        if fault == "late-revocation":
            revoke(auth, key)
        return ForbiddenPost()

    handle = case.signing_handle
    if fault == "foreign-signer":
        handle = bind_already_held_k1_venue_auth_session_v1(
            api_key="foreign-fixture-key",
            api_secret="fixture-secret",
            passphrase="fixture-phrase",
            execution_environment="TESTNET",
        )
    try:
        with pytest.raises((ValueError, RuntimeError)):
            execute_btc_demo_session_close_v1(
                context=context,
                authorization=auth,
                signing_handle=handle,
                baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                perform_real_venue_post=True,
                execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
                    origin_main=case.host.repository_sha, head=case.host.repository_sha, drift=""
                ),
                opener_factory=opener,
            )
        assert not calls
        assert case.host.owner.local_commitment_readback_v1().commitments == held
        send = durable.load_external_effect_durable_consume_v1(store_root=context.store_root_v1())
        if fault == "late-revocation":
            assert send["record"]["transport_attempt"]["phase"] == "ABORTED"
        else:
            assert not send["present"]
    finally:
        if handle is not case.signing_handle:
            release_k1_venue_auth_session_v1(handle)
