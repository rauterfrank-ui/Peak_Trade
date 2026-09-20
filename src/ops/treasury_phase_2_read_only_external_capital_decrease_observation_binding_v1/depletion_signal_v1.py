"""Map typed decrease context to TreasuryExternalDepletionSignalV1. No balance-only crediting."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from src.ops.treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1.context_v1 import (
    TreasuryExternalCapitalDecreaseObservationContextV1,
    TreasuryWithdrawalHistorySignalV1,
)
from src.ops.treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1.errors_v1 import (
    TreasuryExternalCapitalDecreaseObservationBindingError,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryExternalDepletionSignalV1,
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


def resolve_external_depletion_signal_for_decrease_context_v1(
    context: TreasuryExternalCapitalDecreaseObservationContextV1,
    *,
    venue_balance_raw: str,
) -> str:
    """Conservative mapping: CREDIBLE_DEPLETION only with confirmed withdrawal history + lower venue."""
    history = str(
        context.withdrawal_history_freshness or TreasuryWithdrawalHistorySignalV1.UNKNOWN.value
    )
    if history == TreasuryWithdrawalHistorySignalV1.UNKNOWN.value:
        return TreasuryExternalDepletionSignalV1.UNKNOWN.value
    if history in {
        TreasuryWithdrawalHistorySignalV1.UNCONFIRMED.value,
        TreasuryWithdrawalHistorySignalV1.STALE.value,
    }:
        return TreasuryExternalDepletionSignalV1.NONE.value
    if history == TreasuryWithdrawalHistorySignalV1.MISSING.value:
        return TreasuryExternalDepletionSignalV1.NONE.value

    if history != TreasuryWithdrawalHistorySignalV1.CONFIRMED.value:
        return TreasuryExternalDepletionSignalV1.UNKNOWN.value

    if not context.withdrawal_history_confirms_decrease:
        return TreasuryExternalDepletionSignalV1.NONE.value

    venue = _parse_amount(venue_balance_raw)
    prior = _parse_amount(context.prior_reconciled_capital_raw)
    if venue is None or prior is None:
        raise TreasuryExternalCapitalDecreaseObservationBindingError(
            "CREDIBLE_DEPLETION_REQUIRES_PARSEABLE_VENUE_AND_PRIOR"
        )
    if venue >= prior:
        raise TreasuryExternalCapitalDecreaseObservationBindingError(
            "WITHDRAWAL_HISTORY_CONFIRMED_BUT_VENUE_NOT_LOWER_THAN_PRIOR"
        )
    return TreasuryExternalDepletionSignalV1.CREDIBLE_DEPLETION.value
