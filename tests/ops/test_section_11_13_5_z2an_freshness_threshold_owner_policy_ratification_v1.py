"""§11.13.5.Z2AN flatten FRESHNESS_THRESHOLD_MS Owner-policy ratification.

Docs/governance plus offline contract bind. Records the new explicit
Owner ratification of FRESHNESS_THRESHOLD_MS=5000. Does not promote
fixtures as historical authority, does not prove live flatten, does
not enable live wire, and does not authorize GET/POST/order/funding/Canary.
"""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FLATTEN_PRICE_POLICY_FULLY_BOUND,
    FRESHNESS_THRESHOLD_MS,
    LIVE_FLATTEN_PROVABILITY_STATUS,
    OWNER_BINDING_STILL_REQUIRED,
    QUOTE_FRESHNESS_STATUS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AN_HEADING = "### 11.13.5.Z2AN Flatten FRESHNESS_THRESHOLD_MS Owner-policy ratification"
Z2AM_HEADING = "### 11.13.5.Z2AM Post-Z2AL read-only Owner-binding adjudication persist"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_OR_ADJUDICATION_"
    "STEP_NOT_AUTHORIZED_BY_THIS_RATIFICATION_Z2AN_FRESHNESS_THRESHOLD_MS_"
    "5000_OWNER_RATIFIED_EXTRA_DEVIATION_BOUND_NOT_PROVEN_REQUIRED_LIVE_"
    "FLATTEN_UNPROVEN_NO_LIVE_WIRE_NO_ORDER_COUNT_LIMIT_RAISE_TO_2_NO_"
    "RUNTIME_READ_NO_PRODUCTIVE_FLATTEN_NO_GET_NO_ORDER_NO_ALLOWLIST_"
    "CANARY_NOT_AUTHORIZED_SUPPORT_CONTACT_NOT_AUTHORIZED"
)
OWNER_GO = "GRANTED_FOR_POST_Z2AM_FRESHNESS_THRESHOLD_OWNER_POLICY_RATIFICATION_OFFLINE_ONLY"
BASELINE_SHA = "43582d515877669bb2d64a091700b6d15fcfffa4"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2an_section(text: str) -> str:
    start = text.find(Z2AN_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AN heading"
    end = text.find("## 11.14 Live order and economic evidence ladder", start)
    assert end > start, "missing §11.14 boundary after Z2AN"
    return text[start:end]


def test_z2an_heading_is_unique_and_follows_z2am() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AN_HEADING) == 1
    z2am = text.find(Z2AM_HEADING)
    z2an = text.find(Z2AN_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2am < z2an < ladder


def test_z2an_docs_bind_owner_ratified_freshness_without_live_flatten_proven() -> None:
    section = _z2an_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=POST_Z2AM_FRESHNESS_THRESHOLD_OWNER_POLICY_RATIFICATION_OFFLINE_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "LAST_CANONICALLY_CLOSED_STEP=LF_12",
        "OWNER_POLICY_ADJUDICATION=RATIFIED",
        "FRESHNESS_THRESHOLD_MS=5000",
        "FRESHNESS_THRESHOLD_RATIFIED=true",
        "FRESHNESS_BINDING=OWNER_RATIFIED",
        "FRESHNESS_POLICY_CLASS=NEW_EXPLICIT_OWNER_RATIFICATION_NOT_FIXTURE_PROMOTION",
        "TEST_FIXTURE_5000_PROMOTED_TO_POLICY=false",
        "MD_DEFAULT_5S_PROMOTED_TO_POLICY=false",
        "TESTNET_DEFAULT_120S_PROMOTED_TO_POLICY=false",
        "FIXTURE_VALUES_TREATED_AS_AUTHORITY=false",
        "FLATTEN_PRICE_POLICY_IMPLEMENTED=true",
        "FLATTEN_PRICE_POLICY_FULLY_BOUND=true",
        "FINITE_EXTRA_DEVIATION_BOUND=NOT_OWNER_RATIFIED_REJECTED",
        "EXTRA_DEVIATION_BOUND=NOT_PROVEN_REQUIRED",
        "DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED=false",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "LIVE_FLATTEN_PROVABILITY_REMAINS=UNPROVEN_HARD_STOP",
        "NEW_PROVEN_CLOSURE=NONE",
        "PRODUCTIVE_FLATTEN_EXECUTED=false",
        "MARKET_PATH_AVAILABLE=false",
        "CLOSE_POSITION_ENDPOINT_ALLOWLISTED=false",
        "ORDER_COUNT_LIMIT=1",
        "ORDER_COUNT_LIMIT_RAISED=false",
        "POSITION_COUNT_LIMIT=1",
        "LIVE_AUTHORIZED=false",
        "GET_EXECUTED_THIS_STEP=false",
        "POST_EXECUTED=false",
        "NETWORK_REQUEST_EXECUTED=false",
        "RUNTIME_TOUCHED=false",
        "NON_CANONICAL_SUPPLIED_THRESHOLD=REJECTED",
        "OMITTED_THRESHOLD=APPLIES_CANONICAL_5000",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY",
        "HARD_STOP_AFTER_THIS_TASK=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2AN marker: {marker}"
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
        "\nTEST_FIXTURE_5000_PROMOTED_TO_POLICY=true\n",
        "\nMD_DEFAULT_5S_PROMOTED_TO_POLICY=true\n",
        "\nTESTNET_DEFAULT_120S_PROMOTED_TO_POLICY=true\n",
        "\nFIXTURE_VALUES_TREATED_AS_AUTHORITY=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AN marker present: {marker!r}"


def test_z2an_code_constant_matches_ssot() -> None:
    assert FRESHNESS_THRESHOLD_MS == 5000
    assert QUOTE_FRESHNESS_STATUS == "OWNER_RATIFIED_FRESHNESS_THRESHOLD_MS"
    assert FLATTEN_PRICE_POLICY_FULLY_BOUND is True
    assert LIVE_FLATTEN_PROVABILITY_STATUS == "UNPROVEN"
    assert "FRESHNESS_THRESHOLD_MS_CALLER_SUPPLIED_NO_CANONICAL_DEFAULT" not in (
        OWNER_BINDING_STILL_REQUIRED
    )
    assert "NO_OWNER_RATIFIED_EXTRA_DEVIATION_BOUND" in OWNER_BINDING_STILL_REQUIRED
    assert "LIVE_WIRE_AND_PRODUCTIVE_FLATTEN_SEPARATE_OWNER_GO" in OWNER_BINDING_STILL_REQUIRED


def test_z2an_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "§11.13.5.Z2AN |" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AN" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AO" in mot
    assert "FRESHNESS_THRESHOLD_MS=5000" in mot
    assert "FRESHNESS_THRESHOLD_RATIFIED=true" in mot
    assert "FRESHNESS_BINDING=OWNER_RATIFIED" in mot
    assert "TEST_FIXTURE_5000_PROMOTED_TO_POLICY=false" in mot
    assert "LIVE_FLATTEN_PROVABILITY=UNPROVEN" in mot
    assert "LAST_CANONICALLY_CLOSED_STEP=LF_12" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    snapshot_pointer_lines = [
        ln for ln in mot.splitlines() if ln.startswith("NEXT_CANONICAL_STEP_POINTER=")
    ]
    assert snapshot_pointer_lines[-1] != f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}"
    current_pointer = snapshot_pointer_lines[-1].split("=", 1)[1]
    assert "Z2AM_FRESHNESS_BINDING_OWNER_RATIFICATION_REQUIRED" not in current_pointer
    assert "NO_CANONICAL_FRESHNESS_DEFAULT" not in current_pointer
    assert "Z2AN_FRESHNESS_THRESHOLD_MS_5000_OWNER_RATIFIED" not in current_pointer
    assert "Z2AO_EXTRA_DEVIATION_BOUND_NOT_REQUIRED" in current_pointer
    assert "NO_LIVE_WIRE" in current_pointer
    assert "NO_ORDER_COUNT_LIMIT_RAISE_TO_2" in current_pointer
    assert "NO_PRODUCTIVE_FLATTEN" in current_pointer
    assert "NO_RUNTIME_READ" in current_pointer
