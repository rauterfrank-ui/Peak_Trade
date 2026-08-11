"""Owner execute-time input contract / checklist for §11.13.2 (no invented values)."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_2_live_private_read_only_v1.constants_v1 import (
    OWNER_GO_EXECUTE_TOKEN,
    REQUIRED_CREDENTIAL_CLASS,
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
    """Machine- and human-readable checklist. Values intentionally unset."""
    return {
        "contract_id": "SECTION_11_13_2_OWNER_EXECUTE_INPUT_CONTRACT_V1",
        "purpose": "Inputs the Owner must supply before OWNER_GO_LIVE_PRIVATE_READ_ONLY execute",
        "preparation_pr_does_not_execute": True,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
        "LIVE_AUTHORIZED": False,
        "required_credential_class": REQUIRED_CREDENTIAL_CLASS,
        "secretref_convention_example": SECRETREF_CONVENTION_EXAMPLE,
        "separate_execute_go_token": OWNER_GO_EXECUTE_TOKEN,
        "fields": [
            {
                "id": "live_venue_entity",
                "required": True,
                "value": None,
                "notes": "Owner-supplied live venue/entity. Do not invent.",
            },
            {
                "id": "region",
                "required": True,
                "value": None,
                "notes": "Owner-supplied region for the live account binding.",
            },
            {
                "id": "canonical_production_rest_host",
                "required": True,
                "value": None,
                "notes": "Exact production REST host. Not hard-coded in preparation PR.",
            },
            {
                "id": "account_or_subaccount_binding",
                "required": True,
                "value": None,
                "notes": "Account/subaccount identity binding for LIVE private RO.",
            },
            {
                "id": "optional_instrument_scope",
                "required": False,
                "value": None,
                "notes": "Optional instrument scope; omit if account-level RO only.",
            },
            {
                "id": "live_ro_secretref_uri",
                "required": True,
                "value": None,
                "notes": f"SecretRef URI following {SECRETREF_CONVENTION_EXAMPLE}",
            },
            {
                "id": "vault_material_local_never_git",
                "required": True,
                "value": None,
                "notes": "Vault material must remain local. Never commit secrets.",
            },
            {
                "id": "permission_attestation",
                "required": True,
                "value": {"READ": True, "TRADE": False, "WITHDRAW": False},
                "notes": "Owner attestation of API key permissions.",
            },
            {
                "id": "ip_allowlist_status_or_expected_source_ip",
                "required": True,
                "value": None,
                "notes": "Venue-relevant IP allowlist status / expected source IP.",
            },
            {
                "id": "confirm_no_demo_simulation_marker",
                "required": True,
                "value": None,
                "notes": "Confirm no demo/simulation header or credential class is used.",
            },
            {
                "id": "separate_execute_go",
                "required": True,
                "value": OWNER_GO_EXECUTE_TOKEN,
                "notes": "Later separate Owner-GO; not authorized by preparation PR.",
            },
        ],
        "hard_stops": [
            "NO_PRODUCTIVE_LIVE_REQUEST_IN_PREPARATION",
            "NO_CREDENTIAL_VAULT_MATERIAL_IN_GIT",
            "NO_ORDERS",
            "NO_SHADOW",
            "NO_CANARY",
            "NO_ACTIVATION",
            "LIVE_AUTHORIZED_REMAINS_FALSE",
        ],
    }
