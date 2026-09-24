"""Research-only natural age lifecycle host wrapping the typed producer scaffold.

Does not wire Master-V2 / Double-Play hot path. Does not enforce max-age.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.lifecycle_contract_v1 import (
    LifecycleOutcomeV1,
    NaturalAgeLifecycleErrorV1,
    NaturalAgeLifecycleObservationV1,
    RecomputeReasonV1,
    VolatilityEstimateLifecycleState,
    assert_lifecycle_invariants_v1,
    compute_natural_age_seconds_v1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.recompute_policy_v1 import (
    ResearchEstimateRecomputePolicyV1,
    build_natural_age_research_recompute_policy_v1,
    evaluate_recompute_decision_v1,
)
from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.hold_v1 import (
    assert_non_regressing_age_v1,
    empty_age_bucket_observation_counts_v1,
    prereg_age_grid_coverage_complete_v1,
    record_age_bucket_observation_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import MarketSampleIdentityV1
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    TypedRuntimeProducerOutcomeV1,
)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


@dataclass
class NaturalAgeProgressionLifecycleHostV1:
    """Controls estimate recompute vs reuse for natural age evidence."""

    producer: CanonicalVolatilityTypedRuntimeProducerScaffoldV1
    policy: ResearchEstimateRecomputePolicyV1 = field(
        default_factory=build_natural_age_research_recompute_policy_v1
    )
    _lifecycle: Optional[VolatilityEstimateLifecycleState] = None
    _last_observation: Optional[NaturalAgeLifecycleObservationV1] = None
    _late_age_hold_active: bool = False
    _research_age_grid_seconds: tuple[int, ...] = ()
    _minimum_distinct_observations_per_age_bucket: int = 1
    _age_bucket_observation_counts: dict[str, int] = field(default_factory=dict)
    _last_retained_age_seconds: Optional[float] = None
    _track_age_grid_coverage: bool = False

    @classmethod
    def create(
        cls,
        *,
        venue: str,
        canonical_instrument_id: str,
        venue_instrument_id: str,
        persistence_path: Path | None = None,
        policy: ResearchEstimateRecomputePolicyV1 | None = None,
    ) -> "NaturalAgeProgressionLifecycleHostV1":
        producer = CanonicalVolatilityTypedRuntimeProducerScaffoldV1.create(
            venue=venue,
            canonical_instrument_id=canonical_instrument_id,
            venue_instrument_id=venue_instrument_id,
            persistence_path=persistence_path,
        )
        return cls(
            producer=producer,
            policy=policy or build_natural_age_research_recompute_policy_v1(),
        )

    @property
    def lifecycle_state(self) -> Optional[VolatilityEstimateLifecycleState]:
        return self._lifecycle

    @property
    def last_observation(self) -> Optional[NaturalAgeLifecycleObservationV1]:
        return self._last_observation

    @property
    def late_age_hold_active(self) -> bool:
        return bool(self._late_age_hold_active)

    @property
    def age_bucket_observation_counts(self) -> Mapping[str, int]:
        return dict(self._age_bucket_observation_counts)

    def enable_age_grid_coverage_tracking_v1(
        self,
        *,
        research_age_grid_seconds: Sequence[int],
        minimum_distinct_observations_per_age_bucket: int,
        initial_counts: Mapping[str, int] | None = None,
    ) -> None:
        grid = tuple(int(x) for x in research_age_grid_seconds)
        if not grid:
            raise NaturalAgeLifecycleErrorV1("research_age_grid_empty")
        if int(minimum_distinct_observations_per_age_bucket) < 1:
            raise NaturalAgeLifecycleErrorV1("minimum_distinct_observations_per_age_bucket_invalid")
        self._research_age_grid_seconds = grid
        self._minimum_distinct_observations_per_age_bucket = int(
            minimum_distinct_observations_per_age_bucket
        )
        counts = empty_age_bucket_observation_counts_v1(grid)
        if initial_counts is not None:
            for key, value in initial_counts.items():
                if key in counts:
                    counts[key] = int(value)
        self._age_bucket_observation_counts = counts
        self._track_age_grid_coverage = True

    def restore_retained_lifecycle_state_v1(
        self,
        state: VolatilityEstimateLifecycleState,
        *,
        research_age_grid_seconds: Sequence[int],
        minimum_distinct_observations_per_age_bucket: int,
        age_bucket_observation_counts: Mapping[str, int] | None = None,
        enable_late_age_hold: bool = True,
    ) -> None:
        """Restore retained estimate SSOT into lifecycle (no producer _last_estimate copy)."""
        if state is None or state.estimate is None:
            raise NaturalAgeLifecycleErrorV1("retained_lifecycle_state_required")
        self._lifecycle = state
        self.enable_age_grid_coverage_tracking_v1(
            research_age_grid_seconds=research_age_grid_seconds,
            minimum_distinct_observations_per_age_bucket=(
                minimum_distinct_observations_per_age_bucket
            ),
            initial_counts=age_bucket_observation_counts,
        )
        self._late_age_hold_active = bool(enable_late_age_hold)
        if self._late_age_hold_active and self._hold_exit_satisfied_v1():
            self._late_age_hold_active = False

    def _hold_exit_satisfied_v1(self) -> bool:
        if not self._research_age_grid_seconds:
            return False
        return prereg_age_grid_coverage_complete_v1(
            self._age_bucket_observation_counts,
            grid_seconds=self._research_age_grid_seconds,
            minimum_distinct_observations_per_age_bucket=(
                self._minimum_distinct_observations_per_age_bucket
            ),
        )

    def _record_coverage_and_maybe_exit_hold_v1(self, *, age_seconds: float) -> None:
        if not self._track_age_grid_coverage:
            return
        if self._late_age_hold_active:
            try:
                assert_non_regressing_age_v1(
                    prior_age_seconds=self._last_retained_age_seconds,
                    current_age_seconds=float(age_seconds),
                )
            except Exception as exc:  # noqa: BLE001 — map carrier hold errors
                raise NaturalAgeLifecycleErrorV1(str(exc)) from exc
        self._last_retained_age_seconds = float(age_seconds)
        record_age_bucket_observation_v1(
            self._age_bucket_observation_counts,
            age_seconds=float(age_seconds),
            grid_seconds=self._research_age_grid_seconds,
        )
        if self._late_age_hold_active and self._hold_exit_satisfied_v1():
            self._late_age_hold_active = False

    def _reuse_retained_estimate_v1(
        self,
        *,
        market_iso: str,
        prior: VolatilityEstimateLifecycleState,
    ) -> NaturalAgeLifecycleObservationV1:
        reused_state = VolatilityEstimateLifecycleState(
            estimate=prior.estimate,
            produced_at_market_event_time=prior.produced_at_market_event_time,
            last_recompute_reason=prior.last_recompute_reason,
            reuse_count=prior.reuse_count + 1,
            distinct_observations_since_recompute=(prior.distinct_observations_since_recompute + 1),
            source_window_start_event_time=prior.source_window_start_event_time,
            source_window_end_event_time=prior.source_window_end_event_time,
            source_digest=prior.source_digest,
        )
        assert_lifecycle_invariants_v1(prior, reused_state, reused=True)
        age = compute_natural_age_seconds_v1(
            market_event_time=market_iso,
            as_of_event_time=_iso(reused_state.as_of_event_time),
        )
        self._record_coverage_and_maybe_exit_hold_v1(age_seconds=age)
        obs = NaturalAgeLifecycleObservationV1(
            outcome=LifecycleOutcomeV1.REUSED.value,
            market_event_time=market_iso,
            as_of_event_time=_iso(reused_state.as_of_event_time),
            age_seconds=age,
            estimate_reused=True,
            reuse_count=reused_state.reuse_count,
            distinct_observations_since_recompute=(
                reused_state.distinct_observations_since_recompute
            ),
            source_digest=reused_state.source_digest,
            recompute_reason=RecomputeReasonV1.NOT_APPLICABLE.value,
            age_evaluable=True,
            not_evaluable_reason="",
            lifecycle_state=reused_state,
        )
        self._lifecycle = reused_state
        self._last_observation = obs
        return obs

    def on_runtime_cycle_without_sample_v1(self) -> NaturalAgeLifecycleObservationV1:
        """Runtime/poll cycles must not advance age."""
        state = self._lifecycle
        obs = NaturalAgeLifecycleObservationV1(
            outcome=LifecycleOutcomeV1.RUNTIME_CYCLE_NOOP.value,
            market_event_time=None if state is None else state.produced_at_market_event_time,
            as_of_event_time=None if state is None else _iso(state.as_of_event_time),
            age_seconds=None,
            estimate_reused=False,
            reuse_count=0 if state is None else state.reuse_count,
            distinct_observations_since_recompute=(
                0 if state is None else state.distinct_observations_since_recompute
            ),
            source_digest=None if state is None else state.source_digest,
            recompute_reason=RecomputeReasonV1.NOT_APPLICABLE.value,
            age_evaluable=False,
            not_evaluable_reason="runtime_cycle_without_new_distinct_observation",
            lifecycle_state=state,
        )
        self._last_observation = obs
        _ = self.producer.on_runtime_cycle_without_sample_v1()
        return obs

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
    ) -> NaturalAgeLifecycleObservationV1:
        result = self.producer.ingest_finalized_pt1m_mark_sample_v1(
            venue=venue,
            canonical_instrument_id=canonical_instrument_id,
            venue_instrument_id=venue_instrument_id,
            event_time_unix_seconds=event_time_unix_seconds,
            mark_price=mark_price,
            is_final=is_final,
            sample=sample,
            transport=transport,
        )
        outcome = result.outcome

        if outcome is TypedRuntimeProducerOutcomeV1.DUPLICATE_NOOP:
            return self._noop_observation(
                LifecycleOutcomeV1.DUPLICATE_NOOP,
                market_event_time=result.as_of_event_time,
                reason="duplicate_observation_no_age_or_reuse_advance",
            )
        if outcome is TypedRuntimeProducerOutcomeV1.OUT_OF_ORDER_REJECTED:
            return self._noop_observation(
                LifecycleOutcomeV1.OUT_OF_ORDER_NOT_EVALUABLE,
                market_event_time=result.as_of_event_time,
                reason="out_of_order_observation_not_evaluable",
            )
        if outcome in {
            TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED,
            TypedRuntimeProducerOutcomeV1.HISTORY_GAP_REJECTED,
            TypedRuntimeProducerOutcomeV1.PERSISTENCE_REJECTED,
            TypedRuntimeProducerOutcomeV1.MATERIALIZATION_REJECTED,
        }:
            return self._noop_observation(
                LifecycleOutcomeV1.INVALID_SAMPLE_REJECTED,
                market_event_time=result.as_of_event_time,
                reason=str(result.reason),
            )
        if outcome is TypedRuntimeProducerOutcomeV1.WARMUP:
            return self._noop_observation(
                LifecycleOutcomeV1.WARMUP,
                market_event_time=result.as_of_event_time,
                reason=str(result.reason),
            )
        if outcome is not TypedRuntimeProducerOutcomeV1.PRODUCED or result.estimate is None:
            return self._noop_observation(
                LifecycleOutcomeV1.MISSING_ESTIMATE,
                market_event_time=result.as_of_event_time,
                reason=f"unexpected_producer_outcome:{outcome.value}",
            )

        market_dt = result.as_of_event_time
        if market_dt is None:
            raise NaturalAgeLifecycleErrorV1("produced_without_market_event_time")
        market_iso = _iso(market_dt)
        new_estimate = result.estimate
        window_start = (
            None
            if new_estimate.oldest_observation_event_time is None
            else _iso(new_estimate.oldest_observation_event_time)
        )
        window_end = market_iso

        should_recompute, reason = evaluate_recompute_decision_v1(
            policy=self.policy,
            prior_state=self._lifecycle,
            current_market_event_time=market_iso,
            newly_materialized_source_digest=new_estimate.source_digest,
            prior_invalid=False,
        )

        if self._late_age_hold_active:
            if self._lifecycle is None:
                raise NaturalAgeLifecycleErrorV1("fresh_produce_attempt_during_late_age_hold")
            if reason in {
                RecomputeReasonV1.SESSION_START_FIRST_ESTIMATE.value,
                RecomputeReasonV1.MISSING_ESTIMATE.value,
                RecomputeReasonV1.INVALID_PRIOR_ESTIMATE.value,
            }:
                raise NaturalAgeLifecycleErrorV1("fresh_produce_attempt_during_late_age_hold")
            # Suppress elapsed / obs-floor recompute while hold is active; reuse retained SSOT.
            return self._reuse_retained_estimate_v1(market_iso=market_iso, prior=self._lifecycle)

        if should_recompute or self._lifecycle is None:
            state = VolatilityEstimateLifecycleState(
                estimate=new_estimate,
                produced_at_market_event_time=_iso(new_estimate.as_of_event_time),
                last_recompute_reason=reason,
                reuse_count=0,
                distinct_observations_since_recompute=0,
                source_window_start_event_time=window_start or market_iso,
                source_window_end_event_time=window_end,
                source_digest=new_estimate.source_digest,
            )
            age = compute_natural_age_seconds_v1(
                market_event_time=market_iso,
                as_of_event_time=_iso(state.as_of_event_time),
            )
            self._record_coverage_and_maybe_exit_hold_v1(age_seconds=age)
            obs = NaturalAgeLifecycleObservationV1(
                outcome=(
                    LifecycleOutcomeV1.PRODUCED.value
                    if reason == RecomputeReasonV1.SESSION_START_FIRST_ESTIMATE.value
                    else LifecycleOutcomeV1.RECOMPUTED.value
                ),
                market_event_time=market_iso,
                as_of_event_time=_iso(state.as_of_event_time),
                age_seconds=age,
                estimate_reused=False,
                reuse_count=0,
                distinct_observations_since_recompute=0,
                source_digest=state.source_digest,
                recompute_reason=reason,
                age_evaluable=True,
                not_evaluable_reason="",
                lifecycle_state=state,
            )
            self._lifecycle = state
            self._last_observation = obs
            return obs

        # Explicit reuse: keep prior estimate identity / as_of immutable.
        return self._reuse_retained_estimate_v1(market_iso=market_iso, prior=self._lifecycle)

    def _noop_observation(
        self,
        outcome: LifecycleOutcomeV1,
        *,
        market_event_time: Optional[datetime],
        reason: str,
    ) -> NaturalAgeLifecycleObservationV1:
        state = self._lifecycle
        obs = NaturalAgeLifecycleObservationV1(
            outcome=outcome.value,
            market_event_time=None if market_event_time is None else _iso(market_event_time),
            as_of_event_time=None if state is None else _iso(state.as_of_event_time),
            age_seconds=None,
            estimate_reused=False,
            reuse_count=0 if state is None else state.reuse_count,
            distinct_observations_since_recompute=(
                0 if state is None else state.distinct_observations_since_recompute
            ),
            source_digest=None if state is None else state.source_digest,
            recompute_reason=RecomputeReasonV1.NOT_APPLICABLE.value,
            age_evaluable=False,
            not_evaluable_reason=reason,
            lifecycle_state=state,
        )
        self._last_observation = obs
        return obs
