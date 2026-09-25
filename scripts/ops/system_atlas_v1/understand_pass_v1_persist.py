"""Persist UNDERSTAND pass v1 artifacts. Additive. No EVALUATE/disposition/fusion.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scripts.ops.system_atlas_v1.constants_v1 import (
    RECONCILIATION_RELATIVE_ROOT,
    RECONCILIATION_SCHEMA_VERSION,
)
from scripts.ops.system_atlas_v1.understand_pass_v1_records import (
    PARTIAL_OVERRIDES,
    UNDERSTAND_BOUND_SHA,
    clusters_payload,
    purpose_understood_records,
)

NEW_RELATION_TYPES = (
    "IMPORTED_BY",
    "CALLED_BY",
    "TESTED_BY",
    "CONFIGURES",
    "REGISTERED_AS",
    "MOVED_TO",
)


def _dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=120)
    path.write_text(
        "# ATLAS_AUTHORITY=NONE\n# RECONCILIATION_AUTHORITY=NONE\n" + text,
        encoding="utf-8",
    )


def _header() -> dict[str, Any]:
    return {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "bound_against_ref": "origin/main",
        "bound_against_sha": UNDERSTAND_BOUND_SHA,
        "atlas_authority": "NONE",
        "reconciliation_authority": "NONE",
        "understand_pass_id": "UNDERSTAND_PASS_V1",
        "identity_fusion_forbidden": True,
        "disposition_performed": False,
        "current_system_compared": False,
        "evaluate_performed": False,
    }


def _apply_understanding(record: dict[str, Any], payload: dict[str, Any]) -> None:
    understanding = record["understanding"]
    understanding["purpose_understood"] = bool(payload["purpose_understood"])
    understanding["purpose_statement"] = str(payload.get("historical_purpose") or "")
    understanding["historical_problem_statement"] = str(
        payload.get("historical_problem_statement") or ""
    )
    understanding["inputs"] = list(payload.get("historical_inputs") or [])
    understanding["outputs"] = list(payload.get("historical_outputs") or [])
    understanding["dependencies"] = list(payload.get("historical_dependencies") or [])
    understanding["consumers"] = list(payload.get("historical_dependents") or [])
    understanding["authority_role"] = str(payload.get("authority_role") or "")
    understanding["safety_role"] = str(payload.get("safety_role") or "")
    understanding["runtime_role"] = str(payload.get("runtime_role") or "")
    understanding["invariants"] = list(payload.get("invariants") or [])
    understanding["claims"] = list(payload.get("claims") or [])
    adj = record["adjudication"]
    existing_q = [str(x) for x in (adj.get("unresolved_questions") or []) if str(x)]
    merged_q = list(existing_q)
    for q in payload.get("open_questions") or []:
        if q not in merged_q:
            merged_q.append(q)
    adj["unresolved_questions"] = merged_q
    if payload["purpose_understood"] is True:
        adj["lifecycle_state"] = "PURPOSE_UNDERSTOOD"
    else:
        if adj.get("lifecycle_state") not in {"DISCOVERED", "EVIDENCE_BOUND"}:
            adj["lifecycle_state"] = "EVIDENCE_BOUND"
    rel_items = list((record.get("relations") or {}).get("items") or [])
    existing_keys = {
        (str(item.get("relation_type") or ""), str(item.get("target_id") or ""))
        for item in rel_items
    }
    for rel in payload.get("extra_relations") or []:
        key = (str(rel.get("relation_type") or ""), str(rel.get("target_id") or ""))
        if key not in existing_keys:
            rel_items.append(rel)
            existing_keys.add(key)
    record["relations"] = {"items": rel_items}


def persist_understand_pass_v1(*, repo_root: Path) -> dict[str, int]:
    recon = repo_root / RECONCILIATION_RELATIVE_ROOT
    understand_root = recon / "understand"
    records_dir = understand_root / "records"
    evidence_dir = recon / "evidence" / "understand_v1"
    ledger_path = recon / "ledger.yaml"
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    ledger_records = list(ledger.get("records") or [])

    understood = purpose_understood_records()
    by_payload = {row["record_id"]: row for row in understood}
    for rid, override in PARTIAL_OVERRIDES.items():
        if rid in by_payload:
            by_payload[rid].update(override)

    index_rows: list[dict[str, Any]] = []
    purpose_count = 0
    partial_count = 0
    open_count = 0
    open_question_count = 0
    contradiction_count = 0
    purpose_fact_count = 0
    io_fact_count = 0
    dep_fact_count = 0

    for rec in ledger_records:
        rid = rec["identity"]["reconciliation_id"]
        payload = by_payload.get(rid)
        if payload is None:
            payload = {
                "record_id": rid,
                "understand_status": "UNDERSTAND_OPEN",
                "purpose_understood": False,
                "historical_purpose": "",
                "historical_problem_statement": "",
                "historical_inputs": [],
                "historical_outputs": [],
                "historical_dependencies": [],
                "historical_dependents": [],
                "authority_role": "",
                "safety_role": "",
                "runtime_role": "",
                "invariants": [],
                "open_questions": list(rec["adjudication"].get("unresolved_questions") or []),
                "evidence_refs": list(rec["discovery"].get("discovery_evidence") or []),
                "historical_blobs": [],
                "historical_commits": list(rec["discovery"].get("historical_commits") or []),
                "clusters": [],
                "epistemic_class": "OPEN_QUESTION",
                "claims": [
                    {
                        "claim_class": "OPEN_QUESTION",
                        "text": "Purpose not evidence-bound in UNDERSTAND pass v1.",
                        "evidence": list(rec["discovery"].get("discovery_evidence") or []),
                        "used_as_fact": False,
                    }
                ],
                "extra_relations": [],
                "identity_merge_performed": False,
                "current_system_compared": False,
                "disposition_decided": False,
            }
            open_count += 1
        else:
            status = str(payload.get("understand_status") or "")
            if payload.get("purpose_understood") is True:
                purpose_count += 1
                _apply_understanding(rec, payload)
            elif status == "UNDERSTAND_PARTIAL":
                partial_count += 1
                _apply_understanding(rec, payload)
            else:
                open_count += 1
                _apply_understanding(rec, payload)
            if payload.get("historical_purpose"):
                purpose_fact_count += 1
            if payload.get("historical_inputs") or payload.get("historical_outputs"):
                io_fact_count += 1
            if payload.get("historical_dependencies") or payload.get("historical_dependents"):
                dep_fact_count += 1

        open_question_count += len(list(payload.get("open_questions") or []))
        for claim in payload.get("claims") or []:
            if str(claim.get("claim_class") or "") == "CONTRADICTION":
                contradiction_count += 1

        file_payload = {
            **_header(),
            "record_id": rid,
            "canonical_record_name": rec["identity"]["canonical_record_name"],
            "understand_status": payload["understand_status"],
            "purpose_understood": payload["purpose_understood"],
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
            "epistemic_class": payload.get("epistemic_class") or "OPEN_QUESTION",
            "clusters": payload.get("clusters") or [],
            "identity_merge_performed": False,
            "current_system_compared": False,
            "disposition_decided": False,
        }
        _dump(records_dir / f"{rid}.yaml", file_payload)
        index_rows.append(
            {
                "record_id": rid,
                "understand_status": payload["understand_status"],
                "purpose_understood": payload["purpose_understood"],
                "clusters": payload.get("clusters") or [],
            }
        )

    ledger["understand_pass_id"] = "UNDERSTAND_PASS_V1"
    ledger["understand_bound_against_sha"] = UNDERSTAND_BOUND_SHA
    _dump(ledger_path, ledger)

    relation_items = []
    for rec in ledger_records:
        rid = rec["identity"]["reconciliation_id"]
        for rel in (rec.get("relations") or {}).get("items") or []:
            relation_items.append({"from": rid, **rel})
    psa_count = sum(1 for item in relation_items if item.get("relation_type") == "POSSIBLE_SAME_AS")
    relations_doc = {
        **_header(),
        "census_pass_id": "FIND_COMPLETELY_PASS_V3",
        "dedup_rule": "exact_git_blob_sha_only",
        "relation_count": len(relation_items),
        "possible_same_as_count": psa_count,
        "items": relation_items,
        "identity_merges_performed": 0,
        "note": (
            "UNDERSTAND pass v1 copied from ledger. POSSIBLE_SAME_AS remains hypothesis. "
            "No SAME_AS / MERGED_INTO / RENAMED_TO identity fusion."
        ),
    }
    _dump(recon / "relations.yaml", relations_doc)

    status = {
        **_header(),
        "census_closed": True,
        "census_status": "CENSUS_CLOSED",
        "surfaces_exhaustion_proven": 17,
        "ledger_record_count": len(ledger_records),
        "purpose_understood_record_count": purpose_count,
        "understand_partial_record_count": partial_count,
        "understand_open_record_count": open_count,
        "current_system_compared_record_count": 0,
        "adjudicated_record_count": 0,
        "disposition_decided_record_count": 0,
        "identity_merges_performed": 0,
        "no_current_system_comparison_performed": True,
        "no_disposition_decided": True,
        "no_reintegration_performed": True,
        "historical_purpose_fact_count": purpose_fact_count,
        "historical_input_output_fact_count": io_fact_count,
        "historical_dependency_fact_count": dep_fact_count,
        "open_question_count": open_question_count,
        "contradiction_count": contradiction_count,
        "relation_count": len(relation_items),
        "possible_same_as_count": psa_count,
    }
    _dump(understand_root / "pass_v1_status.yaml", status)
    _dump(
        understand_root / "index.yaml",
        {**_header(), "rows": index_rows, "row_count": len(index_rows)},
    )
    _dump(
        understand_root / "clusters.yaml",
        {
            **_header(),
            "clusters_are_not_identity_groups": True,
            "clusters": clusters_payload(),
        },
    )
    quotes = {
        **_header(),
        "kind": "FORENSIC_RAW_QUOTES",
        "interpretation_forbidden_in_this_file": True,
        "items": [
            {
                "id": "Q-LSC-INIT",
                "path": "src/webui/market_dashboard_landscape_v2/__init__.py",
                "quote": (
                    "Market Dashboard Landscape V2 — read-only projection contracts + page shell. "
                    "No runtime activation, orders, or domain recomputation."
                ),
            },
            {
                "id": "Q-LSC-RB",
                "path": (
                    "docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md"
                ),
                "quote": "Ziel: Neuer Market-Workspace als strikt read-only Consumer des Peak_Trade-Systems",
            },
            {
                "id": "Q-DEL",
                "path": "git:b5b8172806eae55d8639f964fcb2ad036337a0f3",
                "quote": "delete(webui): remove market dashboard product stack",
            },
        ],
    }
    _dump(evidence_dir / "raw_quotes.yaml", quotes)

    schema_path = recon / "schema.yaml"
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    allowed = list(schema.get("allowed_relation_types") or [])
    for rel_type in NEW_RELATION_TYPES:
        if rel_type not in allowed:
            allowed.append(rel_type)
    schema["allowed_relation_types"] = allowed
    extra_files = list(schema.get("understand_artifact_files") or [])
    for rel in (
        "understand/pass_v1_status.yaml",
        "understand/index.yaml",
        "understand/clusters.yaml",
        "evidence/understand_v1/raw_quotes.yaml",
    ):
        if rel not in extra_files:
            extra_files.append(rel)
    schema["understand_artifact_files"] = extra_files
    _dump(schema_path, schema)

    return {
        "purpose_understood": purpose_count,
        "partial": partial_count,
        "open": open_count,
        "relations": len(relation_items),
        "ledger": len(ledger_records),
    }


def main() -> int:
    stats = persist_understand_pass_v1(repo_root=Path(__file__).resolve().parents[3])
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
