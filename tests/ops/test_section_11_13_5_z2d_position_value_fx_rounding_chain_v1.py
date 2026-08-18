"""§11.13.5.Z2D remaining UNPROVEN Position-Value / FX / Rounding chain.

Code contract plus docs/governance invariants. Does not authorize Live,
Testnet, orders, funding, scaling, or Multi-Future. Does not invent OKX
PositionValue, USD/USDC conversion, or USDC rounding precision.
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.expiry_fee_economic_uncertainty_bound_v1 import (
    PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_FORM,
    PEAK_TRADE_INTERNAL_NOTIONAL_UNIT,
    QTY_LIMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.governance_state_matrix_v1 import (
    NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_value_fx_rounding_chain_v1 import (
    ACCOUNT_SETTLE_CCY,
    COVER_USDC_STATUS,
    EXCHANGE_TRUTH_CHANGED,
    OKX_POSITION_VALUE_ALGEBRA_STATUS,
    PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE,
    PUBLIC_SETTLE_CCY,
    ROUNDING_APPLIED,
    RULE_FX,
    RULE_FX_STATUS,
    RULE_ROUNDING,
    RULE_ROUNDING_STATUS,
    SCALING_AUTHORIZED,
    TICK_SZ_IS_NOT_USDC_PRECISION,
    USD_USDC_CONVERSION_APPLIED,
    USD_USDC_PARITY_ASSUMED,
    USDC_PRECISION_STATUS,
    PositionValueFxRoundingChainError,
    classify_qty_one_position_value_fx_rounding_chain_v1,
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

Z2D_HEADING = (
    "### 11.13.5.Z2D Remaining unproven Position-Value / FX / Rounding chain "
    "for qty=1 operational reserve"
)
NEXT_POINTER = "OWNER_GO_REQUIRED_TO_RATIFY_EXACT_FORMULA_BODY"
Z2D_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_RESOLVE_REMAINING_UNPROVEN_POSITION_VALUE_FX_AND_ROUNDING_"
    "FOR_OPERATIONAL_RESERVE"
)

_CHAIN_KWARGS = {
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


def _z2d_section(text: str) -> str:
    start = text.find(Z2D_HEADING)
    assert start >= 0, "missing §11.13.5.Z2D heading"
    end = text.find("## 11.14 Live order and economic evidence ladder", start)
    assert end > start, "missing §11.14 boundary after Z2D"
    return text[start:end]


def _chain(**overrides: object):
    kwargs = dict(_CHAIN_KWARGS)
    kwargs.update(overrides)
    return classify_qty_one_position_value_fx_rounding_chain_v1(**kwargs)


def test_exchange_truth_remains_unproven_and_separated_from_internal_envelope() -> None:
    assert OKX_POSITION_VALUE_ALGEBRA_STATUS == "UNPROVEN"
    assert PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE is False
    assert EXCHANGE_TRUTH_CHANGED is False
    assert RULE_FX == "FX-VENUE-CONVERT"
    assert RULE_FX_STATUS == "UNPROVEN"
    assert USD_USDC_PARITY_ASSUMED is False
    assert USD_USDC_CONVERSION_APPLIED is False
    assert COVER_USDC_STATUS == "UNINSTANTIATED"
    assert PUBLIC_SETTLE_CCY == "USD"
    assert ACCOUNT_SETTLE_CCY == "USDC"
    assert RULE_ROUNDING == "RND-CEIL-VENUE-CCY-PRECISION-AFTER-COMPOSITION"
    assert RULE_ROUNDING_STATUS == "UNPROVEN"
    assert ROUNDING_APPLIED is False
    assert USDC_PRECISION_STATUS == "UNPROVEN"
    assert TICK_SZ_IS_NOT_USDC_PRECISION is True
    assert SCALING_AUTHORIZED is False
    chain = _chain()
    assert chain.okx_position_value_algebra_status == "UNPROVEN"
    assert chain.peak_trade_internal_position_value_is_okx_position_value is False
    assert chain.exchange_truth_changed is False
    assert chain.peak_trade_internal_position_value_envelope_form == (
        PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_FORM
    )
    assert "okx" not in chain.peak_trade_internal_position_value_envelope_form.lower()
    assert chain.rule_fx_status == "UNPROVEN"
    assert chain.usd_usdc_conversion_applied is False
    assert chain.cover_usdc_status == "UNINSTANTIATED"
    assert chain.rounding_applied is False
    assert chain.usdc_precision_status == "UNPROVEN"


def test_qty_one_reuses_existing_u_envelope_without_fx_or_rounding() -> None:
    first = _chain()
    second = _chain()
    expected_envelope = Decimal("1") * Decimal("0.0001") * Decimal("63043.7")
    assert first.peak_trade_internal_position_value_envelope == format(expected_envelope, "f")
    assert first.envelope_unit == PEAK_TRADE_INTERNAL_NOTIONAL_UNIT
    assert first.to_dict() == second.to_dict()
    assert first.quantity == "1"
    assert first.qty_limit == "1"
    assert first.minimum_exposure_only is True
    assert first.scaling_authorized is False
    assert first.multi_future_authorized is False
    assert first.live_authorized is False
    assert first.testnet_authorized is False
    assert first.order_effect == "NONE"
    assert first.funding_executed is False
    assert first.public_settle_ccy != first.account_settle_ccy


def test_qty_greater_than_one_is_not_released() -> None:
    with pytest.raises(
        PositionValueFxRoundingChainError,
        match="QTY_NOT_MINIMUM_EXPOSURE_CANARY_LIMIT",
    ):
        _chain(quantity="2")


def test_missing_proven_local_quantity_fails_closed() -> None:
    with pytest.raises(
        PositionValueFxRoundingChainError,
        match="MISSING_PROVEN_LOCAL_QUANTITY:instrument_ct_val",
    ):
        _chain(instrument_ct_val="")
    with pytest.raises(
        PositionValueFxRoundingChainError,
        match="MISSING_PROVEN_LOCAL_QUANTITY:reference_price",
    ):
        _chain(reference_price="")


def test_exchange_formula_fx_and_rounding_inventions_fail_closed() -> None:
    with pytest.raises(
        PositionValueFxRoundingChainError,
        match="OKX_POSITION_VALUE_ALGEBRA_REMAINS_UNPROVEN",
    ):
        _chain(claim_okx_position_value=True)
    with pytest.raises(
        PositionValueFxRoundingChainError,
        match="USD_USDC_CONVERSION_UNPROVEN",
    ):
        _chain(assume_usd_equals_usdc=True)
    with pytest.raises(
        PositionValueFxRoundingChainError,
        match="USD_USDC_CONVERSION_UNPROVEN",
    ):
        _chain(apply_usd_usdc_conversion=True)
    with pytest.raises(
        PositionValueFxRoundingChainError,
        match="USDC_ROUNDING_PRECISION_UNPROVEN",
    ):
        _chain(apply_rounding=True)
    with pytest.raises(
        PositionValueFxRoundingChainError,
        match="USDC_ROUNDING_PRECISION_UNPROVEN",
    ):
        _chain(treat_tick_sz_as_usdc_precision=True)


def test_wrong_scope_or_multi_future_fails_closed() -> None:
    with pytest.raises(
        PositionValueFxRoundingChainError,
        match="SCOPE_NOT_MINIMUM_EXPOSURE_CANARY",
    ):
        _chain(authorization_scope="LIVE_BOUNDED_SINGLE_FUTURE")
    with pytest.raises(
        PositionValueFxRoundingChainError,
        match="MULTI_FUTURE_NOT_AUTHORIZED",
    ):
        classify_qty_one_position_value_fx_rounding_chain_v1(
            **_CHAIN_KWARGS,
            multi_future_requested=True,
        )


def test_z2d_go_does_not_authorize_live_order_or_funding() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert QTY_LIMIT == Decimal("1")
    assert Z2D_OWNER_GO in NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT
    evaluation = evaluate_canary_submit_gates_v1(
        owner_go=Z2D_OWNER_GO,
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


def test_z2d_docs_bind_internal_policy_without_rewriting_exchange_truth() -> None:
    section = _z2d_section(_read(MASTER_RUNBOOK))
    required = (
        "POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN",
        "PEAK_TRADE_U_NOTIONAL_FORM=qty * ctVal * markPx",
        "PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE=false",
        "RULE_FX=FX-VENUE-CONVERT",
        "RULE_FX_STATUS=UNPROVEN",
        "USD_AND_USDC_REMAIN_STRICTLY_DISTINCT_UNITS=true",
        "USD_USDC_PARITY_ASSUMED=false",
        "USD_USDC_CONVERSION_APPLIED=false",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "PUBLIC_SETTLE_CCY=USD",
        "ACCOUNT_SETTLE_CCY=USDC",
        "RULE_ROUNDING=RND-CEIL-VENUE-CCY-PRECISION-AFTER-COMPOSITION",
        "RULE_ROUNDING_STATUS=UNPROVEN",
        "ROUNDING_APPLIED=false",
        "USDC_PRECISION_STATUS=UNPROVEN",
        "TICK_SZ_IS_NOT_USDC_PRECISION=true",
        "EXCHANGE_TRUTH_CHANGED=false",
        "OEM_FEE_MONETARY_BASE_STATUS=UNPROVEN",
        "PROVEN_NORMAL_EXPIRY_RATE=0.0001",
        "PEAK_TRADE_EXPIRY_RESERVE_RATE=0.0003",
        "PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH=false",
        "MINIMUM_EXPOSURE_ONLY=true",
        "QTY_LIMIT=1",
        "SCALING_AUTHORIZED=false",
        "MULTI_FUTURE_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "FUNDING_EXECUTED=false",
        "Z2B_APPLICABILITY_AND_RATE_REMAIN_BINDING=true",
        "Z2C_INTERNAL_EXPIRY_BOUND_REMAINS_BINDING=true",
        f"OWNER_GO={Z2D_OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "EARLIEST_UNRESOLVED_DEPENDENCY=B08_EXACT_FORMULA_BODY_NOT_RATIFIED",
        "NO_OKX_POSITION_VALUE_FORMULA_INVENTION",
        "NO_USD_EQUALS_USDC_ASSUMPTION",
        "NO_USDC_PRECISION_INVENTION",
        "NO_SCALING_FROM_THIS_BOUND",
        "NO_MULTI_FUTURE_FROM_THIS_BOUND",
        "NO_EXECUTE",
        "NO_FUNDING",
    )
    for marker in required:
        assert marker in section, f"missing Z2D marker: {marker}"
    forbidden = (
        "\nPOSITION_VALUE_ALGEBRA_STATUS=PROVEN\n",
        "\nRULE_FX_STATUS=PROVEN\n",
        "\nRULE_ROUNDING_STATUS=PROVEN\n",
        "\nUSD_USDC_PARITY_ASSUMED=true\n",
        "\nUSD_USDC_CONVERSION_APPLIED=true\n",
        "\nROUNDING_APPLIED=true\n",
        "\nCOVER_USDC_STATUS=PROVEN\n",
        "\nEXCHANGE_TRUTH_CHANGED=true\n",
        "\nOEM_FEE_MONETARY_BASE_STATUS=PROVEN\n",
        "\nLIVE_AUTHORIZED=true\n",
        "\nSCALING_AUTHORIZED=true\n",
        "\nFUNDING_AMOUNT_PROVEN=true\n",
        "OKX_POSITION_VALUE_FORMULA=",
        "USD_EQUALS_USDC=true",
    )
    for assignment in forbidden:
        assert assignment not in section, f"forbidden assignment present: {assignment!r}"


def test_map_of_truth_and_spec_follow_z2d_current_pointer() -> None:
    mot = _read(MAP_OF_TRUTH)
    spec = _read(CANARY_SPEC)
    assert "§11.13.5.Z2D" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}" in mot
    assert f"{Z2D_OWNER_GO}_STATUS=CONSUMED_CONTRACT_ONLY_NOT_EXECUTE" in mot
    assert "POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN" in mot
    assert "RULE_FX_STATUS=UNPROVEN" in mot
    assert "RULE_ROUNDING_STATUS=UNPROVEN" in mot
    assert "Current SSOT: Master Runbook §11.13.5.Z2D." in spec
    assert Z2D_OWNER_GO in spec
    assert NEXT_POINTER in spec
    assert "Current SSOT: Master Runbook §11.13.5.Z2C." not in spec
