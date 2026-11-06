"""CI-safe checks against git-tracked adjudication-contract artifacts."""

from __future__ import annotations

import json
from pathlib import Path

REPO_DIR = Path("forensics/derived/FORENSIC_STRUCTURE_SCHEMA_V1_ADJUDICATION_CONTRACT_V1")
ALIGNMENT_DIR = Path(
    "forensics/derived/FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_CANDIDATE_ALIGNMENT_INDEX_V1"
)
DISPOSITION_DIR = Path("forensics/derived/FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_DISPOSITION_V1")
TRANSFORMATION_DIR = Path("forensics/derived/FORENSIC_STRUCTURE_SCHEMA_V1_TRANSFORMATION_V1")


def test_git_tracked_adjudication_artifacts_are_non_authoritative() -> None:
    assert REPO_DIR.is_dir()
    counts = json.loads((REPO_DIR / "counts.json").read_text(encoding="utf-8"))
    residual = json.loads((REPO_DIR / "residual_status.json").read_text(encoding="utf-8"))
    header = json.loads(
        (REPO_DIR / "adjudication_contract_header.json").read_text(encoding="utf-8")
    )
    authority = (REPO_DIR / "AUTHORITY_NONE.txt").read_text(encoding="utf-8")
    contract = json.loads((REPO_DIR / "generation_contract.json").read_text(encoding="utf-8"))
    determinism = json.loads((REPO_DIR / "determinism_report.json").read_text(encoding="utf-8"))
    idempotence = json.loads((REPO_DIR / "idempotence_report.json").read_text(encoding="utf-8"))
    audit = json.loads((REPO_DIR / "non_inference_audit.json").read_text(encoding="utf-8"))
    families = json.loads((REPO_DIR / "family_inventory.json").read_text(encoding="utf-8"))
    competing = json.loads((REPO_DIR / "competing_set_graph.json").read_text(encoding="utf-8"))
    results = json.loads(
        (REPO_DIR / "candidate_adjudication_results.json").read_text(encoding="utf-8")
    )
    decisions = json.loads(
        (REPO_DIR / "adjudication_decision_records.json").read_text(encoding="utf-8")
    )
    boundaries = json.loads((REPO_DIR / "execution_boundaries.json").read_text(encoding="utf-8"))
    assert counts["OCCURRENCE_BINDING_CANDIDATE_COUNT"] == 244
    assert counts["CANDIDATE_FAMILY_COUNT"] == 11
    assert counts["COMPETING_CANDIDATE_SET_COUNT"] == 8
    assert counts["COMPETING_CANDIDATE_MEMBER_COUNT"] == 18
    assert counts["ORIGINAL_AMBIGUOUS_BINDING_CANDIDATE_COUNT"] == 6
    assert counts["PROVEN_OCCURRENCE_IDENTITY_COUNT"] == 0
    assert counts["PROVEN_PARENTAGE_COUNT"] == 0
    assert counts["WINNER_SELECTED_COUNT"] == 0
    assert counts["CURRENTNESS_ADJUDICATION_PERFORMED"] is False
    assert counts["SUPERSESSION_ADJUDICATION_PERFORMED"] is False
    assert counts["RESIDUAL_CLOSE_PERFORMED"] is False
    assert residual["SW-R-002"] == "OPEN"
    assert residual["SW-R-004"] == "OPEN"
    assert residual["SW-R-009"] == "OPEN"
    assert header["authority"] == "NONE"
    assert header["output_canonical"] is False
    assert "AUTHORITY=NONE" in authority
    assert "OUTPUT_CANONICAL=false" in authority
    assert contract["output_canonical"] is False
    assert contract["timestamps_in_hash_bound_outputs"] is False
    assert contract["positive_occurrence_identity_authorized"] is False
    assert determinism["status"] == "PASS"
    assert idempotence["status"] == "PASS"
    assert audit["NO_BIND_FROM_ALIAS_ONLY"] is True
    assert audit["NO_CANONICALIZATION"] is True
    assert families["CANDIDATE_FAMILY_COUNT"] == 11
    assert len(competing) == 8
    assert len(results) == 244
    assert len(decisions) == 244 * 15
    assert all(row["authority"] == "NONE" for row in results)
    assert all(row["output_canonical"] is False for row in decisions)
    assert all(row["outcome"] != "PROVEN_OCCURRENCE_IDENTITY" for row in decisions)
    proven_occ = [row for row in results if row["occurrence_binding_proven"]]
    assert proven_occ == []
    assert boundaries["this_go_authorizes_boundaries_b_through_h"] is False
    assert boundaries["this_go_authorizes_boundary_a_semantic_execution"] is False
    assert len(boundaries["boundaries"]) == 8
    manifest_txt = (REPO_DIR / "MANIFEST_SHA256.txt").read_text(encoding="utf-8")
    assert "MANIFEST_SHA256=" in manifest_txt


def test_prior_forensic_structure_artifacts_remain_non_authoritative() -> None:
    align_counts = json.loads((ALIGNMENT_DIR / "counts.json").read_text(encoding="utf-8"))
    disp_residual = json.loads(
        (DISPOSITION_DIR / "residual_status.json").read_text(encoding="utf-8")
    )
    transform_residual = json.loads(
        (TRANSFORMATION_DIR / "residual_register.json").read_text(encoding="utf-8")
    )
    assert align_counts["ENDPOINT_RECORD_COUNT"] == 244
    assert align_counts["OCCURRENCE_BINDING_PROVEN_COUNT"] == 0
    assert disp_residual["SW-R-002"] == "OPEN"
    assert disp_residual["SW-R-004"] == "OPEN"
    assert disp_residual["SW-R-009"] == "OPEN"
    open_ids = {
        row["residual_id"] for row in transform_residual["records"] if row["status"] == "OPEN"
    }
    assert "SW-R-002" in open_ids
    assert "SW-R-004" in open_ids
    assert "SW-R-009" in open_ids
    assert transform_residual["residuals_auto_closed"] is False
