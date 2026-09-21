"""Typed CURRENT_PRODUCTIVE BASE observation (non-eq, non-stock, USDC).

Wraps Treasury Phase-2 reconciled venue balance numeric evidence for the CT
producer BASE slot. Does not mint risk-admissible capital or AVAILABLE_FOR_SIZING.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    NUMERIC_EQUITY_TTL_SECONDS,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    REQUIRED_SETTLEMENT_CURRENCY,
)
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO,
    CURRENCY_ROW_STATUS_PRESENT,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryFreshnessSignalV1,
    TreasuryReconciliationClassV1,
    TreasuryVenueObservationV1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.constants_v1 import (
    TREASURY_CAPITAL_CCY,
    VENUE_BALANCE_FIELD,
)

SCHEMA_CLASS = "NON_FORBIDDEN_NON_EQ_NON_STOCK_USDC_CURRENT_PRODUCTIVE_OBSERVATION_V1"
CONTRACT_VERSION = "v1"
OUTPUT_UNIT = "USDC_ACCOUNT_EQUITY"
UPSTREAM_OBSERVED_FIELD_NAME = "treasury_phase_2_reconciled_venue_balance"
UPSTREAM_VENUE_FIELD = VENUE_BALANCE_FIELD
REQUIRED_TD_MODE = "cross"
REQUIRED_ACCOUNT_MODE = "FUTURES_MODE"

_FORBIDDEN_SOURCE_MARKERS = (
    "availeq",
    "totaleq",
    "adjeq",
    "availbal",
    "cashbal",
    "frozenbal",
    "isoeq",
    "ordfrozen",
    "eq",
    "upl",
    "kind_set",
)
_SCIENTIFIC = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)[eE][+-]?\d+$")


class NonForbiddenUsdcCurrentProductiveObservationError(ValueError):
    """Fail-closed typed BASE observation violation."""


@dataclass(frozen=True)
class NonForbiddenNonEqNonStockUsdcCurrentProductiveObservationV1:
    schema_class: str
    value_raw: str
    settlement_currency: str
    output_unit: str
    bound_account_identity: str
    bound_venue_identity: str
    bound_td_mode: str
    decision_epoch: str
    observed_at_as_of: str
    age_seconds: str
    freshness_max_age: str
    provenance_digest: str
    upstream_observed_field_name: str
    upstream_venue_field: str
    treasury_reconciliation_class: str
    usdc_row_status: str
    evidence_id: str
    evidence_fingerprint: str


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _parse_non_negative_decimal(raw: str, *, field: str) -> Decimal | None:
    text = str(raw or "").strip()
    if text == "" or text != str(raw):
        return None
    if _SCIENTIFIC.fullmatch(text):
        return None
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite() or value < 0:
        return None
    _ = field
    return value


def _parse_age_seconds(raw: str) -> int | None:
    text = str(raw or "").strip()
    if text == "" or text != str(raw):
        return None
    try:
        age = int(text)
    except ValueError:
        return None
    if str(age) != text or age < 0:
        return None
    return age


def reject_forbidden_upstream_field_name_v1(*, field_name: str) -> None:
    folded = str(field_name or "").strip().lower().replace("_", "").replace("-", "")
    if not folded:
        raise NonForbiddenUsdcCurrentProductiveObservationError("UPSTREAM_FIELD_NAME_MISSING")
    if folded in _FORBIDDEN_SOURCE_MARKERS or any(m in folded for m in _FORBIDDEN_SOURCE_MARKERS):
        raise NonForbiddenUsdcCurrentProductiveObservationError(
            f"UPSTREAM_FIELD_NAME_FORBIDDEN:{field_name}"
        )


def build_non_forbidden_usdc_current_productive_observation_from_treasury_v1(
    *,
    observation: TreasuryVenueObservationV1,
    usdc_row_status: str,
    treasury_reconciliation_class: str,
    bound_account_identity: str,
    bound_venue_identity: str,
    bound_td_mode: str,
    decision_epoch: str,
    age_seconds: str,
    freshness_max_age: str,
) -> NonForbiddenNonEqNonStockUsdcCurrentProductiveObservationV1:
    """Materialize typed observation from reconciled Treasury venue balance only."""
    reject_forbidden_upstream_field_name_v1(field_name=UPSTREAM_OBSERVED_FIELD_NAME)
    if treasury_reconciliation_class != TreasuryReconciliationClassV1.RECONCILED.value:
        raise NonForbiddenUsdcCurrentProductiveObservationError(
            "OBSERVATION_REQUIRES_RECONCILED_TREASURY_CLASS"
        )
    if str(usdc_row_status or "") == CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO:
        raise NonForbiddenUsdcCurrentProductiveObservationError("USDC_ROW_ABSENT_NOT_ZERO")
    if str(usdc_row_status or "") != CURRENCY_ROW_STATUS_PRESENT:
        raise NonForbiddenUsdcCurrentProductiveObservationError("USDC_ROW_STATUS_NOT_PRESENT")
    if str(observation.balance_freshness or "") != TreasuryFreshnessSignalV1.FRESH.value:
        raise NonForbiddenUsdcCurrentProductiveObservationError("TREASURY_BALANCE_NOT_FRESH")
    if bound_account_identity != str(observation.account_identity or ""):
        raise NonForbiddenUsdcCurrentProductiveObservationError("ACCOUNT_IDENTITY_MISMATCH")
    if bound_td_mode != REQUIRED_TD_MODE:
        raise NonForbiddenUsdcCurrentProductiveObservationError("TD_MODE_NOT_CROSS")
    value_raw = str(observation.venue_balance_raw or "").strip()
    if _parse_non_negative_decimal(value_raw, field="venue_balance_raw") is None:
        raise NonForbiddenUsdcCurrentProductiveObservationError("NUMERIC_VALUE_INVALID")
    age = _parse_age_seconds(age_seconds)
    max_age = _parse_age_seconds(freshness_max_age)
    if age is None or max_age is None:
        raise NonForbiddenUsdcCurrentProductiveObservationError("FRESHNESS_UNKNOWN")
    if age > max_age or age > NUMERIC_EQUITY_TTL_SECONDS or max_age > NUMERIC_EQUITY_TTL_SECONDS:
        raise NonForbiddenUsdcCurrentProductiveObservationError("OBSERVATION_STALE")
    epoch = str(decision_epoch or "").strip()
    observed_at = str(observation.observed_at_utc or "").strip()
    if epoch == "" or observed_at == "":
        raise NonForbiddenUsdcCurrentProductiveObservationError("EPOCH_MISSING")
    digest = hashlib.sha256(
        _canonical_json(
            {
                "schema_class": SCHEMA_CLASS,
                "upstream_observed_field_name": UPSTREAM_OBSERVED_FIELD_NAME,
                "upstream_venue_field": UPSTREAM_VENUE_FIELD,
                "capital_ccy": TREASURY_CAPITAL_CCY,
                "value_raw": value_raw,
                "evidence_id": str(observation.evidence_id or ""),
                "evidence_fingerprint": str(observation.evidence_fingerprint or ""),
                "account_identity": bound_account_identity,
                "decision_epoch": epoch,
            }
        ).encode("utf-8")
    ).hexdigest()
    return NonForbiddenNonEqNonStockUsdcCurrentProductiveObservationV1(
        schema_class=SCHEMA_CLASS,
        value_raw=value_raw,
        settlement_currency=REQUIRED_SETTLEMENT_CURRENCY,
        output_unit=OUTPUT_UNIT,
        bound_account_identity=bound_account_identity,
        bound_venue_identity=bound_venue_identity,
        bound_td_mode=bound_td_mode,
        decision_epoch=epoch,
        observed_at_as_of=observed_at,
        age_seconds=str(age),
        freshness_max_age=str(max_age),
        provenance_digest=digest,
        upstream_observed_field_name=UPSTREAM_OBSERVED_FIELD_NAME,
        upstream_venue_field=UPSTREAM_VENUE_FIELD,
        treasury_reconciliation_class=treasury_reconciliation_class,
        usdc_row_status=str(usdc_row_status),
        evidence_id=str(observation.evidence_id or ""),
        evidence_fingerprint=str(observation.evidence_fingerprint or ""),
    )


__all__ = (
    "NonForbiddenNonEqNonStockUsdcCurrentProductiveObservationV1",
    "NonForbiddenUsdcCurrentProductiveObservationError",
    "OUTPUT_UNIT",
    "SCHEMA_CLASS",
    "UPSTREAM_OBSERVED_FIELD_NAME",
    "UPSTREAM_VENUE_FIELD",
    "build_non_forbidden_usdc_current_productive_observation_from_treasury_v1",
    "reject_forbidden_upstream_field_name_v1",
)
