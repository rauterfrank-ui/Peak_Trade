#!/usr/bin/env python3
"""Apply UCS evidence-binding pass to Law Impact Map source. AUTHORITY=NONE."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "config/governance/current_law_impact_map_v1/source_v1.json"

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.ops.law_map_v1.surface_census_v1 import discover_unclassified_current_productive  # noqa: E402
from scripts.ops.law_map_v1.ucs_evidence_binding_v1 import (  # noqa: E402
    apply_bindings,
    build_workset_artifact,
    write_workset_artifact,
)


def main() -> int:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    # Freeze artifact from pre-binding census (78 surfaces).
    write_workset_artifact(doc)
    doc = apply_bindings(doc)
    # Post-binding census: surfaces indexed on SOBJ should not reappear.
    post_discover = discover_unclassified_current_productive(doc)
    if post_discover:
        known = {r["path"] for r in doc["unclassified_current_surfaces"]}
        extra = [r for r in post_discover if r["path"] not in known]
        if extra:
            print(f"warning: newly_discovered_current={len(extra)}", file=sys.stderr)
    SOURCE.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    artifact = build_workset_artifact(json.loads(SOURCE.read_text()))
    print(
        f"law_refs={len(doc['law_references'])} sobj={len(doc['semantic_objects'])} "
        f"edges={len(doc['impact_edges'])} unclassified={len(doc['unclassified_current_surfaces'])} "
        f"workset_dispositions={len(artifact['dispositions'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
