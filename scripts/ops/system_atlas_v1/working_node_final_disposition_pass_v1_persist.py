"""Persist WORKING_NODE_FINAL_DISPOSITION_PASS_V1. Additive. Not RCN census.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Does not overwrite frozen UNDERSTAND/EVALUATE/ADJUDICATE/EVIDENCE_RESOLUTION/
REEVALUATE snapshots. Does not mutate ledger.yaml. Does not reintegrate,
implement ADAPT, delete, restore, rewire runtime, or authorize Live/Testnet.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from scripts.ops.system_atlas_v1.constants_v1 import (
    RECONCILIATION_RELATIVE_ROOT,
    RECONCILIATION_SCHEMA_VERSION,
)
from scripts.ops.system_atlas_v1.working_node_final_disposition_pass_v1_records import (
    BOUND_REF,
    BOUND_SHA,
    EXPECTED_ACCEPTED,
    EXPECTED_ADAPT,
    EXPECTED_CHANGED,
    EXPECTED_COUNT,
    EXPECTED_COVERED,
    EXPECTED_HVBI,
    EXPECTED_REJECT,
    EXPECTED_RETAIN,
    EXPECTED_SAFETY_CRITICAL,
    IDENTITY_UNIVERSE,
    OWNER_GO,
    PASS_ID,
    working_node_final_disposition_records,
)

PASS_REL = "working_nodes"


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
        "bound_against_ref": BOUND_REF,
        "bound_against_sha": BOUND_SHA,
        "atlas_authority": "NONE",
        "reconciliation_authority": "NONE",
        "pass_id": PASS_ID,
        "owner_go": OWNER_GO,
        "identity_universe": IDENTITY_UNIVERSE,
        "identity_fusion_forbidden": True,
        "rcn_census_reopened": False,
        "rcn_ledger_mutated": False,
        "reintegration_performed": False,
        "runtime_mutation_performed": False,
        "implementation_authorized": False,
        "integrate_or_disposition_execution_authorized": False,
    }


def persist_working_node_final_disposition_pass_v1(*, repo_root: Path) -> dict[str, Any]:
    records = working_node_final_disposition_records(repo_root=repo_root)
    if len(records) != EXPECTED_COUNT:
        raise RuntimeError(f"WN_COUNT_MISMATCH:{len(records)}!={EXPECTED_COUNT}")
    ids = [row["working_node_id"] for row in records]
    if len(set(ids)) != EXPECTED_COUNT:
        raise RuntimeError("WN_DUPLICATE_OR_MISSING")
    counts = Counter(row["final_disposition"] for row in records)
    if counts["RETAIN_AS_IS"] != EXPECTED_RETAIN:
        raise RuntimeError(f"RETAIN_COUNT_MISMATCH:{counts['RETAIN_AS_IS']}")
    if counts["ADAPT_AND_REINTEGRATE"] != EXPECTED_ADAPT:
        raise RuntimeError(f"ADAPT_COUNT_MISMATCH:{counts['ADAPT_AND_REINTEGRATE']}")
    if counts["CAPABILITY_ALREADY_COVERED"] != EXPECTED_COVERED:
        raise RuntimeError(f"COVERED_COUNT_MISMATCH:{counts['CAPABILITY_ALREADY_COVERED']}")
    if counts["HISTORICALLY_VALID_BUT_INCOMPATIBLE"] != EXPECTED_HVBI:
        raise RuntimeError(f"HVBI_COUNT_MISMATCH:{counts['HISTORICALLY_VALID_BUT_INCOMPATIBLE']}")
    if counts["REJECT_FOR_CURRENT_SYSTEM"] != EXPECTED_REJECT:
        raise RuntimeError(f"REJECT_COUNT_MISMATCH:{counts['REJECT_FOR_CURRENT_SYSTEM']}")
    accepted = sum(1 for row in records if row["proposal_accepted"] is True)
    changed = sum(1 for row in records if row["proposal_accepted"] is False)
    if accepted != EXPECTED_ACCEPTED or changed != EXPECTED_CHANGED:
        raise RuntimeError(f"ACCEPT_CHANGE_MISMATCH:{accepted}/{changed}")
    safety = sum(1 for row in records if row["safety_critical"] is True)
    if safety != EXPECTED_SAFETY_CRITICAL:
        raise RuntimeError(f"SAFETY_CRITICAL_COUNT_MISMATCH:{safety}")

    recon = repo_root / RECONCILIATION_RELATIVE_ROOT
    root = recon / PASS_REL
    records_dir = root / "records"
    for existing in records_dir.glob("*.yaml"):
        existing.unlink()

    status = _header()
    status.update(
        {
            "working_node_record_count": EXPECTED_COUNT,
            "retain_as_is_count": EXPECTED_RETAIN,
            "adapt_and_reintegrate_count": EXPECTED_ADAPT,
            "capability_already_covered_count": EXPECTED_COVERED,
            "historically_valid_but_incompatible_count": EXPECTED_HVBI,
            "reject_for_current_system_count": EXPECTED_REJECT,
            "proposal_accepted_count": EXPECTED_ACCEPTED,
            "proposal_changed_count": EXPECTED_CHANGED,
            "safety_critical_count": EXPECTED_SAFETY_CRITICAL,
            "remaining_open_record_count": 0,
            "hold_for_owner_review_count": 0,
            "rcn_ledger_record_count_unchanged": 53,
            "frozen_rcn_snapshots_unchanged": True,
            "final_dispositions_authorized": True,
            "integrate_or_disposition_started": False,
        }
    )
    _dump(root / "pass_v1_status.yaml", status)

    index_rows = []
    for row in records:
        payload = _header()
        payload.update(row)
        payload["claims"] = [
            {
                "claim_class": "ADJUDICATED_CONCLUSION",
                "text": (
                    f"{row['working_node_id']} owner-final disposition is "
                    f"{row['final_disposition']} ({row['final_disposition_owner_label']}). "
                    "Classification finality is not implementation, deletion, restoration, "
                    "or runtime authorization."
                ),
                "evidence": list(row["primary_paths"])
                + [
                    "docs/system_atlas/reconciliation/working_nodes/pass_v1_status.yaml",
                    "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
                ],
                "used_as_fact": True,
            }
        ]
        _dump(records_dir / f"{row['working_node_id']}.yaml", payload)
        index_rows.append(
            {
                "working_node_id": row["working_node_id"],
                "adjudication_index": row["adjudication_index"],
                "final_disposition": row["final_disposition"],
                "final_disposition_owner_label": row["final_disposition_owner_label"],
                "proposal_accepted": row["proposal_accepted"],
                "lifecycle_state": row["lifecycle_state"],
                "implementation_authorized": False,
                "safety_critical": row["safety_critical"],
            }
        )
    index = _header()
    index.update({"row_count": EXPECTED_COUNT, "rows": index_rows})
    _dump(root / "index.yaml", index)

    schema_path = recon / "schema.yaml"
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    extra = list(schema.get("working_node_final_disposition_artifact_files") or [])
    for rel in (
        "working_nodes/pass_v1_status.yaml",
        "working_nodes/index.yaml",
    ):
        if rel not in extra:
            extra.append(rel)
    schema["working_node_final_disposition_artifact_files"] = extra
    schema["working_node_final_disposition_is_not_rcn_census"] = True
    schema["working_node_final_disposition_is_not_reintegration"] = True
    schema["working_node_final_disposition_implementation_authorized"] = False
    schema["working_node_final_disposition_record_count"] = EXPECTED_COUNT
    schema["working_node_final_disposition_retain_count"] = EXPECTED_RETAIN
    schema["working_node_final_disposition_adapt_count"] = EXPECTED_ADAPT
    schema["working_node_final_disposition_covered_count"] = EXPECTED_COVERED
    schema["working_node_final_disposition_hvbi_count"] = EXPECTED_HVBI
    schema["working_node_final_disposition_reject_count"] = EXPECTED_REJECT
    _dump(schema_path, schema)
    return status


if __name__ == "__main__":
    persist_working_node_final_disposition_pass_v1(repo_root=Path(".").resolve())
