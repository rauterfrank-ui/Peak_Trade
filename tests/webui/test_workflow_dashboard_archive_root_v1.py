"""Contract tests for Workflow Dashboard archive-root v1."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    REASON_ARCHIVE_ROOT_UNSET,
    REASON_UNIVERSE_ABSENT,
    bind_market_universe_slots,
)
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_archive_root_v1 import (
    CONFIG_CONTRACT_RELATIVE_PATH,
    CONTRACT_ID,
    ENV_ARCHIVE_ROOT,
    OWNER_MODULE,
    OWNER_SYMBOL,
    PRECEDENCE_CHAIN,
    WorkflowDashboardArchiveRootError,
    canonical_default_workflow_dashboard_archive_root,
    resolve_workflow_dashboard_archive_root,
)
from src.webui.workflow_dashboard_runtime_v1 import (
    ENV_ENABLED,
    build_workflow_dashboard_display_context,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / CONFIG_CONTRACT_RELATIVE_PATH


def test_config_contract_matches_owner_constants() -> None:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert payload["schema_id"] == CONTRACT_ID
    assert payload["owner_module"] == OWNER_MODULE
    assert payload["owner_symbol"] == OWNER_SYMBOL
    assert payload["env_override"] == ENV_ARCHIVE_ROOT
    assert tuple(payload["precedence"]) == PRECEDENCE_CHAIN
    assert payload["resolver_creates_filesystem"] is False
    assert payload["fixture_fallback_allowed"] is False
    assert payload["repo_local_runtime_truth_allowed"] is False
    assert payload["tmp_default_allowed"] is False
    assert payload["non_authorizing"] is True


def test_explicit_injected_root_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    injected = tmp_path / "injected_root"
    injected.mkdir()
    env_root = tmp_path / "env_root"
    env_root.mkdir()
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(env_root))
    resolved = resolve_workflow_dashboard_archive_root(explicit=injected)
    assert resolved == injected.resolve()


def test_environment_override_wins_over_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_root = tmp_path / "env_root"
    env_root.mkdir()
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(env_root))
    resolved = resolve_workflow_dashboard_archive_root(explicit=None)
    assert resolved == env_root.resolve()


def test_default_is_deterministic_absolute_and_cwd_independent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    home = tmp_path / "home"
    home.mkdir()
    first = canonical_default_workflow_dashboard_archive_root(
        home=home, platform="darwin", environ={}
    )
    other = tmp_path / "other_cwd"
    other.mkdir()
    monkeypatch.chdir(other)
    second = canonical_default_workflow_dashboard_archive_root(
        home=home, platform="darwin", environ={}
    )
    assert first == second
    assert first.is_absolute()
    assert first == (
        home.resolve() / "Library" / "Application Support" / "Peak_Trade" / "workflow_dashboard_v1"
    )


def test_resolver_performs_no_filesystem_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    home = tmp_path / "home_no_create"
    home.mkdir()
    default = canonical_default_workflow_dashboard_archive_root(
        home=home, platform="darwin", environ={}
    )
    assert not default.exists()
    resolved = resolve_workflow_dashboard_archive_root(
        home=home,
        platform="darwin",
        environ={},
        require_existing_directory=True,
    )
    assert resolved is None
    assert not default.exists()
    # Non-requiring mode still does not create.
    path = resolve_workflow_dashboard_archive_root(
        home=home,
        platform="darwin",
        environ={},
        require_existing_directory=False,
    )
    assert path == default
    assert not default.exists()


def test_fixture_tmp_and_repo_not_selected_as_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    home = tmp_path / "home"
    home.mkdir()
    default = canonical_default_workflow_dashboard_archive_root(
        home=home, platform="darwin", environ={}, repo_root=REPO_ROOT
    )
    assert "tests/fixtures" not in default.as_posix()
    assert not str(default).startswith(str(REPO_ROOT))
    assert "/tmp" not in default.as_posix() or not default.as_posix().startswith("/tmp")
    # Linux with tmp-backed XDG_STATE_HOME falls back to ~/.local/state
    linux_default = canonical_default_workflow_dashboard_archive_root(
        home=home,
        platform="linux",
        environ={"XDG_STATE_HOME": "/tmp/xdg-state"},
        repo_root=REPO_ROOT,
    )
    assert not str(linux_default).startswith("/tmp")
    assert linux_default == (
        home.resolve() / ".local" / "state" / "peak_trade" / "workflow_dashboard_v1"
    )


def test_invalid_explicit_path_shape_fails_closed() -> None:
    with pytest.raises(WorkflowDashboardArchiveRootError):
        resolve_workflow_dashboard_archive_root(explicit="   ")
    with pytest.raises(WorkflowDashboardArchiveRootError):
        resolve_workflow_dashboard_archive_root(explicit="/")


def test_existing_env_workflows_remain_compatible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "archive"
    archive.mkdir()
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    ctx = build_workflow_dashboard_display_context()
    # Empty archive is configured (dir exists) and loads with warnings/errors — not unconfigured.
    assert ctx["gate_enabled"] is True
    assert ctx["display_status"] != "unconfigured"
    assert ctx["display_status"] in ("ready", "ready_with_warnings", "error")


def test_unconfigured_when_default_missing_preserves_runtime_semantics(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    # Point home at a temp home so default cannot accidentally exist.
    home = tmp_path / "isolated_home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    # Also clear LOCALAPPDATA/XDG noise for portability.
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    ctx = build_workflow_dashboard_display_context()
    assert ctx["display_status"] == "unconfigured"
    assert ctx["section_visible"] is False
    assert ctx["readmodel"] is None


def test_missing_readmodel_under_resolved_root_remains_missing_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datetime import datetime, timezone

    root = tmp_path / "empty_durable_root"
    root.mkdir()
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    slots = bind_market_universe_slots(
        generated_at=datetime.now(timezone.utc),
        archive_root=root,
    )
    assert slots["universe_ranking"].availability is Availability.MISSING_SOURCE
    assert REASON_UNIVERSE_ABSENT in slots["universe_ranking"].reason_codes


def test_unset_root_still_reports_archive_root_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from datetime import datetime, timezone

    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    slots = bind_market_universe_slots(generated_at=datetime.now(timezone.utc))
    assert slots["universe_ranking"].availability is Availability.MISSING_SOURCE
    assert REASON_ARCHIVE_ROOT_UNSET in slots["universe_ranking"].reason_codes


def test_linux_and_windows_default_shapes(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    linux = canonical_default_workflow_dashboard_archive_root(
        home=home, platform="linux", environ={}, repo_root=REPO_ROOT
    )
    assert linux == home.resolve() / ".local" / "state" / "peak_trade" / "workflow_dashboard_v1"
    win = canonical_default_workflow_dashboard_archive_root(
        home=home,
        platform="win32",
        environ={"LOCALAPPDATA": str(home / "AppData" / "Local")},
        repo_root=REPO_ROOT,
    )
    assert win == (home.resolve() / "AppData" / "Local" / "Peak_Trade" / "workflow_dashboard_v1")
