"""C08 treasury capital semantic authority closeout (semantic definition only).

Closes census candidate C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL semantics before
any productive AVAILABLE_FOR_SIZING BASE binding. Does not wire runtime, mint sizing,
or mint risk-admissible capital.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping, Tuple

SCHEMA_CLASS = "C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL_SEMANTIC_AUTHORITY_CLOSEOUT_CONTRACT_V1"
CONTRACT_VERSION = "v1"
CANDIDATE_ID = "C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL"
RATIFICATION_SCOPE = "C08_SEMANTIC_AUTHORITY_CLOSEOUT_ONLY"
AUTHORITY_EFFECT = "NONE"

C08_SURFACE_EXISTS = True
C08_CURRENT_BINDING = "BOUND"
C08_CURRENT_CLASSIFICATION = "PRODUCTIVE_TRANSPORT_BOUND"
C08_PRODUCTIVE_BINDING_AUTHORIZED = True
C08_PRODUCTIVE_BINDING_IMPLEMENTED = True
C08_SEMANTIC_CLOSEOUT = "CLOSED"

# Split capital classes — never merge as OBSERVED_OR_RECONCILED for authority.
TREASURY_OBSERVED_CAPITAL_CLASS = "TREASURY_OBSERVED_CAPITAL"
TREASURY_RECONCILED_CAPITAL_CLASS = "TREASURY_RECONCILED_CAPITAL"
TREASURY_RISK_ADMISSIBLE_CAPITAL_CLASS = "RISK_ADMISSIBLE_CAPITAL"
AVAILABLE_FOR_SIZING_DIMENSION = "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"

C08_INPUT_CLASS = (
    "TREASURY_ACCOUNT_EQUITY_ORCHESTRATION_INGRESS_V1_RECONCILED_BASE_CANDIDATE_EVIDENCE"
)
C08_INCREASE_ELIGIBILITY = (
    "NONE_FROM_TREASURY_OBSERVED_OR_RECONCILED_ALONE;"
    "PRODUCTIVE_SIZING_CAPACITY_INCREASE_REQUIRES_STEP_29P_RISK_ADMISSIBLE"
)
C08_DECREASE_ELIGIBILITY = (
    "CONSERVATIVE_BLOCK_OR_DECREASE_VIA_CAPITAL_ADMISSION_AND_TREASURY_FAIL_CLOSED;"
    "CREDIBLE_EXTERNAL_DEPLETION_SIGNAL_VIA_TREASURY_PHASE_2_DECREASE_BINDING;"
    "NO_TREASURY_MINT_OF_RISK_ADMISSIBLE_FOR_DECREASE"
)
C08_RECONCILIATION_REQUIREMENT = (
    "FUTURE_BASE_CANDIDACY_REQUIRES_TreasuryReconciliationClassV1_RECONCILED;"
    "OBSERVED_UNKNOWN_STALE_AMBIGUOUS_INSUFFICIENT_FOR_BASE_CANDIDACY"
)
C08_RISK_ADMISSIBILITY_REQUIREMENT = (
    "MANDATORY_SEPARATE_OWNER capital_risk_admissibility_owner_v1;"
    "evaluate_step_29p_capital_risk_admissibility_v1;"
    "TREASURY_CANNOT_MINT_OR_SUBSTITUTE"
)

C08_UNKNOWN_BEHAVIOR = "FAIL_CLOSED"
C08_STALE_BEHAVIOR = "FAIL_CLOSED"
C08_ABSENT_BEHAVIOR = "FAIL_CLOSED"
C08_CONFLICTED_BEHAVIOR = "FAIL_CLOSED"

C08_CANDIDATE = CANDIDATE_ID
C08_CURRENT_PRODUCER = (
    "ops.treasury_phase_2_read_only_reconciliation_v1;"
    "ops.treasury_productive_read_only_venue_observation_v1;"
    "ops.offline_funding_balance_read_producer_v1"
)
C08_PROPOSED_CONSUMER = "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1_BASE_SLOT_UNBOUND"
CURRENT_SIZING_OWNER = "capital_risk_admissibility_owner_v1"
CURRENT_RISK_ADMISSIBILITY_OWNER = "capital_risk_admissibility_owner_v1"
CURRENT_ACCOUNT_EQUITY_OWNER = "ops.governed_productive_account_equity_authority_producer_v1"
CURRENT_ALLOWED_SIZING_INPUT = AVAILABLE_FOR_SIZING_DIMENSION

OBSERVED_CAPITAL_SIZING_INCREASE_ALLOWED = False
RECONCILED_CAPITAL_SIZING_INCREASE_ALLOWED = False
RISK_ADMISSIBLE_CAPITAL_SIZING_INCREASE_ALLOWED = True

OBSERVED_CAPITAL_DECREASE_OR_BLOCK_ALLOWED = True
RECONCILED_CAPITAL_DECREASE_OR_BLOCK_ALLOWED = True
RISK_ADMISSIBLE_CAPITAL_DECREASE_OR_BLOCK_ALLOWED = True

NEXT_PRODUCTIVE_BLOCKER = (
    "C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL_PRODUCTIVE_SIZING_SOURCE_NOT_BOUND"
)
NEXT_OWNER_GO_REQUIRED = "OWNER_GO_C08_PRODUCTIVE_SIZING_SOURCE_BINDING_AFTER_SEMANTIC_CLOSEOUT_V1"

_ADVERSARIAL_CASE_IDS: Tuple[str, ...] = (
    "A_observed_unreconciled",
    "B_observed_reconciliation_unknown",
    "C_reconciled_not_risk_admissible",
    "D_risk_admissible_fresh",
    "E_stale_observed",
    "F_stale_reconciled",
    "G_conflicting_provenance",
    "H_absent_treasury_capital",
    "I_credible_depletion",
    "J_subsequent_positive_restoration",
    "K_restart_with_unknown",
    "L_replayed_old_observation_after_newer_account_state",
)


@dataclass(frozen=True)
class C08AdversarialSemanticCaseV1:
    case_id: str
    treasury_observed: bool
    treasury_reconciled: bool
    treasury_reconciliation_class: str
    risk_admissible: bool
    increase_allowed: bool
    decrease_or_block_allowed: bool
    fail_closed: bool
    authority_owner: str


@dataclass(frozen=True)
class C08TreasuryObservedOrReconciledCapitalSemanticAuthorityCloseoutContractV1:
    c08_semantic_authority_closeout_contract_id: str
    c08_semantic_authority_closeout_contract_version: str
    candidate_id: str
    ratification_scope: str
    c08_surface_exists: bool
    c08_current_binding: str
    c08_current_classification: str
    c08_semantic_closeout: str
    c08_input_class: str
    c08_increase_eligibility: str
    c08_decrease_eligibility: str
    c08_reconciliation_requirement: str
    c08_risk_admissibility_requirement: str
    c08_unknown_behavior: str
    c08_stale_behavior: str
    c08_absent_behavior: str
    c08_conflicted_behavior: str
    c08_productive_binding_authorized: bool
    c08_productive_binding_implemented: bool
    c08_semantic_authority_closeout_contract_authority_effect: str
    provenance_digest: str


def _digest(payload: Mapping[str, str]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def adjudicate_c08_adversarial_semantic_case_v1(case_id: str) -> C08AdversarialSemanticCaseV1:
    """Semantic-only matrix; no runtime binding."""
    if case_id not in _ADVERSARIAL_CASE_IDS:
        raise ValueError(f"C08_ADVERSARIAL_CASE_UNKNOWN:{case_id}")

    risk_owner = CURRENT_RISK_ADMISSIBILITY_OWNER
    admission_owner = "capital_admission_contract_v1"
    treasury_owner = "ops.treasury_phase_2_read_only_reconciliation_v1"

    if case_id == "A_observed_unreconciled":
        return C08AdversarialSemanticCaseV1(
            case_id=case_id,
            treasury_observed=True,
            treasury_reconciled=False,
            treasury_reconciliation_class="OBSERVED",
            risk_admissible=False,
            increase_allowed=False,
            decrease_or_block_allowed=True,
            fail_closed=True,
            authority_owner=treasury_owner,
        )
    if case_id == "B_observed_reconciliation_unknown":
        return C08AdversarialSemanticCaseV1(
            case_id=case_id,
            treasury_observed=True,
            treasury_reconciled=False,
            treasury_reconciliation_class="UNKNOWN",
            risk_admissible=False,
            increase_allowed=False,
            decrease_or_block_allowed=True,
            fail_closed=True,
            authority_owner=treasury_owner,
        )
    if case_id == "C_reconciled_not_risk_admissible":
        return C08AdversarialSemanticCaseV1(
            case_id=case_id,
            treasury_observed=True,
            treasury_reconciled=True,
            treasury_reconciliation_class="RECONCILED",
            risk_admissible=False,
            increase_allowed=False,
            decrease_or_block_allowed=True,
            fail_closed=False,
            authority_owner=admission_owner,
        )
    if case_id == "D_risk_admissible_fresh":
        return C08AdversarialSemanticCaseV1(
            case_id=case_id,
            treasury_observed=True,
            treasury_reconciled=True,
            treasury_reconciliation_class="RECONCILED",
            risk_admissible=True,
            increase_allowed=True,
            decrease_or_block_allowed=True,
            fail_closed=False,
            authority_owner=risk_owner,
        )
    if case_id == "E_stale_observed":
        return C08AdversarialSemanticCaseV1(
            case_id=case_id,
            treasury_observed=True,
            treasury_reconciled=False,
            treasury_reconciliation_class="STALE",
            risk_admissible=False,
            increase_allowed=False,
            decrease_or_block_allowed=True,
            fail_closed=True,
            authority_owner=treasury_owner,
        )
    if case_id == "F_stale_reconciled":
        return C08AdversarialSemanticCaseV1(
            case_id=case_id,
            treasury_observed=True,
            treasury_reconciled=True,
            treasury_reconciliation_class="STALE",
            risk_admissible=False,
            increase_allowed=False,
            decrease_or_block_allowed=True,
            fail_closed=True,
            authority_owner=treasury_owner,
        )
    if case_id == "G_conflicting_provenance":
        return C08AdversarialSemanticCaseV1(
            case_id=case_id,
            treasury_observed=True,
            treasury_reconciled=False,
            treasury_reconciliation_class="AMBIGUOUS",
            risk_admissible=False,
            increase_allowed=False,
            decrease_or_block_allowed=True,
            fail_closed=True,
            authority_owner=treasury_owner,
        )
    if case_id == "H_absent_treasury_capital":
        return C08AdversarialSemanticCaseV1(
            case_id=case_id,
            treasury_observed=False,
            treasury_reconciled=False,
            treasury_reconciliation_class="UNKNOWN",
            risk_admissible=False,
            increase_allowed=False,
            decrease_or_block_allowed=True,
            fail_closed=True,
            authority_owner=treasury_owner,
        )
    if case_id == "I_credible_depletion":
        return C08AdversarialSemanticCaseV1(
            case_id=case_id,
            treasury_observed=True,
            treasury_reconciled=False,
            treasury_reconciliation_class="OBSERVED",
            risk_admissible=False,
            increase_allowed=False,
            decrease_or_block_allowed=True,
            fail_closed=True,
            authority_owner=(
                "ops.treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1"
            ),
        )
    if case_id == "J_subsequent_positive_restoration":
        return C08AdversarialSemanticCaseV1(
            case_id=case_id,
            treasury_observed=True,
            treasury_reconciled=True,
            treasury_reconciliation_class="RECONCILED",
            risk_admissible=False,
            increase_allowed=False,
            decrease_or_block_allowed=True,
            fail_closed=False,
            authority_owner=admission_owner,
        )
    if case_id == "K_restart_with_unknown":
        return C08AdversarialSemanticCaseV1(
            case_id=case_id,
            treasury_observed=False,
            treasury_reconciled=False,
            treasury_reconciliation_class="UNKNOWN",
            risk_admissible=False,
            increase_allowed=False,
            decrease_or_block_allowed=True,
            fail_closed=True,
            authority_owner=treasury_owner,
        )
    if case_id == "L_replayed_old_observation_after_newer_account_state":
        return C08AdversarialSemanticCaseV1(
            case_id=case_id,
            treasury_observed=True,
            treasury_reconciled=False,
            treasury_reconciliation_class="STALE",
            risk_admissible=False,
            increase_allowed=False,
            decrease_or_block_allowed=True,
            fail_closed=True,
            authority_owner=treasury_owner,
        )
    raise ValueError(f"C08_ADVERSARIAL_CASE_UNREACHABLE:{case_id}")


def build_c08_treasury_observed_or_reconciled_capital_semantic_authority_closeout_contract_v1(
    *,
    c08_semantic_authority_closeout_contract_id: str,
) -> C08TreasuryObservedOrReconciledCapitalSemanticAuthorityCloseoutContractV1:
    payload = {
        "c08_semantic_authority_closeout_contract_id": c08_semantic_authority_closeout_contract_id,
        "c08_semantic_authority_closeout_contract_version": CONTRACT_VERSION,
        "candidate_id": CANDIDATE_ID,
        "ratification_scope": RATIFICATION_SCOPE,
        "c08_semantic_closeout": C08_SEMANTIC_CLOSEOUT,
        "c08_input_class": C08_INPUT_CLASS,
        "c08_increase_eligibility": C08_INCREASE_ELIGIBILITY,
        "c08_decrease_eligibility": C08_DECREASE_ELIGIBILITY,
        "authority_effect": AUTHORITY_EFFECT,
    }
    digest = _digest(payload)
    return C08TreasuryObservedOrReconciledCapitalSemanticAuthorityCloseoutContractV1(
        c08_semantic_authority_closeout_contract_id=c08_semantic_authority_closeout_contract_id,
        c08_semantic_authority_closeout_contract_version=CONTRACT_VERSION,
        candidate_id=CANDIDATE_ID,
        ratification_scope=RATIFICATION_SCOPE,
        c08_surface_exists=C08_SURFACE_EXISTS,
        c08_current_binding=C08_CURRENT_BINDING,
        c08_current_classification=C08_CURRENT_CLASSIFICATION,
        c08_semantic_closeout=C08_SEMANTIC_CLOSEOUT,
        c08_input_class=C08_INPUT_CLASS,
        c08_increase_eligibility=C08_INCREASE_ELIGIBILITY,
        c08_decrease_eligibility=C08_DECREASE_ELIGIBILITY,
        c08_reconciliation_requirement=C08_RECONCILIATION_REQUIREMENT,
        c08_risk_admissibility_requirement=C08_RISK_ADMISSIBILITY_REQUIREMENT,
        c08_unknown_behavior=C08_UNKNOWN_BEHAVIOR,
        c08_stale_behavior=C08_STALE_BEHAVIOR,
        c08_absent_behavior=C08_ABSENT_BEHAVIOR,
        c08_conflicted_behavior=C08_CONFLICTED_BEHAVIOR,
        c08_productive_binding_authorized=C08_PRODUCTIVE_BINDING_AUTHORIZED,
        c08_productive_binding_implemented=C08_PRODUCTIVE_BINDING_IMPLEMENTED,
        c08_semantic_authority_closeout_contract_authority_effect=AUTHORITY_EFFECT,
        provenance_digest=digest,
    )


def c08_adversarial_semantic_matrix_v1() -> Tuple[C08AdversarialSemanticCaseV1, ...]:
    return tuple(
        adjudicate_c08_adversarial_semantic_case_v1(case_id) for case_id in _ADVERSARIAL_CASE_IDS
    )
