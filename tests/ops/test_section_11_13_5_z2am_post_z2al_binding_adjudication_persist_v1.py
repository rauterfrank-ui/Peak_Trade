"""§11.13.5.Z2AM post-Z2AL Owner-binding adjudication persist.

Docs/governance invariants only. Persists the already-completed
read-only freshness and extra-deviation adjudication. Does not ratify a
numeric freshness default, does not invent 5000 ms / 5.0 s / 120 s as
flatten policy, does not ratify an extra deviation bound, does not
prove live flatten, and does not authorize GET/POST/order/funding/Canary.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AM_HEADING = "### 11.13.5.Z2AM Post-Z2AL read-only Owner-binding adjudication persist"
Z2AL_HEADING = "### 11.13.5.Z2AL Static flatten price policy and dedicated flatten transport"
Z2AK_HEADING = "### 11.13.5.Z2AK LF-11 and LF-12 read-only adjudication persist"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_OR_ADJUDICATION_"
    "STEP_NOT_AUTHORIZED_BY_THIS_PERSIST_Z2AM_FRESHNESS_BINDING_"
    "OWNER_RATIFICATION_REQUIRED_NO_CANONICAL_FRESHNESS_DEFAULT_EXTRA_"
    "DEVIATION_BOUND_NOT_PROVEN_REQUIRED_LIVE_FLATTEN_UNPROVEN_NO_"
    "NUMERIC_INVENTION_NO_LIVE_WIRE_NO_ORDER_COUNT_LIMIT_RAISE_TO_2_NO_"
    "RUNTIME_READ_NO_PRODUCTIVE_FLATTEN_NO_GET_NO_ORDER_NO_ALLOWLIST_"
    "CANARY_NOT_AUTHORIZED_SUPPORT_CONTACT_NOT_AUTHORIZED"
)
CONSUMED_Z2AL_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_OR_ADJUDICATION_"
    "STEP_NOT_AUTHORIZED_BY_THIS_IMPLEMENTATION_Z2AL_STATIC_FLATTEN_"
    "PREREQUISITES_PASS_OFFLINE_LIVE_FLATTEN_UNPROVEN_NO_LIVE_WIRE_NO_"
    "ORDER_COUNT_LIMIT_RAISE_TO_2_NO_RUNTIME_READ_NO_PRODUCTIVE_FLATTEN_"
    "NO_GET_NO_ORDER_NO_ALLOWLIST_CANARY_NOT_AUTHORIZED_SUPPORT_CONTACT_"
    "NOT_AUTHORIZED"
)
OWNER_GO = "GRANTED_FOR_POST_Z2AL_READ_ONLY_OWNER_BINDING_ADJUDICATION_SSOT_PERSIST_ONLY"
BASELINE_SHA = "c3672a3c79942d0fa17ef61d87547cc7743ae9a5"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2am_section(text: str) -> str:
    start = text.find(Z2AM_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AM heading"
    end = text.find("## 11.14 Live order and economic evidence ladder", start)
    assert end > start, "missing §11.14 boundary after Z2AM"
    return text[start:end]


def test_z2am_heading_is_unique_and_follows_z2al() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AM_HEADING) == 1
    z2ak = text.find(Z2AK_HEADING)
    z2al = text.find(Z2AL_HEADING)
    z2am = text.find(Z2AM_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2ak < z2al < z2am < ladder


def test_z2am_docs_bind_adjudication_without_numeric_invention() -> None:
    section = _z2am_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=POST_Z2AL_READ_ONLY_OWNER_BINDING_ADJUDICATION_SSOT_PERSIST_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "LAST_CANONICALLY_CLOSED_STEP=LF_12",
        "FLATTEN_PRICE_POLICY_IMPLEMENTED=true",
        "FLATTEN_PRICE_POLICY_FULLY_BOUND=false",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "LIVE_FLATTEN_PROVABILITY_REMAINS=UNPROVEN_HARD_STOP",
        "NEW_PROVEN_CLOSURE=NONE",
        "CLAIMS_NEWLY_PROVEN_THIS_STEP=NONE",
        "NO_NUMERIC_INVENTION=true",
        "NO_IMPLEMENTATION_CHANGE=true",
        "NO_TRADING_LOGIC_CHANGE=true",
        "FRESHNESS_BINDING=OWNER_RATIFICATION_REQUIRED",
        "FRESHNESS_PROVEN_EXISTING_THRESHOLD=NONE",
        "FRESHNESS_UNRATIFIED_POLICY=NO_CANONICAL_DEFAULT_REMAINS_EXPLICIT",
        "FRESHNESS_THRESHOLD_CANONICAL_DEFAULT=NONE_FAIL_CLOSED_IF_ABSENT",
        "FRESHNESS_CALLER_SUPPLIED_POSITIVE_INTEGER_MS_REQUIRED=true",
        "FRESHNESS_THRESHOLD_RATIFIED=false",
        "FRESHNESS_CANONICAL_DEFAULT=NONE",
        "TEST_FIXTURE_5000_PROMOTED_TO_POLICY=false",
        "MD_DEFAULT_5S_PROMOTED_TO_POLICY=false",
        "TESTNET_DEFAULT_120S_PROMOTED_TO_POLICY=false",
        "EXTRA_DEVIATION_BOUND=NOT_PROVEN_REQUIRED",
        "EXTRA_DEVIATION_SAFETY_INVARIANT=NOT_PROVEN",
        "EXTRA_DEVIATION_DEFENSE_IN_DEPTH=OPTIONAL_UNRATIFIED_CURRENTLY_REJECTED",
        "EXTRA_DEVIATION_COVERED_BY_QUOTE_LOCK_AND_TICK_ROUNDING=SELL_BID_ROUND_DOWN_BUY_ASK_ROUND_UP",
        "FLATTEN_PRICE_RULE=SELL_USES_BID_ROUND_DOWN_BUY_USES_ASK_ROUND_UP",
        "FINITE_EXTRA_DEVIATION_BOUND=NOT_OWNER_RATIFIED_REJECTED",
        "EXTRA_DEVIATION_BOUND_RATIFIED=false",
        "Z2P_SLIPPAGE_RESERVE_NUMERIC=0.00002",
        "Z2P_SLIPPAGE_RESERVE_NUMERIC_CLASS=COVER_ALGEBRA_NOT_FLATTEN_PX_GUARD",
        "MINIMUM_MISSING_DISCRIMINATING_EVIDENCE=OWNER_RATIFIED_FRESHNESS_THRESHOLD_MS_FOR_FLATTEN_QUOTE_LOCK",
        "NO_MISSING_EVIDENCE_CLAIMED_THAT_WOULD_PROVE_EXTRA_DEVIATION_BOUND_REQUIRED=true",
        "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "HARD_STOP_AFTER_THIS_TASK=true",
        "LIVE_AUTHORIZED=false",
        "GET_EXECUTED_THIS_PERSIST_STEP=false",
        "POST_EXECUTED=false",
        "ORDER_COUNT_LIMIT=1",
        "CLOSE_POSITION_ENDPOINT_ALLOWLISTED=false",
    )
    for marker in required:
        assert marker in section, f"missing Z2AM marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nFRESHNESS_THRESHOLD_RATIFIED=true\n",
        "\nTEST_FIXTURE_5000_PROMOTED_TO_POLICY=true\n",
        "\nMD_DEFAULT_5S_PROMOTED_TO_POLICY=true\n",
        "\nTESTNET_DEFAULT_120S_PROMOTED_TO_POLICY=true\n",
        "\nEXTRA_DEVIATION_BOUND_RATIFIED=true\n",
        "\nFRESHNESS_BINDING=PROVEN_EXISTING_VALUE\n",
        "\nEXTRA_DEVIATION_BOUND=PROVEN_REQUIRED_WITH_EXISTING_VALUE\n",
        "\nNEW_PROVEN_CLOSURE=FRESHNESS_THRESHOLD_MS\n",
        "\nORDER_COUNT_LIMIT=2\n",
        "\nGET_EXECUTED_THIS_PERSIST_STEP=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nFRESHNESS_CANONICAL_DEFAULT=5000\n",
        "\nFRESHNESS_CANONICAL_DEFAULT=5.0\n",
        "\nFRESHNESS_CANONICAL_DEFAULT=120\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AM marker present: {marker!r}"


def test_z2am_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "§11.13.5.Z2AM |" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AM" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={CONSUMED_Z2AL_POINTER}\n" not in mot
    assert "FRESHNESS_BINDING=OWNER_RATIFICATION_REQUIRED" in mot
    assert "FRESHNESS_PROVEN_EXISTING_THRESHOLD=NONE" in mot
    assert "FRESHNESS_UNRATIFIED_POLICY=NO_CANONICAL_DEFAULT_REMAINS_EXPLICIT" in mot
    assert "FRESHNESS_CANONICAL_DEFAULT=NONE" in mot
    assert "TEST_FIXTURE_5000_PROMOTED_TO_POLICY=false" in mot
    assert "MD_DEFAULT_5S_PROMOTED_TO_POLICY=false" in mot
    assert "TESTNET_DEFAULT_120S_PROMOTED_TO_POLICY=false" in mot
    assert "EXTRA_DEVIATION_BOUND=NOT_PROVEN_REQUIRED" in mot
    assert "EXTRA_DEVIATION_SAFETY_INVARIANT=NOT_PROVEN" in mot
    assert "EXTRA_DEVIATION_DEFENSE_IN_DEPTH=OPTIONAL_UNRATIFIED_CURRENTLY_REJECTED" in mot
    assert "Z2P_SLIPPAGE_RESERVE_NUMERIC_CLASS=COVER_ALGEBRA_NOT_FLATTEN_PX_GUARD" in mot
    assert "NEW_PROVEN_CLOSURE=NONE" in mot
    assert "LIVE_FLATTEN_PROVABILITY=UNPROVEN" in mot
    assert "LAST_CANONICALLY_CLOSED_STEP=LF_12" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    snapshot_pointer_lines = [
        ln for ln in mot.splitlines() if ln.startswith("NEXT_CANONICAL_STEP_POINTER=")
    ]
    assert snapshot_pointer_lines[-1] == f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}"
