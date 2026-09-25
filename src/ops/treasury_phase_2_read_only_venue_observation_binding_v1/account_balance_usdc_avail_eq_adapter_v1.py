"""Build TreasuryVenueObservationV1 from one trusted account-balance USDC availEq read.

Single-source delegation: the margin observation is the only venue numeric read.
Does not perform HTTP. Does not mint sizing authority.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping

from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryDepositHistorySignalV1,
    TreasuryExternalDepletionSignalV1,
    TreasuryFreshnessSignalV1,
    TreasuryInternalTransferSignalV1,
    TreasuryVenueObservationV1,
)

SCHEMA_CLASS = "TREASURY_ACCOUNT_BALANCE_USDC_AVAIL_EQ_ADAPTER_V1"
CONTRACT_VERSION = "v1"


def _digest(payload: Mapping[str, str]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_treasury_venue_observation_from_trusted_account_balance_usdc_avail_eq_v1(
    *,
    avail_eq_raw: str,
    account_identity: str,
    instrument_id: str,
    observed_at_utc: str,
    body_sha256: str,
    decision_epoch: str,
) -> TreasuryVenueObservationV1:
    """Stable reconciled candidacy when prior reconciled equals fresh trusted availEq."""
    value = str(avail_eq_raw or "").strip()
    if value == "":
        raise ValueError("AVAIL_EQ_RAW_MISSING")
    account = str(account_identity or "").strip()
    instrument = str(instrument_id or "").strip()
    observed = str(observed_at_utc or "").strip()
    epoch = str(decision_epoch or "").strip()
    if account == "" or instrument == "" or observed == "" or epoch == "":
        raise ValueError("TREASURY_ADAPTER_SCOPE_MISSING")
    fingerprint = str(body_sha256 or "").strip().lower()
    if len(fingerprint) != 64:
        fingerprint = _digest(
            {
                "avail_eq": value,
                "account": account,
                "instrument": instrument,
                "epoch": epoch,
                "observed": observed,
            }
        )
    evidence_id = _digest(
        {
            "class": SCHEMA_CLASS,
            "fingerprint": fingerprint,
            "epoch": epoch,
            "account": account,
        }
    )
    return TreasuryVenueObservationV1(
        evidence_id=evidence_id,
        evidence_fingerprint=fingerprint,
        observed_at_utc=observed,
        account_identity=account,
        instrument_id=instrument,
        venue_balance_raw=value,
        balance_freshness=TreasuryFreshnessSignalV1.FRESH.value,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.MISSING.value,
        deposit_history_confirms_increase=False,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
        prior_reconciled_capital_raw=value,
        cached_trading_capital_raw=value,
    )


__all__ = (
    "CONTRACT_VERSION",
    "SCHEMA_CLASS",
    "build_treasury_venue_observation_from_trusted_account_balance_usdc_avail_eq_v1",
)
