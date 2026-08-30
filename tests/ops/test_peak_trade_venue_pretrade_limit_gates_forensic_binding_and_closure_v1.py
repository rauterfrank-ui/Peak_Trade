"""VENUE_PRETRADE_LIMIT_GATES forensic binding and productive consumer v1.

No live trading. No POST. No new GET. Reuses committed INSTRUMENT_STATE
public-instruments evidence. minSz/lotSz/tickSz/maxLmtSz are not
maxMktSz, maxLmtAmt, available margin, leverage, or internal order-count.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    REUSED_BINDING_REST_HOST,
    TESTNET_AUTHORIZED,
    public_instruments_query_path_v1 as _query_path,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_pretrade_limit_gates_consumer_v1 import (
    ACCOUNT_MODE_IS_NOT_VENUE_PRETRADE_LIMIT,
    AVAILABLE_MARGIN_IS_NOT_VENUE_PRETRADE_LIMIT,
    FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION,
    HISTORICAL_REUSE_PATH_EXISTS,
    INTERNAL_ORDER_COUNT_LIMIT_IS_NOT_VENUE_LIMIT,
    LEVERAGE_IS_NOT_VENUE_PRETRADE_LIMIT,
    MAX_ICEBERG_SZ_IS_NOT_LIMIT_MAX,
    MAX_LMT_AMT_IS_NOT_MAX_LMT_SZ,
    MAX_MKT_SZ_IS_NOT_LIMIT_MAX,
    NO_IMPLICIT_ROUNDING,
    NO_SILENT_CLAMPING,
    REQUIRED_GATE_COUNT,
    REQUIRED_GATES,
    VENUE_PRETRADE_LIMIT_GATES_CONSUMER_BOUND,
    VENUE_PRETRADE_LIMIT_GATES_FAIL_CLOSED_BOUND,
    LiveCanaryVenuePretradeLimitGatesConsumerError,
    apply_fresh_venue_pretrade_limit_gates_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_pretrade_limit_observation_v1 import (
    COMMITTED_BODY_SHA256,
    COMMITTED_INSTRUMENT_STATE_SNAPSHOT_RELATIVE,
    COMMITTED_LOT_SZ_RAW,
    COMMITTED_MAX_LMT_SZ_RAW,
    COMMITTED_MIN_SZ_RAW,
    COMMITTED_TICK_SZ_RAW,
    VENUE_PRETRADE_LIMIT_AUTH_CLASS,
    VENUE_PRETRADE_LIMIT_FRESHNESS_POLICY,
    VENUE_PRETRADE_LIMIT_TS_AGE_BOUND,
    LiveCanaryVenuePretradeLimitObservationError,
    acquire_fresh_venue_pretrade_limit_observation_from_payload_v1,
    bind_venue_pretrade_limits_from_committed_instrument_state_pack_v1,
    utc_now_iso_v1,
    validate_fresh_venue_pretrade_limit_observation_v1,
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
    "docs/ops/specs/PEAK_TRADE_VENUE_PRETRADE_LIMIT_GATES_FORENSIC_BINDING_AND_CLOSURE_V1.md"
)
PRIOR_ACCOUNT_MODE = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_ACCOUNT_MODE_FORENSIC_BINDING_AND_CLOSURE_V1.md"
)
PRIOR_INSTRUMENT_STATE = REPO_ROOT / (
    "docs/ops/specs/PEAK_TRADE_INSTRUMENT_STATE_FORENSIC_BINDING_AND_CLOSURE_V1.md"
)
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
OWNER_GO = "PEAK_TRADE_POST_6161_VENUE_PRETRADE_LIMIT_GATES_FORENSIC_BINDING_AND_CLOSURE_V1"
ENDPOINT = _query_path()


def _row(**fields: object) -> dict[str, object]:
    row: dict[str, object] = {
        "instId": DEFAULT_INSTRUMENT_ID,
        "instType": "FUTURES",
        "ruleType": "xperp",
        "minSz": "1",
        "lotSz": "1",
        "tickSz": "0.0001",
        "ctVal": "1",
        "ctMult": "1",
        "ctValCcy": "SUI",
        "state": "live",
        "maxLmtSz": "100000000",
        "maxMktSz": "100000",
    }
    row.update(fields)
    return row


def _payload(**fields: object) -> dict[str, object]:
    return {"code": "0", "msg": "", "data": [_row(**fields)]}


def _gate(**kwargs: object) -> dict[str, object]:
    body: dict[str, object] = {
        "pretrade_decision_id": "decision-a",
        "instruments_payload": _payload(),
        "instrument_id": DEFAULT_INSTRUMENT_ID,
        "order_type": "LIMIT",
        "venue_contract_count": "1",
        "planned_limit_px": "0.8209",
        "quantity_domain": ORDER_PLAN_QTY_DOMAIN,
        "http_status": 200,
        "endpoint": ENDPOINT,
        "get_performed": True,
        "historical_reuse": False,
        "auth_header_sent": False,
    }
    body.update(kwargs)
    return apply_fresh_venue_pretrade_limit_gates_v1(**body)  # type: ignore[arg-type]


def _section_5_3(text: str) -> str:
    start = text.index("## 5.3 Canonical productive no-order call graph")
    end = text.index("## 5.4 Closed or materially established baseline capabilities")
    return text[start:end]


def test_positive_binding_boundary_values() -> None:
    result = _gate()
    assert result["ok"] is True
    assert result["required_gate_count"] == REQUIRED_GATE_COUNT == 4
    assert tuple(result["required_gates"]) == REQUIRED_GATES
    assert result["min_sz_raw"] == "1"
    assert result["lot_sz_raw"] == "1"
    assert result["tick_sz_raw"] == "0.0001"
    assert result["max_lmt_sz_raw"] == "100000000"
    assert result["instrument_bound"] is True
    assert result["environment_bound"] is True
    assert result["provenance_bound"] is True
    assert result["account_identity_bound_if_required"] == "N/A"
    assert result["all_required_metadata_edges_bound"] is True
    assert result["max_mkt_sz_applied"] is False
    assert result["conversion_performed"] is False
    assert result["no_silent_clamping"] is True
    assert result["no_implicit_rounding"] is True
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert result["freshness_policy"] == VENUE_PRETRADE_LIMIT_FRESHNESS_POLICY
    assert result["ts_age_bound"] == VENUE_PRETRADE_LIMIT_TS_AGE_BOUND == "UNBOUND"
    assert MAX_MKT_SZ_IS_NOT_LIMIT_MAX is True
    assert MAX_ICEBERG_SZ_IS_NOT_LIMIT_MAX is True
    assert MAX_LMT_AMT_IS_NOT_MAX_LMT_SZ is True
    assert INTERNAL_ORDER_COUNT_LIMIT_IS_NOT_VENUE_LIMIT is True
    assert AVAILABLE_MARGIN_IS_NOT_VENUE_PRETRADE_LIMIT is True
    assert LEVERAGE_IS_NOT_VENUE_PRETRADE_LIMIT is True
    assert ACCOUNT_MODE_IS_NOT_VENUE_PRETRADE_LIMIT is True
    at_min = _gate(venue_contract_count="1")
    assert at_min["ok"] is True
    at_max = _gate(venue_contract_count="100000000")
    assert at_max["ok"] is True


def test_min_size_below_fails_and_equal_passes() -> None:
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_SIZE_BELOW_MIN_SZ",
    ):
        _gate(instruments_payload=_payload(minSz="2"), venue_contract_count="1")
    assert _gate(instruments_payload=_payload(minSz="2"), venue_contract_count="2")["ok"] is True


def test_lot_size_non_multiple_fails_without_rounding() -> None:
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_NOT_EXACT_MULTIPLE:lotSz",
    ):
        _gate(instruments_payload=_payload(lotSz="2"), venue_contract_count="3")
    assert _gate(instruments_payload=_payload(lotSz="2"), venue_contract_count="2")["ok"] is True
    assert NO_IMPLICIT_ROUNDING is True
    assert NO_SILENT_CLAMPING is True


def test_tick_size_non_multiple_fails_without_rounding() -> None:
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_NOT_EXACT_MULTIPLE:tickSz",
    ):
        _gate(planned_limit_px="0.82091")
    assert _gate(planned_limit_px="0.8209")["ok"] is True
    assert _gate(planned_limit_px="0.0001")["ok"] is True


def test_max_limit_size_above_fails_and_equal_passes() -> None:
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_SIZE_ABOVE_MAX_LMT_SZ",
    ):
        _gate(venue_contract_count="100000001")
    assert _gate(venue_contract_count="100000000")["ok"] is True


def test_max_mkt_sz_is_not_substituted_for_limit() -> None:
    result = _gate(venue_contract_count="100001")
    assert result["ok"] is True
    assert result["max_mkt_sz_applied"] is False
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_ORDER_TYPE_NOT_LIMIT:MARKET",
    ):
        _gate(order_type="MARKET")


def test_missing_null_empty_and_wrong_type_fail_closed() -> None:
    for field in ("minSz", "lotSz", "tickSz", "maxLmtSz"):
        missing = _payload()
        del missing["data"][0][field]  # type: ignore[index]
        with pytest.raises(
            LiveCanaryVenuePretradeLimitGatesConsumerError,
            match=f"VENUE_PRETRADE_LIMIT_FIELD_MISSING:{field}",
        ):
            _gate(instruments_payload=missing)
        with pytest.raises(
            LiveCanaryVenuePretradeLimitGatesConsumerError,
            match=f"VENUE_PRETRADE_LIMIT_FIELD_NULL:{field}",
        ):
            _gate(instruments_payload=_payload(**{field: None}))
        with pytest.raises(
            LiveCanaryVenuePretradeLimitGatesConsumerError,
            match=f"VENUE_PRETRADE_LIMIT_FIELD_EMPTY:{field}",
        ):
            _gate(instruments_payload=_payload(**{field: ""}))
        with pytest.raises(
            LiveCanaryVenuePretradeLimitGatesConsumerError,
            match=f"VENUE_PRETRADE_LIMIT_FIELD_WRONG_TYPE:{field}",
        ):
            _gate(instruments_payload=_payload(**{field: 1}))


def test_non_finite_negative_zero_scientific_fail_closed() -> None:
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_FIELD_NON_FINITE:minSz",
    ):
        _gate(instruments_payload=_payload(minSz="NaN"))
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_FIELD_NEGATIVE:minSz",
    ):
        _gate(instruments_payload=_payload(minSz="-1"))
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_FIELD_ZERO_FORBIDDEN:minSz",
    ):
        _gate(instruments_payload=_payload(minSz="0"))
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_FIELD_OUT_OF_DOMAIN:maxLmtSz",
    ):
        _gate(instruments_payload=_payload(maxLmtSz="1e8"))
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_MIN_MAX_INVERSION",
    ):
        _gate(instruments_payload=_payload(minSz="5", maxLmtSz="4"))


def test_wrong_endpoint_instrument_environment_and_provenance() -> None:
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_ENDPOINT_FORBIDDEN",
    ):
        _gate(endpoint="/api/v5/account/max-size")
    with pytest.raises(LiveCanaryVenuePretradeLimitGatesConsumerError, match="INSTRUMENT"):
        _gate(instrument_id="BTC-USD_UM_XPERP-310404")
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError, match="REST_HOST_NOT_PRODUCTION_EEA"
    ):
        _gate(rest_host="demo.okx.com")
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="PUBLIC_INSTRUMENTS_AUTH_HEADER_FORBIDDEN",
    ):
        _gate(auth_header_sent=True)
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="HISTORICAL_VENUE_PRETRADE_LIMIT_REUSE_FORBIDDEN",
    ):
        _gate(historical_reuse=True)
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError, match="FRESH_GET_NOT_PERFORMED"
    ):
        _gate(get_performed=False)
    assert FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION is True
    assert HISTORICAL_REUSE_PATH_EXISTS is False


def test_duplicate_and_missing_rows_fail_closed() -> None:
    row = _row()
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_DUPLICATE_TARGET_ROWS",
    ):
        _gate(instruments_payload={"code": "0", "data": [row, dict(row)]})
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_NOT_OBSERVED",
    ):
        _gate(instruments_payload={"code": "0", "data": []})
    wrong = _row()
    wrong["instId"] = "ETH-USD_UM_XPERP-310404"
    with pytest.raises(
        LiveCanaryVenuePretradeLimitGatesConsumerError,
        match="VENUE_PRETRADE_LIMIT_NOT_OBSERVED",
    ):
        _gate(instruments_payload={"code": "0", "data": [wrong]})


def test_committed_instrument_state_pack_binds_without_network() -> None:
    validated = bind_venue_pretrade_limits_from_committed_instrument_state_pack_v1(
        repo_root=REPO_ROOT,
        pretrade_decision_id="venue-pretrade-limit-gates-forensic-binding-sui-20260830T0728Z",
    )
    assert validated.raw.min_sz_raw == COMMITTED_MIN_SZ_RAW == "1"
    assert validated.raw.lot_sz_raw == COMMITTED_LOT_SZ_RAW == "1"
    assert validated.raw.tick_sz_raw == COMMITTED_TICK_SZ_RAW == "0.0001"
    assert validated.raw.max_lmt_sz_raw == COMMITTED_MAX_LMT_SZ_RAW == "100000000"
    assert validated.min_sz == Decimal("1")
    assert validated.lot_sz == Decimal("1")
    assert validated.tick_sz == Decimal("0.0001")
    assert validated.max_lmt_sz == Decimal("100000000")
    assert validated.conversion_performed is False
    assert validated.raw.body_sha256 == COMMITTED_BODY_SHA256
    assert validated.raw.source_evidence == COMMITTED_INSTRUMENT_STATE_SNAPSHOT_RELATIVE
    assert validated.raw.endpoint == ENDPOINT
    assert validated.raw.rest_host == REUSED_BINDING_REST_HOST


def test_order_plan_wires_limit_gates_and_does_not_change_prior_surfaces() -> None:
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=_instruments_payload(),
        ticker_payload=TICKER,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="4ef142a7ef4747c931773daaee2d947732132dfd",
        pretrade_decision_id="decision-plan-limit-gates",
        **_max_available_plan_kwargs(),
    )
    assert plan.quantity_domain == ORDER_PLAN_QTY_DOMAIN
    assert plan.quantity == "1"
    assert plan.limit_price == "0.8209"
    mutated = _instruments_payload(maxLmtSz="1")
    mutated["data"][0]["minSz"] = "2"  # type: ignore[index]
    with pytest.raises(LiveCanaryOrderPlanError, match="UNSAFE_QUANTITY"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=mutated,
            ticker_payload=TICKER,
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            origin_main_sha="4ef142a7ef4747c931773daaee2d947732132dfd",
            pretrade_decision_id="decision-plan-limit-gates-min",
            **_max_available_plan_kwargs(),
        )
    assert VENUE_PRETRADE_LIMIT_GATES_CONSUMER_BOUND is True
    assert VENUE_PRETRADE_LIMIT_GATES_FAIL_CLOSED_BOUND is True


def test_flatten_does_not_consume_limit_gates() -> None:
    payload = {
        "code": "0",
        "data": [{"instId": DEFAULT_INSTRUMENT_ID, "pos": "1", "mgnMode": "cross"}],
    }
    plan = build_minimum_valid_canary_flatten_order_plan_v1(
        positions_payload=payload,
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha="4ef142a7ef4747c931773daaee2d947732132dfd",
    )
    assert plan.td_mode == "cross"


def test_submit_transport_fail_closed_before_post_when_min_sz_unmet() -> None:
    import json

    transport = _fake_transport()
    instruments = _payload(minSz="2")
    transport.bodies_by_endpoint["/api/v5/public/instruments"] = json.dumps(instruments).encode()
    with pytest.raises(LiveCanarySubmitTransportError):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)


def test_observation_validate_decision_mismatch() -> None:
    obs = acquire_fresh_venue_pretrade_limit_observation_from_payload_v1(
        pretrade_decision_id="decision-one",
        instruments_payload=_payload(),
        instrument_id=DEFAULT_INSTRUMENT_ID,
        observed_at_utc=utc_now_iso_v1(),
        endpoint=ENDPOINT,
        http_status=200,
        get_performed=True,
    )
    with pytest.raises(
        LiveCanaryVenuePretradeLimitObservationError, match="OBSERVATION_DECISION_ID_MISMATCH"
    ):
        validate_fresh_venue_pretrade_limit_observation_v1(
            obs,
            pretrade_decision_id="decision-two",
            instrument_id=DEFAULT_INSTRUMENT_ID,
            quantity_domain=ORDER_PLAN_QTY_DOMAIN,
        )
    assert VENUE_PRETRADE_LIMIT_AUTH_CLASS == "PUBLIC_UNSIGNED_GET"


def test_docs_and_master_pointer() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    prior_account = PRIOR_ACCOUNT_MODE.read_text(encoding="utf-8")
    prior_state = PRIOR_INSTRUMENT_STATE.read_text(encoding="utf-8")
    section = _section_5_3(MASTER_RUNBOOK.read_text(encoding="utf-8"))
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert (
        "VENUE_PRETRADE_LIMIT_GATES_SEMANTIC_DEFINITION="
        "AGGREGATED_TYPED_FAIL_CLOSED_LIMIT_ENTRY_VALIDATOR_FOR_VENUE_NATIVE_INSTRUMENT_MINSZ_LOTSZ_TICKSZ_MAXLMTSZ"
    ) in spec
    assert "REQUIRED_GATE_COUNT=4" in spec
    assert "REQUIRED_GATES=MIN_SIZE,LOT_SIZE,TICK_SIZE,MAX_LIMIT_SIZE" in spec
    assert "MIN_SZ_RAW_VALUE=1" in spec
    assert "LOT_SZ_RAW_VALUE=1" in spec
    assert "TICK_SZ_RAW_VALUE=0.0001" in spec
    assert "MAX_LMT_SZ_RAW_VALUE=100000000" in spec
    assert "VENUE_PRETRADE_LIMIT_GATES_BINDING_STATUS=PROVEN" in spec
    assert "INSTRUMENT_BOUND=true" in spec
    assert "ENVIRONMENT_BOUND=true" in spec
    assert "PROVENANCE_BOUND=true" in spec
    assert "ACCOUNT_IDENTITY_BOUND_IF_REQUIRED=N/A" in spec
    assert "ALL_REQUIRED_METADATA_EDGES_BOUND=true" in spec
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=CANARY_SUBMIT_AUTHORIZATION" in spec
    assert "NEXT_DISTINCT_SURFACE=CANARY_SUBMIT_AUTHORIZATION" in spec
    assert "NEXT_DISTINCT_SURFACE_AUTHORIZED=false" in spec
    assert "NETWORK_GET_PERFORMED=false" in spec
    assert "MAX_MKT_SZ_IS_NOT_LIMIT_MAX=true" in spec
    assert "NO_SILENT_CLAMPING=true" in spec
    assert "NO_IMPLICIT_ROUNDING=true" in spec
    assert "VENUE_PRETRADE_LIMIT_GATES_FORENSIC_BINDING_AND_CLOSURE_V1=true" in section
    assert "VENUE_PRETRADE_LIMIT_GATES_BINDING_STATUS=PROVEN" in section
    assert "VENUE_PRETRADE_LIMIT_GATES_COMPLETE=true" not in section
    assert "PEAK_TRADE_VENUE_PRETRADE_LIMIT_GATES_FORENSIC_BINDING_AND_CLOSURE_V1" in mot
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=VENUE_PRETRADE_LIMIT_GATES" in prior_account
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=ACCOUNT_MODE" in prior_state
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in mot
    assert "NETWORK_POST_PERFORMED=false" in spec
    assert "TRADING_PERFORMED=false" in spec
    assert "LIVE_AUTHORIZED=false" in spec
    assert "TESTNET_AUTHORIZED=false" in spec
    assert "CANARY_AUTHORIZED=false" in spec
    pack = REPO_ROOT / (
        "evidence/ops/instrument_state_forensic_binding_and_closure_v1/20260830T044522Z"
    )
    assert pack.joinpath("MANIFEST.sha256").is_file()
    assert pack.joinpath("GET_SNAPSHOT.sanitized.json").is_file()
