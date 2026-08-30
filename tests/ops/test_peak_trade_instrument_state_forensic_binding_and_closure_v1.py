"""INSTRUMENT_STATE forensic binding and productive consumer v1.

No live trading. No POST. Public GET only. Exact row state=live is not
live authorization. Historical BTC and prior SUI observations are not
current authority. ruleType/instType/expTime/ticker/markPx are not this
edge.
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
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS,
    GET_ENDPOINTS_PUBLIC,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    POST_ENDPOINTS_GATED,
    TESTNET_AUTHORIZED,
    public_instruments_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.instrument_state_consumer_v1 import (
    CANONICAL_REBIND_IS_NOT_CURRENT_STATE_PROOF,
    EXP_TIME_IS_NOT_INSTRUMENT_STATE_AUTHORITY,
    FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION,
    HISTORICAL_REUSE_PATH_EXISTS,
    INST_TYPE_FUTURES_IS_NOT_INSTRUMENT_STATE_AUTHORITY,
    INSTRUMENT_STATE_CONSUMER_BOUND,
    INSTRUMENT_STATE_FAIL_CLOSED_BOUND,
    INSTRUMENT_STATE_IS_NOT_LIVE_AUTHORIZATION,
    MARK_PRICE_EXISTENCE_IS_NOT_INSTRUMENT_STATE_AUTHORITY,
    NOT_OBSERVED_IS_NOT_LIVE,
    RULE_TYPE_XPERP_IS_NOT_INSTRUMENT_STATE_AUTHORITY,
    TICKER_EXISTENCE_IS_NOT_INSTRUMENT_STATE_AUTHORITY,
    UNKNOWN_STATE_IS_NOT_LIVE,
    LiveCanaryInstrumentStateConsumerError,
    apply_fresh_instrument_state_pretrade_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.instrument_state_observation_v1 import (
    GET_VENUE_TS_STATUS,
    HISTORICAL_BTC_INSTRUMENT_ID,
    INSTRUMENT_STATE_AUTH_CLASS,
    INSTRUMENT_STATE_FRESHNESS_POLICY,
    INSTRUMENT_STATE_OUTPUT_DOMAIN,
    INSTRUMENT_STATE_SEMANTIC_CLASS,
    INSTRUMENT_STATE_TS_AGE_BOUND,
    OBSERVATION_CLASS_SUCCESS_LIVE,
    LiveCanaryInstrumentStateObservationError,
    acquire_fresh_instrument_state_observation_from_payload_v1,
    utc_now_iso_v1,
    validate_fresh_instrument_state_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_flatten_order_plan_v1,
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
SPEC_PATH = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_INSTRUMENT_STATE_FORENSIC_BINDING_AND_CLOSURE_V1.md"
)
PRIOR_AVAILABLE_MARGIN = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_AVAILABLE_MARGIN_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ORDER_PLAN = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"
SUBMIT_TRANSPORT = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
CONSUMER = REPO_ROOT / (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/instrument_state_consumer_v1.py"
)
OBSERVATION = REPO_ROOT / (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/instrument_state_observation_v1.py"
)
OWNER_GO = "PEAK_TRADE_INSTRUMENT_STATE_FORENSIC_BINDING_AND_CLOSURE_V1"
ENDPOINT = public_instruments_query_path_v1()


def _payload(**fields: object) -> dict[str, object]:
    row: dict[str, object] = {
        "instId": DEFAULT_INSTRUMENT_ID,
        "instType": "FUTURES",
        "ruleType": "xperp",
        "minSz": "1",
        "lotSz": "1",
        "tickSz": "0.0001",
        "ctVal": "1",
        "ctValCcy": "SUI",
        "state": "live",
        "maxLmtSz": "100000000",
        "maxMktSz": "100000",
        "expTime": "1933056000000",
    }
    row.update(fields)
    return {"code": "0", "data": [row]}


def _gate(**kwargs: object) -> dict[str, object]:
    body: dict[str, object] = {
        "pretrade_decision_id": "decision-a",
        "instruments_payload": _payload(),
        "instrument_id": DEFAULT_INSTRUMENT_ID,
        "instrument_state_domain": INSTRUMENT_STATE_OUTPUT_DOMAIN,
        "http_status": 200,
        "endpoint": ENDPOINT,
        "get_performed": True,
        "historical_reuse": False,
        "auth_header_sent": False,
    }
    body.update(kwargs)
    return apply_fresh_instrument_state_pretrade_gate_v1(**body)  # type: ignore[arg-type]


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_exact_sui_live_is_positive_and_not_live_authorization() -> None:
    result = _gate()
    assert result["ok"] is True
    assert result["observation_class"] == OBSERVATION_CLASS_SUCCESS_LIVE
    assert result["state_raw"] == "live"
    assert result["semantic_value"] == "LIVE"
    assert result["consumer_precondition_satisfied"] is True
    assert result["semantic_class"] == INSTRUMENT_STATE_SEMANTIC_CLASS
    assert result["instrument_state_is_not_live_authorization"] is True
    assert INSTRUMENT_STATE_IS_NOT_LIVE_AUTHORIZATION is True
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert result["rule_type_raw"] == "xperp"
    assert result["inst_type_raw"] == "FUTURES"
    assert result["rule_type_xperp_is_not_instrument_state_authority"] is True
    assert RULE_TYPE_XPERP_IS_NOT_INSTRUMENT_STATE_AUTHORITY is True
    assert INST_TYPE_FUTURES_IS_NOT_INSTRUMENT_STATE_AUTHORITY is True
    assert EXP_TIME_IS_NOT_INSTRUMENT_STATE_AUTHORITY is True
    assert TICKER_EXISTENCE_IS_NOT_INSTRUMENT_STATE_AUTHORITY is True
    assert MARK_PRICE_EXISTENCE_IS_NOT_INSTRUMENT_STATE_AUTHORITY is True
    assert GET_VENUE_TS_STATUS == "ABSENT_NOT_IN_INSTRUMENTS_ROW"
    assert result["get_venue_ts"] == GET_VENUE_TS_STATUS
    assert result["freshness_policy"] == INSTRUMENT_STATE_FRESHNESS_POLICY
    assert result["ts_age_bound"] == INSTRUMENT_STATE_TS_AGE_BOUND == "UNBOUND"


@pytest.mark.parametrize("raw", ["suspend", "preopen", "test"])
def test_documented_negative_states_fail_closed(raw: str) -> None:
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError,
        match=f"INSTRUMENT_STATE_NOT_ADMISSIBLE:{raw}",
    ):
        _gate(instruments_payload=_payload(state=raw))


def test_missing_state_fails_closed() -> None:
    payload = _payload()
    del payload["data"][0]["state"]  # type: ignore[index]
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_STATE_FIELD_MISSING:state"
    ):
        _gate(instruments_payload=payload)
    assert NOT_OBSERVED_IS_NOT_LIVE is True


def test_empty_state_fails_closed() -> None:
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_STATE_FIELD_EMPTY:state"
    ):
        _gate(instruments_payload=_payload(state=""))
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_STATE_FIELD_EMPTY:state"
    ):
        _gate(instruments_payload=_payload(state="   "))


def test_unknown_enum_fails_closed() -> None:
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_STATE_UNKNOWN_ENUM:expired"
    ):
        _gate(instruments_payload=_payload(state="expired"))
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_STATE_UNKNOWN_ENUM:LIVE"
    ):
        _gate(instruments_payload=_payload(state="LIVE"))
    assert UNKNOWN_STATE_IS_NOT_LIVE is True


def test_no_rows_not_observed() -> None:
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_STATE_NOT_OBSERVED"
    ):
        _gate(instruments_payload={"code": "0", "data": []})


def test_wrong_target_btc_row_fails_closed() -> None:
    payload = {
        "code": "0",
        "data": [
            {
                "instId": HISTORICAL_BTC_INSTRUMENT_ID,
                "instType": "FUTURES",
                "ruleType": "xperp",
                "state": "live",
            }
        ],
    }
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_STATE_NOT_OBSERVED"
    ):
        _gate(instruments_payload=payload)
    with pytest.raises(LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_BINDING_MISMATCH"):
        _gate(instrument_id=HISTORICAL_BTC_INSTRUMENT_ID)


def test_duplicate_sui_rows_fail_closed() -> None:
    row = _payload()["data"][0]  # type: ignore[index]
    payload = {"code": "0", "data": [row, dict(row)]}
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_STATE_DUPLICATE_TARGET_ROWS:2"
    ):
        _gate(instruments_payload=payload)
    conflicted = {"code": "0", "data": [row, {**dict(row), "state": "suspend"}]}
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_STATE_DUPLICATE_TARGET_ROWS:2"
    ):
        _gate(instruments_payload=conflicted)


def test_live_with_wrong_rule_type_fails_closed() -> None:
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError,
        match="INSTRUMENT_STATE_GEOMETRY_RULE_TYPE_MISMATCH:pre_market",
    ):
        _gate(instruments_payload=_payload(ruleType="pre_market"))
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError,
        match="INSTRUMENT_STATE_GEOMETRY_INST_TYPE_MISMATCH:SWAP",
    ):
        _gate(instruments_payload=_payload(instType="SWAP"))


def test_stale_historical_reuse_fails_closed() -> None:
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError,
        match="HISTORICAL_INSTRUMENT_STATE_REUSE_FORBIDDEN",
    ):
        _gate(historical_reuse=True)
    assert HISTORICAL_REUSE_PATH_EXISTS is False
    assert CANONICAL_REBIND_IS_NOT_CURRENT_STATE_PROOF is True


def test_missing_get_and_auth_and_venue_failure() -> None:
    with pytest.raises(LiveCanaryInstrumentStateConsumerError, match="FRESH_GET_NOT_PERFORMED"):
        _gate(get_performed=False)
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="PUBLIC_INSTRUMENTS_AUTH_HEADER_FORBIDDEN"
    ):
        _gate(auth_header_sent=True)
    with pytest.raises(LiveCanaryInstrumentStateConsumerError, match="FRESH_GET_HTTP_UNSUCCESSFUL"):
        _gate(http_status=500)
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_STATE_VENUE_CODE_UNSUCCESSFUL"
    ):
        _gate(instruments_payload={"code": "1", "data": []})
    assert FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION is True


def test_wrong_type_and_malformed_fail_closed() -> None:
    with pytest.raises(LiveCanaryInstrumentStateConsumerError, match="INSTRUMENTS_DATA_MISSING"):
        _gate(instruments_payload={"code": "0", "data": {"state": "live"}})
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_STATE_FIELD_WRONG_TYPE"
    ):
        _gate(instruments_payload=_payload(state=1))


def test_null_state_fails_closed() -> None:
    payload = _payload()
    payload["data"][0]["state"] = None  # type: ignore[index]
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_STATE_FIELD_NULL:state"
    ):
        _gate(instruments_payload=payload)


def test_typed_domain_not_mixed() -> None:
    with pytest.raises(
        LiveCanaryInstrumentStateConsumerError, match="INSTRUMENT_STATE_DOMAIN_INCOMPATIBLE"
    ):
        _gate(instrument_state_domain=ORDER_PLAN_QTY_DOMAIN)


def test_order_plan_wires_instrument_state_after_available_margin() -> None:
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=_instruments_payload(),
        ticker_payload=TICKER,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="90c9d6c6f36f780d6ef76a8b99f20b94050e15f4",
        pretrade_decision_id="decision-plan-instrument-state",
        **_max_available_plan_kwargs(),
    )
    assert plan.quantity_domain == ORDER_PLAN_QTY_DOMAIN
    missing = _instruments_payload()
    del missing["data"][0]["state"]  # type: ignore[index]
    with pytest.raises(LiveCanaryOrderPlanError, match="INSTRUMENT_STATE_GATE"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=missing,
            ticker_payload=TICKER,
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            origin_main_sha="90c9d6c6f36f780d6ef76a8b99f20b94050e15f4",
            pretrade_decision_id="decision-plan-instrument-state-missing",
            **_max_available_plan_kwargs(),
        )
    assert INSTRUMENT_STATE_CONSUMER_BOUND is True
    assert INSTRUMENT_STATE_FAIL_CLOSED_BOUND is True


def test_flatten_does_not_consume_instrument_state_gate() -> None:
    payload = {
        "code": "0",
        "data": [{"instId": DEFAULT_INSTRUMENT_ID, "pos": "1", "mgnMode": "cross"}],
    }
    plan = build_minimum_valid_canary_flatten_order_plan_v1(
        positions_payload=payload,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="90c9d6c6f36f780d6ef76a8b99f20b94050e15f4",
    )
    assert plan.td_mode == "cross"


def test_submit_transport_fail_closed_before_post_when_state_not_live() -> None:
    transport = _fake_transport()
    suspended = _payload(state="suspend")
    import json

    transport.bodies_by_endpoint["/api/v5/public/instruments"] = json.dumps(suspended).encode()
    with pytest.raises(LiveCanarySubmitTransportError, match="INSTRUMENT_STATE"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)


def test_submit_transport_reuses_instruments_get_without_second_fetch() -> None:
    transport = _fake_transport()
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["ok"] is True
    instrument_gets = [
        call
        for call in transport.calls
        if str(call.endpoint).startswith("/api/v5/public/instruments")
    ]
    assert len(instrument_gets) == 1


def test_allowlist_public_and_no_trading() -> None:
    assert "/api/v5/public/instruments" in GET_ENDPOINTS_PUBLIC
    assert ENDPOINT == (
        "/api/v5/public/instruments?instType=FUTURES&instId=SUI-USD_UM_XPERP-310404"
    )
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False
    assert "/api/v5/public/instruments" not in POST_ENDPOINTS_GATED
    assert any("set-" in marker for marker in FORBIDDEN_MUTATION_ENDPOINT_MARKERS)


def test_observation_validate_decision_mismatch() -> None:
    obs = acquire_fresh_instrument_state_observation_from_payload_v1(
        pretrade_decision_id="decision-one",
        instruments_payload=_payload(),
        instrument_id=DEFAULT_INSTRUMENT_ID,
        observed_at_utc=utc_now_iso_v1(),
        endpoint=ENDPOINT,
        http_status=200,
        get_performed=True,
    )
    with pytest.raises(
        LiveCanaryInstrumentStateObservationError, match="OBSERVATION_DECISION_ID_MISMATCH"
    ):
        validate_fresh_instrument_state_observation_v1(
            obs,
            pretrade_decision_id="decision-two",
            instrument_id=DEFAULT_INSTRUMENT_ID,
            instrument_state_domain=INSTRUMENT_STATE_OUTPUT_DOMAIN,
        )
    assert INSTRUMENT_STATE_AUTH_CLASS == "PUBLIC_UNSIGNED_GET"
    assert INSTRUMENT_STATE_TS_AGE_BOUND == "UNBOUND"
    assert INSTRUMENT_STATE_FRESHNESS_POLICY == "FRESH_GET_PER_PRETRADE_DECISION"


def test_docs_and_master_pointer() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    prior = PRIOR_AVAILABLE_MARGIN.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert "CANONICAL_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404" in spec
    assert "CANONICAL_INSTRUMENT_BINDING_STATUS=PROVEN" in spec
    assert "INSTRUMENT_STATE_CANONICAL_DEFINITION=VENUE_INSTRUMENT_STATE" in spec
    assert "INSTRUMENT_STATE_ENDPOINT=/api/v5/public/instruments" in spec
    assert "INSTRUMENT_STATE_SOURCE_ENDPOINT=/api/v5/public/instruments" in spec
    assert "INSTRUMENT_STATE_QUERY=instType=FUTURES&instId=SUI-USD_UM_XPERP-310404" in spec
    assert "INSTRUMENT_STATE_RAW_FIELD=state" in spec
    assert "INSTRUMENT_STATE_ADMISSIBLE_RAW=live" in spec
    assert "INSTRUMENT_STATE_RAW_VALUE=live" in spec
    assert "INSTRUMENT_STATE_SEMANTIC_VALUE=LIVE" in spec
    assert "INSTRUMENT_STATE_BINDING_STATUS=PROVEN" in spec
    assert "INSTRUMENT_STATE_FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION" in spec
    assert "INSTRUMENT_STATE_GET_VENUE_TS=ABSENT_NOT_IN_INSTRUMENTS_ROW" in spec
    assert "INSTRUMENT_STATE_TS_AGE_BOUND=UNBOUND" in spec
    assert "INSTRUMENT_STATE_IS_NOT_LIVE_AUTHORIZATION=true" in spec
    assert "RULE_TYPE_XPERP_IS_NOT_INSTRUMENT_STATE_AUTHORITY=true" in spec
    assert "INST_TYPE_FUTURES_IS_NOT_INSTRUMENT_STATE_AUTHORITY=true" in spec
    assert "EXP_TIME_IS_NOT_INSTRUMENT_STATE_AUTHORITY=true" in spec
    assert "TICKER_EXISTENCE_IS_NOT_INSTRUMENT_STATE_AUTHORITY=true" in spec
    assert "MARK_PRICE_EXISTENCE_IS_NOT_INSTRUMENT_STATE_AUTHORITY=true" in spec
    assert "HISTORICAL_BTC_CURRENT_CLAIMS_ARE_NOT_CURRENT_AUTHORITY=true" in spec
    assert "HISTORICAL_SUI_STATE_OBSERVATION_IS_NOT_AUTOMATIC_CURRENT_STATE=true" in spec
    assert "UNKNOWN_STATE_IS_NOT_LIVE=true" in spec
    assert "NOT_OBSERVED_IS_NOT_LIVE=true" in spec
    assert "CANONICAL_REBIND_IS_NOT_CURRENT_STATE_PROOF=true" in spec
    assert "ALL_REQUIRED_METADATA_EDGES_BOUND=true" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=ACCOUNT_MODE" in spec
    assert "NEXT_DISTINCT_SURFACE=ACCOUNT_MODE" in spec
    assert "NEXT_DISTINCT_SURFACE_AUTHORIZED=false" in spec
    assert "INSTRUMENT_STATE_FORENSIC_BINDING_AND_CLOSURE_V1=true" in section
    assert "PEAK_TRADE_INSTRUMENT_STATE_FORENSIC_BINDING_AND_CLOSURE_V1" in mot
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=INSTRUMENT_STATE" in prior
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "TRADING_PERFORMED=false" in spec
    assert "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false" in spec
    assert "PENDING_CURRENT_GET" not in spec
    assert "INSTRUMENT_STATE_OBSERVATION_CLASS=SUCCESS_LIVE" in spec
    assert "LIVE_AUTHORIZED=false" in spec
    assert "TESTNET_AUTHORIZED=false" in spec
    assert "CANARY_AUTHORIZED=false" in spec
    pack = REPO_ROOT / (
        "evidence/ops/instrument_state_forensic_binding_and_closure_v1/20260830T044522Z"
    )
    assert pack.joinpath("MANIFEST.sha256").is_file()
    assert pack.joinpath("GET_SNAPSHOT.sanitized.json").is_file()
    assert ORDER_PLAN.is_file()
    assert SUBMIT_TRANSPORT.is_file()
    assert CONSUMER.is_file()
    assert OBSERVATION.is_file()
