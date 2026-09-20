"""Join Treasury Phase-2 capital admission into account-equity orchestration ingress."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CAPITAL_ADMISSION_AUTHORITY,
    CapitalAdmissionEvidenceV1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
    CapitalAdmissionStatusV1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY,
    AVAILABLE_FOR_SIZING_MINT_AUTHORIZED,
    EDGE_SEAM_ID,
    PARALLEL_ACCOUNT_EQUITY_AUTHORITY_ADDED,
    SECOND_ACCOUNT_EQUITY_AUTHORITY_ADDED,
    STEP_29P_MINT_AUTHORIZED,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_v1.errors_v1 import (
    TreasuryAccountEquityOrchestrationError,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_v1.models_v1 import (
    AccountEquityOrchestrationIngressV1,
    TreasuryAccountEquityOrchestrationJoinV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.join_v1 import (
    assert_treasury_join_never_mints_risk_admissible_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryCapitalAdmissionJoinV1,
    TreasuryReconciliationClassV1,
)

_INCREASE_DEFERRAL_REASON = "CAPITAL_INCREASE_NOT_AUTO_ADMITTED"


def _require_capital_admission_evidence_v1(
    join: TreasuryCapitalAdmissionJoinV1,
) -> CapitalAdmissionEvidenceV1:
    evidence = join.capital_admission_evidence
    if not isinstance(evidence, CapitalAdmissionEvidenceV1):
        raise TreasuryAccountEquityOrchestrationError("CAPITAL_ADMISSION_EVIDENCE_TYPE_INVALID")
    return evidence


def _increase_deferred_to_account_equity_orchestration_v1(
    evidence: CapitalAdmissionEvidenceV1,
    *,
    reconciliation_class: str,
    capital_increase_authority: bool,
) -> bool:
    if reconciliation_class != TreasuryReconciliationClassV1.RECONCILED.value:
        return False
    if not capital_increase_authority:
        return False
    if evidence.evidence_status != CapitalAdmissionStatusV1.CONTRADICTORY.value:
        return False
    codes = set(evidence.reason_codes)
    if _INCREASE_DEFERRAL_REASON not in codes:
        return False
    forbidden = codes - {
        "CAPITAL_ADMISSION_CONTRADICTORY",
        _INCREASE_DEFERRAL_REASON,
        "FULL_CORE_PRE_LIVE_CAPITAL_ADMISSION_SEAM_V1",
    }
    return not forbidden


def join_treasury_capital_admission_into_account_equity_orchestration_v1(
    join: TreasuryCapitalAdmissionJoinV1,
) -> TreasuryAccountEquityOrchestrationJoinV1:
    """E4 only: typed handoff to account-equity orchestration. No STEP-29P or sizing mint."""
    if SECOND_ACCOUNT_EQUITY_AUTHORITY_ADDED or PARALLEL_ACCOUNT_EQUITY_AUTHORITY_ADDED:
        raise TreasuryAccountEquityOrchestrationError("PARALLEL_ACCOUNT_EQUITY_AUTHORITY_DENIED")
    if STEP_29P_MINT_AUTHORIZED or AVAILABLE_FOR_SIZING_MINT_AUTHORIZED:
        raise TreasuryAccountEquityOrchestrationError("DOWNSTREAM_MINT_FORBIDDEN")
    if join.capital_admission_authority != CAPITAL_ADMISSION_AUTHORITY:
        raise TreasuryAccountEquityOrchestrationError("CAPITAL_ADMISSION_AUTHORITY_DRIFT")

    assert_treasury_join_never_mints_risk_admissible_v1(join)
    evidence = _require_capital_admission_evidence_v1(join)
    recon = join.reconciliation

    reasons: list[str] = list(join.treasury_reason_codes)

    if recon.fail_closed:
        ingress = AccountEquityOrchestrationIngressV1(
            orchestration_admitted=False,
            fail_closed=True,
            reason_codes=tuple(
                dict.fromkeys(
                    (
                        *reasons,
                        "TREASURY_ORCHESTRATION_FAIL_CLOSED",
                        "TREASURY_RECONCILIATION_FAIL_CLOSED",
                    )
                )
            ),
            capital_admission_evidence=evidence,
            treasury_reconciliation_class=str(recon.reconciliation_class),
            treasury_capital_increase_authority=bool(recon.capital_increase_authority),
            join_seam_id=EDGE_SEAM_ID,
            capital_admission_authority=CAPITAL_ADMISSION_AUTHORITY,
            account_equity_authority=ACCOUNT_EQUITY_AUTHORITY,
        )
        return TreasuryAccountEquityOrchestrationJoinV1(
            treasury_join_seam_id=str(join.join_seam_id),
            ingress=ingress,
        )

    if _increase_deferred_to_account_equity_orchestration_v1(
        evidence,
        reconciliation_class=str(recon.reconciliation_class),
        capital_increase_authority=bool(recon.capital_increase_authority),
    ):
        ingress = AccountEquityOrchestrationIngressV1(
            orchestration_admitted=True,
            fail_closed=False,
            reason_codes=tuple(
                dict.fromkeys(
                    (
                        *reasons,
                        "TREASURY_ORCHESTRATION_INGRESS_ADMITTED",
                        "CAPITAL_INCREASE_DEFERRED_TO_ACCOUNT_EQUITY_ORCHESTRATION",
                    )
                )
            ),
            capital_admission_evidence=evidence,
            treasury_reconciliation_class=str(recon.reconciliation_class),
            treasury_capital_increase_authority=True,
            join_seam_id=EDGE_SEAM_ID,
            capital_admission_authority=CAPITAL_ADMISSION_AUTHORITY,
            account_equity_authority=ACCOUNT_EQUITY_AUTHORITY,
        )
        return TreasuryAccountEquityOrchestrationJoinV1(
            treasury_join_seam_id=str(join.join_seam_id),
            ingress=ingress,
        )

    if (
        str(recon.reconciliation_class) == TreasuryReconciliationClassV1.RECONCILED.value
        and evidence.evidence_status == CapitalAdmissionStatusV1.TRUSTED_PRESENT.value
        and not recon.capital_increase_authority
    ):
        ingress = AccountEquityOrchestrationIngressV1(
            orchestration_admitted=True,
            fail_closed=False,
            reason_codes=tuple(
                dict.fromkeys(
                    (
                        *reasons,
                        "TREASURY_ORCHESTRATION_INGRESS_ADMITTED",
                        "TREASURY_RECONCILED_STABLE_CAPITAL_HANDOFF",
                    )
                )
            ),
            capital_admission_evidence=evidence,
            treasury_reconciliation_class=str(recon.reconciliation_class),
            treasury_capital_increase_authority=False,
            join_seam_id=EDGE_SEAM_ID,
            capital_admission_authority=CAPITAL_ADMISSION_AUTHORITY,
            account_equity_authority=ACCOUNT_EQUITY_AUTHORITY,
        )
        return TreasuryAccountEquityOrchestrationJoinV1(
            treasury_join_seam_id=str(join.join_seam_id),
            ingress=ingress,
        )

    ingress = AccountEquityOrchestrationIngressV1(
        orchestration_admitted=False,
        fail_closed=True,
        reason_codes=tuple(
            dict.fromkeys(
                (
                    *reasons,
                    "TREASURY_ORCHESTRATION_INGRESS_DENIED",
                )
            )
        ),
        capital_admission_evidence=evidence,
        treasury_reconciliation_class=str(recon.reconciliation_class),
        treasury_capital_increase_authority=bool(recon.capital_increase_authority),
        join_seam_id=EDGE_SEAM_ID,
        capital_admission_authority=CAPITAL_ADMISSION_AUTHORITY,
        account_equity_authority=ACCOUNT_EQUITY_AUTHORITY,
    )
    return TreasuryAccountEquityOrchestrationJoinV1(
        treasury_join_seam_id=str(join.join_seam_id),
        ingress=ingress,
    )


def assert_orchestration_never_mints_sizing_or_step_29p_v1(
    result: TreasuryAccountEquityOrchestrationJoinV1,
) -> bool:
    ingress = result.ingress
    evidence = ingress.capital_admission_evidence
    if evidence.risk_admissible is True:
        raise TreasuryAccountEquityOrchestrationError("ORCHESTRATION_RISK_ADMISSIBLE_TRUE")
    if evidence.capital_authority_class == CAPITAL_AUTHORITY_RISK_ADMISSIBLE:
        raise TreasuryAccountEquityOrchestrationError("ORCHESTRATION_RISK_ADMISSIBLE_CLASS")
    if ingress.orchestration_admitted and ingress.fail_closed:
        raise TreasuryAccountEquityOrchestrationError("ORCHESTRATION_ADMITTED_FAIL_CLOSED_DRIFT")
    _ = STEP_29P_MINT_AUTHORIZED
    _ = AVAILABLE_FOR_SIZING_MINT_AUTHORIZED
    return False
