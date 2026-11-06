"""Standing constants for Route-C net-mode posSide first-party contract evidence."""

from __future__ import annotations

OWNER_GO = "PEAK_TRADE_OWNER_GO_ROUTE_C_NET_MODE_POSSIDE_FIRST_PARTY_CONTRACT_EVIDENCE_V1"
WORKPACKAGE_ID = "ROUTE_C_NET_MODE_POSSIDE_FIRST_PARTY_CONTRACT_EVIDENCE_V1"
THIS_SLICE = "11.13.5.Z2DQ"
PREDECESSOR_SLICE = "11.13.5.Z2DP"
EXPECTED_ORIGIN_MAIN_SHA = "9a764d7e182776521cb09288afa29dcf771e89ed"

POSITION_MODE_SEMANTICS_UNPROVEN = "UNPROVEN"
POSITION_MODE_FAIL_CLOSED = True

EVIDENCE_EXHAUSTION_PROVEN = True
FIRST_PARTY_ROUTE_C_NET_MODE_POSSIDE_CONTRACT_FOUND = False
FIRST_PARTY_CONTRACT_EVIDENCE_SUFFICIENT = False
CANARY_SEMANTICS_TRANSFER_USED = False

G_POSMODE_STATUS_CLOSED = True
G_POSMODE_STATUS_CLOSED_AS = "EVIDENCE_EXHAUSTION_FAIL_CLOSED"

SEARCH_SPACE = (
    "src/, tests/, docs/, evidence/, scripts/, configs/, schemas/, "
    "contracts/, registries/, runbooks/, system_atlas/, fixtures/"
)

SEARCH_FAMILIES = (
    "posMode",
    "posSide",
    "net_mode",
    "account/config",
    "leverage-info",
    "build_venue_native_order_body",
    "trade/order",
    "canary",
    "flatten",
    "route_c",
    "position_mode_submit_body",
)

NEXT_AUTHORITY_BOUNDARY = (
    "SEPARATE_OWNER_GO_REQUIRED_BEFORE_ANY_VENUE_WIRE_OR_GET_OR_POST_"
    "OR_POSITION_CREATION_OR_FLATTEN_OR_LIVE_OR_CANARY"
)

MISSING_EVIDENCE_EDGE = "NO_REPOSITORY_FIRST_PARTY_OKX_SUBMIT_BODY_CONTRACT_FOR_NET_MODE_POSSIDE"
