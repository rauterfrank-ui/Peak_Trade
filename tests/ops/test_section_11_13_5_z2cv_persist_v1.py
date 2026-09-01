"""§11.13.5.Z2CV COVER_USDC offline reproof persist invariants.

Docs/governance plus offline adjudication. No runtime. No venue GET.
"""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_cover_usdc_offline_reproof_v1 import (
    ADJUDICATION,
    BLOCKING_EVIDENCE_GAPS,
    CURRENT_COVER_USDC_STATUS,
    FORENSIC_SOURCE_COUNT,
    OWNER_GO as REPROOF_OWNER_GO,
    REPROOF_PROVEN,
    Z2AR_CLASS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2CU_HEADING = "### 11.13.5.Z2CU Post-Z2CT named progression-track adjudication persist"
Z2CV_HEADING = "### 11.13.5.Z2CV COVER_USDC remaining unranked SUI offline reproof persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2AR_COVER_USDC_REPROOF_OFFLINE_V1"
BASELINE_SHA = "c8616e87accf524eabfb98706b5b81d8746020c1"
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cv_section(text: str) -> str:
    start = text.find(Z2CV_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CV heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2CV"
    return text[start:end]


def _z2cu_section(text: str) -> str:
    start = text.find(Z2CU_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CU heading"
    end = text.find(Z2CV_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CV boundary after Z2CU"
    return text[start:end]


def test_z2cv_heading_is_unique_and_follows_z2cu() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CV_HEADING) == 1
    z2cu = text.find(Z2CU_HEADING)
    z2cv = text.find(Z2CV_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2cu < z2cv < ladder


def test_z2cu_historical_adjudication_slice_was_not_rewritten() -> None:
    section = _z2cu_section(_read(MASTER_RUNBOOK))
    assert "ADJUDICATION=MULTIPLE_OWNER_SELECTABLE_TRACKS" in section
    assert "RECOMMENDED_TRACK=P3_Z2AR_REMAINING_UNRANKED_SUI_REPROOF" in section
    assert (
        "REMAINING_UNRANKED_CLASSES=COVER_USDC;FX;ROUNDING;FINISHED_RISK_ENVELOPE_NUMERIC;USD_USDC_ACCOUNT_SETTLEMENT"
        in section
    )
    assert "GET_EXECUTED_THIS_PERSIST=false" in section
    assert "Z2CV" not in section


def test_z2cv_docs_bind_fail_closed_cover_usdc_without_get() -> None:
    section = _z2cv_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CV_Z2AR_COVER_USDC_OFFLINE_REPROOF_DOCS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "PREDECESSOR_SLICE=11.13.5.Z2CU",
        "LAST_CANONICALLY_CLOSED_11_13_5_SLICE=SECTION_11_13_5_Z2CT",
        "THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CT_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE=true",
        "THIS_NAMED_CLASS_PERSIST_ID=SECTION_11_13_5_Z2CV",
        "Z2AR_CLASS=COVER_USDC",
        "EXACT_Z2AR_CLASS=COVER_USDC",
        "ADJUDICATION=NOT_REPROVEN_MISSING_EVIDENCE",
        "CURRENT_COVER_USDC_STATUS=NOT_REPROVEN_MISSING_EVIDENCE",
        "REPROOF_PROVEN=false",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "COVER_USDC_INSTANTIATED=false",
        "CENSUS_COMPLETE=true",
        f"FORENSIC_SOURCE_COUNT={FORENSIC_SOURCE_COUNT}",
        "GET_EXECUTED_THIS_PERSIST=false",
        "GET_EXECUTED_UNDER_THIS_OWNER_GO=false",
        "AUTHENTICATED_GET_CALLS=0",
        "VENUE_API_CALLS=0",
        "POST_EXECUTED=false",
        "FLATTEN_EXECUTED=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "EXECUTION_READY=false",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
        f"CURRENT_CANONICAL_INSTRUMENT={CURRENT_SUI}",
        "SUI_REPROOF_CLASSES_RANKED=false",
        "NO_RANKING_OF_REMAINDER=true",
        "REMAINING_UNRANKED_AFTER_THIS_CLASS=FX;ROUNDING;FINISHED_RISK_ENVELOPE_NUMERIC;USD_USDC_ACCOUNT_SETTLEMENT",
        "COVER_NEGATIVE_CONTRACT_REMAINS_IN_FORCE=true",
        "Z2BX_COVER_NEGATIVE_CONTRACT_REMAINS_IN_FORCE=true",
        "Z2AJ_COVER_NEGATIVE_CONTRACT_REMAINS_IN_FORCE=true",
        "Z2J_REMAINS_CONTROLLING_FOR_CONVERSION_NUMERIC_STATUS=true",
        "IDXPX_1_IS_NOT_COVER_USDC_OPERATOR=true",
        "FORBIDDEN_UPGRADE_HISTORICAL_TO_PROVEN=true",
        "FORBIDDEN_UPGRADE_NAVIGATION_TO_PROVEN=true",
        "FORBIDDEN_COLLAPSE_COVER_USDC_WITH_USD_USDC=true",
        "FORBIDDEN_COLLAPSE_COVER_USDC_WITH_FX=true",
        "FORBIDDEN_COLLAPSE_COVER_USDC_WITH_RISK_ENVELOPE_NUMERIC=true",
        "INTERNAL_ENVELOPE_IS_NOT_COVER_USDC=true",
        "Z2CU_TEXT_REWRITTEN=false",
        "Z2BX_TEXT_REWRITTEN=false",
        "Z2AJ_TEXT_REWRITTEN=false",
        "Z2CT_TEXT_REWRITTEN=false",
    )
    for token in required:
        assert token in section, token


def test_z2cv_docs_forbid_activation_and_class_collapse() -> None:
    section = _z2cv_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nREPROOF_PROVEN=true\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nCOVER_USDC_INSTANTIATED=true\n",
        "\nADJUDICATION=REPROVEN\n",
        "\nCURRENT_COVER_USDC_STATUS=REPROVEN\n",
        "\nSUI_REPROOF_CLASSES_RANKED=true\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nIDXPX_1_IS_NOT_COVER_USDC_OPERATOR=false\n",
        "\nFX_ADJUDICATED_THIS_PERSIST=true\n",
        "\nROUNDING_ADJUDICATED_THIS_PERSIST=true\n",
        "\nUSD_USDC_ACCOUNT_SETTLEMENT_ADJUDICATED_THIS_PERSIST=true\n",
        "\nFINISHED_RISK_ENVELOPE_NUMERIC_ADJUDICATED_THIS_PERSIST=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_remains_navigation_only() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2CV" not in text
    assert "11.13.5.Z2CV" not in text


def test_python_adjudication_matches_persist() -> None:
    assert OWNER_GO == REPROOF_OWNER_GO
    assert Z2AR_CLASS == "COVER_USDC"
    assert ADJUDICATION == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert CURRENT_COVER_USDC_STATUS == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert REPROOF_PROVEN is False
    assert FORENSIC_SOURCE_COUNT >= 20
    assert "USD_USDC_OPERATOR_STATUS=UNPROVEN" in BLOCKING_EVIDENCE_GAPS


def test_safety_non_regression_standing_flags_and_forbidden_go() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert "CATEGORY_C" not in GATE_NAMES
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
