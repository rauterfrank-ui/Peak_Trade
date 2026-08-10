"""§11.12.8 OKX EEA Demo XPerp ephemeral campaign private-write gate (NO permanent ORDER_POST)."""

from __future__ import annotations

from src.ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.constants_v1 import (
    ACCEPTED_OWNER_GO_SCOPES,
    CANONICAL_NEXT_STEP_AFTER_MERGE,
    CANONICAL_ORDER_SZ,
    CAPABILITY_ID,
    INSTRUMENT_SCOPE_EXACT,
    OWNER,
    PACKAGE_DEFAULT_ORDER_POST_AUTHORIZED,
    PACKAGE_MARKER,
    REST_BASE,
    SECTION_11_12_8_STATUS,
    SCOPED_OWNER_GO_SCOPE,
    VENUE,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.gate_v1 import (
    EphemeralCampaignPrivateWriteGateRecordV1,
    OkxEeaDemoXperpCampaignPrivateWriteGateError,
    assert_mutation_allowed_under_ephemeral_gate_v1,
    evaluate_ephemeral_campaign_private_write_gate_v1,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.verifier_v1 import (
    verify_okx_eea_demo_xperp_campaign_private_write_gate_v1,
)

__all__ = [
    "ACCEPTED_OWNER_GO_SCOPES",
    "CANONICAL_NEXT_STEP_AFTER_MERGE",
    "CANONICAL_ORDER_SZ",
    "CAPABILITY_ID",
    "EphemeralCampaignPrivateWriteGateRecordV1",
    "INSTRUMENT_SCOPE_EXACT",
    "OkxEeaDemoXperpCampaignPrivateWriteGateError",
    "OWNER",
    "PACKAGE_DEFAULT_ORDER_POST_AUTHORIZED",
    "PACKAGE_MARKER",
    "REST_BASE",
    "SCOPED_OWNER_GO_SCOPE",
    "SECTION_11_12_8_STATUS",
    "VENUE",
    "assert_mutation_allowed_under_ephemeral_gate_v1",
    "evaluate_ephemeral_campaign_private_write_gate_v1",
    "verify_okx_eea_demo_xperp_campaign_private_write_gate_v1",
]
