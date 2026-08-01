"""Productive Runtime CMC typed binding v1 (OPTION_2 edge).

Closes the productive edge:

  CanonicalVolatilityTypedRuntimeProducerScaffoldV1
    → bind_typed_canonical_volatility_estimate_into_market_context_v1
    → CanonicalMarketContextV1

Reuses existing producer, validation, binding, and Typed→Float authorities.
Does **not** introduce a second estimator, binder, adapter, numeric max-age,
global typed-only enforcement, or Double-Play typed cutover.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import MarketSampleIdentityV1
from trading.master_v2.canonical_market_context_v1 import (
    CanonicalMarketContextEligibilityV1,
    CanonicalMarketContextV1,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    BINDING_OWNER,
    LEGACY_ADAPTATION_BOUNDARY,
    VolatilityStaleStatusV1,
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
from trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    derive_reuse_and_restart_status_for_age_policy_v1,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    TypedRuntimeProducerOutcomeV1,
    TypedRuntimeProducerResultV1,
)

PACKAGE_MARKER = "MASTER_V2_CANONICAL_VOLATILITY_PRODUCTIVE_RUNTIME_CMC_TYPED_BINDING_V1=true"

CAPABILITY_ID = "MASTER_V2_CANONICAL_VOLATILITY_PRODUCTIVE_RUNTIME_CMC_TYPED_BINDING_V1"
CAPABILITY_VERSION = "canonical_volatility_productive_runtime_cmc_typed_binding/v1"
BINDING_RUNTIME_OWNER = (
    "trading.master_v2.canonical_volatility_productive_runtime_cmc_typed_binding_v1"
)
PRODUCTIVE_RUNTIME_CALLER_OWNER = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
    ".hardening_cycle_bridge_v2"
)

PRODUCTIVE_BIND_TYPED_CALLER = True
CMC_RUNTIME_WIRING = True
DOUBLE_PLAY_TYPED_CUTOVER = False
GLOBAL_TYPED_ONLY_ENFORCEMENT = False
NUMERIC_MAX_AGE_DECIDED = False
LIVE_AUTHORIZATION = False
HARD_STOP = True
SECOND_ESTIMATOR_CREATED = False
SECOND_BINDING_AUTHORITY_CREATED = False
SECOND_ADAPTATION_AUTHORITY_CREATED = False
STATIC_RUNTIME_FALLBACK_USED = False
EXPLICIT_LEGACY_QUARANTINE_CHANGED = False
COMPETING_PRODUCERS_CHANGED = False

MAX_AGE_STATUS = VolatilityStaleStatusV1.UNRESOLVED_MAX_AGE.value
LEGACY_FLOAT_ADAPTATION_OWNER = LEGACY_ADAPTER_OWNER

# Outcomes that must not bind a new or reused estimate into CMC this cycle.
_REJECT_NO_BINDING_OUTCOMES: frozenset[TypedRuntimeProducerOutcomeV1] = frozenset(
    {
        TypedRuntimeProducerOutcomeV1.OUT_OF_ORDER_REJECTED,
        TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED,
        TypedRuntimeProducerOutcomeV1.HISTORY_GAP_REJECTED,
        TypedRuntimeProducerOutcomeV1.PERSISTENCE_REJECTED,
        TypedRuntimeProducerOutcomeV1.MATERIALIZATION_REJECTED,
    }
)

_REUSE_ALLOWED_OUTCOMES: frozenset[TypedRuntimeProducerOutcomeV1] = frozenset(
    {
        TypedRuntimeProducerOutcomeV1.DUPLICATE_NOOP,
        TypedRuntimeProducerOutcomeV1.PRODUCED,
    }
)


class ProductiveTypedBindingFailClosedReasonV1(str, Enum):
    NONE = "NONE"
    WARMUP_NO_ESTIMATE = "WARMUP_NO_ESTIMATE"
    DUPLICATE_WITHOUT_PRIOR_ESTIMATE = "DUPLICATE_WITHOUT_PRIOR_ESTIMATE"
    OUT_OF_ORDER_REJECTED = "OUT_OF_ORDER_REJECTED"
    INVALID_SAMPLE_REJECTED = "INVALID_SAMPLE_REJECTED"
    HISTORY_GAP_REJECTED = "HISTORY_GAP_REJECTED"
    PERSISTENCE_REJECTED = "PERSISTENCE_REJECTED"
    MATERIALIZATION_REJECTED = "MATERIALIZATION_REJECTED"
    RESTART_WITHOUT_ESTIMATE = "RESTART_WITHOUT_ESTIMATE"
    CYCLE_WITHOUT_SAMPLE_NO_ESTIMATE = "CYCLE_WITHOUT_SAMPLE_NO_ESTIMATE"
    VALIDATION_REJECTED = "VALIDATION_REJECTED"
    BINDING_REJECTED = "BINDING_REJECTED"
    NO_SAMPLE_AND_NO_PRIOR_ESTIMATE = "NO_SAMPLE_AND_NO_PRIOR_ESTIMATE"


@dataclass(frozen=True)
class ProductiveRuntimeCmcTypedBindingTelemetryV1:
    producer_outcome: str
    estimate_present: bool
    estimate_as_of_event_time: Optional[str]
    observation_count: Optional[int]
    source_digest: Optional[str]
    typed_binding_performed: bool
    legacy_float_adaptation_owner: str
    fail_closed_reason: str
    restart_without_estimate: bool
    reuse_status: str
    restart_status: str
    max_age_status: str
    typed_cutover_fail_closed: bool
    history_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "producer_outcome": self.producer_outcome,
            "estimate_present": self.estimate_present,
            "estimate_as_of_event_time": self.estimate_as_of_event_time,
            "observation_count": self.observation_count,
            "source_digest": self.source_digest,
            "typed_binding_performed": self.typed_binding_performed,
            "legacy_float_adaptation_owner": self.legacy_float_adaptation_owner,
            "fail_closed_reason": self.fail_closed_reason,
            "restart_without_estimate": self.restart_without_estimate,
            "reuse_status": self.reuse_status,
            "restart_status": self.restart_status,
            "max_age_status": self.max_age_status,
            "typed_cutover_fail_closed": self.typed_cutover_fail_closed,
            "history_digest": self.history_digest,
        }


@dataclass(frozen=True)
class ProductiveRuntimeCmcTypedBindingResultV1:
    context: CanonicalMarketContextV1
    producer_result: TypedRuntimeProducerResultV1
    telemetry: ProductiveRuntimeCmcTypedBindingTelemetryV1
    typed_cutover_fail_closed: bool
    bound_estimate: Optional[CanonicalVolatilityEstimateV1]
    # Eligibility is always computed and must be consumed by the presence gate —
    # never discarded.
    typed_binding_eligibility: CanonicalMarketContextEligibilityV1

    def to_dict(self) -> dict[str, Any]:
        return {
            "telemetry": self.telemetry.to_dict(),
            "typed_cutover_fail_closed": self.typed_cutover_fail_closed,
            "bound_estimate_present": self.bound_estimate is not None,
            "producer_outcome": self.producer_result.outcome.value,
            "producer_reason": self.producer_result.reason,
            "typed_binding_eligibility_block_reasons": [
                r.value for r in self.typed_binding_eligibility.block_reasons
            ],
            "typed_binding_eligibility_scope_allowed": (
                self.typed_binding_eligibility.scope_confirmation_allowed
            ),
            "typed_binding_eligibility_exposure_allowed": (
                self.typed_binding_eligibility.new_directional_exposure_allowed
            ),
        }


def _as_of_iso(estimate: CanonicalVolatilityEstimateV1 | None) -> Optional[str]:
    if estimate is None:
        return None
    as_of = estimate.as_of_event_time
    if isinstance(as_of, datetime):
        return as_of.isoformat()
    return str(as_of)


def _fail_reason_for_outcome(
    outcome: TypedRuntimeProducerOutcomeV1,
    *,
    restart_without_estimate: bool,
    has_reusable_estimate: bool,
    cycle_without_sample: bool,
) -> ProductiveTypedBindingFailClosedReasonV1:
    if restart_without_estimate and not has_reusable_estimate:
        return ProductiveTypedBindingFailClosedReasonV1.RESTART_WITHOUT_ESTIMATE
    if outcome is TypedRuntimeProducerOutcomeV1.WARMUP:
        return ProductiveTypedBindingFailClosedReasonV1.WARMUP_NO_ESTIMATE
    if outcome is TypedRuntimeProducerOutcomeV1.DUPLICATE_NOOP and not has_reusable_estimate:
        return ProductiveTypedBindingFailClosedReasonV1.DUPLICATE_WITHOUT_PRIOR_ESTIMATE
    if outcome is TypedRuntimeProducerOutcomeV1.OUT_OF_ORDER_REJECTED:
        return ProductiveTypedBindingFailClosedReasonV1.OUT_OF_ORDER_REJECTED
    if outcome is TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED:
        return ProductiveTypedBindingFailClosedReasonV1.INVALID_SAMPLE_REJECTED
    if outcome is TypedRuntimeProducerOutcomeV1.HISTORY_GAP_REJECTED:
        return ProductiveTypedBindingFailClosedReasonV1.HISTORY_GAP_REJECTED
    if outcome is TypedRuntimeProducerOutcomeV1.PERSISTENCE_REJECTED:
        return ProductiveTypedBindingFailClosedReasonV1.PERSISTENCE_REJECTED
    if outcome is TypedRuntimeProducerOutcomeV1.MATERIALIZATION_REJECTED:
        return ProductiveTypedBindingFailClosedReasonV1.MATERIALIZATION_REJECTED
    if cycle_without_sample and not has_reusable_estimate:
        return ProductiveTypedBindingFailClosedReasonV1.CYCLE_WITHOUT_SAMPLE_NO_ESTIMATE
    if not has_reusable_estimate:
        return ProductiveTypedBindingFailClosedReasonV1.NO_SAMPLE_AND_NO_PRIOR_ESTIMATE
    return ProductiveTypedBindingFailClosedReasonV1.NONE


@dataclass
class CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1:
    """Persistent host: exactly one typed runtime producer + productive CMC bind."""

    producer: CanonicalVolatilityTypedRuntimeProducerScaffoldV1
    _restart_without_estimate: bool = False
    _produced_since_start_or_restore: bool = False
    _last_telemetry: Optional[ProductiveRuntimeCmcTypedBindingTelemetryV1] = None

    @classmethod
    def create(
        cls,
        *,
        venue: str,
        canonical_instrument_id: str,
        venue_instrument_id: str,
        persistence_path: Path | None = None,
    ) -> "CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1":
        producer = CanonicalVolatilityTypedRuntimeProducerScaffoldV1.create(
            venue=venue,
            canonical_instrument_id=canonical_instrument_id,
            venue_instrument_id=venue_instrument_id,
            persistence_path=persistence_path,
        )
        return cls(producer=producer)

    @classmethod
    def restore_from_persistence_v1(
        cls,
        *,
        persistence_path: Path,
    ) -> "CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1":
        producer = CanonicalVolatilityTypedRuntimeProducerScaffoldV1.restore_from_persistence_v1(
            persistence_path=persistence_path,
        )
        # History restored; estimate is NOT rematerialized (fail-closed until PRODUCED).
        return cls(
            producer=producer,
            _restart_without_estimate=True,
            _produced_since_start_or_restore=False,
        )

    @property
    def restart_without_estimate(self) -> bool:
        return bool(self._restart_without_estimate) and not self._produced_since_start_or_restore

    @property
    def last_telemetry(self) -> Optional[ProductiveRuntimeCmcTypedBindingTelemetryV1]:
        return self._last_telemetry

    def _reusable_estimate_v1(self) -> Optional[CanonicalVolatilityEstimateV1]:
        if self.restart_without_estimate:
            return None
        port = self.producer.output_port_v1()
        if not port.ready_for_binding_handoff or port.estimate is None:
            return None
        return port.estimate

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
        """Ingest optional finalized PT1M sample and bind typed estimate into CMC.

        ``ingest_sample=True`` requires either ``sample`` or raw finalized mark fields.
        When ``ingest_sample=False``, treats the cycle as without a new sample and may
        reuse a previously PRODUCED estimate via the producer output port.
        """
        cycle_without_sample = not ingest_sample
        restart_pending_before_cycle = self.restart_without_estimate
        if ingest_sample:
            producer_result = self.producer.ingest_finalized_pt1m_mark_sample_v1(
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
            producer_result = self.producer.on_runtime_cycle_without_sample_v1()

        outcome = producer_result.outcome
        first_production_after_restart = False
        if (
            outcome is TypedRuntimeProducerOutcomeV1.PRODUCED
            and producer_result.estimate is not None
        ):
            first_production_after_restart = restart_pending_before_cycle
            self._produced_since_start_or_restore = True
            self._restart_without_estimate = False

        reusable = self._reusable_estimate_v1()
        bind_estimate: Optional[CanonicalVolatilityEstimateV1] = None
        fail_reason = ProductiveTypedBindingFailClosedReasonV1.NONE

        if (
            outcome is TypedRuntimeProducerOutcomeV1.PRODUCED
            and producer_result.estimate is not None
        ):
            bind_estimate = producer_result.estimate
        elif (
            outcome in _REUSE_ALLOWED_OUTCOMES or cycle_without_sample
        ) and outcome not in _REJECT_NO_BINDING_OUTCOMES:
            if reusable is not None and not self.restart_without_estimate:
                # Process-internal reuse only; UNRESOLVED_MAX_AGE is not freshness approval.
                bind_estimate = reusable
            else:
                fail_reason = _fail_reason_for_outcome(
                    outcome,
                    restart_without_estimate=self.restart_without_estimate,
                    has_reusable_estimate=False,
                    cycle_without_sample=cycle_without_sample,
                )
        else:
            fail_reason = _fail_reason_for_outcome(
                outcome,
                restart_without_estimate=self.restart_without_estimate,
                has_reusable_estimate=reusable is not None,
                cycle_without_sample=cycle_without_sample,
            )
            bind_estimate = None

        if self.restart_without_estimate and bind_estimate is None:
            fail_reason = ProductiveTypedBindingFailClosedReasonV1.RESTART_WITHOUT_ESTIMATE

        bound_context = context
        typed_binding_performed = False
        bound_estimate: Optional[CanonicalVolatilityEstimateV1] = None

        if bind_estimate is not None:
            try:
                validated = validate_typed_estimate_for_cmc_binding_v1(bind_estimate)
                # Single validation boundary (typed contract) + single binder.
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
                bound_context = replace(
                    context,
                    canonical_volatility_estimate=None,
                )
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
            # Fail-closed typed cutover: do not carry a prior typed carrier into this cycle.
            if context.canonical_volatility_estimate is not None:
                bound_context = replace(context, canonical_volatility_estimate=None)
            typed_binding_performed = False
            bound_estimate = None

        typed_cutover_fail_closed = not typed_binding_performed
        estimate_for_telemetry = bound_estimate
        reuse_status, restart_status = derive_reuse_and_restart_status_for_age_policy_v1(
            producer_outcome=outcome.value,
            cycle_without_sample=cycle_without_sample,
            estimate_bound=estimate_for_telemetry is not None,
            restart_without_estimate=self.restart_without_estimate,
            first_production_after_restart=first_production_after_restart,
        )
        telemetry = ProductiveRuntimeCmcTypedBindingTelemetryV1(
            producer_outcome=outcome.value,
            estimate_present=estimate_for_telemetry is not None,
            estimate_as_of_event_time=_as_of_iso(estimate_for_telemetry),
            observation_count=(
                None
                if estimate_for_telemetry is None
                else int(estimate_for_telemetry.observation_count)
            ),
            source_digest=(
                None
                if estimate_for_telemetry is None
                else str(estimate_for_telemetry.source_digest)
            ),
            typed_binding_performed=typed_binding_performed,
            legacy_float_adaptation_owner=LEGACY_FLOAT_ADAPTATION_OWNER,
            fail_closed_reason=fail_reason.value,
            restart_without_estimate=self.restart_without_estimate,
            reuse_status=reuse_status.value,
            restart_status=restart_status.value,
            max_age_status=MAX_AGE_STATUS,
            typed_cutover_fail_closed=typed_cutover_fail_closed,
            history_digest=str(self.producer.history.history_digest),
        )
        self._last_telemetry = telemetry

        # Always compute eligibility and return it for the presence gate to consume.
        # This capability does not itself authorize Double-Play cutover.
        typed_binding_eligibility = evaluate_typed_volatility_binding_eligibility_v1(bound_context)

        return ProductiveRuntimeCmcTypedBindingResultV1(
            context=bound_context,
            producer_result=producer_result,
            telemetry=telemetry,
            typed_cutover_fail_closed=typed_cutover_fail_closed,
            bound_estimate=bound_estimate,
            typed_binding_eligibility=typed_binding_eligibility,
        )


def assert_architecture_guards_v1(*, repo_root: Optional[Path] = None) -> dict[str, Any]:
    """Guards: single adapter/binder/estimator; productive caller outside tests."""
    root = repo_root or Path(__file__).resolve().parents[3]
    this_src = (
        root
        / "src/trading/master_v2/canonical_volatility_productive_runtime_cmc_typed_binding_v1.py"
    ).read_text(encoding="utf-8")
    typed_src = (
        root
        / "src/trading/master_v2/canonical_volatility_estimate_typed_consumption_contract_v1.py"
    ).read_text(encoding="utf-8")
    binding_src = (
        root / "src/trading/master_v2/canonical_volatility_binding_and_provenance_transport_v1.py"
    ).read_text(encoding="utf-8")
    bridge_src = (
        root
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
        / "hardening_cycle_bridge_v2.py"
    ).read_text(encoding="utf-8")
    producer_src = (
        root / "src/trading/master_v2/canonical_volatility_typed_runtime_producer_scaffold_v1.py"
    ).read_text(encoding="utf-8")

    adapter_def = "def " + "adapt_canonical_volatility_estimate_to_legacy_float_v1("
    binder_def = "def " + "bind_typed_canonical_volatility_estimate_into_market_context_v1("
    materializer_def = "def " + "compute_canonical_volatility_estimate_from_mark_prices_v1("

    if typed_src.count(adapter_def) != 1:
        raise RuntimeError("EXPECTED_EXACTLY_ONE_TYPED_TO_FLOAT_ADAPTER_DEF")
    if this_src.count(adapter_def) != 0:
        raise RuntimeError("SECOND_ADAPTER_DEF_IN_PRODUCTIVE_BINDING_FORBIDDEN")
    if binding_src.count(binder_def) != 1:
        raise RuntimeError("EXPECTED_EXACTLY_ONE_BIND_TYPED_DEF")
    if this_src.count(binder_def) != 0:
        raise RuntimeError("SECOND_BINDER_DEF_IN_PRODUCTIVE_BINDING_FORBIDDEN")
    if this_src.count(materializer_def) != 0:
        raise RuntimeError("SECOND_ESTIMATOR_DEF_IN_PRODUCTIVE_BINDING_FORBIDDEN")

    # Productive caller must live in hardening bridge (not only tests).
    if "CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1" not in bridge_src:
        raise RuntimeError("PRODUCTIVE_RUNTIME_CALLER_MISSING_IN_HARDENING_BRIDGE")
    if "apply_to_market_context_v1" not in bridge_src:
        raise RuntimeError("PRODUCTIVE_RUNTIME_CMC_BIND_CALL_MISSING")
    if "bind_typed_canonical_volatility_estimate_into_market_context_v1" not in this_src:
        raise RuntimeError("PRODUCTIVE_BINDING_MUST_CALL_EXISTING_BIND_TYPED")

    code_before_guards = this_src.split("def assert_architecture_guards_v1", 1)[0]
    if "adapt_canonical_volatility_estimate_to_legacy_float_v1(" in code_before_guards:
        raise RuntimeError("DIRECT_TYPED_TO_FLOAT_CALL_IN_HOST_FORBIDDEN")

    forbidden_value_extract = "canonical_volatility_estimate.value"
    if forbidden_value_extract in bridge_src or forbidden_value_extract in code_before_guards:
        raise RuntimeError("LOCAL_ESTIMATE_VALUE_EXTRACTION_FORBIDDEN")

    if GLOBAL_TYPED_ONLY_ENFORCEMENT or DOUBLE_PLAY_TYPED_CUTOVER or LIVE_AUTHORIZATION:
        raise RuntimeError("CUTOVER_OR_LIVE_FLAG_DRIFT")
    if NUMERIC_MAX_AGE_DECIDED or STATIC_RUNTIME_FALLBACK_USED:
        raise RuntimeError("MAX_AGE_OR_FALLBACK_FLAG_DRIFT")
    if (
        SECOND_ESTIMATOR_CREATED
        or SECOND_BINDING_AUTHORITY_CREATED
        or SECOND_ADAPTATION_AUTHORITY_CREATED
    ):
        raise RuntimeError("SECOND_AUTHORITY_FLAG_DRIFT")

    # Scaffold remains non-wiring; this capability owns productive bind.
    if (
        "PRODUCTIVE_BIND_TYPED_CALLER = True"
        in producer_src.split("assert_capability_guards_v1", 1)[0]
    ):
        raise RuntimeError("SCAFFOLD_MUST_REMAIN_NON_WIRING")

    return {
        "adapter_defs_in_typed": typed_src.count(adapter_def),
        "binder_defs_in_binding": binding_src.count(binder_def),
        "productive_bind_typed_caller": PRODUCTIVE_BIND_TYPED_CALLER,
        "cmc_runtime_wiring": CMC_RUNTIME_WIRING,
        "double_play_typed_cutover": DOUBLE_PLAY_TYPED_CUTOVER,
        "global_typed_only_enforcement": GLOBAL_TYPED_ONLY_ENFORCEMENT,
        "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
        "max_age_status": MAX_AGE_STATUS,
        "legacy_float_adaptation_owner": LEGACY_FLOAT_ADAPTATION_OWNER,
        "legacy_adaptation_boundary": LEGACY_ADAPTATION_BOUNDARY,
        "binding_owner_reused": BINDING_OWNER,
        "productive_runtime_caller_owner": PRODUCTIVE_RUNTIME_CALLER_OWNER,
        "live_authorization": LIVE_AUTHORIZATION,
        "hard_stop": HARD_STOP,
        "guards_pass": True,
    }


def assert_capability_non_goals_v1() -> dict[str, Any]:
    return {
        "capability_id": CAPABILITY_ID,
        "capability_version": CAPABILITY_VERSION,
        "binding_runtime_owner": BINDING_RUNTIME_OWNER,
        "productive_bind_typed_caller": PRODUCTIVE_BIND_TYPED_CALLER,
        "cmc_runtime_wiring": CMC_RUNTIME_WIRING,
        "double_play_typed_cutover": DOUBLE_PLAY_TYPED_CUTOVER,
        "global_typed_only_enforcement": GLOBAL_TYPED_ONLY_ENFORCEMENT,
        "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
        "max_age_status": MAX_AGE_STATUS,
        "live_authorization": LIVE_AUTHORIZATION,
        "hard_stop": HARD_STOP,
        "second_estimator_created": SECOND_ESTIMATOR_CREATED,
        "second_binding_authority_created": SECOND_BINDING_AUTHORITY_CREATED,
        "second_adaptation_authority_created": SECOND_ADAPTATION_AUTHORITY_CREATED,
        "static_runtime_fallback_used": STATIC_RUNTIME_FALLBACK_USED,
        "explicit_legacy_quarantine_changed": EXPLICIT_LEGACY_QUARANTINE_CHANGED,
        "competing_producers_changed": COMPETING_PRODUCERS_CHANGED,
        "package_marker": PACKAGE_MARKER,
        "gaps_remaining": (
            "C1_G10_NUMERIC_MAX_AGE",
            "G3_UNTYPED_EXPLICIT_LEGACY_STILL_ADMISSIBLE",
            "G15_COMPETING_NON_ALIAS_PRODUCERS",
        ),
    }


__all__ = [
    "BINDING_RUNTIME_OWNER",
    "CAPABILITY_ID",
    "CAPABILITY_VERSION",
    "CMC_RUNTIME_WIRING",
    "CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1",
    "DOUBLE_PLAY_TYPED_CUTOVER",
    "GLOBAL_TYPED_ONLY_ENFORCEMENT",
    "HARD_STOP",
    "LEGACY_FLOAT_ADAPTATION_OWNER",
    "LIVE_AUTHORIZATION",
    "MAX_AGE_STATUS",
    "PACKAGE_MARKER",
    "PRODUCTIVE_BIND_TYPED_CALLER",
    "PRODUCTIVE_RUNTIME_CALLER_OWNER",
    "ProductiveRuntimeCmcTypedBindingResultV1",
    "ProductiveRuntimeCmcTypedBindingTelemetryV1",
    "ProductiveTypedBindingFailClosedReasonV1",
    "assert_architecture_guards_v1",
    "assert_capability_non_goals_v1",
]
