"""§11.13.5.Z2CE P7.3 first-party zero-semantics persist.

Docs/governance invariants only. Records proven venue query-grammar
and omit-versus-zero semantics without closing current SUI zero,
flatten precondition, P7.4, Cover, live, testnet, or canary. Does not
rewrite Z2CD or Z2CA. Does not infer never-held or current-zero from
absent evidence.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2CD_HEADING = "### 11.13.5.Z2CD Post-Z2CC P8 final forensic audit persist"
Z2CE_HEADING = (
    "### 11.13.5.Z2CE Post-Z2CD P7.3 first-party query-grammar and "
    "zero-elicitation semantics persist"
)
Z2CF_HEADING = (
    "### 11.13.5.Z2CF Post-Z2CE / post-#6058 normal-system next-pointer adjudication persist"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = (
    "SECTION_11_13_5_POST_Z2CD_P7_3_EXTERNAL_FIRST_PARTY_ZERO_SEMANTICS_ADJUDICATION_PERSIST_ONLY"
)
BASELINE_SHA = "f953f5a76885fa7f6adecfd2c8253642d72d65dd"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2ce_section(text: str) -> str:
    start = text.find(Z2CE_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CE heading"
    end = text.find(Z2CF_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CF boundary after Z2CE"
    return text[start:end]


def _z2cd_section(text: str) -> str:
    start = text.find(Z2CD_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CD heading"
    end = text.find(Z2CE_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CE boundary after Z2CD"
    return text[start:end]


def test_z2ce_heading_is_unique_and_follows_z2cd() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CE_HEADING) == 1
    z2cd = text.find(Z2CD_HEADING)
    z2ce = text.find(Z2CE_HEADING)
    z2cf = text.find(Z2CF_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2cd < z2ce < z2cf < ladder


def test_z2cd_historical_slice_was_not_rewritten() -> None:
    section = _z2cd_section(_read(MASTER_RUNBOOK))
    assert "P8_FINAL_FORENSIC_AUDIT_STATUS=PASS" in section
    assert "P7_3_FLATTEN_PRECONDITION_STATUS=UNRESOLVED_FAIL_CLOSED" in section
    assert "EMPTY_EQUALS_ZERO=false" in section
    assert "LIVE_AUTHORIZED=false" in section
    assert "Z2CE" not in section


def test_z2ce_docs_bind_first_party_semantics_without_current_sui_zero() -> None:
    section = _z2ce_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CE_POST_Z2CD_P7_3_EXTERNAL_FIRST_PARTY_ZERO_SEMANTICS_ADJUDICATION_PERSIST_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "PERSIST_CLASS=Z2CE_P7_3_FIRST_PARTY_ZERO_SEMANTICS_SSOT_PERSIST_DOCS_ONLY",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "ORIGIN_MAIN_SUPERSESSION_STATUS=NONE",
        "PREDECESSOR_SLICE=11.13.5.Z2CD",
        f"PREDECESSOR_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "Z2CD_TEXT_REWRITTEN=false",
        "Z2CA_TEXT_REWRITTEN=false",
        "CHAT_TRANSCRIPT_AUTHORITY=NONE",
        "QUERY_GRAMMAR_STATUS=PROVEN",
        "CAN_QUERY_GRAMMAR_BE_CLOSED_WITHOUT_RUNTIME=true",
        "OMIT_VS_ZERO_SEMANTICS_STATUS=PROVEN",
        "CAN_OMIT_VS_ZERO_SEMANTICS_BE_CLOSED_WITHOUT_RUNTIME=true",
        "EMPTY_EQUALS_ZERO=false",
        "UNFILTERED_EMPTY_SEMANTICS_STATUS=TARGET_INSTRUMENT_NOT_OBSERVED_NOT_TARGET_POSITION_ZERO",
        "FIRST_PARTY_EN_INSTID_ZERO_RULE_STATUS=PRESENT_CONFIRMED",
        "FIRST_PARTY_ZH_INSTID_ZERO_RULE_STATUS=PRESENT_CONFIRMED",
        "SPECIFIC_INSTID_ZERO_ELICITATION_AUTHORITY_STATUS=PROVEN_CONDITIONAL_ON_PREVIOUS_POSITION_AND_VALID_POSID",
        "CAN_INSTID_ZERO_ELICITATION_RULE_BE_CLOSED_WITHOUT_RUNTIME=true",
        "IS_PREVIOUSLY_HELD_A_DOCUMENTED_PRECONDITION_FOR_INSTID_ZERO_RETURN=true",
        "IS_VALID_POSID_A_DOCUMENTED_PRECONDITION_FOR_INSTID_ZERO_RETURN=true",
        "DOES_CLIENT_NEED_TO_KNOW_POSID_FOR_INSTID_PATH=false",
        "EXPLICIT_POSID_CLOSED_ELICITATION_AUTHORITY_STATUS=PROVEN",
        "ISOLATED_MARGIN_POS_ZERO_MUST_NOT_TRANSFER_TO_SUI_XPERP=true",
        "TRICK_EN_MUST_NOT_NEGATE_GET_POSITIONS_INSTID_ZERO_RULE=true",
        "TARGET_INSTRUMENT=SUI-USD_UM_XPERP-310404",
        "TARGET_INSTRUMENT_NOT_OBSERVED=true",
        "TARGET_POSITION_ZERO_PROVEN=false",
        "Z2CA_REINTERPRETED=false",
        "SUI_EVER_OPENED_OR_HELD_CANONICAL_EVIDENCE_STATUS=ABSENT",
        "SUI_VALID_OR_POTENTIALLY_STILL_VALID_POSID_CANONICAL_EVIDENCE_STATUS=ABSENT",
        "ABSENT_HOLD_EVIDENCE_IS_NOT_NEVER_HELD=true",
        "ABSENT_HOLD_EVIDENCE_IS_NOT_CURRENT_ZERO=true",
        "CURRENT_SUI_ZERO_STATE_STATUS=UNPROVEN",
        "CAN_CURRENT_SUI_ZERO_STATE_BE_CLOSED_WITHOUT_RUNTIME=false",
        "DOES_FILTERED_INSTID_GET_HAVE_NEW_PROOF_VALUE_FOR_THIS_EXACT_SUI_TARGET=false",
        "P7_3_FLATTEN_PRECONDITION_STATUS=UNRESOLVED_FAIL_CLOSED",
        "POSITION_PROOF_GAP_CLASS=EXACT_TARGET_INSTID_ZERO_ROW_PRECONDITIONS_NOT_ESTABLISHED",
        "PRIOR_GAP_CLASS=QUERY_GRAMMAR_AND_ZERO_ELICITATION_SEMANTICS",
        "PRIOR_GAP_CLASS_STATUS=SUPERSEDED_NOT_JOINTLY_UNKNOWN",
        "PRIOR_CLAIM_SPECIFIC_INSTID_ZERO_ELICITATION_AUTHORITY_STATUS_NOT_PROVEN=SUPERSEDED",
        "PRIOR_CLAIM_ZERO_CLOSED_ROWS_DOCUMENTED_ONLY_THROUGH_EXPLICIT_POSID=SUPERSEDED",
        "NONE_OF_THOSE_PROPOSITIONS_PROVES_CURRENT_SUI_POSITION_ZERO=true",
        "NEXT_PROOF_PATH=NO_EXISTING_PROOF_PATH_STOP_BECAUSE_INSTID_PRECONDITIONS_ARE_NOT_ESTABLISHED",
        "P7_4_STATUS=CLOSED_FAIL_CLOSED_NO_MUTATION",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "ADAPTER_BEHAVIOR_CHANGED=false",
        "CONSUMER_BEHAVIOR_CHANGED=false",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "Z2CD_UNCHANGED=true",
        "Z2CA_UNCHANGED=true",
        "CURRENT_CANONICAL_INSTRUMENT=SUI-USD_UM_XPERP-310404",
    )
    for marker in required:
        assert marker in section, f"missing Z2CE marker: {marker}"
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
        "\nSUI_EVER_OPENED_OR_HELD_CANONICAL_EVIDENCE_STATUS=PROVEN\n",
        "\nZ2CA_REINTERPRETED=true\n",
        "\nZ2CD_TEXT_REWRITTEN=true\n",
        "\nCONSUMER_BEHAVIOR_CHANGED=true\n",
        "\nBTC_EVIDENCE_PROMOTED_TO_SUI=true\n",
        "\nSUI_POSID_INVENTED=true\n",
        "\nCHAT_TRANSCRIPT_AUTHORITY=SSOT\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2CE marker present: {marker!r}"
    assert "SPECIFIC_INSTID_ZERO_ELICITATION_AUTHORITY_STATUS=NOT_PROVEN" not in section
    assert "POSITION_PROOF_GAP_CLASS=QUERY_GRAMMAR_AND_ZERO_ELICITATION_SEMANTICS" not in section


def test_z2ce_map_of_truth_remains_navigation_only_without_z2ce_ssot_row() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "§11.13.5.Z2CE |" not in mot
    assert "§11.13.5.Z2CD |" not in mot
    assert "§11.13.5.Z2CF |" not in mot
