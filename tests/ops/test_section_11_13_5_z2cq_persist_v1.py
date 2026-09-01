"""§11.13.5.Z2CQ persist invariants. Docs/governance plus offline cluster contract."""

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.execution_prerequisite_08_cluster_contract_v1 import (
    AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS,
    CLASS_D_CONSUMED,
    EARLIER_THAN_08_UNRESOLVED_IN_NUMBERED_MATRIX,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXECUTION_READY,
    HIGHER_AUTHORITY_BLOCKED_ITEMS,
    LAST_CANONICALLY_CLOSED_11_13_5_SLICE,
    LIVE_FLATTEN_PROVABILITY,
    OFFLINE_CLOSABLE_ITEMS,
    PREREQUISITE_16_CURRENT_STATUS,
    PREREQUISITE_23_CURRENT_STATUS,
    RUNTIME_FACT_REQUIRED_ITEMS,
    SEND_TIME_PASS_18_19_21_24,
    UNRESOLVED_CLUSTER,
    Z2AP_CONSUMED,
    Z2CN_IS_NOT_CURRENT_PREREQUISITE_08_PROOF,
    Z2CP_CANONICALLY_CLOSED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2CP_HEADING = (
    "### 11.13.5.Z2CP Post-Z2CO position-observation freshness numeric policy persist "
    "and offline fail-closed enforcement"
)
Z2CQ_HEADING = "### 11.13.5.Z2CQ Post-Z2CP EXECUTION_PREREQUISITE_08 flatten dependency cluster "
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_SECTION_11_13_5_POST_Z2CP_MAXIMUM_SAFE_LEVERAGE_CLUSTER_V1"
BASELINE_SHA = "6e7cfce9854f340cbc6ba2a63f93acc8883aad1c"
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cq_section(text: str) -> str:
    start = text.find(Z2CQ_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CQ heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2CQ"
    return text[start:end]


def _z2cp_section(text: str) -> str:
    start = text.find(Z2CP_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CP heading"
    end = text.find(Z2CQ_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CQ boundary after Z2CP"
    return text[start:end]


def test_z2cq_heading_is_unique_and_follows_z2cp() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CQ_HEADING) == 1
    z2cp = text.find(Z2CP_HEADING)
    z2cq = text.find(Z2CQ_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2cp < z2cq < ladder


def test_z2cp_historical_freshness_persist_was_not_rewritten() -> None:
    section = _z2cp_section(_read(MASTER_RUNBOOK))
    assert "FRESHNESS_NUMERIC_MAX_AGE=5000ms" in section
    assert "POSITION_OBSERVATION_FRESHNESS_ENFORCEMENT_IMPLEMENTED=true" in section
    assert "EXECUTION_PREREQUISITE_08_STATUS=UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW" in section
    assert "LAST_CANONICALLY_CLOSED_11_13_5_SLICE=SECTION_11_13_5_Z2CN" in section
    assert "Z2CP_PERSIST_IS_NOT_PREREQUISITE_08_DISCRIMINATOR=true" in section


def test_z2cq_docs_bind_cluster_without_flatten_or_prereq_08() -> None:
    section = _z2cq_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CQ_POST_Z2CP_EXECUTION_PREREQUISITE_08_CLUSTER_CENSUS_AND_OFFLINE_FAIL_CLOSED_GATING_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "PREDECESSOR_SLICE=11.13.5.Z2CP",
        "LAST_CANONICALLY_CLOSED_11_13_5_SLICE=SECTION_11_13_5_Z2CN",
        "THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CN_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE=true",
        "Z2CP_CANONICALLY_CLOSED=false",
        "THIS_NAMED_CLASS_PERSIST_ID=SECTION_11_13_5_Z2CQ",
        "Z2CP_TEXT_REWRITTEN=false",
        "Z2CN_TEXT_REWRITTEN=false",
        "Z2CK_TEXT_REWRITTEN=false",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "FLATTEN_EXECUTED=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "EXECUTION_READY=false",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "EXECUTION_PREREQUISITE_08_STATUS=UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW",
        "EARLIEST_UNRESOLVED_DEPENDENCY=EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
        "EARLIER_THAN_08_UNRESOLVED_IN_NUMBERED_MATRIX=false",
        "Z2CN_IS_NOT_CURRENT_PREREQUISITE_08_PROOF=true",
        "SEND_TIME_PASS_18_19_21_24=UNPROVEN",
        "PREREQUISITE_23_CURRENT_STATUS=DEFINED_CHOICE_B",
        "PREREQUISITE_23_DEFINITION_IS_NOT_CURRENT_UNRESOLVED=true",
        "TARGET_POSITION_STATE_PRE_SEND_GATE_IMPLEMENTED=true",
        "DEPENDENT_09_12_20_CANNOT_PASS_WITHOUT_08_NONZERO=true",
        "FIXTURE_NONZERO_IS_NOT_PRODUCTIVE_08_PROOF=true",
        "POSSIDE_ADDED_TO_FLATTEN_BODY=false",
        "HMAC_HANDLE_INVENTED=false",
        "Z2CQ_PERSIST_IS_NOT_FLATTEN_EXECUTE=true",
        "Z2CQ_PERSIST_IS_NOT_HMAC_HANDLE=true",
        "Z2CQ_PERSIST_IS_NOT_PREREQUISITE_08_DISCRIMINATOR=true",
        "Z2CQ_DOES_NOT_CLAIM_SEND_TIME_PASS_18_19_21_24=true",
        "Z2CK_COUNTS_REWRITTEN=false",
        f"CURRENT_CANONICAL_INSTRUMENT={CURRENT_SUI}",
        "LIVE_AUTHORIZED=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
    )
    for token in required:
        assert token in section, token


def test_z2cq_docs_forbid_activation_and_08_proof() -> None:
    section = _z2cq_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nZ2CP_TEXT_REWRITTEN=true\n",
        "\nZ2CK_COUNTS_REWRITTEN=true\n",
        "\nZ2CN_IS_NOT_CURRENT_PREREQUISITE_08_PROOF=false\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nSEND_TIME_PASS_18_19_21_24=PROVEN\n",
        "\nHMAC_HANDLE_INVENTED=true\n",
        "\nPOSSIDE_ADDED_TO_FLATTEN_BODY=true\n",
        "\nZ2CP_CANONICALLY_CLOSED=true\n",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_remains_navigation_only() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2CQ" not in text
    assert "11.13.5.Z2CQ" not in text


def test_python_cluster_constants_match_persist() -> None:
    assert EARLIEST_UNRESOLVED_DEPENDENCY == (
        "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN"
    )
    assert LAST_CANONICALLY_CLOSED_11_13_5_SLICE == "SECTION_11_13_5_Z2CN"
    assert Z2CP_CANONICALLY_CLOSED is False
    assert CLASS_D_CONSUMED is False
    assert Z2AP_CONSUMED is False
    assert EXECUTION_READY is False
    assert LIVE_FLATTEN_PROVABILITY == "UNPROVEN"
    assert SEND_TIME_PASS_18_19_21_24 == "UNPROVEN"
    assert Z2CN_IS_NOT_CURRENT_PREREQUISITE_08_PROOF is True
    assert EARLIER_THAN_08_UNRESOLVED_IN_NUMBERED_MATRIX is False
    assert PREREQUISITE_23_CURRENT_STATUS == "DEFINED_CHOICE_B"
    assert PREREQUISITE_16_CURRENT_STATUS == (
        "OFFLINE_IMPLEMENTED_RUNTIME_UNAUTHORIZED_STILL_BLOCKING"
    )
    assert AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS == "REMAINS_UNRESOLVED"
    assert "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN" in UNRESOLVED_CLUSTER
    assert "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN" in RUNTIME_FACT_REQUIRED_ITEMS
    assert "AUTHENTICATED_PRODUCTIVE_TRANSPORT" in HIGHER_AUTHORITY_BLOCKED_ITEMS
    assert "TARGET_POSITION_STATE_PRE_SEND_GATE" in OFFLINE_CLOSABLE_ITEMS


def test_safety_non_regression_standing_flags_and_forbidden_go() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert "CATEGORY_C" not in GATE_NAMES
    assert "TARGET_POSITION_STATE" in GATE_NAMES
    assert "POSITION_OBSERVATION_FRESHNESS" in GATE_NAMES
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
