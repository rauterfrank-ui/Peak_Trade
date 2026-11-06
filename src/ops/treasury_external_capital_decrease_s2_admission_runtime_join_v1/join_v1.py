"""Join S1 decrease observations into the productive capital admission runtime seam."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CAPITAL_ADMISSION_AUTHORITY,
    CapitalAdmissionEvidenceV1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
)
from src.ops.treasury_external_capital_decrease_s2_admission_runtime_join_v1.constants_v1 import (
    CAPITAL_ADMISSION_OWNER,
    JOIN_SEAM_ID,
    PARALLEL_CAPITAL_AUTHORITY_ADDED,
    SECOND_CAPITAL_AUTHORITY_ADDED,
)
from src.ops.treasury_external_capital_decrease_s2_admission_runtime_join_v1.contract_v1 import (
    evaluate_treasury_external_capital_decrease_s2_admission_contract_v1,
)
from src.ops.treasury_external_capital_decrease_s2_admission_runtime_join_v1.errors_v1 import (
    TreasuryExternalCapitalDecreaseS2AdmissionError,
)
from src.ops.treasury_external_capital_decrease_s2_admission_runtime_join_v1.models_v1 import (
    TreasuryExternalCapitalDecreaseAdmissionRuntimeJoinV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.join_v1 import (
    join_treasury_reconciliation_into_capital_admission_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryVenueObservationV1,
)


def join_treasury_external_capital_decrease_into_capital_admission_runtime_v1(
    observation: TreasuryVenueObservationV1,
    *,
    expected_account_identity: str,
    expected_instrument_id: str,
    admission_context: str = ADMISSION_CONTEXT_LIVE,
) -> TreasuryExternalCapitalDecreaseAdmissionRuntimeJoinV1:
    """Reuse Phase-2 capital admission join; S2 contract is conjunct-only, not owner."""
    if PARALLEL_CAPITAL_AUTHORITY_ADDED or SECOND_CAPITAL_AUTHORITY_ADDED:
        raise TreasuryExternalCapitalDecreaseS2AdmissionError("PARALLEL_CAPITAL_AUTHORITY_DENIED")
    if CAPITAL_ADMISSION_OWNER != CAPITAL_ADMISSION_AUTHORITY:
        raise TreasuryExternalCapitalDecreaseS2AdmissionError("CAPITAL_ADMISSION_AUTHORITY_DRIFT")

    treasury_join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=expected_account_identity,
        expected_instrument_id=expected_instrument_id,
        admission_context=admission_context,
    )
    if treasury_join.capital_admission_authority != CAPITAL_ADMISSION_AUTHORITY:
        raise TreasuryExternalCapitalDecreaseS2AdmissionError("TREASURY_JOIN_AUTHORITY_DRIFT")

    contract = evaluate_treasury_external_capital_decrease_s2_admission_contract_v1(
        observation=observation,
        treasury_join=treasury_join,
    )
    evidence = treasury_join.capital_admission_evidence
    if not isinstance(evidence, CapitalAdmissionEvidenceV1):
        raise TreasuryExternalCapitalDecreaseS2AdmissionError(
            "CAPITAL_ADMISSION_EVIDENCE_TYPE_INVALID"
        )

    return TreasuryExternalCapitalDecreaseAdmissionRuntimeJoinV1(
        contract=contract,
        treasury_join=treasury_join,
        capital_admission_evidence=evidence,
        join_seam_id=JOIN_SEAM_ID,
        capital_admission_authority=CAPITAL_ADMISSION_AUTHORITY,
    )
