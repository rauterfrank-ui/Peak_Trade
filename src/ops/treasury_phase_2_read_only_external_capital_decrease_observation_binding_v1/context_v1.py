"""Typed withdrawal/depletion context for decrease observation. Not inferred from balance."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryFreshnessSignalV1,
    TreasuryInternalTransferSignalV1,
)
from src.ops.treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1.constants_v1 import (
    OBSERVED_BALANCE_ALONE_CONFIRMS_DEPLETION,
    OBSERVED_BALANCE_ALONE_CONFIRMS_EXTERNAL_WITHDRAWAL,
)
from src.ops.treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1.errors_v1 import (
    TreasuryExternalCapitalDecreaseObservationBindingError,
)


class TreasuryWithdrawalHistorySignalV1(str, Enum):
    CONFIRMED = "CONFIRMED"
    UNCONFIRMED = "UNCONFIRMED"
    STALE = "STALE"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class TreasuryExternalCapitalDecreaseObservationContextV1:
    """Signals funding balance GET cannot mint (withdrawal history, prior capital, transfers)."""

    evidence_id: str
    account_identity: str
    instrument_id: str
    withdrawal_history_freshness: str
    withdrawal_history_confirms_decrease: bool
    internal_transfer_signal: str = TreasuryInternalTransferSignalV1.UNKNOWN.value
    prior_reconciled_capital_raw: str = ""
    cached_trading_capital_raw: str = ""
    balance_freshness_override: str = ""
    phase1_lifecycle_state: str = ""


def validate_treasury_external_capital_decrease_observation_context_v1(
    context: TreasuryExternalCapitalDecreaseObservationContextV1,
) -> None:
    if OBSERVED_BALANCE_ALONE_CONFIRMS_DEPLETION is True:
        raise TreasuryExternalCapitalDecreaseObservationBindingError(
            "OBSERVED_BALANCE_ALONE_CONFIRMS_DEPLETION_FORBIDDEN"
        )
    if OBSERVED_BALANCE_ALONE_CONFIRMS_EXTERNAL_WITHDRAWAL is True:
        raise TreasuryExternalCapitalDecreaseObservationBindingError(
            "OBSERVED_BALANCE_ALONE_CONFIRMS_EXTERNAL_WITHDRAWAL_FORBIDDEN"
        )
    if not str(context.evidence_id or "").strip():
        raise TreasuryExternalCapitalDecreaseObservationBindingError("EVIDENCE_ID_REQUIRED")
    if not str(context.account_identity or "").strip():
        raise TreasuryExternalCapitalDecreaseObservationBindingError("ACCOUNT_IDENTITY_REQUIRED")
    if not str(context.instrument_id or "").strip():
        raise TreasuryExternalCapitalDecreaseObservationBindingError("INSTRUMENT_ID_REQUIRED")

    history = str(
        context.withdrawal_history_freshness or TreasuryWithdrawalHistorySignalV1.UNKNOWN.value
    )
    if (
        context.withdrawal_history_confirms_decrease
        and history != TreasuryWithdrawalHistorySignalV1.CONFIRMED.value
    ):
        raise TreasuryExternalCapitalDecreaseObservationBindingError(
            "WITHDRAWAL_DECREASE_CONFIRM_REQUIRES_CONFIRMED_HISTORY"
        )

    override = str(context.balance_freshness_override or "").strip()
    if override and override not in {member.value for member in TreasuryFreshnessSignalV1}:
        raise TreasuryExternalCapitalDecreaseObservationBindingError(
            "BALANCE_FRESHNESS_OVERRIDE_INVALID"
        )
