"""Fresh max-size observation and productive pretrade consumer v1.

No live trading. No POST. Historical #6148 values are not reused.
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
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    REUSED_BINDING_REST_HOST,
    TESTNET_AUTHORIZED,
    public_instruments_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_size_consumer_v1 import (
    FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION,
    HISTORICAL_REUSE_PATH_EXISTS,
    LIMIT_MAX_SIZE_GATE_BOUND,
    MARKET_MAX_SIZE_GATE_BOUND,
    MAX_SIZE_CONSUMER_BOUND,
    LiveCanaryMaxSizeConsumerError,
    apply_fresh_max_size_pretrade_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_size_observation_v1 import (
    HISTORICAL_6148_RUN_ID,
    LiveCanaryMaxSizeObservationError,
    acquire_fresh_max_size_observation_from_payload_v1,
    fetch_unsigned_public_instruments_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_order_plan_v1,
    extract_instrument_constraints_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    ORDER_PLAN_QTY_DOMAIN,
)
from tests.ops.test_section_11_13_5_canary_submit_transport_v1 import (
    _max_available_plan_kwargs,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1.md"
)
PRIOR_POLICY = (
    REPO_ROOT / "docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1.md"
)
PRIOR_6148 = (
    REPO_ROOT
    / "docs/ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ORDER_PLAN = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"
EXPOSURE = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/exposure_v1.py"
SUBMIT_TRANSPORT = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
CONSUMER = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/max_size_consumer_v1.py"
)
OWNER_GO = "PEAK_TRADE_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1"
ENDPOINT = public_instruments_query_path_v1()
TICKER = {"code": "0", "data": [{"instId": DEFAULT_INSTRUMENT_ID, "last": "0.8209"}]}


def _payload(**fields: str) -> dict[str, object]:
    row = {
        "instId": DEFAULT_INSTRUMENT_ID,
        "instType": "FUTURES",
        "ruleType": "xperp",
        "minSz": "1",
        "lotSz": "1",
        "tickSz": "0.0001",
        "ctVal": "1",
        "ctValCcy": "SUI",
        "maxLmtSz": "100000000",
        "maxMktSz": "100000",
    }
    row.update(fields)
    return {"code": "0", "data": [row]}


def _gate(**kwargs: object) -> dict[str, object]:
    body = {
        "pretrade_decision_id": "decision-a",
        "instruments_payload": _payload(),
        "instrument_id": DEFAULT_INSTRUMENT_ID,
        "order_type": "LIMIT",
        "venue_contract_count": "1",
        "quantity_domain": ORDER_PLAN_QTY_DOMAIN,
        "http_status": 200,
        "endpoint": ENDPOINT,
        "get_performed": True,
        "historical_reuse": False,
    }
    body.update(kwargs)
    return apply_fresh_max_size_pretrade_gate_v1(**body)  # type: ignore[arg-type]


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_limit_uses_only_fresh_maxlmtsz() -> None:
    result = _gate(order_type="LIMIT")
    assert result["max_size_field"] == "maxLmtSz"
    assert result["ok"] is True
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="MAXLMTSZ"):
        _gate(order_type="LIMIT", venue_contract_count="100000001")


def test_market_uses_only_fresh_maxmktsz() -> None:
    result = _gate(order_type="MARKET")
    assert result["max_size_field"] == "maxMktSz"
    assert result["ok"] is True
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="MAXMKTSZ"):
        _gate(order_type="MARKET", venue_contract_count="100001")


def test_historical_value_is_not_operatively_reused() -> None:
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="HISTORICAL_MAX_SIZE_REUSE"):
        _gate(historical_reuse=True)
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="HISTORICAL_6148"):
        _gate(pretrade_decision_id=HISTORICAL_6148_RUN_ID)
    assert HISTORICAL_REUSE_PATH_EXISTS is False
    prior = PRIOR_6148.read_text(encoding="utf-8")
    assert "CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false" in prior


def test_missing_observation_and_get_failure_fail_closed() -> None:
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="FRESH_GET_NOT_PERFORMED"):
        _gate(get_performed=False)
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="FRESH_GET_HTTP_UNSUCCESSFUL"):
        _gate(http_status=500)
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="PRETRADE_DECISION_ID_REQUIRED"):
        _gate(pretrade_decision_id=" ")
    assert FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION is True


def test_fetch_failure_fail_closed() -> None:
    transport = RecordingFakeCanaryTransportV1(status_code=503, body=b"nope")
    client = LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host=REUSED_BINDING_REST_HOST,
        transport=transport,
        max_retries=0,
    )
    response = fetch_unsigned_public_instruments_v1(client=client)
    assert response.status_code == 503
    with pytest.raises(LiveCanaryMaxSizeObservationError, match="FRESH_GET_HTTP_UNSUCCESSFUL"):
        acquire_fresh_max_size_observation_from_payload_v1(
            pretrade_decision_id="decision-fetch-fail",
            instruments_payload={"code": "0", "data": []},
            observed_at_utc="2026-08-29T21:00:00.000000Z",
            endpoint=ENDPOINT,
            http_status=response.status_code,
            get_performed=True,
        )


def test_wrong_instrument_and_missing_field_fail_closed() -> None:
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="INSTRUMENT_MISMATCH"):
        _gate(
            instruments_payload={
                "code": "0",
                "data": [
                    {
                        "instId": "SUI-USD_UM_XPERP-999999",
                        "instType": "FUTURES",
                        "ruleType": "xperp",
                        "minSz": "1",
                        "lotSz": "1",
                        "tickSz": "0.0001",
                        "ctVal": "1",
                        "maxLmtSz": "100000000",
                        "maxMktSz": "100000",
                    }
                ],
            }
        )
    missing = _payload()
    del missing["data"][0]["maxLmtSz"]  # type: ignore[index]
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="MAX_SIZE_FIELD_MISSING:maxLmtSz"):
        _gate(instruments_payload=missing, order_type="LIMIT")
    null_row = _payload()
    null_row["data"][0]["maxMktSz"] = None  # type: ignore[index]
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="MAX_SIZE_FIELD_NULL:maxMktSz"):
        _gate(instruments_payload=null_row, order_type="MARKET")


def test_invalid_numeric_and_incompatible_domain_fail_closed() -> None:
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="NON_NUMERIC"):
        _gate(instruments_payload=_payload(maxLmtSz="not-a-number"))
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="NEGATIVE"):
        _gate(instruments_payload=_payload(maxLmtSz="-1"))
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="ZERO_FORBIDDEN"):
        _gate(instruments_payload=_payload(maxLmtSz="0"))
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="QUANTITY_DOMAIN_INCOMPATIBLE"):
        _gate(quantity_domain="NOTIONAL")


def test_exact_admissible_size_and_over_max_reject() -> None:
    ok = _gate(venue_contract_count="1", order_type="LIMIT")
    assert ok["ok"] is True
    at_cap = _gate(venue_contract_count="100000000", order_type="LIMIT")
    assert at_cap["ok"] is True
    with pytest.raises(LiveCanaryMaxSizeConsumerError, match="EXCEEDS_MAXLMTSZ"):
        _gate(venue_contract_count="100000001", order_type="LIMIT")


def test_observation_is_bound_to_pretrade_decision() -> None:
    first = _gate(pretrade_decision_id="decision-one")
    second = _gate(pretrade_decision_id="decision-two")
    assert first["pretrade_decision_id"] == "decision-one"
    assert second["pretrade_decision_id"] == "decision-two"
    obs = acquire_fresh_max_size_observation_from_payload_v1(
        pretrade_decision_id="decision-one",
        instruments_payload=_payload(),
        observed_at_utc="2026-08-29T21:00:00.000000Z",
        endpoint=ENDPOINT,
        http_status=200,
        get_performed=True,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_size_observation_v1 import (
        validate_fresh_max_size_observation_v1,
    )

    with pytest.raises(LiveCanaryMaxSizeObservationError, match="OBSERVATION_DECISION_ID_MISMATCH"):
        validate_fresh_max_size_observation_v1(
            obs,
            pretrade_decision_id="decision-two",
            instrument_id=DEFAULT_INSTRUMENT_ID,
            quantity_domain=ORDER_PLAN_QTY_DOMAIN,
        )


def test_typed_order_plan_domain_preserved_and_plan_gate_wired() -> None:
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=_payload(),
        ticker_payload=TICKER,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="ae302d2b4c0425c4d42ece494d1b5996a9e54243",
        pretrade_decision_id="decision-plan",
        **_max_available_plan_kwargs(),
    )
    assert plan.quantity_domain == ORDER_PLAN_QTY_DOMAIN
    assert plan.quantity == "1"
    with pytest.raises(LiveCanaryOrderPlanError, match="MAX_SIZE_GATE"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=_payload(maxLmtSz="0"),
            ticker_payload=TICKER,
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            origin_main_sha="ae302d2b4c0425c4d42ece494d1b5996a9e54243",
            pretrade_decision_id="decision-plan-zero",
        )
    assert extract_instrument_constraints_v1 is not None
    assert 'required = ("minSz", "lotSz", "tickSz", "ctVal")' in ORDER_PLAN.read_text(
        encoding="utf-8"
    )
    for source in (ORDER_PLAN.read_text(encoding="utf-8"), EXPOSURE.read_text(encoding="utf-8")):
        assert "maxLmtSz" not in source
        assert "maxMktSz" not in source
    transport = SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    assert "maxLmtSz" not in transport
    assert "maxMktSz" not in transport
    consumer = CONSUMER.read_text(encoding="utf-8")
    assert "maxLmtSz" in consumer
    assert MAX_SIZE_CONSUMER_BOUND is True
    assert LIMIT_MAX_SIZE_GATE_BOUND is True
    assert MARKET_MAX_SIZE_GATE_BOUND is True


def test_no_trading_or_post_path_activated() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False
    assert "post_entry_order" not in CONSUMER.read_text(encoding="utf-8")
    assert "ENDPOINT_SUBMIT" not in CONSUMER.read_text(encoding="utf-8")


def test_docs_and_master_pointer() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    policy = PRIOR_POLICY.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert "MAX_SIZE_CONSUMER_BOUND=true" in spec
    assert "MAX_SIZE_FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION" in spec
    assert "MAX_SIZE_FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION" in policy
    assert "MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1=true" in section
    assert "PEAK_TRADE_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1" in mot
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "TRADING_PERFORMED=false" in spec
    assert "CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false" in spec
    assert "CURRENT_REUSABLE_MAXMKTSZ_PROVEN=false" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MAX_AVAILABLE" in spec
    assert "MAX_SIZE_BINDING_STATUS=PROVEN" in spec
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
