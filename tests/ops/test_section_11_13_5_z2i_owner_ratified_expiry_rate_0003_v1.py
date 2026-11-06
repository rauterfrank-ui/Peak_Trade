"""§11.13.5.Z2I owner-ratified operative expiry-settlement rate.

Code contract plus docs/governance invariants. Distinguishes verified
first-party OKX API provenance from Owner semantic adjudication. Does
not authorize Live, Testnet, orders, funding, scaling, or Multi-Future.
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
    ACTUAL_EXPIRY_FEE_AMOUNT_STATUS,
    API_DELIVERY_0_0003_STATUS,
    CANONICAL_EXPIRY_SETTLEMENT_RATE,
    CANONICAL_RATE_PROVENANCE,
    DELIVERY_RATE_ARTIFACT_VERIFIED,
    DELIVERY_RATE_ENDPOINT,
    DELIVERY_RATE_FIELD,
    DELIVERY_RATE_OWNER_GENERATED,
    DELIVERY_RATE_PEAK_TRADE_GENERATED,
    DELIVERY_RATE_SOURCE,
    DELIVERY_RATE_VALUE,
    DELIVERY_RATE_VALUE_PROVENANCE,
    EXPIRY_RATE_BLOCKER,
    EXPIRY_RATE_GATE,
    EXPIRY_SETTLEMENT_RATE,
    EXPIRY_SETTLEMENT_RATE_ADJUDICATION,
    EXPIRY_SETTLEMENT_RATE_PERCENT,
    EXPIRY_SETTLEMENT_RATE_VALUE_PROVENANCE,
    OEM_FEE_MONETARY_BASE_STATUS,
    OEM_OKX_MONETARY_BASE_IDENTITY_STATUS,
    OPERATIVE_EXPIRY_FEE_RATE,
    OPERATIVE_EXPIRY_SETTLEMENT_RATE,
    PEAK_TRADE_EXPIRY_RESERVE_RATE,
    PEAK_TRADE_EXPIRY_RESERVE_RATE_HISTORICAL_SOURCE,
    PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH,
    PEAK_TRADE_EXPIRY_RESERVE_RATE_SOURCE,
    PEAK_TRADE_INTERNAL_NOTIONAL_UNIT,
    PR_5960_SEMANTICS_STATUS,
    RATE_ADJUDICATION_CLOSED,
    SINGLE_CURRENT_RATE_TRUTH,
    SUPPORT_RATE_0_0001_CAN_BLOCK_CURRENT_RATE,
    SUPPORT_RATE_0_0001_STATUS,
    SUPPORT_REQUIRED_FOR_RATE_DECISION,
    SUPPORT_TICKET_7823581_STATUS,
    assert_canonical_expiry_settlement_rate_v1,
    evaluate_internal_expiry_fee_economic_uncertainty_bound_v1,
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
W_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_v_fresh_xperp_trade_fee_get_evidence_v1"
    / "20260816T075803Z"
)

Z2I_HEADING = (
    "### 11.13.5.Z2I Owner-ratified operative expiry-settlement rate from "
    "verified first-party OKX `delivery`"
)
Z2I_HIST_HEADING = (
    "### 11.13.5.Z2I-HIST Delivery 0.0003 versus expiry-settlement 0.0001 provenance adjudication"
)
Z2I_OWNER_GO = "OWNER_POLICY_OVERRIDE_GO"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_"
    "COVER_USDC_TERMS_AFTER_CURRENT_TICKER_BID_ASK_BEFORE_FUNDING"
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


def _z2i_section(text: str) -> str:
    start = text.find(Z2I_HEADING)
    assert start >= 0, "missing §11.13.5.Z2I heading"
    end = text.find("### 11.13.5.Z2J ", start)
    if end < 0:
        end = text.find("## 11.14 Live order and economic evidence ladder", start)
    assert end > start, "missing §11.13.5.Z2J or §11.14 boundary after Z2I"
    return text[start:end]


def _z2i_hist_section(text: str) -> str:
    start = text.find(Z2I_HIST_HEADING)
    assert start >= 0, "missing §11.13.5.Z2I-HIST heading"
    end = text.find(Z2I_HEADING, start)
    assert end > start, "missing current §11.13.5.Z2I after Z2I-HIST"
    return text[start:end]


def _bound(**overrides: str):
    kwargs = dict(_BOUND_KWARGS)
    kwargs.update(overrides)
    return evaluate_internal_expiry_fee_economic_uncertainty_bound_v1(**kwargs)


def test_verified_api_provenance_is_not_peak_trade_or_owner_generated() -> None:
    assert DELIVERY_RATE_VALUE == Decimal("0.0003")
    assert DELIVERY_RATE_VALUE_PROVENANCE == "VERIFIED_FIRST_PARTY_OKX_API_ARTIFACT"
    assert DELIVERY_RATE_SOURCE == "OKX_EEA_PRODUCTION_API"
    assert DELIVERY_RATE_ENDPOINT == "/api/v5/account/trade-fee"
    assert DELIVERY_RATE_FIELD == "delivery"
    assert DELIVERY_RATE_ARTIFACT_VERIFIED is True
    assert DELIVERY_RATE_PEAK_TRADE_GENERATED is False
    assert DELIVERY_RATE_OWNER_GENERATED is False
    assert CANONICAL_RATE_PROVENANCE == "VERIFIED_FIRST_PARTY_OKX_API_ARTIFACT"
    snapshot = _read(W_PACK / "GET_SNAPSHOT.sanitized.json")
    assert '"delivery": "0.0003"' in snapshot


def test_owner_adjudication_is_semantic_not_value_generation() -> None:
    assert EXPIRY_SETTLEMENT_RATE == Decimal("0.0003") == CANONICAL_EXPIRY_SETTLEMENT_RATE
    assert EXPIRY_SETTLEMENT_RATE_PERCENT == "0.03%"
    assert EXPIRY_SETTLEMENT_RATE_VALUE_PROVENANCE == "VERIFIED_FIRST_PARTY_OKX_API_ARTIFACT"
    assert EXPIRY_SETTLEMENT_RATE_ADJUDICATION == (
        "OWNER_RATIFIED_FROM_VERIFIED_FIRST_PARTY_OKX_DELIVERY_FIELD"
    )
    assert OPERATIVE_EXPIRY_SETTLEMENT_RATE == Decimal("0.0003")
    assert OPERATIVE_EXPIRY_FEE_RATE == "0.0003"
    assert OPERATIVE_EXPIRY_FEE_RATE != "NONE"
    assert OPERATIVE_EXPIRY_FEE_RATE != "0.0001"
    assert SINGLE_CURRENT_RATE_TRUTH is True
    assert PR_5960_SEMANTICS_STATUS == "HISTORICAL_SUPERSEDED"
    assert API_DELIVERY_0_0003_STATUS == (
        "VERIFIED_FIRST_PARTY_VALUE_OWNER_RATIFIED_OPERATIVE_ADJUDICATION"
    )
    assert RATE_ADJUDICATION_CLOSED is True
    assert_canonical_expiry_settlement_rate_v1()


def test_historical_support_rate_cannot_block_or_overwrite() -> None:
    assert SUPPORT_RATE_0_0001_STATUS == "HISTORICAL_SUPERSEDED"
    assert SUPPORT_TICKET_7823581_STATUS == "HISTORICAL_SUPERSEDED_FOR_RATE_ADJUDICATION"
    assert SUPPORT_RATE_0_0001_CAN_BLOCK_CURRENT_RATE is False
    assert SUPPORT_REQUIRED_FOR_RATE_DECISION is False
    assert EXPIRY_RATE_GATE == "PASS"
    assert EXPIRY_RATE_BLOCKER is False


def test_reserve_reuses_same_numeric_without_rewriting_api_provenance() -> None:
    assert PEAK_TRADE_EXPIRY_RESERVE_RATE == Decimal("0.0003") == EXPIRY_SETTLEMENT_RATE
    assert PEAK_TRADE_EXPIRY_RESERVE_RATE_SOURCE == (
        "PEAK_TRADE_POLICY_REUSE_OF_SAME_NUMERIC_VALUE"
    )
    assert PEAK_TRADE_EXPIRY_RESERVE_RATE_HISTORICAL_SOURCE == "CONSERVATIVE_INTERNAL_POLICY"
    assert PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH is False
    assert DELIVERY_RATE_VALUE_PROVENANCE != "CONSERVATIVE_INTERNAL_POLICY"
    assert DELIVERY_RATE_PEAK_TRADE_GENERATED is False


def test_qty_one_bound_uses_decimal_verified_rate_and_existing_envelope() -> None:
    first = _bound()
    second = _bound()
    expected_envelope = Decimal("1") * Decimal("0.0001") * Decimal("63043.7")
    expected_bound = Decimal("0.0003") * expected_envelope
    assert first.absolute_economic_uncertainty_bound == format(expected_bound, "f")
    assert first.reserve_rate == "0.0003"
    assert first.operative_expiry_fee_rate == "0.0003"
    assert first.oem_fee_monetary_base_status == "BOUND_PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE"
    assert OEM_FEE_MONETARY_BASE_STATUS == "BOUND_PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE"
    assert OEM_OKX_MONETARY_BASE_IDENTITY_STATUS == "UNPROVEN"
    assert first.actual_expiry_fee_amount_status == ACTUAL_EXPIRY_FEE_AMOUNT_STATUS
    assert first.bound_unit == PEAK_TRADE_INTERNAL_NOTIONAL_UNIT
    assert first.to_dict() == second.to_dict()
    assert "." in first.absolute_economic_uncertainty_bound
    assert isinstance(EXPIRY_SETTLEMENT_RATE, Decimal)
    assert not isinstance(EXPIRY_SETTLEMENT_RATE, float)


def test_z2i_go_does_not_authorize_live_order_or_funding() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert Z2I_OWNER_GO in NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT
    evaluation = evaluate_canary_submit_gates_v1(
        owner_go=Z2I_OWNER_GO,
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


def test_pr_5960_persist_is_historical_superseded_not_current_z2i() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2I_HEADING) == 1
    assert text.count(Z2I_HIST_HEADING) == 1
    hist = _z2i_hist_section(text)
    current = _z2i_section(text)
    assert "PERSIST_STATUS=HISTORICAL_SUPERSEDED" in hist
    assert "PR_5960_SEMANTICS_STATUS=HISTORICAL_SUPERSEDED" in hist
    assert "CURRENT_NORMATIVE_AUTHORITY=false" in hist
    assert "OPERATIVE_EXPIRY_SETTLEMENT_RATE=NONE" in hist
    assert "EXPIRY_SETTLEMENT_RATE_NORMATIVE=0.0001" in hist
    assert "SINGLE_CURRENT_RATE_TRUTH=true" not in hist
    assert "OPERATIVE_EXPIRY_SETTLEMENT_RATE=0.0003" in current
    assert "\nOPERATIVE_EXPIRY_SETTLEMENT_RATE=NONE\n" not in current
    assert "SINGLE_CURRENT_RATE_TRUTH=true" in current


def test_z2i_docs_bind_provenance_and_adjudication_without_rewriting_evidence() -> None:
    section = _z2i_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=OWNER_RATIFIED_EXPIRY_SETTLEMENT_RATE_ADJUDICATION_FROM_VERIFIED_API_DELIVERY",
        "PARALLEL_TO_SECTION_11_13_5_Z2H=true",
        "Z2H_CANONICAL_POINTER_REPLACED=false",
        "DELIVERY_RATE_VALUE=0.0003",
        "DELIVERY_RATE_VALUE_PROVENANCE=VERIFIED_FIRST_PARTY_OKX_API_ARTIFACT",
        "DELIVERY_RATE_SOURCE=OKX_EEA_PRODUCTION_API",
        "DELIVERY_RATE_ENDPOINT=/api/v5/account/trade-fee",
        "DELIVERY_RATE_FIELD=delivery",
        "DELIVERY_RATE_ARTIFACT_VERIFIED=true",
        "DELIVERY_RATE_PEAK_TRADE_GENERATED=false",
        "DELIVERY_RATE_OWNER_GENERATED=false",
        "EXPIRY_SETTLEMENT_RATE=0.0003",
        "EXPIRY_SETTLEMENT_RATE_PERCENT=0.03%",
        "OPERATIVE_EXPIRY_SETTLEMENT_RATE=0.0003",
        "SINGLE_CURRENT_RATE_TRUTH=true",
        "PR_5960_SEMANTICS_STATUS=HISTORICAL_SUPERSEDED",
        "EXPIRY_SETTLEMENT_RATE_VALUE_PROVENANCE=VERIFIED_FIRST_PARTY_OKX_API_ARTIFACT",
        "EXPIRY_SETTLEMENT_RATE_ADJUDICATION=OWNER_RATIFIED_FROM_VERIFIED_FIRST_PARTY_OKX_DELIVERY_FIELD",
        "OPERATIVE_EXPIRY_FEE_RATE=0.0003",
        "EXPIRY_RATE_GATE=PASS",
        "EXPIRY_RATE_BLOCKER=false",
        "SUPPORT_REQUIRED_FOR_RATE_DECISION=false",
        "SUPPORT_RATE_0_0001_STATUS=HISTORICAL_SUPERSEDED",
        "SUPPORT_TICKET_7823581_STATUS=HISTORICAL_SUPERSEDED_FOR_RATE_ADJUDICATION",
        "SUPPORT_RATE_0_0001_CAN_BLOCK_CURRENT_RATE=false",
        "PEAK_TRADE_EXPIRY_RESERVE_RATE=0.0003",
        "PEAK_TRADE_EXPIRY_RESERVE_RATE_SOURCE=PEAK_TRADE_POLICY_REUSE_OF_SAME_NUMERIC_VALUE",
        "PEAK_TRADE_EXPIRY_RESERVE_RATE_HISTORICAL_SOURCE=CONSERVATIVE_INTERNAL_POLICY",
        "PEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH=false",
        "ACTIVE_EXPIRY_RATE_VALUES=0.0003",
        "NO_FALLBACK_SELECTION_BETWEEN_0001_AND_0003=true",
        "NO_0_0001_PROMOTION_TO_OPERATIVE_COMPUTATION=true",
        "NO_INVENTED_OKX_SUPPORT_SEMANTIC_CONFIRMATION=true",
        "OEM_OKX_MONETARY_BASE_IDENTITY_STATUS=UNPROVEN",
        "RATE_CANNOT_BE_RESET_TO_NONE_BY_MONETARY_BASE_QUESTION=true",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        f"OWNER_GO={Z2I_OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "NO_FUNDING=true",
        "NO_EXECUTE=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2I marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nOPERATIVE_EXPIRY_FEE_RATE=NONE\n",
        "\nOPERATIVE_EXPIRY_FEE_RATE=0.0001\n",
        "\nEXPIRY_RATE_GATE=FAIL\n",
        "\nEXPIRY_RATE_BLOCKER=true\n",
        "\nSUPPORT_REQUIRED_FOR_RATE_DECISION=true\n",
        "\nDELIVERY_RATE_PEAK_TRADE_GENERATED=true\n",
        "\nDELIVERY_RATE_OWNER_GENERATED=true\n",
        "\nPEAK_TRADE_EXPIRY_RESERVE_RATE_IS_OKX_FEE_TRUTH=true\n",
        "\nCOVER_USDC_STATUS=PROVEN\n",
        "CANONICAL_RATE_SOURCE=OWNER_POLICY",
        "0.0003 is an internal assumption",
        "0.0003 is Peak_Trade-generated",
    )
    for assignment in forbidden:
        assert assignment not in section, f"forbidden assignment present: {assignment!r}"


def test_map_of_truth_and_spec_record_z2i_rate_without_replacing_z2h() -> None:
    mot = _read(MAP_OF_TRUTH)
    spec = _read(CANARY_SPEC)
    assert "§11.13.5.Z2I" in mot
    assert "OWNER_POLICY_OVERRIDE_GO_STATUS=CONSUMED_RATE_ADJUDICATION_NOT_EXECUTE" in mot
    assert "OPERATIVE_EXPIRY_FEE_RATE=0.0003" in mot
    assert "EXPIRY_SETTLEMENT_RATE_VALUE_PROVENANCE=VERIFIED_FIRST_PARTY_OKX_API_ARTIFACT" in mot
    assert "EXPIRY_RATE_GATE=PASS" in mot
    assert "SUPPORT_RATE_0_0001_STATUS=HISTORICAL_SUPERSEDED" in mot
    assert "SINGLE_CURRENT_RATE_TRUTH=true" in mot
    assert "OPERATIVE_EXPIRY_SETTLEMENT_RATE=0.0003" in mot
    assert "§11.13.5.Z2I-HIST" in mot
    assert "PR_5960_SEMANTICS_STATUS=HISTORICAL_SUPERSEDED" in mot
    assert f"{NEXT_POINTER}_STATUS=CONSUMED_GET_ONLY_PUBLIC_TIER_MMR_OBSERVED_NOT_COVER_USDC" in mot
    assert "Current SSOT: Master Runbook §11.13.5.Z2K." in spec
    assert "Current SSOT: Master Runbook §11.13.5.Z2H." not in spec
    assert "Current SSOT: Master Runbook §11.13.5.Z2I." not in spec
    assert Z2I_OWNER_GO in spec
    assert "VERIFIED_FIRST_PARTY_OKX_API_ARTIFACT" in spec


def test_sealed_w_pack_is_unchanged_first_party_artifact() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
        verify_manifest_v1,
    )

    verify = verify_manifest_v1(W_PACK)
    assert verify["MANIFEST_VERIFY_RC"] == 0
    snapshot = _read(W_PACK / "GET_SNAPSHOT.sanitized.json")
    assert '"delivery": "0.0003"' in snapshot
    assert W_PACK.is_dir()
