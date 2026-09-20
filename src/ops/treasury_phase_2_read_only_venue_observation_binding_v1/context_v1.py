"""Typed deposit/capital context for Phase-2 venue observation. Not inferred from balance alone."""

from __future__ import annotations

from dataclasses import dataclass

from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryDepositHistorySignalV1,
    TreasuryExternalDepletionSignalV1,
    TreasuryFreshnessSignalV1,
    TreasuryInternalTransferSignalV1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.constants_v1 import (
    OBSERVED_BALANCE_ALONE_CONFIRMS_DEPOSIT,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.errors_v1 import (
    TreasuryPhase2VenueObservationBindingError,
)


@dataclass(frozen=True)
class TreasuryCapitalDepositObservationContextV1:
    """Signals that funding balance GET cannot mint (deposit history, prior capital, depletion)."""

    evidence_id: str
    account_identity: str
    instrument_id: str
    deposit_history_freshness: str
    deposit_history_confirms_increase: bool
    internal_transfer_signal: str = TreasuryInternalTransferSignalV1.UNKNOWN.value
    external_depletion_signal: str = TreasuryExternalDepletionSignalV1.NONE.value
    prior_reconciled_capital_raw: str = ""
    cached_trading_capital_raw: str = ""
    balance_freshness_override: str = ""
    phase1_lifecycle_state: str = ""


def validate_treasury_capital_deposit_observation_context_v1(
    context: TreasuryCapitalDepositObservationContextV1,
) -> None:
    if OBSERVED_BALANCE_ALONE_CONFIRMS_DEPOSIT is True:
        raise TreasuryPhase2VenueObservationBindingError(
            "OBSERVED_BALANCE_ALONE_CONFIRMS_DEPOSIT_FORBIDDEN"
        )
    if not str(context.evidence_id or "").strip():
        raise TreasuryPhase2VenueObservationBindingError("EVIDENCE_ID_REQUIRED")
    if not str(context.account_identity or "").strip():
        raise TreasuryPhase2VenueObservationBindingError("ACCOUNT_IDENTITY_REQUIRED")
    if not str(context.instrument_id or "").strip():
        raise TreasuryPhase2VenueObservationBindingError("INSTRUMENT_ID_REQUIRED")

    history = str(context.deposit_history_freshness or TreasuryDepositHistorySignalV1.UNKNOWN.value)
    if (
        context.deposit_history_confirms_increase
        and history != TreasuryDepositHistorySignalV1.CONFIRMED.value
    ):
        raise TreasuryPhase2VenueObservationBindingError(
            "DEPOSIT_INCREASE_CONFIRM_REQUIRES_CONFIRMED_HISTORY"
        )

    override = str(context.balance_freshness_override or "").strip()
    if override and override not in {member.value for member in TreasuryFreshnessSignalV1}:
        raise TreasuryPhase2VenueObservationBindingError("BALANCE_FRESHNESS_OVERRIDE_INVALID")
