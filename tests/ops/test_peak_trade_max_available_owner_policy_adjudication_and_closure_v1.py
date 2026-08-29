"""MAX_AVAILABLE owner-policy adjudication and productive consumer v1.

No live trading. No POST. Historical max-avail-size / BTC windows are not reused.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.capability_11_9_live_canary_order_execution_v1.constants_v1 import (
    LIVE_EXECUTION_REACHABLE,
    TESTNET_EXECUTION_REACHABLE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_ACCOUNT_MAX_SIZE,
    GET_ENDPOINTS_PRIVATE,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    REUSED_BINDING_REST_HOST,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_available_consumer_v1 import (
    AVAILABLE_MARGIN_BINDING_STATUS,
    FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION,
    HISTORICAL_REUSE_PATH_EXISTS,
    MAX_AVAILABLE_CONSUMER_BOUND,
    MAX_AVAILABLE_FAIL_CLOSED_BOUND,
    LiveCanaryMaxAvailableConsumerError,
    apply_fresh_max_available_pretrade_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_available_observation_v1 import (
    HISTORICAL_BTC_INSTRUMENT_ID,
    HISTORICAL_SUPERSEDED_MAX_AVAIL_SIZE_PATH,
    MAX_AVAILABLE_COMPARISON_DOMAIN,
    LiveCanaryMaxAvailableObservationError,
    account_max_size_query_path_v1,
    acquire_fresh_max_available_observation_from_payload_v1,
    classify_max_available_observation_class_v1,
    select_max_available_field_for_side_v1,
    validate_fresh_max_available_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_order_plan_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_transport_v1 import (
    LiveCanarySubmitTransportError,
    run_canary_submit_transport_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    ORDER_PLAN_QTY_DOMAIN,
)
from tests.ops.test_peak_trade_max_size_fresh_observation_and_consumer_wiring_v1 import (
    _payload as _instruments_payload,
)
from tests.ops.test_section_11_13_5_canary_submit_transport_v1 import (
    TICKER,
    _assert_no_post,
    _fake_transport,
    _max_available_plan_kwargs,
    _transport_kwargs,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_MAX_AVAILABLE_OWNER_POLICY_ADJUDICATION_AND_CLOSURE_V1.md"
)
PRIOR_MAX_SIZE = (
    REPO_ROOT / "docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1.md"
)
PRIOR_6148 = REPO_ROOT / "docs/ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md"
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ORDER_PLAN = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"
SUBMIT_TRANSPORT = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
CONSUMER = (
    REPO_ROOT
    / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/max_available_consumer_v1.py"
)
MAX_SIZE_CONSUMER = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/max_size_consumer_v1.py"
)
OWNER_GO = "PEAK_TRADE_MAX_AVAILABLE_OWNER_POLICY_ADJUDICATION_AND_CLOSURE_V1"
ENDPOINT = account_max_size_query_path_v1(
    instrument_id=DEFAULT_INSTRUMENT_ID, td_mode="cross", px="0.8209"
)


def _payload(
    *, max_buy: str = "100", max_sell: str = "100", inst_id: str = DEFAULT_INSTRUMENT_ID
) -> dict[str, object]:
    return {
        "code": "0",
        "data": [{"instId": inst_id, "maxBuy": max_buy, "maxSell": max_sell}],
    }


def _gate(**kwargs: object) -> dict[str, object]:
    body: dict[str, object] = {
        "pretrade_decision_id": "decision-a",
        "payload": _payload(),
        "instrument_id": DEFAULT_INSTRUMENT_ID,
        "side": "BUY",
        "td_mode": "cross",
        "venue_contract_count": "1",
        "quantity_domain": ORDER_PLAN_QTY_DOMAIN,
        "http_status": 200,
        "endpoint": ENDPOINT,
        "px_sent": "0.8209",
        "get_performed": True,
        "historical_reuse": False,
    }
    body.update(kwargs)
    return apply_fresh_max_available_pretrade_gate_v1(**body)  # type: ignore[arg-type]


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_buy_selects_maxbuy_and_sell_selects_maxsell() -> None:
    buy = _gate(side="BUY")
    assert buy["max_available_field"] == "maxBuy"
    assert buy["ok"] is True
    sell = _gate(side="SELL")
    assert sell["max_available_field"] == "maxSell"
    assert select_max_available_field_for_side_v1(side="BUY") == "maxBuy"
    assert select_max_available_field_for_side_v1(side="SELL") == "maxSell"


def test_limit_and_market_share_side_selector() -> None:
    assert select_max_available_field_for_side_v1(side="BUY") == "maxBuy"
    buy_limit = _gate(side="BUY")
    buy_again = _gate(side="BUY")
    assert buy_limit["max_available_field"] == buy_again["max_available_field"] == "maxBuy"


def test_quantity_lt_eq_gt_and_zero_max() -> None:
    assert _gate(venue_contract_count="1", payload=_payload(max_buy="100"))["ok"] is True
    assert _gate(venue_contract_count="100", payload=_payload(max_buy="100"))["ok"] is True
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="EXCEEDS_MAXBUY"):
        _gate(venue_contract_count="101", payload=_payload(max_buy="100"))
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="EXCEEDS_MAXBUY"):
        _gate(venue_contract_count="1", payload=_payload(max_buy="0"))


def test_missing_and_malformed_fields_fail_closed() -> None:
    missing = _payload()
    del missing["data"][0]["maxBuy"]  # type: ignore[index]
    with pytest.raises(
        LiveCanaryMaxAvailableConsumerError, match="MAX_AVAILABLE_FIELD_MISSING:maxBuy"
    ):
        _gate(payload=missing, side="BUY")
    null_row = _payload()
    null_row["data"][0]["maxSell"] = None  # type: ignore[index]
    with pytest.raises(
        LiveCanaryMaxAvailableConsumerError, match="MAX_AVAILABLE_FIELD_NULL:maxSell"
    ):
        _gate(payload=null_row, side="SELL")
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="NON_NUMERIC"):
        _gate(payload=_payload(max_buy="not-a-number"))
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="NON_NUMERIC"):
        _gate(payload=_payload(max_buy="NaN"))
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="NON_NUMERIC"):
        _gate(payload=_payload(max_buy="Infinity"))
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="NEGATIVE"):
        _gate(payload=_payload(max_buy="-1"))


def test_http_and_venue_code_and_missing_get_fail_closed() -> None:
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="FRESH_GET_NOT_PERFORMED"):
        _gate(get_performed=False)
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="MAX_AVAILABLE_NETWORK_ERROR"):
        _gate(http_status=500)
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="MAX_AVAILABLE_AUTH_ERROR"):
        _gate(http_status=401)
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="VENUE_CODE_UNSUCCESSFUL"):
        _gate(
            payload={
                "code": "1",
                "data": [{"instId": DEFAULT_INSTRUMENT_ID, "maxBuy": "0", "maxSell": "0"}],
            }
        )
    with pytest.raises(
        LiveCanaryMaxAvailableConsumerError, match="MAX_AVAILABLE_AUTH_HEADER_REQUIRED"
    ):
        _gate(auth_header_sent=False)
    assert FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION is True


def test_stale_reuse_and_wrong_endpoint_and_instrument_fail_closed() -> None:
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="HISTORICAL_MAX_AVAILABLE_REUSE"):
        _gate(historical_reuse=True)
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="SUPERSEDED_MAX_AVAIL_SIZE"):
        _gate(
            endpoint=HISTORICAL_SUPERSEDED_MAX_AVAIL_SIZE_PATH + "?instId=" + DEFAULT_INSTRUMENT_ID
        )
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="HISTORICAL_BTC"):
        _gate(endpoint=ENDPOINT.replace(DEFAULT_INSTRUMENT_ID, HISTORICAL_BTC_INSTRUMENT_ID))
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="INSTRUMENT_MISMATCH"):
        _gate(payload=_payload(inst_id="SUI-USD_UM_XPERP-999999"))
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="MAX_AVAILABLE_LEVERAGE_QUERY"):
        _gate(endpoint=ENDPOINT + "&leverage=3")
    assert HISTORICAL_REUSE_PATH_EXISTS is False


def test_observation_bound_to_decision_and_typed_domain() -> None:
    obs = acquire_fresh_max_available_observation_from_payload_v1(
        pretrade_decision_id="decision-one",
        payload=_payload(),
        td_mode="cross",
        px_sent="0.8209",
        observed_at_utc="2026-08-29T21:30:00.000000Z",
        endpoint=ENDPOINT,
        http_status=200,
        get_performed=True,
    )
    with pytest.raises(
        LiveCanaryMaxAvailableObservationError, match="OBSERVATION_DECISION_ID_MISMATCH"
    ):
        validate_fresh_max_available_observation_v1(
            obs,
            pretrade_decision_id="decision-two",
            instrument_id=DEFAULT_INSTRUMENT_ID,
            quantity_domain=ORDER_PLAN_QTY_DOMAIN,
        )
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="QUANTITY_DOMAIN_INCOMPATIBLE"):
        _gate(quantity_domain="NOTIONAL")
    assert MAX_AVAILABLE_COMPARISON_DOMAIN == ORDER_PLAN_QTY_DOMAIN


def test_order_plan_wires_max_available_and_preserves_max_size() -> None:
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=_instruments_payload(),
        ticker_payload=TICKER,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="ef6d555bee94a8a6ccce78bd94b1742328764c97",
        pretrade_decision_id="decision-plan-max-available",
        **_max_available_plan_kwargs(),
    )
    assert plan.quantity_domain == ORDER_PLAN_QTY_DOMAIN
    assert plan.quantity == "1"
    with pytest.raises(LiveCanaryOrderPlanError, match="MAX_AVAILABLE_GATE"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=_instruments_payload(),
            ticker_payload=TICKER,
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            origin_main_sha="ef6d555bee94a8a6ccce78bd94b1742328764c97",
            pretrade_decision_id="decision-plan-zero-avail",
            **_max_available_plan_kwargs(max_available_payload=_payload(max_buy="0")),
        )
    with pytest.raises(LiveCanaryOrderPlanError, match="MAX_SIZE_GATE"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=_instruments_payload(maxLmtSz="0"),
            ticker_payload=TICKER,
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            origin_main_sha="ef6d555bee94a8a6ccce78bd94b1742328764c97",
            pretrade_decision_id="decision-plan-zero-max-size",
            **_max_available_plan_kwargs(),
        )
    assert MAX_AVAILABLE_CONSUMER_BOUND is True
    assert MAX_AVAILABLE_FAIL_CLOSED_BOUND is True
    assert AVAILABLE_MARGIN_BINDING_STATUS == "UNBOUND"


def test_submit_transport_fail_closed_before_post_when_max_available_zero() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint[ENDPOINT_ACCOUNT_MAX_SIZE] = (
        b'{"code":"0","data":[{"instId":"SUI-USD_UM_XPERP-310404","maxBuy":"0","maxSell":"0"}]}'
    )
    with pytest.raises(LiveCanarySubmitTransportError, match="MAX_AVAILABLE_GATE"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)
    assert any(ENDPOINT_ACCOUNT_MAX_SIZE in str(call.endpoint) for call in transport.calls)


def test_allowlist_and_no_trading() -> None:
    assert ENDPOINT_ACCOUNT_MAX_SIZE in GET_ENDPOINTS_PRIVATE
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False
    assert "post_entry_order" not in CONSUMER.read_text(encoding="utf-8")
    assert "apply_fresh_max_size_pretrade_gate_v1" in MAX_SIZE_CONSUMER.read_text(encoding="utf-8")
    assert "maxBuy" in CONSUMER.read_text(encoding="utf-8")
    assert "maxAvailSize" not in ORDER_PLAN.read_text(encoding="utf-8")
    assert "maxAvailSize" not in SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    transport = SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    assert "account_max_size_query_path_v1" in transport
    assert "apply_fresh_max_available_pretrade_gate_v1" in ORDER_PLAN.read_text(encoding="utf-8")


def test_docs_and_master_pointer() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    prior = PRIOR_MAX_SIZE.read_text(encoding="utf-8")
    unit = PRIOR_6148.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert "MAX_AVAILABLE_CANONICAL_DEFINITION=VENUE_ACCOUNT_MAXIMUM_ORDER_QUANTITY" in spec
    assert "MAX_AVAILABLE_ENDPOINT=/api/v5/account/max-size" in spec
    assert "MAX_AVAILABLE_BINDING_STATUS=PROVEN" in spec
    assert "PREVIOUS_BINDING_DISPOSITION=SUPERSEDED_BY_OWNER_ADJUDICATION" in spec
    assert "AVAILABLE_MARGIN_BINDING_STATUS=UNBOUND" in spec
    assert "MAX_AVAILABLE_FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION" in spec
    assert "MAX_AVAILABLE_OWNER_POLICY_ADJUDICATION_AND_CLOSURE_V1=true" in section
    assert "PEAK_TRADE_MAX_AVAILABLE_OWNER_POLICY_ADJUDICATION_AND_CLOSURE_V1" in mot
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MAX_AVAILABLE" in prior
    assert "OFFICIAL_MAX_AVAIL_SURFACE=GET &#47;api&#47;v5&#47;account&#47;max-avail-size" in unit
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "TRADING_PERFORMED=false" in spec
    assert "MAX_AVAILABLE_PX_SOURCE=ORDER_PLAN_LIMIT_PX" in spec
    assert "MAX_AVAILABLE_LEVERAGE_REQUEST_POLICY=OMIT" in spec
    assert "ACCOUNT_MODE=UNPROVEN" in spec
    assert "ZERO_NORMALIZATION_PERFORMED=false" in spec
    assert "MAX_AVAIL_SIZE_FALLBACK_USED=false" in spec
    assert "AVAILABLE_MARGIN_CLOSED_BY_THIS_SLICE=false" in spec
    assert "MAX_AVAILABLE_GET_TIMESTAMP_UTC=2026-08-29T22:02:34.509031Z" in spec
    assert "MAX_AVAILABLE_OBSERVATION_CLASS=SUCCESS_NUMERIC" in spec
    assert "MAX_AVAILABLE_VALIDATED_VALUE=0" in spec
    assert "MAX_AVAILABLE_GET_TIMESTAMP_UTC=2026-08-29T22:02:34.509031Z" in section
    assert "MAX_AVAILABLE_OBSERVATION_CLASS=SUCCESS_NUMERIC" in section


def test_unsupported_and_malformed_are_not_normalized_to_zero() -> None:
    with pytest.raises(
        LiveCanaryMaxAvailableConsumerError, match="MAX_AVAILABLE_BLOCKED_BY_ACCOUNT_MODE_SUPPORT"
    ):
        _gate(
            payload={
                "code": "51000",
                "msg": "Calculation of maximum buy/sell/open amount is not supported for cross-mode derivatives under Portfolio Margin account",
                "data": [{"instId": DEFAULT_INSTRUMENT_ID, "maxBuy": "0", "maxSell": "0"}],
            }
        )
    with pytest.raises(
        LiveCanaryMaxAvailableConsumerError, match="MAX_AVAILABLE_MALFORMED|VENUE_CODE"
    ):
        _gate(
            payload={
                "code": "1",
                "msg": "request failed",
                "data": [{"maxBuy": "0", "maxSell": "0"}],
            }
        )
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="EXCEEDS_MAXBUY"):
        _gate(payload=_payload(max_buy="0", max_sell="10"), venue_contract_count="1")


def test_zero_success_is_distinct_from_unsupported() -> None:
    with pytest.raises(LiveCanaryMaxAvailableConsumerError, match="EXCEEDS_MAXBUY"):
        _gate(payload=_payload(max_buy="0"), venue_contract_count="1")
    result = classify_max_available_observation_class_v1(
        get_performed=True, http_status=200, payload=_payload(max_buy="0")
    )
    assert result == "SUCCESS_NUMERIC"
    unsupported = classify_max_available_observation_class_v1(
        get_performed=True,
        http_status=200,
        payload={
            "code": "1",
            "msg": "not supported in Portfolio Margin",
            "data": [{"maxBuy": "0", "maxSell": "0"}],
        },
    )
    assert unsupported == "UNSUPPORTED_ACCOUNT_MODE"


def test_limit_px_bound_and_leverage_omitted_and_market_omits_px() -> None:
    limit_ep = account_max_size_query_path_v1(
        instrument_id=DEFAULT_INSTRUMENT_ID, td_mode="cross", px="0.8209", order_type="LIMIT"
    )
    assert "px=0.8209" in limit_ep
    assert "leverage=" not in limit_ep
    market_ep = account_max_size_query_path_v1(
        instrument_id=DEFAULT_INSTRUMENT_ID, td_mode="cross", order_type="MARKET"
    )
    assert "px=" not in market_ep
    with pytest.raises(
        LiveCanaryMaxAvailableObservationError, match="MAX_AVAILABLE_LIMIT_PX_REQUIRED"
    ):
        account_max_size_query_path_v1(
            instrument_id=DEFAULT_INSTRUMENT_ID, td_mode="cross", order_type="LIMIT"
        )
    market_obs = acquire_fresh_max_available_observation_from_payload_v1(
        pretrade_decision_id="decision-market",
        payload=_payload(),
        td_mode="cross",
        px_sent="",
        observed_at_utc="2026-08-29T21:30:00.000000Z",
        endpoint=market_ep,
        http_status=200,
        get_performed=True,
        order_type="MARKET",
    )
    assert market_obs.px_sent == ""
    assert "px=" not in market_obs.endpoint
    passed = _gate()
    assert passed["px_source"] == "ORDER_PLAN_LIMIT_PX"
    assert passed["leverage_request_policy"] == "OMIT"
    assert passed["account_mode"] == "UNPROVEN"
    assert passed["default_tdmode_cross_is_not_account_mode_proof"] is True
    assert passed["zero_normalization_performed"] is False
    assert passed["max_avail_size_fallback_used"] is False
    assert passed["available_margin_closed_by_this_slice"] is False
    assert "leverage=" not in SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    assert HISTORICAL_SUPERSEDED_MAX_AVAIL_SIZE_PATH not in SUBMIT_TRANSPORT.read_text(
        encoding="utf-8"
    )


def test_submit_transport_unsupported_account_mode_does_not_post() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint[ENDPOINT_ACCOUNT_MAX_SIZE] = (
        b'{"code":"1","msg":"not supported for cross-mode derivatives under Portfolio Margin","data":[{"instId":"SUI-USD_UM_XPERP-310404","maxBuy":"0","maxSell":"0"}]}'
    )
    with pytest.raises(LiveCanarySubmitTransportError, match="MAX_AVAILABLE"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)
