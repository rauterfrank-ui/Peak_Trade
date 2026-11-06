"""Typed Phase-2 read-only reconciliation models. Distinct from Phase-1 lifecycle names."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class TreasuryFreshnessSignalV1(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class TreasuryDepositHistorySignalV1(str, Enum):
    CONFIRMED = "CONFIRMED"
    UNCONFIRMED = "UNCONFIRMED"
    STALE = "STALE"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


class TreasuryInternalTransferSignalV1(str, Enum):
    CLEAR = "CLEAR"
    DEBIT_BEFORE_CREDIT_UNSETTLED = "DEBIT_BEFORE_CREDIT_UNSETTLED"
    UNKNOWN = "UNKNOWN"


class TreasuryExternalDepletionSignalV1(str, Enum):
    NONE = "NONE"
    CREDIBLE_DEPLETION = "CREDIBLE_DEPLETION"
    UNKNOWN = "UNKNOWN"


class TreasuryReconciliationClassV1(str, Enum):
    """Phase-2 reconciliation class. Not a Phase-1 lifecycle alias."""

    OBSERVED = "OBSERVED"
    RECONCILED = "RECONCILED"
    AMBIGUOUS = "AMBIGUOUS"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class TreasuryVenueObservationV1:
    evidence_id: str
    evidence_fingerprint: str
    observed_at_utc: str
    account_identity: str
    instrument_id: str
    venue_balance_raw: str
    balance_freshness: str
    deposit_history_freshness: str
    deposit_history_confirms_increase: bool
    internal_transfer_signal: str
    external_depletion_signal: str
    prior_reconciled_capital_raw: str = ""
    cached_trading_capital_raw: str = ""
    phase1_lifecycle_state: str = ""


@dataclass(frozen=True)
class TreasuryReconciliationEvaluationV1:
    reconciliation_class: str
    capital_increase_authority: bool
    fail_closed: bool
    reason_codes: Tuple[str, ...]
    evidence_id: str
    evidence_fingerprint: str
    observed_at_utc: str
    join_seam_id: str
    authority: str


@dataclass(frozen=True)
class TreasuryCapitalAdmissionJoinV1:
    reconciliation: TreasuryReconciliationEvaluationV1
    capital_admission_evidence: object
    treasury_reason_codes: Tuple[str, ...]
    join_seam_id: str
    capital_admission_authority: str
