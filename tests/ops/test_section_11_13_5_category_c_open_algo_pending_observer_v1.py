"""Deterministic mock-only tests for Category-C open algo-pending observer.

No Exchange network. No urllib wire send. No submit/cancel/amend/flatten.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.category_c_open_algo_pending_observer_v1 import (
    CATEGORY_C_ORD_TYPE_VARIANTS,
    CATEGORY_C_PAGE_LIMIT,
    CategoryCObservationOutcomeV1,
    build_category_c_orders_algo_pending_endpoint_v1,
    observe_category_c_open_algo_pending_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_ORDERS_ALGO_PENDING,
    GET_ENDPOINTS_PRIVATE,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    POST_ENDPOINTS_GATED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    RecordingFakeCanaryTransportV1,
)

_OBSERVER_PATH = Path(
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
    "category_c_open_algo_pending_observer_v1.py"
)
_FOREIGN_INST = "BTC-USDT-SWAP"
_REGULAR_PENDING = "/api/v5/trade/orders-pending"


def _ok_body(rows: list[Mapping[str, Any]] | None = None) -> bytes:
    return json.dumps({"code": "0", "data": list(rows or [])}).encode()


def _row(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "algoId": "algo-1",
        "instId": DEFAULT_INSTRUMENT_ID,
        "ordType": "conditional",
        "side": "sell",
        "sz": "1",
        "state": "live",
        "tpTriggerPx": "80000",
        "tpOrdPx": "-1",
        "slTriggerPx": "",
        "slOrdPx": "",
        "triggerPx": "",
        "reduceOnly": "true",
        "attachAlgoOrds": [],
        "cTime": "1",
        "uTime": "1",
    }
    payload.update(overrides)
    return payload


def _endpoint(ord_type: str, *, after: str | None = None) -> str:
    return build_category_c_orders_algo_pending_endpoint_v1(
        ord_type=ord_type,
        instrument_id=DEFAULT_INSTRUMENT_ID,
        after=after,
    )


def _transport(
    bodies: Mapping[str, bytes] | None = None,
    *,
    default: bytes | None = None,
) -> RecordingFakeCanaryTransportV1:
    return RecordingFakeCanaryTransportV1(
        body=default if default is not None else _ok_body(),
        bodies_by_endpoint=dict(bodies or {}),
    )


def _client(
    transport: RecordingFakeCanaryTransportV1,
    *,
    max_request_count: int = 64,
) -> LiveCanaryHttpClientV1:
    return LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host="eea.okx.com",
        transport=transport,
        max_request_count=max_request_count,
    )


def _observe(
    transport: RecordingFakeCanaryTransportV1,
    **kwargs: Any,
) -> Any:
    return observe_category_c_open_algo_pending_v1(
        client=_client(transport),
        instrument_id=DEFAULT_INSTRUMENT_ID,
        **kwargs,
    )


def _query(endpoint: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(endpoint).query, keep_blank_values=True)


def test_algo_endpoint_constant_and_private_allowlist() -> None:
    assert ENDPOINT_ORDERS_ALGO_PENDING == "/api/v5/trade/orders-algo-pending"
    assert ENDPOINT_ORDERS_ALGO_PENDING in GET_ENDPOINTS_PRIVATE
    assert ENDPOINT_ORDERS_ALGO_PENDING not in POST_ENDPOINTS_GATED
    assert _REGULAR_PENDING in GET_ENDPOINTS_PRIVATE
    assert _REGULAR_PENDING != ENDPOINT_ORDERS_ALGO_PENDING


def test_observer_issues_required_get_variants_with_filters_and_no_body() -> None:
    transport = _transport()
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED
    assert len(transport.calls) == 3
    assert {c.method for c in transport.calls} == {"GET"}
    assert all(c.body_text == "" for c in transport.calls)
    seen_ord: list[str] = []
    for call in transport.calls:
        path = urlparse(call.endpoint).path or call.endpoint.split("?", 1)[0]
        assert path == ENDPOINT_ORDERS_ALGO_PENDING
        assert _REGULAR_PENDING not in call.endpoint
        query = _query(call.endpoint)
        seen_ord.extend(query["ordType"])
        assert query["instType"] == ["FUTURES"]
        assert query["instId"] == [DEFAULT_INSTRUMENT_ID]
        assert query["limit"] == ["100"]
        assert "after" not in query
    assert seen_ord == list(CATEGORY_C_ORD_TYPE_VARIANTS)
    assert CATEGORY_C_ORD_TYPE_VARIANTS == (
        "conditional,oco",
        "trigger",
        "move_order_stop",
    )


@pytest.mark.parametrize(
    ("ord_type", "variant"),
    [
        ("conditional", "conditional,oco"),
        ("oco", "conditional,oco"),
        ("trigger", "trigger"),
        ("move_order_stop", "move_order_stop"),
    ],
)
def test_target_named_row_is_observed(ord_type: str, variant: str) -> None:
    ep = _endpoint(variant)
    transport = _transport({ep: _ok_body([_row(ordType=ord_type, algoId=f"id-{ord_type}")])})
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_OBSERVED
    assert len(result.target_rows) == 1
    assert result.target_rows[0].to_dict()["ordType"] == ord_type
    assert result.target_rows[0].to_dict()["algoId"] == f"id-{ord_type}"
    assert result.canonical_binding_status == "UNBOUND"


def test_len_100_paginates_with_after_last_algo_id_and_empty_followup_terminates() -> None:
    first_rows = [
        _row(algoId=f"algo-{index:03d}", ordType="trigger")
        for index in range(CATEGORY_C_PAGE_LIMIT)
    ]
    first_ep = _endpoint("trigger")
    last_id = f"algo-{CATEGORY_C_PAGE_LIMIT - 1:03d}"
    second_ep = _endpoint("trigger", after=last_id)
    transport = _transport(
        {
            first_ep: _ok_body(first_rows),
            second_ep: _ok_body([]),
        }
    )
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_OBSERVED
    trigger_calls = [c for c in transport.calls if "ordType=trigger" in c.endpoint]
    assert len(trigger_calls) == 2
    assert "after=" not in trigger_calls[0].endpoint
    assert _query(trigger_calls[1].endpoint)["after"] == [last_id]
    assert len(result.target_rows) == CATEGORY_C_PAGE_LIMIT


def test_short_page_terminates_variant_without_after() -> None:
    ep = _endpoint("conditional,oco")
    transport = _transport({ep: _ok_body([_row(), _row(algoId="algo-2", ordType="oco")])})
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_OBSERVED
    variant_calls = [c for c in transport.calls if "ordType=conditional,oco" in c.endpoint]
    assert len(variant_calls) == 1
    assert "after=" not in variant_calls[0].endpoint
    assert len(result.target_rows) == 2
    assert [row.to_dict()["algoId"] for row in result.target_rows] == ["algo-1", "algo-2"]


def test_transport_error_is_unproven() -> None:
    class _Boom(RecordingFakeCanaryTransportV1):
        def send(self, request):  # type: ignore[no-untyped-def]
            self.calls.append(request)
            raise LiveCanaryHttpError("FAKE_TRANSPORT")

    transport = _Boom()
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN
    assert result.fail_closed_reason == "TRANSPORT_OR_CLIENT_ERROR:LiveCanaryHttpError"
    assert {c.method for c in transport.calls} == {"GET"}


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        (json.dumps({"code": "50000", "data": []}).encode(), "API_CODE_NOT_SUCCESS"),
        (json.dumps({"code": "0"}).encode(), "DATA_MISSING"),
        (json.dumps({"code": "0", "data": None}).encode(), "DATA_NULL"),
        (json.dumps({"code": "0", "data": {"rows": []}}).encode(), "DATA_NOT_LIST"),
        (json.dumps({"code": "0", "data": ["not-an-object"]}).encode(), "ROW_NOT_OBJECT"),
    ],
)
def test_malformed_or_unsuccessful_payload_is_unproven(body: bytes, reason: str) -> None:
    transport = _transport(default=body)
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN
    assert result.fail_closed_reason == reason
    assert result.outcome is not CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED


def test_missing_instid_is_unproven() -> None:
    row = _row()
    del row["instId"]
    transport = _transport({_endpoint("conditional,oco"): _ok_body([row])})
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN
    assert result.fail_closed_reason == "INSTID_MISSING"


def test_foreign_instid_must_not_yield_not_observed() -> None:
    transport = _transport({_endpoint("conditional,oco"): _ok_body([_row(instId=_FOREIGN_INST)])})
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN
    assert result.fail_closed_reason == "FOREIGN_INSTID"
    assert result.outcome is not CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED


def test_unknown_ordtype_is_unknown_type_present() -> None:
    transport = _transport({_endpoint("trigger"): _ok_body([_row(ordType="iceberg", algoId="x")])})
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.CATEGORY_C_UNKNOWN_TYPE_PRESENT
    assert result.fail_closed_reason == "UNKNOWN_ORDTYPE:iceberg"
    assert result.outcome is not CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED


def test_missing_state_is_unproven() -> None:
    row = _row()
    del row["state"]
    transport = _transport({_endpoint("conditional,oco"): _ok_body([row])})
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN
    assert result.fail_closed_reason == "STATE_MISSING"


def test_unexpected_state_is_unproven() -> None:
    transport = _transport({_endpoint("conditional,oco"): _ok_body([_row(state="filled")])})
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN
    assert result.fail_closed_reason == "STATE_UNEXPECTED:filled"


def test_missing_algoid_is_unproven() -> None:
    row = _row()
    del row["algoId"]
    transport = _transport({_endpoint("conditional,oco"): _ok_body([row])})
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN
    assert result.fail_closed_reason == "ALGOID_MISSING"


def test_duplicate_algo_id_is_unproven() -> None:
    transport = _transport(
        {
            _endpoint("conditional,oco"): _ok_body(
                [_row(algoId="dup"), _row(algoId="dup", ordType="oco")]
            )
        }
    )
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN
    assert result.fail_closed_reason == "DUPLICATE_ALGO_ID"


def test_cyclic_pagination_cursor_is_unproven() -> None:
    page = [_row(algoId=f"algo-{index:03d}") for index in range(CATEGORY_C_PAGE_LIMIT)]
    last_id = f"algo-{CATEGORY_C_PAGE_LIMIT - 1:03d}"
    transport = _transport(
        {
            _endpoint("conditional,oco"): _ok_body(page),
            _endpoint("conditional,oco", after=last_id): _ok_body(page),
        }
    )
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN
    assert result.fail_closed_reason == "DUPLICATE_ALGO_ID"


def test_missing_algoid_on_full_page_fails_closed() -> None:
    rows = [_row(algoId=f"algo-{index:03d}") for index in range(CATEGORY_C_PAGE_LIMIT)]
    del rows[-1]["algoId"]
    transport = _transport({_endpoint("conditional,oco"): _ok_body(rows)})
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.OBSERVATION_UNPROVEN
    assert result.fail_closed_reason == "ALGOID_MISSING"
    assert result.outcome is not CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED


def test_incomplete_variant_coverage_cannot_yield_not_observed() -> None:
    transport = _transport()
    result = _observe(transport, max_requests=1)
    assert result.outcome is CategoryCObservationOutcomeV1.CATEGORY_C_OBSERVATION_INCOMPLETE
    assert result.fail_closed_reason == "REQUEST_GUARD_EXCEEDED"
    assert result.outcome is not CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED
    assert len(transport.calls) == 1


def test_page_guard_exceeded_is_incomplete() -> None:
    rows = [_row(algoId=f"algo-{index:03d}") for index in range(CATEGORY_C_PAGE_LIMIT)]
    transport = _transport({_endpoint("conditional,oco"): _ok_body(rows)})
    result = _observe(transport, max_pages_per_variant=1)
    assert result.outcome is CategoryCObservationOutcomeV1.CATEGORY_C_OBSERVATION_INCOMPLETE
    assert result.fail_closed_reason == "PAGE_GUARD_EXCEEDED"
    assert result.outcome is not CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED


def test_regular_pending_emptiness_has_no_bearing_and_is_not_called() -> None:
    transport = _transport()
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED
    assert all(_REGULAR_PENDING not in c.endpoint for c in transport.calls)
    assert all(_REGULAR_PENDING not in c.url for c in transport.calls)
    signature = inspect.signature(observe_category_c_open_algo_pending_v1)
    assert "pending" not in signature.parameters
    assert "orders_pending" not in signature.parameters


def test_no_submit_cancel_amend_flatten_invoked_and_calls_are_get_only() -> None:
    transport = _transport()
    client = _client(transport)
    result = observe_category_c_open_algo_pending_v1(
        client=client, instrument_id=DEFAULT_INSTRUMENT_ID
    )
    assert result.outcome is CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED
    assert client.counters.entry_submit_count == 0
    assert client.counters.flatten_submit_count == 0
    assert client.counters.cancel_request_count == 0
    assert client.counters.amend_request_count == 0
    assert client.counters.write_request_count == 0
    assert all(m == "GET" for m in result.methods_used)
    assert {c.method for c in transport.calls} == {"GET"}
    source = _OBSERVER_PATH.read_text(encoding="utf-8")
    for needle in (
        "post_entry_order",
        "post_flatten_order",
        "wire_send_enabled=True",
        "CanaryEntrySubmitPermitV1",
        "CanaryFlattenHttpPermitV1",
    ):
        assert needle not in source


def test_live_and_testnet_authorization_flags_unchanged() -> None:
    before = (LIVE_AUTHORIZED, LIVE_ENABLED, LIVE_ARMED, TESTNET_AUTHORIZED)
    transport = _transport()
    _observe(transport)
    after = (LIVE_AUTHORIZED, LIVE_ENABLED, LIVE_ARMED, TESTNET_AUTHORIZED)
    assert before == after == (False, False, False, False)


def test_observer_import_and_construction_do_not_use_network() -> None:
    source = _OBSERVER_PATH.read_text(encoding="utf-8")
    for needle in (
        "urlopen",
        "UrllibLiveCanaryTransportV1",
        "wire_send_enabled",
        "urllib.request",
    ):
        assert needle not in source
    transport = _transport()
    assert transport.venue_live_contact is False
    _observe(transport)
    assert transport.venue_live_contact is False


def test_present_evidence_fields_retained_absent_fields_not_invented() -> None:
    row = {
        "algoId": "keep-1",
        "instId": DEFAULT_INSTRUMENT_ID,
        "ordType": "conditional",
        "side": "sell",
        "sz": "1",
        "state": "pause",
    }
    transport = _transport({_endpoint("conditional,oco"): _ok_body([row])})
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_OBSERVED
    values = result.target_rows[0].to_dict()
    assert values["algoId"] == "keep-1"
    assert values["state"] == "pause"
    assert "tpTriggerPx" not in values
    assert "attachAlgoOrds" not in values


def test_header_factory_receives_full_url_and_get_has_no_body() -> None:
    seen: list[str] = []

    def factory(url: str) -> dict[str, str]:
        seen.append(url)
        return {"X-Test": "1"}

    transport = _transport()
    observe_category_c_open_algo_pending_v1(
        client=_client(transport),
        instrument_id=DEFAULT_INSTRUMENT_ID,
        header_factory=factory,
    )
    assert len(seen) == 3
    assert all(u.startswith("https://eea.okx.com/api/v5/trade/orders-algo-pending?") for u in seen)
    assert all(c.body_text == "" for c in transport.calls)
    assert all(c.headers.get("X-Test") == "1" for c in transport.calls)


def test_short_followup_page_after_full_page_terminates() -> None:
    first_rows = [_row(algoId=f"algo-{index:03d}") for index in range(CATEGORY_C_PAGE_LIMIT)]
    last_id = f"algo-{CATEGORY_C_PAGE_LIMIT - 1:03d}"
    transport = _transport(
        {
            _endpoint("conditional,oco"): _ok_body(first_rows),
            _endpoint("conditional,oco", after=last_id): _ok_body(
                [_row(algoId="algo-tail", ordType="oco")]
            ),
        }
    )
    result = _observe(transport)
    assert result.outcome is CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_OBSERVED
    q1_calls = [c for c in transport.calls if "ordType=conditional,oco" in c.endpoint]
    assert len(q1_calls) == 2
    assert _query(q1_calls[1].endpoint)["after"] == [last_id]
    assert result.target_rows[-1].to_dict()["algoId"] == "algo-tail"
    assert len(result.variants_completed) == 3
