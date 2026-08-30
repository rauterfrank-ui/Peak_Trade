"""AVAILABLE_MARGIN forensic binding and productive consumer v1.

No live trading. No POST. Authenticated GET only. details.availEq is not
availBal, not account-level availEq, not max-size, and not max-avail-size.
USD is not USDC. Empty details are not zero.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.capability_11_9_live_canary_order_execution_v1.constants_v1 import (
    LIVE_EXECUTION_REACHABLE,
    TESTNET_EXECUTION_REACHABLE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_consumer_v1 import (
    AVAILABLE_MARGIN_CONSUMER_BOUND,
    AVAILABLE_MARGIN_FAIL_CLOSED_BOUND,
    EMPTY_RESPONSE_USED_AS_ZERO_AUTHORITY,
    FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION,
    HISTORICAL_REUSE_PATH_EXISTS,
    LEVERAGE_USED_AS_AVAILABLE_MARGIN_AUTHORITY,
    MARGIN_MODE_USED_AS_NUMERIC_AVAILABLE_MARGIN_AUTHORITY,
    MAX_SIZE_USED_AS_AVAILABLE_MARGIN_AUTHORITY,
    POS_MODE_USED_AS_AVAILABLE_MARGIN_AUTHORITY,
    USD_USDC_EQUIVALENCE_ASSUMED_CONSUMER,
    ZERO_NORMALIZATION_PERFORMED,
    LiveCanaryAvailableMarginConsumerError,
    apply_fresh_available_margin_pretrade_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    ACCOUNT_AVAIL_EQ_IS_NOT_AUTHORITY,
    AVAIL_BAL_IS_NOT_AUTHORITY,
    AVAILABLE_MARGIN_AUTH_CLASS,
    AVAILABLE_MARGIN_COMPARISON_DOMAIN,
    AVAILABLE_MARGIN_CONSUMER_SCOPE,
    AVAILABLE_MARGIN_FRESHNESS_POLICY,
    AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY,
    AVAILABLE_MARGIN_OUTPUT_DOMAIN,
    AVAILABLE_MARGIN_REQUIRED_CCY,
    AVAILABLE_MARGIN_REQUIRED_TD_MODE,
    AVAILABLE_MARGIN_SEMANTIC_CLASS,
    AVAILABLE_MARGIN_TS_AGE_BOUND,
    AVAILABLE_MARGIN_UNIT,
    AVAILABLE_MARGIN_VENUE_SCOPE,
    AVAIL_EQ_STATUS_OBSERVED,
    EMPTY_DATA_IS_NOT_ZERO,
    HISTORICAL_BTC_INSTRUMENT_ID,
    USD_USDC_EQUIVALENCE_ASSUMED,
    LiveCanaryAvailableMarginObservationError,
    account_balance_query_path_v1,
    acquire_fresh_available_margin_observation_from_payload_v1,
    utc_now_iso_v1,
    validate_fresh_available_margin_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_TD_MODE,
    ENDPOINT_ACCOUNT_BALANCE,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS,
    GET_ENDPOINTS_PRIVATE,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    POST_ENDPOINTS_GATED,
    SETTLEMENT_ACCOUNT_TRUTH,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.leverage_observation_v1 import (
    LEVERAGE_OUTPUT_DOMAIN,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.margin_mode_observation_v1 import (
    MARGIN_MODE_OUTPUT_DOMAIN,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_flatten_order_plan_v1,
    build_minimum_valid_canary_order_plan_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1 import (
    POS_MODE_OUTPUT_DOMAIN,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.price_band_observation_v1 import (
    PRICE_BAND_OUTPUT_DOMAIN,
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
    AVAILABLE_MARGIN,
    TICKER,
    _assert_no_post,
    _fake_transport,
    _max_available_plan_kwargs,
    _transport_kwargs,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_AVAILABLE_MARGIN_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md"
)
PRIOR_MARGIN_MODE = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_MARGIN_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ORDER_PLAN = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"
SUBMIT_TRANSPORT = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
CONSUMER = REPO_ROOT / (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/available_margin_consumer_v1.py"
)
OBSERVATION = REPO_ROOT / (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/available_margin_observation_v1.py"
)
OWNER_GO = "PEAK_TRADE_AVAILABLE_MARGIN_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1"
ENDPOINT = account_balance_query_path_v1()


def _payload(
    *,
    usdc_avail_eq: str = "10.25",
    usdc_avail_bal: str = "10.10",
    account_avail_eq: str = "12.5",
    extra_details: list[dict[str, object]] | None = None,
    omit_usdc: bool = False,
) -> dict[str, object]:
    details: list[dict[str, object]] = []
    if not omit_usdc:
        details.append(
            {
                "ccy": "USDC",
                "availEq": usdc_avail_eq,
                "availBal": usdc_avail_bal,
                "eq": "10.25",
                "cashBal": "10.25",
                "uTime": "1788042908790",
            }
        )
    if extra_details:
        details.extend(extra_details)
    return {
        "code": "0",
        "msg": "",
        "data": [
            {
                "adjEq": "12.5",
                "availEq": account_avail_eq,
                "totalEq": "12.5",
                "uTime": "1788042908790",
                "details": details,
            }
        ],
    }


def _gate(**kwargs: object) -> dict[str, object]:
    body: dict[str, object] = {
        "pretrade_decision_id": "decision-a",
        "payload": _payload(),
        "instrument_id": DEFAULT_INSTRUMENT_ID,
        "available_margin_domain": AVAILABLE_MARGIN_OUTPUT_DOMAIN,
        "planned_td_mode": "cross",
        "http_status": 200,
        "endpoint": ENDPOINT,
        "get_performed": True,
        "historical_reuse": False,
        "auth_header_sent": True,
    }
    body.update(kwargs)
    return apply_fresh_available_margin_pretrade_gate_v1(**body)  # type: ignore[arg-type]


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_usdc_detail_avail_eq_is_authority() -> None:
    result = _gate()
    assert result["ok"] is True
    assert result["observation_class"] == "SUCCESS_NUMERIC"
    assert result["selected_ccy"] == "USDC"
    assert result["avail_eq_raw"] == "10.25"
    assert result["avail_eq"] == "10.25"
    assert result["avail_eq_status"] == AVAIL_EQ_STATUS_OBSERVED
    assert result["account_avail_eq_raw"] == "12.5"
    assert result["account_avail_eq_raw"] != result["avail_eq_raw"]
    assert result["selected_avail_bal_raw"] == "10.10"
    assert result["selected_avail_bal_raw"] != result["avail_eq_raw"]
    assert result["semantic_class"] == AVAILABLE_MARGIN_SEMANTIC_CLASS
    assert result["unit"] == AVAILABLE_MARGIN_UNIT
    assert result["required_ccy"] == SETTLEMENT_ACCOUNT_TRUTH == "USDC"
    assert result["instrument_settle_ccy"] == "USD"
    assert result["usd_usdc_equivalence_assumed"] is False
    assert ACCOUNT_AVAIL_EQ_IS_NOT_AUTHORITY is True
    assert AVAIL_BAL_IS_NOT_AUTHORITY is True


def test_zero_avail_eq_is_numeric_not_empty() -> None:
    result = _gate(payload=_payload(usdc_avail_eq="0"))
    assert result["avail_eq_raw"] == "0"
    assert result["avail_eq"] == "0"
    assert EMPTY_RESPONSE_USED_AS_ZERO_AUTHORITY is False
    assert EMPTY_DATA_IS_NOT_ZERO is True


def test_empty_details_are_not_zero() -> None:
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError,
        match="AVAILABLE_MARGIN_USDC_AVAILEQ_NOT_OBSERVED",
    ):
        _gate(payload=_payload(omit_usdc=True))
    assert EMPTY_DATA_IS_NOT_ZERO is True
    assert EMPTY_RESPONSE_USED_AS_ZERO_AUTHORITY is False


def test_empty_avail_eq_is_not_zero() -> None:
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError,
        match="AVAILABLE_MARGIN_FIELD_EMPTY:details.availEq",
    ):
        _gate(payload=_payload(usdc_avail_eq=""))


def test_missing_avail_eq_field_fails_closed() -> None:
    payload = _payload()
    details = payload["data"][0]["details"][0]  # type: ignore[index]
    del details["availEq"]
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError,
        match="AVAILABLE_MARGIN_FIELD_MISSING:details.availEq",
    ):
        _gate(payload=payload)


def test_stale_historical_reuse_fails_closed() -> None:
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError,
        match="HISTORICAL_AVAILABLE_MARGIN_REUSE_FORBIDDEN",
    ):
        _gate(historical_reuse=True)


def test_usd_row_is_not_usdc_authority() -> None:
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError,
        match="AVAILABLE_MARGIN_USDC_AVAILEQ_NOT_OBSERVED",
    ):
        _gate(
            payload=_payload(
                omit_usdc=True,
                extra_details=[
                    {
                        "ccy": "USD",
                        "availEq": "10.25",
                        "availBal": "10.10",
                    }
                ],
            )
        )
    assert USD_USDC_EQUIVALENCE_ASSUMED is False
    assert USD_USDC_EQUIVALENCE_ASSUMED_CONSUMER is False
    assert AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY == "USD"
    assert AVAILABLE_MARGIN_REQUIRED_CCY == "USDC"


def test_usd_contextual_row_does_not_replace_usdc() -> None:
    result = _gate(
        payload=_payload(extra_details=[{"ccy": "USD", "availEq": "99", "availBal": "98"}])
    )
    assert result["selected_ccy"] == "USDC"
    assert result["avail_eq_raw"] == "10.25"
    assert "USD" in result["other_detail_ccys"]
    assert result["usd_usdc_equivalence_assumed"] is False


def test_isolated_planned_tdmode_fails_closed() -> None:
    with pytest.raises(LiveCanaryAvailableMarginConsumerError, match="AVAILABLE_MARGIN_TD_MODE"):
        _gate(planned_td_mode="isolated")


def test_missing_get_fails_closed() -> None:
    with pytest.raises(LiveCanaryAvailableMarginConsumerError, match="FRESH_GET_NOT_PERFORMED"):
        _gate(get_performed=False)
    assert FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION is True


def test_query_grammar_is_none() -> None:
    assert account_balance_query_path_v1() == ENDPOINT_ACCOUNT_BALANCE
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError, match="AVAILABLE_MARGIN_QUERY_FORBIDDEN"
    ):
        _gate(endpoint=f"{ENDPOINT}?ccy=USDC")
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError, match="AVAILABLE_MARGIN_QUERY_FORBIDDEN"
    ):
        _gate(endpoint=f"{ENDPOINT}?ccy=USD")


def test_max_size_and_max_avail_cannot_be_source() -> None:
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError,
        match="AVAILABLE_MARGIN_RECONSTRUCTION_SOURCE_FORBIDDEN",
    ):
        _gate(endpoint="/api/v5/account/max-size")
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError,
        match="AVAILABLE_MARGIN_RECONSTRUCTION_SOURCE_FORBIDDEN",
    ):
        _gate(endpoint="/api/v5/account/max-avail-size")
    assert MAX_SIZE_USED_AS_AVAILABLE_MARGIN_AUTHORITY is False


def test_wrong_type_and_malformed_fail_closed() -> None:
    with pytest.raises(LiveCanaryAvailableMarginConsumerError, match="AVAILABLE_MARGIN"):
        _gate(payload={"code": "0", "data": {"availEq": "10"}})
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError, match="AVAILABLE_MARGIN_FIELD_NON_NUMERIC"
    ):
        _gate(payload=_payload(usdc_avail_eq="not-a-number"))
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError, match="AVAILABLE_MARGIN_FIELD_NEGATIVE"
    ):
        _gate(payload=_payload(usdc_avail_eq="-1"))


def test_auth_and_venue_failure() -> None:
    with pytest.raises(LiveCanaryAvailableMarginConsumerError, match="AVAILABLE_MARGIN_AUTH_ERROR"):
        _gate(http_status=401)
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError, match="AVAILABLE_MARGIN_VENUE_CODE_UNSUCCESSFUL"
    ):
        _gate(payload={"code": "1", "data": []})


def test_historical_btc_cannot_substitute() -> None:
    with pytest.raises(LiveCanaryAvailableMarginConsumerError, match="HISTORICAL_BTC_INSTRUMENT"):
        _gate(instrument_id=HISTORICAL_BTC_INSTRUMENT_ID)
    assert HISTORICAL_REUSE_PATH_EXISTS is False


def test_typed_domain_not_mixed() -> None:
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError, match="AVAILABLE_MARGIN_DOMAIN_INCOMPATIBLE"
    ):
        _gate(available_margin_domain=ORDER_PLAN_QTY_DOMAIN)
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError, match="AVAILABLE_MARGIN_DOMAIN_INCOMPATIBLE"
    ):
        _gate(available_margin_domain=PRICE_BAND_OUTPUT_DOMAIN)
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError, match="AVAILABLE_MARGIN_DOMAIN_INCOMPATIBLE"
    ):
        _gate(available_margin_domain=LEVERAGE_OUTPUT_DOMAIN)
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError, match="AVAILABLE_MARGIN_DOMAIN_INCOMPATIBLE"
    ):
        _gate(available_margin_domain=POS_MODE_OUTPUT_DOMAIN)
    with pytest.raises(
        LiveCanaryAvailableMarginConsumerError, match="AVAILABLE_MARGIN_DOMAIN_INCOMPATIBLE"
    ):
        _gate(available_margin_domain=MARGIN_MODE_OUTPUT_DOMAIN)
    assert AVAILABLE_MARGIN_OUTPUT_DOMAIN == "CURRENCY_SCOPED_AVAILABLE_EQUITY"
    assert AVAILABLE_MARGIN_COMPARISON_DOMAIN != ORDER_PLAN_QTY_DOMAIN
    assert ZERO_NORMALIZATION_PERFORMED is False


def test_order_plan_wires_available_margin_and_preserves_typed_quantity_domain() -> None:
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=_instruments_payload(),
        ticker_payload=TICKER,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="bb63f3ba07e7d441d7c92f387e195298a5181a2b",
        pretrade_decision_id="decision-plan-available-margin",
        **_max_available_plan_kwargs(),
    )
    assert plan.quantity_domain == ORDER_PLAN_QTY_DOMAIN
    assert plan.td_mode == "cross"
    assert plan.venue_native_payload["tdMode"] == "cross"
    with pytest.raises(LiveCanaryOrderPlanError, match="AVAILABLE_MARGIN_GATE"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=_instruments_payload(),
            ticker_payload=TICKER,
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            origin_main_sha="bb63f3ba07e7d441d7c92f387e195298a5181a2b",
            pretrade_decision_id="decision-plan-available-margin-missing",
            **_max_available_plan_kwargs(available_margin_get_performed=False),
        )
    assert AVAILABLE_MARGIN_CONSUMER_BOUND is True
    assert AVAILABLE_MARGIN_FAIL_CLOSED_BOUND is True


def test_flatten_td_mode_remains_canonical_cross() -> None:
    payload = {
        "code": "0",
        "data": [{"instId": DEFAULT_INSTRUMENT_ID, "pos": "1", "mgnMode": "cross"}],
    }
    plan = build_minimum_valid_canary_flatten_order_plan_v1(
        positions_payload=payload,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="bb63f3ba07e7d441d7c92f387e195298a5181a2b",
    )
    assert plan.td_mode == "cross"
    assert AVAILABLE_MARGIN_REQUIRED_TD_MODE == DEFAULT_TD_MODE == "cross"


def test_submit_transport_fail_closed_before_post_when_usdc_row_absent() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint[ENDPOINT_ACCOUNT_BALANCE] = (
        b'{"code":"0","data":[{"availEq":"","details":[],"uTime":"1"}]}'
    )
    with pytest.raises(LiveCanarySubmitTransportError, match="AVAILABLE_MARGIN"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)


def test_submit_transport_uses_balance_get_and_does_not_normalize_usd() -> None:
    transport = _fake_transport()
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["ok"] is True
    assert any(ENDPOINT_ACCOUNT_BALANCE in str(call.endpoint) for call in transport.calls)
    assert all("ccy=" not in str(call.endpoint) for call in transport.calls)


def test_allowlist_private_and_no_trading() -> None:
    assert ENDPOINT_ACCOUNT_BALANCE in GET_ENDPOINTS_PRIVATE
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False
    assert ENDPOINT_ACCOUNT_BALANCE not in POST_ENDPOINTS_GATED
    assert any("set-" in marker for marker in FORBIDDEN_MUTATION_ENDPOINT_MARKERS)


def test_observation_validate_decision_mismatch() -> None:
    obs = acquire_fresh_available_margin_observation_from_payload_v1(
        pretrade_decision_id="decision-one",
        payload=_payload(),
        instrument_id=DEFAULT_INSTRUMENT_ID,
        planned_td_mode="cross",
        observed_at_utc=utc_now_iso_v1(),
        endpoint=ENDPOINT,
        http_status=200,
        get_performed=True,
    )
    with pytest.raises(
        LiveCanaryAvailableMarginObservationError, match="OBSERVATION_DECISION_ID_MISMATCH"
    ):
        validate_fresh_available_margin_observation_v1(
            obs,
            pretrade_decision_id="decision-two",
            instrument_id=DEFAULT_INSTRUMENT_ID,
            available_margin_domain=AVAILABLE_MARGIN_OUTPUT_DOMAIN,
            planned_td_mode="cross",
        )
    assert obs.venue_scope == AVAILABLE_MARGIN_VENUE_SCOPE
    assert obs.consumer_scope == AVAILABLE_MARGIN_CONSUMER_SCOPE
    assert AVAILABLE_MARGIN_AUTH_CLASS == "AUTHENTICATED_PRIVATE_GET"
    assert AVAILABLE_MARGIN_TS_AGE_BOUND == "UNBOUND"
    assert AVAILABLE_MARGIN_FRESHNESS_POLICY == "FRESH_GET_PER_PRETRADE_DECISION"
    assert POS_MODE_USED_AS_AVAILABLE_MARGIN_AUTHORITY is False
    assert MARGIN_MODE_USED_AS_NUMERIC_AVAILABLE_MARGIN_AUTHORITY is False
    assert LEVERAGE_USED_AS_AVAILABLE_MARGIN_AUTHORITY is False


def test_docs_and_master_pointer() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    prior = PRIOR_MARGIN_MODE.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert (
        "AVAILABLE_MARGIN_CANONICAL_DEFINITION="
        "CURRENCY_SCOPED_CROSS_MARGIN_FREE_MARGIN_DETAILS_AVAILEQ" in spec
    )
    assert "AVAILABLE_MARGIN_ENDPOINT=/api/v5/account/balance" in spec
    assert "AVAILABLE_MARGIN_BINDING_STATUS=PROVEN" in spec
    assert "AVAILABLE_MARGIN_REQUIRED_CCY=USDC" in spec
    assert "AVAILABLE_MARGIN_INSTRUMENT_SETTLE_CCY=USD" in spec
    assert "USD_USDC_EQUIVALENCE_ASSUMED=false" in spec
    assert "ACCOUNT_AVAIL_EQ_ROLE=CONTEXTUAL_USD_DENOMINATED_ACCOUNT_AVAILABLE_EQUITY" in spec
    assert "ACCOUNT_AVAIL_BAL_ROLE=NOT_CROSS_FUTURES_FREE_MARGIN" in spec
    assert "MAX_AVAILABLE_ROLE=VENUE_ACCOUNT_MAXIMUM_ORDER_QUANTITY_NOT_THIS_EDGE" in spec
    assert "MAX_SIZE_USED_AS_AVAILABLE_MARGIN_AUTHORITY=false" in spec
    assert "EMPTY_RESPONSE_USED_AS_ZERO_AUTHORITY=false" in spec
    assert "AVAILABLE_MARGIN_FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION" in spec
    assert "EXECUTION_TD_MODE=cross" in spec
    assert "AVAILABLE_MARGIN_EXECUTION_TD_MODE_CONSISTENT=true" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=INSTRUMENT_STATE" in spec
    assert "AVAILABLE_MARGIN_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1=true" in section
    assert "PEAK_TRADE_AVAILABLE_MARGIN_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1" in mot
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=AVAILABLE_MARGIN" in prior
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "TRADING_PERFORMED=false" in spec
    assert "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false" in spec
    assert "PENDING_CURRENT_GET" not in spec
    assert "AVAILABLE_MARGIN_OBSERVATION_CLASS=SUCCESS_NOT_OBSERVED" in spec
    assert "AVAILABLE_MARGIN_RAW_VALUE=NOT_OBSERVED" in spec
    pack = REPO_ROOT / (
        "evidence/ops/available_margin_forensic_binding_implementation_and_closure_v1/"
        "20260830T004150Z"
    )
    assert pack.joinpath("MANIFEST.sha256").is_file()
    assert pack.joinpath("GET_SNAPSHOT.sanitized.json").is_file()
    assert ORDER_PLAN.is_file()
    assert SUBMIT_TRANSPORT.is_file()
    assert CONSUMER.is_file()
    assert OBSERVATION.is_file()
