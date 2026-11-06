"""UCS frozen workset evidence-binding contracts. AUTHORITY=NONE."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.ops.law_map_v1.ucs_evidence_binding_v1 import (
    FROZEN_BASELINE_SHA,
    build_workset_artifact,
    disposition_records,
    frozen_workset_paths,
    validate_dispositions_against_frozen,
    workset_sha256,
)

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "config/governance/current_law_impact_map_v1/source_v1.json"
WORKSET = REPO / "config/governance/current_law_impact_map_v1/ucs_frozen_workset_v1.json"
WORKSET_MD = (
    REPO / "docs/governance/current_law_impact_map_v1/generated/ucs_workset_disposition_v1.md"
)


def _doc():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def test_frozen_workset_count_and_hash_stable() -> None:
    paths = frozen_workset_paths()
    assert len(paths) == 78
    assert validate_dispositions_against_frozen(paths) == []
    artifact = build_workset_artifact()
    assert artifact["frozen_workset_count"] == 78
    assert artifact["frozen_workset_sha256"] == workset_sha256(paths)
    assert artifact["frozen_baseline_sha"] == FROZEN_BASELINE_SHA


def test_every_surface_exactly_one_disposition() -> None:
    rows = disposition_records()
    assert len(rows) == 78
    ids = [r["workset_id"] for r in rows]
    assert ids == [f"UCS-{i:04d}" for i in range(1, 79)]
    surfaces = [r["surface"] for r in rows]
    assert len(set(surfaces)) == 78


def test_positive_bindings_have_provenance() -> None:
    for row in disposition_records():
        if row["disposition"].startswith("UNCLASSIFIED"):
            continue
        assert row["evidence_refs"], row["workset_id"]
        if row["disposition"] in ("BOUND_EXISTING_SOBJ", "BOUND_NEW_SOBJ", "NAVIGATION_ONLY"):
            assert row["bound_sobj"], row["workset_id"]
        if row["disposition"] in ("BOUND_EXISTING_SOBJ", "BOUND_NEW_SOBJ"):
            for ref in row["evidence_refs"]:
                assert (
                    (REPO / ref).is_file() or ref.startswith("config/") or ref.startswith("docs/")
                )


def test_workset_artifact_on_disk_matches_builder() -> None:
    assert WORKSET.is_file()
    on_disk = json.loads(WORKSET.read_text())
    assert on_disk["authority"] == "NONE"
    assert on_disk["ssot"] is False
    assert on_disk["navigation_evidence_only"] is True
    assert on_disk == build_workset_artifact()


def test_workset_markdown_banner() -> None:
    assert WORKSET_MD.is_file()
    text = WORKSET_MD.read_text(encoding="utf-8")
    assert "AUTHORITY=NONE" in text
    assert "SSOT=false" in text
    assert "NAVIGATION/EVIDENCE ONLY" in text


def test_source_post_binding_counts_and_authority() -> None:
    doc = _doc()
    assert doc["map_authority"] == "NONE"
    assert doc["law_reference_is_normative"] is False
    assert doc["bootstrap_exhaustive"] is False
    assert doc["baseline_sha"] == "6093436031fb27ce2cc0c91074efbab71a9369a3"
    assert len(doc["law_references"]) >= 26
    assert len(doc["semantic_objects"]) == 33
    assert len(doc.get("unclassified_current_surfaces", [])) == 9
    assert doc["surface_census_meta"]["census_id"] == "UCS_EVIDENCE_BINDING_V1"


def test_persists_and_replays_edges_present() -> None:
    doc = _doc()
    edges = doc.get("impact_edges", [])
    persists = [e for e in edges if e["edge_class"] == "PERSISTS"]
    replays = [e for e in edges if e["edge_class"] == "REPLAYS"]
    assert len(persists) >= 3
    assert len(replays) >= 1
    for e in persists + replays:
        assert e.get("evidence_refs")


def test_new_b05_sobjs_have_lref_sha256_currency() -> None:
    doc = _doc()
    for lid in (
        "B05-REFERENCE-PRICE-RATIFICATION-V1",
        "B05-INSTRUMENT-METADATA-RATIFICATION-V1",
    ):
        lref = next(x for x in doc["law_references"] if x["law_id"] == lid)
        src = REPO / lref["canonical_source"]
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        assert lref["source_sha256"] == digest
        assert lref["law_reference_authority"] == "NONE"


def test_unclassified_reasons_reference_ucs_ids() -> None:
    doc = _doc()
    for row in doc["unclassified_current_surfaces"]:
        assert row["reason"].startswith("UCS-")


@pytest.mark.parametrize(
    "forbidden",
    [
        "src/trading/master_v2",
        "runtime/",
    ],
)
def test_forbidden_paths_not_modified(forbidden: str) -> None:
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD", "--", forbidden],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""
