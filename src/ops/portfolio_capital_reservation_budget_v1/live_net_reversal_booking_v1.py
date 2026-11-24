"""Store the authenticated reversal settlement with the unchanged original hold."""

from dataclasses import asdict, dataclass
from decimal import Decimal, localcontext
import re

from .durable_store_v1 import digest
from .live_l10_close_booking_v1 import venue_decimal_v1
from .contract_v1 import ReservationStateV1


@dataclass(frozen=True)
class LiveNetReversalBookingV1:
    reservation_id: str
    account: str
    slot_id: str
    instrument_id: str
    native_id: str
    selection_digest: str
    previous_episode_id: str
    envelope_digest: str
    client_order_id: str
    venue_order_id: str
    margin_mode: str
    current_contracts: str
    position_contracts: str
    position_id: str
    position_created_ms: str
    position_updated_ms: str
    position_fee: str
    average_entry_price: str
    opening_fill_ms: str
    last_trade_id: str
    settlement_currency: str
    settlement_native: str
    valuation_rate_usdc: str
    net_result_usdc: str
    settlement_digest: str

    def to_dict_v1(self):
        body = asdict(self)
        return {**body, "booking_digest": digest(body)}


def _require(condition):
    if not condition:
        raise ValueError("NET_REVERSAL_BOOKING_ORIGINAL_CHAIN_UNPROVEN")


def restore_live_net_reversal_bookings_v1(owner, rows):
    from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
        parse_exchange_reconciliation_identity_v1,
    )

    _require(type(rows) is dict)
    prior_by_hold = {}
    venue_orders = set()
    for key, group in rows.items():
        _require(type(group) is list and bool(group))
        hold = owner._by_key.get(owner._by_id.get(key))
        link = owner._execution_links.get(key)
        bound = owner._reservation_bindings.get(key, {}).get("bound", {})
        _require(
            hold is not None and link is not None and link["phase"] == "SUBMIT_MAY_HAVE_OCCURRED"
        )
        identity = parse_exchange_reconciliation_identity_v1(link["identity"])
        previous = identity.identity_digest()
        previous_contracts = venue_decimal_v1(
            link["reconciliation"]["decision"]["cumulative_filled_qty"]
        )
        if identity.selected_side.upper() == "SHORT":
            previous_contracts = -previous_contracts
        previous_time = Decimal(0)
        seen = {previous}
        for row in group:
            body = dict(row)
            row_digest = body.pop("booking_digest")
            booking = LiveNetReversalBookingV1(**body)
            _require(
                all(type(value) is str and bool(value) for value in body.values())
                and row_digest == digest(body)
                and booking.previous_episode_id == previous
                and booking.envelope_digest not in seen
                and booking.reservation_id == key
                and booking.account == owner._account_identity
                and booking.account == identity.account_identity
                and identity.execution_environment == owner.execution_environment_v1()
                and booking.slot_id == str(hold.slot_id)
                and (booking.instrument_id, booking.native_id, booking.selection_digest)
                == (
                    bound["instrument_id"],
                    bound["venue_native_id"],
                    bound["selection_integrity_digest"],
                )
                and booking.margin_mode == link["envelope"]["td_mode"]
                and booking.settlement_currency in {"USDT", "USDC"}
                and all(
                    re.fullmatch(r"[a-f0-9]{64}", value)
                    for value in (booking.envelope_digest, booking.settlement_digest)
                )
                and all(
                    re.fullmatch(r"[1-9][0-9]{0,31}", value)
                    for value in (
                        booking.position_id,
                        booking.venue_order_id,
                        booking.last_trade_id,
                    )
                )
            )
            venue_key = (booking.native_id, booking.venue_order_id)
            _require(venue_key not in venue_orders)
            seen.add(booking.envelope_digest)
            venue_orders.add(venue_key)
            opened, created, updated = map(
                venue_decimal_v1,
                (booking.opening_fill_ms, booking.position_created_ms, booking.position_updated_ms),
            )
            signed = venue_decimal_v1(booking.position_contracts)
            rate = Decimal(booking.valuation_rate_usdc)
            with localcontext() as ctx:
                ctx.prec = 96
                _require(
                    previous_time < opened <= created <= updated
                    and venue_decimal_v1(booking.current_contracts) == previous_contracts
                    and signed * previous_contracts < 0
                    and venue_decimal_v1(booking.average_entry_price) > 0
                    and rate.is_finite()
                    and rate > 0
                    and (booking.settlement_currency != "USDC" or rate == 1)
                    and Decimal(booking.net_result_usdc)
                    == Decimal(booking.settlement_native) * rate
                )
            venue_decimal_v1(booking.position_fee)
            previous, previous_contracts, previous_time = booking.envelope_digest, signed, updated
        prior_by_hold[key] = [dict(row) for row in group]
    return prior_by_hold


def build_live_net_reversal_booking_v1(
    owner, *, plan, envelope, fill, native_net, settlement_digest
):
    """Use the same bound quote valuation used for the retained reversal."""
    rid = plan.old_reservation_id
    original = owner._sizing_bindings[rid].monetary_source
    _require(original is not None)
    _, money, _ = original.rebuild_v1()
    _require(
        money.settle_currency == fill.currency
        and (fill.currency == "USDC" or money.quote_currency == fill.currency)
    )
    rate = Decimal(1) if fill.currency == "USDC" else plan.quote_to_usdc
    with localcontext() as ctx:
        ctx.prec = 96
        net = native_net * rate
    return LiveNetReversalBookingV1(
        rid,
        plan.episode.account_scope.account_identity,
        plan.episode.lane_id,
        plan.episode.instrument_id,
        plan.episode.venue_native_id,
        plan.selection_digest,
        plan.episode.episode_id,
        envelope.envelope_digest,
        envelope.client_order_id,
        fill.venue_order_id,
        envelope.td_mode,
        str(plan.current_contracts),
        fill.signed_position_contracts,
        fill.position_id,
        fill.position_created_ms,
        fill.position_updated_ms,
        str(fill.position_fee),
        fill.average_entry_price,
        fill.opening_fill_ms,
        fill.last_trade_id,
        fill.currency,
        str(native_net),
        str(rate),
        str(net),
        settlement_digest,
    )


def insert_live_net_reversal_booking_locked_v1(owner, booking):
    """Validate the whole continuation before the owner commits one state revision."""
    rid = booking.reservation_id
    hold = owner._by_key.get(owner._by_id.get(rid))
    _require(
        hold is not None
        and hold.state is ReservationStateV1.COMMITTED
        and owner._reservation_bindings.get(rid) == owner._lane_bindings.get(booking.slot_id)
    )
    series = owner._live_net_reversal_bookings.get(rid, [])
    result = booking.to_dict_v1()
    prior = next((row for row in series if row["envelope_digest"] == booking.envelope_digest), None)
    if prior is not None:
        _require(prior == result)
        return dict(prior)
    owner._live_net_reversal_bookings = restore_live_net_reversal_bookings_v1(
        owner, {**owner._live_net_reversal_bookings, rid: [*series, result]}
    )
    owner._persist_locked()
    return dict(result)
