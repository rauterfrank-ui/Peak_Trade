"""WP_B05_BYPASS_FATE_OPERATOR_ADJUDICATION_V1 — static contract pins (governance only)."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ADJUDICATION_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_bypass_fate_operator_adjudication_v1.json"
)
ADJUDICATION_DOC = (
    REPO_ROOT / "docs" / "governance" / "RISK_SIZING_BYPASS_FATE_OPERATOR_ADJUDICATION_V1.md"
)
VOCABULARY_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_bypass_fate_vocabulary_and_decision_authority_freeze_v1.json"
)
INVENTORY_JSON = REPO_ROOT / "config" / "governance" / "risk_sizing_owner_inventory_ssot_v1.json"

EXPECTED_BYPASS_IDS = (
    "BYPASS_CLASSIC_BACKTEST_DEFAULT",
    "BYPASS_CORE_POSITION_SIZER",
    "BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS",
    "BYPASS_LIVE_SHADOW_POSITION_FRACTION",
    "BYPASS_OFFLINE_EVAL_SIZING_CONTRACT",
)

EXPECTED_FATES = {
    "BYPASS_CLASSIC_BACKTEST_DEFAULT": "GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE",
    "BYPASS_CORE_POSITION_SIZER": "KEEP_PARALLEL_NON_CANONICAL",
    "BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS": "KEEP_PARALLEL_NON_CANONICAL",
    "BYPASS_LIVE_SHADOW_POSITION_FRACTION": "GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE",
    "BYPASS_OFFLINE_EVAL_SIZING_CONTRACT": "RESEARCH_OR_OFFLINE_SCOPE_ONLY",
}

ALLOWED_TOKENS = frozenset(
    {
        "CONFLICTING",
        "GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE",
        "INTEND_REBIND_TO_CRS",
        "KEEP_PARALLEL_NON_CANONICAL",
        "RESEARCH_OR_OFFLINE_SCOPE_ONLY",
        "UNKNOWN",
    }
)

FOREIGN_TOKENS = frozenset({"DEPRECATE_LEGACY_PATH", "DEPRECATED_QUARANTINED"})


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_adjudication_contract_pins_and_boundaries() -> None:
    payload = _load(ADJUDICATION_JSON)
    markers = payload["markers"]
    assert payload["workpackage_id"] == "WP_B05_BYPASS_FATE_OPERATOR_ADJUDICATION_V1"
    assert markers["OPERATOR_FATE_ADJUDICATION_EXECUTED"] is True
    assert markers["FATE_IMPLEMENTATION_EXECUTED"] is True
    assert markers["RUNTIME_REWIRE_EXECUTED"] is False
    assert markers["BYPASS_SET_CHANGED"] is False
    assert markers["BYPASS_PATH_COUNT"] == 5
    assert markers["UNKNOWN_FATE_COUNT"] == 0
    assert markers["CONFLICTING_FATE_COUNT"] == 0
    assert markers["CONVERSION_READY"] is False
    assert markers["C2_INPUT_AUTHORITIES"] == "UNRESOLVED"
    assert markers["CONSOLIDATION_STATUS"] == "NOT_STARTED"
    assert markers["AUTHORITY_EFFECT"] == "NONE"
    assert markers["RUNTIME_EFFECT"] == "NONE"
    assert markers["PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED"] is False
    assert payload["decision_authority"]["scoped_operator_go_present"] is True


def test_all_five_bypasses_adjudicated_with_allowed_tokens() -> None:
    payload = _load(ADJUDICATION_JSON)
    summary = payload["operator_fate_summary_sorted"]
    assert set(summary.keys()) == set(EXPECTED_BYPASS_IDS)
    assert summary == EXPECTED_FATES
    for bid in EXPECTED_BYPASS_IDS:
        row = payload["bypass_fate_adjudications"][bid]
        fate = row["operator_fate_adjudication"]
        assert fate in ALLOWED_TOKENS
        assert fate not in FOREIGN_TOKENS
        assert row["required_evidence_satisfied"] is True
        assert row["required_evidence_for_token"]
        record = row["evidence_record"]
        assert record["CANONICAL_AUTHORITY"]
        assert record["OBSERVED_CURRENT_EVIDENCE"]


def test_inventory_and_vocabulary_pins_match_adjudication() -> None:
    adjudication = _load(ADJUDICATION_JSON)
    summary = adjudication["operator_fate_summary_sorted"]
    vocabulary = _load(VOCABULARY_JSON)
    assert vocabulary["current_bypass_fate_pins"] == summary
    assert vocabulary["markers"]["PER_BYPASS_FATE_ADJUDICATION_EXECUTED"] is True
    assert vocabulary["markers"]["UNKNOWN_FATE_COUNT"] == 0

    inventory = _load(INVENTORY_JSON)
    assert inventory["markers"]["OPERATOR_FATE_ADJUDICATION_EXECUTED"] is True
    inventored = {b["id"]: b["operator_fate_adjudication"] for b in inventory["bypass_paths"]}
    assert inventored == summary


def test_adjudication_doc_markers_present() -> None:
    text = ADJUDICATION_DOC.read_text(encoding="utf-8")
    for marker in (
        "RISK_SIZING_BYPASS_FATE_OPERATOR_ADJUDICATION_V1=true",
        "OPERATOR_FATE_ADJUDICATION_EXECUTED=true",
        "RUNTIME_EFFECT=NONE",
        "CONVERSION_READY=false",
    ):
        assert marker in text


def test_productive_src_does_not_import_adjudication_contract() -> None:
    needle = "risk_sizing_bypass_fate_operator_adjudication_v1"
    hits: list[str] = []
    for path in (REPO_ROOT / "src").rglob("*.py"):
        if needle in path.read_text(encoding="utf-8"):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []
