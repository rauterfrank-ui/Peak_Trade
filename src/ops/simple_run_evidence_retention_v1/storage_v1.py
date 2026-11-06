"""Owner run evidence storage root (local home default; fail-closed)."""

from __future__ import annotations

import os
from pathlib import Path

from .constants_v1 import (
    ENV_OWNER_RUN_EVIDENCE_ROOT,
    OWNER_HOME_DIR_NAME,
    OWNER_INDEX_DIRNAME,
    OWNER_INDEX_FILENAME,
    OWNER_RUNS_DIRNAME,
)


class OwnerRunEvidenceRootError(RuntimeError):
    """Owner storage root could not be resolved (fail-closed)."""


def _absolute_owner_root_path(raw: str) -> Path:
    candidate = Path(raw.strip()).expanduser()
    if not candidate.is_absolute():
        raise OwnerRunEvidenceRootError(
            "OWNER_RUN_EVIDENCE_ROOT_RELATIVE_FORBIDDEN: path must be absolute"
        )
    return candidate.resolve()


def resolve_home_directory(*, env: dict[str, str] | None = None) -> Path:
    """Resolve the current user home directory. No fallback to archive or /tmp."""
    _ = env  # reserved; Path.home() is OS-defined
    try:
        home = Path.home()
    except (RuntimeError, OSError) as exc:
        raise OwnerRunEvidenceRootError(
            "OWNER_RUN_EVIDENCE_HOME_UNRESOLVED: Path.home() failed"
        ) from exc
    if not home.is_absolute():
        raise OwnerRunEvidenceRootError(
            "OWNER_RUN_EVIDENCE_HOME_UNRESOLVED: home path is not absolute"
        )
    return home.resolve()


def resolve_owner_run_evidence_root(
    *,
    env: dict[str, str] | None = None,
    explicit: str | Path | None = None,
) -> Path:
    """Resolve owner run evidence root for this layer only.

    Precedence:
    1. ``explicit`` argument (CLI/testing)
    2. ``PEAK_TRADE_OWNER_RUN_EVIDENCE_ROOT``
    3. ``Path.home() / Peak_Trade_Run_Evidence``

    Never uses ``PEAK_TRADE_DATA_ARCHIVE_ROOT``.
    """
    env_map = env if env is not None else os.environ
    if explicit is not None:
        raw_explicit = str(explicit).strip()
        if raw_explicit:
            return _absolute_owner_root_path(raw_explicit)

    override = str(env_map.get(ENV_OWNER_RUN_EVIDENCE_ROOT, "") or "").strip()
    if override:
        return _absolute_owner_root_path(override)

    home = resolve_home_directory(env=env_map)
    return (home / OWNER_HOME_DIR_NAME).resolve()


def owner_runs_root(
    *,
    env: dict[str, str] | None = None,
    explicit: str | Path | None = None,
) -> Path:
    root = resolve_owner_run_evidence_root(env=env, explicit=explicit)
    return root / OWNER_RUNS_DIRNAME


def default_owner_index_path(
    *,
    env: dict[str, str] | None = None,
    explicit: str | Path | None = None,
) -> Path:
    root = resolve_owner_run_evidence_root(env=env, explicit=explicit)
    return root / OWNER_INDEX_DIRNAME / OWNER_INDEX_FILENAME
