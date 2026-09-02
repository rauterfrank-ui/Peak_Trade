"""Observation-only DDO capture adapters v0.

PRODUCER_RESULT -> OBSERVATION_ONLY_CAPTURE_ADAPTER -> EXISTING_DDO_RECORD
-> APPEND_ONLY_DDO_LEDGER.

Capture runs after the authoritative producer has returned. Capture failure
does not change the productive result. This module is duck-typed: it must not
import src.ops, src.trading, src.execution, src.live, or src.risk*.
"""

from __future__ import annotations

import functools
import hashlib
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, TypeVar

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    RECORD_ID_RE,
    SCHEMA_NAME_DECISION_EVENT,
    SCHEMA_NAME_INCIDENT_RECORD,
    SCHEMA_VERSION_DECISION_EVENT_V0,
    SCHEMA_VERSION_INCIDENT_RECORD_V0,
    UTC_EVENT_TIME_RE,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    DECISION_TYPE_V0,
    UNKNOWN,
)
from src.learning.deterministic_decision_outcome_v0.incident_record_v0 import (
    build_incident_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import (
    AppendOnlyDdoLedgerV0,
)
from src.learning.deterministic_decision_outcome_v0.reason_codes_v0 import (
    BLUEPRINT_REASON_TAXONOMY_ID,
    EXISTING_OPAQUE_TAXONOMY_ID,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    canonical_json_dumps_v0,
)

CAPTURE_ADAPTER_ID: str = "peak_trade.learning.ddo.capture_v0"
CAPTURE_FAILURE_CHANGES_DECISION: bool = False
CAPTURE_RUNTIME_EFFECT: str = "OBSERVATION_ONLY"

SEAM_SELECTION_UNIVERSE: str = "selection.universe"
SEAM_SELECTION_RANKING: str = "selection.ranking"
SEAM_SELECTION_SINGLE_FUTURE: str = "selection.single_future"
SEAM_SELECTION_RUNTIME_BINDING: str = "selection.runtime_binding"
SEAM_C1_OBSERVATION_ACCEPTANCE: str = "c1.observation_acceptance"
SEAM_FEATURE_REGIME: str = "feature.regime"
SEAM_TYPED_VOLATILITY: str = "feature.typed_volatility"
SEAM_BULL_BEAR: str = "core.bull_bear"
SEAM_CONFIRMATION_STATE: str = "confirmation.state"
SEAM_MASTER_V2_EVIDENCE: str = "core.master_v2_evidence"
SEAM_DOUBLE_PLAY_ENTRY_EXIT: str = "core.double_play_entry_exit"
SEAM_DYNAMIC_SCOPE: str = "core.dynamic_scope"
SEAM_SURVIVAL_SUITABILITY_COMPOSITION: str = "core.survival_suitability_composition"
SEAM_EXIT_POLICY: str = "core.exit_policy"
SEAM_STEP_29P_RISK_SIZING: str = "risk.step_29p"
SEAM_SAFETY_KERNEL: str = "safety.kernel"
SEAM_KILLSWITCH_FLAG: str = "safety.killswitch_blocked_flag"
SEAM_STEP_29Q_PLAN: str = "plan.step_29q"
SEAM_MAPPER: str = "mapper.intended_action"
SEAM_RECONCILIATION_STARTUP_GATE: str = "recon.startup_gate"
SEAM_SIMULATED_EXECUTION_OUTCOME: str = "execution.simulated_outcome"

IMPLEMENTED_CAPTURE_SEAMS_V0: tuple[str, ...] = (
    SEAM_SELECTION_UNIVERSE,
    SEAM_SELECTION_RANKING,
    SEAM_SELECTION_SINGLE_FUTURE,
    SEAM_SELECTION_RUNTIME_BINDING,
    SEAM_C1_OBSERVATION_ACCEPTANCE,
    SEAM_FEATURE_REGIME,
    SEAM_TYPED_VOLATILITY,
    SEAM_BULL_BEAR,
    SEAM_CONFIRMATION_STATE,
    SEAM_MASTER_V2_EVIDENCE,
    SEAM_DOUBLE_PLAY_ENTRY_EXIT,
    SEAM_DYNAMIC_SCOPE,
    SEAM_SURVIVAL_SUITABILITY_COMPOSITION,
    SEAM_EXIT_POLICY,
    SEAM_STEP_29P_RISK_SIZING,
    SEAM_SAFETY_KERNEL,
    SEAM_KILLSWITCH_FLAG,
    SEAM_STEP_29Q_PLAN,
    SEAM_MAPPER,
    SEAM_RECONCILIATION_STARTUP_GATE,
    SEAM_SIMULATED_EXECUTION_OUTCOME,
)

BLOCKED_CAPTURE_SEAMS_V0: tuple[str, ...] = (
    "independent_killswitch_layer",
    "execution_permission_controller",
    "venue_execution",
    "promotion_authority",
    "supervisor_productive_runtime",
    "real_outcome_horizon_engine",
    "stale_root_cause_inference",
    "decision_result_trade_token_expansion",
)

HOST_DECORATOR_SPINE_COMPLETE_V0: bool = True
_UNIX_EVENT_TIME_MIN: float = 1_000_000_000.0
_UNIX_EVENT_TIME_MAX: float = 4_102_444_800.0
_EVENT_TIME_STRING_KEYS: tuple[str, ...] = (
    "event_time_utc",
    "producer_observed_at",
    "event_time",
    "as_of_event_time",
    "generated_at_event_time",
    "market_event_time",
    "decision_time",
)
_EVENT_TIME_UNIX_KEYS: tuple[str, ...] = (
    "producer_observed_at_unix",
    "now_unix",
    "event_ts_unix",
    "current_event_time",
    "venue_event_time",
)
_NESTED_TIME_CARRIER_KEYS: tuple[str, ...] = (
    "evidence",
    "observation_identity",
    "canonical_market_context",
    "intermediate",
    "candidate",
    "inp",
    "build_input",
    "sizing_input",
)

SRC_UNIVERSE: str = "src/ops/governed_futures_universe_producer_v1/reason_codes_v1.py"
SRC_RANKING: str = "src/ops/productive_futures_ranking_producer_v1/reason_codes_v1.py"
SRC_SELECTION: str = "src/ops/single_selected_future_policy_v1/reason_codes_v1.py"
SRC_BINDING: str = "src/ops/single_selected_future_runtime_binding_v1/reason_codes_v1.py"
SRC_C1: str = "src/trading/market_state/distinct_market_observation_acceptor_v1.py"
SRC_FEATURE: str = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
    "feature_regime_pipeline_v1.py"
)
SRC_MASTER_V2: str = "src/trading/master_v2/canonical_trading_decision_evidence_v1.py"
SRC_DIRECTIONAL: str = "src/trading/master_v2/directional_assessment_v1.py"
SRC_DOUBLE_PLAY: str = "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
SRC_SCOPE: str = "src/trading/master_v2/deterministic_scope_event_generator_v1.py"
SRC_CONFIRMATION: str = (
    "src/ops/stateful_confirmation_and_c1_productive_binding_v1/reason_codes_v1.py"
)
SRC_COMPOSITION: str = "src/trading/master_v2/double_play_composition_matrix_v1.py"
SRC_EXIT: str = "src/ops/exit_policy_producer_binding_v1/reason_codes_v1.py"
SRC_29P: str = "src/governance/capital_risk_sizing_v1.py"
SRC_SAFETY: str = "src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py"
SRC_29Q: str = "src/governance/canonical_order_intent_v1.py"
SRC_MAPPER: str = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
    "intended_action_mapper_v1.py"
)
SRC_RECON: str = "src/ops/productive_reconciliation_runtime_binding_v1/taxonomy_v1.py"
SRC_SIM_EXEC: str = (
    "src/ops/single_future_stateful_no_order_runtime_activation_v1/simulated_execution_port_v1.py"
)

_LONG_SIDE_TOKENS: frozenset[str] = frozenset({"long", "bull", "long_armed", "long_active", "buy"})
_SHORT_SIDE_TOKENS: frozenset[str] = frozenset(
    {"short", "bear", "short_armed", "short_active", "sell"}
)
_NO_ENTRY_OUTCOMES: frozenset[str] = frozenset(
    {"no_action", "observe", "hold", "blocked", "cancel_pending", "reconcile_only", "NO_ACTION"}
)
_VIEW_KEYS: tuple[str, ...] = (
    "ok",
    "hard_stop",
    "failure_codes",
    "blockers",
    "reason_codes",
    "reason_code",
    "classification",
    "outcome",
    "decision_outcome",
    "killswitch_blocked",
    "event_type",
    "last_scope_advanced",
    "volatility_estimate",
    "warmup_complete",
    "regime_id",
    "execution_eligible",
    "fill",
    "fill_present",
    "intended_side",
    "intended_quantity",
    "previous_direction_state",
    "next_direction_state",
    "entry_eligibility",
    "exit_class",
    "config_digest",
    "alpha_enabled",
    "master_v2_reconciliation_state",
    "replay_pass",
    "fail_reasons",
    "safety_blocked",
    "intent_action",
    "quantity_source",
    "selected_side",
    "scope_advanced",
    "confirmation_session_id",
    "side",
    "status",
    "hard_block_reasons",
    "blocked_reasons",
    "strategy_advance_allowed",
)

F = TypeVar("F", bound=Callable[..., Any])


@dataclass(frozen=True)
class SeamSpecV0:
    seam_id: str
    producer_id: str
    authority_owner: str
    source_taxonomy_ref: str
    default_decision_type: str
    incident_class: str | None = None


SEAM_SPECS_V0: dict[str, SeamSpecV0] = {
    SEAM_SELECTION_UNIVERSE: SeamSpecV0(
        SEAM_SELECTION_UNIVERSE,
        "governed_futures_universe_producer_v1",
        "ops.governed_futures_universe_producer_v1",
        SRC_UNIVERSE,
        "NO_ENTRY",
    ),
    SEAM_SELECTION_RANKING: SeamSpecV0(
        SEAM_SELECTION_RANKING,
        "productive_futures_ranking_producer_v1",
        "ops.productive_futures_ranking_producer_v1",
        SRC_RANKING,
        "NO_ENTRY",
    ),
    SEAM_SELECTION_SINGLE_FUTURE: SeamSpecV0(
        SEAM_SELECTION_SINGLE_FUTURE,
        "single_selected_future_policy_v1",
        "ops.single_selected_future_policy_v1",
        SRC_SELECTION,
        "NO_ENTRY",
    ),
    SEAM_SELECTION_RUNTIME_BINDING: SeamSpecV0(
        SEAM_SELECTION_RUNTIME_BINDING,
        "single_selected_future_runtime_binding_v1",
        "ops.single_selected_future_runtime_binding_v1",
        SRC_BINDING,
        "NO_ENTRY",
    ),
    SEAM_C1_OBSERVATION_ACCEPTANCE: SeamSpecV0(
        SEAM_C1_OBSERVATION_ACCEPTANCE,
        "distinct_market_observation_acceptor_v1",
        "trading.market_state.distinct_market_observation_acceptor_v1",
        SRC_C1,
        UNKNOWN,
    ),
    SEAM_FEATURE_REGIME: SeamSpecV0(
        SEAM_FEATURE_REGIME,
        "feature_regime_pipeline_v1",
        "ops.wallclock_feature_regime_pipeline_v1",
        SRC_FEATURE,
        UNKNOWN,
    ),
    SEAM_TYPED_VOLATILITY: SeamSpecV0(
        SEAM_TYPED_VOLATILITY,
        "feature_regime_pipeline_v1",
        "ops.wallclock_feature_regime_pipeline_v1",
        SRC_FEATURE,
        UNKNOWN,
    ),
    SEAM_BULL_BEAR: SeamSpecV0(
        SEAM_BULL_BEAR,
        "directional_assessment_v1",
        "trading.master_v2.directional_assessment_v1",
        SRC_DIRECTIONAL,
        UNKNOWN,
    ),
    SEAM_CONFIRMATION_STATE: SeamSpecV0(
        SEAM_CONFIRMATION_STATE,
        "stateful_confirmation_and_c1_productive_binding_v1",
        "ops.stateful_confirmation_and_c1_productive_binding_v1",
        SRC_CONFIRMATION,
        UNKNOWN,
    ),
    SEAM_MASTER_V2_EVIDENCE: SeamSpecV0(
        SEAM_MASTER_V2_EVIDENCE,
        "integrated_offline_trading_logic_replay_v1",
        "trading.master_v2.integrated_offline_trading_logic_replay_v1",
        SRC_MASTER_V2,
        UNKNOWN,
    ),
    SEAM_DOUBLE_PLAY_ENTRY_EXIT: SeamSpecV0(
        SEAM_DOUBLE_PLAY_ENTRY_EXIT,
        "double_play_entry_exit_policy_v0",
        "trading.master_v2.double_play_entry_exit_policy_v0",
        SRC_DOUBLE_PLAY,
        "NO_ENTRY",
    ),
    SEAM_DYNAMIC_SCOPE: SeamSpecV0(
        SEAM_DYNAMIC_SCOPE,
        "deterministic_scope_event_generator_v1",
        "trading.master_v2.deterministic_scope_event_generator_v1",
        SRC_SCOPE,
        "DYNAMIC_SCOPE_NON_TRANSITION",
    ),
    SEAM_SURVIVAL_SUITABILITY_COMPOSITION: SeamSpecV0(
        SEAM_SURVIVAL_SUITABILITY_COMPOSITION,
        "double_play_composition_matrix_v1",
        "trading.master_v2.double_play_composition_matrix_v1",
        SRC_COMPOSITION,
        UNKNOWN,
    ),
    SEAM_EXIT_POLICY: SeamSpecV0(
        SEAM_EXIT_POLICY,
        "exit_policy_producer_binding_v1",
        "ops.exit_policy_producer_binding_v1",
        SRC_EXIT,
        "NO_EXIT",
    ),
    SEAM_STEP_29P_RISK_SIZING: SeamSpecV0(
        SEAM_STEP_29P_RISK_SIZING,
        "capital_risk_sizing_v1",
        "src.governance.capital_risk_sizing_v1",
        SRC_29P,
        UNKNOWN,
        incident_class="RISK",
    ),
    SEAM_SAFETY_KERNEL: SeamSpecV0(
        SEAM_SAFETY_KERNEL,
        "safety_kernel_offline_replay_binding_adapter_v0",
        "trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0",
        SRC_SAFETY,
        UNKNOWN,
        incident_class="KILL_SWITCH",
    ),
    SEAM_KILLSWITCH_FLAG: SeamSpecV0(
        SEAM_KILLSWITCH_FLAG,
        "safety_kernel_offline_replay_binding_adapter_v0",
        "trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0",
        SRC_SAFETY,
        UNKNOWN,
        incident_class="KILL_SWITCH",
    ),
    SEAM_STEP_29Q_PLAN: SeamSpecV0(
        SEAM_STEP_29Q_PLAN,
        "canonical_order_intent_v1",
        "src.governance.canonical_order_intent_v1",
        SRC_29Q,
        UNKNOWN,
    ),
    SEAM_MAPPER: SeamSpecV0(
        SEAM_MAPPER,
        "intended_action_mapper_v1",
        "ops.intended_action_mapper_v1",
        SRC_MAPPER,
        UNKNOWN,
    ),
    SEAM_RECONCILIATION_STARTUP_GATE: SeamSpecV0(
        SEAM_RECONCILIATION_STARTUP_GATE,
        "productive_reconciliation_startup_gate_v1",
        "ops.productive_reconciliation_runtime_binding_v1",
        SRC_RECON,
        UNKNOWN,
        incident_class="RECONCILIATION",
    ),
    SEAM_SIMULATED_EXECUTION_OUTCOME: SeamSpecV0(
        SEAM_SIMULATED_EXECUTION_OUTCOME,
        "simulated_execution_port_v1",
        "ops.simulated_execution_port_v1",
        SRC_SIM_EXEC,
        UNKNOWN,
    ),
}


@dataclass(frozen=True)
class HostDecoratorBindingV0:
    seam_id: str
    source_path: str


PROVEN_HOST_DECORATOR_BINDINGS_V0: tuple[HostDecoratorBindingV0, ...] = (
    HostDecoratorBindingV0(
        SEAM_SELECTION_UNIVERSE,
        "src/ops/governed_futures_universe_producer_v1/producer_v1.py",
    ),
    HostDecoratorBindingV0(
        SEAM_SELECTION_RANKING,
        "src/ops/productive_futures_ranking_producer_v1/producer_v1.py",
    ),
    HostDecoratorBindingV0(
        SEAM_SELECTION_SINGLE_FUTURE,
        "src/ops/single_selected_future_policy_v1/selection_v1.py",
    ),
    HostDecoratorBindingV0(
        SEAM_SELECTION_RUNTIME_BINDING,
        "src/ops/single_selected_future_runtime_binding_v1/binding_gate_v1.py",
    ),
    HostDecoratorBindingV0(
        SEAM_C1_OBSERVATION_ACCEPTANCE,
        SRC_C1,
    ),
    HostDecoratorBindingV0(
        SEAM_FEATURE_REGIME,
        SRC_FEATURE,
    ),
    HostDecoratorBindingV0(
        SEAM_TYPED_VOLATILITY,
        SRC_FEATURE,
    ),
    HostDecoratorBindingV0(
        SEAM_BULL_BEAR,
        SRC_DIRECTIONAL,
    ),
    HostDecoratorBindingV0(
        SEAM_CONFIRMATION_STATE,
        "src/ops/stateful_confirmation_and_c1_productive_binding_v1/host_binding_v1.py",
    ),
    HostDecoratorBindingV0(
        SEAM_MASTER_V2_EVIDENCE,
        "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    ),
    HostDecoratorBindingV0(
        SEAM_DOUBLE_PLAY_ENTRY_EXIT,
        SRC_DOUBLE_PLAY,
    ),
    HostDecoratorBindingV0(
        SEAM_DYNAMIC_SCOPE,
        SRC_SCOPE,
    ),
    HostDecoratorBindingV0(
        SEAM_SURVIVAL_SUITABILITY_COMPOSITION,
        SRC_COMPOSITION,
    ),
    HostDecoratorBindingV0(
        SEAM_EXIT_POLICY,
        "src/ops/exit_policy_producer_binding_v1/producers_v1.py",
    ),
    HostDecoratorBindingV0(
        SEAM_STEP_29P_RISK_SIZING,
        SRC_29P,
    ),
    HostDecoratorBindingV0(
        SEAM_SAFETY_KERNEL,
        SRC_SAFETY,
    ),
    HostDecoratorBindingV0(
        SEAM_KILLSWITCH_FLAG,
        SRC_SAFETY,
    ),
    HostDecoratorBindingV0(
        SEAM_STEP_29Q_PLAN,
        SRC_29Q,
    ),
    HostDecoratorBindingV0(
        SEAM_MAPPER,
        SRC_MAPPER,
    ),
    HostDecoratorBindingV0(
        SEAM_RECONCILIATION_STARTUP_GATE,
        "src/ops/productive_reconciliation_runtime_binding_v1/startup_gate_v1.py",
    ),
    HostDecoratorBindingV0(
        SEAM_SIMULATED_EXECUTION_OUTCOME,
        SRC_SIM_EXEC,
    ),
)


@dataclass
class DdoCaptureBindingV0:
    """Fail-open observation cursor. Never a trading or promotion authority."""

    enabled: bool = True
    ledger_path: Path | str | None = None
    captured_records: list[dict[str, Any]] = field(default_factory=list)
    captured_ids: list[str] = field(default_factory=list)
    last_error: str | None = None
    last_result: dict[str, Any] | None = None
    _ledger: AppendOnlyDdoLedgerV0 | None = field(default=None, repr=False)

    def ledger(self) -> AppendOnlyDdoLedgerV0 | None:
        if self.ledger_path is None:
            return None
        if self._ledger is None:
            self._ledger = AppendOnlyDdoLedgerV0(self.ledger_path)
        return self._ledger


_CAPTURE_SESSION: ContextVar[DdoCaptureBindingV0 | None] = ContextVar(
    "ddo_capture_session_v0", default=None
)


def current_capture_binding_v0() -> DdoCaptureBindingV0 | None:
    return _CAPTURE_SESSION.get()


def bind_capture_session_v0(
    binding: DdoCaptureBindingV0 | None,
) -> Token[DdoCaptureBindingV0 | None]:
    return _CAPTURE_SESSION.set(binding)


def reset_capture_session_v0(token: Token[DdoCaptureBindingV0 | None]) -> None:
    _CAPTURE_SESSION.reset(token)


def with_ddo_capture_session_v0(fn: F) -> F:
    """Install the host capture session for the duration of a productive cycle."""

    @functools.wraps(fn)
    def wrapped(state: Any, *args: Any, **kwargs: Any) -> Any:
        binding = getattr(state, "ddo_capture_binding", None)
        token = bind_capture_session_v0(
            binding if isinstance(binding, DdoCaptureBindingV0) else None
        )
        try:
            return fn(state, *args, **kwargs)
        finally:
            reset_capture_session_v0(token)

    return wrapped  # type: ignore[return-value]


def observe_after_producer_v0(*, seam_id: str) -> Callable[[F], F]:
    """Compute the producer result first, then observe. Always return the original result."""

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = fn(*args, **kwargs)
            binding = current_capture_binding_v0()
            if binding is None or not binding.enabled:
                return result
            try:
                observe_producer_result_v0(
                    binding,
                    seam_id=seam_id,
                    result=result,
                    kwargs=kwargs,
                    args=args,
                )
            except Exception as exc:  # noqa: BLE001
                binding.last_error = f"{type(exc).__name__}:{exc}"
                binding.last_result = {
                    "ok": False,
                    "error": binding.last_error,
                    "decision_unchanged": True,
                    "seam_id": seam_id,
                }
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def observe_producer_result_v0(
    binding: DdoCaptureBindingV0,
    *,
    seam_id: str,
    result: Any,
    kwargs: Mapping[str, Any] | None = None,
    args: tuple[Any, ...] | None = None,
    event_time_utc: str | None = None,
    correlation_id: str | None = None,
    cycle_id: str | None = None,
    repository_sha: str | None = None,
) -> dict[str, Any]:
    """Build and persist one DecisionEvent (and optional Incident) from producer output."""
    if not binding.enabled:
        return {"ok": True, "skipped": True, "reason": "CAPTURE_DISABLED"}
    spec = SEAM_SPECS_V0[seam_id]
    view = _view(result)
    codes = _codes_from_view(view)
    event_time = (
        event_time_utc
        or _event_time_from_kwargs(kwargs)
        or _event_time_from_args(args)
        or _event_time_from_view(view)
        or _event_time_from_object(result)
    )
    if event_time is None:
        raise ValueError("CAPTURE_EVENT_TIME_MISSING")
    decision_type = _decision_type_for_seam(spec, view)
    hard_stop = bool(view.get("hard_stop"))
    opaque = _opaque_codes(codes, spec.source_taxonomy_ref)
    if not opaque:
        opaque = [
            {
                "taxonomy_id": BLUEPRINT_REASON_TAXONOMY_ID,
                "code": UNKNOWN,
                "source_taxonomy_ref": None,
            }
        ]
    hard_blocks = list(opaque) if hard_stop else []
    identity = {
        "seam_id": spec.seam_id,
        "event_time_utc": event_time,
        "codes": [item["code"] for item in opaque],
        "hard_stop": hard_stop,
        "decision_type": decision_type,
        "cycle_id": cycle_id or UNKNOWN,
        "correlation_id": correlation_id or "ddo.corr.default",
        "repository_sha": repository_sha or UNKNOWN,
    }
    record_id = _stable_record_id("ddo.dec", identity)
    event_id = _stable_record_id("ddo.evt", identity)
    corr = _as_record_id(correlation_id or "ddo.corr.default")
    cycle_ref = _optional_record_id(cycle_id)
    payload = {
        "schema_name": SCHEMA_NAME_DECISION_EVENT,
        "schema_version": SCHEMA_VERSION_DECISION_EVENT_V0,
        "record_id": record_id,
        "event_id": event_id,
        "correlation_id": corr,
        "cycle_id": cycle_ref,
        "event_time_utc": event_time,
        "decision_type": decision_type,
        "decision_result": "NO_ACTION",
        "reason_codes": opaque,
        "hard_block_reasons": hard_blocks,
        "decision_time_information_set_ref": None,
        "market_snapshot_ref": None,
        "feature_snapshot_ref": None,
        "data_quality_ref": None,
        "risk_snapshot_ref": None,
        "position_snapshot_ref": None,
        "selected_instrument_ref": None,
        "code_sha": UNKNOWN,
        "config_hash": _sha_or_unknown(view.get("config_digest")),
        "authority_owner": spec.authority_owner,
        "producer_id": spec.producer_id,
        "evidence_hash": UNKNOWN,
        "causal_parent_ids": [],
        "evidence_source_refs": [spec.source_taxonomy_ref],
    }
    record = dict(build_decision_event_v0(payload))
    _persist(binding, record)
    incident_record = None
    if _should_emit_incident(spec, view, hard_stop):
        incident_identity = dict(identity)
        incident_identity["kind"] = "incident"
        incident_id = _stable_record_id("ddo.inc", incident_identity)
        incident_payload = {
            "schema_name": SCHEMA_NAME_INCIDENT_RECORD,
            "schema_version": SCHEMA_VERSION_INCIDENT_RECORD_V0,
            "record_id": incident_id,
            "incident_id": _stable_record_id("ddo.incd", incident_identity),
            "correlation_id": corr,
            "cycle_id": cycle_ref,
            "event_time_utc": event_time,
            "incident_class": spec.incident_class or UNKNOWN,
            "reason_codes": opaque,
            "hard_block_reasons": hard_blocks or list(opaque),
            "stale_root_cause": UNKNOWN,
            "decision_event_ref": record_id,
            "decision_time_information_set_ref": None,
            "market_snapshot_ref": None,
            "data_quality_ref": None,
            "risk_snapshot_ref": None,
            "position_snapshot_ref": None,
            "code_sha": UNKNOWN,
            "config_hash": _sha_or_unknown(view.get("config_digest")),
            "authority_owner": spec.authority_owner,
            "producer_id": spec.producer_id,
            "evidence_hash": UNKNOWN,
            "causal_parent_ids": [record_id],
            "evidence_source_refs": [spec.source_taxonomy_ref],
        }
        incident_record = dict(build_incident_record_v0(incident_payload))
        _persist(binding, incident_record)
    summary = {
        "ok": True,
        "seam_id": spec.seam_id,
        "record_id": record_id,
        "content_hash": record["content_hash"],
        "decision_type": decision_type,
        "decision_result": "NO_ACTION",
        "decision_unchanged": True,
        "incident_id": None if incident_record is None else incident_record["record_id"],
    }
    binding.last_error = None
    binding.last_result = dict(summary)
    return summary


def record_productive_cycle_capture_v0(
    binding: DdoCaptureBindingV0 | None,
    *,
    repository_sha: str,
    session_id: str,
    cycle_index: int,
    event_ts_unix: float,
    observation_acceptance_result: Any = None,
    features: Any = None,
    replay: Any = None,
    intended: Any = None,
    fill: Any = None,
    confirmation_binding: Any = None,
    dynamic_scope_binding: Any = None,
    exit_policy_binding: Any = None,
    safety_result: Any = None,
    risk_sizing_result: Any = None,
    cycle: Any = None,
) -> dict[str, Any]:
    """Observe already-computed cycle objects. Never alter the productive cycle."""
    if binding is None or not binding.enabled:
        return {"ok": True, "skipped": True, "reason": "CAPTURE_DISABLED"}
    try:
        event_time = _from_unix(event_ts_unix)
        correlation_id = _as_record_id(f"ddo.corr.{session_id}"[:128])
        cycle_id = _optional_record_id(f"{session_id}:cycle:{cycle_index}")
        intermediate = getattr(replay, "intermediate", None) if replay is not None else None
        evidence = getattr(replay, "evidence", None) if replay is not None else None
        observations: list[tuple[str, Any]] = [
            (SEAM_C1_OBSERVATION_ACCEPTANCE, observation_acceptance_result),
            (SEAM_FEATURE_REGIME, features),
            (SEAM_TYPED_VOLATILITY, features),
            (SEAM_CONFIRMATION_STATE, confirmation_binding),
            (SEAM_MASTER_V2_EVIDENCE, evidence if evidence is not None else replay),
            (SEAM_BULL_BEAR, intermediate),
            (SEAM_DOUBLE_PLAY_ENTRY_EXIT, getattr(intermediate, "entry_exit_decision", None)),
            (
                SEAM_DYNAMIC_SCOPE,
                dynamic_scope_binding if dynamic_scope_binding is not None else intermediate,
            ),
            (SEAM_SURVIVAL_SUITABILITY_COMPOSITION, intermediate),
            (SEAM_EXIT_POLICY, exit_policy_binding),
            (
                SEAM_STEP_29P_RISK_SIZING,
                getattr(intermediate, "capital_risk_sizing_decision", None),
            ),
            (SEAM_SAFETY_KERNEL, evidence),
            (
                SEAM_KILLSWITCH_FLAG,
                evidence if evidence is not None else {"killswitch_blocked": False},
            ),
            (SEAM_STEP_29Q_PLAN, getattr(intermediate, "canonical_order_intent", None)),
            (SEAM_MAPPER, intended),
            (SEAM_SIMULATED_EXECUTION_OUTCOME, fill),
        ]
        captured: list[str] = []
        for seam_id, obj in observations:
            if obj is None:
                continue
            extra_view = None
            if seam_id == SEAM_BULL_BEAR and intermediate is not None:
                extra_view = _bull_bear_view(intermediate)
            if seam_id == SEAM_DYNAMIC_SCOPE:
                extra_view = _scope_view(dynamic_scope_binding, intermediate)
            if seam_id == SEAM_TYPED_VOLATILITY:
                extra_view = _volatility_view(features)
            if seam_id == SEAM_KILLSWITCH_FLAG:
                extra_view = _killswitch_view(evidence)
            if extra_view is not None:
                obj = extra_view
            summary = observe_producer_result_v0(
                binding,
                seam_id=seam_id,
                result=obj,
                event_time_utc=event_time,
                correlation_id=correlation_id,
                cycle_id=cycle_id,
                repository_sha=repository_sha,
            )
            captured.append(str(summary.get("record_id") or ""))
        # Cycle-level safety/risk strings are already-computed host labels, not new authority.
        if safety_result is not None or risk_sizing_result is not None or cycle is not None:
            _ = (safety_result, risk_sizing_result, cycle)
        result = {
            "ok": True,
            "captured_count": len(captured),
            "record_ids": captured,
            "decision_unchanged": True,
        }
        binding.last_result = dict(result)
        return result
    except Exception as exc:  # noqa: BLE001
        binding.last_error = f"{type(exc).__name__}:{exc}"
        result = {
            "ok": False,
            "error": binding.last_error,
            "decision_unchanged": True,
        }
        binding.last_result = dict(result)
        return result


def _persist(binding: DdoCaptureBindingV0, record: Mapping[str, Any]) -> None:
    frozen = dict(record)
    binding.captured_records.append(frozen)
    binding.captured_ids.append(str(frozen["record_id"]))
    ledger = binding.ledger()
    if ledger is not None:
        ledger.append(frozen)


def _view(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, Mapping):
        return dict(obj)
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    out: dict[str, Any] = {}
    for key in _VIEW_KEYS:
        if hasattr(obj, key):
            out[key] = getattr(obj, key)
    return out


def _token(value: Any) -> str:
    if value is None or isinstance(value, bool):
        return ""
    raw = getattr(value, "value", value)
    if isinstance(raw, str) and raw:
        return raw
    return ""


def _codes_from_view(view: Mapping[str, Any]) -> tuple[str, ...]:
    out: list[str] = []
    for key in (
        "failure_codes",
        "blockers",
        "reason_codes",
        "hard_block_reasons",
        "blocked_reasons",
        "fail_reasons",
    ):
        val = view.get(key)
        if isinstance(val, str) and val:
            out.append(val)
        elif isinstance(val, (list, tuple)):
            for item in val:
                token = _token(item)
                if token:
                    out.append(token)
    for key in ("reason_code", "classification", "outcome", "decision_outcome", "event_type"):
        token = _token(view.get(key))
        if token:
            out.append(token)
    if view.get("killswitch_blocked") is True:
        out.append("killswitch_blocked")
    seen: set[str] = set()
    unique: list[str] = []
    for code in out:
        if code not in seen:
            seen.add(code)
            unique.append(code)
    return tuple(unique)


def _opaque_codes(codes: tuple[str, ...], source_taxonomy_ref: str) -> list[dict[str, Any]]:
    return [
        {
            "taxonomy_id": EXISTING_OPAQUE_TAXONOMY_ID,
            "code": code,
            "source_taxonomy_ref": source_taxonomy_ref,
        }
        for code in codes
        if code
    ]


def _decision_type_for_seam(spec: SeamSpecV0, view: Mapping[str, Any]) -> str:
    if spec.seam_id == SEAM_DYNAMIC_SCOPE:
        return _scope_decision_type(view)
    if spec.seam_id == SEAM_BULL_BEAR:
        return _bull_bear_decision_type(view)
    if spec.seam_id == SEAM_DOUBLE_PLAY_ENTRY_EXIT:
        outcome = _token(view.get("decision_outcome")).lower()
        if outcome in {item.lower() for item in _NO_ENTRY_OUTCOMES}:
            return "NO_ENTRY"
        return UNKNOWN
    if spec.seam_id == SEAM_STEP_29P_RISK_SIZING:
        if _token(view.get("outcome")).upper() == "BLOCKED":
            return "RISK_BLOCK"
        return UNKNOWN
    if spec.seam_id in {SEAM_SAFETY_KERNEL, SEAM_KILLSWITCH_FLAG}:
        if view.get("killswitch_blocked") is True:
            return "KILL_SWITCH"
        return UNKNOWN
    if spec.seam_id == SEAM_RECONCILIATION_STARTUP_GATE:
        if bool(view.get("hard_stop")):
            return "RECONCILIATION_BLOCK"
        return UNKNOWN
    decision_type = spec.default_decision_type
    if decision_type not in DECISION_TYPE_V0:
        return UNKNOWN
    return decision_type


def _scope_decision_type(view: Mapping[str, Any]) -> str:
    advanced = view.get("last_scope_advanced")
    if advanced is None:
        advanced = view.get("scope_advanced")
    if advanced is True:
        return "DYNAMIC_SCOPE_TRANSITION"
    if advanced is False:
        return "DYNAMIC_SCOPE_NON_TRANSITION"
    event_type = _token(view.get("event_type")).lower()
    if event_type in {"noop", "scope_blocked", ""}:
        return "DYNAMIC_SCOPE_NON_TRANSITION"
    return "DYNAMIC_SCOPE_TRANSITION"


def _bull_bear_decision_type(view: Mapping[str, Any]) -> str:
    prev = _side_bucket(
        _token(view.get("previous_direction_state")) or _token(view.get("previous_side"))
    )
    nxt = _side_bucket(_token(view.get("next_direction_state")) or _token(view.get("next_side")))
    if prev == "long" and nxt == "short":
        return "BULL_TO_BEAR"
    if prev == "short" and nxt == "long":
        return "BEAR_TO_BULL"
    return UNKNOWN


def _side_bucket(token: str) -> str:
    lowered = token.lower()
    if lowered in _LONG_SIDE_TOKENS:
        return "long"
    if lowered in _SHORT_SIDE_TOKENS:
        return "short"
    return ""


def _should_emit_incident(spec: SeamSpecV0, view: Mapping[str, Any], hard_stop: bool) -> bool:
    if spec.incident_class == "RISK":
        return _token(view.get("outcome")).upper() == "BLOCKED" or hard_stop
    if spec.incident_class == "KILL_SWITCH":
        return view.get("killswitch_blocked") is True
    if spec.incident_class == "RECONCILIATION":
        return hard_stop
    return False


def _bull_bear_view(intermediate: Any) -> dict[str, Any]:
    entry = getattr(intermediate, "entry_exit_decision", None)
    bull = getattr(intermediate, "bull_assessment", None)
    bear = getattr(intermediate, "bear_assessment", None)
    view = _view(entry)
    view["previous_direction_state"] = getattr(entry, "previous_direction_state", None)
    view["next_direction_state"] = getattr(entry, "selected_side", None)
    view["bull_status"] = getattr(bull, "status", None)
    view["bear_status"] = getattr(bear, "status", None)
    view["reason_codes"] = tuple(
        list(_codes_from_view(_view(bull))) + list(_codes_from_view(_view(bear)))
    )
    return view


def _scope_view(binding: Any, intermediate: Any) -> dict[str, Any]:
    view: dict[str, Any] = {}
    if binding is not None:
        view.update(_view(binding))
        view["last_scope_advanced"] = bool(getattr(binding, "last_scope_advanced", False))
    scope_event = getattr(intermediate, "scope_event", None) if intermediate is not None else None
    if scope_event is not None:
        event_view = _view(scope_event)
        view["event_type"] = event_view.get("event_type") or getattr(
            scope_event, "event_type", None
        )
        view["blocked_reasons"] = event_view.get("blocked_reasons") or getattr(
            scope_event, "blocked_reasons", ()
        )
        if "last_scope_advanced" not in view:
            event_type = _token(view.get("event_type")).lower()
            view["last_scope_advanced"] = event_type not in {"noop", "scope_blocked", ""}
    if "last_scope_advanced" not in view:
        view["last_scope_advanced"] = False
    return view


def _volatility_view(features: Any) -> dict[str, Any]:
    view = _view(features)
    view["typed_volatility_present"] = view.get("volatility_estimate") is not None
    return view


def _killswitch_view(evidence: Any) -> dict[str, Any]:
    view = _view(evidence)
    flag = bool(view.get("killswitch_blocked") or getattr(evidence, "killswitch_blocked", False))
    effect = _token(view.get("killswitch_boundary_effect"))
    return {
        "killswitch_blocked": flag,
        "killswitch_boundary_effect": effect,
        "reason_codes": ("killswitch_blocked",) if flag else (),
    }


def _event_time_from_kwargs(kwargs: Mapping[str, Any] | None) -> str | None:
    if not kwargs:
        return None
    for key in ("producer_observed_at_unix", "now_unix", "event_ts_unix", "current_event_time"):
        if key in kwargs and kwargs[key] is not None:
            found = _event_time_from_unixish(kwargs[key])
            if found is not None:
                return found
            found = _event_time_from_rfc3339(kwargs[key])
            if found is not None:
                return found
    for value in kwargs.values():
        found = _event_time_from_object(value)
        if found is not None:
            return found
    return None


def _event_time_from_args(args: tuple[Any, ...] | None) -> str | None:
    if not args:
        return None
    for arg in args:
        found = _event_time_from_object(arg)
        if found is not None:
            return found
    return None


def _event_time_from_view(view: Mapping[str, Any]) -> str | None:
    for key in _EVENT_TIME_STRING_KEYS:
        found = _event_time_from_rfc3339(view.get(key))
        if found is not None:
            return found
    for key in _EVENT_TIME_UNIX_KEYS:
        found = _event_time_from_unixish(view.get(key))
        if found is not None:
            return found
    identity = view.get("observation_identity")
    if isinstance(identity, Mapping):
        found = _event_time_from_unixish(identity.get("venue_event_time"))
        if found is not None:
            return found
        found = _event_time_from_rfc3339(identity.get("venue_event_time"))
        if found is not None:
            return found
    return None


def _event_time_from_object(
    obj: Any, *, _seen: set[int] | None = None, _depth: int = 0
) -> str | None:
    if obj is None or _depth > 4:
        return None
    found = _event_time_from_rfc3339(obj) or _event_time_from_unixish(obj)
    if found is not None:
        return found
    if isinstance(obj, datetime):
        if obj.tzinfo is None:
            return None
        return obj.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    oid = id(obj)
    seen = _seen if _seen is not None else set()
    if oid in seen:
        return None
    carrier_keys = (*_EVENT_TIME_STRING_KEYS, *_NESTED_TIME_CARRIER_KEYS)
    if not isinstance(obj, (Mapping, tuple, list)) and not hasattr(obj, "__dict__"):
        if not any(hasattr(obj, key) for key in carrier_keys):
            return None
    seen.add(oid)
    view = _view(obj)
    found = _event_time_from_view(view)
    if found is not None:
        return found
    for key in (*_EVENT_TIME_STRING_KEYS, *_EVENT_TIME_UNIX_KEYS, *_NESTED_TIME_CARRIER_KEYS):
        if hasattr(obj, key):
            found = _event_time_from_object(getattr(obj, key), _seen=seen, _depth=_depth + 1)
            if found is not None:
                return found
        if key in view:
            found = _event_time_from_object(view[key], _seen=seen, _depth=_depth + 1)
            if found is not None:
                return found
    return None


def _event_time_from_unixish(value: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    ts = float(value)
    if _UNIX_EVENT_TIME_MIN <= ts <= _UNIX_EVENT_TIME_MAX:
        return _from_unix(ts)
    return None


def _event_time_from_rfc3339(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    if UTC_EVENT_TIME_RE.fullmatch(value):
        return value
    if value.endswith("+00:00"):
        candidate = value[:-6] + "Z"
        if UTC_EVENT_TIME_RE.fullmatch(candidate):
            return candidate
    return None


def _from_unix(value: Any) -> str:
    ts = float(value)
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha_or_unknown(value: Any) -> str:
    if (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value)
    ):
        return value
    return UNKNOWN


def _stable_record_id(prefix: str, identity: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(canonical_json_dumps_v0(dict(identity)).encode("utf-8")).hexdigest()[
        :24
    ]
    raw = f"{prefix}:{digest}"
    return _as_record_id(raw)


def _as_record_id(raw: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._:-" else "_" for ch in raw)
    if len(cleaned) < 8:
        cleaned = (cleaned + "_padid01")[:128]
    if len(cleaned) > 128:
        cleaned = cleaned[:128]
    if not RECORD_ID_RE.fullmatch(cleaned):
        cleaned = ("ddo.id:" + hashlib.sha256(raw.encode("utf-8")).hexdigest())[:128]
    return cleaned


def _optional_record_id(raw: str | None) -> str | None:
    if raw is None or not raw:
        return None
    candidate = _as_record_id(raw)
    return candidate if RECORD_ID_RE.fullmatch(candidate) else None
