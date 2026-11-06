"""Exhaustive Route-C create-path blocker census records after Z2DQ.

Each record binds one machine-readable blocker from already-persisted
upstream slices (Z2DP, Z2DO, Z2DN, Z2DQ) and standing fail-closed
constants. No network I/O. No new venue observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_create_path_blocker_constants_v1 import (
    G_POSMODE_RESULT_CLASS,
    G_POSMODE_STATUS,
    G_POSMODE_STATUS_CLOSED_AS,
    Z2DP_EVIDENCE_PACK,
    Z2DQ_EVIDENCE_PACK,
)


@dataclass(frozen=True)
class CreatePathBlockerRecordV1:
    gap_id: str
    description: str
    status: str
    blocked_by: str
    blocks: str
    authority_class: str
    risk_class: str
    offline_only: bool
    runtime_fact_required: bool
    higher_authority_required: bool
    upstream_slice: str
    upstream_evidence: str
    can_be_closed_offline: bool
    bundle_with: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "description": self.description,
            "status": self.status,
            "blocked_by": self.blocked_by,
            "blocks": self.blocks,
            "authority_class": self.authority_class,
            "risk_class": self.risk_class,
            "offline_only": self.offline_only,
            "runtime_fact_required": self.runtime_fact_required,
            "higher_authority_required": self.higher_authority_required,
            "upstream_slice": self.upstream_slice,
            "upstream_evidence": self.upstream_evidence,
            "can_be_closed_offline": self.can_be_closed_offline,
            "bundle_with": self.bundle_with,
        }


CREATE_PATH_BLOCKER_RECORDS_V1: tuple[CreatePathBlockerRecordV1, ...] = (
    CreatePathBlockerRecordV1(
        gap_id="G-POSMODE",
        description=(
            "Route-C net_mode submit-body posSide semantics remain UNPROVEN fail-closed; "
            "repository first-party census exhausted without normative OKX contract"
        ),
        status="CLOSED_FAIL_CLOSED",
        blocked_by="NO_REPOSITORY_FIRST_PARTY_OKX_SUBMIT_BODY_CONTRACT_FOR_NET_MODE_POSSIDE",
        blocks="CREATE_READINESS; submission-ready Route-C body; posSide emit or omit rule",
        authority_class="CONFIG_CONTRACT_OR_FIRST_PARTY_BIND",
        risk_class="R1_OFFLINE_EXHAUSTED",
        offline_only=True,
        runtime_fact_required=False,
        higher_authority_required=False,
        upstream_slice="11.13.5.Z2DQ",
        upstream_evidence=Z2DQ_EVIDENCE_PACK,
        can_be_closed_offline=False,
        bundle_with="none; offline exhaustion complete",
    ),
    CreatePathBlockerRecordV1(
        gap_id="G-PRETRADE-AVAILEQ",
        description=(
            "Trading-account USDC details.availEq NOT_OBSERVED; AVAILABLE_MARGIN gate false; "
            "empty details are not zero"
        ),
        status="OPEN",
        blocked_by="venue observation / account composition",
        blocks="PRETRADE_GATES_READY; FUNDING_EXPOSURE_READY",
        authority_class="VENUE_GET_OBSERVATION",
        risk_class="R2_GET_ONLY_NO_POST",
        offline_only=False,
        runtime_fact_required=True,
        higher_authority_required=True,
        upstream_slice="11.13.5.Z2DP",
        upstream_evidence=Z2DP_EVIDENCE_PACK,
        can_be_closed_offline=False,
        bundle_with="G-CAPACITY_under_explicit_funding_GO_only",
    ),
    CreatePathBlockerRecordV1(
        gap_id="G-CAPACITY",
        description=(
            "Venue maxBuy=0 maxSell=0; VENUE_NONZERO_CAPACITY=PROVEN_ZERO; "
            "quantity BLOCKED_BY_VENUE_CAPACITY"
        ),
        status="OPEN",
        blocked_by="venue capacity / likely unfunded trading account",
        blocks="CREATE_READINESS; any create submit even if posSide were proven",
        authority_class="FUNDING_OR_VENUE_STATE",
        risk_class="R2_GET_OR_FUNDING",
        offline_only=False,
        runtime_fact_required=True,
        higher_authority_required=True,
        upstream_slice="11.13.5.Z2DP",
        upstream_evidence=Z2DP_EVIDENCE_PACK,
        can_be_closed_offline=False,
        bundle_with="G-PRETRADE-AVAILEQ_under_explicit_funding_GO_only",
    ),
    CreatePathBlockerRecordV1(
        gap_id="G-P08",
        description=(
            "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN unresolved; "
            "TARGET_POSITION_NOT_OBSERVED; empty data[] is not zero"
        ),
        status="OPEN",
        blocked_by=(
            "G-POSMODE + G-PRETRADE-AVAILEQ + G-CAPACITY + unauthorized position creation; "
            "or later proven nonzero observation of preexisting position (Z2DN policy)"
        ),
        blocks="flatten cluster 09/12/20; Class-D send-time PASS; execution_ready",
        authority_class="VENUE_GET_OR_AUTHORIZED_CREATE",
        risk_class="R3_GET_OR_POSITION_CREATION",
        offline_only=False,
        runtime_fact_required=True,
        higher_authority_required=True,
        upstream_slice="11.13.5.Z2DP;11.13.5.Z2DN",
        upstream_evidence=Z2DP_EVIDENCE_PACK,
        can_be_closed_offline=False,
        bundle_with="none_with_G-POSMODE; not_same_GO_as_funding",
    ),
    CreatePathBlockerRecordV1(
        gap_id="G-WIRE",
        description=(
            "CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE=false; CURRENT_PRODUCTIVE_WIRE_REACHABLE=false"
        ),
        status="OPEN",
        blocked_by="standing fail-closed constants; upstream blockers unresolved",
        blocks="productive HTTP submit; live transport reachability",
        authority_class="EXECUTION_WIRE",
        risk_class="R4_POST_OR_WIRE",
        offline_only=False,
        runtime_fact_required=False,
        higher_authority_required=True,
        upstream_slice="11.13.5.Z2DO;11.13.5.Z2DQ",
        upstream_evidence=Z2DQ_EVIDENCE_PACK,
        can_be_closed_offline=False,
        bundle_with="none_until_upstream_blockers_close",
    ),
    CreatePathBlockerRecordV1(
        gap_id="G-CREATE-AUTH",
        description="CREATE_PATH_CURRENTLY_AUTHORIZED=false; POSITION_CREATION_CURRENTLY_AUTHORIZED=false",
        status="OPEN",
        blocked_by="all upstream create-path blockers; no risk-bearing Owner-GO consumed",
        blocks="any authorized Route-C create or position creation",
        authority_class="OWNER_GO_EXECUTION",
        risk_class="R4_POST_OR_POSITION_CREATION",
        offline_only=False,
        runtime_fact_required=False,
        higher_authority_required=True,
        upstream_slice="11.13.5.Z2DO;11.13.5.Z2DP;11.13.5.Z2DQ",
        upstream_evidence=Z2DQ_EVIDENCE_PACK,
        can_be_closed_offline=False,
        bundle_with="none",
    ),
    CreatePathBlockerRecordV1(
        gap_id="G-POSITION-MODE-READY",
        description="POSITION_MODE_READY=false; POSITION_MODE_SUBMIT_BODY_SEMANTICS=UNPROVEN",
        status="OPEN",
        blocked_by=G_POSMODE_RESULT_CLASS,
        blocks="submission-ready body; Route-C CANDIDATE to submission-ready promotion",
        authority_class="CONFIG_CONTRACT",
        risk_class="R1_OFFLINE_FAIL_CLOSED",
        offline_only=True,
        runtime_fact_required=False,
        higher_authority_required=False,
        upstream_slice="11.13.5.Z2DQ",
        upstream_evidence=Z2DQ_EVIDENCE_PACK,
        can_be_closed_offline=False,
        bundle_with="G-POSMODE; same adjudication",
    ),
    CreatePathBlockerRecordV1(
        gap_id="G-FUNDING-EXPOSURE",
        description="FUNDING_EXPOSURE_READY=false from Z2DP fresh GET adjudication",
        status="OPEN",
        blocked_by="G-PRETRADE-AVAILEQ; G-CAPACITY",
        blocks="CREATE_READINESS; pre-submit funding envelope",
        authority_class="FUNDING_OR_VENUE_STATE",
        risk_class="R2_GET_OR_FUNDING",
        offline_only=False,
        runtime_fact_required=True,
        higher_authority_required=True,
        upstream_slice="11.13.5.Z2DP",
        upstream_evidence=Z2DP_EVIDENCE_PACK,
        can_be_closed_offline=False,
        bundle_with="G-PRETRADE-AVAILEQ; G-CAPACITY",
    ),
    CreatePathBlockerRecordV1(
        gap_id="G-EXEC-PERMIT",
        description=(
            "Route-C submit composition requires separate risk-bearing execution permit; "
            "implementation GO cannot be execution permit"
        ),
        status="OPEN",
        blocked_by="no consumed risk-bearing Owner-GO for Route-C entry submit",
        blocks="submission-ready promotion even if all pretrade gates pass",
        authority_class="OWNER_GO_EXECUTION",
        risk_class="R4_POST",
        offline_only=False,
        runtime_fact_required=False,
        higher_authority_required=True,
        upstream_slice="11.13.5.Z2DO",
        upstream_evidence=Z2DQ_EVIDENCE_PACK,
        can_be_closed_offline=False,
        bundle_with="G-CREATE-AUTH",
    ),
)


DEPENDENCY_EDGES_V1: tuple[tuple[str, str, str], ...] = (
    ("G-POSMODE", "G-POSITION-MODE-READY", "SAME_ADJUDICATION"),
    ("G-POSMODE", "G-CREATE-AUTH", "BLOCKS_SUBMISSION_READY"),
    ("G-PRETRADE-AVAILEQ", "G-FUNDING-EXPOSURE", "REQUIRED_FOR"),
    ("G-CAPACITY", "G-FUNDING-EXPOSURE", "REQUIRED_FOR"),
    ("G-PRETRADE-AVAILEQ", "G-CREATE-AUTH", "BLOCKS_PRETRADE"),
    ("G-CAPACITY", "G-CREATE-AUTH", "BLOCKS_QUANTITY"),
    ("G-P08", "G-CREATE-AUTH", "CANONICAL_EARLIEST_DEPENDENCY"),
    ("G-POSMODE", "G-P08", "INDEPENDENT_BLOCKER"),
    ("G-WIRE", "G-CREATE-AUTH", "DOWNSTREAM_OF_AUTH"),
    ("G-EXEC-PERMIT", "G-CREATE-AUTH", "REQUIRED_FOR_SUBMIT"),
)


def census_summary_v1() -> dict[str, Any]:
    open_gaps = [r for r in CREATE_PATH_BLOCKER_RECORDS_V1 if r.status == "OPEN"]
    closed_gaps = [r for r in CREATE_PATH_BLOCKER_RECORDS_V1 if r.status != "OPEN"]
    offline_closable = [r for r in CREATE_PATH_BLOCKER_RECORDS_V1 if r.can_be_closed_offline]
    runtime_required = [r for r in CREATE_PATH_BLOCKER_RECORDS_V1 if r.runtime_fact_required]
    higher_auth = [r for r in CREATE_PATH_BLOCKER_RECORDS_V1 if r.higher_authority_required]
    return {
        "BLOCKER_RECORD_COUNT": len(CREATE_PATH_BLOCKER_RECORDS_V1),
        "OPEN_GAP_COUNT": len(open_gaps),
        "CLOSED_GAP_COUNT": len(closed_gaps),
        "OFFLINE_CLOSABLE_GAP_COUNT": len(offline_closable),
        "RUNTIME_FACT_REQUIRED_GAP_COUNT": len(runtime_required),
        "HIGHER_AUTHORITY_GAP_COUNT": len(higher_auth),
        "G_POSMODE_STATUS": G_POSMODE_STATUS,
        "G_POSMODE_STATUS_CLOSED_AS": G_POSMODE_STATUS_CLOSED_AS,
        "UNADJUDICATED_BLOCKER_COUNT": 0,
        "CONTRADICTION_COUNT": 0,
    }
