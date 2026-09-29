#!/usr/bin/env python3
"""Validate CURRENT_SYSTEM_CENSUS_GRAPH_V1. AUTHORITY=NONE; READ-ONLY checks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO / "config/governance/current_system_census_graph_v1"
SOURCE_PATH = ARTIFACT_DIR / "source_v1.json"
SCHEMA_PATH = ARTIFACT_DIR / "schema_v1.json"

PRIMARY_CLASSES = frozenset(
    {
        "POSITIVE_UNIVERSE_MEMBER",
        "CROSS_UNIVERSE_BOUNDARY",
        "SHARED_INFRASTRUCTURE",
        "SUPPORT_INFRASTRUCTURE",
        "OFFLINE_RESEARCH",
        "PRESENTATION_ONLY",
        "UNASSIGNED_CURRENT",
        "UNKNOWN_MEMBERSHIP",
        "CONFLICTING_MEMBERSHIP",
    }
)

EXPECTED_COUNTS = {
    "POSITIVE_UNIVERSE_MEMBER": 42,
    "CROSS_UNIVERSE_BOUNDARY": 46,
    "SHARED_INFRASTRUCTURE": 30,
    "SUPPORT_INFRASTRUCTURE": 145,
    "OFFLINE_RESEARCH": 29,
    "PRESENTATION_ONLY": 9,
    "UNASSIGNED_CURRENT": 0,
    "UNKNOWN_MEMBERSHIP": 0,
    "CONFLICTING_MEMBERSHIP": 0,
}

EXPECTED_OBJECTS = 301
EXPECTED_EDGES = 84

MAP_EDGE_RECON = {
    "MAP_AND_SYSTEM_EDGE_COUNT": 31,
    "SYSTEM_ONLY_EDGE_COUNT": 9,
    "MAP_ONLY_EDGE_COUNT": 44,
    "EDGE_CONFLICT_COUNT": 1,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()


def validate_structure(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in (
        "artifact_id",
        "schema_version",
        "authority",
        "map_authority",
        "runtime_authority",
        "decision_authority",
        "not_a_runtime_authority",
        "source_baseline_head",
        "census_objects",
        "semantic_edges",
        "topology_domains",
        "websocket_topology",
        "intelligence_topology",
        "productive_hot_path",
        "productive_terminal",
        "authority_map_reconciliation",
        "census_discrepancies",
    ):
        if key not in doc:
            errors.append(f"missing top-level key: {key}")
    if doc.get("artifact_id") != "current_system_census_graph_v1":
        errors.append("artifact_id must be current_system_census_graph_v1")
    if doc.get("authority") != "NONE":
        errors.append("authority must be NONE")
    for k in ("map_authority", "runtime_authority", "decision_authority"):
        if doc.get(k) != "NONE":
            errors.append(f"{k} must be NONE")
    if doc.get("not_a_runtime_authority") is not True:
        errors.append("not_a_runtime_authority must be true")
    if doc.get("not_a_universe_ratification") is not True:
        errors.append("not_a_universe_ratification must be true")
    return errors


def validate_objects(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    objects = doc.get("census_objects", [])
    if len(objects) != EXPECTED_OBJECTS:
        errors.append(f"expected {EXPECTED_OBJECTS} objects, got {len(objects)}")
    ids = [o.get("object_id") for o in objects]
    if len(ids) != len(set(ids)):
        errors.append("duplicate object_id")
    counts = Counter(o.get("primary_class") for o in objects)
    for cls, exp in EXPECTED_COUNTS.items():
        if counts.get(cls, 0) != exp:
            errors.append(f"primary_class {cls}: expected {exp}, got {counts.get(cls, 0)}")
    for o in objects:
        if o.get("primary_class") not in PRIMARY_CLASSES:
            errors.append(f"invalid primary_class on {o.get('object_id')}")
        if o.get("canonical_universe") is True:
            errors.append(f"forbidden canonical_universe on {o.get('object_id')}")
    return errors


def validate_edges(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    edges = doc.get("semantic_edges", [])
    if len(edges) != EXPECTED_EDGES:
        errors.append(f"expected {EXPECTED_EDGES} semantic edges, got {len(edges)}")
    ids = [e.get("edge_id") for e in edges]
    if len(ids) != len(set(ids)):
        errors.append("duplicate edge_id")
    obj_ids = {o["object_id"] for o in doc.get("census_objects", [])}
    rel_counts = Counter(e.get("map_relationship") for e in edges)
    for k, v in MAP_EDGE_RECON.items():
        field = k.lower()
        if field in doc.get("edge_reconciliation", {}):
            if doc["edge_reconciliation"][field] != v:
                errors.append(f"edge_reconciliation.{field} expected {v}")
    # map relationship buckets (84 total)
    code_and_map = rel_counts.get("CODE_AND_MAP", 0)
    code_only = rel_counts.get("CODE_ONLY", 0)
    map_only = rel_counts.get("MAP_ONLY", 0)
    conflicting = rel_counts.get("CONFLICTING", 0)
    if code_and_map + code_only + map_only + conflicting != EXPECTED_EDGES:
        errors.append("map_relationship counts do not sum to edge total")
    er = doc.get("edge_reconciliation", {})
    if er.get("reconciliation_status") != "DISCREPANCY_PRESERVED":
        errors.append("edge_reconciliation.reconciliation_status must be DISCREPANCY_PRESERVED")
    for k, v in MAP_EDGE_RECON.items():
        if er.get(k.lower()) != v:
            errors.append(f"edge_reconciliation.{k.lower()} expected census-reported {v}")
    materialized = er.get("materialized_map_relationship_tally", {})
    if sum(materialized.values()) != EXPECTED_EDGES:
        errors.append("materialized_map_relationship_tally must sum to edge total")
    for e in edges:
        for side in ("source_object", "target_object"):
            ref = e.get(side)
            if ref and ref.startswith(("SO-",)) and ref not in obj_ids:
                errors.append(f"edge {e.get('edge_id')} unresolved {side}={ref}")
    return errors


def validate_topology(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not doc.get("websocket_topology"):
        errors.append("missing websocket_topology")
    if not doc.get("intelligence_topology"):
        errors.append("missing intelligence_topology")
    if doc.get("taxonomy_status") != "OPEN_CURRENT":
        errors.append("taxonomy_status must be OPEN_CURRENT")
    if doc.get("canonical_universe_count_asserted") is not False:
        errors.append("canonical_universe_count_asserted must be false")
    return errors


def validate_discrepancies(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    disc = doc.get("census_discrepancies", [])
    if not disc:
        errors.append("census_discrepancies must be non-empty")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-head-drift", action="store_true")
    args = parser.parse_args()

    doc = load_json(SOURCE_PATH)
    errors: list[str] = []
    errors.extend(validate_structure(doc))
    errors.extend(validate_objects(doc))
    errors.extend(validate_edges(doc))
    errors.extend(validate_topology(doc))
    errors.extend(validate_discrepancies(doc))

    baseline = doc.get("source_baseline_head", "")
    head = git_head()
    baseline_match = head == baseline
    if args.check_head_drift:
        print(f"BASELINE_MATCH={baseline_match}")
        print(f"source_baseline_head={baseline}")
        print(f"current_head={head}")

    if errors:
        for e in errors:
            print(f"VALIDATION_ERROR: {e}", file=sys.stderr)
        print("VALIDATOR_RESULT=FAIL")
        return 1

    print("VALIDATOR_RESULT=PASS")
    print(f"BASELINE_MATCH={baseline_match}")
    print(f"MATERIALIZED_OBJECT_COUNT={len(doc['census_objects'])}")
    print(f"MATERIALIZED_EDGE_COUNT={len(doc['semantic_edges'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
