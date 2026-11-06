"""§11.13.5.Z2AP live-flatten closure work-package persist.

Docs/governance plus offline post-action proof contract. Records that
pre-execution flatten prerequisites are closed and only productive live
flatten proof remains. Does not prove live flatten, does not enable live
wire, and does not authorize GET/POST/order/funding/Canary.
"""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    OWNER_BINDING_STILL_REQUIRED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_action_proof_contract_v1 import (
    FLATTEN_POST_ACTION_PROOF_CONTRACT_IMPLEMENTED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AP_HEADING = (
    "### 11.13.5.Z2AP Post-Z2AO live-flatten closure work package to next safety boundary"
)
Z2AO_HEADING = (
    "### 11.13.5.Z2AO Post-Z2AN extra-deviation-bound offline read-only adjudication persist"
)
Z2AR_HEADING = "### 11.13.5.Z2AR SUI successor public evidence pack and reproof boundary persist"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_PRODUCTIVE_LIVE_FLATTEN_PROOF_NOT_"
    "AUTHORIZED_BY_THIS_CLOSURE_Z2AP_OFFLINE_POST_ACTION_PROOF_CONTRACT_"
    "BOUND_PRODUCTIVE_PROOF_READY_TRUE_LIVE_FLATTEN_UNPROVEN_NO_LIVE_WIRE_"
    "NO_ORDER_COUNT_LIMIT_RAISE_TO_2_NO_RUNTIME_READ_NO_PRODUCTIVE_FLATTEN_"
    "NO_GET_NO_ORDER_NO_ALLOWLIST_CANARY_NOT_AUTHORIZED_SUPPORT_CONTACT_NOT_"
    "AUTHORIZED"
)
OWNER_GO = "GRANTED_FOR_POST_Z2AO_LIVE_FLATTEN_CLOSURE_WORK_PACKAGE_TO_NEXT_SAFETY_BOUNDARY"
BASELINE_SHA = "e381ad877f62200f538b23206240485bbcdf94a6"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2ap_section(text: str) -> str:
    start = text.find(Z2AP_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AP heading"
    end = text.find(Z2AR_HEADING, start)
    assert end > start, "missing §11.13.5.Z2AR boundary after Z2AP"
    return text[start:end]


def test_z2ap_heading_is_unique_and_follows_z2ao() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AP_HEADING) == 1
    z2ao = text.find(Z2AO_HEADING)
    z2ap = text.find(Z2AP_HEADING)
    z2ar = text.find(Z2AR_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2ao < z2ap < z2ar < ladder


def test_z2ap_docs_bind_productive_proof_ready_without_live_flatten_proven() -> None:
    section = _z2ap_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=POST_Z2AO_LIVE_FLATTEN_CLOSURE_WORK_PACKAGE_TO_NEXT_SAFETY_BOUNDARY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "LAST_CANONICALLY_CLOSED_STEP=LF_12",
        "TERMINAL_CLASS=B",
        "PRODUCTIVE_PROOF_READY=true",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "FLATTEN_POST_ACTION_PROOF_CONTRACT_IMPLEMENTED=true",
        "EXTRA_DEVIATION_BOUND_REQUIRED=false",
        "OWNER_BINDING_STILL_REQUIRED=LIVE_WIRE_AND_PRODUCTIVE_FLATTEN_SEPARATE_OWNER_GO",
        "DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=false",
        "ORDER_COUNT_LIMIT=1",
        "GET_EXECUTED_THIS_STEP=false",
        "POST_EXECUTED=false",
        "MINIMUM_MISSING_DISCRIMINATING_EVIDENCE=PRODUCTIVE_LIVE_FLATTEN_PROOF_SEPARATE_OWNER_GO",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY",
        "HARD_STOP_AFTER_THIS_TASK=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2AP marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nORDER_COUNT_LIMIT=2\n",
        "\nGET_EXECUTED_THIS_STEP=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nDEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=true\n",
        "\nEXTRA_DEVIATION_BOUND_REQUIRED=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AP marker present: {marker!r}"


def test_z2ap_code_constants_match_ssot() -> None:
    assert FLATTEN_POST_ACTION_PROOF_CONTRACT_IMPLEMENTED is True
    assert DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False
    assert OWNER_BINDING_STILL_REQUIRED == "LIVE_WIRE_AND_PRODUCTIVE_FLATTEN_SEPARATE_OWNER_GO"


def test_z2ap_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "§11.13.5.Z2AP |" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AP" in mot
    assert "TERMINAL_CLASS=B" in mot
    assert "PRODUCTIVE_PROOF_READY=true" in mot
    assert "FLATTEN_POST_ACTION_PROOF_CONTRACT_IMPLEMENTED=true" in mot
    assert "LIVE_FLATTEN_PROVABILITY=UNPROVEN" in mot
    assert "LAST_CANONICALLY_CLOSED_STEP=LF_12" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    snapshot_pointer_lines = [
        ln for ln in mot.splitlines() if ln.startswith("NEXT_CANONICAL_STEP_POINTER=")
    ]
    assert snapshot_pointer_lines[-1] == f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}"
    current_pointer = snapshot_pointer_lines[-1].split("=", 1)[1]
    assert "Z2AO_EXTRA_DEVIATION_BOUND_NOT_REQUIRED" not in current_pointer
    assert "Z2AP_OFFLINE_POST_ACTION_PROOF_CONTRACT_BOUND" in current_pointer
    assert "PRODUCTIVE_PROOF_READY_TRUE" in current_pointer
    assert "NO_LIVE_WIRE" in current_pointer
    assert "NO_ORDER_COUNT_LIMIT_RAISE_TO_2" in current_pointer
    assert "NO_PRODUCTIVE_FLATTEN" in current_pointer
