"""§11.13.5.Z2CU persist invariants. Docs/governance plus offline adjudication. No runtime."""

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.post_z2ct_named_progression_track_adjudication_v1 import (
    ADJUDICATION,
    OWNER_GO as ADJUDICATION_OWNER_GO,
    RECOMMENDED_TRACK,
    UNIQUE_CANONICAL_NEXT_TRACK,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2CT_HEADING = (
    "### 11.13.5.Z2CT Post-Z2CS single unfiltered Prerequisite-08 position observation persist"
)
Z2CU_HEADING = "### 11.13.5.Z2CU Post-Z2CT named progression-track adjudication persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_POST_Z2CT_NAMED_PROGRESSION_TRACK_ADJUDICATION_V1"
BASELINE_SHA = "0917c6b426e85be94303984b5361c4d796a4cd35"
EMPTY_ENVELOPE_SHA = "fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a"
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cu_section(text: str) -> str:
    start = text.find(Z2CU_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CU heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2CU"
    return text[start:end]


def _z2ct_section(text: str) -> str:
    start = text.find(Z2CT_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CT heading"
    end = text.find(Z2CU_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CU boundary after Z2CT"
    return text[start:end]


def test_z2cu_heading_is_unique_and_follows_z2ct() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CU_HEADING) == 1
    z2ct = text.find(Z2CT_HEADING)
    z2cu = text.find(Z2CU_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2ct < z2cu < ladder


def test_z2ct_historical_observation_slice_was_not_rewritten() -> None:
    section = _z2ct_section(_read(MASTER_RUNBOOK))
    assert "GET_EXECUTED_UNDER_THIS_OWNER_GO=true" in section
    assert "AUTHENTICATED_GET_CALLS=1" in section
    assert "TARGET_POSITION_STATE=NOT_OBSERVED" in section
    assert "EXECUTION_PREREQUISITE_08_STATUS=UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW" in section
    assert "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2CT" in section
    assert f"BODY_SHA256={EMPTY_ENVELOPE_SHA}" in section
    assert "Z2CU" not in section


def test_z2cu_docs_bind_multiple_tracks_without_get_or_flatten() -> None:
    section = _z2cu_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CU_POST_Z2CT_NAMED_PROGRESSION_TRACK_ADJUDICATION_DOCS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "PREDECESSOR_SLICE=11.13.5.Z2CT",
        "LAST_CANONICALLY_CLOSED_11_13_5_SLICE=SECTION_11_13_5_Z2CT",
        "THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CT_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE=true",
        "THIS_NAMED_CLASS_PERSIST_ID=SECTION_11_13_5_Z2CU",
        "Z2CT_TEXT_REWRITTEN=false",
        "Z2CS_TEXT_REWRITTEN=false",
        "Z2CR_TEXT_REWRITTEN=false",
        "Z2CQ_TEXT_REWRITTEN=false",
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
        "EMPTY_DATA_IS_ZERO=false",
        "P3_INDEPENDENT_PARALLEL_TRACKS_POLICY=true",
        "GLOBAL_UNIQUE_CANONICAL_NEXT_STEP=NONE_BY_P3_POLICY",
        "ADJUDICATION=MULTIPLE_OWNER_SELECTABLE_TRACKS",
        "UNIQUE_CANONICAL_NEXT_TRACK=NONE",
        "RECOMMENDED_TRACK=P3_Z2AR_REMAINING_UNRANKED_SUI_REPROOF",
        "OFFLINE_PROGRESSION_AVAILABLE=true",
        "RUNTIME_REOBSERVATION_IS_ONLY_VALID_NEXT_TRACK=false",
        "IDENTICAL_UNFILTERED_GET_IS_PERMITTED_OBSERVATION_PATH_ONLY=true",
        "AUTOMATIC_PREREQUISITE_08_REOBSERVATION_AUTHORIZED=false",
        "P3_INTENTIONALLY_LEAVES_SUCCESSOR_SELECTION_TO_OWNER=true",
        f"CURRENT_CANONICAL_INSTRUMENT={CURRENT_SUI}",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
        "EARLIEST_UNRESOLVED_DEPENDENCY=EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
    )
    for token in required:
        assert token in section, token


def test_z2cu_docs_forbid_activation_and_unique_next() -> None:
    section = _z2cu_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nTARGET_POSITION_NONZERO_PROVEN=true\n",
        "\nEMPTY_DATA_IS_ZERO=true\n",
        "\nUNIQUE_CANONICAL_NEXT_TRACK=P3_",
        "\nADJUDICATION=UNIQUE_CANONICAL_NEXT_TRACK\n",
        "\nADJUDICATION=RUNTIME_REOBSERVATION_IS_ONLY_VALID_NEXT_TRACK\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nCAP21_OPTION_A_SELECTED=true\n",
        "\nCAP21_OPTION_B_SELECTED=true\n",
        "\nSUI_REPROOF_CLASSES_RANKED=true\n",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_remains_navigation_only() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2CU" not in text
    assert "11.13.5.Z2CU" not in text


def test_python_adjudication_matches_persist() -> None:
    assert OWNER_GO == ADJUDICATION_OWNER_GO
    assert ADJUDICATION == "MULTIPLE_OWNER_SELECTABLE_TRACKS"
    assert UNIQUE_CANONICAL_NEXT_TRACK == "NONE"
    assert RECOMMENDED_TRACK == "P3_Z2AR_REMAINING_UNRANKED_SUI_REPROOF"


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
