"""CI-safe checks against git-tracked alignment-index artifacts."""

from __future__ import annotations

import json
from pathlib import Path

REPO_DIR = Path(
    "forensics/derived/FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_CANDIDATE_ALIGNMENT_INDEX_V1"
)


def test_git_tracked_alignment_artifacts_are_non_authoritative() -> None:
    assert REPO_DIR.is_dir()
    counts = json.loads((REPO_DIR / "counts.json").read_text(encoding="utf-8"))
    residual = json.loads((REPO_DIR / "residual_status.json").read_text(encoding="utf-8"))
    header = json.loads((REPO_DIR / "alignment_index_header.json").read_text(encoding="utf-8"))
    authority = (REPO_DIR / "AUTHORITY_NONE.txt").read_text(encoding="utf-8")
    contract = json.loads((REPO_DIR / "generation_contract.json").read_text(encoding="utf-8"))
    determinism = json.loads((REPO_DIR / "determinism_report.json").read_text(encoding="utf-8"))
    idempotence = json.loads((REPO_DIR / "idempotence_report.json").read_text(encoding="utf-8"))
    non_identity = json.loads((REPO_DIR / "non_identity_audit.json").read_text(encoding="utf-8"))
    evidence = json.loads((REPO_DIR / "evidence_edge_report.json").read_text(encoding="utf-8"))
    assert counts["T4_RECORD_COUNT"] == 7175
    assert counts["LAYER3_RELATION_COUNT"] == 122
    assert counts["ENDPOINT_RECORD_COUNT"] == 244
    assert counts["VIEW_COUNT"] == 12
    assert counts["OCCURRENCE_BINDING_PROVEN_COUNT"] == 0
    assert counts["PROVEN_PARENTAGE_COUNT"] == 0
    assert counts["WINNER_SELECTED_COUNT"] == 0
    assert counts["SEMANTIC_BINDING_PERFORMED"] is False
    assert counts["CURRENTNESS_ADJUDICATION_PERFORMED"] is False
    assert counts["SUPERSESSION_ADJUDICATION_PERFORMED"] is False
    assert residual["SW-R-002"] == "OPEN"
    assert residual["SW-R-004"] == "OPEN"
    assert residual["SW-R-009"] == "OPEN"
    assert header["authority"] == "NONE"
    assert header["output_canonical"] is False
    assert "AUTHORITY=NONE" in authority
    assert "OUTPUT_CANONICAL=false" in authority
    assert contract["output_canonical"] is False
    assert contract["timestamps_in_hash_bound_outputs"] is False
    assert contract["hash_sort_as_semantic_order"] is False
    assert determinism["status"] == "PASS"
    assert idempotence["status"] == "PASS"
    assert non_identity["PRESERVED"] is True
    assert non_identity["COLLAPSED_COUNT"] == 0
    assert evidence["CLOSE_ORDER_TRUE_COUNT"] == 0
    assert evidence["MISSING_EVIDENCE_CLASS_COUNT"] == 0
    manifest_txt = (REPO_DIR / "MANIFEST_SHA256.txt").read_text(encoding="utf-8")
    assert "MANIFEST_SHA256=" in manifest_txt
    catalog = json.loads((REPO_DIR / "dataset_catalog.json").read_text(encoding="utf-8"))
    assert "t4_overlay_records.json" in catalog["shard_sha256s"]
    assert catalog["output_canonical"] is False
