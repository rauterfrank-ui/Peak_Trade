"""§11.13.5.Z2AU offline Z2AP flatten construction/gate-binding persist.

Docs/governance invariants only. Records the offline slice: B8 cap
bound on flatten, composed construction pipeline, and injected
post-submit evidence states. Does not prove live flatten, does not
consume Z2AP/Z2AR, and does not invent a unique global next.
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

Z2AU_HEADING = "### 11.13.5.Z2AU Offline Z2AP live-flatten construction and gate-binding persist"
Z2AT_HEADING = "### 11.13.5.Z2AT Post-B8 pre-submit open-position-cap SSOT persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_SCOPED_NAMED_TRACK_OR_NAMED_CLASS_"
    "PROGRESSION_NOT_AUTHORIZED_BY_THIS_PERSIST_Z2AU_OFFLINE_Z2AP_"
    "FLATTEN_CONSTRUCTION_AND_GATE_BINDING_ONLY_GLOBAL_UNIQUE_"
    "CANONICAL_NEXT_STEP_NONE_BY_P3_POLICY_NO_Z2AP_CONSUME_NO_Z2AR_"
    "CONSUME_NO_FLATTEN_EXECUTE_NO_LIVE_WIRE_NO_SUI_REPROOF_NO_"
    "CANONICAL_REBIND_NO_GET_NO_POST_NO_ORDER_NO_FUNDING_NO_CANARY_"
    "NOT_AUTHORIZED"
)
OWNER_GO = (
    "SECTION_11_13_5_Z2AP_PRODUCTIVE_LIVE_FLATTEN_PROVABILITY_NEXT_"
    "MAX_SAFE_SLICE_FAIL_CLOSED_NO_IMPLICIT_EXECUTE"
)
BASELINE_SHA = "05366731f23f95f210c6d6b442130b4d114d912e"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


Z2AV_HEADING = "### 11.13.5.Z2AV Productive live-flatten wiring persist"


def _z2au_section(text: str) -> str:
    start = text.find(Z2AU_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AU heading"
    end = text.find(Z2AV_HEADING, start)
    if end < 0:
        end = text.find(LADDER_HEADING, start)
    assert end > start, "missing Z2AV/§11.14 boundary after Z2AU"
    return text[start:end]


def test_z2au_heading_is_unique_and_follows_z2at() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AU_HEADING) == 1
    z2at = text.find(Z2AT_HEADING)
    z2au = text.find(Z2AU_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2at < z2au < ladder


def test_z2au_docs_bind_offline_slice_without_execution_or_track_consumption() -> None:
    section = _z2au_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2AU_OFFLINE_Z2AP_FLATTEN_CONSTRUCTION_AND_GATE_BINDING_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "PERSIST_CLASS=OFFLINE_IMPLEMENTATION_PLUS_SSOT_PERSIST",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "Z2AS_REMAINS_P3_POLICY_BASIS=true",
        "Z2AS_TEXT_REWRITTEN=false",
        "Z2AP_TEXT_REWRITTEN=false",
        "Z2AR_TEXT_REWRITTEN=false",
        "Z2AT_TEXT_REWRITTEN=false",
        "Z2AP_CONSUMED=false",
        "Z2AR_CONSUMED=false",
        "Z2AP_PRODUCTIVE_FLATTEN_NEXT_POINTER_CONSUMED_AS_FLATTEN_PROOF=false",
        "Z2AR_FURTHER_SUI_PROOF_NEXT_POINTER_CONSUMED_AS_SUI_PROOF=false",
        "P3_INDEPENDENT_PARALLEL_TRACKS_POLICY=true",
        "TRACK_RELATION=INDEPENDENT_PARALLEL",
        "GLOBAL_UNIQUE_CANONICAL_NEXT_STEP=NONE_BY_P3_POLICY",
        "GLOBAL_POINTER_PRECEDENCE=NONE_BY_P3_POLICY",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "LAST_CANONICALLY_CLOSED_STEP=LF_12",
        "OFFLINE_FLATTEN_REQUEST_CONSTRUCTION_AND_GATE_BINDING=PROVEN",
        "POST_SUBMIT_STATE_MACHINE_OFFLINE_PROOF=PROVEN_CONTRACT_ONLY",
        "B8_FLATTEN_TRANSPORT_CAP_BOUND=true",
        "DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=false",
        "LIVE_WIRE=false",
        "FRESHNESS_THRESHOLD_MS=5000",
        "ORDER_COUNT_LIMIT=1",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "PRODUCTIVE_PROOF_READY=true",
        "PRODUCTIVE_PROOF_EXECUTED=false",
        "POSITION_CLOSED_PROVEN_MEANS_INJECTED_SNAPSHOT_CONTRACT_ONLY=true",
        "MOCKS_ARE_NOT_VENUE_PROOF=true",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "CAN_SUBMIT_ORDER_TODAY=false",
        "GET_EXECUTED_THIS_STEP=false",
        "POST_EXECUTED=false",
        "NETWORK_REQUEST_EXECUTED=false",
        "ORDER_SUBMISSION=false",
        "FLATTEN_EXECUTION=false",
        "CANARY_EXECUTED=false",
        "TESTNET_ORDER_EXECUTED=false",
        "LIVE_ORDER_EXECUTED=false",
        "NEXT_EVIDENCE_REQUIRES_SEPARATE_EXECUTION_GO=true",
        "MAX_SAFE_OFFLINE_SLICE_AFTER_THIS_PERSIST=NONE",
        "Z2AP_TRACK_STATUS=OPEN_UNCONSUMED",
        "Z2AR_SUI_TRACK_STATUS=OPEN_UNCONSUMED",
        "NO_STRATEGY_LOGIC_CHANGE=true",
        "THIS_PERSIST_CREATES_NO_IMPLICIT_EXECUTE_GO=true",
        "OFFLINE_GATE_BINDING_NE_LIVE_FLATTEN_PROVABILITY=true",
        "INJECTED_POSITION_CLOSED_CONTRACT_NE_VENUE_CLOSURE=true",
        "Z2AU_SLICE_CONSUMED_NE_Z2AP_FLATTEN_PROOF_CONSUMED=true",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "SECTION_LOCAL_CANONICAL_NEXT_STEP_ROLE="
        "RESIDUAL_AUTHORIZATION_BOUNDARY_OF_THIS_PERSIST_NOT_GLOBAL_UNIQUE_NEXT",
        "HARD_STOP_AFTER_THIS_TASK=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2AU marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nCAN_SUBMIT_ORDER_TODAY=true\n",
        "\nPRODUCTIVE_PROOF_EXECUTED=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nZ2AR_CONSUMED=true\n",
        "\nZ2AP_PRODUCTIVE_FLATTEN_NEXT_POINTER_CONSUMED_AS_FLATTEN_PROOF=true\n",
        "\nZ2AR_FURTHER_SUI_PROOF_NEXT_POINTER_CONSUMED_AS_SUI_PROOF=true\n",
        "\nGET_EXECUTED_THIS_STEP=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nLIVE_WIRE=true\n",
        "\nDEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=true\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nCANARY_EXECUTED=true\n",
        "\nTESTNET_ORDER_EXECUTED=true\n",
        "\nLIVE_ORDER_EXECUTED=true\n",
        "\nFLATTEN_EXECUTION=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AU marker present: {marker!r}"
    assert LIVE_FLATTEN_PROVABILITY == LIVE_FLATTEN_PROVABILITY_STATUS == "UNPROVEN"
    assert DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False
    assert FRESHNESS_THRESHOLD_MS == 5000


def test_z2au_map_of_truth_remains_navigation_only_without_z2au_ssot_row() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "§11.13.5.Z2AU |" not in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}\n" not in mot
