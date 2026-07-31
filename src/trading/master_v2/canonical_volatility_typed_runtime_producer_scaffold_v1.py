"""Typed runtime producer scaffold for CanonicalVolatilityEstimateV1.

Production-near but **not** wired into Master-V2 / Double-Play hot path.
Reuses only existing canonical authorities:

- Market-Sample / Distinctness: ``accept_distinct_market_sample_v1`` (via history host)
- ``MarketSampleIdentityV1`` / ``EventTimeInstantV1``
- Materializer P1: ``compute_canonical_volatility_estimate_from_mark_prices_v1``
- Typed factory P2: ``materialize_typed_canonical_volatility_estimate_v1``
- Existing source / typed digests from the typed consumption contract

Non-goals (explicit):
- no runtime cutover, no Double-Play wiring, no productive ``bind_typed`` call
- no CMC mutation, no DynamicScopeRules / Survival / Suitability wiring
- no P7 / wallclock feature_regime producer
- no parameter-value decision, no numeric max-age, no silent fallback / floor
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationClassification,
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
    TimeSampleEpochSemanticsErrorV1,
)
from trading.master_v2 import canonical_volatility_estimate_feature_contract_v1 as contract
from trading.master_v2 import canonical_volatility_estimate_materializer_v1 as materializer
from trading.master_v2 import (
    canonical_volatility_estimate_typed_consumption_contract_v1 as typed,
)
from trading.master_v2.canonical_volatility_runtime_mark_history_v1 import (
    BAR_INTERVAL_SECONDS,
    CAPABILITY_ID as HISTORY_CAPABILITY_ID,
    CanonicalVolatilityRuntimeMarkHistoryHostV1,
    HISTORY_OWNER,
    REQUIRED_PRICE_OBSERVATIONS,
    RuntimeMarkHistoryError,
    assert_pt1m_trailing_window_contiguous_v1,
    atomic_write_history_persistence_v1,
    load_history_persistence_v1,
)

PACKAGE_MARKER = "MASTER_V2_CANONICAL_VOLATILITY_TYPED_RUNTIME_PRODUCER_SCAFFOLD_V1=true"

CAPABILITY_ID = "MASTER_V2_CANONICAL_VOLATILITY_TYPED_RUNTIME_PRODUCER_SCAFFOLD_V1"
CAPABILITY_VERSION = "canonical_volatility_typed_runtime_producer_scaffold/v1"
PRODUCER_OWNER = "trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1"

SINGLE_CANONICAL_VOLATILITY_ESTIMATOR = True
SINGLE_TYPED_FACTORY = True
SINGLE_SAMPLE_ACCEPTANCE_AUTHORITY = True
SINGLE_EVENT_TIME_AUTHORITY = True
NO_SECOND_BINDING_ADAPTER = True
NO_FLOAT_ONLY_RUNTIME_OUTPUT = True
NO_SILENT_FALLBACK = True
NO_NUMERIC_FLOOR = True
NO_RUNTIME_CUTOVER = True
NO_DOUBLE_PLAY_WIRING = True
NO_PARAMETER_VALUE_DECISION = True
FAIL_CLOSED = True

RUNTIME_EFFECT = False
TRADING_LOGIC_EFFECT = False
PARAMETER_EFFECT = False
LIVE_AUTHORIZATION = False
RUNTIME_WIRING = False
RUNTIME_PRODUCER_CUTOVER = False
PRODUCTIVE_BIND_TYPED_CALLER = False
CMC_RUNTIME_WIRING = False
DOUBLE_PLAY_RUNTIME_WIRING = False
P7_REPLACED = False
NUMERIC_MAX_AGE_DECIDED = False

FORBIDDEN_FALLBACK_LITERALS: tuple[float, ...] = (0.2, 0.02, 1.0, 1e-9)


class TypedRuntimeProducerOutcomeV1(str, Enum):
    WARMUP = "WARMUP"
    PRODUCED = "PRODUCED"
    DUPLICATE_NOOP = "DUPLICATE_NOOP"
    OUT_OF_ORDER_REJECTED = "OUT_OF_ORDER_REJECTED"
    INVALID_SAMPLE_REJECTED = "INVALID_SAMPLE_REJECTED"
    HISTORY_GAP_REJECTED = "HISTORY_GAP_REJECTED"
    PERSISTENCE_REJECTED = "PERSISTENCE_REJECTED"
    MATERIALIZATION_REJECTED = "MATERIALIZATION_REJECTED"


@dataclass(frozen=True)
class TypedRuntimeProducerResultV1:
    """Explicit producer result; distinguishes warmup / produced / reject / noop."""

    outcome: TypedRuntimeProducerOutcomeV1
    estimate: Optional[typed.CanonicalVolatilityEstimateV1]
    history_digest: str
    observation_count_prices: int
    as_of_event_time: Optional[datetime]
    reason: str
    sample_digest: Optional[str] = None

    @property
    def produced(self) -> bool:
        return self.outcome is TypedRuntimeProducerOutcomeV1.PRODUCED and self.estimate is not None


@dataclass(frozen=True)
class TypedRuntimeProducerOutputPortV1:
    """Non-productive output port for a later capability to call bind_typed.

    This capability never invokes ``bind_typed_canonical_volatility_estimate_*``.
    """

    estimate: Optional[typed.CanonicalVolatilityEstimateV1]
    source_digest: Optional[str]
    history_digest: str
    as_of_event_time: Optional[datetime]
    outcome: TypedRuntimeProducerOutcomeV1
    ready_for_binding_handoff: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "estimate": None if self.estimate is None else self.estimate.to_dict(),
            "source_digest": self.source_digest,
            "history_digest": self.history_digest,
            "as_of_event_time": (
                None if self.as_of_event_time is None else self.as_of_event_time.isoformat()
            ),
            "outcome": self.outcome.value,
            "ready_for_binding_handoff": self.ready_for_binding_handoff,
            "productive_bind_typed_caller": PRODUCTIVE_BIND_TYPED_CALLER,
        }


def _event_time_to_datetime(event_time: EventTimeInstantV1) -> datetime:
    return datetime.fromtimestamp(event_time.unix_seconds, tz=timezone.utc)


def _classify_non_distinct(
    classification: ObservationClassification,
) -> TypedRuntimeProducerOutcomeV1:
    if classification in {
        ObservationClassification.DUPLICATE,
        ObservationClassification.TRANSPORT_ONLY_DUPLICATE,
    }:
        return TypedRuntimeProducerOutcomeV1.DUPLICATE_NOOP
    if classification is ObservationClassification.OUT_OF_ORDER:
        return TypedRuntimeProducerOutcomeV1.OUT_OF_ORDER_REJECTED
    return TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED


def validate_finalized_mark_sample_fields_v1(
    *,
    venue: Any,
    canonical_instrument_id: Any,
    venue_instrument_id: Any,
    event_time_unix_seconds: Any,
    mark_price: Any,
    is_final: Any,
) -> MarketSampleIdentityV1:
    """Fail-closed pre-authority validation for raw finalized mark inputs."""
    if is_final is not True:
        raise RuntimeMarkHistoryError("UNFINALIZED_OR_INVALID_IS_FINAL")
    if mark_price is None:
        raise RuntimeMarkHistoryError("MARK_PRICE_NULL")
    try:
        price = float(mark_price)
    except (TypeError, ValueError) as exc:
        raise RuntimeMarkHistoryError("MARK_PRICE_NON_NUMERIC") from exc
    if not math.isfinite(price) or price <= 0.0:
        raise RuntimeMarkHistoryError("MARK_PRICE_NON_FINITE_OR_NONPOSITIVE")
    try:
        sample = MarketSampleIdentityV1(
            venue=str(venue),
            canonical_instrument_id=str(canonical_instrument_id),
            venue_instrument_id=str(venue_instrument_id),
            event_time=EventTimeInstantV1(unix_seconds=float(event_time_unix_seconds)),
            mark_price=price,
        )
    except TimeSampleEpochSemanticsErrorV1 as exc:
        raise RuntimeMarkHistoryError(f"INVALID_SAMPLE_IDENTITY:{exc}") from exc
    return sample


@dataclass
class CanonicalVolatilityTypedRuntimeProducerScaffoldV1:
    """Scaffold producer: distinct finalized PT1M mark → typed estimate (offline port)."""

    history: CanonicalVolatilityRuntimeMarkHistoryHostV1
    persistence_path: Optional[Path] = None
    _last_result: Optional[TypedRuntimeProducerResultV1] = None
    _last_estimate: Optional[typed.CanonicalVolatilityEstimateV1] = None
    _last_source_digest: Optional[str] = None

    @classmethod
    def create(
        cls,
        *,
        venue: str,
        canonical_instrument_id: str,
        venue_instrument_id: str,
        persistence_path: Path | None = None,
    ) -> "CanonicalVolatilityTypedRuntimeProducerScaffoldV1":
        history = CanonicalVolatilityRuntimeMarkHistoryHostV1.create(
            venue=venue,
            canonical_instrument_id=canonical_instrument_id,
            venue_instrument_id=venue_instrument_id,
        )
        return cls(history=history, persistence_path=persistence_path)

    @classmethod
    def restore_from_persistence_v1(
        cls,
        *,
        persistence_path: Path,
    ) -> "CanonicalVolatilityTypedRuntimeProducerScaffoldV1":
        try:
            history = load_history_persistence_v1(persistence_path)
        except RuntimeMarkHistoryError:
            raise
        except Exception as exc:  # noqa: BLE001 — fail-closed persistence boundary
            raise RuntimeMarkHistoryError(f"PERSISTENCE_RESTORE_FAILED:{exc}") from exc
        return cls(history=history, persistence_path=persistence_path)

    def output_port_v1(self) -> TypedRuntimeProducerOutputPortV1:
        outcome = (
            TypedRuntimeProducerOutcomeV1.WARMUP
            if self._last_result is None
            else self._last_result.outcome
        )
        estimate = self._last_estimate
        return TypedRuntimeProducerOutputPortV1(
            estimate=estimate,
            source_digest=None if estimate is None else estimate.source_digest,
            history_digest=self.history.history_digest,
            as_of_event_time=None if estimate is None else estimate.as_of_event_time,
            outcome=outcome,
            ready_for_binding_handoff=estimate is not None,
        )

    def on_runtime_cycle_without_sample_v1(self) -> TypedRuntimeProducerResultV1:
        """Runtime/poll cycle without a new sample must not invent an estimate."""
        result = TypedRuntimeProducerResultV1(
            outcome=(
                self._last_result.outcome
                if self._last_result is not None
                else TypedRuntimeProducerOutcomeV1.WARMUP
            ),
            estimate=None,
            history_digest=self.history.history_digest,
            observation_count_prices=self.history.observation_count_prices,
            as_of_event_time=(
                None
                if self.history.last_accepted_event_time is None
                else _event_time_to_datetime(self.history.last_accepted_event_time)
            ),
            reason="runtime_cycle_without_new_sample_no_estimate",
            sample_digest=None,
        )
        # Do not overwrite last produced estimate on the output port.
        return result

    def _persist_fail_closed(self) -> Optional[TypedRuntimeProducerResultV1]:
        if self.persistence_path is None:
            return None
        try:
            atomic_write_history_persistence_v1(path=self.persistence_path, host=self.history)
        except Exception as exc:  # noqa: BLE001
            result = TypedRuntimeProducerResultV1(
                outcome=TypedRuntimeProducerOutcomeV1.PERSISTENCE_REJECTED,
                estimate=None,
                history_digest=self.history.history_digest,
                observation_count_prices=self.history.observation_count_prices,
                as_of_event_time=(
                    None
                    if self.history.last_accepted_event_time is None
                    else _event_time_to_datetime(self.history.last_accepted_event_time)
                ),
                reason=f"persistence_write_failed:{exc}",
            )
            self._last_result = result
            return result
        return None

    def ingest_finalized_pt1m_mark_sample_v1(
        self,
        *,
        venue: Any = None,
        canonical_instrument_id: Any = None,
        venue_instrument_id: Any = None,
        event_time_unix_seconds: Any = None,
        mark_price: Any = None,
        is_final: Any = True,
        sample: MarketSampleIdentityV1 | None = None,
        transport: ObservationTransportMetadataV1 | None = None,
    ) -> TypedRuntimeProducerResultV1:
        """Ingest one finalized PT1M mark sample through sample authority + P1/P2."""
        try:
            if sample is None:
                sample = validate_finalized_mark_sample_fields_v1(
                    venue=venue if venue is not None else self.history.venue,
                    canonical_instrument_id=(
                        canonical_instrument_id
                        if canonical_instrument_id is not None
                        else self.history.canonical_instrument_id
                    ),
                    venue_instrument_id=(
                        venue_instrument_id
                        if venue_instrument_id is not None
                        else self.history.venue_instrument_id
                    ),
                    event_time_unix_seconds=event_time_unix_seconds,
                    mark_price=mark_price,
                    is_final=is_final,
                )
            elif is_final is not True:
                raise RuntimeMarkHistoryError("UNFINALIZED_SAMPLE_REJECTED")
        except (
            RuntimeMarkHistoryError,
            TimeSampleEpochSemanticsErrorV1,
            TypeError,
            ValueError,
        ) as exc:
            result = TypedRuntimeProducerResultV1(
                outcome=TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED,
                estimate=None,
                history_digest=self.history.history_digest,
                observation_count_prices=self.history.observation_count_prices,
                as_of_event_time=(
                    None
                    if self.history.last_accepted_event_time is None
                    else _event_time_to_datetime(self.history.last_accepted_event_time)
                ),
                reason=f"invalid_sample:{exc}",
            )
            self._last_result = result
            return result

        prior_digest = self.history.history_digest
        prior_count = self.history.observation_count_prices
        prior_estimate = self._last_estimate
        prior_source = self._last_source_digest

        try:
            classification, record = self.history.try_advance_with_sample_v1(
                sample,
                is_final=True,
                transport=transport,
            )
        except RuntimeMarkHistoryError as exc:
            msg = str(exc)
            if "INSTRUMENT" in msg or "VENUE" in msg or "IDENTITY" in msg:
                outcome = TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED
            else:
                outcome = TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED
            result = TypedRuntimeProducerResultV1(
                outcome=outcome,
                estimate=None,
                history_digest=self.history.history_digest,
                observation_count_prices=self.history.observation_count_prices,
                as_of_event_time=(
                    None
                    if self.history.last_accepted_event_time is None
                    else _event_time_to_datetime(self.history.last_accepted_event_time)
                ),
                reason=msg,
            )
            self._last_result = result
            return result

        if classification is not ObservationClassification.DISTINCT:
            outcome = _classify_non_distinct(classification)
            # Guarantees: duplicate must not change history or estimate digests.
            assert self.history.history_digest == prior_digest
            assert self.history.observation_count_prices == prior_count
            assert self._last_estimate is prior_estimate
            assert self._last_source_digest is prior_source
            result = TypedRuntimeProducerResultV1(
                outcome=outcome,
                estimate=None,
                history_digest=self.history.history_digest,
                observation_count_prices=self.history.observation_count_prices,
                as_of_event_time=(
                    None
                    if self.history.last_accepted_event_time is None
                    else _event_time_to_datetime(self.history.last_accepted_event_time)
                ),
                reason=f"sample_authority:{classification.value}",
                sample_digest=None if record is None else record.sample_digest,
            )
            self._last_result = result
            return result

        assert record is not None
        persist_reject = self._persist_fail_closed()
        if persist_reject is not None:
            return persist_reject

        if self.history.observation_count_prices < REQUIRED_PRICE_OBSERVATIONS:
            result = TypedRuntimeProducerResultV1(
                outcome=TypedRuntimeProducerOutcomeV1.WARMUP,
                estimate=None,
                history_digest=self.history.history_digest,
                observation_count_prices=self.history.observation_count_prices,
                as_of_event_time=_event_time_to_datetime(record.event_time),
                reason=(
                    f"warmup_incomplete:prices={self.history.observation_count_prices}"
                    f":required={REQUIRED_PRICE_OBSERVATIONS}"
                ),
                sample_digest=record.sample_digest,
            )
            self._last_result = result
            return result

        trailing = self.history.trailing_window_records_v1(count=REQUIRED_PRICE_OBSERVATIONS)
        try:
            assert_pt1m_trailing_window_contiguous_v1(trailing)
        except RuntimeMarkHistoryError as exc:
            result = TypedRuntimeProducerResultV1(
                outcome=TypedRuntimeProducerOutcomeV1.HISTORY_GAP_REJECTED,
                estimate=None,
                history_digest=self.history.history_digest,
                observation_count_prices=self.history.observation_count_prices,
                as_of_event_time=_event_time_to_datetime(record.event_time),
                reason=str(exc),
                sample_digest=record.sample_digest,
            )
            self._last_result = result
            return result

        # Venue/instrument coherence over the closed window.
        bound = self.history.bound_instrument_key
        for item in trailing:
            if (
                item.venue != bound.venue
                or item.canonical_instrument_id != bound.canonical_instrument_id
                or item.venue_instrument_id != bound.venue_instrument_id
            ):
                result = TypedRuntimeProducerResultV1(
                    outcome=TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED,
                    estimate=None,
                    history_digest=self.history.history_digest,
                    observation_count_prices=self.history.observation_count_prices,
                    as_of_event_time=_event_time_to_datetime(record.event_time),
                    reason="trailing_window_instrument_incoherence",
                    sample_digest=record.sample_digest,
                )
                self._last_result = result
                return result

        series = self.history.mark_price_series_v1().iloc[-REQUIRED_PRICE_OBSERVATIONS:]
        as_of = _event_time_to_datetime(record.event_time)
        try:
            estimate = typed.materialize_typed_canonical_volatility_estimate_v1(
                series,
                as_of_event_time=as_of,
            )
        except (
            typed.CanonicalVolatilityTypedConsumptionError,
            materializer.CanonicalVolatilityEstimateMaterializerError,
        ) as exc:
            result = TypedRuntimeProducerResultV1(
                outcome=TypedRuntimeProducerOutcomeV1.MATERIALIZATION_REJECTED,
                estimate=None,
                history_digest=self.history.history_digest,
                observation_count_prices=self.history.observation_count_prices,
                as_of_event_time=as_of,
                reason=f"materialization_rejected:{exc}",
                sample_digest=record.sample_digest,
            )
            self._last_result = result
            return result

        if estimate.fallback_used is not False:
            result = TypedRuntimeProducerResultV1(
                outcome=TypedRuntimeProducerOutcomeV1.MATERIALIZATION_REJECTED,
                estimate=None,
                history_digest=self.history.history_digest,
                observation_count_prices=self.history.observation_count_prices,
                as_of_event_time=as_of,
                reason="fallback_used_must_be_false",
                sample_digest=record.sample_digest,
            )
            self._last_result = result
            return result

        # Event-time coherence: estimate as_of must match last used accepted sample.
        if estimate.as_of_event_time != as_of:
            result = TypedRuntimeProducerResultV1(
                outcome=TypedRuntimeProducerOutcomeV1.MATERIALIZATION_REJECTED,
                estimate=None,
                history_digest=self.history.history_digest,
                observation_count_prices=self.history.observation_count_prices,
                as_of_event_time=as_of,
                reason="as_of_event_time_coherence_failed",
                sample_digest=record.sample_digest,
            )
            self._last_result = result
            return result

        self._last_estimate = estimate
        self._last_source_digest = estimate.source_digest
        result = TypedRuntimeProducerResultV1(
            outcome=TypedRuntimeProducerOutcomeV1.PRODUCED,
            estimate=estimate,
            history_digest=self.history.history_digest,
            observation_count_prices=self.history.observation_count_prices,
            as_of_event_time=as_of,
            reason="produced_via_p1_p2",
            sample_digest=record.sample_digest,
        )
        self._last_result = result
        return result


def assert_capability_guards_v1() -> dict[str, Any]:
    """Machine-readable architecture guards / non-goals for this scaffold."""
    guards = {
        "capability_id": CAPABILITY_ID,
        "capability_version": CAPABILITY_VERSION,
        "producer_owner": PRODUCER_OWNER,
        "history_owner": HISTORY_OWNER,
        "history_capability_id": HISTORY_CAPABILITY_ID,
        "estimator_owner": materializer.MATERIALIZER_OWNER,
        "typed_factory_owner": typed.TYPED_CARRIER_OWNER,
        "semantics_owner": contract.CONTRACT_OWNER,
        "SINGLE_CANONICAL_VOLATILITY_ESTIMATOR": SINGLE_CANONICAL_VOLATILITY_ESTIMATOR,
        "SINGLE_TYPED_FACTORY": SINGLE_TYPED_FACTORY,
        "SINGLE_SAMPLE_ACCEPTANCE_AUTHORITY": SINGLE_SAMPLE_ACCEPTANCE_AUTHORITY,
        "SINGLE_EVENT_TIME_AUTHORITY": SINGLE_EVENT_TIME_AUTHORITY,
        "NO_SECOND_BINDING_ADAPTER": NO_SECOND_BINDING_ADAPTER,
        "NO_FLOAT_ONLY_RUNTIME_OUTPUT": NO_FLOAT_ONLY_RUNTIME_OUTPUT,
        "NO_SILENT_FALLBACK": NO_SILENT_FALLBACK,
        "NO_NUMERIC_FLOOR": NO_NUMERIC_FLOOR,
        "NO_RUNTIME_CUTOVER": NO_RUNTIME_CUTOVER,
        "NO_DOUBLE_PLAY_WIRING": NO_DOUBLE_PLAY_WIRING,
        "NO_PARAMETER_VALUE_DECISION": NO_PARAMETER_VALUE_DECISION,
        "FAIL_CLOSED": FAIL_CLOSED,
        "PRODUCTIVE_BIND_TYPED_CALLER": PRODUCTIVE_BIND_TYPED_CALLER,
        "CMC_RUNTIME_WIRING": CMC_RUNTIME_WIRING,
        "DOUBLE_PLAY_RUNTIME_WIRING": DOUBLE_PLAY_RUNTIME_WIRING,
        "P7_REPLACED": P7_REPLACED,
        "NUMERIC_MAX_AGE_DECIDED": NUMERIC_MAX_AGE_DECIDED,
        "RUNTIME_EFFECT": RUNTIME_EFFECT,
        "LIVE_AUTHORIZATION": LIVE_AUTHORIZATION,
        "forbidden_fallback_literals": list(FORBIDDEN_FALLBACK_LITERALS),
        "bar_interval_seconds": BAR_INTERVAL_SECONDS,
        "required_price_observations": REQUIRED_PRICE_OBSERVATIONS,
        "package_marker": PACKAGE_MARKER,
        "non_goals": [
            "runtime_cutover",
            "double_play_wiring",
            "productive_bind_typed",
            "cmc_runtime_mutation",
            "dynamic_scope_rules_wiring",
            "survival_suitability_composition_wiring",
            "p7_replacement",
            "numeric_max_age_decision",
            "parameter_value_decision",
            "silent_fallback",
            "numeric_floor",
        ],
    }
    if not all(
        (
            SINGLE_CANONICAL_VOLATILITY_ESTIMATOR,
            SINGLE_TYPED_FACTORY,
            SINGLE_SAMPLE_ACCEPTANCE_AUTHORITY,
            SINGLE_EVENT_TIME_AUTHORITY,
            NO_SECOND_BINDING_ADAPTER,
            NO_FLOAT_ONLY_RUNTIME_OUTPUT,
            NO_SILENT_FALLBACK,
            NO_NUMERIC_FLOOR,
            NO_RUNTIME_CUTOVER,
            NO_DOUBLE_PLAY_WIRING,
            NO_PARAMETER_VALUE_DECISION,
            FAIL_CLOSED,
        )
    ):
        raise RuntimeError("CAPABILITY_GUARD_DRIFT")
    if PRODUCTIVE_BIND_TYPED_CALLER or CMC_RUNTIME_WIRING or DOUBLE_PLAY_RUNTIME_WIRING:
        raise RuntimeError("WIRING_GUARD_DRIFT")
    if LIVE_AUTHORIZATION or RUNTIME_PRODUCER_CUTOVER or RUNTIME_WIRING:
        raise RuntimeError("ACTIVATION_GUARD_DRIFT")
    return guards


__all__ = [
    "BAR_INTERVAL_SECONDS",
    "CAPABILITY_ID",
    "CAPABILITY_VERSION",
    "CanonicalVolatilityTypedRuntimeProducerScaffoldV1",
    "FAIL_CLOSED",
    "FORBIDDEN_FALLBACK_LITERALS",
    "NO_DOUBLE_PLAY_WIRING",
    "NO_FLOAT_ONLY_RUNTIME_OUTPUT",
    "NO_NUMERIC_FLOOR",
    "NO_PARAMETER_VALUE_DECISION",
    "NO_RUNTIME_CUTOVER",
    "NO_SECOND_BINDING_ADAPTER",
    "NO_SILENT_FALLBACK",
    "PACKAGE_MARKER",
    "PRODUCER_OWNER",
    "PRODUCTIVE_BIND_TYPED_CALLER",
    "REQUIRED_PRICE_OBSERVATIONS",
    "SINGLE_CANONICAL_VOLATILITY_ESTIMATOR",
    "SINGLE_EVENT_TIME_AUTHORITY",
    "SINGLE_SAMPLE_ACCEPTANCE_AUTHORITY",
    "SINGLE_TYPED_FACTORY",
    "TypedRuntimeProducerOutcomeV1",
    "TypedRuntimeProducerOutputPortV1",
    "TypedRuntimeProducerResultV1",
    "assert_capability_guards_v1",
    "validate_finalized_mark_sample_fields_v1",
]
