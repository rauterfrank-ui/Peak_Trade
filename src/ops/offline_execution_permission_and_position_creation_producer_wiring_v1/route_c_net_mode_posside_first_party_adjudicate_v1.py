"""Adjudicate Route-C net-mode posSide first-party contract evidence exhaustion."""

from __future__ import annotations

from typing import Any

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_net_mode_posside_first_party_census_v1 import (
    FIRST_PARTY_EVIDENCE_RECORDS_V1,
    census_summary_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_net_mode_posside_first_party_contract_evidence_constants_v1 import (
    CANARY_SEMANTICS_TRANSFER_USED,
    EVIDENCE_EXHAUSTION_PROVEN,
    FIRST_PARTY_CONTRACT_EVIDENCE_SUFFICIENT,
    FIRST_PARTY_ROUTE_C_NET_MODE_POSSIDE_CONTRACT_FOUND,
    G_POSMODE_STATUS_CLOSED,
    G_POSMODE_STATUS_CLOSED_AS,
    MISSING_EVIDENCE_EDGE,
    OWNER_GO,
    POSITION_MODE_FAIL_CLOSED,
    POSITION_MODE_SEMANTICS_UNPROVEN,
    PREDECESSOR_SLICE,
    SEARCH_FAMILIES,
    SEARCH_SPACE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_constants_v1 import (
    CREATE_PATH_ARCHITECTURALLY_COMPLETE,
    CREATE_PATH_CURRENTLY_AUTHORIZED,
    CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE,
    CURRENT_PRODUCTIVE_WIRE_REACHABLE,
    PREREQUISITE_08_CLOSED,
)


def adjudicate_route_c_net_mode_posside_first_party_contract_v1() -> dict[str, Any]:
    summary = census_summary_v1()
    proven_records = [r for r in FIRST_PARTY_EVIDENCE_RECORDS_V1 if r.proves_submit_body_semantics]
    if proven_records:
        result_class = "FIRST_PARTY_CONTRACT_EVIDENCE_SUFFICIENT"
        sufficient = True
        exhaustion = False
        contract_found = True
    else:
        result_class = "FIRST_PARTY_CONTRACT_EVIDENCE_INSUFFICIENT_FAIL_CLOSED"
        sufficient = False
        exhaustion = True
        contract_found = False

    return {
        "OWNER_GO": OWNER_GO,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "RESULT_CLASS": result_class,
        "G_POSMODE_ADJUDICATION": result_class,
        "FIRST_PARTY_CONTRACT_EVIDENCE_SUFFICIENT": sufficient,
        "EVIDENCE_EXHAUSTION_PROVEN": exhaustion,
        "FIRST_PARTY_ROUTE_C_NET_MODE_POSSIDE_CONTRACT_FOUND": contract_found,
        "POSITION_MODE_SUBMIT_BODY_SEMANTICS": POSITION_MODE_SEMANTICS_UNPROVEN,
        "POSITION_MODE_FAIL_CLOSED": POSITION_MODE_FAIL_CLOSED,
        "PROVEN_POSSIDE_RULE": None,
        "PROVEN_SCOPE": None,
        "PROVENANCE": "REPOSITORY_FIRST_PARTY_CENSUS_EXHAUSTION",
        "CANARY_SEMANTICS_TRANSFER_USED": CANARY_SEMANTICS_TRANSFER_USED,
        "G_POSMODE_STATUS": G_POSMODE_STATUS_CLOSED,
        "G_POSMODE_STATUS_CLOSED_AS": G_POSMODE_STATUS_CLOSED_AS,
        "MISSING_EVIDENCE_EDGE": MISSING_EVIDENCE_EDGE if not sufficient else None,
        "POSMODE_NET_SEMANTICS": (
            "ACCOUNT_CONFIG_POSMODE_RAW_net_mode_PROVEN_SEPARATE_FROM_SUBMIT_BODY_POSSIDE"
        ),
        "POSSIDE_ORDER_REQUEST_SEMANTICS": "UNPROVEN_FAIL_CLOSED",
        "POSITION_REPRESENTATION_VS_ORDER_REQUEST_DISTINCTION": (
            "POSITION_GET_AND_LEVERAGE_GET_POSSIDE_ARE_NOT_SUBMIT_BODY_PROOF"
        ),
        "CREATE_PATH_ARCHITECTURALLY_COMPLETE": CREATE_PATH_ARCHITECTURALLY_COMPLETE,
        "CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE": CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE,
        "CURRENT_PRODUCTIVE_WIRE_REACHABLE": CURRENT_PRODUCTIVE_WIRE_REACHABLE,
        "CREATE_PATH_CURRENTLY_AUTHORIZED": CREATE_PATH_CURRENTLY_AUTHORIZED,
        "PREREQUISITE_08_CLOSED": PREREQUISITE_08_CLOSED,
        "SEARCH_SPACE": SEARCH_SPACE,
        "SEARCH_FAMILIES": list(SEARCH_FAMILIES),
        "CENSUS_STATUS": "EXHAUSTIVE_COMPLETE",
        **summary,
        "CENSUS_RECORDS": [r.to_dict() for r in FIRST_PARTY_EVIDENCE_RECORDS_V1],
        "OPEN_CONTRADICTIONS": [],
    }
