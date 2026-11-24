"""Original Demo net POST with ephemeral grants, fake HTTP and no real keys."""

import json
import pytest
from tests.ops.test_btc_demo_entry_submit_v1 import entry_send as entry_send
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)

from src.ops.full_core_live_path_composition_root_v1.current_productive_double_play_reversal_v1 import (
    read_retained_net_reversal_post_context_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    execute_authenticated_net_reversal_post_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    AuthenticatedEntryEpisodeRequestV1,
)
from tests.ops.test_btc_testnet_original_net_reversal_v1 import (
    reversal_inputs,
    original_testnet_entry as original_testnet_entry,
    demo_entry as demo_entry,
)
from tests.ops.test_current_productive_shared_post_owner_authority_v1 import (
    signed_post_authorization,
)
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network


@pytest.fixture
def sealed_net_order(original_testnet_entry, monkeypatch):
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        invoke_occupied_lane_governed_cycle_n1_consumer_v1,
    )
    from src.ops.gates.risk_gate import canonical_kill_switch_state_path
    from src.ops.full_core_live_path_composition_root_v1 import (
        external_effect_permit_durable_consume_v1 as durable,
    )

    world = original_testnet_entry
    pairs, kw, _ = reversal_inputs(world, monkeypatch)
    governed = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kw)[
        "LANE_3"
    ].governed_cycle_result
    assert governed.position_management_reversal is not None, governed.first_genuine_blocker
    world["host"].execution_incident_state_path = canonical_kill_switch_state_path()
    entry = AuthenticatedEntryEpisodeRequestV1(world["proof_root"], world["proof"])
    context = read_retained_net_reversal_post_context_v1(
        lane_pair=pairs["LANE_3"], recovery=world["context"], authenticated_entry=entry
    )
    monkeypatch.setattr(
        durable, "_utc_now_iso_v1", lambda: world["now"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    )
    return world, pairs["LANE_3"], entry, context


def submit_unknown(sealed_net_order, tmp_path, *, fault=None):
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        MockCurrentProductive29PIntegrityBackendV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    world, pair, entry, context = sealed_net_order
    auth, _ = signed_post_authorization(
        tmp_path,
        context.envelope,
        account=world["host"].account,
        action="DIRECT_DOUBLE_PLAY_REVERSAL",
        execution_environment="LIVE" if fault == "grant" else "TESTNET",
    )
    calls = []
    before = world["host"].owner.local_commitment_readback_v1().commitments

    class Opener:
        def open(self, request, timeout):
            assert request.get_method() == "POST"
            assert request.full_url == "https://eea.okx.com/api/v5/trade/order"
            assert request.get_header("X-simulated-trading") == "1"
            body = json.loads(request.data)
            assert body["instId"] == world["bound"].venue_native_id
            assert Decimal(body["sz"]) == abs(context.reversal.signed_order_contracts)
            retained = load_external_effect_durable_consume_v1(store_root=context.store_root_v1())
            assert retained["record"]["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
            calls.append(body)
            raise TimeoutError("offline uncertainty after socket barrier")

    from decimal import Decimal

    args = dict(
        lane_pair=pair,
        recovery=world["context"],
        authenticated_entry=entry,
        authorization=auth,
        baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        perform_real_venue_post=True,
        testnet_signing_handle=world["host"].reconciliation_transport._handle,
        opener_factory=Opener,
        execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
            origin_main=world["host"].repository_sha, head=world["host"].repository_sha, drift=""
        ),
    )
    if fault is not None:
        from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
            bind_already_held_k1_venue_auth_session_v1,
            release_k1_venue_auth_session_v1,
        )
        from tests.ops.test_current_productive_shared_post_owner_authority_v1 import _claim_rows

        other = None
        if fault == "missing-signer":
            args["testnet_signing_handle"] = None
            reason = "TESTNET_SIGNER_REQUIRED"
        elif fault in {"live-signer", "foreign-signer"}:
            other = bind_already_held_k1_venue_auth_session_v1(
                api_key="other-key" if fault == "foreign-signer" else "fixture-key",
                api_secret="fixture-secret",
                passphrase="fixture-phrase",
                execution_environment="LIVE" if fault == "live-signer" else "TESTNET",
            )
            args["testnet_signing_handle"] = other
            reason = "TESTNET_SIGNER_REQUIRED" if fault == "live-signer" else "CREDENTIAL"
        elif fault == "grant":
            reason = "GRANT_ENVIRONMENT_MISMATCH"
        else:
            raise AssertionError(fault)
        try:
            with pytest.raises((ValueError, RuntimeError), match=reason):
                execute_authenticated_net_reversal_post_v1(**args)
        finally:
            if other is not None:
                release_k1_venue_auth_session_v1(other)
        assert not calls and not _claim_rows(auth)
        assert not load_external_effect_durable_consume_v1(store_root=context.store_root_v1())[
            "present"
        ]
        assert world["host"].owner.local_commitment_readback_v1().commitments == before
        return args
    result = execute_authenticated_net_reversal_post_v1(**args)
    assert result.unknown_outcome and len(calls) == 1
    assert world["host"].owner.local_commitment_readback_v1().commitments == before
    with pytest.raises(ValueError, match="ALREADY_CONSUMED"):
        execute_authenticated_net_reversal_post_v1(**args)
    assert len(calls) == 1
    return args


def test_demo_net_timeout_consumes_one_attempt_and_keeps_original_hold(sealed_net_order, tmp_path):
    submit_unknown(sealed_net_order, tmp_path)


@pytest.mark.parametrize("fault", ["missing-signer", "live-signer", "foreign-signer", "grant"])
def test_demo_net_rejects_wrong_signer_or_environment_before_claim(
    sealed_net_order, tmp_path, fault
):
    submit_unknown(sealed_net_order, tmp_path, fault=fault)


@pytest.mark.parametrize("scenario", ["complete", "partial", "missing-page", "bad-cash"])
def test_demo_signed_settlement_books_once_and_recovers_same_hold(
    sealed_net_order, tmp_path, monkeypatch, scenario
):
    from contextlib import contextmanager
    from dataclasses import asdict
    from datetime import timedelta
    from decimal import Decimal
    from types import SimpleNamespace
    from base64 import b64encode
    import hmac
    from urllib.parse import urlsplit, parse_qs
    from tests.ops.test_authenticated_net_reversal_booking_v1 import SignedNetReversalGetFixture
    from src.ops.full_core_live_path_composition_root_v1 import (
        productive_read_only_get_transport_v1 as wire,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_double_play_reversal_v1 import (
        recover_submitted_net_reversal_v1,
    )

    world, pair, entry, context = sealed_net_order
    opening_contracts = context.reversal.current_contracts
    submit_unknown(sealed_net_order, tmp_path)
    host = world["host"]
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
        position_id="8924",
        venue_order_id="91235",
    )

    class DemoGets(SignedNetReversalGetFixture):
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
                from tests.ops.test_portfolio_budget_host_v1 import _fetch

                rows = _fetch(uid=host.account)(path, query)["data"]
            elif path.endswith("/positions"):
                rows = [self.position()]
            elif (
                path.endswith("/orders-pending")
                or path.endswith("/orders-algo-pending")
                or "/tradingBot/" in path
            ):
                rows = []
            elif path.endswith(("/orders-history", "/fills")) and "instId" not in query:
                rows = []
            else:
                rows = super().body(path, query)
            for row in rows:
                for key in ("instType",):
                    if key in row:
                        row[key] = "FUTURES"
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
            assert request.get_method() == "GET" and url.hostname == "eea.okx.com"
            assert request.get_header("X-simulated-trading") == "1"
            stamp = request.get_header("Ok-access-timestamp")
            endpoint = url.path + ("?" + url.query if url.query else "")
            expected = hmac.digest(b"fixture-secret", f"{stamp}GET{endpoint}".encode(), "sha256")
            assert request.get_header("Ok-access-sign").encode() == b64encode(expected)
            self.calls.append(endpoint)
            rows = self.body(url.path, parse_qs(url.query))
            raw = json.dumps(dict(code="0", data=rows)).encode()
            yield SimpleNamespace(status=200, url=request.full_url, read=lambda: raw)

    gets = DemoGets(data, scenario)
    monkeypatch.setattr(wire, "build_opener", lambda *_: gets)
    monkeypatch.setattr(wire, "utc_now_iso_v1", gets.clock.isoformat)
    host.clock = gets.clock.timestamp
    host.reconciliation_transport = wire.FullCoreProductiveReadOnlyGetTransportV1(
        handle=host.reconciliation_transport._handle,
        execution_environment="TESTNET",
        max_request_count=150,
    )
    args = dict(lane_pair=pair, get_budget_host=lambda: host, proof_root=world["proof_root"])
    recovered = recover_submitted_net_reversal_v1(**args)
    if scenario != "complete":
        assert recovered.reconciliation_blocker and not recovered.booking_digest
        assert host.owner.read_authenticated_net_reversal_v1(world["rid"]) is None
        assert (
            host.owner.execution_links_v1()[world["rid"]]["reconciliation"]["reservation_released"]
            is False
        )
        basis = host.owner.authenticated_reversal_slot_basis_v1(
            slot_id="LANE_3", reservation_id=world["rid"], bound=world["bound"]
        )
        assert basis.net_basis_usdc == basis.initial_usdc == 25
        return
    assert recovered.booking_digest, recovered.reconciliation_blocker
    row = host.owner.read_authenticated_net_reversal_v1(world["rid"])
    assert row["booking_digest"] == recovered.booking_digest
    # Explicit venue cash rows: 0.20 PnL - 0.01 original opening fee,
    # - 0.02 close fee - 0.02 new opening fee - 0.01 funding = 0.14 USDC.
    assert Decimal(row["settlement_native"]) == Decimal("0.14")
    assert Decimal(row["position_contracts"]) == context.reversal.target_contracts
    basis = host.owner.authenticated_reversal_slot_basis_v1(
        slot_id="LANE_3", reservation_id=world["rid"], bound=world["bound"]
    )
    assert basis.initial_usdc == 25 and basis.net_basis_usdc == Decimal("25.14")
    calls = list(gets.calls)
    assert recover_submitted_net_reversal_v1(**args) == recovered
    assert gets.calls == calls
    from src.ops.btc_demo_budget_owner_v3 import CONTRACT
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
        PortfolioBudgetHostV1,
        StandingStartupAccountObservationPortV1,
        collect_host_account_observation_v1,
    )
    from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
        K1AccountObservationSourceV1,
    )

    allocation = host.owner.risk_snapshot_v1()["state"]["slot_capital_allocation"]
    account_source = K1AccountObservationSourceV1(
        credential=host.reconciliation_transport._handle,
        transport=host.reconciliation_transport,
        expected_account_identity=host.account,
        session_id="offline-demo-net-cold-recovery",
        clock=gets.clock.timestamp,
        account_inventory_guard=True,
        inventory_inst_type="FUTURES",
    )
    host.close()
    cold = PortfolioBudgetHostV1(
        root=host.root,
        private_rest_fetch=account_source,
        repository_sha=host.repository_sha,
        session_id="offline-demo-net-cold-recovery",
        expected_account_identity=host.account,
        durable_mode="recover",
        clock=gets.clock.timestamp,
        execution_environment="TESTNET",
        entry_budget_policy=host.entry_budget_policy,
        reconciliation_transport=host.reconciliation_transport,
        execution_incident_state_path=host.execution_incident_state_path,
        testnet_owner_contract=CONTRACT,
    )
    try:
        args["get_budget_host"] = lambda: cold
        assert recover_submitted_net_reversal_v1(**args) == recovered
        assert gets.calls == calls
        assert cold.owner.risk_snapshot_v1()["state"]["slot_capital_allocation"] == allocation
        collect_host_account_observation_v1(
            private_rest_fetch=StandingStartupAccountObservationPortV1(
                fetch=cold.fetch,
                reconcile=lambda observation: cold.reconcile_standing_startup_observation_v1(
                    {"LANE_3": world["bound"]},
                    observation,
                    net_reversal_proof_root=world["proof_root"],
                ),
            ),
            instrument_ids_by_native_id={
                world["bound"].venue_native_id: world["bound"].instrument_id
            },
            session_id=cold.session_id,
            clock=cold.clock,
            expected_account=cold.account,
        )
        next_context, proofs = cold.observe_authenticated_execution_reconciliation_v1(
            {"LANE_3": world["bound"]},
            proof_root=world["proof_root"],
            deliver_authenticated_incidents=True,
        )
        assert proofs[world["rid"]].identity_digest == context.envelope.envelope_digest
        episode = next_context.bind_current_authenticated_entry_episode_v1(
            lane_id="LANE_3",
            proof_root=world["proof_root"],
            proof=proofs[world["rid"]],
            config_digest=world["episode"].binding.config_digest,
        )
        assert episode.identity.episode_id == context.envelope.envelope_digest
        assert episode.identity.position_side != world["episode"].identity.position_side
        assert episode.identity.account_scope.execution_environment == "TESTNET"
        world.update(
            host=cold,
            context=next_context,
            proof=proofs[world["rid"]],
            episode=episode,
            now=gets.clock,
        )
        pairs, kw, _ = reversal_inputs(world, monkeypatch)
        kw["cycle_id_prefix"] += "-return"
        from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
            invoke_occupied_lane_governed_cycle_n1_consumer_v1,
        )

        next_plan = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kw)[
            "LANE_3"
        ].governed_cycle_result
        assert next_plan.position_management_reversal is not None, next_plan.first_genuine_blocker
        next_reversal = next_plan.position_management_reversal
        assert next_reversal.episode.episode_id == context.envelope.envelope_digest
        assert next_reversal.current_contracts == context.reversal.target_contracts
        assert next_reversal.current_contracts * next_reversal.target_contracts < 0
        assert next_reversal.slot_capital_basis_usdc == Decimal("25.14")
        assert next_reversal.old_reservation_id == world["rid"]
        assert cold.owner.risk_snapshot_v1()["state"]["slot_capital_allocation"] == allocation
        next_entry = AuthenticatedEntryEpisodeRequestV1(world["proof_root"], proofs[world["rid"]])
        context = read_retained_net_reversal_post_context_v1(
            lane_pair=pairs["LANE_3"], recovery=next_context, authenticated_entry=next_entry
        )
        second_root = tmp_path / "return-authority"
        second_root.mkdir()
        submit_unknown((world, pairs["LANE_3"], next_entry, context), second_root)
        second_data = dict(
            data,
            observed_at=(world["now"] + timedelta(seconds=1)).isoformat(),
            socket_ms=int(world["now"].timestamp() * 1000),
            envelope=asdict(context.envelope),
            closing_size=str(abs(context.reversal.current_contracts)),
            old_position_id=row["position_id"],
            old_created_ms=row["position_created_ms"],
            old_position_fee=row["position_fee"],
            position_id="8925",
            venue_order_id="91236",
            closing_trade_id="125",
            opening_trade_id="126",
        )
        gets = DemoGets(second_data, "complete")
        monkeypatch.setattr(wire, "utc_now_iso_v1", gets.clock.isoformat)
        cold.clock = gets.clock.timestamp
        cold.reconciliation_transport = wire.FullCoreProductiveReadOnlyGetTransportV1(
            handle=cold.reconciliation_transport._handle,
            execution_environment="TESTNET",
            max_request_count=30,
        )
        returned = recover_submitted_net_reversal_v1(**args)
        assert returned.booking_digest, returned.reconciliation_blocker
        latest = cold.owner.read_authenticated_net_reversal_v1(world["rid"])
        # The preceding opening fee was already booked; do not charge it twice.
        assert Decimal(latest["settlement_native"]) == Decimal("0.15")
        assert Decimal(latest["position_contracts"]) == next_reversal.target_contracts
        assert Decimal(latest["position_contracts"]) * opening_contracts > 0
        basis = cold.owner.authenticated_reversal_slot_basis_v1(
            slot_id="LANE_3", reservation_id=world["rid"], bound=world["bound"]
        )
        assert basis.initial_usdc == 25 and basis.net_basis_usdc == Decimal("25.29")
        series = cold.owner.risk_snapshot_v1()["state"]["live_net_reversal_bookings"][world["rid"]]
        assert len(series) == 2
        assert latest["previous_episode_id"] == row["envelope_digest"]
        assert cold.owner.risk_snapshot_v1()["state"]["slot_capital_allocation"] == allocation
        calls = list(gets.calls)
        assert recover_submitted_net_reversal_v1(**args) == returned
        assert gets.calls == calls
    finally:
        cold.close()
        account_source.close()
