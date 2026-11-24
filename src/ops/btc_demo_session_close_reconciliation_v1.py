"""Authenticated bounded-close settlement in the original TESTNET writer.

The prior net-opening fee is excluded exactly once. No marked price return,
POST acknowledgement or local flat label can release the original hold.
"""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import json
from urllib.parse import urlencode, urlsplit

from src.ops.btc_demo_session_close_v1 import _need, close_root_v1, _position_parent_v1
from src.ops.btc_demo_session_control_v1 import (
    BoundedDemoSessionRegistrationV1,
    utc_v1,
    validate_session_control_v1,
)
from src.ops.execution_reconciliation_get_provenance_v1 import (
    AuthenticatedReconciliationGetV1,
    resolve_reconciliation_query_options_v1,
)
from src.ops.execution_reconciliation_proof_store_v1 import _decode_get, _RecordedReconciliationGets
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    require_same_k1_venue_credential_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
    POST_OWNER_GO,
    SHARED_POST_OWNER_CLAIM_FIELD,
    load_durable_post_owner_go_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_l10_close_reconciliation_v1 import (
    _utc_ms,
    _validate_close_order_and_fills_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    load_external_effect_durable_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    EvidenceLayer,
    FullCoreExchangeReconciliationIdentityV1,
    LocalSubmitOutcome,
    OUTCOME_CONFIRMED_FILLED,
    adjudicate_full_core_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    fetch_okx_read_only_reconciliation_snapshot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    immutable_json_v1,
)
from src.ops.full_core_live_path_composition_root_v1.pretrade_acquisition_v1 import (
    acquisition_age_seconds_v1,
    utc_now_iso_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    FUTURES_FINANCIAL_BASE_GETS,
    futures_financial_pending_gets_v1,
    K1AccountObservationSourceV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    ReleaseReasonV1,
    ReservationStateV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    PortfolioBudgetHostV1,
    collect_host_account_observation_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.live_l10_close_booking_v1 import (
    venue_decimal_v1 as dec,
)


def _original_send_v1(owner, control):
    registration = BoundedDemoSessionRegistrationV1(**control["registration"])
    root = close_root_v1(owner, registration)
    envelope = FinalOrderEnvelopeV1(**control["close_plan"]["envelope"])
    send = load_external_effect_durable_consume_v1(store_root=root)
    mandate = load_durable_post_owner_go_consume_v1(store_root=root)
    record = send["record"] or {}
    _need(
        send["durable_consumed"]
        and mandate["consumed"]
        and mandate["owner_go_token"] == POST_OWNER_GO
        and mandate["record"].get(SHARED_POST_OWNER_CLAIM_FIELD)
        and mandate["record"]["baseline_origin_main_sha"] == control["close_plan"]["repository_sha"]
        and record.get("authority_ref") == POST_OWNER_GO
        and (record.get("envelope_id"), record.get("envelope_digest"))
        == (envelope.envelope_id, envelope.envelope_digest)
        and record.get("transport_attempt", {}).get("phase") == "MAY_HAVE_SENT",
        "ORIGINAL_CLOSE_SOCKET_UNPROVEN",
    )
    return registration, envelope, record


def _identity_v1(owner, plan, envelope, record):
    return FullCoreExchangeReconciliationIdentityV1(
        canonical_decision_id=plan["plan_digest"],
        decision_outcome="EXIT",
        selected_side="LONG" if Decimal(plan["position"]["pos"]) > 0 else "SHORT",
        instrument_id=owner._lane_bindings["LANE_3"]["bound"]["instrument_id"],
        native_id=envelope.instrument_id,
        account_identity=owner._account_identity,
        execution_environment="TESTNET",
        venue="OKX",
        venue_plan_identity=envelope.venue_plan_clordid,
        venue_plan_digest="",
        envelope_identity=envelope.envelope_id,
        envelope_digest=envelope.envelope_digest,
        final_quantity=envelope.quantity,
        quantity_unit=envelope.quantity_unit,
        order_type=envelope.order_type,
        order_price=envelope.price,
        clordid=envelope.client_order_id,
        exchange_ord_id=None,
        owner_go=record["authority_ref"],
        atomic_consumption_key=record["permit_id"],
        submit_attempt_id=record["transport_attempt"]["claim_id"],
        local_durable_state_version="full_core_external_effect_permit_consume_v1",
    )


def _history_endpoint_v1(position, envelope):
    return "/api/v5/account/positions-history?" + urlencode(
        dict(
            instType="FUTURES",
            instId=envelope.instrument_id,
            mgnMode="cross",
            posId=position["posId"],
            limit="100",
        )
    )


def _prove_packet_v1(owner, control, packet):
    registration, envelope, record = _original_send_v1(owner, control)
    plan = control["close_plan"]
    _need(
        type(packet) is dict
        and set(packet)
        == {
            "schema",
            "plan_digest",
            "send_record_digest",
            "observed_at",
            "position_coverage",
            "gets",
            "history_get",
            "inventory_gets",
            "inventory_started",
            "inventory_completed",
        }
        and packet["schema"] == "btc_demo_bounded_session_close_originals.v1"
        and packet["plan_digest"] == plan["plan_digest"]
        and packet["send_record_digest"] == digest(record),
        "CLOSE_ORIGINAL_PACKET_MISMATCH",
    )
    decoded = [_decode_get(row) for row in packet["gets"]]
    reads = [p[0] for p in decoded]
    history_get, history = _decode_get(packet["history_get"])
    observed = utc_v1(packet["observed_at"])
    socket_ms = _utc_ms(record["transport_attempt"]["socket_boundary_at_utc"])
    prefix = "bounded-close:" + envelope.envelope_digest
    _need(
        len(reads) >= 6
        and reads[0].endpoint == "/api/v5/account/config"
        and reads[0].decision_id == prefix + ":account"
        and all(read.decision_id == prefix + ":order" for read in reads[1:])
        and history_get.decision_id == prefix + ":history"
        and socket_ms <= _utc_ms(reads[0].acquired_at.isoformat())
        and reads[0].acquired_at <= observed <= reads[1].acquired_at
        and all(a.acquired_at <= b.acquired_at for a, b in zip(reads, reads[1:]))
        and reads[-1].acquired_at <= history_get.acquired_at
        and (history_get.acquired_at - reads[0].acquired_at).total_seconds() <= 5,
        "CLOSE_GET_CLOCK_OR_SCOPE_UNPROVEN",
    )
    config = decoded[0][1]
    _need(
        config.get("code") == "0"
        and len(config["data"]) == 1
        and (
            config["data"][0].get("uid"),
            config["data"][0].get("posMode"),
            config["data"][0].get("settleCcy"),
        )
        == (owner._account_identity, "net_mode", "USDC"),
        "CLOSE_ACCOUNT_UNPROVEN",
    )
    identity = _identity_v1(owner, plan, envelope, record)
    options = resolve_reconciliation_query_options_v1(
        instrument_id=identity.instrument_id,
        native_id=identity.native_id,
        offline_l10_close=True,
    )
    coverage = packet["position_coverage"]
    _need(type(coverage) is dict, "COMPLETE_POSITION_COVERAGE_REQUIRED")
    times = iter((coverage["started_at_utc"], coverage["completed_at_utc"]))
    replay = iter(decoded[1:])
    snapshot = fetch_okx_read_only_reconciliation_snapshot_v1(
        identity=identity,
        options=options,
        read_only_get_transport=_RecordedReconciliationGets(replay),
        pretrade_decision_id=prefix + ":order",
        received_at=observed.isoformat(),
        acquisition_clock=lambda: next(times),
    )
    _need(
        next(replay, None) is None
        and snapshot.positions_observation["query_coverage"] == coverage
        and snapshot.positions_observation["response"] == {"code": "0", "data": []}
        and snapshot.pending_orders_observation["response"] == {"code": "0", "data": []},
        "CLOSE_FLAT_OR_PENDING_UNPROVEN",
    )
    _need(
        all(
            payload["data"] == []
            for read, payload in decoded
            if urlsplit(read.endpoint).path == "/api/v5/trade/orders-pending"
        ),
        "CLOSE_ORDERS_STILL_OPEN",
    )
    decision = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity,
        snapshot=snapshot,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_UNKNOWN,
    )
    _need(
        decision.outcome == OUTCOME_CONFIRMED_FILLED
        and Decimal(decision.cumulative_filled_qty) == Decimal(envelope.quantity),
        "CLOSE_FULL_FILL_REQUIRED:" + decision.outcome + ":" + ",".join(decision.reasons),
    )
    last_fill = _validate_close_order_and_fills_v1(
        snapshot=snapshot,
        decision=decision,
        envelope=envelope,
        inst_type="FUTURES",
        socket_ms=socket_ms,
        observed_ms=_utc_ms(reads[-1].acquired_at.isoformat()),
    )
    fills = {
        item.payload["tradeId"]: item.payload
        for item in snapshot.evidence_items
        if item.layer is EvidenceLayer.EXCHANGE_FILL_STATE
    }
    old = plan["position"]
    rows = history["data"]
    matches = [
        row for row in rows if (row.get("posId"), row.get("cTime")) == (old["posId"], old["cTime"])
    ]
    _need(
        history_get.endpoint == _history_endpoint_v1(old, envelope)
        and history["code"] == "0"
        and len(rows) < 100
        and len(matches) == 1,
        "CLOSE_HISTORY_EPISODE_UNPROVEN",
    )
    row = matches[0]
    quantity = Decimal(envelope.quantity)
    _need(
        (
            row.get("instId"),
            row.get("instType"),
            row.get("direction"),
            row.get("posSide"),
            row.get("mgnMode"),
            row.get("ccy"),
            row.get("type"),
        )
        == (
            envelope.instrument_id,
            "FUTURES",
            "long" if Decimal(old["pos"]) > 0 else "short",
            "net",
            "cross",
            "USDC",
            "2",
        )
        and dec(row["openMaxPos"]) == dec(row["closeTotalPos"]) == quantity
        and dec(old["uTime"])
        < socket_ms
        <= last_fill
        <= dec(row["uTime"])
        <= _utc_ms(reads[-1].acquired_at.isoformat())
        and all(fill.get("feeCcy") == "USDC" for fill in fills.values()),
        "CLOSE_HISTORY_SCOPE_UNPROVEN",
    )
    parent, prior = _position_parent_v1(owner, plan["reservation_id"])
    _need(parent == plan["episode_id"], "CLOSE_EPISODE_PARENT_CHANGED")
    with localcontext() as ctx:
        ctx.prec = 96
        pnl, fee, funding, settled, penalty, realized = (
            dec(row[key])
            for key in ("pnl", "fee", "fundingFee", "settledPnl", "liqPenalty", "realizedPnl")
        )
        _need(
            penalty == 0
            and pnl == sum(dec(f["fillPnl"]) for f in fills.values())
            and fee == dec(old["fee"]) + sum(dec(f["fee"]) for f in fills.values())
            and realized == pnl + fee + funding + settled,
            "CLOSE_NET_CASH_UNPROVEN",
        )
        excluded = Decimal(0) if prior is None else dec(prior["position_fee"])
        net = realized - excluded
    inventory = packet["inventory_gets"]
    empty_paths = futures_financial_pending_gets_v1()
    _need(
        type(inventory) is dict and set(inventory) == {*FUTURES_FINANCIAL_BASE_GETS, *empty_paths},
        "CLOSE_FULL_ACCOUNT_INVENTORY_REQUIRED",
    )
    started, completed = (
        utc_v1(packet[key]) for key in ("inventory_started", "inventory_completed")
    )
    _need(
        history_get.acquired_at <= started <= completed
        and (completed - reads[0].acquired_at).total_seconds() <= 5,
        "CLOSE_INVENTORY_CLOCK_UNPROVEN",
    )
    for endpoint, get in inventory.items():
        _need(
            get["endpoint"] == endpoint
            and get["method"] == "GET"
            and get["http_status"] == 200
            and get["get_performed"] is True
            and get["auth_header_sent"] is True
            and get["historical_reuse"] is False
            and get["venue_live_contact"] is True
            and not get["error_class"]
            and get["payload"].get("code") == "0"
            and started <= utc_v1(get["acquired_at_utc"]) <= completed,
            "CLOSE_INVENTORY_GET_UNPROVEN",
        )
        if endpoint in empty_paths or endpoint == "/api/v5/account/positions":
            _need(get["payload"]["data"] == [], "CLOSE_ACCOUNT_NOT_FLAT")
    _need(inventory["/api/v5/account/config"]["payload"] == config, "CLOSE_ACCOUNT_CHANGED")
    balances = inventory["/api/v5/account/balance"]["payload"]["data"]
    _need(
        len(balances) == 1
        and len([d for d in balances[0].get("details", []) if d.get("ccy") == "USDC"]) == 1,
        "CLOSE_USDC_BALANCE_UNPROVEN",
    )
    return dict(
        reservation_id=plan["reservation_id"],
        episode_id=parent,
        close_envelope_digest=envelope.envelope_digest,
        plan_digest=plan["plan_digest"],
        proof_digest=digest(packet),
        settlement_digest=digest(dict(history=row, fills=fills)),
        settlement_currency="USDC",
        realized_position_usdc=str(realized),
        previously_booked_opening_fee_usdc=str(excluded),
        net_result_usdc=str(net),
        confirmed_at_utc=completed.isoformat(),
    )


def validate_close_receipt_v1(owner, control):
    receipt = control["close_receipt"]
    registration = BoundedDemoSessionRegistrationV1(**control["registration"])
    packet = json.loads(
        (close_root_v1(owner, registration) / "confirmed-close-originals.json").read_bytes()
    )
    _need(_prove_packet_v1(owner, control, packet) == receipt, "CLOSE_RECEIPT_REPROOF_FAILED")
    hold = owner._by_key[owner._by_id[receipt["reservation_id"]]]
    _need(
        hold.state is ReservationStateV1.RELEASED
        and hold.terminal_reason == ReleaseReasonV1.RECONCILED_POSITION_FLAT.value,
        "CLOSE_ORIGINAL_RELEASE_UNPROVEN",
    )
    return deepcopy(receipt)


def reconcile_btc_demo_session_close_v1(*, host):
    """Read actual original GET sources, then book and release atomically."""
    from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3

    _need(
        type(host) is PortfolioBudgetHostV1
        and type(host.owner) is BtcDemoBudgetOwnerV3
        and not host.closed,
        "ORIGINAL_TESTNET_SESSION_HOST_REQUIRED",
    )
    owner = host.owner
    with owner._lock:
        control = owner._bounded_demo_session_control
        registration = validate_session_control_v1(owner, control)
        _need(
            registration is not None and control["phase"] in {"CLOSING", "CLOSED"},
            "ORIGINAL_CLOSING_SESSION_REQUIRED",
        )
        if control["phase"] == "CLOSED":
            return validate_close_receipt_v1(owner, control)
        registration, envelope, record = _original_send_v1(owner, control)
        plan = control["close_plan"]
        transport = host.reconciliation_transport
        _need(
            transport.execution_environment == "TESTNET"
            and host.account == owner._account_identity
            and host.execution_environment == "TESTNET"
            and not host.closed,
            "ORIGINAL_TESTNET_CLOSE_READER_REQUIRED",
        )
        source = AuthenticatedReconciliationGetV1(
            transport, account=host.account, clock=host.clock, retain_response_bodies=True
        )
        identity = _identity_v1(owner, plan, envelope, record)
        prefix = "bounded-close:" + envelope.envelope_digest
        source.get(
            endpoint="/api/v5/account/config",
            auth_required=True,
            pretrade_decision_id=prefix + ":account",
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )
        observed = datetime.fromtimestamp(host.clock(), timezone.utc)
        options = resolve_reconciliation_query_options_v1(
            instrument_id=identity.instrument_id,
            native_id=identity.native_id,
            productive_l10_close=True,
        )
        snapshot = fetch_okx_read_only_reconciliation_snapshot_v1(
            identity=identity,
            options=options,
            read_only_get_transport=source,
            pretrade_decision_id=prefix + ":order",
            received_at=observed.isoformat(),
            acquisition_clock=lambda: datetime.fromtimestamp(
                host.clock(), timezone.utc
            ).isoformat(),
        )
        reads, bodies = source.completed_order_read_set_v1(
            account_decision_id=prefix + ":account",
            order_decision_id=prefix + ":order",
            observed_at=observed,
            paged_l10_close=True,
        )
        before = datetime.fromtimestamp(host.clock(), timezone.utc)
        source.get(
            endpoint=_history_endpoint_v1(plan["position"], envelope),
            auth_required=True,
            pretrade_decision_id=prefix + ":history",
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )
        history_get, history_body = source.completed_close_history_get_v1(
            decision_id=prefix + ":history", after=before
        )
        account_source = host.fetch
        _need(
            type(account_source) is K1AccountObservationSourceV1
            and account_source.inventory_inst_type == "FUTURES"
            and account_source.account_inventory_guard,
            "ORIGINAL_FULL_ACCOUNT_SOURCE_REQUIRED",
        )
        require_same_k1_venue_credential_v1(source.original_handle_v1(), account_source.credential)
        observation = collect_host_account_observation_v1(
            private_rest_fetch=account_source,
            instrument_ids_by_native_id={identity.native_id: identity.instrument_id},
            session_id=host.session_id,
            clock=host.clock,
            expected_account=host.account,
        )
        financial = account_source.inspect_futures_financial_gets_v1(
            observation, read_count=account_source.transport.read_count
        )
        packet = dict(
            schema="btc_demo_bounded_session_close_originals.v1",
            plan_digest=plan["plan_digest"],
            send_record_digest=digest(record),
            observed_at=observed.isoformat(),
            position_coverage=snapshot.positions_observation["query_coverage"],
            gets=[
                {**read.to_reference_v1(), "body": body.decode("utf-8")}
                for read, body in zip(reads, bodies, strict=True)
            ],
            history_get={**history_get.to_reference_v1(), "body": history_body.decode("utf-8")},
            inventory_gets=financial.gets,
            inventory_started=datetime.fromtimestamp(
                observation.observed.event_time_unix, timezone.utc
            ).isoformat(),
            inventory_completed=datetime.fromtimestamp(
                observation.observed.wall_time_unix, timezone.utc
            ).isoformat(),
        )
        receipt = _prove_packet_v1(owner, control, packet)
        acquisition_age_seconds_v1(
            acquired_at_utc=receipt["confirmed_at_utc"], now_utc=utc_now_iso_v1()
        )
        _need(
            owner._bounded_demo_session_control == control
            and _original_send_v1(owner, control)[2] == record,
            "CLOSE_PARENT_CHANGED_DURING_GETS",
        )
        hold_key = owner._by_id[receipt["reservation_id"]]
        hold = owner._by_key[hold_key]
        _need(
            hold.state is ReservationStateV1.COMMITTED and hold.counts_against_budget,
            "ORIGINAL_CLOSE_HOLD_REQUIRED",
        )
        immutable_json_v1(
            close_root_v1(owner, registration) / "confirmed-close-originals.json", packet
        )
        owner._by_key[hold_key] = replace(
            hold,
            state=ReservationStateV1.RELEASED,
            transition_trace=(*hold.transition_trace, "RELEASED"),
            terminal_reason=ReleaseReasonV1.RECONCILED_POSITION_FLAT.value,
        )
        owner._bounded_demo_session_control = dict(
            deepcopy(control), phase="CLOSED", close_receipt=receipt
        )
        owner._admitted = False
        owner._recovery_required = True
        owner._persist_locked()
        return deepcopy(receipt)
