"""Original signed reads at injected boundaries and original durable owners under FILEGATE."""

from contextlib import contextmanager
from dataclasses import replace
import json

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_futures_simulated_dispatch_v1 as dispatch,
    productive_read_only_get_transport_v1 as wire,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    load_external_effect_durable_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    parse_exchange_reconciliation_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreTradeOrderPostResultV1,
    TRANSPORT_CLASS_NON_NETWORKING_TEST,
)
from src.ops.gates.risk_gate import kill_switch_should_block_trading
from src.ops.offline_fault_monitor_v1 import OfflineFaultMonitorV1, OfflineFaultPortsV1
from src.ops.offline_public_feed_account_reconciliation_v1 import (
    capture_offline_feed_account_reconciliation_v1,
)
from src.ops.offline_public_feed_recovery_v1 import OfflinePublicFeedRecoveryError
from src.ops.offline_public_feed_restart_v1 import OfflinePublicFeedRestartV1
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    FUTURES_INVENTORY_REQUEST_COUNT,
    open_k1_account_observation_source_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import InstrumentRefV1
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import EVIDENCE_FILENAME
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
    ProductiveReconciliationEvidenceV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import (
    persist_reconciliation_bundle_atomic,
)
from src.ops.productive_reconciliation_runtime_binding_v1.single_writer_v1 import (
    ConflictingWriterError,
    ProductivePortfolioSingleWriterV1,
)
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.ops.test_current_futures_simulated_dispatch_v1 import seeded
from tests.ops.test_current_scope_public_mark_source_v1 import push
from tests.ops.test_execution_reconciliation_get_provenance_v1 import (
    SignedReconciliationHttpFixture,
)
from tests.ops.test_k1_account_observation_source_v1 import InjectedOpener, _FakeKeychainBackend
from tests.ops.test_offline_public_feed_recovery_v1 import FeedFixture


def _account_payload(path, payload):
    if path == "/api/v5/account/config":
        payload["data"][0]["settleCcy"] = "USDC"
    if path == "/api/v5/account/balance":
        payload["data"][0]["details"] = [dict(ccy="USDC", availEq="1000", frozenBal="0")]
    return payload


class ReconciliationVenue(SignedReconciliationHttpFixture):
    def body(self, path, params):
        payload = json.loads(super().body(path, params))
        return json.dumps(_account_payload(path, payload)).encode()


def _mark_feed(
    host, bound, monkeypatch, *, started_at=None, mark_px="101", index_px=None, repair=True
):
    feed = FeedFixture(
        host.root.parent,
        monkeypatch,
        instrument=InstrumentRefV1(
            canonical_instrument_id=bound.instrument_id,
            venue_native_id=bound.venue_native_id,
            venue="okx_eea",
            instrument_type="FUTURES",
            settlement_asset="USD",
            mapping_provenance_digest=bound.selection_integrity_digest,
        ),
        session_id=host.session_id,
        started_at=started_at,
    )
    values = {"markPx": mark_px}
    if index_px is not None:
        values["idxPx"] = index_px
    feed.frames = [push(native=bound.venue_native_id, timestamp=feed.event_ms(1), **values)]
    receipt = feed.run() if repair else None
    return feed, receipt


@contextmanager
def _open_budget_host(prior, feed, venue, monkeypatch, *, reads):
    monkeypatch.setattr(wire, "build_opener", lambda *handlers: venue)
    monkeypatch.setattr(wire, "utc_now_iso_v1", lambda: feed.now.isoformat())

    def now():
        return feed.now.timestamp()

    with open_k1_account_observation_source_v1(
        expected_account_identity=prior.expected_account_identity,
        session_id=prior.session_id,
        max_request_count=reads,
        account_inventory_guard=True,
        inventory_inst_type="FUTURES",
        clock=now,
        k1_lookup_backend=_FakeKeychainBackend(),
    ) as source:
        host = PortfolioBudgetHostV1(
            root=prior.root,
            private_rest_fetch=source,
            repository_sha=prior.repository_sha,
            session_id=prior.session_id,
            expected_account_identity=prior.expected_account_identity,
            clock=now,
            execution_environment=dispatch.SIMULATED_ENVIRONMENT,
            reconciliation_transport=source.transport._transport,
        )
        try:
            yield host
        finally:
            host.close()


def _inventory_venue(account, **kwargs):
    venue = InjectedOpener(account=account, **kwargs)
    fetch = venue.fetch
    venue.fetch = lambda path, query: _account_payload(path, fetch(path, query))
    return venue


def test_flat_original_inventory_and_commitments_bind_to_feed_revision(seeded, monkeypatch):
    old_host, bound, _, send = seeded
    generation = old_host.owner.local_commitment_readback_v1().generation_digest
    hold = old_host.owner.local_commitment_readback_v1().active_commitment_sum
    old_host.close()
    feed, mark = _mark_feed(old_host, bound, monkeypatch)
    venue = _inventory_venue(old_host.account)
    with _open_budget_host(
        old_host, feed, venue, monkeypatch, reads=FUTURES_INVENTORY_REQUEST_COUNT
    ) as host:
        evidence = capture_offline_feed_account_reconciliation_v1(
            feed.cold_reader(), host=host, bindings={"LANE_1": bound}
        )
        assert evidence["feed_binding"] == mark["binding"]
        assert evidence["feed_mark_fact_sha256"] == mark["mark"]["fact_sha256"]
        assert evidence["local_commitment_generation"] == generation
        assert evidence["active_local_commitment_usdc"] == str(hold)
        assert evidence["execution_reconciliation"] == {}
        assert host.owner.budget_state_v1().recovery_required
    assert len(venue.requests) == FUTURES_INVENTORY_REQUEST_COUNT
    assert send["simulated_transport"].post_count == 0
    assert feed.incident.state_path.read_bytes() == feed.initial_state
    assert kill_switch_should_block_trading(explicit_active=False)


@pytest.mark.parametrize(
    ("pending", "reason"),
    [
        (dict(pending=True), "STARTUP_PENDING_ORDERS_UNRESOLVED"),
        (dict(algo_pending="iceberg"), "STARTUP_PENDING_ALGO_ORDERS_UNRESOLVED"),
        (dict(bot_fault="contract_grid"), "K1_FUTURES_ACCOUNT_BOT_CUSTODY_PRESENT"),
        (dict(bot_fault="bot-continuation"), "OBSERVATION_RESPONSE_SCOPE_UNPROVEN"),
    ],
)
def test_pending_or_incomplete_account_inventory_stays_blocked(
    seeded, monkeypatch, pending, reason
):
    old_host, bound, _, _ = seeded
    old_host.close()
    feed, _ = _mark_feed(old_host, bound, monkeypatch)
    venue = _inventory_venue(old_host.account, **pending)
    with _open_budget_host(
        old_host, feed, venue, monkeypatch, reads=FUTURES_INVENTORY_REQUEST_COUNT
    ) as host:
        with pytest.raises((ValueError, RuntimeError), match=reason):
            capture_offline_feed_account_reconciliation_v1(
                feed.repair, host=host, bindings={"LANE_1": bound}
            )
    assert feed.incident.state_path.read_bytes() == feed.initial_state
    assert kill_switch_should_block_trading(explicit_active=False)


def _simulated_unknown_submission(send):
    transport = send["simulated_transport"]
    transport.simulated_response = FullCoreTradeOrderPostResultV1(
        post_attempted=True,
        venue_live_contact=False,
        method="POST",
        endpoint="/api/v5/trade/order",
        http_status=0,
        payload={},
        transport_class=TRANSPORT_CLASS_NON_NETWORKING_TEST,
        unknown_outcome=True,
    )
    result = dispatch.dispatch_current_futures_simulated_entry_v1(**send)
    assert result.unknown_outcome and result.mocked_post_count == 1
    record = load_external_effect_durable_consume_v1(store_root=send["store_root"])["record"]
    return parse_exchange_reconciliation_identity_v1(record["execution_identity"])


def _store_preincident_position(host, bound):
    """Use the original writer to represent a previously reconciled position in the fixture."""
    root = host.root / "reconciliation"
    prior = ProductiveReconciliationEvidenceV1(**json.loads((root / EVIDENCE_FILENAME).read_text()))
    position = PositionTruthV1.from_signed(instrument_id=bound.instrument_id, signed_quantity="1")
    stored = PortfolioTruthSnapshotV1(positions=(position,))
    writer = ProductivePortfolioSingleWriterV1(state_root=root, session_id=host.session_id)
    writer.acquire(now_unix=host.clock())
    try:
        persist_reconciliation_bundle_atomic(
            state_root=root,
            writer=writer,
            portfolio=stored,
            evidence=replace(prior, post_state_digest=stored.digest()),
        )
    finally:
        writer.release()


@pytest.mark.parametrize(
    "fault", ["missing-order", "position-contradiction", "canceled-after-partial"]
)
def test_original_owned_order_and_fill_reconciliation_preserves_hold(seeded, monkeypatch, fault):
    old_host, bound, _, send = seeded
    identity = _simulated_unknown_submission(send)
    hold = old_host.owner.active_sum_v1()
    if fault == "canceled-after-partial":
        _store_preincident_position(old_host, bound)
    old_host.close()
    feed, mark = _mark_feed(old_host, bound, monkeypatch)
    venue = ReconciliationVenue(identity)
    venue.fault = "canceled-after-partial" if fault == "position-contradiction" else fault
    with _open_budget_host(old_host, feed, venue, monkeypatch, reads=26) as host:
        if fault == "missing-order":
            with pytest.raises(OfflinePublicFeedRecoveryError, match="EXECUTION_UNRESOLVED"):
                capture_offline_feed_account_reconciliation_v1(
                    feed.repair, host=host, bindings={"LANE_1": bound}
                )
        elif fault == "position-contradiction":
            with pytest.raises(
                OfflinePublicFeedRecoveryError, match="ORIGINAL_POSITION_NOT_MATCHED"
            ):
                capture_offline_feed_account_reconciliation_v1(
                    feed.repair, host=host, bindings={"LANE_1": bound}
                )
        else:
            result = capture_offline_feed_account_reconciliation_v1(
                feed.repair, host=host, bindings={"LANE_1": bound}
            )
            outcome = result["execution_reconciliation"][identity.portfolio_reservation_id]
            assert outcome["confirmed_filled_qty"] == "1"
            assert outcome["identity_digest"] == identity.identity_digest()
            assert outcome["budget_sequence"] > 0
            assert result["feed_binding"] == mark["binding"]
        assert host.owner.active_sum_v1() == hold > 0
        assert host.owner.budget_state_v1().recovery_required
        assert host.fetch.transport._transport.methods_used == ["GET"] * 26
    assert send["simulated_transport"].post_count == 1
    assert kill_switch_should_block_trading(explicit_active=False)


@pytest.mark.parametrize("fault", ["missing-order", "canceled-after-partial"])
def test_monitor_reobserves_original_obligation_after_cold_restart(
    seeded, monkeypatch, tmp_path, fault
):
    old_host, bound, _, send = seeded
    identity = _simulated_unknown_submission(send)
    hold = old_host.owner.active_sum_v1()
    if fault == "canceled-after-partial":
        _store_preincident_position(old_host, bound)
    old_host.close()
    feed, _ = _mark_feed(old_host, bound, monkeypatch, repair=False)
    directory = tmp_path.resolve().with_name(tmp_path.name + "-witness")
    directory.mkdir(mode=0o700)
    key = b"isolated test for read-only monitoring"

    def monitor():
        safety = OfflinePublicFeedRestartV1(
            feed.cold_reader(), authority_key=key, witness_directory=directory
        )
        return safety, OfflineFaultMonitorV1(
            safety, interval_seconds=1, clock=lambda: feed.now.timestamp()
        )

    safety, first = monitor()
    safety.initialize_witness_v1()
    safety.record_kill_v1(reason="EMERGENCY")

    @contextmanager
    def open_ports():
        venue = ReconciliationVenue(identity)
        venue.fault = fault
        with _open_budget_host(old_host, feed, venue, monkeypatch, reads=26) as host:
            yield OfflineFaultPortsV1(host=host, bound=bound)
            assert host.owner.active_sum_v1() == hold
            assert host.fetch.transport._transport.methods_used == ["GET"] * 26

    initial = first.poll_v1(open_ports)
    assert initial["status"] == "BLOCKED_OBSERVING", initial.get("reason")
    _, cold = monitor()
    assert cold.poll_v1(lambda: pytest.fail("must obey persisted cadence"))["status"] == (
        "WAITING_FOR_NEXT_OBSERVATION"
    )
    feed.advance(2)
    result = cold.poll_v1(open_ports)
    assert result["observed_at"] > initial["observed_at"]
    order = result["account_observation"]["execution_reconciliation"][
        identity.portfolio_reservation_id
    ]
    assert order["identity_digest"] == identity.identity_digest()
    assert order["reservation_released"] is False
    assert order["original_submit_barrier"]["permit_id"] == identity.send_permit_id
    assert order["original_submit_barrier"]["resubmit_allowed"] is False
    if fault == "canceled-after-partial":
        assert order["confirmed_filled_qty"] == "1"
    else:
        assert order["matched"] is False
    assert send["simulated_transport"].post_count == 1
    assert kill_switch_should_block_trading(explicit_active=False)


def test_kill_while_collecting_inventory_rejects_account_evidence(seeded, monkeypatch):
    old_host, bound, _, _ = seeded
    old_host.close()
    feed, _ = _mark_feed(old_host, bound, monkeypatch)
    venue = _inventory_venue(old_host.account)
    fetch = venue.fetch

    def fetch_with_new_kill(path, query):
        if path == "/api/v5/trade/fills":
            feed.store.save(
                KillSwitchState.KILLED,
                killed_at=feed.now.replace(tzinfo=None),
                trigger_reason="NEW_SAFETY_INCIDENT",
            )
        return fetch(path, query)

    venue.fetch = fetch_with_new_kill
    with _open_budget_host(
        old_host, feed, venue, monkeypatch, reads=FUTURES_INVENTORY_REQUEST_COUNT
    ) as host:
        with pytest.raises(OfflinePublicFeedRecoveryError, match="STOP_CHANGED_OR_UNPROVEN"):
            capture_offline_feed_account_reconciliation_v1(
                feed.repair, host=host, bindings={"LANE_1": bound}
            )
    assert feed.store.load()["trigger_reason"] == "NEW_SAFETY_INCIDENT"
    assert kill_switch_should_block_trading(explicit_active=False)


def test_original_portfolio_writer_conflict_stops_before_get(seeded, monkeypatch):
    old_host, bound, _, _ = seeded
    old_host.close()
    feed, _ = _mark_feed(old_host, bound, monkeypatch)
    venue = _inventory_venue(old_host.account)
    writer = ProductivePortfolioSingleWriterV1(
        state_root=old_host.root / "reconciliation", session_id="previous-writer"
    )
    writer.acquire(now_unix=feed.now.timestamp())
    try:
        with _open_budget_host(
            old_host, feed, venue, monkeypatch, reads=FUTURES_INVENTORY_REQUEST_COUNT
        ) as host:
            with pytest.raises(ConflictingWriterError, match="CONFLICTING_WRITER"):
                capture_offline_feed_account_reconciliation_v1(
                    feed.repair, host=host, bindings={"LANE_1": bound}
                )
        writer.assert_held()
        assert venue.requests == []
        assert kill_switch_should_block_trading(explicit_active=False)
    finally:
        writer.release()
