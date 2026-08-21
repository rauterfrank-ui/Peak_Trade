"""§11.13.5.Z2AO extra-deviation-bound offline adjudication persist.

Docs/governance invariants only. Records that a separate extra-deviation
bound is not required for the dedicated quote-locked flatten LIMIT
contract after Z2AN. Does not invent a numeric collar, does not prove
live flatten, does not enable live wire, and does not authorize
GET/POST/order/funding/Canary.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AO_HEADING = (
    "### 11.13.5.Z2AO Post-Z2AN extra-deviation-bound offline read-only adjudication persist"
)
Z2AN_HEADING = "### 11.13.5.Z2AN Flatten FRESHNESS_THRESHOLD_MS Owner-policy ratification"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_OR_ADJUDICATION_"
    "STEP_NOT_AUTHORIZED_BY_THIS_PERSIST_Z2AO_EXTRA_DEVIATION_BOUND_NOT_"
    "REQUIRED_FOR_DEDICATED_FLATTEN_CONTRACT_QUOTE_LOCK_PLUS_TICK_PLUS_"
    "FRESHNESS_5000_SUFFICIENT_LIVE_FLATTEN_UNPROVEN_NO_LIVE_WIRE_NO_"
    "ORDER_COUNT_LIMIT_RAISE_TO_2_NO_RUNTIME_READ_NO_PRODUCTIVE_FLATTEN_"
    "NO_GET_NO_ORDER_NO_ALLOWLIST_CANARY_NOT_AUTHORIZED_SUPPORT_CONTACT_"
    "NOT_AUTHORIZED"
)
OWNER_GO = "GRANTED_FOR_POST_Z2AN_EXTRA_DEVIATION_BOUND_OFFLINE_READ_ONLY_ADJUDICATION_ONLY"
BASELINE_SHA = "be446c75606a4aa4d9a780108edaee6f57bbc667"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2ao_section(text: str) -> str:
    start = text.find(Z2AO_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AO heading"
    end = text.find("## 11.14 Live order and economic evidence ladder", start)
    assert end > start, "missing §11.14 boundary after Z2AO"
    return text[start:end]


def test_z2ao_heading_is_unique_and_follows_z2an() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AO_HEADING) == 1
    z2an = text.find(Z2AN_HEADING)
    z2ao = text.find(Z2AO_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2an < z2ao < ladder


def test_z2ao_docs_bind_extra_deviation_not_required_without_live_flatten_proven() -> None:
    section = _z2ao_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=POST_Z2AN_EXTRA_DEVIATION_BOUND_OFFLINE_READ_ONLY_ADJUDICATION_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "LAST_CANONICALLY_CLOSED_STEP=LF_12",
        "ADJUDICATED_DEPENDENCY=EXTRA_DEVIATION_BOUND",
        "ADJUDICATION_RESULT=C",
        "ADJUDICATION_CLASS=EXTRA_DEVIATION_BOUND_NOT_REQUIRED_FOR_THE_DEDICATED_FLATTEN_CONTRACT",
        "EXTRA_DEVIATION_BOUND_REQUIRED=false",
        "EXTRA_DEVIATION_BOUND_PROVEN=false",
        "EXTRA_DEVIATION_BOUND_VALUE=NONE",
        "REST_QUOTE_LOCK_SUFFICIENT_WITHOUT_EXTRA_BOUND=true",
        "OWNER_POLICY_REQUIRED=false",
        "OWNER_POLICY_DECISION_REQUIRED=NONE",
        "FIXTURE_VALUES_TREATED_AS_AUTHORITY=false",
        "FINITE_EXTRA_DEVIATION_BOUND=NOT_OWNER_RATIFIED_REJECTED",
        "Z2P_SLIPPAGE_RESERVE_NUMERIC_CLASS=COVER_ALGEBRA_NOT_FLATTEN_PX_GUARD",
        "FRESHNESS_THRESHOLD_MS=5000",
        "FLATTEN_PRICE_RULE=SELL_USES_BID_ROUND_DOWN_BUY_USES_ASK_ROUND_UP",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "NO_NUMERIC_INVENTION=true",
        "NO_IMPLEMENTATION_CHANGE=true",
        "GET_EXECUTED_THIS_STEP=false",
        "POST_EXECUTED=false",
        "MINIMUM_MISSING_DISCRIMINATING_EVIDENCE=NONE_FOR_EXTRA_DEVIATION_BOUND",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY",
        "HARD_STOP_AFTER_THIS_TASK=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2AO marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nORDER_COUNT_LIMIT=2\n",
        "\nEXTRA_DEVIATION_BOUND_REQUIRED=true\n",
        "\nEXTRA_DEVIATION_BOUND_PROVEN=true\n",
        "\nOWNER_POLICY_REQUIRED=true\n",
        "\nFIXTURE_VALUES_TREATED_AS_AUTHORITY=true\n",
        "\nGET_EXECUTED_THIS_STEP=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nNO_IMPLEMENTATION_CHANGE=false\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AO marker present: {marker!r}"


def test_z2ao_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "§11.13.5.Z2AO |" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AO" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AP" in mot
    assert "ADJUDICATION_RESULT=C" in mot
    assert "EXTRA_DEVIATION_BOUND_REQUIRED=false" in mot
    assert "REST_QUOTE_LOCK_SUFFICIENT_WITHOUT_EXTRA_BOUND=true" in mot
    assert "LIVE_FLATTEN_PROVABILITY=UNPROVEN" in mot
    assert "LAST_CANONICALLY_CLOSED_STEP=LF_12" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    snapshot_pointer_lines = [
        ln for ln in mot.splitlines() if ln.startswith("NEXT_CANONICAL_STEP_POINTER=")
    ]
    assert snapshot_pointer_lines[-1] != f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}"
    current_pointer = snapshot_pointer_lines[-1].split("=", 1)[1]
    assert "Z2AN_FRESHNESS_THRESHOLD_MS_5000_OWNER_RATIFIED" not in current_pointer
    assert "Z2AO_EXTRA_DEVIATION_BOUND_NOT_REQUIRED" not in current_pointer
    assert "Z2AP_OFFLINE_POST_ACTION_PROOF_CONTRACT_BOUND" in current_pointer
    assert "NO_LIVE_WIRE" in current_pointer
    assert "NO_ORDER_COUNT_LIMIT_RAISE_TO_2" in current_pointer
    assert "NO_PRODUCTIVE_FLATTEN" in current_pointer
    assert "NO_RUNTIME_READ" in current_pointer
