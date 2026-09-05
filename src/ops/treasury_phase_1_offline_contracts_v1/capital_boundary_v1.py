"""Treasury capital-state boundary. Reuses Capital Admission. Does not mint RISK_ADMISSIBLE."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE,
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
)
from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
    CAPITAL_ADMISSION_AUTHORITY,
    RISK_ADMISSIBLE_GRANTED,
    SECOND_CAPITAL_AUTHORITY_ADDED,
    TREASURY_RECONCILED_IMPLIES_RISK_ADMISSIBLE,
    TERMINAL_VENUE_STATE_IMPLIES_RECONCILED,
)
from src.ops.treasury_phase_1_offline_contracts_v1.errors_v1 import TreasuryPhase1ContractError
from src.ops.treasury_phase_1_offline_contracts_v1.models_v1 import (
    TreasuryCapitalSemanticClassV1,
    TreasuryIntentRecordV1,
    TreasuryLifecycleStateV1,
)

_S = TreasuryLifecycleStateV1


def treasury_state_to_capital_semantic_v1(state: str) -> str:
    if state == _S.ECONOMIC_EFFECT_RECONCILED.value:
        return TreasuryCapitalSemanticClassV1.RECONCILED_CAPITAL.value
    if state == _S.REMOTE_TERMINAL_SUCCESS.value:
        return TreasuryCapitalSemanticClassV1.OBSERVED_CAPITAL.value
    return TreasuryCapitalSemanticClassV1.OBSERVED_CAPITAL.value


def treasury_lifecycle_cannot_mint_risk_admissible_v1(record: TreasuryIntentRecordV1) -> str:
    if SECOND_CAPITAL_AUTHORITY_ADDED is True:
        raise TreasuryPhase1ContractError("SECOND_CAPITAL_AUTHORITY_DENIED")
    if record.capital_admission_authority != CAPITAL_ADMISSION_AUTHORITY:
        raise TreasuryPhase1ContractError("CAPITAL_ADMISSION_AUTHORITY_DRIFT")
    if record.risk_admissible is True or RISK_ADMISSIBLE_GRANTED is True:
        raise TreasuryPhase1ContractError("TREASURY_CANNOT_MINT_RISK_ADMISSIBLE")
    semantic = treasury_state_to_capital_semantic_v1(record.lifecycle_state)
    if semantic == TreasuryCapitalSemanticClassV1.RISK_ADMISSIBLE_CAPITAL.value:
        raise TreasuryPhase1ContractError("TREASURY_STATE_MAPPED_TO_RISK_ADMISSIBLE")
    if (
        record.lifecycle_state == _S.ECONOMIC_EFFECT_RECONCILED.value
        and TREASURY_RECONCILED_IMPLIES_RISK_ADMISSIBLE is True
    ):
        raise TreasuryPhase1ContractError("RECONCILED_MUST_NOT_IMPLY_RISK_ADMISSIBLE")
    if (
        record.lifecycle_state == _S.REMOTE_TERMINAL_SUCCESS.value
        and TERMINAL_VENUE_STATE_IMPLIES_RECONCILED is True
    ):
        raise TreasuryPhase1ContractError("TERMINAL_VENUE_MUST_NOT_IMPLY_RECONCILED")
    if (
        record.capital_semantic_class
        == TreasuryCapitalSemanticClassV1.RISK_ADMISSIBLE_CAPITAL.value
    ):
        raise TreasuryPhase1ContractError("TREASURY_CANNOT_MINT_RISK_ADMISSIBLE")
    if CAPITAL_AUTHORITY_RISK_ADMISSIBLE == record.capital_semantic_class:
        raise TreasuryPhase1ContractError("TREASURY_CANNOT_MINT_RISK_ADMISSIBLE")
    _ = CAPITAL_AUTHORITY_OBSERVED_NOT_RISK_ADMISSIBLE
    return semantic
