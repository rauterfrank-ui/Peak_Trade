"""MARGIN_MODE forensic binding and productive consumer v1.

No live trading. No POST. No margin-mode mutation. Authenticated GET only.
tdMode is not mgnMode. Empty positions are not a margin mode. acctLv and
posMode are not MARGIN_MODE. No global account margin-mode claim.
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
    DEFAULT_TD_MODE,
    ENDPOINT_ACCOUNT_POSITIONS,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS,
    GET_ENDPOINTS_PRIVATE,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    POST_ENDPOINTS_GATED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.margin_mode_consumer_v1 import (
    ACCOUNT_CONFIG_USED_AS_MARGIN_MODE_AUTHORITY,
    ACCT_LV_USED_AS_MARGIN_MODE_AUTHORITY,
    EMPTY_POSITIONS_USED_AS_MARGIN_MODE_AUTHORITY,
    FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION,
    HISTORICAL_REUSE_PATH_EXISTS,
    LEVERAGE_USED_AS_MARGIN_MODE_AUTHORITY,
    MARGIN_MODE_CONSUMER_BOUND,
    MARGIN_MODE_FAIL_CLOSED_BOUND,
    MARGIN_MODE_MUTATION_PERFORMED,
    POS_MODE_USED_AS_MARGIN_MODE_AUTHORITY,
    ZERO_NORMALIZATION_PERFORMED,
    LiveCanaryMarginModeConsumerError,
    apply_fresh_margin_mode_pretrade_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.margin_mode_observation_v1 import (
    ACCTLV_IS_NOT_MARGIN_MODE,
    EMPTY_DATA_IS_NOT_ZERO,
    HISTORICAL_BTC_INSTRUMENT_ID,
    MARGIN_MODE_AUTH_CLASS,
    MARGIN_MODE_COMPARISON_DOMAIN,
    MARGIN_MODE_CONSUMER_SCOPE,
    MARGIN_MODE_FRESHNESS_POLICY,
    MARGIN_MODE_GLOBAL_ACCOUNT_SETTING_EXISTS,
    MARGIN_MODE_NO_TS_FIELD,
    MARGIN_MODE_OUTPUT_DOMAIN,
    MARGIN_MODE_REQUIRED_ORDER_TD_MODE,
    MARGIN_MODE_SEMANTIC_CLASS_ORDER_TDMODE_CROSS,
    MARGIN_MODE_TS_AGE_BOUND,
    MARGIN_MODE_VENUE_SCOPE,
    POSMODE_IS_NOT_MARGIN_MODE,
    POSITION_MGN_MODE_STATUS_NOT_OBSERVED,
    POSITION_MGN_MODE_STATUS_OBSERVED,
    LiveCanaryMarginModeObservationError,
    account_positions_query_path_v1,
    acquire_fresh_margin_mode_observation_from_payload_v1,
    require_canonical_execution_td_mode_v1,
    utc_now_iso_v1,
    validate_fresh_margin_mode_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_flatten_order_plan_v1,
    build_minimum_valid_canary_order_plan_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.leverage_observation_v1 import (
    LEVERAGE_OUTPUT_DOMAIN,
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
    TICKER,
    _assert_no_post,
    _fake_transport,
    _max_available_plan_kwargs,
    _transport_kwargs,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_MARGIN_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md"
)
PRIOR_POS_MODE = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ORDER_PLAN = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"
SUBMIT_TRANSPORT = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
CONSUMER = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/margin_mode_consumer_v1.py"
)
OBSERVATION = REPO_ROOT / (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/margin_mode_observation_v1.py"
)
OWNER_GO = "PEAK_TRADE_MARGIN_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1"
ENDPOINT = account_positions_query_path_v1()


def _empty_payload() -> dict[str, object]:
    return {"code": "0", "msg": "", "data": []}


def _position_payload(*, mgn_mode: str = "cross", inst_id: str = DEFAULT_INSTRUMENT_ID) -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [
            {
                "instId": inst_id,
                "pos": "1",
                "mgnMode": mgn_mode,
                "posSide": "net",
            }
        ],
    }


def _gate(**kwargs: object) -> dict[str, object]:
    body: dict[str, object] = {
        "pretrade_decision_id": "decision-a",
        "payload": _empty_payload(),
        "instrument_id": DEFAULT_INSTRUMENT_ID,
        "margin_mode_domain": MARGIN_MODE_OUTPUT_DOMAIN,
        "planned_td_mode": "cross",
        "http_status": 200,
        "endpoint": ENDPOINT,
        "get_performed": True,
        "historical_reuse": False,
        "auth_header_sent": True,
        "leverage_mgn_mode": "cross",
        "acct_lv": "2",
        "pos_mode": "net_mode",
    }
    body.update(kwargs)
    return apply_fresh_margin_mode_pretrade_gate_v1(**body)  # type: ignore[arg-type]


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_empty_positions_pass_as_not_observed_not_cross() -> None:
    result = _gate()
    assert result["ok"] is True
    assert result["observation_class"] == "SUCCESS_NOT_OBSERVED"
    assert result["order_td_mode"] == "cross"
    assert result["position_mgn_mode_raw"] == ""
    assert result["position_mgn_mode_status"] == POSITION_MGN_MODE_STATUS_NOT_OBSERVED
    assert result["semantic_class"] == MARGIN_MODE_SEMANTIC_CLASS_ORDER_TDMODE_CROSS
    assert result["empty_positions_used_as_margin_mode_authority"] is False
    assert result["empty_data_is_not_zero"] is True
    assert EMPTY_DATA_IS_NOT_ZERO is True
    assert EMPTY_POSITIONS_USED_AS_MARGIN_MODE_AUTHORITY is False


def test_observed_cross_position_matches_order_tdmode() -> None:
    result = _gate(payload=_position_payload(mgn_mode="cross"))
    assert result["ok"] is True
    assert result["observation_class"] == "SUCCESS_TOKEN"
    assert result["position_mgn_mode_raw"] == "cross"
    assert result["position_mgn_mode_status"] == POSITION_MGN_MODE_STATUS_OBSERVED
    assert result["order_td_mode"] == "cross"


def test_isolated_planned_tdmode_fails_closed() -> None:
    with pytest.raises(
        LiveCanaryMarginModeConsumerError,
        match="MARGIN_MODE_REQUIRED_ORDER_TDMODE_MISMATCH:isolated",
    ):
        _gate(planned_td_mode="isolated")


def test_unknown_tdmode_fails_closed() -> None:
    with pytest.raises(LiveCanaryMarginModeConsumerError, match="MARGIN_MODE_UNKNOWN_TDMODE:cash"):
        _gate(planned_td_mode="cash")


def test_isolated_target_position_is_scoped_conflict() -> None:
    with pytest.raises(LiveCanaryMarginModeConsumerError, match="MARGIN_MODE_SCOPED_CONFLICT"):
        _gate(payload=_position_payload(mgn_mode="isolated"))


def test_missing_get_fails_closed() -> None:
    with pytest.raises(LiveCanaryMarginModeConsumerError, match="FRESH_GET_NOT_PERFORMED"):
        _gate(get_performed=False)
    assert FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION is True


def test_query_grammar_is_none() -> None:
    assert account_positions_query_path_v1() == ENDPOINT_ACCOUNT_POSITIONS
    with pytest.raises(LiveCanaryMarginModeConsumerError, match="MARGIN_MODE_QUERY_FORBIDDEN"):
        _gate(endpoint=f"{ENDPOINT}?instId={DEFAULT_INSTRUMENT_ID}")


def test_account_config_and_leverage_cannot_be_source() -> None:
    with pytest.raises(
        LiveCanaryMarginModeConsumerError, match="MARGIN_MODE_RECONSTRUCTION_SOURCE_FORBIDDEN"
    ):
        _gate(endpoint="/api/v5/account/config")
    with pytest.raises(
        LiveCanaryMarginModeConsumerError, match="MARGIN_MODE_RECONSTRUCTION_SOURCE_FORBIDDEN"
    ):
        _gate(endpoint="/api/v5/account/leverage-info?instId=x&mgnMode=cross")
    assert ACCOUNT_CONFIG_USED_AS_MARGIN_MODE_AUTHORITY is False
    assert LEVERAGE_USED_AS_MARGIN_MODE_AUTHORITY is False


def test_acctlv_and_posmode_are_not_margin_mode() -> None:
    result = _gate(acct_lv="2", pos_mode="net_mode")
    assert result["acct_lv_used_as_margin_mode_authority"] is False
    assert result["pos_mode_used_as_margin_mode_authority"] is False
    assert ACCTLV_IS_NOT_MARGIN_MODE is True
    assert POSMODE_IS_NOT_MARGIN_MODE is True
    assert ACCT_LV_USED_AS_MARGIN_MODE_AUTHORITY is False
    assert POS_MODE_USED_AS_MARGIN_MODE_AUTHORITY is False


def test_no_global_account_margin_mode_claim() -> None:
    result = _gate()
    assert result["margin_mode_global_account_setting_exists"] is False
    assert MARGIN_MODE_GLOBAL_ACCOUNT_SETTING_EXISTS is False
    assert result["venue_scope"] == "CURRENT_SINGLE_SELECTED_FUTURE_EXECUTION"
    assert result["venue_scope"] != "ACCOUNT_GLOBAL"


def test_other_instrument_mgnmode_is_not_sui_authority() -> None:
    payload = {
        "code": "0",
        "data": [{"instId": "BTC-USD_UM_XPERP-310404", "mgnMode": "isolated", "pos": "1"}],
    }
    result = _gate(payload=payload)
    assert result["position_mgn_mode_status"] == POSITION_MGN_MODE_STATUS_NOT_OBSERVED
    assert result["other_instrument_mgn_modes"] == ["isolated"]
    assert result["empty_positions_used_as_margin_mode_authority"] is False


def test_historical_btc_cannot_substitute() -> None:
    with pytest.raises(LiveCanaryMarginModeConsumerError, match="HISTORICAL_BTC_INSTRUMENT"):
        _gate(instrument_id=HISTORICAL_BTC_INSTRUMENT_ID)
    assert HISTORICAL_REUSE_PATH_EXISTS is False


def test_forbidden_set_isolated_mode_source() -> None:
    with pytest.raises(
        LiveCanaryMarginModeConsumerError, match="MARGIN_MODE_RECONSTRUCTION_SOURCE_FORBIDDEN"
    ):
        _gate(endpoint="/api/v5/account/set-isolated-mode")
    assert MARGIN_MODE_MUTATION_PERFORMED is False
    assert any("set-" in marker for marker in FORBIDDEN_MUTATION_ENDPOINT_MARKERS)


def test_typed_domain_not_mixed() -> None:
    with pytest.raises(LiveCanaryMarginModeConsumerError, match="MARGIN_MODE_DOMAIN_INCOMPATIBLE"):
        _gate(margin_mode_domain=ORDER_PLAN_QTY_DOMAIN)
    with pytest.raises(LiveCanaryMarginModeConsumerError, match="MARGIN_MODE_DOMAIN_INCOMPATIBLE"):
        _gate(margin_mode_domain=PRICE_BAND_OUTPUT_DOMAIN)
    with pytest.raises(LiveCanaryMarginModeConsumerError, match="MARGIN_MODE_DOMAIN_INCOMPATIBLE"):
        _gate(margin_mode_domain=LEVERAGE_OUTPUT_DOMAIN)
    with pytest.raises(LiveCanaryMarginModeConsumerError, match="MARGIN_MODE_DOMAIN_INCOMPATIBLE"):
        _gate(margin_mode_domain=POS_MODE_OUTPUT_DOMAIN)
    assert MARGIN_MODE_OUTPUT_DOMAIN == "ORDER_TDMODE"
    assert MARGIN_MODE_COMPARISON_DOMAIN != ORDER_PLAN_QTY_DOMAIN
    assert ZERO_NORMALIZATION_PERFORMED is False


def test_leverage_isolated_supporting_conflict() -> None:
    with pytest.raises(
        LiveCanaryMarginModeConsumerError, match="MARGIN_MODE_LEVERAGE_SCOPE_CONFLICT"
    ):
        _gate(leverage_mgn_mode="isolated")
    assert LEVERAGE_USED_AS_MARGIN_MODE_AUTHORITY is False


def test_require_canonical_execution_td_mode() -> None:
    assert require_canonical_execution_td_mode_v1("cross") == "cross"
    assert MARGIN_MODE_REQUIRED_ORDER_TD_MODE == DEFAULT_TD_MODE == "cross"
    with pytest.raises(LiveCanaryMarginModeObservationError, match="MISMATCH:isolated"):
        require_canonical_execution_td_mode_v1("isolated")


def test_order_plan_wires_margin_mode_and_preserves_typed_quantity_domain() -> None:
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=_instruments_payload(),
        ticker_payload=TICKER,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="80f621a2c4eeb531b56aafe861273b6ca05850f4",
        pretrade_decision_id="decision-plan-margin-mode",
        **_max_available_plan_kwargs(),
    )
    assert plan.quantity_domain == ORDER_PLAN_QTY_DOMAIN
    assert plan.td_mode == "cross"
    assert plan.venue_native_payload["tdMode"] == "cross"
    with pytest.raises(LiveCanaryOrderPlanError, match="MARGIN_MODE_GATE"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=_instruments_payload(),
            ticker_payload=TICKER,
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            origin_main_sha="80f621a2c4eeb531b56aafe861273b6ca05850f4",
            pretrade_decision_id="decision-plan-margin-mode-missing",
            **_max_available_plan_kwargs(margin_mode_get_performed=False),
        )
    assert MARGIN_MODE_CONSUMER_BOUND is True
    assert MARGIN_MODE_FAIL_CLOSED_BOUND is True


def test_flatten_td_mode_must_match_canonical_cross() -> None:
    payload = {
        "code": "0",
        "data": [{"instId": DEFAULT_INSTRUMENT_ID, "pos": "1", "mgnMode": "cross"}],
    }
    plan = build_minimum_valid_canary_flatten_order_plan_v1(
        positions_payload=payload,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="80f621a2c4eeb531b56aafe861273b6ca05850f4",
    )
    assert plan.td_mode == "cross"
    with pytest.raises(LiveCanaryOrderPlanError, match="MARGIN_MODE_GATE"):
        build_minimum_valid_canary_flatten_order_plan_v1(
            positions_payload=payload,
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            origin_main_sha="80f621a2c4eeb531b56aafe861273b6ca05850f4",
            td_mode="isolated",
        )


def test_submit_transport_fail_closed_before_post_when_isolated_position() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint[ENDPOINT_ACCOUNT_POSITIONS] = (
        b'{"code":"0","data":[{"instId":"SUI-USD_UM_XPERP-310404","mgnMode":"isolated","pos":"1"}]}'
    )
    with pytest.raises(LiveCanarySubmitTransportError, match="MARGIN_MODE"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)


def test_submit_transport_empty_positions_do_not_invent_cross() -> None:
    transport = _fake_transport()
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["ok"] is True
    assert any(ENDPOINT_ACCOUNT_POSITIONS in str(call.endpoint) for call in transport.calls)
    plan_body = next(call for call in transport.calls if call.method == "POST")
    assert '"tdMode":"cross"' in plan_body.body_text or "tdMode" in plan_body.body_text


def test_allowlist_private_and_no_trading() -> None:
    assert ENDPOINT_ACCOUNT_POSITIONS in GET_ENDPOINTS_PRIVATE
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False
    assert ENDPOINT_ACCOUNT_POSITIONS not in POST_ENDPOINTS_GATED


def test_observation_validate_decision_mismatch() -> None:
    obs = acquire_fresh_margin_mode_observation_from_payload_v1(
        pretrade_decision_id="decision-one",
        payload=_empty_payload(),
        instrument_id=DEFAULT_INSTRUMENT_ID,
        planned_td_mode="cross",
        observed_at_utc=utc_now_iso_v1(),
        endpoint=ENDPOINT,
        http_status=200,
        get_performed=True,
    )
    with pytest.raises(
        LiveCanaryMarginModeObservationError, match="OBSERVATION_DECISION_ID_MISMATCH"
    ):
        validate_fresh_margin_mode_observation_v1(
            obs,
            pretrade_decision_id="decision-two",
            instrument_id=DEFAULT_INSTRUMENT_ID,
            margin_mode_domain=MARGIN_MODE_OUTPUT_DOMAIN,
            planned_td_mode="cross",
        )
    assert obs.venue_scope == MARGIN_MODE_VENUE_SCOPE
    assert obs.consumer_scope == MARGIN_MODE_CONSUMER_SCOPE
    assert MARGIN_MODE_AUTH_CLASS == "AUTHENTICATED_PRIVATE_GET"
    assert MARGIN_MODE_NO_TS_FIELD is True
    assert MARGIN_MODE_TS_AGE_BOUND == "UNBOUND"
    assert MARGIN_MODE_FRESHNESS_POLICY == "FRESH_GET_PER_PRETRADE_DECISION"


def test_docs_and_master_pointer() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    prior = PRIOR_POS_MODE.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert (
        "MARGIN_MODE_CANONICAL_DEFINITION=CURRENT_SINGLE_SELECTED_FUTURE_EXECUTION_TDMODE" in spec
    )
    assert "MARGIN_MODE_ENDPOINT=/api/v5/account/positions" in spec
    assert "MARGIN_MODE_BINDING_STATUS=PROVEN" in spec
    assert "MARGIN_MODE_GLOBAL_ACCOUNT_SETTING_EXISTS=false" in spec
    assert "MARGIN_MODE_VENUE_SCOPE=CURRENT_SINGLE_SELECTED_FUTURE_EXECUTION" in spec
    assert "MARGIN_MODE_OUTPUT_DOMAIN=ORDER_TDMODE" in spec
    assert "MARGIN_MODE_AUTH_CLASS=AUTHENTICATED_PRIVATE_GET" in spec
    assert "ORDER_PLAN_TD_MODE=cross" in spec
    assert "MAX_AVAILABLE_TD_MODE=cross" in spec
    assert "FLATTEN_TD_MODE=cross" in spec
    assert "EXECUTION_TD_MODE=cross" in spec
    assert "PLANNING_EXECUTION_TD_MODE_CONSISTENT=true" in spec
    assert "EMPTY_POSITIONS_USED_AS_MARGIN_MODE_AUTHORITY=false" in spec
    assert "ACCOUNT_CONFIG_USED_AS_MARGIN_MODE_AUTHORITY=false" in spec
    assert "ACCT_LV_USED_AS_MARGIN_MODE_AUTHORITY=false" in spec
    assert "POS_MODE_USED_AS_MARGIN_MODE_AUTHORITY=false" in spec
    assert "LEVERAGE_USED_AS_MARGIN_MODE_AUTHORITY=false" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=AVAILABLE_MARGIN" in spec
    assert "MARGIN_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1=true" in section
    assert "PEAK_TRADE_MARGIN_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1" in mot
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=MARGIN_MODE" in prior
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "TRADING_PERFORMED=false" in spec
    assert "PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false" in spec
    assert ORDER_PLAN.is_file()
    assert SUBMIT_TRANSPORT.is_file()
    assert CONSUMER.is_file()
    assert OBSERVATION.is_file()
    assert "apply_fresh_margin_mode_pretrade_gate_v1" in ORDER_PLAN.read_text(encoding="utf-8")
    assert "account_positions_query_path_v1" in SUBMIT_TRANSPORT.read_text(encoding="utf-8")
