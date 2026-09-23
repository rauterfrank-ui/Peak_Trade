"""WP_B05_OWNER_TOPOLOGY_OPERATOR_ADJUDICATION_V1 — static contract pins (governance only)."""

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


def test_freeze_owner_topology_adjudication_pins() -> None:
    data = _load(FREEZE)
    markers = data["markers"]
    assert markers["SINGULAR_REPO_WIDE_OWNER_REQUIRED"] is False
    assert markers["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert markers["MV2_INTENT_BOUND_QUANTITY_ALGEBRA_OWNER"] == CRS_OWNER
    assert markers["CONVERSION_READY"] is False
    topo = data["owner_topology_adjudication_v1"]
    assert topo["runtime_rewire_performed"] is False
    assert topo["conversion_ready"] is False
    assert topo["account_equity_authority_owner"] == "UNRESOLVED"


def test_inventory_bypass_fates_unknown_and_crs_scope_adjudicated() -> None:
    data = _load(INVENTORY)
    assert data["markers"]["SINGULAR_REPO_WIDE_OWNER_REQUIRED"] is False
    assert data["canonical_status"]["singular_repo_wide_owner_required"] is False
    assert data["canonical_status"]["mv2_intent_bound_quantity_algebra_owner_adjudicated"] is True
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


def test_topology_contract_naming_pins_do_not_assign_repo_wide_owner() -> None:
    markers = _load(TOPOLOGY)["markers"]
    assert markers["SINGULAR_REPO_WIDE_OWNER_REQUIRED"] is False
    assert markers["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert markers["MV2_INTENT_BOUND_QUANTITY_ALGEBRA_OWNER"] == CRS_OWNER
