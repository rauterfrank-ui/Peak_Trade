"""Reuse-versus-fresh matrix. This GO does not promote predecessor Live facts."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    REUSE_CLASSIFICATIONS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)


def _row(
    *,
    candidate: str,
    classification: str,
    target_11_14_field: str,
    reason: str,
    evidence_paths: tuple[str, ...],
) -> dict[str, Any]:
    if classification not in REUSE_CLASSIFICATIONS:
        raise Section1114OfflineSurfaceError(f"UNKNOWN_REUSE_CLASS:{classification}")
    return {
        "candidate": candidate,
        "classification": classification,
        "target_11_14_field": target_11_14_field,
        "reusable_as_identical_11_14_fact": classification == "REUSABLE_AS_IDENTICAL_11_14_FACT",
        "promotion_authorized_by_this_go": False,
        "reason": reason,
        "evidence_paths": list(evidence_paths),
    }


def build_reuse_vs_fresh_matrix_v1() -> dict[str, Any]:
    rows = [
        _row(
            candidate="SECTION_11_13_2_LIVE_PRIVATE_READ_ONLY_PROVEN",
            classification="REQUIRES_OWNER_POLICY_DECISION",
            target_11_14_field="LIVE_PRIVATE_READ_ONLY_PROVEN",
            reason=(
                "Same field name is bound true as §11.13.2 SSOT on SHA "
                "d10a44a51d2c3314f80bdc546423c9fd32e0eb5b. This GO forbids "
                "promoting predecessor proven fields into §11.14. Identity of "
                "11.14 consumption is unproven; freshness versus current main "
                "is unproven."
            ),
            evidence_paths=(
                "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
                "evidence/ops/section_11_13_2_live_private_read_only_proven_v1/20260811T170310Z/",
            ),
        ),
        _row(
            candidate="SECTION_11_13_3_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION",
            classification="SEMANTICALLY_DIFFERENT",
            target_11_14_field="LIVE_POSITION_RECONCILED",
            reason=(
                "§11.13.3 proves LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION. That "
                "is not LIVE_POSITION_RECONCILED. Historical SHA "
                "c9c70233db9787f54b164026501ff3aaad286c38."
            ),
            evidence_paths=(
                "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
                "evidence/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1/20260811T211828Z/",
            ),
        ),
        _row(
            candidate="SECTION_11_13_4_LIVE_DRY_RUN_ORDER_PLAN_PROVEN",
            classification="SEMANTICALLY_DIFFERENT",
            target_11_14_field="LIVE_ORDER_PLAN_OBSERVED",
            reason=(
                "§11.13.4 proves LIVE_DRY_RUN_ORDER_PLAN_PROVEN with "
                "ORDER_PLAN_RESULT=BLOCKED_NO_EXECUTE and NO_LIVE_ORDER_SUBMIT. "
                "That is not LIVE_ORDER_PLAN_OBSERVED."
            ),
            evidence_paths=(
                "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
                "evidence/ops/section_11_13_4_live_dry_run_order_plan_proven_v1/20260811T230805Z/",
            ),
        ),
        _row(
            candidate="SECTION_11_13_5_E_LIVE_RECONCILIATION_PROVEN",
            classification="SEMANTICALLY_DIFFERENT",
            target_11_14_field="LIVE_POSITION_RECONCILED",
            reason=(
                "§11.13.5.E binds LIVE_RECONCILIATION_PROVEN=true for economic "
                "baseline adoption. Canonical distinction: "
                "LIVE_RECONCILIATION_PROVEN is not LIVE_POSITION_RECONCILED."
            ),
            evidence_paths=(
                "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
                "evidence/ops/section_11_13_5_economic_baseline_and_okx_clearance_v1/20260812T153425Z/",
            ),
        ),
        _row(
            candidate="SECTION_11_13_5_I_CANARY_FIRST_SUBMIT_HTTP_401",
            classification="SUPPORTING_CONTEXT_ONLY",
            target_11_14_field="LIVE_SUBMIT_ACK_OBSERVED",
            reason=(
                "Historical canary first submit HTTP 401 with "
                "CANARY_FIRST_SUBMIT_ACKNOWLEDGED=false. Negative submit is not "
                "LIVE_SUBMIT_ACK_OBSERVED."
            ),
            evidence_paths=("docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",),
        ),
        _row(
            candidate="PRODUCTIVE_FLATTEN_POST_ACKNOWLEDGEMENT",
            classification="SUPPORTING_CONTEXT_ONLY",
            target_11_14_field="LIVE_SUBMIT_ACK_OBSERVED",
            reason=(
                "Flatten POST_RESULT=POST_ACCEPTED is bound under §11.13.5 G10, "
                "not as §11.14 LIVE_SUBMIT_ACK_OBSERVED. This GO forbids promotion."
            ),
            evidence_paths=(
                "evidence/ops/section_11_13_5_productive_flatten_post_and_reconciliation_v1/20260904T061816Z/POST_ACTION.sanitized.json",
                "evidence/ops/section_11_13_5_productive_flatten_post_and_reconciliation_v1/20260904T061816Z/SUMMARY.json",
            ),
        ),
        _row(
            candidate="PRODUCTIVE_FILL_OBSERVATIONS",
            classification="SUPPORTING_CONTEXT_ONLY",
            target_11_14_field="LIVE_FILL_OBSERVED",
            reason=(
                "Venue fill rows exist in flatten observations and G12 P3. They "
                "are 11.13.5/G12 facts. Empty clOrdId on the buy fill remains "
                "unbound as Peak_Trade submit identity. Not §11.14 LIVE_FILL_OBSERVED."
            ),
            evidence_paths=(
                "evidence/ops/section_11_13_5_productive_flatten_post_and_reconciliation_v1/20260904T061816Z/OBSERVATIONS.sanitized.json",
            ),
        ),
        _row(
            candidate="PRODUCTIVE_FEE_OBSERVATIONS",
            classification="SUPPORTING_CONTEXT_ONLY",
            target_11_14_field="LIVE_FEE_OBSERVED",
            reason=(
                "fee=-0.00015548 feeCcy=USDC appears on a buy fill in the flatten "
                "GET pack. Immediate flatten order fee was 0. Supporting context "
                "only; not §11.14 LIVE_FEE_OBSERVED."
            ),
            evidence_paths=(
                "evidence/ops/section_11_13_5_productive_flatten_post_and_reconciliation_v1/20260904T061816Z/OBSERVATIONS.sanitized.json",
            ),
        ),
        _row(
            candidate="G12_P2_VENUE_ACCEPTED",
            classification="SUPPORTING_CONTEXT_ONLY",
            target_11_14_field="LIVE_SUBMIT_ACK_OBSERVED",
            reason="G12 P2 is flatten-conjunction venue-accepted, not a §11.14 ACK claim.",
            evidence_paths=(
                "evidence/ops/section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1/20260904T114059Z/ADJUDICATION.json",
            ),
        ),
        _row(
            candidate="G12_P3_ORDER_FILLED",
            classification="SUPPORTING_CONTEXT_ONLY",
            target_11_14_field="LIVE_FILL_OBSERVED",
            reason="G12 P3 FILL_BOUND_TO_CLORDID is flatten-conjunction, not §11.14 LIVE_FILL_OBSERVED.",
            evidence_paths=(
                "evidence/ops/section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1/20260904T114059Z/ADJUDICATION.json",
            ),
        ),
        _row(
            candidate="G12_P5_DELAYED_TARGET_ZERO",
            classification="SUPPORTING_CONTEXT_ONLY",
            target_11_14_field="LIVE_POSITION_RECONCILED",
            reason="P5 is a delayed posId-zero window. It is not LIVE_POSITION_RECONCILED.",
            evidence_paths=(
                "evidence/ops/section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1/20260904T114059Z/SUMMARY.json",
            ),
        ),
        _row(
            candidate="G12_P7_PENDING_EMPTY",
            classification="SUPPORTING_CONTEXT_ONLY",
            target_11_14_field="LIVE_POSITION_RECONCILED",
            reason="P7 pending-empty is not position-zero and not LIVE_POSITION_RECONCILED.",
            evidence_paths=(
                "evidence/ops/section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1/20260904T114059Z/SUMMARY.json",
            ),
        ),
        _row(
            candidate="G12_P9_NO_UNEXPECTED_RELATED_NONZERO",
            classification="SUPPORTING_CONTEXT_ONLY",
            target_11_14_field="LIVE_POSITION_RECONCILED",
            reason="P9 unfiltered no-unexpected-related-nonzero is not LIVE_POSITION_RECONCILED.",
            evidence_paths=(
                "evidence/ops/section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1/20260904T114059Z/SUMMARY.json",
            ),
        ),
        _row(
            candidate="G12_CANONICAL_CLOSEOUT",
            classification="SUPPORTING_CONTEXT_ONLY",
            target_11_14_field="LIVE_END_TO_END_EVIDENCE_PROVEN",
            reason=(
                "G12_STATUS=CLOSED_LIVE_FLATTEN_PROVABILITY_PROVEN is the "
                "predecessor closeout. SECTION_11_14_AUTHORIZED remains false. "
                "G12 does not authorize §11.14 and does not satisfy observed fields."
            ),
            evidence_paths=(
                "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
                "evidence/ops/section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1/20260904T114059Z/ADJUDICATION.json",
            ),
        ),
        _row(
            candidate="SECTION_11_14_LIVE_EXECUTION_CODE_EXISTS",
            classification="CURRENT_AND_ADMISSIBLE",
            target_11_14_field="LIVE_EXECUTION_PATH_REACHABLE",
            reason=(
                "LIVE_EXECUTION_CODE_EXISTS=true is current on origin/main "
                "fa02c54468cc0320fe8c756bb4da08485fb84597 and proves "
                "STATIC_EXECUTION_GRAPH_COMPLETE / ENTRYPOINT_INTEGRATED. It is "
                "not sufficient for PATH_REACHABLE."
            ),
            evidence_paths=(
                "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
                "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/20260904T123100Z/",
            ),
        ),
        _row(
            candidate="SECTION_11_13_2_PRIVATE_GET_SUCCESS",
            classification="STALE_FOR_REACHABILITY",
            target_11_14_field="LIVE_EXECUTION_PATH_REACHABLE",
            reason=(
                "§11.13.2 private-read success is historical (20260811). "
                "Credential-once-worked is not current authenticated connectivity. "
                "Also not LIVE_PRIVATE_READ_ONLY_PROVEN for §11.14."
            ),
            evidence_paths=(
                "evidence/ops/section_11_13_2_live_private_read_only_proven_v1/20260811T170310Z/",
            ),
        ),
        _row(
            candidate="SECTION_11_13_5_P08_READ_ONLY_CLOSURE_GET_20260903T210159Z",
            classification="STALE_FOR_REACHABILITY",
            target_11_14_field="LIVE_EXECUTION_PATH_REACHABLE",
            reason=(
                "P08 read-only closure GET pack is a different Owner-GO, different "
                "purpose, and previous-day observation. Historical success does not "
                "imply current reachable. Supporting context only for credential "
                "class reuse; REQUIRES_FRESH_OBSERVATION for auth/host/read-access."
            ),
            evidence_paths=(
                "evidence/ops/section_11_13_5_p08_read_only_closure_v1/20260903T210159Z/",
            ),
        ),
        _row(
            candidate="SECTION_11_13_5_G12_P7_P9_PRIVATE_GET",
            classification="STALE_FOR_REACHABILITY",
            target_11_14_field="LIVE_EXECUTION_PATH_REACHABLE",
            reason=(
                "G12 P7/P9 private GETs proved flatten-conjunction observations, "
                "not current §11.14 path reachability."
            ),
            evidence_paths=(
                "evidence/ops/section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1/20260904T114059Z/",
            ),
        ),
        _row(
            candidate="CONFIGURED_EEA_HOST_DEFAULT",
            classification="CURRENT_BUT_INSUFFICIENT",
            target_11_14_field="LIVE_EXECUTION_PATH_REACHABLE",
            reason=(
                "REUSED_BINDING_REST_HOST=eea.okx.com is a configured default. "
                "Configured host is not current resolvability or connectivity."
            ),
            evidence_paths=(
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/constants_v1.py",
            ),
        ),
        _row(
            candidate="SECTION_4_9_CURRENTLY_REACHABLE",
            classification="SEMANTICALLY_DIFFERENT",
            target_11_14_field="LIVE_EXECUTION_PATH_REACHABLE",
            reason=(
                "§4.9 CURRENTLY_REACHABLE means the Python surface is constructible. "
                "Canonical distinction: CURRENTLY_REACHABLE is not "
                "LIVE_EXECUTION_PATH_REACHABLE."
            ),
            evidence_paths=("docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",),
        ),
    ]
    identical = [row for row in rows if row["reusable_as_identical_11_14_fact"]]
    if identical:
        names = ",".join(row["candidate"] for row in identical)
        if names != "SECTION_11_14_LIVE_EXECUTION_CODE_EXISTS":
            raise Section1114OfflineSurfaceError("UNEXPECTED_IDENTICAL_REUSE:" + names)
    return {
        "schema_version": "section_11_14_reuse_vs_fresh.v1",
        "default_rule": "NON_REUSE_WHEN_IDENTITY_NOT_PROVEN",
        "promotion_authorized_by_this_go": False,
        "row_count": len(rows),
        "rows": rows,
    }
