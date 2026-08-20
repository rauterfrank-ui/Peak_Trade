"""Offline tests for §11.13.5 acctLv=2 documentary discriminator contract.

No network. Does not prove Rule C or unlock submit/live/canary.

Theoretical candidate A/B notional ratio is THEORETICAL_DOCUMENTARY_ONLY,
NOT_OKX_RUNTIME_PROOF.
"""

from __future__ import annotations

import inspect
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    SUBMIT_UNLOCKED,
)
from src.ops.section_11_13_5_okx_acct_lv2_unfilled_order_documentary_discriminator_contract_v1 import (
    ACCT_LV_FUTURES,
    ACCT_LV_MULTI_CURRENCY,
    ACCT_LV_PORTFOLIO,
    ACCT_LV_SPOT,
    CANDIDATE_A_CT_VAL,
    CANDIDATE_B_CT_VAL,
    DISCRIMINATION_CLASS,
    ENDPOINT_ORDER_PRECHECK,
    ENDPOINT_ORDER_SUBMIT,
    EXPECTED_DISCRIMINATION_FACTOR,
    LIVE_EEA_ACCT_LV_EVIDENCE_PATH,
    LIVE_EEA_ACCT_LV_EVIDENCE_VALUE,
    NOT_OKX_RUNTIME_PROOF,
    ORDER_FIELD_NOTIONAL_USD,
    PRECHECK_CANNOT_CREATE_ORDER,
    PRECHECK_DEFAULT_ENABLED,
    PRECHECK_EXECUTION_AUTHORIZED,
    PRECHECK_REQUEST_FIELDS,
    PRECHECK_RESPONSE_FIELDS,
    RULE_C_STATUS,
    SELECTED_PATH,
    OrderPrecheckExecutionForbiddenError,
    UnsupportedAcctLvFailClosedError,
    assert_no_submit_unlock_in_binding,
    order_precheck_execution_allowed,
    refuse_order_precheck_execution_v1,
    supports_order_precheck,
    theoretical_candidate_notional_ratio,
    theoretical_linear_notional_usd,
    unfilled_order_documentary_binding_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_live_eea_acct_lv_2_is_bound_to_existing_evidence_file() -> None:
    evidence = REPO_ROOT / LIVE_EEA_ACCT_LV_EVIDENCE_PATH
    assert evidence.is_file()
    text = evidence.read_text(encoding="utf-8")
    assert '"acctLv": "2"' in text
    assert '"path": "/api/v5/account/config"' in text
    assert '"HOST": "eea.okx.com"' in text
    assert LIVE_EEA_ACCT_LV_EVIDENCE_VALUE == ACCT_LV_FUTURES


def test_precheck_applicability_follows_official_v5_modes() -> None:
    assert supports_order_precheck(ACCT_LV_MULTI_CURRENCY) is True
    assert supports_order_precheck(ACCT_LV_PORTFOLIO) is True
    assert supports_order_precheck(ACCT_LV_FUTURES) is False
    assert supports_order_precheck(ACCT_LV_SPOT) is False
    with pytest.raises(UnsupportedAcctLvFailClosedError, match="ACCT_LV_UNKNOWN"):
        supports_order_precheck(None)
    with pytest.raises(UnsupportedAcctLvFailClosedError, match="ACCT_LV_UNSUPPORTED"):
        supports_order_precheck("UNKNOWN")


def test_precheck_execution_is_hard_blocked_for_every_acct_lv() -> None:
    assert PRECHECK_DEFAULT_ENABLED is False
    assert PRECHECK_EXECUTION_AUTHORIZED is False
    assert PRECHECK_CANNOT_CREATE_ORDER is True
    for acct_lv in (
        ACCT_LV_SPOT,
        ACCT_LV_FUTURES,
        ACCT_LV_MULTI_CURRENCY,
        ACCT_LV_PORTFOLIO,
        None,
    ):
        assert order_precheck_execution_allowed(acct_lv) is False
    with pytest.raises(OrderPrecheckExecutionForbiddenError):
        refuse_order_precheck_execution_v1()


def test_precheck_endpoint_is_isolated_from_order_submit() -> None:
    assert ENDPOINT_ORDER_PRECHECK == "/api/v5/trade/order-precheck"
    assert ENDPOINT_ORDER_SUBMIT == "/api/v5/trade/order"
    assert ENDPOINT_ORDER_PRECHECK != ENDPOINT_ORDER_SUBMIT
    source = inspect.getsource(
        __import__(
            "src.ops.section_11_13_5_okx_acct_lv2_unfilled_order_documentary_discriminator_contract_v1",
            fromlist=["refuse_order_precheck_execution_v1"],
        )
    )
    assert "urlopen" not in source
    assert "http.client" not in source
    assert "requests." not in source
    assert "post_entry_order" not in source
    assert "run_canary_submit_transport_v1" not in source


def test_precheck_fields_match_official_v5_names() -> None:
    assert PRECHECK_REQUEST_FIELDS == (
        "instId",
        "tdMode",
        "side",
        "ordType",
        "sz",
        "px",
    )
    assert "imr" in PRECHECK_RESPONSE_FIELDS
    assert "imrChg" in PRECHECK_RESPONSE_FIELDS
    assert "mmr" in PRECHECK_RESPONSE_FIELDS
    assert "mmrChg" in PRECHECK_RESPONSE_FIELDS
    assert "adjEqChg" in PRECHECK_RESPONSE_FIELDS
    assert "mgnRatioChg" in PRECHECK_RESPONSE_FIELDS
    assert "liqPxDiff" in PRECHECK_RESPONSE_FIELDS


def test_theoretical_linear_notional_discrimination_factor_is_100() -> None:
    # THEORETICAL_DOCUMENTARY_ONLY / NOT_OKX_RUNTIME_PROOF
    mark_px = Decimal("63043.7")
    notional_a = theoretical_linear_notional_usd(sz="1", ct_val=CANDIDATE_A_CT_VAL, mark_px=mark_px)
    notional_b = theoretical_linear_notional_usd(sz="1", ct_val=CANDIDATE_B_CT_VAL, mark_px=mark_px)
    ratio = theoretical_candidate_notional_ratio(mark_px=mark_px)
    assert ratio == EXPECTED_DISCRIMINATION_FACTOR
    assert notional_b / notional_a == Decimal("100")
    assert DISCRIMINATION_CLASS == "THEORETICAL_DOCUMENTARY_ONLY"
    assert NOT_OKX_RUNTIME_PROOF is True


def test_unfilled_order_binding_does_not_unlock_submit_or_claim_rule_c() -> None:
    binding = unfilled_order_documentary_binding_v1()
    assert_no_submit_unlock_in_binding(binding)
    assert binding["SELECTED_PATH"] == SELECTED_PATH
    assert binding["ORDER_OBJECT_FIELD"] == ORDER_FIELD_NOTIONAL_USD
    assert binding["RULE_C_STATUS"] == RULE_C_STATUS == "UNPROVEN"
    assert binding["NOT_OKX_RUNTIME_PROOF"] is True
    assert binding["PRECHECK_CANNOT_CREATE_ORDER"] is True
    assert binding["ORDER_PRECHECK_APPLICABLE_FOR_LIVE_EEA_ACCT_LV_2"] is False
    assert SUBMIT_UNLOCKED is False
    assert LIVE_ARMED is False
