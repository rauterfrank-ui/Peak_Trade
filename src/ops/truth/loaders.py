"""
YAML loaders for docs truth map and repo truth claims.

Both configs are plain YAML; structure is validated minimally for deterministic use.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


def require_yaml() -> Any:
    if yaml is None:
        raise RuntimeError("PyYAML is required (pip install pyyaml).")
    return yaml


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML file; root must be a mapping."""
    y = require_yaml()
    raw = path.read_text(encoding="utf-8")
    data = y.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping.")
    return data


def load_docs_truth_map(path: Path) -> dict[str, Any]:
    """Load `config/ops/docs_truth_map.yaml` (rules list, version)."""
    return load_yaml_file(path)


def load_repo_truth_claims(path: Path) -> dict[str, Any]:
    """Load `config/ops/repo_truth_claims.yaml` (claims list, version)."""
    return load_yaml_file(path)
