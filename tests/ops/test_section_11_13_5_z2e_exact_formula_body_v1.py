"""§11.13.5.Z2E exact internal conservative qty=1 formula-body ratification.

Code contract plus docs/governance invariants. Does not authorize Live,
Testnet, orders, funding, scaling, or Multi-Future. Does not invent OKX
fee truth, a monetary base, COVER_USDC, or a numeric funding amount.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from src.core.environment import LIVE_CONFIRM_TOKEN
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exact_formula_body_v1 import (
    API_DELIVERY_0_0003_STATUS,
    B08_EXACT_FORMULA_BODY_KIND,
    B08_EXACT_FORMULA_BODY_STATUS,
    COVER_USDC_STATUS,
    DELIVERY_COVER_INTERNAL_STATUS,
    EXACT_OKX_FEE_FORMULA_STATUS,
    EXCHANGE_TRUTH_CHANGED,
    FEE_RESERVE_RATES_STATUS,
    FUNDING_RATE_RESERVE,
    FX_STATUS,
    IM_FRESH_ROLE,
    MM_LIQ_BUFFER_STATUS,
    MONETARY_BASE_STATUS,
    NORMAL_EXPIRY_RATE_ROLE,
    NUMERIC_FUNDING_AMOUNT,
    PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH,
    PEAK_TRADE_INTERNAL_NOTIONAL_UNIT,
    PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE,
    PROVEN_NORMAL_EXPIRY_RATE,
    QTY_LIMIT,
    ROUNDING_STATUS,
    SCALING_AUTHORIZED,
    SLIPPAGE_RESERVE_STATUS,
    SUM_INTERNAL_NUMERIC_STATUS,
    VENUE_MIN_AVAIL_EQ_ROLE,
    ExactFormulaBodyError,
    evaluate_qty_one_internal_exact_formula_body_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.expiry_fee_economic_uncertainty_bound_v1 import (
    PEAK_TRADE_EXPIRY_RESERVE_RATE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.governance_state_matrix_v1 import (
    NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_gates_v1 import (
    evaluate_canary_submit_gates_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
CANARY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_V1.md"
)

Z2E_HEADING = "### 11.13.5.Z2E Exact internal conservative qty=1 formula-body ratification"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_TO_BIND_UNINSTANTIATED_FORMULA_TERM_INSTANCES_AND_FX_ROUNDING_BEFORE_FUNDING"
)
Z2E_OWNER_GO = "OWNER_GO_REQUIRED_TO_RATIFY_EXACT_FORMULA_BODY"

_BODY_KWARGS = {
    "quantity": "1",
    "instrument_ct_val": "0.0001",
    "reference_price": "63043.7",
    "instrument_id": DEFAULT_INSTRUMENT_ID,
    "authorization_scope": AUTHORIZATION_SCOPE,
    "instrument_tick_sz": "0.1",
}


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2e_section(text: str) -> str:
    start = text.find(Z2E_HEADING)
    assert start >= 0, "missing §11.13.5.Z2E heading"
    end = text.find("### 11.13.5.Z2F", start)
    assert end > start, "missing §11.13.5.Z2F boundary after Z2E"
    return text[start:end]


def _body(**overrides: object):
    kwargs = dict(_BODY_KWARGS)
    kwargs.update(overrides)
    return evaluate_qty_one_internal_exact_formula_body_v1(**kwargs)


def test_0003_is_not_okx_fee_truth_and_0001_is_non_operative() -> None:
    assert PEAK_TRADE_EXPIRY_RESERVE_RATE == Decimal("0.0003")
    assert PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH is False
    assert PROVEN_NORMAL_EXPIRY_RATE == Decimal("0.0001")
    assert NORMAL_EXPIRY_RATE_ROLE == "HISTORICAL_SUPERSEDED_NON_OPERATIVE"
    assert API_DELIVERY_0_0003_STATUS == (
        "VERIFIED_FIRST_PARTY_VALUE_OWNER_RATIFIED_OPERATIVE_ADJUDICATION"
    )
    assert MONETARY_BASE_STATUS == "BOUND_PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE"
    assert EXACT_OKX_FEE_FORMULA_STATUS == "UNPROVEN"
    body = _body()
    assert body.conservative_reserve_rate == "0.0003"
    assert body.conservative_reserve_rate_is_okx_fee_truth is False
    assert body.proven_normal_expiry_rate == "0.0001"
    assert body.normal_expiry_rate_role == "HISTORICAL_SUPERSEDED_NON_OPERATIVE"
    assert "okx" not in body.internal_notional_envelope_form.lower()
    with pytest.raises(
        ExactFormulaBodyError,
        match="PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_NOT_OKX_FEE_TRUTH",
    ):
        _body(claim_0003_is_okx_fee_truth=True)
    with pytest.raises(
        ExactFormulaBodyError,
        match="HISTORICAL_SUPPORT_RATE_0_0001_IS_NOT_OPERATIVE",
    ):
        _body(consume_0001_as_operative_fee_input=True)


def test_internal_output_is_not_usdc_and_cover_usdc_stays_uninstantiated() -> None:
    body = _body()
    assert body.output_unit == PEAK_TRADE_INTERNAL_NOTIONAL_UNIT
    assert body.output_unit != "USDC"
    assert "USDC" not in body.output_unit
    assert body.cover_usdc_status == COVER_USDC_STATUS == "UNINSTANTIATED"
    assert body.fx_applied is False
    assert body.rounding_applied is False
    assert body.fx_status == FX_STATUS
    assert body.rounding_status == ROUNDING_STATUS
    assert body.sum_internal_numeric_status == SUM_INTERNAL_NUMERIC_STATUS
    assert body.sum_internal_numeric == "NONE"
    assert body.numeric_funding_amount == NUMERIC_FUNDING_AMOUNT == "NONE"
    with pytest.raises(ExactFormulaBodyError, match="OUTPUT_UNIT_IS_NOT_USDC"):
        _body(label_output_usdc=True)
    with pytest.raises(
        ExactFormulaBodyError,
        match="COVER_USDC_REMAINS_UNINSTANTIATED",
    ):
        _body(instantiate_cover_usdc=True)
    with pytest.raises(
        ExactFormulaBodyError,
        match="COVER_USDC_REMAINS_UNINSTANTIATED",
    ):
        _body(apply_usd_usdc_conversion=True)
    with pytest.raises(
        ExactFormulaBodyError,
        match="COVER_USDC_REMAINS_UNINSTANTIATED",
    ):
        _body(apply_rounding=True)


def test_im_fresh_and_venue_min_avail_eq_are_floors_not_addends() -> None:
    body = _body()
    assert body.im_fresh_role == IM_FRESH_ROLE == "MANDATORY_FLOOR_NOT_ADDITIVE_RESERVE_TERM"
    assert body.venue_min_avail_eq_role == VENUE_MIN_AVAIL_EQ_ROLE
    assert "NEVER_ADDITIVE" in body.venue_min_avail_eq_role
    assert body.funding_rate_reserve == FUNDING_RATE_RESERVE
    assert body.funding_rate_reserve.startswith("EXCLUDED")
    with pytest.raises(
        ExactFormulaBodyError,
        match="IM_FRESH_IS_FLOOR_NOT_ADDITIVE_RESERVE_TERM",
    ):
        _body(add_im_fresh_to_sum=True)
    with pytest.raises(
        ExactFormulaBodyError,
        match="VENUE_MIN_AVAIL_EQ_IS_CONSTRAINT_FLOOR_NOT_ADDITIVE",
    ):
        _body(add_venue_min_avail_eq_to_sum=True)
    with pytest.raises(
        ExactFormulaBodyError,
        match="FUNDING_RATE_RESERVE_REMAINS_EXCLUDED",
    ):
        _body(include_funding_rate_reserve=True)


def test_uninstantiated_terms_cannot_become_a_funding_amount() -> None:
    body = _body()
    assert body.fee_reserve_rates_status == FEE_RESERVE_RATES_STATUS
    assert body.delivery_cover_internal_status == DELIVERY_COVER_INTERNAL_STATUS
    assert body.slippage_reserve_status == SLIPPAGE_RESERVE_STATUS
    assert body.mm_liq_buffer_status == MM_LIQ_BUFFER_STATUS
    expected_envelope = Decimal("1") * Decimal("0.0001") * Decimal("63043.7")
    expected_delivery = Decimal("0.0003") * expected_envelope
    assert body.internal_notional_envelope == format(expected_envelope, "f")
    assert body.delivery_cover_internal == format(expected_delivery, "f")
    assert body.internal_notional_is_okx_position_value is False
    assert PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE is False
    with pytest.raises(ExactFormulaBodyError, match="SECTION_W_FEE_RATES_NOT_FROZEN"):
        _body(freeze_section_w_fee_rates=True)
    with pytest.raises(ExactFormulaBodyError, match="SLIPPAGE_RESERVE_UNINSTANTIATED"):
        _body(instantiate_slippage=True)
    with pytest.raises(ExactFormulaBodyError, match="MM_LIQ_BUFFER_UNINSTANTIATED"):
        _body(instantiate_mm_liq=True)
    with pytest.raises(
        ExactFormulaBodyError,
        match="NUMERIC_FUNDING_AMOUNT_REMAINS_UNPROVEN",
    ):
        _body(produce_numeric_funding_amount=True)


def test_qty_greater_than_one_and_scaling_remain_blocked() -> None:
    assert QTY_LIMIT == Decimal("1")
    assert SCALING_AUTHORIZED is False
    with pytest.raises(
        Exception,
        match="QTY_NOT_MINIMUM_EXPOSURE_CANARY_LIMIT",
    ):
        _body(quantity="2")
    with pytest.raises(
        Exception,
        match="MULTI_FUTURE_NOT_AUTHORIZED",
    ):
        _body(multi_future_requested=True)


def test_z2e_go_does_not_authorize_live_order_or_funding() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert EXCHANGE_TRUTH_CHANGED is False
    assert Z2E_OWNER_GO in NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT
    body = _body()
    assert body.live_authorized is False
    assert body.testnet_authorized is False
    assert body.order_effect == "NONE"
    assert body.funding_executed is False
    assert body.scaling_authorized is False
    assert body.multi_future_authorized is False
    evaluation = evaluate_canary_submit_gates_v1(
        owner_go=Z2E_OWNER_GO,
        owner_go_consumed=False,
        authorization_scope=AUTHORIZATION_SCOPE,
        bound_origin_main_sha="abc",
        expected_origin_main_sha="abc",
        live_canary_authorized=True,
        live_enabled=True,
        live_armed=True,
        confirm_token=LIVE_CONFIRM_TOKEN,
        blocks_new_entry=False,
        unresolved_economic_divergence=False,
        live_reconciliation_proven=True,
        permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
        environment="LIVE",
        fixture_or_demo_or_testnet=False,
        max_notional="6.30437",
        min_executable_notional="6.30437",
        order_count=0,
        position_count=0,
        exposure_above_minimum_bound=False,
        live_canary_cybersecurity_gate="PASS",
        rest_host="eea.okx.com",
        secretref_uri="secretref://vault/peak-trade/live-canary-minimum-exposure/okx",
    )
    assert evaluation.submit_allowed is False
    assert "REEVALUATION_OR_PREPARATION_GO_CANNOT_AUTHORIZE_SUBMIT" in evaluation.reasons


def test_z2e_docs_bind_internal_formula_body_without_rewriting_exchange_truth() -> None:
    section = _z2e_section(_read(MASTER_RUNBOOK))
    required = (
        f"B08_EXACT_FORMULA_BODY_KIND={B08_EXACT_FORMULA_BODY_KIND}",
        f"B08_EXACT_FORMULA_BODY_STATUS={B08_EXACT_FORMULA_BODY_STATUS}",
        "NORMAL_EXPIRY_RATE=0.0001",
        "NORMAL_EXPIRY_RATE_ROLE=PROVEN_APPLICABILITY_NON_OPERATIVE",
        "PEAK_TRADE_EXPIRY_RESERVE_RATE=0.0003",
        "PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH=false",
        "MONETARY_BASE=UNPROVEN",
        "EXACT_OKX_FEE_FORMULA=UNPROVEN",
        "API_DELIVERY_0_0003=NON_OPERATIVE",
        "POSITION_VALUE_ALGEBRA=UNPROVEN",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "COVER_USDC=UNINSTANTIATED",
        "FX_APPLIED=false",
        "ROUNDING_APPLIED=false",
        "NUMERIC_FUNDING_AMOUNT=NONE",
        "IM_FRESH_ROLE=MANDATORY_FLOOR_NOT_ADDITIVE_RESERVE_TERM",
        "VENUE_MIN_AVAIL_EQ_ROLE=CONSTRAINT_AND_POSSIBLE_FLOOR_NEVER_ADDITIVE",
        "FUNDING_RATE_RESERVE=EXCLUDED_UNRESOLVED_AND_NOT_USABLE",
        "QTY_LIMIT=1",
        "SCALING_AUTHORIZED=false",
        "MULTI_FUTURE_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "FUNDING_EXECUTED=false",
        "EXCHANGE_TRUTH_CHANGED=false",
        f"OWNER_GO={Z2E_OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "EARLIEST_UNRESOLVED_DEPENDENCY=UNINSTANTIATED_SLIPPAGE_MMR_FX_ROUNDING",
        "NO_OKX_FEE_FORMULA_INVENTION",
        "NO_API_DELIVERY_0_0003_PROMOTION",
        "NO_0_0001_PROMOTION_TO_OPERATIVE_COMPUTATION",
        "NO_MONETARY_BASE_INVENTION",
        "NO_USD_EQUALS_USDC",
        "NO_USDC_PRECISION_INVENTION",
        "NO_RESERVE_REDUCTION",
        "NO_AUTHORITY_WIDENING",
        "NO_FUNDING",
        "NO_EXECUTE",
    )
    for marker in required:
        assert marker in section, f"missing Z2E marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nSCALING_AUTHORIZED=true\n",
        "\nFUNDING_AMOUNT_PROVEN=true\n",
        "\nCOVER_USDC_STATUS=PROVEN\n",
        "\nEXCHANGE_TRUTH_CHANGED=true\n",
        "\nPEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH=true\n",
        "\nFX_APPLIED=true\n",
        "\nROUNDING_APPLIED=true\n",
        "OKX_EXPIRY_FEE_FORMULA=",
        "\nUSD_EQUALS_USDC=true\n",
    )
    for assignment in forbidden:
        assert assignment not in section, f"forbidden assignment present: {assignment!r}"


def test_map_of_truth_and_spec_record_z2e_as_consumed_historical() -> None:
    mot = _read(MAP_OF_TRUTH)
    spec = _read(CANARY_SPEC)
    assert "§11.13.5.Z2E" in mot
    assert f"{Z2E_OWNER_GO}_STATUS=CONSUMED_CONTRACT_ONLY_NOT_EXECUTE" in mot
    assert f"{NEXT_POINTER}_STATUS=CONSUMED_CONTRACT_ONLY_NOT_EXECUTE" in mot
    assert "B08_EXACT_FORMULA_BODY_STATUS=RATIFIED_INTERNAL_CONSERVATIVE_QTY1_NOT_COVER_USDC" in mot
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in mot
    assert Z2E_OWNER_GO in spec
    assert NEXT_POINTER in spec
    assert "Current SSOT: Master Runbook §11.13.5.Z2E." not in spec
