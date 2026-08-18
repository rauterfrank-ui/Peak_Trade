"""§11.13.5.Z2C internal conservative expiry-fee economic-uncertainty bound.

Code contract plus docs/governance invariants. Does not authorize Live,
Testnet, orders, funding, scaling, or Multi-Future.
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
    ABSOLUTE_BOUND_USES_UNPROVEN_EXCHANGE_FORMULA,
    ACTUAL_EXPIRY_FEE_AMOUNT_STATUS,
    OEM_FEE_MONETARY_BASE_STATUS,
    OPERATIVE_EXPIRY_FEE_RATE,
    PEAK_TRADE_EXPIRY_RESERVE_RATE,
    PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH,
    PEAK_TRADE_INTERNAL_NOTIONAL_UNIT,
    PROVEN_NORMAL_EXPIRY_RATE,
    QTY_LIMIT,
    SCALING_AUTHORIZED,
    ExpiryFeeEconomicUncertaintyBoundError,
    evaluate_internal_expiry_fee_economic_uncertainty_bound_v1,
    reconcile_observed_expiry_fee_against_internal_bound_v1,
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

Z2C_HEADING = (
    "### 11.13.5.Z2C Bound unproven normal-expiry-fee economic risk with "
    "internal conservative reserve"
)
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_TO_RESOLVE_REMAINING_UNPROVEN_POSITION_VALUE_FX_AND_ROUNDING_"
    "FOR_OPERATIONAL_RESERVE"
)
Z2C_OWNER_GO = (
    "OWNER_GO_BOUND_UNPROVEN_NORMAL_EXPIRY_FEE_ECONOMIC_RISK_WITH_INTERNAL_CONSERVATIVE_RESERVE"
)

_BOUND_KWARGS = {
    "quantity": "1",
    "instrument_ct_val": "0.0001",
    "reference_price": "63043.7",
    "instrument_id": DEFAULT_INSTRUMENT_ID,
    "authorization_scope": AUTHORIZATION_SCOPE,
}


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2c_section(text: str) -> str:
    start = text.find(Z2C_HEADING)
    assert start >= 0, "missing §11.13.5.Z2C heading"
    end = text.find("## 11.14 Live order and economic evidence ladder", start)
    assert end > start, "missing §11.14 boundary after Z2C"
    return text[start:end]


def _bound(**overrides: str):
    kwargs = dict(_BOUND_KWARGS)
    kwargs.update(overrides)
    return evaluate_internal_expiry_fee_economic_uncertainty_bound_v1(**kwargs)


def test_normative_rate_and_internal_reserve_remain_separated() -> None:
    assert PROVEN_NORMAL_EXPIRY_RATE == Decimal("0.0001")
    assert PEAK_TRADE_EXPIRY_RESERVE_RATE == Decimal("0.0003")
    assert PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH is False
    assert OEM_FEE_MONETARY_BASE_STATUS == "UNPROVEN"
    assert ACTUAL_EXPIRY_FEE_AMOUNT_STATUS == "UNPROVEN"
    assert OPERATIVE_EXPIRY_FEE_RATE == "NONE"
    assert ABSOLUTE_BOUND_USES_UNPROVEN_EXCHANGE_FORMULA is False
    assert SCALING_AUTHORIZED is False
    bound = _bound()
    assert bound.proven_normal_expiry_rate == "0.0001"
    assert bound.reserve_rate == "0.0003"
    assert bound.reserve_rate_is_okx_fee_truth is False
    assert bound.oem_fee_monetary_base_status == "UNPROVEN"
    assert bound.actual_expiry_fee_amount_status == "UNPROVEN"
    assert bound.operative_expiry_fee_rate == "NONE"
    assert bound.uses_unproven_exchange_formula is False
    assert "okx" not in bound.derivation.lower()


def test_qty_one_forms_deterministic_internal_absolute_bound() -> None:
    first = _bound()
    second = _bound()
    expected_envelope = Decimal("1") * Decimal("0.0001") * Decimal("63043.7")
    expected_bound = Decimal("0.0003") * expected_envelope
    assert first.absolute_economic_uncertainty_bound == format(expected_bound, "f")
    assert first.internal_notional_envelope == format(expected_envelope, "f")
    assert first.bound_unit == PEAK_TRADE_INTERNAL_NOTIONAL_UNIT
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
    assert first.post_settlement_reconciliation_required is True
    assert first.observed_fee_can_rewrite_normative_truth is False


def test_qty_greater_than_one_is_not_released() -> None:
    with pytest.raises(
        ExpiryFeeEconomicUncertaintyBoundError,
        match="QTY_NOT_MINIMUM_EXPOSURE_CANARY_LIMIT",
    ):
        _bound(quantity="2")


def test_missing_proven_local_quantity_fails_closed() -> None:
    with pytest.raises(
        ExpiryFeeEconomicUncertaintyBoundError,
        match="MISSING_PROVEN_LOCAL_QUANTITY:instrument_ct_val",
    ):
        _bound(instrument_ct_val="")
    with pytest.raises(
        ExpiryFeeEconomicUncertaintyBoundError,
        match="MISSING_PROVEN_LOCAL_QUANTITY:reference_price",
    ):
        _bound(reference_price="")
    with pytest.raises(
        ExpiryFeeEconomicUncertaintyBoundError,
        match="MISSING_PROVEN_LOCAL_QUANTITY:quantity",
    ):
        _bound(quantity="")


def test_wrong_scope_or_multi_future_fails_closed() -> None:
    with pytest.raises(
        ExpiryFeeEconomicUncertaintyBoundError,
        match="SCOPE_NOT_MINIMUM_EXPOSURE_CANARY",
    ):
        _bound(authorization_scope="LIVE_BOUNDED_SINGLE_FUTURE")
    with pytest.raises(
        ExpiryFeeEconomicUncertaintyBoundError,
        match="MULTI_FUTURE_NOT_AUTHORIZED",
    ):
        evaluate_internal_expiry_fee_economic_uncertainty_bound_v1(
            **_BOUND_KWARGS,
            multi_future_requested=True,
        )


def test_observed_fee_within_bound_does_not_rewrite_normative_truth() -> None:
    bound = _bound()
    result = reconcile_observed_expiry_fee_against_internal_bound_v1(
        bound=bound,
        observed_fee_amount="0.001",
        observed_fee_unit=PEAK_TRADE_INTERNAL_NOTIONAL_UNIT,
    )
    assert result.reconciliation_status == "RECONCILIATION_PASS_NORMATIVE_TRUTH_UNCHANGED"
    assert result.fail_closed is False
    assert result.further_canary_requires_review is False
    assert result.scaling_blocked is True
    assert result.observed_fee_rewrote_normative_truth is False
    assert result.proven_normal_expiry_rate == "0.0001"
    assert result.oem_fee_monetary_base_status == "UNPROVEN"
    assert result.actual_expiry_fee_amount_status == "UNPROVEN"
    assert result.operative_expiry_fee_rate == "NONE"
    assert result.live_authorized is False
    assert result.testnet_authorized is False
    assert result.order_effect == "NONE"


def test_observed_fee_above_bound_fails_closed_and_requires_review() -> None:
    bound = _bound()
    result = reconcile_observed_expiry_fee_against_internal_bound_v1(
        bound=bound,
        observed_fee_amount="1",
        observed_fee_unit=PEAK_TRADE_INTERNAL_NOTIONAL_UNIT,
    )
    assert result.reconciliation_status == "FAIL_CLOSED_BOUND_EXCEEDED_REVIEW_REQUIRED"
    assert result.fail_closed is True
    assert result.scaling_blocked is True
    assert result.further_canary_requires_review is True
    assert result.observed_fee_rewrote_normative_truth is False
    assert result.proven_normal_expiry_rate == "0.0001"
    assert result.operative_expiry_fee_rate == "NONE"


def test_observed_fee_unit_mismatch_fails_closed_because_fx_unproven() -> None:
    bound = _bound()
    with pytest.raises(
        ExpiryFeeEconomicUncertaintyBoundError,
        match="UNIT_MISMATCH_FX_UNPROVEN",
    ):
        reconcile_observed_expiry_fee_against_internal_bound_v1(
            bound=bound,
            observed_fee_amount="0.001",
            observed_fee_unit="USDC",
        )


def test_z2c_go_does_not_authorize_live_order_or_funding() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert QTY_LIMIT == Decimal("1")
    assert Z2C_OWNER_GO in NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT
    evaluation = evaluate_canary_submit_gates_v1(
        owner_go=Z2C_OWNER_GO,
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


def test_z2c_docs_bind_internal_policy_without_rewriting_exchange_truth() -> None:
    section = _z2c_section(_read(MASTER_RUNBOOK))
    required = (
        "NORMAL_EXPIRY_FEE_RATE_DECIMAL=0.0001",
        "PROVEN_NORMAL_EXPIRY_RATE=0.0001",
        "PEAK_TRADE_EXPIRY_RESERVE_RATE=0.0003",
        "PEAK_TRADE_EXPIRY_RESERVE_RATE_SOURCE=CONSERVATIVE_INTERNAL_POLICY",
        "PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH=false",
        "OEM_FEE_MONETARY_BASE_STATUS=UNPROVEN",
        "ACTUAL_EXPIRY_FEE_AMOUNT_STATUS=UNPROVEN",
        "OPERATIVE_EXPIRY_FEE_RATE=NONE",
        "RATE_PROVEN_NON_OPERATIVE=true",
        "W_PACK_DELIVERY_0_0003_NOT_OPERATIVE=true",
        "API_DELIVERY_0_0003_STATUS=UNPROVEN",
        "ABSOLUTE_BOUND_USES_UNPROVEN_EXCHANGE_FORMULA=false",
        "POST_SETTLEMENT_RECONCILIATION_REQUIRED=true",
        "OBSERVED_FEE_MUST_NOT_REWRITE_NORMATIVE_TRUTH=true",
        "MINIMUM_EXPOSURE_ONLY=true",
        "QTY_LIMIT=1",
        "SCALING_AUTHORIZED=false",
        "MULTI_FUTURE_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "FUNDING_EXECUTED=false",
        "Z2B_APPLICABILITY_AND_RATE_REMAIN_BINDING=true",
        "OEM_MONETARY_BASE_NOT_CRITICAL_PATH_FOR_MINIMUM_EXPOSURE_CANARY=true",
        f"OWNER_GO={Z2C_OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "EARLIEST_UNRESOLVED_DEPENDENCY=REMAINING_UNPROVEN_POSITION_VALUE_FX_AND_ROUNDING",
        "NO_GENERIC_UNKNOWN_FEE_WAIVER",
        "NO_UNKNOWN_MARGIN_EXCEPTION",
        "NO_UNKNOWN_LIQUIDATION_EXCEPTION",
        "NO_SCALING_FROM_THIS_BOUND",
        "NO_MULTI_FUTURE_FROM_THIS_BOUND",
        "NO_EXECUTE",
        "NO_FUNDING",
    )
    for marker in required:
        assert marker in section, f"missing Z2C marker: {marker}"
    forbidden = (
        "\nOPERATIVE_EXPIRY_FEE_RATE=0.0001\n",
        "\nOPERATIVE_EXPIRY_FEE_RATE=0.0003\n",
        "\nOEM_FEE_MONETARY_BASE_STATUS=PROVEN\n",
        "\nACTUAL_EXPIRY_FEE_AMOUNT_STATUS=PROVEN\n",
        "\nAPI_DELIVERY_0_0003_STATUS=PROVEN\n",
        "\nLIVE_AUTHORIZED=true\n",
        "\nSCALING_AUTHORIZED=true\n",
        "\nFUNDING_AMOUNT_PROVEN=true\n",
        "OKX_EXPIRY_FEE_FORMULA=",
        "OKX_EXPIRY_FEE_FORMULA=true",
    )
    for assignment in forbidden:
        assert assignment not in section, f"forbidden assignment present: {assignment!r}"


def test_map_of_truth_and_spec_follow_z2c_current_pointer() -> None:
    mot = _read(MAP_OF_TRUTH)
    spec = _read(CANARY_SPEC)
    assert "§11.13.5.Z2C" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}" in mot
    assert f"{Z2C_OWNER_GO}_STATUS=CONSUMED_CONTRACT_ONLY_NOT_EXECUTE" in mot
    assert (
        "OWNER_GO_REQUIRED_TO_SUPPLY_OR_POINT_TO_A_CURRENT_NORMATIVE_OKX_EEA_OEM_XPERP_NORMAL_EXPIRY_FEE_MONETARY_BASE_STATUS=SUPERSEDED_NOT_CRITICAL_PATH_FOR_MINIMUM_EXPOSURE_CANARY"
        in mot
    )
    assert "OPERATIVE_EXPIRY_FEE_RATE=NONE" in mot
    assert "Current SSOT: Master Runbook §11.13.5.Z2C." in spec
    assert Z2C_OWNER_GO in spec
    assert NEXT_POINTER in spec
