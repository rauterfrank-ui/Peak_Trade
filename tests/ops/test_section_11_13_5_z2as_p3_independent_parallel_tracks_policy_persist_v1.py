"""§11.13.5.Z2AS P3 independent-parallel-tracks policy persist.

Docs/governance invariants only. Records the owner-ratified P3
selection semantic: Z2AP productive live-flatten proof and Z2AR SUI
successor/reproof remain independent parallel open tracks. Does not
select a unique global next, does not rank either track, does not
execute flatten or SUI reproof, and does not authorize GET/POST/order/
funding/Canary or Map-of-Truth mutation.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AS_HEADING = "### 11.13.5.Z2AS Owner P3 independent parallel tracks selection-semantics persist"
Z2AR_HEADING = "### 11.13.5.Z2AR SUI successor public evidence pack and reproof boundary persist"
Z2AP_HEADING = (
    "### 11.13.5.Z2AP Post-Z2AO live-flatten closure work package to next safety boundary"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_SCOPED_NAMED_TRACK_OR_NAMED_CLASS_"
    "PROGRESSION_NOT_AUTHORIZED_BY_THIS_PERSIST_Z2AS_P3_INDEPENDENT_"
    "PARALLEL_TRACKS_POLICY_ONLY_GLOBAL_UNIQUE_CANONICAL_NEXT_STEP_NONE_"
    "BY_P3_POLICY_NO_Z2AP_PRIORITY_NO_Z2AR_PRIORITY_NO_FLATTEN_EXECUTE_"
    "NO_SUI_REPROOF_NO_SUI_CLASS_SELECTION_NO_CANONICAL_REBIND_NO_GET_"
    "NO_POST_NO_ORDER_NO_LIVE_WIRE_NO_FUNDING_NO_CANARY_NOT_AUTHORIZED"
)
OWNER_GO = "P3_INDEPENDENT_PARALLEL_TRACKS_POLICY_PERSIST_ONLY"
BASELINE_SHA = "56cb70e91603a118ec98966d197a3533b5e52ea8"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2as_section(text: str) -> str:
    start = text.find(Z2AS_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AS heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2AS"
    return text[start:end]


def test_z2as_heading_is_unique_and_follows_z2ar() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AS_HEADING) == 1
    z2ap = text.find(Z2AP_HEADING)
    z2ar = text.find(Z2AR_HEADING)
    z2as = text.find(Z2AS_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2ap < z2ar < z2as < ladder


def test_z2as_docs_bind_p3_parallel_tracks_without_unique_next_or_execution() -> None:
    section = _z2as_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_P3_INDEPENDENT_PARALLEL_TRACKS_POLICY_PERSIST_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "POLICY_IS_NEW_OWNER_POLICY=true",
        "OWNER_POLICY_SELECTION=P3_INDEPENDENT_PARALLEL_TRACKS",
        "P3_INDEPENDENT_PARALLEL_TRACKS_POLICY=true",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "PARALLEL_TO_SECTION_11_13_5_Z2AP=true",
        "PARALLEL_TO_SECTION_11_13_5_Z2AR=true",
        "Z2AP_PRODUCTIVE_FLATTEN_NEXT_POINTER_CONSUMED_AS_FLATTEN_PROOF=false",
        "Z2AR_FURTHER_SUI_PROOF_NEXT_POINTER_CONSUMED_AS_SUI_PROOF=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "TARGET_AUTHORITY_OF_TEMPORARY_FORENSIC_WORKING_RUNBOOK=NONE",
        "LAST_CANONICALLY_CLOSED_STEP=LF_12",
        "TRACK_RELATION=INDEPENDENT_PARALLEL",
        "GLOBAL_UNIQUE_CANONICAL_NEXT_STEP=NONE_BY_P3_POLICY",
        "GLOBAL_POINTER_PRECEDENCE=NONE_BY_P3_POLICY",
        "SCOPED_OWNER_GO_MAY_PROGRESS_NAMED_TRACK=true",
        "PROGRESS_ONE_TRACK_AFFECTS_OTHER_TRACK=false",
        "Z2AP_TRACK_STATUS=OPEN_UNCONSUMED",
        "Z2AR_SUI_TRACK_STATUS=OPEN_UNCONSUMED",
        "Z2AP_POINTER_CONSUMED=false",
        "Z2AR_SUI_POINTER_CONSUMED=false",
        "SUI_REPROOF_REQUIREMENTS_REMAIN_UNRANKED=true",
        "REPROOF_REQUIREMENTS_ARE_NOT_EXECUTION_ORDER=true",
        "SUI_REPROOF_CLASS_SELECTED=false",
        "SUI_REPROOF_CLASSES_RANKED=false",
        "Z2AP_NOT_PRIORITIZED_BY_THIS_POLICY=true",
        "Z2AR_SUI_NOT_PRIORITIZED_BY_THIS_POLICY=true",
        "DOES_NOT_ESTABLISH_PRECEDENCE_OVER_OTHER_TRACK=true",
        "SUCCESSOR_CONSUMPTION_REQUIRES_EXPLICIT_CANONICAL_BINDING=true",
        "SUI_SELECTED_AS_CURRENT_CANONICAL_INSTRUMENT=false",
        "SUI_CANONICAL_REBIND_EXECUTED=false",
        "DEFAULT_INSTRUMENT_ID_CHANGED=false",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "BTC_PRODUCTIVE_PROOF=DO_NOT_RUN",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "PRODUCTIVE_LIVE_FLATTEN_PROOF_EXECUTED=false",
        "GET_EXECUTED_THIS_STEP=false",
        "POST_EXECUTED=false",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "SECTION_LOCAL_CANONICAL_NEXT_STEP_ROLE="
        "RESIDUAL_AUTHORIZATION_BOUNDARY_OF_THIS_PERSIST_NOT_GLOBAL_UNIQUE_NEXT",
        "HARD_STOP_AFTER_THIS_TASK=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2AS marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nBTC_PRODUCTIVE_PROOF=RUN\n",
        "\nSUI_REPROOF_CLASS_SELECTED=true\n",
        "\nSUI_REPROOF_CLASSES_RANKED=true\n",
        "\nSUI_SELECTED_AS_CURRENT_CANONICAL_INSTRUMENT=true\n",
        "\nSUI_CANONICAL_REBIND_EXECUTED=true\n",
        "\nDEFAULT_INSTRUMENT_ID_CHANGED=true\n",
        "\nZ2AP_POINTER_CONSUMED=true\n",
        "\nZ2AR_SUI_POINTER_CONSUMED=true\n",
        "\nZ2AP_PRODUCTIVE_FLATTEN_NEXT_POINTER_CONSUMED_AS_FLATTEN_PROOF=true\n",
        "\nZ2AR_FURTHER_SUI_PROOF_NEXT_POINTER_CONSUMED_AS_SUI_PROOF=true\n",
        "\nPRODUCTIVE_LIVE_FLATTEN_PROOF_EXECUTED=true\n",
        "\nGET_EXECUTED_THIS_STEP=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nPROGRESS_ONE_TRACK_AFFECTS_OTHER_TRACK=true\n",
        "\nZ2AP_NOT_PRIORITIZED_BY_THIS_POLICY=false\n",
        "\nZ2AR_SUI_NOT_PRIORITIZED_BY_THIS_POLICY=false\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AS marker present: {marker!r}"
    assert "GLOBAL_UNIQUE_CANONICAL_NEXT_STEP=NONE_BY_P3_POLICY" in section
    assert "TRACK_RELATION=INDEPENDENT_PARALLEL" in section


def test_z2as_map_of_truth_remains_navigation_only_without_z2as_ssot_row() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "§11.13.5.Z2AS |" not in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}\n" not in mot
