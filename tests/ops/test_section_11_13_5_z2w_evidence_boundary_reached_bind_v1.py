"""§11.13.5.Z2W Evidence Boundary Reached bind.

Docs/governance invariants only. Distinguishes the completed
NO_SUBMIT + NO_POSITION + NO_FUNDING path adjudication from Rule-C
proof, Face-Value resolution, COVER_USDC instantiation, and any new
runtime state class. Does not authorize Live, Testnet, orders,
funding, conversion, transfer, Canary execute, support contact, or a
productive HTTP GET.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2W_HEADING = "### 11.13.5.Z2W Evidence boundary reached bind"
Z2V_HEADING = (
    "### 11.13.5.Z2V Independent account-runtime IM &#47; notionalUsd &#47; UPL probe bind"
)
Z2X_HEADING = "### 11.13.5.Z2X Unfilled-order state class does not produce independent account IM"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_NEW_RUNTIME_STATE_CLASS_ORDER_DERIVED_OR_"
    "POSITION_DERIVED_IM_NOTIONALUSD_OR_UPL_EVIDENCE_BOUNDARY_REACHED_NO_"
    "CANONICAL_NO_SUBMIT_NO_POSITION_NO_FUNDING_DISCRIMINATOR_REMAINS_RULE_C_"
    "UNPROVEN_FACE_VALUE_CONFLICT_UNRESOLVED_COVER_USDC_UNINSTANTIATED_REPEAT_"
    "ZERO_EQUITY_NO_POSITION_GETS_HAVE_NO_DISCRIMINATORY_VALUE_SUPPORT_CONTACT_"
    "NOT_AUTHORIZED_CANARY_NOT_AUTHORIZED"
)
OWNER_GO = "OWNER_GO_Z2V_PLUS_PR_5979_EVIDENCE_BOUNDARY_REACHED_BIND_DOCS_EVIDENCE_ONLY"
BASELINE_SHA = "6958af1d017f3941108d7c7245662d97c2bbc3ec"
NEGATIVE_PATHS = (
    "Z2V_ZERO_EQUITY_NO_POSITION_GETS,"
    "SECTION_S_MAX_AVAIL_SIZE_AND_ORDERS_PENDING_EMPTY,"
    "EXISTORD_FALSE,"
    "ORDFROZ_EMPTY,"
    "THEORETICAL_IM_NOT_ACCOUNT_IM,"
    "PUBLIC_CTVAL_METADATA_NOT_RULE_C,"
    "OEM_0.01_NOT_RULE_C,"
    "ORDER_PRECHECK_N_A_AT_ACCT_LV_2,"
    "REPEAT_ZERO_EQUITY_GET_NON_DISCRIMINATING"
)
CANDIDATE_PATHS = (
    "P01_BALANCE,P02_POSITIONS,P03_ACCOUNT_POSITION_RISK,P04_POSITIONS_HISTORY,"
    "P05_ADJUST_LEVERAGE_INFO,P06_MAX_SIZE,P07_MAX_AVAIL_SIZE,P08_ORDERS_PENDING,"
    "P09_ACCOUNT_CONFIG,P10_LEVERAGE_INFO,P11_ACCOUNT_AND_PUBLIC_INSTRUMENTS,"
    "P12_TRADE_FEE_AND_PUBLIC_MARK_TICKER_TIERS,P13_PR5979_THEORETICAL_LINEAR_NOTIONAL,"
    "P14_ORDER_PRECHECK,P15_UI_ESTIMATE"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2w_section(text: str) -> str:
    start = text.find(Z2W_HEADING)
    assert start >= 0, "missing §11.13.5.Z2W heading"
    end = text.find(Z2X_HEADING, start)
    assert end > start, "missing §11.13.5.Z2X boundary after Z2W"
    return text[start:end]


def test_z2w_heading_is_unique_and_follows_z2v() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2W_HEADING) == 1
    z2v = text.find(Z2V_HEADING)
    z2w = text.find(Z2W_HEADING)
    z2x = text.find(Z2X_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2v < z2w < z2x < ladder


def test_z2w_docs_bind_evidence_boundary_without_proving_rule_c() -> None:
    section = _z2w_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=Z2V_PLUS_PR_5979_PATH_ADJUDICATION_EVIDENCE_BOUNDARY_REACHED_BIND_DOCS_EVIDENCE_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EVIDENCE_BOUNDARY_REACHED=true",
        "EVIDENCE_BOUNDARY_MEANS_RULE_C_PROVEN=false",
        "EVIDENCE_BOUNDARY_MEANS_FACE_VALUE_CLOSED=false",
        "EVIDENCE_BOUNDARY_MEANS_COVER_USDC_INSTANTIATED=false",
        "DOES_ANY_CANONICAL_NO_SUBMIT_NO_POSITION_NO_FUNDING_DISCRIMINATOR_REMAIN=false",
        "RECOMMENDED_BRANCH=EVIDENCE_BOUNDARY_REACHED",
        "RUNTIME_PROOF_OBTAINED=false",
        "RULE_C_STATUS=UNPROVEN",
        "RULE_C_INDEPENDENT_RUNTIME_IM_SATISFIED=false",
        "FACE_VALUE_CONFLICT_STATUS=UNRESOLVED",
        "FACE_VALUE_CONFLICT_CLOSED=false",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "COVER_USDC_INSTANTIATED=false",
        "ACCOUNT_LEVEL_VALUE=2",
        "ORDER_PRECHECK_ACCOUNT_LEVEL_2_STATUS=NOT_APPLICABLE",
        "ORDER_PRECHECK_APPLICABLE_FOR_LIVE_EEA_ACCT_LV_2=false",
        "PR_5979_DISCRIMINATION_CLASS=THEORETICAL_DOCUMENTARY_ONLY",
        "PR_5979_NOT_OKX_RUNTIME_PROOF=true",
        "PR_5979_CREATED_NEW_Z_SECTION=false",
        "CANDIDATE_A=0.0001_BTC",
        "CANDIDATE_A_CLASS=API_GUIDE_METADATA_CLUSTER",
        "CANDIDATE_B=0.01_BTC",
        "CANDIDATE_B_CLASS=OEM_SPEC_CLUSTER",
        "CONFLICT_FACTOR=100",
        "MINIMAL_NEW_STATE_CLASS_IF_REQUIRED=ORDER_DERIVED_OR_POSITION_DERIVED_IM_NOTIONALUSD_OR_UPL",
        "NEW_RUNTIME_STATE_CLASS_AUTHORIZED=false",
        "REPEAT_ZERO_EQUITY_NO_POSITION_GET_DISCRIMINATORY_VALUE=false",
        "SUPPORT_CONTACT_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "RUNTIME_EXECUTION_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "GET_EXECUTED_THIS_PERSIST_STEP=false",
        "OKX_API_CALL_PERFORMED=false",
        "NO_CAPABILITY_ADVANCEMENT=true",
        "NEXT_OWNER_AUTHORIZATION_REQUIRED=true",
        f"CANONICAL_CANDIDATE_PATHS_REVIEWED={CANDIDATE_PATHS}",
        f"CANONICAL_NEGATIVE_PATHS_CONFIRMED={NEGATIVE_PATHS}",
        "22G_EVIDENCE_BOUNDARY_REACHED_NO_CANONICAL_NO_SUBMIT_NO_POSITION_NO_FUNDING_DISCRIMINATOR_REMAINS_RULE_C_UNPROVEN",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "NO_FUNDING",
        "NO_ORDER",
        "NO_CANARY",
        "NO_EXECUTE",
        "NO_ARTIFICIAL_RULE_C_CLOSE=true",
        "NO_REPEAT_ZERO_EQUITY_NO_POSITION_GET=true",
        "NO_CTMULT_1_AS_HIDDEN_FACTOR_100=true",
        "NO_ALGEBRAIC_CONSISTENCY_AS_RUNTIME_PROOF=true",
        "NO_PROMOTE_PR_5979_THEORETICAL_LINEAR_NOTIONAL_TO_RULE_C=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2W marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nOPERATIVE_CONTRACT_VALUE_PROVEN=true\n",
        "\nRULE_C_STATUS=PROVEN\n",
        "\nRULE_C_INDEPENDENT_RUNTIME_IM_SATISFIED=true\n",
        "\nFACE_VALUE_CONFLICT_STATUS=RESOLVED\n",
        "\nFACE_VALUE_CONFLICT_CLOSED=true\n",
        "\nCOVER_USDC_INSTANTIATED=true\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nRUNTIME_PROOF_OBTAINED=true\n",
        "\nRUNTIME_EXECUTION_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nCANARY_EXECUTE_AUTHORIZED=true\n",
        "\nNEW_RUNTIME_STATE_CLASS_AUTHORIZED=true\n",
        "\nORDER_PRECHECK_ACCOUNT_LEVEL_2_STATUS=APPLICABLE\n",
        "\nDOES_ANY_CANONICAL_NO_SUBMIT_NO_POSITION_NO_FUNDING_DISCRIMINATOR_REMAIN=true\n",
        "\nOKX_API_CALL_PERFORMED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST_STEP=true\n",
        "\nORDER_SUBMITTED=true\n",
        "\nNO_USD_EQUALS_USDC=false\n",
        "\nNO_CAPABILITY_ADVANCEMENT=false\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2W marker present: {marker!r}"


def test_z2w_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "§11.13.5.Z2W |" in mot
    assert "historical next pointer superseded by §11.13.5.Z2W" in mot
    assert "historical next pointer superseded by §11.13.5.Z2X" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}\n" not in mot
    assert (
        "NEXT_CANONICAL_STEP_POINTER=OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEW_RUNTIME_STATE_"
        "SUCH_AS_POSITION_OR_ORDER_DERIVED_IM_NOTIONALUSD_OR_UPL_REPEAT_ZERO_EQUITY_NO_"
        "POSITION_GET_HAS_NO_DISCRIMINATORY_VALUE_FACE_VALUE_AND_COVER_USDC_REMAIN_"
        "UNRESOLVED_SUPPORT_CONTACT_NOT_AUTHORIZED_CANARY_NOT_AUTHORIZED\n" not in mot
    )
