"""LEVERAGE forensic binding and productive consumer v1.

No live trading. No POST. No set-leverage. Authenticated GET only.
Historical BTC lever=3 is not reused. mgnMode is not tdMode or account mode.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.capability_11_9_live_canary_order_execution_v1.constants_v1 import (
    LIVE_EXECUTION_REACHABLE,
    TESTNET_EXECUTION_REACHABLE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_FAMILY,
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_ACCOUNT_LEVERAGE_INFO,
    GET_ENDPOINTS_PRIVATE,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.leverage_consumer_v1 import (
    DEFAULT_LEVERAGE_USED,
    FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION,
    HISTORICAL_BTC_LEVERAGE_REUSED,
    HISTORICAL_REUSE_PATH_EXISTS,
    IMR_MMR_RECONSTRUCTION_USED,
    LEVERAGE_CONSUMER_BOUND,
    LEVERAGE_FAIL_CLOSED_BOUND,
    MAX_LEVERAGE_SUBSTITUTION_USED,
    ZERO_NORMALIZATION_PERFORMED,
    LiveCanaryLeverageConsumerError,
    apply_fresh_leverage_pretrade_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.leverage_observation_v1 import (
    HISTORICAL_BTC_INSTRUMENT_ID,
    LEVERAGE_AUTH_CLASS,
    LEVERAGE_COMPARISON_DOMAIN,
    LEVERAGE_EXPECTED_MGN_MODE,
    LEVERAGE_EXPECTED_POS_SIDE,
    LEVERAGE_FRESHNESS_POLICY,
    LEVERAGE_NO_TS_FIELD,
    LEVERAGE_OUTPUT_DOMAIN,
    LEVERAGE_REQUEST_INSTID_ROLE,
    LEVERAGE_SCOPE,
    LEVERAGE_TS_AGE_BOUND,
    MGNMODE_IS_NOT_ACCOUNT_MODE,
    MGNMODE_IS_NOT_TDMODE,
    TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF,
    LiveCanaryLeverageObservationError,
    account_leverage_info_query_path_v1,
    acquire_fresh_leverage_observation_from_payload_v1,
    validate_fresh_leverage_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_order_plan_v1,
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
    TICKER,
    _assert_no_post,
    _fake_transport,
    _max_available_plan_kwargs,
    _transport_kwargs,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md"
)
PRIOR_PRICE_BAND = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ORDER_PLAN = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"
SUBMIT_TRANSPORT = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
CONSUMER = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/leverage_consumer_v1.py"
)
OBSERVATION = REPO_ROOT / (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/leverage_observation_v1.py"
)
OWNER_GO = "PEAK_TRADE_LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1"
ENDPOINT = account_leverage_info_query_path_v1(
    instrument_id=DEFAULT_INSTRUMENT_ID, mgn_mode=LEVERAGE_EXPECTED_MGN_MODE
)


def _payload(
    *,
    lever: str = "5",
    inst_id: str = DEFAULT_INSTRUMENT_ID,
    mgn_mode: str = "cross",
    pos_side: str = "net",
    ccy: str = "",
) -> dict[str, object]:
    return {
        "code": "0",
        "msg": "",
        "data": [
            {
                "instId": inst_id,
                "ccy": ccy,
                "mgnMode": mgn_mode,
                "posSide": pos_side,
                "lever": lever,
            }
        ],
    }


def _gate(**kwargs: object) -> dict[str, object]:
    body: dict[str, object] = {
        "pretrade_decision_id": "decision-a",
        "payload": _payload(),
        "instrument_id": DEFAULT_INSTRUMENT_ID,
        "mgn_mode": LEVERAGE_EXPECTED_MGN_MODE,
        "leverage_domain": LEVERAGE_OUTPUT_DOMAIN,
        "http_status": 200,
        "endpoint": ENDPOINT,
        "get_performed": True,
        "historical_reuse": False,
        "auth_header_sent": True,
        "td_mode": "cross",
    }
    body.update(kwargs)
    return apply_fresh_leverage_pretrade_gate_v1(**body)  # type: ignore[arg-type]


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_valid_sui_leverage_passes() -> None:
    result = _gate()
    assert result["ok"] is True
    assert result["observation_class"] == "SUCCESS_NUMERIC"
    assert result["lever"] == "5"
    assert result["pos_side"] == "net"
    assert result["mgn_mode"] == "cross"
    assert result["inst_family"] == DEFAULT_INST_FAMILY
    assert result["leverage_scope"] == LEVERAGE_SCOPE
    assert result["request_instid_role"] == LEVERAGE_REQUEST_INSTID_ROLE


def test_query_grammar_is_instid_and_mgnmode_only() -> None:
    query = account_leverage_info_query_path_v1(
        instrument_id=DEFAULT_INSTRUMENT_ID, mgn_mode="cross"
    )
    assert query.startswith(ENDPOINT_ACCOUNT_LEVERAGE_INFO)
    assert "instId=" in query
    assert "mgnMode=cross" in query
    assert "tdMode=" not in query
    assert "ccy=" not in query
    assert "posSide=" not in query
    assert "leverage=" not in query


def test_correct_instrument_and_margin_mode_scope() -> None:
    result = _gate()
    assert result["inst_id"] == DEFAULT_INSTRUMENT_ID
    assert result["mgn_mode"] == LEVERAGE_EXPECTED_MGN_MODE
    assert result["expected_mgn_mode"] == "cross"


def test_net_pos_side_required() -> None:
    assert _gate()["pos_side"] == LEVERAGE_EXPECTED_POS_SIDE
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_POS_SIDE_NOT_NET:long"):
        _gate(payload=_payload(pos_side="long"))
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_POS_SIDE_NOT_NET:short"):
        _gate(payload=_payload(pos_side="short"))


def test_missing_and_empty_lever_fail_closed() -> None:
    missing = _payload()
    del missing["data"][0]["lever"]  # type: ignore[index]
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_FIELD_MISSING:lever"):
        _gate(payload=missing)
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_FIELD_MISSING:lever"):
        _gate(payload=_payload(lever=""))
    null_row = _payload()
    null_row["data"][0]["lever"] = None  # type: ignore[index]
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_FIELD_NULL:lever"):
        _gate(payload=null_row)


def test_malformed_nan_infinity_zero_negative_fail_closed() -> None:
    with pytest.raises(LiveCanaryLeverageConsumerError, match="NON_NUMERIC"):
        _gate(payload=_payload(lever="not-a-number"))
    with pytest.raises(LiveCanaryLeverageConsumerError, match="NON_NUMERIC"):
        _gate(payload=_payload(lever="NaN"))
    with pytest.raises(LiveCanaryLeverageConsumerError, match="NON_NUMERIC"):
        _gate(payload=_payload(lever="Infinity"))
    with pytest.raises(LiveCanaryLeverageConsumerError, match="NON_POSITIVE"):
        _gate(payload=_payload(lever="0"))
    with pytest.raises(LiveCanaryLeverageConsumerError, match="NON_POSITIVE"):
        _gate(payload=_payload(lever="-1"))
    assert DEFAULT_LEVERAGE_USED is False


def test_mismatched_instid_and_mgnmode_fail_closed() -> None:
    with pytest.raises(LiveCanaryLeverageConsumerError, match="INSTRUMENT_MISMATCH"):
        _gate(payload=_payload(inst_id="SUI-USD_UM_XPERP-999999"))
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_MGNMODE_MISMATCH"):
        _gate(payload=_payload(mgn_mode="isolated"))


def test_btc_leverage_three_cannot_substitute_for_sui() -> None:
    with pytest.raises(LiveCanaryLeverageConsumerError, match="HISTORICAL_BTC_INSTRUMENT"):
        _gate(
            instrument_id=HISTORICAL_BTC_INSTRUMENT_ID,
            payload=_payload(inst_id=HISTORICAL_BTC_INSTRUMENT_ID, lever="3"),
            endpoint=ENDPOINT.replace(DEFAULT_INSTRUMENT_ID, HISTORICAL_BTC_INSTRUMENT_ID),
        )
    with pytest.raises(LiveCanaryLeverageConsumerError, match="HISTORICAL_BTC"):
        _gate(endpoint=ENDPOINT.replace(DEFAULT_INSTRUMENT_ID, HISTORICAL_BTC_INSTRUMENT_ID))
    assert HISTORICAL_BTC_LEVERAGE_REUSED is False


def test_swap_and_forbidden_source_markers_fail_closed() -> None:
    with pytest.raises(LiveCanaryLeverageConsumerError, match="SWAP_LEVERAGE_SUBSTITUTION"):
        _gate(endpoint=f"{ENDPOINT_ACCOUNT_LEVERAGE_INFO}?instId=BTC-USDT-SWAP&mgnMode=cross")
    with pytest.raises(
        LiveCanaryLeverageConsumerError, match="LEVERAGE_RECONSTRUCTION_SOURCE_FORBIDDEN"
    ):
        _gate(endpoint="/api/v5/account/adjust-leverage-info?instId=x&mgnMode=cross")
    with pytest.raises(
        LiveCanaryLeverageConsumerError, match="LEVERAGE_RECONSTRUCTION_SOURCE_FORBIDDEN"
    ):
        _gate(endpoint="/api/v5/public/position-tiers?tdMode=cross")


def test_tdmode_query_and_ccy_query_forbidden() -> None:
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_TDMODE_QUERY_FORBIDDEN"):
        _gate(endpoint=f"{ENDPOINT}&tdMode=cross")
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_CCY_QUERY_FORBIDDEN"):
        _gate(endpoint=f"{ENDPOINT}&ccy=USDC")


def test_http_venue_empty_data_ambiguous_and_auth_fail_closed() -> None:
    with pytest.raises(LiveCanaryLeverageConsumerError, match="FRESH_GET_NOT_PERFORMED"):
        _gate(get_performed=False)
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_NETWORK_ERROR"):
        _gate(http_status=500)
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_AUTH_ERROR"):
        _gate(http_status=401)
    with pytest.raises(LiveCanaryLeverageConsumerError, match="VENUE_CODE_UNSUCCESSFUL"):
        _gate(payload={"code": "1", "data": _payload()["data"]})
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_DATA_MISSING"):
        _gate(payload={"code": "0", "data": []})
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_AMBIGUOUS_TARGET_ROW"):
        _gate(
            payload={
                "code": "0",
                "data": [
                    _payload()["data"][0],
                    _payload(pos_side="short")["data"][0],
                ],
            }
        )
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_AUTH_HEADER_REQUIRED"):
        _gate(auth_header_sent=False)
    with pytest.raises(LiveCanaryLeverageConsumerError, match="HISTORICAL_LEVERAGE_REUSE"):
        _gate(historical_reuse=True)
    assert FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION is True
    assert HISTORICAL_REUSE_PATH_EXISTS is False


def test_tdmode_cross_is_not_account_mode_proof() -> None:
    result = _gate(td_mode="cross")
    assert result["ok"] is True
    assert result["mgnmode_is_not_tdmode"] is True
    assert result["mgnmode_is_not_account_mode"] is True
    assert result["tdmode_cross_is_not_account_mode_proof"] is True
    assert MGNMODE_IS_NOT_TDMODE is True
    assert MGNMODE_IS_NOT_ACCOUNT_MODE is True
    assert TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF is True
    assert LEVERAGE_AUTH_CLASS == "AUTHENTICATED_PRIVATE_GET"
    assert LEVERAGE_NO_TS_FIELD is True
    assert LEVERAGE_TS_AGE_BOUND == "UNBOUND"
    assert LEVERAGE_FRESHNESS_POLICY == "FRESH_GET_PER_PRETRADE_DECISION"


def test_typed_domain_not_mixed_with_quantity_or_price() -> None:
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_DOMAIN_INCOMPATIBLE"):
        _gate(leverage_domain=ORDER_PLAN_QTY_DOMAIN)
    with pytest.raises(LiveCanaryLeverageConsumerError, match="LEVERAGE_DOMAIN_INCOMPATIBLE"):
        _gate(leverage_domain=PRICE_BAND_OUTPUT_DOMAIN)
    assert LEVERAGE_OUTPUT_DOMAIN == "SET_ACCOUNT_LEVERAGE"
    assert LEVERAGE_COMPARISON_DOMAIN != ORDER_PLAN_QTY_DOMAIN
    assert LEVERAGE_OUTPUT_DOMAIN != PRICE_BAND_OUTPUT_DOMAIN
    assert ZERO_NORMALIZATION_PERFORMED is False
    assert MAX_LEVERAGE_SUBSTITUTION_USED is False
    assert IMR_MMR_RECONSTRUCTION_USED is False


def test_order_plan_wires_leverage_and_preserves_typed_quantity_domain() -> None:
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=_instruments_payload(),
        ticker_payload=TICKER,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="e968777cf717f6a63f065b50a49eeb777328bc61",
        pretrade_decision_id="decision-plan-leverage",
        **_max_available_plan_kwargs(),
    )
    assert plan.quantity_domain == ORDER_PLAN_QTY_DOMAIN
    assert plan.limit_price == "0.8209"
    with pytest.raises(LiveCanaryOrderPlanError, match="LEVERAGE_GATE"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=_instruments_payload(),
            ticker_payload=TICKER,
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            origin_main_sha="e968777cf717f6a63f065b50a49eeb777328bc61",
            pretrade_decision_id="decision-plan-leverage-missing",
            **_max_available_plan_kwargs(leverage_get_performed=False),
        )
    assert LEVERAGE_CONSUMER_BOUND is True
    assert LEVERAGE_FAIL_CLOSED_BOUND is True


def test_submit_transport_fail_closed_before_post_when_leverage_fails() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint[ENDPOINT_ACCOUNT_LEVERAGE_INFO] = b'{"code":"0","data":[]}'
    with pytest.raises(LiveCanarySubmitTransportError, match="LEVERAGE"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)
    assert any(ENDPOINT_ACCOUNT_LEVERAGE_INFO in str(call.endpoint) for call in transport.calls)


def test_submit_transport_btc_three_does_not_post() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint[ENDPOINT_ACCOUNT_LEVERAGE_INFO] = (
        b'{"code":"0","data":[{"instId":"BTC-USD_UM_XPERP-310404","ccy":"",'
        b'"mgnMode":"cross","posSide":"net","lever":"3"}]}'
    )
    with pytest.raises(LiveCanarySubmitTransportError, match="LEVERAGE"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)


def test_allowlist_private_and_no_trading() -> None:
    assert ENDPOINT_ACCOUNT_LEVERAGE_INFO in GET_ENDPOINTS_PRIVATE
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False
    consumer = CONSUMER.read_text(encoding="utf-8")
    observation = OBSERVATION.read_text(encoding="utf-8")
    assert "post_entry_order" not in consumer
    assert "set-leverage" in observation
    assert "apply_fresh_leverage_pretrade_gate_v1" in ORDER_PLAN.read_text(encoding="utf-8")
    assert "account_leverage_info_query_path_v1" in SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    assert "DEFAULT_LEVERAGE=3" not in consumer
    assert "DEFAULT_LEVERAGE=3" not in observation


def test_observation_bound_to_decision_and_leverage_domain() -> None:
    obs = acquire_fresh_leverage_observation_from_payload_v1(
        pretrade_decision_id="decision-one",
        payload=_payload(),
        observed_at_utc="2026-08-30T00:00:00.000000Z",
        endpoint=ENDPOINT,
        http_status=200,
        get_performed=True,
    )
    with pytest.raises(
        LiveCanaryLeverageObservationError, match="OBSERVATION_DECISION_ID_MISMATCH"
    ):
        validate_fresh_leverage_observation_v1(
            obs,
            pretrade_decision_id="decision-two",
            instrument_id=DEFAULT_INSTRUMENT_ID,
            leverage_domain=LEVERAGE_OUTPUT_DOMAIN,
        )
    assert obs.leverage_scope == "PER_INSTRUMENT_FAMILY"
    assert obs.request_instid_role == "FAMILY_SELECTOR"
    assert obs.inst_family_bound == DEFAULT_INST_FAMILY


def test_docs_and_master_pointer() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    prior = PRIOR_PRICE_BAND.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert "LEVERAGE_CANONICAL_DEFINITION=SET_ACCOUNT_LEVERAGE" in spec
    assert "LEVERAGE_ENDPOINT=/api/v5/account/leverage-info" in spec
    assert "LEVERAGE_BINDING_STATUS=PROVEN" in spec
    assert "LEVERAGE_FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION" in spec
    assert "LEVERAGE_TS_AGE_BOUND=UNBOUND" in spec
    assert "LEVERAGE_OUTPUT_DOMAIN=SET_ACCOUNT_LEVERAGE" in spec
    assert "LEVERAGE_AUTH_CLASS=AUTHENTICATED_PRIVATE_GET" in spec
    assert "LEVERAGE_SCOPE=PER_INSTRUMENT_FAMILY" in spec
    assert "REQUEST_INSTID_ROLE=FAMILY_SELECTOR" in spec
    assert "MGNMODE_IS_NOT_TDMODE=true" in spec
    assert "HISTORICAL_BTC_LEVERAGE_REUSED=false" in spec
    assert "DEFAULT_LEVERAGE_USED=false" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=POS_MODE" in spec
    assert "LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1=true" in section
    assert "PEAK_TRADE_LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1" in mot
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=LEVERAGE" in prior
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "TRADING_PERFORMED=false" in spec
    assert "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false" in spec
    assert "SET_LEVERAGE_EXECUTED=false" in spec
    assert "CROSS_TDMODE_USED_AS_ACCOUNT_MODE_PROOF=false" in spec
