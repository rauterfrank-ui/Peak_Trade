"""Post-merge pre-Canary owner/security dependency forensic resolution.

Docs/evidence only. No productive network, no secret values, no Canary execute.
Does not clear BLOCKS_NEW_ENTRY or set LIVE_RECONCILIATION_PROVEN.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    BLOCKS_NEW_ENTRY,
    LIVE_RECONCILIATION_PROVEN,
    POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1,
    POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1,
    POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1,
    PRIOR_DRY_RUN_PERMISSION_ATTESTATION,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_ENTITY,
    REUSED_BINDING_REGION,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
    SECRETREF_CONVENTION_EXAMPLE,
    UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cybersecurity_canary_gate_v1 import (
    evaluate_live_canary_cybersecurity_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.forensic_reconciliation_v1 import (
    prove_forensic_classification_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.trade_permission_forensic_v1 import (
    build_trade_permission_forensic_v1,
)


def resolve_trade_attestation_dependency_v1(
    *,
    owner_trade_key_attestation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail-closed TRADE_ATTESTATION resolution from sealed evidence only.

    Without an explicit Owner attestation payload proving a separate trade-capable,
    withdrawal-disabled LIVE Canary key bound to the SecretRef contract, attestation
    remains false. This function never reads secret values or mutates API keys.
    """
    sealed = build_trade_permission_forensic_v1()
    owner = dict(owner_trade_key_attestation or {})
    required = dict(REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT)
    secretref_uri = str(owner.get("secretref_uri") or "").strip()
    secretref_ok = (
        "live-canary-minimum-exposure" in secretref_uri
        and secretref_uri.startswith("secretref://")
        and "://" in secretref_uri
        and not any(
            marker in secretref_uri.lower()
            for marker in ("apikey", "secret", "passphrase", "token=")
        )
    )
    owner_perm = {
        "READ": owner.get("READ"),
        "TRADE": owner.get("TRADE"),
        "WITHDRAW": owner.get("WITHDRAW"),
    }
    owner_complete = (
        owner_perm["READ"] is True
        and owner_perm["TRADE"] is True
        and owner_perm["WITHDRAW"] is False
        and str(owner.get("credential_class") or "") == REQUIRED_CREDENTIAL_CLASS
        and secretref_ok
        and str(owner.get("venue") or "") == REUSED_BINDING_VENUE
        and str(owner.get("rest_host") or "") == REUSED_BINDING_REST_HOST
        and str(owner.get("account_scope") or "") == REUSED_BINDING_ACCOUNT_SCOPE
        and str(owner.get("region") or "") == REUSED_BINDING_REGION
    )
    # No Owner attestation supplied under this GO → ambiguous → fail closed.
    trade_attestation = bool(owner_complete)
    blockers: list[str] = []
    if not owner:
        blockers.append("OWNER_TRADE_KEY_ATTESTATION_ABSENT")
    if sealed["PRIOR_PERMISSION_ATTESTATION"].get("TRADE") is False:
        blockers.append("SEALED_PRIOR_DRY_RUN_KEY_TRADE_FALSE_NOT_REUSABLE")
    if owner and not owner_complete:
        blockers.append("OWNER_TRADE_KEY_ATTESTATION_AMBIGUOUS_OR_INCOMPLETE")
    if owner_perm.get("WITHDRAW") is True:
        blockers.append("WITHDRAW_ENABLED_FORBIDDEN")
    if owner and not secretref_ok:
        blockers.append("SECRETREF_CONTRACT_AMBIGUOUS_OR_INVALID")

    return {
        "DOCUMENT_CLASS": "SECTION_11_13_5_B_TRADE_ATTESTATION_RESOLUTION_V1",
        "TRADE_ATTESTATION": trade_attestation,
        "WITHDRAW_ATTESTATION": bool(owner_perm.get("WITHDRAW") is True)
        or bool(PRIOR_DRY_RUN_PERMISSION_ATTESTATION.get("WITHDRAW")),
        "READ_ATTESTATION_SEALED_PRIOR": True,
        "REQUIRED_API_KEY_CAPABILITY": required,
        "REQUIRED_CREDENTIAL_CLASS": REQUIRED_CREDENTIAL_CLASS,
        "INTENDED_KEY_TRADE_CAPABLE_VERIFIED": trade_attestation,
        "INTENDED_KEY_WITHDRAWAL_DISABLED_VERIFIED": trade_attestation,
        "ACCOUNT_VENUE_REGION_HOST_BINDINGS": {
            "venue": REUSED_BINDING_VENUE,
            "entity": REUSED_BINDING_ENTITY,
            "region": REUSED_BINDING_REGION,
            "rest_host": REUSED_BINDING_REST_HOST,
            "account_scope": REUSED_BINDING_ACCOUNT_SCOPE,
            "binding_status": "SEALED_FROM_PRIOR_PROOF_REUSED_FOR_CANARY_SCOPE",
        },
        "SECRETREF_CONTRACT": {
            "convention_example": SECRETREF_CONVENTION_EXAMPLE.replace("<venue>", "okx"),
            "path_marker_required": "/live-canary-minimum-exposure/",
            "secret_values_persisted": False,
            "secret_value_access": "NONE",
            "owner_attested_uri_present": bool(secretref_uri),
            "owner_attested_uri_contract_ok": secretref_ok,
        },
        "SEALED_PRIOR_PERMISSION_FORENSIC": sealed,
        "FAIL_CLOSED_IF_AMBIGUOUS": True,
        "BLOCKERS": blockers,
        "RESOLUTION_STATUS": "RESOLVED_FALSE_FAIL_CLOSED"
        if not trade_attestation
        else "RESOLVED_TRUE",
        "NETWORK_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "ACCOUNT_MUTATION_EFFECT": "NONE",
        "SECRET_VALUE_ACCESS": "NONE",
        "ok": True,
    }


def resolve_exchange_truth_adoption_dependency_v1(
    *,
    repo_root: str | Any,
    owner_adoption_decisions: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Encode required Owner adoption policies; do not auto-clear economic gates."""
    forensic = prove_forensic_classification_contract_v1(repo_root=repo_root)
    decisions = dict(owner_adoption_decisions or {})
    required = list(forensic.get("OWNER_ADOPTION_POLICIES_REQUIRED") or [])
    adopted = {
        POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1: bool(
            decisions.get(POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1) is True
        ),
        POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1: bool(
            decisions.get(POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1) is True
        ),
        POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1: bool(
            decisions.get(POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1) is True
        ),
    }
    all_adopted = all(adopted[p] for p in required) if required else False
    # This GO does not authorize adoption. Preserve economic block.
    blocks_new_entry = True if not all_adopted else BLOCKS_NEW_ENTRY
    live_recon_proven = False if not all_adopted else LIVE_RECONCILIATION_PROVEN
    return {
        "DOCUMENT_CLASS": "SECTION_11_13_5_B_EXCHANGE_TRUTH_ADOPTION_RESOLUTION_V1",
        "EXCHANGE_TRUTH_ADOPTION_STATUS": (
            "OWNER_POLICIES_REQUIRED_NOT_ADOPTED" if not all_adopted else "OWNER_POLICIES_ADOPTED"
        ),
        "FORENSIC_CLASSIFICATION_SUMMARY": {
            "PRIMARY_CLASSIFICATION_CODES": forensic.get("PRIMARY_CLASSIFICATION_CODES"),
            "ANY_LAYER_CLASSIFIED_AS_REAL_ECONOMIC_DIVERGENCE_D": forensic.get(
                "ANY_LAYER_CLASSIFIED_AS_REAL_ECONOMIC_DIVERGENCE_D"
            ),
            "layers": forensic.get("layers"),
        },
        "OWNER_ADOPTION_POLICIES_REQUIRED": required,
        "OWNER_ADOPTION_POLICY_DECISIONS_ENCODED": {
            POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1: {
                "required": True,
                "adopted": adopted[POLICY_ADOPT_EXCHANGE_VENUE_METADATA_BASELINE_V1],
                "effect_if_adopted": (
                    "Accept sealed exchange venue/instrument metadata digest as "
                    "LIVE canary baseline for BTC-USDT-SWAP; does not alone clear "
                    "BLOCKS_NEW_ENTRY."
                ),
            },
            POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1: {
                "required": True,
                "adopted": adopted[POLICY_ADOPT_EXCHANGE_BALANCE_BASELINE_V1],
                "effect_if_adopted": (
                    "Seed local LIVE balance/equity baseline from sealed exchange "
                    "observation (local was flat_or_empty). Required to progress "
                    "LIVE_RECONCILIATION_PROVEN evaluation."
                ),
            },
            POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1: {
                "required": True,
                "adopted": adopted[POLICY_ADOPT_EXCHANGE_LOCAL_PORTFOLIO_BASELINE_V1],
                "effect_if_adopted": (
                    "Align local portfolio/accounting baseline to exchange-observed "
                    "portfolio digest (including alias note E). Required with balance "
                    "policy before clearing unresolved divergence block."
                ),
            },
        },
        "OWNER_ADOPTION_AUTHORIZED_BY_THIS_GO": False,
        "LIVE_RECONCILIATION_PROVEN": live_recon_proven,
        "BLOCKS_NEW_ENTRY": blocks_new_entry,
        "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": (
            UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY if not all_adopted else False
        ),
        "AUTOMATIC_BLOCKS_NEW_ENTRY_CLEAR_FORBIDDEN": True,
        "NETWORK_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "ACCOUNT_MUTATION_EFFECT": "NONE",
        "SECRET_VALUE_ACCESS": "NONE",
        "ok": True,
    }


def evaluate_pre_canary_readiness_terminal_v1(
    *,
    repo_root: str | Any,
    merge_commit_sha: str,
    owner_trade_key_attestation: Mapping[str, Any] | None = None,
    owner_adoption_decisions: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    trade = resolve_trade_attestation_dependency_v1(
        owner_trade_key_attestation=owner_trade_key_attestation
    )
    exchange = resolve_exchange_truth_adoption_dependency_v1(
        repo_root=repo_root,
        owner_adoption_decisions=owner_adoption_decisions,
    )
    gate = evaluate_live_canary_cybersecurity_gate_v1(
        productive_surface_merged_to_origin_main=True,
        trade_attestation=bool(trade["TRADE_ATTESTATION"]),
        withdraw_attestation=bool(trade["WITHDRAW_ATTESTATION"]),
        read_attestation=True,
    )
    ready = (
        trade["TRADE_ATTESTATION"] is True
        and exchange["EXCHANGE_TRUTH_ADOPTION_STATUS"] == "OWNER_POLICIES_ADOPTED"
        and gate["LIVE_CANARY_CYBERSECURITY_GATE"] == "PASS"
        and exchange["LIVE_RECONCILIATION_PROVEN"] is True
        and exchange["BLOCKS_NEW_ENTRY"] is False
    )
    terminal = (
        "PRE_CANARY_READY_AWAITING_NEW_OWNER_GO" if ready else "FAIL_CLOSED_PRE_CANARY_BLOCKED"
    )
    earliest = (
        "NEW_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
        if ready
        else (
            "OWNER_TRADE_ATTESTATION_FOR_LIVE_CANARY"
            if not trade["TRADE_ATTESTATION"]
            else "OWNER_EXCHANGE_TRUTH_ADOPTION_POLICIES_FOR_LIVE_CANARY_GATES"
        )
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_13_5_B_PRE_CANARY_READINESS_TERMINAL_V1",
        "MERGE_COMMIT_SHA": merge_commit_sha,
        "PRODUCTIVE_CANARY_SURFACE_MERGED_TO_ORIGIN_MAIN": True,
        "TRADE_ATTESTATION_RESOLUTION": trade,
        "EXCHANGE_TRUTH_ADOPTION_RESOLUTION": exchange,
        "LIVE_CANARY_CYBERSECURITY_GATE_EVAL": gate,
        "TERMINAL_STATE": terminal,
        "TRADE_ATTESTATION": trade["TRADE_ATTESTATION"],
        "WITHDRAW_ATTESTATION": trade["WITHDRAW_ATTESTATION"],
        "EXCHANGE_TRUTH_ADOPTION_STATUS": exchange["EXCHANGE_TRUTH_ADOPTION_STATUS"],
        "LIVE_CANARY_CYBERSECURITY_GATE": gate["LIVE_CANARY_CYBERSECURITY_GATE"],
        "LIVE_RECONCILIATION_PROVEN": exchange["LIVE_RECONCILIATION_PROVEN"],
        "BLOCKS_NEW_ENTRY": exchange["BLOCKS_NEW_ENTRY"],
        "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED": False,
        "LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN": False,
        "LIVE_AUTHORIZED": False,
        "PRIOR_CANARY_OWNER_GO_REUSED": False,
        "NEW_CANARY_OWNER_GO_GRANTED": False,
        "NETWORK_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "ACCOUNT_MUTATION_EFFECT": "NONE",
        "SECRET_VALUE_ACCESS": "NONE",
        "EARLIEST_UNRESOLVED_DEPENDENCY": earliest,
        "CANONICAL_NEXT_STEP": (
            "NEW_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
            if ready
            else "OWNER_ACTIONS_RESOLVE_TRADE_ATTESTATION_AND_EXCHANGE_TRUTH_ADOPTION_THEN_NEW_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
        ),
        "HARD_STOP_REASONS": list(gate.get("BLOCKERS") or []) + list(trade.get("BLOCKERS") or []),
        "ok": True,
    }
