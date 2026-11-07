"""Source/meaning boundaries of N1 planning limits; every source is synthetic."""

from dataclasses import replace
import json
from urllib.parse import urlencode

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_n1_venue_quantity_limit_admission_v1 import (
    assess_n1_final_plan_venue_quantity_v1,
    capture_n1_venue_quantity_limits_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import _bound

EPOCH = "2026-11-07T12:00:00Z"
CYCLE = "synthetic-n1-cycle"
ACCOUNT = "synthetic-account"
ACQUISITION = json.dumps(
    {"decision_epoch": EPOCH, "cycle_id": CYCLE}, sort_keys=True, separators=(",", ":")
)


def sources(*, public_value="10", private_buy="10", private_sell="0", price=""):
    native = _bound().venue_native_id
    public = {
        "code": "0",
        "data": [
            {
                "instId": native,
                "instType": "SWAP",
                "maxMktSz": public_value,
                "maxLmtSz": public_value,
            }
        ],
    }
    private = {
        "code": "0",
        "data": [{"instId": native, "maxBuy": private_buy, "maxSell": private_sell}],
    }
    query = {"instId": native, "tdMode": "cross"}
    if price:
        query["px"] = price

    def result(endpoint, payload, private):
        return FreshPretradeGetTransportResultV1(
            get_performed=True,
            method="GET",
            endpoint=endpoint,
            http_status=200,
            payload=payload,
            auth_header_sent=private,
            transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
            venue_live_contact=False,
            historical_reuse=False,
            error_class="",
            pretrade_decision_id=ACQUISITION,
            acquired_at_utc=EPOCH,
        )

    return {
        "instruments": result(
            "/api/v5/public/instruments?" + urlencode({"instType": "SWAP", "instId": native}),
            public,
            False,
        ),
        "max_size": result("/api/v5/account/max-size?" + urlencode(query), private, True),
    }


def capture(results):
    return capture_n1_venue_quantity_limits_v1(
        results=results,
        acquisition_decision_id=ACQUISITION,
        account_identity=ACCOUNT,
        bound_instrument=_bound(),
        decision_epoch=EPOCH,
        cycle_id=CYCLE,
    )


def plan(*, side="buy", order_type="market", quantity="1", price=""):
    wire = {
        "instId": _bound().venue_native_id,
        "side": side,
        "ordType": order_type,
        "sz": quantity,
        "tdMode": "cross",
    }
    if price:
        wire["px"] = price
    return VenuePlanCandidateV1(
        instrument_id=_bound().venue_native_id,
        side=side,
        quantity=quantity,
        order_type=order_type,
        td_mode="cross",
        reduce_only=False,
        clordid="synthetic-plan",
        venue_native_payload=wire,
        quantity_source="SYNTHETIC_CANONICAL_COUNT",
        side_source="SYNTHETIC",
        instrument_source="SYNTHETIC",
        path_kind="SYNTHETIC",
    )


def assess(observation, order=None, **kwargs):
    args = dict(
        observation=observation,
        plan=order or plan(),
        bound_instrument=_bound(),
        account_identity=ACCOUNT,
        decision_epoch=EPOCH,
        cycle_id=CYCLE,
        evaluated_at_utc=EPOCH,
    )
    args.update(kwargs)
    return assess_n1_final_plan_venue_quantity_v1(**args)


@pytest.mark.parametrize(
    ("side", "allowed", "field"), [("buy", True, "maxBuy"), ("sell", False, "maxSell")]
)
def test_order_side_selects_private_contract_count(side, allowed, field):
    result = assess(capture(sources(private_buy="1", private_sell="0")), plan(side=side))
    assert result.allowed is allowed
    assert result.selected_private_field == field
    assert result.final_native_quantity == "1"


def test_limits_reject_without_clamping_final_quantity():
    order = plan(quantity="1")
    before = order.quantity, dict(order.venue_native_payload)
    result = assess(capture(sources(public_value="0.5")), order)
    assert not result.allowed
    assert result.reason_codes == ("VENUE_QUANTITY_EXCEEDS_MAXMKTSZ",)
    assert (order.quantity, order.venue_native_payload) == before


@pytest.mark.parametrize(
    ("order_type", "public_field"), [("market", "maxMktSz"), ("limit", "maxLmtSz")]
)
def test_equality_and_order_type_are_distinct(order_type, public_field):
    raw = sources(public_value="1", private_buy="1", price="20" if order_type == "limit" else "")
    row = raw["instruments"].payload["data"][0]
    row["maxLmtSz" if public_field == "maxMktSz" else "maxMktSz"] = "0"
    result = assess(
        capture(raw), plan(order_type=order_type, price="20" if order_type == "limit" else "")
    )
    assert result.allowed and result.selected_public_field == public_field
    assert result.public_maximum == result.private_maximum == "1"


@pytest.mark.parametrize("value", [None, "", "NaN", "Infinity", "-1", True, 1, " 1", "bad"])
@pytest.mark.parametrize("source", ["public", "private"])
def test_invalid_limits_are_unknown_not_unlimited(value, source):
    raw = sources(public_value=value) if source == "public" else sources(private_buy=value)
    assert not assess(capture(raw)).allowed


@pytest.mark.parametrize("group", ["instruments", "max_size"])
@pytest.mark.parametrize("fault", ["duplicate", "foreign", "venue_error", "malformed_row"])
def test_exact_unique_response_row_and_success_are_required(group, fault):
    raw = sources()
    payload = raw[group].payload
    if fault == "duplicate":
        payload["data"].append(dict(payload["data"][0]))
    elif fault == "foreign":
        payload["data"][0]["instId"] = "foreign"
    elif fault == "venue_error":
        payload["code"] = "51000"
        with pytest.raises(ValueError, match="SOURCE_NOT_TRUSTED"):
            capture(raw)
        return
    else:
        payload["data"].append(None)
    assert not assess(capture(raw)).allowed


@pytest.mark.parametrize(
    ("group", "field", "value"),
    [
        ("max_size", "get_performed", False),
        ("max_size", "auth_header_sent", False),
        ("instruments", "http_status", 500),
        ("max_size", "method", "POST"),
        ("max_size", "historical_reuse", True),
        ("max_size", "pretrade_decision_id", "foreign"),
    ],
)
def test_capture_requires_the_original_successful_acquisition(group, field, value):
    raw = sources()
    raw[group] = replace(raw[group], **{field: value})
    with pytest.raises(ValueError):
        capture(raw)


@pytest.mark.parametrize("group", ["instruments", "max_size"])
@pytest.mark.parametrize(
    "clock", ["2026-11-07T11:59:00Z", "2026-11-07T12:00:01Z", "", "2026-11-07T12:00:00"]
)
def test_original_acquisition_age_policy_is_rechecked_at_consumer(group, clock):
    raw = sources()
    raw[group] = replace(raw[group], acquired_at_utc=clock)
    assert not assess(capture(raw)).allowed


@pytest.mark.parametrize(
    "context",
    [
        {"account_identity": "foreign"},
        {"decision_epoch": "2026-11-07T12:00:01Z"},
        {"cycle_id": "foreign"},
        {"bound_instrument": replace(_bound(), selection_id="another-generation")},
    ],
)
def test_current_owner_and_full_binding_generation_are_required(context):
    assert not assess(capture(sources()), **context).allowed


def test_detached_source_survives_mutable_transport_payload_change():
    raw = sources(private_buy="1")
    observation = capture(raw)
    raw["max_size"].payload["data"][0]["maxBuy"] = "0"
    assert assess(observation).allowed
    assert not assess(capture(raw)).allowed


def test_changed_observation_cannot_keep_the_original_digest():
    observation = capture(sources())
    changed = replace(
        observation,
        private_source=replace(observation.private_source, payload_json='{"code":"0","data":[]}'),
    )
    assert assess(changed).reason_codes == ("VENUE_QUANTITY_OBSERVATION_CHANGED",)


@pytest.mark.parametrize(
    "query",
    [
        {"instId": "foreign", "tdMode": "cross"},
        {"instId": _bound().venue_native_id, "tdMode": "isolated"},
        {"instId": _bound().venue_native_id, "tdMode": "cross", "leverage": "100"},
    ],
)
def test_private_request_scope_cannot_be_substituted(query):
    raw = sources()
    raw["max_size"] = replace(
        raw["max_size"], endpoint="/api/v5/account/max-size?" + urlencode(query)
    )
    assert not assess(capture(raw)).allowed


@pytest.mark.parametrize(("source_price", "order_price"), [("", "20"), ("19", "20")])
def test_limit_price_needs_its_own_exact_maximum_source(source_price, order_price):
    assert not assess(
        capture(sources(price=source_price)), plan(order_type="limit", price=order_price)
    ).allowed


def test_market_order_cannot_borrow_a_limit_price_observation():
    assert not assess(capture(sources(price="20")), plan()).allowed


def test_wire_quantity_and_plan_must_be_identical():
    order = plan()
    order.venue_native_payload["sz"] = "2"
    assert not assess(capture(sources()), order).allowed


def test_reduce_only_does_not_enter_opening_capacity_admission():
    order = replace(plan(), reduce_only=True)
    assert not assess(capture(sources()), order).allowed


def test_missing_observation_is_fail_closed():
    assert assess(None).reason_codes == ("VENUE_QUANTITY_OBSERVATION_MISSING",)
