"""Necessary observed movement/cost admission at the original financial owner.

Uses the original B03 volatility/amplitude computations and actual final quantity.
Observed historical range is neither a forecast nor a guarantee of accessible PnL.
No resizing, ranking, independent state writer, or Survival-ratio conversion.
"""

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from fractions import Fraction
import json

from src.ops.economic_md_input_producer_v1.models_v1 import EconomicMdInstrumentRawInputV1
from src.ops.economic_md_input_producer_v1.constants_v1 import MARK_SOURCE_CLASS, MARK_ENDPOINT_PATH
from src.ops.peak_trade_ranking_feature_production_v1.marks_window_v1 import (
    extract_contiguous_finalized_pt1m_mark_window_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.pure_compute_v1 import (
    population_sigma_log_returns_v1,
    pt1m_mid_relative_range_v1,
)
from . import entry_execution_cost_v1 as cost
from .durable_store_v1 import canonical, digest
from .native_cost_cover_v1 import original_costs_v1

RULE = "OBSERVED_PT1M_MID_RELATIVE_RANGE_TIMES_CURRENT_NATIVE_NOTIONAL_GT_ORIGINAL_ROUNDTRIP_COSTS"


def _instant_ms(value):
    if type(value) is not str or not value:
        raise ValueError("MOVEMENT_CAPTURE_TIME_REQUIRED")
    if value.isdigit():
        result = int(value)
    else:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.utcoffset() is None:
            raise ValueError("MOVEMENT_CAPTURE_TIME_TIMEZONE_REQUIRED")
        result = int(parsed.timestamp() * 1000)
    if result <= 0:
        raise ValueError("MOVEMENT_CAPTURE_TIME_INVALID")
    return result


def _fraction(value):
    return Fraction(cost._money(str(value)))


def _rational(value):
    return dict(numerator=str(value.numerator), denominator=str(value.denominator))


@dataclass(frozen=True)
class AbsoluteMovementCostObservationV1:
    instrument_raw_input_json: str
    opening_observation_digest: str
    evaluated_at_utc: str

    @classmethod
    def capture_v1(cls, *, instrument_raw_input, opening_observation, evaluated_at_utc):
        if type(instrument_raw_input) is not EconomicMdInstrumentRawInputV1:
            raise ValueError("MOVEMENT_ORIGINAL_ECONOMIC_MD_REQUIRED")
        if type(opening_observation) is not cost.EntryExecutionCostObservationV1:
            raise ValueError("MOVEMENT_ORIGINAL_OPENING_OBSERVATION_REQUIRED")
        return cls(
            instrument_raw_input_json=canonical(instrument_raw_input.to_dict()),
            opening_observation_digest=digest(opening_observation.to_dict_v1()),
            evaluated_at_utc=evaluated_at_utc,
        )

    def to_dict_v1(self):
        return dict(schema="absolute_movement_cost_observation.v1", **asdict(self))

    @classmethod
    def from_dict_v1(cls, raw):
        if (
            type(raw) is not dict
            or set(raw)
            != {
                "schema",
                "instrument_raw_input_json",
                "opening_observation_digest",
                "evaluated_at_utc",
            }
            or raw["schema"] != "absolute_movement_cost_observation.v1"
        ):
            raise ValueError("MOVEMENT_OBSERVATION_SCHEMA_INVALID")
        return cls(**{key: value for key, value in raw.items() if key != "schema"})


def assess_absolute_movement_cost_v1(observation, *, sizing, evaluated_at_utc=None):
    if type(observation) is not AbsoluteMovementCostObservationV1:
        raise ValueError("MOVEMENT_TYPED_OBSERVATION_REQUIRED")
    now = evaluated_at_utc or observation.evaluated_at_utc
    cost.acquisition_age_seconds_v1(acquired_at_utc=observation.evaluated_at_utc, now_utc=now)
    # Reuse every original source validation. Remove only this new binding to
    # avoid recursive validation when rereading the original sizing envelope.
    prior = replace(sizing, absolute_movement_cost_binding=None)
    margin, values = original_costs_v1(prior)
    if sizing.entry_cost_binding is None:
        raise ValueError("MOVEMENT_ORIGINAL_COST_BINDINGS_REQUIRED")
    if observation.opening_observation_digest != digest(
        json.loads(sizing.entry_cost_binding.observation_json)
    ):
        raise ValueError("MOVEMENT_OPENING_SOURCE_MISMATCH")
    raw = json.loads(observation.instrument_raw_input_json)
    instrument = EconomicMdInstrumentRawInputV1.from_dict(raw)
    if (
        raw != instrument.to_dict()
        or instrument.raw_input_eligible is not True
        or instrument.exclusion_reason_codes
        or instrument.raw_input_digest != instrument.compute_raw_input_digest()
        or instrument.canonical_instrument_id != sizing.applied_input.instrument_id
        or instrument.venue_native_id != sizing.monetary_source.venue_native_id
    ):
        raise ValueError("MOVEMENT_ECONOMIC_MD_IDENTITY_OR_INTEGRITY_INVALID")
    extraction = extract_contiguous_finalized_pt1m_mark_window_v1(instrument.finalized_pt1m_marks)
    if not extraction.ok or extraction.window is None:
        raise ValueError("MOVEMENT_FINALIZED_CONTIGUOUS_PT1M_WINDOW_REQUIRED")
    window = extraction.window
    if window.source_endpoint != MARK_ENDPOINT_PATH or window.source_class not in {
        MARK_SOURCE_CLASS,
        "FinalizedPt1mMarkFactV1",
    }:
        raise ValueError("MOVEMENT_CANONICAL_FINALIZED_MARK_SOURCE_REQUIRED")
    current_ms, known_ms = _instant_ms(now), _instant_ms(observation.evaluated_at_utc)
    # Candle timestamps are opening times. Use the latest completed minute,
    # independently of receive time; receiving old history does not refresh it.
    expected_last = current_ms // 60_000 * 60_000 - 60_000
    if int(window.as_of_event_time) != expected_last:
        raise ValueError("MOVEMENT_LATEST_COMPLETED_PT1M_WINDOW_REQUIRED")
    for event, capture in zip(window.event_timestamps, window.receive_or_capture_timestamps):
        capture_ms = _instant_ms(capture)
        if int(event) % 60_000 or int(event) + 60_000 > capture_ms or capture_ms > known_ms:
            raise ValueError("MOVEMENT_FINALITY_OR_KNOWLEDGE_TIME_INVALID")
    volatility = population_sigma_log_returns_v1(window.mark_px)
    amplitude = pt1m_mid_relative_range_v1(window.mark_px)
    low, high = min(map(_fraction, window.mark_px)), max(map(_fraction, window.mark_px))
    exact_amplitude = (high - low) / ((high + low) / 2)
    quantity = _fraction(sizing.decision.final_quantity)
    native_notional = (
        quantity
        * _fraction(sizing.applied_input.instrument.contract_multiplier)
        * _fraction(sizing.monetary_source.native_reference_price)
    )
    movement = exact_amplitude * native_notional
    total_cost = sum((values[key] for key in ("opening", "closing", "funding")), Fraction(0))
    if movement <= total_cost:
        raise ValueError("MOVEMENT_OBSERVED_AMPLITUDE_DOES_NOT_EXCEED_ROUNDTRIP_COSTS")
    return dict(
        schema="absolute_movement_cost_receipt.v1",
        rule=RULE,
        observation_digest=digest(observation.to_dict_v1()),
        instrument_raw_input_digest=instrument.raw_input_digest,
        canonical_instrument_id=instrument.canonical_instrument_id,
        venue_native_id=instrument.venue_native_id,
        side=sizing.applied_input.selected_side,
        final_native_quantity=str(sizing.decision.final_quantity),
        original_sizing_request_digest=sizing.request_digest,
        native_settlement_currency=margin["settlement_currency"],
        native_reference_price=sizing.monetary_source.native_reference_price,
        window_first_open_ms=window.event_timestamps[0],
        window_last_open_ms=window.event_timestamps[-1],
        window_source_class=window.source_class,
        window_source_endpoint=window.source_endpoint,
        mark_count=61,
        log_return_count=60,
        original_volatility=str(volatility),
        original_relative_amplitude=str(amplitude),
        exact_relative_amplitude=_rational(exact_amplitude),
        observed_amplitude_native_money=_rational(movement),
        original_roundtrip_costs_native_money=_rational(total_cost),
        opening_cost_binding_digest=digest(sizing.entry_cost_binding.to_dict_v1()),
        closing_cost_binding_digest=digest(sizing.close_cost_binding.to_dict_v1()),
        funding_cost_binding_digest=digest(sizing.funding_cost_binding.to_dict_v1()),
        expected_profit_forecast=False,
        accessible_range_guaranteed=False,
        survival_ratio_mapping=False,
        economic_profitability_proven=False,
    )


@dataclass(frozen=True)
class AbsoluteMovementCostBindingV1:
    observation_json: str
    receipt_json: str

    def to_dict_v1(self):
        return dict(schema="absolute_movement_cost_binding.v1", **asdict(self))

    @classmethod
    def from_dict_v1(cls, raw):
        if (
            type(raw) is not dict
            or set(raw) != {"schema", "observation_json", "receipt_json"}
            or raw["schema"] != "absolute_movement_cost_binding.v1"
        ):
            raise ValueError("MOVEMENT_BINDING_SCHEMA_INVALID")
        return cls(observation_json=raw["observation_json"], receipt_json=raw["receipt_json"])

    def validate_v1(self, *, sizing, evaluated_at_utc=None):
        observation = AbsoluteMovementCostObservationV1.from_dict_v1(
            json.loads(self.observation_json)
        )
        result = assess_absolute_movement_cost_v1(
            observation, sizing=sizing, evaluated_at_utc=evaluated_at_utc
        )
        if self.receipt_json != canonical(result):
            raise ValueError("MOVEMENT_RETAINED_RECEIPT_MISMATCH")
        return result


def bind_absolute_movement_cost_v1(observation, *, sizing, evaluated_at_utc=None):
    receipt = assess_absolute_movement_cost_v1(
        observation, sizing=sizing, evaluated_at_utc=evaluated_at_utc
    )
    return AbsoluteMovementCostBindingV1(
        observation_json=canonical(observation.to_dict_v1()),
        receipt_json=canonical(receipt),
    )
