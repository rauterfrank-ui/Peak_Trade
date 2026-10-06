#!/usr/bin/env python3
"""Validate CURRENT_UNIVERSE_LANDSCAPE_SNAPSHOT_V1. AUTHORITY=NONE. Offline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = (
    REPO_ROOT / "config/governance/current_universe_landscape_snapshot_v1/source_v1.json"
)
SCHEMA_PATH = REPO_ROOT / "config/governance/current_universe_landscape_snapshot_v1/schema_v1.json"
CENSUS_PATH = REPO_ROOT / "config/governance/current_system_census_graph_v1/source_v1.json"

REQUIRED_MARKERS = (
    "PRODUCTIVE_PORTFOLIO_RECONCILIATION_SINGLE_CHECK",
    "RECONCILIATION_AUTHORITY_TRANSFER",
    "PRE_EXTERNAL_TERMINAL",
)


def main() -> int:
    if not SNAPSHOT_PATH.is_file():
        print(f"missing snapshot: {SNAPSHOT_PATH}", file=sys.stderr)
        return 1
    doc = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    if doc.get("authority_effect") != "NONE":
        print("authority_effect must be NONE", file=sys.stderr)
        return 1
    if doc.get("runtime_authorization_effect") != "NONE":
        print("runtime_authorization_effect must be NONE", file=sys.stderr)
        return 1
    if doc.get("not_operational_ssot") is not True:
        print("not_operational_ssot must be true", file=sys.stderr)
        return 1
    if "ssot_companion_doc" in doc:
        print("ssot_companion_doc is forbidden (use companion_navigation_doc)", file=sys.stderr)
        return 1
    if not doc.get("companion_navigation_doc"):
        print("companion_navigation_doc required", file=sys.stderr)
        return 1
    cart = doc.get("cartography_semantics") or {}
    if cart.get("AUTHORITY") != "NONE" or cart.get("MAP_AUTHORITY") != "NONE":
        print("cartography_semantics authority pins must be NONE", file=sys.stderr)
        return 1
    if cart.get("CURRENT_UNIVERSE_LANDSCAPE_IS_AUTHORITY") is not False:
        print("CURRENT_UNIVERSE_LANDSCAPE_IS_AUTHORITY must be false", file=sys.stderr)
        return 1
    if cart.get("ONE_AUTHORITATIVE_UNIVERSE_MAP") is not False:
        print("ONE_AUTHORITATIVE_UNIVERSE_MAP must be false", file=sys.stderr)
        return 1
    for flag in (
        "TRADING_AUTHORITY",
        "SELECTION_AUTHORITY",
        "BINDING_AUTHORITY",
        "RUNTIME_AUTHORITY",
        "CONFIGURATION_AUTHORITY",
        "GOVERNANCE_DECISION_AUTHORITY",
    ):
        if cart.get(flag) is not False:
            print(f"cartography_semantics.{flag} must be false", file=sys.stderr)
            return 1
    fix = doc.get("architecture_fixpoint") or {}
    if fix.get("closure") != "PROVEN_CURRENT":
        print("architecture_fixpoint.closure must be PROVEN_CURRENT", file=sys.stderr)
        return 1
    surfaces = doc.get("surfaces") or []
    if not surfaces:
        print("surfaces empty", file=sys.stderr)
        return 1
    ids = {s.get("surface_id") for s in surfaces}
    if len(ids) != len(surfaces):
        print("duplicate surface_id", file=sys.stderr)
        return 1
    for req in (
        "SURFACE:PR6974_RECONCILIATION_MV2_ADMISSION",
        "SURFACE:PRE_EXTERNAL_TERMINAL",
    ):
        if req not in ids:
            print(f"missing required surface {req}", file=sys.stderr)
            return 1
    pr6974 = next(
        s for s in surfaces if s["surface_id"] == "SURFACE:PR6974_RECONCILIATION_MV2_ADMISSION"
    )
    blob = json.dumps(pr6974)
    for marker in REQUIRED_MARKERS:
        if marker not in blob:
            print(f"PR6974 surface missing marker {marker}", file=sys.stderr)
            return 1
    if pr6974.get("authority_transfer") is not False:
        print("PR6974 authority_transfer must be false", file=sys.stderr)
        return 1
    counts = doc.get("coverage_counts") or {}
    if counts.get("unmapped_material_surface_count", -1) != 0:
        print("unmapped_material_surface_count must be 0", file=sys.stderr)
        return 1
    if CENSUS_PATH.is_file():
        census = json.loads(CENSUS_PATH.read_text(encoding="utf-8"))
        topo_ids = {t["topology_id"] for t in census.get("topology_domains") or []}
        for s in surfaces:
            pm = s.get("positive_membership")
            if pm and pm.startswith("TD-") and pm not in topo_ids:
                if s["surface_id"] != "SURFACE:PR6974_RECONCILIATION_MV2_ADMISSION":
                    print(f"positive_membership {pm} not in census topology", file=sys.stderr)
                    return 1
    print("UNIVERSE_LANDSCAPE_SNAPSHOT_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
