"""§11.13.5.Z2CY persist invariants. Docs/governance plus offline census. No runtime."""

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.post_z2cx_p3_dependency_reconciliation_v1 import (
    ADJUDICATION,
    BLOCKER_CLASS,
    NEXT_ACTIONABLE_BLOCKER,
    OPEN_DEPENDENCY_COUNT,
    OWNER_GO as ADJUDICATION_OWNER_GO,
    UNIQUE_CANONICAL_NEXT_TRACK,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2CX_HEADING = "### 11.13.5.Z2CX remaining unranked SUI offline reproof bundle persist"
Z2CY_HEADING = "### 11.13.5.Z2CY Post-Z2CX P3 dependency reconciliation and next-blocker persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_POST_Z2CX_P3_DEPENDENCY_RECONCILIATION_AND_NEXT_BLOCKER_V1"
BASELINE_SHA = "00910a2f67f94ad3ebc84b48d441648cc04b1ea1"
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cy_section(text: str) -> str:
    start = text.find(Z2CY_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CY heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2CY"
    return text[start:end]


def _z2cx_section(text: str) -> str:
    start = text.find(Z2CX_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CX heading"
    end = text.find(Z2CY_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CY boundary after Z2CX"
    return text[start:end]


def test_z2cy_heading_is_unique_and_follows_z2cx() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CY_HEADING) == 1
    z2cx = text.find(Z2CX_HEADING)
    z2cy = text.find(Z2CY_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2cx < z2cy < ladder


def test_z2cx_historical_bundle_slice_was_not_rewritten() -> None:
    section = _z2cx_section(_read(MASTER_RUNBOOK))
    assert "ROUNDING_STATUS=NOT_REPROVEN_MISSING_EVIDENCE" in section
    assert "FX_STATUS=NOT_REPROVEN_MISSING_EVIDENCE" in section
    assert "FX_REOPENED=false" in section
    assert "COVER_USDC_ADJUDICATED=false" in section
    assert "REMAINING_UNRANKED_AFTER_THIS_BUNDLE=NONE" in section
    assert "GET_EXECUTED_THIS_PERSIST=false" in section
    assert "Z2CY" not in section


def test_z2cy_docs_bind_critical_path_without_get_or_flatten() -> None:
    section = _z2cy_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CY_POST_Z2CX_P3_DEPENDENCY_RECONCILIATION_DOCS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "PREDECESSOR_SLICE=11.13.5.Z2CX",
        "LAST_CANONICALLY_CLOSED_11_13_5_SLICE=SECTION_11_13_5_Z2CT",
        "THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CT_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE=true",
        "THIS_NAMED_CLASS_PERSIST_ID=SECTION_11_13_5_Z2CY",
        "Z2CX_TEXT_REWRITTEN=false",
        "Z2CW_TEXT_REWRITTEN=false",
        "Z2CV_TEXT_REWRITTEN=false",
        "Z2CU_TEXT_REWRITTEN=false",
        "Z2CT_TEXT_REWRITTEN=false",
        "GET_EXECUTED_THIS_PERSIST=false",
        "GET_EXECUTED_UNDER_THIS_OWNER_GO=false",
        "AUTHENTICATED_GET_CALLS=0",
        "VENUE_API_CALLS=0",
        "RUNTIME_API_CALLS=0",
        "GET_PERFORMED=false",
        "POST_EXECUTED=false",
        "POST_PERFORMED=false",
        "FLATTEN_EXECUTED=false",
        "FLATTEN_PERFORMED=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "EXECUTION_READY=false",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "EXECUTION_PREREQUISITE_08_STATUS=UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW",
        "EMPTY_DATA_IS_ZERO=false",
        "P3_INDEPENDENT_PARALLEL_TRACKS_POLICY=true",
        "GLOBAL_UNIQUE_CANONICAL_NEXT_STEP=NONE_BY_P3_POLICY",
        "ADJUDICATION=CRITICAL_PATH_BLOCKER_IDENTIFIED_NO_UNIQUE_CANONICAL_NEXT",
        "UNIQUE_CANONICAL_NEXT_TRACK=NONE",
        "EARLIEST_UNRESOLVED_DEPENDENCY=EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
        "NEXT_ACTIONABLE_BLOCKER=EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
        "BLOCKER_CLASS=NEW_FIRST_PARTY_GET_REQUIRED",
        "OFFLINE_RESOLUTION_POSSIBLE=false",
        "OFFLINE_REMAINING_UNRANKED_Z2AR_SURFACE=EXHAUSTED",
        "REMAINING_UNRANKED_AFTER_Z2CX=NONE",
        "REMAINING_UNADJUDICATED_Z2AR_UNRANKED_CLASSES=NONE",
        "CENSUS_COMPLETE=true",
        "OPEN_DEPENDENCY_COUNT=10",
        "FX_STATUS=NOT_REPROVEN_MISSING_EVIDENCE",
        "FX_REOPENED=false",
        "COVER_USDC_ADJUDICATED=false",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "ROUNDING_STATUS=NOT_REPROVEN_MISSING_EVIDENCE",
        "FINISHED_RISK_ENVELOPE_NUMERIC_STATUS=NOT_REPROVEN_MISSING_EVIDENCE",
        "USD_USDC_ACCOUNT_SETTLEMENT_STATUS=NOT_REPROVEN_MISSING_EVIDENCE",
        "CAN_08_BE_SATISFIED_WITHOUT_FURTHER_RUNTIME_OBSERVATION=false",
        "CURRENT_UNCONSUMED_RUNTIME_GO_FOR_RESOLUTION_PATH=NONE",
        "NON_CRITICAL_OFFLINE_REMAINDER_NOT_SELECTED=true",
        "AUTOMATIC_PREREQUISITE_08_REOBSERVATION_AUTHORIZED=false",
        f"CURRENT_CANONICAL_INSTRUMENT={CURRENT_SUI}",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
        "HARD_STOP=true",
    )
    for token in required:
        assert token in section, token


def test_z2cy_docs_forbid_activation_and_upgrades() -> None:
    section = _z2cy_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nGET_PERFORMED=true\n",
        "\nTARGET_POSITION_NONZERO_PROVEN=true\n",
        "\nEMPTY_DATA_IS_ZERO=true\n",
        "\nOFFLINE_RESOLUTION_POSSIBLE=true\n",
        "\nFX_REOPENED=true\n",
        "\nCOVER_USDC_ADJUDICATED=true\n",
        "\nUNIQUE_CANONICAL_NEXT_TRACK=P3_",
        "\nSUI_REPROOF_CLASSES_RANKED=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_remains_navigation_only() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2CY" not in text
    assert "11.13.5.Z2CY" not in text


def test_python_adjudication_matches_persist() -> None:
    assert OWNER_GO == ADJUDICATION_OWNER_GO
    assert ADJUDICATION == "CRITICAL_PATH_BLOCKER_IDENTIFIED_NO_UNIQUE_CANONICAL_NEXT"
    assert UNIQUE_CANONICAL_NEXT_TRACK == "NONE"
    assert NEXT_ACTIONABLE_BLOCKER == ("EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN")
    assert BLOCKER_CLASS == "NEW_FIRST_PARTY_GET_REQUIRED"
    assert OPEN_DEPENDENCY_COUNT == 10


def test_safety_non_regression_standing_flags_and_forbidden_go() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert "CATEGORY_C" not in GATE_NAMES
    assert "TARGET_POSITION_STATE" in GATE_NAMES
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
