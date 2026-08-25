"""§11.13.5.Z2CF post-Z2CE / post-#6058 next-pointer adjudication persist.

Docs/governance invariants only. Records the already-adjudicated
normal-system pointer state without runtime, GET, POST, flatten,
Cover, live, testnet, canary, track selection, or P7.3 reopen. Does
not rewrite Z2CE. Does not treat #6058 as a normal Z2 slice. Does not
treat P8 PASS as live readiness. Does not treat Face Value as fully
closed. Does not treat NONE_BY_P3_POLICY as no open tracks.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2CE_HEADING = (
    "### 11.13.5.Z2CE Post-Z2CD P7.3 first-party query-grammar and "
    "zero-elicitation semantics persist"
)
Z2CF_HEADING = (
    "### 11.13.5.Z2CF Post-Z2CE / post-#6058 normal-system next-pointer adjudication persist"
)
SECTION_22_HEADING = "# 22. Immediate Next Capability"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = (
    "SECTION_11_13_5_POST_Z2CE_POST_6058_NORMAL_SYSTEM_NEXT_POINTER_ADJUDICATION_PERSIST_ONLY"
)
BASELINE_SHA = "101ce76d92afb6c90418735fcf46cf706b6e956b"
PREDECESSOR_SHA = "79fe30591fabe15b816df24b9078613430e73067"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cf_section(text: str) -> str:
    start = text.find(Z2CF_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CF heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2CF"
    return text[start:end]


def _z2ce_section(text: str) -> str:
    start = text.find(Z2CE_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CE heading"
    end = text.find(Z2CF_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CF boundary after Z2CE"
    return text[start:end]


def _section_22(text: str) -> str:
    start = text.find(SECTION_22_HEADING)
    assert start >= 0, "missing §22 heading"
    end = text.find("## 22.0 Historical superseded Immediate Next", start)
    assert end > start, "missing §22.0 boundary"
    return text[start:end]


def test_z2cf_heading_is_unique_and_follows_z2ce() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CF_HEADING) == 1
    z2ce = text.find(Z2CE_HEADING)
    z2cf = text.find(Z2CF_HEADING)
    ladder = text.find(LADDER_HEADING)
    section_22 = text.find(SECTION_22_HEADING)
    assert 0 <= z2ce < z2cf < ladder < section_22


def test_z2ce_historical_slice_was_not_rewritten() -> None:
    section = _z2ce_section(_read(MASTER_RUNBOOK))
    assert "QUERY_GRAMMAR_STATUS=PROVEN" in section
    assert "OMIT_VS_ZERO_SEMANTICS_STATUS=PROVEN" in section
    assert "P7_3_FLATTEN_PRECONDITION_STATUS=UNRESOLVED_FAIL_CLOSED" in section
    assert (
        "NEXT_PROOF_PATH=NO_EXISTING_PROOF_PATH_STOP_BECAUSE_INSTID_PRECONDITIONS_ARE_NOT_ESTABLISHED"
        in section
    )
    assert "EMPTY_EQUALS_ZERO=false" in section
    assert "LIVE_AUTHORIZED=false" in section
    assert "Z2CF" not in section


def test_z2cf_docs_bind_next_pointer_adjudication_without_track_selection() -> None:
    section = _z2cf_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CF_CANDIDATE_ADDITIVE_DOCS_ONLY_NEXT_POINTER_ADJUDICATION_PERSIST",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "PERSIST_CLASS=Z2CF_POST_Z2CE_POST_6058_NEXT_POINTER_ADJUDICATION_SSOT_PERSIST_DOCS_ONLY",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "ORIGIN_MAIN_SUPERSESSION_STATUS=NONE",
        "PREDECESSOR_NORMAL_SLICE=11.13.5.Z2CE",
        "PREDECESSOR_NORMAL_PR=#6057",
        f"PREDECESSOR_NORMAL_SHA={PREDECESSOR_SHA}",
        "Z2CE_TEXT_REWRITTEN=false",
        "Z2CD_TEXT_REWRITTEN=false",
        "Z2CA_TEXT_REWRITTEN=false",
        "LAST_CANONICALLY_CLOSED_NORMAL_STEP=SECTION_11_13_5_Z2CE",
        "LAST_CANONICALLY_CLOSED_NORMAL_PR=#6057",
        f"LAST_CANONICALLY_CLOSED_NORMAL_SHA={PREDECESSOR_SHA}",
        "PR_6058_ROLE=FORENSIC_INGRESS_GATE_POLICY_ORTHOGONAL_TO_NORMAL_11_13_5_NEXT_POINTER",
        "PR_6058_DOES_NOT_CREATE_NEW_NORMAL_NEXT_POINTER=true",
        "PR_6058_IS_NOT_A_Z2_SLICE=true",
        "P3_INDEPENDENT_PARALLEL_TRACKS_POLICY=true",
        "GLOBAL_UNIQUE_CANONICAL_NEXT_STEP=NONE_BY_P3_POLICY",
        "CURRENT_CANONICAL_NEXT_POINTER=NONE_BY_P3_POLICY",
        "NONE_BY_P3_POLICY_DOES_NOT_MEAN_NO_OPEN_TRACKS=true",
        "NONE_BY_P3_POLICY_DOES_NOT_MEAN_NO_OPEN_RESIDUALS=true",
        "NO_PARALLEL_TRACK_ORDER_INVENTED=true",
        "P7_3_STATUS=SLICE_CLOSED_RESIDUAL_FAIL_CLOSED",
        "P7_3_SLICE=CLOSED",
        "P7_3_SLICE_REOPENED=false",
        "P7_3_RESIDUAL=UNRESOLVED_FAIL_CLOSED",
        "QUERY_GRAMMAR_STATUS=PROVEN",
        "OMIT_VS_ZERO_SEMANTICS_STATUS=PROVEN",
        "SPECIFIC_INSTID_ZERO_ELICITATION_AUTHORITY_STATUS=PROVEN_CONDITIONAL_ON_PREVIOUS_POSITION_AND_VALID_POSID",
        "CURRENT_SUI_ZERO_STATE_STATUS=UNPROVEN",
        "P7_3_FLATTEN_PRECONDITION_STATUS=UNRESOLVED_FAIL_CLOSED",
        "NEXT_PROOF_PATH=NO_EXISTING_PROOF_PATH_STOP_BECAUSE_INSTID_PRECONDITIONS_ARE_NOT_ESTABLISHED",
        "NO_SAFE_HIGHER_VALUE_RUNTIME_PROOF_PATH_CURRENTLY_AVAILABLE=true",
        "DO_NOT_REPEAT_FILTERED_INSTID_GET_AS_PROOF=true",
        "ABSENT_DOES_NOT_PROVE_ZERO=true",
        "ABSENT_DOES_NOT_PROVE_NEVER_HELD=true",
        "EMPTY_EQUALS_ZERO=false",
        "P8_STATUS=PERSISTED_FORENSIC_PASS_NOT_LIVE_READY",
        "P8_PASS_DOES_NOT_MEAN_LIVE_READY=true",
        "P8_PASS_IS_NOT_LIVE_READY=true",
        "FERTIG_B=false",
        "LIVE_READY=false",
        "FACE_VALUE_STATUS=SUPERSEDED_AS_NEXT_STEP_BLOCKER_DOCUMENTARY_OPEN_QUARANTINED",
        "FACE_VALUE_AS_NEXT_BLOCKER=SUPERSEDED",
        "FACE_VALUE_CONFLICT_AS_DOCUMENTARY_CONFLICT=OPEN_QUARANTINED",
        "FACE_VALUE_CONFLICT_RESOLVED_GLOBALLY=false",
        "FACE_VALUE_IS_NOT_FULLY_CLOSED=true",
        "SETTLEMENT_PNL_STATUS=NOT_RELEVANT_TO_NEXT_STEP_UNPROVEN_RESIDUAL",
        "SETTLEMENT_PNL_AS_NEXT_BLOCKER=NOT_RELEVANT",
        "SETTLEMENT_PNL=UNPROVEN",
        "USD_USDC_OPERATOR_STATUS=UNRESOLVED_OPTIONAL_P6_NOT_MANDATORY_NEXT",
        "USD_USDC_OPERATOR=OPTIONAL_P6_UNPROVEN_NOT_MANDATORY_NEXT",
        "P6_STATUS=NOT_EXECUTED",
        "P6_CLASS=OPTIONAL",
        "SECTION_22_IMMEDIATE_NEXT_ROLE=HISTORICAL_SUPERSEDED_DO_NOT_FOLLOW",
        "SECTION_22_LAST_CLOSED_Z2K_POINTER_IS_NOT_CURRENT=true",
        "SECTION_22_COVER_USDC_NEXT_POINTER_IS_NOT_CURRENT=true",
        "SECTION_22_HISTORICAL_SNAPSHOT_PRESERVED=true",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "FORENSIC_WORKSTREAM_TOUCHED=false",
        "FORENSIC_SOURCE_IMPORTED=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "Z2CF_PERSIST_IS_NOT_TRACK_SELECTION=true",
        "Z2CF_PERSIST_DOES_NOT_REOPEN_P7_3=true",
        "Z2CF_PERSIST_DOES_NOT_TREAT_6058_AS_NORMAL_Z2_PROGRESS=true",
        "Z2CE_UNCHANGED=true",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "CURRENT_CANONICAL_INSTRUMENT=SUI-USD_UM_XPERP-310404",
        "NOT_AUTHORIZED_GLOBAL_UNIQUE_CANONICAL_NEXT_STEP_NONE_BY_P3_POLICY",
    )
    for marker in required:
        assert marker in section, f"missing Z2CF marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nEMPTY_EQUALS_ZERO=true\n",
        "\nTARGET_POSITION_ZERO_PROVEN=true\n",
        "\nCURRENT_SUI_ZERO_STATE_STATUS=PROVEN\n",
        "\nP7_3_SLICE_REOPENED=true\n",
        "\nZ2CA_REINTERPRETED=true\n",
        "\nZ2CE_TEXT_REWRITTEN=true\n",
        "\nFERTIG_B=true\n",
        "\nLIVE_READY=true\n",
        "\nFACE_VALUE_CONFLICT_RESOLVED_GLOBALLY=true\n",
        "\nFORENSIC_SOURCE_IMPORTED=true\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nBTC_EVIDENCE_PROMOTED_TO_SUI=true\n",
        "\nNONE_BY_P3_POLICY_DOES_NOT_MEAN_NO_OPEN_TRACKS=false\n",
        "\nNO_PARALLEL_TRACK_ORDER_INVENTED=false\n",
        "\nPR_6058_DOES_NOT_CREATE_NEW_NORMAL_NEXT_POINTER=false\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2CF marker present: {marker!r}"


def test_section_22_is_marked_historical_without_deleting_z2k_snapshot() -> None:
    section = _section_22(_read(MASTER_RUNBOOK))
    assert "SECTION_22_IMMEDIATE_NEXT_ROLE=HISTORICAL_SUPERSEDED_DO_NOT_FOLLOW" in section
    assert "SECTION_22_LAST_CLOSED_Z2K_POINTER_IS_NOT_CURRENT=true" in section
    assert "SECTION_22_COVER_USDC_NEXT_POINTER_IS_NOT_CURRENT=true" in section
    assert "HISTORICAL_SUPERSEDED_Z2K_ERA_SNAPSHOT; DO_NOT_FOLLOW" in section
    assert "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2K" in section
    assert (
        "CANONICAL_NEXT_STEP=OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_COVER_USDC_TERMS_AFTER_CURRENT_PUBLIC_TIER_MMR_BEFORE_FUNDING"
        in section
    )
    assert "CURRENT_FORENSIC_TRUTH_SHA=bc9c8f91465cf3a826c6a3d156d3a7599bf65403" in section
    assert "and is **not** a current Owner-GO." in section


def test_z2cf_map_of_truth_remains_navigation_only_without_z2cf_ssot_row() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "§11.13.5.Z2CF |" not in mot
    assert "§11.13.5.Z2CE |" not in mot
    assert "§11.13.5.Z2CD |" not in mot
