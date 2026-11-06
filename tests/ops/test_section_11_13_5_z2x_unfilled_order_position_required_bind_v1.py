"""§11.13.5.Z2X unfilled-order state class does not produce Rule-C IM.

Docs/governance invariants only. Adjudicates that at live EEA acctLv=2
(Futures mode) independent account-runtime IM / notionalUsd / UPL is
position-derived. Does not submit orders, call OKX, fund, open a
position, unlock Canary, or prove Rule C / Face Value / COVER_USDC.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2X_HEADING = "### 11.13.5.Z2X Unfilled-order state class does not produce independent account IM"
Z2W_HEADING = "### 11.13.5.Z2W Evidence boundary reached bind"
Z2Y_HEADING = "### 11.13.5.Z2Y Filled-position-derived probe is not presently authorizable"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_POSITION_DERIVED_IM_NOTIONALUSD_OR_UPL_"
    "UNFILLED_ORDER_DOES_NOT_PRODUCE_INDEPENDENT_ACCOUNT_RUNTIME_DISCRIMINATOR_"
    "AT_ACCT_LV_2_RULE_C_UNPROVEN_FACE_VALUE_CONFLICT_UNRESOLVED_COVER_USDC_"
    "UNINSTANTIATED_FUNDING_NOT_AUTHORIZED_PARTIAL_FILL_NOT_AUTHORIZED_"
    "SUPPORT_CONTACT_NOT_AUTHORIZED_CANARY_NOT_AUTHORIZED"
)
OWNER_GO = "OWNER_GO_Z2W_ORDER_DERIVED_OR_POSITION_DERIVED_STATE_CLASS_FAIL_CLOSED_ADJUDICATION"
BASELINE_SHA = "ac4e9d2cf6925f2ed0b8dc8edeb7e4240643f697"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2x_section(text: str) -> str:
    start = text.find(Z2X_HEADING)
    assert start >= 0, "missing §11.13.5.Z2X heading"
    end = text.find(Z2Y_HEADING, start)
    assert end > start, "missing §11.13.5.Z2Y boundary after Z2X"
    return text[start:end]


def test_z2x_heading_is_unique_and_follows_z2w() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2X_HEADING) == 1
    z2w = text.find(Z2W_HEADING)
    z2x = text.find(Z2X_HEADING)
    z2y = text.find(Z2Y_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2w < z2x < z2y < ladder


def test_z2x_docs_bind_adjudication_b_without_submit_or_rule_c() -> None:
    section = _z2x_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=Z2W_ORDER_DERIVED_OR_POSITION_DERIVED_STATE_CLASS_FAIL_CLOSED_ADJUDICATION_DOCS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "ADJUDICATION=B",
        "ADJUDICATION_CLASS=UNFILLED_ORDER_DOES_NOT_PRODUCE_DISCRIMINATOR_POSITION_REQUIRED",
        "RESULT=POSITION_DERIVED_EVIDENCE_REQUIRED",
        "MINIMAL_DISCRIMINATING_STATE_CLASS=FILLED_POSITION_DERIVED",
        "UNFILLED_ORDER_DISCRIMINATOR_THEORETICALLY_AVAILABLE=false",
        "UNFILLED_ORDER_SAFE_PROBE_PROVEN=false",
        "PRODUCTIVE_ORDER_SUBMIT_PERFORMED=false",
        "ORDER_COUNT_SUBMITTED=0",
        "ORDER_FILLED=false",
        "PARTIAL_FILL_OCCURRED=false",
        "POSITION_CREATED=false",
        "PARTIAL_FILL_AUTHORIZED=false",
        "POSITION_OPENING_AUTHORIZED=false",
        "UNFILLED_ORDER_PRODUCES_INDEPENDENT_ACCOUNT_RUNTIME_DISCRIMINATOR=false",
        "UNFILLED_ORDER_DOES_NOT_PRODUCE_DISCRIMINATOR_POSITION_REQUIRED=true",
        "CLASS_1_ORDER_OBJECT_NOTIONALUSD=ESTIMATED_NOTIONAL_VALUE_IN_USD_OF_ORDER",
        "CLASS_1_ORDER_OBJECT_NOTIONALUSD_IS_RULE_C=false",
        "CLASS_1_DETAILS_IMR=APPLICABLE_ONLY_WHEN_CROSS_POSITION_EXISTS",
        "CLASS_1_UPL=REQUIRES_POSITION",
        "CLASS_3_AUTHORIZED=false",
        "QTY_ONE_VENUE_ADMISSIBLE=false",
        "TOTAL_EQ=0",
        "SUBMIT_UNLOCKED=false",
        "NO_PROMOTE_ORDER_NOTIONALUSD_ESTIMATE_TO_RULE_C=true",
        "NO_PROMOTE_DETAILS_ORDFROZEN_TO_RULE_C=true",
        "RULE_C_STATUS=UNPROVEN",
        "RULE_C_INDEPENDENT_RUNTIME_IM_SATISFIED=false",
        "FACE_VALUE_CONFLICT_STATUS=UNRESOLVED",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "RUNTIME_EVIDENCE_OBTAINED=false",
        "ACCOUNT_RUNTIME_FIELD_OBSERVED=NONE",
        "OKX_API_CALL_PERFORMED=false",
        "GET_EXECUTED_THIS_PERSIST_STEP=false",
        "ORDER_SUBMITTED=false",
        "CANARY_AUTHORIZED=false",
        "RUNTIME_EXECUTION_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        "SUPPORT_CONTACT_AUTHORIZED=false",
        "NO_CAPABILITY_ADVANCEMENT=true",
        "NEXT_OWNER_AUTHORIZATION_REQUIRED=true",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "NO_FUNDING",
        "NO_ORDER",
        "NO_CANARY",
        "NO_EXECUTE",
    )
    for marker in required:
        assert marker in section, f"missing Z2X marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nRULE_C_STATUS=PROVEN\n",
        "\nFACE_VALUE_CONFLICT_STATUS=RESOLVED\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nPRODUCTIVE_ORDER_SUBMIT_PERFORMED=true\n",
        "\nORDER_SUBMITTED=true\n",
        "\nPOSITION_CREATED=true\n",
        "\nPOSITION_OPENING_AUTHORIZED=true\n",
        "\nPARTIAL_FILL_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nRUNTIME_EXECUTION_AUTHORIZED=true\n",
        "\nOKX_API_CALL_PERFORMED=true\n",
        "\nUNFILLED_ORDER_DISCRIMINATOR_THEORETICALLY_AVAILABLE=true\n",
        "\nADJUDICATION=A\n",
        "\nADJUDICATION=C\n",
        "\nADJUDICATION=D\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2X marker present: {marker!r}"


def test_z2x_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "§11.13.5.Z2X |" in mot
    assert "historical next pointer superseded by §11.13.5.Z2X" in mot
    assert "historical next pointer superseded by §11.13.5.Z2Y" in mot
    assert "ADJUDICATION=B" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}\n" not in mot
    assert (
        "NEXT_CANONICAL_STEP_POINTER=OWNER_GO_REQUIRED_SEPARATE_FOR_NEW_RUNTIME_STATE_CLASS_"
        "ORDER_DERIVED_OR_POSITION_DERIVED_IM_NOTIONALUSD_OR_UPL_EVIDENCE_BOUNDARY_REACHED_"
        "NO_CANONICAL_NO_SUBMIT_NO_POSITION_NO_FUNDING_DISCRIMINATOR_REMAINS_RULE_C_UNPROVEN_"
        "FACE_VALUE_CONFLICT_UNRESOLVED_COVER_USDC_UNINSTANTIATED_REPEAT_ZERO_EQUITY_NO_"
        "POSITION_GETS_HAVE_NO_DISCRIMINATORY_VALUE_SUPPORT_CONTACT_NOT_AUTHORIZED_CANARY_"
        "NOT_AUTHORIZED\n" not in mot
    )
