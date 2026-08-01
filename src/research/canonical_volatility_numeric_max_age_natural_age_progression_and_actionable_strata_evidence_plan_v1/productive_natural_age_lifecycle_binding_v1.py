"""Productive-bridge CMC binding host owned by NaturalAgeProgressionLifecycleHostV1.

Replaces per-sample rematerialization authority on the productive research
evidence path. Master-V2 / Double-Play decision logic is unchanged; this host
only controls which typed estimate identity/as_of is bound into CMC so natural
age can accumulate under the research recompute contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.constants_v1 import (
    AGE_FORMULA_VERSION,
    AGE_REFERENCE_CLOCK,
    RESEARCH_WIRING_LABEL,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.lifecycle_contract_v1 import (
    LifecycleOutcomeV1,
    NaturalAgeLifecycleErrorV1,
    NaturalAgeLifecycleObservationV1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.lifecycle_host_v1 import (
    NaturalAgeProgressionLifecycleHostV1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.recompute_policy_v1 import (
    ResearchEstimateRecomputePolicyV1,
    build_natural_age_research_recompute_policy_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import MarketSampleIdentityV1
from trading.master_v2.canonical_market_context_v1 import (
    CanonicalMarketContextV1,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
    validate_typed_estimate_for_cmc_binding_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    LEGACY_ADAPTER_OWNER,
    CanonicalVolatilityEstimateV1,
    CanonicalVolatilityTypedConsumptionError,
    validate_canonical_volatility_estimate_v1,
)
from trading.master_v2.canonical_volatility_hot_path_contract_closure_v1 import (
    clear_untyped_productive_volatility_float_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    VolatilityRestartStatusV1,
    VolatilityReuseStatusV1,
    derive_reuse_and_restart_status_for_age_policy_v1,
)
from trading.master_v2.canonical_volatility_productive_runtime_cmc_typed_binding_v1 import (
    MAX_AGE_STATUS,
    ProductiveRuntimeCmcTypedBindingResultV1,
    ProductiveRuntimeCmcTypedBindingTelemetryV1,
    ProductiveTypedBindingFailClosedReasonV1,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    TypedRuntimeProducerOutcomeV1,
    TypedRuntimeProducerResultV1,
)

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_BRIDGE_"
    "NATURAL_AGE_LIFECYCLE_WIRING_V1=true"
)
CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_BRIDGE_"
    "NATURAL_AGE_LIFECYCLE_WIRING_V1"
)
NATURAL_AGE_LIFECYCLE_HOST_PRODUCTIVE_BOUND = True
LEGACY_PER_SAMPLE_REMATERIALIZATION_UNREACHABLE = True
SECOND_AGE_AUTHORITY_PRESENT = False
SECOND_DECISION_AUTHORITY_PRESENT = False


def _as_of_iso(estimate: CanonicalVolatilityEstimateV1 | None) -> Optional[str]:
    if estimate is None:
        return None
    as_of = estimate.as_of_event_time
    if isinstance(as_of, datetime):
        return as_of.isoformat()
    return str(as_of)


def _map_lifecycle_to_producer_outcome(
    outcome: str,
) -> TypedRuntimeProducerOutcomeV1:
    if outcome == LifecycleOutcomeV1.WARMUP.value:
        return TypedRuntimeProducerOutcomeV1.WARMUP
    if outcome == LifecycleOutcomeV1.DUPLICATE_NOOP.value:
        return TypedRuntimeProducerOutcomeV1.DUPLICATE_NOOP
    if outcome == LifecycleOutcomeV1.OUT_OF_ORDER_NOT_EVALUABLE.value:
        return TypedRuntimeProducerOutcomeV1.OUT_OF_ORDER_REJECTED
    if outcome == LifecycleOutcomeV1.INVALID_SAMPLE_REJECTED.value:
        return TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED
    if outcome in {
        LifecycleOutcomeV1.PRODUCED.value,
        LifecycleOutcomeV1.REUSED.value,
        LifecycleOutcomeV1.RECOMPUTED.value,
    }:
        return TypedRuntimeProducerOutcomeV1.PRODUCED
    if outcome == LifecycleOutcomeV1.RUNTIME_CYCLE_NOOP.value:
        return TypedRuntimeProducerOutcomeV1.DUPLICATE_NOOP
    return TypedRuntimeProducerOutcomeV1.MATERIALIZATION_REJECTED


def _fail_reason_for_lifecycle(
    obs: NaturalAgeLifecycleObservationV1,
    *,
    has_bind_estimate: bool,
    restart_without_estimate: bool,
    cycle_without_sample: bool,
) -> ProductiveTypedBindingFailClosedReasonV1:
    if restart_without_estimate and not has_bind_estimate:
        return ProductiveTypedBindingFailClosedReasonV1.RESTART_WITHOUT_ESTIMATE
    if obs.outcome == LifecycleOutcomeV1.WARMUP.value:
        return ProductiveTypedBindingFailClosedReasonV1.WARMUP_NO_ESTIMATE
    if obs.outcome == LifecycleOutcomeV1.DUPLICATE_NOOP.value and not has_bind_estimate:
        return ProductiveTypedBindingFailClosedReasonV1.DUPLICATE_WITHOUT_PRIOR_ESTIMATE
    if obs.outcome == LifecycleOutcomeV1.OUT_OF_ORDER_NOT_EVALUABLE.value:
        return ProductiveTypedBindingFailClosedReasonV1.OUT_OF_ORDER_REJECTED
    if obs.outcome == LifecycleOutcomeV1.INVALID_SAMPLE_REJECTED.value:
        return ProductiveTypedBindingFailClosedReasonV1.INVALID_SAMPLE_REJECTED
    if obs.outcome == LifecycleOutcomeV1.MISSING_ESTIMATE.value:
        return ProductiveTypedBindingFailClosedReasonV1.NO_SAMPLE_AND_NO_PRIOR_ESTIMATE
    if cycle_without_sample and not has_bind_estimate:
        return ProductiveTypedBindingFailClosedReasonV1.CYCLE_WITHOUT_SAMPLE_NO_ESTIMATE
    if not has_bind_estimate:
        return ProductiveTypedBindingFailClosedReasonV1.NO_SAMPLE_AND_NO_PRIOR_ESTIMATE
    return ProductiveTypedBindingFailClosedReasonV1.NONE


@dataclass(frozen=True)
class ProductiveNaturalAgeBindingTelemetryV1(ProductiveRuntimeCmcTypedBindingTelemetryV1):
    """CMC binding telemetry plus natural-age lifecycle authority fields."""

    lifecycle_outcome: str = ""
    natural_age_seconds: Optional[float] = None
    distinct_observations_since_recompute: int = 0
    recompute_reason: str = ""
    natural_age_lifecycle_host_bound: bool = True
    research_recompute_wiring_label: str = RESEARCH_WIRING_LABEL
    age_formula_version: str = AGE_FORMULA_VERSION
    age_reference_clock: str = AGE_REFERENCE_CLOCK
    volatility_value: Optional[float] = None
    volatility_unit: Optional[str] = None
    volatility_horizon_seconds: Optional[float] = None
    volatility_estimator: Optional[str] = None
    estimate_id: Optional[str] = None
    estimate_reused: bool = False
    reuse_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload.update(
            {
                "age_formula_version": self.age_formula_version,
                "age_reference_clock": self.age_reference_clock,
                "distinct_observations_since_recompute": (
                    self.distinct_observations_since_recompute
                ),
                "estimate_id": self.estimate_id,
                "estimate_reused": self.estimate_reused,
                "lifecycle_outcome": self.lifecycle_outcome,
                "natural_age_lifecycle_host_bound": self.natural_age_lifecycle_host_bound,
                "natural_age_seconds": self.natural_age_seconds,
                "recompute_reason": self.recompute_reason,
                "research_recompute_wiring_label": self.research_recompute_wiring_label,
                "reuse_count": self.reuse_count,
                "volatility_estimator": self.volatility_estimator,
                "volatility_horizon_seconds": self.volatility_horizon_seconds,
                "volatility_unit": self.volatility_unit,
                "volatility_value": self.volatility_value,
            }
        )
        return payload


@dataclass
class ProductiveNaturalAgeLifecycleCmcBindingHostV1:
    """Duck-typed CMC binding host for productive bridge natural-age wiring."""

    lifecycle: NaturalAgeProgressionLifecycleHostV1
    _restart_without_estimate: bool = False
    _produced_since_start_or_restore: bool = False
    _last_telemetry: Optional[ProductiveNaturalAgeBindingTelemetryV1] = None
    _last_observation: Optional[NaturalAgeLifecycleObservationV1] = None

    @classmethod
    def create(
        cls,
        *,
        venue: str,
        canonical_instrument_id: str,
        venue_instrument_id: str,
        persistence_path: Path | None = None,
        policy: ResearchEstimateRecomputePolicyV1 | None = None,
    ) -> "ProductiveNaturalAgeLifecycleCmcBindingHostV1":
        lifecycle = NaturalAgeProgressionLifecycleHostV1.create(
            venue=venue,
            canonical_instrument_id=canonical_instrument_id,
            venue_instrument_id=venue_instrument_id,
            persistence_path=persistence_path,
            policy=policy or build_natural_age_research_recompute_policy_v1(),
        )
        return cls(lifecycle=lifecycle)

    @classmethod
    def restore_from_persistence_v1(
        cls,
        *,
        persistence_path: Path,
        policy: ResearchEstimateRecomputePolicyV1 | None = None,
    ) -> "ProductiveNaturalAgeLifecycleCmcBindingHostV1":
        producer = CanonicalVolatilityTypedRuntimeProducerScaffoldV1.restore_from_persistence_v1(
            persistence_path=persistence_path,
        )
        lifecycle = NaturalAgeProgressionLifecycleHostV1(
            producer=producer,
            policy=policy or build_natural_age_research_recompute_policy_v1(),
        )
        return cls(
            lifecycle=lifecycle,
            _restart_without_estimate=True,
            _produced_since_start_or_restore=False,
        )

    @property
    def producer(self) -> CanonicalVolatilityTypedRuntimeProducerScaffoldV1:
        return self.lifecycle.producer

    @property
    def restart_without_estimate(self) -> bool:
        return bool(self._restart_without_estimate) and not self._produced_since_start_or_restore

    @property
    def last_telemetry(self) -> Optional[ProductiveNaturalAgeBindingTelemetryV1]:
        return self._last_telemetry

    @property
    def last_observation(self) -> Optional[NaturalAgeLifecycleObservationV1]:
        return self._last_observation

    def apply_to_market_context_v1(
        self,
        context: CanonicalMarketContextV1,
        *,
        sample: MarketSampleIdentityV1 | None = None,
        transport: ObservationTransportMetadataV1 | None = None,
        venue: Any = None,
        canonical_instrument_id: Any = None,
        venue_instrument_id: Any = None,
        event_time_unix_seconds: Any = None,
        mark_price: Any = None,
        is_final: Any = True,
        ingest_sample: bool = False,
    ) -> ProductiveRuntimeCmcTypedBindingResultV1:
        cycle_without_sample = not ingest_sample
        restart_pending_before_cycle = self.restart_without_estimate

        if ingest_sample:
            obs = self.lifecycle.ingest_finalized_pt1m_mark_sample_v1(
                sample=sample,
                transport=transport,
                venue=venue,
                canonical_instrument_id=canonical_instrument_id,
                venue_instrument_id=venue_instrument_id,
                event_time_unix_seconds=event_time_unix_seconds,
                mark_price=mark_price,
                is_final=is_final,
            )
        else:
            obs = self.lifecycle.on_runtime_cycle_without_sample_v1()
        self._last_observation = obs

        producer_outcome = _map_lifecycle_to_producer_outcome(obs.outcome)
        first_production_after_restart = False
        bind_estimate: Optional[CanonicalVolatilityEstimateV1] = None

        if obs.outcome in {
            LifecycleOutcomeV1.PRODUCED.value,
            LifecycleOutcomeV1.RECOMPUTED.value,
        }:
            if obs.lifecycle_state is None or obs.lifecycle_state.estimate is None:
                raise NaturalAgeLifecycleErrorV1("produced_without_lifecycle_state")
            bind_estimate = obs.lifecycle_state.estimate
            first_production_after_restart = restart_pending_before_cycle
            self._produced_since_start_or_restore = True
            self._restart_without_estimate = False
        elif obs.outcome == LifecycleOutcomeV1.REUSED.value:
            if obs.lifecycle_state is None or obs.lifecycle_state.estimate is None:
                raise NaturalAgeLifecycleErrorV1("reuse_without_lifecycle_state")
            bind_estimate = obs.lifecycle_state.estimate
            self._produced_since_start_or_restore = True
            self._restart_without_estimate = False
        elif obs.outcome in {
            LifecycleOutcomeV1.DUPLICATE_NOOP.value,
            LifecycleOutcomeV1.RUNTIME_CYCLE_NOOP.value,
        }:
            # Duplicate/runtime must not advance lifecycle counters; may keep prior bind.
            if self.lifecycle.lifecycle_state is not None and not self.restart_without_estimate:
                bind_estimate = self.lifecycle.lifecycle_state.estimate
        else:
            bind_estimate = None

        fail_reason = _fail_reason_for_lifecycle(
            obs,
            has_bind_estimate=bind_estimate is not None,
            restart_without_estimate=self.restart_without_estimate,
            cycle_without_sample=cycle_without_sample,
        )

        bound_context = context
        typed_binding_performed = False
        bound_estimate: Optional[CanonicalVolatilityEstimateV1] = None
        history_price_count = int(len(self.lifecycle.producer.history.records))
        producer_result = TypedRuntimeProducerResultV1(
            outcome=producer_outcome,
            estimate=bind_estimate if obs.age_evaluable else None,
            history_digest=str(self.lifecycle.producer.history.history_digest),
            observation_count_prices=history_price_count,
            as_of_event_time=None if bind_estimate is None else bind_estimate.as_of_event_time,
            reason=obs.not_evaluable_reason or obs.outcome,
            sample_digest=obs.source_digest,
        )

        if (
            bind_estimate is not None
            and fail_reason is ProductiveTypedBindingFailClosedReasonV1.NONE
        ):
            try:
                validated = validate_typed_estimate_for_cmc_binding_v1(bind_estimate)
                _ = validate_canonical_volatility_estimate_v1(validated)
                bound_context = bind_typed_canonical_volatility_estimate_into_market_context_v1(
                    context,
                    validated,
                )
                typed_binding_performed = True
                bound_estimate = bound_context.canonical_volatility_estimate
                fail_reason = ProductiveTypedBindingFailClosedReasonV1.NONE
            except (CanonicalVolatilityTypedConsumptionError, ValueError, TypeError) as exc:
                typed_binding_performed = False
                bound_estimate = None
                bound_context = clear_untyped_productive_volatility_float_v1(context)
                fail_reason = ProductiveTypedBindingFailClosedReasonV1.VALIDATION_REJECTED
                producer_result = TypedRuntimeProducerResultV1(
                    outcome=producer_result.outcome,
                    estimate=None,
                    history_digest=producer_result.history_digest,
                    observation_count_prices=producer_result.observation_count_prices,
                    as_of_event_time=producer_result.as_of_event_time,
                    reason=f"{producer_result.reason};binding_or_validation_rejected:{exc}",
                    sample_digest=producer_result.sample_digest,
                )
        else:
            bound_context = clear_untyped_productive_volatility_float_v1(context)
            typed_binding_performed = False
            bound_estimate = None

        typed_cutover_fail_closed = not typed_binding_performed
        reuse_status, restart_status = derive_reuse_and_restart_status_for_age_policy_v1(
            producer_outcome=producer_outcome.value,
            cycle_without_sample=cycle_without_sample,
            estimate_bound=bound_estimate is not None,
            restart_without_estimate=self.restart_without_estimate,
            first_production_after_restart=first_production_after_restart,
        )
        if obs.outcome == LifecycleOutcomeV1.REUSED.value and bound_estimate is not None:
            reuse_status = VolatilityReuseStatusV1.DUPLICATE_SAMPLE_REUSE
            restart_status = VolatilityRestartStatusV1.NOT_APPLICABLE
        elif (
            obs.outcome
            in {
                LifecycleOutcomeV1.PRODUCED.value,
                LifecycleOutcomeV1.RECOMPUTED.value,
            }
            and bound_estimate is not None
        ):
            reuse_status = VolatilityReuseStatusV1.FRESHLY_PRODUCED

        telemetry = ProductiveNaturalAgeBindingTelemetryV1(
            producer_outcome=obs.outcome,
            estimate_present=bound_estimate is not None,
            estimate_as_of_event_time=_as_of_iso(bound_estimate),
            observation_count=(
                None if bound_estimate is None else int(bound_estimate.observation_count)
            ),
            source_digest=(None if bound_estimate is None else str(bound_estimate.source_digest)),
            typed_binding_performed=typed_binding_performed,
            legacy_float_adaptation_owner=LEGACY_ADAPTER_OWNER,
            fail_closed_reason=fail_reason.value,
            restart_without_estimate=self.restart_without_estimate,
            reuse_status=reuse_status.value,
            restart_status=restart_status.value,
            max_age_status=MAX_AGE_STATUS,
            typed_cutover_fail_closed=typed_cutover_fail_closed,
            history_digest=str(self.lifecycle.producer.history.history_digest),
            lifecycle_outcome=obs.outcome,
            natural_age_seconds=obs.age_seconds,
            distinct_observations_since_recompute=int(obs.distinct_observations_since_recompute),
            recompute_reason=obs.recompute_reason,
            estimate_reused=bool(obs.estimate_reused),
            reuse_count=int(obs.reuse_count),
            volatility_value=None if bound_estimate is None else float(bound_estimate.value),
            # Evidence ledger uses research unit labels; typed carrier unit stays on estimate.
            volatility_unit=None if bound_estimate is None else "DECIMAL_FRACTION",
            volatility_horizon_seconds=(
                None if bound_estimate is None else float(bound_estimate.horizon_seconds)
            ),
            volatility_estimator=(
                None if bound_estimate is None else str(bound_estimate.estimator)
            ),
            estimate_id=(
                None if bound_estimate is None else f"est_{str(bound_estimate.source_digest)[:24]}"
            ),
        )
        self._last_telemetry = telemetry
        typed_binding_eligibility = evaluate_typed_volatility_binding_eligibility_v1(bound_context)
        return ProductiveRuntimeCmcTypedBindingResultV1(
            context=bound_context,
            producer_result=producer_result,
            telemetry=telemetry,
            typed_cutover_fail_closed=typed_cutover_fail_closed,
            bound_estimate=bound_estimate,
            typed_binding_eligibility=typed_binding_eligibility,
        )


def assert_natural_age_lifecycle_productive_binding_guards_v1(
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    binding_path = root / (
        "src/research/canonical_volatility_numeric_max_age_natural_age_progression_"
        "and_actionable_strata_evidence_plan_v1/productive_natural_age_lifecycle_binding_v1.py"
    )
    runner_path = root / (
        "src/research/canonical_volatility_max_age_productive_research_evidence_"
        "accumulation_v1/productive_bridge_runner_v1.py"
    )
    binding_src = binding_path.read_text(encoding="utf-8")
    runner_src = runner_path.read_text(encoding="utf-8")

    if "ProductiveNaturalAgeLifecycleCmcBindingHostV1" not in runner_src:
        raise RuntimeError("NATURAL_AGE_LIFECYCLE_HOST_NOT_BOUND_IN_PRODUCTIVE_RUNNER")
    if "CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.create" in runner_src:
        raise RuntimeError("LEGACY_CMC_BINDING_HOST_STILL_CREATED_IN_PRODUCTIVE_RUNNER")
    if "NaturalAgeProgressionLifecycleHostV1" not in binding_src:
        raise RuntimeError("LIFECYCLE_HOST_MISSING_FROM_BINDING_ADAPTER")
    if SECOND_AGE_AUTHORITY_PRESENT or SECOND_DECISION_AUTHORITY_PRESENT:
        raise RuntimeError("SECOND_AUTHORITY_FLAG_DRIFT")
    if not NATURAL_AGE_LIFECYCLE_HOST_PRODUCTIVE_BOUND:
        raise RuntimeError("NATURAL_AGE_LIFECYCLE_HOST_PRODUCTIVE_BOUND_DRIFT")
    if not LEGACY_PER_SAMPLE_REMATERIALIZATION_UNREACHABLE:
        raise RuntimeError("LEGACY_REMATERIALIZATION_GUARD_DRIFT")

    return {
        "NATURAL_AGE_LIFECYCLE_HOST_PRODUCTIVE_BOUND": True,
        "LEGACY_PER_SAMPLE_REMATERIALIZATION_UNREACHABLE": True,
        "SECOND_AGE_AUTHORITY_PRESENT": False,
        "SECOND_DECISION_AUTHORITY_PRESENT": False,
        "guards_pass": True,
        "capability_id": CAPABILITY_ID,
        "package_marker": PACKAGE_MARKER,
    }
