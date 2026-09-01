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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_action_proof_contract_v1 import (
    POSITION_OBSERVATION_FRESHNESS_POLICY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2CK_HEADING = (
    "### 11.13.5.Z2CK Post-Z2CJ / post-#6114 P3 Class D / Z2AP "
    "pre-execution readiness fail-closed canonical persist"
)
Z2CL_HEADING = (
    "### 11.13.5.Z2CL Post-Z2CK CHOICE_B post-action success predicate "
    "and offline productive flatten urllib persist"
)
Z2CN_HEADING = (
    "### 11.13.5.Z2CN Post-Z2CM fresh unfiltered target-position runtime observation persist"
)
Z2CO_HEADING = (
    "### 11.13.5.Z2CO Post-Z2CN Z2AP flatten non-position contract residuals persist "
    "(BOUND; DOCS-ONLY; PERSIST-ONLY; NO GET; NO POST; NO MUTATION; "
    "FRESHNESS FORM RATIFIED THRESHOLD UNBOUND; "
    "PREREQUISITES 18/19/21/24 CURRENT SSOT WITH PROVENANCE; "
    "NOT CLASS D; NOT FLATTEN; NOT LIVE)"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_SECTION_11_13_5_Z2AP_FLATTEN_NON_POSITION_CONTRACT_RESIDUALS_DOCS_ONLY_V1"
)
BASELINE_SHA = "001404d148fb9c203217e110bdf041406e7bb5e4"
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


def _z2ck_section(text: str) -> str:
    start = text.find(Z2CK_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CK heading"
    end = text.find(Z2CL_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CL boundary after Z2CK"
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
    assert "GET_EXECUTED_UNDER_THIS_OWNER_GO=true" in section
    assert "CLASSIFICATION_RESULT=TARGET_POSITION_NOT_OBSERVED" in section
    assert "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2CN" in section
    assert "CLASS_D_CONSUMED=false" in section
    assert "Z2CO" not in section


def test_z2ck_historical_counts_and_non_blocking_ids_were_not_rewritten() -> None:
    section = _z2ck_section(_read(MASTER_RUNBOOK))
    assert "CLASS_D_PRECONDITION_COUNT=25" in section
    assert "CLASS_D_PRECONDITION_PROVEN_COUNT=12" in section
    assert "CLASS_D_PRECONDITION_UNPROVEN_COUNT=10" in section
    assert "CLASS_D_PRECONDITION_DISPROVEN_COUNT=3" in section
    assert "NON_BLOCKING_NON_PROVEN_PRECONDITION_COUNT=4" in section
    assert (
        "NON_BLOCKING_NON_PROVEN_PRECONDITION_IDS="
        "EXECUTION_PREREQUISITE_18_NO_OTHER_TRADE_THROUGH_SAME_FLOW;"
        "EXECUTION_PREREQUISITE_19_MUTATION_LIMITED_TO_CANONICAL_SUI;"
        "EXECUTION_PREREQUISITE_21_DUPLICATE_SUBMIT_PROTECTION;"
        "EXECUTION_PREREQUISITE_24_AUDIT_TRAIL_SUFFICIENT"
    ) in section
    assert "Z2CO" not in section
    assert (
        "PREREQUISITE_21_STATUS_AFTER=CODE_BOUND_DUPLICATE_POST_FORBIDDEN_SEND_TIME_PASS_UNPROVEN"
        not in section
    )


def test_z2co_docs_bind_cluster_without_numeric_freshness_or_flatten() -> None:
    section = _z2co_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CO_Z2AP_FLATTEN_NON_POSITION_CONTRACT_RESIDUALS_DOCS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "TRACK_ID=P3_Z2AP_FLATTEN_NON_POSITION_CONTRACT_RESIDUALS",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "PREDECESSOR_SLICE=11.13.5.Z2CN",
        "LAST_CANONICALLY_CLOSED_11_13_5_SLICE=SECTION_11_13_5_Z2CN",
        "THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CN_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE=true",
        "THIS_NAMED_CLASS_PERSIST_ID=SECTION_11_13_5_Z2CO",
        "Z2CN_TEXT_REWRITTEN=false",
        "Z2CK_TEXT_REWRITTEN=false",
        "Z2CL_TEXT_REWRITTEN=false",
        "GET_EXECUTED_THIS_PERSIST=false",
        "GET_EXECUTED_UNDER_THIS_OWNER_GO=false",
        "AUTHENTICATED_GET_CALLS=0",
        "POST_EXECUTED=false",
        "FLATTEN_EXECUTED=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "CLASS_C_CONSUMED=true",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "EXECUTION_READY=false",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "TARGET_POSITION_NONZERO_PROVEN=false",
        "TARGET_POSITION_NOT_OBSERVED=true",
        "CURRENT_SUI_ZERO=UNPROVEN",
        "EMPTY_EQUALS_ZERO=false",
        "FILTERED_INSTID_GET_IS_NOT_CURRENT_SUI_ZERO_PROOF=true",
        "Z2CL_CHOICE_B_REMAINS_CURRENT_FROM_THAT_SLICE_FORWARD=true",
        "OFFLINE_URLLIB_IS_NOT_SEND_AUTHORIZATION=true",
        "EXECUTION_PREREQUISITE_08_STATUS=UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW",
        "THIS_CLUSTER_DOES_NOT_RESOLVE_PREREQUISITE_08=true",
        "THIS_CLUSTER_DOES_NOT_AUTHORIZE_FLATTEN=true",
        "POSITION_OBSERVATION_FRESHNESS_POLICY_STATUS=FORM_RATIFIED_THRESHOLD_UNBOUND",
        "POSITION_OBSERVATION_FRESHNESS_POLICY_FORM_RATIFIED=true",
        "FRESHNESS_NUMERIC_THRESHOLD_CANONICALLY_AUTHORIZED=false",
        "POSITION_OBSERVATION_FRESHNESS_NUMERIC_THRESHOLD_STATUS=ABSENT_NOT_INVENTED",
        "POSITION_OBSERVATION_FRESHNESS_ENFORCEMENT_IMPLEMENTED=false",
        "PYTHON_CONTRACT_TOKEN_REMAINS=UNPROVEN",
        "SILENT_DEFAULT_MAX_AGE_FORBIDDEN=true",
        "DERIVE_THRESHOLD_FROM_HTTP_TIMEOUTS_FORBIDDEN=true",
        "DERIVE_THRESHOLD_FROM_INTERVALS_FORBIDDEN=true",
        "OBSERVATION_MUST_NOT_BE_TREATED_AS_FRESH_WITHOUT_OWNER_NUMERIC_THRESHOLD=true",
        "Z2CB_HISTORICAL_EXECUTION_PREREQUISITE_18_NO_OTHER_TRADE_THROUGH_SAME_FLOW=UNREACHABLE_BECAUSE_SEND_UNIMPLEMENTED",
        "PREREQUISITE_18_STATUS_AFTER=OFFLINE_FLATTEN_FLOW_CONTRACT_BOUND_SEND_TIME_PASS_UNPROVEN",
        "Z2CB_HISTORICAL_EXECUTION_PREREQUISITE_19_MUTATION_LIMITED_TO_CANONICAL_SUI=UNREACHABLE",
        "PREREQUISITE_19_STATUS_AFTER=OFFLINE_CANONICAL_SUI_INSTRUMENT_BINDING_BOUND_SEND_TIME_PASS_UNPROVEN",
        "Z2CB_HISTORICAL_EXECUTION_PREREQUISITE_21_DUPLICATE_SUBMIT_PROTECTION=PASS_CODE_PRESENT_BUT_UNREACHABLE",
        "DUPLICATE_POST_FORBIDDEN=true",
        "DUPLICATE_POST_FORBIDDEN_PROVENANCE=SECTION_11_13_5_Z2CL",
        "PREREQUISITE_21_STATUS_AFTER=CODE_BOUND_DUPLICATE_POST_FORBIDDEN_SEND_TIME_PASS_UNPROVEN",
        "Z2CK_NOT_RETROACTIVELY_MARKED_PROVEN=true",
        "Z2CK_HISTORICAL_STATUS_PRESERVED=true",
        "Z2CB_HISTORICAL_EXECUTION_PREREQUISITE_24_AUDIT_TRAIL_SUFFICIENT=PASS_CODE_PRESENT_BUT_UNREACHABLE",
        "PREREQUISITE_24_STATUS_AFTER=OFFLINE_AUDIT_BOUNDARY_PRESENT_SEND_TIME_PASS_UNPROVEN",
        "Z2CK_CLASS_D_PRECONDITION_COUNT=25",
        "Z2CK_CLASS_D_PRECONDITION_PROVEN_COUNT=12",
        "HISTORICAL_COUNTS_REWRITTEN=false",
        "Z2CO_DOES_NOT_INVENT_FRESHNESS_NUMERIC=true",
        "Z2CO_PERSIST_IS_NOT_FLATTEN_EXECUTE=true",
        "Z2CO_PERSIST_IS_NOT_CLASS_D_CONSUME=true",
        "Z2CO_PERSIST_IS_NOT_HMAC_HANDLE=true",
        "Z2CO_PERSIST_IS_NOT_PREREQUISITE_16=true",
        "Z2CO_PERSIST_IS_NOT_PREREQUISITE_08_DISCRIMINATOR=true",
        f"CURRENT_CANONICAL_INSTRUMENT={CURRENT_SUI}",
        "LIVE_AUTHORIZED=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
    )
    for token in required:
        assert token in section, token


def test_z2co_docs_forbid_activation_and_historical_rewrite() -> None:
    section = _z2co_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nEMPTY_EQUALS_ZERO=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nGET_EXECUTED_UNDER_THIS_OWNER_GO=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nZ2CK_TEXT_REWRITTEN=true\n",
        "\nZ2CN_TEXT_REWRITTEN=true\n",
        "\nHISTORICAL_COUNTS_REWRITTEN=true\n",
        "\nZ2CK_NOT_RETROACTIVELY_MARKED_PROVEN=false\n",
        "\nFRESHNESS_NUMERIC_THRESHOLD_CANONICALLY_AUTHORIZED=true\n",
        "\nPOSITION_OBSERVATION_FRESHNESS_ENFORCEMENT_IMPLEMENTED=true\n",
        "\nTHIS_CLUSTER_DOES_NOT_RESOLVE_PREREQUISITE_08=false\n",
        "\nTHIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CN_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE=false\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nNETWORK_SESSION_ENABLED=true\n",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_remains_navigation_only() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2CO" not in text
    assert "11.13.5.Z2CO" not in text


def test_python_freshness_token_remains_unproven() -> None:
    assert POSITION_OBSERVATION_FRESHNESS_POLICY == "UNPROVEN"


def test_safety_non_regression_standing_flags_and_forbidden_go() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert "CATEGORY_C" not in GATE_NAMES
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
