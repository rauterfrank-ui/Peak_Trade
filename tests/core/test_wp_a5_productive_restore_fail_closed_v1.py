"""WP-A5 productive restore fail-closed regression.

Protects the already-adjudicated D5 path:

    D5=DEFER_NO_PRODUCTIVE_RESTORE

Backup/snapshot creation remains available.
Dry-run inspection remains available and non-mutating.
Productive restore through RecoveryManager.restore_backup is denied
before any restore copy/write.

Restore remains operational infrastructure, not recovery/activation/autonomy
authority. This module does not invent an execution-guard set.
"""

from __future__ import annotations

import inspect
import os
from pathlib import Path

import pytest

from src.core import backup_recovery as backup_recovery_mod
from src.core.backup_recovery import (
    PRODUCTIVE_RESTORE_DENIED,
    BackupType,
    ConfigBackup,
    DataBackup,
    RecoveryManager,
)

_FORBIDDEN_ACTIVATION_TOKENS: frozenset[str] = frozenset(
    {
        "LIVE_ENABLED",
        "LIVE_ARMED",
        "LIVE_AUTHORIZED",
        "TESTNET_AUTHORIZED",
        "CANARY_AUTHORIZED",
        "enable_live_trading",
        "live_mode_armed",
        "live_authorized",
        "testnet_authorized",
        "canary_authorized",
    }
)
_FORBIDDEN_RESTORE_TARGETS: frozenset[str] = frozenset(
    {
        "credentials",
        "secrets",
        "api_key",
        "api_secret",
        "whitelist",
        "ip_whitelist",
        "Permit",
        "ExecutionPermit",
        "submit_state",
        "LIVE_ENABLED",
        "LIVE_ARMED",
        "TESTNET_AUTHORIZED",
        "CANARY_AUTHORIZED",
    }
)


def _workspace_snapshot(root: Path) -> dict[str, tuple[int, str]]:
    snapshot: dict[str, tuple[int, str]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            snapshot[str(path.relative_to(root))] = (path.stat().st_mtime_ns, path.read_text())
    return snapshot


def _recording_copy(original, calls: list[str], label: str):
    def _wrapped(src, dst, *args, **kwargs):
        calls.append(f"{label}:{src}->{dst}")
        return original(src, dst, *args, **kwargs)

    return _wrapped


def test_wp_a5_restore_is_not_authority() -> None:
    source = inspect.getsource(RecoveryManager.restore_backup)
    lowered = source.lower()
    for token in _FORBIDDEN_RESTORE_TARGETS:
        assert token.lower() not in lowered, f"restore must not target {token}"
    for token in _FORBIDDEN_ACTIVATION_TOKENS:
        assert token not in source


def test_productive_restore_fails_closed_before_filesystem_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config_file = workspace / "config.toml"
    config_file.write_text("setting = 'original'")
    data_file = workspace / "data.txt"
    data_file.write_text("payload")

    recovery = RecoveryManager(backup_dir=str(tmp_path / "backups"))
    recovery.config_backup.add_config(config_file)
    recovery.data_backup.add_data_path(data_file)
    backup_id = recovery.create_backup(include_config=True, include_data=True)

    config_file.write_text("setting = 'mutated'")
    data_file.write_text("mutated")
    before = _workspace_snapshot(tmp_path)

    copy_calls: list[str] = []
    monkeypatch.setattr(
        backup_recovery_mod.shutil,
        "copy2",
        _recording_copy(backup_recovery_mod.shutil.copy2, copy_calls, "copy2"),
    )
    monkeypatch.setattr(
        backup_recovery_mod.shutil,
        "copytree",
        _recording_copy(backup_recovery_mod.shutil.copytree, copy_calls, "copytree"),
    )

    with pytest.raises(PermissionError, match=PRODUCTIVE_RESTORE_DENIED):
        recovery.restore_backup(
            backup_id,
            restore_config=True,
            restore_data=True,
            restore_state=True,
            dry_run=False,
        )

    assert copy_calls == []
    assert _workspace_snapshot(tmp_path) == before
    assert config_file.read_text() == "setting = 'mutated'"
    assert data_file.read_text() == "mutated"


def test_dry_run_restore_is_non_mutating(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text("setting = 'original'")
    data_file = tmp_path / "data.txt"
    data_file.write_text("payload")

    recovery = RecoveryManager(backup_dir=str(tmp_path / "backups"))
    recovery.config_backup.add_config(config_file)
    recovery.data_backup.add_data_path(data_file)
    recovery.state_snapshot.register_provider("probe", lambda: {"ok": True})
    backup_id = recovery.create_backup(include_config=True, include_state=True, include_data=True)

    config_file.write_text("setting = 'mutated'")
    data_file.write_text("mutated")
    before = _workspace_snapshot(tmp_path)

    copy_calls: list[str] = []
    monkeypatch.setattr(
        backup_recovery_mod.shutil,
        "copy2",
        _recording_copy(backup_recovery_mod.shutil.copy2, copy_calls, "copy2"),
    )
    monkeypatch.setattr(
        backup_recovery_mod.shutil,
        "copytree",
        _recording_copy(backup_recovery_mod.shutil.copytree, copy_calls, "copytree"),
    )

    success = recovery.restore_backup(
        backup_id,
        restore_config=True,
        restore_data=True,
        restore_state=True,
        dry_run=True,
    )

    assert success is True
    assert copy_calls == []
    assert _workspace_snapshot(tmp_path) == before
    assert config_file.read_text() == "setting = 'mutated'"
    assert data_file.read_text() == "mutated"


def test_backup_creation_list_and_metadata_remain_functional(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text("setting = 'value'")
    recovery = RecoveryManager(backup_dir=str(tmp_path / "backups"))
    recovery.config_backup.add_config(config_file)
    recovery.state_snapshot.register_provider("probe", lambda: {"metric": 1})

    backup_id = recovery.create_backup(
        include_config=True,
        include_state=True,
        description="wp-a5 creation preserved",
        tags=["wp-a5"],
    )
    backups = recovery.list_backups(tags=["wp-a5"])
    assert len(backups) == 1
    assert backups[0].backup_id == backup_id
    assert backups[0].backup_type == BackupType.CONFIG
    assert backups[0].description == "wp-a5 creation preserved"

    backup_dir = recovery._get_backup_dir(backup_id)
    metadata = recovery._load_metadata(backup_dir)
    assert metadata is not None
    assert metadata.backup_id == backup_id
    assert (backup_dir / "config" / config_file.name).is_file()
    assert (backup_dir / "state.json").is_file()
    assert (backup_dir / "metadata.json").is_file()


def test_denied_restore_does_not_change_authorization_or_env(tmp_path: Path) -> None:
    tracked = (
        "LIVE_ENABLED",
        "LIVE_ARMED",
        "LIVE_AUTHORIZED",
        "TESTNET_AUTHORIZED",
        "CANARY_AUTHORIZED",
    )
    before_env = {key: os.environ.get(key) for key in tracked}

    config_file = tmp_path / "config.toml"
    config_file.write_text("setting = 'value'")
    recovery = RecoveryManager(backup_dir=str(tmp_path / "backups"))
    recovery.config_backup.add_config(config_file)
    backup_id = recovery.create_backup(include_config=True)

    with pytest.raises(PermissionError, match=PRODUCTIVE_RESTORE_DENIED):
        recovery.restore_backup(backup_id, restore_config=True, dry_run=False)

    assert {key: os.environ.get(key) for key in tracked} == before_env
    for key in tracked:
        assert os.environ.get(key) in (None, "false", "False", "0")


def test_default_restore_backup_call_is_productive_and_denied(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text("setting = 'value'")
    recovery = RecoveryManager(backup_dir=str(tmp_path / "backups"))
    recovery.config_backup.add_config(config_file)
    backup_id = recovery.create_backup(include_config=True)

    signature = inspect.signature(RecoveryManager.restore_backup)
    assert signature.parameters["dry_run"].default is False

    with pytest.raises(PermissionError, match=PRODUCTIVE_RESTORE_DENIED):
        recovery.restore_backup(backup_id)


def test_lower_level_helpers_remain_callable_for_offline_fixtures(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    (backup_dir / "fixture.toml").write_text("restored = true")
    (backup_dir / "fixture.txt").write_text("data")

    config_target = tmp_path / "fixture.toml"
    data_target = tmp_path / "fixture.txt"
    assert ConfigBackup([config_target]).restore(backup_dir) == 1
    assert DataBackup([data_target]).restore(backup_dir) == 1
    assert config_target.read_text() == "restored = true"
    assert data_target.read_text() == "data"
