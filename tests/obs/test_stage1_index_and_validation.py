from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True)


def test_stage1_index_and_validation_ok(tmp_path: Path) -> None:
    root = tmp_path / "stage1"
    root.mkdir(parents=True, exist_ok=True)

    run_date = "2026-02-03"
    (root / f"{run_date}_snapshot.md").write_text("# snapshot\n", encoding="utf-8")
    (root / f"{run_date}_summary.json").write_text('{"ok": true}\n', encoding="utf-8")
    (root / "stage1_trend.json").write_text('{"trend": "flat"}\n', encoding="utf-8")

    idx_path = root / "index.json"
    val_path = root / "validation.json"

    r1 = _run(
        [
            "python3",
            "scripts/obs/stage1_report_index.py",
            "--root",
            str(root),
            "--out",
            str(idx_path),
            "--run-date",
            run_date,
        ]
    )
    assert r1.returncode == 0, r1.stderr
    assert idx_path.exists()

    r2 = _run(
        [
            "python3",
            "scripts/obs/validate_stage1_index.py",
            "--root",
            str(root),
            "--index",
            str(idx_path),
            "--out",
            str(val_path),
            "--require",
            f"{run_date}_snapshot.md",
            "--require",
            f"{run_date}_summary.json",
            "--require",
            "stage1_trend.json",
        ]
    )
    assert r2.returncode == 0, r2.stderr
    assert val_path.exists()

    v = json.loads(val_path.read_text(encoding="utf-8"))
    assert v["schema_version"] == "stage1_validation.v1"
    assert v["ok"] is True
    assert v["errors"] == []


def test_stage1_validation_fails_on_tampered_sha(tmp_path: Path) -> None:
    root = tmp_path / "stage1"
    root.mkdir(parents=True, exist_ok=True)

    run_date = "2026-02-03"
    snap = root / f"{run_date}_snapshot.md"
    summ = root / f"{run_date}_summary.json"
    trend = root / "stage1_trend.json"

    snap.write_text("# snapshot\n", encoding="utf-8")
    summ.write_text('{"ok": true}\n', encoding="utf-8")
    trend.write_text('{"trend": "flat"}\n', encoding="utf-8")

    idx_path = root / "index.json"
    val_path = root / "validation.json"

    r1 = _run(
        [
            "python3",
            "scripts/obs/stage1_report_index.py",
            "--root",
            str(root),
            "--out",
            str(idx_path),
            "--run-date",
            run_date,
        ]
    )
    assert r1.returncode == 0, r1.stderr

    # Tamper: change file after index is built -> sha mismatch expected
    snap.write_text("# snapshot tampered\n", encoding="utf-8")

    r2 = _run(
        [
            "python3",
            "scripts/obs/validate_stage1_index.py",
            "--root",
            str(root),
            "--index",
            str(idx_path),
            "--out",
            str(val_path),
            "--require",
            f"{run_date}_snapshot.md",
            "--require",
            f"{run_date}_summary.json",
            "--require",
            "stage1_trend.json",
        ]
    )
    assert r2.returncode == 2, r2.stdout + "\n" + r2.stderr

    v = json.loads(val_path.read_text(encoding="utf-8"))
    assert v["ok"] is False
    assert any("sha256 mismatch" in e for e in v.get("errors", []))
