"""Machine-checkable PR #6252 merge-closeout lineage."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_pr_6252_merge_closeout_v1.constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    G12_STATUS_VALUE,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_MERGE_GO_FOR_PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_PR_STATUS,
    PR_6252_MERGE_SHA,
    PREDECESSOR_SLICE,
    RECOVERY_POSITION_SEMANTICS_VALUE,
    STALE_POINTER_WAS_VALUE,
    TARGET_INSTRUMENT_ID,
)

LINEAGE_FIELD_NAMES: tuple[str, ...] = (
    "producer",
    "field",
    "source_path",
    "status",
    "semantic_object",
    "observed_value",
    "transformation",
    "output_object",
    "epistemic_class",
    "adjudication_status",
)


def _seam(
    *,
    producer: str,
    field: str,
    source_path: str,
    status: str,
    semantic_object: str,
    observed_value: str,
    transformation: str,
    output_object: str,
    epistemic_class: str,
    adjudication_status: str,
) -> dict[str, str]:
    return {
        "producer": producer,
        "field": field,
        "source_path": source_path,
        "status": status,
        "semantic_object": semantic_object,
        "observed_value": observed_value,
        "transformation": transformation,
        "output_object": output_object,
        "epistemic_class": epistemic_class,
        "adjudication_status": adjudication_status,
    }


PR_6252_MERGE_CLOSEOUT_LINEAGE: tuple[dict[str, str], ...] = (
    _seam(
        producer="PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
        field="PREDECESSOR",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="current_bound_predecessor",
        semantic_object=PREDECESSOR_SLICE,
        observed_value="PREDECESSOR_CLOSED",
        transformation="PREDECESSOR_REQUIRED_NOT_REWRITTEN",
        output_object="FLATTEN_PERSIST_CLOSED_INPUT",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_PREDECESSOR_WAS_PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
    ),
    _seam(
        producer="github_pr_6252_squash_merge",
        field="PR_6252_MERGE_SHA",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="current_bound_producer",
        semantic_object="SQUASH_MERGED_ONTO_ORIGIN_MAIN",
        observed_value=PR_6252_MERGE_SHA,
        transformation="POST_MERGE_CLOSEOUT_NOT_NEW_MERGE",
        output_object="PR_6252_SQUASH_MERGED",
        epistemic_class="FORENSIC_RAW",
        adjudication_status="PROVEN_PR_6252_SQUASH_MERGED_AT_BOUND_SHA",
    ),
    _seam(
        producer="adjudicate_pr_6252_merge_closeout_v1",
        field="OWNER_MERGE_GO",
        source_path=("src/ops/section_11_13_5_pr_6252_merge_closeout_v1/adjudicate_v1.py"),
        status="current_bound_producer",
        semantic_object="STALE_NEXT_POINTER_CORRECTION",
        observed_value=STALE_POINTER_WAS_VALUE,
        transformation="CONSUMED_CLOSED_NOT_REWRITTEN_IN_PREDECESSOR",
        output_object=OWNER_MERGE_GO_FOR_PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_PR_STATUS,
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_OWNER_MERGE_GO_CONSUMED_BY_PR_6252",
    ),
    _seam(
        producer="PRODUCTIVE_FLATTEN_RECOVERY_READ_ONLY",
        field="G12_STATUS",
        source_path=(
            "evidence/ops/section_11_13_5_productive_flatten_post_and_reconciliation_v1/"
            "20260904T061816Z/ADJUDICATION.json"
        ),
        status="current_bound_producer",
        semantic_object="LIVE_FLATTEN_PROVABILITY",
        observed_value=G12_STATUS_VALUE,
        transformation="PRESERVE_OPEN_NOT_PROMOTE",
        output_object="G12_REMAINS_OPEN",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_G12_MUST_REMAIN_OPEN",
    ),
    _seam(
        producer="PRODUCTIVE_FLATTEN_RECOVERY_READ_ONLY",
        field="RECOVERY_POSITION_SEMANTICS",
        source_path=(
            "evidence/ops/section_11_13_5_productive_flatten_post_and_reconciliation_v1/"
            "20260904T061816Z_recovery_read_only/RECOVERY_RECON.sanitized.json"
        ),
        status="current_bound_producer",
        semantic_object="CASE_C_EMPTY_DATA_NOT_ZERO",
        observed_value=RECOVERY_POSITION_SEMANTICS_VALUE,
        transformation="EMPTY_DATA_NOT_COLLAPSED_ONTO_ZERO",
        output_object="TARGET_POSITION_ZERO_REMAINS_UNPROVEN",
        epistemic_class="FORENSIC_RAW",
        adjudication_status="PROVEN_EMPTY_DATA_IS_NOT_ZERO",
    ),
    _seam(
        producer="adjudicate_pr_6252_merge_closeout_v1",
        field="EARLIEST_UNRESOLVED_DEPENDENCY",
        source_path=("src/ops/section_11_13_5_pr_6252_merge_closeout_v1/adjudicate_v1.py"),
        status="current_bound_producer",
        semantic_object="NEXT_AUTHORITY_BOUNDARY",
        observed_value=EARLIEST_UNRESOLVED_DEPENDENCY,
        transformation="OWNER_MERGE_GO_CONSUMED_G12_REMAINS",
        output_object=NEXT_OWNER_GO_REQUIRED,
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_NEXT_NOT_AUTHORIZED",
    ),
    _seam(
        producer="PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
        field="TARGET_INSTRUMENT_ID",
        source_path="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        status="current_bound_scope",
        semantic_object="CANONICAL_INSTRUMENT_SCOPE",
        observed_value=TARGET_INSTRUMENT_ID,
        transformation="SCOPE_PRESERVED_NOT_MUTATED",
        output_object="CLOSEOUT_INSTRUMENT_SCOPE",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_FAIL_CLOSED",
    ),
    _seam(
        producer="adjudicate_pr_6252_merge_closeout_v1",
        field="BOUND_ORIGIN_MAIN_SHA",
        source_path=("src/ops/section_11_13_5_pr_6252_merge_closeout_v1/constants_v1.py"),
        status="current_bound_producer",
        semantic_object="EXPECTED_ORIGIN_MAIN_SHA",
        observed_value=EXPECTED_ORIGIN_MAIN_SHA,
        transformation="CLOSEOUT_BOUND_TO_MERGED_FLATTEN_PERSIST",
        output_object="SHA_MATCH_REQUIRED",
        epistemic_class="CANONICAL_AUTHORITY",
        adjudication_status="PROVEN_SHA_BOUND_NOT_NETWORK",
    ),
)


def pr_6252_merge_closeout_lineage_v1() -> list[dict[str, str]]:
    return [dict(item) for item in PR_6252_MERGE_CLOSEOUT_LINEAGE]


def lineage_census_summary_v1() -> dict[str, Any]:
    seams = pr_6252_merge_closeout_lineage_v1()
    counts: dict[str, int] = {}
    proven = 0
    not_promoted = 0
    for seam in seams:
        klass = str(seam.get("epistemic_class") or "")
        counts[klass] = counts.get(klass, 0) + 1
        status = str(seam.get("adjudication_status") or "")
        if status.startswith("PROVEN"):
            proven += 1
        if "NOT_AUTHORIZED" in status or "REMAIN" in status or "NOT_ZERO" in status:
            not_promoted += 1
    return {
        "SEAM_COUNT": len(seams),
        "EPISTEMIC_CLASS_COUNTS": counts,
        "PROVEN_SEAMS": proven,
        "NOT_PROMOTED_SEAMS": not_promoted,
        "LINEAGE_FIELD_NAMES": list(LINEAGE_FIELD_NAMES),
    }
