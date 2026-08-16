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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.incident_classification_v1 import (
    HISTORICAL_FIRST_401_ROOT_CAUSE,
    HTTP_401_REQUEST_CLASS_ONESHOT_TRADING_POST,
    HTTP_401_WITH_PARSEABLE_ALLOWLISTED_OKX_CODE_MSG,
    HTTP_401_WITHOUT_PROVEN_OKX_BODY,
    OKX_50124_OBSERVED_ONESHOT_TRADING_POST,
    UNPROVEN_FAIL_CLOSED,
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
        "OWNER_GO_EXECUTE_STATUS": "CONSUMED",
        "RETRY_SAFE_NOW": False,
        "POST_401_ROOT_CAUSE": UNPROVEN_FAIL_CLOSED,
        "HISTORICAL_FIRST_401_ROOT_CAUSE": HISTORICAL_FIRST_401_ROOT_CAUSE,
        "LATEST_50124_CLASSIFICATION": OKX_50124_OBSERVED_ONESHOT_TRADING_POST,
        "HTTP_401_REQUEST_CLASS": HTTP_401_REQUEST_CLASS_ONESHOT_TRADING_POST,
        "HTTP_50124_INSTRUMENT_SPECIFIC_PROVEN": False,
        "ROOT_CAUSE_PROVEN": False,
        "HTTP_401_WITHOUT_PROVEN_OKX_BODY": HTTP_401_WITHOUT_PROVEN_OKX_BODY,
        "HTTP_401_WITH_PARSEABLE_ALLOWLISTED_OKX_CODE_MSG": (
            HTTP_401_WITH_PARSEABLE_ALLOWLISTED_OKX_CODE_MSG
        ),
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
                "notes": (
                    "Canonical live EEA X-Perp BTC-USD_UM_XPERP-310404 / FUTURES. "
                    "BTC-USDT-SWAP and Demo BTC-USD_UM_XPERP-310328 are rejected."
                ),
            },
            {
                "field": "inst_type",
                "value_hint": "FUTURES",
                "notes": "Must be FUTURES. SWAP is fail-closed for this canary path.",
            },
            {
                "field": "instrument_min_sz/lot_sz/ct_val/tick_sz",
                "value_hint": "FROM_VENUE_PUBLIC_INSTRUMENTS_AT_EXECUTE",
                "notes": "Must be derived from venue metadata at execute; XPERP minSz/lotSz=1.",
            },
            {
                "field": "secretref_uri",
                "value_hint": SECRETREF_CONVENTION_EXAMPLE.replace("<venue>", "okx"),
                "notes": "Trade-capable key; never commit vault material.",
            },
            {
                "field": "vault_file",
                "value_hint": "--vault-file path to local SecretRef JSON map (execute only)",
                "notes": "Same §11.13.2/3/4 CLI pattern. Values may be JSON strings or nested objects; no secrets in git/argv/logs.",
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
            "--vault-file required for execute; absence fails closed",
        ],
    }
