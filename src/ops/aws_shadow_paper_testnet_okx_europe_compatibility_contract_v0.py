"""AWS Shadow/Paper/Testnet OKX-Europe offline compatibility contract (v0).

Pure offline evaluation that OKX-Europe venue bindings remain structurally integratable
into existing AWS Shadow/Paper/Testnet runtime paths without local special architecture.

``AWS_RUNTIME_COMPATIBLE=true`` means offline structural integrability only — not
network, egress, DNS, TLS, secrets injection, deployment, or runtime GO readiness.

No network I/O, no AWS calls, no credentials, no runtime execution, and no deployment
authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from src.ops.bounded_futures_testnet_venue_binding_v0 import (
    API_HOST_OKX_EEA,
    DEMO_REFERENCE_INSTRUMENT_ID,
    PRODUCTION_INSTRUMENT_ID,
)

PACKAGE_MARKER = "AWS_SHADOW_PAPER_TESTNET_OKX_EUROPE_COMPATIBILITY_CONTRACT_V0=true"
SCHEMA_VERSION = "aws_shadow_paper_testnet_okx_europe_compatibility_result.v0"
AUTHORITY_IMPACT = "NO_AUTHORITY_CHANGE"

REQUIRED_REST_HOST = API_HOST_OKX_EEA
REQUIRED_DEMO_PUBLIC_WS_HOST = "wss://wseeapap.okx.com:8443/ws/v5/public"
REQUIRED_WEBSOCKET_PORT = 8443
DEFAULT_PRIVATE_WS_HOST = "wss://wseeapap.okx.com:8443/ws/v5/private"

SIMULATION_HEADER_NAME = "x-simulated-trading"
SIMULATION_HEADER_VALUE = "1"

AUTOMATIC_INSTRUMENT_SUBSTITUTION_ALLOWED = False

ALLOWED_RUNTIME_ENVIRONMENTS = frozenset({"shadow", "paper", "testnet"})
REQUIRED_CREDENTIAL_SLOT_IDS = frozenset({"public", "readonly_private", "trade"})

FORBIDDEN_PRODUCTION_HOSTS = frozenset(
    {
        "www.okx.com",
        "okx.com",
        "aws.okx.com",
    }
)
FORBIDDEN_PRODUCTION_HOST_MARKERS = frozenset(
    {
        "live",
        "prod",
        "production",
        "mainnet",
    }
)
ALLOWED_OKX_EEA_HOSTS = frozenset(
    {
        "eea.okx.com",
        "wseeapap.okx.com",
    }
)
FORBIDDEN_LOCALHOST_MARKERS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
    }
)
FORBIDDEN_SERIALIZATION_KEYS = frozenset(
    {
        "api_key",
        "api_secret",
        "secret",
        "passphrase",
        "password",
        "token",
        "credential",
        "credentials",
        "private_key",
    }
)

AWS_RUNTIME_OWNER_PATHS: tuple[str, ...] = (
    "src/ops/bounded_futures_testnet_venue_binding_v0.py",
    "scripts/ops/aws_remote_247_bounded_offline_smoke_preflight_v0.py",
    "scripts/ops/preflight_remote_runtime_runner_v0.py",
    "scripts/ops/preflight_s3_finalized_evidence_export_v0.py",
    "scripts/ops/run_paper_only_bounded_observation_adapter_v0.py",
    "scripts/ops/run_shadow_bounded_observation_adapter_v0.py",
    "tests/fixtures/ops/remote_host_inventory_planning_v0.json",
    "docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md",
    "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md",
    "docs/ops/specs/LOCAL_BOUNDED_SECRET_ENV_FILE_CONTRACT.md",
)

REASON_RUNTIME_ENVIRONMENT_MISSING = "RUNTIME_ENVIRONMENT_MISSING"
REASON_RUNTIME_ENVIRONMENT_FORBIDDEN = "RUNTIME_ENVIRONMENT_FORBIDDEN"
REASON_REST_HOST_MISMATCH = "REST_HOST_MISMATCH"
REASON_REST_HOST_PRODUCTION = "REST_HOST_PRODUCTION"
REASON_PUBLIC_WS_HOST_MISMATCH = "PUBLIC_WS_HOST_MISMATCH"
REASON_PRIVATE_WS_HOST_MISSING = "PRIVATE_WS_HOST_MISSING"
REASON_PRIVATE_WS_HOST_PRODUCTION = "PRIVATE_WS_HOST_PRODUCTION"
REASON_WEBSOCKET_PORT_NOT_EXPLICIT = "WEBSOCKET_PORT_NOT_EXPLICIT"
REASON_WEBSOCKET_PORT_443_ASSUMED = "WEBSOCKET_PORT_443_ASSUMED"
REASON_SIMULATION_HEADER_DISABLED = "SIMULATION_HEADER_DISABLED"
REASON_SIMULATION_HEADER_NAME_MISMATCH = "SIMULATION_HEADER_NAME_MISMATCH"
REASON_SIMULATION_HEADER_VALUE_MISMATCH = "SIMULATION_HEADER_VALUE_MISMATCH"
REASON_CREDENTIALS_NOT_EXTERNALIZED = "CREDENTIALS_NOT_EXTERNALIZED"
REASON_HARDCODED_CREDENTIALS = "HARDCODED_CREDENTIALS"
REASON_CREDENTIAL_SCOPES_NOT_SEPARATED = "CREDENTIAL_SCOPES_NOT_SEPARATED"
REASON_SHARED_READONLY_TRADE_SECRET_SLOT = "SHARED_READONLY_TRADE_SECRET_SLOT"
REASON_LOCAL_FILE_PATH_DEPENDENCY = "LOCAL_FILE_PATH_DEPENDENCY"
REASON_LOCALHOST_DEPENDENCY = "LOCALHOST_DEPENDENCY"
REASON_LOG_CREDENTIALS = "LOG_CREDENTIALS"
REASON_UNBOUNDED_RETRY = "UNBOUNDED_RETRY"
REASON_UNBOUNDED_RECONNECT = "UNBOUNDED_RECONNECT"
REASON_RECONNECT_POLICY_MISSING = "RECONNECT_POLICY_MISSING"
REASON_RATE_LIMIT_NOT_FAIL_CLOSED = "RATE_LIMIT_NOT_FAIL_CLOSED"
REASON_DEMO_PRODUCTION_INSTRUMENT_COLLISION = "DEMO_PRODUCTION_INSTRUMENT_COLLISION"
REASON_PRODUCTION_INSTRUMENT_IN_NON_PRODUCTION_ENV = "PRODUCTION_INSTRUMENT_IN_NON_PRODUCTION_ENV"
REASON_AUTOMATIC_INSTRUMENT_SUBSTITUTION = "AUTOMATIC_INSTRUMENT_SUBSTITUTION"
REASON_AUTOMATIC_PRODUCTION_FALLBACK = "AUTOMATIC_PRODUCTION_FALLBACK"
REASON_AWS_DEPLOYMENT_AUTHORIZED = "AWS_DEPLOYMENT_AUTHORIZED"
REASON_AWS_RUNTIME_EXECUTED = "AWS_RUNTIME_EXECUTED"
REASON_SECRET_MATERIAL_REJECTED = "SECRET_MATERIAL_REJECTED"


class AwsShadowPaperTestnetCompatibilityError(ValueError):
    """Fail-closed AWS Shadow/Paper/Testnet compatibility evaluation error."""


class AwsShadowPaperTestnetCompatibilityVerdictKind(str, Enum):
    AWS_RUNTIME_COMPATIBLE = "AWS_RUNTIME_COMPATIBLE"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class BoundedReconnectPolicy:
    max_attempts: int
    initial_backoff_seconds: float
    max_backoff_seconds: float
    heartbeat_interval_seconds: float
    reconnect_timeout_seconds: float


@dataclass(frozen=True)
class CredentialSlotBinding:
    slot_id: str
    env_var_name: str
    capability: str


@dataclass(frozen=True)
class AwsShadowPaperTestnetOkxEuropeBindingInput:
    runtime_environment: str = ""
    rest_host: str = ""
    public_ws_host: str = ""
    private_ws_host: str = ""
    websocket_port: int | None = None
    simulation_header_name: str = SIMULATION_HEADER_NAME
    simulation_header_value: str = SIMULATION_HEADER_VALUE
    simulation_header_enabled: bool = False
    demo_instrument_id: str = ""
    production_instrument_id: str = ""
    active_instrument_id: str = ""
    credential_slots: tuple[CredentialSlotBinding, ...] = ()
    reconnect_policy: BoundedReconnectPolicy | None = None
    rate_limit_fail_closed: bool = False
    local_file_path_dependencies: tuple[str, ...] = ()
    localhost_dependencies: tuple[str, ...] = ()
    hardcoded_credentials: bool = False
    shared_readonly_trade_secret_slot: bool = False
    log_credentials: bool = False
    automatic_instrument_substitution: bool = False
    automatic_production_fallback: bool = False
    aws_deployment_authorized: bool = False
    aws_runtime_executed: bool = False
    unbounded_retry: bool = False
    unbounded_reconnect: bool = False


@dataclass(frozen=True)
class AwsShadowPaperTestnetOkxEuropeCompatibilityResult:
    verdict: AwsShadowPaperTestnetCompatibilityVerdictKind
    reason_codes: tuple[str, ...]
    aws_runtime_compatible: bool
    runtime_environment_explicit: bool
    rest_host_explicit: bool
    public_ws_host_explicit: bool
    private_ws_host_explicit: bool
    websocket_port_explicit: bool
    simulation_header_explicit: bool
    credentials_externalized: bool
    credential_scopes_separated: bool
    secrets_log_redaction_required: bool
    stateless_restart_supported: bool
    durable_reconciliation_supported: bool
    bounded_reconnect_policy_required: bool
    rate_limit_fail_closed: bool
    production_demo_environment_separation: bool
    automatic_production_fallback_allowed: bool
    automatic_instrument_substitution_allowed: bool
    aws_deployment_authorized: bool
    authority_impact: str
    value_redacted: bool
    no_secret_material: bool


@dataclass(frozen=True)
class AwsShadowPaperTestnetCloseoutMachineLines:
    aws_runtime_compatible: bool
    aws_runtime_owner_paths: tuple[str, ...]
    aws_config_reuse_possible: bool
    aws_secret_injection_compatible: bool
    aws_network_requirements_documented: bool
    aws_websocket_port_requirement: int
    aws_simulation_header_transportable: bool
    aws_restart_reconciliation_compatible: bool
    aws_production_demo_separation_proven: bool
    aws_deployment_authorized: bool
    aws_runtime_executed: bool


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _normalize_host_url(url: str) -> str:
    normalized = url.strip().rstrip("/")
    if not normalized:
        return ""
    if not normalized.startswith(("http://", "https://", "ws://", "wss://")):
        normalized = f"https://{normalized}"
    return normalized


def _contains_forbidden_marker(value: str, markers: frozenset[str]) -> bool:
    normalized = _normalize(value)
    return any(marker in normalized for marker in markers)


def _extract_hostname(value: str) -> str:
    normalized = _normalize_host_url(value)
    if not normalized:
        return ""
    parsed = urlparse(normalized)
    if parsed.hostname:
        return parsed.hostname.lower()
    stripped = normalized
    for prefix in ("https://", "http://", "wss://", "ws://"):
        if stripped.startswith(prefix):
            stripped = stripped[len(prefix) :]
    return stripped.split("/", 1)[0].split(":", 1)[0].lower()


def _is_forbidden_production_host(value: str) -> bool:
    hostname = _extract_hostname(value)
    if not hostname:
        return False
    if hostname in ALLOWED_OKX_EEA_HOSTS:
        return False
    if hostname in FORBIDDEN_PRODUCTION_HOSTS:
        return True
    return _contains_forbidden_marker(hostname, FORBIDDEN_PRODUCTION_HOST_MARKERS)


def _parse_websocket_port(ws_host: str) -> int | None:
    parsed = urlparse(ws_host.strip())
    if parsed.port is not None:
        return parsed.port
    if parsed.scheme in {"ws", "wss"} and not parsed.port:
        return None
    return None


def _validate_runtime_environment(runtime_environment: str) -> tuple[list[str], bool]:
    normalized = _normalize(runtime_environment)
    if not normalized:
        return [REASON_RUNTIME_ENVIRONMENT_MISSING], False
    if normalized not in ALLOWED_RUNTIME_ENVIRONMENTS:
        return [REASON_RUNTIME_ENVIRONMENT_FORBIDDEN], False
    return [], True


def _validate_rest_host(rest_host: str) -> tuple[list[str], bool]:
    normalized = _normalize_host_url(rest_host)
    if not normalized:
        return [REASON_REST_HOST_MISMATCH], False
    if normalized != REQUIRED_REST_HOST:
        if _is_forbidden_production_host(normalized):
            return [REASON_REST_HOST_PRODUCTION, REASON_REST_HOST_MISMATCH], False
        return [REASON_REST_HOST_MISMATCH], False
    return [], True


def _validate_public_ws_host(public_ws_host: str) -> tuple[list[str], bool]:
    normalized = public_ws_host.strip().rstrip("/")
    if not normalized:
        return [REASON_PUBLIC_WS_HOST_MISMATCH], False
    if normalized != REQUIRED_DEMO_PUBLIC_WS_HOST.rstrip("/"):
        if _is_forbidden_production_host(normalized):
            return [REASON_PUBLIC_WS_HOST_MISMATCH], False
        return [REASON_PUBLIC_WS_HOST_MISMATCH], False
    return [], True


def _validate_private_ws_host(private_ws_host: str) -> tuple[list[str], bool]:
    normalized = private_ws_host.strip().rstrip("/")
    if not normalized:
        return [REASON_PRIVATE_WS_HOST_MISSING], False
    if _is_forbidden_production_host(normalized):
        return [REASON_PRIVATE_WS_HOST_PRODUCTION, REASON_PRIVATE_WS_HOST_MISSING], False
    return [], True


def _validate_websocket_port(
    *,
    public_ws_host: str,
    private_ws_host: str,
    websocket_port: int | None,
) -> tuple[list[str], bool]:
    reasons: list[str] = []
    parsed_public = _parse_websocket_port(public_ws_host)
    parsed_private = _parse_websocket_port(private_ws_host)
    explicit_port = websocket_port if websocket_port is not None else parsed_public
    if explicit_port is None:
        reasons.append(REASON_WEBSOCKET_PORT_NOT_EXPLICIT)
        return reasons, False
    if explicit_port == 443:
        reasons.append(REASON_WEBSOCKET_PORT_443_ASSUMED)
        return reasons, False
    if explicit_port != REQUIRED_WEBSOCKET_PORT:
        reasons.append(REASON_WEBSOCKET_PORT_NOT_EXPLICIT)
        return reasons, False
    if parsed_private is not None and parsed_private != REQUIRED_WEBSOCKET_PORT:
        reasons.append(REASON_WEBSOCKET_PORT_NOT_EXPLICIT)
        return reasons, False
    return [], True


def _validate_simulation_header(
    *,
    enabled: bool,
    header_name: str,
    header_value: str,
) -> tuple[list[str], bool]:
    reasons: list[str] = []
    if not enabled:
        reasons.append(REASON_SIMULATION_HEADER_DISABLED)
        return reasons, False
    if _normalize(header_name) != _normalize(SIMULATION_HEADER_NAME):
        reasons.append(REASON_SIMULATION_HEADER_NAME_MISMATCH)
    if header_value.strip() != SIMULATION_HEADER_VALUE:
        reasons.append(REASON_SIMULATION_HEADER_VALUE_MISMATCH)
    return reasons, not reasons


def _validate_credential_slots(
    slots: tuple[CredentialSlotBinding, ...],
    *,
    hardcoded_credentials: bool,
    shared_readonly_trade_secret_slot: bool,
) -> tuple[list[str], bool, bool]:
    reasons: list[str] = []
    if hardcoded_credentials:
        reasons.append(REASON_HARDCODED_CREDENTIALS)
    if shared_readonly_trade_secret_slot:
        reasons.append(REASON_SHARED_READONLY_TRADE_SECRET_SLOT)
    if not slots:
        reasons.extend(
            [
                REASON_CREDENTIALS_NOT_EXTERNALIZED,
                REASON_CREDENTIAL_SCOPES_NOT_SEPARATED,
            ]
        )
        return reasons, False, False

    slot_ids = {slot.slot_id for slot in slots}
    env_names = [slot.env_var_name.strip() for slot in slots]
    if not all(env_names):
        reasons.append(REASON_CREDENTIALS_NOT_EXTERNALIZED)
    if len(set(env_names)) != len(env_names):
        reasons.append(REASON_CREDENTIAL_SCOPES_NOT_SEPARATED)
    if slot_ids != REQUIRED_CREDENTIAL_SLOT_IDS:
        reasons.append(REASON_CREDENTIAL_SCOPES_NOT_SEPARATED)
    externalized = not hardcoded_credentials and all(env_names) and not reasons
    separated = (
        slot_ids == REQUIRED_CREDENTIAL_SLOT_IDS
        and len(set(env_names)) == len(env_names)
        and not shared_readonly_trade_secret_slot
    )
    if not separated and REASON_CREDENTIAL_SCOPES_NOT_SEPARATED not in reasons:
        reasons.append(REASON_CREDENTIAL_SCOPES_NOT_SEPARATED)
    if not externalized and REASON_CREDENTIALS_NOT_EXTERNALIZED not in reasons:
        reasons.append(REASON_CREDENTIALS_NOT_EXTERNALIZED)
    return reasons, externalized, separated


def _validate_local_dependencies(
    *,
    local_file_path_dependencies: tuple[str, ...],
    localhost_dependencies: tuple[str, ...],
) -> list[str]:
    reasons: list[str] = []
    if local_file_path_dependencies:
        reasons.append(REASON_LOCAL_FILE_PATH_DEPENDENCY)
    for dep in localhost_dependencies:
        if _contains_forbidden_marker(dep, FORBIDDEN_LOCALHOST_MARKERS):
            reasons.append(REASON_LOCALHOST_DEPENDENCY)
    return reasons


def _validate_reconnect_policy(
    policy: BoundedReconnectPolicy | None,
    *,
    unbounded_retry: bool,
    unbounded_reconnect: bool,
) -> tuple[list[str], bool]:
    reasons: list[str] = []
    if unbounded_retry:
        reasons.append(REASON_UNBOUNDED_RETRY)
    if unbounded_reconnect:
        reasons.append(REASON_UNBOUNDED_RECONNECT)
    if policy is None:
        reasons.append(REASON_RECONNECT_POLICY_MISSING)
        return reasons, False
    if policy.max_attempts <= 0:
        reasons.append(REASON_UNBOUNDED_RECONNECT)
    if policy.initial_backoff_seconds <= 0 or policy.max_backoff_seconds <= 0:
        reasons.append(REASON_UNBOUNDED_RETRY)
    if policy.max_backoff_seconds < policy.initial_backoff_seconds:
        reasons.append(REASON_UNBOUNDED_RETRY)
    if policy.heartbeat_interval_seconds <= 0 or policy.reconnect_timeout_seconds <= 0:
        reasons.append(REASON_RECONNECT_POLICY_MISSING)
    return reasons, not reasons


def _validate_instrument_separation(
    *,
    runtime_environment: str,
    demo_instrument_id: str,
    production_instrument_id: str,
    active_instrument_id: str,
    automatic_instrument_substitution: bool,
) -> tuple[list[str], bool]:
    reasons: list[str] = []
    demo = demo_instrument_id.strip()
    production = production_instrument_id.strip()
    active = active_instrument_id.strip() or demo
    if automatic_instrument_substitution:
        reasons.append(REASON_AUTOMATIC_INSTRUMENT_SUBSTITUTION)
    if not demo or not production:
        reasons.append(REASON_DEMO_PRODUCTION_INSTRUMENT_COLLISION)
        return reasons, False
    if demo == production:
        reasons.append(REASON_DEMO_PRODUCTION_INSTRUMENT_COLLISION)
    if _normalize(runtime_environment) in ALLOWED_RUNTIME_ENVIRONMENTS and active == production:
        reasons.append(REASON_PRODUCTION_INSTRUMENT_IN_NON_PRODUCTION_ENV)
    separated = not reasons and demo != production and active != production
    return reasons, separated


def _immutable_result_fields(
    *,
    verdict: AwsShadowPaperTestnetCompatibilityVerdictKind,
    reason_codes: list[str],
    runtime_environment_explicit: bool,
    rest_host_explicit: bool,
    public_ws_host_explicit: bool,
    private_ws_host_explicit: bool,
    websocket_port_explicit: bool,
    simulation_header_explicit: bool,
    credentials_externalized: bool,
    credential_scopes_separated: bool,
    bounded_reconnect_policy_required: bool,
    rate_limit_fail_closed: bool,
    production_demo_environment_separation: bool,
) -> AwsShadowPaperTestnetOkxEuropeCompatibilityResult:
    deduped = tuple(dict.fromkeys(reason_codes))
    compatible = verdict == AwsShadowPaperTestnetCompatibilityVerdictKind.AWS_RUNTIME_COMPATIBLE
    return AwsShadowPaperTestnetOkxEuropeCompatibilityResult(
        verdict=verdict,
        reason_codes=deduped,
        aws_runtime_compatible=compatible,
        runtime_environment_explicit=runtime_environment_explicit,
        rest_host_explicit=rest_host_explicit,
        public_ws_host_explicit=public_ws_host_explicit,
        private_ws_host_explicit=private_ws_host_explicit,
        websocket_port_explicit=websocket_port_explicit,
        simulation_header_explicit=simulation_header_explicit,
        credentials_externalized=credentials_externalized,
        credential_scopes_separated=credential_scopes_separated,
        secrets_log_redaction_required=True,
        stateless_restart_supported=True,
        durable_reconciliation_supported=True,
        bounded_reconnect_policy_required=bounded_reconnect_policy_required,
        rate_limit_fail_closed=rate_limit_fail_closed,
        production_demo_environment_separation=production_demo_environment_separation,
        automatic_production_fallback_allowed=False,
        automatic_instrument_substitution_allowed=False,
        aws_deployment_authorized=False,
        authority_impact=AUTHORITY_IMPACT,
        value_redacted=True,
        no_secret_material=True,
    )


def evaluate_aws_shadow_paper_testnet_okx_europe_compatibility(
    inp: AwsShadowPaperTestnetOkxEuropeBindingInput,
) -> AwsShadowPaperTestnetOkxEuropeCompatibilityResult:
    """Evaluate OKX-Europe binding structural compatibility with AWS runtime paths."""
    reasons: list[str] = []

    env_reasons, runtime_environment_explicit = _validate_runtime_environment(
        inp.runtime_environment
    )
    reasons.extend(env_reasons)

    rest_reasons, rest_host_explicit = _validate_rest_host(inp.rest_host)
    reasons.extend(rest_reasons)

    private_ws = inp.private_ws_host or DEFAULT_PRIVATE_WS_HOST
    private_reasons, private_ws_host_explicit = _validate_private_ws_host(private_ws)
    reasons.extend(private_reasons)

    public_reasons, public_ws_host_explicit = _validate_public_ws_host(inp.public_ws_host)
    reasons.extend(public_reasons)

    port_reasons, websocket_port_explicit = _validate_websocket_port(
        public_ws_host=inp.public_ws_host,
        private_ws_host=private_ws,
        websocket_port=inp.websocket_port,
    )
    reasons.extend(port_reasons)

    sim_reasons, simulation_header_explicit = _validate_simulation_header(
        enabled=inp.simulation_header_enabled,
        header_name=inp.simulation_header_name,
        header_value=inp.simulation_header_value,
    )
    reasons.extend(sim_reasons)

    cred_reasons, credentials_externalized, credential_scopes_separated = (
        _validate_credential_slots(
            inp.credential_slots,
            hardcoded_credentials=inp.hardcoded_credentials,
            shared_readonly_trade_secret_slot=inp.shared_readonly_trade_secret_slot,
        )
    )
    reasons.extend(cred_reasons)

    reasons.extend(
        _validate_local_dependencies(
            local_file_path_dependencies=inp.local_file_path_dependencies,
            localhost_dependencies=inp.localhost_dependencies,
        )
    )

    if inp.log_credentials:
        reasons.append(REASON_LOG_CREDENTIALS)

    reconnect_reasons, bounded_reconnect_policy_required = _validate_reconnect_policy(
        inp.reconnect_policy,
        unbounded_retry=inp.unbounded_retry,
        unbounded_reconnect=inp.unbounded_reconnect,
    )
    reasons.extend(reconnect_reasons)

    if not inp.rate_limit_fail_closed:
        reasons.append(REASON_RATE_LIMIT_NOT_FAIL_CLOSED)
    rate_limit_fail_closed = inp.rate_limit_fail_closed

    instrument_reasons, production_demo_environment_separation = _validate_instrument_separation(
        runtime_environment=inp.runtime_environment,
        demo_instrument_id=inp.demo_instrument_id,
        production_instrument_id=inp.production_instrument_id,
        active_instrument_id=inp.active_instrument_id,
        automatic_instrument_substitution=inp.automatic_instrument_substitution,
    )
    reasons.extend(instrument_reasons)

    if inp.automatic_production_fallback:
        reasons.append(REASON_AUTOMATIC_PRODUCTION_FALLBACK)
    if inp.aws_deployment_authorized:
        reasons.append(REASON_AWS_DEPLOYMENT_AUTHORIZED)
    if inp.aws_runtime_executed:
        reasons.append(REASON_AWS_RUNTIME_EXECUTED)

    deduped = list(dict.fromkeys(reasons))
    if deduped:
        return _immutable_result_fields(
            verdict=AwsShadowPaperTestnetCompatibilityVerdictKind.FAIL_CLOSED,
            reason_codes=deduped,
            runtime_environment_explicit=runtime_environment_explicit,
            rest_host_explicit=rest_host_explicit,
            public_ws_host_explicit=public_ws_host_explicit,
            private_ws_host_explicit=private_ws_host_explicit,
            websocket_port_explicit=websocket_port_explicit,
            simulation_header_explicit=simulation_header_explicit,
            credentials_externalized=credentials_externalized,
            credential_scopes_separated=credential_scopes_separated,
            bounded_reconnect_policy_required=bounded_reconnect_policy_required,
            rate_limit_fail_closed=rate_limit_fail_closed,
            production_demo_environment_separation=production_demo_environment_separation,
        )

    return _immutable_result_fields(
        verdict=AwsShadowPaperTestnetCompatibilityVerdictKind.AWS_RUNTIME_COMPATIBLE,
        reason_codes=[],
        runtime_environment_explicit=True,
        rest_host_explicit=True,
        public_ws_host_explicit=True,
        private_ws_host_explicit=True,
        websocket_port_explicit=True,
        simulation_header_explicit=True,
        credentials_externalized=True,
        credential_scopes_separated=True,
        bounded_reconnect_policy_required=True,
        rate_limit_fail_closed=True,
        production_demo_environment_separation=True,
    )


def default_bounded_reconnect_policy() -> BoundedReconnectPolicy:
    return BoundedReconnectPolicy(
        max_attempts=5,
        initial_backoff_seconds=1.0,
        max_backoff_seconds=30.0,
        heartbeat_interval_seconds=20.0,
        reconnect_timeout_seconds=10.0,
    )


def default_okx_europe_credential_slots() -> tuple[CredentialSlotBinding, ...]:
    return (
        CredentialSlotBinding(
            slot_id="public",
            env_var_name="OKX_EEA_PUBLIC_API_KEY",
            capability="public_read",
        ),
        CredentialSlotBinding(
            slot_id="readonly_private",
            env_var_name="OKX_EEA_READONLY_API_KEY",
            capability="private_readonly",
        ),
        CredentialSlotBinding(
            slot_id="trade",
            env_var_name="OKX_EEA_TRADE_API_KEY",
            capability="trade",
        ),
    )


def default_aws_shadow_paper_testnet_okx_europe_binding_input() -> (
    AwsShadowPaperTestnetOkxEuropeBindingInput
):
    return AwsShadowPaperTestnetOkxEuropeBindingInput()


def default_valid_aws_shadow_paper_testnet_okx_europe_binding_input(
    **overrides: object,
) -> AwsShadowPaperTestnetOkxEuropeBindingInput:
    base: dict[str, object] = {
        "runtime_environment": "testnet",
        "rest_host": REQUIRED_REST_HOST,
        "public_ws_host": REQUIRED_DEMO_PUBLIC_WS_HOST,
        "private_ws_host": DEFAULT_PRIVATE_WS_HOST,
        "websocket_port": REQUIRED_WEBSOCKET_PORT,
        "simulation_header_enabled": True,
        "demo_instrument_id": DEMO_REFERENCE_INSTRUMENT_ID,
        "production_instrument_id": PRODUCTION_INSTRUMENT_ID,
        "active_instrument_id": DEMO_REFERENCE_INSTRUMENT_ID,
        "credential_slots": default_okx_europe_credential_slots(),
        "reconnect_policy": default_bounded_reconnect_policy(),
        "rate_limit_fail_closed": True,
    }
    base.update(overrides)
    return AwsShadowPaperTestnetOkxEuropeBindingInput(**base)  # type: ignore[arg-type]


def reject_secret_like_mapping(mapping: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for key in mapping:
        if key.lower() in FORBIDDEN_SERIALIZATION_KEYS:
            reasons.append(REASON_SECRET_MATERIAL_REJECTED)
    return reasons


def build_aws_shadow_paper_testnet_closeout_machine_lines(
    result: AwsShadowPaperTestnetOkxEuropeCompatibilityResult,
) -> AwsShadowPaperTestnetCloseoutMachineLines:
    validate_aws_shadow_paper_testnet_okx_europe_compatibility_result(result)
    return AwsShadowPaperTestnetCloseoutMachineLines(
        aws_runtime_compatible=result.aws_runtime_compatible,
        aws_runtime_owner_paths=AWS_RUNTIME_OWNER_PATHS,
        aws_config_reuse_possible=result.aws_runtime_compatible,
        aws_secret_injection_compatible=result.credentials_externalized
        and result.credential_scopes_separated,
        aws_network_requirements_documented=True,
        aws_websocket_port_requirement=REQUIRED_WEBSOCKET_PORT,
        aws_simulation_header_transportable=result.simulation_header_explicit,
        aws_restart_reconciliation_compatible=result.stateless_restart_supported
        and result.durable_reconciliation_supported,
        aws_production_demo_separation_proven=result.production_demo_environment_separation,
        aws_deployment_authorized=False,
        aws_runtime_executed=False,
    )


def serialize_aws_shadow_paper_testnet_closeout_machine_lines(
    lines: AwsShadowPaperTestnetCloseoutMachineLines,
) -> dict[str, str | bool | int | tuple[str, ...]]:
    data: dict[str, str | bool | int | tuple[str, ...]] = {
        "AWS_RUNTIME_COMPATIBLE": str(lines.aws_runtime_compatible).lower(),
        "AWS_RUNTIME_OWNER_PATHS": lines.aws_runtime_owner_paths,
        "AWS_CONFIG_REUSE_POSSIBLE": str(lines.aws_config_reuse_possible).lower(),
        "AWS_SECRET_INJECTION_COMPATIBLE": str(lines.aws_secret_injection_compatible).lower(),
        "AWS_NETWORK_REQUIREMENTS_DOCUMENTED": str(
            lines.aws_network_requirements_documented
        ).lower(),
        "AWS_WEBSOCKET_PORT_REQUIREMENT": lines.aws_websocket_port_requirement,
        "AWS_SIMULATION_HEADER_TRANSPORTABLE": str(
            lines.aws_simulation_header_transportable
        ).lower(),
        "AWS_RESTART_RECONCILIATION_COMPATIBLE": str(
            lines.aws_restart_reconciliation_compatible
        ).lower(),
        "AWS_PRODUCTION_DEMO_SEPARATION_PROVEN": str(
            lines.aws_production_demo_separation_proven
        ).lower(),
        "AWS_DEPLOYMENT_AUTHORIZED": "false",
        "AWS_RUNTIME_EXECUTED": "false",
    }
    for key in data:
        if isinstance(key, str) and key.lower() in FORBIDDEN_SERIALIZATION_KEYS:
            raise AwsShadowPaperTestnetCompatibilityError(
                f"closeout machine lines must not include forbidden key {key!r}"
            )
    return data


def serialize_aws_shadow_paper_testnet_okx_europe_compatibility_result(
    result: AwsShadowPaperTestnetOkxEuropeCompatibilityResult,
) -> dict[str, Any]:
    validate_aws_shadow_paper_testnet_okx_europe_compatibility_result(result)
    closeout = build_aws_shadow_paper_testnet_closeout_machine_lines(result)
    closeout_data = serialize_aws_shadow_paper_testnet_closeout_machine_lines(closeout)
    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_marker": PACKAGE_MARKER,
        "verdict": result.verdict.value,
        "reason_codes": list(result.reason_codes),
        "aws_runtime_compatible": result.aws_runtime_compatible,
        "runtime_environment_explicit": result.runtime_environment_explicit,
        "rest_host_explicit": result.rest_host_explicit,
        "public_ws_host_explicit": result.public_ws_host_explicit,
        "private_ws_host_explicit": result.private_ws_host_explicit,
        "websocket_port_explicit": result.websocket_port_explicit,
        "simulation_header_explicit": result.simulation_header_explicit,
        "credentials_externalized": result.credentials_externalized,
        "credential_scopes_separated": result.credential_scopes_separated,
        "secrets_log_redaction_required": result.secrets_log_redaction_required,
        "stateless_restart_supported": result.stateless_restart_supported,
        "durable_reconciliation_supported": result.durable_reconciliation_supported,
        "bounded_reconnect_policy_required": result.bounded_reconnect_policy_required,
        "rate_limit_fail_closed": result.rate_limit_fail_closed,
        "production_demo_environment_separation": result.production_demo_environment_separation,
        "automatic_production_fallback_allowed": result.automatic_production_fallback_allowed,
        "automatic_instrument_substitution_allowed": result.automatic_instrument_substitution_allowed,
        "aws_deployment_authorized": result.aws_deployment_authorized,
        "authority_impact": result.authority_impact,
        "value_redacted": result.value_redacted,
        "no_secret_material": result.no_secret_material,
        "required_rest_host": REQUIRED_REST_HOST,
        "required_demo_public_ws_host": REQUIRED_DEMO_PUBLIC_WS_HOST,
        "required_websocket_port": REQUIRED_WEBSOCKET_PORT,
        "simulation_header_name": SIMULATION_HEADER_NAME,
        "simulation_header_value": SIMULATION_HEADER_VALUE,
        "production_instrument_id": PRODUCTION_INSTRUMENT_ID,
        "demo_instrument_id": DEMO_REFERENCE_INSTRUMENT_ID,
        "closeout_machine_lines": closeout_data,
    }
    for key in data:
        if key.lower() in FORBIDDEN_SERIALIZATION_KEYS:
            raise AwsShadowPaperTestnetCompatibilityError(
                f"serialized result must not include forbidden key {key!r}"
            )
    return data


def validate_aws_shadow_paper_testnet_okx_europe_compatibility_result(
    result: AwsShadowPaperTestnetOkxEuropeCompatibilityResult,
) -> None:
    if result.authority_impact != AUTHORITY_IMPACT:
        raise AwsShadowPaperTestnetCompatibilityError(
            "authority_impact must remain NO_AUTHORITY_CHANGE"
        )
    if not result.value_redacted or not result.no_secret_material:
        raise AwsShadowPaperTestnetCompatibilityError(
            "value_redacted and no_secret_material must remain true"
        )
    if result.automatic_production_fallback_allowed:
        raise AwsShadowPaperTestnetCompatibilityError(
            "automatic_production_fallback_allowed must remain false"
        )
    if result.automatic_instrument_substitution_allowed:
        raise AwsShadowPaperTestnetCompatibilityError(
            "automatic_instrument_substitution_allowed must remain false"
        )
    if result.aws_deployment_authorized:
        raise AwsShadowPaperTestnetCompatibilityError("aws_deployment_authorized must remain false")
    if not result.secrets_log_redaction_required:
        raise AwsShadowPaperTestnetCompatibilityError(
            "secrets_log_redaction_required must remain true"
        )
    if not result.stateless_restart_supported or not result.durable_reconciliation_supported:
        raise AwsShadowPaperTestnetCompatibilityError(
            "stateless_restart_supported and durable_reconciliation_supported must remain true"
        )
    if result.verdict == AwsShadowPaperTestnetCompatibilityVerdictKind.AWS_RUNTIME_COMPATIBLE:
        if result.reason_codes:
            raise AwsShadowPaperTestnetCompatibilityError(
                "AWS_RUNTIME_COMPATIBLE requires empty reason_codes"
            )
        if not result.aws_runtime_compatible:
            raise AwsShadowPaperTestnetCompatibilityError(
                "AWS_RUNTIME_COMPATIBLE requires aws_runtime_compatible=true"
            )
    else:
        if not result.reason_codes:
            raise AwsShadowPaperTestnetCompatibilityError(
                "FAIL_CLOSED requires non-empty reason_codes"
            )
