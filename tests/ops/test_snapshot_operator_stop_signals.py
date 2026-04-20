"""Tests for scripts/ops/snapshot_operator_stop_signals.py — read-only stop signal snapshot."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "ops" / "snapshot_operator_stop_signals.py"


def test_script_exists() -> None:
    assert SCRIPT.is_file()


def test_build_snapshot_missing_all_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.ops.snapshot_operator_stop_signals as mod

    for k in mod.PT_STOP_KEYS:
        monkeypatch.delenv(k, raising=False)
    snap = mod.build_stop_signal_snapshot(tmp_path)
    assert snap["contract"] == mod.CONTRACT_ID
    assert snap["kill_switch_file"]["status"] == "unavailable"
    assert snap["incident_stop_artifact"]["status"] == "none"
    assert snap["kill_switch_file"]["kill_switch_active"] is None


def test_kill_switch_active_and_env_divergence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.ops.snapshot_operator_stop_signals as mod

    ks_dir = tmp_path / "data" / "kill_switch"
    ks_dir.mkdir(parents=True)
    (ks_dir / "state.json").write_text('{"state": "idle"}\n', encoding="utf-8")
    monkeypatch.setenv("PT_FORCE_NO_TRADE", "1")
    monkeypatch.delenv("PT_INCIDENT_STOP", raising=False)

    snap = mod.build_stop_signal_snapshot(tmp_path)
    assert snap["kill_switch_file"]["kill_switch_active"] is False
    notes = snap["consistency_notes"]
    assert any("divergence: kill_switch_active is false" in n for n in notes)


def test_kill_switch_active_true_without_pt_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.ops.snapshot_operator_stop_signals as mod

    for k in mod.PT_STOP_KEYS:
        monkeypatch.delenv(k, raising=False)
    ks_dir = tmp_path / "data" / "kill_switch"
    ks_dir.mkdir(parents=True)
    (ks_dir / "state.json").write_text('{"state": "KILLED"}\n', encoding="utf-8")

    snap = mod.build_stop_signal_snapshot(tmp_path)
    assert snap["kill_switch_file"]["kill_switch_active"] is True
    assert any("divergence: kill_switch_active is true" in n for n in snap["consistency_notes"])


def test_incident_artifact_vs_process_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.snapshot_operator_stop_signals as mod

    for k in mod.PT_STOP_KEYS:
        monkeypatch.delenv(k, raising=False)
    inc_dir = tmp_path / "out" / "ops" / "incident_stop_20990101T000000Z_test"
    inc_dir.mkdir(parents=True)
    (inc_dir / "incident_stop_state.env").write_text(
        "PT_FORCE_NO_TRADE=1\nPT_ENABLED=0\nPT_ARMED=0\n",
        encoding="utf-8",
    )

    snap = mod.build_stop_signal_snapshot(tmp_path)
    assert snap["incident_stop_artifact"]["status"] == "ok"
    assert any("artifact_vs_process" in n for n in snap["consistency_notes"])


def test_kill_switch_invalid_json(tmp_path: Path) -> None:
    import scripts.ops.snapshot_operator_stop_signals as mod

    ks_dir = tmp_path / "data" / "kill_switch"
    ks_dir.mkdir(parents=True)
    (ks_dir / "state.json").write_text("not-json", encoding="utf-8")

    snap = mod.build_stop_signal_snapshot(tmp_path)
    assert snap["kill_switch_file"]["status"] == "error"
    assert any("kill_switch_file:" in n for n in snap["consistency_notes"])


def test_main_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, tmp_path: Path
) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("snapshot_operator_stop_signals", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    for k in mod.PT_STOP_KEYS:
        monkeypatch.delenv(k, raising=False)

    monkeypatch.setattr(sys, "argv", ["x", "--json", "--repo-root", str(tmp_path)])
    assert mod.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["contract"] == mod.CONTRACT_ID
