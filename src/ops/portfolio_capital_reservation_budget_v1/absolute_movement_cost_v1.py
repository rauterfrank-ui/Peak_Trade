"""Necessary observed movement/cost admission at the original financial owner.

Uses the original B03 volatility/amplitude computations and actual final quantity.
Observed historical range is neither a forecast nor a guarantee of accessible PnL.
No resizing, ranking, independent state writer, or Survival-ratio conversion.
"""

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
import re
from urllib.parse import urlencode

from src.ops.economic_md_input_producer_v1.models_v1 import (
    EconomicMdInstrumentRawInputV1,
    FinalizedPt1mMarkObservationV1,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import MARK_SOURCE_CLASS, MARK_ENDPOINT_PATH
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_runtime_economic_md_adapter_v1 import (
    persist_bound_ranking_mark_window_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.canonical_fact_decoder_v1 import (
    canonical_fact_source_v1,
    fact_capture_timestamp_v1,
    fact_event_time_ms_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import EEA_REST_HOST
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from src.ops.peak_trade_public_market_data_runtime_v1.historical_query_v1 import (
    query_historical_facts_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.rest_recovery_v1 import (
    public_instrument_ref_for_binding_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
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
class EntryPublicMarkSourceV1:
    """The original public REST and durable fact path, scoped to one entry."""

    store_root: Path
    transport: FullCoreProductiveReadOnlyGetTransportV1

    def observe_v1(self, *, bound, opening_observation):
        if type(opening_observation) is not cost.EntryExecutionCostObservationV1:
            raise ValueError("MOVEMENT_ORIGINAL_OPENING_OBSERVATION_REQUIRED")
        if (
            not self.store_root.is_absolute()
            or type(self.transport) is not FullCoreProductiveReadOnlyGetTransportV1
        ):
            raise ValueError("MOVEMENT_PUBLIC_SOURCE_BINDING_REQUIRED")
        if json.loads(opening_observation.bound_instrument_json) != bound.to_dict():
            raise ValueError("MOVEMENT_OPENING_SOURCE_INSTRUMENT_MISMATCH")
        instrument = public_instrument_ref_for_binding_v1(bound)
        session = opening_observation.acquisition_decision_id

        def fetch_json(path, query):
            endpoint = path + "?" + urlencode(query)
            result = self.transport.get(
                endpoint=endpoint,
                auth_required=False,
                pretrade_decision_id=session,
                get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
            )
            if (
                result.get_performed is not True
                or result.method != "GET"
                or result.endpoint != endpoint
                or result.http_status != 200
                or result.error_class
                or result.auth_header_sent is not False
                or result.venue_live_contact is not True
                or result.historical_reuse is not False
                or result.pretrade_decision_id != session
                or not re.fullmatch(r"[0-9a-f]{64}", result.body_sha256 or "")
            ):
                raise ValueError("MOVEMENT_ORIGINAL_PUBLIC_GET_UNPROVEN")
            cost.acquisition_age_seconds_v1(
                acquired_at_utc=result.acquired_at_utc, now_utc=cost.utc_now_iso_v1()
            )
            return result.payload

        window = persist_bound_ranking_mark_window_v1(
            store_root=self.store_root,
            fetch_json=fetch_json,
            instrument_ref=instrument,
            session_id=session,
        )
        history = query_historical_facts_v1(
            self.store_root,
            venue_native_id=instrument.venue_native_id,
            fact_kind="FinalizedPt1mMarkFactV1",
        )
        facts = {
            fingerprint: fact
            for fact in history.facts
            if (fingerprint := fact_digest(fact)) in window.fact_digests
        }
        if facts.keys() != window.fact_digests:
            raise ValueError("MOVEMENT_PUBLIC_FACT_READBACK_UNPROVEN")
        return AbsoluteMovementCostObservationV1(
            instrument_raw_input_json="null",
            opening_observation_digest=digest(opening_observation.to_dict_v1()),
            evaluated_at_utc=max(
                opening_observation.evaluated_at_utc,
                *(fact_capture_timestamp_v1(fact) for fact in facts.values()),
                key=_instant_ms,
            ),
            original_public_facts_json=canonical(facts),
        )


@dataclass(frozen=True)
class AbsoluteMovementCostObservationV1:
    instrument_raw_input_json: str
    opening_observation_digest: str
    evaluated_at_utc: str
    original_public_facts_json: str | None = None

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
        body = asdict(self)
        if self.original_public_facts_json is None:
            body.pop("original_public_facts_json")
            return dict(schema="absolute_movement_cost_observation.v1", **body)
        return dict(schema="absolute_movement_cost_observation.v2", **body)

    @classmethod
    def from_dict_v1(cls, raw):
        keys = {
            "schema",
            "instrument_raw_input_json",
            "opening_observation_digest",
            "evaluated_at_utc",
        }
        if type(raw) is not dict:
            raise ValueError("MOVEMENT_OBSERVATION_SCHEMA_INVALID")
        schema = raw.get("schema")
        if schema == "absolute_movement_cost_observation.v2":
            keys.add("original_public_facts_json")
            if not isinstance(raw.get("original_public_facts_json"), str):
                raise ValueError("MOVEMENT_PUBLIC_FACT_READBACK_UNPROVEN")
        elif schema != "absolute_movement_cost_observation.v1":
            raise ValueError("MOVEMENT_OBSERVATION_SCHEMA_INVALID")
        if set(raw) != keys:
            raise ValueError("MOVEMENT_OBSERVATION_SCHEMA_INVALID")
        return cls(**{key: value for key, value in raw.items() if key != "schema"})


def _public_mark_inputs(raw, *, sizing):
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

    original = json.loads(sizing.entry_cost_binding.observation_json)
    bound = BoundInstrumentV1(**json.loads(original["bound_instrument_json"]))
    instrument = public_instrument_ref_for_binding_v1(bound).to_dict()
    if type(raw) is not dict or len(raw) != 61:
        raise ValueError("MOVEMENT_PUBLIC_FACT_READBACK_UNPROVEN")
    marks = []
    for fingerprint, fact in raw.items():
        source = canonical_fact_source_v1(fact)
        event_ms = fact_event_time_ms_v1(fact)
        provenance = fact["provenance"]
        quality = fact["quality"]
        if (
            fingerprint != fact_digest(fact)
            or fact.get("instrument") != instrument
            or fact.get("interval_start_ms") != event_ms
            or fact.get("confirm") != "1"
            or fact.get("source_price_kind") != "mark_price_candle"
            or provenance.get("transport") != "public_rest"
            or provenance.get("eea_endpoint_family") != EEA_REST_HOST
            or not re.fullmatch(r"[0-9a-f]{64}", provenance.get("raw_payload_digest", ""))
            or not provenance.get("session_id")
            or quality.get("finalized") is not True
            or any(
                quality.get(key) is not False
                for key in (
                    "in_progress",
                    "missing",
                    "stale",
                    "duplicate",
                    "out_of_order",
                    "gap_detected",
                )
            )
            or source
            != {
                "source_class": "FinalizedPt1mMarkFactV1",
                "source_endpoint": MARK_ENDPOINT_PATH,
            }
        ):
            raise ValueError("MOVEMENT_ORIGINAL_PUBLIC_MARK_FACT_INVALID")
        marks.append(
            FinalizedPt1mMarkObservationV1(
                mark_px=fact["mark_px"],
                event_timestamp=str(event_ms),
                receive_or_capture_timestamp=fact_capture_timestamp_v1(fact),
                finalization_status="FINALIZED",
                **source,
            )
        )
    return sorted(marks, key=lambda row: int(row.event_timestamp))


def assess_absolute_movement_cost_v1(observation, *, sizing, evaluated_at_utc=None):
    if type(observation) is not AbsoluteMovementCostObservationV1:
        raise ValueError("MOVEMENT_TYPED_OBSERVATION_REQUIRED")
    now = evaluated_at_utc or observation.evaluated_at_utc
    cost.acquisition_age_seconds_v1(acquired_at_utc=observation.evaluated_at_utc, now_utc=now)
    # Reuse every original source validation. Remove only this new binding to
    # avoid recursive validation when rereading the original sizing envelope.
    prior = replace(sizing, absolute_movement_cost_binding=None, xperp_liquidation_binding=None)
    margin, values = original_costs_v1(prior)
    if sizing.entry_cost_binding is None:
        raise ValueError("MOVEMENT_ORIGINAL_COST_BINDINGS_REQUIRED")
    if observation.opening_observation_digest != digest(
        json.loads(sizing.entry_cost_binding.observation_json)
    ):
        raise ValueError("MOVEMENT_OPENING_SOURCE_MISMATCH")
    public_digest = None
    if observation.original_public_facts_json is not None:
        if observation.instrument_raw_input_json != "null":
            raise ValueError("MOVEMENT_ORIGINAL_PUBLIC_MARK_FACT_INVALID")
        public_facts = json.loads(observation.original_public_facts_json)
        marks = _public_mark_inputs(public_facts, sizing=sizing)
        public_digest = digest(public_facts)
        raw_digest = None
    else:
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
        marks = instrument.finalized_pt1m_marks
        raw_digest = instrument.raw_input_digest
    extraction = extract_contiguous_finalized_pt1m_mark_window_v1(marks)
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
    receipt = dict(
        schema="absolute_movement_cost_receipt.v1",
        rule=RULE,
        observation_digest=digest(observation.to_dict_v1()),
        instrument_raw_input_digest=raw_digest,
        canonical_instrument_id=sizing.applied_input.instrument_id,
        venue_native_id=sizing.monetary_source.venue_native_id,
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
    if public_digest is not None:
        receipt.update(
            schema="absolute_movement_cost_receipt.v2",
            original_public_facts_digest=public_digest,
        )
    return receipt


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

    def require_original_public_facts_v1(self):
        retained = AbsoluteMovementCostObservationV1.from_dict_v1(json.loads(self.observation_json))
        if retained.original_public_facts_json is None:
            raise ValueError("MOVEMENT_ORIGINAL_PUBLIC_FACTS_REQUIRED")


def bind_absolute_movement_cost_v1(observation, *, sizing, evaluated_at_utc=None):
    receipt = assess_absolute_movement_cost_v1(
        observation, sizing=sizing, evaluated_at_utc=evaluated_at_utc
    )
    return AbsoluteMovementCostBindingV1(
        observation_json=canonical(observation.to_dict_v1()),
        receipt_json=canonical(receipt),
    )
