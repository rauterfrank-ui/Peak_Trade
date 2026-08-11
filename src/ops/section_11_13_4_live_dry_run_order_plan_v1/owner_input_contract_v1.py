"""Owner execute-time input contract for §11.13.4 LIVE_DRY_RUN_ORDER_PLAN."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (
    OWNER_GO_EXECUTE,
    REUSED_SECTION_11_13_3_BINDING_ACCOUNT_SCOPE,
    REUSED_SECTION_11_13_3_BINDING_ENTITY,
    REUSED_SECTION_11_13_3_BINDING_REGION,
    REUSED_SECTION_11_13_3_BINDING_REST_HOST,
    REUSED_SECTION_11_13_3_BINDING_SOURCE,
    REUSED_SECTION_11_13_3_BINDING_VENUE,
    REUSED_SECTION_11_13_3_DRY_RUN_SECRETREF_URI,
    SECRETREF_CONVENTION_EXAMPLE,
)


REQUIRED_OWNER_INPUT_IDS: tuple[str, ...] = (
    "live_venue_entity",
    "region",
    "canonical_production_rest_host",
    "account_or_subaccount_binding",
    "instrument_id",
    "live_ro_secretref_uri",
    "vault_material_local_never_git",
    "permission_attestation_read",
    "permission_attestation_trade",
    "permission_attestation_withdraw",
    "confirm_no_demo_simulation_marker",
    "separate_execute_go",
)


def build_owner_execute_input_contract_v1() -> dict[str, Any]:
    return {
        "document_class": "OWNER_EXECUTE_INPUT_CHECKLIST",
        "document_role": "NON_SSOT",
        "no_invented_values": True,
        "LIVE_AUTHORIZED": False,
        "LIVE_RECONCILIATION_PROVEN": False,
        "BLOCKS_NEW_ENTRY": True,
        "SEPARATE_EXECUTE_GO": OWNER_GO_EXECUTE,
        "REUSED_FROM_SECTION_11_13_3_PROVEN_BINDING": True,
        "REUSED_BINDING_SOURCE": REUSED_SECTION_11_13_3_BINDING_SOURCE,
        "secretref_convention_example": SECRETREF_CONVENTION_EXAMPLE,
        "fields": [
            {
                "id": "live_venue_entity",
                "required": True,
                "value": f"{REUSED_SECTION_11_13_3_BINDING_VENUE} / {REUSED_SECTION_11_13_3_BINDING_ENTITY}",
                "notes": "Reuse §11.13.3 proven binding",
            },
            {
                "id": "region",
                "required": True,
                "value": REUSED_SECTION_11_13_3_BINDING_REGION,
                "notes": "Reuse §11.13.3 proven binding",
            },
            {
                "id": "canonical_production_rest_host",
                "required": True,
                "value": REUSED_SECTION_11_13_3_BINDING_REST_HOST,
                "notes": "Reuse §11.13.3 proven binding",
            },
            {
                "id": "account_or_subaccount_binding",
                "required": True,
                "value": REUSED_SECTION_11_13_3_BINDING_ACCOUNT_SCOPE,
                "notes": "Reuse §11.13.3 proven binding",
            },
            {
                "id": "instrument_id",
                "required": True,
                "value": "BTC-USDT-SWAP",
                "notes": "Canonical dry-run instrument for plan construction",
            },
            {
                "id": "live_ro_secretref_uri",
                "required": True,
                "value": REUSED_SECTION_11_13_3_DRY_RUN_SECRETREF_URI,
                "notes": f"Dry-run schema ({SECRETREF_CONVENTION_EXAMPLE}); local vault key only.",
            },
            {
                "id": "vault_material_local_never_git",
                "required": True,
                "value": "LOCAL_ONLY",
                "notes": "Never commit vault material",
            },
            {
                "id": "permission_attestation_read",
                "required": True,
                "value": True,
                "notes": "Must be true",
            },
            {
                "id": "permission_attestation_trade",
                "required": True,
                "value": False,
                "notes": "Must remain false",
            },
            {
                "id": "permission_attestation_withdraw",
                "required": True,
                "value": False,
                "notes": "Must remain false",
            },
            {
                "id": "confirm_no_demo_simulation_marker",
                "required": True,
                "value": True,
                "notes": "Reuse §11.13.3 proven binding",
            },
            {
                "id": "separate_execute_go",
                "required": True,
                "value": OWNER_GO_EXECUTE,
                "notes": "One-shot; consumed by productive dry-run execute",
            },
        ],
        "hard_stops": [
            "No Live order submit / ACK / FILL / CANCEL",
            "No account / position / funds mutation",
            "No LIVE_AUTHORIZED=true",
            "No clearing of BLOCKS_NEW_ENTRY while divergence unresolved",
            "No LIVE_RECONCILIATION_PROVEN=true claim from this package",
            "Cap 11.8 remains fixture-only",
        ],
    }
