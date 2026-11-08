"""Exact current native quantity sources at actual POST; no sizing or grant."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1 import (
    price_band_consumer_v1 as price_owner,
    price_band_observation_v1 as price_source_owner,
)
from . import current_productive_n1_venue_quantity_limit_admission_v1 as source_owner

from .current_productive_n1_venue_quantity_limit_admission_v1 import (
    VenueQuantitySourceV1,
    assess_native_order_venue_quantity_sources_v1,
    capture_venue_quantity_source_v1,
)
from .datasafety_gate_join_into_execution_admission_v1 import (
    evaluate_datasafety_admission_for_transport_result_v1,
)
from .execution_admission_contract_v1 import DataSafetyAdmissionStatusV1
from .final_order_envelope_v1 import FinalOrderEnvelopeV1, assert_envelope_unmodified_v1


class CurrentPostVenueQuantityError(ValueError):
    pass


def _exact_multiple_v1(value, step):
    """Exact decimal lattice check, independent of Decimal context precision."""
    a, b = value.as_tuple(), step.as_tuple()
    numerator = int(type(value)((0, a.digits, 0)))
    denominator = int(type(step)((0, b.digits, 0)))
    shift = a.exponent - b.exponent
    if shift >= 0:
        return (numerator % denominator) * pow(10, shift, denominator) % denominator == 0
    # Do not allocate a power of ten greater than the positive numerator.
    if -shift >= len(a.digits):
        return False
    return numerator % (denominator * 10 ** (-shift)) == 0


def _current_contract_constraints_v1(context, *, envelope, evaluated_at_utc):
    """Reject an unchanged order against its original current public row.

    Existing N1 sizing remains its own owner. No rounding, replacement price,
    future-rule application or extra request is performed here.
    """
    row = source_owner._row(context.public_source, native=envelope.instrument_id)
    if row.get("state") != "live":
        raise ValueError("VENUE_ORDER_INSTRUMENT_NOT_LIVE")
    minimum = source_owner._decimal(
        row.get("minSz"), positive=True, reason="VENUE_ORDER_MINIMUM_UNPROVEN"
    )
    lot = source_owner._decimal(
        row.get("lotSz"), positive=True, reason="VENUE_ORDER_LOT_STEP_UNPROVEN"
    )
    quantity = source_owner._decimal(
        envelope.quantity, positive=True, reason="VENUE_ORDER_QUANTITY_UNPROVEN"
    )
    if quantity < minimum:
        raise ValueError("VENUE_ORDER_BELOW_MINIMUM")
    if not _exact_multiple_v1(quantity, lot):
        raise ValueError("VENUE_ORDER_LOT_STEP_MISMATCH")
    tick = None
    if envelope.order_type == "limit":
        tick = source_owner._decimal(
            row.get("tickSz"), positive=True, reason="VENUE_ORDER_PRICE_STEP_UNPROVEN"
        )
        price = source_owner._decimal(
            envelope.price, positive=True, reason="VENUE_ORDER_LIMIT_PRICE_UNPROVEN"
        )
        if not _exact_multiple_v1(price, tick):
            raise ValueError("VENUE_ORDER_PRICE_STEP_MISMATCH")
    changes = row.get("upcChg")
    if not isinstance(changes, list):
        raise ValueError("VENUE_ORDER_UPCOMING_CHANGES_UNPROVEN")
    now = datetime.fromisoformat(evaluated_at_utc.replace("Z", "+00:00"))
    elapsed = now.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    now_ms = elapsed.days * 86400000 + elapsed.seconds * 1000 + elapsed.microseconds // 1000
    for change in changes:
        if (
            not isinstance(change, dict)
            or set(change) != {"param", "newValue", "effTime"}
            or change["param"] not in {"tickSz", "minSz", "maxMktSz"}
            or type(change["effTime"]) is not str
            or not change["effTime"].isascii()
            or not change["effTime"].isdigit()
            or int(change["effTime"]) <= 0
        ):
            raise ValueError("VENUE_ORDER_UPCOMING_CHANGE_UNPROVEN")
        source_owner._decimal(
            change["newValue"],
            positive=change["param"] != "maxMktSz",
            reason="VENUE_ORDER_UPCOMING_CHANGE_UNPROVEN",
        )
        if now_ms >= int(change["effTime"]):
            raise ValueError("VENUE_ORDER_ANNOUNCED_CHANGE_EFFECTIVE_REFRESH_REQUIRED")
    return {
        "instrument_state": row["state"],
        "minimum_native_quantity": str(minimum),
        "native_quantity_step": str(lot),
        "limit_price_step": str(tick) if tick is not None else "NOT_APPLICABLE_MARKET",
        "announced_changes": json.loads(json.dumps(changes)),
        "evaluated_at_utc": evaluated_at_utc,
    }


def _current_limit_price_band_v1(context, *, envelope, evaluated_at_utc):
    if envelope.order_type == "market":
        return {"status": "NOT_APPLICABLE_MARKET", "price_domain": "VENUE_LIMIT_PRICE"}
    source = context.price_band_source
    if (
        type(source) is not VenueQuantitySourceV1
        or source.acquisition_decision_id != context.acquisition_decision_id
    ):
        raise ValueError("VENUE_PRICE_BAND_SOURCE_REQUIRED")
    source_owner.acquisition_age_seconds_v1(
        acquired_at_utc=source.acquired_at_utc, now_utc=evaluated_at_utc
    )
    query = source_owner._query(source, path="/api/v5/public/price-limit")
    if query != {"instId": [envelope.instrument_id]}:
        raise ValueError("VENUE_PRICE_BAND_QUERY_MISMATCH")
    row = source_owner._row(source, native=envelope.instrument_id)
    public_query = source_owner._query(context.public_source, path="/api/v5/public/instruments")
    if row.get("instType") != public_query["instType"][0]:
        raise ValueError("VENUE_PRICE_BAND_INSTRUMENT_TYPE_MISMATCH")
    if price_source_owner.normalize_enabled_raw_v1(row.get("enabled")) != "true":
        raise ValueError("VENUE_PRICE_BAND_NOT_ACTIVE")
    ts = row.get("ts")
    if type(ts) is not str or not ts.isascii() or not ts.isdigit() or int(ts) <= 0:
        raise ValueError("VENUE_PRICE_BAND_TIMESTAMP_UNPROVEN")
    for field in ("buyLmt", "sellLmt"):
        raw = row.get(field)
        if type(raw) is not str or not raw or raw != raw.strip():
            raise ValueError("VENUE_PRICE_BAND_RAW_PRICE_UNPROVEN:" + field)
    buy = price_source_owner._require_non_negative_decimal(row.get("buyLmt"), field="buyLmt")
    sell = price_source_owner._require_non_negative_decimal(row.get("sellLmt"), field="sellLmt")
    side, field, selected, px = price_owner.compare_native_limit_price_to_band_v1(
        side=envelope.side, planned_limit_px=envelope.price, buy_lmt=buy, sell_lmt=sell
    )
    return dict(
        status="LIMIT_PRICE_WITHIN_ORIGINAL_SIDE_BOUND",
        side=side,
        selected_field=field,
        selected_value=str(selected),
        planned_limit_px=str(px),
        buy_lmt_raw=row["buyLmt"],
        sell_lmt_raw=row["sellLmt"],
        ts_raw=ts,
        enabled=True,
        price_domain="VENUE_LIMIT_PRICE",
        venue_timestamp_age_bound="UNBOUND",
        evaluated_at_utc=evaluated_at_utc,
    )


@dataclass(frozen=True)
class CurrentPostVenueQuantityContextV1:
    envelope: FinalOrderEnvelopeV1
    acquisition_decision_id: str
    public_source: VenueQuantitySourceV1
    private_source: VenueQuantitySourceV1
    price_band_source: VenueQuantitySourceV1 | None = None

    def inspect_v1(self, *, envelope, stage):
        try:
            assert_envelope_unmodified_v1(envelope)
            if self.envelope != envelope:
                raise ValueError("ENVELOPE_MISMATCH")
            if (
                not isinstance(self.acquisition_decision_id, str)
                or not self.acquisition_decision_id
                or self.acquisition_decision_id != self.acquisition_decision_id.strip()
                or envelope.quantity_unit.upper() not in {"CONTRACT", "CONTRACTS"}
                or envelope.reduce_only is not False
            ):
                raise ValueError("NATIVE_NEW_ENTRY_CONTEXT_REQUIRED")
            now = source_owner.utc_now_iso_v1()
            assessment = assess_native_order_venue_quantity_sources_v1(
                public_source=self.public_source,
                private_source=self.private_source,
                acquisition_decision_id=self.acquisition_decision_id,
                native=envelope.instrument_id,
                side=envelope.side,
                quantity=envelope.quantity,
                order_type=envelope.order_type,
                td_mode=envelope.td_mode,
                price=envelope.price,
                evaluated_at_utc=now,
            )
            if not assessment["allowed"]:
                raise ValueError(",".join(assessment["reason_codes"]))
            constraints = _current_contract_constraints_v1(
                self, envelope=envelope, evaluated_at_utc=now
            )
            price_band = _current_limit_price_band_v1(self, envelope=envelope, evaluated_at_utc=now)
            return {
                **assessment,
                "scope": "CURRENT_NATIVE_VENUE_ORDER_CONSTRAINTS_ONLY",
                "order_constraints": constraints,
                "price_band": price_band,
                "envelope_digest": envelope.envelope_digest,
                "acquisition_decision_id": self.acquisition_decision_id,
                "sources": {
                    label: {
                        **asdict(source),
                        "payload_sha256": hashlib.sha256(source.payload_json.encode()).hexdigest(),
                    }
                    for label, source in (
                        ("public", self.public_source),
                        ("private", self.private_source),
                        ("price_band", self.price_band_source),
                    )
                    if source is not None
                },
            }
        except (
            ValueError,
            TypeError,
            AttributeError,
            KeyError,
            price_owner.LiveCanaryPriceBandConsumerError,
            price_source_owner.LiveCanaryPriceBandObservationError,
        ) as exc:
            raise CurrentPostVenueQuantityError(f"POST_QUANTITY_DENIED:{stage}:{exc}") from exc


def capture_current_post_venue_quantity_v1(*, envelope, results, acquisition_decision_id):
    limit_order = envelope.order_type == "limit"
    for group in ("instruments", "max_size", *(["price_limit"] if limit_order else [])):
        if (
            evaluate_datasafety_admission_for_transport_result_v1(results.get(group))
            != DataSafetyAdmissionStatusV1.SATISFIED.value
        ):
            raise CurrentPostVenueQuantityError("POST_QUANTITY_DATASAFETY_UNPROVEN")
    try:
        if limit_order and results["price_limit"].auth_header_sent is not False:
            raise ValueError("VENUE_PRICE_BAND_PUBLIC_UNSIGNED_REQUIRED")
        return CurrentPostVenueQuantityContextV1(
            envelope=envelope,
            acquisition_decision_id=acquisition_decision_id,
            public_source=capture_venue_quantity_source_v1(
                results=results, item_id="MAX_SIZE", acquisition_decision_id=acquisition_decision_id
            ),
            private_source=capture_venue_quantity_source_v1(
                results=results,
                item_id="MAX_AVAILABLE",
                acquisition_decision_id=acquisition_decision_id,
            ),
            price_band_source=(
                capture_venue_quantity_source_v1(
                    results=results,
                    item_id="PRICE_BAND",
                    acquisition_decision_id=acquisition_decision_id,
                )
                if limit_order
                else None
            ),
        )
    except (ValueError, TypeError, AttributeError, KeyError) as exc:
        raise CurrentPostVenueQuantityError(f"POST_QUANTITY_SOURCE_UNPROVEN:{exc}") from exc


def inspect_current_post_venue_quantity_v1(context, *, envelope, stage):
    if type(context) is not CurrentPostVenueQuantityContextV1:
        raise CurrentPostVenueQuantityError(f"POST_QUANTITY_CONTEXT_REQUIRED:{stage}")
    return context.inspect_v1(envelope=envelope, stage=stage)
