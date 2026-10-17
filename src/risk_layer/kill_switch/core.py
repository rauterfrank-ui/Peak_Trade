"""Kill Switch Core Implementation.

This is the heart of the Emergency Kill Switch system - Layer 4 of the
Defense-in-Depth architecture. It MUST always work, regardless of other
system failures.

Durable mode (a ``StatePersistence`` is bound):

- Every transition re-reads the durable state under a process-exclusive lock
  (compare-and-swap); in-memory state is never trusted for a transition.
- ``trigger`` journals KILL before taking the lock and never needs the approval
  secret. It never writes state without the lock; on lock timeout the journaled
  KILL alone already denies every ACTIVE reader.
- Recovery requires the approval secret from the environment (``approval_code_env``),
  an operator identity, the persisted request id, a valid recovery timestamp and
  an expired cooldown. ``require_approval_code`` cannot disable this.
- ACTIVE is written only with an HMAC attestation bound to the signed journal
  REQUESTED/COMPLETED pair. ACTIVE means "kill-switch recovery completed" only;
  it is not a trading, live or venue-POST authorization.
- A missing durable state file restores as KILLED (never armed); persisted
  DISABLED is never honored.
"""

from __future__ import annotations

import hmac
import logging
from datetime import datetime, timedelta
from threading import RLock
from typing import TYPE_CHECKING, Any, Callable, List, Optional

from .recovery_attestation import (
    KIND_KILL,
    KIND_RECOVERY_COMPLETED,
    KIND_RECOVERY_DENIED,
    KIND_RECOVERY_REQUESTED,
    JournalError,
    TransitionJournal,
    active_record_fields,
    active_state_superseded_by_journal,
    approval_code_matches,
    completed_event_fields,
    derive_attestation_key,
    journal_path_for_state_file,
    new_identifier,
    parse_naive_utc,
    requested_event_fields,
    resolve_approval_secret,
    sign_fields,
    verify_active_attestation,
    verify_pending_request_binding,
)
from .state import KillSwitchEvent, KillSwitchState

if TYPE_CHECKING:
    from .persistence import StatePersistence

DEFAULT_STATE_LOCK_TIMEOUT_SECONDS = 10.0
MAX_RECOVERY_FUTURE_SKEW_SECONDS = 1.0

DENY_NOT_KILLED = "RECOVERY_REQUIRES_KILLED"
DENY_NOT_RECOVERING = "COMPLETE_REQUIRES_RECOVERING"
DENY_AUTHORITY_MISSING = "RECOVERY_AUTHORITY_MISSING"
DENY_EXPECTED_CODE_UNAVAILABLE = "APPROVAL_EXPECTED_CODE_UNAVAILABLE"
DENY_CODE_MISSING = "APPROVAL_CODE_MISSING"
DENY_CODE_INVALID = "APPROVAL_CODE_INVALID"
DENY_REQUEST_ID_MISMATCH = "RECOVERY_REQUEST_ID_MISMATCH"
DENY_BINDING_MISSING = "RECOVERY_REQUEST_BINDING_MISSING"
DENY_TIMESTAMP_MISSING = "RECOVERY_TIMESTAMP_MISSING"
DENY_TIMESTAMP_INVALID = "RECOVERY_TIMESTAMP_INVALID"
DENY_TIMESTAMP_FUTURE = "RECOVERY_TIMESTAMP_IN_FUTURE"
DENY_COOLDOWN_ACTIVE = "RECOVERY_COOLDOWN_ACTIVE"
DENY_LOCK_TIMEOUT = "KILL_SWITCH_STATE_LOCK_TIMEOUT"
DENY_JOURNAL_UNAVAILABLE = "RECOVERY_JOURNAL_UNAVAILABLE"
DENY_AUDIT_WRITE_FAILED = "RECOVERY_AUDIT_WRITE_FAILED"
DENY_STATE_WRITE_FAILED = "RECOVERY_STATE_WRITE_FAILED"
DENY_KILL_PRIORITY = "RECOVERY_SUPERSEDED_BY_KILL"


class KillSwitchKillPendingError(RuntimeError):
    """KILL is journaled (every ACTIVE reader denies) but the state write was blocked."""


class KillSwitchKillFailedError(RuntimeError):
    """Neither the KILL journal entry nor the KILLED state could be made durable."""


class KillSwitch:
    """Emergency Kill Switch for Peak_Trade.

    Layer 4 of Defense-in-Depth architecture.
    Last line of defense - MUST ALWAYS WORK.

    Thread-safe through RLock; process-safe through the durable state lock.

    Usage:
        >>> config = {"recovery_cooldown_seconds": 300}
        >>> ks = KillSwitch(config)
        >>>
        >>> # Trigger emergency stop
        >>> ks.trigger("Drawdown threshold exceeded")
        >>>
        >>> # Check if trading is blocked
        >>> if ks.check_and_block():
        ...     raise TradingBlockedError()
        >>>
        >>> # Request recovery
        >>> ks.request_recovery("operator", "APPROVAL_CODE")
        >>>
        >>> # After cooldown
        >>> ks.complete_recovery("operator", "APPROVAL_CODE", request_id)
    """

    def __init__(
        self,
        config: dict,
        logger: Optional[logging.Logger] = None,
        persistence: Optional["StatePersistence"] = None,
    ):
        """Initialize Kill Switch.

        Args:
            config: Configuration dictionary (from config.toml)
            logger: Optional logger instance
            persistence: Optional durable store. When omitted and
                ``persist_state`` is true, binds ``StatePersistence`` at the
                canonical FILEGATE path.
        """
        self._lock = RLock()
        self._state = KillSwitchState.ACTIVE
        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        self._trigger_reason: Optional[str] = None
        self._persistence = self._bind_persistence(persistence, config)
        self._journal: Optional[TransitionJournal] = (
            TransitionJournal(journal_path_for_state_file(self._persistence.state_file))
            if self._persistence is not None
            else None
        )
        self._lock_timeout = float(
            config.get("state_lock_timeout_seconds", DEFAULT_STATE_LOCK_TIMEOUT_SECONDS)
        )
        self._recovery: Optional[dict] = None
        self._last_denial_reason: Optional[str] = None

        # Compatibility: Override flag for enabled property (does NOT mutate config)
        self._enabled_override: Optional[bool] = None

        # Check if disabled (backtest mode). A durable kill switch is never DISABLED.
        if config.get("mode") == "disabled":
            if self._persistence is None:
                self._state = KillSwitchState.DISABLED
                self._logger.warning(
                    "⚠️  Kill Switch DISABLED (Backtest Mode) - Trading will NOT be blocked!"
                )
            else:
                self._logger.critical(
                    "mode=disabled rejected for a durable kill switch; DISABLED is backtest-only"
                )

        # Event history for audit
        self._events: List[KillSwitchEvent] = []

        # Callbacks for state changes
        self._on_kill_callbacks: List[Callable[[KillSwitchEvent], None]] = []
        self._on_recover_callbacks: List[Callable[[KillSwitchEvent], None]] = []

        # Timestamps
        self._killed_at: Optional[datetime] = None
        self._recovery_started_at: Optional[datetime] = None

        # Cooldown configuration
        self._recovery_cooldown = timedelta(seconds=config.get("recovery_cooldown_seconds", 300))

        if self._persistence is not None:
            self._restore_from_persistence()

        self._logger.info(
            f"KillSwitch initialized: state={self._state.name}, cooldown={self._recovery_cooldown}"
        )

    def _bind_persistence(
        self,
        persistence: Optional[StatePersistence],
        config: dict,
    ) -> Optional[StatePersistence]:
        if persistence is not None:
            return persistence
        if not config.get("persist_state"):
            return None
        from src.ops.gates.risk_gate import (
            canonical_kill_switch_state_path,
            kill_switch_env_override_rejected,
        )

        from .persistence import StatePersistence as _StatePersistence

        path = canonical_kill_switch_state_path()
        if kill_switch_env_override_rejected():
            self._logger.critical(
                "Kill-switch state path env override rejected; persisting at canonical %s",
                path,
            )
        self._logger.info("KillSwitch persistence bound at %s", path)
        return _StatePersistence(path, logger_instance=self._logger)

    @staticmethod
    def _parse_iso_datetime(value: object) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return None

    # ------------------------------------------------------------------ durable state

    def _read_durable(self) -> tuple[KillSwitchState, dict]:
        """Classify the durable file fail-closed: missing/unreadable/invalid/DISABLED → KILLED."""
        assert self._persistence is not None
        data = self._persistence.load()
        path = self._persistence.state_file
        if data is None or not isinstance(data, dict):
            if path.is_file():
                self._logger.critical(
                    "Unreadable kill-switch state file %s; latching KILLED (fail-closed)", path
                )
            return KillSwitchState.KILLED, {}
        name = str(data.get("state", "")).strip().upper()
        try:
            restored = KillSwitchState[name]
        except KeyError:
            self._logger.critical(
                "Invalid kill-switch state %r in %s; latching KILLED (fail-closed)", name, path
            )
            return KillSwitchState.KILLED, {}
        if restored is KillSwitchState.DISABLED:
            self._logger.critical(
                "Persisted DISABLED in %s is never honored; latching KILLED (fail-closed)", path
            )
            return KillSwitchState.KILLED, {}
        if restored is KillSwitchState.ACTIVE and active_state_superseded_by_journal(path, data):
            self._logger.critical(
                "Persisted ACTIVE in %s is superseded by the transition journal; latching KILLED",
                path,
            )
            return KillSwitchState.KILLED, {}
        return restored, data

    def _sync_from_durable(self, state: KillSwitchState, data: dict) -> None:
        self._state = state
        self._killed_at = self._parse_iso_datetime(data.get("killed_at"))
        self._recovery_started_at = parse_naive_utc(data.get("recovery_started_at"))
        reason = data.get("trigger_reason")
        self._trigger_reason = str(reason) if reason else None
        recovery = data.get("recovery")
        self._recovery = (
            dict(recovery)
            if state is KillSwitchState.RECOVERING and isinstance(recovery, dict)
            else None
        )

    def _restore_from_persistence(self) -> None:
        """Load durable state. Nothing here ever arms ACTIVE on its own.

        Missing file → KILLED (never armed). Unreadable, invalid, DISABLED or
        journal-superseded ACTIVE → KILLED (fail-closed).
        """
        assert self._persistence is not None
        state, data = self._read_durable()
        self._sync_from_durable(state, data)
        self._logger.info("KillSwitch restored from persistence: state=%s", state.name)

    def _persist_current_state(self) -> None:
        if self._persistence is None:
            return
        with self._lock:
            state = self._state
            killed_at = self._killed_at
            recovery_started_at = self._recovery_started_at
            trigger_reason = self._trigger_reason
            recovery = dict(self._recovery) if self._recovery else None
        self._persistence.save(
            state,
            killed_at=killed_at,
            trigger_reason=trigger_reason,
            recovery_started_at=recovery_started_at,
            recovery=recovery,
        )

    # ------------------------------------------------------------------ authorization

    def _expected_approval_code(self) -> Optional[str]:
        env_secret = resolve_approval_secret(self._config.get("approval_code_env"))
        if self._persistence is not None:
            return env_secret
        configured = self._config.get("approval_code")
        return str(configured) if configured else env_secret

    def _approval_required(self) -> bool:
        return self._persistence is not None or bool(
            self._config.get("require_approval_code", False)
        )

    def _authorization_denial(
        self, approved_by: Optional[str], approval_code: Optional[str]
    ) -> Optional[str]:
        if not isinstance(approved_by, str) or not approved_by.strip():
            return DENY_AUTHORITY_MISSING
        if not self._approval_required():
            return None
        expected = self._expected_approval_code()
        if not expected:
            return DENY_EXPECTED_CODE_UNAVAILABLE
        if not isinstance(approval_code, str) or not approval_code.strip():
            return DENY_CODE_MISSING
        if not approval_code_matches(expected, approval_code):
            return DENY_CODE_INVALID
        return None

    def _deny(self, code: str, *, approved_by: Optional[str] = None) -> bool:
        self._last_denial_reason = code
        self._logger.error("❌ Kill-switch recovery denied: %s (by=%s)", code, approved_by)
        if self._journal is not None:
            try:
                self._journal.append(
                    {
                        "kind": KIND_RECOVERY_DENIED,
                        "reason_code": code,
                        "approved_by": approved_by,
                        "previous_state": self._state.name,
                        "new_state": self._state.name,
                        "triggered_by": "manual",
                        "trigger_reason": f"Recovery denied: {code}",
                    }
                )
            except Exception:  # denial is already the safe outcome
                self._logger.error("Failed to journal recovery denial %s", code, exc_info=True)
        return False

    # ------------------------------------------------------------------ properties

    @property
    def state(self) -> KillSwitchState:
        """Current state (thread-safe read)."""
        with self._lock:
            return self._state

    @property
    def is_killed(self) -> bool:
        """True if trading is stopped."""
        return self.state in (KillSwitchState.KILLED, KillSwitchState.RECOVERING)

    @property
    def is_active(self) -> bool:
        """True if the kill switch is ACTIVE (recovery completed; not a trading authorization)."""
        return self.state == KillSwitchState.ACTIVE

    @property
    def enabled(self) -> bool:
        """Check if Kill Switch is enabled.

        Compatibility property for callers that expect an ``enabled`` flag in config.

        Priority:
            1. Override flag (if set via setter)
            2. Config "enabled" key
            3. Default: True

        Returns:
            True if enabled, False if disabled
        """
        # Check override first (set via setter)
        if self._enabled_override is not None:
            return bool(self._enabled_override)

        # Check config
        cfg = getattr(self, "_config", None)
        if cfg is None:
            return True

        # Support both dict and object configs
        if isinstance(cfg, dict):
            return bool(cfg.get("enabled", True))

        return bool(getattr(cfg, "enabled", True))

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set enabled override.

        Does NOT mutate config - uses override flag instead.

        Args:
            value: True to enable, False to disable
        """
        with self._lock:
            self._enabled_override = bool(value)
            self._logger.debug(f"Kill Switch enabled override set to: {value}")

    @property
    def is_disabled(self) -> bool:
        """True if kill switch is disabled (backtest mode)."""
        return self.state == KillSwitchState.DISABLED

    @property
    def persistence_path(self) -> Optional[str]:
        """Durable state file path when persistence is bound, else None."""
        if self._persistence is None:
            return None
        return str(self._persistence.state_file)

    @property
    def journal_path(self) -> Optional[str]:
        """Durable transition journal path when persistence is bound, else None."""
        if self._journal is None:
            return None
        return str(self._journal.path)

    @property
    def last_denial_reason(self) -> Optional[str]:
        return self._last_denial_reason

    @property
    def pending_request_id(self) -> Optional[str]:
        """Request id of the current RECOVERING binding (not a secret)."""
        with self._lock:
            if self._state is KillSwitchState.RECOVERING and self._recovery:
                value = self._recovery.get("request_id")
                return str(value) if value else None
            return None

    # ------------------------------------------------------------------ transitions

    def _apply_kill_in_memory(
        self, reason: str, triggered_by: str, metadata: Optional[dict]
    ) -> Optional[KillSwitchEvent]:
        """Caller holds ``self._lock``. Returns the event for a real transition."""
        previous = self._state
        self._state = KillSwitchState.KILLED
        self._trigger_reason = reason
        self._recovery = None
        self._recovery_started_at = None
        if previous is KillSwitchState.KILLED:
            self._logger.warning("Kill Switch already KILLED (idempotent)")
            if self._killed_at is None:
                self._killed_at = datetime.utcnow()
            return None
        self._killed_at = datetime.utcnow()
        event = KillSwitchEvent(
            timestamp=self._killed_at,
            previous_state=previous,
            new_state=self._state,
            trigger_reason=reason,
            triggered_by=triggered_by,
            metadata=metadata or {},
        )
        self._events.append(event)
        self._logger.critical(
            f"🚨 KILL SWITCH TRIGGERED: {reason} (by={triggered_by}, from={previous.name})"
        )
        return event

    def trigger(
        self,
        reason: str,
        triggered_by: str = "system",
        metadata: Optional[dict] = None,
    ) -> bool:
        """Activate Kill Switch (EMERGENCY STOP).

        This is idempotent - calling multiple times is safe.

        Args:
            reason: Reason for trigger (for audit)
            triggered_by: Who triggered ("system", "manual", "threshold", etc.)
            metadata: Additional context data

        Returns:
            True if successfully triggered or already killed
            False if disabled (in-memory backtest mode only)

        Raises:
            KillSwitchKillPendingError: KILL journaled, state write blocked by the lock.
            KillSwitchKillFailedError: neither journal nor state could be made durable.
        """
        if self._persistence is None:
            with self._lock:
                if self._state == KillSwitchState.DISABLED:
                    self._logger.warning(
                        "⚠️  Kill Switch is DISABLED (Backtest Mode) - Trigger ignored"
                    )
                    return False
                event = self._apply_kill_in_memory(reason, triggered_by, metadata)
                callbacks = list(self._on_kill_callbacks) if event else []
            if event is not None:
                self._execute_callbacks(callbacks, event)
            return True

        assert self._journal is not None
        journaled = False
        try:
            self._journal.append(
                {
                    "kind": KIND_KILL,
                    "previous_state": self.state.name,
                    "new_state": KillSwitchState.KILLED.name,
                    "triggered_by": triggered_by,
                    "trigger_reason": reason,
                }
            )
            journaled = True
        except Exception:
            self._logger.critical("KILL journal append failed; persisting state", exc_info=True)

        from .persistence import StateLockTimeoutError

        try:
            with self._persistence.exclusive_lock(self._lock_timeout):
                with self._lock:
                    event = self._apply_kill_in_memory(reason, triggered_by, metadata)
                    callbacks = list(self._on_kill_callbacks) if event else []
                self._persist_current_state()
        except StateLockTimeoutError:
            with self._lock:
                event = self._apply_kill_in_memory(reason, triggered_by, metadata)
                callbacks = list(self._on_kill_callbacks) if event else []
            if event is not None:
                self._execute_callbacks(callbacks, event)
            if journaled:
                raise KillSwitchKillPendingError(
                    "KILL_JOURNALED_STATE_WRITE_BLOCKED_BY_LOCK"
                ) from None
            raise KillSwitchKillFailedError("KILL_NOT_DURABLE") from None
        if event is not None:
            self._execute_callbacks(callbacks, event)
        return True

    def request_recovery(
        self,
        approved_by: str,
        approval_code: Optional[str] = None,
    ) -> bool:
        """Start recovery process (with cooldown).

        Args:
            approved_by: Who approved the recovery
            approval_code: Approval code (mandatory in durable mode)

        Returns:
            True if recovery started (or already RECOVERING)
            False if denied
        """
        if self._persistence is None:
            return self._request_recovery_in_memory(approved_by, approval_code)

        from .persistence import StateLockTimeoutError

        try:
            with self._persistence.exclusive_lock(self._lock_timeout):
                with self._lock:
                    state, data = self._read_durable()
                    self._sync_from_durable(state, data)
                    if state is KillSwitchState.RECOVERING:
                        self._logger.info(
                            f"Already RECOVERING (idempotent request by {approved_by})"
                        )
                        return True
                    if state is not KillSwitchState.KILLED:
                        return self._deny(DENY_NOT_KILLED, approved_by=approved_by)
                    denial = self._authorization_denial(approved_by, approval_code)
                    if denial:
                        return self._deny(denial, approved_by=approved_by)
                    key = derive_attestation_key(self._expected_approval_code())
                    assert self._journal is not None and key is not None
                    try:
                        self._journal.read_events()
                    except JournalError as exc:
                        return self._deny(
                            f"{DENY_JOURNAL_UNAVAILABLE}:{exc}", approved_by=approved_by
                        )

                    started_at = datetime.utcnow()
                    request = {
                        "kind": KIND_RECOVERY_REQUESTED,
                        "event_id": new_identifier(),
                        "request_id": new_identifier(),
                        "recovery_started_at": started_at.isoformat(),
                        "cooldown_seconds": self._recovery_cooldown.total_seconds(),
                        "approved_by": approved_by,
                        "previous_state": KillSwitchState.KILLED.name,
                        "new_state": KillSwitchState.RECOVERING.name,
                        "triggered_by": "manual",
                        "trigger_reason": f"Recovery requested by {approved_by}",
                    }
                    request["tag"] = sign_fields(
                        key, requested_event_fields(self._persistence.state_file, request)
                    )
                    try:
                        self._journal.append(request)
                    except Exception:
                        self._logger.error("Recovery request journal write failed", exc_info=True)
                        return self._deny(DENY_AUDIT_WRITE_FAILED, approved_by=approved_by)

                    previous = self._state
                    self._state = KillSwitchState.RECOVERING
                    self._recovery_started_at = started_at
                    self._recovery = {
                        "request_id": request["request_id"],
                        "requested_event_id": request["event_id"],
                        "recovery_started_at": request["recovery_started_at"],
                        "cooldown_seconds": request["cooldown_seconds"],
                        "approved_by": approved_by,
                    }
                    self._events.append(
                        KillSwitchEvent(
                            timestamp=started_at,
                            previous_state=previous,
                            new_state=self._state,
                            trigger_reason=f"Recovery requested by {approved_by}",
                            triggered_by="manual",
                            metadata={
                                "approved_by": approved_by,
                                "request_id": request["request_id"],
                            },
                        )
                    )
                    self._persist_current_state()
                    self._last_denial_reason = None
                    self._logger.warning(
                        f"⏳ RECOVERY STARTED: cooldown={self._recovery_cooldown}, "
                        f"approved_by={approved_by}, request_id={request['request_id']}"
                    )
                    return True
        except StateLockTimeoutError:
            return self._deny(DENY_LOCK_TIMEOUT, approved_by=approved_by)

    def _request_recovery_in_memory(self, approved_by: str, approval_code: Optional[str]) -> bool:
        with self._lock:
            if self._state == KillSwitchState.RECOVERING:
                self._logger.info(f"Already RECOVERING (idempotent request by {approved_by})")
                return True
            if self._state != KillSwitchState.KILLED:
                self._logger.warning(
                    f"Recovery only possible from KILLED state, currently: {self._state.name}"
                )
                return False
            if self._approval_required() and not self._validate_approval_code(approval_code):
                self._last_denial_reason = DENY_CODE_INVALID
                self._logger.error("❌ Invalid Approval Code")
                return False
            previous = self._state
            self._state = KillSwitchState.RECOVERING
            self._recovery_started_at = datetime.utcnow()
            self._recovery = {"request_id": new_identifier()}
            self._events.append(
                KillSwitchEvent(
                    timestamp=self._recovery_started_at,
                    previous_state=previous,
                    new_state=self._state,
                    trigger_reason=f"Recovery requested by {approved_by}",
                    triggered_by="manual",
                    metadata={"approved_by": approved_by},
                )
            )
            self._logger.warning(
                f"⏳ RECOVERY STARTED: cooldown={self._recovery_cooldown}, "
                f"approved_by={approved_by}"
            )
            return True

    def _cooldown_denial(self, started_raw: object, bound_cooldown: object) -> Optional[str]:
        if started_raw in (None, ""):
            return DENY_TIMESTAMP_MISSING
        started = parse_naive_utc(started_raw)
        if started is None:
            return DENY_TIMESTAMP_INVALID
        now = datetime.utcnow()
        if started > now + timedelta(seconds=MAX_RECOVERY_FUTURE_SKEW_SECONDS):
            return DENY_TIMESTAMP_FUTURE
        cooldown = self._recovery_cooldown
        try:
            if bound_cooldown is not None:
                cooldown = max(cooldown, timedelta(seconds=float(bound_cooldown)))
        except (TypeError, ValueError):
            return DENY_BINDING_MISSING
        if now - started < cooldown:
            remaining = cooldown - (now - started)
            self._logger.warning(f"⏳ Cooldown still active: {remaining.seconds}s remaining")
            return DENY_COOLDOWN_ACTIVE
        return None

    def complete_recovery(
        self,
        approved_by: Optional[str] = None,
        approval_code: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> bool:
        """Complete recovery (after cooldown).

        Durable mode requires ``approved_by``, the approval code and the persisted
        ``request_id``. ACTIVE only means "kill-switch recovery completed".

        Returns:
            True if successfully recovered
            False if denied (see :attr:`last_denial_reason`)
        """
        if self._persistence is None:
            return self._complete_recovery_in_memory(approval_code, request_id)

        from .persistence import StateLockTimeoutError

        try:
            with self._persistence.exclusive_lock(self._lock_timeout):
                with self._lock:
                    event = self._complete_recovery_locked(approved_by, approval_code, request_id)
                    callbacks = list(self._on_recover_callbacks)
        except StateLockTimeoutError:
            return self._deny(DENY_LOCK_TIMEOUT, approved_by=approved_by)
        if not isinstance(event, KillSwitchEvent):
            return False
        self._execute_callbacks(callbacks, event)
        return True

    def _complete_recovery_locked(
        self,
        approved_by: Optional[str],
        approval_code: Optional[str],
        request_id: Optional[str],
    ) -> KillSwitchEvent | bool:
        """Returns the ACTIVE event on success, ``False`` on any denial."""
        assert self._persistence is not None and self._journal is not None
        state_file = self._persistence.state_file
        state, data = self._read_durable()
        self._sync_from_durable(state, data)
        if state is not KillSwitchState.RECOVERING:
            self._logger.warning(
                f"Complete recovery only possible from RECOVERING state, currently: {state.name}"
            )
            return self._deny(DENY_NOT_RECOVERING, approved_by=approved_by)
        binding = data.get("recovery")
        if not isinstance(binding, dict) or not all(
            isinstance(binding.get(k), str) and binding.get(k)
            for k in ("request_id", "requested_event_id", "recovery_started_at")
        ):
            return self._deny(DENY_BINDING_MISSING, approved_by=approved_by)
        if not isinstance(request_id, str) or not hmac.compare_digest(
            request_id.encode("utf-8"), str(binding["request_id"]).encode("utf-8")
        ):
            return self._deny(DENY_REQUEST_ID_MISMATCH, approved_by=approved_by)
        denial = self._authorization_denial(approved_by, approval_code)
        if denial:
            return self._deny(denial, approved_by=approved_by)
        if data.get("recovery_started_at") != binding.get("recovery_started_at"):
            return self._deny(DENY_TIMESTAMP_INVALID, approved_by=approved_by)
        denial = self._cooldown_denial(
            data.get("recovery_started_at"), binding.get("cooldown_seconds")
        )
        if denial:
            return self._deny(denial, approved_by=approved_by)

        key = derive_attestation_key(self._expected_approval_code())
        try:
            events = self._journal.read_events()
        except JournalError as exc:
            return self._deny(f"{DENY_JOURNAL_UNAVAILABLE}:{exc}", approved_by=approved_by)
        check = verify_pending_request_binding(
            state_file=state_file, events=events, recovery=binding, key=key
        )
        if not check.verified:
            return self._deny(f"{DENY_KILL_PRIORITY}:{check.reason}", approved_by=approved_by)

        assert key is not None
        completed_at = datetime.utcnow().isoformat()
        completed = {
            "kind": KIND_RECOVERY_COMPLETED,
            "event_id": new_identifier(),
            "request_id": binding["request_id"],
            "parent_event_id": binding["requested_event_id"],
            "completed_at": completed_at,
            "approved_by": approved_by,
            "previous_state": KillSwitchState.RECOVERING.name,
            "new_state": KillSwitchState.ACTIVE.name,
            "triggered_by": "manual",
            "trigger_reason": "Recovery completed",
        }
        completed["tag"] = sign_fields(key, completed_event_fields(state_file, completed))
        try:
            self._journal.append(completed)
        except Exception:
            self._logger.error("Recovery completion journal write failed", exc_info=True)
            return self._deny(DENY_AUDIT_WRITE_FAILED, approved_by=approved_by)

        record = {
            "request_id": binding["request_id"],
            "requested_event_id": binding["requested_event_id"],
            "completed_event_id": completed["event_id"],
            "recovery_started_at": binding["recovery_started_at"],
            "completed_at": completed_at,
        }
        record["attestation"] = sign_fields(key, active_record_fields(state_file, record))
        payload = {"state": KillSwitchState.ACTIVE.name, "recovery": record}
        pre_write = verify_active_attestation(state_file=state_file, payload=payload, key=key)
        if not pre_write.verified:
            return self._deny(f"{DENY_KILL_PRIORITY}:{pre_write.reason}", approved_by=approved_by)

        try:
            self._persistence.save(KillSwitchState.ACTIVE, recovery=record)
        except Exception:
            self._logger.error("ACTIVE state write failed; durable state unchanged", exc_info=True)
            return self._deny(DENY_STATE_WRITE_FAILED, approved_by=approved_by)

        written = self._persistence.load() or {}
        post_write = verify_active_attestation(state_file=state_file, payload=written, key=key)
        if not post_write.verified:
            self._logger.critical(
                "KILL won against concurrent recovery (%s); restoring KILLED", post_write.reason
            )
            self._apply_kill_in_memory(f"{DENY_KILL_PRIORITY}:{post_write.reason}", "system", None)
            self._persist_current_state()
            return self._deny(f"{DENY_KILL_PRIORITY}:{post_write.reason}", approved_by=approved_by)

        previous = self._state
        self._state = KillSwitchState.ACTIVE
        self._killed_at = None
        self._recovery_started_at = None
        self._trigger_reason = None
        self._recovery = None
        self._last_denial_reason = None
        event = KillSwitchEvent(
            timestamp=datetime.utcnow(),
            previous_state=previous,
            new_state=self._state,
            trigger_reason="Recovery completed",
            triggered_by="manual",
            metadata={"approved_by": approved_by, "request_id": record["request_id"]},
        )
        self._events.append(event)
        self._logger.info(
            "✅ KILL SWITCH RECOVERED (kill-switch only; no trading/POST authorization)"
        )
        return event

    def _complete_recovery_in_memory(
        self, approval_code: Optional[str], request_id: Optional[str]
    ) -> bool:
        with self._lock:
            if self._state != KillSwitchState.RECOVERING:
                self._logger.warning(
                    f"Complete recovery only possible from RECOVERING state, "
                    f"currently: {self._state.name}"
                )
                return False
            if request_id is not None and request_id != (self._recovery or {}).get("request_id"):
                self._last_denial_reason = DENY_REQUEST_ID_MISMATCH
                return False
            if self._recovery_started_at is None:
                self._last_denial_reason = DENY_TIMESTAMP_MISSING
                return False
            denial = self._cooldown_denial(self._recovery_started_at.isoformat(), None)
            if denial:
                self._last_denial_reason = denial
                return False

            previous = self._state
            self._state = KillSwitchState.ACTIVE
            event = KillSwitchEvent(
                timestamp=datetime.utcnow(),
                previous_state=previous,
                new_state=self._state,
                trigger_reason="Recovery completed",
                triggered_by="system",
                metadata={},
            )
            self._events.append(event)
            self._killed_at = None
            self._recovery_started_at = None
            self._trigger_reason = None
            self._recovery = None
            self._logger.info("✅ KILL SWITCH RECOVERED: Trading active again")
            callbacks = list(self._on_recover_callbacks)

        self._execute_callbacks(callbacks, event)
        return True

    def check_and_block(self) -> bool:
        """Check if trading is blocked.

        Returns:
            True if trading is BLOCKED (killed or recovering)
            False if trading is allowed

        Usage:
            if kill_switch.check_and_block():
                raise TradingBlockedError("Kill Switch active")
        """
        return self.is_killed

    def register_on_kill(self, callback: Callable[[KillSwitchEvent], None]):
        """Register callback for kill events.

        Args:
            callback: Function to call when kill switch is triggered
        """
        with self._lock:
            self._on_kill_callbacks.append(callback)

    def register_on_recover(self, callback: Callable[[KillSwitchEvent], None]):
        """Register callback for recovery events.

        Args:
            callback: Function to call when recovery completes
        """
        with self._lock:
            self._on_recover_callbacks.append(callback)

    def get_audit_trail(self) -> List[KillSwitchEvent]:
        """Get all events for audit.

        Returns:
            List of all kill switch events
        """
        with self._lock:
            return list(self._events)

    def get_status(self) -> dict:
        """Get current status information.

        Returns:
            Dictionary with current status
        """
        with self._lock:
            status: dict[str, Any] = {
                "state": self._state.name,
                "is_killed": self.is_killed,
                "is_active": self.is_active,
                "killed_at": self._killed_at.isoformat() if self._killed_at else None,
                "recovery_started_at": (
                    self._recovery_started_at.isoformat() if self._recovery_started_at else None
                ),
                "event_count": len(self._events),
                "request_id": self.pending_request_id,
                "last_denial_reason": self._last_denial_reason,
            }

            # Add cooldown info if recovering
            if self._state == KillSwitchState.RECOVERING and self._recovery_started_at:
                elapsed = datetime.utcnow() - self._recovery_started_at
                remaining = max(timedelta(0), self._recovery_cooldown - elapsed)
                status["cooldown_remaining_seconds"] = remaining.total_seconds()

            return status

    def _validate_approval_code(self, code: Optional[str]) -> bool:
        """Validate approval code (fail-closed, constant-time).

        A missing expected code, a missing provided code or a mismatch all deny.
        """
        return approval_code_matches(self._expected_approval_code(), code)

    def _execute_callbacks(
        self,
        callbacks: List[Callable],
        event: KillSwitchEvent,
    ):
        """Execute callbacks safely.

        Args:
            callbacks: List of callback functions
            event: Event to pass to callbacks
        """
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                self._logger.error(f"Callback error: {e}", exc_info=True)


class TradingBlockedError(Exception):
    """Exception raised when trading is blocked by Kill Switch."""

    def __init__(self, message: str = "Trading blocked by Kill Switch"):
        super().__init__(message)
