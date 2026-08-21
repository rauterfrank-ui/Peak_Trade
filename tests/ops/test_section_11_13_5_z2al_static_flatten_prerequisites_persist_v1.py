"""§11.13.5.Z2AL static flatten prerequisite implementation persist.

Docs/governance invariants only. Records quote-locked LIMIT flatten
price policy and dedicated flatten transport. Does not prove live
flatten, does not enable live wire, does not raise ORDER_COUNT_LIMIT
to 2, and does not authorize GET/POST/order/funding/Canary.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AL_HEADING = "### 11.13.5.Z2AL Static flatten price policy and dedicated flatten transport"
Z2AK_HEADING = "### 11.13.5.Z2AK LF-11 and LF-12 read-only adjudication persist"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_OR_ADJUDICATION_"
    "STEP_NOT_AUTHORIZED_BY_THIS_IMPLEMENTATION_Z2AL_STATIC_FLATTEN_"
    "PREREQUISITES_PASS_OFFLINE_LIVE_FLATTEN_UNPROVEN_NO_LIVE_WIRE_NO_"
    "ORDER_COUNT_LIMIT_RAISE_TO_2_NO_RUNTIME_READ_NO_PRODUCTIVE_FLATTEN_"
    "NO_GET_NO_ORDER_NO_ALLOWLIST_CANARY_NOT_AUTHORIZED_SUPPORT_CONTACT_"
    "NOT_AUTHORIZED"
)
OWNER_GO = "GRANTED_FOR_STATIC_FLATTEN_PREREQUISITES_IMPLEMENTATION_ONLY"
BASELINE_SHA = "a8c29cd94513431aaf93db8844e62c1ede388884"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2al_section(text: str) -> str:
    start = text.find(Z2AL_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AL heading"
    end = text.find("## 11.14 Live order and economic evidence ladder", start)
    assert end > start, "missing §11.14 boundary after Z2AL"
    return text[start:end]


def test_z2al_heading_is_unique_and_follows_z2ak() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AL_HEADING) == 1
    z2ak = text.find(Z2AK_HEADING)
    z2al = text.find(Z2AL_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2ak < z2al < ladder


def test_z2al_docs_bind_static_prerequisites_without_live_flatten_proven() -> None:
    section = _z2al_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=STATIC_FLATTEN_PREREQUISITES_IMPLEMENTATION_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "LAST_CANONICALLY_CLOSED_STEP=LF_12",
        "FLATTEN_PRICE_POLICY_IMPLEMENTED=true",
        "FLATTEN_PRICE_POLICY_FULLY_BOUND=false",
        "DEDICATED_FLATTEN_TRANSPORT_IMPLEMENTED=true",
        "DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=false",
        "REDUCE_ONLY_FLATTEN_INTENT_IMPLEMENTED=true",
        "STATIC_FLATTEN_PREREQUISITES_STATUS=PASS_OFFLINE",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "LIVE_FLATTEN_PROVABILITY_REMAINS=UNPROVEN_HARD_STOP",
        "PRODUCTIVE_FLATTEN_EXECUTED=false",
        "MARKET_PATH_AVAILABLE=false",
        "CLOSE_POSITION_ENDPOINT_ALLOWLISTED=false",
        "ORDER_COUNT_LIMIT=1",
        "ORDER_COUNT_LIMIT_RAISED=false",
        "POSITION_COUNT_LIMIT=1",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "GET_EXECUTED_THIS_STEP=false",
        "AUTHENTICATED_REQUEST_PERFORMED=false",
        "POST_EXECUTED=false",
        "NO_PRODUCTIVE_WIRE=true",
        "FRESHNESS_THRESHOLD_CANONICAL_DEFAULT=NONE_FAIL_CLOSED_IF_ABSENT",
        "FLATTEN_SUBMIT_ENDPOINT=POST_&#47;api&#47;v5&#47;trade&#47;order",
        "ENTRY_TRANSPORT_REMAINS_SEPARATE=true",
        "OVERSIZE_REJECTED=true",
        "ZERO_POSITION_REJECTED=true",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY",
        "HARD_STOP_AFTER_THIS_TASK=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2AL marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nORDER_COUNT_LIMIT=2\n",
        "\nORDER_COUNT_LIMIT_RAISED=true\n",
        "\nCLOSE_POSITION_ENDPOINT_ALLOWLISTED=true\n",
        "\nMARKET_PATH_AVAILABLE=true\n",
        "\nDEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=true\n",
        "\nPRODUCTIVE_FLATTEN_EXECUTED=true\n",
        "\nGET_EXECUTED_THIS_STEP=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AL marker present: {marker!r}"


def test_z2al_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "§11.13.5.Z2AL |" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AL" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AM" in mot
    assert "FLATTEN_PRICE_POLICY_IMPLEMENTED=true" in mot
    assert "DEDICATED_FLATTEN_TRANSPORT_IMPLEMENTED=true" in mot
    assert "STATIC_FLATTEN_PREREQUISITES_STATUS=PASS_OFFLINE" in mot
    assert "LIVE_FLATTEN_PROVABILITY=UNPROVEN" in mot
    assert "LAST_CANONICALLY_CLOSED_STEP=LF_12" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    snapshot_pointer_lines = [
        ln for ln in mot.splitlines() if ln.startswith("NEXT_CANONICAL_STEP_POINTER=")
    ]
    assert snapshot_pointer_lines[-1] != f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}"
    current_pointer = snapshot_pointer_lines[-1].split("=", 1)[1]
    assert "Z2AL_STATIC_FLATTEN_PREREQUISITES" not in current_pointer
    assert "Z2AP_OFFLINE_POST_ACTION_PROOF_CONTRACT_BOUND" in current_pointer
    assert "NO_CANONICAL_FRESHNESS_DEFAULT" not in current_pointer
    assert "NO_LIVE_WIRE" in current_pointer
    assert "NO_ORDER_COUNT_LIMIT_RAISE_TO_2" in current_pointer
