"""WP-A6 negative/quarantine regression for Health/Resilience.

Protects the already-adjudicated D6 path:

    OWNER_DECISION_D6_RATE_LIMITER=REUSE_EXISTING_SRC_CORE_RATE_LIMITER_SSOT
    OWNER_DECISION_D6_DOMAIN_PROBES=NO_NEW_DOMAIN_PROBES_WITHOUT_PERSISTED_EVIDENCE
    A6_HIST_BODY_REQUIRED_FOR_ADAPT=false

This module is tests-only quarantine. It does not revive historical
src/infra/health or src/infra/resilience. It does not port historical
bodies. It does not prove SAME_AS / replacement / semantic parity
between historical packages and current namesakes.

Health/Resilience remain infrastructure, not trading/activation/live
authority. This module does not invent an execution-guard set.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CURRENT_HEALTHCHECK_SSOT_REL = "src/core/resilience.py"
CURRENT_RATELIMITER_SSOT_REL = "src/core/rate_limiter.py"
CURRENT_RESILIENCE_HELPERS_REL = "src/core/resilience_helpers.py"

HIST_INFRA_HEALTH_ROOT = "src/infra/health"
HIST_INFRA_RESILIENCE_ROOT = "src/infra/resilience"

# Historical revival surfaces bound by WN-HIST-INFRA-HEALTH / WN-HIST-INFRA-RESILIENCE.
# Absence only. Not a SAME_AS claim versus current namesakes.
HIST_HEALTH_REVIVAL_PATHS: tuple[str, ...] = (
    "src/infra/health",
    "src/infra/health.py",
    "src/infra/health/__init__.py",
    "src/infra/health/health_checker.py",
    "src/infra/health/checks/__init__.py",
    "src/infra/health/checks/base_check.py",
    "src/infra/health/checks/backtest_check.py",
    "src/infra/health/checks/exchange_check.py",
    "src/infra/health/checks/live_check.py",
    "src/infra/health/checks/portfolio_check.py",
    "src/infra/health/checks/risk_check.py",
)
HIST_RESILIENCE_REVIVAL_PATHS: tuple[str, ...] = (
    "src/infra/resilience",
    "src/infra/resilience.py",
    "src/infra/resilience/__init__.py",
    "src/infra/resilience/circuit_breaker.py",
    "src/infra/resilience/fallback.py",
    "src/infra/resilience/rate_limiter.py",
    "src/infra/resilience/retry.py",
)

# Required non-claims. Do not invert these in this surface.
HIST_CURRENT_IDENTITY_PROVEN = False
HIST_INFRA_HEALTH_SAME_AS_CORE_RESILIENCE = False
HIST_INFRA_RESILIENCE_SAME_AS_CORE_RESILIENCE = False
HIST_RATELIMITER_SAME_AS_CURRENT_RATELIMITER = False
HIST_HEALTHCHECKER_SAME_AS_KILL_SWITCH_HEALTHCHECKER = False
SEMANTIC_PARITY_PROVEN = False
SUPERSEDED = False
A6_HIST_BODY_REQUIRED_FOR_ADAPT = False
SELF_LEARNING_TOPOLOGY = "OPEN_NOT_YET_ADJUDICATED"
SELF_LEARNING_TOPOLOGY_ASSUMED = False

_ENABLE_LIVE_HEALTH_GATE_NAMES: frozenset[str] = frozenset(
    {
        "enable_live_trading",
        "enable_live",
        "LIVE_ENABLED",
        "LIVE_ARMED",
        "LIVE_AUTHORIZED",
    }
)


def _repo_path(rel: str) -> Path:
    return REPO_ROOT / rel


def _parse(rel: str) -> ast.AST:
    return ast.parse(_repo_path(rel).read_text(encoding="utf-8"))


def _iter_src_python_files() -> tuple[Path, ...]:
    src_root = REPO_ROOT / "src"
    return tuple(sorted(path for path in src_root.rglob("*.py") if "__pycache__" not in path.parts))


def _class_names(tree: ast.AST) -> tuple[str, ...]:
    return tuple(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))


def _function_names(tree: ast.AST) -> tuple[str, ...]:
    return tuple(node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))


def _class_def(tree: ast.AST, name: str) -> ast.ClassDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _resolve_import_from(path: Path, node: ast.ImportFrom) -> str | None:
    rel_parts = path.resolve().relative_to(REPO_ROOT).with_suffix("").parts
    if rel_parts[-1] == "__init__":
        package_parts = list(rel_parts[:-1])
    else:
        package_parts = list(rel_parts[:-1])
    if node.level == 0:
        return node.module
    base = package_parts
    for _ in range(node.level - 1):
        if not base:
            return None
        base = base[:-1]
    if node.module:
        base = [*base, *node.module.split(".")]
    return ".".join(base)


def _imported_rate_limiter_modules(path: Path, tree: ast.AST) -> tuple[str, ...]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "src.core.rate_limiter" or alias.name.endswith(".rate_limiter"):
                    hits.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            resolved = _resolve_import_from(path, node)
            names = {alias.name for alias in node.names}
            if "RateLimiter" not in names or not resolved:
                continue
            hits.append(resolved)
    return tuple(hits)


def _enable_live_health_gate_hits(tree: ast.AST) -> tuple[str, ...]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in _ENABLE_LIVE_HEALTH_GATE_NAMES:
            hits.append(node.id)
        elif isinstance(node, ast.Attribute) and node.attr in _ENABLE_LIVE_HEALTH_GATE_NAMES:
            hits.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in _ENABLE_LIVE_HEALTH_GATE_NAMES:
                hits.append(node.value)
        elif isinstance(node, ast.keyword) and node.arg in _ENABLE_LIVE_HEALTH_GATE_NAMES:
            hits.append(node.arg)
    return tuple(hits)


def test_wp_a6_does_not_normalize_historical_current_identity() -> None:
    assert HIST_CURRENT_IDENTITY_PROVEN is False
    assert HIST_INFRA_HEALTH_SAME_AS_CORE_RESILIENCE is False
    assert HIST_INFRA_RESILIENCE_SAME_AS_CORE_RESILIENCE is False
    assert HIST_RATELIMITER_SAME_AS_CURRENT_RATELIMITER is False
    assert HIST_HEALTHCHECKER_SAME_AS_KILL_SWITCH_HEALTHCHECKER is False
    assert SEMANTIC_PARITY_PROVEN is False
    assert SUPERSEDED is False
    assert A6_HIST_BODY_REQUIRED_FOR_ADAPT is False
    assert SELF_LEARNING_TOPOLOGY == "OPEN_NOT_YET_ADJUDICATED"
    assert SELF_LEARNING_TOPOLOGY_ASSUMED is False


def test_hist_infra_health_package_is_absent() -> None:
    for rel in HIST_HEALTH_REVIVAL_PATHS:
        assert not _repo_path(rel).exists(), (
            f"{rel} must remain absent (HIST_INFRA_HEALTH_REVIVED=false)"
        )
    src_infra = _repo_path("src/infra")
    if src_infra.is_dir():
        leftover = [
            str(path.relative_to(REPO_ROOT))
            for path in src_infra.rglob("*")
            if "health" in path.relative_to(src_infra).parts[:1]
        ]
        assert leftover == []


def test_hist_infra_resilience_package_is_absent() -> None:
    for rel in HIST_RESILIENCE_REVIVAL_PATHS:
        assert not _repo_path(rel).exists(), (
            f"{rel} must remain absent (HIST_INFRA_RESILIENCE_REVIVED=false)"
        )
    src_infra = _repo_path("src/infra")
    if src_infra.is_dir():
        leftover = [
            str(path.relative_to(REPO_ROOT))
            for path in src_infra.rglob("*")
            if "resilience" in path.relative_to(src_infra).parts[:1]
        ]
        assert leftover == []


def test_current_healthcheck_circuitbreaker_retry_ssot_is_resilience_py() -> None:
    tree = _parse(CURRENT_HEALTHCHECK_SSOT_REL)
    class_names = _class_names(tree)
    function_names = _function_names(tree)
    assert "HealthCheck" in class_names
    assert "HealthCheckResult" in class_names
    assert "CircuitBreaker" in class_names
    assert "retry_with_backoff" in function_names
    assert "RateLimiter" not in class_names
    assert "Fallback" not in class_names


def test_current_ratelimiter_ssot_is_src_core_rate_limiter_py() -> None:
    tree = _parse(CURRENT_RATELIMITER_SSOT_REL)
    assert "RateLimiter" in _class_names(tree)
    assert _class_def(tree, "RateLimiter") is not None


def test_resilience_helpers_import_current_ratelimiter_ssot() -> None:
    helpers_path = _repo_path(CURRENT_RESILIENCE_HELPERS_REL)
    tree = _parse(CURRENT_RESILIENCE_HELPERS_REL)
    imported = _imported_rate_limiter_modules(helpers_path, tree)
    assert imported == ("src.core.rate_limiter",)
    assert "src.infra.resilience.rate_limiter" not in imported
    assert "src.infra.resilience" not in imported


def test_no_class_fallback_under_productive_src() -> None:
    hits: list[str] = []
    for path in _iter_src_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "Fallback":
                hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []


def test_resilience_py_has_no_enable_live_health_gate_mechanism() -> None:
    tree = _parse(CURRENT_HEALTHCHECK_SSOT_REL)
    assert _enable_live_health_gate_hits(tree) == ()
    health_check = _class_def(tree, "HealthCheck")
    assert health_check is not None
    assert _enable_live_health_gate_hits(health_check) == ()


def test_healthcheck_ssot_is_not_bound_historical_live_gate() -> None:
    tree = _parse(CURRENT_HEALTHCHECK_SSOT_REL)
    health_check = _class_def(tree, "HealthCheck")
    assert health_check is not None
    method_names = tuple(
        node.name for node in health_check.body if isinstance(node, ast.FunctionDef)
    )
    assert "enable_live_trading" not in method_names
    assert "arm_live" not in method_names
    assert "authorize_live" not in method_names
    assert "set_live" not in method_names
    live_check = _class_def(tree, "LiveHealthCheck")
    assert live_check is None
    assert "LiveHealthCheck" not in _class_names(tree)
    assert "ExchangeHealthCheck" not in _class_names(tree)


def test_no_new_okx_no_order_domain_probe_is_required_by_this_surface() -> None:
    # D6 forbids inventing OKX/no-order domain probes. This surface therefore
    # only protects historical revival absence, and does not require a new probe.
    assert A6_HIST_BODY_REQUIRED_FOR_ADAPT is False
    assert not _repo_path("src/infra/health/checks/exchange_check.py").exists()
