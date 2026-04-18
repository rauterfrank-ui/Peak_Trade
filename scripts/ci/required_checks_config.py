"""Shared loader for required checks config semantics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _normalize_context_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise RuntimeError(f"{field_name} must be a list")
    return [str(item).strip() for item in value if str(item).strip()]


def load_effective_required_contexts(config_path: str | Path) -> list[str]:
    """Return required_contexts with ignored_contexts excluded, preserving order."""
    data = json.loads(Path(config_path).read_text(encoding="utf-8"))
    required = _normalize_context_list(data.get("required_contexts", []), "required_contexts")
    ignored = set(_normalize_context_list(data.get("ignored_contexts", []), "ignored_contexts"))
    return [ctx for ctx in required if ctx not in ignored]
