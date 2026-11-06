#!/usr/bin/env python3
"""Apply evidence-backed surface expansion to Law Impact Map source. AUTHORITY=NONE."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "config/governance/current_law_impact_map_v1/source_v1.json"

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.ops.law_map_v1.surface_census_v1 import (  # noqa: E402
    discover_unclassified_current_productive,
    expansion_payload,
)


def _merge_by_id(existing: list[dict], new: list[dict], key: str) -> list[dict]:
    seen = {row[key]: row for row in existing}
    for row in new:
        seen[row[key]] = row
    return [seen[k] for k in sorted(seen)]


def main() -> int:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    payload = expansion_payload()
    doc["baseline_sha"] = "f3e6e98089e611c89e2ef935d185944a9d221f21"
    doc["law_references"] = _merge_by_id(doc["law_references"], payload["law_references"], "law_id")
    doc["semantic_objects"] = _merge_by_id(
        doc["semantic_objects"], payload["semantic_objects"], "id"
    )
    doc["impact_edges"] = _merge_by_id(doc.get("impact_edges", []), payload["impact_edges"], "id")
    doc["unknown_relations"] = _merge_by_id(
        doc["unknown_relations"], payload["unknown_relations"], "id"
    )
    doc["semantic_divergence_index"] = payload["semantic_divergence_index"]
    unclassified = discover_unclassified_current_productive(doc)
    doc["unclassified_current_surfaces"] = unclassified
    doc["surface_census_meta"] = {
        "census_id": "CURRENT_SEMANTIC_SURFACE_EXPANSION_V1",
        "authority": "NONE",
        "bootstrap_exhaustive": False,
        "census_method": "CSIA_FIRST_CLASS_DOMAINS+PRODUCTIVE_CHAIN+CURRENT_PRODUCTIVE_GLOB",
        "unclassified_sample_cap": 120,
        "notes": "Navigation-only; not compliance adjudication.",
    }
    SOURCE.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(
        f"law_refs={len(doc['law_references'])} sobj={len(doc['semantic_objects'])} "
        f"edges={len(doc['impact_edges'])} unk={len(doc['unknown_relations'])} "
        f"unclassified={len(unclassified)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
