"""Census pass v1 contracts. Discovery/evidence-binding only."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ops.system_atlas_v1.census_inventory_v2 import (
    collect_ref_inventory,
    unique_trees_by_group,
)
from scripts.ops.system_atlas_v1.reconciliation_v1 import (
    load_reconciliation_v1,
    validate_reconciliation_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_LIFECYCLE = frozenset({"DISCOVERED", "EVIDENCE_BOUND"})
FORBIDDEN_LIFECYCLE = frozenset(
    {
        "PURPOSE_UNDERSTOOD",
        "CURRENT_SYSTEM_COMPARED",
        "ADJUDICATED",
        "DISPOSITION_DECIDED",
        "REINTEGRATED",
        "COVERED",
        "INCOMPATIBLE",
        "REJECTED",
    }
)


def _payload() -> dict:
    return load_reconciliation_v1(repo_root=REPO_ROOT)


def test_census_pass_v1_live_tree_valid() -> None:
    payload = _payload()
    assert validate_reconciliation_v1(payload) == []


def test_census_pass_v1_lifecycle_and_epistemic_bounds() -> None:
    payload = _payload()
    ledger = payload["records"]["ledger.yaml"]
    records = list(ledger.get("records") or [])
    assert ledger["ledger_record_count"] == len(records)
    assert len(records) > 0
    purpose_true = 0
    compared = 0
    adjudicated = 0
    dispositioned = 0
    for rec in records:
        understanding = rec.get("understanding") or {}
        adjudication = rec.get("adjudication") or {}
        comparison = rec.get("current_comparison") or {}
        integration = rec.get("integration") or {}
        lifecycle = str(adjudication.get("lifecycle_state") or "")
        assert lifecycle in ALLOWED_LIFECYCLE
        assert lifecycle not in FORBIDDEN_LIFECYCLE
        assert understanding.get("purpose_understood") is False
        assert str(understanding.get("purpose_statement") or "") == ""
        assert str(adjudication.get("disposition") or "") == ""
        assert integration.get("reintegration_required") is False
        assert str(comparison.get("current_equivalent") or "") == ""
        assert list(comparison.get("current_paths") or []) == []
        if understanding.get("purpose_understood") is True:
            purpose_true += 1
        if str(comparison.get("capability_overlap") or ""):
            compared += 1
        if lifecycle in {"ADJUDICATED", "DISPOSITION_DECIDED"}:
            adjudicated += 1
        if str(adjudication.get("disposition") or ""):
            dispositioned += 1
    assert purpose_true == 0
    assert compared == 0
    assert adjudicated == 0
    assert dispositioned == 0


def test_census_pass_v1_artifacts_and_anchors() -> None:
    payload = _payload()
    census = payload["records"]["census_status.yaml"]
    assert census["search_universe_bound"] is True
    assert census["census_closed"] is True
    assert census["census_exhaustion_proven"] is True
    assert census["census_status"] == "CENSUS_CLOSED"
    for rel in (
        "search_surfaces.yaml",
        "coverage.yaml",
        "discovery_candidates.yaml",
        "relations.yaml",
    ):
        assert rel in payload["records"]
    candidates = payload["records"]["discovery_candidates.yaml"]
    assert candidates.get("counted_as_ledger_records") is False
    assert str(candidates.get("kind") or "") == "CANDIDATE_NOT_LEDGER_BOUND"
    anchors = payload["records"]["search_anchors.yaml"]
    assert anchors["counted_as_ledger_records"] is False
    assert anchors["anchors_are_not_census_boundaries"] is True
    coverage = payload["records"]["coverage.yaml"]
    assert coverage.get("exhaustion_proven") is True
    assert coverage.get("census_closed") is True
    assert int(coverage.get("surfaces_exhaustion_unproven") or 0) == 0
    assert int(coverage.get("surfaces_exhaustion_proven") or 0) == 17


def test_census_pass_v2_no_identity_fusion_or_disposition() -> None:
    payload = _payload()
    ledger = payload["records"]["ledger.yaml"]
    fusion_types = {"MERGED_INTO", "RENAMED_TO", "SPLIT_INTO"}
    psa = 0
    for rec in ledger["records"]:
        rid = rec["identity"]["reconciliation_id"]
        discovery = rec["discovery"]
        evidence = list(discovery.get("discovery_evidence") or [])
        claims = list(discovery.get("claims") or rec.get("claims") or [])
        claim_evidence = []
        for claim in claims:
            if isinstance(claim, dict):
                claim_evidence.extend(list(claim.get("evidence") or []))
        assert evidence or claim_evidence, rid
        for rel in (rec.get("relations") or {}).get("items") or []:
            rtype = str(rel.get("relation_type") or "")
            assert rtype not in fusion_types, rid
            if rtype == "POSSIBLE_SAME_AS":
                psa += 1
                assert str(rel.get("epistemic_status") or "") == "HYPOTHESIS", rid
    relations = payload["records"]["relations.yaml"]
    assert int(relations.get("identity_merges_performed") or 0) == 0
    assert psa == sum(
        1
        for item in relations.get("items") or []
        if item.get("relation_type") == "POSSIBLE_SAME_AS"
    )


def test_census_pass_v2_coverage_and_reproducible_tip_trees() -> None:
    payload = _payload()
    coverage = payload["records"]["coverage.yaml"]
    rows = list(coverage.get("rows") or [])
    assert len(rows) == 17
    proven = [row for row in rows if row.get("exhaustion_proven") is True]
    unproven = [row for row in rows if row.get("exhaustion_proven") is False]
    assert len(proven) == int(coverage["surfaces_exhaustion_proven"])
    assert len(unproven) == int(coverage["surfaces_exhaustion_unproven"])
    assert coverage["census_closed"] is True
    assert len(proven) == 17
    assert len(unproven) == 0
    for row in proven:
        assert row.get("searched") is True
        assert str(row.get("evidence_reference") or row.get("evidence_ref") or "")
        evidence = REPO_ROOT / str(row.get("evidence_reference") or row.get("evidence_ref"))
        assert evidence.is_file(), str(evidence)
    for row in unproven:
        assert str(row.get("remaining_gap") or "")
        assert str(row.get("exhaustion_unproven_reason") or row.get("limitations") or "")

    inventory = collect_ref_inventory(repo_root=REPO_ROOT)
    grouped = unique_trees_by_group(inventory)
    summary = yaml.safe_load(
        (REPO_ROOT / "docs/system_atlas/reconciliation/inventories/summary.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert len(grouped["local"]) == int(summary["unique_local_branch_tree_count"])
    assert len(grouped["origin"]) == int(summary["unique_origin_branch_tree_count"])
    assert len(grouped["tag"]) == int(summary["unique_tag_tree_count"])
    inner = yaml.safe_load(
        (
            REPO_ROOT
            / "docs/system_atlas/reconciliation/inventories/inner_archive_peaktraderepo.yaml"
        ).read_text(encoding="utf-8")
    )
    assert int(inner["file_count"]) == len(inner["files"]) == 16
    blob = yaml.safe_load(
        (
            REPO_ROOT / "docs/system_atlas/reconciliation/inventories/blob_scan_decision.yaml"
        ).read_text(encoding="utf-8")
    )
    assert blob["blob_level_scan_performed"] is True
    assert str(blob.get("blob_level_scan_scope") or "") != "none"
    candidates = payload["records"]["discovery_candidates.yaml"]
    assert candidates["counted_as_ledger_records"] is False
    assert len(list(candidates.get("candidates") or [])) == 7


def test_census_pass_v3_bound_universes_and_blob_sha_dedup() -> None:
    from scripts.ops.system_atlas_v1.census_blob_v3 import (
        BOUND_REV_LIST_ARGS,
        _parse_objects,
        classify_blob,
        commit_shas,
        sha256_sorted,
        unique_blob_index,
    )

    universe = yaml.safe_load(
        (REPO_ROOT / "docs/system_atlas/reconciliation/inventories/git_universe_v3.yaml").read_text(
            encoding="utf-8"
        )
    )
    summary = yaml.safe_load(
        (REPO_ROOT / "docs/system_atlas/reconciliation/inventories/pass_v3_summary.yaml").read_text(
            encoding="utf-8"
        )
    )
    scope = yaml.safe_load(
        (REPO_ROOT / "docs/system_atlas/reconciliation/inventories/blob_scope_v3.yaml").read_text(
            encoding="utf-8"
        )
    )
    messages = yaml.safe_load(
        (
            REPO_ROOT / "docs/system_atlas/reconciliation/inventories/commit_messages_v3.yaml"
        ).read_text(encoding="utf-8")
    )
    main = commit_shas(repo_root=REPO_ROOT, args=["origin/main"])
    bound = commit_shas(repo_root=REPO_ROOT, args=list(BOUND_REV_LIST_ARGS))
    all_refs = commit_shas(repo_root=REPO_ROOT, args=["--all"])
    assert len(main) == int(summary["reachable_commit_count_origin_main"])
    assert len(bound) == int(summary["reachable_commit_count_all_bound"])
    assert len(bound) < len(all_refs)
    assert int(universe["commits_only_on_extra_local_refs_count"]) == len(
        set(all_refs) - set(bound)
    )
    assert int(messages["commit_message_count"]) == len(bound)
    assert messages["commit_message_count_matches_bound_commits"] is True
    assert int(messages["commit_message_with_body_count"]) > 0

    blobs_main = unique_blob_index(repo_root=REPO_ROOT, rev_list_args=["origin/main"])
    assert len(blobs_main) == int(scope["unique_blob_count_origin_main"])
    assert sha256_sorted(blobs_main) == scope["blob_sha_digest_origin_main"]
    assert int(scope["unique_non_main_blob_count"]) > 0
    sample = list(scope.get("non_main_blob_sample") or [])
    assert sample
    assert any(row.get("sample_commit_shas") for row in sample)

    parsed = _parse_objects("abc123 path/one.py\nabc123 path/two.py\ndef456 other.py\n")
    assert parsed["abc123"] == {"path/one.py", "path/two.py"}
    assert classify_blob(["src/a.py", "src/b.py"], 10) == "relevant_text"
    assert classify_blob(["foo.png"], 10) == "excluded_binary"
    relevant = int(scope["unique_relevant_text_blob_count"])
    binary = int(scope["excluded_binary_blob_count"])
    vendor = int(scope["excluded_generated_or_vendor_blob_count"])
    other = int(scope["other_excluded_blob_count"])
    assert relevant + binary + vendor + other == int(scope["unique_blob_count_total"])
    assert scope["name_based_dedup_forbidden"] is True


def test_census_pass_v3_candidates_have_blob_or_path_provenance() -> None:
    payload = _payload()
    candidates = payload["records"]["discovery_candidates.yaml"]["candidates"]
    assert len(candidates) == 7
    for cand in candidates:
        evidence = list(cand.get("evidence") or [])
        assert evidence, cand["id"]
        has_blob = bool(cand.get("blob_sha")) or any(
            str(item).startswith("blob:") for item in evidence
        )
        has_path = bool(cand.get("historical_paths")) or any(
            "origin/main:" in str(item) or str(item).endswith(".yaml") for item in evidence
        )
        assert has_blob or has_path, cand["id"]
        assert "disposition" not in cand
    relations = payload["records"]["relations.yaml"]
    assert int(relations.get("identity_merges_performed") or 0) == 0
    ledger = payload["records"]["ledger.yaml"]
    assert ledger["ledger_record_count"] == 53
    ids = {rec["identity"]["reconciliation_id"] for rec in ledger["records"]}
    assert "RCN-000053" in ids
    for rec in ledger["records"]:
        understanding = rec["understanding"]
        assert understanding["purpose_understood"] is False
        assert rec["adjudication"]["disposition"] == ""
        assert rec["current_comparison"]["current_equivalent"] == ""


def test_census_pass_v3_close_requires_seventeen_proven_surfaces() -> None:
    payload = _payload()
    coverage = payload["records"]["coverage.yaml"]
    rows = list(coverage.get("rows") or [])
    proven = [row for row in rows if row.get("exhaustion_proven") is True]
    assert len(rows) == 17
    assert len(proven) == 17
    for row in proven:
        evidence = REPO_ROOT / str(row.get("evidence_reference") or row.get("evidence_ref"))
        assert evidence.is_file(), str(evidence)
    census = payload["records"]["census_status.yaml"]
    assert census["census_closed"] is True
    assert census["census_exhaustion_proven"] is True
    for rel in (
        "inventories/git_universe_v3.yaml",
        "inventories/blob_scope_v3.yaml",
        "inventories/commit_messages_v3.yaml",
        "inventories/pass_v3_summary.yaml",
        "inventories/candidate_class_adjudication_v3.yaml",
    ):
        assert (REPO_ROOT / "docs/system_atlas/reconciliation" / rel).is_file()


def test_census_cannot_close_when_a_surface_is_unproven() -> None:
    from scripts.ops.system_atlas_v1.reconciliation_v1 import (
        ReconciliationValidationError,
        validate_reconciliation_v1,
    )

    payload = _payload()
    import copy

    cloned = copy.deepcopy(payload)
    cloned["records"]["census_status.yaml"]["census_closed"] = True
    cloned["records"]["census_status.yaml"]["census_status"] = "CENSUS_CLOSED"
    cloned["records"]["census_status.yaml"]["census_exhaustion_proven"] = True
    coverage = cloned["records"]["coverage.yaml"]
    coverage["rows"][1]["exhaustion_proven"] = False
    coverage["rows"][1]["remaining_gap"] = "forced"
    coverage["rows"][1]["exhaustion_unproven_reason"] = "forced"
    coverage["surfaces_exhaustion_proven"] = 16
    coverage["surfaces_exhaustion_unproven"] = 1
    coverage["census_closed"] = True
    raised = False
    try:
        validate_reconciliation_v1(cloned)
    except ReconciliationValidationError as exc:
        raised = True
        assert "CENSUS_CLOSED_WITH_UNPROVEN_SURFACES" in str(exc)
    assert raised is True
