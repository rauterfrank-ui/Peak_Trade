"""
Deterministic offline perpetual-futures funding model v1 (RUNBOOK STEP 29M).

Fail-closed binding for funding-rate series, interval-aligned payments, and
funding-drag evidence. No live fetch, no credentials, no implicit zero funding.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from ..core.errors import BacktestError

FUNDING_MODEL_VERSION = "backtest_funding_perpetual_interval_v1"
FUNDING_MODEL_OWNER = "backtest.funding_model_v1"
LONG_SHORT_SIGN_SEMANTICS = "long_pays_positive_rate"
DEFAULT_PAYMENT_INTERVAL_HOURS = 8
FUNDING_RATE_SOURCE_BARS_COLUMN = "bars_funding_rate_column"
FUNDING_APPLICATION_POLICY = "interval_aligned_position_notional"
DEFAULT_RATE_COLUMN = "funding_rate"
MARK_PRICE_COLUMN = "mark_price"

REASON_FUNDING_BOUND = "FUNDING_MODEL_BOUND"
REASON_EXPLICIT_ZERO_RATE = "EXPLICIT_ZERO_FUNDING_RATE"
REASON_MISSING_FUNDING_SERIES = "FUNDING_SERIES_MISSING"
REASON_MISSING_FUNDING_RATE = "FUNDING_RATE_MISSING_AT_PAYMENT"
REASON_DUPLICATE_FUNDING_EVENT = "DUPLICATE_FUNDING_EVENT"
REASON_OUT_OF_ORDER_FUNDING_EVENT = "OUT_OF_ORDER_FUNDING_EVENT"


class FundingModelError(BacktestError):
    """Fail-closed funding model error."""


class FundingRatePresence(str, Enum):
    PRESENT = "PRESENT"
    EXPLICIT_ZERO = "EXPLICIT_ZERO"
    MISSING = "MISSING"


@dataclass(frozen=True)
class FundingModelConfigV1:
    model_version: str
    owner: str
    payment_interval_hours: int
    rate_source: str
    rate_column: str
    mark_price_column: str
    long_short_sign_semantics: str
    funding_application_policy: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_version": self.model_version,
            "owner": self.owner,
            "payment_interval_hours": self.payment_interval_hours,
            "rate_source": self.rate_source,
            "rate_column": self.rate_column,
            "mark_price_column": self.mark_price_column,
            "long_short_sign_semantics": self.long_short_sign_semantics,
            "funding_application_policy": self.funding_application_policy,
        }

    def config_digest(self) -> str:
        return _stable_digest(self.to_dict())


@dataclass(frozen=True)
class FundingPaymentEventV1:
    timestamp: str
    position_sign: int
    mark_price: float
    funding_rate: float
    rate_presence: FundingRatePresence
    notional: float
    payment_amount: float
    payment_index: int


@dataclass(frozen=True)
class FundingDragResultV1:
    model_version: str
    owner: str
    config_digest: str
    data_digest: str
    implementation_digest: str
    total_payment_amount: float
    funding_drag: float
    payment_count: int
    explicit_zero_rate_count: int
    missing_rate_count: int
    payment_events: tuple[FundingPaymentEventV1, ...]
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_version": self.model_version,
            "owner": self.owner,
            "config_digest": self.config_digest,
            "data_digest": self.data_digest,
            "implementation_digest": self.implementation_digest,
            "total_payment_amount": self.total_payment_amount,
            "funding_drag": self.funding_drag,
            "payment_count": self.payment_count,
            "explicit_zero_rate_count": self.explicit_zero_rate_count,
            "missing_rate_count": self.missing_rate_count,
            "payment_events": [
                {
                    "timestamp": event.timestamp,
                    "position_sign": event.position_sign,
                    "mark_price": event.mark_price,
                    "funding_rate": event.funding_rate,
                    "rate_presence": event.rate_presence.value,
                    "notional": event.notional,
                    "payment_amount": event.payment_amount,
                    "payment_index": event.payment_index,
                }
                for event in self.payment_events
            ],
            "reason_codes": list(self.reason_codes),
        }

    def evidence_digest(self) -> str:
        payload = self.to_dict()
        payload.pop("payment_events", None)
        return _stable_digest(payload)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def default_funding_model_config_v1() -> FundingModelConfigV1:
    return FundingModelConfigV1(
        model_version=FUNDING_MODEL_VERSION,
        owner=FUNDING_MODEL_OWNER,
        payment_interval_hours=DEFAULT_PAYMENT_INTERVAL_HOURS,
        rate_source=FUNDING_RATE_SOURCE_BARS_COLUMN,
        rate_column=DEFAULT_RATE_COLUMN,
        mark_price_column=MARK_PRICE_COLUMN,
        long_short_sign_semantics=LONG_SHORT_SIGN_SEMANTICS,
        funding_application_policy=FUNDING_APPLICATION_POLICY,
    )


def load_funding_model_config_v1(cfg: Mapping[str, Any] | None = None) -> FundingModelConfigV1:
    if cfg is None:
        return default_funding_model_config_v1()
    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        return default_funding_model_config_v1()
    funding = backtest.get("funding")
    if funding is None:
        return default_funding_model_config_v1()
    if not isinstance(funding, Mapping):
        raise FundingModelError("backtest_funding_section_not_mapping")
    model_version = str(funding.get("model_version", FUNDING_MODEL_VERSION))
    if model_version != FUNDING_MODEL_VERSION:
        raise FundingModelError(f"funding_model_version_mismatch:{model_version}")
    interval = int(funding.get("payment_interval_hours", DEFAULT_PAYMENT_INTERVAL_HOURS))
    if interval <= 0:
        raise FundingModelError("payment_interval_hours_invalid")
    rate_source = str(funding.get("rate_source", FUNDING_RATE_SOURCE_BARS_COLUMN))
    if rate_source != FUNDING_RATE_SOURCE_BARS_COLUMN:
        raise FundingModelError(f"funding_rate_source_unsupported:{rate_source}")
    rate_column = str(funding.get("rate_column", DEFAULT_RATE_COLUMN))
    mark_column = str(funding.get("mark_price_column", MARK_PRICE_COLUMN))
    return FundingModelConfigV1(
        model_version=model_version,
        owner=str(funding.get("owner", FUNDING_MODEL_OWNER)),
        payment_interval_hours=interval,
        rate_source=rate_source,
        rate_column=rate_column,
        mark_price_column=mark_column,
        long_short_sign_semantics=str(
            funding.get("long_short_sign_semantics", LONG_SHORT_SIGN_SEMANTICS)
        ),
        funding_application_policy=str(
            funding.get("funding_application_policy", FUNDING_APPLICATION_POLICY)
        ),
    )


def funding_binding_requested(cfg: Mapping[str, Any]) -> bool:
    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        return False
    funding = backtest.get("funding")
    if not isinstance(funding, Mapping):
        return False
    bind_flag = funding.get("bind")
    if bind_flag is True:
        return True
    return str(funding.get("model_version", "")) == FUNDING_MODEL_VERSION


def classify_funding_rate_value(value: Any) -> FundingRatePresence:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return FundingRatePresence.MISSING
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise FundingModelError(f"funding_rate_invalid:{value!r}") from exc
    if not math.isfinite(numeric):
        raise FundingModelError(f"funding_rate_non_finite:{value!r}")
    if numeric == 0.0:
        return FundingRatePresence.EXPLICIT_ZERO
    return FundingRatePresence.PRESENT


def is_funding_payment_timestamp(ts: pd.Timestamp, interval_hours: int) -> bool:
    normalized = pd.Timestamp(ts).tz_convert("UTC") if ts.tzinfo else pd.Timestamp(ts, tz="UTC")
    return (
        normalized.minute == 0
        and normalized.second == 0
        and normalized.microsecond == 0
        and normalized.hour % interval_hours == 0
    )


def _resolve_mark_price(bar: pd.Series, config: FundingModelConfigV1) -> float:
    if config.mark_price_column in bar.index:
        return float(bar[config.mark_price_column])
    if "close" in bar.index:
        return float(bar["close"])
    raise FundingModelError("mark_price_column_missing")


def _payment_amount(position_sign: int, notional: float, funding_rate: float) -> float:
    if position_sign == 0:
        return 0.0
    return -float(position_sign) * abs(notional) * funding_rate


def compute_funding_drag_v1(
    *,
    bars: pd.DataFrame,
    position_series: pd.Series,
    initial_equity: float,
    config: FundingModelConfigV1 | None = None,
    data_digest: str = "",
    fail_closed_on_missing_rate: bool = True,
) -> FundingDragResultV1:
    """
    Compute interval-aligned funding payments and funding drag.

    Long pays positive rates; short receives positive rates. Explicit 0.0 is valid.
    Missing rates fail-closed when fail_closed_on_missing_rate is True.
    """
    model = config or default_funding_model_config_v1()
    if model.model_version != FUNDING_MODEL_VERSION:
        raise FundingModelError("funding_model_not_version_bound")
    if model.rate_column not in bars.columns:
        raise FundingModelError(REASON_MISSING_FUNDING_SERIES)
    if bars.empty:
        raise FundingModelError("bars_empty")
    if initial_equity <= 0.0:
        raise FundingModelError("initial_equity_non_positive")
    if bars.index.has_duplicates:
        raise FundingModelError(REASON_DUPLICATE_FUNDING_EVENT)

    aligned_positions = position_series.reindex(bars.index).fillna(0).astype(int)
    events: list[FundingPaymentEventV1] = []
    reason_codes: list[str] = []
    explicit_zero_count = 0
    missing_rate_count = 0
    seen_timestamps: set[str] = set()
    last_timestamp: Optional[pd.Timestamp] = None

    payment_index = 0
    for ts, bar in bars.iterrows():
        timestamp = pd.Timestamp(ts)
        if last_timestamp is not None and timestamp < last_timestamp:
            raise FundingModelError(REASON_OUT_OF_ORDER_FUNDING_EVENT)
        last_timestamp = timestamp
        if not is_funding_payment_timestamp(timestamp, model.payment_interval_hours):
            continue
        ts_key = timestamp.isoformat()
        if ts_key in seen_timestamps:
            raise FundingModelError(REASON_DUPLICATE_FUNDING_EVENT)
        seen_timestamps.add(ts_key)

        position_value = aligned_positions.loc[timestamp]
        if isinstance(position_value, pd.Series):
            raise FundingModelError(REASON_DUPLICATE_FUNDING_EVENT)
        position_sign = int(position_value)
        rate_presence = classify_funding_rate_value(bar[model.rate_column])
        if rate_presence is FundingRatePresence.MISSING:
            missing_rate_count += 1
            if fail_closed_on_missing_rate:
                raise FundingModelError(REASON_MISSING_FUNDING_RATE)
            continue
        funding_rate = float(bar[model.rate_column])
        if rate_presence is FundingRatePresence.EXPLICIT_ZERO:
            explicit_zero_count += 1
            reason_codes.append(REASON_EXPLICIT_ZERO_RATE)

        mark_price = _resolve_mark_price(bar, model)
        notional = abs(position_sign) * mark_price
        payment = _payment_amount(position_sign, notional, funding_rate)
        events.append(
            FundingPaymentEventV1(
                timestamp=ts_key,
                position_sign=position_sign,
                mark_price=mark_price,
                funding_rate=funding_rate,
                rate_presence=rate_presence,
                notional=notional,
                payment_amount=payment,
                payment_index=payment_index,
            )
        )
        payment_index += 1

    total_payment = sum(event.payment_amount for event in events)
    funding_drag = total_payment / initial_equity
    if events:
        reason_codes.append(REASON_FUNDING_BOUND)

    return FundingDragResultV1(
        model_version=model.model_version,
        owner=model.owner,
        config_digest=model.config_digest(),
        data_digest=data_digest,
        implementation_digest=_stable_digest(
            {
                "owner": FUNDING_MODEL_OWNER,
                "model_version": FUNDING_MODEL_VERSION,
                "long_short_sign_semantics": LONG_SHORT_SIGN_SEMANTICS,
            }
        ),
        total_payment_amount=total_payment,
        funding_drag=funding_drag,
        payment_count=len(events),
        explicit_zero_rate_count=explicit_zero_count,
        missing_rate_count=missing_rate_count,
        payment_events=tuple(events),
        reason_codes=tuple(sorted(set(reason_codes))),
    )


def funding_model_schema_v1() -> dict[str, Any]:
    return {
        "contract_name": "funding_model_v1",
        "model_version": FUNDING_MODEL_VERSION,
        "owner": FUNDING_MODEL_OWNER,
        "payment_interval_hours": DEFAULT_PAYMENT_INTERVAL_HOURS,
        "rate_source": FUNDING_RATE_SOURCE_BARS_COLUMN,
        "long_short_sign_semantics": LONG_SHORT_SIGN_SEMANTICS,
        "funding_application_policy": FUNDING_APPLICATION_POLICY,
        "authority_effect": "NONE",
        "runtime_effect": False,
        "order_effect": False,
    }
