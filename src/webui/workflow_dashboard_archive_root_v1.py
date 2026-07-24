"""Canonical durable archive-root contract for Workflow/Market Dashboard.

Sole owner of archive-root *location* resolution for dashboard consumers.
Does not create directories, does not write readmodels, and does not authorize
trading. GET /market consumers may resolve this root (explicit → Env →
canonical default) to read-only-load universe_selection_readmodel.v1.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path

CONTRACT_ID = "workflow_dashboard_archive_root_v1"
CONTRACT_SCHEMA_VERSION = 1
CONFIG_CONTRACT_RELATIVE_PATH = "config/webui/workflow_dashboard_archive_root_v1.json"
ENV_ARCHIVE_ROOT = "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT"

OWNER_MODULE = "src.webui.workflow_dashboard_archive_root_v1"
OWNER_SYMBOL = "resolve_workflow_dashboard_archive_root"

DEFAULT_APP_DIRNAME = "Peak_Trade"
DEFAULT_ARCHIVE_LEAF = "workflow_dashboard_v1"
LINUX_APP_DIRNAME = "peak_trade"

PRECEDENCE_EXPLICIT = "explicit_injection"
PRECEDENCE_ENV = "environment_override"
PRECEDENCE_DEFAULT = "canonical_default"
PRECEDENCE_CHAIN: tuple[str, ...] = (
    PRECEDENCE_EXPLICIT,
    PRECEDENCE_ENV,
    PRECEDENCE_DEFAULT,
)


class WorkflowDashboardArchiveRootError(ValueError):
    """Fail-closed archive-root contract error."""


def _repo_root() -> Path:
    # src/webui/<module>.py → parents[2] = repo root
    return Path(__file__).resolve().parents[2]


def _environ_map(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    return os.environ if environ is None else environ


def _platform_name(platform: str | None) -> str:
    return sys.platform if platform is None else platform


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _tmp_roots() -> tuple[Path, ...]:
    """POSIX ephemeral roots that must not host the canonical default.

    Intentionally excludes process TMPDIR/TMP (often /var/folders on macOS),
    which is not the dashboard default convention and would break isolated tests.
    """
    roots: list[Path] = []
    for raw in ("/tmp", "/var/tmp"):
        p = Path(raw)
        try:
            if p.exists():
                roots.append(p.resolve())
            else:
                roots.append(p)
        except OSError:
            roots.append(p)
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root)
        if key not in seen:
            out.append(root)
            seen.add(key)
    return tuple(out)


def _path_is_under_tmp(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path.absolute()
    resolved_posix = resolved.as_posix()
    for tmp_root in _tmp_roots():
        tmp_posix = tmp_root.as_posix().rstrip("/")
        if resolved_posix == tmp_posix or resolved_posix.startswith(tmp_posix + "/"):
            return True
    return False


def _assert_default_path_safe(path: Path, *, repo_root: Path) -> Path:
    if not path.is_absolute():
        raise WorkflowDashboardArchiveRootError("DEFAULT_ARCHIVE_ROOT_NOT_ABSOLUTE")
    if path == Path(path.anchor):
        raise WorkflowDashboardArchiveRootError("DEFAULT_ARCHIVE_ROOT_IS_FILESYSTEM_ROOT")
    if path == Path.home().resolve():
        raise WorkflowDashboardArchiveRootError("DEFAULT_ARCHIVE_ROOT_IS_HOME_DIRECTORY")
    if _is_under(path, repo_root) or path == repo_root.resolve():
        raise WorkflowDashboardArchiveRootError("DEFAULT_ARCHIVE_ROOT_INSIDE_GIT_REPO")
    if _is_under(path, repo_root / "tests" / "fixtures"):
        raise WorkflowDashboardArchiveRootError("DEFAULT_ARCHIVE_ROOT_IS_FIXTURE_PATH")
    if _path_is_under_tmp(path):
        raise WorkflowDashboardArchiveRootError("DEFAULT_ARCHIVE_ROOT_UNDER_TMP")
    return path


def canonical_default_workflow_dashboard_archive_root(
    *,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
    platform: str | None = None,
    repo_root: Path | None = None,
) -> Path:
    """Return the deterministic canonical default archive root (absolute).

    Never creates filesystem entries. Never selects fixtures, /tmp, or the
    repository working tree. Independent of the process cwd.
    """
    env_map = _environ_map(environ)
    plat = _platform_name(platform)
    home_path = (Path.home() if home is None else Path(home)).expanduser()
    if not home_path.is_absolute():
        raise WorkflowDashboardArchiveRootError("HOME_NOT_ABSOLUTE")
    home_path = home_path.resolve()
    repo = (_repo_root() if repo_root is None else Path(repo_root)).resolve()

    if plat == "darwin":
        candidate = (
            home_path
            / "Library"
            / "Application Support"
            / DEFAULT_APP_DIRNAME
            / DEFAULT_ARCHIVE_LEAF
        )
    elif plat.startswith("linux"):
        xdg = str(env_map.get("XDG_STATE_HOME", "") or "").strip()
        if xdg:
            state_home = Path(xdg).expanduser()
            if not state_home.is_absolute():
                state_home = (home_path / state_home).resolve()
            else:
                state_home = state_home.resolve()
            # Reject tmp-backed XDG_STATE_HOME for the canonical default.
            if _path_is_under_tmp(state_home):
                state_home = home_path / ".local" / "state"
        else:
            state_home = home_path / ".local" / "state"
        candidate = state_home / LINUX_APP_DIRNAME / DEFAULT_ARCHIVE_LEAF
    elif plat.startswith("win"):
        local_app = str(env_map.get("LOCALAPPDATA", "") or "").strip()
        if local_app:
            base = Path(local_app).expanduser()
            if not base.is_absolute():
                raise WorkflowDashboardArchiveRootError("LOCALAPPDATA_NOT_ABSOLUTE")
            base = base.resolve()
        else:
            base = home_path / "AppData" / "Local"
        candidate = base / DEFAULT_APP_DIRNAME / DEFAULT_ARCHIVE_LEAF
    else:
        # Fail-closed portable fallback: user state under home, never repo/tmp.
        candidate = home_path / ".local" / "state" / LINUX_APP_DIRNAME / DEFAULT_ARCHIVE_LEAF

    return _assert_default_path_safe(candidate.resolve(), repo_root=repo)


def _normalize_injected_or_env_path(raw: str) -> Path:
    text = raw.strip()
    if not text:
        raise WorkflowDashboardArchiveRootError("ARCHIVE_ROOT_EMPTY")
    path = Path(text).expanduser()
    if not path.is_absolute():
        # Preserve historical Env/CLI behavior: resolve relative to cwd.
        path = path.resolve()
    else:
        path = path.resolve()
    if path == Path(path.anchor):
        raise WorkflowDashboardArchiveRootError("ARCHIVE_ROOT_IS_FILESYSTEM_ROOT")
    return path


def resolve_workflow_dashboard_archive_root(
    *,
    explicit: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    platform: str | None = None,
    repo_root: Path | None = None,
    require_existing_directory: bool = True,
) -> Path | None:
    """Resolve durable Workflow Dashboard archive root.

    Precedence:
      1. explicit injection
      2. PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT
      3. canonical platform-aware default

    When ``require_existing_directory`` is True (consumer default), a candidate
    that is missing or not a directory yields ``None``. This preserves existing
    unconfigured / MISSING_SOURCE semantics until an operator or writer creates
    the directory. Resolution itself never creates filesystem entries.
    """
    env_map = _environ_map(environ)
    source_raw: str | None = None
    source_kind: str | None = None

    if explicit is not None:
        source_raw = str(explicit).strip()
        source_kind = PRECEDENCE_EXPLICIT
        if not source_raw:
            raise WorkflowDashboardArchiveRootError("EXPLICIT_ARCHIVE_ROOT_EMPTY")
    else:
        env_raw = str(env_map.get(ENV_ARCHIVE_ROOT, "") or "").strip()
        if env_raw:
            source_raw = env_raw
            source_kind = PRECEDENCE_ENV

    if source_raw is not None:
        try:
            candidate = _normalize_injected_or_env_path(source_raw)
        except WorkflowDashboardArchiveRootError:
            if source_kind == PRECEDENCE_EXPLICIT:
                raise
            # Env override with invalid shape: fail soft to None (historic runtime).
            return None
    else:
        candidate = canonical_default_workflow_dashboard_archive_root(
            home=home,
            environ=env_map,
            platform=platform,
            repo_root=repo_root,
        )

    if require_existing_directory:
        if not candidate.is_dir():
            return None
        return candidate.resolve()
    return candidate.resolve()


__all__ = [
    "CONFIG_CONTRACT_RELATIVE_PATH",
    "CONTRACT_ID",
    "CONTRACT_SCHEMA_VERSION",
    "ENV_ARCHIVE_ROOT",
    "OWNER_MODULE",
    "OWNER_SYMBOL",
    "PRECEDENCE_CHAIN",
    "WorkflowDashboardArchiveRootError",
    "canonical_default_workflow_dashboard_archive_root",
    "resolve_workflow_dashboard_archive_root",
]
