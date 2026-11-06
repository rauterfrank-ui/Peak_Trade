"""§11.13.5.Z2F uninstantiated B08 term-instance and FX / rounding binding.

Code contract plus docs/governance invariants. Does not authorize Live,
Testnet, orders, funding, GET, scaling, or Multi-Future. Does not invent
OKX fee truth, a monetary base, COVER_USDC, or a numeric funding amount.
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.formula_term_instance_binding_v1 import (
    B08_EXACT_FORMULA_BODY_KIND,
    B08_EXACT_FORMULA_BODY_STATUS,
    CONSERVATIVE_RATE_0_0003_STATUS,
    CONSERVATIVE_RATE_KIND,
    COVER_USDC_STATUS,
    CTVAL_BOUND_CCY,
    CTVAL_BOUND_VALUE,
    CTVAL_DELIVERY_FEE_OPERAND_STATUS,
    CTVAL_TERM_KIND,
    CTVAL_TERM_STATUS,
    EXACT_OKX_FEE_FORMULA_STATUS,
    EXCHANGE_TRUTH_CHANGED,
    FX_KIND,
    FX_STATUS,
    FormulaTermInstanceBindingError,
    HISTORICAL_L_PACK_MARKPX,
    HISTORICAL_S_PACK_MARKPX,
    KIND_INTERNAL_POLICY,
    KIND_PROVEN,
    KIND_UNPROVEN,
    MARKPX_CURRENT_VALUE,
    MARKPX_TERM_KIND,
    MARKPX_TERM_STATUS,
    MONETARY_BASE_KIND,
    MONETARY_BASE_STATUS,
    NORMAL_EXPIRY_RATE_0_0001_STATUS,
    NUMERIC_FUNDING_AMOUNT,
    NUMERIC_FUNDING_AMOUNT_PRODUCED,
    OKX_POSITION_VALUE_ALGEBRA_STATUS,
    QTY_BOUND_VALUE,
    QTY_LIMIT,
    QTY_TERM_KIND,
    QTY_TERM_STATUS,
    ROUNDING_KIND,
    ROUNDING_STATUS,
    RULE_FX_STATUS,
    RULE_ROUNDING_STATUS,
    bind_qty_one_uninstantiated_formula_term_instances_v1,
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

Z2F_HEADING = "### 11.13.5.Z2F Bind uninstantiated formula-term instances and FX / rounding"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_INSTANTIATE_REMAINING_"
    "UNPROVEN_COVER_USDC_TERMS_BEFORE_FUNDING"
)
Z2F_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_BIND_UNINSTANTIATED_FORMULA_TERM_INSTANCES_AND_FX_ROUNDING_BEFORE_FUNDING"
)

_BIND_KWARGS = {
    "quantity": "1",
    "instrument_ct_val": "0.0001",
    "instrument_id": DEFAULT_INSTRUMENT_ID,
    "authorization_scope": AUTHORIZATION_SCOPE,
}


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2f_section(text: str) -> str:
    start = text.find(Z2F_HEADING)
    assert start >= 0, "missing §11.13.5.Z2F heading"
    end = text.find("### 11.13.5.Z2G", start)
    assert end > start, "missing §11.13.5.Z2G boundary after Z2F"
    return text[start:end]


def _bind(**overrides: object):
    kwargs = dict(_BIND_KWARGS)
    kwargs.update(overrides)
    return bind_qty_one_uninstantiated_formula_term_instances_v1(**kwargs)


def test_qty_and_ctval_are_proven_without_scaling() -> None:
    assert QTY_TERM_STATUS == KIND_PROVEN == "PROVEN"
    assert QTY_TERM_KIND == KIND_PROVEN
    assert QTY_BOUND_VALUE == "1"
    assert QTY_LIMIT == Decimal("1")
    assert CTVAL_TERM_STATUS == KIND_PROVEN
    assert CTVAL_TERM_KIND == KIND_PROVEN
    assert CTVAL_BOUND_VALUE == "0.0001"
    assert CTVAL_BOUND_CCY == "BTC"
    assert CTVAL_DELIVERY_FEE_OPERAND_STATUS == "UNPROVEN"
    bound = _bind()
    assert bound.qty_term_status == "PROVEN"
    assert bound.qty_bound_value == "1"
    assert bound.ctval_term_status == "PROVEN"
    assert bound.ctval_bound_value == "0.0001"
    assert bound.ctval_bound_ccy == "BTC"
    assert bound.ctval_delivery_fee_operand_status == "UNPROVEN"
    assert bound.scaling_authorized is False
    assert bound.multi_future_authorized is False
    with pytest.raises(
        FormulaTermInstanceBindingError,
        match="QTY_NOT_MINIMUM_EXPOSURE_CANARY_LIMIT",
    ):
        _bind(quantity="2")
    with pytest.raises(
        FormulaTermInstanceBindingError,
        match="CTVAL_NOT_CANONICAL_INSTRUMENT_METADATA",
    ):
        _bind(instrument_ct_val="0.01")
    with pytest.raises(FormulaTermInstanceBindingError, match="MULTI_FUTURE_NOT_AUTHORIZED"):
        _bind(multi_future_requested=True)


def test_markpx_remains_uninstantiated_runtime_term() -> None:
    assert MARKPX_TERM_STATUS == "UNINSTANTIATED"
    assert MARKPX_TERM_KIND == KIND_UNPROVEN
    assert MARKPX_CURRENT_VALUE == "UNINSTANTIATED"
    bound = _bind()
    assert bound.markpx_term_status == "UNINSTANTIATED"
    assert bound.markpx_current_value == "UNINSTANTIATED"
    assert bound.historical_markpx_is_not_current is True
    assert bound.no_live_markpx_get_this_step is True
    assert bound.markpx_current_value not in {HISTORICAL_L_PACK_MARKPX, HISTORICAL_S_PACK_MARKPX}
    with pytest.raises(
        FormulaTermInstanceBindingError,
        match="MARKPX_CURRENT_VALUE_REMAINS_UNINSTANTIATED",
    ):
        _bind(current_mark_px=HISTORICAL_L_PACK_MARKPX)
    with pytest.raises(
        FormulaTermInstanceBindingError,
        match="MARKPX_CURRENT_VALUE_REMAINS_UNINSTANTIATED",
    ):
        _bind(current_mark_px=HISTORICAL_S_PACK_MARKPX)
    with pytest.raises(
        FormulaTermInstanceBindingError,
        match="HISTORICAL_MARKPX_IS_NOT_CURRENT",
    ):
        _bind(freeze_historical_mark_px_as_current=True)
    with pytest.raises(
        FormulaTermInstanceBindingError,
        match="LIVE_MARKPX_GET_NOT_AUTHORIZED",
    ):
        _bind(execute_live_mark_px_get=True)


def test_monetary_base_fx_and_rounding_remain_unproven() -> None:
    assert MONETARY_BASE_STATUS == KIND_UNPROVEN == "UNPROVEN"
    assert MONETARY_BASE_KIND == KIND_UNPROVEN
    assert FX_STATUS == KIND_UNPROVEN
    assert FX_KIND == KIND_UNPROVEN
    assert RULE_FX_STATUS == "UNPROVEN"
    assert ROUNDING_STATUS == KIND_UNPROVEN
    assert ROUNDING_KIND == KIND_UNPROVEN
    assert RULE_ROUNDING_STATUS == "UNPROVEN"
    bound = _bind()
    assert bound.monetary_base_status == "UNPROVEN"
    assert bound.fx_status == "UNPROVEN"
    assert bound.fx_applied is False
    assert bound.usd_usdc_conversion_applied is False
    assert bound.normative_usd_usdc_conversion_defined_for_expiry_cover is False
    assert bound.rounding_status == "UNPROVEN"
    assert bound.rounding_applied is False
    assert bound.tick_sz_is_not_usdc_precision is True
    with pytest.raises(FormulaTermInstanceBindingError, match="MONETARY_BASE_REMAINS_UNPROVEN"):
        _bind(invent_monetary_base=True)
    with pytest.raises(FormulaTermInstanceBindingError, match="USD_USDC_CONVERSION_UNPROVEN"):
        _bind(apply_usd_usdc_conversion=True)
    with pytest.raises(FormulaTermInstanceBindingError, match="USD_USDC_CONVERSION_UNPROVEN"):
        _bind(assume_usd_equals_usdc=True)
    with pytest.raises(FormulaTermInstanceBindingError, match="USDC_ROUNDING_PRECISION_UNPROVEN"):
        _bind(apply_rounding=True)
    with pytest.raises(FormulaTermInstanceBindingError, match="USDC_ROUNDING_PRECISION_UNPROVEN"):
        _bind(invent_rounding_precision=True)
    with pytest.raises(FormulaTermInstanceBindingError, match="USDC_ROUNDING_PRECISION_UNPROVEN"):
        _bind(treat_tick_sz_as_usdc_precision=True)


def test_rates_and_cover_usdc_remain_separated_and_uninstantiated() -> None:
    assert NORMAL_EXPIRY_RATE_0_0001_STATUS == "HISTORICAL_SUPERSEDED"
    assert CONSERVATIVE_RATE_0_0003_STATUS == "PEAK_TRADE_POLICY_REUSE_OF_SAME_NUMERIC_VALUE"
    assert CONSERVATIVE_RATE_KIND == KIND_INTERNAL_POLICY
    assert EXACT_OKX_FEE_FORMULA_STATUS == "UNPROVEN"
    assert OKX_POSITION_VALUE_ALGEBRA_STATUS == "UNPROVEN"
    assert B08_EXACT_FORMULA_BODY_STATUS == "RATIFIED_INTERNAL_CONSERVATIVE_QTY1_NOT_COVER_USDC"
    assert COVER_USDC_STATUS == "UNINSTANTIATED"
    assert NUMERIC_FUNDING_AMOUNT_PRODUCED is False
    bound = _bind()
    assert bound.proven_normal_expiry_rate == "0.0001"
    assert bound.conservative_reserve_rate == "0.0003"
    assert bound.conservative_reserve_rate_is_okx_fee_truth is False
    assert bound.cover_usdc_status == "UNINSTANTIATED"
    assert bound.numeric_funding_amount == NUMERIC_FUNDING_AMOUNT == "NONE"
    assert bound.numeric_funding_amount_produced is False
    assert bound.b08_internal_algebra_status == B08_EXACT_FORMULA_BODY_STATUS
    assert bound.b08_exact_formula_body_kind == B08_EXACT_FORMULA_BODY_KIND
    assert bound.exchange_truth_changed is False
    with pytest.raises(
        FormulaTermInstanceBindingError,
        match="PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_NOT_OKX_FEE_TRUTH",
    ):
        _bind(claim_0003_is_okx_fee_truth=True)
    with pytest.raises(
        FormulaTermInstanceBindingError,
        match="CANONICAL_EXPIRY_RATE_CANNOT_RESET_TO_HISTORICAL_0001",
    ):
        _bind(reset_conservative_rate_to_0001=True)
    with pytest.raises(
        FormulaTermInstanceBindingError,
        match="HISTORICAL_SUPPORT_RATE_0_0001_IS_NOT_OPERATIVE",
    ):
        _bind(consume_0001_as_operative_fee_input=True)
    with pytest.raises(
        FormulaTermInstanceBindingError,
        match="COVER_USDC_REMAINS_UNINSTANTIATED",
    ):
        _bind(instantiate_cover_usdc=True)
    with pytest.raises(
        FormulaTermInstanceBindingError,
        match="NUMERIC_FUNDING_AMOUNT_REMAINS_UNPROVEN",
    ):
        _bind(produce_numeric_funding_amount=True)
    with pytest.raises(
        FormulaTermInstanceBindingError,
        match="OKX_POSITION_VALUE_ALGEBRA_REMAINS_UNPROVEN",
    ):
        _bind(claim_okx_position_value=True)


def test_z2f_go_does_not_authorize_live_order_or_funding() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert EXCHANGE_TRUTH_CHANGED is False
    assert Z2F_OWNER_GO in NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT
    bound = _bind()
    assert bound.live_authorized is False
    assert bound.testnet_authorized is False
    assert bound.order_effect == "NONE"
    assert bound.funding_executed is False
    evaluation = evaluate_canary_submit_gates_v1(
        owner_go=Z2F_OWNER_GO,
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


def test_z2f_docs_bind_term_instances_without_cover_usdc() -> None:
    section = _z2f_section(_read(MASTER_RUNBOOK))
    required = (
        "QTY_TERM_STATUS=PROVEN",
        "QTY_TERM_KIND=PROVEN",
        "QTY_BOUND_VALUE=1",
        "CTVAL_TERM_STATUS=PROVEN",
        "CTVAL_TERM_KIND=PROVEN",
        "CTVAL_BOUND_VALUE=0.0001",
        "CTVAL_BOUND_CCY=BTC",
        "CTVAL_DELIVERY_FEE_OPERAND_STATUS=UNPROVEN",
        "MARKPX_TERM_STATUS=UNINSTANTIATED",
        "MARKPX_TERM_KIND=UNPROVEN",
        "MARKPX_CURRENT_VALUE=UNINSTANTIATED",
        "HISTORICAL_MARKPX_IS_NOT_CURRENT=true",
        "NO_LIVE_MARKPX_GET_THIS_STEP=true",
        "MONETARY_BASE_STATUS=UNPROVEN",
        "FX_STATUS=UNPROVEN",
        "FX_KIND=UNPROVEN",
        "USD_USDC_CONVERSION_APPLIED=false",
        "ROUNDING_STATUS=UNPROVEN",
        "ROUNDING_KIND=UNPROVEN",
        "ROUNDING_APPLIED=false",
        "NORMAL_EXPIRY_RATE_0_0001_STATUS=PROVEN_APPLICABILITY_NON_OPERATIVE",
        "CONSERVATIVE_RATE_0_0003_STATUS=INTERNAL_CONSERVATIVE_POLICY_NOT_EXCHANGE_TRUTH",
        "CONSERVATIVE_RATE_KIND=INTERNAL_POLICY",
        "PEAK_TRADE_EXPIRY_RESERVE_RATE=0.0003",
        "PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH=false",
        "EXACT_OKX_FEE_FORMULA_STATUS=UNPROVEN",
        "POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN",
        f"B08_INTERNAL_ALGEBRA_STATUS={B08_EXACT_FORMULA_BODY_STATUS}",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "NUMERIC_FUNDING_AMOUNT_PRODUCED=false",
        "NUMERIC_FUNDING_AMOUNT=NONE",
        "QTY_LIMIT=1",
        "SCALING_AUTHORIZED=false",
        "MULTI_FUTURE_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "FUNDING_EXECUTED=false",
        "EXCHANGE_TRUTH_CHANGED=false",
        f"OWNER_GO={Z2F_OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "NO_OKX_FEE_FORMULA_INVENTION",
        "NO_USD_EQUALS_USDC",
        "NO_USDC_PRECISION_INVENTION",
        "NO_COVER_USDC_INSTANTIATION",
        "NO_NUMERIC_FUNDING_AMOUNT",
        "NO_FUNDING",
        "NO_EXECUTE",
    )
    for marker in required:
        assert marker in section, f"missing Z2F marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nSCALING_AUTHORIZED=true\n",
        "\nFUNDING_AMOUNT_PROVEN=true\n",
        "\nCOVER_USDC_STATUS=PROVEN\n",
        "\nEXCHANGE_TRUTH_CHANGED=true\n",
        "\nPEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH=true\n",
        "\nFX_APPLIED=true\n",
        "\nROUNDING_APPLIED=true\n",
        "\nFX_STATUS=PROVEN\n",
        "\nROUNDING_STATUS=PROVEN\n",
        "\nMONETARY_BASE_STATUS=PROVEN\n",
        "\nNUMERIC_FUNDING_AMOUNT_PRODUCED=true\n",
        "\nUSD_EQUALS_USDC=true\n",
        "OKX_EXPIRY_FEE_FORMULA=",
    )
    for assignment in forbidden:
        assert assignment not in section, f"forbidden assignment present: {assignment!r}"
    assert HISTORICAL_L_PACK_MARKPX not in section
    assert HISTORICAL_S_PACK_MARKPX not in section


def test_map_of_truth_and_spec_record_z2f_as_consumed_historical() -> None:
    mot = _read(MAP_OF_TRUTH)
    spec = _read(CANARY_SPEC)
    assert "§11.13.5.Z2F" in mot
    assert f"{Z2F_OWNER_GO}_STATUS=CONSUMED_CONTRACT_ONLY_NOT_EXECUTE" in mot
    assert f"{NEXT_POINTER}_STATUS=CONSUMED_GET_ONLY_MARKPX_OBSERVED_NOT_COVER_USDC" in mot
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in mot
    assert "FX_STATUS=UNPROVEN" in mot
    assert "ROUNDING_STATUS=UNPROVEN" in mot
    assert Z2F_OWNER_GO in spec
    assert NEXT_POINTER in spec
    assert "Current SSOT: Master Runbook §11.13.5.Z2F." not in spec
