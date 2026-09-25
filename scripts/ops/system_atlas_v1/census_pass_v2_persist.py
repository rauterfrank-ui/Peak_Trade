"""Persist FIND_COMPLETELY pass v2 ledger, coverage, and census status.

ATLAS_AUTHORITY=NONE. No disposition. No push.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ops.system_atlas_v1.census_inventory_v2 import schema_header
from scripts.ops.system_atlas_v1.census_pass_v2_records import coverage_row, pass_v2_records
from scripts.ops.system_atlas_v1.constants_v1 import RECONCILIATION_RELATIVE_ROOT

INV = "docs/system_atlas/reconciliation/inventories"


def _dump(path: Path, payload: dict) -> None:
    text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=120)
    path.write_text(
        "# ATLAS_AUTHORITY=NONE\n# RECONCILIATION_AUTHORITY=NONE\n" + text, encoding="utf-8"
    )


def persist_pass_v2(*, repo_root: Path) -> dict[str, int]:
    recon = repo_root / RECONCILIATION_RELATIVE_ROOT
    header = schema_header()
    header["bound_against_sha"] = "1b52df25b99a36b99eed91943c2a203ce84f1cad"

    summary = yaml.safe_load((recon / "inventories" / "summary.yaml").read_text(encoding="utf-8"))
    corpus = yaml.safe_load(
        (recon / "inventories" / "corpus_enumeration.yaml").read_text(encoding="utf-8")
    )
    hist = yaml.safe_load(
        (recon / "inventories" / "historical_path_families.yaml").read_text(encoding="utf-8")
    )
    tree = yaml.safe_load(
        (recon / "inventories" / "tree_content_census.yaml").read_text(encoding="utf-8")
    )
    symbols = yaml.safe_load(
        (recon / "inventories" / "import_symbol_census.yaml").read_text(encoding="utf-8")
    )
    terms = yaml.safe_load(
        (recon / "inventories" / "terminology_census.yaml").read_text(encoding="utf-8")
    )
    inner = yaml.safe_load(
        (recon / "inventories" / "inner_archive_peaktraderepo.yaml").read_text(encoding="utf-8")
    )
    reachable = yaml.safe_load(
        (recon / "inventories" / "reachable_object_paths.yaml").read_text(encoding="utf-8")
    )

    blob = {
        **header,
        "blob_level_scan_required": True,
        "blob_level_scan_performed": False,
        "blob_level_scan_scope": "none",
        "reason_required": (
            "After ref/tree/path/symbol/terminology census, symbols and headings that exist only "
            "inside historical non-tip blob contents remain unprovable. Path names of 19428 reachable "
            "objects are inventoried. Unique tip trees were delta-walked. This does not read blob "
            "contents of 7260 reachable commits."
        ),
        "reachable_commit_count_all_refs": 7260,
        "reachable_object_path_count": reachable["reachable_object_path_count"],
        "next_exhaustion_stage": "BLOB_LEVEL_COMMIT_CONTENT_SCAN",
    }
    _dump(recon / "inventories" / "blob_scan_decision.yaml", blob)

    ledger_path = recon / "ledger.yaml"
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    existing = list(ledger.get("records") or [])
    new_records = pass_v2_records()
    existing_ids = {
        str((rec.get("identity") or {}).get("reconciliation_id") or "") for rec in existing
    }
    added = [rec for rec in new_records if rec["identity"]["reconciliation_id"] not in existing_ids]
    ledger["records"] = existing + added
    ledger["ledger_record_count"] = len(ledger["records"])
    ledger["census_pass_id"] = "FIND_COMPLETELY_PASS_V2"
    _dump(ledger_path, ledger)

    relation_items = []
    for rec in ledger["records"]:
        rid = rec["identity"]["reconciliation_id"]
        for rel in (rec.get("relations") or {}).get("items") or []:
            relation_items.append({"from": rid, **rel})
    relations_doc = {
        **header,
        "relation_count": len(relation_items),
        "items": relation_items,
        "identity_merges_performed": 0,
        "note": "Copied from ledger. POSSIBLE_SAME_AS remains hypothesis until identity is proven.",
    }
    _dump(recon / "relations.yaml", relations_doc)

    candidates = {
        **header,
        "kind": "CANDIDATE_NOT_LEDGER_BOUND",
        "counted_as_ledger_records": False,
        "note": (
            "Hits below ledger threshold, or identity too weak for an RCN-ID. "
            "Promoted v0/docs/gate-family candidates were moved to the ledger as separate records."
        ),
        "candidates": [
            {
                "id": "CAND:functional_core_literal",
                "observed_names": ["FUNCTIONAL_CORE", "Functional Core"],
                "discovery_source": "SURF:atlas_index",
                "why_not_ledger_bound": (
                    "Atlas historical_terminology reports the literal token absent from origin/main "
                    "history. Absence is not a component."
                ),
                "evidence": ["docs/system_atlas/census/historical_terminology.yaml"],
                "current_presence": "CURRENT_IDENTITY_UNRESOLVED",
            },
            {
                "id": "CAND:ssot_child_literal",
                "observed_names": ["SSOT_CHILD", "SSOT child"],
                "discovery_source": "SURF:atlas_index",
                "why_not_ledger_bound": "Literal search reported no origin/main history hit.",
                "evidence": ["docs/system_atlas/census/historical_terminology.yaml"],
                "current_presence": "CURRENT_IDENTITY_UNRESOLVED",
            },
            {
                "id": "CAND:risk_hotfix_smoke_test",
                "observed_names": ["hotfix_smoke_test"],
                "historical_paths": ["src/risk/hotfix_smoke_test.py"],
                "discovery_source": "SURF:historical_path_family_src",
                "why_not_ledger_bound": "Single deleted test/helper file; not a named architecture component.",
                "evidence": ["git log --all --diff-filter=D -- src/risk/hotfix_smoke_test.py"],
                "current_presence": "CURRENTLY_ABSENT",
            },
            {
                "id": "CAND:position_sizer_old_backup",
                "observed_names": ["position_sizer_old_backup"],
                "historical_paths": ["src/risk/position_sizer_old_backup.py"],
                "discovery_source": "SURF:historical_path_family_src",
                "why_not_ledger_bound": "Filename marks a backup copy; identity/purpose unproven.",
                "evidence": [
                    "git log --all --diff-filter=D -- src/risk/position_sizer_old_backup.py"
                ],
                "current_presence": "CURRENTLY_ABSENT",
                "possible_same_as_open": ["RCN-000045"],
            },
            {
                "id": "CAND:local_branch_tip_inventory_is_not_a_component",
                "observed_names": ["local refs/heads"],
                "discovery_source": "SURF:local_branches",
                "why_not_ledger_bound": (
                    "Ref/tree inventory is coverage, not a component. Pass v2 walked unique local "
                    "tip trees. Remaining git-history blob contents are a coverage gap, not a ledger record."
                ),
                "evidence": [f"{INV}/ref_inventory.yaml", f"{INV}/unique_trees.yaml"],
                "current_presence": "CURRENT_IDENTITY_UNRESOLVED",
            },
            {
                "id": "CAND:src_risk_ci_gate_test",
                "observed_names": ["ci_gate_test"],
                "historical_paths": ["src/risk/ci_gate_test.py"],
                "discovery_source": "SURF:local_branches",
                "why_not_ledger_bound": "Single helper/test file on non-main tips; not a named architecture component.",
                "evidence": [f"{INV}/tree_content_census.yaml"],
                "current_presence": "CURRENTLY_ABSENT",
            },
            {
                "id": "CAND:src_docs_workflow_notes",
                "observed_names": ["Peak_Trade_WORKFLOW_NOTES.md"],
                "historical_paths": ["src/docs/Peak_Trade_WORKFLOW_NOTES.md"],
                "discovery_source": "SURF:local_branches",
                "why_not_ledger_bound": "Single misplaced documentation file under src/docs; not a runtime component.",
                "evidence": [f"{INV}/tree_content_census.yaml"],
                "current_presence": "CURRENTLY_ABSENT",
            },
        ],
    }
    _dump(recon / "discovery_candidates.yaml", candidates)

    rows = [
        coverage_row(
            surface_id="SURF:current_tree",
            surface_type="CURRENT_TREE",
            searched=True,
            method="git ls-tree -r of relevant prefixes on origin/main; first-level package listing",
            scope_count=int(sum((corpus.get("file_counts_origin_main") or {}).values())),
            evidence_reference=f"{INV}/corpus_enumeration.yaml",
            exhaustion_proven=True,
            remaining_gap="Not every file is a ledger record; that is identification policy.",
            exhaustion_unproven_reason="",
            limitations="Relevant prefixes only; ignored non-relevant root clutter as component sources.",
        ),
        coverage_row(
            surface_id="SURF:git_history_origin_main",
            surface_type="GIT_HISTORY",
            searched=True,
            method="git log origin/main --diff-filter=D --name-only; blob contents not read",
            scope_count=int(hist["deleted_path_count_origin_main"]),
            evidence_reference=f"{INV}/historical_path_families.yaml",
            exhaustion_proven=False,
            remaining_gap="Blob contents of origin/main commits were not scanned.",
            exhaustion_unproven_reason="Path-name deletion census is not blob-level content exhaustion.",
            limitations="Deleted paths listed; historical blob contents unread.",
        ),
        coverage_row(
            surface_id="SURF:git_history_all_reachable",
            surface_type="GIT_HISTORY",
            searched=True,
            method="git rev-list --objects --all path inventory; unique tip-tree delta vs origin/main",
            scope_count=int(reachable["reachable_object_path_count"]),
            evidence_reference=f"{INV}/reachable_object_paths.yaml",
            exhaustion_proven=False,
            remaining_gap="Blob contents of 7260 reachable commits were not scanned.",
            exhaustion_unproven_reason="Object path inventory is not blob-level content exhaustion.",
            limitations="Path names bound; per-commit blob contents unread.",
        ),
        coverage_row(
            surface_id="SURF:local_branches",
            surface_type="LOCAL_BRANCH",
            searched=True,
            method="git for-each-ref refs/heads + unique tip tree SHA + relevant-path delta vs origin/main",
            scope_count=int(summary["local_branch_count"]),
            evidence_reference=f"{INV}/ref_inventory.yaml",
            exhaustion_proven=True,
            remaining_gap="Tip trees exhausted; intermediate non-tip commits belong to GIT_HISTORY.",
            exhaustion_unproven_reason="",
            limitations="Bound space is local branch tips, not full branch histories.",
        ),
        coverage_row(
            surface_id="SURF:origin_branches",
            surface_type="REMOTE_BRANCH",
            searched=True,
            method="git for-each-ref refs/remotes/origin + unique tip tree SHA + relevant-path delta",
            scope_count=int(summary["origin_remote_branch_count"]),
            evidence_reference=f"{INV}/ref_inventory.yaml",
            exhaustion_proven=True,
            remaining_gap="Tip trees exhausted; intermediate origin commits belong to GIT_HISTORY.",
            exhaustion_unproven_reason="",
            limitations="Bound space is origin remote tips.",
        ),
        coverage_row(
            surface_id="SURF:tags",
            surface_type="TAG",
            searched=True,
            method="git for-each-ref refs/tags + unique peeled tip tree SHA + relevant-path delta",
            scope_count=int(summary["tag_count"]),
            evidence_reference=f"{INV}/ref_inventory.yaml",
            exhaustion_proven=True,
            remaining_gap="Tag tip trees exhausted; tag-pointed commit bodies not blob-scanned.",
            exhaustion_unproven_reason="",
            limitations="Bound space is tag tip trees.",
        ),
        coverage_row(
            surface_id="SURF:historical_path_family_src",
            surface_type="HISTORICAL_PATH_FAMILY",
            searched=True,
            method="git log --all --diff-filter=D/R plus reachable object src families",
            scope_count=len(hist.get("deleted_src_paths") or []),
            evidence_reference=f"{INV}/historical_path_families.yaml",
            exhaustion_proven=True,
            remaining_gap="Named deleted/renamed src paths bound; blob contents unread.",
            exhaustion_unproven_reason="",
            limitations="Name-status census, not content understanding.",
        ),
        coverage_row(
            surface_id="SURF:historical_path_family_docs",
            surface_type="HISTORICAL_PATH_FAMILY",
            searched=True,
            method="git log --all --diff-filter=D/R docs families plus tip-tree added docs paths",
            scope_count=int(hist["deleted_path_count_all_refs"]),
            evidence_reference=f"{INV}/historical_path_families.yaml",
            exhaustion_proven=True,
            remaining_gap="Named deleted docs paths bound; markdown contents not mined for purpose.",
            exhaustion_unproven_reason="",
            limitations="Path-family inventory, not document understanding.",
        ),
        coverage_row(
            surface_id="SURF:evidence_corpus",
            surface_type="EVIDENCE_CORPUS",
            searched=True,
            method="git ls-tree evidence/ plus evidence/ops pack directory file counts",
            scope_count=int(corpus["evidence_ops_pack_count"]),
            evidence_reference=f"{INV}/corpus_enumeration.yaml",
            exhaustion_proven=True,
            remaining_gap="Pack contents were counted, not semantically opened as components.",
            exhaustion_unproven_reason="",
            limitations="Directory/file-count inventory of origin/main evidence/.",
        ),
        coverage_row(
            surface_id="SURF:forensic_corpus",
            surface_type="FORENSIC_CORPUS",
            searched=True,
            method="git ls-tree forensics/, forensic/, docs/forensics, docs/forensic",
            scope_count=int(
                corpus["file_counts_origin_main"]["forensics"]
                + corpus["file_counts_origin_main"]["forensic"]
            ),
            evidence_reference=f"{INV}/corpus_enumeration.yaml",
            exhaustion_proven=True,
            remaining_gap="LOSS_REGISTER derived blobs remain out of repository-internal scope.",
            exhaustion_unproven_reason="",
            limitations="In-repo forensic directory inventory only.",
        ),
        coverage_row(
            surface_id="SURF:archived_code",
            surface_type="ARCHIVED_CODE",
            searched=True,
            method="ls-tree archive/PeakTradeRepo plus added-path listing of other archive/ trees",
            scope_count=int(inner["file_count"]),
            evidence_reference=f"{INV}/inner_archive_peaktraderepo.yaml",
            exhaustion_proven=True,
            remaining_gap="Inner file contents were inventoried, not understood.",
            exhaustion_unproven_reason="",
            limitations="File inventory of nested archive trees in reachable history.",
        ),
        coverage_row(
            surface_id="SURF:archived_docs",
            surface_type="ARCHIVED_DOCS",
            searched=True,
            method="deleted docs/product and docs/observability plus archive/legacy_docs path inventory",
            scope_count=len(hist.get("deleted_docs_families") or {}),
            evidence_reference=f"{INV}/historical_path_families.yaml",
            exhaustion_proven=True,
            remaining_gap="Deleted markdown bodies not mined for purpose.",
            exhaustion_unproven_reason="",
            limitations="Path inventory of archived/deleted docs families.",
        ),
        coverage_row(
            surface_id="SURF:test_corpus",
            surface_type="TEST_CORPUS",
            searched=True,
            method="origin/main tests/ first-level listing plus deleted tests path families",
            scope_count=int(corpus["file_counts_origin_main"]["tests"]),
            evidence_reference=f"{INV}/corpus_enumeration.yaml",
            exhaustion_proven=True,
            remaining_gap="Tests remain evidence pointers; not individually ledger-bound as components.",
            exhaustion_unproven_reason="",
            limitations="Path inventory, not every test as a component.",
        ),
        coverage_row(
            surface_id="SURF:tooling_corpus",
            surface_type="TOOLING_CORPUS",
            searched=True,
            method="origin/main scripts/ first-level listing plus deleted scripts path families",
            scope_count=int(corpus["file_counts_origin_main"]["scripts"]),
            evidence_reference=f"{INV}/corpus_enumeration.yaml",
            exhaustion_proven=True,
            remaining_gap="Historical deleted scripts listed by family; not every script is a component.",
            exhaustion_unproven_reason="",
            limitations="Path inventory of tooling.",
        ),
        coverage_row(
            surface_id="SURF:manifest_index",
            surface_type="MANIFEST_INDEX",
            searched=True,
            method="origin/main ls-tree paths whose names contain MANIFEST",
            scope_count=int(corpus["manifest_path_count"]),
            evidence_reference=f"{INV}/corpus_enumeration.yaml",
            exhaustion_proven=True,
            remaining_gap="Manifest files listed; contents not imported as components.",
            exhaustion_unproven_reason="",
            limitations="Filename inventory, not manifest-body census.",
        ),
        coverage_row(
            surface_id="SURF:atlas_index",
            surface_type="ATLAS_INDEX",
            searched=True,
            method="path inventory of docs/system_atlas YAML; Atlas COMPLETE flags ignored",
            scope_count=int(corpus["atlas_yaml_count"]),
            evidence_reference=f"{INV}/corpus_enumeration.yaml",
            exhaustion_proven=True,
            remaining_gap="Atlas YAML paths listed. Atlas COMPLETE flags are not reconciliation exhaustion.",
            exhaustion_unproven_reason="",
            limitations="Navigation only. census_meta SHA remains stale relative to origin/main.",
        ),
        coverage_row(
            surface_id="SURF:commit_messages",
            surface_type="GIT_HISTORY",
            searched=True,
            method="pass v1 seed grep plus pass v2 path/token census; commit bodies not fully scanned",
            scope_count=int(summary["reachable_object_path_count"]),
            evidence_reference=f"{INV}/blob_scan_decision.yaml",
            exhaustion_proven=False,
            remaining_gap="Commit message bodies of 7260 reachable commits were not exhaustively tokenized.",
            exhaustion_unproven_reason="Subject/body blob scan was not this pass's bound completed space.",
            limitations="Seed grep plus path/token census; unknown names in commit bodies remain.",
        ),
    ]
    proven = sum(1 for row in rows if row["exhaustion_proven"] is True)
    unproven = len(rows) - proven
    coverage = {
        **header,
        "census_status": "CENSUS_IN_PROGRESS",
        "exhaustion_proven": False,
        "census_closed": False,
        "surfaces_exhaustion_proven": proven,
        "surfaces_exhaustion_unproven": unproven,
        "open_coverage_gaps": [
            "Blob-level scan of 7260 reachable commits not performed.",
            "Commit message bodies not exhaustively tokenized.",
            "Import/symbol census of historical non-tip blobs not performed.",
            "Terminology census of historical blob contents beyond current headings and path tokens not performed.",
            "Atlas census_meta SHA stale; COMPLETE flags ignored for exhaustion.",
            "LOSS_REGISTER derived blobs remain out of repository-internal scope.",
        ],
        "tree_content_census_count": int(tree["unique_added_relevant_path_count"]),
        "historical_path_family_count": int(summary["historical_path_family_count"]),
        "import_symbol_census_count": int(symbols["current_class_count"]),
        "terminology_candidate_count": int(terms["current_heading_token_count"]),
        "inner_archive_file_count": int(inner["file_count"]),
        "rows": rows,
    }
    _dump(recon / "coverage.yaml", coverage)

    surfaces = yaml.safe_load((recon / "search_surfaces.yaml").read_text(encoding="utf-8"))
    surfaces["census_pass_id"] = "FIND_COMPLETELY_PASS_V2"
    surfaces["exhaustion_proven"] = False
    surfaces["unique_local_branch_tree_count"] = summary["unique_local_branch_tree_count"]
    surfaces["unique_origin_branch_tree_count"] = summary["unique_origin_branch_tree_count"]
    surfaces["unique_tag_tree_count"] = summary["unique_tag_tree_count"]
    surfaces["union_unique_tip_tree_count"] = summary["union_unique_tip_tree_count"]
    surfaces["reachable_object_path_count"] = summary["reachable_object_path_count"]
    surfaces["note"] = (
        "Pass v2 bound and walked unique tip trees by exact tree SHA, inventoried reachable "
        "object path names, and file-inventoried archive/PeakTradeRepo. Git-history blob contents "
        "remain unproven. Census is not closed."
    )
    by_id = {row["surface_id"]: row for row in rows}
    for surf in surfaces.get("surfaces") or []:
        cov = by_id.get(surf.get("id"))
        if not cov:
            continue
        surf["coverage_method"] = cov["method"]
        surf["coverage_status"] = "SEARCHED" if cov["exhaustion_proven"] else "PARTIALLY_SEARCHED"
        surf["exhaustion_proven"] = cov["exhaustion_proven"]
        surf["remaining_gap"] = cov["remaining_gap"]
        surf["evidence_pointer"] = cov["evidence_reference"]
        surf["known_limitations"] = [cov["limitations"]]
        if cov["exhaustion_unproven_reason"]:
            surf["known_limitations"].append(cov["exhaustion_unproven_reason"])
    _dump(recon / "search_surfaces.yaml", surfaces)

    census = yaml.safe_load((recon / "census_status.yaml").read_text(encoding="utf-8"))
    census["census_status"] = "CENSUS_IN_PROGRESS"
    census["census_exhaustion_proven"] = False
    census["census_closed"] = False
    census["search_universe_bound"] = True
    census["historical_census_performed"] = True
    census["census_pass_id"] = "FIND_COMPLETELY_PASS_V2"
    census["surfaces_exhaustion_proven"] = proven
    census["surfaces_exhaustion_unproven"] = unproven
    census["exhaustion_evidence"] = [
        f"{INV}/ref_inventory.yaml",
        f"{INV}/unique_trees.yaml",
        f"{INV}/tree_content_census.yaml",
        f"{INV}/inner_archive_peaktraderepo.yaml",
        f"{INV}/corpus_enumeration.yaml",
        f"{INV}/blob_scan_decision.yaml",
    ]
    census["note"] = (
        "FIND_COMPLETELY pass v2. Unique tip trees walked by exact SHA. Inner archive "
        "file-inventoried. Census not closed: git-history blob contents remain unproven."
    )
    _dump(recon / "census_status.yaml", census)

    return {
        "ledger_record_count": ledger["ledger_record_count"],
        "new_ledger_record_count": len(added),
        "candidate_count": len(candidates["candidates"]),
        "relation_count": len(relation_items),
        "surfaces_exhaustion_proven": proven,
        "surfaces_exhaustion_unproven": unproven,
    }


if __name__ == "__main__":
    stats = persist_pass_v2(repo_root=Path(__file__).resolve().parents[3])
    print(stats)
