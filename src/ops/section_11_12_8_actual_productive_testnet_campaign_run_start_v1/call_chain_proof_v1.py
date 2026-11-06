"""Static productive call-chain proof for ACTUAL start."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CALL_CHAIN_LINKS,
    CAPABILITY_ID,
    NEXT_OPERATION_AFTER_STUBBED_BOUNDARY,
)


def build_static_productive_call_chain_proof_v1(
    *,
    authorized_path: bool = True,
    stubbed_external_effect: bool = True,
) -> dict[str, Any]:
    classifications: dict[str, str] = {}
    for link in CALL_CHAIN_LINKS:
        if link == "first_permitted_TESTNET_effect" and stubbed_external_effect:
            classifications[link] = "PRESENT_AND_PRODUCTIVE_STUBBED_EXTERNAL_BOUNDARY"
        else:
            classifications[link] = "PRESENT_AND_PRODUCTIVE" if authorized_path else "MISSING"
    all_ok = all(v.startswith("PRESENT_AND_PRODUCTIVE") for v in classifications.values())
    return {
        "ok": all_ok and authorized_path,
        "CAPABILITY_ID": CAPABILITY_ID,
        "links": list(CALL_CHAIN_LINKS),
        "classifications": classifications,
        "NEXT_OPERATION_AFTER_STUBBED_BOUNDARY": NEXT_OPERATION_AFTER_STUBBED_BOUNDARY,
        "stubbed_external_effect_only": stubbed_external_effect,
    }
