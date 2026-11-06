"""Bind productive read-only funding balance GET to TreasuryVenueObservationV1.

Reuses offline_funding_balance_read_producer_v1 GET transport. Does not mint
AVAILABLE_FOR_SIZING, STEP_29P, or capital admission evidence. Deposit-history
semantics are supplied only via TreasuryCapitalDepositObservationContextV1.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping

from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    OBSERVATION_CLASS_SUCCESS,
    FundingAccountBalanceObservationV1,
    row_for_ccy_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.producer_v1 import (
    build_offline_funding_balance_read_client_v1,
    observe_funding_account_balances_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryTransportV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryFreshnessSignalV1,
    TreasuryVenueObservationV1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.constants_v1 import (
    EDGE_SEAM_ID,
    TREASURY_CAPITAL_CCY,
    VENUE_BALANCE_FIELD,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.context_v1 import (
    TreasuryCapitalDepositObservationContextV1,
    validate_treasury_capital_deposit_observation_context_v1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.errors_v1 import (
    TreasuryPhase2VenueObservationBindingError,
)


def _canonical_json_v1(payload: dict[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def treasury_venue_observation_evidence_fingerprint_v1(
    *,
    funding: FundingAccountBalanceObservationV1,
    context: TreasuryCapitalDepositObservationContextV1,
) -> str:
    material = {
        "edge_seam_id": EDGE_SEAM_ID,
        "evidence_id": str(context.evidence_id),
        "account_identity": str(context.account_identity),
        "instrument_id": str(context.instrument_id),
        "funding_body_sha256": str(funding.body_sha256),
        "deposit_history_freshness": str(context.deposit_history_freshness),
        "deposit_history_confirms_increase": str(context.deposit_history_confirms_increase),
        "internal_transfer_signal": str(context.internal_transfer_signal),
        "external_depletion_signal": str(context.external_depletion_signal),
        "prior_reconciled_capital_raw": str(context.prior_reconciled_capital_raw),
        "cached_trading_capital_raw": str(context.cached_trading_capital_raw),
        "venue_balance_field": VENUE_BALANCE_FIELD,
    }
    return hashlib.sha256(_canonical_json_v1(material).encode("utf-8")).hexdigest()


def map_funding_balance_to_treasury_venue_balance_raw_v1(
    funding: FundingAccountBalanceObservationV1,
    *,
    capital_ccy: str = TREASURY_CAPITAL_CCY,
) -> str:
    if funding.observation_class != OBSERVATION_CLASS_SUCCESS:
        return ""
    row = row_for_ccy_v1(funding, capital_ccy)
    if row is None:
        return ""
    return str(row.avail_bal_raw)


def resolve_balance_freshness_from_funding_v1(
    funding: FundingAccountBalanceObservationV1,
    *,
    context: TreasuryCapitalDepositObservationContextV1,
) -> str:
    override = str(context.balance_freshness_override or "").strip()
    if override:
        return override
    if funding.observation_class == OBSERVATION_CLASS_SUCCESS and funding.get_performed:
        return TreasuryFreshnessSignalV1.FRESH.value
    return TreasuryFreshnessSignalV1.UNKNOWN.value


def build_treasury_venue_observation_from_funding_balance_v1(
    funding: FundingAccountBalanceObservationV1,
    context: TreasuryCapitalDepositObservationContextV1,
) -> TreasuryVenueObservationV1:
    validate_treasury_capital_deposit_observation_context_v1(context)
    venue_balance_raw = map_funding_balance_to_treasury_venue_balance_raw_v1(funding)
    balance_freshness = resolve_balance_freshness_from_funding_v1(funding, context=context)
    fingerprint = treasury_venue_observation_evidence_fingerprint_v1(
        funding=funding,
        context=context,
    )
    return TreasuryVenueObservationV1(
        evidence_id=str(context.evidence_id),
        evidence_fingerprint=fingerprint,
        observed_at_utc=str(funding.observed_at_utc),
        account_identity=str(context.account_identity),
        instrument_id=str(context.instrument_id),
        venue_balance_raw=venue_balance_raw,
        balance_freshness=balance_freshness,
        deposit_history_freshness=str(context.deposit_history_freshness),
        deposit_history_confirms_increase=bool(context.deposit_history_confirms_increase),
        internal_transfer_signal=str(context.internal_transfer_signal),
        external_depletion_signal=str(context.external_depletion_signal),
        prior_reconciled_capital_raw=str(context.prior_reconciled_capital_raw),
        cached_trading_capital_raw=str(context.cached_trading_capital_raw),
        phase1_lifecycle_state=str(context.phase1_lifecycle_state),
    )


def produce_treasury_venue_observation_via_funding_balance_get_v1(
    *,
    transport: LiveCanaryTransportV1,
    context: TreasuryCapitalDepositObservationContextV1,
    headers: Mapping[str, str] | None = None,
) -> TreasuryVenueObservationV1:
    """Exactly one allowlisted funding balance GET, then typed Treasury observation."""
    validate_treasury_capital_deposit_observation_context_v1(context)
    if transport is None:
        raise TreasuryPhase2VenueObservationBindingError("FUNDING_BALANCE_TRANSPORT_REQUIRED")
    client = build_offline_funding_balance_read_client_v1(transport=transport)
    funding = observe_funding_account_balances_v1(client=client, headers=headers)
    return build_treasury_venue_observation_from_funding_balance_v1(funding, context)
