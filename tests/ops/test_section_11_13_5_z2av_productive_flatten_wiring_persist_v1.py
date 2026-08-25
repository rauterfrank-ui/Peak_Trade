"""§11.13.5.Z2AV productive flatten wiring persist.

Docs/governance invariants only. Records the wiring slice: dedicated
productive flatten transport, runner flatten_execute wiring, separate
flatten-execute authority, and full pre-send gate object. Does not prove
live flatten, does not consume Z2AP/Z2AR, and does not invent a unique
global next.
"""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    LIVE_FLATTEN_PROVABILITY_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
    LIVE_FLATTEN_PROVABILITY,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AV_HEADING = "### 11.13.5.Z2AV Productive live-flatten wiring persist"
Z2AU_HEADING = "### 11.13.5.Z2AU Offline Z2AP live-flatten construction and gate-binding persist"
Z2AW_HEADING = (
    "### 11.13.5.Z2AW Post-Z2AV productive flatten pre-execution same-pack GET evidence persist"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = (
    "SECTION_11_13_5_POST_Z2AU_PRODUCTIVE_LIVE_FLATTEN_WIRING_MAX_SAFE_SLICE_"
    "FAIL_CLOSED_NO_NETWORK_NO_GET_NO_POST_NO_EXECUTE"
)
BASELINE_SHA = "7085b6e76fef9036319f6d9a4bce0329e5493b02"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_SCOPED_NAMED_TRACK_OR_NAMED_CLASS_"
    "PROGRESSION_NOT_AUTHORIZED_BY_THIS_PERSIST_Z2AV_PRODUCTIVE_"
    "FLATTEN_WIRING_ONLY_GLOBAL_UNIQUE_CANONICAL_NEXT_STEP_NONE_BY_"
    "P3_POLICY_NO_Z2AP_CONSUME_NO_Z2AR_CONSUME_NO_FLATTEN_EXECUTE_"
    "NO_LIVE_WIRE_NO_SUI_REPROOF_NO_CANONICAL_REBIND_NO_GET_NO_POST_"
    "NO_ORDER_NO_FUNDING_NO_CANARY_NOT_AUTHORIZED"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2av_section(text: str) -> str:
    start = text.find(Z2AV_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AV heading"
    end = text.find(Z2AW_HEADING, start)
    assert end > start, "missing §11.13.5.Z2AW boundary after Z2AV"
    return text[start:end]


def test_z2av_heading_is_unique_and_follows_z2au() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AV_HEADING) == 1
    z2au = text.find(Z2AU_HEADING)
    z2av = text.find(Z2AV_HEADING)
    z2aw = text.find(Z2AW_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2au < z2av < z2aw < ladder


def test_z2av_docs_bind_wiring_slice_without_execution_or_track_consumption() -> None:
    section = _z2av_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2AV_PRODUCTIVE_FLATTEN_WIRING_FAIL_CLOSED_NO_NETWORK_NO_GET_NO_POST_NO_EXECUTE_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "PERSIST_CLASS=WIRING_IMPLEMENTATION_PLUS_SSOT_PERSIST",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "Z2AS_REMAINS_P3_POLICY_BASIS=true",
        "Z2AS_TEXT_REWRITTEN=false",
        "Z2AP_TEXT_REWRITTEN=false",
        "Z2AR_TEXT_REWRITTEN=false",
        "Z2AU_TEXT_REWRITTEN=false",
        "Z2AP_CONSUMED=false",
        "Z2AR_CONSUMED=false",
        "P3_INDEPENDENT_PARALLEL_TRACKS_POLICY=true",
        "GLOBAL_UNIQUE_CANONICAL_NEXT_STEP=NONE_BY_P3_POLICY",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "PRODUCTIVE_FLATTEN_PATH_STRUCTURALLY_REACHABLE=true",
        "PRODUCTIVE_WIRE_SEND_WITHOUT_FULL_RUNTIME_GATES=false",
        "PRODUCTIVE_WIRE_SEND_WITHOUT_SEPARATE_FLATTEN_EXECUTE_AUTHORITY=false",
        "NETWORK_USED_DURING_SLICE=false",
        "GET_EXECUTED_THIS_STEP=false",
        "POST_EXECUTED=false",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "PRODUCTIVE_PROOF_EXECUTED=false",
        "STRUCTURALLY_REACHABLE_NE_PRODUCTIVELY_PROVEN=true",
        "DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=false",
        "B8_MANDATORY=true",
        "REDUCE_ONLY_MANDATORY=true",
        "LIMIT_ONLY_MANDATORY=true",
        "FRESHNESS_5000MS_MANDATORY=true",
        "ONE_SHOT_NO_RETRY=true",
        "DUPLICATE_POST_PROTECTION=true",
        "POST_SUBMIT_PROOF_CONTRACT_PRESERVED=true",
        "DEFAULT_PRODUCTIVE_SEND_DENIED=true",
        "NO_AUTONOMOUS_FLATTEN_TRIGGER=true",
        "THIS_OWNER_GO_IS_NOT_FLATTEN_EXECUTE_TOKEN=true",
        "NO_FLATTEN_EXECUTE_GO_INVENTED_BY_THIS_PERSIST=true",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "HARD_STOP_AFTER_THIS_TASK=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2AV marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nCAN_SUBMIT_ORDER_TODAY=true\n",
        "\nPRODUCTIVE_PROOF_EXECUTED=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nZ2AR_CONSUMED=true\n",
        "\nGET_EXECUTED_THIS_STEP=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nDEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=true\n",
        "\nFLATTEN_EXECUTION=true\n",
        "\nNETWORK_USED_DURING_SLICE=true\n",
        "\nPRODUCTIVE_WIRE_SEND_WITHOUT_FULL_RUNTIME_GATES=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AV marker present: {marker!r}"
    assert LIVE_FLATTEN_PROVABILITY == LIVE_FLATTEN_PROVABILITY_STATUS == "UNPROVEN"
    assert DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False
    assert FRESHNESS_THRESHOLD_MS == 5000


def test_z2av_map_of_truth_remains_navigation_only_without_z2av_ssot_row() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "§11.13.5.Z2AV |" not in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}\n" not in mot
