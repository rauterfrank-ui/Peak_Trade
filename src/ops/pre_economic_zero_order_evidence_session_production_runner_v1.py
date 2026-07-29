"""Production runner for Pre-Economic Zero-Order Evidence session authorization path v1.

Capability: PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION

Default state: blocked. Starts only with enabled∧armed∧authorized∧valid GO.
Never submits orders. Never grants Economic/Shadow/Paper/Testnet/Live authority.
Does not silently resume after process loss.
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import tempfile
import time
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Protocol

from src.ops.pre_economic_zero_order_decision_cycle_observer_v1 import (
    DecisionCycleObserverV1,
)
from src.ops.pre_economic_zero_order_economic_evidence_v1 import (
    EVIDENCE_FILE,
    SUMMARY_FILE,
    append_decision_jsonl,
    build_session_economic_summary_v1,
    load_decision_records,
    write_session_economic_summary,
)
from src.ops.pre_economic_zero_order_evidence_session_authorization_v1 import (
    CAPABILITY_ID,
    PRODUCTION_SESSION_DURATION_SECONDS,
    SESSION_CONTRACT_ID,
    AuthorizationContractError,
    AuthorizationContractV1,
    consume_authorization_one_time_v1,
    fingerprint_go_token,
    load_authorization_contract_v1,
    validate_operator_go_and_contract_v1,
)
from src.ops.pre_economic_zero_order_evidence_session_okx_readonly_telemetry_v1 import (
    OkxFuturesReadOnlyTelemetryV1,
    SimulatedOkxTelemetryClientV1,
    TelemetryError,
    TelemetrySummaryV1,
    build_default_okx_public_client,
)
from src.ops.pre_economic_zero_order_evidence_session_safety_preflight_v1 import (
    SafetyPreflightResultV1,
    run_safety_preflight_v1,
)
from src.ops.pre_economic_zero_order_evidence_session_state_machine_v1 import (
    SessionState,
    SessionStateMachineError,
    assert_transition_allowed,
)
from src.ops.pre_economic_zero_order_wallclock_arming_v1 import (
    TRUTH_CLAIM as WALLCLOCK_ARMING_TRUTH_CLAIM,
    WallclockArmingError,
    consume_wallclock_arming_one_time_v1,
    load_wallclock_arming_lease_v1,
    validate_wallclock_arming_against_go_v1,
)

PACKAGE_MARKER = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION=true"
PRODUCER_FAMILY = "ops.pre_economic_zero_order_evidence_session_production_runner_v1"
SCHEMA_VERSION = "v1"
EVIDENCE_SCHEMA_VERSION = "v1"
DEFAULT_CONFIG_RELPATH = "config/ops/pre_economic_zero_order_evidence_session_authorization_v1.toml"
DEFAULT_LOCK_NAME = "production_session.lock"
RUNTIME_AUTHORITY_NONE = "NONE"


class ProductionRunnerError(ValueError):
    """Fail-closed production runner error."""


class WallMonotonicClock(Protocol):
    def wall(self) -> float: ...

    def mono(self) -> float: ...


@dataclass
class SystemDualClock:
    def wall(self) -> float:
        return time.time()

    def mono(self) -> float:
        return time.monotonic()


@dataclass
class ControllableDualClock:
    """Test clock: wall and monotonic advanced independently."""

    _wall: float = 0.0
    _mono: float = 0.0

    def wall(self) -> float:
        return float(self._wall)

    def mono(self) -> float:
        return float(self._mono)

    def advance(self, seconds: float, *, wall: bool = True, mono: bool = True) -> None:
        if seconds < 0:
            raise ProductionRunnerError("CLOCK_NON_MONOTONE_ADVANCE")
        if wall:
            self._wall += float(seconds)
        if mono:
            self._mono += float(seconds)


@dataclass(frozen=True)
class ProductionConfigV1:
    schema_version: str
    capability_id: str
    session_contract_id: str
    implementation_enabled: bool
    session_execution_authorized: bool
    enabled: bool
    armed: bool
    dry_run: bool
    zero_order_only: bool
    orders_allowed: bool
    broker_writes_allowed: bool
    network_allowed_for_readonly_telemetry: bool
    venue: str
    market_type: str
    instrument_allowlist: tuple[str, ...]
    btc_forbidden: bool
    spot_forbidden: bool
    production_session_duration_seconds: int
    output_root: str
    authorization_contract_path: str
    authorization_consumption_store: str
    heartbeat_interval_seconds: float
    stale_threshold_seconds: float
    max_clock_skew_seconds: float
    max_clock_drift_seconds: float
    runtime_authority: str
    allow_unknown_config_fields: bool
    config_path: str
    config_digest: str
    # Test-only simulation budget; production path ignores unless explicitly allowed.
    maximum_test_runtime_seconds: int
    allow_test_duration_override: bool
    broker_write: bool = False
    live_authorized: bool = False
    paper_authorized: bool = False
    testnet_authorized: bool = False
    shadow_activation_authorized: bool = False
    wallclock_arming_required: bool = True
    wallclock_arming_lease_path: str = (
        "config/ops/pre_economic_zero_order_wallclock_arming_lease_template_v1.json"
    )
    wallclock_arming_consumption_store: str = (
        "out/ops/pre_economic_zero_order_evidence_session_authorization_v1/arming_consumption"
    )
    wallclock_arming_max_ttl_seconds: int = 900
    wallclock_execution_authorized: bool = False
    fee_bps: float = 2.0
    slippage_bps: float = 1.5

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["instrument_allowlist"] = list(self.instrument_allowlist)
        return payload


KNOWN_CONFIG_KEYS = frozenset(
    {
        "schema_version",
        "capability_id",
        "session_contract_id",
        "implementation_enabled",
        "session_execution_authorized",
        "enabled",
        "armed",
        "dry_run",
        "zero_order_only",
        "orders_allowed",
        "broker_writes_allowed",
        "broker_write",
        "live_authorized",
        "paper_authorized",
        "testnet_authorized",
        "shadow_activation_authorized",
        "network_allowed_for_readonly_telemetry",
        "venue",
        "market_type",
        "instrument_allowlist",
        "btc_forbidden",
        "spot_forbidden",
        "production_session_duration_seconds",
        "output_root",
        "authorization_contract_path",
        "authorization_consumption_store",
        "wallclock_arming_required",
        "wallclock_arming_lease_path",
        "wallclock_arming_consumption_store",
        "wallclock_arming_max_ttl_seconds",
        "wallclock_execution_authorized",
        "fee_bps",
        "slippage_bps",
        "heartbeat_interval_seconds",
        "stale_threshold_seconds",
        "max_clock_skew_seconds",
        "max_clock_drift_seconds",
        "runtime_authority",
        "allow_unknown_config_fields",
        "maximum_test_runtime_seconds",
        "allow_test_duration_override",
    }
)


def _canonical_json(payload: Mapping[str, Any] | list[Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def atomic_write_text(*, path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_symlink():
        raise ProductionRunnerError("SYMLINK_OUTPUT_FORBIDDEN")
    data = text.encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".tmp_{path.name}_", suffix=".partial")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise
    read_back = path.read_bytes()
    if hashlib.sha256(read_back).hexdigest() != digest:
        raise ProductionRunnerError("INTEGRITY_FAILURE:READBACK_MISMATCH")
    return digest


def resolve_repo_relative(*, repo_root: Path, relative: str) -> Path:
    raw = str(relative or "").strip()
    if not raw or raw.startswith("/") or ".." in raw.split("/") or "\\" in raw:
        raise ProductionRunnerError("OUTPUT_PATH_ESCAPE")
    dest = (repo_root / raw).resolve()
    try:
        dest.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ProductionRunnerError("OUTPUT_PATH_OUTSIDE_REPO") from exc
    return dest


def load_production_config_v1(
    *,
    repo_root: Path,
    config_path: Optional[Path] = None,
) -> ProductionConfigV1:
    path = config_path or (repo_root / DEFAULT_CONFIG_RELPATH)
    if not path.is_file():
        raise ProductionRunnerError("CONFIG_MISSING")
    raw_text = path.read_text(encoding="utf-8")
    try:
        raw = tomllib.loads(raw_text)
    except tomllib.TOMLDecodeError as exc:
        raise ProductionRunnerError(f"CONFIG_PARSE_ERROR:{exc}") from exc
    if not isinstance(raw, dict):
        raise ProductionRunnerError("CONFIG_NOT_TABLE")
    unknown = sorted(set(raw) - KNOWN_CONFIG_KEYS)
    allow_unknown = bool(raw.get("allow_unknown_config_fields", False))
    if unknown and not allow_unknown:
        raise ProductionRunnerError("UNKNOWN_CONFIG_FIELDS:" + ",".join(unknown))

    def _req(key: str) -> Any:
        if key not in raw:
            raise ProductionRunnerError(f"CONFIG_FIELD_MISSING:{key}")
        return raw[key]

    allowlist_raw = _req("instrument_allowlist")
    if not isinstance(allowlist_raw, list) or not allowlist_raw:
        raise ProductionRunnerError("INSTRUMENT_ALLOWLIST_EMPTY")
    cfg = ProductionConfigV1(
        schema_version=str(_req("schema_version")),
        capability_id=str(_req("capability_id")),
        session_contract_id=str(_req("session_contract_id")),
        implementation_enabled=bool(_req("implementation_enabled")),
        session_execution_authorized=bool(_req("session_execution_authorized")),
        enabled=bool(_req("enabled")),
        armed=bool(_req("armed")),
        dry_run=bool(_req("dry_run")),
        zero_order_only=bool(_req("zero_order_only")),
        orders_allowed=bool(_req("orders_allowed")),
        broker_writes_allowed=bool(_req("broker_writes_allowed")),
        network_allowed_for_readonly_telemetry=bool(_req("network_allowed_for_readonly_telemetry")),
        venue=str(_req("venue")).upper(),
        market_type=str(_req("market_type")).upper(),
        instrument_allowlist=tuple(str(x) for x in allowlist_raw),
        btc_forbidden=bool(_req("btc_forbidden")),
        spot_forbidden=bool(_req("spot_forbidden")),
        production_session_duration_seconds=int(_req("production_session_duration_seconds")),
        output_root=str(_req("output_root")),
        authorization_contract_path=str(_req("authorization_contract_path")),
        authorization_consumption_store=str(_req("authorization_consumption_store")),
        heartbeat_interval_seconds=float(_req("heartbeat_interval_seconds")),
        stale_threshold_seconds=float(_req("stale_threshold_seconds")),
        max_clock_skew_seconds=float(_req("max_clock_skew_seconds")),
        max_clock_drift_seconds=float(_req("max_clock_drift_seconds")),
        runtime_authority=str(_req("runtime_authority")),
        allow_unknown_config_fields=allow_unknown,
        config_path=str(path.relative_to(repo_root))
        if path.is_relative_to(repo_root)
        else str(path),
        config_digest=_sha256_text(raw_text),
        maximum_test_runtime_seconds=int(_req("maximum_test_runtime_seconds")),
        allow_test_duration_override=bool(_req("allow_test_duration_override")),
        broker_write=bool(raw.get("broker_write", False)),
        live_authorized=bool(raw.get("live_authorized", False)),
        paper_authorized=bool(raw.get("paper_authorized", False)),
        testnet_authorized=bool(raw.get("testnet_authorized", False)),
        shadow_activation_authorized=bool(raw.get("shadow_activation_authorized", False)),
        wallclock_arming_required=bool(raw.get("wallclock_arming_required", True)),
        wallclock_arming_lease_path=str(
            raw.get(
                "wallclock_arming_lease_path",
                "config/ops/pre_economic_zero_order_wallclock_arming_lease_template_v1.json",
            )
        ),
        wallclock_arming_consumption_store=str(
            raw.get(
                "wallclock_arming_consumption_store",
                "out/ops/pre_economic_zero_order_evidence_session_authorization_v1/arming_consumption",
            )
        ),
        wallclock_arming_max_ttl_seconds=int(raw.get("wallclock_arming_max_ttl_seconds", 900)),
        wallclock_execution_authorized=bool(raw.get("wallclock_execution_authorized", False)),
        fee_bps=float(raw.get("fee_bps", 2.0)),
        slippage_bps=float(raw.get("slippage_bps", 1.5)),
    )
    _validate_production_config(cfg)
    return cfg


def _validate_production_config(cfg: ProductionConfigV1) -> None:
    if cfg.schema_version != SCHEMA_VERSION:
        raise ProductionRunnerError("CONFIG_SCHEMA_VERSION_MISMATCH")
    if cfg.capability_id != CAPABILITY_ID:
        raise ProductionRunnerError("CONFIG_CAPABILITY_MISMATCH")
    if cfg.session_contract_id != SESSION_CONTRACT_ID:
        raise ProductionRunnerError("CONFIG_SESSION_CONTRACT_MISMATCH")
    if cfg.runtime_authority != RUNTIME_AUTHORITY_NONE:
        raise ProductionRunnerError("CONFIG_RUNTIME_AUTHORITY_MUST_BE_NONE")
    if cfg.orders_allowed is not False:
        raise ProductionRunnerError("CONFIG_ORDERS_MUST_BE_FALSE")
    if cfg.broker_writes_allowed is not False or cfg.broker_write is not False:
        raise ProductionRunnerError("CONFIG_BROKER_WRITES_MUST_BE_FALSE")
    if not cfg.zero_order_only:
        raise ProductionRunnerError("CONFIG_ZERO_ORDER_MUST_BE_TRUE")
    if not cfg.btc_forbidden or not cfg.spot_forbidden:
        raise ProductionRunnerError("CONFIG_BTC_OR_SPOT_FORBIDDEN_REQUIRED")
    if cfg.venue != "OKX":
        raise ProductionRunnerError("CONFIG_VENUE_MUST_BE_OKX")
    if cfg.market_type not in {"SWAP", "FUTURES"}:
        raise ProductionRunnerError("CONFIG_MARKET_TYPE_INVALID")
    if cfg.production_session_duration_seconds != PRODUCTION_SESSION_DURATION_SECONDS:
        raise ProductionRunnerError("CONFIG_PRODUCTION_DURATION_MISMATCH")
    if cfg.live_authorized or cfg.paper_authorized or cfg.testnet_authorized:
        raise ProductionRunnerError("CONFIG_LIVE_PAPER_TESTNET_MUST_BE_FALSE")
    if cfg.shadow_activation_authorized:
        raise ProductionRunnerError("CONFIG_SHADOW_MUST_BE_FALSE")
    if cfg.wallclock_arming_max_ttl_seconds <= 0 or cfg.wallclock_arming_max_ttl_seconds > 900:
        raise ProductionRunnerError("CONFIG_WALLCLOCK_ARMING_TTL_INVALID")
    if cfg.fee_bps < 0 or cfg.slippage_bps < 0:
        raise ProductionRunnerError("CONFIG_FEE_OR_SLIPPAGE_NEGATIVE")
    # Canonical defaults remain blocked.
    if cfg.enabled and cfg.armed and cfg.session_execution_authorized and not cfg.dry_run:
        # Allowed only when external authorization + GO + wallclock arming are also valid
        # at runtime; config alone still does not start a session.
        pass


@dataclass
class ProductionRunResultV1:
    capability_id: str
    session_id: str
    mode: str
    state: str
    abort_reason: str
    orders_attempted: int
    orders_submitted: int
    zero_order_only: bool
    runtime_authority: str
    authorization_id: str
    go_token_fingerprint: str
    config_digest: str
    revision_sha: str
    venue: str
    market_type: str
    instrument_id: str
    start_wall: float
    end_wall: float
    start_mono: float
    end_mono: float
    wall_elapsed_seconds: float
    mono_elapsed_seconds: float
    completeness: str
    integrity_status: str
    evidence_root: str
    generated_files: tuple[str, ...]
    consumer_eligibility: bool
    session_evidence_status: str
    session_evidence_valid: bool
    economic_gate_effect: str
    shadow_activation_eligible: bool
    safety_preflight: dict[str, Any]
    telemetry_summary: dict[str, Any]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceEmitterV1:
    evidence_root: Path
    digests: dict[str, str] = field(default_factory=dict)

    def write_json(self, relative_name: str, payload: Mapping[str, Any] | list[Any]) -> str:
        safe = relative_name.replace("\\", "/")
        if ".." in safe or safe.startswith("/"):
            raise ProductionRunnerError("EVIDENCE_PATH_ESCAPE")
        path = self.evidence_root / safe
        digest = atomic_write_text(path=path, text=_canonical_json(payload))  # type: ignore[arg-type]
        self.digests[safe] = digest
        return digest

    def write_manifest(self) -> str:
        lines = [f"{digest}  {name}" for name, digest in sorted(self.digests.items())]
        text = "\n".join(lines) + ("\n" if lines else "")
        path = self.evidence_root / "evidence_manifest.sha256"
        digest = atomic_write_text(path=path, text=text)
        self.digests["evidence_manifest.sha256"] = digest
        return digest


def _acquire_session_lock(lock_path: Path) -> None:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.exists():
        raise ProductionRunnerError("PARALLEL_SESSION_LOCK_HELD")
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError as exc:
        raise ProductionRunnerError("PARALLEL_SESSION_LOCK_HELD") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(_canonical_json({"pid": os.getpid(), "created_at": time.time()}))


def _release_session_lock(lock_path: Path) -> None:
    try:
        if lock_path.exists():
            lock_path.unlink()
    except OSError:
        pass


def forbid_order_attempt(action: str = "order") -> None:
    raise ProductionRunnerError(f"ORDER_ATTEMPT_FORBIDDEN:{action}")


def validate_config_only_v1(
    *, repo_root: Path, config_path: Optional[Path] = None
) -> dict[str, Any]:
    cfg = load_production_config_v1(repo_root=repo_root, config_path=config_path)
    return {
        "ok": True,
        "config_digest": cfg.config_digest,
        "enabled": cfg.enabled,
        "armed": cfg.armed,
        "session_execution_authorized": cfg.session_execution_authorized,
        "dry_run": cfg.dry_run,
        "orders_allowed": cfg.orders_allowed,
        "runtime_authority": cfg.runtime_authority,
        "notes": [
            "CONFIG_VALID",
            "DEFAULT_PRODUCTION_START_REMAINS_BLOCKED_WITHOUT_AUTH_AND_GO",
        ],
    }


def preflight_production_session_v1(
    *,
    repo_root: Path,
    config: Optional[ProductionConfigV1] = None,
    authorization_path: Optional[Path] = None,
    go_token: Optional[str] = None,
    revision_sha: str = "UNKNOWN",
    client: Any = None,
    now: Optional[float] = None,
    arming_lease_path: Optional[Path] = None,
) -> dict[str, Any]:
    cfg = config or load_production_config_v1(repo_root=repo_root)
    blockers: list[str] = []
    auth_path = authorization_path or resolve_repo_relative(
        repo_root=repo_root, relative=cfg.authorization_contract_path
    )
    contract: Optional[AuthorizationContractV1] = None
    auth_result = None
    arming_result = None
    try:
        contract = load_authorization_contract_v1(
            auth_path,
            expected_config_digest=cfg.config_digest,
            expected_revision_sha=revision_sha if revision_sha != "UNKNOWN" else None,
        )
    except AuthorizationContractError as exc:
        blockers.append(str(exc))

    consumption_store = resolve_repo_relative(
        repo_root=repo_root, relative=cfg.authorization_consumption_store
    )
    if contract is not None:
        auth_result = validate_operator_go_and_contract_v1(
            contract=contract,
            go_token=go_token,
            now=now,
            expected_config_digest=cfg.config_digest,
            expected_revision_sha=revision_sha if revision_sha != "UNKNOWN" else None,
            consumption_store=consumption_store,
        )
        blockers.extend(auth_result.blockers)

    # Stage 2: wallclock arming lease (required for production wallclock path).
    if cfg.wallclock_arming_required:
        lease_path = arming_lease_path or resolve_repo_relative(
            repo_root=repo_root, relative=cfg.wallclock_arming_lease_path
        )
        arming_store = resolve_repo_relative(
            repo_root=repo_root, relative=cfg.wallclock_arming_consumption_store
        )
        try:
            lease = load_wallclock_arming_lease_v1(lease_path)
            if contract is None:
                blockers.append("WALLCLOCK_ARMING_REQUIRES_VALID_GO_CONTRACT")
            else:
                arming_result = validate_wallclock_arming_against_go_v1(
                    lease=lease,
                    contract=contract,
                    go_token=go_token,
                    now=now,
                    expected_config_digest=cfg.config_digest,
                    expected_revision_sha=revision_sha if revision_sha != "UNKNOWN" else None,
                    consumption_store=arming_store,
                    require_production_flags=True,
                )
                blockers.extend(arming_result.blockers)
        except WallclockArmingError as exc:
            blockers.append(str(exc))

    use_client = client
    if use_client is None:
        if cfg.network_allowed_for_readonly_telemetry and not cfg.dry_run:
            use_client = build_default_okx_public_client()
        else:
            use_client = SimulatedOkxTelemetryClientV1()
    safety = run_safety_preflight_v1(client=use_client)
    if not safety.ok:
        blockers.extend(safety.blockers)

    # Config flags alone are insufficient.
    if not (cfg.enabled and cfg.armed and cfg.session_execution_authorized and not cfg.dry_run):
        blockers.append("CONFIG_PRODUCTION_FLAGS_NOT_SATISFIED")
    if go_token is None or not str(go_token).strip():
        if "OPERATOR_GO_TOKEN_ABSENT" not in blockers:
            blockers.append("OPERATOR_GO_TOKEN_ABSENT")

    return {
        "ok": not blockers,
        "blockers": blockers,
        "config_digest": cfg.config_digest,
        "authorization": None if auth_result is None else auth_result.to_dict(),
        "wallclock_arming": None if arming_result is None else arming_result.to_dict(),
        "safety_preflight": safety.to_dict(),
        "session_execution_authorized": False,
        "operator_go_granted": False,
        "production_start_allowed": False if blockers else True,
        "notes": [
            "PREFLIGHT_DOES_NOT_START_SESSION",
            "TWO_STAGE_AUTHORITY_REQUIRED",
            "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false",
            "SHADOW_ACTIVATION_AUTHORIZED=false",
            f"TRUTH_CLAIM={WALLCLOCK_ARMING_TRUTH_CLAIM}",
        ],
    }


def run_production_session_v1(
    *,
    repo_root: Path,
    config: Optional[ProductionConfigV1] = None,
    session_id: Optional[str] = None,
    authorization_path: Optional[Path] = None,
    go_token: Optional[str] = None,
    revision_sha: str = "UNKNOWN",
    clock: Optional[WallMonotonicClock] = None,
    client: Any = None,
    max_cycles: Optional[int] = None,
    target_duration_seconds: Optional[int] = None,
    force_abort: Optional[str] = None,
    inject_exception: Optional[BaseException] = None,
    allow_test_simulation: bool = False,
    evidence_subdir: Optional[str] = None,
    install_signal_handlers: bool = False,
    resume_requested: bool = False,
    merge_partial_runs: Optional[list[Path]] = None,
    arming_lease_path: Optional[Path] = None,
    allow_wallclock_sleep: bool = False,
) -> ProductionRunResultV1:
    """Run production observation path or fail closed.

    Real 6h wallclock sleep requires two-stage authority (GO + arming lease) and
    ``allow_wallclock_sleep=True``. Unit tests use a controllable clock with
    ``allow_test_simulation=True``.
    """

    root = repo_root.resolve()
    cfg = config or load_production_config_v1(repo_root=root)
    clk: WallMonotonicClock = clock or SystemDualClock()
    sid = session_id or f"pez_prod_{_sha256_text(str(clk.wall()))[:16]}"

    if resume_requested:
        raise ProductionRunnerError("RESUME_REQUIRES_NEW_AUTHORIZATION")
    if merge_partial_runs:
        raise ProductionRunnerError("PARTIAL_RUN_MERGE_FORBIDDEN")

    output_root = resolve_repo_relative(repo_root=root, relative=cfg.output_root)
    evidence_root = output_root / (evidence_subdir or sid)
    if evidence_root.exists() and any(evidence_root.iterdir()):
        raise ProductionRunnerError("EVIDENCE_DIR_NONEMPTY")
    evidence_root.mkdir(parents=True, exist_ok=True)
    lock_path = output_root / DEFAULT_LOCK_NAME
    _acquire_session_lock(lock_path)

    emitter = EvidenceEmitterV1(evidence_root=evidence_root)
    state = SessionState.CREATED
    abort_reason = "NONE"
    completeness = "INCOMPLETE"
    integrity_status = "UNKNOWN"
    orders_attempted = 0
    orders_submitted = 0
    auth_id = ""
    go_fp = ""
    arming_id = ""
    instrument_id = cfg.instrument_allowlist[0]
    safety_payload: dict[str, Any] = {}
    telemetry_payload: dict[str, Any] = {}
    economic_summary_payload: dict[str, Any] = {}
    observer: Optional[DecisionCycleObserverV1] = None
    start_wall = float(clk.wall())
    start_mono = float(clk.mono())
    end_wall = start_wall
    end_mono = start_mono
    mode = "PRODUCTION" if not cfg.dry_run else "DRY_RUN_BLOCKED"
    signal_abort = {"armed": False}
    cycles_completed = 0

    def _handle_signal(_signum: int, _frame: Any) -> None:
        signal_abort["armed"] = True

    previous_handlers: dict[int, Any] = {}
    if install_signal_handlers:
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[sig] = signal.signal(sig, _handle_signal)

    lifecycle: list[dict[str, Any]] = []

    def _transition(to_state: SessionState, detail: str = "") -> None:
        nonlocal state
        assert_transition_allowed(from_state=state, to_state=to_state)
        state = to_state
        lifecycle.append(
            {
                "state": state.value,
                "wall": float(clk.wall()),
                "mono": float(clk.mono()),
                "detail": detail,
            }
        )

    try:
        duration = int(
            cfg.production_session_duration_seconds
            if target_duration_seconds is None
            else target_duration_seconds
        )
        if duration != PRODUCTION_SESSION_DURATION_SECONDS:
            if not (
                allow_test_simulation
                and cfg.allow_test_duration_override
                and duration <= cfg.maximum_test_runtime_seconds
            ):
                abort_reason = "DURATION_NOT_21600"
                raise ProductionRunnerError("DURATION_NOT_21600")

        # Preflight authorization + safety.
        use_client = client
        if use_client is None:
            if allow_test_simulation:
                use_client = SimulatedOkxTelemetryClientV1()
            elif cfg.network_allowed_for_readonly_telemetry and not cfg.dry_run:
                use_client = build_default_okx_public_client()
            else:
                use_client = SimulatedOkxTelemetryClientV1()

        pre = preflight_production_session_v1(
            repo_root=root,
            config=cfg,
            authorization_path=authorization_path,
            go_token=go_token,
            revision_sha=revision_sha,
            client=use_client,
            now=float(clk.wall()),
            arming_lease_path=arming_lease_path,
        )
        safety_payload = pre.get("safety_preflight") or {}
        if not pre.get("ok"):
            abort_reason = "PREFLIGHT_BLOCKED"
            raise ProductionRunnerError("PREFLIGHT_BLOCKED:" + ",".join(pre.get("blockers") or []))

        auth_payload = pre.get("authorization") or {}
        contract_dict = auth_payload.get("contract") or {}
        auth_id = str(contract_dict.get("authorization_id") or "")
        go_fp = str(
            auth_payload.get("go_token_fingerprint") or fingerprint_go_token(go_token or "")
        )
        instrument_id = str((contract_dict.get("instrument_allowlist") or [instrument_id])[0])
        arming_payload = pre.get("wallclock_arming") or {}
        arming_lease_dict = arming_payload.get("lease") or {}
        arming_id = str(arming_lease_dict.get("arming_id") or "")

        _transition(SessionState.AUTHORIZED, "auth_ok")
        # Consume one-time authorization atomically before RUNNING.
        consume_store = resolve_repo_relative(
            repo_root=root, relative=cfg.authorization_consumption_store
        )
        auth_path = authorization_path or resolve_repo_relative(
            repo_root=root, relative=cfg.authorization_contract_path
        )
        contract = load_authorization_contract_v1(auth_path)
        consume_authorization_one_time_v1(
            store=consume_store,
            contract=contract,
            go_token_fingerprint=go_fp,
            revision_sha=revision_sha,
            now=float(clk.wall()),
        )
        if cfg.wallclock_arming_required:
            lease_path = arming_lease_path or resolve_repo_relative(
                repo_root=root, relative=cfg.wallclock_arming_lease_path
            )
            arming_store = resolve_repo_relative(
                repo_root=root, relative=cfg.wallclock_arming_consumption_store
            )
            lease = load_wallclock_arming_lease_v1(lease_path)
            consume_wallclock_arming_one_time_v1(
                store=arming_store,
                lease=lease,
                now=float(clk.wall()),
            )
            arming_id = lease.arming_id

        _transition(SessionState.STARTING, "starting")
        telemetry = OkxFuturesReadOnlyTelemetryV1(
            instrument_id=instrument_id,
            market_type=cfg.market_type,
            venue=cfg.venue,
            allowlist=cfg.instrument_allowlist,
            stale_threshold_seconds=cfg.stale_threshold_seconds,
            client=use_client,
            clock=clk.wall,
            monotonic=clk.mono,
        )
        observer = DecisionCycleObserverV1(
            instrument=instrument_id,
            fee_bps=cfg.fee_bps,
            slippage_bps=cfg.slippage_bps,
            switch_stale_after_seconds=cfg.stale_threshold_seconds,
        )
        decisions_path = evidence_root / EVIDENCE_FILE
        _transition(SessionState.RUNNING, "running")

        cycles = int(max_cycles if max_cycles is not None else max(1, duration))
        step = float(duration) / float(cycles)
        for cycle_idx in range(cycles):
            if signal_abort["armed"]:
                abort_reason = "SIGNAL_ABORT"
                raise ProductionRunnerError("SIGNAL_ABORT")
            if force_abort:
                abort_reason = force_abort
                raise ProductionRunnerError(force_abort)
            if inject_exception is not None:
                raise inject_exception
            snap = telemetry.poll_once()
            if snap.stale and snap.connection_status != "CONNECTED":
                abort_reason = "TELEMETRY_STALE"
                raise ProductionRunnerError("TELEMETRY_STALE")
            snap_dict = snap.to_dict()
            mid = 100.0 + (0.15 * float(cycle_idx)) if allow_test_simulation else None
            decision = observer.observe(
                timestamp=float(clk.wall()),
                cycle_index=cycle_idx,
                snapshot=snap_dict,
                mid_price=mid,
            )
            append_decision_jsonl(path=decisions_path, record=decision)
            cycles_completed += 1
            if isinstance(clk, ControllableDualClock):
                clk.advance(step)
            elif allow_test_simulation:
                pass
            elif allow_wallclock_sleep and not cfg.dry_run:
                remaining = max(0.0, float(duration) - (float(clk.mono()) - start_mono))
                time.sleep(min(step, remaining))
            else:
                abort_reason = "WALLCLOCK_ARMING_SLEEP_NOT_ENABLED"
                raise ProductionRunnerError("WALLCLOCK_ARMING_SLEEP_NOT_ENABLED")

        telemetry_summary = telemetry.summary()
        telemetry_payload = telemetry_summary.to_dict()
        if telemetry_summary.unresolved_integrity_violation:
            abort_reason = "TELEMETRY_INTEGRITY_VIOLATION"
            raise ProductionRunnerError("TELEMETRY_INTEGRITY_VIOLATION")

        end_wall = float(clk.wall())
        end_mono = float(clk.mono())
        mono_elapsed = end_mono - start_mono
        if mono_elapsed + 1e-9 < float(duration):
            abort_reason = "DURATION_INCOMPLETE"
            raise ProductionRunnerError("DURATION_INCOMPLETE")
        wall_elapsed = end_wall - start_wall
        if abs(wall_elapsed - mono_elapsed) > float(cfg.max_clock_drift_seconds):
            abort_reason = "CLOCK_ANOMALY"
            raise ProductionRunnerError("CLOCK_ANOMALY")

        _transition(SessionState.COMPLETED, "completed")
        completeness = "COMPLETE"
        mode = "PRODUCTION_SIMULATED" if allow_test_simulation else "PRODUCTION"
    except (
        ProductionRunnerError,
        AuthorizationContractError,
        WallclockArmingError,
        TelemetryError,
        SessionStateMachineError,
    ) as exc:
        end_wall = float(clk.wall())
        end_mono = float(clk.mono())
        if abort_reason == "NONE":
            abort_reason = str(exc).split(":", 1)[0]
        if state in {SessionState.RUNNING, SessionState.STARTING, SessionState.AUTHORIZED}:
            try:
                if force_abort == "PROCESS_LOSS" or abort_reason in {
                    "SIGNAL_ABORT",
                    "PROCESS_LOSS",
                }:
                    _transition(SessionState.INCOMPLETE, str(exc))
                    completeness = "INCOMPLETE"
                elif "REVOKED" in str(exc) or abort_reason.startswith("AUTHORIZATION_REVOKED"):
                    _transition(SessionState.REVOKED, str(exc))
                    completeness = "INVALID"
                elif "EXPIRED" in str(exc):
                    _transition(SessionState.EXPIRED, str(exc))
                    completeness = "INVALID"
                else:
                    _transition(SessionState.ABORTED, str(exc))
                    completeness = "ABORTED"
            except SessionStateMachineError:
                state = SessionState.INVALID
                completeness = "INVALID"
        elif state == SessionState.CREATED:
            state = SessionState.INVALID
            completeness = "INVALID"
        else:
            completeness = "INVALID" if completeness == "INCOMPLETE" else completeness
    except Exception as exc:  # noqa: BLE001
        end_wall = float(clk.wall())
        end_mono = float(clk.mono())
        abort_reason = "UNEXPECTED_EXCEPTION"
        try:
            if state not in {
                SessionState.COMPLETED,
                SessionState.ABORTED,
                SessionState.INCOMPLETE,
                SessionState.INVALID,
                SessionState.REVOKED,
                SessionState.EXPIRED,
            }:
                _transition(SessionState.INVALID, str(exc))
        except SessionStateMachineError:
            state = SessionState.INVALID
        completeness = "INVALID"
    finally:
        for sig, prev in previous_handlers.items():
            signal.signal(sig, prev)
        _release_session_lock(lock_path)

    wall_elapsed = max(0.0, end_wall - start_wall)
    mono_elapsed = max(0.0, end_mono - start_mono)

    try:
        records = load_decision_records(evidence_root / EVIDENCE_FILE)
        data_gaps = int((telemetry_payload or {}).get("data_gap_events") or 0)
        switch_transitions = (
            int(observer.state.state_switch_transitions) if observer is not None else 0
        )
        switch_stale = int(observer.state.switch_stale_count) if observer is not None else 0
        kill_interventions = (
            int(observer.state.killstate_interventions) if observer is not None else 0
        )
        summary = build_session_economic_summary_v1(
            records=records,
            runtime_duration_seconds=mono_elapsed,
            cycles=cycles_completed,
            data_gaps=data_gaps,
            state_switch_transitions=switch_transitions,
            switch_stale_count=switch_stale,
            killstate_interventions=kill_interventions,
            verifier_result="PENDING",
        )
        write_session_economic_summary(path=evidence_root / SUMMARY_FILE, summary=summary)
        economic_summary_payload = summary.to_dict()
    except Exception:
        economic_summary_payload = {}

    identity = {
        "capability_id": CAPABILITY_ID,
        "session_contract_id": SESSION_CONTRACT_ID,
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        "session_id": sid,
        "mode": mode,
        "authorization_id": auth_id,
        "arming_id": arming_id,
        "go_token_fingerprint": go_fp,
        "config_digest": cfg.config_digest,
        "revision_sha": revision_sha,
        "runner_version": PRODUCER_FAMILY,
        "verifier_version": "ops.pre_economic_zero_order_evidence_session_production_verifier_v1",
        "venue": cfg.venue,
        "market_type": cfg.market_type,
        "instrument_id": instrument_id,
        "runtime_authority": RUNTIME_AUTHORITY_NONE,
        "synthetic": bool(allow_test_simulation),
        "replayed": False,
        "truth_claim": WALLCLOCK_ARMING_TRUTH_CLAIM,
    }
    terminal = {
        **identity,
        "state": state.value,
        "abort_reason": abort_reason,
        "orders_attempted": orders_attempted,
        "orders_submitted": orders_submitted,
        "zero_order_only": True,
        "start_wall": start_wall,
        "end_wall": end_wall,
        "start_mono": start_mono,
        "end_mono": end_mono,
        "wall_elapsed_seconds": wall_elapsed,
        "mono_elapsed_seconds": mono_elapsed,
        "completeness": completeness,
        "consumer_eligibility": False,
        "session_execution_authorized": False,
        "session_evidence_valid": False,
        "economic_gate_effect": "NONE",
        "shadow_activation_eligible": False,
        "atomic_closeout": True,
        "cycles_completed": cycles_completed,
    }

    try:
        emitter.write_json("session_manifest.json", identity)
        emitter.write_json("effective_config_snapshot.json", cfg.to_dict())
        emitter.write_json("lifecycle_events.json", {"events": lifecycle, "state": state.value})
        emitter.write_json(
            "authorization_binding.json",
            {
                "authorization_id": auth_id,
                "arming_id": arming_id,
                "go_token_fingerprint": go_fp,
                "config_digest": cfg.config_digest,
                "revision_sha": revision_sha,
                "truth_claim": WALLCLOCK_ARMING_TRUTH_CLAIM,
            },
        )
        emitter.write_json("safety_preflight.json", safety_payload)
        emitter.write_json("telemetry_summary.json", telemetry_payload)
        if economic_summary_payload:
            emitter.write_json(SUMMARY_FILE, economic_summary_payload)
        if (evidence_root / EVIDENCE_FILE).is_file():
            emitter.digests[EVIDENCE_FILE] = _sha256_text(
                (evidence_root / EVIDENCE_FILE).read_text(encoding="utf-8")
            )
        emitter.write_json("terminal_result.json", terminal)
        emitter.write_json(
            "integrity_manifest.json",
            {
                "session_id": sid,
                "algorithm": "sha256",
                "files": dict(sorted(emitter.digests.items())),
                "chain_seed": cfg.config_digest,
            },
        )
        emitter.write_manifest()
        integrity_status = "PASS"
        # Mark closeout complete.
        emitter.write_json(
            "closeout.json",
            {
                "atomic_closeout": True,
                "state": state.value,
                "completeness": completeness,
                "session_evidence_valid": False,
            },
        )
        emitter.write_manifest()
    except Exception as exc:  # noqa: BLE001
        integrity_status = "FAIL"
        completeness = "INVALID"
        abort_reason = f"EVIDENCE_WRITE_FAILURE:{exc}"
        state = SessionState.INVALID

    session_evidence_status = "SESSION_NOT_AUTHORIZED"
    if completeness in {"ABORTED", "INVALID", "INCOMPLETE"}:
        session_evidence_status = (
            "SESSION_EVIDENCE_INVALID"
            if integrity_status == "FAIL" or completeness == "INVALID"
            else "SESSION_EVIDENCE_INCOMPLETE"
        )
    elif completeness == "COMPLETE":
        # Production runner never self-attests VALID; verifier owns that.
        session_evidence_status = "SESSION_EVIDENCE_PENDING_VERIFIER"

    notes = (
        WALLCLOCK_ARMING_TRUTH_CLAIM,
        "PRODUCTION_SESSION_EXECUTED=false",
        "SESSION_EVIDENCE_VALID=false",
        "OPERATOR_GO_GRANTED=false",
        "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false",
        "SHADOW_ACTIVATION_AUTHORIZED=false",
        "ORDERS=false",
        "DOWNSTREAM_AUTHORITY_GRANTED=false",
    )
    result = ProductionRunResultV1(
        capability_id=CAPABILITY_ID,
        session_id=sid,
        mode=mode,
        state=state.value,
        abort_reason=abort_reason,
        orders_attempted=orders_attempted,
        orders_submitted=orders_submitted,
        zero_order_only=True,
        runtime_authority=RUNTIME_AUTHORITY_NONE,
        authorization_id=auth_id,
        go_token_fingerprint=go_fp,
        config_digest=cfg.config_digest,
        revision_sha=revision_sha,
        venue=cfg.venue,
        market_type=cfg.market_type,
        instrument_id=instrument_id,
        start_wall=start_wall,
        end_wall=end_wall,
        start_mono=start_mono,
        end_mono=end_mono,
        wall_elapsed_seconds=wall_elapsed,
        mono_elapsed_seconds=mono_elapsed,
        completeness=completeness,
        integrity_status=integrity_status,
        evidence_root=str(evidence_root.relative_to(root))
        if evidence_root.is_relative_to(root)
        else str(evidence_root),
        generated_files=tuple(sorted(emitter.digests.keys())),
        consumer_eligibility=False,
        session_evidence_status=session_evidence_status,
        session_evidence_valid=False,
        economic_gate_effect="NONE",
        shadow_activation_eligible=False,
        safety_preflight=safety_payload,
        telemetry_summary=telemetry_payload,
        notes=notes,
    )
    try:
        emitter.write_json("run_result.json", result.to_dict())
        emitter.write_manifest()
    except Exception:
        pass
    return result
