"""Shared loader for required checks config semantics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _normalize_context_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise RuntimeError(f"{field_name} must be a list")
    return [str(item).strip() for item in value if str(item).strip()]


def load_required_checks_config(config_path: str | Path) -> dict[str, list[str]]:
    """
    Return canonical required-check semantics from JSON config.

    The result always contains:
      - required_contexts
      - ignored_contexts
      - effective_required_contexts (= required_contexts - ignored_contexts)
    """
    data = json.loads(Path(config_path).read_text(encoding="utf-8"))
    required = _normalize_context_list(data.get("required_contexts", []), "required_contexts")
    ignored = _normalize_context_list(data.get("ignored_contexts", []), "ignored_contexts")
    ignored_set = set(ignored)
    effective = [ctx for ctx in required if ctx not in ignored_set]
    return {
        "required_contexts": required,
        "ignored_contexts": ignored,
        "effective_required_contexts": effective,
    }


def load_effective_required_contexts(config_path: str | Path) -> list[str]:
    """Return required_contexts with ignored_contexts excluded, preserving order."""
    return load_required_checks_config(config_path)["effective_required_contexts"]
