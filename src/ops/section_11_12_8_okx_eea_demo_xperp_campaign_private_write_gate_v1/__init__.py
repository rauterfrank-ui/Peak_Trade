"""§11.12.8 OKX EEA Demo XPerp ephemeral campaign private-write gate (NO permanent ORDER_POST)."""

from __future__ import annotations

from src.ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.constants_v1 import (
    ACCEPTED_OWNER_GO_SCOPES,
    ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH,
    BTC_USDT_SWAP_PATH_STATUS,
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
    SWAP_RUNTIME_FALLBACK,
    SWAP_WRITE_AUTHORIZATION,
    VENUE,
    XPERP_ONLY_ACTIVE_WRITE_SCOPE,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.gate_v1 import (
    EphemeralCampaignPrivateWriteGateRecordV1,
    OkxEeaDemoXperpCampaignPrivateWriteGateError,
    assert_deprecated_btc_usdt_swap_path_forbidden_v1,
    assert_mutation_allowed_under_ephemeral_gate_v1,
    evaluate_ephemeral_campaign_private_write_gate_v1,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.verifier_v1 import (
    verify_okx_eea_demo_xperp_campaign_private_write_gate_v1,
)

__all__ = [
    "ACCEPTED_OWNER_GO_SCOPES",
    "ACTIVE_SECTION_11_12_8_DERIVATIVES_CAMPAIGN_PATH",
    "BTC_USDT_SWAP_PATH_STATUS",
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
    "SWAP_RUNTIME_FALLBACK",
    "SWAP_WRITE_AUTHORIZATION",
    "VENUE",
    "XPERP_ONLY_ACTIVE_WRITE_SCOPE",
    "assert_deprecated_btc_usdt_swap_path_forbidden_v1",
    "assert_mutation_allowed_under_ephemeral_gate_v1",
    "evaluate_ephemeral_campaign_private_write_gate_v1",
    "verify_okx_eea_demo_xperp_campaign_private_write_gate_v1",
]
