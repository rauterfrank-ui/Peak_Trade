"""Join Treasury read-only reconciliation into capital_admission_contract_v1."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CAPITAL_ADMISSION_AUTHORITY,
    CapitalAdmissionClaimV1,
    EVIDENCE_CLASS_LIVE_TYPED,
    evaluate_capital_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE,
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
    CAPITAL_SOURCE_OBSERVED_VENUE,
    CapitalAdmissionStatusV1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
    RISK_ADMISSIBLE_GRANTED,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.constants_v1 import (
    JOIN_SEAM_ID,
    RISK_ADMISSIBLE_MINT_AUTHORIZED,
    SECOND_CAPITAL_AUTHORITY_ADDED,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.errors_v1 import (
    TreasuryPhase2ReconciliationError,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryCapitalAdmissionJoinV1,
    TreasuryReconciliationClassV1,
    TreasuryVenueObservationV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.reconciliation_v1 import (
    evaluate_treasury_read_only_reconciliation_v1,
)

EVIDENCE_CLASS_TREASURY_PHASE_2 = "TREASURY_PHASE_2_READ_ONLY_TYPED"


def _treasury_join_denied_claim(
    observation: TreasuryVenueObservationV1,
    *,
    observed_capital_raw: str,
) -> CapitalAdmissionClaimV1:
    return CapitalAdmissionClaimV1(
        source_class=CAPITAL_SOURCE_OBSERVED_VENUE,
        account_identity=str(observation.account_identity),
        instrument_id=str(observation.instrument_id),
        observed_capital_raw=observed_capital_raw,
        observed_field_name="treasury_phase_2_venue_balance",
        previously_admitted_risk_capital=str(observation.prior_reconciled_capital_raw or ""),
        evidence_class=EVIDENCE_CLASS_TREASURY_PHASE_2,
        evidence_id=str(observation.evidence_id),
    )


def join_treasury_reconciliation_into_capital_admission_v1(
    observation: TreasuryVenueObservationV1,
    *,
    expected_account_identity: str,
    expected_instrument_id: str,
    admission_context: str = ADMISSION_CONTEXT_LIVE,
) -> TreasuryCapitalAdmissionJoinV1:
    if SECOND_CAPITAL_AUTHORITY_ADDED is True:
        raise TreasuryPhase2ReconciliationError("SECOND_CAPITAL_AUTHORITY_DENIED")
    if RISK_ADMISSIBLE_MINT_AUTHORIZED is True or RISK_ADMISSIBLE_GRANTED is True:
        raise TreasuryPhase2ReconciliationError("TREASURY_CANNOT_MINT_RISK_ADMISSIBLE")

    reconciliation = evaluate_treasury_read_only_reconciliation_v1(observation)
    treasury_reasons = tuple(reconciliation.reason_codes)

    recon_class = reconciliation.reconciliation_class
    venue_raw = str(observation.venue_balance_raw or "")

    if recon_class in {
        TreasuryReconciliationClassV1.UNKNOWN.value,
        TreasuryReconciliationClassV1.AMBIGUOUS.value,
    }:
        claim = _treasury_join_denied_claim(observation, observed_capital_raw=venue_raw)
        evidence = evaluate_capital_admission_v1(
            claim=claim,
            expected_account_identity=expected_account_identity,
            expected_instrument_id=expected_instrument_id,
            admission_context=admission_context,
        )
        return TreasuryCapitalAdmissionJoinV1(
            reconciliation=reconciliation,
            capital_admission_evidence=evidence,
            treasury_reason_codes=tuple(
                dict.fromkeys(
                    (
                        *treasury_reasons,
                        "TREASURY_RECONCILIATION_FAIL_CLOSED",
                        "TREASURY_PHASE_2_EVIDENCE_CLASS_NON_PRODUCTIVE_FOR_ADMISSION",
                    )
                )
            ),
            join_seam_id=JOIN_SEAM_ID,
            capital_admission_authority=CAPITAL_ADMISSION_AUTHORITY,
        )

    if recon_class == TreasuryReconciliationClassV1.STALE.value:
        claim = _treasury_join_denied_claim(observation, observed_capital_raw=venue_raw)
        evidence = evaluate_capital_admission_v1(
            claim=claim,
            expected_account_identity=expected_account_identity,
            expected_instrument_id=expected_instrument_id,
            admission_context=admission_context,
        )
        return TreasuryCapitalAdmissionJoinV1(
            reconciliation=reconciliation,
            capital_admission_evidence=evidence,
            treasury_reason_codes=tuple(
                dict.fromkeys((*treasury_reasons, "TREASURY_STALE_FAIL_CLOSED"))
            ),
            join_seam_id=JOIN_SEAM_ID,
            capital_admission_authority=CAPITAL_ADMISSION_AUTHORITY,
        )

    if recon_class == TreasuryReconciliationClassV1.OBSERVED.value:
        claim = _treasury_join_denied_claim(observation, observed_capital_raw=venue_raw)
        evidence = evaluate_capital_admission_v1(
            claim=claim,
            expected_account_identity=expected_account_identity,
            expected_instrument_id=expected_instrument_id,
            admission_context=admission_context,
        )
        extra = ()
        if not reconciliation.capital_increase_authority:
            extra = ("TREASURY_OBSERVED_NO_CAPITAL_INCREASE_AUTHORITY",)
        return TreasuryCapitalAdmissionJoinV1(
            reconciliation=reconciliation,
            capital_admission_evidence=evidence,
            treasury_reason_codes=tuple(dict.fromkeys((*treasury_reasons, *extra))),
            join_seam_id=JOIN_SEAM_ID,
            capital_admission_authority=CAPITAL_ADMISSION_AUTHORITY,
        )

    if recon_class == TreasuryReconciliationClassV1.RECONCILED.value:
        claim = CapitalAdmissionClaimV1(
            source_class=CAPITAL_SOURCE_OBSERVED_VENUE,
            account_identity=str(observation.account_identity),
            instrument_id=str(observation.instrument_id),
            observed_capital_raw=venue_raw,
            observed_field_name="treasury_phase_2_reconciled_venue_balance",
            previously_admitted_risk_capital=str(observation.prior_reconciled_capital_raw or ""),
            evidence_class=EVIDENCE_CLASS_LIVE_TYPED,
            evidence_id=str(observation.evidence_id),
        )
        evidence = evaluate_capital_admission_v1(
            claim=claim,
            expected_account_identity=expected_account_identity,
            expected_instrument_id=expected_instrument_id,
            admission_context=admission_context,
        )
        if evidence.risk_admissible is True:
            raise TreasuryPhase2ReconciliationError("TREASURY_JOIN_MINTED_RISK_ADMISSIBLE")
        if evidence.capital_authority_class == CAPITAL_AUTHORITY_RISK_ADMISSIBLE:
            raise TreasuryPhase2ReconciliationError("TREASURY_JOIN_RISK_ADMISSIBLE_CLASS")
        return TreasuryCapitalAdmissionJoinV1(
            reconciliation=reconciliation,
            capital_admission_evidence=evidence,
            treasury_reason_codes=treasury_reasons,
            join_seam_id=JOIN_SEAM_ID,
            capital_admission_authority=CAPITAL_ADMISSION_AUTHORITY,
        )

    raise TreasuryPhase2ReconciliationError("TREASURY_RECONCILIATION_CLASS_UNKNOWN")


def assert_treasury_join_never_mints_risk_admissible_v1(
    join: TreasuryCapitalAdmissionJoinV1,
) -> bool:
    evidence = join.capital_admission_evidence
    risk = getattr(evidence, "risk_admissible", None)
    authority = getattr(evidence, "capital_authority_class", "")
    if risk is True:
        raise TreasuryPhase2ReconciliationError("TREASURY_JOIN_RISK_ADMISSIBLE_TRUE")
    if authority == CAPITAL_AUTHORITY_RISK_ADMISSIBLE:
        raise TreasuryPhase2ReconciliationError("TREASURY_JOIN_RISK_ADMISSIBLE_AUTHORITY")
    _ = CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE
    if (
        join.reconciliation.capital_increase_authority
        and join.reconciliation.reconciliation_class
        != (TreasuryReconciliationClassV1.RECONCILED.value)
    ):
        raise TreasuryPhase2ReconciliationError("INCREASE_AUTHORITY_DRIFT")
    return False
