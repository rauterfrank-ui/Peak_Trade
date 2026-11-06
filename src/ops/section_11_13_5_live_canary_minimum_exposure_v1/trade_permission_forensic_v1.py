"""Trade-permission forensic (no secret values; no automatic key mutation)."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    PRIOR_DRY_RUN_PERMISSION_ATTESTATION,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_ENTITY,
    REUSED_BINDING_REGION,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
    REUSED_SECTION_11_13_4_BINDING_SOURCE,
    SECRETREF_CONVENTION_EXAMPLE,
)


def build_trade_permission_forensic_v1(
    *,
    prior_attestation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    prior = dict(prior_attestation or PRIOR_DRY_RUN_PERMISSION_ATTESTATION)
    trade = prior.get("TRADE")
    # Prior dry-run required TRADE=false for RO key class — actually not permitted.
    actually_not_permitted = trade is False
    not_yet_attested = trade is None
    return {
        "DOCUMENT_CLASS": "SECTION_11_13_5_TRADE_PERMISSION_FORENSIC_V1",
        "PRIOR_BINDING_SOURCE": REUSED_SECTION_11_13_4_BINDING_SOURCE,
        "VENUE": REUSED_BINDING_VENUE,
        "ENTITY": REUSED_BINDING_ENTITY,
        "REGION": REUSED_BINDING_REGION,
        "REST_HOST": REUSED_BINDING_REST_HOST,
        "ACCOUNT_SCOPE": REUSED_BINDING_ACCOUNT_SCOPE,
        "PRIOR_PERMISSION_ATTESTATION": {
            "READ": prior.get("READ"),
            "TRADE": prior.get("TRADE"),
            "WITHDRAW": prior.get("WITHDRAW"),
        },
        "REQUIRED_FOR_CANARY_SUBMIT": dict(REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT),
        "DISTINCTION": (
            "ACTUALLY_NOT_PERMITTED"
            if actually_not_permitted
            else ("NOT_YET_ATTESTED" if not_yet_attested else "UNEXPECTED_PRIOR_STATE")
        ),
        "TRADE_ATTESTATION": False,
        "TRADE_ATTESTATION_BLOCKER": (
            "PRIOR_LIVE_DRY_RUN_KEY_CLASS_ATTESTED_TRADE_FALSE;"
            "CANARY_REQUIRES_SEPARATE_TRADE_CAPABLE_API_KEY_AND_ATTESTATION"
        ),
        "AUTOMATIC_API_KEY_PERMISSION_CHANGE": False,
        "SECRET_VALUE_ACCESS": "NONE",
        "OWNER_UI_ACTION_REQUIRED": True,
        "OWNER_UI_ACTION": (
            "On OKX EEA (eea.okx.com) API Management for account "
            f"{REUSED_BINDING_ACCOUNT_SCOPE}: create or select a LIVE production API key "
            "with Trade=enabled and Withdraw=disabled (Read remains enabled). Do not reuse "
            "the dry-run/read-only SecretRef. Store material only in local vault under "
            f"{SECRETREF_CONVENTION_EXAMPLE.replace('<venue>', 'okx')}. "
            f"Credential class must be {REQUIRED_CREDENTIAL_CLASS}."
        ),
        "EVIDENCE_REQUIRED_AFTERWARDS": (
            "1) Owner attestation flags READ=true TRADE=true WITHDRAW=false; "
            "2) GET-only permission/config proof under a future canary execute GO "
            "(not this authoring GO); "
            "3) SecretRef URI with /live-canary-minimum-exposure/ path marker; "
            "4) redacted authorization_binding.json without secret values."
        ),
        "ok": True,
    }
