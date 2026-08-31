"""Persist INTEGRATE_OR_DISPOSITION pass v1. Adjudication only.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Does not reintegrate, fuse identities, or mutate runtime.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scripts.ops.system_atlas_v1.adjudicate_pass_v1_records import (
    ADJUDICATE_BOUND_REF,
    ADJUDICATE_BOUND_SHA,
    INSUFFICIENT,
    RETAIN,
    adjudicate_records,
)
from scripts.ops.system_atlas_v1.constants_v1 import (
    RECONCILIATION_RELATIVE_ROOT,
    RECONCILIATION_SCHEMA_VERSION,
)
from scripts.ops.system_atlas_v1.understand_pass_v1_persist import _dump

ADJUDICATE_PASS_ID = "INTEGRATE_OR_DISPOSITION_PASS_V1"
FUSION = frozenset({"MERGED_INTO", "RENAMED_TO", "SPLIT_INTO", "SAME_AS"})


def _header() -> dict[str, Any]:
    return {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "bound_against_ref": ADJUDICATE_BOUND_REF,
        "bound_against_sha": ADJUDICATE_BOUND_SHA,
        "atlas_authority": "NONE",
        "reconciliation_authority": "NONE",
        "adjudicate_pass_id": ADJUDICATE_PASS_ID,
        "identity_fusion_forbidden": True,
        "disposition_performed": True,
        "current_system_compared": True,
        "evaluate_performed": True,
        "adjudication_attempted": True,
        "reintegration_performed": False,
        "runtime_mutation_performed": False,
    }


def persist_adjudicate_pass_v1(*, repo_root: Path) -> dict[str, int]:
    recon = repo_root / RECONCILIATION_RELATIVE_ROOT
    adjudicate_root = recon / "adjudicate"
    records_dir = adjudicate_root / "records"
    evidence_dir = recon / "evidence" / "adjudicate_v1"
    ledger_path = recon / "ledger.yaml"
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    ledger_records = list(ledger.get("records") or [])
    by_id = {row["record_id"]: row for row in adjudicate_records()}
    if len(by_id) != 53:
        raise ValueError(f"adjudicate_record_count_mismatch:{len(by_id)}")
    if len(ledger_records) != 53:
        raise ValueError(f"ledger_record_count_mismatch:{len(ledger_records)}")

    disposition_counts: dict[str, int] = {}
    attempted = 0
    decided = 0
    open_insufficient = 0
    for rec in ledger_records:
        rid = rec["identity"]["reconciliation_id"]
        payload = by_id[rid]
        for rel in (rec.get("relations") or {}).get("items") or []:
            if str(rel.get("relation_type") or "") in FUSION:
                raise ValueError(f"identity_fusion_present:{rid}")
        presence = rec["discovery"].get("current_presence") or ""
        if rid == "RCN-000052" and presence != "CURRENTLY_ABSENT":
            raise ValueError("census_presence_rewrite_forbidden:RCN-000052")
        adj = rec["adjudication"]
        adj["lifecycle_state"] = payload["lifecycle_state"]
        adj["disposition"] = payload["disposition"]
        adj["positive_reason"] = payload["positive_reason"]
        adj["evidence_refs"] = list(payload["evidence_refs"])
        adj["identity_status"] = payload["identity_status"]
        adj["alternatives_rejected"] = list(payload["alternatives_rejected"])
        adj["further_evidence_required"] = payload["further_evidence_required"]
        adj["reintegration_candidate"] = payload["reintegration_candidate"]
        adj["adjudication_attempted"] = True
        adj["claims"] = list(payload["claims"])
        existing_q = [str(x) for x in (adj.get("unresolved_questions") or []) if str(x)]
        for q in payload.get("unresolved_questions") or []:
            if q not in existing_q:
                existing_q.append(q)
        adj["unresolved_questions"] = existing_q
        existing_c = [str(x) for x in (adj.get("contradictions") or []) if str(x)]
        for text in payload.get("contradictions") or []:
            if text and text not in existing_c:
                existing_c.append(text)
        for claim in payload.get("claims") or []:
            if str(claim.get("claim_class") or "") == "CONTRADICTION":
                text = str(claim.get("text") or "")
                if text and text not in existing_c:
                    existing_c.append(text)
        adj["contradictions"] = existing_c
        integration = rec["integration"]
        if integration.get("reintegration_required") is True:
            raise ValueError(f"reintegration_flag_set:{rid}")
        integration["reintegration_required"] = False
        integration["adaptation_required"] = False
        audit = rec["audit"]
        audit["last_adjudicated_against_sha"] = ADJUDICATE_BOUND_SHA
        note = str(audit.get("notes") or "")
        marker = f"INTEGRATE_OR_DISPOSITION_PASS_V1 adjudicated against {ADJUDICATE_BOUND_SHA}."
        if marker not in note:
            audit["notes"] = (note + " " + marker).strip()
        file_payload = {
            **_header(),
            "record_id": rid,
            "canonical_record_name": rec["identity"]["canonical_record_name"],
            "census_current_presence": presence,
            "evaluate_capability_overlap": rec["current_comparison"].get("capability_overlap")
            or "",
            **{
                key: payload[key]
                for key in (
                    "adjudication_attempted",
                    "disposition",
                    "lifecycle_state",
                    "identity_status",
                    "positive_reason",
                    "alternatives_rejected",
                    "further_evidence_required",
                    "reintegration_candidate",
                    "reintegration_performed",
                    "identity_fusion_forbidden",
                    "claims",
                    "evidence_refs",
                    "contradictions",
                    "unresolved_questions",
                    "bound_against_ref",
                    "bound_against_sha",
                    "evaluate_compared_sha",
                )
            },
        }
        _dump(records_dir / f"{rid}.yaml", file_payload)
        attempted += 1
        disposition = str(payload["disposition"])
        disposition_counts[disposition] = disposition_counts.get(disposition, 0) + 1
        if payload["lifecycle_state"] == "DISPOSITION_DECIDED":
            decided += 1
        if disposition == INSUFFICIENT:
            open_insufficient += 1

    ledger["adjudicate_pass_id"] = ADJUDICATE_PASS_ID
    ledger["adjudicate_bound_against_sha"] = ADJUDICATE_BOUND_SHA
    _dump(ledger_path, ledger)

    index_rows = []
    for rec in ledger_records:
        rid = rec["identity"]["reconciliation_id"]
        payload = by_id[rid]
        index_rows.append(
            {
                "record_id": rid,
                "disposition": payload["disposition"],
                "lifecycle_state": payload["lifecycle_state"],
                "identity_status": payload["identity_status"],
                "census_current_presence": rec["discovery"].get("current_presence") or "",
                "evaluate_capability_overlap": rec["current_comparison"].get("capability_overlap")
                or "",
                "reintegration_candidate": payload["reintegration_candidate"],
                "reintegration_performed": False,
            }
        )

    status = {
        **_header(),
        "census_closed": True,
        "census_status": "CENSUS_CLOSED",
        "surfaces_exhaustion_proven": 17,
        "ledger_record_count": len(ledger_records),
        "current_system_compared_record_count": 53,
        "adjudication_attempted_record_count": attempted,
        "adjudicated_record_count": attempted,
        "disposition_decided_record_count": decided,
        "open_insufficient_evidence_count": open_insufficient,
        "retain_as_is_count": disposition_counts.get(RETAIN, 0),
        "adapt_and_reintegrate_count": disposition_counts.get("ADAPT_AND_REINTEGRATE", 0),
        "capability_already_covered_count": disposition_counts.get("CAPABILITY_ALREADY_COVERED", 0),
        "historically_valid_but_incompatible_count": disposition_counts.get(
            "HISTORICALLY_VALID_BUT_INCOMPATIBLE", 0
        ),
        "reject_for_current_system_count": disposition_counts.get("REJECT_FOR_CURRENT_SYSTEM", 0),
        "insufficient_evidence_count": disposition_counts.get(INSUFFICIENT, 0),
        "identity_merges_performed": 0,
        "no_reintegration_performed": True,
        "no_identity_fusion_performed": True,
        "no_runtime_mutation_performed": True,
        "disposition_counts": disposition_counts,
        "adjudicate_phase_status": "ADJUDICATION_ATTEMPTED",
    }
    _dump(adjudicate_root / "pass_v1_status.yaml", status)
    _dump(
        adjudicate_root / "index.yaml",
        {**_header(), "rows": index_rows, "row_count": len(index_rows)},
    )
    _dump(
        evidence_dir / "raw_quotes.yaml",
        {
            **_header(),
            "kind": "FORENSIC_RAW_QUOTES",
            "interpretation_forbidden_in_this_file": True,
            "items": [
                {
                    "record_id": "RCN-000001",
                    "source": "src/webui/market_dashboard_landscape_v2/owner_registry.py",
                    "quote": (
                        "This package is a consumer boundary only — it does not own trading truth."
                    ),
                },
                {
                    "record_id": "RCN-000015",
                    "source": "src/ops/single_selected_future_policy_v1/policy_v1.py",
                    "quote": '"single_selected_future": SINGLE_SELECTED_FUTURE,',
                },
                {
                    "record_id": "RCN-000019",
                    "source": "src/risk_layer/kill_switch/__init__.py",
                    "quote": "from src.risk_layer.kill_switch import KillSwitch",
                },
                {
                    "record_id": "RCN-000052",
                    "source": "docs/webui/observability/OBSERVABILITY_HUB_V0.md",
                    "quote": "read-only / display-only",
                },
            ],
        },
    )

    schema_path = recon / "schema.yaml"
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    extra = list(schema.get("adjudicate_artifact_files") or [])
    for rel in (
        "adjudicate/pass_v1_status.yaml",
        "adjudicate/index.yaml",
        "evidence/adjudicate_v1/raw_quotes.yaml",
    ):
        if rel not in extra:
            extra.append(rel)
    schema["adjudicate_artifact_files"] = extra
    adj_fields = list(schema.get("adjudication") or [])
    for field in (
        "identity_status",
        "alternatives_rejected",
        "further_evidence_required",
        "reintegration_candidate",
        "adjudication_attempted",
        "claims",
    ):
        if field not in adj_fields:
            adj_fields.append(field)
    schema["adjudication"] = adj_fields
    _dump(schema_path, schema)
    return {
        "attempted": attempted,
        "decided": decided,
        "open_insufficient": open_insufficient,
        "ledger": len(ledger_records),
        "disposition_classes": len(disposition_counts),
    }


def main() -> int:
    stats = persist_adjudicate_pass_v1(repo_root=Path(__file__).resolve().parents[3])
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
