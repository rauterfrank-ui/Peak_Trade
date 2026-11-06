"""BOUNDED_WP_B05_BYPASS_FATE_IMPLEMENTATION_CLOSEOUT_V1 — global 5/5 completion."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

IMPLEMENTATION_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_bypass_fate_implementation_contract_v1.json"
)
PROVENANCE_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_bypass_fate_provenance_binding_v1.json"
)
ADJUDICATION_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_bypass_fate_operator_adjudication_v1.json"
)
INVENTORY_JSON = REPO_ROOT / "config" / "governance" / "risk_sizing_owner_inventory_ssot_v1.json"

ALL_BYPASS_IDS = (
    "BYPASS_CLASSIC_BACKTEST_DEFAULT",
    "BYPASS_CORE_POSITION_SIZER",
    "BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS",
    "BYPASS_LIVE_SHADOW_POSITION_FRACTION",
    "BYPASS_OFFLINE_EVAL_SIZING_CONTRACT",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_global_completion_markers_and_closeout_slice() -> None:
    impl = _load(IMPLEMENTATION_JSON)
    markers = impl["markers"]
    assert markers["FATE_IMPLEMENTATION_EXECUTED"] is True
    assert markers["PER_BYPASS_FATE_IMPLEMENTATION_EXECUTED_COUNT"] == 5
    assert markers["BYPASS_PATH_COUNT"] == 5
    assert markers["B05_FATE_PHASE_STATUS"] == "CLOSED"
    assert markers["S3_RESEARCH_OR_OFFLINE_SCOPE_FATE_IMPLEMENTATION_EXECUTED"] is True
    assert markers["CONVERSION_READY"] is False
    assert markers["C2_INPUT_AUTHORITIES"] == "UNRESOLVED"
    assert markers["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert markers["CONSOLIDATION_STATUS"] == "NOT_STARTED"
    assert markers["RUNTIME_MUTATION_EXECUTED"] is False
    assert markers["PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED"] is False
    closeout = impl["bypass_fate_implementation_closeout_v1"]
    assert closeout["workpackage_id"] == "BOUNDED_WP_B05_BYPASS_FATE_IMPLEMENTATION_CLOSEOUT_V1"
    assert closeout["global_fate_implementation_executed_set_true"] is True
    assert closeout["per_bypass_fate_implementation_executed_count"] == 5


def test_all_five_bypasses_complete_against_adjudication() -> None:
    impl = _load(IMPLEMENTATION_JSON)
    adjudication = _load(ADJUDICATION_JSON)
    summary = adjudication["operator_fate_summary_sorted"]
    prov = _load(PROVENANCE_JSON)
    assert set(summary.keys()) == set(ALL_BYPASS_IDS)
    for bid in ALL_BYPASS_IDS:
        row = impl["bypass_fate_implementations"][bid]
        assert row["operator_fate_adjudication"] == summary[bid]
        assert row["fate_implementation_status"] == "COMPLETE"
        assert row["fate_implementation_executed"] is True
        assert row["completion_evidence_satisfied"] is True
        assert row["minimum_implementation_requirements_verified"] is True
        assert prov["bypass_provenance_pins"][bid]["fate_implementation_executed"] is True


def test_global_completion_rule_conjunction_satisfied() -> None:
    impl = _load(IMPLEMENTATION_JSON)
    adjudication = _load(ADJUDICATION_JSON)
    markers = impl["markers"]
    implementations = impl["bypass_fate_implementations"]
    assert markers["PER_BYPASS_FATE_IMPLEMENTATION_EXECUTED_COUNT"] == markers["BYPASS_PATH_COUNT"]
    assert all(implementations[bid]["fate_implementation_executed"] for bid in ALL_BYPASS_IDS)
    assert all(implementations[bid]["completion_evidence_satisfied"] for bid in ALL_BYPASS_IDS)
    assert all(
        implementations[bid]["minimum_implementation_requirements_verified"]
        for bid in ALL_BYPASS_IDS
    )
    for bid in ALL_BYPASS_IDS:
        assert (
            implementations[bid]["operator_fate_adjudication"]
            == adjudication["operator_fate_summary_sorted"][bid]
        )
    assert markers["CONVERSION_READY"] is False
    assert markers["C2_INPUT_AUTHORITIES"] == "UNRESOLVED"


def test_inventory_and_provenance_global_pins() -> None:
    inventory = _load(INVENTORY_JSON)
    assert inventory["markers"]["FATE_IMPLEMENTATION_EXECUTED"] is True
    assert inventory["markers"]["PER_BYPASS_FATE_IMPLEMENTATION_EXECUTED_COUNT"] == 5
    assert inventory["markers"]["B05_FATE_PHASE_STATUS"] == "CLOSED"
    prov = _load(PROVENANCE_JSON)
    assert prov["markers"]["BYPASS_FATE_PROVENANCE_BINDING_COMPLETE_COUNT"] == 5
    assert prov["markers"]["FATE_IMPLEMENTATION_EXECUTED"] is True
