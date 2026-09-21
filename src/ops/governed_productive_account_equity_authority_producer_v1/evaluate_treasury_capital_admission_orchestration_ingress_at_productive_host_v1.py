"""Evaluate E4 orchestration ingress at the governed productive account-equity host.

Consumer-only: transports Treasury capital-admission/orchestration ingress into the
canonical account-equity authority host boundary. Does not mint equity, sizing, or
risk-admissible capital. Does not GET or POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED,
    GOVERNED_PRODUCER_CREATED,
    STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.constants_v1 import (
    AVAILABLE_FOR_SIZING_MINT_AUTHORIZED,
    JOIN_SEAM_ID,
    RISK_ADMISSIBLE_MINT_AUTHORIZED,
    SIZING_AUTHORITY_CHANGED,
    STEP_29P_MINT_AUTHORIZED,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.errors_v1 import (
    TreasuryE4ProductiveHostJoinError,
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


def evaluate_treasury_capital_admission_orchestration_ingress_at_productive_host_v1(
    orchestration_join: TreasuryAccountEquityOrchestrationJoinV1,
    *,
    usdc_row_status: str = "",
) -> ProductiveHostTreasuryCapitalAdmissionEvaluationV1:
    """Productive host ingress evaluation — transport only, fail-closed by default."""
    if RISK_ADMISSIBLE_MINT_AUTHORIZED or STEP_29P_MINT_AUTHORIZED:
        raise TreasuryE4ProductiveHostJoinError("DOWNSTREAM_MINT_FORBIDDEN")
    if AVAILABLE_FOR_SIZING_MINT_AUTHORIZED or SIZING_AUTHORITY_CHANGED:
        raise TreasuryE4ProductiveHostJoinError("SIZING_AUTHORITY_CHANGE_FORBIDDEN")
    if CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED is True or GOVERNED_PRODUCER_CREATED is True:
        raise TreasuryE4ProductiveHostJoinError("PARALLEL_EQUITY_PRODUCER_MINT_FORBIDDEN")
    if STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER is not True:
        raise TreasuryE4ProductiveHostJoinError("STEP_29P_EQUITY_AUTHORITY_DRIFT")

    assert_orchestration_never_mints_sizing_or_step_29p_v1(orchestration_join)
    ingress = orchestration_join.ingress
    if ingress.account_equity_authority != ACCOUNT_EQUITY_AUTHORITY_OWNER:
        raise TreasuryE4ProductiveHostJoinError("ACCOUNT_EQUITY_AUTHORITY_DRIFT")

    reconciliation_status = str(ingress.treasury_reconciliation_class)
    orchestration_admitted = ingress.orchestration_admitted is True and ingress.fail_closed is False
    fail_closed = ingress.fail_closed is True or not orchestration_admitted

    reasons = list(ingress.reason_codes)
    if fail_closed:
        reasons.append("PRODUCTIVE_HOST_TREASURY_CAPITAL_ADMISSION_FAIL_CLOSED")
    else:
        reasons.append("PRODUCTIVE_HOST_ORCHESTRATION_INGRESS_CONSUMED")
    reasons.append("TREASURY_CAPITAL_NOT_ADMITTED_TO_SIZING_OR_EXECUTION")

    return ProductiveHostTreasuryCapitalAdmissionEvaluationV1(
        productive_host_reachable=True,
        fail_closed=fail_closed,
        orchestration_ingress_admitted=orchestration_admitted,
        treasury_capital_admitted=False,
        observed_equity_minted=False,
        reconciled_equity_minted=False,
        risk_admissible_mint=False,
        sizing_authority_changed=False,
        treasury_reconciliation_status=reconciliation_status,
        usdc_row_status=str(usdc_row_status or ""),
        reason_codes=tuple(dict.fromkeys(reasons)),
        join_seam_id=JOIN_SEAM_ID,
        account_equity_authority=ACCOUNT_EQUITY_AUTHORITY_OWNER,
        e4_join_seam_id=str(ingress.join_seam_id),
        capital_admission_authority=str(ingress.capital_admission_authority),
    )
