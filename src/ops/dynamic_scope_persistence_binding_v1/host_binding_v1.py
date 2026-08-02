"""Productive Dynamic Scope persistence binding for the single-future host.

SERIALIZATION_ADAPTER_HAS_NO_DECISION_AUTHORITY=true
CORE_LOGIC_CHANGE=false
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    ALLOWED_RESET_REASONS,
    DEFAULT_VENUE,
    FROZEN_ADVERSE_EXIT_DISTANCE,
    FROZEN_REVERSAL_DISTANCE,
    FROZEN_UP_DISTANCE,
    OWNER,
    STATE_VERSION,
)
from src.ops.dynamic_scope_persistence_binding_v1.models_v1 import (
    CanonicalDynamicScopeStateV1,
    ScopeResetRecordV1,
)
from src.ops.dynamic_scope_persistence_binding_v1.persistence_v1 import (
    DynamicScopePersistenceError,
    assert_no_silent_reinitialization_v1,
    load_dynamic_scope_state_v1,
    persist_dynamic_scope_state_atomic_v1,
    prior_commit_exists,
)
from src.ops.dynamic_scope_persistence_binding_v1.reason_codes_v1 import (
    DynamicScopeBindingFailureCodeV1,
)
from src.ops.dynamic_scope_persistence_binding_v1.single_writer_v1 import (
    DynamicScopeStateSingleWriterV1,
)
from trading.master_v2.canonical_scope_initialization_v1 import CanonicalScopeSnapshotV1
from trading.master_v2.double_play_state import RuntimeScopeState
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
    ObservationClassification,
)


def dynamic_scope_config_digest_v1(
    *,
    up_distance: float = FROZEN_UP_DISTANCE,
    adverse_exit_distance: float = FROZEN_ADVERSE_EXIT_DISTANCE,
    reversal_distance: float = FROZEN_REVERSAL_DISTANCE,
) -> str:
    material = (
        f"cap62-config:up={float(up_distance)}:"
        f"adverse={float(adverse_exit_distance)}:"
        f"reversal={float(reversal_distance)}:owner={OWNER}:sv={STATE_VERSION}"
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def stable_scope_session_id_v1(
    *,
    instrument_id: str,
    venue: str = DEFAULT_VENUE,
    repository_sha: str,
    config_digest: str,
) -> str:
    material = f"scope-session:{venue}:{instrument_id}:{repository_sha}:{config_digest}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    return f"scsess-{venue.lower()}-{instrument_id}-{digest}"


def _observation_identity_digest(result: ObservationAcceptanceResultV1 | None) -> str | None:
    if result is None or result.observation_identity is None:
        return None
    ident = result.observation_identity
    material = (
        f"{ident.venue}:{ident.canonical_instrument_id}:{ident.venue_event_time}:{ident.mark_price}"
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass
class HostDynamicScopeBindingV1:
    """Caller-owned Dynamic Scope binding surface carried by BridgeSessionStateV1."""

    enabled: bool = True
    scope_session_id: str = ""
    venue: str = DEFAULT_VENUE
    instrument_id: str = ""
    repository_sha: str = ""
    config_digest: str = ""
    existing_scope: Optional[CanonicalScopeSnapshotV1] = None
    runtime_scope_state: Optional[RuntimeScopeState] = None
    runtime_scope_bound_instrument_id: str = ""
    confirmation_session_id: str = ""
    market_observation_epoch: Optional[int] = None
    last_market_event_time: Optional[float] = None
    last_accepted_observation_identity_digest: Optional[str] = None
    position_context: dict[str, Any] = field(default_factory=dict)
    scope_direction_state: str = "LONG"
    side_state: str = "neutral_observe"
    host_trading_epoch: int = 0
    price_path_tail: tuple[float, ...] = ()
    previous_state_digest: str = ""
    last_reset: Optional[ScopeResetRecordV1] = None
    state_root: Optional[str] = None
    commit_sequence: int = 0
    prior_commit_seen: bool = False
    initialized: bool = False
    last_scope_advanced: bool = False
    alpha_blocked: bool = False
    alpha_block_reason: str = ""

    def to_canonical_state(self) -> CanonicalDynamicScopeStateV1:
        return CanonicalDynamicScopeStateV1(
            scope_session_id=self.scope_session_id,
            instrument_id=self.instrument_id,
            venue=self.venue,
            existing_scope=self.existing_scope,
            runtime_scope_state=self.runtime_scope_state,
            runtime_scope_bound_instrument_id=(
                self.runtime_scope_bound_instrument_id or self.instrument_id
            ),
            confirmation_session_id=self.confirmation_session_id,
            market_observation_epoch=self.market_observation_epoch,
            last_market_event_time=self.last_market_event_time,
            last_accepted_observation_identity_digest=(
                self.last_accepted_observation_identity_digest
            ),
            position_context=dict(self.position_context),
            scope_direction_state=self.scope_direction_state,
            side_state=self.side_state,
            host_trading_epoch=int(self.host_trading_epoch),
            price_path_tail=tuple(float(x) for x in self.price_path_tail),
            repository_sha=self.repository_sha,
            config_digest=self.config_digest,
            previous_state_digest=self.previous_state_digest,
            last_reset=self.last_reset,
            commit_identity="",
            commit_sequence=self.commit_sequence,
            prior_commit_seen=self.prior_commit_seen,
        )


def ensure_host_dynamic_scope_binding_v1(
    binding: HostDynamicScopeBindingV1,
    *,
    instrument_id: str,
    venue: str = DEFAULT_VENUE,
    repository_sha: str,
    config_digest: str | None = None,
    state_root: Path | None = None,
    require_load_if_prior_commit: bool = True,
) -> HostDynamicScopeBindingV1:
    """Initialize or restart-load Dynamic Scope binding. No silent reinitialization."""
    digest = config_digest or dynamic_scope_config_digest_v1()
    root = (
        Path(state_root)
        if state_root is not None
        else (Path(binding.state_root) if binding.state_root else None)
    )
    if binding.initialized and binding.scope_session_id:
        if binding.instrument_id != instrument_id:
            raise DynamicScopePersistenceError(
                DynamicScopeBindingFailureCodeV1.INSTRUMENT_ISOLATION_VIOLATION,
                f"{binding.instrument_id}!={instrument_id}",
            )
        if binding.repository_sha != repository_sha:
            raise DynamicScopePersistenceError(
                DynamicScopeBindingFailureCodeV1.REPOSITORY_SHA_MISMATCH,
                f"{binding.repository_sha}!={repository_sha}",
            )
        if binding.config_digest != digest:
            raise DynamicScopePersistenceError(
                DynamicScopeBindingFailureCodeV1.CONFIG_DIGEST_MISMATCH,
                f"{binding.config_digest}!={digest}",
            )
        return binding

    session_id = stable_scope_session_id_v1(
        instrument_id=instrument_id,
        venue=venue,
        repository_sha=repository_sha,
        config_digest=digest,
    )
    loaded: Optional[CanonicalDynamicScopeStateV1] = None
    if root is not None:
        binding.state_root = str(root)
        try:
            loaded = load_dynamic_scope_state_v1(
                root,
                require_present=bool(require_load_if_prior_commit and prior_commit_exists(root)),
                expected_repository_sha=repository_sha,
                expected_config_digest=digest,
                expected_instrument_id=instrument_id,
                allow_missing_before_first_state=not prior_commit_exists(root),
            )
        except DynamicScopePersistenceError as exc:
            # Missing/corrupt after prior commit: alpha block; never silent empty scope.
            if exc.code in {
                DynamicScopeBindingFailureCodeV1.CHECKPOINT_MISSING_AFTER_PRIOR_COMMIT,
                DynamicScopeBindingFailureCodeV1.CORRUPTED_CHECKPOINT,
                DynamicScopeBindingFailureCodeV1.CONFIG_DIGEST_MISMATCH,
                DynamicScopeBindingFailureCodeV1.STATE_VERSION_MISMATCH,
                DynamicScopeBindingFailureCodeV1.REPOSITORY_SHA_MISMATCH,
            }:
                binding.alpha_blocked = True
                binding.alpha_block_reason = exc.code.value
                binding.enabled = True
                binding.venue = venue
                binding.instrument_id = instrument_id
                binding.repository_sha = repository_sha
                binding.config_digest = digest
                binding.initialized = True
                binding.prior_commit_seen = True
                raise
            raise
        assert_no_silent_reinitialization_v1(
            state_root=root,
            loaded=loaded,
            initializing_fresh=loaded is None,
        )

    if loaded is not None:
        if loaded.scope_session_id != session_id:
            raise DynamicScopePersistenceError(
                DynamicScopeBindingFailureCodeV1.SESSION_ID_UNSTABLE,
                f"{loaded.scope_session_id}!={session_id}",
            )
        binding.scope_session_id = loaded.scope_session_id
        binding.existing_scope = loaded.existing_scope
        binding.runtime_scope_state = loaded.runtime_scope_state
        binding.runtime_scope_bound_instrument_id = loaded.runtime_scope_bound_instrument_id
        binding.confirmation_session_id = loaded.confirmation_session_id
        binding.market_observation_epoch = loaded.market_observation_epoch
        binding.last_market_event_time = loaded.last_market_event_time
        binding.last_accepted_observation_identity_digest = (
            loaded.last_accepted_observation_identity_digest
        )
        binding.position_context = dict(loaded.position_context)
        binding.scope_direction_state = loaded.scope_direction_state
        binding.side_state = loaded.side_state
        binding.host_trading_epoch = int(loaded.host_trading_epoch)
        binding.price_path_tail = tuple(float(x) for x in loaded.price_path_tail)
        binding.previous_state_digest = loaded.state_digest()
        binding.last_reset = loaded.last_reset
        binding.commit_sequence = loaded.commit_sequence
        binding.prior_commit_seen = True
    else:
        if root is not None and prior_commit_exists(root):
            raise DynamicScopePersistenceError(
                DynamicScopeBindingFailureCodeV1.SILENT_REINITIALIZATION_BLOCKED,
                str(root),
            )
        reset = ScopeResetRecordV1(
            reason="FIRST_EVER_STATE",
            authority=OWNER,
            previous_state_digest="",
            new_state_digest="",
            instrument_identity=instrument_id,
            event_time_context="FIRST_EVER_NO_EVENT_TIME",
        )
        binding.scope_session_id = session_id
        binding.existing_scope = None
        binding.runtime_scope_state = None
        binding.runtime_scope_bound_instrument_id = instrument_id
        binding.previous_state_digest = ""
        binding.last_reset = reset
        binding.commit_sequence = 0
        binding.prior_commit_seen = False

    binding.enabled = True
    binding.venue = venue
    binding.instrument_id = instrument_id
    binding.repository_sha = repository_sha
    binding.config_digest = digest
    binding.initialized = True
    binding.alpha_blocked = False
    binding.alpha_block_reason = ""
    return binding


def observation_may_advance_scope_v1(result: ObservationAcceptanceResultV1 | None) -> bool:
    """Duplicate / no-sample / out-of-order / non-advancing must not progress scope."""
    if result is None:
        return False
    if not bool(result.strategy_advance_allowed):
        return False
    if result.classification is ObservationClassification.DISTINCT:
        return True
    return False


def record_semantic_reset_v1(
    binding: HostDynamicScopeBindingV1,
    *,
    reason: str,
    authority: str,
    event_time_context: str,
    new_existing_scope: CanonicalScopeSnapshotV1 | None = None,
    new_runtime_scope_state: RuntimeScopeState | None = None,
) -> ScopeResetRecordV1:
    if reason not in ALLOWED_RESET_REASONS:
        raise DynamicScopePersistenceError(
            DynamicScopeBindingFailureCodeV1.INVALID_RESET_REASON,
            reason,
        )
    previous_digest = ""
    if binding.initialized and (
        binding.existing_scope is not None or binding.runtime_scope_state is not None
    ):
        previous_digest = binding.to_canonical_state().state_digest()
    binding.existing_scope = new_existing_scope
    binding.runtime_scope_state = new_runtime_scope_state
    binding.runtime_scope_bound_instrument_id = binding.instrument_id
    provisional = binding.to_canonical_state()
    reset = ScopeResetRecordV1(
        reason=reason,
        authority=authority,
        previous_state_digest=previous_digest,
        new_state_digest=provisional.state_digest(),
        instrument_identity=binding.instrument_id,
        event_time_context=event_time_context,
    )
    binding.last_reset = reset
    binding.previous_state_digest = previous_digest
    return reset


def commit_host_dynamic_scope_after_replay_v1(
    binding: HostDynamicScopeBindingV1,
    *,
    observation_acceptance_result: ObservationAcceptanceResultV1 | None,
    current_scope: CanonicalScopeSnapshotV1 | None,
    runtime_scope_state_after: RuntimeScopeState | None,
    confirmation_session_id: str,
    market_observation_epoch: int | None,
    last_market_event_time: float | None,
    position_context: Mapping[str, Any],
    scope_direction_state: str,
    side_state: str,
    host_trading_epoch: int,
    price_path_tail: tuple[float, ...] | list[float],
    persist: bool = True,
    writer_session_id: str | None = None,
    runtime_scope_reinitialized: bool = False,
) -> Mapping[str, Any]:
    """Adopt and optionally persist scope only when observation may advance scope."""
    if binding.alpha_blocked:
        raise DynamicScopePersistenceError(
            DynamicScopeBindingFailureCodeV1.ALPHA_BLOCKED_SCOPE_STATE_UNRECOVERABLE,
            binding.alpha_block_reason,
        )
    if not binding.initialized:
        raise RuntimeError("DYNAMIC_SCOPE_BINDING_NOT_INITIALIZED")

    may_advance = observation_may_advance_scope_v1(observation_acceptance_result)
    binding.last_scope_advanced = False
    if not may_advance:
        return {
            "persisted": False,
            "scope_advanced": False,
            "reason": "NON_ADVANCING_OBSERVATION_SCOPE_NOOP",
            "classification": (
                None
                if observation_acceptance_result is None
                else observation_acceptance_result.classification.value
            ),
        }
    if current_scope is None or runtime_scope_state_after is None:
        return {
            "persisted": False,
            "scope_advanced": False,
            "reason": "SCOPE_NOT_MATERIALIZED_THIS_CYCLE",
        }

    previous_digest = ""
    if binding.existing_scope is not None or binding.runtime_scope_state is not None:
        previous_digest = binding.to_canonical_state().state_digest()

    # First productive scope materialization is a classified FIRST_EVER_STATE reset.
    if binding.runtime_scope_state is None and runtime_scope_state_after is not None:
        record_semantic_reset_v1(
            binding,
            reason="FIRST_EVER_STATE",
            authority=OWNER,
            event_time_context=str(last_market_event_time or ""),
            new_existing_scope=current_scope,
            new_runtime_scope_state=runtime_scope_state_after,
        )
    elif runtime_scope_reinitialized and binding.prior_commit_seen:
        # Productive reinit after prior commit is forbidden unless classified reset.
        # Treat unexpected reinit as fail-closed governed path marker.
        raise DynamicScopePersistenceError(
            DynamicScopeBindingFailureCodeV1.SILENT_REINITIALIZATION_BLOCKED,
            "RUNTIME_SCOPE_REINITIALIZED_AFTER_PRIOR_COMMIT",
        )
    else:
        binding.existing_scope = current_scope
        binding.runtime_scope_state = runtime_scope_state_after
        binding.runtime_scope_bound_instrument_id = binding.instrument_id

    binding.confirmation_session_id = confirmation_session_id
    binding.market_observation_epoch = market_observation_epoch
    binding.last_market_event_time = last_market_event_time
    binding.last_accepted_observation_identity_digest = _observation_identity_digest(
        observation_acceptance_result
    )
    binding.position_context = dict(position_context)
    binding.scope_direction_state = scope_direction_state
    binding.side_state = str(side_state)
    binding.host_trading_epoch = int(host_trading_epoch)
    binding.price_path_tail = tuple(float(x) for x in price_path_tail)
    binding.previous_state_digest = previous_digest
    binding.last_scope_advanced = True

    persist_result: dict[str, Any] = {"persisted": False, "scope_advanced": True}
    if persist and binding.state_root:
        root = Path(binding.state_root)
        writer = DynamicScopeStateSingleWriterV1(
            state_root=root,
            session_id=writer_session_id or binding.scope_session_id,
            instrument_id=binding.instrument_id,
        )
        writer.acquire()
        try:
            canonical = binding.to_canonical_state()
            out = persist_dynamic_scope_state_atomic_v1(
                state_root=root,
                state=canonical,
                writer=writer,
            )
            committed_state: CanonicalDynamicScopeStateV1 = out["state"]
            binding.commit_sequence = committed_state.commit_sequence
            binding.prior_commit_seen = True
            binding.previous_state_digest = previous_digest
            persist_result = {
                "persisted": True,
                "scope_advanced": True,
                "commit_identity": committed_state.commit_identity,
                "commit_sequence": committed_state.commit_sequence,
                "state_digest": committed_state.state_digest(),
            }
        finally:
            writer.release()
    return persist_result
