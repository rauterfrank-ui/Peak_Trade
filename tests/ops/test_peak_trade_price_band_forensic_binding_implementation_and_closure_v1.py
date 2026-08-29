"""PRICE_BAND forensic binding and productive consumer v1.

No live trading. No POST. Public unsigned GET only. Historical BTC/testnet
51006 packs and percent-field reconstruction are not reused.
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
    ENDPOINT_PUBLIC_PRICE_LIMIT,
    GET_ENDPOINTS_PUBLIC,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_order_plan_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.price_band_consumer_v1 import (
    ENABLED_FALSE_POLICY,
    FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION,
    HISTORICAL_REUSE_PATH_EXISTS,
    MARKPX_SUBSTITUTION_USED,
    PERCENT_FIELD_RECONSTRUCTION_USED,
    PRICE_BAND_CONSUMER_BOUND,
    PRICE_BAND_FAIL_CLOSED_BOUND,
    ZERO_NORMALIZATION_PERFORMED,
    LiveCanaryPriceBandConsumerError,
    apply_fresh_price_band_pretrade_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.price_band_observation_v1 import (
    HISTORICAL_BTC_INSTRUMENT_ID,
    PRICE_BAND_COMPARISON_DOMAIN,
    PRICE_BAND_FRESHNESS_POLICY,
    PRICE_BAND_OUTPUT_DOMAIN,
    PRICE_BAND_TS_AGE_BOUND,
    LiveCanaryPriceBandObservationError,
    acquire_fresh_price_band_observation_from_payload_v1,
    public_price_limit_query_path_v1,
    select_price_band_field_for_side_v1,
    validate_fresh_price_band_observation_v1,
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
SPEC_PATH = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md"
)
PRIOR_MAX_AVAILABLE = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_MAX_AVAILABLE_OWNER_POLICY_ADJUDICATION_AND_CLOSURE_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ORDER_PLAN = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"
SUBMIT_TRANSPORT = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
CONSUMER = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/price_band_consumer_v1.py"
)
OBSERVATION = REPO_ROOT / (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/price_band_observation_v1.py"
)
OWNER_GO = "PEAK_TRADE_PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1"
ENDPOINT = public_price_limit_query_path_v1(instrument_id=DEFAULT_INSTRUMENT_ID)


def _payload(
    *,
    buy_lmt: str = "2.0000",
    sell_lmt: str = "0.0001",
    inst_id: str = DEFAULT_INSTRUMENT_ID,
    inst_type: str = "FUTURES",
    enabled: object = True,
    ts: str = "1725000000000",
) -> dict[str, object]:
    return {
        "code": "0",
        "msg": "",
        "data": [
            {
                "instId": inst_id,
                "instType": inst_type,
                "buyLmt": buy_lmt,
                "sellLmt": sell_lmt,
                "ts": ts,
                "enabled": enabled,
            }
        ],
    }


def _gate(**kwargs: object) -> dict[str, object]:
    body: dict[str, object] = {
        "pretrade_decision_id": "decision-a",
        "payload": _payload(),
        "instrument_id": DEFAULT_INSTRUMENT_ID,
        "side": "BUY",
        "planned_limit_px": "0.8209",
        "price_domain": PRICE_BAND_OUTPUT_DOMAIN,
        "http_status": 200,
        "endpoint": ENDPOINT,
        "get_performed": True,
        "historical_reuse": False,
        "auth_header_sent": False,
    }
    body.update(kwargs)
    return apply_fresh_price_band_pretrade_gate_v1(**body)  # type: ignore[arg-type]


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_enabled_true_valid_limits_pass() -> None:
    result = _gate()
    assert result["ok"] is True
    assert result["observation_class"] == "SUCCESS_NUMERIC"
    assert result["enabled"] is True
    assert result["buy_lmt"] == "2.0000"
    assert result["sell_lmt"] == "0.0001"


def test_buy_selects_buylmt_and_sell_selects_selllmt() -> None:
    buy = _gate(side="BUY")
    assert buy["price_band_field"] == "buyLmt"
    sell = _gate(side="SELL")
    assert sell["price_band_field"] == "sellLmt"
    assert select_price_band_field_for_side_v1(side="BUY") == "buyLmt"
    assert select_price_band_field_for_side_v1(side="SELL") == "sellLmt"


def test_buy_boundary_equal_accepted_and_above_fail_closed() -> None:
    assert _gate(side="BUY", planned_limit_px="2.0000")["ok"] is True
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="EXCEEDS_BUYLMT"):
        _gate(side="BUY", planned_limit_px="2.0001")


def test_sell_boundary_equal_accepted_and_below_fail_closed() -> None:
    assert _gate(side="SELL", planned_limit_px="0.0001")["ok"] is True
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="BELOW_SELLLMT"):
        _gate(side="SELL", planned_limit_px="0.00009")


def test_enabled_false_empty_limits_fail_closed_not_zero() -> None:
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="PRICE_BAND_NOT_ACTIVE"):
        _gate(payload=_payload(enabled=False, buy_lmt="", sell_lmt=""))
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="PRICE_BAND_NOT_ACTIVE"):
        _gate(payload=_payload(enabled="false", buy_lmt="", sell_lmt=""))
    assert ENABLED_FALSE_POLICY == "FAIL_CLOSED_NOT_ACTIVE"
    assert ZERO_NORMALIZATION_PERFORMED is False


def test_enabled_true_empty_selected_limit_fail_closed() -> None:
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="PRICE_BAND_FIELD_MISSING:buyLmt"):
        _gate(side="BUY", payload=_payload(buy_lmt=""))
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="PRICE_BAND_FIELD_MISSING:sellLmt"):
        _gate(side="SELL", payload=_payload(sell_lmt=""))


def test_malformed_nan_infinity_and_non_numeric_fail_closed() -> None:
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="NON_NUMERIC"):
        _gate(payload=_payload(buy_lmt="not-a-number"))
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="NON_NUMERIC"):
        _gate(payload=_payload(buy_lmt="NaN"))
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="NON_NUMERIC"):
        _gate(payload=_payload(buy_lmt="Infinity"))
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="NEGATIVE"):
        _gate(payload=_payload(buy_lmt="-1"))


def test_missing_selected_field_fail_closed() -> None:
    missing = _payload()
    del missing["data"][0]["buyLmt"]  # type: ignore[index]
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="PRICE_BAND_FIELD_MISSING:buyLmt"):
        _gate(payload=missing, side="BUY")
    null_row = _payload()
    null_row["data"][0]["sellLmt"] = None  # type: ignore[index]
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="PRICE_BAND_FIELD_NULL:sellLmt"):
        _gate(payload=null_row, side="SELL")


def test_mismatched_instid_and_unexpected_insttype_fail_closed() -> None:
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="INSTRUMENT_MISMATCH"):
        _gate(payload=_payload(inst_id="SUI-USD_UM_XPERP-999999"))
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="INST_TYPE_BINDING_MISMATCH"):
        _gate(payload=_payload(inst_type="SWAP"))


def test_stale_reuse_and_missing_ts_fail_closed_age_bound_unbound() -> None:
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="HISTORICAL_PRICE_BAND_REUSE"):
        _gate(historical_reuse=True)
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="HISTORICAL_BTC"):
        _gate(endpoint=ENDPOINT.replace(DEFAULT_INSTRUMENT_ID, HISTORICAL_BTC_INSTRUMENT_ID))
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="PRICE_BAND_FIELD_MISSING:ts"):
        _gate(payload=_payload(ts=""))
    assert PRICE_BAND_TS_AGE_BOUND == "UNBOUND"
    assert PRICE_BAND_FRESHNESS_POLICY == "FRESH_GET_PER_PRETRADE_DECISION"
    assert HISTORICAL_REUSE_PATH_EXISTS is False


def test_http_venue_empty_data_and_ambiguous_row_fail_closed() -> None:
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="FRESH_GET_NOT_PERFORMED"):
        _gate(get_performed=False)
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="PRICE_BAND_NETWORK_ERROR"):
        _gate(http_status=500)
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="PRICE_BAND_AUTH_ERROR"):
        _gate(http_status=401)
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="VENUE_CODE_UNSUCCESSFUL"):
        _gate(payload={"code": "1", "data": _payload()["data"]})
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="PRICE_BAND_DATA_MISSING"):
        _gate(payload={"code": "0", "data": []})
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="PRICE_BAND_AMBIGUOUS_TARGET_ROW"):
        _gate(
            payload={
                "code": "0",
                "data": [
                    _payload()["data"][0],
                    _payload()["data"][0],
                ],
            }
        )
    with pytest.raises(
        LiveCanaryPriceBandConsumerError, match="PUBLIC_PRICE_LIMIT_AUTH_HEADER_FORBIDDEN"
    ):
        _gate(auth_header_sent=True)
    assert FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION is True


def test_order_plan_wires_price_band_and_preserves_typed_quantity_domain() -> None:
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=_instruments_payload(),
        ticker_payload=TICKER,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="e50930dbb80fc31aacad5d5a1cf9a1fc2c6a883f",
        pretrade_decision_id="decision-plan-price-band",
        **_max_available_plan_kwargs(),
    )
    assert plan.quantity_domain == ORDER_PLAN_QTY_DOMAIN
    assert plan.limit_price == "0.8209"
    with pytest.raises(LiveCanaryOrderPlanError, match="PRICE_BAND_GATE"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=_instruments_payload(),
            ticker_payload=TICKER,
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            origin_main_sha="e50930dbb80fc31aacad5d5a1cf9a1fc2c6a883f",
            pretrade_decision_id="decision-plan-buy-exceeds",
            **_max_available_plan_kwargs(price_band_payload=_payload(buy_lmt="0.1000")),
        )
    assert PRICE_BAND_CONSUMER_BOUND is True
    assert PRICE_BAND_FAIL_CLOSED_BOUND is True
    assert PRICE_BAND_COMPARISON_DOMAIN != ORDER_PLAN_QTY_DOMAIN
    assert PRICE_BAND_OUTPUT_DOMAIN == "VENUE_LIMIT_PRICE"


def test_submit_transport_fail_closed_before_post_when_price_band_fails() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint[ENDPOINT_PUBLIC_PRICE_LIMIT] = (
        b'{"code":"0","data":[{"instId":"SUI-USD_UM_XPERP-310404","instType":"FUTURES",'
        b'"buyLmt":"0.0001","sellLmt":"0.0001","ts":"1","enabled":true}]}'
    )
    with pytest.raises(LiveCanarySubmitTransportError, match="PRICE_BAND"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)
    assert any(ENDPOINT_PUBLIC_PRICE_LIMIT in str(call.endpoint) for call in transport.calls)


def test_submit_transport_enabled_false_does_not_post() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint[ENDPOINT_PUBLIC_PRICE_LIMIT] = (
        b'{"code":"0","data":[{"instId":"SUI-USD_UM_XPERP-310404","instType":"FUTURES",'
        b'"buyLmt":"","sellLmt":"","ts":"1","enabled":false}]}'
    )
    with pytest.raises(LiveCanarySubmitTransportError, match="PRICE_BAND_NOT_ACTIVE"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)


def test_allowlist_public_and_no_trading() -> None:
    assert ENDPOINT_PUBLIC_PRICE_LIMIT in GET_ENDPOINTS_PUBLIC
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False
    consumer = CONSUMER.read_text(encoding="utf-8")
    assert "post_entry_order" not in consumer
    assert "apply_fresh_price_band_pretrade_gate_v1" in ORDER_PLAN.read_text(encoding="utf-8")
    assert "public_price_limit_query_path_v1" in SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    assert "maxPxLmtPct" not in consumer
    assert "markPx" not in consumer
    assert PERCENT_FIELD_RECONSTRUCTION_USED is False
    assert MARKPX_SUBSTITUTION_USED is False


def test_observation_bound_to_decision_and_price_domain() -> None:
    obs = acquire_fresh_price_band_observation_from_payload_v1(
        pretrade_decision_id="decision-one",
        payload=_payload(),
        observed_at_utc="2026-08-30T00:00:00.000000Z",
        endpoint=ENDPOINT,
        http_status=200,
        get_performed=True,
    )
    with pytest.raises(
        LiveCanaryPriceBandObservationError, match="OBSERVATION_DECISION_ID_MISMATCH"
    ):
        validate_fresh_price_band_observation_v1(
            obs,
            pretrade_decision_id="decision-two",
            instrument_id=DEFAULT_INSTRUMENT_ID,
            price_domain=PRICE_BAND_OUTPUT_DOMAIN,
        )
    with pytest.raises(LiveCanaryPriceBandConsumerError, match="PRICE_DOMAIN_INCOMPATIBLE"):
        _gate(price_domain=ORDER_PLAN_QTY_DOMAIN)
    query = public_price_limit_query_path_v1(instrument_id=DEFAULT_INSTRUMENT_ID)
    assert query.startswith(ENDPOINT_PUBLIC_PRICE_LIMIT)
    assert "tdMode=" not in query
    assert "px=" not in query
    assert "leverage=" not in query


def test_docs_and_master_pointer() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    prior = PRIOR_MAX_AVAILABLE.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert "PRICE_BAND_CANONICAL_DEFINITION=VENUE_NATIVE_PRICE_BAND" in spec
    assert "PRICE_BAND_ENDPOINT=/api/v5/public/price-limit" in spec
    assert "PRICE_BAND_BINDING_STATUS=PROVEN" in spec
    assert "PRICE_BAND_FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION" in spec
    assert "PRICE_BAND_TS_AGE_BOUND=UNBOUND" in spec
    assert "PRICE_BAND_ENABLED_FALSE_POLICY=FAIL_CLOSED_NOT_ACTIVE" in spec
    assert "PRICE_BAND_OUTPUT_DOMAIN=VENUE_LIMIT_PRICE" in spec
    assert "PRICE_BAND_SIDE_RULE=BUY_PX_LE_BUYLMT_SELL_PX_GE_SELLLMT" in spec
    assert "PRICE_BAND_AUTH_CLASS=PUBLIC_UNSIGNED_GET" in spec
    assert "NETWORK_AUTHENTICATED_GET_PERFORMED=false" in spec
    assert "PERCENT_FIELD_RECONSTRUCTION_USED=false" in spec
    assert "MARKPX_SUBSTITUTION_USED=false" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=LEVERAGE" in spec
    assert "PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1=true" in section
    assert "PEAK_TRADE_PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1" in mot
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=PRICE_BAND" in prior
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "TRADING_PERFORMED=false" in spec
    assert "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false" in spec
    assert "PRICE_BAND_GET_TIMESTAMP_UTC=2026-08-29T22:35:08.786566Z" in spec
    assert "PRICE_BAND_OBSERVATION_CLASS=SUCCESS_NUMERIC" in spec
    assert "PRICE_BAND_RAW_BUYLMT=0.7461" in spec
    assert "PRICE_BAND_GET_TIMESTAMP_UTC=2026-08-29T22:35:08.786566Z" in section
    assert "PRICE_BAND_OBSERVATION_CLASS=SUCCESS_NUMERIC" in section
