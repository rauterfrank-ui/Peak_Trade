#!/usr/bin/env python3
"""
Peak_Trade – Phase 16L: Report Path Utilities

Provides robust, Docker-friendly path resolution for reports output.
Respects ENV PEAK_REPORTS_DIR for container/CI use cases.
"""

from __future__ import annotations

import os
from pathlib import Path


def get_repo_root() -> Path:
    """
    Find repo root by searching up from this file for pyproject.toml.
    Fallback: assume this file is at src/utils/report_paths.py -> 2 levels up.
    """
    current = Path(__file__).resolve().parent
    # Search upward for markers
    for parent in [current, *list(current.parents)]:
        if (parent / "pyproject.toml").exists():
            return parent
        if (parent / "uv.lock").exists():
            return parent
        if (parent / ".git").is_dir():
            return parent
    # Fallback: assume src/utils/report_paths.py structure
    return current.parent.parent


def get_reports_root(default_rel: str = "reports") -> Path:
    """
    Determine the reports root directory.

    Priority:
    1. ENV PEAK_REPORTS_DIR (absolute or relative to repo root)
    2. default_rel relative to repo root

    Args:
        default_rel: Default relative path from repo root (e.g. "reports")

    Returns:
        Absolute Path to reports root
    """
    repo_root = get_repo_root()

    env_override = os.environ.get("PEAK_REPORTS_DIR", "").strip()
    if env_override:
        p = Path(env_override)
        if p.is_absolute():
            return p
        else:
            return (repo_root / p).resolve()

    return (repo_root / default_rel).resolve()


def ensure_dir(p: Path) -> Path:
    """
    Ensure directory exists (mkdir -p equivalent).

    Args:
        p: Path to create

    Returns:
        The same Path (for chaining)
    """
    p.mkdir(parents=True, exist_ok=True)
    return p
