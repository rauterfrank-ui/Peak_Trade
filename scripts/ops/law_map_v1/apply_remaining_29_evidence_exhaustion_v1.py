#!/usr/bin/env python3
"""Apply remaining-29 evidence exhaustion bindings. AUTHORITY=NONE."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "config/governance/current_law_impact_map_v1/source_v1.json"

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.ops.law_map_v1.remaining_29_evidence_exhaustion_v1 import (  # noqa: E402
    apply_bindings,
    assert_source_matches_frozen_workset,
    write_artifact,
)


def main() -> int:
    write_artifact()
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    doc = apply_bindings(doc)
    SOURCE.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    write_artifact()
    assert_source_matches_frozen_workset()
    print(
        f"unclassified={len(doc['unclassified_current_surfaces'])} "
        f"law_refs={len(doc['law_references'])} divs={len(doc['semantic_divergence_index'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
