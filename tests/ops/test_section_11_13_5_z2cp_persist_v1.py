"""§11.13.5.Z2CP persist invariants. Docs/governance plus offline contract token."""

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_action_proof_contract_v1 import (
    POSITION_OBSERVATION_FRESHNESS_POLICY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    POSITION_OBSERVATION_FRESHNESS_ENFORCEMENT_IMPLEMENTED,
    POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
    Z2AN_QUOTE_LOCK_5000MS_AUTHORITY_TRANSFERRED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2CO_HEADING = (
    "### 11.13.5.Z2CO Post-Z2CN Z2AP flatten non-position contract residuals persist "
    "(BOUND; DOCS-ONLY; PERSIST-ONLY; NO GET; NO POST; NO MUTATION; "
    "FRESHNESS FORM RATIFIED THRESHOLD UNBOUND; "
    "PREREQUISITES 18/19/21/24 CURRENT SSOT WITH PROVENANCE; "
    "NOT CLASS D; NOT FLATTEN; NOT LIVE)"
)
Z2CP_HEADING = (
    "### 11.13.5.Z2CP Post-Z2CO position-observation freshness numeric policy persist "
    "and offline fail-closed enforcement"
)
Z2CQ_HEADING = "### 11.13.5.Z2CQ Post-Z2CP EXECUTION_PREREQUISITE_08 flatten dependency cluster "
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_13_5_POSITION_OBSERVATION_FRESHNESS_PERSIST_IMPLEMENT_PR_V1"
)
BASELINE_SHA = "d45a3c0b4ed64e4632a7b92d827818a1fd054361"
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cp_section(text: str) -> str:
    start = text.find(Z2CP_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CP heading"
    end = text.find(Z2CQ_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CQ boundary after Z2CP"
    return text[start:end]


def _z2co_section(text: str) -> str:
    start = text.find(Z2CO_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CO heading"
    end = text.find(Z2CP_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CP boundary after Z2CO"
    return text[start:end]


def test_z2cp_heading_is_unique_and_follows_z2co() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CP_HEADING) == 1
    z2co = text.find(Z2CO_HEADING)
    z2cp = text.find(Z2CP_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2co < z2cp < ladder


def test_z2co_historical_form_unbound_was_not_rewritten() -> None:
    section = _z2co_section(_read(MASTER_RUNBOOK))
    assert "POSITION_OBSERVATION_FRESHNESS_POLICY_STATUS=FORM_RATIFIED_THRESHOLD_UNBOUND" in section
    assert "FRESHNESS_NUMERIC_THRESHOLD_CANONICALLY_AUTHORIZED=false" in section
    assert "POSITION_OBSERVATION_FRESHNESS_ENFORCEMENT_IMPLEMENTED=false" in section
    assert "PYTHON_CONTRACT_TOKEN_REMAINS=UNPROVEN" in section
    assert "Z2CO_DOES_NOT_INVENT_FRESHNESS_NUMERIC=true" in section
    assert "LAST_CANONICALLY_CLOSED_11_13_5_SLICE=SECTION_11_13_5_Z2CN" in section


def test_z2cp_docs_bind_numeric_policy_without_flatten_or_prereq_08() -> None:
    section = _z2cp_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CP_POSITION_OBSERVATION_FRESHNESS_NUMERIC_POLICY_PERSIST_AND_OFFLINE_ENFORCEMENT_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "PREDECESSOR_SLICE=11.13.5.Z2CO",
        "LAST_CANONICALLY_CLOSED_11_13_5_SLICE=SECTION_11_13_5_Z2CN",
        "THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CN_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE=true",
        "THIS_NAMED_CLASS_PERSIST_ID=SECTION_11_13_5_Z2CP",
        "Z2CO_TEXT_REWRITTEN=false",
        "Z2CN_TEXT_REWRITTEN=false",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "FLATTEN_EXECUTED=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "EXECUTION_READY=false",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "EXECUTION_PREREQUISITE_08_STATUS=UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW",
        "SEND_TIME_PASS_18_19_21_24=UNPROVEN",
        "FRESHNESS_NUMERIC_THRESHOLD_CANONICALLY_AUTHORIZED=true",
        "FRESHNESS_NUMERIC_MAX_AGE=5000ms",
        "OWNER_POSITION_OBSERVATION_MAX_AGE=5000",
        "UNIT=ms",
        "APPLIES_TO=FLATTEN_PRE_SEND_POSITION_OBSERVATION",
        "ALSO_APPLIES_TO_POST_ACTION_READBACK=false",
        "OBSERVATION_TIMESTAMP_FIELD=LOCAL_RESPONSE_RECEIVED_AT",
        "CLOCK_DOMAIN=LOCAL_MONOTONIC_ELAPSED_TIME",
        "AGE_EVALUATION_POINT=IMMEDIATELY_BEFORE_FLATTEN_SEND_PERMIT_DECISION",
        "BOUNDARY_COMPARATOR=STRICT_GREATER_THAN",
        "AGE_EQUAL_TO_MAX_AGE_ALLOWED=true",
        "FAIL_CLOSED_ON_AGE_EXCEEDED=true",
        "Z2AN_QUOTE_LOCK_5000MS_AUTHORITY_TRANSFERRED=false",
        "POSITION_OBSERVATION_5000MS_IS_NEW_INDEPENDENT_OWNER_RATIFICATION=true",
        "POSITION_OBSERVATION_FRESHNESS_ENFORCEMENT_IMPLEMENTED=true",
        "PYTHON_CONTRACT_TOKEN=POLICY_BOUND_ENFORCEMENT_IMPLEMENTED_OFFLINE_SEND_TIME_UNPROVEN",
        "POST_ACTION_READBACK_FRESHNESS_POLICY=SEPARATE_LATER_IF_REQUIRED",
        "SAME_GET_MAY_SERVE_PRE_SEND_AND_POST_READBACK=false",
        "Z2CP_PERSIST_IS_NOT_FLATTEN_EXECUTE=true",
        "Z2CP_PERSIST_IS_NOT_HMAC_HANDLE=true",
        "Z2CP_DOES_NOT_TRANSFER_Z2AN_QUOTE_LOCK_AUTHORITY=true",
        f"CURRENT_CANONICAL_INSTRUMENT={CURRENT_SUI}",
        "LIVE_AUTHORIZED=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
    )
    for token in required:
        assert token in section, token


def test_z2cp_docs_forbid_activation_and_authority_transfer() -> None:
    section = _z2cp_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nZ2CO_TEXT_REWRITTEN=true\n",
        "\nZ2AN_QUOTE_LOCK_5000MS_AUTHORITY_TRANSFERRED=true\n",
        "\nALSO_APPLIES_TO_POST_ACTION_READBACK=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nSEND_TIME_PASS_18_19_21_24=PROVEN\n",
        "\nPYTHON_CONTRACT_TOKEN=PROVEN\n",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_remains_navigation_only() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2CP" not in text
    assert "11.13.5.Z2CP" not in text


def test_python_token_and_enforcement_match_persist() -> None:
    assert POSITION_OBSERVATION_FRESHNESS_POLICY == (
        "POLICY_BOUND_ENFORCEMENT_IMPLEMENTED_OFFLINE_SEND_TIME_UNPROVEN"
    )
    assert POSITION_OBSERVATION_FRESHNESS_ENFORCEMENT_IMPLEMENTED is True
    assert POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS == 5000
    assert Z2AN_QUOTE_LOCK_5000MS_AUTHORITY_TRANSFERRED is False


def test_safety_non_regression_standing_flags_and_forbidden_go() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert "CATEGORY_C" not in GATE_NAMES
    assert "POSITION_OBSERVATION_FRESHNESS" in GATE_NAMES
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
