"""Pure offline MVR feature computation. Local formula copies. No authority transfer."""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from src.ops.cap22_offline_mvr_evidence_harness_v1.constants_v1 import (
    LOG_RETURN_COUNT,
    MINIMUM_FINALIZED_PT1M_MARKS,
    PT1M_STEP_MS,
    VOLATILITY_ESTIMATOR,
    VOLATILITY_UNITS,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.reason_codes_v1 import (
    OfflineMvrHarnessFailureCodeV1,
)
from src.ops.cap22_offline_mvr_spread_challenger_order_contract_v1 import (
    SPREAD_AGGREGATOR,
    SPREAD_FORMULA_ID,
    SPREAD_UNITS,
)
from src.ops.economic_md_input_producer_v1.models_v1 import (
    EconomicMdInstrumentRawInputV1,
    canonical_json_dumps,
    sha256_hex,
)


class OfflineMvrFeatureError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _decimal_positive(raw: str) -> Decimal:
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError, ArithmeticError) as exc:
        raise OfflineMvrFeatureError(
            OfflineMvrHarnessFailureCodeV1.INVALID_BID_ASK.value, str(raw)
        ) from exc
    return value


def population_sigma_log_returns_v1(mark_px: tuple[str, ...]) -> Decimal:
    if len(mark_px) != MINIMUM_FINALIZED_PT1M_MARKS:
        raise OfflineMvrFeatureError(
            OfflineMvrHarnessFailureCodeV1.INSUFFICIENT_MARKS.value,
            str(len(mark_px)),
        )
    values: list[Decimal] = []
    for raw in mark_px:
        try:
            px = Decimal(str(raw).strip())
        except (InvalidOperation, ValueError, ArithmeticError) as exc:
            raise OfflineMvrFeatureError(
                OfflineMvrHarnessFailureCodeV1.NONPOSITIVE_MARK.value, str(raw)
            ) from exc
        if px <= 0:
            raise OfflineMvrFeatureError(
                OfflineMvrHarnessFailureCodeV1.NONPOSITIVE_MARK.value, str(raw)
            )
        values.append(px)
    logs: list[float] = []
    for prev, cur in zip(values, values[1:]):
        logs.append(math.log(float(cur / prev)))
    if len(logs) != LOG_RETURN_COUNT:
        raise OfflineMvrFeatureError(
            OfflineMvrHarnessFailureCodeV1.INSUFFICIENT_MARKS.value, str(len(logs))
        )
    mean = sum(logs) / float(LOG_RETURN_COUNT)
    var = sum((item - mean) ** 2 for item in logs) / float(LOG_RETURN_COUNT)
    sigma = math.sqrt(var)
    return Decimal(format(sigma, ".16e"))


def relative_bid_ask_spread_over_mid_v1(*, bid_px: str, ask_px: str) -> Decimal:
    bid = _decimal_positive(bid_px)
    ask = _decimal_positive(ask_px)
    if bid <= 0 or ask <= 0:
        raise OfflineMvrFeatureError(OfflineMvrHarnessFailureCodeV1.INVALID_BID_ASK.value)
    if bid > ask:
        raise OfflineMvrFeatureError(OfflineMvrHarnessFailureCodeV1.CROSSED_QUOTE.value)
    mid = (ask + bid) / Decimal(2)
    if mid <= 0:
        raise OfflineMvrFeatureError(OfflineMvrHarnessFailureCodeV1.INVALID_BID_ASK.value)
    return (ask - bid) / mid


@dataclass(frozen=True)
class OfflineMvrInstrumentFeaturesV1:
    canonical_instrument_id: str
    venue_native_id: str
    volatility: Decimal
    relative_spread: Decimal
    exact_zero_spread: bool
    volatility_units: str
    spread_formula_id: str
    spread_units: str
    spread_aggregator: str
    feature_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "exact_zero_spread": self.exact_zero_spread,
            "feature_digest": self.feature_digest,
            "relative_spread": format(self.relative_spread, "f"),
            "spread_aggregator": self.spread_aggregator,
            "spread_formula_id": self.spread_formula_id,
            "spread_units": self.spread_units,
            "venue_native_id": self.venue_native_id,
            "volatility": format(self.volatility, ".16e"),
            "volatility_estimator": VOLATILITY_ESTIMATOR,
            "volatility_units": self.volatility_units,
        }

    def deterministic_payload_for_digest(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("feature_digest", None)
        return payload


def _require_finalized_contiguous_marks(
    row: EconomicMdInstrumentRawInputV1,
) -> tuple[str, ...]:
    marks = row.finalized_pt1m_marks
    if len(marks) < MINIMUM_FINALIZED_PT1M_MARKS:
        raise OfflineMvrFeatureError(
            OfflineMvrHarnessFailureCodeV1.INSUFFICIENT_MARKS.value,
            str(len(marks)),
        )
    if len(marks) > MINIMUM_FINALIZED_PT1M_MARKS:
        marks = marks[-MINIMUM_FINALIZED_PT1M_MARKS:]
    timestamps: list[int] = []
    px: list[str] = []
    for mark in marks:
        if str(mark.finalization_status) != "FINALIZED":
            raise OfflineMvrFeatureError(
                OfflineMvrHarnessFailureCodeV1.NON_FINALIZED_MARK.value,
                str(mark.event_timestamp),
            )
        if mark.mark_px in (None, ""):
            raise OfflineMvrFeatureError(OfflineMvrHarnessFailureCodeV1.MISSING_MARK.value)
        px.append(str(mark.mark_px))
        try:
            timestamps.append(int(str(mark.event_timestamp)))
        except (TypeError, ValueError) as exc:
            raise OfflineMvrFeatureError(
                OfflineMvrHarnessFailureCodeV1.MISSING_MARK.value,
                str(mark.event_timestamp),
            ) from exc
    for prev, cur in zip(timestamps, timestamps[1:]):
        if cur - prev != PT1M_STEP_MS:
            raise OfflineMvrFeatureError(
                OfflineMvrHarnessFailureCodeV1.MISSING_MARK.value,
                f"{prev}->{cur}",
            )
    return tuple(px)


def compute_instrument_features_v1(
    row: EconomicMdInstrumentRawInputV1,
) -> OfflineMvrInstrumentFeaturesV1:
    if not row.raw_input_eligible:
        raise OfflineMvrFeatureError(
            OfflineMvrHarnessFailureCodeV1.RAW_INPUT_NOT_ELIGIBLE.value,
            row.canonical_instrument_id,
        )
    if row.ticker is None:
        raise OfflineMvrFeatureError(OfflineMvrHarnessFailureCodeV1.TICKER_MISSING.value)
    mark_px = _require_finalized_contiguous_marks(row)
    volatility = population_sigma_log_returns_v1(mark_px)
    relative_spread = relative_bid_ask_spread_over_mid_v1(
        bid_px=row.ticker.bid_px,
        ask_px=row.ticker.ask_px,
    )
    features = OfflineMvrInstrumentFeaturesV1(
        canonical_instrument_id=row.canonical_instrument_id,
        venue_native_id=row.venue_native_id,
        volatility=volatility,
        relative_spread=relative_spread,
        exact_zero_spread=relative_spread == 0,
        volatility_units=VOLATILITY_UNITS,
        spread_formula_id=SPREAD_FORMULA_ID,
        spread_units=SPREAD_UNITS,
        spread_aggregator=SPREAD_AGGREGATOR,
        feature_digest="",
    )
    digest = sha256_hex(canonical_json_dumps(features.deterministic_payload_for_digest()))
    return OfflineMvrInstrumentFeaturesV1(
        canonical_instrument_id=features.canonical_instrument_id,
        venue_native_id=features.venue_native_id,
        volatility=features.volatility,
        relative_spread=features.relative_spread,
        exact_zero_spread=features.exact_zero_spread,
        volatility_units=features.volatility_units,
        spread_formula_id=features.spread_formula_id,
        spread_units=features.spread_units,
        spread_aggregator=features.spread_aggregator,
        feature_digest=digest,
    )
