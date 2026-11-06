"""Contract tests for p7_ctl run-shadow / run-paper (argv, dry-run, outdir guards).

Uses subprocess mocking — does not execute real paper/shadow runners.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
P7_CTL = ROOT / "scripts" / "ops" / "p7_ctl.py"
SHADOW_SPEC = ROOT / "tests" / "fixtures" / "p6" / "shadow_session_min_v1_p7.json"
PAPER_SPEC = ROOT / "tests" / "fixtures" / "p7" / "paper_run_min_v0.json"


def _import_p7ctl():
    import importlib.util

    spec = importlib.util.spec_from_file_location("p7_ctl", P7_CTL)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def p7():
    return _import_p7ctl()


def test_run_shadow_cmd_includes_dry_run_when_default(
    p7: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(p7.subprocess, "run", fake_run)
    out = tmp_path / "shadow_out"
    out.mkdir()
    args = SimpleNamespace(
        spec=str(SHADOW_SPEC.relative_to(ROOT)),
        run_id="contract_rid",
        outdir=str(out.resolve()),
        p7_evidence=1,
        dry_run=True,
    )
    assert p7.cmd_run_shadow(args) == 0
    cmd = captured["cmd"]
    runner = cmd.index(str(ROOT / "scripts" / "aiops" / "run_shadow_session.py"))
    assert "--dry-run" in cmd[runner:]


def test_run_shadow_cmd_includes_no_dry_run(
    p7: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(p7.subprocess, "run", fake_run)
    out = tmp_path / "shadow_out"
    out.mkdir()
    args = SimpleNamespace(
        spec=str(SHADOW_SPEC.relative_to(ROOT)),
        run_id="contract_rid",
        outdir=str(out.resolve()),
        p7_evidence=0,
        dry_run=False,
    )
    assert p7.cmd_run_shadow(args) == 0
    cmd = captured["cmd"]
    assert "--no-dry-run" in cmd
    assert "--dry-run" not in cmd


def test_run_shadow_rejects_nonempty_outdir_before_subprocess(
    p7: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def boom(*_a: object, **_k: object) -> None:
        raise AssertionError("subprocess.run must not be called")

    monkeypatch.setattr(p7.subprocess, "run", boom)
    out = tmp_path / "shadow_out"
    out.mkdir()
    (out / "stale.json").write_text("{}", encoding="utf-8")
    args = SimpleNamespace(
        spec=str(SHADOW_SPEC.relative_to(ROOT)),
        run_id="x",
        outdir=str(out),
        p7_evidence=1,
        dry_run=True,
    )
    assert p7.cmd_run_shadow(args) == p7._P7_ERR_OUTDIR_NOT_EMPTY


def test_run_paper_cmd_includes_dry_run(
    p7: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(p7.subprocess, "run", fake_run)
    out = tmp_path / "paper_out"
    out.mkdir()
    args = SimpleNamespace(
        spec=str(PAPER_SPEC.relative_to(ROOT)),
        run_id="",
        outdir=str(out.resolve()),
        evidence=0,
        dry_run=True,
    )
    assert p7.cmd_run_paper(args) == 0
    cmd = captured["cmd"]
    r = cmd.index(str(ROOT / "scripts" / "aiops" / "run_paper_trading_session.py"))
    assert "--dry-run" in cmd[r:]


def test_run_paper_rejects_nonempty_outdir(
    p7: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        p7.subprocess,
        "run",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("subprocess.run")),
    )
    out = tmp_path / "paper_out"
    out.mkdir()
    (out / "fills.json").write_text("{}", encoding="utf-8")
    args = SimpleNamespace(
        spec=str(PAPER_SPEC.relative_to(ROOT)),
        run_id="",
        outdir=str(out),
        evidence=1,
        dry_run=False,
    )
    assert p7.cmd_run_paper(args) == p7._P7_ERR_OUTDIR_NOT_EMPTY


def test_main_run_shadow_invocation_integration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "", "")

    p7 = _import_p7ctl()
    monkeypatch.setattr(p7.subprocess, "run", fake_run)
    out = tmp_path / "sout"
    out.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "p7_ctl",
            "run-shadow",
            "--spec",
            str(SHADOW_SPEC.relative_to(ROOT)),
            "--outdir",
            str(out.resolve()),
        ],
    )
    assert p7.main() == 0
    assert "--dry-run" in captured["cmd"]


def test_main_run_paper_dry_run_invocation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "", "")

    p7 = _import_p7ctl()
    monkeypatch.setattr(p7.subprocess, "run", fake_run)
    out = tmp_path / "pout"
    out.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "p7_ctl",
            "run-paper",
            "--spec",
            str(PAPER_SPEC.relative_to(ROOT)),
            "--outdir",
            str(out.resolve()),
            "--dry-run",
        ],
    )
    assert p7.main() == 0
    assert "--dry-run" in captured["cmd"]
