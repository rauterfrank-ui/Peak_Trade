"""Canonical Canary governance state-transition matrix (§11.13.5 / audit).

States must not collapse. Authoring/audit only — no execute authority.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    OWNER_GO_AUTHORING,
    OWNER_GO_EXECUTE,
)

# Permanent historical consume — never reusable via authoring/docs/Notion/merge.
PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_BINDING = (
    "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE@0f21b53e001e94085941c774a43a27562a1743fe"
)
PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_STATUS = "CONSUMED_ONCE_FAIL_CLOSED_NO_EXECUTE"
PRIOR_OWNER_GO_REUSABLE = False

CANARY_GOVERNANCE_STATES: tuple[str, ...] = (
    "CANARY_SURFACE_AUTHORED",
    "CANARY_SURFACE_MERGED",
    "CANARY_PREREQUISITES_PROVEN",
    "OWNER_GO_CANARY_GRANTED",
    "OWNER_GO_CANARY_CONSUMED",
    "CANARY_EXECUTED",
    "CANARY_RECONCILED",
    "CANARY_PROVEN",
    "POST_CANARY_PROGRESSION_AUTHORIZED",
    "GENERAL_LIVE_AUTHORIZED",
)

MERGE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT: tuple[str, ...] = (
    "GO_MERGE",
    "OWNER_GO_MERGE",
    "MERGE_GO",
    "PR_MERGE",
)
NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT: tuple[str, ...] = (
    "SECTION_11_13_5_CANARY_EXECUTION_REEVALUATION",
    "SECTION_11_13_5_CANARY_EXECUTION_PLUMBING_REMEDIATION_PREPARATION",
    "OWNER_GO_CANARY_SUBMIT_TRANSPORT_PREPARATION",
    "OWNER_GO_SECTION_11_13_LIVE_CANARY_PRODUCTIVE_SURFACE_AUTHORING",
    "SECTION_11_13_5_POST_HTTP_401_BOUNDED_REMEDIATION_PREPARATION",
    # Historical consumed GO identity. The MARKET_PERMISSION substring is
    # not a proven root-cause classification.
    "SECTION_11_13_5_OKX_50124_MARKET_PERMISSION_REMEDIATION_AND_CLASSIFICATION_PREPARATION",
    "OWNER_GO_BOUND_UNPROVEN_NORMAL_EXPIRY_FEE_ECONOMIC_RISK_WITH_INTERNAL_CONSERVATIVE_RESERVE",
    "OWNER_GO_REQUIRED_TO_RESOLVE_REMAINING_UNPROVEN_POSITION_VALUE_FX_AND_ROUNDING_FOR_OPERATIONAL_RESERVE",
    "OWNER_GO_REQUIRED_TO_RATIFY_EXACT_FORMULA_BODY",
    "OWNER_GO_REQUIRED_TO_BIND_UNINSTANTIATED_FORMULA_TERM_INSTANCES_AND_FX_ROUNDING_BEFORE_FUNDING",
)


def build_canary_governance_state_matrix_v1() -> list[dict[str, Any]]:
    """Return explicit transition rows; each next state requires separate proof/GO."""

    def row(
        current: str,
        *,
        required_proof: str,
        required_owner_auth: str,
        network: str,
        order: str,
        account: str,
        max_exposure: str,
        next_state: str,
        fail_closed: str,
        evidence: str,
        consumption: str,
    ) -> dict[str, Any]:
        return {
            "CURRENT_STATE": current,
            "REQUIRED_PROOF": required_proof,
            "REQUIRED_OWNER_AUTHORIZATION": required_owner_auth,
            "NETWORK_EFFECT_ALLOWED": network,
            "ORDER_EFFECT_ALLOWED": order,
            "ACCOUNT_MUTATION_ALLOWED": account,
            "MAX_EXPOSURE_ALLOWED": max_exposure,
            "NEXT_STATE": next_state,
            "FAIL_CLOSED_STATE": fail_closed,
            "EVIDENCE_REQUIRED": evidence,
            "AUTHORIZATION_CONSUMPTION_RULE": consumption,
        }

    return [
        row(
            "CANARY_SURFACE_AUTHORED",
            required_proof="PACKAGE_TESTS_PASS+SSOT_AUTHORING_FACTS",
            required_owner_auth=OWNER_GO_AUTHORING,
            network="NONE",
            order="NONE",
            account="NONE",
            max_exposure="0",
            next_state="CANARY_SURFACE_MERGED",
            fail_closed="CANARY_SURFACE_AUTHORED",
            evidence="section_11_13_5 package+forensic evidence",
            consumption="AUTHORING_GO_ONE_SHOT_NOT_EXECUTE",
        ),
        row(
            "CANARY_SURFACE_MERGED",
            required_proof="ORIGIN_MAIN_CONTAINS_SECTION_11_13_5_PACKAGE",
            required_owner_auth="MERGE_GO_OR_PROTECTED_MAIN_MERGE",
            network="NONE",
            order="NONE",
            account="NONE",
            max_exposure="0",
            next_state="CANARY_PREREQUISITES_PROVEN",
            fail_closed="CANARY_SURFACE_AUTHORED",
            evidence="origin/main SHA + CI required checks",
            consumption="MERGE_GO_IS_NOT_CANARY_EXECUTE",
        ),
        row(
            "CANARY_PREREQUISITES_PROVEN",
            required_proof=(
                "LIVE_RECONCILIATION_PROVEN=true+"
                "BLOCKS_NEW_ENTRY=false+"
                "TRADE_ATTESTATION=true+"
                "LIVE_CANARY_CYBERSECURITY_GATE=PASS"
            ),
            required_owner_auth="OWNER_ADOPTION_POLICIES+OWNER_TRADE_KEY_ATTESTATION",
            network="GET_ONLY_IF_SEPARATELY_AUTHORIZED",
            order="NONE",
            account="NONE",
            max_exposure="0",
            next_state="OWNER_GO_CANARY_GRANTED",
            fail_closed="CANARY_SURFACE_MERGED",
            evidence="adoption+permission+cyber gate sealed evidence",
            consumption="PREREQUISITE_PROOFS_DO_NOT_CONSUME_EXECUTE_GO",
        ),
        row(
            "OWNER_GO_CANARY_GRANTED",
            required_proof="NEW_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_BOUND_TO_ORIGIN_MAIN_SHA",
            required_owner_auth=OWNER_GO_EXECUTE,
            network="NONE_UNTIL_EXECUTE",
            order="NONE_UNTIL_EXECUTE",
            account="NONE_UNTIL_EXECUTE",
            max_exposure="0_UNTIL_EXECUTE",
            next_state="CANARY_EXECUTED",
            fail_closed="OWNER_GO_CANARY_CONSUMED",
            evidence="authorization_binding.json one-shot",
            consumption="ONE_SHOT_SHA_SCOPED;PRIOR_FAIL_CLOSED_GO_NOT_REUSABLE",
        ),
        row(
            "OWNER_GO_CANARY_CONSUMED",
            required_proof="EXECUTE_ATTEMPT_OR_EXPLICIT_CONSUME_RECORD",
            required_owner_auth="NONE_FURTHER_ON_SAME_TOKEN",
            network="AS_RECORDED",
            order="AS_RECORDED",
            account="AS_RECORDED",
            max_exposure="AS_RECORDED",
            next_state="REQUIRES_NEW_OWNER_GO_FOR_ANY_FURTHER_EXECUTE",
            fail_closed="OWNER_GO_CANARY_CONSUMED",
            evidence="consume ledger + claims",
            consumption="PERMANENT_NON_REUSABLE",
        ),
        row(
            "CANARY_EXECUTED",
            required_proof="ORDER_SUBMIT_ACK_OR_REJECT_SEALED",
            required_owner_auth=OWNER_GO_EXECUTE + "_ALREADY_BOUND",
            network="LIVE_CANARY_MINIMUM_EXPOSURE",
            order="SINGLE_MIN_EXPOSURE_LIMIT",
            account="BOUNDED_CANARY_ONLY",
            max_exposure="MIN_EXECUTABLE_NOTIONAL_ONLY",
            next_state="CANARY_RECONCILED",
            fail_closed="HALTED_OWNER_REVIEW",
            evidence="LIVE_CANARY proof root",
            consumption="EXECUTE_GO_CONSUMED_ON_ATTEMPT",
        ),
        row(
            "CANARY_RECONCILED",
            required_proof="POST_TRADE_RECON_PASS_NO_RESIDUALS",
            required_owner_auth="NONE_ADDITIONAL",
            network="GET_ONLY_RECON",
            order="NONE_NEW",
            account="NONE_NEW",
            max_exposure="FLAT_OR_MIN_ONLY",
            next_state="CANARY_PROVEN",
            fail_closed="CANARY_EXECUTED_UNRECONCILED",
            evidence="post-trade reconciliation layers",
            consumption="NO_NEW_GO",
        ),
        row(
            "CANARY_PROVEN",
            required_proof="VERIFIER_PASS+MANIFEST_VERIFY_RC=0+SSOT_BIND",
            required_owner_auth="NONE_ADDITIONAL",
            network="NONE",
            order="NONE",
            account="NONE",
            max_exposure="0_NEW",
            next_state="POST_CANARY_PROGRESSION_AUTHORIZED",
            fail_closed="CANARY_RECONCILED",
            evidence="SSOT proven closeout",
            consumption="PROVEN_IS_NOT_GENERAL_LIVE",
        ),
        row(
            "POST_CANARY_PROGRESSION_AUTHORIZED",
            required_proof="SEPARATE_OWNER_GO_FOR_NEXT_STAGE",
            required_owner_auth="OWNER_GO_LIVE_BOUNDED_SINGLE_FUTURE_OR_EQUIVALENT",
            network="NONE_UNTIL_THAT_GO",
            order="NONE_UNTIL_THAT_GO",
            account="NONE_UNTIL_THAT_GO",
            max_exposure="0_UNTIL_THAT_GO",
            next_state="STAGE_SPECIFIC",
            fail_closed="CANARY_PROVEN",
            evidence="separate stage GO binding",
            consumption="CANARY_SUCCESS_DOES_NOT_AUTHORIZE_PROGRESSION",
        ),
        row(
            "GENERAL_LIVE_AUTHORIZED",
            required_proof="SEPARATE_FULL_LIVE_AUTHORIZATION_CONTRACT",
            required_owner_auth="OWNER_GO_LIVE_ACTIVATION_OR_EQUIVALENT",
            network="PER_THAT_CONTRACT",
            order="PER_THAT_CONTRACT",
            account="PER_THAT_CONTRACT",
            max_exposure="PER_THAT_CONTRACT",
            next_state="OUT_OF_CANARY_SCOPE",
            fail_closed="NOT_GENERAL_LIVE",
            evidence="Live activation evidence ladder",
            consumption="CANARY_SUCCESS_DOES_NOT_SET_LIVE_AUTHORIZED",
        ),
    ]


def prove_canary_governance_matrix_invariants_v1() -> dict[str, Any]:
    matrix = build_canary_governance_state_matrix_v1()
    states = [row["CURRENT_STATE"] for row in matrix]
    ok = all(
        [
            list(states) == list(CANARY_GOVERNANCE_STATES),
            len(set(states)) == len(states),
            PRIOR_OWNER_GO_REUSABLE is False,
            PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_STATUS
            == "CONSUMED_ONCE_FAIL_CLOSED_NO_EXECUTE",
            any(
                row["CURRENT_STATE"] == "CANARY_PROVEN"
                and "NOT_GENERAL_LIVE" in row["AUTHORIZATION_CONSUMPTION_RULE"]
                or row["CURRENT_STATE"] == "CANARY_PROVEN"
                and "PROVEN_IS_NOT_GENERAL_LIVE" in row["AUTHORIZATION_CONSUMPTION_RULE"]
                for row in matrix
            ),
            any(
                row["CURRENT_STATE"] == "GENERAL_LIVE_AUTHORIZED"
                and "CANARY_SUCCESS_DOES_NOT_SET_LIVE_AUTHORIZED"
                in row["AUTHORIZATION_CONSUMPTION_RULE"]
                for row in matrix
            ),
            any(
                row["CURRENT_STATE"] == "POST_CANARY_PROGRESSION_AUTHORIZED"
                and "DOES_NOT_AUTHORIZE_PROGRESSION" in row["AUTHORIZATION_CONSUMPTION_RULE"]
                for row in matrix
            ),
        ]
    )
    return {
        "ok": ok,
        "states": states,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_BINDING,
        "PRIOR_OWNER_GO_STATUS": PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_STATUS,
        "PRIOR_OWNER_GO_REUSABLE": False,
        "CANARY_SUCCESS_IMPLIES_GENERAL_LIVE": False,
        "CANARY_SUCCESS_IMPLIES_EXPOSURE_INCREASE": False,
        "LEGACY_FIXTURE_AUTHORITY_BLOCKED": True,
        "matrix": matrix,
    }


def refuse_merge_go_as_canary_execute_v1(*, owner_go: str) -> None:
    token = str(owner_go or "").strip().upper()
    if any(marker in token for marker in MERGE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT):
        raise RuntimeError(f"MERGE_GO_CANNOT_AUTHORIZE_CANARY_SUBMIT:{owner_go}")
    if token == OWNER_GO_AUTHORING.upper():
        raise RuntimeError("AUTHORING_GO_CANNOT_AUTHORIZE_CANARY_SUBMIT")


def refuse_prior_consumed_canary_go_reuse_v1(*, owner_go_binding: str) -> None:
    if owner_go_binding == PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_BINDING:
        raise RuntimeError(
            "PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_NOT_REUSABLE:"
            f"{PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_STATUS}"
        )
