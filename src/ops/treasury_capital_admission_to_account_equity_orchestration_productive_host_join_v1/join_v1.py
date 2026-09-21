"""Wire Treasury observation → Phase-2 → E4 → governed productive account-equity host."""

from __future__ import annotations

from src.ops.governed_productive_account_equity_authority_producer_v1.evaluate_treasury_capital_admission_orchestration_ingress_at_productive_host_v1 import (
    evaluate_treasury_capital_admission_orchestration_ingress_at_productive_host_v1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.constants_v1 import (
    CAPITAL_ADMISSION_OWNER,
    JOIN_SEAM_ID,
    PARALLEL_ACCOUNT_EQUITY_AUTHORITY_ADDED,
    SECOND_ACCOUNT_EQUITY_AUTHORITY_ADDED,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.errors_v1 import (
    TreasuryE4ProductiveHostJoinError,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.models_v1 import (
    TreasuryE4ProductiveHostJoinResultV1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_v1.join_v1 import (
    join_treasury_capital_admission_into_account_equity_orchestration_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.join_v1 import (
    join_treasury_reconciliation_into_capital_admission_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryVenueObservationV1,
)


def join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
    observation: TreasuryVenueObservationV1,
    *,
    expected_account_identity: str,
    expected_instrument_id: str,
    usdc_row_status: str = "",
) -> TreasuryE4ProductiveHostJoinResultV1:
    """Full E4 productive host join chain. No network. No authority expansion."""
    if PARALLEL_ACCOUNT_EQUITY_AUTHORITY_ADDED or SECOND_ACCOUNT_EQUITY_AUTHORITY_ADDED:
        raise TreasuryE4ProductiveHostJoinError("PARALLEL_ACCOUNT_EQUITY_AUTHORITY_DENIED")

    treasury_join = join_treasury_reconciliation_into_capital_admission_v1(
        observation,
        expected_account_identity=expected_account_identity,
        expected_instrument_id=expected_instrument_id,
    )
    if treasury_join.capital_admission_authority != CAPITAL_ADMISSION_OWNER:
        raise TreasuryE4ProductiveHostJoinError("CAPITAL_ADMISSION_AUTHORITY_DRIFT")

    orchestration_join = join_treasury_capital_admission_into_account_equity_orchestration_v1(
        treasury_join
    )
    host_evaluation = (
        evaluate_treasury_capital_admission_orchestration_ingress_at_productive_host_v1(
            orchestration_join,
            usdc_row_status=usdc_row_status,
        )
    )

    return TreasuryE4ProductiveHostJoinResultV1(
        treasury_join=treasury_join,
        orchestration_join=orchestration_join,
        host_evaluation=host_evaluation,
        join_seam_id=JOIN_SEAM_ID,
    )
