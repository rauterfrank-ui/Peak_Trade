"""Pre-Economic Zero-Order Evidence session runner v1 (implementation readiness).

Capability: PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_IMPLEMENTATION_READINESS_V1

Offline / dry-run session simulation with durable evidence emission.
Never authorizes Shadow / Paper / Testnet / Live / Economic PASS.
Never submits orders. Never starts a real 6h session without a separate,
explicit operator-authorization capability (not present here).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import tempfile
import tomllib
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Protocol

PACKAGE_MARKER = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_IMPLEMENTATION_READINESS_V1=true"
CAPABILITY_ID = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_IMPLEMENTATION_READINESS_V1"
SESSION_CONTRACT_ID = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1"
PRODUCER_FAMILY = "ops.pre_economic_zero_order_evidence_session_runner_v1"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v1"
EVIDENCE_SCHEMA_VERSION = "v1"
CONTRACT_VERSION = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1"
DEFAULT_CONFIG_RELPATH = "config/ops/pre_economic_zero_order_evidence_session_v1.toml"
CONTRACT_DOC_RELPATH = "docs/ops/runbooks/PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1.md"

RUNTIME_AUTHORITY_NONE = "NONE"
PRODUCTION_SESSION_DURATION_SECONDS = 21600

SENSITIVE_KEY_FRAGMENTS = frozenset(
    {
        "secret",
        "token",
        "password",
        "api_key",
        "apikey",
        "private_key",
        "access_key",
        "credential",
        "passwd",
        "bearer",
    }
)
SENSITIVE_KEY_EXACT = frozenset(
    {
        "auth",
        "authorization",
        "authentication",
    }
)

_PATH_ESCAPE = re.compile(r"(^|/)\.\.(/|$)")

KNOWN_CONFIG_KEYS = frozenset(
    {
        "schema_version",
        "contract_version",
        "capability_id",
        "implementation_enabled",
        "session_execution_authorized",
        "operator_go_required",
        "dry_run",
        "zero_order_enforced",
        "maximum_test_runtime_seconds",
        "production_session_duration_seconds",
        "output_root",
        "heartbeat_interval_seconds",
        "stale_threshold_seconds",
        "maximum_test_cycles",
        "runtime_authority",
        "orders_allowed",
        "broker_writes_allowed",
        "network_allowed",
        "allow_unknown_config_fields",
    }
)


class PreEconomicSessionRunnerError(ValueError):
    """Fail-closed runner / config / evidence error."""


class TelemetryState(str, Enum):
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    HEARTBEAT = "HEARTBEAT"
    HOLD = "HOLD"
    ABORTING = "ABORTING"
    ABORTED = "ABORTED"
    COMPLETED = "COMPLETED"
    INVALID = "INVALID"


TERMINAL_STATES = frozenset(
    {
        TelemetryState.ABORTED,
        TelemetryState.COMPLETED,
        TelemetryState.INVALID,
    }
)

ALLOWED_TRANSITIONS: dict[TelemetryState, frozenset[TelemetryState]] = {
    TelemetryState.INITIALIZING: frozenset(
        {
            TelemetryState.READY,
            TelemetryState.HOLD,
            TelemetryState.ABORTING,
            TelemetryState.INVALID,
        }
    ),
    TelemetryState.READY: frozenset(
        {
            TelemetryState.RUNNING,
            TelemetryState.HOLD,
            TelemetryState.ABORTING,
            TelemetryState.INVALID,
        }
    ),
    TelemetryState.RUNNING: frozenset(
        {
            TelemetryState.HEARTBEAT,
            TelemetryState.HOLD,
            TelemetryState.ABORTING,
            TelemetryState.COMPLETED,
            TelemetryState.INVALID,
        }
    ),
    TelemetryState.HEARTBEAT: frozenset(
        {
            TelemetryState.RUNNING,
            TelemetryState.HEARTBEAT,
            TelemetryState.HOLD,
            TelemetryState.ABORTING,
            TelemetryState.COMPLETED,
            TelemetryState.INVALID,
        }
    ),
    TelemetryState.HOLD: frozenset(
        {
            TelemetryState.ABORTING,
            TelemetryState.ABORTED,
            TelemetryState.INVALID,
        }
    ),
    TelemetryState.ABORTING: frozenset(
        {
            TelemetryState.ABORTED,
            TelemetryState.INVALID,
        }
    ),
    TelemetryState.ABORTED: frozenset(),
    TelemetryState.COMPLETED: frozenset(),
    TelemetryState.INVALID: frozenset(),
}

HEARTBEAT_ALLOWED_FROM = frozenset(
    {
        TelemetryState.RUNNING,
        TelemetryState.HEARTBEAT,
    }
)


class AbortReason(str, Enum):
    OPERATOR_ABORT = "OPERATOR_ABORT"
    SIGNAL_ABORT = "SIGNAL_ABORT"
    HEARTBEAT_TIMEOUT = "HEARTBEAT_TIMEOUT"
    TELEMETRY_FAILURE = "TELEMETRY_FAILURE"
    EVIDENCE_WRITE_FAILURE = "EVIDENCE_WRITE_FAILURE"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    CONFIG_MISMATCH = "CONFIG_MISMATCH"
    UNEXPECTED_EXCEPTION = "UNEXPECTED_EXCEPTION"
    TIME_BUDGET_EXCEEDED = "TIME_BUDGET_EXCEEDED"
    ORDER_ATTEMPT_FORBIDDEN = "ORDER_ATTEMPT_FORBIDDEN"
    SESSION_NOT_AUTHORIZED = "SESSION_NOT_AUTHORIZED"
    PRODUCTION_DURATION_BLOCKED = "PRODUCTION_DURATION_BLOCKED"
    NONE = "NONE"


class Clock(Protocol):
    def now(self) -> float: ...


@dataclass
class ControllableClock:
    """Monotone injectable clock (seconds)."""

    _now: float = 0.0

    def now(self) -> float:
        return float(self._now)

    def advance(self, seconds: float) -> float:
        if seconds < 0:
            raise PreEconomicSessionRunnerError("CLOCK_NON_MONOTONE_ADVANCE")
        self._now = float(self._now + seconds)
        return self._now


@dataclass(frozen=True)
class SessionConfigV1:
    schema_version: str
    contract_version: str
    capability_id: str
    implementation_enabled: bool
    session_execution_authorized: bool
    operator_go_required: bool
    dry_run: bool
    zero_order_enforced: bool
    maximum_test_runtime_seconds: int
    production_session_duration_seconds: int
    output_root: str
    heartbeat_interval_seconds: float
    stale_threshold_seconds: float
    maximum_test_cycles: int
    runtime_authority: str
    orders_allowed: bool
    broker_writes_allowed: bool
    network_allowed: bool
    allow_unknown_config_fields: bool
    config_path: str
    config_digest: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TelemetryEventV1:
    sequence: int
    state: str
    elapsed_seconds: float
    timestamp: float
    detail: str = ""
    abort_reason: str = AbortReason.NONE.value


@dataclass
class TelemetryLedgerV1:
    session_id: str
    events: list[TelemetryEventV1] = field(default_factory=list)
    current_state: TelemetryState = TelemetryState.INITIALIZING
    heartbeat_count: int = 0
    terminal_emitted: bool = False

    def transition(
        self,
        *,
        to_state: TelemetryState,
        clock: Clock,
        start_ts: float,
        detail: str = "",
        abort_reason: AbortReason = AbortReason.NONE,
    ) -> TelemetryEventV1:
        if self.terminal_emitted or self.current_state in TERMINAL_STATES:
            raise PreEconomicSessionRunnerError("EVENT_AFTER_TERMINAL_STATE")
        allowed = ALLOWED_TRANSITIONS.get(self.current_state, frozenset())
        if to_state not in allowed:
            raise PreEconomicSessionRunnerError(
                f"INVALID_STATE_TRANSITION:{self.current_state.value}->{to_state.value}"
            )
        if (
            to_state == TelemetryState.HEARTBEAT
            and self.current_state not in HEARTBEAT_ALLOWED_FROM
        ):
            raise PreEconomicSessionRunnerError("HEARTBEAT_IN_INVALID_STATE")
        now = float(clock.now())
        elapsed = now - float(start_ts)
        if elapsed < 0:
            raise PreEconomicSessionRunnerError("NON_MONOTONE_ELAPSED")
        if self.events and elapsed + 1e-12 < self.events[-1].elapsed_seconds:
            raise PreEconomicSessionRunnerError("NON_MONOTONE_TIME")
        seq = len(self.events) + 1
        if self.events and seq <= self.events[-1].sequence:
            raise PreEconomicSessionRunnerError("NON_MONOTONE_SEQUENCE")
        event = TelemetryEventV1(
            sequence=seq,
            state=to_state.value,
            elapsed_seconds=elapsed,
            timestamp=now,
            detail=detail,
            abort_reason=abort_reason.value,
        )
        self.events.append(event)
        if to_state == TelemetryState.HEARTBEAT:
            self.heartbeat_count += 1
        self.current_state = to_state
        if to_state in TERMINAL_STATES:
            if self.terminal_emitted:
                raise PreEconomicSessionRunnerError("DUPLICATE_TERMINAL_EVENT")
            self.terminal_emitted = True
        return event

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "current_state": self.current_state.value,
            "heartbeat_count": self.heartbeat_count,
            "terminal_emitted": self.terminal_emitted,
            "events": [asdict(e) for e in self.events],
        }


def redact_mapping(value: Any) -> Any:
    """Recursively redact sensitive keys; never persist secrets."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            key_l = str(key).lower()
            key_parts = set(key_l.replace("-", "_").split("_"))
            if key_l in SENSITIVE_KEY_EXACT or key_parts & SENSITIVE_KEY_EXACT:
                out[str(key)] = "[REDACTED]"
            elif any(frag in key_l for frag in SENSITIVE_KEY_FRAGMENTS):
                out[str(key)] = "[REDACTED]"
            else:
                out[str(key)] = redact_mapping(item)
        return out
    if isinstance(value, list):
        return [redact_mapping(v) for v in value]
    if isinstance(value, tuple):
        return [redact_mapping(v) for v in value]
    return value


def _canonical_json(payload: Mapping[str, Any] | list[Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def atomic_write_text(*, path: Path, text: str, verify_readback: bool = True) -> str:
    """Temp + flush/fsync + atomic replace + optional read-back verification."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_symlink():
        raise PreEconomicSessionRunnerError("SYMLINK_OUTPUT_FORBIDDEN")
    data = text.encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".tmp_{path.name}_",
        suffix=".partial",
    )
    closed = False
    try:
        with os.fdopen(fd, "wb") as handle:
            closed = True
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except OSError as exc:
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        raise PreEconomicSessionRunnerError(f"EVIDENCE_WRITE_FAILURE:{exc}") from exc
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        raise
    finally:
        if not closed:
            try:
                os.close(fd)
            except OSError:
                pass
    if verify_readback:
        read_back = path.read_bytes()
        if hashlib.sha256(read_back).hexdigest() != digest:
            raise PreEconomicSessionRunnerError("INTEGRITY_FAILURE:READBACK_MISMATCH")
    return digest


def resolve_output_root(*, repo_root: Path, output_root: str) -> Path:
    raw = str(output_root or "").strip()
    if not raw:
        raise PreEconomicSessionRunnerError("OUTPUT_ROOT_EMPTY")
    if raw.startswith("/") or _PATH_ESCAPE.search(raw) or "\\" in raw:
        raise PreEconomicSessionRunnerError("OUTPUT_PATH_ESCAPE")
    root = repo_root.resolve()
    candidate = root / raw
    if candidate.exists() and candidate.is_symlink():
        raise PreEconomicSessionRunnerError("SYMLINK_OUTPUT_FORBIDDEN")
    dest = candidate.resolve()
    try:
        dest.relative_to(root)
    except ValueError as exc:
        raise PreEconomicSessionRunnerError("OUTPUT_PATH_OUTSIDE_REPO") from exc
    if dest.exists() and dest.is_symlink():
        raise PreEconomicSessionRunnerError("SYMLINK_OUTPUT_FORBIDDEN")
    return dest


def load_session_config_v1(
    *,
    repo_root: Path,
    config_path: Optional[Path] = None,
) -> SessionConfigV1:
    path = config_path or (repo_root / DEFAULT_CONFIG_RELPATH)
    if not path.is_file():
        raise PreEconomicSessionRunnerError("CONFIG_MISSING")
    raw_text = path.read_text(encoding="utf-8")
    try:
        raw = tomllib.loads(raw_text)
    except tomllib.TOMLDecodeError as exc:
        raise PreEconomicSessionRunnerError(f"CONFIG_PARSE_ERROR:{exc}") from exc
    if not isinstance(raw, dict):
        raise PreEconomicSessionRunnerError("CONFIG_NOT_TABLE")

    unknown = sorted(set(raw) - KNOWN_CONFIG_KEYS)
    allow_unknown = bool(raw.get("allow_unknown_config_fields", False))
    if unknown and not allow_unknown:
        raise PreEconomicSessionRunnerError("UNKNOWN_CONFIG_FIELDS:" + ",".join(unknown))

    def _req(key: str) -> Any:
        if key not in raw:
            raise PreEconomicSessionRunnerError(f"CONFIG_FIELD_MISSING:{key}")
        return raw[key]

    cfg = SessionConfigV1(
        schema_version=str(_req("schema_version")),
        contract_version=str(_req("contract_version")),
        capability_id=str(_req("capability_id")),
        implementation_enabled=bool(_req("implementation_enabled")),
        session_execution_authorized=bool(_req("session_execution_authorized")),
        operator_go_required=bool(_req("operator_go_required")),
        dry_run=bool(_req("dry_run")),
        zero_order_enforced=bool(_req("zero_order_enforced")),
        maximum_test_runtime_seconds=int(_req("maximum_test_runtime_seconds")),
        production_session_duration_seconds=int(_req("production_session_duration_seconds")),
        output_root=str(_req("output_root")),
        heartbeat_interval_seconds=float(_req("heartbeat_interval_seconds")),
        stale_threshold_seconds=float(_req("stale_threshold_seconds")),
        maximum_test_cycles=int(_req("maximum_test_cycles")),
        runtime_authority=str(_req("runtime_authority")),
        orders_allowed=bool(_req("orders_allowed")),
        broker_writes_allowed=bool(_req("broker_writes_allowed")),
        network_allowed=bool(_req("network_allowed")),
        allow_unknown_config_fields=allow_unknown,
        config_path=_repo_relative_or_str(path, repo_root.resolve()),
        config_digest=_sha256_text(raw_text),
    )
    _validate_config_invariants(cfg)
    return cfg


def _repo_relative_or_str(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


def _validate_config_invariants(cfg: SessionConfigV1) -> None:
    if cfg.schema_version != SCHEMA_VERSION:
        raise PreEconomicSessionRunnerError("CONFIG_SCHEMA_VERSION_MISMATCH")
    if cfg.contract_version != CONTRACT_VERSION:
        raise PreEconomicSessionRunnerError("CONFIG_CONTRACT_VERSION_MISMATCH")
    if cfg.capability_id != CAPABILITY_ID:
        raise PreEconomicSessionRunnerError("CONFIG_CAPABILITY_MISMATCH")
    if cfg.runtime_authority != RUNTIME_AUTHORITY_NONE:
        raise PreEconomicSessionRunnerError("CONFIG_RUNTIME_AUTHORITY_MUST_BE_NONE")
    if cfg.orders_allowed is not False:
        raise PreEconomicSessionRunnerError("CONFIG_ORDERS_MUST_BE_FALSE")
    if cfg.broker_writes_allowed is not False:
        raise PreEconomicSessionRunnerError("CONFIG_BROKER_WRITES_MUST_BE_FALSE")
    if cfg.network_allowed is not False:
        raise PreEconomicSessionRunnerError("CONFIG_NETWORK_MUST_BE_FALSE")
    if cfg.zero_order_enforced is not True:
        raise PreEconomicSessionRunnerError("CONFIG_ZERO_ORDER_MUST_BE_TRUE")
    if cfg.operator_go_required is not True:
        raise PreEconomicSessionRunnerError("CONFIG_OPERATOR_GO_REQUIRED_MUST_BE_TRUE")
    if cfg.production_session_duration_seconds != PRODUCTION_SESSION_DURATION_SECONDS:
        raise PreEconomicSessionRunnerError("CONFIG_PRODUCTION_DURATION_MISMATCH")
    if cfg.maximum_test_runtime_seconds <= 0:
        raise PreEconomicSessionRunnerError("CONFIG_TEST_RUNTIME_INVALID")
    if cfg.maximum_test_runtime_seconds >= PRODUCTION_SESSION_DURATION_SECONDS:
        raise PreEconomicSessionRunnerError("CONFIG_TEST_RUNTIME_TOO_LARGE")
    if cfg.heartbeat_interval_seconds <= 0:
        raise PreEconomicSessionRunnerError("CONFIG_HEARTBEAT_INTERVAL_INVALID")
    if cfg.stale_threshold_seconds <= 0:
        raise PreEconomicSessionRunnerError("CONFIG_STALE_THRESHOLD_INVALID")
    if cfg.stale_threshold_seconds < cfg.heartbeat_interval_seconds:
        raise PreEconomicSessionRunnerError("CONFIG_STALE_THRESHOLD_TOO_SMALL")
    if cfg.maximum_test_cycles <= 0:
        raise PreEconomicSessionRunnerError("CONFIG_MAX_CYCLES_INVALID")
    # Unsafe combinations: authorized real session with defaults of this capability.
    if cfg.session_execution_authorized and not cfg.dry_run:
        raise PreEconomicSessionRunnerError("CONFIG_UNSAFE_SESSION_AUTHORIZATION")
    if cfg.implementation_enabled and cfg.session_execution_authorized:
        raise PreEconomicSessionRunnerError("CONFIG_UNSAFE_IMPLEMENTATION_PLUS_AUTH")


@dataclass
class EvidenceEmitterV1:
    """Versioned evidence emitter with atomic writes and hash chain."""

    evidence_root: Path
    session_id: str
    digests: dict[str, str] = field(default_factory=dict)

    def write_json(self, relative_name: str, payload: Mapping[str, Any] | list[Any]) -> str:
        safe = relative_name.replace("\\", "/")
        if _PATH_ESCAPE.search(safe) or safe.startswith("/"):
            raise PreEconomicSessionRunnerError("EVIDENCE_PATH_ESCAPE")
        path = self.evidence_root / safe
        try:
            path.relative_to(self.evidence_root.resolve())
        except ValueError as exc:
            raise PreEconomicSessionRunnerError("EVIDENCE_PATH_ESCAPE") from exc
        redacted = redact_mapping(payload)
        text = _canonical_json(redacted)  # type: ignore[arg-type]
        digest = atomic_write_text(path=path, text=text)
        self.digests[safe] = digest
        return digest

    def write_manifest(self) -> str:
        lines = [f"{digest}  {name}" for name, digest in sorted(self.digests.items())]
        text = "\n".join(lines) + ("\n" if lines else "")
        path = self.evidence_root / "evidence_manifest.sha256"
        digest = atomic_write_text(path=path, text=text)
        self.digests["evidence_manifest.sha256"] = digest
        return digest


@dataclass
class SessionRunResultV1:
    capability_id: str
    session_id: str
    mode: str
    terminal_state: str
    abort_reason: str
    orders_attempted: int
    orders_submitted: int
    zero_order_enforced: bool
    runtime_authority: str
    operator_go_present: bool
    start_timestamp: float
    end_timestamp: float
    elapsed_seconds: float
    heartbeat_count: int
    expected_heartbeat_count: int
    completeness: str
    integrity_status: str
    config_digest: str
    implementation_digest: str
    evidence_root: str
    generated_files: tuple[str, ...]
    consumer_eligibility: bool
    implementation_readiness: str
    session_evidence_status: str
    economic_gate_effect: str
    shadow_activation_eligible: bool
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def forbid_order_attempt(action: str = "order") -> None:
    """Hard technical intercept for any order-shaped attempt."""

    raise PreEconomicSessionRunnerError(f"ORDER_ATTEMPT_FORBIDDEN:{action}")


def _implementation_digest(*, repo_root: Path, head_sha: Optional[str]) -> str:
    identity = {
        "capability_id": CAPABILITY_ID,
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "head_sha": head_sha or "UNKNOWN",
        "runner_module": PRODUCER_FAMILY,
    }
    return _sha256_text(_canonical_json(identity))


def run_pre_economic_zero_order_evidence_session_v1(
    *,
    repo_root: Path,
    config: Optional[SessionConfigV1] = None,
    session_id: Optional[str] = None,
    clock: Optional[Clock] = None,
    max_cycles: Optional[int] = None,
    requested_duration_seconds: Optional[int] = None,
    operator_go_present: bool = False,
    dry_run_override: Optional[bool] = None,
    allow_implementation_dry_run: bool = False,
    force_abort: Optional[AbortReason] = None,
    inject_exception: Optional[BaseException] = None,
    order_attempt: bool = False,
    head_sha: Optional[str] = None,
    evidence_subdir: Optional[str] = None,
    install_signal_handlers: bool = False,
    on_signal: Optional[Callable[[], None]] = None,
) -> SessionRunResultV1:
    """Run offline/dry-run evidence session simulation (never real 6h by default).

    Real production duration (21600s) is always rejected in this capability.
    ``session_execution_authorized`` remains false in canonical config.
    """

    root = repo_root.resolve()
    cfg = config or load_session_config_v1(repo_root=root)
    clk: Clock = clock or ControllableClock(0.0)
    sid = session_id or f"pez_{_sha256_text(str(clk.now()))[:16]}"
    dry_run = cfg.dry_run if dry_run_override is None else bool(dry_run_override)
    cycles = int(max_cycles if max_cycles is not None else cfg.maximum_test_cycles)
    requested = (
        int(requested_duration_seconds)
        if requested_duration_seconds is not None
        else int(cfg.maximum_test_runtime_seconds)
    )

    output_root = resolve_output_root(repo_root=root, output_root=cfg.output_root)
    evidence_root = output_root / (evidence_subdir or sid)
    if evidence_root.exists() and any(evidence_root.iterdir()):
        raise PreEconomicSessionRunnerError("EVIDENCE_DIR_NONEMPTY")
    evidence_root.mkdir(parents=True, exist_ok=True)

    emitter = EvidenceEmitterV1(evidence_root=evidence_root, session_id=sid)
    ledger = TelemetryLedgerV1(session_id=sid)
    start_ts = float(clk.now())
    abort_reason = AbortReason.NONE
    orders_attempted = 0
    orders_submitted = 0
    terminal_state = TelemetryState.INITIALIZING
    completeness = "INCOMPLETE"
    integrity_status = "UNKNOWN"
    signal_abort_flag = {"armed": False}

    def _handle_signal(_signum: int, _frame: Any) -> None:
        signal_abort_flag["armed"] = True
        if on_signal is not None:
            on_signal()

    previous_handlers: dict[int, Any] = {}
    if install_signal_handlers:
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[sig] = signal.signal(sig, _handle_signal)

    # Seed INITIALIZING event without invalid self-transition.
    now = float(clk.now())
    ledger.events.append(
        TelemetryEventV1(
            sequence=1,
            state=TelemetryState.INITIALIZING.value,
            elapsed_seconds=0.0,
            timestamp=now,
            detail="seed",
        )
    )
    ledger.current_state = TelemetryState.INITIALIZING

    try:
        # Authorization / duration guards (fail-closed).
        if requested >= PRODUCTION_SESSION_DURATION_SECONDS and not (
            cfg.session_execution_authorized and operator_go_present
        ):
            abort_reason = AbortReason.PRODUCTION_DURATION_BLOCKED
            raise PreEconomicSessionRunnerError("PRODUCTION_DURATION_BLOCKED")
        if requested > cfg.maximum_test_runtime_seconds and dry_run:
            # Dry-run / implementation readiness must stay within test budget.
            if requested >= PRODUCTION_SESSION_DURATION_SECONDS:
                abort_reason = AbortReason.PRODUCTION_DURATION_BLOCKED
                raise PreEconomicSessionRunnerError("PRODUCTION_DURATION_BLOCKED")
            abort_reason = AbortReason.TIME_BUDGET_EXCEEDED
            raise PreEconomicSessionRunnerError("TIME_BUDGET_EXCEEDED")
        if not dry_run:
            abort_reason = AbortReason.SESSION_NOT_AUTHORIZED
            raise PreEconomicSessionRunnerError("NON_DRY_RUN_NOT_AUTHORIZED")
        if cfg.session_execution_authorized:
            abort_reason = AbortReason.SESSION_NOT_AUTHORIZED
            raise PreEconomicSessionRunnerError(
                "SESSION_EXECUTION_AUTHORIZED_BLOCKED_IN_CAPABILITY"
            )
        if cfg.operator_go_required and operator_go_present:
            # Operator GO for a real session is out of scope for this capability.
            # Presence alone must not unlock production execution here.
            pass
        if not allow_implementation_dry_run and not cfg.implementation_enabled:
            # Explicit dry-run allow flag required when implementation_enabled=false.
            # Tests and CLI pass allow_implementation_dry_run=True for offline proof.
            abort_reason = AbortReason.SESSION_NOT_AUTHORIZED
            raise PreEconomicSessionRunnerError("IMPLEMENTATION_DRY_RUN_NOT_ALLOWED")

        if order_attempt or not cfg.zero_order_enforced:
            orders_attempted = 1
            forbid_order_attempt("synthetic_order")

        ledger.transition(
            to_state=TelemetryState.READY,
            clock=clk,
            start_ts=start_ts,
            detail="ready",
        )
        ledger.transition(
            to_state=TelemetryState.RUNNING,
            clock=clk,
            start_ts=start_ts,
            detail="running",
        )

        expected_heartbeats = max(1, cycles)
        for cycle in range(expected_heartbeats):
            if signal_abort_flag["armed"]:
                abort_reason = AbortReason.SIGNAL_ABORT
                raise PreEconomicSessionRunnerError("SIGNAL_ABORT")
            if force_abort is not None:
                abort_reason = force_abort
                raise PreEconomicSessionRunnerError(force_abort.value)
            if inject_exception is not None:
                raise inject_exception
            if isinstance(clk, ControllableClock):
                clk.advance(float(cfg.heartbeat_interval_seconds))
            ledger.transition(
                to_state=TelemetryState.HEARTBEAT,
                clock=clk,
                start_ts=start_ts,
                detail=f"heartbeat:{cycle + 1}",
            )
            elapsed = float(clk.now()) - start_ts
            if elapsed > float(cfg.maximum_test_runtime_seconds) + 1e-9:
                abort_reason = AbortReason.TIME_BUDGET_EXCEEDED
                raise PreEconomicSessionRunnerError("TIME_BUDGET_EXCEEDED")

        if isinstance(clk, ControllableClock):
            clk.advance(0.0)
        ledger.transition(
            to_state=TelemetryState.COMPLETED,
            clock=clk,
            start_ts=start_ts,
            detail="completed_dry_run",
        )
        terminal_state = TelemetryState.COMPLETED
        completeness = "COMPLETE"
    except PreEconomicSessionRunnerError as exc:
        if abort_reason is AbortReason.NONE:
            msg = str(exc)
            if msg.startswith("ORDER_ATTEMPT"):
                abort_reason = AbortReason.ORDER_ATTEMPT_FORBIDDEN
            elif "CONFIG" in msg:
                abort_reason = AbortReason.CONFIG_MISMATCH
            elif "INTEGRITY" in msg or "READBACK" in msg:
                abort_reason = AbortReason.INTEGRITY_FAILURE
            elif "EVIDENCE_WRITE" in msg:
                abort_reason = AbortReason.EVIDENCE_WRITE_FAILURE
            elif "SIGNAL" in msg:
                abort_reason = AbortReason.SIGNAL_ABORT
            elif "PRODUCTION_DURATION" in msg:
                abort_reason = AbortReason.PRODUCTION_DURATION_BLOCKED
            elif "TIME_BUDGET" in msg:
                abort_reason = AbortReason.TIME_BUDGET_EXCEEDED
            elif "TELEMETRY" in msg or "STATE" in msg or "SEQUENCE" in msg:
                abort_reason = AbortReason.TELEMETRY_FAILURE
            elif "NOT_AUTHORIZED" in msg or "DRY_RUN" in msg:
                abort_reason = AbortReason.SESSION_NOT_AUTHORIZED
            else:
                abort_reason = AbortReason.UNEXPECTED_EXCEPTION
        terminal_state = _safe_abort(ledger, clk, start_ts, abort_reason, detail=str(exc))
        completeness = "ABORTED"
    except Exception as exc:  # noqa: BLE001 — fail-closed durable evidence
        abort_reason = AbortReason.UNEXPECTED_EXCEPTION
        terminal_state = _safe_abort(
            ledger,
            clk,
            start_ts,
            abort_reason,
            detail=type(exc).__name__,
        )
        completeness = "ABORTED"
    finally:
        if install_signal_handlers:
            for sig, handler in previous_handlers.items():
                signal.signal(sig, handler)

    end_ts = float(clk.now())
    elapsed = max(0.0, end_ts - start_ts)
    impl_digest = _implementation_digest(repo_root=root, head_sha=head_sha)
    expected_hb = (
        ledger.heartbeat_count
        if terminal_state == TelemetryState.COMPLETED
        else max(ledger.heartbeat_count, 0)
    )

    effective_config = redact_mapping(cfg.to_dict())
    identity = {
        "capability_id": CAPABILITY_ID,
        "session_contract_id": SESSION_CONTRACT_ID,
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "session_id": sid,
        "package_marker": PACKAGE_MARKER,
        "runtime_authority": RUNTIME_AUTHORITY_NONE,
        "head_sha": head_sha or "UNKNOWN",
        "implementation_digest": impl_digest,
    }

    lifecycle = ledger.to_dict()
    heartbeat_summary = {
        "session_id": sid,
        "heartbeat_count": ledger.heartbeat_count,
        "expected_heartbeat_count": expected_hb
        if terminal_state == TelemetryState.COMPLETED
        else expected_hb,
        "heartbeat_interval_seconds": cfg.heartbeat_interval_seconds,
        "stale_threshold_seconds": cfg.stale_threshold_seconds,
        "stale": False,
    }
    abort_summary = {
        "session_id": sid,
        "abort_reason": abort_reason.value,
        "aborted": terminal_state == TelemetryState.ABORTED
        or terminal_state == TelemetryState.INVALID,
        "terminal_state": terminal_state.value,
    }
    terminal_result = {
        "contract_version": CONTRACT_VERSION,
        "session_id": sid,
        "mode": "DRY_RUN_OFFLINE" if dry_run else "UNAUTHORIZED",
        "zero_order_enforced": True,
        "orders_attempted": orders_attempted,
        "orders_submitted": orders_submitted,
        "runtime_authority": RUNTIME_AUTHORITY_NONE,
        "operator_go_present": bool(operator_go_present),
        "start_timestamp": start_ts,
        "end_timestamp": end_ts,
        "elapsed_seconds": elapsed,
        "heartbeat_count": ledger.heartbeat_count,
        "expected_heartbeat_count": (
            ledger.heartbeat_count if terminal_state == TelemetryState.COMPLETED else None
        ),
        "abort_reason": abort_reason.value,
        "terminal_state": terminal_state.value,
        "completeness": completeness,
        "config_digest": cfg.config_digest,
        "implementation_digest": impl_digest,
        "evidence_root": str(evidence_root.relative_to(root))
        if evidence_root.is_relative_to(root)
        else str(evidence_root),
        "consumer_eligibility": False,
        "session_execution_authorized": False,
        "six_hour_session_executed": False,
        "economic_gate_effect": "NONE",
        "shadow_activation_eligible": False,
    }

    write_error: Optional[str] = None
    try:
        emitter.write_json("session_manifest.json", identity)
        emitter.write_json("effective_config_snapshot.json", effective_config)  # type: ignore[arg-type]
        emitter.write_json("lifecycle_events.json", lifecycle)
        emitter.write_json("heartbeat_summary.json", heartbeat_summary)
        emitter.write_json("abort_summary.json", abort_summary)
        emitter.write_json("terminal_result.json", terminal_result)
        hash_chain = {
            "session_id": sid,
            "algorithm": "sha256",
            "files": dict(sorted(emitter.digests.items())),
            "chain_seed": cfg.config_digest,
        }
        emitter.write_json("integrity_manifest.json", hash_chain)
        emitter.write_manifest()
        integrity_status = "PASS"
    except PreEconomicSessionRunnerError as exc:
        write_error = str(exc)
        integrity_status = "FAIL"
        if completeness == "COMPLETE":
            completeness = "INVALID"
            terminal_state = TelemetryState.INVALID
        abort_reason = AbortReason.EVIDENCE_WRITE_FAILURE

    implementation_readiness = (
        "IMPLEMENTATION_READINESS_PASS"
        if (
            terminal_state == TelemetryState.COMPLETED
            and completeness == "COMPLETE"
            and integrity_status == "PASS"
            and orders_attempted == 0
            and orders_submitted == 0
            and dry_run
            and not operator_go_present
        )
        else "IMPLEMENTATION_READINESS_BLOCKED"
    )
    session_evidence_status = "SESSION_NOT_AUTHORIZED"
    if completeness in {"ABORTED", "INVALID", "INCOMPLETE"}:
        if integrity_status == "FAIL":
            session_evidence_status = "SESSION_EVIDENCE_INVALID"
        elif completeness == "INCOMPLETE":
            session_evidence_status = "SESSION_EVIDENCE_INCOMPLETE"
        else:
            session_evidence_status = "SESSION_NOT_AUTHORIZED"

    notes = (
        "DRY_RUN_OFFLINE_ONLY",
        "SIX_HOUR_SESSION_EXECUTED=false",
        "SESSION_EXECUTION_AUTHORIZED=false",
        "ORDERS_ALLOWED=false",
        "ECONOMIC_GATE_EFFECT=NONE",
        "SHADOW_ACTIVATION_ELIGIBLE=false",
        "CONSUMER_ELIGIBILITY=false",
    )
    if write_error:
        notes = notes + (f"WRITE_ERROR:{write_error}",)

    result = SessionRunResultV1(
        capability_id=CAPABILITY_ID,
        session_id=sid,
        mode="DRY_RUN_OFFLINE" if dry_run else "UNAUTHORIZED",
        terminal_state=terminal_state.value,
        abort_reason=abort_reason.value,
        orders_attempted=orders_attempted,
        orders_submitted=orders_submitted,
        zero_order_enforced=True,
        runtime_authority=RUNTIME_AUTHORITY_NONE,
        operator_go_present=bool(operator_go_present),
        start_timestamp=start_ts,
        end_timestamp=end_ts,
        elapsed_seconds=elapsed,
        heartbeat_count=ledger.heartbeat_count,
        expected_heartbeat_count=int(
            ledger.heartbeat_count if terminal_state == TelemetryState.COMPLETED else 0
        ),
        completeness=completeness,
        integrity_status=integrity_status,
        config_digest=cfg.config_digest,
        implementation_digest=impl_digest,
        evidence_root=str(evidence_root.relative_to(root))
        if evidence_root.is_relative_to(root)
        else str(evidence_root),
        generated_files=tuple(sorted(emitter.digests.keys())),
        consumer_eligibility=False,
        implementation_readiness=implementation_readiness,
        session_evidence_status=session_evidence_status,
        economic_gate_effect="NONE",
        shadow_activation_eligible=False,
        notes=notes,
    )
    try:
        emitter.write_json("run_result.json", result.to_dict())
        emitter.write_manifest()
    except PreEconomicSessionRunnerError:
        # Already captured integrity failure; return durable best-effort result.
        pass
    return result


def _safe_abort(
    ledger: TelemetryLedgerV1,
    clock: Clock,
    start_ts: float,
    abort_reason: AbortReason,
    *,
    detail: str,
) -> TelemetryState:
    try:
        if ledger.current_state not in TERMINAL_STATES:
            if ledger.current_state != TelemetryState.ABORTING:
                # HOLD or ABORTING path depending on current state.
                if ledger.current_state in {
                    TelemetryState.RUNNING,
                    TelemetryState.HEARTBEAT,
                    TelemetryState.READY,
                    TelemetryState.INITIALIZING,
                }:
                    try:
                        ledger.transition(
                            to_state=TelemetryState.ABORTING,
                            clock=clock,
                            start_ts=start_ts,
                            detail=detail,
                            abort_reason=abort_reason,
                        )
                    except PreEconomicSessionRunnerError:
                        ledger.transition(
                            to_state=TelemetryState.HOLD,
                            clock=clock,
                            start_ts=start_ts,
                            detail=detail,
                            abort_reason=abort_reason,
                        )
                        ledger.transition(
                            to_state=TelemetryState.ABORTING,
                            clock=clock,
                            start_ts=start_ts,
                            detail=detail,
                            abort_reason=abort_reason,
                        )
                elif ledger.current_state == TelemetryState.HOLD:
                    ledger.transition(
                        to_state=TelemetryState.ABORTING,
                        clock=clock,
                        start_ts=start_ts,
                        detail=detail,
                        abort_reason=abort_reason,
                    )
            ledger.transition(
                to_state=TelemetryState.ABORTED,
                clock=clock,
                start_ts=start_ts,
                detail=detail,
                abort_reason=abort_reason,
            )
            return TelemetryState.ABORTED
    except PreEconomicSessionRunnerError:
        try:
            if not ledger.terminal_emitted:
                # Force INVALID terminal when transition graph cannot abort cleanly.
                now = float(clock.now())
                elapsed = max(0.0, now - float(start_ts))
                ledger.events.append(
                    TelemetryEventV1(
                        sequence=len(ledger.events) + 1,
                        state=TelemetryState.INVALID.value,
                        elapsed_seconds=elapsed,
                        timestamp=now,
                        detail=detail,
                        abort_reason=abort_reason.value,
                    )
                )
                ledger.current_state = TelemetryState.INVALID
                ledger.terminal_emitted = True
            return TelemetryState.INVALID
        except Exception:  # noqa: BLE001
            return TelemetryState.INVALID
    return ledger.current_state


def simulate_signal_abort(
    *,
    repo_root: Path,
    session_id: str = "signal_abort_test",
) -> SessionRunResultV1:
    """Test helper: abort mid-run via force_abort=SIGNAL_ABORT."""

    cfg = load_session_config_v1(repo_root=repo_root)
    return run_pre_economic_zero_order_evidence_session_v1(
        repo_root=repo_root,
        config=cfg,
        session_id=session_id,
        clock=ControllableClock(0.0),
        max_cycles=3,
        allow_implementation_dry_run=True,
        force_abort=AbortReason.SIGNAL_ABORT,
        evidence_subdir=session_id,
    )
