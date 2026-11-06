"""Dependency-bound contract: prometheus-client declared and usable by src/core/metrics.py."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

from src.core.metrics import PROMETHEUS_AVAILABLE, MetricsCollector

REPO_ROOT = Path(__file__).resolve().parents[2]
_NS = "peak_trade_prometheus_dependency_bound_contract_v0"


def _normalize_dependency_name(requirement: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9_.-]+)", requirement)
    assert match is not None, f"Could not parse dependency requirement: {requirement!r}"
    return match.group(1).replace("_", "-").lower()


def test_prometheus_client_dependency_bound_in_pyproject_v0() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = pyproject["project"]["dependencies"]
    prometheus = [d for d in deps if _normalize_dependency_name(d) == "prometheus-client"]
    assert prometheus, "prometheus-client must be declared in pyproject.toml"
    assert any(">=" in req for req in prometheus)


def test_prometheus_client_importable_in_project_environment_v0() -> None:
    assert importlib.util.find_spec("prometheus_client") is not None


def test_metrics_collector_uses_bound_prometheus_client_without_drift_v0() -> None:
    assert PROMETHEUS_AVAILABLE is True
    body, content_type = MetricsCollector(namespace=_NS).export_prometheus()
    assert isinstance(content_type, str)
    raw = body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body
    assert _NS in raw
    assert len(raw) > 0
