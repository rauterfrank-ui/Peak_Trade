"""Standing fee/slippage and non-executing exact execution envelope tests. No wire."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_FAMILY,
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.capture_compat_v1 import (
    project_envelope_onto_capture_record_v1,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.census_v1 import (
    fee_source_census_v1,
    slippage_source_census_v1,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.constants_v1 import (
    CLORDID_PLAN_SENTINEL,
    HISTORICAL_BTC_FAMILY,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.execution_envelope_v1 import (
    ExactExecutionEnvelopeError,
    build_exact_execution_envelope_v1,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.fee_policy_v1 import (
    StandingFeePolicyError,
    bind_standing_fee_policy_from_trade_fee_payload_v1,
    compute_expected_fee_amount_v1,
    trade_fee_query_path_v1,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.offline_order_plan_v1 import (
    OfflineExactOrderPlanError,
    build_offline_exact_order_plan_v1,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.slippage_policy_v1 import (
    StandingSlippagePolicyError,
    bind_standing_limit_slippage_policy_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    REQUIRED_HANDOFF_FIELDS,
)


def _fee_payload(**overrides: object) -> dict:
    row = {
        "instType": "FUTURES",
        "instFamily": DEFAULT_INST_FAMILY,
        "taker": "-0.0005",
        "maker": "-0.0002",
        "delivery": "0.0003",
    }
    row.update({k: v for k, v in overrides.items() if k != "code"})
    return {"code": str(overrides.get("code", "0")), "data": [row]}


def _fee_policy(**overrides: object):
    return bind_standing_fee_policy_from_trade_fee_payload_v1(
        payload=_fee_payload(**overrides),
        instrument_id=DEFAULT_INSTRUMENT_ID,
    )


def _pass(extracted: dict | None = None) -> dict:
    return {"status": "PASS", "extracted": extracted or {}}


def _predicates() -> dict:
    return {
        "INSTRUMENT_STATE_CURRENT": _pass({"state": "live"}),
        "ACCOUNT_MODE_CURRENT": _pass({"acctLv": "2"}),
        "POSITION_MODE_CURRENT": _pass({"posMode": "net_mode"}),
        "LEVERAGE_CURRENT": _pass({"lever": "3"}),
        "PRICE_BAND_CURRENT": _pass({"buyLmt": "0.8277"}),
        "PRICE_SOURCE_CURRENT": _pass({"reference_price": "0.8237"}),
        "EXACT_PRICE_SEMANTICS_BOUND": _pass({"EXECUTION_LIMIT_PRICE": "0.8237"}),
        "AVAILABLE_MARGIN_CURRENT": _pass({"availEq": "2.10", "selected_ccy": "USDC"}),
        "MAX_AVAILABLE_MAX_SIZE_CURRENT": _pass({"maxBuy": "7"}),
        "MARGIN_MODE_CURRENT": {"status": "NOT_OBSERVED", "extracted": {}},
        "EXPECTED_PRE_EXISTING_POSITION": {"status": "NOT_OBSERVED", "extracted": {}},
    }


def _envelope(**overrides: object):
    kwargs = {
        "instrument_id": DEFAULT_INSTRUMENT_ID,
        "side": "BUY",
        "order_type": "LIMIT",
        "td_mode": "cross",
        "pos_mode": "net_mode",
        "leverage": "3",
        "qty": "1",
        "qty_unit": "CONTRACTS_SZ",
        "min_sz": "1",
        "lot_sz": "1",
        "tick_sz": "0.0001",
        "ct_val": "1",
        "ct_val_ccy": "SUI",
        "settle_ccy": "USDC",
        "reference_price": "0.8237",
        "limit_price": "0.8237",
        "buy_lmt": "0.8277",
        "sell_lmt": "0.8194",
        "max_buy": "7",
        "available_margin": "2.10",
        "available_margin_ccy": "USDC",
        "instrument_state": "live",
        "account_mode": "2",
        "fee_policy": _fee_policy(),
        "predicates": _predicates(),
        "owner_execution_authorized": False,
    }
    kwargs.update(overrides)
    return build_exact_execution_envelope_v1(**kwargs)


def test_fee_and_slippage_census_rejects_historical_and_wrong_scope() -> None:
    fees = {row["CANDIDATE"]: row["ADJUDICATED_STATUS"] for row in fee_source_census_v1()}
    slips = {row["CANDIDATE"]: row["ADJUDICATED_STATUS"] for row in slippage_source_census_v1()}
    assert fees["HISTORICAL_Z2N_BTC_RATES"] == "REJECTED_NOT_CURRENT_SUI_AUTHORITY"
    assert fees["ROUND_TRIP_FEE_RESERVE"] == "REJECTED_ROUND_TRIP_NOT_SINGLE_FILL"
    assert fees["RESEARCH_BACKTEST_TAKER"] == "REJECTED_NOT_CURRENT_LIVE_FEE_POLICY"
    assert fees["DELIVERY_FIELD"] == "EXCLUDED_FROM_ENTRY_FILL_EXPECTED_FEE"
    assert slips["HISTORICAL_0_0008"] == "REJECTED_NOT_CURRENT"
    assert slips["VENUE_PRICE_LIMIT_BAND"] == "NOT_SLIPPAGE_BOUND"
    assert slips["LIMIT_WORST_FILL_EQUALS_LIMIT_PX"] == "BOUND"


def test_trade_fee_query_rejects_historical_btc_family() -> None:
    with pytest.raises(StandingFeePolicyError, match="HISTORICAL_BTC_FAMILY"):
        trade_fee_query_path_v1(inst_family=HISTORICAL_BTC_FAMILY)


def test_fee_policy_binds_taker_usdc_when_generic_empty() -> None:
    policy = bind_standing_fee_policy_from_trade_fee_payload_v1(
        payload={
            "code": "0",
            "data": [
                {
                    "instType": "FUTURES",
                    "instFamily": DEFAULT_INST_FAMILY,
                    "taker": "",
                    "maker": "",
                    "takerUSDC": "-0.0005",
                    "makerUSDC": "-0.0002",
                }
            ],
        }
    )
    assert policy.policy_bound is True
    assert policy.taker_field == "takerUSDC"
    assert policy.conservative_rate == "0.0005"
    assert policy.delivery_role == "NOT_PART_OF_ENTRY_FILL"
    assert policy.historical_rates_used is False


def test_fee_policy_unknown_rate_denies() -> None:
    with pytest.raises(StandingFeePolicyError, match="FEE_RATE_UNKNOWN"):
        _fee_policy(taker="", maker="", takerUSDC="", makerUSDC="")


def test_fee_policy_historical_reuse_denied() -> None:
    with pytest.raises(StandingFeePolicyError, match="HISTORICAL_FEE_EVIDENCE"):
        bind_standing_fee_policy_from_trade_fee_payload_v1(
            payload=_fee_payload(),
            historical_reuse=True,
        )


def test_fee_currency_mismatch_denies() -> None:
    with pytest.raises(StandingFeePolicyError, match="FEE_CURRENCY_MISMATCH"):
        compute_expected_fee_amount_v1(
            conservative_rate="0.0005",
            qty="1",
            ct_val="1",
            worst_fill_px="0.8237",
            fee_ccy="USDT",
        )


def test_fee_amount_conversion_and_conservative_ceiling() -> None:
    out = compute_expected_fee_amount_v1(
        conservative_rate="0.0005",
        qty="1",
        ct_val="1",
        worst_fill_px="0.8237",
    )
    notional = Decimal("0.8237")
    exact = Decimal("0.0005") * notional
    assert Decimal(out["GROSS_NOTIONAL"]) == notional
    assert Decimal(out["FEE_AMOUNT_EXACT"]) == exact
    assert Decimal(out["FEE_AMOUNT_CONSERVATIVE"]) >= exact
    assert out["FEE_CCY"] == "USDC"


def test_positive_rebate_does_not_reduce_worst_case_debit() -> None:
    policy = _fee_policy(taker="-0.0005", maker="0.0002")
    assert policy.maker_debit == "0"
    assert policy.conservative_rate == "0.0005"


def test_slippage_limit_equals_worst_fill_for_buy() -> None:
    bound = bind_standing_limit_slippage_policy_v1(
        side="BUY",
        reference_price="0.8237",
        limit_price="0.8237",
        tick_sz="0.0001",
    )
    assert bound.policy_bound is True
    assert bound.worst_fill_price == "0.8237"
    assert Decimal(bound.slippage_abs) == Decimal("0")
    assert bound.price_limit_used_as_slippage is False
    assert bound.historical_0008_used is False


def test_slippage_buy_limit_above_reference_denied() -> None:
    with pytest.raises(StandingSlippagePolicyError, match="BUY_LIMIT_ABOVE_REFERENCE"):
        bind_standing_limit_slippage_policy_v1(
            side="BUY",
            reference_price="0.8237",
            limit_price="0.8238",
            tick_sz="0.0001",
        )


def test_slippage_off_tick_denied() -> None:
    with pytest.raises(StandingSlippagePolicyError, match="LIMIT_PRICE_NOT_ON_TICK"):
        bind_standing_limit_slippage_policy_v1(
            side="BUY",
            reference_price="0.8237",
            limit_price="0.82375",
            tick_sz="0.0001",
        )


def test_envelope_happy_path_does_not_authorize_live() -> None:
    env = _envelope().to_dict()
    assert env["EXACT_EXECUTION_ENVELOPE_COMPLETE"] is True
    assert env["TECHNICAL_EXECUTION_READY"] is True
    assert env["OWNER_EXECUTION_AUTHORIZED"] is False
    assert env["LIVE_EXECUTION_AUTHORIZED"] is False
    assert env["LIVE_SUBMIT_EXECUTED"] is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    plan = build_offline_exact_order_plan_v1(envelope=env)
    assert plan["WIRE_SEND_EXECUTED"] is False
    assert plan["WIRE_SEND_BLOCKED"] is True
    assert plan["VENUE_NATIVE_PAYLOAD"]["instId"] == DEFAULT_INSTRUMENT_ID
    assert plan["VENUE_NATIVE_PAYLOAD"]["sz"] == "1"
    assert plan["VENUE_NATIVE_PAYLOAD"]["px"] == "0.8237"
    assert plan["VENUE_NATIVE_PAYLOAD"]["tdMode"] == "cross"
    assert plan["VENUE_NATIVE_PAYLOAD"]["side"] == "buy"
    assert plan["VENUE_NATIVE_PAYLOAD"]["ordType"] == "limit"
    assert plan["VENUE_NATIVE_PAYLOAD"]["clOrdId"] == CLORDID_PLAN_SENTINEL
    assert "posSide" not in plan["VENUE_NATIVE_PAYLOAD"]


def test_qty_below_min_denies() -> None:
    with pytest.raises(ExactExecutionEnvelopeError, match="QTY_NOT_VENUE_ADMISSIBLE"):
        _envelope(min_sz="2")


def test_qty_above_max_denies() -> None:
    with pytest.raises(ExactExecutionEnvelopeError, match="QTY_ABOVE_MAX_AVAILABLE"):
        _envelope(max_buy="0")


def test_price_outside_band_denies() -> None:
    with pytest.raises(ExactExecutionEnvelopeError, match="PRICE_OUTSIDE_BAND"):
        _envelope(buy_lmt="0.1000")


def test_wrong_instrument_denies() -> None:
    with pytest.raises(ExactExecutionEnvelopeError, match="WRONG_INSTRUMENT"):
        _envelope(instrument_id="BTC-USD_UM_XPERP-310404")


def test_wrong_pos_mode_denies() -> None:
    with pytest.raises(ExactExecutionEnvelopeError, match="WRONG_POS_MODE"):
        _envelope(pos_mode="long_short_mode")


def test_wrong_margin_mode_denies() -> None:
    with pytest.raises(ExactExecutionEnvelopeError, match="WRONG_TD_MODE"):
        _envelope(td_mode="isolated")


def test_missing_usdc_margin_denies() -> None:
    with pytest.raises(ExactExecutionEnvelopeError, match="MARGIN_CCY_MISMATCH"):
        _envelope(available_margin_ccy="")


def test_unknown_max_available_denies() -> None:
    with pytest.raises(ExactExecutionEnvelopeError, match="ENVELOPE_INPUT_UNKNOWN:maxBuy"):
        _envelope(max_buy="UNKNOWN")


def test_owner_execution_true_cannot_complete_envelope() -> None:
    with pytest.raises(ExactExecutionEnvelopeError, match="OWNER_EXECUTION_AUTHORIZED"):
        _envelope(owner_execution_authorized=True)


def test_incomplete_envelope_cannot_build_plan() -> None:
    with pytest.raises(OfflineExactOrderPlanError, match="ENVELOPE_INCOMPLETE"):
        build_offline_exact_order_plan_v1(envelope={"EXACT_EXECUTION_ENVELOPE_COMPLETE": False})


def test_capture_optional_fields_do_not_rewrite_required_identity() -> None:
    env = _envelope().to_dict()
    projected = project_envelope_onto_capture_record_v1(
        envelope=env,
        required_identity={"clOrdId": "x", "ordId": "y", "instId": DEFAULT_INSTRUMENT_ID},
    )
    assert projected["CAPTURE_PATH_COMPATIBLE"] is True
    assert projected["RESTART_CONSUMER_COMPATIBLE"] is True
    assert projected["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is False
    assert projected["RESTART_EXECUTED"] is False
    for name in REQUIRED_HANDOFF_FIELDS:
        assert name not in projected["OPTIONAL_ENVELOPE_FIELDS"]
    assert projected["OPTIONAL_ENVELOPE_FIELDS"]["expected_fee"] == env["EXPECTED_FEE_AMOUNT"]
