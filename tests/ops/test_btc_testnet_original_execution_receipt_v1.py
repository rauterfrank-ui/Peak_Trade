"""Original TESTNET journal -> signed GET fixture -> original episode; no POST."""

from base64 import b64encode
from contextlib import contextmanager
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
import hmac
import json
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest

from src.ops.btc_demo_budget_owner_v3 import CONTRACT, BtcDemoBudgetOwnerV3
from src.ops.full_core_live_path_composition_root_v1 import (
    productive_read_only_get_transport_v1 as wire,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    bind_already_held_k1_venue_auth_session_v1,
    release_k1_venue_auth_session_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    K1AccountObservationSourceV1,
    FUTURES_INVENTORY_REQUEST_COUNT,
)
from src.ops.exit_policy_producer_binding_v1.constants_v1 import FROZEN_PROFIT_PROTECTION_DISTANCE
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    layer_c_derived_exit_policy_adverse_config_digest_v1,
)
from tests.ops.test_btc_demo_entry_reservation_v1 import demo_entry as demo_entry
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _permit,
)
from tests.ops.test_portfolio_budget_host_v1 import _fetch


def test_original_host_recovers_v3_then_binds_a_testnet_entry_episode(
    demo_entry, tmp_path, monkeypatch
):
    demo, entry, reads, movement, instant, payloads = demo_entry
    owner, bound = demo.budget.owner, demo.budget.bound
    result, _ = demo.reserve_testnet_entry_v1(
        entry=entry, reads=reads, movement_input=movement, clock=instant.timestamp
    )
    rid = result.reservation.reservation_id
    envelope, plan_context = demo.plan_testnet_entry_v1(
        entry=entry,
        reservation_id=rid,
        expected_revision=demo.budget.budget_revision_ref_v1(),
        clock=instant.timestamp,
    )
    # This local synthetic permit exercises the original writer only. No
    # transport attempt or durable send-permit consume is created by this test.
    identity = owner.begin_execution_submit_v2(rid, envelope, plan_context, _permit(envelope))
    assert identity.execution_environment == "TESTNET"
    policy = owner.entry_budget_policy_v1()
    root = owner._store.root.parent
    held = owner.local_commitment_readback_v1().commitments
    owner.close()
    now = instant + timedelta(seconds=1)
    stamp = int(now.timestamp() * 1000)
    long = envelope.side == "buy"
    position = dict(
        instId=bound.venue_native_id,
        instType="FUTURES",
        posSide="net",
        mgnMode="cross",
        pos=envelope.quantity if long else "-" + envelope.quantity,
        avgPx="60000",
        tradeId="22",
        posId="8923",
        cTime=str(stamp - 200),
        uTime=str(stamp - 100),
        ccy="USDC",
        fee="-0.01",
    )
    order = dict(
        instId=bound.venue_native_id,
        instType="FUTURES",
        clOrdId=envelope.client_order_id,
        ordId="91234",
        sz=envelope.quantity,
        accFillSz=envelope.quantity,
        state="filled",
    )
    calls = []

    class Endpoint:
        @contextmanager
        def open(self, request, timeout):
            url = urlsplit(request.full_url)
            assert request.get_method() == "GET" and request.data is None
            assert (
                url.hostname == "eea.okx.com" and request.get_header("X-simulated-trading") == "1"
            )
            timestamp = request.get_header("Ok-access-timestamp")
            endpoint = url.path + ("?" + url.query if url.query else "")
            assert request.get_header("Ok-access-sign").encode() == b64encode(
                hmac.digest(b"fixture-secret", f"{timestamp}GET{endpoint}".encode(), "sha256")
            )
            calls.append(endpoint)
            if url.path.endswith("/config"):
                rows = payloads["account"]["data"]
            elif url.path.endswith("/balance"):
                rows = _fetch(uid=demo.budget.account)("/api/v5/account/balance", {})["data"]
            elif url.path.endswith("/positions"):
                rows = [position]
            elif url.path.endswith("/orders-pending"):
                rows = []
            elif url.path.endswith("/fills"):
                rows = [
                    {
                        **order,
                        "tradeId": "22",
                        "fillSz": envelope.quantity,
                        "fillPx": "60000",
                        "side": envelope.side,
                        "posSide": "net",
                        "fillTime": str(stamp - 200),
                        "fee": "-0.01",
                        "feeCcy": "USDC",
                    }
                ]
            elif url.path.endswith(("/orders-history", "/order")):
                rows = [order]
            elif url.path.endswith("/orders-algo-pending") or "/tradingBot/" in url.path:
                rows = []
            else:
                raise AssertionError(url.path)
            body = json.dumps(dict(code="0", data=rows)).encode()
            yield SimpleNamespace(url=request.full_url, status=200, read=lambda: body)

    handle = bind_already_held_k1_venue_auth_session_v1(
        api_key="fixture-key",
        api_secret="fixture-secret",
        passphrase="fixture-phrase",
        execution_environment="TESTNET",
    )
    monkeypatch.setattr(wire, "build_opener", lambda *_: Endpoint())
    monkeypatch.setattr(wire, "utc_now_iso_v1", now.isoformat)
    transport = wire.FullCoreProductiveReadOnlyGetTransportV1(
        handle=handle,
        execution_environment="TESTNET",
        max_request_count=40,
    )
    account_source = K1AccountObservationSourceV1(
        credential=handle,
        transport=transport,
        expected_account_identity=demo.budget.account,
        session_id="offline-testnet-original-recovery",
        clock=now.timestamp,
        account_inventory_guard=True,
        inventory_inst_type="FUTURES",
    )
    host = PortfolioBudgetHostV1(
        root=root,
        private_rest_fetch=account_source,
        repository_sha=demo.repository_sha,
        session_id="offline-testnet-original-recovery",
        expected_account_identity=demo.budget.account,
        durable_mode="recover",
        clock=now.timestamp,
        execution_environment="TESTNET",
        entry_budget_policy=policy,
        reconciliation_transport=transport,
        testnet_owner_contract=CONTRACT,
    )
    proof_root = tmp_path / "private-proofs"
    proof_root.mkdir(mode=0o700)
    try:
        context, proofs = host.observe_authenticated_execution_reconciliation_v1(
            {"LANE_3": bound}, proof_root=proof_root
        )
        assert type(host.owner) is BtcDemoBudgetOwnerV3
        assert context.execution_reconciliation[rid]["matched"] is True
        assert context.execution_reconciliation[rid]["reservation_released"] is False
        assert host.owner.local_commitment_readback_v1().commitments == tuple(
            replace(row, reconciliation_outcome="CONFIRMED_FILLED", reconciliation_matched=True)
            for row in held
        )
        basis = host.owner.authenticated_reversal_slot_basis_v1(
            slot_id="LANE_3", reservation_id=rid, bound=bound
        )
        assert basis.initial_usdc == basis.net_basis_usdc == Decimal(25)
        assert (
            host.owner.live_reversal_slot_basis_v1(
                slot_id="LANE_3", reservation_id=rid, bound=bound
            )
            is None
        )
        episode = context.bind_current_authenticated_entry_episode_v1(
            lane_id="LANE_3",
            proof_root=proof_root,
            proof=proofs[rid],
            config_digest=layer_c_derived_exit_policy_adverse_config_digest_v1(
                profit_protection_distance=FROZEN_PROFIT_PROTECTION_DISTANCE
            ),
        )
        assert episode.identity.account_scope.execution_environment == "TESTNET"
        assert episode.identity.position_side == ("long" if long else "short")
        assert episode.identity.episode_id == identity.identity_digest()
        assert len(calls) == FUTURES_INVENTORY_REQUEST_COUNT + 6
        assert host.owner.budget_state_v1().recovery_required
    finally:
        host.close()
        account_source.close()
        release_k1_venue_auth_session_v1(handle)
