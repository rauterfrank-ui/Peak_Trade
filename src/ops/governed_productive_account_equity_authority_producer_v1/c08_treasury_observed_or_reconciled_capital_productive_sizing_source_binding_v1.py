"""C08 productive sizing-source transport binding (RECONCILED base candidacy only).

Wires Treasury E4 orchestration ingress into the unbound BASE slot transport of
CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1. Does not mint AVAILABLE_FOR_SIZING,
risk-admissible capital, or numeric BASE values. STEP-29P policy unchanged.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping, Tuple

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CapitalAdmissionEvidenceV1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    CapitalAdmissionStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    RISK_EQUITY_DIMENSION,
    STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
    Step29PCapitalRiskAdmissibilityClaimV1,
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.c08_treasury_observed_or_reconciled_capital_semantic_authority_closeout_contract_v1 import (
    C08_INPUT_CLASS,
    CURRENT_RISK_ADMISSIBILITY_OWNER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS,
)
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.constants_v1 import (
    AVAILABLE_FOR_SIZING_MINT_AUTHORIZED,
    RISK_ADMISSIBLE_MINT_AUTHORIZED,
    STEP_29P_MINT_AUTHORIZED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.c08_treasury_observed_or_reconciled_capital_productive_sizing_source_binding_models_v1 import (
    C08ProductiveSizingSourceBindingError,
    C08ProductiveSizingSourceBindingV1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.models_v1 import (
    ProductiveHostTreasuryCapitalAdmissionEvaluationV1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_v1.join_v1 import (
    assert_orchestration_never_mints_sizing_or_step_29p_v1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_v1.models_v1 import (
    TreasuryAccountEquityOrchestrationJoinV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryCapitalAdmissionJoinV1,
    TreasuryFreshnessSignalV1,
    TreasuryReconciliationClassV1,
)

SCHEMA_CLASS = "C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL_PRODUCTIVE_SIZING_SOURCE_BINDING_V1"
CONTRACT_VERSION = "v1"
WP_ID = "C08_PRODUCTIVE_SIZING_SOURCE_BINDING_AFTER_SEMANTIC_CLOSEOUT_V1"
OWNER_GO = "OWNER_GO_C08_PRODUCTIVE_SIZING_SOURCE_BINDING_AFTER_SEMANTIC_CLOSEOUT_V1"
JOIN_SEAM_ID = "C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL_PRODUCTIVE_SIZING_SOURCE_BINDING_V1"

C08_CURRENT_BINDING = "BOUND"
C08_CURRENT_CLASSIFICATION = "PRODUCTIVE_TRANSPORT_BOUND"
C08_PRODUCTIVE_BINDING_AUTHORIZED = True
C08_PRODUCTIVE_BINDING_IMPLEMENTED = True
C08_BASE_CANDIDATE_TRANSPORT_STATUS = "C08_RECONCILED_BASE_CANDIDATE_TRANSPORT_BOUND"
C08_BASE_VALUE_STATUS = CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS

CURRENT_SIZING_OWNER = CURRENT_RISK_ADMISSIBILITY_OWNER
CURRENT_AVAILABLE_FOR_SIZING_PRODUCER = "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1"
CURRENT_STEP_29P_INPUT = RISK_EQUITY_DIMENSION

EARLIEST_NEW_REAL_BLOCKER_AFTER_WP = (
    "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_UNBOUND_AFTER_PRODUCER_DEFINED"
)

_NETWORK_ALLOWED = False
_TREASURY_MINT_FORBIDDEN = True

_ADVERSARIAL_CASE_IDS: Tuple[str, ...] = (
    "A_observed_only",
    "B_observed_unknown",
    "C_reconciled_not_risk_admissible",
    "D_reconciled_risk_admissible",
    "E_stale",
    "F_conflicted_provenance",
    "G_absent",
    "H_credible_depletion",
    "I_positive_restoration_after_depletion",
    "J_restart_unknown",
    "K_replay_old_after_newer_state",
    "L_duplicate_reconciled",
    "M_valid_reconciled_step_29p_deny",
    "N_valid_reconciled_step_29p_admit",
)


def _digest(payload: Mapping[str, str]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _assert_binding_envelope() -> None:
    if not C08_PRODUCTIVE_BINDING_AUTHORIZED or not C08_PRODUCTIVE_BINDING_IMPLEMENTED:
        raise C08ProductiveSizingSourceBindingError("C08_PRODUCTIVE_BINDING_NOT_AUTHORIZED")
    if RISK_ADMISSIBLE_MINT_AUTHORIZED or STEP_29P_MINT_AUTHORIZED:
        raise C08ProductiveSizingSourceBindingError("DOWNSTREAM_MINT_FORBIDDEN")
    if AVAILABLE_FOR_SIZING_MINT_AUTHORIZED:
        raise C08ProductiveSizingSourceBindingError("AVAILABLE_FOR_SIZING_MINT_FORBIDDEN")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS != "UNBOUND":
        raise C08ProductiveSizingSourceBindingError("BASE_NUMERIC_VALUE_MUST_REMAIN_UNBOUND")


def _ingress_evidence_v1(
    orchestration_join: TreasuryAccountEquityOrchestrationJoinV1,
) -> CapitalAdmissionEvidenceV1:
    evidence = orchestration_join.ingress.capital_admission_evidence
    if not isinstance(evidence, CapitalAdmissionEvidenceV1):
        raise C08ProductiveSizingSourceBindingError("CAPITAL_ADMISSION_EVIDENCE_TYPE_INVALID")
    return evidence


def _reconciled_base_candidacy_eligible_v1(
    *,
    treasury_join: TreasuryCapitalAdmissionJoinV1,
    orchestration_join: TreasuryAccountEquityOrchestrationJoinV1,
    usdc_row_status: str,
    balance_freshness: str,
) -> tuple[bool, tuple[str, ...]]:
    ingress = orchestration_join.ingress
    recon = treasury_join.reconciliation
    reasons: list[str] = []

    if str(usdc_row_status or "") == CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO:
        reasons.append("USDC_ROW_ABSENT_NOT_ZERO_FAIL_CLOSED")
        return False, tuple(dict.fromkeys(reasons))

    if str(balance_freshness or "") == TreasuryFreshnessSignalV1.STALE.value:
        reasons.append("C08_STALE_FAIL_CLOSED")
        return False, tuple(dict.fromkeys(reasons))

    recon_class = str(ingress.treasury_reconciliation_class or "")
    if recon_class != TreasuryReconciliationClassV1.RECONCILED.value:
        reasons.append("C08_BASE_CANDIDACY_REQUIRES_RECONCILED")
        return False, tuple(dict.fromkeys(reasons))

    if ingress.fail_closed is True or ingress.orchestration_admitted is not True:
        reasons.append("TREASURY_ORCHESTRATION_INGRESS_NOT_ADMITTED")
        return False, tuple(dict.fromkeys(reasons))

    if recon.fail_closed is True:
        reasons.append("TREASURY_RECONCILIATION_FAIL_CLOSED")
        return False, tuple(dict.fromkeys(reasons))

    evidence = _ingress_evidence_v1(orchestration_join)
    if evidence.risk_admissible is True:
        raise C08ProductiveSizingSourceBindingError("TREASURY_EVIDENCE_RISK_ADMISSIBLE_MINT")

    allowed_status = {
        CapitalAdmissionStatusV1.TRUSTED_PRESENT.value,
        CapitalAdmissionStatusV1.CONTRADICTORY.value,
    }
    if str(evidence.evidence_status or "") not in allowed_status:
        reasons.append("C08_CAPITAL_ADMISSION_EVIDENCE_NOT_CONTRACT_VALID")
        return False, tuple(dict.fromkeys(reasons))

    return True, tuple(dict.fromkeys((*reasons, "C08_RECONCILED_BASE_CANDIDATE_CREATED")))


def bind_c08_productive_sizing_source_from_e4_host_join_v1(
    *,
    treasury_join: TreasuryCapitalAdmissionJoinV1,
    orchestration_join: TreasuryAccountEquityOrchestrationJoinV1,
    host_evaluation: ProductiveHostTreasuryCapitalAdmissionEvaluationV1,
    usdc_row_status: str = "",
    step_29p_claim: Step29PCapitalRiskAdmissibilityClaimV1 | None = None,
    balance_freshness: str = "",
) -> C08ProductiveSizingSourceBindingV1:
    """Transport-only C08 binding at productive host boundary."""
    _assert_binding_envelope()
    assert_orchestration_never_mints_sizing_or_step_29p_v1(orchestration_join)

    ingress = orchestration_join.ingress
    host_eval = host_evaluation
    recon_status = str(
        ingress.treasury_reconciliation_class or host_eval.treasury_reconciliation_status
    )
    reasons: list[str] = list(host_eval.reason_codes)

    if recon_status in {
        TreasuryReconciliationClassV1.UNKNOWN.value,
        TreasuryReconciliationClassV1.AMBIGUOUS.value,
        TreasuryReconciliationClassV1.STALE.value,
        TreasuryReconciliationClassV1.OBSERVED.value,
    }:
        reasons.append("C08_RECONCILIATION_CLASS_INSUFFICIENT_FOR_BASE_CANDIDACY")
        fail_closed = host_eval.fail_closed is True or recon_status in {
            TreasuryReconciliationClassV1.UNKNOWN.value,
            TreasuryReconciliationClassV1.AMBIGUOUS.value,
            TreasuryReconciliationClassV1.STALE.value,
        }
        base_created = False
    elif host_eval.fail_closed is True:
        reasons.append("PRODUCTIVE_HOST_FAIL_CLOSED")
        fail_closed = True
        base_created = False
    else:
        eligible, candidacy_reasons = _reconciled_base_candidacy_eligible_v1(
            treasury_join=treasury_join,
            orchestration_join=orchestration_join,
            usdc_row_status=usdc_row_status,
            balance_freshness=balance_freshness,
        )
        reasons.extend(candidacy_reasons)
        base_created = eligible
        fail_closed = not eligible

    evidence = _ingress_evidence_v1(orchestration_join)
    admissibility = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=evidence,
        claim=step_29p_claim,
    )
    risk_admissible = admissibility.risk_admissible is True
    if base_created is not True:
        risk_admissible = False

    sizing_increase = base_created is True and risk_admissible is True
    if sizing_increase:
        reasons.append("C08_SIZING_INCREASE_ONLY_VIA_STEP_29P_RISK_ADMISSIBLE")
    else:
        reasons.append("C08_NO_SIZING_INCREASE_WITHOUT_STEP_29P_ADMIT")

    block_or_decrease = fail_closed or not sizing_increase

    digest = _digest(
        {
            "join_seam_id": JOIN_SEAM_ID,
            "evidence_id": str(treasury_join.reconciliation.evidence_id or ""),
            "evidence_fingerprint": str(treasury_join.reconciliation.evidence_fingerprint or ""),
            "recon_status": recon_status,
            "base_created": str(base_created),
            "usdc_row_status": str(usdc_row_status or ""),
        }
    )

    if risk_admissible:
        authority_owner = CURRENT_RISK_ADMISSIBILITY_OWNER
    elif base_created:
        authority_owner = "capital_admission_contract_v1"
    else:
        authority_owner = "ops.treasury_phase_2_read_only_reconciliation_v1"

    return C08ProductiveSizingSourceBindingV1(
        c08_binding_implemented=True,
        c08_input_class=C08_INPUT_CLASS,
        base_slot_id=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID,
        base_value_status=C08_BASE_VALUE_STATUS,
        base_candidate_transport_status=(
            C08_BASE_CANDIDATE_TRANSPORT_STATUS if base_created else "UNBOUND"
        ),
        base_candidate_created=base_created,
        base_candidate_directly_available_for_sizing=False,
        risk_admissible=risk_admissible,
        risk_admissibility_separate=True,
        treasury_risk_admissible_mint=False,
        treasury_available_for_sizing_mint=False,
        sizing_increase=sizing_increase,
        block_or_decrease=block_or_decrease,
        fail_closed=fail_closed,
        treasury_reconciliation_status=recon_status,
        usdc_row_status=str(usdc_row_status or host_eval.usdc_row_status or ""),
        reason_codes=tuple(dict.fromkeys((*reasons, JOIN_SEAM_ID))),
        authority_owner=authority_owner,
        join_seam_id=JOIN_SEAM_ID,
        step_29p_authority=STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
        productive_host_code_reachable=host_eval.productive_host_reachable is True,
        provenance_digest=digest,
    )


__all__ = [
    "C08ProductiveSizingSourceBindingError",
    "C08ProductiveSizingSourceBindingV1",
    "bind_c08_productive_sizing_source_from_e4_host_join_v1",
]
