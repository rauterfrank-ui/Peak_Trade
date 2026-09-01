"""§11.13.5.Z2CS persist invariants. Docs/governance plus offline adjudication. No runtime."""

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_resolution_authority_adjudication_v1 import (
    ADJUDICATION,
    AUTHORIZED_RESOLUTION_PATH,
    CONTRACT_GAP_CLASS,
    EMPTY_DATA_IS_ZERO,
    OWNER_GO as ADJUDICATION_OWNER_GO,
    OMISSION_OF_INSTRUMENT_ROW_MEANS_ZERO_CANONICAL_RULE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2CR_HEADING = "### 11.13.5.Z2CR Post-Z2CQ fresh unfiltered target-position observation persist"
Z2CS_HEADING = (
    "### 11.13.5.Z2CS Post-Z2CR Prerequisite-08 resolution-authority adjudication persist"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_13_5_PREREQUISITE_08_RESOLUTION_AUTHORITY_ADJUDICATION_V1"
)
BASELINE_SHA = "121edb3b91978d70fd6966e7fd8cddf4c22be32c"
EMPTY_ENVELOPE_SHA = "fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a"
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cs_section(text: str) -> str:
    start = text.find(Z2CS_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CS heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2CS"
    return text[start:end]


def _z2cr_section(text: str) -> str:
    start = text.find(Z2CR_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CR heading"
    end = text.find(Z2CS_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CS boundary after Z2CR"
    return text[start:end]


def test_z2cs_heading_is_unique_and_follows_z2cr() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CS_HEADING) == 1
    z2cr = text.find(Z2CR_HEADING)
    z2cs = text.find(Z2CS_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2cr < z2cs < ladder


def test_z2cr_historical_observation_slice_was_not_rewritten() -> None:
    section = _z2cr_section(_read(MASTER_RUNBOOK))
    assert "GET_EXECUTED_UNDER_THIS_OWNER_GO=true" in section
    assert "AUTHENTICATED_GET_CALLS=1" in section
    assert "TARGET_POSITION_STATE=NOT_OBSERVED" in section
    assert "EXECUTION_PREREQUISITE_08_STATUS=UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW" in section
    assert "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2CR" in section
    assert f"BODY_SHA256={EMPTY_ENVELOPE_SHA}" in section
    assert "Z2CS" not in section


def test_z2cs_docs_bind_resolution_path_without_get_or_flatten() -> None:
    section = _z2cs_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CS_PREREQUISITE_08_RESOLUTION_AUTHORITY_ADJUDICATION_DOCS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "PREDECESSOR_SLICE=11.13.5.Z2CR",
        "LAST_CANONICALLY_CLOSED_11_13_5_SLICE=SECTION_11_13_5_Z2CR",
        "THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CR_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE=true",
        "THIS_NAMED_CLASS_PERSIST_ID=SECTION_11_13_5_Z2CS",
        "Z2CR_TEXT_REWRITTEN=false",
        "Z2CQ_TEXT_REWRITTEN=false",
        "Z2CE_TEXT_REWRITTEN=false",
        "Z2CN_TEXT_REWRITTEN=false",
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
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "EXECUTION_PREREQUISITE_08_STATUS=UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW",
        "EARLIEST_UNRESOLVED_DEPENDENCY=EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
        "ADJUDICATION=RESOLUTION_PATH_ALREADY_EXISTS",
        "CONTRACT_GAP_CLASS=NONE",
        "AUTHORIZED_RESOLUTION_PATH_COUNT=1",
        "AUTHORIZED_RESOLUTION_PATHS=UNFILTERED_GET_API_V5_ACCOUNT_POSITIONS_PLUS_CLASSIFY_TARGET_POSITION_STATE_V1",
        "CURRENT_UNCONSUMED_RUNTIME_GO_FOR_RESOLUTION_PATH=NONE",
        "TARGET_NOT_OBSERVED_SEMANTICS=INTENTIONAL_FAIL_CLOSED_THIS_WINDOW_NOT_ZERO_NOT_NONZERO_NOT_COMPLETENESS",
        "EMPTY_DATA_IS_ZERO=false",
        "OMISSION_OF_INSTRUMENT_ROW_MEANS_ZERO_CANONICAL_RULE=NONE",
        "POSITION_QTY_UNIT_STATUS=UNPROVEN",
        "CAN_08_BE_SATISFIED_WITHOUT_FURTHER_RUNTIME_OBSERVATION=false",
        "NOT_OBSERVED_EXPOSES_ZERO_SEMANTICS_CONTRACT_GAP_FOR_08=false",
        "FILTERED_INSTID_GET_IS_NOT_08_RESOLUTION_PATH=true",
        "Z2CL_CHOICE_B_IS_NOT_PRE_SEND_08_PATH=true",
        "Z2CA_Z2CN_Z2CR_EMPTY_SHA_IS_NOT_CURRENT_08_PROOF=true",
        "THIS_GO_AUTHORIZES_GET=false",
        "THIS_GO_AUTHORIZES_POST=false",
        "THIS_GO_AUTHORIZES_FLATTEN=false",
        "Z2CS_PERSIST_IS_NOT_FLATTEN_EXECUTE=true",
        "Z2CS_PERSIST_IS_NOT_PREREQUISITE_08_DISCRIMINATOR=true",
        f"CURRENT_CANONICAL_INSTRUMENT={CURRENT_SUI}",
        "LIVE_AUTHORIZED=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
    )
    for token in required:
        assert token in section, token


def test_z2cs_docs_forbid_activation_and_08_proof() -> None:
    section = _z2cs_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nZ2CR_TEXT_REWRITTEN=true\n",
        "\nEMPTY_DATA_IS_ZERO=true\n",
        "\nTARGET_POSITION_NONZERO_PROVEN=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nTHIS_GO_AUTHORIZES_GET=true\n",
        "\nCONTRACT_GAP_CLASS=missing zero-semantics contract\n",
        "\nADJUDICATION=CONTRACT_GAP_CONFIRMED\n",
        "\nADJUDICATION=PREREQUISITE_DEFINITION_INCONSISTENT\n",
        "\nADJUDICATION=INSUFFICIENT_EVIDENCE\n",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_remains_navigation_only() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2CS" not in text
    assert "11.13.5.Z2CS" not in text


def test_python_adjudication_matches_persist() -> None:
    assert OWNER_GO == ADJUDICATION_OWNER_GO
    assert ADJUDICATION == "RESOLUTION_PATH_ALREADY_EXISTS"
    assert CONTRACT_GAP_CLASS == "NONE"
    assert EMPTY_DATA_IS_ZERO is False
    assert OMISSION_OF_INSTRUMENT_ROW_MEANS_ZERO_CANONICAL_RULE == "NONE"
    assert AUTHORIZED_RESOLUTION_PATH == (
        "UNFILTERED_GET_API_V5_ACCOUNT_POSITIONS_PLUS_CLASSIFY_TARGET_POSITION_STATE_V1"
    )


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
