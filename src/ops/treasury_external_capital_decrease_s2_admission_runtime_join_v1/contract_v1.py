"""Fail-closed S2 admission contract for external capital decrease. No deposit increase."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CapitalAdmissionEvidenceV1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
    CapitalAdmissionStatusV1,
)
from src.ops.treasury_external_capital_decrease_s2_admission_runtime_join_v1.constants_v1 import (
    JOIN_SEAM_ID,
)
from src.ops.treasury_external_capital_decrease_s2_admission_runtime_join_v1.errors_v1 import (
    TreasuryExternalCapitalDecreaseS2AdmissionError,
)
from src.ops.treasury_external_capital_decrease_s2_admission_runtime_join_v1.models_v1 import (
    TreasuryExternalCapitalDecreaseS2AdmissionContractV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.join_v1 import (
    assert_treasury_join_never_mints_risk_admissible_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryCapitalAdmissionJoinV1,
    TreasuryReconciliationClassV1,
    TreasuryVenueObservationV1,
)


def _parse_amount(raw: str) -> Decimal | None:
    text = str(raw or "").strip()
    if text == "":
        return None
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite() or value < 0:
        return None
    return value


def evaluate_treasury_external_capital_decrease_s2_admission_contract_v1(
    *,
    observation: TreasuryVenueObservationV1,
    treasury_join: TreasuryCapitalAdmissionJoinV1,
) -> TreasuryExternalCapitalDecreaseS2AdmissionContractV1:
    """Credible decrease must not raise admissible capital; unknown/stale stay fail-closed."""
    if observation.deposit_history_confirms_increase:
        raise TreasuryExternalCapitalDecreaseS2AdmissionError("DEPOSIT_INCREASE_PATH_DENIED")

    if treasury_join.reconciliation.capital_increase_authority:
        raise TreasuryExternalCapitalDecreaseS2AdmissionError("CAPITAL_INCREASE_AUTHORITY_DENIED")

    venue = _parse_amount(observation.venue_balance_raw)
    prior = _parse_amount(observation.prior_reconciled_capital_raw)
    if venue is not None and prior is not None and venue > prior:
        raise TreasuryExternalCapitalDecreaseS2AdmissionError("OBSERVED_INCREASE_DENIED")

    assert_treasury_join_never_mints_risk_admissible_v1(treasury_join)
    evidence = treasury_join.capital_admission_evidence
    if not isinstance(evidence, CapitalAdmissionEvidenceV1):
        raise TreasuryExternalCapitalDecreaseS2AdmissionError(
            "CAPITAL_ADMISSION_EVIDENCE_TYPE_INVALID"
        )
    if evidence.risk_admissible is True:
        raise TreasuryExternalCapitalDecreaseS2AdmissionError("RISK_ADMISSIBLE_MINT_DENIED")
    if evidence.capital_authority_class == CAPITAL_AUTHORITY_RISK_ADMISSIBLE:
        raise TreasuryExternalCapitalDecreaseS2AdmissionError("RISK_ADMISSIBLE_CLASS_DENIED")

    reasons: list[str] = ["S2_EXTERNAL_CAPITAL_DECREASE_ADMISSION_CONTRACT"]
    recon_class = str(treasury_join.reconciliation.reconciliation_class)
    fail_closed = bool(treasury_join.reconciliation.fail_closed)

    if recon_class in {
        TreasuryReconciliationClassV1.UNKNOWN.value,
        TreasuryReconciliationClassV1.AMBIGUOUS.value,
        TreasuryReconciliationClassV1.STALE.value,
    }:
        reasons.append("S2_DECREASE_RECONCILIATION_FAIL_CLOSED")
        fail_closed = True
    if recon_class == TreasuryReconciliationClassV1.UNKNOWN.value:
        reasons.append("S2_UNKNOWN_NO_OPTIMISTIC_RESTORE")
    if evidence.evidence_status == CapitalAdmissionStatusV1.TRUSTED_PRESENT.value:
        if venue is not None and prior is not None and prior > venue:
            raise TreasuryExternalCapitalDecreaseS2AdmissionError(
                "CREDIBLE_DECREASE_TRUSTED_PRESENT_DENIED"
            )

    return TreasuryExternalCapitalDecreaseS2AdmissionContractV1(
        contract_satisfied=True,
        fail_closed=fail_closed,
        optimistic_restore_denied=True,
        capital_increase_denied=True,
        reason_codes=tuple(dict.fromkeys(reasons)),
        join_seam_id=JOIN_SEAM_ID,
    )
