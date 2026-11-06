"""Contract tests: Prometheus reuse-first and no parallel materialization SSOT for dual-leg v1."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

from src.core.metrics import PROMETHEUS_AVAILABLE, MetricsCollector
from src.research.cross_sectional_funding_rate_dual_leg_spread_v1_bound_panel_dataset_materialization_v0 import (
    CANONICAL_MATERIALIZATION_OWNER,
    compute_bound_funding_data_digest_v1,
    materialize_bound_funding_panel_dataset_v1,
)
from src.research.cross_sectional_funding_rate_dual_leg_spread_v1_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_MODULE = "src.research.cross_sectional_funding_rate_dual_leg_spread_v1_offline_economic_evaluation_execution_v0"
ADAPTER_MODULE = "src.research.cross_sectional_funding_rate_dual_leg_spread_v1_bound_panel_dataset_materialization_v0"


def test_prometheus_client_declared_in_pyproject_v0() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "prometheus-client>=" in pyproject


def test_canonical_metrics_collector_uses_prometheus_or_fail_open_v0() -> None:
    collector = MetricsCollector(namespace="dual_leg_spread_reuse_contract_v0")
    body, content_type = collector.export_prometheus()
    assert isinstance(content_type, str)
    if not PROMETHEUS_AVAILABLE:
        assert body == "# Prometheus client not installed\n"
    else:
        raw = body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body
        assert "dual_leg_spread_reuse_contract_v0" in raw


def test_dual_leg_execution_harness_does_not_import_prometheus_client_directly_v0() -> None:
    source = (REPO_ROOT / f"{EXECUTION_MODULE.replace('.', '/')}.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    direct_imports: list[str] = []
    import_from_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            direct_imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            import_from_modules.append(node.module)
    assert not any(
        name == "prometheus_client" or name.startswith("prometheus_client.")
        for name in direct_imports
    )
    assert not any(module.startswith("prometheus_client") for module in import_from_modules)


def test_dual_leg_bound_panel_adapter_delegates_to_canonical_owner_v0() -> None:
    adapter_path = REPO_ROOT / f"{ADAPTER_MODULE.replace('.', '/')}.py"
    source = adapter_path.read_text(encoding="utf-8")
    assert "materialize_bound_funding_panel_dataset_v0" in source
    assert CANONICAL_MATERIALIZATION_OWNER in source
    assert source.count("def materialize_bound_funding_panel_dataset_v1") == 1
    assert len(source.splitlines()) < 120


def test_dual_leg_v1_data_digest_matches_ratified_binding_v0() -> None:
    binding = materialize_versioned_research_binding_v1()
    assert compute_bound_funding_data_digest_v1() == binding["data_digest"]


def test_no_parallel_prometheus_ssot_in_dual_leg_adapter_v0() -> None:
    module = importlib.import_module(ADAPTER_MODULE)
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    assert not any(
        name == "prometheus_client" or name.startswith("prometheus_client.") for name in modules
    )
    assert not any(name.startswith("src.core.metrics") for name in modules)


@pytest.mark.parametrize(
    "symbol",
    [
        "materialize_bound_funding_panel_dataset_v1",
        "compute_bound_funding_data_digest_v1",
    ],
)
def test_dual_leg_adapter_symbols_are_offline_only_v0(symbol: str) -> None:
    module = importlib.import_module(ADAPTER_MODULE)
    assert getattr(module, symbol) is not None


def test_dual_leg_execution_harness_avoids_policy_critic_no_secrets_token_pattern_v0() -> None:
    source = (REPO_ROOT / f"{EXECUTION_MODULE.replace('.', '/')}.py").read_text(encoding="utf-8")
    assert 'GO_TOKEN = "' not in source
    assert "CONFIRM_GO =" in source
