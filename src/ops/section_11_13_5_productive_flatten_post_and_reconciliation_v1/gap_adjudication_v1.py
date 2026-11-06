"""Gap adjudication for productive flatten POST and reconciliation."""

from __future__ import annotations

from typing import Any, Mapping


def adjudicate_gaps_v1(*, runtime_facts: Mapping[str, Any]) -> dict[str, Any]:
    permit_issued = bool((runtime_facts.get("PERMIT_AUDIT") or {}).get("issued"))
    post_used = runtime_facts.get("POST_USED") is True
    post_accepted = str(runtime_facts.get("POST_RESULT") or "") == "POST_ACCEPTED"
    recon = runtime_facts.get("RECONCILIATION_ATTEMPTED") is True
    zero = runtime_facts.get("TARGET_POSITION_ZERO_PROVEN") is True
    proven = runtime_facts.get("LIVE_FLATTEN_PROVABILITY_PROVEN") is True
    pending_pre = (runtime_facts.get("OBSERVATIONS") or {}).get("GET_ORDERS_PENDING_PRE") or {}
    pending_ok = pending_pre.get("SUCCESS") is True
    session = runtime_facts.get("NETWORK_SESSION_INSTANCE_AUTHORIZED") is True
    gaps = (
        {
            "GAP_ID": "G09",
            "CURRENT_STATUS": (
                "CLOSED_FLATTEN_NETWORK_SESSION_INSTANCE_AUTHORIZED"
                if session and post_used
                else "OPEN_FLATTEN_NETWORK_SESSION_NOT_USED"
            ),
            "EVIDENCE": "AuthenticatedGatedProductiveFlattenTransportV1 instance flag",
            "AUTHORITY_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
            "CAN_CLOSE_UNDER_THIS_GO": True,
            "RATIONALE": "Instance session flag is authorized; standing LIVE_AUTHORIZED remains false.",
        },
        {
            "GAP_ID": "G10",
            "CURRENT_STATUS": (
                "CLOSED_PRODUCTIVE_FLATTEN_POST_PERFORMED"
                if post_used
                else "OPEN_PRODUCTIVE_FLATTEN_POST_NOT_PERFORMED"
            ),
            "EVIDENCE": f"POST_USED={post_used}; POST_RESULT={runtime_facts.get('POST_RESULT')}",
            "AUTHORITY_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
            "CAN_CLOSE_UNDER_THIS_GO": True,
            "RATIONALE": "Exactly one flatten POST is authorized when every pre-wire gate PASSes.",
        },
        {
            "GAP_ID": "G11",
            "CURRENT_STATUS": (
                "CLOSED_POST_EXEC_RECONCILIATION_PERFORMED"
                if recon
                else "OPEN_POST_EXEC_RECONCILIATION_NOT_PERFORMED"
            ),
            "EVIDENCE": f"RECONCILIATION_ATTEMPTED={recon}",
            "AUTHORITY_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
            "CAN_CLOSE_UNDER_THIS_GO": True,
            "RATIONALE": "Read-only post-action GETs are authorized after POST.",
        },
        {
            "GAP_ID": "G12",
            "CURRENT_STATUS": (
                "CLOSED_LIVE_FLATTEN_PROVABILITY_PROVEN"
                if proven
                else "OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN"
            ),
            "EVIDENCE": (f"venue_accepted={post_accepted}; target_zero={zero}; proven={proven}"),
            "AUTHORITY_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
            "CAN_CLOSE_UNDER_THIS_GO": True,
            "RATIONALE": "LIVE_FLATTEN_PROVABILITY_PROVEN requires POST plus post-action POS==0 lineage.",
        },
        {
            "GAP_ID": "G13",
            "CURRENT_STATUS": (
                "CLOSED_PENDING_ORDERS_GET_PERFORMED"
                if pending_ok
                else "OPEN_PENDING_ORDERS_GET_NOT_PROVEN"
            ),
            "EVIDENCE": "GET /api/v5/trade/orders-pending reused as N08 open-order producer",
            "AUTHORITY_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
            "CAN_CLOSE_UNDER_THIS_GO": True,
            "RATIONALE": "Canonical pending endpoint is ENDPOINT_ORDERS_PENDING; this GO performs it.",
        },
        {
            "GAP_ID": "G14",
            "CURRENT_STATUS": (
                "CLOSED_RUNTIME_PERMIT_REISSUED_CURRENT_SHA"
                if permit_issued
                else "OPEN_RUNTIME_PERMIT_NOT_ISSUED"
            ),
            "EVIDENCE": "Fresh RuntimeIssuedPermitV1 bound to current origin/main SHA",
            "AUTHORITY_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
            "CAN_CLOSE_UNDER_THIS_GO": True,
            "RATIONALE": "Historical permit is stale; this GO re-issues against current SHA.",
        },
    )
    remaining = [
        str(item["GAP_ID"]) for item in gaps if str(item["CURRENT_STATUS"]).startswith("OPEN_")
    ]
    remaining_owner = ["OWNER_MERGE_GO"]
    if not proven:
        remaining_owner.append("LIVE_FLATTEN_PROVABILITY_IF_NOT_PROVEN")
    return {
        "GAPS": list(gaps),
        "REMAINING_GAP_COUNT": len(remaining),
        "REMAINING_RUNTIME_GAPS": remaining,
        "REMAINING_EXTERNAL_STATE_GAPS": remaining,
        "REMAINING_OWNER_DECISIONS": remaining_owner,
        "G09_STATUS": gaps[0]["CURRENT_STATUS"],
        "G10_STATUS": gaps[1]["CURRENT_STATUS"],
        "G11_STATUS": gaps[2]["CURRENT_STATUS"],
        "G12_STATUS": gaps[3]["CURRENT_STATUS"],
        "G13_STATUS": gaps[4]["CURRENT_STATUS"],
        "G14_STATUS": gaps[5]["CURRENT_STATUS"],
    }
