"""Owner execute-time input contract / checklist for §11.13.3.

Values below are Owner-authorized reuse of the already PROVEN §11.13.2 binding
(not invented). Unlock authoring does not execute or borrow vault material.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.constants_v1 import (
    OWNER_GO_EXECUTE,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_PERMISSION_ATTESTATION,
    REUSED_SECTION_11_13_2_BINDING_ACCOUNT_SCOPE,
    REUSED_SECTION_11_13_2_BINDING_ENTITY,
    REUSED_SECTION_11_13_2_BINDING_REGION,
    REUSED_SECTION_11_13_2_BINDING_REST_HOST,
    REUSED_SECTION_11_13_2_BINDING_SOURCE,
    REUSED_SECTION_11_13_2_BINDING_VENUE,
    REUSED_SECTION_11_13_2_SHADOW_SECRETREF_URI,
    SECRETREF_CONVENTION_EXAMPLE,
)


OWNER_EXECUTE_INPUT_FIELDS_V1: tuple[str, ...] = (
    "live_venue_entity",
    "region",
    "canonical_production_rest_host",
    "account_or_subaccount_binding",
    "optional_instrument_scope",
    "live_ro_secretref_uri",
    "vault_material_local_never_git",
    "permission_attestation_READ_true",
    "permission_attestation_TRADE_false",
    "permission_attestation_WITHDRAW_false",
    "ip_allowlist_status_or_expected_source_ip",
    "confirm_no_demo_simulation_marker",
    "separate_execute_go",
)


def build_owner_execute_input_contract_v1() -> dict[str, Any]:
    """Machine- and human-readable checklist with reused proven binding metadata."""
    return {
        "contract_id": "SECTION_11_13_3_OWNER_EXECUTE_INPUT_CONTRACT_V1",
        "purpose": "Inputs confirmed before OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION execute",
        "preparation_pr_does_not_execute": True,
        "unlock_authoring_does_not_execute": True,
        "LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN": False,
        "LIVE_AUTHORIZED": False,
        "REUSED_FROM_SECTION_11_13_2_PROVEN_BINDING": True,
        "REUSED_BINDING_SOURCE": REUSED_SECTION_11_13_2_BINDING_SOURCE,
        "required_credential_class": REQUIRED_CREDENTIAL_CLASS,
        "secretref_convention_example": SECRETREF_CONVENTION_EXAMPLE,
        "separate_execute_go": OWNER_GO_EXECUTE,
        "fields": [
            {
                "id": "live_venue_entity",
                "required": True,
                "value": f"{REUSED_SECTION_11_13_2_BINDING_VENUE} / {REUSED_SECTION_11_13_2_BINDING_ENTITY}",
                "notes": "Reused from §11.13.2 proven binding. Do not invent.",
            },
            {
                "id": "region",
                "required": True,
                "value": REUSED_SECTION_11_13_2_BINDING_REGION,
                "notes": "Reused from §11.13.2 proven binding.",
            },
            {
                "id": "canonical_production_rest_host",
                "required": True,
                "value": REUSED_SECTION_11_13_2_BINDING_REST_HOST,
                "notes": "Reused from §11.13.2 proven binding.",
            },
            {
                "id": "account_or_subaccount_binding",
                "required": True,
                "value": REUSED_SECTION_11_13_2_BINDING_ACCOUNT_SCOPE,
                "notes": "Reused from §11.13.2 proven binding.",
            },
            {
                "id": "optional_instrument_scope",
                "required": False,
                "value": None,
                "notes": "Account-level RO only for this stage.",
            },
            {
                "id": "live_ro_secretref_uri",
                "required": True,
                "value": REUSED_SECTION_11_13_2_SHADOW_SECRETREF_URI,
                "notes": f"Shadow schema ({SECRETREF_CONVENTION_EXAMPLE}); local vault key only.",
            },
            {
                "id": "vault_material_local_never_git",
                "required": True,
                "value": "local_only_never_git",
                "notes": "Vault material must remain local. Never commit secrets. Authoring does not borrow.",
            },
            {
                "id": "permission_attestation",
                "required": True,
                "value": dict(REQUIRED_PERMISSION_ATTESTATION),
                "notes": "Reused from §11.13.2 proven attestation.",
            },
            {
                "id": "ip_allowlist_status_or_expected_source_ip",
                "required": True,
                "value": "REUSED_FROM_SECTION_11_13_2_LOCAL_OWNER_BINDINGS_METADATA",
                "notes": "Reuse §11.13.2 local owner_bindings IP metadata; no secret values.",
            },
            {
                "id": "confirm_no_demo_simulation_marker",
                "required": True,
                "value": True,
                "notes": "Reused from §11.13.2 proven binding.",
            },
            {
                "id": "separate_execute_go",
                "required": True,
                "value": OWNER_GO_EXECUTE,
                "notes": "Later separate Owner-GO; not authorized by unlock authoring.",
            },
        ],
        "hard_stops": [
            "NO_PRODUCTIVE_LIVE_REQUEST_IN_UNLOCK_AUTHORING",
            "NO_CREDENTIAL_VAULT_MATERIAL_IN_GIT",
            "NO_ORDERS",
            "NO_CANARY",
            "NO_ACTIVATION",
            "LIVE_AUTHORIZED_REMAINS_FALSE",
            "NO_AUTOMATIC_LOCAL_RECONCILIATION_CORRECTION",
        ],
    }
