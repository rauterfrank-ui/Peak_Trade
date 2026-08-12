"""Live-Canary cybersecurity gate evaluation (fresh; not historical carry-forward).

Authoring/audit only. Historical PRE_LIVE_CYBERSECURITY_GATE=PASS does not
satisfy LIVE_CANARY_CYBERSECURITY_GATE when canary surface prerequisites differ.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    BLOCKS_NEW_ENTRY,
    CAPABILITY_11_9_LIVE_CANARY_ACTIVATED,
    CAPABILITY_11_9_REMAINS_FIXTURE_ONLY,
    LIVE_AUTHORIZED,
    LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED,
    LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN,
    LIVE_RECONCILIATION_PROVEN,
    PRIOR_DRY_RUN_PERMISSION_ATTESTATION,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
    UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.governance_state_matrix_v1 import (
    PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_BINDING,
    PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_STATUS,
)


def evaluate_live_canary_cybersecurity_gate_v1(
    *,
    pre_live_cybersecurity_gate: str = "PASS",
    productive_surface_merged_to_origin_main: bool,
    trade_attestation: bool,
    withdraw_attestation: bool,
    read_attestation: bool,
    secret_plaintext_in_repo_or_evidence: bool = False,
    fixture_authority_claimed_as_live: bool = False,
    permission_attestation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    perm = dict(permission_attestation or PRIOR_DRY_RUN_PERMISSION_ATTESTATION)
    blockers: list[str] = []

    if pre_live_cybersecurity_gate != "PASS":
        blockers.append("PRE_LIVE_CYBERSECURITY_GATE_NOT_PASS")
    if not productive_surface_merged_to_origin_main:
        blockers.append("PRODUCTIVE_CANARY_SURFACE_NOT_ON_ORIGIN_MAIN")
    if not read_attestation or perm.get("READ") is not True:
        blockers.append("READ_ATTESTATION_FALSE")
    if not trade_attestation or perm.get("TRADE") is not True:
        blockers.append("TRADE_ATTESTATION_FALSE")
    if withdraw_attestation or perm.get("WITHDRAW") is True:
        blockers.append("WITHDRAW_MUST_REMAIN_FALSE")
    if secret_plaintext_in_repo_or_evidence:
        blockers.append("SECRET_PLAINTEXT_DETECTED")
    if fixture_authority_claimed_as_live or CAPABILITY_11_9_LIVE_CANARY_ACTIVATED:
        blockers.append("FIXTURE_OR_CAP11_9_ACTIVATION_CLAIM")
    if not CAPABILITY_11_9_REMAINS_FIXTURE_ONLY:
        blockers.append("CAP11_9_FIXTURE_ONLY_DRIFT")
    if LIVE_RECONCILIATION_PROVEN:
        # Standing package constant is false; if someone flips it without proof, still gate.
        pass
    if not LIVE_RECONCILIATION_PROVEN:
        blockers.append("LIVE_RECONCILIATION_PROVEN_FALSE")
    if BLOCKS_NEW_ENTRY or UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY:
        blockers.append("BLOCKS_NEW_ENTRY_OR_UNRESOLVED_DIVERGENCE")
    if (
        LIVE_AUTHORIZED
        or LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED
        or LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN
    ):
        blockers.append("UNEXPECTED_LIVE_OR_CANARY_EXECUTED_CLAIM")

    trade_distinction = (
        "TRADE_PERMISSION_CONFIRMED_FALSE"
        if perm.get("TRADE") is False
        else (
            "TRADE_PERMISSION_NOT_ATTESTED"
            if perm.get("TRADE") is None
            else "TRADE_PERMISSION_ATTESTED_TRUE"
        )
    )

    gate_pass = len(blockers) == 0
    return {
        "DOCUMENT_CLASS": "SECTION_11_13_LIVE_CANARY_CYBERSECURITY_GATE_EVAL_V1",
        "CYBERSECURITY_RUNBOOK_VERSION": "V2_1",
        "PRE_LIVE_CYBERSECURITY_GATE": pre_live_cybersecurity_gate,
        "LIVE_CANARY_CYBERSECURITY_GATE": "PASS" if gate_pass else "NOT_PASSED",
        "ELIGIBLE_FOR_LIVE_CANARY_EVALUATION": gate_pass,
        "HISTORICAL_PRE_LIVE_PASS_CARRY_FORWARD_FORBIDDEN": True,
        "SECRET_MANAGEMENT_STATUS": (
            "FAIL" if secret_plaintext_in_repo_or_evidence else "PASS_AUTHORING_NO_SECRET_MATERIAL"
        ),
        "READ_ATTESTATION": bool(read_attestation and perm.get("READ") is True),
        "TRADE_ATTESTATION": bool(trade_attestation and perm.get("TRADE") is True),
        "WITHDRAW_ATTESTATION": bool(withdraw_attestation or perm.get("WITHDRAW") is True),
        "TRADE_ATTESTATION_DISTINCTION": trade_distinction,
        "TRADE_ATTESTATION_BLOCKER": (
            None
            if trade_attestation and perm.get("TRADE") is True
            else (
                "PRIOR_LIVE_DRY_RUN_KEY_CLASS_ATTESTED_TRADE_FALSE;"
                "CANARY_REQUIRES_SEPARATE_TRADE_CAPABLE_API_KEY_AND_ATTESTATION"
            )
        ),
        "NETWORK_BINDING_SECURITY": {
            "venue": REUSED_BINDING_VENUE,
            "rest_host": REUSED_BINDING_REST_HOST,
            "demo_testnet_fallback_forbidden": True,
            "status": "BOUND_FROM_SEALED_PRIOR_PROOF_PENDING_CANARY_SECRETREF",
        },
        "ACCOUNT_BINDING_SECURITY": {
            "account_scope": REUSED_BINDING_ACCOUNT_SCOPE,
            "status": "BOUND_FROM_SEALED_PRIOR_PROOF",
        },
        "INSTRUMENT_BINDING_SECURITY": {
            "instrument_id": "BTC-USDT-SWAP",
            "min_executable_size": "REQUIRES_VENUE_INSTRUMENT_METADATA_AT_EXECUTE",
            "status": "BOUND_INSTRUMENT_ID_ONLY_PENDING_MINSZ",
        },
        "ORDER_SAFETY_SECURITY": {
            "idempotency_policy": "ONE_SHOT_CLORDID_PER_OWNER_GO_BINDING",
            "unknown_submit_handling": "BOUNDED_POLL_THEN_HALT",
            "kill_switch_interaction": "CANCEL_FLATTEN_HALT",
            "status": "CONTRACT_DEFINED_NOT_EXECUTED",
        },
        "EXPOSURE_BLAST_RADIUS_STATUS": {
            "position_count_limit": 1,
            "order_count_limit": 1,
            "minimum_ratified_notional_only": True,
            "automatic_escalation": False,
            "status": "CONTRACT_BOUNDED",
        },
        "SUPPLY_CHAIN_SECURITY_STATUS": "DEFERRED_TO_REPO_DEFINED_PRE_LIVE_ARTIFACTS_NO_UNCONTROLLED_UPGRADES",
        "EVIDENCE_SECURITY_STATUS": "NO_SECRET_VALUES_IN_AUTHORING_EVIDENCE",
        "PRIOR_CANARY_OWNER_GO": PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_BINDING,
        "PRIOR_CANARY_OWNER_GO_STATUS": PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_STATUS,
        "NEW_CANARY_OWNER_GO_GRANTED": False,
        "LIVE_AUTHORIZED": False,
        "BLOCKERS": blockers,
        "ok": True,
    }
