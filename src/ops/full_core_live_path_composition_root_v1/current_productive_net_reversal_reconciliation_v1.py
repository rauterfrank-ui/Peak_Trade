"""Authenticate the original net fill and the occupied position it created."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from urllib.parse import urlencode, urlsplit

from src.ops.execution_reconciliation_get_provenance_v1 import (
    AuthenticatedReconciliationGetV1,
    ENDPOINT_ACCOUNT_POSITIONS_HISTORY,
    resolve_reconciliation_query_options_v1,
)
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import canonical_digest_v1
from src.ops.portfolio_capital_reservation_budget_v1.live_l10_close_booking_v1 import (
    venue_decimal_v1,
)
from .fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from .full_core_exchange_reconciliation_v1 import (
    EvidenceLayer,
    LocalSubmitOutcome,
    OUTCOME_CONFIRMED_FILLED,
    FullCoreExchangeReconciliationIdentityV1,
    adjudicate_full_core_exchange_reconciliation_v1,
)
from .full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    ENDPOINT_ORDERS_PENDING,
    fetch_okx_read_only_reconciliation_snapshot_v1,
)
from .current_productive_l10_close_reconciliation_v1 import _utc_ms


class NetReversalReconciliationError(ValueError):
    """The exact same-slot reversal is still unresolved."""


def _need(condition, reason):
    if not condition:
        raise NetReversalReconciliationError(reason)


@dataclass(frozen=True)
class AuthenticatedNetReversalFillV1:
    venue_order_id: str
    currency: str
    position_id: str
    position_created_ms: str
    position_updated_ms: str
    signed_position_contracts: str
    average_entry_price: str
    last_trade_id: str
    opening_fill_ms: str
    position_fee: Decimal
    old_position_pnl: Decimal
    order_fee: Decimal
    evidence_digest: str


def collect_authenticated_net_reversal_fill_v1(*, transport, clock, plan, envelope, record):
    """Use the actual K1 GET producer with the retained order and transport barrier."""
    account = plan.episode.account_scope.account_identity
    source = AuthenticatedReconciliationGetV1(
        transport,
        account=account,
        clock=clock,
        retain_response_bodies=True,
    )
    identity = FullCoreExchangeReconciliationIdentityV1(
        canonical_decision_id=plan.digest_v1(),
        decision_outcome=envelope.path_kind,
        selected_side="LONG" if plan.target_contracts > 0 else "SHORT",
        instrument_id=plan.episode.instrument_id,
        native_id=plan.episode.venue_native_id,
        account_identity=account,
        execution_environment=plan.episode.account_scope.execution_environment,
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
    prefix = f"net-reversal:{envelope.envelope_digest}"
    config_id, order_id = prefix + ":account", prefix + ":order"
    source.get(
        endpoint=ENDPOINT_ACCOUNT_CONFIG,
        auth_required=True,
        pretrade_decision_id=config_id,
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )

    def now():
        return datetime.fromtimestamp(clock(), timezone.utc)

    observed = now()
    options = resolve_reconciliation_query_options_v1(
        instrument_id=identity.instrument_id,
        native_id=identity.native_id,
        productive_l10_close=True,
    )
    snapshot = fetch_okx_read_only_reconciliation_snapshot_v1(
        identity=identity,
        read_only_get_transport=source,
        pretrade_decision_id=order_id,
        options=options,
        received_at=observed.isoformat(),
        acquisition_clock=lambda: now().isoformat(),
    )
    reads, bodies = source.completed_order_read_set_v1(
        account_decision_id=config_id,
        order_decision_id=order_id,
        observed_at=observed,
        paged_l10_close=True,
    )
    socket_ms = _utc_ms(record["transport_attempt"]["socket_boundary_at_utc"])
    _need(
        source.account_position_mode == "net_mode"
        and socket_ms <= _utc_ms(reads[0].acquired_at.isoformat()),
        "NET_REVERSAL_ACCOUNT_MODE_OR_CLOCK_UNPROVEN",
    )
    decision = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity,
        snapshot=snapshot,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_UNKNOWN,
    )
    _need(
        decision.outcome == OUTCOME_CONFIRMED_FILLED and decision.venue_ord_id,
        "NET_REVERSAL_FULL_FILL_REQUIRED:" + ",".join(decision.reasons or (decision.outcome,)),
    )
    fill = _prove_net_fill_v1(
        reads=reads,
        bodies=bodies,
        snapshot=snapshot,
        plan=plan,
        envelope=envelope,
        inst_type=options.inst_type,
        socket_ms=socket_ms,
        venue_order_id=decision.venue_ord_id,
    )
    return source, fill, reads, bodies


def _prove_net_fill_v1(
    *, reads, bodies, snapshot, plan, envelope, inst_type, socket_ms, venue_order_id
):
    import json

    _need(
        any(urlsplit(read.endpoint).path == ENDPOINT_ORDERS_PENDING for read in reads)
        and all(
            json.loads(body)["data"] == []
            for read, body in zip(reads, bodies, strict=True)
            if urlsplit(read.endpoint).path == ENDPOINT_ORDERS_PENDING
        ),
        "NET_REVERSAL_OPEN_ORDERS",
    )
    exact = [
        item.payload for item in snapshot.evidence_items if item.source == "exact-order-lookup"
    ]
    _need(len(exact) == 1, "NET_REVERSAL_EXACT_ORDER_UNPROVEN")
    order = exact[0]
    expected = {
        "instId": envelope.instrument_id,
        "instType": inst_type,
        "clOrdId": envelope.client_order_id,
        "ordId": venue_order_id,
        "side": envelope.side,
        "posSide": "net",
    }
    order_time = venue_decimal_v1(order["uTime"])
    size = venue_decimal_v1(envelope.quantity)
    _need(
        all(order.get(key) == value for key, value in expected.items())
        and order.get("ordType") == envelope.order_type
        and order.get("tdMode") == envelope.td_mode
        and order.get("reduceOnly") in (False, "false")
        and venue_decimal_v1(order["sz"]) == venue_decimal_v1(order["accFillSz"]) == size
        and socket_ms <= order_time <= _utc_ms(reads[-1].acquired_at.isoformat()),
        "NET_REVERSAL_EXACT_ORDER_MISMATCH",
    )
    fills = {}
    for item in snapshot.evidence_items:
        if item.layer is not EvidenceLayer.EXCHANGE_FILL_STATE:
            continue
        fill = item.payload
        trade = fill["tradeId"]
        _need(
            type(trade) is str
            and trade.isascii()
            and trade.isdecimal()
            and int(trade) > 0
            and all(fill.get(key) == value for key, value in expected.items())
            and fills.setdefault(trade, fill) == fill
            and socket_ms <= venue_decimal_v1(fill["fillTime"]) <= order_time
            and venue_decimal_v1(fill["fillPx"]) > 0
            and venue_decimal_v1(fill["fillSz"]) > 0,
            "NET_REVERSAL_FILL_IDENTITY_OR_TIME_UNPROVEN",
        )

    positions = snapshot.positions_observation
    rows = positions["response"]["data"]
    _need(positions.get("query_coverage") and len(rows) == 1, "NET_REVERSAL_POSITION_UNPROVEN")
    position = rows[0]
    position_read = next(
        read for read in reads if urlsplit(read.endpoint).path == "/api/v5/account/positions"
    )
    position_time = venue_decimal_v1(position["uTime"])
    target = venue_decimal_v1(position["pos"])
    currency = position["ccy"]
    _need(
        (position["instId"], position["instType"], position["posSide"], position["mgnMode"])
        == (envelope.instrument_id, inst_type, "net", envelope.td_mode)
        and venue_decimal_v1(position["avgPx"]) > 0
        and currency in {"USDC", "USDT"}
        and type(position["posId"]) is str
        and position["posId"].isascii()
        and position["posId"].isdecimal()
        and int(position["posId"]) > 0,
        "NET_REVERSAL_POSITION_BINDING_UNPROVEN",
    )

    with localcontext() as ctx:
        ctx.prec = 96
        quantity = Decimal(0)
        opening_time = None
        ordered = sorted(
            fills.values(), key=lambda row: (int(row["fillTime"]), int(row["tradeId"]))
        )
        pnl = Decimal(0)
        fees = Decimal(0)
        for fill in ordered:
            opened_before = quantity >= abs(plan.current_contracts)
            quantity += venue_decimal_v1(fill["fillSz"])
            if opening_time is None and quantity > abs(plan.current_contracts):
                opening_time = venue_decimal_v1(fill["fillTime"])
            value = venue_decimal_v1(fill["fillPnl"])
            _need(
                fill.get("feeCcy") == currency and (not opened_before or value == 0),
                "NET_REVERSAL_FILL_SETTLEMENT_UNPROVEN",
            )
            pnl += value
            fees += venue_decimal_v1(fill["fee"])
        _need(
            opening_time is not None
            and quantity == size
            and plan.current_contracts + (quantity if envelope.side == "buy" else -quantity)
            == target
            == plan.target_contracts,
            "NET_REVERSAL_TARGET_POSITION_UNPROVEN",
        )
    last_fill = ordered[-1]
    _need(
        position.get("tradeId") == last_fill["tradeId"]
        and opening_time <= venue_decimal_v1(position["cTime"]) <= position_time
        and venue_decimal_v1(last_fill["fillTime"])
        <= position_time
        <= _utc_ms(position_read.acquired_at.isoformat()),
        "NET_REVERSAL_RESULTING_POSITION_TIME_UNPROVEN",
    )
    return AuthenticatedNetReversalFillV1(
        venue_order_id,
        currency,
        position["posId"],
        position["cTime"],
        position["uTime"],
        str(target),
        position["avgPx"],
        last_fill["tradeId"],
        str(opening_time),
        venue_decimal_v1(position["fee"]),
        pnl,
        fees,
        canonical_digest_v1([read.to_reference_v1() for read in reads]),
    )


def collect_reversal_settlement_v1(
    *, source, fill, plan, envelope, old_position, socket_ms, previously_booked_fee
):
    """Bind the closed-side history to the original position, without a close order."""
    query = urlencode(
        {
            "instType": old_position["instType"],
            "instId": envelope.instrument_id,
            "mgnMode": envelope.td_mode,
            "posId": old_position["posId"],
            "before": str(int(socket_ms) - 1),
            "limit": "100",
        }
    )
    endpoint = ENDPOINT_ACCOUNT_POSITIONS_HISTORY + "?" + query
    decision_id = f"net-reversal:{envelope.envelope_digest}:settlement"
    before = datetime.fromtimestamp(source.clock(), timezone.utc)
    result = source.get(
        endpoint=endpoint,
        auth_required=True,
        pretrade_decision_id=decision_id,
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    read, body = source.completed_close_history_get_v1(decision_id=decision_id, after=before)
    rows = result.payload["data"]
    matches = [
        row
        for row in rows
        if (row.get("posId"), row.get("cTime")) == (old_position["posId"], old_position["cTime"])
    ]
    _need(
        result.payload["code"] == "0" and len(rows) < 100 and len(matches) == 1,
        "NET_REVERSAL_SETTLEMENT_HISTORY_UNPROVEN",
    )
    row = matches[0]
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
            old_position["instType"],
            plan.episode.position_side,
            "net",
            envelope.td_mode,
            fill.currency,
            "2",
        )
        and venue_decimal_v1(row["openMaxPos"])
        == venue_decimal_v1(row["closeTotalPos"])
        == abs(plan.current_contracts)
        and socket_ms
        <= venue_decimal_v1(row["uTime"])
        <= venue_decimal_v1(fill.position_updated_ms)
        and venue_decimal_v1(row["pnl"]) == fill.old_position_pnl
        and venue_decimal_v1(row["liqPenalty"]) == 0,
        "NET_REVERSAL_SETTLEMENT_HISTORY_MISMATCH",
    )
    with localcontext() as ctx:
        ctx.prec = 96
        settled = (
            Decimal(0)
            if row.get("settledPnl") in ("", None) and row["instType"] == "SWAP"
            else venue_decimal_v1(row["settledPnl"])
        )
        pnl, fee, funding = (venue_decimal_v1(row[field]) for field in ("pnl", "fee", "fundingFee"))
        _need(
            venue_decimal_v1(row["realizedPnl"]) == pnl + fee + funding + settled
            and venue_decimal_v1(old_position["fee"]) + fill.order_fee == fee + fill.position_fee
            and venue_decimal_v1(old_position["uTime"]) < socket_ms
            and old_position.get("ccy") == fill.currency,
            "NET_REVERSAL_SETTLEMENT_AMOUNT_UNPROVEN",
        )
        # Book the new opening fee now and exclude the fee already recorded
        # when the old position was opened by the preceding net reversal.
        native_net = pnl + fee + funding + settled + fill.position_fee - previously_booked_fee
    return native_net, read, body


def observe_booked_net_position_v1(
    *, source, booking, observed, occupancy_payloads, pending_orders, session_id, revision_ref
):
    """Reconfirm the booked exposure with fresh GETs before an occupied cycle."""
    from src.ops.execution_reconciliation_get_provenance_v1 import (
        AuthenticatedExecutionReconciliationProofV1,
    )
    from src.ops.execution_reconciliation_proof_store_v1 import (
        require_booked_net_reversal_readback_v1,
    )
    from .fresh_pretrade_runtime_get_v1 import ENDPOINT_ACCOUNT_POSITIONS
    from .productive_read_only_get_transport_v1 import AUTHORIZED_HOST

    _need(
        type(source) is AuthenticatedReconciliationGetV1
        and source.account_position_mode == "net_mode"
        and source.account == booking["account"]
        and source.proof_root is not None
        and not pending_orders,
        "NET_REVERSAL_NEXT_ACCOUNT_OR_PENDING_UNPROVEN",
    )
    require_booked_net_reversal_readback_v1(root=source.proof_root, booking=booking)
    rid = booking["reservation_id"]
    decision_id = f"{session_id}:net-reversal:{booking['envelope_digest']}"

    def get(endpoint):
        return source.get(
            endpoint=endpoint,
            auth_required=True,
            pretrade_decision_id=decision_id,
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        ).payload

    native = booking["native_id"]
    options = resolve_reconciliation_query_options_v1(
        instrument_id=booking["instrument_id"], native_id=native
    )
    pending = get(
        ENDPOINT_ORDERS_PENDING + "?" + urlencode({"instType": options.inst_type, "instId": native})
    )
    payload = get(ENDPOINT_ACCOUNT_POSITIONS + "?" + urlencode({"instId": native}))
    rows = payload["data"]
    inventory = occupancy_payloads["POSITIONS"]["data"]
    signed = venue_decimal_v1(booking["position_contracts"])
    _need(
        pending["code"] == "0"
        and pending["data"] == []
        and payload["code"] == "0"
        and len(rows) == 1
        and len(inventory) == 1
        and tuple((p.instrument_id, p.signed_quantity) for p in observed.positions)
        == ((booking["instrument_id"], signed),),
        "NET_REVERSAL_NEXT_POSITION_NOT_RECONCILED",
    )
    reads = (*source._gets[f"{session_id}:execution-recovery"], *source._gets[decision_id])
    position_identity = {
        "instId": native,
        "instType": options.inst_type,
        "posSide": "net",
        "mgnMode": booking["margin_mode"],
        "posId": booking["position_id"],
        "cTime": booking["position_created_ms"],
        "tradeId": booking["last_trade_id"],
        "ccy": booking["settlement_currency"],
    }
    _need(
        all(
            all(position.get(key) == value for key, value in position_identity.items())
            and venue_decimal_v1(position["avgPx"])
            == venue_decimal_v1(booking["average_entry_price"])
            and venue_decimal_v1(position["fee"]) == venue_decimal_v1(booking["position_fee"])
            and venue_decimal_v1(position["pos"]) == signed
            and venue_decimal_v1(booking["position_updated_ms"])
            <= venue_decimal_v1(position["uTime"])
            <= _utc_ms(reads[-1].acquired_at.isoformat())
            for position in (rows[0], inventory[0])
        )
        and 0 <= source.clock() - reads[0].acquired_at.timestamp() <= observed.max_age_seconds,
        "NET_REVERSAL_NEXT_POSITION_IDENTITY_UNPROVEN",
    )
    proof = AuthenticatedExecutionReconciliationProofV1(
        AUTHORIZED_HOST,
        source.account,
        session_id,
        rid,
        booking["envelope_digest"],
        revision_ref,
        canonical_digest_v1([read.to_reference_v1() for read in reads]),
        reads,
        None,
    )
    source.evidence[rid] = proof
    source.position_margin_modes[rid] = (booking["margin_mode"],)
    return {
        "identity_digest": proof.identity_digest,
        "snapshot_digest": proof.snapshot_digest,
        "portfolio_digest": observed.digest(),
        "reservation_released": False,
        "matched": True,
        "decision": {"reconciliation_complete": True},
        "net_reversal_booking_digest": booking["booking_digest"],
    }


def open_booked_net_position_episode_v1(*, host, bound, booking, config_digest, recover_only):
    """Open the opposite exposure through the same exit-state owner and cursor lane."""
    from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
        PositionEpisodeIdentityV1,
        PositionEpisodeScopeV1,
        open_position_episode_binding_v1,
    )

    identity = PositionEpisodeIdentityV1(
        booking["slot_id"],
        bound.instrument_id,
        bound.venue_native_id,
        booking["envelope_digest"],
        "long" if Decimal(booking["position_contracts"]) > 0 else "short",
        PositionEpisodeScopeV1(booking["account"], "LIVE"),
    )
    source_ref = "authenticated_net_reversal.v1:" + booking["booking_digest"]
    args = dict(
        identity=identity,
        state_root=host.root / "position-episodes" / identity.episode_id,
        repository_sha=host.repository_sha,
        config_digest=config_digest,
        writer_session_id=host.session_id,
        entry_source_ref=source_ref,
        entry_price_basis="CONFIRMED_POSITION_ENTRY_PRICE",
    )
    price = float(Decimal(booking["average_entry_price"]))
    entry_time = float(Decimal(booking["opening_fill_ms"]) / 1000)
    if not recover_only:
        try:
            return open_position_episode_binding_v1(
                **args, mode="create", entry_price=price, entry_event_time=entry_time
            )
        except FileExistsError:
            pass
    binding = open_position_episode_binding_v1(**args, mode="recover")
    _need(
        (binding.binding.entry_price, binding.binding.entry_event_time) == (price, entry_time),
        "NET_REVERSAL_NEXT_EPISODE_ANCHORS_CHANGED",
    )
    return binding
