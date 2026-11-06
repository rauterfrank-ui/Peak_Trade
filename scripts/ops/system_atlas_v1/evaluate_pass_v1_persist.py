"""Persist EVALUATE_INDIVIDUALLY pass v1. Current-system comparison only.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Does not decide disposition, reintegration, or identity fusion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scripts.ops.system_atlas_v1.constants_v1 import (
    RECONCILIATION_RELATIVE_ROOT,
    RECONCILIATION_SCHEMA_VERSION,
)
from scripts.ops.system_atlas_v1.evaluate_pass_v1_records import (
    EVALUATE_BOUND_REF,
    EVALUATE_BOUND_SHA,
    evaluate_records,
)
from scripts.ops.system_atlas_v1.understand_pass_v1_persist import _dump

EVALUATE_PASS_ID = "EVALUATE_INDIVIDUALLY_PASS_V1"


def _header() -> dict[str, Any]:
    return {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "bound_against_ref": EVALUATE_BOUND_REF,
        "bound_against_sha": EVALUATE_BOUND_SHA,
        "atlas_authority": "NONE",
        "reconciliation_authority": "NONE",
        "evaluate_pass_id": EVALUATE_PASS_ID,
        "identity_fusion_forbidden": True,
        "disposition_performed": False,
        "current_system_compared": True,
        "evaluate_performed": True,
        "reintegration_performed": False,
    }


def persist_evaluate_pass_v1(*, repo_root: Path) -> dict[str, int]:
    recon = repo_root / RECONCILIATION_RELATIVE_ROOT
    evaluate_root = recon / "evaluate"
    records_dir = evaluate_root / "records"
    evidence_dir = recon / "evidence" / "evaluate_v1"
    ledger_path = recon / "ledger.yaml"
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    ledger_records = list(ledger.get("records") or [])
    by_id = {row["record_id"]: row for row in evaluate_records()}
    if len(by_id) != 53:
        raise ValueError(f"evaluate_record_count_mismatch:{len(by_id)}")

    overlap_counts: dict[str, int] = {}
    compared = 0
    for rec in ledger_records:
        rid = rec["identity"]["reconciliation_id"]
        payload = by_id[rid]
        comparison = rec["current_comparison"]
        comparison["current_equivalent"] = payload["current_equivalent"]
        comparison["current_paths"] = list(payload["current_paths"])
        comparison["capability_overlap"] = payload["capability_overlap"]
        comparison["semantic_compatibility"] = payload["semantic_compatibility"]
        comparison["authority_compatibility"] = payload["authority_compatibility"]
        comparison["safety_compatibility"] = payload["safety_compatibility"]
        comparison["runtime_compatibility"] = payload["runtime_compatibility"]
        comparison["conflicts"] = list(payload["conflicts"])
        comparison["gaps"] = list(payload["gaps"])
        comparison["compared_against_ref"] = EVALUATE_BOUND_REF
        comparison["compared_against_sha"] = EVALUATE_BOUND_SHA
        comparison["comparison_status"] = "CURRENT_SYSTEM_COMPARED"
        comparison["claims"] = list(payload["claims"])
        adj = rec["adjudication"]
        if str(adj.get("disposition") or "").strip():
            raise ValueError(f"disposition_already_set:{rid}")
        adj["lifecycle_state"] = "CURRENT_SYSTEM_COMPARED"
        existing_q = [str(x) for x in (adj.get("unresolved_questions") or []) if str(x)]
        for q in payload.get("open_questions") or []:
            if q not in existing_q:
                existing_q.append(q)
        adj["unresolved_questions"] = existing_q
        existing_c = [str(x) for x in (adj.get("contradictions") or []) if str(x)]
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
        note = str(audit.get("notes") or "")
        marker = f"EVALUATE_PASS_V1 compared against {EVALUATE_BOUND_SHA}."
        if marker not in note:
            audit["notes"] = (note + " " + marker).strip()
        file_payload = {
            **_header(),
            "record_id": rid,
            "canonical_record_name": rec["identity"]["canonical_record_name"],
            "census_current_presence": rec["discovery"].get("current_presence") or "",
            **{
                key: payload[key]
                for key in (
                    "comparison_status",
                    "compared_against_ref",
                    "compared_against_sha",
                    "current_equivalent",
                    "current_paths",
                    "capability_overlap",
                    "semantic_compatibility",
                    "authority_compatibility",
                    "safety_compatibility",
                    "runtime_compatibility",
                    "conflicts",
                    "gaps",
                    "claims",
                    "open_questions",
                    "disposition_performed",
                    "identity_fusion_forbidden",
                    "reintegration_performed",
                )
            },
        }
        _dump(records_dir / f"{rid}.yaml", file_payload)
        compared += 1
        overlap = str(payload["capability_overlap"])
        overlap_counts[overlap] = overlap_counts.get(overlap, 0) + 1

    ledger["evaluate_pass_id"] = EVALUATE_PASS_ID
    ledger["evaluate_bound_against_sha"] = EVALUATE_BOUND_SHA
    _dump(ledger_path, ledger)

    index_rows = []
    for rec in ledger_records:
        rid = rec["identity"]["reconciliation_id"]
        payload = by_id[rid]
        index_rows.append(
            {
                "record_id": rid,
                "comparison_status": "CURRENT_SYSTEM_COMPARED",
                "capability_overlap": payload["capability_overlap"],
                "census_current_presence": rec["discovery"].get("current_presence") or "",
                "disposition_performed": False,
            }
        )

    status = {
        **_header(),
        "census_closed": True,
        "census_status": "CENSUS_CLOSED",
        "surfaces_exhaustion_proven": 17,
        "ledger_record_count": len(ledger_records),
        "current_system_compared_record_count": compared,
        "adjudicated_record_count": 0,
        "disposition_decided_record_count": 0,
        "identity_merges_performed": 0,
        "no_disposition_decided": True,
        "no_reintegration_performed": True,
        "no_identity_fusion_performed": True,
        "overlap_counts": overlap_counts,
        "evaluate_phase_status": "CURRENT_SYSTEM_COMPARED",
    }
    _dump(evaluate_root / "pass_v1_status.yaml", status)
    _dump(
        evaluate_root / "index.yaml",
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
    extra = list(schema.get("evaluate_artifact_files") or [])
    for rel in (
        "evaluate/pass_v1_status.yaml",
        "evaluate/index.yaml",
        "evidence/evaluate_v1/raw_quotes.yaml",
    ):
        if rel not in extra:
            extra.append(rel)
    schema["evaluate_artifact_files"] = extra
    comparison_fields = list(schema.get("current_comparison") or [])
    for field in (
        "compared_against_ref",
        "compared_against_sha",
        "comparison_status",
        "claims",
    ):
        if field not in comparison_fields:
            comparison_fields.append(field)
    schema["current_comparison"] = comparison_fields
    _dump(schema_path, schema)
    return {
        "compared": compared,
        "overlap_counts_len": len(overlap_counts),
        "ledger": len(ledger_records),
    }


def main() -> int:
    stats = persist_evaluate_pass_v1(repo_root=Path(__file__).resolve().parents[3])
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
