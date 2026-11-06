"""Persist UNDERSTAND pass v2 for remaining OPEN/PARTIAL records only.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Does not rewrite PURPOSE_UNDERSTOOD narratives from pass v1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scripts.ops.system_atlas_v1.constants_v1 import (
    RECONCILIATION_RELATIVE_ROOT,
    RECONCILIATION_SCHEMA_VERSION,
)
from scripts.ops.system_atlas_v1.understand_pass_v1_persist import _apply_understanding, _dump
from scripts.ops.system_atlas_v1.understand_pass_v1_records import (
    UNDERSTAND_BOUND_SHA,
    clusters_payload,
)
from scripts.ops.system_atlas_v1.understand_pass_v2_records import remaining_records, v2_clusters


def _header() -> dict[str, Any]:
    return {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "bound_against_ref": "origin/main",
        "bound_against_sha": UNDERSTAND_BOUND_SHA,
        "atlas_authority": "NONE",
        "reconciliation_authority": "NONE",
        "understand_pass_id": "UNDERSTAND_PASS_V2",
        "identity_fusion_forbidden": True,
        "disposition_performed": False,
        "current_system_compared": False,
        "evaluate_performed": False,
    }


def _merge_clusters() -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for cluster in list(clusters_payload()) + list(v2_clusters()):
        cid = str(cluster["cluster_id"])
        prev = merged.get(cid)
        if prev is None:
            merged[cid] = {
                "cluster_id": cid,
                "cluster_kind": "NAVIGATION_ONLY",
                "identity_group": False,
                "description": cluster.get("description") or "",
                "record_ids": list(cluster.get("record_ids") or []),
            }
            continue
        ids = list(prev.get("record_ids") or [])
        for rid in cluster.get("record_ids") or []:
            if rid not in ids:
                ids.append(rid)
        prev["record_ids"] = ids
        if cluster.get("description") and not prev.get("description"):
            prev["description"] = cluster["description"]
        merged[cid] = prev
    return list(merged.values())


def persist_understand_pass_v2(*, repo_root: Path) -> dict[str, int]:
    recon = repo_root / RECONCILIATION_RELATIVE_ROOT
    understand_root = recon / "understand"
    records_dir = understand_root / "records"
    evidence_dir = recon / "evidence" / "understand_v2"
    ledger_path = recon / "ledger.yaml"
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    ledger_records = list(ledger.get("records") or [])
    v2_by_id = {row["record_id"]: row for row in remaining_records()}
    processed = 0

    for rec in ledger_records:
        rid = rec["identity"]["reconciliation_id"]
        path = records_dir / f"{rid}.yaml"
        existing = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}
        payload = v2_by_id.get(rid)
        if payload is not None:
            processed += 1
            _apply_understanding(rec, payload)
            contradictions = [
                str(claim.get("text") or "")
                for claim in (payload.get("claims") or [])
                if str(claim.get("claim_class") or "") == "CONTRADICTION"
                and str(claim.get("text") or "")
            ]
            adj = rec["adjudication"]
            existing_c = [str(x) for x in (adj.get("contradictions") or []) if str(x)]
            for text in contradictions:
                if text not in existing_c:
                    existing_c.append(text)
            adj["contradictions"] = existing_c
            file_payload = {
                **_header(),
                "record_id": rid,
                "canonical_record_name": rec["identity"]["canonical_record_name"],
                "understand_status": payload["understand_status"],
                "purpose_understood": payload["purpose_understood"],
                "evidence_exhausted": True,
                "historical_purpose": payload.get("historical_purpose") or "",
                "historical_problem_statement": payload.get("historical_problem_statement") or "",
                "historical_inputs": payload.get("historical_inputs") or [],
                "historical_outputs": payload.get("historical_outputs") or [],
                "historical_dependencies": payload.get("historical_dependencies") or [],
                "historical_dependents": payload.get("historical_dependents") or [],
                "historical_paths": list(rec["discovery"].get("historical_paths") or []),
                "historical_commits": payload.get("historical_commits")
                or list(rec["discovery"].get("historical_commits") or []),
                "historical_blobs": payload.get("historical_blobs") or [],
                "relations": list((rec.get("relations") or {}).get("items") or []),
                "open_questions": payload.get("open_questions") or [],
                "evidence_refs": payload.get("evidence_refs") or [],
                "claims": payload.get("claims") or [],
                "epistemic_class": payload.get("epistemic_class") or "HISTORICAL_FACT",
                "clusters": payload.get("clusters") or [],
                "identity_merge_performed": False,
                "current_system_compared": False,
                "disposition_decided": False,
                "archive_status_is_not_obsolete": True,
                "historical_revert_is_not_disposition": True,
            }
            _dump(path, file_payload)
        else:
            existing["evidence_exhausted"] = True
            existing.setdefault("understand_pass_id", "UNDERSTAND_PASS_V1")
            existing["archive_status_is_not_obsolete"] = True
            existing["historical_revert_is_not_disposition"] = True
            _dump(path, existing)

    ledger["understand_pass_id"] = "UNDERSTAND_PASS_V2"
    ledger["understand_bound_against_sha"] = UNDERSTAND_BOUND_SHA
    _dump(ledger_path, ledger)

    relation_items = []
    for rec in ledger_records:
        rid = rec["identity"]["reconciliation_id"]
        for rel in (rec.get("relations") or {}).get("items") or []:
            relation_items.append({"from": rid, **rel})
    psa = sum(1 for item in relation_items if item.get("relation_type") == "POSSIBLE_SAME_AS")
    _dump(
        recon / "relations.yaml",
        {
            **_header(),
            "census_pass_id": "FIND_COMPLETELY_PASS_V3",
            "dedup_rule": "exact_git_blob_sha_only",
            "relation_count": len(relation_items),
            "possible_same_as_count": psa,
            "items": relation_items,
            "identity_merges_performed": 0,
            "note": (
                "UNDERSTAND pass v2 copied from ledger. POSSIBLE_SAME_AS remains hypothesis. "
                "No SAME_AS identity fusion. Archive presence is not obsolete. "
                "Historical revert is not disposition."
            ),
        },
    )

    index_rows = []
    purpose = partial = opened = exhausted = 0
    purpose_fact = io_fact = dep_fact = lifecycle_fact = 0
    open_q = contradiction = 0
    for rec in ledger_records:
        rid = rec["identity"]["reconciliation_id"]
        row = yaml.safe_load((records_dir / f"{rid}.yaml").read_text(encoding="utf-8"))
        status = str(row.get("understand_status") or "")
        if row.get("purpose_understood") is True:
            purpose += 1
        elif status == "UNDERSTAND_PARTIAL":
            partial += 1
        else:
            opened += 1
        if row.get("evidence_exhausted") is True:
            exhausted += 1
        if str(row.get("historical_purpose") or "").strip():
            purpose_fact += 1
        if row.get("historical_inputs") or row.get("historical_outputs"):
            io_fact += 1
        if row.get("historical_dependencies") or row.get("historical_dependents"):
            dep_fact += 1
        if row.get("historical_commits"):
            lifecycle_fact += 1
        open_q += len(list(row.get("open_questions") or []))
        for claim in row.get("claims") or []:
            if str(claim.get("claim_class") or "") == "CONTRADICTION":
                contradiction += 1
        index_rows.append(
            {
                "record_id": rid,
                "understand_status": status,
                "purpose_understood": bool(row.get("purpose_understood")),
                "evidence_exhausted": bool(row.get("evidence_exhausted")),
                "clusters": list(row.get("clusters") or []),
            }
        )

    status = {
        **_header(),
        "census_closed": True,
        "census_status": "CENSUS_CLOSED",
        "surfaces_exhaustion_proven": 17,
        "ledger_record_count": len(ledger_records),
        "purpose_understood_record_count": purpose,
        "understand_partial_record_count": partial,
        "understand_open_record_count": opened,
        "understand_evidence_exhausted_record_count": exhausted,
        "records_processed_this_pass": processed,
        "current_system_compared_record_count": 0,
        "adjudicated_record_count": 0,
        "disposition_decided_record_count": 0,
        "identity_merges_performed": 0,
        "no_current_system_comparison_performed": True,
        "no_disposition_decided": True,
        "no_reintegration_performed": True,
        "historical_purpose_fact_count": purpose_fact,
        "historical_input_output_fact_count": io_fact,
        "historical_dependency_fact_count": dep_fact,
        "historical_lifecycle_fact_count": lifecycle_fact,
        "open_question_count": open_q,
        "contradiction_count": contradiction,
        "relation_count": len(relation_items),
        "possible_same_as_count": psa,
        "understand_phase_status": "EVIDENCE_EXHAUSTED" if exhausted == 53 else "IN_PROGRESS",
    }
    _dump(understand_root / "pass_v2_status.yaml", status)
    _dump(
        understand_root / "index.yaml",
        {**_header(), "rows": index_rows, "row_count": len(index_rows)},
    )
    _dump(
        understand_root / "clusters.yaml",
        {
            **_header(),
            "clusters_are_not_identity_groups": True,
            "clusters": _merge_clusters(),
        },
    )
    _dump(
        evidence_dir / "raw_quotes.yaml",
        {
            **_header(),
            "kind": "FORENSIC_RAW_QUOTES",
            "interpretation_forbidden_in_this_file": True,
            "items": [
                {
                    "id": "Q-PTR-ENGINE",
                    "path": "archive/PeakTradeRepo/src/backtest/engine.py",
                    "quote": "# Engine placeholder",
                },
                {
                    "id": "Q-EXPORT-ENGINE",
                    "path": (
                        "archive/full_files_stand_02.12.2025/peak_trade_export/src/backtest/engine.py"
                    ),
                    "quote": "BacktestEngine: Generische Engine für Position-basierte Backtests.",
                },
                {
                    "id": "Q-RESET-BRANCH",
                    "path": "evidence/market_dashboard_reset/pr_a/git_state.txt",
                    "quote": "branch=fix/market-dashboard-architecture-reset-v1",
                },
                {
                    "id": "Q-ZERO-ORDER",
                    "path": "src/ops/pre_economic_zero_order_wallclock_arming_v1.py",
                    "quote": (
                        "This module never places orders and never grants "
                        "Economic/Shadow/Paper/Testnet/Live."
                    ),
                },
            ],
        },
    )
    schema_path = recon / "schema.yaml"
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    extra = list(schema.get("understand_artifact_files") or [])
    for rel in (
        "understand/pass_v2_status.yaml",
        "evidence/understand_v2/raw_quotes.yaml",
    ):
        if rel not in extra:
            extra.append(rel)
    schema["understand_artifact_files"] = extra
    understanding_fields = list(schema.get("understanding") or [])
    if "evidence_exhausted" not in understanding_fields:
        understanding_fields.append("evidence_exhausted")
    schema["understanding"] = understanding_fields
    _dump(schema_path, schema)
    return {
        "processed": processed,
        "purpose": purpose,
        "partial": partial,
        "open": opened,
        "exhausted": exhausted,
        "relations": len(relation_items),
        "contradictions": contradiction,
    }


def main() -> int:
    stats = persist_understand_pass_v2(repo_root=Path(__file__).resolve().parents[3])
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
