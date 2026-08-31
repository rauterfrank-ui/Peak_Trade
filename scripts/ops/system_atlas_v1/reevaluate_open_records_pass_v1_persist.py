"""Persist REEVALUATE_OPEN_RECORDS_PASS_V1. Re-evaluate/adjudicate OPEN records only.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Does not reintegrate, fuse identities, or mutate runtime.
UNDERSTAND / EVALUATE / INTEGRATE_OR_DISPOSITION / OPEN_EVIDENCE_RESOLUTION
snapshots remain frozen.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scripts.ops.system_atlas_v1.constants_v1 import (
    RECONCILIATION_RELATIVE_ROOT,
    RECONCILIATION_SCHEMA_VERSION,
)
from scripts.ops.system_atlas_v1.evidence_resolution_pass_v1_records import (
    ADJUDICATE_FROZEN_SHA,
    EVIDENCE_RESOLUTION_PASS_ID,
    LANDSCAPE_V1_IDS,
    OPEN_IDS,
)
from scripts.ops.system_atlas_v1.reevaluate_open_records_pass_v1_records import (
    INSUFFICIENT,
    INPUT_PASS_ID,
    REEVALUATE_BOUND_REF,
    REEVALUATE_BOUND_SHA,
    REEVALUATE_PASS_ID,
    reevaluate_open_records,
)
from scripts.ops.system_atlas_v1.understand_pass_v1_persist import _dump

FROZEN_SNAPSHOT_DIRS = ("understand", "evaluate", "adjudicate", "evidence_resolution")
PREVIOUS_ADJUDICATE_PASS_ID = "INTEGRATE_OR_DISPOSITION_PASS_V1"


def _header() -> dict[str, Any]:
    return {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "bound_against_ref": REEVALUATE_BOUND_REF,
        "bound_against_sha": REEVALUATE_BOUND_SHA,
        "atlas_authority": "NONE",
        "reconciliation_authority": "NONE",
        "reevaluate_pass_id": REEVALUATE_PASS_ID,
        "input_pass_id": INPUT_PASS_ID,
        "identity_fusion_forbidden": True,
        "reintegration_performed": False,
        "runtime_mutation_performed": False,
        "identity_merges_performed": 0,
        "understand_snapshot_frozen": True,
        "evaluate_snapshot_frozen": True,
        "adjudication_snapshot_frozen": True,
        "evidence_resolution_snapshot_frozen": True,
    }


def persist_reevaluate_open_records_pass_v1(*, repo_root: Path) -> dict[str, int]:
    recon = repo_root / RECONCILIATION_RELATIVE_ROOT
    for frozen in FROZEN_SNAPSHOT_DIRS:
        if not (recon / frozen / "records").is_dir():
            raise ValueError(f"frozen_snapshot_missing:{frozen}")

    er_status_path = recon / "evidence_resolution" / "pass_v1_status.yaml"
    er_status = yaml.safe_load(er_status_path.read_text(encoding="utf-8"))
    if er_status.get("evidence_resolution_pass_id") != EVIDENCE_RESOLUTION_PASS_ID:
        raise ValueError("input_pass_id_mismatch")
    if int(er_status["input_open_record_count"]) != 35:
        raise ValueError("input_open_record_count_mismatch")
    if int(er_status["evidence_resolution_attempted_count"]) != 35:
        raise ValueError("evidence_resolution_attempted_count_mismatch")
    if int(er_status["final_disposition_changes_performed"]) != 0:
        raise ValueError("input_pass_changed_disposition")
    if int(er_status["evidence_gap_resolved_count"]) != 0:
        raise ValueError("input_pass_resolved_count_mismatch")
    if int(er_status["evidence_gap_partially_resolved_count"]) != 34:
        raise ValueError("input_pass_partial_count_mismatch")
    if int(er_status["evidence_gap_unresolved_count"]) != 0:
        raise ValueError("input_pass_unresolved_count_mismatch")
    if int(er_status["contradiction_discovered_count"]) != 1:
        raise ValueError("input_pass_contradiction_count_mismatch")

    pass_root = recon / "reevaluate"
    records_dir = pass_root / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    ledger_path = recon / "ledger.yaml"
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    ledger_records = list(ledger.get("records") or [])
    generated = {row["record_id"]: row for row in reevaluate_open_records()}
    if len(generated) != 35:
        raise ValueError(f"reevaluate_record_count_mismatch:{len(generated)}")
    if tuple(generated[rid]["record_id"] for rid in OPEN_IDS) != OPEN_IDS:
        raise ValueError("reevaluate_id_order_mismatch")

    attempted = 0
    remaining_open = 0
    new_final = 0
    index_rows: list[dict[str, Any]] = []
    marker = (
        f"{REEVALUATE_PASS_ID} bound against {REEVALUATE_BOUND_SHA}. "
        "Disposition unchanged; INSUFFICIENT_EVIDENCE remains OPEN."
    )

    for rec in ledger_records:
        rid = rec["identity"]["reconciliation_id"]
        adj = rec["adjudication"]
        presence = rec["discovery"].get("current_presence") or ""
        if rid == "RCN-000052" and presence != "CURRENTLY_ABSENT":
            raise ValueError("census_presence_rewrite_forbidden:RCN-000052")
        if rid not in generated:
            if rec.get("reevaluate") is not None:
                raise ValueError(f"reevaluate_on_non_open_record:{rid}")
            continue
        if str(adj.get("disposition") or "") != INSUFFICIENT:
            raise ValueError(f"open_record_disposition_drift:{rid}:{adj.get('disposition')}")
        if str(adj.get("lifecycle_state") or "") != "OPEN":
            raise ValueError(f"open_record_lifecycle_drift:{rid}:{adj.get('lifecycle_state')}")
        payload = generated[rid]
        if payload["disposition_burden_met"] is True:
            raise ValueError(f"unexpected_burden_met:{rid}")
        if payload["disposition"] != INSUFFICIENT:
            raise ValueError(f"unexpected_non_open_disposition:{rid}")
        if payload["final_disposition_change_performed"] is True:
            raise ValueError(f"unexpected_final_disposition_change:{rid}")
        rec["reevaluate"] = {
            "pass_id": REEVALUATE_PASS_ID,
            "input_pass_id": INPUT_PASS_ID,
            "disposition_burden_met": False,
            "disposition_candidate": INSUFFICIENT,
            "disposition": INSUFFICIENT,
            "lifecycle_state": "OPEN",
            "final_disposition_change_performed": False,
            "identity_merge_performed": False,
            "reintegration_performed": False,
            "reintegration_candidate": False,
            "runtime_mutation_performed": False,
            "further_evidence_required": True,
            "current_evidence_set": list(payload["current_evidence_set"]),
            "historical_function": payload["historical_function"],
            "historical_relations": payload["historical_relations"],
            "current_system_analogues": payload["current_system_analogues"],
            "identity_status": payload["identity_status"],
            "successor_status": payload["successor_status"],
            "replacement_status": payload["replacement_status"],
            "current_value_status": payload["current_value_status"],
            "current_compatibility_status": payload["current_compatibility_status"],
            "contradictions": list(payload["contradictions"]),
            "unresolved_gaps": list(payload["unresolved_gaps"]),
            "evaluation_result": payload["evaluation_result"],
            "alternatives_rejected": list(payload["alternatives_rejected"]),
            "claims": list(payload["claims"]),
            "evidence_refs": list(payload["evidence_refs"]),
            "previous_adjudication": {
                "pass_id": PREVIOUS_ADJUDICATE_PASS_ID,
                "bound_sha": ADJUDICATE_FROZEN_SHA,
                "disposition": INSUFFICIENT,
                "lifecycle_state": "OPEN",
            },
            "bound_against_sha": REEVALUATE_BOUND_SHA,
        }
        audit = rec["audit"]
        note = str(audit.get("notes") or "")
        if marker not in note:
            audit["notes"] = (note + " " + marker).strip()
        file_payload = {**_header(), **payload}
        _dump(records_dir / f"{rid}.yaml", file_payload)
        attempted += 1
        remaining_open += 1
        index_rows.append(
            {
                "record_id": rid,
                "census_current_presence": presence,
                "disposition_burden_met": False,
                "disposition_candidate": INSUFFICIENT,
                "disposition": INSUFFICIENT,
                "lifecycle_state": "OPEN",
                "final_disposition_change_performed": False,
                "identity_merge_performed": False,
                "reintegration_performed": False,
            }
        )

    if attempted != 35:
        raise ValueError(f"attempted_count_mismatch:{attempted}")
    if remaining_open + new_final != 35:
        raise ValueError("count_invariant_mismatch")
    if len(ledger_records) != 53:
        raise ValueError(f"ledger_record_count_mismatch:{len(ledger_records)}")

    ledger["reevaluate_pass_id"] = REEVALUATE_PASS_ID
    ledger["reevaluate_bound_against_sha"] = REEVALUATE_BOUND_SHA
    ledger["reevaluate_input_pass_id"] = INPUT_PASS_ID
    _dump(ledger_path, ledger)

    status = {
        **_header(),
        "census_closed": True,
        "census_status": "CENSUS_CLOSED",
        "adjudicate_pass_id_frozen": PREVIOUS_ADJUDICATE_PASS_ID,
        "adjudicate_bound_against_sha_frozen": ADJUDICATE_FROZEN_SHA,
        "input_pass_id": INPUT_PASS_ID,
        "ledger_record_count": len(ledger_records),
        "input_record_count": 35,
        "reevaluation_attempted_record_count": attempted,
        "new_retain_as_is_count": 0,
        "new_adapt_and_reintegrate_count": 0,
        "new_capability_already_covered_count": 0,
        "new_historically_valid_but_incompatible_count": 0,
        "new_reject_for_current_system_count": 0,
        "remaining_insufficient_evidence_open_count": remaining_open,
        "new_final_disposition_count": new_final,
        "final_disposition_changes_performed": new_final,
        "identity_merges_performed": 0,
        "reintegration_performed": False,
        "runtime_mutation_performed": False,
        "landscape_v1_ids": list(LANDSCAPE_V1_IDS),
        "total_ledger_record_count": 53,
        "total_retain_as_is_count": 18,
        "total_adapt_and_reintegrate_count": 0,
        "total_capability_already_covered_count": 0,
        "total_historically_valid_but_incompatible_count": 0,
        "total_reject_for_current_system_count": 0,
        "total_insufficient_evidence_count": 35,
    }
    _dump(pass_root / "pass_v1_status.yaml", status)
    _dump(
        pass_root / "index.yaml",
        {**_header(), "rows": index_rows, "row_count": len(index_rows)},
    )

    schema_path = recon / "schema.yaml"
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    extra = list(schema.get("reevaluate_artifact_files") or [])
    for rel in (
        "reevaluate/pass_v1_status.yaml",
        "reevaluate/index.yaml",
    ):
        if rel not in extra:
            extra.append(rel)
    schema["reevaluate_artifact_files"] = extra
    if "reevaluate" not in schema:
        schema["reevaluate"] = []
    for field in (
        "pass_id",
        "input_pass_id",
        "disposition_burden_met",
        "disposition_candidate",
        "disposition",
        "lifecycle_state",
        "final_disposition_change_performed",
        "current_evidence_set",
        "historical_function",
        "historical_relations",
        "current_system_analogues",
        "identity_status",
        "successor_status",
        "replacement_status",
        "current_value_status",
        "current_compatibility_status",
        "contradictions",
        "unresolved_gaps",
        "evaluation_result",
        "alternatives_rejected",
        "claims",
        "evidence_refs",
        "previous_adjudication",
    ):
        if field not in schema["reevaluate"]:
            schema["reevaluate"].append(field)
    schema["reevaluate_is_not_reintegration"] = True
    schema["reevaluate_burden_unmet_remains_open"] = True
    _dump(schema_path, schema)
    return {
        "attempted": attempted,
        "remaining_open": remaining_open,
        "new_final": new_final,
    }


def main() -> int:
    stats = persist_reevaluate_open_records_pass_v1(repo_root=Path(__file__).resolve().parents[3])
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
