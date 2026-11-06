"""Gap adjudication for authenticated private runtime read / permit issuance."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.runtime_permit_v1 import (
    PRICE_BINDING_ROLE,
)


def adjudicate_gaps_v1(*, runtime_facts: Mapping[str, Any]) -> dict[str, Any]:
    get_performed = runtime_facts.get("GET_PERFORMED_THIS_PERSIST") is True
    private_auth = runtime_facts.get("PRIVATE_AUTH_USED") is True
    unsigned = runtime_facts.get("UNSIGNED_FLATTEN_TRANSPORT_USED") is True
    flatten_transport = runtime_facts.get("GATED_PRODUCTIVE_FLATTEN_TRANSPORT_USED") is True
    permit_issued = bool((runtime_facts.get("PERMIT_AUDIT") or {}).get("issued"))
    observation_class = str(
        (runtime_facts.get("OBSERVATION") or {}).get("POSITION_OBSERVATION_CLASS") or ""
    )
    hmac_present = bool(
        ((runtime_facts.get("AUTH_PATH") or {}).get("HEADER_PRESENCE") or {}).get(
            "AUTH_SIGN_HEADER_PRESENT"
        )
    )
    g05_get_path_closed = (
        get_performed
        and unsigned is False
        and flatten_transport is False
        and (hmac_present or not private_auth)
    )
    g06_closed = permit_issued
    g07_closed = get_performed
    g08_closed = permit_issued
    gaps = (
        {
            "GAP_ID": "G05",
            "CURRENT_STATUS": (
                "CLOSED_AUTHENTICATED_PRIVATE_GET_PATH"
                if g05_get_path_closed
                else "OPEN_GET_PATH_HMAC_OR_TRANSPORT_NOT_PROVEN"
            ),
            "EVIDENCE": (
                "Authenticated GET uses LiveCanaryHttpClientV1 + HMAC signer; "
                "GatedProductiveFlattenTransportV1 is forbidden on this path. "
                "Unsigned flatten POST urllib remains N12 PRODUCTIVE_FLATTEN_POST."
            ),
            "AUTHORITY_CLASS": "AUTHENTICATED_PRIVATE_RUNTIME_READ",
            "CAN_CLOSE_UNDER_THIS_GO": True,
            "RATIONALE": (
                "GET-path unsigned-urllib relationship is in this GO. Unsigned "
                "flatten POST opener enables N12 and remains outside this GO."
            ),
            "UNSIGNED_FLATTEN_POST_URLLIB_REMAINS_N12": True,
            "GET_PATH_HMAC_REQUIRED": True,
        },
        {
            "GAP_ID": "G06",
            "CURRENT_STATUS": (
                "CLOSED_SIZE_AND_OBSERVATION_BINDING"
                if g06_closed
                else "OPEN_RUNTIME_PERMIT_NOT_ISSUED"
            ),
            "EVIDENCE": (
                "RuntimeIssuedPermitV1 binds observation_identity, "
                "observation_body_sha256, size_binding, instrument, account, "
                f"SHA, expiry. price_binding_role={PRICE_BINDING_ROLE}"
            ),
            "AUTHORITY_CLASS": "RUNTIME_PERMIT_ISSUANCE",
            "CAN_CLOSE_UNDER_THIS_GO": True,
            "RATIONALE": (
                "Size and observation identity are permit-issuance class. Price "
                "is FlattenPricePermitV1 at N08; public GET is not on this path."
            ),
            "PRICE_BINDING_ROLE": PRICE_BINDING_ROLE,
        },
        {
            "GAP_ID": "G07",
            "CURRENT_STATUS": (
                "CLOSED_AUTHENTICATED_PRIVATE_GET_PERFORMED"
                if g07_closed
                else "OPEN_GET_NOT_PERFORMED"
            ),
            "EVIDENCE": f"GET_PERFORMED_THIS_PERSIST={get_performed}",
            "AUTHORITY_CLASS": "AUTHENTICATED_PRIVATE_RUNTIME_READ",
            "CAN_CLOSE_UNDER_THIS_GO": True,
            "RATIONALE": (
                "N11 private GET is authorized. STPR_RUNTIME_PROVEN remains a "
                "frozen STPR field and is not rewritten."
            ),
        },
        {
            "GAP_ID": "G08",
            "CURRENT_STATUS": (
                "CLOSED_RUNTIME_PERMIT_ISSUED" if g08_closed else "OPEN_RUNTIME_PERMIT_NOT_ISSUED"
            ),
            "EVIDENCE": f"PERMIT_ISSUED={permit_issued}; CLASS={observation_class}",
            "AUTHORITY_CLASS": "RUNTIME_PERMIT_ISSUANCE",
            "CAN_CLOSE_UNDER_THIS_GO": True,
            "RATIONALE": (
                "Issuance is authorized only when fresh CASE_A nonzero observation "
                "and size binding pass. Fail-closed is not a fake permit."
            ),
        },
        {
            "GAP_ID": "G09",
            "CURRENT_STATUS": "OPEN_FLATTEN_NETWORK_SESSION_REMAINS_UNAUTHORIZED",
            "EVIDENCE": "NETWORK_SESSION_AUTHORIZED=false; GET uses UrllibLiveCanaryTransportV1",
            "AUTHORITY_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
            "CAN_CLOSE_UNDER_THIS_GO": False,
            "RATIONALE": (
                "Flatten productive network_session_authorized remains N12. GET "
                "wire is not that flag."
            ),
        },
        {
            "GAP_ID": "G10",
            "CURRENT_STATUS": "OPEN_PRODUCTIVE_FLATTEN_POST_NOT_AUTHORIZED",
            "EVIDENCE": "POST_PERFORMED=false",
            "AUTHORITY_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
            "CAN_CLOSE_UNDER_THIS_GO": False,
            "RATIONALE": "This GO hard-stops before POST.",
        },
        {
            "GAP_ID": "G11",
            "CURRENT_STATUS": "OPEN_POST_EXEC_RECONCILIATION_NOT_AUTHORIZED",
            "EVIDENCE": "PRODUCTIVE_RECONCILIATION_AUTHORIZED=false",
            "AUTHORITY_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
            "CAN_CLOSE_UNDER_THIS_GO": False,
            "RATIONALE": "Reconciliation presupposes productive POST.",
        },
        {
            "GAP_ID": "G12",
            "CURRENT_STATUS": "OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN",
            "EVIDENCE": "LIVE_FLATTEN_PROVABILITY remains UNPROVEN",
            "AUTHORITY_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
            "CAN_CLOSE_UNDER_THIS_GO": False,
            "RATIONALE": "Terminal requires POST plus post-action POS==0.",
        },
        {
            "GAP_ID": "G13",
            "CURRENT_STATUS": "OPEN_PENDING_ORDERS_GET_ENDPOINT_UNPROVEN_FOR_PERMIT",
            "EVIDENCE": "PENDING_ORDERS_GET_PERFORMED=false; N11 open question retained",
            "AUTHORITY_CLASS": "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
            "CAN_CLOSE_UNDER_THIS_GO": False,
            "RATIONALE": (
                "Pending-orders GET is an N08/N12 send-time open-order producer, "
                "not a proven permit-issuance prerequisite. Exact endpoint remains "
                "an open question; this GO does not invent it."
            ),
        },
    )
    remaining = [g for g in gaps if not str(g["CURRENT_STATUS"]).startswith("CLOSED_")]
    runtime_remaining = [
        g["GAP_ID"]
        for g in remaining
        if g["GAP_ID"] in {"G07", "G08", "G09", "G10", "G11", "G12", "G13"}
    ]
    if g07_closed and "G07" in runtime_remaining:
        runtime_remaining.remove("G07")
    if g08_closed and "G08" in runtime_remaining:
        runtime_remaining.remove("G08")
    return {
        "GAPS": list(gaps),
        "G05_STATUS": gaps[0]["CURRENT_STATUS"],
        "G06_STATUS": gaps[1]["CURRENT_STATUS"],
        "G07_STATUS": gaps[2]["CURRENT_STATUS"],
        "G08_STATUS": gaps[3]["CURRENT_STATUS"],
        "REMAINING_GAP_COUNT": len(remaining),
        "REMAINING_RUNTIME_GAPS": runtime_remaining,
        "REMAINING_EXTERNAL_STATE_GAPS": [
            g["GAP_ID"] for g in remaining if g["GAP_ID"] in {"G09", "G10", "G11", "G12", "G13"}
        ],
        "REMAINING_OWNER_DECISIONS": [
            "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION",
        ],
    }
