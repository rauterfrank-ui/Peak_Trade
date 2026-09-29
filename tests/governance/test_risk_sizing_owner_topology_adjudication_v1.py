"""WP_B05_OWNER_TOPOLOGY + governance semantic marker alignment — static contract pins."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FREEZE = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_authority_decision_contract_freeze_v1.json"
)
INVENTORY = REPO_ROOT / "config" / "governance" / "risk_sizing_owner_inventory_ssot_v1.json"
TOPOLOGY = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_caller_owner_topology_contract_v0.json"
)
CLOSURE = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_c2_canonical_risk_sizing_authority_closure_v1.json"
)

CRS_OWNER = "src.governance.capital_risk_sizing_v1"
BYPASS_IDS = (
    "BYPASS_CLASSIC_BACKTEST_DEFAULT",
    "BYPASS_CORE_POSITION_SIZER",
    "BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS",
    "BYPASS_LIVE_SHADOW_POSITION_FRACTION",
    "BYPASS_OFFLINE_EVAL_SIZING_CONTRACT",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_freeze_productive_canonical_marker_pins() -> None:
    data = _load(FREEZE)
    markers = data["markers"]
    assert markers["CANONICAL_PRODUCTIVE_RISK_SIZING_OWNER"] == CRS_OWNER
    assert markers["PRODUCTIVE_FINAL_QUANTITY_OWNER_COUNT"] == 1
    assert markers["REPOSITORY_SIZING_IMPLEMENTATION_COUNT"] == 5
    assert markers["REPO_WIDE_SINGLE_SIZING_IMPLEMENTATION_REQUIRED"] is False
    assert markers["SINGULAR_REPO_WIDE_OWNER_REQUIRED"] is True
    assert markers["CANONICAL_RISK_SIZING_OWNER"] == CRS_OWNER
    assert markers["MV2_INTENT_BOUND_QUANTITY_ALGEBRA_OWNER"] == CRS_OWNER
    topo = data["owner_topology_adjudication_v1"]
    assert topo["runtime_rewire_performed"] is False
    assert topo["current_productive_canonical_semantics_superseded_by"] == (
        "config/governance/risk_sizing_c2_canonical_risk_sizing_authority_closure_v1.json"
    )


def test_inventory_bypass_fates_and_productive_crs_scope() -> None:
    data = _load(INVENTORY)
    markers = data["markers"]
    assert markers["CANONICAL_PRODUCTIVE_RISK_SIZING_OWNER"] == CRS_OWNER
    assert markers["PRODUCTIVE_FINAL_QUANTITY_OWNER_COUNT"] == 1
    assert markers["REPOSITORY_SIZING_IMPLEMENTATION_COUNT"] == 5
    assert markers["REPO_WIDE_SINGLE_SIZING_IMPLEMENTATION_REQUIRED"] is False
    assert markers["SINGULAR_REPO_WIDE_OWNER_REQUIRED"] is True
    assert data["canonical_status"]["mv2_intent_bound_quantity_algebra_owner_adjudicated"] is True
    assert data["canonical_status"]["productive_final_quantity_owner_count"] == 1
    bypass = {item["id"]: item for item in data["bypass_paths"]}
    assert set(bypass) == set(BYPASS_IDS)
    for bid in BYPASS_IDS:
        assert bypass[bid]["canonical_for_mv2_intent_bound_scope"] is False
        assert bypass[bid]["operator_fate_adjudication"] in (
            "GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE",
            "KEEP_PARALLEL_NON_CANONICAL",
            "RESEARCH_OR_OFFLINE_SCOPE_ONLY",
        )
        assert bypass[bid]["reachability"] == "REACHABLE_PRODUCTIVE"
    crs = next(o for o in data["productive_decision_owners"] if o["owner_id"] == CRS_OWNER)
    assert crs["mv2_intent_bound_quantity_algebra_owner_adjudicated"] is True
    assert crs["canonical_productive_mv2_final_quantity_owner_status"] == "RESOLVED"
    closure = _load(CLOSURE)
    assert closure["owner_decision_required"] is False


def test_topology_contract_naming_pins_do_not_assign_repo_wide_owner() -> None:
    markers = _load(TOPOLOGY)["markers"]
    assert markers["SINGULAR_REPO_WIDE_OWNER_REQUIRED"] is False
    assert markers["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert markers["MV2_INTENT_BOUND_QUANTITY_ALGEBRA_OWNER"] == CRS_OWNER
