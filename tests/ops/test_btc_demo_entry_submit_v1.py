"""Original Slot-3 entry dispatch with signed fake HTTP and ephemeral authority."""

from base64 import b64encode
from contextlib import contextmanager
from dataclasses import asdict, replace
import hmac
import json
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest

from src.ops.btc_demo_entry_submit_v1 import (
    BtcDemoEntryPostContextV1,
    execute_btc_demo_entry_post_v1,
    capture_btc_demo_entry_quantity_v1,
    btc_demo_entry_reader_v1,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    productive_read_only_get_transport_v1 as wire,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    bind_already_held_k1_venue_auth_session_v1,
    release_k1_venue_auth_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_pending_observation_v1 import (
    capture_current_post_pending_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_venue_quantity_v1 import (
    capture_current_post_venue_quantity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    load_external_effect_durable_consume_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    K1AccountObservationSourceV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    collect_host_account_observation_v1,
)
from tests.ops.test_btc_demo_entry_reservation_v1 import demo_entry as demo_entry
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)
from tests.ops.test_current_productive_shared_post_owner_authority_v1 import (
    signed_post_authorization,
    _claim_rows,
)
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    MockCurrentProductive29PIntegrityBackendV1,
)


@pytest.fixture
def entry_send(demo_entry, monkeypatch, tmp_path, request):
    host, entry, reads, movement, instant, payloads = demo_entry
    if getattr(request, "param", None) == "bounded-session":
        from src.ops.btc_demo_session_control_v1 import BoundedDemoSessionRegistrationV1
        from src.ops.full_core_live_path_composition_root_v1 import pretrade_acquisition_v1

        monkeypatch.setattr(pretrade_acquisition_v1, "utc_now_iso_v1", instant.isoformat)
        host.budget.owner.register_bounded_demo_session_v1(
            BoundedDemoSessionRegistrationV1(
                session_id=host.writer_session_id,
                account_identity=host.budget.account,
                instrument_id=host.budget.bound.instrument_id,
                started_at_utc=instant.isoformat(),
                operator_start_digest="a" * 64,
            ),
            expected_head=host.budget.budget_revision_ref_v1()[1],
            now_utc=instant.isoformat(),
        )
    result, _ = host.reserve_testnet_entry_v1(
        entry=entry, reads=reads, movement_input=movement, clock=instant.timestamp
    )
    rid = result.reservation.reservation_id
    envelope, plan = host.plan_testnet_entry_v1(
        entry=entry,
        reservation_id=rid,
        expected_revision=host.budget.budget_revision_ref_v1(),
        clock=instant.timestamp,
    )
    from src.ops.full_core_live_path_composition_root_v1 import (
        pretrade_acquisition_v1,
        current_productive_n1_venue_quantity_limit_admission_v1 as quantity_owner,
    )
    from tests.ops.test_portfolio_budget_host_v1 import _fetch

    monkeypatch.setattr(pretrade_acquisition_v1, "utc_now_iso_v1", instant.isoformat)
    monkeypatch.setattr(quantity_owner, "utc_now_iso_v1", instant.isoformat)
    monkeypatch.setattr(wire, "utc_now_iso_v1", instant.isoformat)
    calls = []

    class Gets:
        @contextmanager
        def open(self, request, timeout):
            url = urlsplit(request.full_url)
            assert request.get_method() == "GET" and url.hostname == "eea.okx.com"
            assert request.get_header("X-simulated-trading") == "1"
            if url.path.endswith("/config"):
                rows = payloads["account"]["data"]
            elif url.path.endswith("/balance"):
                rows = _fetch(uid=host.budget.account)(url.path, {})["data"]
            elif url.path.endswith("/instruments"):
                rows = [
                    dict(
                        payloads["instruments"]["data"][0],
                        upcChg=[],
                        maxMktSz="1000",
                        maxLmtSz="1000",
                    )
                ]
            elif url.path.endswith("/max-size"):
                rows = [dict(instId=envelope.instrument_id, maxBuy="1000", maxSell="1000")]
            else:
                rows = []
            yield SimpleNamespace(
                url=request.full_url,
                status=200,
                read=lambda: json.dumps(dict(code="0", data=rows)).encode(),
            )

    handle = bind_already_held_k1_venue_auth_session_v1(
        api_key="fixture-key",
        api_secret="fixture-secret",
        passphrase="fixture-phrase",
        execution_environment="TESTNET",
    )
    monkeypatch.setattr(wire, "build_opener", lambda *_: Gets())
    transport = wire.FullCoreProductiveReadOnlyGetTransportV1(
        handle=handle, execution_environment="TESTNET", max_request_count=100
    )
    source = K1AccountObservationSourceV1(
        credential=handle,
        transport=transport,
        expected_account_identity=host.budget.account,
        session_id=host.writer_session_id,
        clock=instant.timestamp,
        account_inventory_guard=True,
        inventory_inst_type="FUTURES",
    )
    try:
        collect_host_account_observation_v1(
            private_rest_fetch=source,
            instrument_ids_by_native_id={envelope.instrument_id: host.budget.bound.instrument_id},
            session_id=host.writer_session_id,
            clock=instant.timestamp,
            expected_account=host.budget.account,
        )
        pending = capture_current_post_pending_v1(
            envelope=envelope, source=source, execution_environment="TESTNET"
        )
        context = BtcDemoEntryPostContextV1(host, entry, rid, envelope, plan, pending)
        from src.ops import btc_demo_lane3_v2 as demo

        monkeypatch.setattr(demo, "build_opener", lambda *_: Gets())
        quantity_reads = btc_demo_entry_reader_v1(signing_handle=handle)
        quantity = capture_btc_demo_entry_quantity_v1(context=context, reads=quantity_reads)
        authority_root = tmp_path / "first-entry-authority"
        authority_root.mkdir()
        auth, key = signed_post_authorization(
            authority_root,
            envelope,
            account=host.budget.account,
            action="ENTER",
            execution_environment="TESTNET",
        )
        args = dict(
            context=context,
            authorization=auth,
            signing_handle=handle,
            quantity_context=quantity,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            perform_real_venue_post=True,
            execution_integrity_backend=MockCurrentProductive29PIntegrityBackendV1(
                origin_main=host.repository_sha, head=host.repository_sha, drift=""
            ),
        )
        yield SimpleNamespace(
            host=host,
            entry=entry,
            rid=rid,
            envelope=envelope,
            context=context,
            auth=auth,
            key=key,
            args=args,
            calls=calls,
            instant=instant,
            payloads=payloads,
            movement=movement,
        )
    finally:
        source.close()
        release_k1_venue_auth_session_v1(handle)


def send_btc_demo_entry_fixture_v1(case, outcome):
    before = case.host.budget.owner.local_commitment_readback_v1()

    class Post:
        @contextmanager
        def open(self, request, timeout):
            assert request.full_url == "https://eea.okx.com/api/v5/trade/order"
            assert (
                request.get_method() == "POST" and request.get_header("X-simulated-trading") == "1"
            )
            stamp = request.get_header("Ok-access-timestamp")
            signed = hmac.digest(
                b"fixture-secret",
                f"{stamp}POST/api/v5/trade/order".encode() + request.data,
                "sha256",
            )
            assert request.get_header("Ok-access-sign").encode() == b64encode(signed)
            record = load_external_effect_durable_consume_v1(
                store_root=case.context.store_root_v1()
            )["record"]
            assert record["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
            assert record["execution_identity"]["execution_environment"] == "TESTNET"
            assert _claim_rows(case.auth) == [(case.auth.grant.grant_id, 1)]
            body = json.loads(request.data)
            assert body["sz"] == case.envelope.quantity and body["side"] == case.envelope.side
            case.calls.append(body)
            if outcome == "timeout":
                raise TimeoutError("offline uncertainty only")
            raw = json.dumps(
                dict(
                    code="0",
                    data=[dict(ordId="91234", clOrdId=body["clOrdId"], sCode="0", sMsg="")],
                )
            ).encode()
            yield SimpleNamespace(url=request.full_url, status=200, read=lambda: raw)

    result = execute_btc_demo_entry_post_v1(**case.args, opener_factory=Post)
    assert result.durable_consumed and result.http_post_attempts == 1
    assert result.external_effect_count == 0
    assert result.unknown_outcome is (outcome == "timeout")
    owner = case.host.budget.owner
    link = owner.execution_links_v1()[case.rid]
    assert link["reconciliation"] is None
    assert (
        owner.local_commitment_readback_v1().active_commitment_sum == before.active_commitment_sum
    )
    assert owner.slot_capital_basis_v1("LANE_3").initial_usdc == 25
    assert len(case.calls) == 1
    return result


@pytest.mark.parametrize("outcome", ["ack", "timeout"])
def test_original_demo_entry_crosses_both_barriers_once_without_booking_a_fill(entry_send, outcome):
    case = entry_send
    send_btc_demo_entry_fixture_v1(case, outcome)
    with pytest.raises(ValueError, match="ALREADY_CONSUMED"):
        execute_btc_demo_entry_post_v1(
            **case.args, opener_factory=lambda: pytest.fail("replay reached HTTP")
        )
    assert len(case.calls) == 1


@pytest.mark.parametrize(
    "fault",
    [
        "no-send",
        "live-signer",
        "foreign-signer",
        "live-grant",
        "wrong-action",
        "revoked",
        "stale-inventory",
        "quantity-source",
        "quantity-decision",
        "cost-source",
    ],
)
def test_demo_entry_denies_before_grant_or_budget_submit(entry_send, fault):
    case = entry_send
    args = dict(case.args)
    other = None
    if fault == "no-send":
        args["perform_real_venue_post"] = False
    elif fault in {"live-signer", "foreign-signer"}:
        other = bind_already_held_k1_venue_auth_session_v1(
            api_key="fixture-key" if fault == "live-signer" else "foreign-key",
            api_secret="fixture-secret",
            passphrase="fixture-phrase",
            execution_environment="LIVE" if fault == "live-signer" else "TESTNET",
        )
        args["signing_handle"] = other
    elif fault in {"live-grant", "wrong-action"}:
        grant = replace(
            case.auth.grant,
            **({"environment": "LIVE"} if fault == "live-grant" else {"action": "L10_CLOSE"}),
            signature=b"",
        )
        args["authorization"] = replace(
            case.auth,
            grant=replace(grant, signature=case.key.sign(grant.signing_bytes_v1()).signature),
        )
    elif fault == "revoked":
        from tests.ops.test_current_productive_shared_post_owner_authority_v1 import revoke

        revoke(case.auth, case.key)
    elif fault == "quantity-decision":
        args["quantity_context"] = replace(
            args["quantity_context"], acquisition_decision_id="foreign-decision"
        )
    elif fault == "quantity-source":
        path = case.context.store_root_v1() / "quantity-sources.json"
        payload = json.loads(path.read_bytes())
        payload["original_bodies_hex"]["max_size"] = "00"
        path.write_text(json.dumps(payload))
    elif fault == "cost-source":
        from src.ops import btc_demo_lane3_v2 as demo

        path = next(
            (demo._demo_lane_root(case.host.budget.root) / "entry-reservation-sources").glob(
                "*.json"
            )
        )
        payload = json.loads(path.read_bytes())
        payload["native_price_currency"] = "USDC"
        path.write_text(json.dumps(payload))
    else:
        case.context.pending_context.source.clock = lambda: case.instant.timestamp() + 6
    before = case.host.budget.budget_revision_ref_v1()
    try:
        with pytest.raises((ValueError, RuntimeError)):
            execute_btc_demo_entry_post_v1(
                **args, opener_factory=lambda: pytest.fail("denied request reached HTTP")
            )
    finally:
        if other:
            release_k1_venue_auth_session_v1(other)
    assert not _claim_rows(case.auth)
    assert not load_external_effect_durable_consume_v1(store_root=case.context.store_root_v1())[
        "present"
    ]
    assert case.host.budget.budget_revision_ref_v1() == before


@pytest.mark.parametrize(
    "fault", ["revoke", "quantity-source", "expired-inventory", "quantity-context"]
)
def test_demo_entry_rechecks_before_socket_and_retains_hold_after_late_denial(
    entry_send, fault, monkeypatch
):
    case = entry_send
    before = case.host.budget.owner.local_commitment_readback_v1().active_commitment_sum
    if fault == "quantity-context":
        from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
            FullCoreProductiveHttpTradeOrderTransportV1,
        )

        original = FullCoreProductiveHttpTradeOrderTransportV1.__init__

        def changed(self, **kwargs):
            original(self, **kwargs)
            self._post_quantity_context = replace(self._post_quantity_context)

        monkeypatch.setattr(FullCoreProductiveHttpTradeOrderTransportV1, "__init__", changed)

    class NeverOpen:
        def open(self, *args, **kwargs):
            pytest.fail("late denial reached socket")

    def late_change():
        if fault == "revoke":
            from tests.ops.test_current_productive_shared_post_owner_authority_v1 import revoke

            revoke(case.auth, case.key)
        elif fault == "quantity-source":
            path = case.context.store_root_v1() / "quantity-sources.json"
            payload = json.loads(path.read_bytes())
            payload["original_bodies_hex"]["max_size"] = "00"
            path.write_text(json.dumps(payload))
        elif fault == "expired-inventory":
            case.context.pending_context.source.clock = lambda: case.instant.timestamp() + 6
        return NeverOpen()

    with pytest.raises((ValueError, RuntimeError)):
        execute_btc_demo_entry_post_v1(**case.args, opener_factory=late_change)
    record = load_external_effect_durable_consume_v1(store_root=case.context.store_root_v1())[
        "record"
    ]
    assert record["transport_attempt"]["phase"] == "ABORTED"
    assert _claim_rows(case.auth) == [(case.auth.grant.grant_id, 0)]
    assert case.host.budget.owner.local_commitment_readback_v1().active_commitment_sum == before
    assert case.host.budget.owner.execution_links_v1()[case.rid]["reconciliation"] is None


def test_live_join_does_not_admit_demo_plan_without_explicit_demo_context(entry_send):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
        POST_OWNER_GO,
        attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1,
    )

    case = entry_send
    before = case.host.budget.budget_revision_ref_v1()
    with pytest.raises(RuntimeError, match="ENVIRONMENT_MISMATCH"):
        attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
            envelope=case.envelope,
            post_owner_go=POST_OWNER_GO,
            store_root=case.context.store_root_v1(),
            k1_backend=None,
            portfolio_budget_owner=case.host.budget.owner,
            portfolio_reservation_id=case.rid,
            execution_plan_context=case.context.plan_context,
        )
    assert case.host.budget.budget_revision_ref_v1() == before
    assert not _claim_rows(case.auth)
