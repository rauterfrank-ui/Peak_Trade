"""Owner input contract for future §11.13.5 canary execute (non-authorizing)."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    OWNER_GO_AUTHORING,
    OWNER_GO_EXECUTE,
    POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1,
    POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1,
    POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_ENTITY,
    REUSED_BINDING_REGION,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
    REUSED_SECTION_11_13_3_BINDING_SOURCE,
    REUSED_SECTION_11_13_4_BINDING_SOURCE,
    SECRETREF_CONVENTION_EXAMPLE,
)


def build_owner_execute_input_contract_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "OWNER_EXECUTE_INPUT_CHECKLIST",
        "DOCUMENT_ROLE": "NON_SSOT",
        "NO_INVENTED_VALUES": True,
        "LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN": False,
        "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": False,
        "LIVE_AUTHORIZED": False,
        "LIVE_RECONCILIATION_PROVEN": True,
        "BLOCKS_NEW_ENTRY": False,
        "AUTHORING_GO": OWNER_GO_AUTHORING,
        "SEPARATE_EXECUTE_GO": OWNER_GO_EXECUTE,
        "OWNER_GO_EXECUTE_STATUS": "GRANTED_UNCONSUMED",
        "CANARY_SUBMIT_TRANSPORT_IMPLEMENTED": True,
        "SUBMIT_UNLOCKED": False,
        "REUSED_BINDING_SOURCES": {
            "section_11_13_3": REUSED_SECTION_11_13_3_BINDING_SOURCE,
            "section_11_13_4": REUSED_SECTION_11_13_4_BINDING_SOURCE,
        },
        "required_fields": [
            {
                "field": "venue/entity/region/host/account",
                "value_hint": (
                    f"{REUSED_BINDING_VENUE}/{REUSED_BINDING_ENTITY}/"
                    f"{REUSED_BINDING_REGION}/{REUSED_BINDING_REST_HOST}/"
                    f"{REUSED_BINDING_ACCOUNT_SCOPE}"
                ),
                "notes": "Reuse proven LIVE binding; do not invent.",
            },
            {
                "field": "instrument_id",
                "value_hint": DEFAULT_INSTRUMENT_ID,
                "notes": "Canonical canary instrument unless Owner rebinds.",
            },
            {
                "field": "instrument_min_sz/lot_sz/ct_val/tick_sz",
                "value_hint": "FROM_VENUE_PUBLIC_INSTRUMENTS_AT_EXECUTE",
                "notes": "Must be derived from venue metadata; not invented in authoring.",
            },
            {
                "field": "secretref_uri",
                "value_hint": SECRETREF_CONVENTION_EXAMPLE.replace("<venue>", "okx"),
                "notes": "Trade-capable key; never commit vault material.",
            },
            {
                "field": "credential_class",
                "value_hint": REQUIRED_CREDENTIAL_CLASS,
                "notes": "Distinct from dry-run RO class.",
            },
            {
                "field": "permission_attestation",
                "value_hint": REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT,
                "notes": "TRADE must be true; WITHDRAW must remain false.",
            },
            {
                "field": "exchange_truth_adoption_policies",
                "value_hint": [
                    POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1,
                    POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1,
                    POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1,
                ],
                "notes": "Required before LIVE_RECONCILIATION_PROVEN/BLOCKS_NEW_ENTRY can clear.",
            },
            {
                "field": "enabled/armed/confirm_token",
                "value_hint": "session gates + I_KNOW_WHAT_I_AM_DOING",
                "notes": "Checked at submit; standing package constants remain false.",
            },
        ],
        "hard_stops": [
            "Authoring GO cannot authorize submit",
            "Consumed execute GO cannot authorize submit",
            "BLOCKS_NEW_ENTRY=true blocks submit",
            "LIVE_RECONCILIATION_PROVEN=false blocks submit",
            "TRADE_ATTESTATION=false blocks submit",
            "Fixture/demo/testnet cannot satisfy productive LIVE binding",
            "No secret values in Git or logs",
            "Cap 11.9 remains fixture-only",
        ],
    }
