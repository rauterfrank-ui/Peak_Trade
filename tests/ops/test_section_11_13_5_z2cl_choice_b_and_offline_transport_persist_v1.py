"""§11.13.5.Z2CL CHOICE_B and offline productive urllib persist.

Docs/governance invariants only. Does not authorize flatten execute,
live, testnet, canary, network session, Class D consume, or CAP21.
Does not rewrite Z2CK, Z2CB, Z2CA, Z2CE, or Z2AP.
"""

from __future__ import annotations

from pathlib import Path

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
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = (
    "PEAK_TRADE_11_13_5_Z2CL_POST_ACTION_SUCCESS_PREDICATE_CHOICE_B_"
    "AND_OFFLINE_PRODUCTIVE_TRANSPORT_WORKPACKAGE_V1"
)
BASELINE_SHA = "ffabdd075d99135f4ebcbc9998271138eef54b89"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cl_section(text: str) -> str:
    start = text.find(Z2CL_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CL heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2CL"
    return text[start:end]


def _z2ck_section(text: str) -> str:
    start = text.find(Z2CK_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CK heading"
    end = text.find(Z2CL_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CL boundary after Z2CK"
    return text[start:end]


def test_z2cl_heading_is_unique_and_follows_z2ck() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CL_HEADING) == 1
    z2ck = text.find(Z2CK_HEADING)
    z2cl = text.find(Z2CL_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2ck < z2cl < ladder


def test_z2ck_historical_slice_was_not_rewritten() -> None:
    section = _z2ck_section(_read(MASTER_RUNBOOK))
    assert "SUCCESS_PREDICATE_STATUS=CONTRADICTED" in section
    assert "CLASS_D_CONSUMED=false" in section
    assert "PRODUCTIVE_URLLIB_SEND_IMPLEMENTED=false" in section
    assert "Z2CL" not in section


def test_z2cl_docs_bind_choice_b_without_execute() -> None:
    section = _z2cl_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "OWNER_CANONICAL_DECISION=CHOICE_B",
        "POST_ACTION_SUCCESS_PREDICATE_STATUS=BOUND_CHOICE_B",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "PREDECESSOR_SLICE=11.13.5.Z2CK",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2CL",
        "Z2CK_TEXT_REWRITTEN=false",
        "Z2CB_TEXT_REWRITTEN=false",
        "Z2CA_TEXT_REWRITTEN=false",
        "Z2CE_TEXT_REWRITTEN=false",
        "Z2AP_TEXT_REWRITTEN=false",
        "Z2CB_PREREQUISITE_23_HISTORICAL_STATUS=FAIL_AMBIGUOUS",
        "Z2CK_SUCCESS_PREDICATE_HISTORICAL_STATUS=CONTRADICTED",
        "POST_ACTION_MISSING_TARGET_MAY_SATISFY_POS_EQ_0=true",
        "ONLY_IF_PRE_TARGET_NONZERO_EXPLICITLY_PROVEN=true",
        "SCOPE=FLATTEN_POST_ACTION_SUCCESS_EVALUATOR_ONLY",
        "P7_3_EMPTY_DATA_IS_ZERO=false",
        "PRE_SEND_TARGET_NOT_OBSERVED_NE_ZERO=true",
        "NO_GLOBAL_MISSING_EQUALS_ZERO=true",
        "PRE_MISSING_PLUS_POST_MISSING_IS_ALREADY_FLAT_NOOP_NOT_PRODUCTIVE_SUCCESS=true",
        "MISSING_TARGET_ALONE_PROVES_NO_FLIP=false",
        "CB-01_PRE_TARGET_NONZERO_EXPLICITLY_PROVEN=true",
        "CB-08_DATA_NONE_IS_NOT_VALID_EMPTY_SUCCESS_EVIDENCE=true",
        "CB-10_FLIP_OR_UNEXPECTED_RELATED_STATE_CANNOT_BE_MASKED_BY_MISSING_TARGET=true",
        "DUMMY_ALLOWED_RECEIPT_ACCEPTED=false",
        "REQUEST_BODY_BOUND_TO_RECEIPT=true",
        "HTTP_200_IMPLIES_FLATTEN_SUCCESS=false",
        "POSITION_OBSERVATION_FRESHNESS_POLICY=UNPROVEN",
        "Z2CL_FIRST_PR_HEAD_SHA=624392b638348a9673cbdf536e1c8630df5a2cf5",
        "Z2CL_PREMERGE_HARDENING_OWNER_GO=P6_Z2CL_PREMERGE_CHOICE_B_CAUSAL_AND_PRODUCTIVE_TRANSPORT_HARDENING_V1",
        "Z2CL_PREMERGE_AUDIT_VERDICT_AT_FIRST_HEAD=DO_NOT_MERGE_YET",
        "EXPLICIT_ZERO_ROW_NOT_REQUIRED_FROM_VENUE=true",
        "EXECUTION_PREREQUISITE_23_READBACK_SUCCESS_PREDICATE_DEFINED_BEFORE_POST=DEFINED_CHOICE_B",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "EXECUTION_READY=false",
        "PRODUCTIVE_URLLIB_SEND_IMPLEMENTED=true",
        "NETWORK_SESSION_AUTHORIZED_DEFAULT=false",
        "OFFLINE_IMPLEMENTATION_IMPLIES_NETWORK_AUTHORIZATION=false",
        "CANARY_TRANSPORT_REUSED_AS_WHOLE=false",
        "PRODUCTIVE_SIGNING_REUSE_PROVEN=false",
        "AUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS=REMAINS_UNRESOLVED",
        "PREREQUISITE_16_STATUS_AFTER=OFFLINE_IMPLEMENTED_RUNTIME_UNAUTHORIZED_STILL_BLOCKING",
        "CAP21_STATUS=OPTION_C_DEFER_KEEP_UNPROVEN",
        "EMPTY_EQUALS_ZERO=false",
        "LIVE_AUTHORIZED=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
    )
    for marker in required:
        assert marker in section, f"missing Z2CL marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nEMPTY_EQUALS_ZERO=true\n",
        "\nNETWORK_SESSION_AUTHORIZED_DEFAULT=true\n",
        "\nCANARY_TRANSPORT_REUSED_AS_WHOLE=true\n",
        "\nPRODUCTIVE_SIGNING_REUSE_PROVEN=true\n",
        "\nAUTHENTICATED_PRODUCTIVE_TRANSPORT_STATUS=CLOSED\n",
        "\nCAP21_OPTION_A_SELECTED=true\n",
        "\nCAP21_OPTION_B_SELECTED=true\n",
        "\nZ2CK_TEXT_REWRITTEN=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nPOST_EXECUTED=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2CL marker present: {marker!r}"


def test_z2cl_map_of_truth_remains_navigation_only() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "§11.13.5.Z2CL |" not in mot
