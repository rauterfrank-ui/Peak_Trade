"""§11.13.5.Z2CO persist invariants. Docs/governance only. No runtime."""

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

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
PRE_SEND_GATE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "section_11_13_5_live_canary_minimum_exposure_v1"
    / "flatten_pre_send_gate_v1.py"
)

Z2CN_HEADING = (
    "### 11.13.5.Z2CN Post-Z2CM fresh unfiltered target-position runtime observation persist"
)
Z2CO_HEADING = (
    "### 11.13.5.Z2CO Post-Z2CN prerequisite 08 POST-branch refinement and "
    "not-observed no-action closure persist"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_POST_Z2CN_MAXIMUM_LEVERAGE_CANONICAL_PROGRESSION_V1"
BASELINE_SHA = "3848c713ae7e8ef1de0cf9ba4c19c4c7e683ccef"
PARENT_SHA = "c2f31370aff75bf1973e0e2520a405b8b85c3767"
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2co_section(text: str) -> str:
    start = text.find(Z2CO_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CO heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2CO"
    return text[start:end]


def _z2cn_section(text: str) -> str:
    start = text.find(Z2CN_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CN heading"
    end = text.find(Z2CO_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CO boundary after Z2CN"
    return text[start:end]


def test_z2co_heading_is_unique_and_follows_z2cn() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CO_HEADING) == 1
    z2cn = text.find(Z2CN_HEADING)
    z2co = text.find(Z2CO_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2cn < z2co < ladder


def test_z2cn_historical_slice_was_not_rewritten() -> None:
    section = _z2cn_section(_read(MASTER_RUNBOOK))
    assert "CLASSIFICATION_RESULT=TARGET_POSITION_NOT_OBSERVED" in section
    assert "EXECUTION_PREREQUISITE_08_STATUS=UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW" in section
    assert "TARGET_POSITION_ZERO_PROVEN=false" in section
    assert "CLASS_D_CONSUMED=false" in section
    assert "Z2CO" not in section


def test_z2co_docs_bind_08_post_branch_and_no_action_without_zero() -> None:
    section = _z2co_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CO_PREREQUISITE_08_POST_BRANCH_REFINEMENT_AND_NOT_OBSERVED_NO_ACTION_CLOSURE_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"PREVIOUS_ORIGIN_MAIN_SHA={PARENT_SHA}",
        "PREDECESSOR_SLICE=11.13.5.Z2CN",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2CO",
        "SELECTED_WORKPACKAGE_ID=C1_PLUS_C3_PREREQUISITE_08_POST_BRANCH_AND_NO_ACTION_CLOSURE",
        "PREREQUISITE_08_OVERCONSTRAINED=true",
        "PREREQUISITE_08_IS_FLATTEN_POST_BRANCH_ONLY=true",
        "NOT_OBSERVED_IS_UNRESOLVED_PHASE_BLOCKER=false",
        "TARGET_POSITION_NOT_OBSERVED=true",
        "TARGET_POSITION_ZERO_PROVEN=false",
        "TARGET_POSITION_NONZERO_PROVEN=false",
        "UNIQUE_ACTIONABLE_FLATTEN_CANDIDATE=false",
        "FLATTEN_POST_PERMITTED=false",
        "FLATTEN_POST_CONSTRUCTABLE_THIS_WINDOW=false",
        "EMPTY_DATA_ARRAY_IS_ZERO=false",
        "ABSENCE_TO_ZERO_INFERENCE_ALLOWED=false",
        "QUERY_COMPLETENESS_PROVEN=false",
        "HTTP_200_OR_CODE0_IMPLIES_COMPLETENESS=false",
        "EQUIVALENT_UNFILTERED_GET_ADDS_PROOF_VALUE=false",
        "NEW_NETWORK_CALL_PERFORMED=false",
        "FILTERED_INSTID_GET_PERFORMED=false",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "POST_EXECUTED=false",
        "FLATTEN_EXECUTED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "P6_RECOVERY_LOOP_ACTIVE=false",
        "Z2CN_TEXT_REWRITTEN=false",
        "Z2CM_TEXT_REWRITTEN=false",
        "Z2CE_TEXT_REWRITTEN=false",
        "Z2CA_TEXT_REWRITTEN=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
    )
    for token in required:
        assert token in section, token


def test_map_of_truth_remains_navigation_only() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2CO" not in text
    assert "11.13.5.Z2CO" not in text


def test_safety_non_regression_standing_flags_and_gates() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert "CATEGORY_C" not in GATE_NAMES
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS


def test_category_c_remains_absent_from_pre_send_gate_source() -> None:
    src = _read(PRE_SEND_GATE)
    assert "category_c_open_algo_pending_observer_v1" not in src
    assert "flatten_action_eligibility_v1" not in src
