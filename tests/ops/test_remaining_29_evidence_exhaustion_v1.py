"""Remaining-29 evidence exhaustion contracts. AUTHORITY=NONE."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from scripts.ops.law_map_v1.remaining_29_evidence_exhaustion_v1 import (
    POST_MERGE_BASELINE_SHA,
    _build_rows,
    build_artifact,
    frozen_workset_sha256,
)

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "config/governance/current_law_impact_map_v1/source_v1.json"
R29 = REPO / "config/governance/current_law_impact_map_v1/remaining_29_frozen_workset_v1.json"


def test_frozen_remaining_count_and_partition() -> None:
    rows = _build_rows()
    assert len(rows) == 29
    c = Counter(r.exhaustion_disposition for r in rows)
    assert c["EXISTING_CURRENT_EVIDENCE_BINDABLE"] == 10
    assert c["GENUINELY_CANONICAL_OWNER_BLOCKED"] == 19
    assert sum(c.values()) == 29


def test_workset_hash_stable() -> None:
    rows = _build_rows()
    artifact = build_artifact()
    assert artifact["frozen_remaining_workset_count"] == 29
    assert artifact["frozen_remaining_workset_sha256"] == frozen_workset_sha256(rows)


def test_artifact_on_disk() -> None:
    assert R29.is_file()
    on_disk = json.loads(R29.read_text())
    assert on_disk == build_artifact()


def test_source_after_apply() -> None:
    doc = json.loads(SOURCE.read_text())
    assert doc["baseline_sha"] == POST_MERGE_BASELINE_SHA
    assert len(doc["unclassified_current_surfaces"]) == 19
    assert any(d["id"] == "SEM-SURF-DIV-00003" for d in doc["semantic_divergence_index"])
    for row in doc["unclassified_current_surfaces"]:
        assert "EXHAUSTION=" in row["reason"]


def test_bindable_lrefs_have_provenance() -> None:
    doc = json.loads(SOURCE.read_text())
    bindable_ids = {
        r.bind_lref
        for r in _build_rows()
        if r.exhaustion_disposition == "EXISTING_CURRENT_EVIDENCE_BINDABLE"
    }
    lref_ids = {x["law_id"] for x in doc["law_references"]}
    assert bindable_ids <= lref_ids
    for lid in bindable_ids:
        lref = next(x for x in doc["law_references"] if x["law_id"] == lid)
        assert (REPO / lref["canonical_source"]).is_file()
