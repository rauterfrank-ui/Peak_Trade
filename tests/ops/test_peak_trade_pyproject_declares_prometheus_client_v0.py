from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.9/3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]


REPO_ROOT = Path(__file__).resolve().parents[2]


def _normalize_dependency_name(requirement: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9_.-]+)", requirement)
    assert match is not None, f"Could not parse dependency requirement: {requirement!r}"
    return match.group(1).replace("_", "-").lower()


def test_peak_trade_pyproject_declares_prometheus_client_dependency_v0() -> None:
    pyproject_path = REPO_ROOT / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    dependencies = pyproject["project"]["dependencies"]

    prometheus_requirements = [
        requirement
        for requirement in dependencies
        if _normalize_dependency_name(requirement) == "prometheus-client"
    ]

    assert prometheus_requirements == ["prometheus-client>=0.19.0"]
