"""Tests for scripts/ops/snapshot_operator_stop_signals.py — read-only stop signal snapshot."""

import json
import os
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


def test_build_stop_signal_snapshot_selects_newest_incident_stop_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When multiple incident_stop_* dirs exist, the newest by directory mtime wins."""

    import scripts.ops.snapshot_operator_stop_signals as mod

    for k in mod.PT_STOP_KEYS:
        monkeypatch.delenv(k, raising=False)

    out_ops = tmp_path / "out" / "ops"
    older = out_ops / "incident_stop_20990101T000001Z_first"
    newer = out_ops / "incident_stop_20990101T000002Z_second"
    older.mkdir(parents=True)
    newer.mkdir(parents=True)
    (older / "incident_stop_state.env").write_text(
        "PT_FORCE_NO_TRADE=0\nPT_ENABLED=0\nPT_ARMED=0\n",
        encoding="utf-8",
    )
    (newer / "incident_stop_state.env").write_text(
        "PT_FORCE_NO_TRADE=1\nPT_ENABLED=0\nPT_ARMED=0\n",
        encoding="utf-8",
    )
    os.utime(older, (100, 100))
    os.utime(newer, (300, 300))

    snap = mod.build_stop_signal_snapshot(tmp_path)
    assert snap["incident_stop_artifact"]["status"] == "ok"
    art_path = snap["incident_stop_artifact"]["path"]
    assert "20990101T000002Z_second" in str(art_path)
    parsed = snap["incident_stop_artifact"]["parsed"]
    assert isinstance(parsed, dict)
    assert parsed.get("PT_FORCE_NO_TRADE") == "1"


def test_build_stop_signal_snapshot_without_operator_record_has_no_context_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.ops.snapshot_operator_stop_signals as mod

    for k in mod.PT_STOP_KEYS:
        monkeypatch.delenv(k, raising=False)
    snap = mod.build_stop_signal_snapshot(tmp_path)
    assert "operator_decision_context_v0" not in snap


def test_build_stop_signal_snapshot_operator_decision_record_includes_context_v0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.ops.snapshot_operator_stop_signals as mod

    for k in mod.PT_STOP_KEYS:
        monkeypatch.delenv(k, raising=False)
    decision = tmp_path / "OPERATOR_DECISION.md"
    decision.write_text(
        "\n".join(
            [
                "# decision",
                "OPERATOR_CLASSIFICATION=stale_closed",
                "CURRENT_STATE=HOLD_NO_PAPER_RUN_PENDING_RERUN",
                "GO_LIVE_NEXT_STEP=read_only_snapshot_and_preflight_rerun",
                "",
            ]
        ),
        encoding="utf-8",
    )
    snap = mod.build_stop_signal_snapshot(tmp_path, operator_decision_record=decision)
    ctx = snap["operator_decision_context_v0"]
    assert ctx["schema_version"] == "operator_decision_context.v0"
    assert ctx["record_present"] is True
    assert ctx["non_authorizing"] is True
    assert ctx["raw_artifacts_preserved"] is True
    assert ctx["permits_scheduler_runtime_paper_testnet_live"] is False
    assert ctx["operator_classification"] == "stale_closed"
    assert ctx["current_state"] == "HOLD_NO_PAPER_RUN_PENDING_RERUN"
    assert ctx["go_live_next_step"] == "read_only_snapshot_and_preflight_rerun"
    assert ctx["record_path"] == str(decision.resolve())


def test_build_stop_signal_snapshot_operator_record_preserves_incident_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.ops.snapshot_operator_stop_signals as mod

    for k in mod.PT_STOP_KEYS:
        monkeypatch.delenv(k, raising=False)
    inc_dir = tmp_path / "out" / "ops" / "incident_stop_20990101T000000Z_test"
    inc_dir.mkdir(parents=True)
    (inc_dir / "incident_stop_state.env").write_text(
        "PT_INCIDENT_STOP=1\nPT_FORCE_NO_TRADE=1\nPT_ENABLED=0\nPT_ARMED=0\n",
        encoding="utf-8",
    )
    decision = tmp_path / "decision.md"
    decision.write_text("OPERATOR_CLASSIFICATION=stale_closed\n", encoding="utf-8")
    snap = mod.build_stop_signal_snapshot(tmp_path, operator_decision_record=decision)
    art = snap["incident_stop_artifact"]
    assert art["status"] == "ok"
    assert art["parsed"] is not None
    assert art["parsed"].get("PT_INCIDENT_STOP") == "1"
    assert art["parsed"].get("PT_FORCE_NO_TRADE") == "1"
    assert snap["operator_decision_context_v0"]["operator_classification"] == "stale_closed"


def test_build_stop_signal_snapshot_invalid_operator_record_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.ops.snapshot_operator_stop_signals as mod

    for k in mod.PT_STOP_KEYS:
        monkeypatch.delenv(k, raising=False)
    missing = tmp_path / "nope.md"
    with pytest.raises(ValueError, match="not a file"):
        mod.build_stop_signal_snapshot(tmp_path, operator_decision_record=missing)


def test_main_operator_decision_record_missing_file_exits_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("snapshot_operator_stop_signals", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    missing = tmp_path / "missing_decision.md"
    monkeypatch.setattr(
        sys,
        "argv",
        ["x", "--json", "--repo-root", str(tmp_path), "--operator-decision-record", str(missing)],
    )
    assert mod.main() == 2


def test_snapshot_owner_crosslinks_gap5_and_scheduler_dry_run_hardening_v0() -> None:
    gap5_owner = ROOT / "tests" / "ops" / "test_gap5_stop_criteria_contract_v0.py"
    hardening_owner = (
        ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
    )
    hardening_marker = "SCHEDULER_DRY_RUN_HARDENING_SOURCE_CONTRACT_V0=true"

    assert gap5_owner.is_file()
    assert hardening_owner.is_file()

    gap5_drift_guard = ROOT / "tests" / "ops" / "test_gap5_stop_criteria_drift_guard_contract_v0.py"
    gap5_text = gap5_owner.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in gap5_text
    assert hardening_marker in gap5_text
    assert Path(__file__).name in gap5_text
    assert gap5_drift_guard.is_file()
    assert "snapshot_operator_stop_signals.py" in gap5_drift_guard.read_text(encoding="utf-8")

    hardening_text = hardening_owner.read_text(encoding="utf-8")
    assert "test_gap5_stop_criteria_contract_v0.py" in hardening_text
    assert Path(__file__).name in hardening_text
