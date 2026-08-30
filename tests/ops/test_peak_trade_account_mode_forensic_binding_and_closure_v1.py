"""ACCOUNT_MODE forensic binding and productive consumer v1.

No live trading. No POST. No new GET. Reuses committed POS_MODE
account-config evidence. acctLv=2 is not posMode, tdMode, mgnMode,
leverage, settleCcy, instrument state, or live authorization.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.capability_11_9_live_canary_order_execution_v1.constants_v1 import (
    LIVE_EXECUTION_REACHABLE,
    TESTNET_EXECUTION_REACHABLE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.account_mode_consumer_v1 import (
    ACCOUNT_MODE_CONSUMER_BOUND,
    ACCOUNT_MODE_FAIL_CLOSED_BOUND,
    ACCOUNT_MODE_MUTATION_PERFORMED,
    DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF,
    FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION,
    HISTORICAL_REUSE_PATH_EXISTS,
    INSTRUMENT_STATE_IS_NOT_ACCOUNT_MODE,
    MGNMODE_CROSS_IS_NOT_ACCOUNT_MODE,
    POS_MODE_IS_NOT_ACCOUNT_MODE,
    SET_ACCOUNT_LEVEL_EXECUTED,
    TDMODE_CROSS_IS_NOT_ACCOUNT_MODE,
    LiveCanaryAccountModeConsumerError,
    apply_fresh_account_mode_pretrade_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.account_mode_observation_v1 import (
    ACCOUNT_MODE_AUTH_CLASS,
    ACCOUNT_MODE_FRESHNESS_POLICY,
    ACCOUNT_MODE_OUTPUT_DOMAIN,
    ACCOUNT_MODE_REQUIRED_VALUE,
    ACCOUNT_MODE_SEMANTIC_CLASS,
    ACCOUNT_MODE_TS_AGE_BOUND,
    COMMITTED_POS_MODE_SNAPSHOT_RELATIVE,
    HISTORICAL_BTC_PACK,
    OBSERVATION_CLASS_SUCCESS_TOKEN,
    LiveCanaryAccountModeObservationError,
    acquire_fresh_account_mode_observation_from_payload_v1,
    account_mode_query_path_v1,
    bind_account_mode_from_committed_pos_mode_pack_v1,
    utc_now_iso_v1,
    validate_fresh_account_mode_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    REUSED_BINDING_ACCOUNT_SCOPE,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_flatten_order_plan_v1,
    build_minimum_valid_canary_order_plan_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_consumer_v1 import (
    apply_fresh_pos_mode_pretrade_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1 import (
    POS_MODE_OUTPUT_DOMAIN,
    account_config_query_path_v1,
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
    POS_MODE,
    TICKER,
    _assert_no_post,
    _fake_transport,
    _max_available_plan_kwargs,
    _transport_kwargs,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_ACCOUNT_MODE_FORENSIC_BINDING_AND_CLOSURE_V1.md"
)
PRIOR_INSTRUMENT_STATE = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_INSTRUMENT_STATE_FORENSIC_BINDING_AND_CLOSURE_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ORDER_PLAN = REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"
SUBMIT_TRANSPORT = (
    REPO_ROOT / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
CONSUMER = REPO_ROOT / (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/account_mode_consumer_v1.py"
)
OBSERVATION = REPO_ROOT / (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/account_mode_observation_v1.py"
)
OWNER_GO = "PEAK_TRADE_POST_6160_ACCOUNT_MODE_FORENSIC_BINDING_AND_CLOSURE_V1"
ENDPOINT = account_mode_query_path_v1()


def _payload(
    *,
    acct_lv: object = "2",
    uid: object = REUSED_BINDING_ACCOUNT_SCOPE,
    pos_mode: str = "net_mode",
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "uid": uid,
        "acctLv": acct_lv,
        "posMode": pos_mode,
        "perm": "read_only,trade",
    }
    if extra:
        row.update(extra)
    return {"code": "0", "msg": "", "data": [row]}


def _gate(**kwargs: object) -> dict[str, object]:
    body: dict[str, object] = {
        "pretrade_decision_id": "decision-a",
        "payload": _payload(),
        "instrument_id": DEFAULT_INSTRUMENT_ID,
        "account_mode_domain": ACCOUNT_MODE_OUTPUT_DOMAIN,
        "http_status": 200,
        "endpoint": ENDPOINT,
        "get_performed": True,
        "historical_reuse": False,
        "auth_header_sent": True,
        "td_mode": "cross",
        "mgn_mode": "cross",
        "pos_mode": "net_mode",
    }
    body.update(kwargs)
    return apply_fresh_account_mode_pretrade_gate_v1(**body)  # type: ignore[arg-type]


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_exact_acctlv_2_is_positive_and_not_confused_with_pos_mode() -> None:
    result = _gate()
    assert result["ok"] is True
    assert result["observation_class"] == OBSERVATION_CLASS_SUCCESS_TOKEN
    assert result["acct_lv_raw"] == "2"
    assert result["acct_lv"] == ACCOUNT_MODE_REQUIRED_VALUE
    assert result["semantic_class"] == ACCOUNT_MODE_SEMANTIC_CLASS
    assert result["uid_raw"] == REUSED_BINDING_ACCOUNT_SCOPE
    assert result["account_identity_bound"] is True
    assert result["environment_bound"] is True
    assert result["provenance_bound"] is True
    assert result["all_required_metadata_edges_bound"] is True
    assert result["pos_mode_bound"] is False
    assert result["pos_mode_is_not_account_mode"] is True
    assert POS_MODE_IS_NOT_ACCOUNT_MODE is True
    assert TDMODE_CROSS_IS_NOT_ACCOUNT_MODE is True
    assert MGNMODE_CROSS_IS_NOT_ACCOUNT_MODE is True
    assert INSTRUMENT_STATE_IS_NOT_ACCOUNT_MODE is True
    assert DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF is True
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert result["freshness_policy"] == ACCOUNT_MODE_FRESHNESS_POLICY
    assert result["ts_age_bound"] == ACCOUNT_MODE_TS_AGE_BOUND == "UNBOUND"
    assert result["source_evidence"] == COMMITTED_POS_MODE_SNAPSHOT_RELATIVE
    assert SET_ACCOUNT_LEVEL_EXECUTED is False
    assert ACCOUNT_MODE_MUTATION_PERFORMED is False


def test_pos_mode_consumer_still_leaves_acctlv_unbound() -> None:
    result = apply_fresh_pos_mode_pretrade_gate_v1(
        pretrade_decision_id="decision-a",
        payload=_payload(),
        instrument_id=DEFAULT_INSTRUMENT_ID,
        pos_mode_domain=POS_MODE_OUTPUT_DOMAIN,
        http_status=200,
        endpoint=account_config_query_path_v1(),
        get_performed=True,
        auth_header_sent=True,
    )
    assert result["acct_lv_raw"] == "2"
    assert result["acct_lv_bound"] is False


@pytest.mark.parametrize("raw", ["1", "3", "4"])
def test_documented_negative_acctlv_fail_closed(raw: str) -> None:
    with pytest.raises(
        LiveCanaryAccountModeConsumerError, match=f"ACCOUNT_MODE_NOT_ADMISSIBLE:{raw}"
    ):
        _gate(payload=_payload(acct_lv=raw))


def test_missing_acctlv_fails_closed() -> None:
    payload = _payload()
    del payload["data"][0]["acctLv"]  # type: ignore[index]
    with pytest.raises(
        LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_FIELD_MISSING:acctLv"
    ):
        _gate(payload=payload)


def test_empty_acctlv_fails_closed() -> None:
    with pytest.raises(LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_FIELD_EMPTY:acctLv"):
        _gate(payload=_payload(acct_lv=""))
    with pytest.raises(LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_FIELD_EMPTY:acctLv"):
        _gate(payload=_payload(acct_lv="  2  "))


def test_null_and_wrong_type_fail_closed() -> None:
    payload = _payload()
    payload["data"][0]["acctLv"] = None  # type: ignore[index]
    with pytest.raises(LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_FIELD_NULL:acctLv"):
        _gate(payload=payload)
    with pytest.raises(
        LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_FIELD_WRONG_TYPE:acctLv"
    ):
        _gate(payload=_payload(acct_lv=2))


def test_unknown_enum_fails_closed() -> None:
    with pytest.raises(
        LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_UNKNOWN_ENUM:futures"
    ):
        _gate(payload=_payload(acct_lv="futures"))
    with pytest.raises(
        LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_UNKNOWN_ENUM:FUTURES"
    ):
        _gate(payload=_payload(acct_lv="FUTURES"))
    with pytest.raises(LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_UNKNOWN_ENUM:5"):
        _gate(payload=_payload(acct_lv="5"))


def test_wrong_endpoint_and_wrong_account_fail_closed() -> None:
    with pytest.raises(LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_ENDPOINT_MISMATCH"):
        _gate(endpoint="/api/v5/account/bills")
    with pytest.raises(
        LiveCanaryAccountModeConsumerError,
        match="ACCOUNT_MODE_RECONSTRUCTION_SOURCE_FORBIDDEN:account/positions",
    ):
        _gate(endpoint="/api/v5/account/positions")
    with pytest.raises(
        LiveCanaryAccountModeConsumerError,
        match="ACCOUNT_MODE_RECONSTRUCTION_SOURCE_FORBIDDEN:leverage-info",
    ):
        _gate(endpoint="/api/v5/account/leverage-info")
    with pytest.raises(LiveCanaryAccountModeConsumerError, match="ACCOUNT_IDENTITY_MISMATCH"):
        _gate(payload=_payload(uid="000000000000000000"))


def test_wrong_environment_and_demo_host_fail_closed() -> None:
    with pytest.raises(LiveCanaryAccountModeConsumerError, match="REST_HOST_NOT_PRODUCTION_EEA"):
        _gate(rest_host="demo.okx.com")
    with pytest.raises(LiveCanaryAccountModeConsumerError, match="REST_HOST_NOT_PRODUCTION_EEA"):
        _gate(rest_host="www.okx.com")


def test_stale_historical_reuse_and_gate20_fail_closed() -> None:
    with pytest.raises(
        LiveCanaryAccountModeConsumerError, match="HISTORICAL_ACCOUNT_MODE_REUSE_FORBIDDEN"
    ):
        _gate(historical_reuse=True)
    with pytest.raises(
        LiveCanaryAccountModeConsumerError,
        match="HISTORICAL_BTC_ACCOUNT_MODE_PACK_REUSE_FORBIDDEN",
    ):
        _gate(pretrade_decision_id=f"reuse-{HISTORICAL_BTC_PACK}")
    with pytest.raises(
        LiveCanaryAccountModeConsumerError,
        match="HISTORICAL_GATE20_STATUS_IS_NOT_CURRENT_AUTHORITY",
    ):
        _gate(
            pretrade_decision_id=(
                "SATISFIED_HISTORICAL_ACCOUNT_WIDE_GET_acctLv=2_NOT_REOBSERVED_POST_SUI"
            )
        )
    assert HISTORICAL_REUSE_PATH_EXISTS is False


def test_missing_get_auth_and_venue_failure() -> None:
    with pytest.raises(LiveCanaryAccountModeConsumerError, match="FRESH_GET_NOT_PERFORMED"):
        _gate(get_performed=False)
    with pytest.raises(
        LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_AUTH_HEADER_REQUIRED"
    ):
        _gate(auth_header_sent=False)
    with pytest.raises(LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_NETWORK_ERROR"):
        _gate(http_status=500)
    with pytest.raises(
        LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_VENUE_CODE_UNSUCCESSFUL"
    ):
        _gate(payload={"code": "1", "data": []})
    assert FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION is True


def test_ambiguous_and_malformed_fail_closed() -> None:
    with pytest.raises(LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_DATA_MISSING"):
        _gate(payload={"code": "0", "data": []})
    row = _payload()["data"][0]  # type: ignore[index]
    with pytest.raises(
        LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_AMBIGUOUS_CONFIG_OBJECT"
    ):
        _gate(payload={"code": "0", "data": [row, dict(row)]})
    conflicted = {"code": "0", "data": [row, {**dict(row), "acctLv": "3"}]}
    with pytest.raises(
        LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_AMBIGUOUS_CONFIG_OBJECT"
    ):
        _gate(payload=conflicted)
    with pytest.raises(LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_MALFORMED"):
        _gate(payload={"code": "0", "data": {"acctLv": "2"}})


def test_typed_domain_not_mixed() -> None:
    with pytest.raises(
        LiveCanaryAccountModeConsumerError, match="ACCOUNT_MODE_DOMAIN_INCOMPATIBLE"
    ):
        _gate(account_mode_domain=ORDER_PLAN_QTY_DOMAIN)


def test_committed_pos_mode_pack_binds_without_network() -> None:
    validated = bind_account_mode_from_committed_pos_mode_pack_v1(
        repo_root=REPO_ROOT,
        pretrade_decision_id="account-mode-forensic-binding-sui-20260830T0704Z",
    )
    assert validated.acct_lv == "2"
    assert validated.semantic_class == "FUTURES_MODE"
    assert validated.account_identity_bound is True
    assert validated.environment_bound is True
    assert validated.provenance_bound is True
    assert validated.raw.uid_raw == REUSED_BINDING_ACCOUNT_SCOPE
    assert validated.raw.source_evidence == COMMITTED_POS_MODE_SNAPSHOT_RELATIVE
    assert validated.raw.endpoint == "/api/v5/account/config"


def test_order_plan_wires_account_mode_after_instrument_state() -> None:
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=_instruments_payload(),
        ticker_payload=TICKER,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="996f92bf5555237a96f9dc81b9bf4bb4445c12b7",
        pretrade_decision_id="decision-plan-account-mode",
        **_max_available_plan_kwargs(),
    )
    assert plan.quantity_domain == ORDER_PLAN_QTY_DOMAIN
    missing_state = _instruments_payload()
    del missing_state["data"][0]["state"]  # type: ignore[index]
    with pytest.raises(LiveCanaryOrderPlanError, match="INSTRUMENT_STATE_GATE"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=missing_state,
            ticker_payload=TICKER,
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            origin_main_sha="996f92bf5555237a96f9dc81b9bf4bb4445c12b7",
            pretrade_decision_id="decision-plan-account-mode-before-state",
            **_max_available_plan_kwargs(),
        )
    mutated = dict(POS_MODE)
    mutated["data"] = [{**dict(POS_MODE["data"][0]), "acctLv": "3"}]
    with pytest.raises(LiveCanaryOrderPlanError, match="ACCOUNT_MODE_GATE"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=_instruments_payload(),
            ticker_payload=TICKER,
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            origin_main_sha="996f92bf5555237a96f9dc81b9bf4bb4445c12b7",
            pretrade_decision_id="decision-plan-account-mode-negative",
            **_max_available_plan_kwargs(pos_mode_payload=mutated),
        )
    assert ACCOUNT_MODE_CONSUMER_BOUND is True
    assert ACCOUNT_MODE_FAIL_CLOSED_BOUND is True


def test_flatten_does_not_consume_account_mode_gate() -> None:
    payload = {
        "code": "0",
        "data": [{"instId": DEFAULT_INSTRUMENT_ID, "pos": "1", "mgnMode": "cross"}],
    }
    plan = build_minimum_valid_canary_flatten_order_plan_v1(
        positions_payload=payload,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="996f92bf5555237a96f9dc81b9bf4bb4445c12b7",
    )
    assert plan.td_mode == "cross"


def test_submit_transport_fail_closed_before_post_when_acctlv_not_2() -> None:
    import json

    transport = _fake_transport()
    transport.bodies_by_endpoint["/api/v5/account/config"] = json.dumps(
        _payload(acct_lv="3")
    ).encode()
    with pytest.raises(LiveCanarySubmitTransportError, match="ACCOUNT_MODE"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)


def test_submit_transport_reuses_account_config_get_without_second_fetch() -> None:
    transport = _fake_transport()
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["ok"] is True
    config_gets = [
        call for call in transport.calls if str(call.endpoint).startswith("/api/v5/account/config")
    ]
    assert len(config_gets) == 1


def test_allowlist_and_no_trading() -> None:
    assert ENDPOINT == "/api/v5/account/config"
    assert account_mode_query_path_v1() == account_config_query_path_v1()
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_EXECUTION_REACHABLE is False
    assert TESTNET_EXECUTION_REACHABLE is False
    assert any("set-" in marker for marker in FORBIDDEN_MUTATION_ENDPOINT_MARKERS)


def test_observation_validate_decision_mismatch() -> None:
    obs = acquire_fresh_account_mode_observation_from_payload_v1(
        pretrade_decision_id="decision-one",
        payload=_payload(),
        instrument_id=DEFAULT_INSTRUMENT_ID,
        observed_at_utc=utc_now_iso_v1(),
        endpoint=ENDPOINT,
        http_status=200,
        get_performed=True,
    )
    with pytest.raises(
        LiveCanaryAccountModeObservationError, match="OBSERVATION_DECISION_ID_MISMATCH"
    ):
        validate_fresh_account_mode_observation_v1(
            obs,
            pretrade_decision_id="decision-two",
            instrument_id=DEFAULT_INSTRUMENT_ID,
            account_mode_domain=ACCOUNT_MODE_OUTPUT_DOMAIN,
        )
    assert ACCOUNT_MODE_AUTH_CLASS == "AUTHENTICATED_PRIVATE_GET"
    assert ACCOUNT_MODE_TS_AGE_BOUND == "UNBOUND"
    assert (
        ACCOUNT_MODE_FRESHNESS_POLICY == "CONFIGURATION_SCOPED_CURRENT_READ_PER_PRETRADE_DECISION"
    )


def test_docs_and_master_pointer() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    prior = PRIOR_INSTRUMENT_STATE.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert "ACCOUNT_MODE_CANONICAL_DEFINITION=OKX_ACCOUNT_CONFIG_ACCTLV" in spec
    assert "ACCOUNT_MODE_ENDPOINT=/api/v5/account/config" in spec
    assert "ACCOUNT_MODE_SOURCE_ENDPOINT=/api/v5/account/config" in spec
    assert "ACCOUNT_MODE_RAW_FIELD=acctLv" in spec
    assert "ACCOUNT_MODE_RAW_VALUE=2" in spec
    assert "ACCOUNT_MODE_SEMANTIC_VALUE=FUTURES_MODE" in spec
    assert "ACCOUNT_MODE_BINDING_STATUS=PROVEN" in spec
    assert "ACCOUNT_IDENTITY_BOUND=true" in spec
    assert "ENVIRONMENT_BOUND=true" in spec
    assert "PROVENANCE_BOUND=true" in spec
    assert "ALL_REQUIRED_METADATA_EDGES_BOUND=true" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=VENUE_PRETRADE_LIMIT_GATES" in spec
    assert "NEXT_DISTINCT_SURFACE=VENUE_PRETRADE_LIMIT_GATES" in spec
    assert "NEXT_DISTINCT_SURFACE_AUTHORIZED=false" in spec
    assert "NETWORK_GET_PERFORMED=false" in spec
    assert "ACCOUNT_MODE_REUSES_POS_MODE_ACCOUNT_CONFIG_GET=true" in spec
    assert "POS_MODE_IS_NOT_ACCOUNT_MODE=true" in spec
    assert "INTEGER_2_IS_NOT_STRING_2=true" in spec
    assert "GATE20_HISTORICAL_SATISFIED_IS_NOT_CURRENT_BINDING=true" in spec
    assert "ACCOUNT_MODE_FORENSIC_BINDING_AND_CLOSURE_V1=true" in section
    assert "PEAK_TRADE_ACCOUNT_MODE_FORENSIC_BINDING_AND_CLOSURE_V1" in mot
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=ACCOUNT_MODE" in prior
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "TRADING_PERFORMED=false" in spec
    assert "LIVE_AUTHORIZED=false" in spec
    assert "TESTNET_AUTHORIZED=false" in spec
    assert "CANARY_AUTHORIZED=false" in spec
    pack = REPO_ROOT / (
        "evidence/ops/pos_mode_forensic_binding_implementation_and_closure_v1/20260829T233351Z"
    )
    assert pack.joinpath("MANIFEST.sha256").is_file()
    assert pack.joinpath("GET_SNAPSHOT.sanitized.json").is_file()
    assert ORDER_PLAN.is_file()
    assert SUBMIT_TRANSPORT.is_file()
    assert CONSUMER.is_file()
    assert OBSERVATION.is_file()
