"""POS_MODE forensic binding and productive consumer v1.

No live trading. No POST. No set-position-mode. Authenticated GET only.
posMode raw net_mode is not posSide net. acctLv is not POS_MODE.
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
    ENDPOINT_ACCOUNT_CONFIG,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS,
    GET_ENDPOINTS_PRIVATE,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    POST_ENDPOINTS_GATED,
    POSITION_COUNT_LIMIT,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_consumer_v1 import (
    DEFAULT_POS_MODE_USED,
    FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION,
    HISTORICAL_POS_MODE_REUSED,
    HISTORICAL_REUSE_PATH_EXISTS,
    LEVERAGE_POSSIDE_NET_REUSED_AS_POS_MODE_PROOF,
    MGNMODE_CROSS_REUSED_AS_POS_MODE_PROOF,
    POS_MODE_CONSUMER_BOUND,
    POS_MODE_FAIL_CLOSED_BOUND,
    SET_POSITION_MODE_EXECUTED,
    TDMODE_CROSS_REUSED_AS_POS_MODE_PROOF,
    ZERO_NORMALIZATION_PERFORMED,
    LiveCanaryPosModeConsumerError,
    apply_fresh_pos_mode_pretrade_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1 import (
    ACCTLV_IS_NOT_POS_MODE,
    HISTORICAL_BTC_INSTRUMENT_ID,
    POS_MODE_AUTH_CLASS,
    POS_MODE_COMPARISON_DOMAIN,
    POS_MODE_CONSUMER_SCOPE,
    POS_MODE_FRESHNESS_POLICY,
    POS_MODE_NO_TS_FIELD,
    POS_MODE_OUTPUT_DOMAIN,
    POS_MODE_REQUIRED_VALUE,
    POS_MODE_SEMANTIC_CLASS,
    POS_MODE_TS_AGE_BOUND,
    POS_MODE_VENUE_SCOPE,
    POSSIDE_NET_IS_NOT_POS_MODE,
    LiveCanaryPosModeObservationError,
    account_config_query_path_v1,
    acquire_fresh_pos_mode_observation_from_payload_v1,
    validate_fresh_pos_mode_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_order_plan_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.leverage_observation_v1 import (
    LEVERAGE_OUTPUT_DOMAIN,
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
    "docs/ops/specs/PEAK_TRADE_POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md"
)
PRIOR_LEVERAGE = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ORDER_PLAN = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"
SUBMIT_TRANSPORT = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
CONSUMER = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pos_mode_consumer_v1.py"
)
OBSERVATION = REPO_ROOT / (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/pos_mode_observation_v1.py"
)
OWNER_GO = "PEAK_TRADE_POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1"
ENDPOINT = account_config_query_path_v1()


def _payload(*, pos_mode: str = "net_mode", acct_lv: str = "2") -> dict[str, object]:
    return {
        "code": "0",
        "msg": "",
        "data": [
            {
                "uid": "856964404452495999",
                "acctLv": acct_lv,
                "posMode": pos_mode,
                "perm": "read_only,trade",
            }
        ],
    }


def _gate(**kwargs: object) -> dict[str, object]:
    body: dict[str, object] = {
        "pretrade_decision_id": "decision-a",
        "payload": _payload(),
        "instrument_id": DEFAULT_INSTRUMENT_ID,
        "pos_mode_domain": POS_MODE_OUTPUT_DOMAIN,
        "http_status": 200,
        "endpoint": ENDPOINT,
        "get_performed": True,
        "historical_reuse": False,
        "auth_header_sent": True,
        "td_mode": "cross",
        "mgn_mode": "cross",
        "pos_side": "net",
        "max_positions": POSITION_COUNT_LIMIT,
        "single_selected_future": True,
    }
    body.update(kwargs)
    return apply_fresh_pos_mode_pretrade_gate_v1(**body)  # type: ignore[arg-type]


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_valid_required_pos_mode_passes() -> None:
    result = _gate()
    assert result["ok"] is True
    assert result["observation_class"] == "SUCCESS_TOKEN"
    assert result["pos_mode"] == "net_mode"
    assert result["pos_mode_raw"] == "net_mode"
    assert result["semantic_class"] == POS_MODE_SEMANTIC_CLASS
    assert result["venue_scope"] == POS_MODE_VENUE_SCOPE
    assert result["consumer_scope"] == POS_MODE_CONSUMER_SCOPE
    assert result["acct_lv_bound"] is False
    assert result["acct_lv_raw"] == "2"


def test_exact_venue_token_parsing() -> None:
    result = _gate()
    assert result["pos_mode_raw"] == "net_mode"
    assert result["pos_mode"] != "net"
    assert result["required_value"] == "net_mode"


def test_required_peak_trade_value_match() -> None:
    assert POS_MODE_REQUIRED_VALUE == "net_mode"
    assert _gate()["pos_mode"] == POS_MODE_REQUIRED_VALUE


def test_long_short_mode_fails_closed() -> None:
    with pytest.raises(
        LiveCanaryPosModeConsumerError, match="POS_MODE_REQUIRED_VALUE_MISMATCH:long_short_mode"
    ):
        _gate(payload=_payload(pos_mode="long_short_mode"))


def test_missing_and_empty_pos_mode_fail_closed() -> None:
    missing = _payload()
    del missing["data"][0]["posMode"]  # type: ignore[index]
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_FIELD_MISSING:posMode"):
        _gate(payload=missing)
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_FIELD_MISSING:posMode"):
        _gate(payload=_payload(pos_mode=""))
    null_row = _payload()
    null_row["data"][0]["posMode"] = None  # type: ignore[index]
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_FIELD_NULL:posMode"):
        _gate(payload=null_row)


def test_posside_token_net_is_not_pos_mode() -> None:
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_POSSIDE_TOKEN_REJECTED:net"):
        _gate(payload=_payload(pos_mode="net"))
    assert POSSIDE_NET_IS_NOT_POS_MODE is True
    assert LEVERAGE_POSSIDE_NET_REUSED_AS_POS_MODE_PROOF is False


def test_malformed_unknown_pos_mode_fail_closed() -> None:
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_UNKNOWN_TOKEN:hedge"):
        _gate(payload=_payload(pos_mode="hedge"))
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_UNKNOWN_TOKEN:one_way"):
        _gate(payload=_payload(pos_mode="one_way"))
    assert DEFAULT_POS_MODE_USED is False


def test_http_venue_empty_data_ambiguous_and_auth_fail_closed() -> None:
    with pytest.raises(LiveCanaryPosModeConsumerError, match="FRESH_GET_NOT_PERFORMED"):
        _gate(get_performed=False)
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_NETWORK_ERROR"):
        _gate(http_status=500)
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_AUTH_ERROR"):
        _gate(http_status=401)
    with pytest.raises(LiveCanaryPosModeConsumerError, match="VENUE_CODE_UNSUCCESSFUL"):
        _gate(payload={"code": "1", "data": _payload()["data"]})
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_DATA_MISSING"):
        _gate(payload={"code": "0", "data": []})
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_AMBIGUOUS_CONFIG_OBJECT"):
        _gate(
            payload={
                "code": "0",
                "data": [_payload()["data"][0], _payload()["data"][0]],
            }
        )
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_AUTH_HEADER_REQUIRED"):
        _gate(auth_header_sent=False)
    with pytest.raises(LiveCanaryPosModeConsumerError, match="HISTORICAL_POS_MODE_REUSE"):
        _gate(historical_reuse=True)
    assert FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION is True
    assert HISTORICAL_REUSE_PATH_EXISTS is False


def test_query_grammar_is_none() -> None:
    assert account_config_query_path_v1() == ENDPOINT_ACCOUNT_CONFIG
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_QUERY_FORBIDDEN"):
        _gate(endpoint=f"{ENDPOINT}?instId={DEFAULT_INSTRUMENT_ID}")


def test_historical_btc_cannot_substitute() -> None:
    with pytest.raises(LiveCanaryPosModeConsumerError, match="HISTORICAL_BTC_INSTRUMENT"):
        _gate(instrument_id=HISTORICAL_BTC_INSTRUMENT_ID)
    with pytest.raises(LiveCanaryPosModeConsumerError, match="HISTORICAL_BTC"):
        _gate(endpoint=f"{ENDPOINT}?note={HISTORICAL_BTC_INSTRUMENT_ID}")
    assert HISTORICAL_POS_MODE_REUSED is False


def test_leverage_posside_tdmode_mgnmode_cannot_substitute() -> None:
    result = _gate(pos_side="net", td_mode="cross", mgn_mode="cross")
    assert result["ok"] is True
    assert result["posside_net_is_not_pos_mode"] is True
    assert result["tdmode_cross_is_not_pos_mode"] is True
    assert result["mgnmode_cross_is_not_pos_mode"] is True
    assert result["leverage_posside_net_reused_as_pos_mode_proof"] is False
    assert TDMODE_CROSS_REUSED_AS_POS_MODE_PROOF is False
    assert MGNMODE_CROSS_REUSED_AS_POS_MODE_PROOF is False
    with pytest.raises(
        LiveCanaryPosModeConsumerError, match="POS_MODE_RECONSTRUCTION_SOURCE_FORBIDDEN"
    ):
        _gate(endpoint="/api/v5/account/leverage-info?instId=x&mgnMode=cross")


def test_max_positions_and_single_selected_future_cannot_substitute() -> None:
    result = _gate(max_positions=1, single_selected_future=True)
    assert result["ok"] is True
    assert result["max_positions_is_not_pos_mode"] is True
    assert result["single_selected_future_is_not_pos_mode"] is True
    assert POSITION_COUNT_LIMIT == 1


def test_acctlv_is_not_pos_mode() -> None:
    result = _gate(payload=_payload(acct_lv="2"))
    assert result["acct_lv_raw"] == "2"
    assert result["acct_lv_bound"] is False
    assert ACCTLV_IS_NOT_POS_MODE is True
    assert "acctLv" in result["unbound_account_config_fields"]
    assert "uid" in result["unbound_account_config_fields"]


def test_forbidden_set_position_mode_source() -> None:
    with pytest.raises(
        LiveCanaryPosModeConsumerError, match="POS_MODE_RECONSTRUCTION_SOURCE_FORBIDDEN"
    ):
        _gate(endpoint="/api/v5/account/set-position-mode")
    assert SET_POSITION_MODE_EXECUTED is False
    assert "/api/v5/account/set-position-mode" not in POST_ENDPOINTS_GATED
    assert any("set-" in marker for marker in FORBIDDEN_MUTATION_ENDPOINT_MARKERS)


def test_typed_domain_not_mixed_with_quantity_or_price() -> None:
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_DOMAIN_INCOMPATIBLE"):
        _gate(pos_mode_domain=ORDER_PLAN_QTY_DOMAIN)
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_DOMAIN_INCOMPATIBLE"):
        _gate(pos_mode_domain=PRICE_BAND_OUTPUT_DOMAIN)
    with pytest.raises(LiveCanaryPosModeConsumerError, match="POS_MODE_DOMAIN_INCOMPATIBLE"):
        _gate(pos_mode_domain=LEVERAGE_OUTPUT_DOMAIN)
    assert POS_MODE_OUTPUT_DOMAIN == "ACCOUNT_POS_MODE"
    assert POS_MODE_COMPARISON_DOMAIN != ORDER_PLAN_QTY_DOMAIN
    assert ZERO_NORMALIZATION_PERFORMED is False


def test_order_plan_wires_pos_mode_and_preserves_typed_quantity_domain() -> None:
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=_instruments_payload(),
        ticker_payload=TICKER,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="73b8f7e06d12a1e446b5ac0a4289531e35e3642e",
        pretrade_decision_id="decision-plan-pos-mode",
        **_max_available_plan_kwargs(),
    )
    assert plan.quantity_domain == ORDER_PLAN_QTY_DOMAIN
    assert "posMode" not in plan.venue_native_payload
    assert "posSide" not in plan.venue_native_payload
    with pytest.raises(LiveCanaryOrderPlanError, match="POS_MODE_GATE"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=_instruments_payload(),
            ticker_payload=TICKER,
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            origin_main_sha="73b8f7e06d12a1e446b5ac0a4289531e35e3642e",
            pretrade_decision_id="decision-plan-pos-mode-missing",
            **_max_available_plan_kwargs(pos_mode_get_performed=False),
        )
    assert POS_MODE_CONSUMER_BOUND is True
    assert POS_MODE_FAIL_CLOSED_BOUND is True


def test_submit_transport_fail_closed_before_post_when_pos_mode_fails() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint[ENDPOINT_ACCOUNT_CONFIG] = b'{"code":"0","data":[]}'
    with pytest.raises(LiveCanarySubmitTransportError, match="POS_MODE"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)
    assert any(ENDPOINT_ACCOUNT_CONFIG in str(call.endpoint) for call in transport.calls)


def test_submit_transport_long_short_does_not_post() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint[ENDPOINT_ACCOUNT_CONFIG] = (
        b'{"code":"0","data":[{"uid":"x","acctLv":"2","posMode":"long_short_mode"}]}'
    )
    with pytest.raises(LiveCanarySubmitTransportError, match="POS_MODE"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)


def test_allowlist_private_and_no_trading() -> None:
    assert ENDPOINT_ACCOUNT_CONFIG in GET_ENDPOINTS_PRIVATE
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False
    consumer = CONSUMER.read_text(encoding="utf-8")
    observation = OBSERVATION.read_text(encoding="utf-8")
    assert "post_entry_order" not in consumer
    assert "set-position-mode" in observation
    assert "apply_fresh_pos_mode_pretrade_gate_v1" in ORDER_PLAN.read_text(encoding="utf-8")
    assert "account_config_query_path_v1" in SUBMIT_TRANSPORT.read_text(encoding="utf-8")
    assert "DEFAULT_POS_MODE=net" not in consumer
    assert "DEFAULT_POS_MODE=net_mode" not in observation


def test_observation_bound_to_decision_and_account_scope() -> None:
    obs = acquire_fresh_pos_mode_observation_from_payload_v1(
        pretrade_decision_id="decision-one",
        payload=_payload(),
        observed_at_utc="2026-08-30T00:00:00.000000Z",
        endpoint=ENDPOINT,
        http_status=200,
        get_performed=True,
    )
    with pytest.raises(LiveCanaryPosModeObservationError, match="OBSERVATION_DECISION_ID_MISMATCH"):
        validate_fresh_pos_mode_observation_v1(
            obs,
            pretrade_decision_id="decision-two",
            instrument_id=DEFAULT_INSTRUMENT_ID,
            pos_mode_domain=POS_MODE_OUTPUT_DOMAIN,
        )
    assert obs.venue_scope == "ACCOUNT_GLOBAL"
    assert obs.consumer_scope == "CURRENT_SUI_PRETRADE_CONSUMER"
    assert POS_MODE_AUTH_CLASS == "AUTHENTICATED_PRIVATE_GET"
    assert POS_MODE_NO_TS_FIELD is True
    assert POS_MODE_TS_AGE_BOUND == "UNBOUND"
    assert POS_MODE_FRESHNESS_POLICY == ("CONFIGURATION_SCOPED_CURRENT_READ_PER_PRETRADE_DECISION")


def test_docs_and_master_pointer() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    prior = PRIOR_LEVERAGE.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert "POS_MODE_CANONICAL_DEFINITION=ACCOUNT_POS_MODE" in spec
    assert "POS_MODE_ENDPOINT=/api/v5/account/config" in spec
    assert "POS_MODE_BINDING_STATUS=PROVEN" in spec
    assert (
        "POS_MODE_FRESHNESS_POLICY=CONFIGURATION_SCOPED_CURRENT_READ_PER_PRETRADE_DECISION" in spec
    )
    assert "POS_MODE_TS_AGE_BOUND=UNBOUND" in spec
    assert "POS_MODE_OUTPUT_DOMAIN=ACCOUNT_POS_MODE" in spec
    assert "POS_MODE_AUTH_CLASS=AUTHENTICATED_PRIVATE_GET" in spec
    assert "POS_MODE_VENUE_SCOPE=ACCOUNT_GLOBAL" in spec
    assert "POS_MODE_REQUIRED_VALUE=net_mode" in spec
    assert "POS_MODE_RAW_VALUE=net_mode" in spec
    assert "LEVERAGE_POSSIDE_NET_REUSED_AS_POS_MODE_PROOF=false" in spec
    assert "SET_POSITION_MODE_EXECUTED=false" in spec
    assert "HISTORICAL_POS_MODE_REUSED=false" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MARGIN_MODE" in spec
    assert "POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1=true" in section
    assert "PEAK_TRADE_POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1" in mot
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=POS_MODE" in prior
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "TRADING_PERFORMED=false" in spec
    assert "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false" in spec
    assert "POS_SIDE_INFERENCE_USED_AS_AUTHORITY=false" in spec
