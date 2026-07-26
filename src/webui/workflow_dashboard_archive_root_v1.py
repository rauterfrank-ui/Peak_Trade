"""Canonical durable archive-root contract for Workflow/Market Dashboard.

Sole owner of archive-root *location* resolution for dashboard consumers.
Does not create directories, does not write readmodels, and does not authorize
trading. GET /market consumers may resolve this root (explicit → Env →
canonical default → discovered governed OKX sibling) to read-only-load
universe_selection_readmodel.v1 and okx_selected_instrument_ohlcv_readmodel.v1.
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
PRECEDENCE_DISCOVERED_GOVERNED_OKX = "discovered_governed_okx_archive"
PRECEDENCE_CHAIN: tuple[str, ...] = (
    PRECEDENCE_EXPLICIT,
    PRECEDENCE_ENV,
    PRECEDENCE_DEFAULT,
    PRECEDENCE_DISCOVERED_GOVERNED_OKX,
)

UNIVERSE_SELECTION_READMODEL_RELATIVE = "readmodels/universe_selection_readmodel.v1.json"
OKX_OHLCV_READMODEL_RELATIVE = "readmodels/okx_selected_instrument_ohlcv_readmodel.v1.json"
_DISCOVER_NAME_PREFIX = "workflow_dashboard_v1"


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


def _read_json_object(path: Path) -> dict[str, object] | None:
    import json

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    return raw if isinstance(raw, dict) else None


def _instrument_is_excluded_btc_or_spot(instrument_id: str, market_type: str) -> bool:
    symbol = instrument_id.strip().upper()
    mtype = market_type.strip().lower()
    if not symbol:
        return True
    if symbol.startswith("BTC-") or symbol == "BTC" or symbol.startswith("BTC/"):
        return True
    if mtype in {"spot", "cash"}:
        return True
    if "-SWAP" not in symbol and "PERPETUAL" not in mtype and mtype != "swap":
        # Futures-only: require SWAP / perpetual marker from persisted identity.
        return True
    return False


def archive_root_has_governed_okx_futures_readmodels(archive_root: Path) -> bool:
    """Return True when root holds authentic OKX USDT-perp identity + OHLCV.

    Read-only validation. Never creates paths. Rejects BTC/Spot/fixture-only.
    """
    root = Path(archive_root)
    universe_path = root / UNIVERSE_SELECTION_READMODEL_RELATIVE
    ohlcv_path = root / OKX_OHLCV_READMODEL_RELATIVE
    if not universe_path.is_file() or not ohlcv_path.is_file():
        return False
    universe = _read_json_object(universe_path)
    ohlcv = _read_json_object(ohlcv_path)
    if universe is None or ohlcv is None:
        return False
    if universe.get("schema_name") != "universe_selection_readmodel.v1":
        return False
    if ohlcv.get("schema_name") != "okx_selected_instrument_ohlcv_readmodel.v1":
        return False
    if ohlcv.get("fixture_only") is True or universe.get("fixture_marked") is True:
        return False
    venue = str(ohlcv.get("venue") or "").strip().lower()
    if venue != "okx":
        return False
    instrument_id = str(ohlcv.get("instrument_id") or "").strip()
    market_type = str(ohlcv.get("market_type") or "").strip()
    if _instrument_is_excluded_btc_or_spot(instrument_id, market_type):
        return False
    selected = universe.get("selected_future")
    if not isinstance(selected, dict):
        return False
    selected_symbol = str(selected.get("symbol") or "").strip()
    if not selected_symbol or selected_symbol.upper() != instrument_id.upper():
        return False
    bars = ohlcv.get("bars")
    bar_count = ohlcv.get("bar_count")
    has_bars = isinstance(bars, list) and len(bars) > 0
    has_count = isinstance(bar_count, int) and bar_count > 0
    return has_bars or has_count


def discover_governed_okx_workflow_dashboard_archive(
    *,
    search_parent: Path,
    exclude: Path | None = None,
) -> Path | None:
    """Discover newest eligible governed OKX archive under a durable parent.

    Never creates directories. Never selects repo/tmp/fixture roots. Returns None
    when no eligible sibling archive exists.
    """
    parent = Path(search_parent)
    try:
        if not parent.is_dir():
            return None
        if _path_is_under_tmp(parent):
            return None
    except OSError:
        return None

    exclude_resolved: Path | None = None
    if exclude is not None:
        try:
            exclude_resolved = Path(exclude).resolve()
        except OSError:
            exclude_resolved = Path(exclude)

    candidates: list[tuple[float, Path]] = []
    try:
        entries = list(parent.iterdir())
    except OSError:
        return None
    for entry in entries:
        try:
            if not entry.is_dir():
                continue
            name = entry.name
            if name != _DISCOVER_NAME_PREFIX and not name.startswith(_DISCOVER_NAME_PREFIX + "_"):
                continue
            resolved = entry.resolve()
            if exclude_resolved is not None and resolved == exclude_resolved:
                continue
            if _path_is_under_tmp(resolved):
                continue
            if not archive_root_has_governed_okx_futures_readmodels(resolved):
                continue
            ohlcv = resolved / OKX_OHLCV_READMODEL_RELATIVE
            mtime = ohlcv.stat().st_mtime
            candidates.append((mtime, resolved))
        except OSError:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


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
      3. canonical platform-aware default (when directory exists)
      4. discovered governed OKX archive sibling under the canonical parent
         (only when the canonical default directory is absent)

    When ``require_existing_directory`` is True (consumer default), a missing
    explicit/env path yields ``None``. Canonical-default absence may fall through
    to read-only sibling discovery. Resolution itself never creates filesystem
    entries and never fabricates market data.
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
        if require_existing_directory:
            if not candidate.is_dir():
                return None
            return candidate.resolve()
        return candidate.resolve()

    candidate = canonical_default_workflow_dashboard_archive_root(
        home=home,
        environ=env_map,
        platform=platform,
        repo_root=repo_root,
    )

    if not require_existing_directory:
        return candidate.resolve()

    if candidate.is_dir():
        return candidate.resolve()

    # Canonical leaf absent: discover governed OKX sibling under the same parent.
    discovered = discover_governed_okx_workflow_dashboard_archive(
        search_parent=candidate.parent,
        exclude=candidate,
    )
    if discovered is None:
        return None
    return discovered.resolve()


__all__ = [
    "CONFIG_CONTRACT_RELATIVE_PATH",
    "CONTRACT_ID",
    "CONTRACT_SCHEMA_VERSION",
    "ENV_ARCHIVE_ROOT",
    "OKX_OHLCV_READMODEL_RELATIVE",
    "OWNER_MODULE",
    "OWNER_SYMBOL",
    "PRECEDENCE_CHAIN",
    "PRECEDENCE_DISCOVERED_GOVERNED_OKX",
    "UNIVERSE_SELECTION_READMODEL_RELATIVE",
    "WorkflowDashboardArchiveRootError",
    "archive_root_has_governed_okx_futures_readmodels",
    "canonical_default_workflow_dashboard_archive_root",
    "discover_governed_okx_workflow_dashboard_archive",
    "resolve_workflow_dashboard_archive_root",
]
