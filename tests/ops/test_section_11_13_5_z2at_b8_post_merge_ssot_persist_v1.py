"""§11.13.5.Z2AT post-B8 pre-submit cap SSOT persist.

Docs/governance invariants only. Records that B8 is merged on main and
bound offline on Canary entry + SP-04, without venue proof, without
consuming Z2AP/Z2AR, and without inventing a unique global next.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AT_HEADING = "### 11.13.5.Z2AT Post-B8 pre-submit open-position-cap SSOT persist"
Z2AS_HEADING = "### 11.13.5.Z2AS Owner P3 independent parallel tracks selection-semantics persist"
Z2AU_HEADING = "### 11.13.5.Z2AU Offline Z2AP live-flatten construction and gate-binding persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_SCOPED_NAMED_TRACK_OR_NAMED_CLASS_"
    "PROGRESSION_NOT_AUTHORIZED_BY_THIS_PERSIST_Z2AT_B8_POST_MERGE_"
    "SSOT_ALIGN_ONLY_GLOBAL_UNIQUE_CANONICAL_NEXT_STEP_NONE_BY_P3_POLICY_"
    "NO_Z2AP_CONSUME_NO_Z2AR_CONSUME_NO_B8_VENUE_TRACK_NO_FLATTEN_EXECUTE_"
    "NO_SUI_REPROOF_NO_CANONICAL_REBIND_NO_GET_NO_POST_NO_ORDER_NO_LIVE_"
    "WIRE_NO_FUNDING_NO_CANARY_NOT_AUTHORIZED"
)
OWNER_GO = "SECTION_11_13_5_B8_POST_MERGE_CANONICAL_SSOT_PERSIST_COMPOUND_FAIL_CLOSED_NO_EXECUTE"
BASELINE_SHA = "50737fb3ab6beb6c4f2aa1dde51e83549646d066"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2at_section(text: str) -> str:
    start = text.find(Z2AT_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AT heading"
    end = text.find(Z2AU_HEADING, start)
    assert end > start, "missing §11.13.5.Z2AU boundary after Z2AT"
    return text[start:end]


def test_z2at_heading_is_unique_and_follows_z2as() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AT_HEADING) == 1
    z2as = text.find(Z2AS_HEADING)
    z2at = text.find(Z2AT_HEADING)
    z2au = text.find(Z2AU_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2as < z2at < z2au < ladder


def test_z2at_docs_bind_b8_merge_without_execution_or_track_consumption() -> None:
    section = _z2at_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_B8_POST_MERGE_CANONICAL_SSOT_PERSIST_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "PERSIST_CLASS=DOCS_SSOT_ALIGNMENT_ONLY",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"B8_MERGE_SHA={BASELINE_SHA}",
        "B8_PR=6018",
        "B8_ON_MAIN=true",
        "B8_STATUS=MERGED_TO_MAIN",
        "MERGE_NE_EXECUTION_PROOF=true",
        "Z2AS_REMAINS_P3_POLICY_BASIS=true",
        "Z2AS_TEXT_REWRITTEN=false",
        "Z2AP_TEXT_REWRITTEN=false",
        "Z2AR_TEXT_REWRITTEN=false",
        "Z2AP_CONSUMED=false",
        "Z2AR_CONSUMED=false",
        "Z2AP_PRODUCTIVE_FLATTEN_NEXT_POINTER_CONSUMED_AS_FLATTEN_PROOF=false",
        "Z2AR_FURTHER_SUI_PROOF_NEXT_POINTER_CONSUMED_AS_SUI_PROOF=false",
        "P3_INDEPENDENT_PARALLEL_TRACKS_POLICY=true",
        "TRACK_RELATION=INDEPENDENT_PARALLEL",
        "GLOBAL_UNIQUE_CANONICAL_NEXT_STEP=NONE_BY_P3_POLICY",
        "GLOBAL_POINTER_PRECEDENCE=NONE_BY_P3_POLICY",
        "B8_VENUE_PROOF_IS_NOT_A_THIRD_CANONICAL_TRACK=true",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "LAST_CANONICALLY_CLOSED_STEP=LF_12",
        "B8_SCOPED_HOSTS=CANARY_ENTRY+SP04_PRODUCTIVE_TESTNET_SUBMIT",
        "B8_SCOPED_IMPLEMENTATION_GAP=NONE",
        "B8_FLATTEN_TRANSPORT_IN_SCOPE=false",
        "B8_OPERATIONAL_EXECUTION_PROVEN=false",
        "B8_VENUE_SUCCESS_PROVEN=false",
        "CANARY_EXECUTED=false",
        "TESTNET_ORDER_EXECUTED=false",
        "LIVE_ORDER_EXECUTED=false",
        "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED=false",
        "B7_FINDING_A_STATUS=PARTIALLY_CLOSED",
        "B7_FINDING_B_STATUS=CLOSED",
        "B7_FINDING_C_STATUS=CLOSED",
        "B7_FINDING_D_STATUS=SUPERSEDED_AS_AUTHORITY",
        "B7_FINDING_E_STATUS=CLOSED",
        "B7_FINDING_F_STATUS=CLOSED",
        "B7_FINDING_G_STATUS=CLOSED_OFFLINE",
        "CANARY_LEGACY_POSITION_COUNT_0_IS_NOT_AUTHORITY=true",
        "Z2AP_TRACK_STATUS=OPEN_UNCONSUMED",
        "Z2AR_SUI_TRACK_STATUS=OPEN_UNCONSUMED",
        "LIVE_FLATTEN_STATUS=UNPROVEN_FORBIDDEN",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "CAN_SUBMIT_ORDER_TODAY=false",
        "FACE_VALUE_CONFLICT_AS_DOCUMENTARY_CONFLICT=OPEN_QUARANTINED",
        "SETTLEMENT_PNL=UNPROVEN",
        "USD_USDC_OPERATOR=UNPROVEN",
        "COVER_USDC=UNINSTANTIATED",
        "NOT_A_B8_PRE_SUBMIT_CAP_BLOCKER=true",
        "NOT_A_Z2AP_FLATTEN_POST_PREREQUISITE=true",
        "DOCS_PERSIST_IS_NOT_ADMISSIBLE_PRODUCTIVE_EVIDENCE=true",
        "MERGED_PLUS_OFFLINE_TESTED_IS_NOT_PRODUCTIVE_PROOF=true",
        "B8_MERGED_NE_B8_OPERATIONAL_PROVEN=true",
        "LEGACY_CANARY_POSITION_COUNT_0_NE_ACCOUNT_WIDE_CAP_AUTHORITY=true",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "SECTION_LOCAL_CANONICAL_NEXT_STEP_ROLE="
        "RESIDUAL_AUTHORIZATION_BOUNDARY_OF_THIS_PERSIST_NOT_GLOBAL_UNIQUE_NEXT",
        "HARD_STOP_AFTER_THIS_TASK=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2AT marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nCAN_SUBMIT_ORDER_TODAY=true\n",
        "\nB8_OPERATIONAL_EXECUTION_PROVEN=true\n",
        "\nB8_VENUE_SUCCESS_PROVEN=true\n",
        "\nCANARY_EXECUTED=true\n",
        "\nTESTNET_ORDER_EXECUTED=true\n",
        "\nLIVE_ORDER_EXECUTED=true\n",
        "\nLIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nZ2AR_CONSUMED=true\n",
        "\nZ2AP_PRODUCTIVE_FLATTEN_NEXT_POINTER_CONSUMED_AS_FLATTEN_PROOF=true\n",
        "\nZ2AR_FURTHER_SUI_PROOF_NEXT_POINTER_CONSUMED_AS_SUI_PROOF=true\n",
        "\nGET_EXECUTED_THIS_STEP=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nB8_VENUE_PROOF_IS_NOT_A_THIRD_CANONICAL_TRACK=false\n",
        "\nCANARY_LEGACY_POSITION_COUNT_0_IS_NOT_AUTHORITY=false\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AT marker present: {marker!r}"
    assert "GLOBAL_UNIQUE_CANONICAL_NEXT_STEP=NONE_BY_P3_POLICY" in section
    assert "B8_SCOPED_HOSTS=CANARY_ENTRY+SP04_PRODUCTIVE_TESTNET_SUBMIT" in section


def test_z2at_map_of_truth_remains_navigation_only_without_z2at_ssot_row() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "§11.13.5.Z2AT |" not in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}\n" not in mot
