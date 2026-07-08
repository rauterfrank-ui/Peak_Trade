from __future__ import annotations

import json
from pathlib import Path

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import (
    SURFACES,
    build_inventory,
    render_markdown,
)


def test_inventory_schema_and_surface_coverage() -> None:
    inventory = build_inventory(Path.cwd())
    assert inventory["schema"] == "BacktestRuntimeDecisionParityInventoryV1"
    assert inventory["runtime_authority"] is False
    assert inventory["orders_allowed"] is False
    assert inventory["economic_claim"] is False
    assert inventory["system_economic_evidence_admissible"] is False
    assert inventory["full_canonical_chain_wired_claimed"] is False
    assert inventory["backtest_runtime_decision_parity_pass_claimed"] is False
    assert inventory["inventory_surface_count"] == len(SURFACES)
    assert len(inventory["surfaces"]) >= 12


def test_inventory_surfaces_are_reuse_first_gap_inventory_not_status_only() -> None:
    inventory = build_inventory(Path.cwd())
    classifications = {surface["gap_classification"] for surface in inventory["surfaces"]}
    allowed = {
        "OWNER_DISCOVERY_REQUIRED",
        "CANONICAL_OWNER_FOUND_BACKTEST_BINDING_GAP",
        "CANONICAL_AND_BACKTEST_FOUND_RUNTIME_BOUNDARY_UNDISCOVERED",
        "PARITY_TRACE_CANDIDATE_FOUND",
    }
    assert classifications
    assert classifications <= allowed
    for surface in inventory["surfaces"]:
        assert surface["required_status"]
        assert surface["reuse_first_rewire_action"]
        assert surface["rewire_planning_note"]
        assert "STATUS_ONLY" not in surface["gap_classification"]


def test_inventory_markdown_is_renderable_and_json_serializable() -> None:
    inventory = build_inventory(Path.cwd())
    encoded = json.dumps(inventory, sort_keys=True)
    assert "BacktestRuntimeDecisionParityInventoryV1" in encoded
    markdown = render_markdown(inventory)
    assert "Backtest Runtime Decision Parity Inventory V1" in markdown
    assert "NO_RUNTIME_AUTHORITY=true" in markdown
    assert "Surface inventory" in markdown
