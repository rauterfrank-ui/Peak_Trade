"""Host binding for Cap 6.5 exit-policy producer evaluation and restart state."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
    CANONICAL_DECISION_CONFIG_DIGEST,
    CANONICAL_UP_DISTANCE,
)
from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS,
    OWNER,
    STATE_VERSION,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import (
    CanonicalExitPolicyStateV1,
    ExitPolicyProducerBundleV1,
)
from src.ops.exit_policy_producer_binding_v1.persistence_v1 import (
    ExitPolicyPersistenceError,
    load_exit_policy_state_v1,
    persist_exit_policy_state_atomic_v1,
    prior_commit_exists,
)
from src.ops.exit_policy_producer_binding_v1.producers_v1 import (
    bundle_to_policy_signals_v1,
    evaluate_exit_policy_producers_v1,
)
from src.ops.exit_policy_producer_binding_v1.reason_codes_v1 import (
    ExitPolicyBindingFailureCodeV1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    PolicySignalV0,
    SafetyMode,
    TradingGate,
)
from trading.market_state.directional_confirmation_progress_v1 import (
    ConfirmationAssessmentStateV1,
)


def exit_policy_config_digest_v1(
    *,
    adverse_exit_distance: float = float(CANONICAL_ADVERSE_EXIT_DISTANCE),
    profit_protection_distance: float = float(CANONICAL_UP_DISTANCE),
    time_exit_max_hold_seconds: float = CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS,
) -> str:
    material = (
        f"cap65-config:adverse={float(adverse_exit_distance)}:"
        f"profit={float(profit_protection_distance)}:"
        f"time_hold={float(time_exit_max_hold_seconds)}:"
        f"owner={OWNER}:sv={STATE_VERSION}:"
        f"cap63={CANONICAL_DECISION_CONFIG_DIGEST}"
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass
class HostExitPolicyBindingV1:
    enabled: bool = False
    initialized: bool = False
    state_root: Optional[str] = None
    repository_sha: str = ""
    config_digest: str = ""
    instrument_id: str = ""
    commit_sequence: int = 0
    prior_commit_seen: bool = False
    alpha_blocked: bool = False
    alpha_block_reason: str = ""
    has_open_position: bool = False
    existing_position_side: str = "none"
    entry_price: Optional[float] = None
    entry_event_time: Optional[float] = None
    entry_trading_epoch: Optional[int] = None
    time_exit_max_hold_seconds: float = CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS
    pending_exit_class: str = ""
    pending_exit_reason: str = ""
    pending_exit_identity: str = ""
    last_exit_intent_identity: str = ""
    last_observation_digest: str = ""
    last_evaluated_event_time: Optional[float] = None
    last_bundle: dict[str, Any] = field(default_factory=dict)
    last_commit: dict[str, Any] = field(default_factory=dict)

    def to_canonical_state(self) -> CanonicalExitPolicyStateV1:
        return CanonicalExitPolicyStateV1(
            state_version=STATE_VERSION,
            instrument_id=self.instrument_id,
            repository_sha=self.repository_sha,
            config_digest=self.config_digest,
            has_open_position=bool(self.has_open_position),
            existing_position_side=str(self.existing_position_side),
            entry_price=self.entry_price,
            entry_event_time=self.entry_event_time,
            entry_trading_epoch=self.entry_trading_epoch,
            time_exit_max_hold_seconds=float(self.time_exit_max_hold_seconds),
            pending_exit_class=str(self.pending_exit_class or ""),
            pending_exit_reason=str(self.pending_exit_reason or ""),
            pending_exit_identity=str(self.pending_exit_identity or ""),
            last_exit_intent_identity=str(self.last_exit_intent_identity or ""),
            last_observation_digest=str(self.last_observation_digest or ""),
            last_evaluated_event_time=self.last_evaluated_event_time,
            commit_sequence=int(self.commit_sequence),
            owner=OWNER,
        )


def ensure_host_exit_policy_binding_v1(
    binding: HostExitPolicyBindingV1,
    *,
    instrument_id: str,
    repository_sha: str,
    config_digest: str,
    state_root: Path | None,
) -> HostExitPolicyBindingV1:
    binding.enabled = True
    binding.instrument_id = instrument_id
    binding.repository_sha = repository_sha
    binding.config_digest = config_digest
    if state_root is None:
        binding.initialized = True
        return binding
    root = Path(state_root)
    binding.state_root = str(root)
    if prior_commit_exists(root):
        try:
            loaded = load_exit_policy_state_v1(
                root,
                expected_repository_sha=repository_sha,
                expected_config_digest=config_digest,
            )
        except ExitPolicyPersistenceError as exc:
            binding.alpha_blocked = True
            binding.alpha_block_reason = exc.code.value
            binding.initialized = True
            binding.prior_commit_seen = True
            raise
        binding.has_open_position = bool(loaded.has_open_position)
        binding.existing_position_side = str(loaded.existing_position_side)
        binding.entry_price = loaded.entry_price
        binding.entry_event_time = loaded.entry_event_time
        binding.entry_trading_epoch = loaded.entry_trading_epoch
        binding.time_exit_max_hold_seconds = float(loaded.time_exit_max_hold_seconds)
        binding.pending_exit_class = str(loaded.pending_exit_class or "")
        binding.pending_exit_reason = str(loaded.pending_exit_reason or "")
        binding.pending_exit_identity = str(loaded.pending_exit_identity or "")
        binding.last_exit_intent_identity = str(loaded.last_exit_intent_identity or "")
        binding.last_observation_digest = str(loaded.last_observation_digest or "")
        binding.last_evaluated_event_time = loaded.last_evaluated_event_time
        binding.commit_sequence = int(loaded.commit_sequence)
        binding.prior_commit_seen = True
    binding.initialized = True
    binding.alpha_blocked = False
    binding.alpha_block_reason = ""
    return binding


def _confirmation_invalid(binding_confirmation: Any) -> bool:
    carrier = getattr(binding_confirmation, "confirmation_side_carrier", None)
    if carrier is None:
        return False
    for side_name in ("bull_confirmation_state", "bear_confirmation_state"):
        side = getattr(carrier, side_name, None)
        if side is None:
            continue
        assessment = getattr(side, "assessment_state", None)
        if assessment == ConfirmationAssessmentStateV1.INVALID:
            return True
        if str(assessment) == ConfirmationAssessmentStateV1.INVALID.value:
            return True
    return False


def evaluate_host_exit_policy_producers_v1(
    binding: HostExitPolicyBindingV1,
    *,
    mark_price: float,
    event_ts_unix: float,
    observation_digest: str,
    has_open_position: bool,
    existing_position_side: str,
    entry_price: float | None,
    entry_event_time: float | None,
    entry_trading_epoch: int | None,
    confirmation_binding: Any = None,
    data_integrity_trusted: bool = True,
    scope_adverse_matched: bool = False,
    scope_adverse_candidate: bool = False,
    adverse_exit_distance: float = float(CANONICAL_ADVERSE_EXIT_DISTANCE),
    profit_protection_distance: float = float(CANONICAL_UP_DISTANCE),
    killstate_active: bool = False,
    killstate_trigger: str = "",
    warmup_complete: bool = True,
    regime_ok: bool = True,
    price_basis_ok: bool = True,
    max_drawdown: float = 0.0,
) -> tuple[ExitPolicyProducerBundleV1, dict[str, PolicySignalV0], SafetyMode, TradingGate]:
    if binding.alpha_blocked:
        raise ExitPolicyPersistenceError(
            ExitPolicyBindingFailureCodeV1.ALPHA_BLOCKED_EXIT_STATE_UNRECOVERABLE,
            binding.alpha_block_reason,
        )
    duplicate = bool(
        observation_digest
        and binding.last_observation_digest
        and observation_digest == binding.last_observation_digest
    )
    # Prefer restart-restored entry continuity when host has open position.
    eff_entry_price = binding.entry_price if binding.entry_price is not None else entry_price
    eff_entry_event = (
        binding.entry_event_time if binding.entry_event_time is not None else entry_event_time
    )
    if has_open_position and binding.has_open_position:
        if binding.entry_price is not None:
            eff_entry_price = binding.entry_price
        if binding.entry_event_time is not None:
            eff_entry_event = binding.entry_event_time
    if has_open_position and not binding.has_open_position:
        # Arm entry anchors on first open observation.
        binding.entry_price = entry_price
        binding.entry_event_time = entry_event_time
        binding.entry_trading_epoch = entry_trading_epoch
        eff_entry_price = entry_price
        eff_entry_event = entry_event_time
    if not has_open_position:
        binding.entry_price = None
        binding.entry_event_time = None
        binding.entry_trading_epoch = None
        binding.pending_exit_class = ""
        binding.pending_exit_reason = ""
        binding.pending_exit_identity = ""
        eff_entry_price = None
        eff_entry_event = None

    binding.has_open_position = bool(has_open_position)
    binding.existing_position_side = str(existing_position_side)
    bundle = evaluate_exit_policy_producers_v1(
        has_open_position=bool(has_open_position),
        existing_position_side=str(existing_position_side),
        entry_price=eff_entry_price,
        mark_price=float(mark_price),
        entry_event_time=eff_entry_event,
        current_event_time=float(event_ts_unix),
        confirmation_assessment_invalid=_confirmation_invalid(confirmation_binding),
        data_integrity_trusted=bool(data_integrity_trusted),
        scope_adverse_matched=bool(scope_adverse_matched),
        scope_adverse_candidate=bool(scope_adverse_candidate),
        adverse_exit_distance=float(adverse_exit_distance),
        profit_protection_distance=float(profit_protection_distance),
        max_hold_seconds=float(binding.time_exit_max_hold_seconds),
        killstate_active=bool(killstate_active),
        killstate_trigger=str(killstate_trigger or ""),
        warmup_complete=bool(warmup_complete),
        regime_ok=bool(regime_ok),
        price_basis_ok=bool(price_basis_ok),
        max_drawdown=float(max_drawdown),
        pending_exit_class=str(binding.pending_exit_class or ""),
        duplicate_observation=duplicate,
    )
    signals = bundle_to_policy_signals_v1(bundle)
    # Arm pending exit on first true mandatory/safety trigger.
    for evidence in (
        bundle.safety_exit,
        bundle.hard_risk_reduction,
        bundle.scope_adverse_exit,
        bundle.profit_protection,
        bundle.time_exit,
        bundle.strategy_invalidation,
    ):
        if evidence.triggered and not binding.pending_exit_class:
            binding.pending_exit_class = evidence.exit_class
            binding.pending_exit_reason = evidence.reason_code
            identity = hashlib.sha256(
                f"{binding.instrument_id}:{evidence.exit_class}:{evidence.reason_code}:"
                f"{eff_entry_event}:{observation_digest}".encode()
            ).hexdigest()[:32]
            binding.pending_exit_identity = identity
            break
    if duplicate and binding.last_exit_intent_identity:
        # Do not mint a new exit intent identity on duplicate observation.
        pass
    elif binding.pending_exit_identity and not binding.last_exit_intent_identity:
        binding.last_exit_intent_identity = binding.pending_exit_identity
    binding.last_observation_digest = str(observation_digest or "")
    binding.last_evaluated_event_time = float(event_ts_unix)
    binding.last_bundle = bundle.to_dict()
    return (
        bundle,
        signals,
        SafetyMode(bundle.safety_mode),
        TradingGate(bundle.trading_gate),
    )


def commit_host_exit_policy_state_v1(
    binding: HostExitPolicyBindingV1,
    *,
    persist: bool,
    writer_session_id: str,
) -> Mapping[str, Any]:
    if not persist or not binding.state_root:
        return {"ok": True, "persisted": False}
    binding.commit_sequence = int(binding.commit_sequence) + 1
    state = binding.to_canonical_state()
    out = persist_exit_policy_state_atomic_v1(
        state_root=Path(binding.state_root),
        state=state,
        writer_session_id=writer_session_id,
    )
    binding.last_commit = dict(out)
    binding.prior_commit_seen = True
    return out
