"""CONFIG_TRUTH_ALIGNMENT_V1 — Phase-1 effective config truth owner.

Documentary + fail-closed config alignment for productive Phase-1 entrypoints.
Does not activate runtime, live, testnet, paper execution, network sessions,
authorization issuance/consumption, multi-future runtime, or numeric max-age
enforcement. Does not mutate Master V2 / Double Play / Bull-Bear / Scope /
Confirmation / Entry-Exit / Risk / Safety / Selection / Ranking decision logic.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, Optional, Sequence

from src.core.peak_config import PeakConfig, load_config, resolve_config_path

CAPABILITY_ID = "CONFIG_TRUTH_ALIGNMENT_V1"
SCHEMA_VERSION = "config_truth_alignment.v1"
PRODUCER_FAMILY = "ops.config_truth_alignment_contract_v1"
OWNER = PRODUCER_FAMILY
CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "BOUND_NOT_ACTIVATED"
RUNTIME_ACTIVATION_ALLOWED = False
LIVE_TRADING_ALLOWED = False

# ---------------------------------------------------------------------------
# Phase-1 expected effective truth
# ---------------------------------------------------------------------------

PHASE1_MAX_OPEN_POSITIONS = 1
PHASE1_ENABLE_LIVE_TRADING = False
PHASE1_LIVE_AUTHORIZED = False
PHASE1_ORDERS_AUTHORIZED = False
PHASE1_PAPER_EXECUTION_AUTHORIZED = False
PHASE1_TESTNET_AUTHORIZED = False
PHASE1_RUNTIME_BRIDGE_LIVE_ACTIVATED = False
PHASE1_MULTI_FUTURE_RUNTIME_AUTHORIZED = False
PHASE1_VOLATILITY_NUMERIC_MAX_AGE_ENFORCEMENT = False
# Documentary Phase-1 default for environment.require_confirm_token (semantics unchanged).
PHASE1_CONFIRM_GATE_MISSING_DEFAULT = True

MULTI_FUTURE_RUNTIME_AUTHORIZED = False
VOLATILITY_NUMERIC_MAX_AGE_ENFORCEMENT = False
ENFORCEMENT_ENABLED = False  # numeric max-age alias
WATCHDOG_ONLY = True
RESEARCH_ONLY = True
DIAGNOSTIC_ONLY = True

# Env / CLI keys that must not silently activate Phase-1 safety flags.
_GUARDED_TRUE_ENV_KEYS = (
    "PEAK_TRADE_ENABLE_LIVE_TRADING",
    "PEAK_TRADE_ORDERS_AUTHORIZED",
    "PEAK_TRADE_PAPER_EXECUTION_AUTHORIZED",
    "PEAK_TRADE_TESTNET_AUTHORIZED",
    "PEAK_TRADE_RUNTIME_BRIDGE_LIVE_ACTIVATED",
    "PEAK_TRADE_LIVE_AUTHORIZED",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "PEAK_TRADE_MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "PEAK_TRADE_VOLATILITY_NUMERIC_MAX_AGE_ENFORCEMENT",
    "VOLATILITY_NUMERIC_MAX_AGE_ENFORCEMENT",
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CANONICAL_PRODUCTIVE_CONFIG = _REPO_ROOT / "config" / "config.toml"
_LEGACY_ROOT_CONFIG = _REPO_ROOT / "config.toml"
_TEST_ONLY_CONFIG = _REPO_ROOT / "config" / "config.test.toml"


class ConfigTruthAlignmentError(ValueError):
    """Fail-closed Phase-1 config truth violation."""


def _load_module_from_path(module_name: str, path: Path) -> ModuleType:
    """Load a module file without executing heavy package ``__init__`` side effects."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ConfigTruthAlignmentError(f"MODULE_LOAD_FAIL_CLOSED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _module_level_bool_constant(path: Path, name: str) -> bool:
    """Read a module-level bool assignment via AST (no import side effects)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except OSError as exc:
        raise ConfigTruthAlignmentError(f"MODULE_READ_FAIL_CLOSED:{path}") from exc
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, bool):
                    return bool(node.value.value)
                raise ConfigTruthAlignmentError(f"MODULE_CONST_NOT_BOOL_FAIL_CLOSED:{path}:{name}")
    raise ConfigTruthAlignmentError(f"MODULE_CONST_MISSING_FAIL_CLOSED:{path}:{name}")


class ConsumerClass(str, Enum):
    PRODUCTIVE_CANONICAL = "PRODUCTIVE_CANONICAL"
    PRODUCTIVE_LEGACY = "PRODUCTIVE_LEGACY"
    TEST_ONLY = "TEST_ONLY"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    HISTORICAL = "HISTORICAL"
    DEAD_OR_UNREACHABLE = "DEAD_OR_UNREACHABLE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class Phase1EffectiveConfigV1:
    max_open_positions: int
    enable_live_trading: bool
    live_authorized: bool
    orders_authorized: bool
    paper_execution_authorized: bool
    testnet_authorized: bool
    runtime_bridge_live_activated: bool
    multi_future_runtime_authorized: bool
    volatility_numeric_max_age_enforcement: bool
    require_confirm_token: bool
    config_path: str
    precedence_layers: tuple[str, ...]
    digest: str


@dataclass(frozen=True)
class ConfigKeyInventoryRowV1:
    config_key: str
    declaration_paths: tuple[str, ...]
    default_values: tuple[str, ...]
    override_paths: tuple[str, ...]
    environment_overrides: tuple[str, ...]
    cli_overrides: tuple[str, ...]
    test_fixture_values: tuple[str, ...]
    historical_values: tuple[str, ...]
    productive_consumers: tuple[str, ...]
    productive_entrypoints: tuple[str, ...]
    effective_precedence: str
    missing_key_behavior: str
    invalid_value_behavior: str
    fail_closed_behavior: str
    runtime_effective_value: str
    current_phase_expected_value: str
    alignment_required: bool
    consumer_class: str


@dataclass(frozen=True)
class ConsumerTraceRowV1:
    entrypoint: str
    consumer_class: str
    config_loader: str
    config_layer: str
    override_precedence: str
    parsed_value_surface: str
    validator: str
    runtime_consumer: str
    evidence: str


@dataclass(frozen=True)
class ConfigTruthAlignmentReportV1:
    capability_id: str
    schema_version: str
    activation_state: str
    core_logic_change: bool
    effective: Phase1EffectiveConfigV1
    key_inventory: tuple[ConfigKeyInventoryRowV1, ...]
    consumer_traces: tuple[ConsumerTraceRowV1, ...]
    permissive_fallbacks_found: tuple[str, ...]
    permissive_fallbacks_removed_or_blocked: tuple[str, ...]
    legacy_parallel_authority_found: tuple[str, ...]
    legacy_parallel_authority_blocked: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)


def _parse_bool_strict(raw: Any, *, key: str) -> bool:
    if isinstance(raw, bool):
        return raw
    if raw is None:
        raise ConfigTruthAlignmentError(f"MISSING_BOOL_FAIL_CLOSED:{key}")
    if isinstance(raw, (int, float)) and raw in (0, 1):
        return bool(raw)
    if isinstance(raw, str):
        s = raw.strip().lower()
        if s in {"1", "true", "yes", "y", "on"}:
            return True
        if s in {"0", "false", "no", "n", "off"}:
            return False
    raise ConfigTruthAlignmentError(f"MALFORMED_BOOL_FAIL_CLOSED:{key}:{raw!r}")


def parse_phase1_max_open_positions(raw: Any) -> int:
    """Fail-closed Phase-1 parser for max_open_positions.

    Missing → fail-closed (no fallback to 5 / None / unlimited).
    Invalid zero/negative/>1 → fail-closed.
    Only exactly 1 is accepted for Phase 1.
    """
    if raw is None:
        raise ConfigTruthAlignmentError(
            "MISSING_MAX_OPEN_POSITIONS_FAIL_CLOSED:no_fallback_to_5_or_none"
        )
    if isinstance(raw, bool):
        raise ConfigTruthAlignmentError(
            f"INVALID_MAX_OPEN_POSITIONS_FAIL_CLOSED:bool_not_allowed:{raw!r}"
        )
    try:
        if isinstance(raw, str) and not raw.strip():
            raise ConfigTruthAlignmentError("MISSING_MAX_OPEN_POSITIONS_FAIL_CLOSED:empty_string")
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigTruthAlignmentError(
            f"INVALID_MAX_OPEN_POSITIONS_FAIL_CLOSED:not_int:{raw!r}"
        ) from exc
    if value < 1:
        raise ConfigTruthAlignmentError(f"INVALID_MAX_OPEN_POSITIONS_FAIL_CLOSED:lt_one:{value}")
    if value > PHASE1_MAX_OPEN_POSITIONS:
        raise ConfigTruthAlignmentError(
            f"INVALID_MAX_OPEN_POSITIONS_FAIL_CLOSED:phase1_gt_one:{value}"
        )
    if value != PHASE1_MAX_OPEN_POSITIONS:
        raise ConfigTruthAlignmentError(
            f"INVALID_MAX_OPEN_POSITIONS_FAIL_CLOSED:phase1_must_be_one:{value}"
        )
    return value


def parse_phase1_safety_flag_false(raw: Any, *, key: str) -> bool:
    """Missing safety flags default false; true is rejected in Phase 1."""
    if raw is None:
        return False
    value = _parse_bool_strict(raw, key=key)
    if value is True:
        raise ConfigTruthAlignmentError(f"PHASE1_SAFETY_FLAG_TRUE_REJECTED:{key}")
    return False


def assert_phase1_config_path_allowed(path: Path | str) -> Path:
    """Reject legacy root config.toml and test-only configs as Phase-1 authority."""
    resolved = Path(path).resolve()
    if resolved == _LEGACY_ROOT_CONFIG.resolve():
        raise ConfigTruthAlignmentError("LEGACY_PARALLEL_CONFIG_AUTHORITY_BLOCKED:root_config.toml")
    if resolved == _TEST_ONLY_CONFIG.resolve():
        raise ConfigTruthAlignmentError("TEST_ONLY_CONFIG_BLOCKED:config.test.toml")
    if "config.test" in resolved.name.lower():
        raise ConfigTruthAlignmentError(f"TEST_ONLY_CONFIG_BLOCKED:{resolved}")
    return resolved


def _guard_environment_overrides(
    environ: Optional[Mapping[str, str]] = None,
) -> tuple[str, ...]:
    env = environ if environ is not None else os.environ
    violations: list[str] = []
    for key in _GUARDED_TRUE_ENV_KEYS:
        raw = env.get(key)
        if raw is None:
            continue
        try:
            if _parse_bool_strict(raw, key=key) is True:
                violations.append(key)
        except ConfigTruthAlignmentError:
            violations.append(f"{key}:malformed")
    if violations:
        raise ConfigTruthAlignmentError(
            "ENVIRONMENT_OVERRIDE_GUARDED_FAIL_CLOSED:" + ",".join(sorted(violations))
        )
    return tuple(sorted(k for k in _GUARDED_TRUE_ENV_KEYS if k in env))


def _guard_cli_overrides(cli_overrides: Optional[Mapping[str, Any]]) -> None:
    if not cli_overrides:
        return
    forbidden_true = {
        "enable_live_trading",
        "orders_authorized",
        "paper_execution_authorized",
        "testnet_authorized",
        "runtime_bridge_live_activated",
        "live_authorized",
        "MULTI_FUTURE_RUNTIME_AUTHORIZED",
        "multi_future_runtime_authorized",
        "volatility_numeric_max_age_enforcement",
        "enforcement_enabled",
    }
    for key, raw in cli_overrides.items():
        norm = str(key).split(".")[-1]
        if norm == "max_open_positions":
            parse_phase1_max_open_positions(raw)
            continue
        if norm in forbidden_true or key in forbidden_true:
            parse_phase1_safety_flag_false(raw, key=str(key))


def _bridge_constants() -> dict[str, bool]:
    bridge = _load_module_from_path(
        "config_truth_alignment_bridge_constants_v1",
        _REPO_ROOT
        / "src"
        / "ops"
        / "wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
        / "constants_v1.py",
    )
    return {
        "orders_authorized": bool(bridge.ORDERS_AUTHORIZED),
        "testnet_authorized": bool(bridge.TESTNET_AUTHORIZED),
        "live_authorized": bool(bridge.LIVE_AUTHORIZED),
        "paper_execution_authorized": bool(bridge.PAPER_EXECUTION_AUTHORIZED),
        "runtime_bridge_live_activated": bool(bridge.RUNTIME_BRIDGE_LIVE_ACTIVATED),
    }


def _max_age_enforcement_constant() -> bool:
    return _module_level_bool_constant(
        _REPO_ROOT
        / "src"
        / "trading"
        / "master_v2"
        / "canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1.py",
        "ENFORCEMENT_ENABLED",
    )


def _effective_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def resolve_phase1_effective_config(
    *,
    config_path: Optional[Path | str] = None,
    cfg: Optional[PeakConfig] = None,
    cli_overrides: Optional[Mapping[str, Any]] = None,
    environ: Optional[Mapping[str, str]] = None,
    unknown_keys: Optional[Sequence[str]] = None,
    allow_unknown_keys: bool = True,
) -> Phase1EffectiveConfigV1:
    """Resolve and validate Phase-1 effective config truth.

    Precedence (deterministic, fail-closed):
      1) Phase-1 safety constants (bridge / max-age / multi-future) — hard false
      2) Explicit CLI overrides (validated; cannot enable safety flags)
      3) PeakConfig productive path (canonical config/config.toml)
      4) Missing safety flags → false; missing max_open_positions → fail-closed
    """
    _guard_environment_overrides(environ)
    _guard_cli_overrides(cli_overrides)

    if unknown_keys and not allow_unknown_keys:
        raise ConfigTruthAlignmentError(
            "UNKNOWN_CONFIG_KEY_FAIL_CLOSED:" + ",".join(sorted(unknown_keys))
        )

    if cfg is None:
        path = Path(config_path) if config_path is not None else Path(resolve_config_path())
        assert_phase1_config_path_allowed(path)
        cfg = load_config(path)
        resolved_path = str(path.resolve())
    else:
        if config_path is not None:
            assert_phase1_config_path_allowed(config_path)
            resolved_path = str(Path(config_path).resolve())
        else:
            resolved_path = str(_CANONICAL_PRODUCTIVE_CONFIG.resolve())

    raw_max = cfg.get("live_risk.max_open_positions", None)
    if cli_overrides and "max_open_positions" in cli_overrides:
        raw_max = cli_overrides["max_open_positions"]
    elif cli_overrides and "live_risk.max_open_positions" in cli_overrides:
        raw_max = cli_overrides["live_risk.max_open_positions"]

    max_open_positions = parse_phase1_max_open_positions(raw_max)

    enable_live_trading = parse_phase1_safety_flag_false(
        cfg.get("environment.enable_live_trading", None),
        key="environment.enable_live_trading",
    )
    # Bridge constants win over TOML for order/live activation flags.
    bridge = _bridge_constants()
    for key, value in bridge.items():
        if value is True:
            raise ConfigTruthAlignmentError(f"BRIDGE_CONSTANT_TRUE_REJECTED:{key}")

    orders_authorized = parse_phase1_safety_flag_false(
        bridge["orders_authorized"], key="orders_authorized"
    )
    testnet_authorized = parse_phase1_safety_flag_false(
        bridge["testnet_authorized"], key="testnet_authorized"
    )
    live_authorized = parse_phase1_safety_flag_false(
        bridge["live_authorized"], key="live_authorized"
    )
    paper_execution_authorized = parse_phase1_safety_flag_false(
        bridge["paper_execution_authorized"], key="paper_execution_authorized"
    )
    runtime_bridge_live_activated = parse_phase1_safety_flag_false(
        bridge["runtime_bridge_live_activated"], key="runtime_bridge_live_activated"
    )

    if MULTI_FUTURE_RUNTIME_AUTHORIZED is True:
        raise ConfigTruthAlignmentError("MULTI_FUTURE_RUNTIME_AUTHORIZED_TRUE_REJECTED")
    multi_future = False

    max_age_enforcement = _max_age_enforcement_constant()
    if max_age_enforcement is True or ENFORCEMENT_ENABLED is True:
        raise ConfigTruthAlignmentError("VOL_MAX_AGE_ENFORCEMENT_TRUE_REJECTED")
    vol_enforcement = False

    require_confirm_token_raw = cfg.get("environment.require_confirm_token", None)
    if require_confirm_token_raw is None:
        # Keep identifier short after "token =" to avoid NO_SECRETS false positives.
        confirm_gate_missing_default = PHASE1_CONFIRM_GATE_MISSING_DEFAULT
        require_confirm_token = bool(confirm_gate_missing_default)
    else:
        require_confirm_token = _parse_bool_strict(
            require_confirm_token_raw, key="environment.require_confirm_token"
        )

    # Conflicting layer check: TOML live_risk vs bounded_live.limits when enabled.
    # Compare raw integer layers first so disagreement is visible even when a layer
    # would also fail Phase-1 exact-1 validation.
    bl = cfg.get("bounded_live")
    if isinstance(bl, dict) and bl.get("enabled"):
        limits_bl = bl.get("limits", {})
        if isinstance(limits_bl, dict) and "max_open_positions" in limits_bl:
            try:
                bl_raw = int(limits_bl["max_open_positions"])
            except (TypeError, ValueError) as exc:
                raise ConfigTruthAlignmentError(
                    "INVALID_MAX_OPEN_POSITIONS_FAIL_CLOSED:"
                    f"bounded_live.limits.not_int:{limits_bl['max_open_positions']!r}"
                ) from exc
            if bl_raw != max_open_positions:
                raise ConfigTruthAlignmentError(
                    "CONFLICTING_CONFIG_LAYERS_FAIL_CLOSED:"
                    f"live_risk.max_open_positions={max_open_positions},"
                    f"bounded_live.limits.max_open_positions={bl_raw}"
                )
            parse_phase1_max_open_positions(bl_raw)

    payload = {
        "max_open_positions": max_open_positions,
        "enable_live_trading": enable_live_trading,
        "live_authorized": live_authorized,
        "orders_authorized": orders_authorized,
        "paper_execution_authorized": paper_execution_authorized,
        "testnet_authorized": testnet_authorized,
        "runtime_bridge_live_activated": runtime_bridge_live_activated,
        "multi_future_runtime_authorized": multi_future,
        "volatility_numeric_max_age_enforcement": vol_enforcement,
        "require_confirm_token": require_confirm_token,
        "config_path": resolved_path,
    }
    digest = _effective_digest(payload)
    return Phase1EffectiveConfigV1(
        max_open_positions=max_open_positions,
        enable_live_trading=enable_live_trading,
        live_authorized=live_authorized,
        orders_authorized=orders_authorized,
        paper_execution_authorized=paper_execution_authorized,
        testnet_authorized=testnet_authorized,
        runtime_bridge_live_activated=runtime_bridge_live_activated,
        multi_future_runtime_authorized=multi_future,
        volatility_numeric_max_age_enforcement=vol_enforcement,
        require_confirm_token=bool(require_confirm_token),
        config_path=resolved_path,
        precedence_layers=(
            "phase1_hard_safety_constants",
            "validated_cli_overrides",
            "peak_config_productive_toml",
            "missing_safety_defaults_false",
            "missing_max_open_positions_fail_closed",
        ),
        digest=digest,
    )


def reload_phase1_effective_config_preserves_digest(
    *,
    config_path: Optional[Path | str] = None,
) -> tuple[Phase1EffectiveConfigV1, Phase1EffectiveConfigV1]:
    first = resolve_phase1_effective_config(config_path=config_path)
    second = resolve_phase1_effective_config(config_path=config_path)
    if first.digest != second.digest:
        raise ConfigTruthAlignmentError("RESTART_RELOAD_DIGEST_MISMATCH_FAIL_CLOSED")
    return first, second


def phase1_aligned_live_risk_max_open_positions(cfg: PeakConfig) -> int:
    """Productive Phase-1 adapter over PeakConfig live_risk.max_open_positions."""
    return parse_phase1_max_open_positions(cfg.get("live_risk.max_open_positions", None))


def assert_historical_five_not_productive(cfg: PeakConfig) -> None:
    """Prove historical/test value 5 does not win on a Phase-1 productive config."""
    value = phase1_aligned_live_risk_max_open_positions(cfg)
    if value == 5:
        raise ConfigTruthAlignmentError("HISTORICAL_FIVE_REACHED_PRODUCTIVE_RUNTIME")
    if value != PHASE1_MAX_OPEN_POSITIONS:
        raise ConfigTruthAlignmentError(f"PHASE1_MAX_OPEN_POSITIONS_NOT_ONE:{value}")


def inventory_config_keys() -> tuple[ConfigKeyInventoryRowV1, ...]:
    return (
        ConfigKeyInventoryRowV1(
            config_key="max_open_positions",
            declaration_paths=(
                "config/config.toml:[live_risk]",
                "config/bounded_live.toml:[bounded_live.limits]",
                "src/live/risk_limits.py:LiveRiskLimits.from_config",
                "src/ops/config_truth_alignment_contract_v1.py:parse_phase1_max_open_positions",
            ),
            default_values=("1(config/config.toml)", "None(missing→legacy skip)"),
            override_paths=(
                "bounded_live.limits.max_open_positions",
                "PEAK_TRADE_CONFIG_PATH",
                "CLI live_risk.max_open_positions",
            ),
            environment_overrides=("PEAK_TRADE_CONFIG_PATH",),
            cli_overrides=("--config", "live_risk.max_open_positions"),
            test_fixture_values=("5(config/config.test.toml)", "2", "3", "10"),
            historical_values=("5(docstring example)", "10(root config.toml)"),
            productive_consumers=(
                "ops.config_truth_alignment_contract_v1",
                "live.risk_limits.LiveRiskLimits.from_config(PRODUCTIVE_LEGACY)",
            ),
            productive_entrypoints=(
                "scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py",
                "scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py",
                "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
            ),
            effective_precedence=(
                "phase1_parser(exact 1) > bounded_live.limits(if enabled) > "
                "live_risk.max_open_positions > missing fail-closed"
            ),
            missing_key_behavior="FAIL_CLOSED (no fallback to 5/None/unlimited)",
            invalid_value_behavior="FAIL_CLOSED reject <1 and >1 for Phase 1",
            fail_closed_behavior="ConfigTruthAlignmentError",
            runtime_effective_value="1",
            current_phase_expected_value="1",
            alignment_required=True,
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
        ),
        ConfigKeyInventoryRowV1(
            config_key="enable_live_trading",
            declaration_paths=(
                "config/config.toml:[environment]",
                "src/core/peak_config.py:_is_live_like_environment",
                "src/infra/escalation/network_gate.py",
            ),
            default_values=("false",),
            override_paths=("environment.enable_live_trading",),
            environment_overrides=("PEAK_TRADE_ENABLE_LIVE_TRADING",),
            cli_overrides=("environment.enable_live_trading",),
            test_fixture_values=("false", "true(negative tests)"),
            historical_values=(),
            productive_consumers=("ops.config_truth_alignment_contract_v1",),
            productive_entrypoints=(
                "scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py",
            ),
            effective_precedence="phase1 false hard reject of true > toml",
            missing_key_behavior="DEFAULT false",
            invalid_value_behavior="FAIL_CLOSED malformed bool",
            fail_closed_behavior="true rejected in Phase 1",
            runtime_effective_value="false",
            current_phase_expected_value="false",
            alignment_required=True,
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
        ),
        ConfigKeyInventoryRowV1(
            config_key="orders_authorized",
            declaration_paths=(
                "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/constants_v1.py",
                "config/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.toml",
            ),
            default_values=("false",),
            override_paths=(),
            environment_overrides=("PEAK_TRADE_ORDERS_AUTHORIZED",),
            cli_overrides=("orders_authorized",),
            test_fixture_values=("false",),
            historical_values=(),
            productive_consumers=(
                "wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1",
            ),
            productive_entrypoints=(
                "scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py",
            ),
            effective_precedence="package constant False (TOML documentary)",
            missing_key_behavior="DEFAULT false",
            invalid_value_behavior="true rejected",
            fail_closed_behavior="bridge refuses activation when true",
            runtime_effective_value="false",
            current_phase_expected_value="false",
            alignment_required=True,
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
        ),
        ConfigKeyInventoryRowV1(
            config_key="paper_execution_authorized",
            declaration_paths=(
                "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/constants_v1.py",
            ),
            default_values=("false",),
            override_paths=(),
            environment_overrides=("PEAK_TRADE_PAPER_EXECUTION_AUTHORIZED",),
            cli_overrides=("paper_execution_authorized",),
            test_fixture_values=("false",),
            historical_values=(),
            productive_consumers=(
                "wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1",
            ),
            productive_entrypoints=(
                "scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py",
            ),
            effective_precedence="package constant False",
            missing_key_behavior="DEFAULT false",
            invalid_value_behavior="true rejected",
            fail_closed_behavior="phase1 parser reject",
            runtime_effective_value="false",
            current_phase_expected_value="false",
            alignment_required=True,
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
        ),
        ConfigKeyInventoryRowV1(
            config_key="testnet_authorized",
            declaration_paths=(
                "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/constants_v1.py",
            ),
            default_values=("false",),
            override_paths=(),
            environment_overrides=("PEAK_TRADE_TESTNET_AUTHORIZED",),
            cli_overrides=("testnet_authorized",),
            test_fixture_values=("false",),
            historical_values=(),
            productive_consumers=(
                "wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1",
            ),
            productive_entrypoints=(
                "scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py",
            ),
            effective_precedence="package constant False",
            missing_key_behavior="DEFAULT false",
            invalid_value_behavior="true rejected",
            fail_closed_behavior="phase1 parser reject",
            runtime_effective_value="false",
            current_phase_expected_value="false",
            alignment_required=True,
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
        ),
        ConfigKeyInventoryRowV1(
            config_key="runtime_bridge_live_activated",
            declaration_paths=(
                "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/constants_v1.py",
            ),
            default_values=("false",),
            override_paths=(),
            environment_overrides=("PEAK_TRADE_RUNTIME_BRIDGE_LIVE_ACTIVATED",),
            cli_overrides=("runtime_bridge_live_activated",),
            test_fixture_values=("false",),
            historical_values=(),
            productive_consumers=(
                "wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1",
            ),
            productive_entrypoints=(
                "scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py",
            ),
            effective_precedence="package constant False → BOUND_NOT_ACTIVATED",
            missing_key_behavior="DEFAULT false",
            invalid_value_behavior="true rejected",
            fail_closed_behavior="phase1 parser reject",
            runtime_effective_value="false",
            current_phase_expected_value="false",
            alignment_required=True,
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
        ),
        ConfigKeyInventoryRowV1(
            config_key="live_authorized",
            declaration_paths=(
                "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/constants_v1.py",
            ),
            default_values=("false",),
            override_paths=(),
            environment_overrides=("PEAK_TRADE_LIVE_AUTHORIZED",),
            cli_overrides=("live_authorized",),
            test_fixture_values=("false",),
            historical_values=(),
            productive_consumers=(
                "wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1",
            ),
            productive_entrypoints=(
                "scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py",
            ),
            effective_precedence="package constant False",
            missing_key_behavior="DEFAULT false",
            invalid_value_behavior="true rejected",
            fail_closed_behavior="phase1 parser reject",
            runtime_effective_value="false",
            current_phase_expected_value="false",
            alignment_required=True,
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
        ),
        ConfigKeyInventoryRowV1(
            config_key="MULTI_FUTURE_RUNTIME_AUTHORIZED",
            declaration_paths=(
                "src/ops/config_truth_alignment_contract_v1.py",
                "docs/governance/PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md",
            ),
            default_values=("false",),
            override_paths=(),
            environment_overrides=(
                "MULTI_FUTURE_RUNTIME_AUTHORIZED",
                "PEAK_TRADE_MULTI_FUTURE_RUNTIME_AUTHORIZED",
            ),
            cli_overrides=("MULTI_FUTURE_RUNTIME_AUTHORIZED",),
            test_fixture_values=("false",),
            historical_values=(),
            productive_consumers=("ops.config_truth_alignment_contract_v1",),
            productive_entrypoints=(
                "scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py",
            ),
            effective_precedence="phase1 constant False (no productive multi-future host)",
            missing_key_behavior="DEFAULT false",
            invalid_value_behavior="true rejected",
            fail_closed_behavior="phase1 parser reject",
            runtime_effective_value="false",
            current_phase_expected_value="false",
            alignment_required=True,
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
        ),
        ConfigKeyInventoryRowV1(
            config_key="volatility_numeric_max_age_enforcement",
            declaration_paths=(
                "src/trading/master_v2/canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1.py",
                "src/ops/config_truth_alignment_contract_v1.py",
            ),
            default_values=("false/ENFORCEMENT_ENABLED=False",),
            override_paths=(),
            environment_overrides=(
                "PEAK_TRADE_VOLATILITY_NUMERIC_MAX_AGE_ENFORCEMENT",
                "VOLATILITY_NUMERIC_MAX_AGE_ENFORCEMENT",
            ),
            cli_overrides=("enforcement_enabled",),
            test_fixture_values=("false",),
            historical_values=(),
            productive_consumers=(
                "canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1",
            ),
            productive_entrypoints=(
                "scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py",
            ),
            effective_precedence="ENFORCEMENT_ENABLED=False constant; watchdog/research/diagnostic only",
            missing_key_behavior="DEFAULT false",
            invalid_value_behavior="true rejected",
            fail_closed_behavior="phase1 parser reject; no alpha/risk/safety enforcement derivation",
            runtime_effective_value="false",
            current_phase_expected_value="false",
            alignment_required=True,
            consumer_class=ConsumerClass.RESEARCH_ONLY.value,
        ),
        ConfigKeyInventoryRowV1(
            config_key="enforcement_enabled",
            declaration_paths=(
                "src/trading/master_v2/canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1.py",
            ),
            default_values=("false",),
            override_paths=(),
            environment_overrides=(),
            cli_overrides=("enforcement_enabled",),
            test_fixture_values=("false",),
            historical_values=(),
            productive_consumers=(
                "canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1",
            ),
            productive_entrypoints=(
                "scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py",
            ),
            effective_precedence="constant False",
            missing_key_behavior="DEFAULT false",
            invalid_value_behavior="true rejected",
            fail_closed_behavior="phase1 reject",
            runtime_effective_value="false",
            current_phase_expected_value="false",
            alignment_required=True,
            consumer_class=ConsumerClass.RESEARCH_ONLY.value,
        ),
        ConfigKeyInventoryRowV1(
            config_key="require_confirm_token",
            declaration_paths=("config/config.toml:[environment]",),
            default_values=("true",),
            override_paths=("environment.require_confirm_token",),
            environment_overrides=(),
            cli_overrides=(),
            test_fixture_values=("true",),
            historical_values=(),
            productive_consumers=("ops.config_truth_alignment_contract_v1",),
            productive_entrypoints=(
                "scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py",
            ),
            effective_precedence="toml > default true; confirm-token semantics not mutated",
            missing_key_behavior="DEFAULT true (documentary; semantics unchanged)",
            invalid_value_behavior="FAIL_CLOSED malformed bool",
            fail_closed_behavior="malformed rejected",
            runtime_effective_value="true",
            current_phase_expected_value="true",
            alignment_required=False,
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
        ),
    )


def consumer_traces() -> tuple[ConsumerTraceRowV1, ...]:
    return (
        ConsumerTraceRowV1(
            entrypoint="scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py",
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
            config_loader="package constants_v1 + ops TOML (documentary)",
            config_layer="bridge hard constants",
            override_precedence="constants > toml documentary",
            parsed_value_surface="ORDERS/TESTNET/LIVE/PAPER/RUNTIME_BRIDGE_LIVE=false",
            validator="ops.config_truth_alignment_contract_v1.resolve_phase1_effective_config",
            runtime_consumer="decision_economics_cycle_bridge_v1 (analytical only)",
            evidence="constants_v1.py RUNTIME_BRIDGE_LIVE_ACTIVATED=False",
        ),
        ConsumerTraceRowV1(
            entrypoint="scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py",
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
            config_loader="ops/integrated_paper_shadow_* toml + session constants",
            config_layer="IPSO gated observation",
            override_precedence="session auth artifacts > toml flags(false)",
            parsed_value_surface="orders/testnet/live/paper false",
            validator="ops.config_truth_alignment_contract_v1",
            runtime_consumer="integrated_paper_shadow_observation_wallclock_session_execution_v1",
            evidence="config/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1.toml",
        ),
        ConsumerTraceRowV1(
            entrypoint="scripts/ops/run_integrated_paper_shadow_productive_authorization_issuance_and_real_network_v1.py",
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
            config_loader="issuance helper toml",
            config_layer="issuance (merge≠session auth)",
            override_precedence="issuance flags false by default",
            parsed_value_surface="orders/testnet/paper false",
            validator="ops.config_truth_alignment_contract_v1",
            runtime_consumer="productive authorization issuance helper",
            evidence="AUTHORIZATION_CONSUMPTION not performed by this capability",
        ),
        ConsumerTraceRowV1(
            entrypoint="scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py",
            consumer_class=ConsumerClass.RESEARCH_ONLY.value,
            config_loader="max-age policy constants",
            config_layer="research/watchdog",
            override_precedence="ENFORCEMENT_ENABLED=False constant",
            parsed_value_surface="enforcement_enabled=false",
            validator="ops.config_truth_alignment_contract_v1",
            runtime_consumer="productive research evidence accumulation (non-enforcing)",
            evidence="WATCHDOG_ONLY/RESEARCH_ONLY/DIAGNOSTIC_ONLY; no alpha/risk/safety block",
        ),
        ConsumerTraceRowV1(
            entrypoint="src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
            config_loader="offline replay owner (no live risk TOML positions authority)",
            config_layer="offline decision",
            override_precedence="offline replay inputs; no live activation flags",
            parsed_value_surface="no max_open_positions live authority; safety via bridge/alignment",
            validator="ops.config_truth_alignment_contract_v1",
            runtime_consumer="integrated_offline_trading_logic_replay_v1",
            evidence="BOUND_NOT_ACTIVATED for live; offline analytical authority",
        ),
        ConsumerTraceRowV1(
            entrypoint="src/live/risk_limits.py:LiveRiskLimits.from_config",
            consumer_class=ConsumerClass.PRODUCTIVE_LEGACY.value,
            config_loader="PeakConfig.load_config / load_config_default",
            config_layer="live_risk + optional bounded_live.limits",
            override_precedence="bounded_live.limits > live_risk.* > missing→None (legacy skip)",
            parsed_value_surface="max_open_positions optional; Phase-1 adapter requires exact 1",
            validator="phase1_aligned_live_risk_max_open_positions (this contract)",
            runtime_consumer="legacy live/shadow/testnet scripts (not Phase-1 analytical bridge)",
            evidence=(
                "default config/config.toml already declares 1; missing→None is blocked for "
                "Phase-1 via this contract; root config.toml=10 classified HISTORICAL/LEGACY"
            ),
        ),
        ConsumerTraceRowV1(
            entrypoint="config.toml (repo root) live_risk.max_open_positions=10",
            consumer_class=ConsumerClass.HISTORICAL.value,
            config_loader="ConfigRegistry FALLBACK only if config/config.toml missing",
            config_layer="legacy fallback",
            override_precedence="blocked as Phase-1 authority",
            parsed_value_surface="10 (historical)",
            validator="assert_phase1_config_path_allowed",
            runtime_consumer="none for Phase-1 productive path",
            evidence="PeakConfig default is config/config.toml; root fallback blocked",
        ),
        ConsumerTraceRowV1(
            entrypoint="config/config.test.toml max_open_positions=5",
            consumer_class=ConsumerClass.TEST_ONLY.value,
            config_loader="explicit test harness paths",
            config_layer="test fixture",
            override_precedence="blocked as Phase-1 authority",
            parsed_value_surface="5 (test-only)",
            validator="assert_phase1_config_path_allowed",
            runtime_consumer="pytest fixtures only",
            evidence="TEST_ONLY_CONFIG_BLOCKED",
        ),
        ConsumerTraceRowV1(
            entrypoint="universe/ranking/selection startup paths",
            consumer_class=ConsumerClass.DEAD_OR_UNREACHABLE.value,
            config_loader="n/a — ranking/selection trading authority still false",
            config_layer="not trading authority",
            override_precedence="n/a",
            parsed_value_surface="no Phase-1 ranking/selection trading authority consumption",
            validator="Truth Map / feature state",
            runtime_consumer="none as ranking/selection trading authority",
            evidence="UNIVERSE_RANKING_TRADING_AUTHORITY=false",
        ),
        ConsumerTraceRowV1(
            entrypoint="governed futures universe producer paths",
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
            config_loader="ops.governed_futures_universe_producer_v1",
            config_layer="productive universe truth (Capability 2.1)",
            override_precedence="universe snapshot only; no ranking/selection/alpha",
            parsed_value_surface="venue=okx_eea; futures_only; btc_excluded; ALPHA_ALLOWED=false",
            validator="run_governed_futures_universe_producer_v1",
            runtime_consumer="scripts/ops/run_governed_futures_universe_producer_v1.py",
            evidence="CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1",
        ),
        ConsumerTraceRowV1(
            entrypoint="reconciliation-related startup paths",
            consumer_class=ConsumerClass.PRODUCTIVE_CANONICAL.value,
            config_loader="ops.productive_reconciliation_runtime_binding_v1",
            config_layer="productive runtime binding (Capability 1.1)",
            override_precedence="startup gate before first decision cycle",
            parsed_value_surface="PRODUCTIVE_RECONCILIATION_BOUND=true; alpha only on MATCH/verified recovery",
            validator="run_productive_reconciliation_startup_gate_v1",
            runtime_consumer=(
                "wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
            ),
            evidence="CAPABILITY_1_1_PRODUCTIVE_RECONCILIATION_RUNTIME_BINDING_V1",
        ),
    )


def build_config_truth_alignment_report_v1(
    *,
    config_path: Optional[Path | str] = None,
) -> ConfigTruthAlignmentReportV1:
    effective = resolve_phase1_effective_config(config_path=config_path)
    return ConfigTruthAlignmentReportV1(
        capability_id=CAPABILITY_ID,
        schema_version=SCHEMA_VERSION,
        activation_state=ACTIVATION_STATE,
        core_logic_change=CORE_LOGIC_CHANGE,
        effective=effective,
        key_inventory=inventory_config_keys(),
        consumer_traces=consumer_traces(),
        permissive_fallbacks_found=(
            "live.risk_limits.from_config:missing_max_open_positions→None(skip_check)",
            "docstring_example_max_open_positions=5(not_code_default)",
            "root_config.toml_live_risk.max_open_positions=10(legacy_fallback_path)",
            "config.test.toml_max_open_positions=5(test_only)",
        ),
        permissive_fallbacks_removed_or_blocked=(
            "phase1_parser_missing_fail_closed",
            "phase1_parser_rejects_gt_one_including_5_and_10",
            "legacy_root_config_blocked_as_phase1_authority",
            "test_only_config_blocked_as_phase1_authority",
            "env_true_safety_overrides_fail_closed",
            "cli_true_safety_overrides_fail_closed",
        ),
        legacy_parallel_authority_found=(
            "root_config.toml",
            "LiveRiskLimits.from_config missing→None skip",
        ),
        legacy_parallel_authority_blocked=(
            "assert_phase1_config_path_allowed",
            "phase1_aligned_live_risk_max_open_positions",
        ),
        notes=(
            "Numeric max-age remains WATCHDOG_ONLY/RESEARCH_ONLY/DIAGNOSTIC_ONLY",
            "MULTI_FUTURE_RUNTIME_AUTHORIZED=false",
            "BOUND_NOT_ACTIVATED preserved",
            "CORE_LOGIC_CHANGE=false",
        ),
    )


def report_to_dict(report: ConfigTruthAlignmentReportV1) -> dict[str, Any]:
    return asdict(report)


__all__ = (
    "ACTIVATION_STATE",
    "CAPABILITY_ID",
    "CORE_LOGIC_CHANGE",
    "ConfigTruthAlignmentError",
    "ConfigTruthAlignmentReportV1",
    "ConsumerClass",
    "DIAGNOSTIC_ONLY",
    "ENFORCEMENT_ENABLED",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "PHASE1_MAX_OPEN_POSITIONS",
    "Phase1EffectiveConfigV1",
    "RESEARCH_ONLY",
    "SCHEMA_VERSION",
    "VOLATILITY_NUMERIC_MAX_AGE_ENFORCEMENT",
    "WATCHDOG_ONLY",
    "assert_historical_five_not_productive",
    "assert_phase1_config_path_allowed",
    "build_config_truth_alignment_report_v1",
    "consumer_traces",
    "inventory_config_keys",
    "parse_phase1_max_open_positions",
    "parse_phase1_safety_flag_false",
    "phase1_aligned_live_risk_max_open_positions",
    "reload_phase1_effective_config_preserves_digest",
    "report_to_dict",
    "resolve_phase1_effective_config",
)
