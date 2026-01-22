from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/ops/pt_compare_consume.py", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        f.write("\n")


def _minimal_report(*, status: str, exit_code: int, reasons: list[str] | None = None) -> dict:
    return {
        "schema_version": "REPLAY_COMPARE_REPORT_V1",
        "meta": {
            "bundle_id": "b",
            "run_id": "r",
            "generated_at_utc": "2000-01-01T00:00:00Z",
            "tool": "pt_replay_pack",
            "tool_version": "1.2.3",
            "compare_version": "1",
        },
        "replay": {
            "validate_bundle": "PASS",
            "replay_exit_code": 0,
            "check_outputs": "disabled",
            "invariants": {"fills": "SKIP", "positions": "SKIP"},
            "diffs": {
                "fills_diff": {"added": 0, "removed": 0, "changed": 0, "sample": []},
                "positions_diff": {"added": 0, "removed": 0, "changed": 0, "sample": []},
            },
        },
        "summary": {"status": status, "reasons": reasons or [], "exit_code": int(exit_code)},
    }


def test_consume_pass_exit_0_and_writes_minified_summary(tmp_path: Path) -> None:
    report = _minimal_report(status="PASS", exit_code=0, reasons=[])
    report_path = tmp_path / "meta" / "compare_report.json"
    _write_json(report_path, report)

    cp = _run(["--report", str(report_path)], cwd=_repo_root())
    assert cp.returncode == 0, cp.stderr
    assert "STATUS=PASS" in cp.stdout

    out_path = report_path.parent / "compare_summary.min.json"
    assert out_path.exists()
    b = out_path.read_bytes()
    assert b"\r\n" not in b
    assert b.endswith(b"\n")
    # Minified JSON has no spaces/newlines besides trailing LF
    assert b" " not in b[:-1]
    assert b"\n" not in b[:-1]

    obj = json.loads(out_path.read_text(encoding="utf-8"))
    assert obj["schema_version"] == "REPLAY_COMPARE_SUMMARY_V1"
    assert obj["status"] == "PASS"
    assert int(obj["exit_code"]) == 0


def test_consume_fail_default_exit_0(tmp_path: Path) -> None:
    report = _minimal_report(
        status="FAIL", exit_code=4, reasons=["REPLAY_MISMATCH:EXPECTED_OUTPUTS"]
    )
    report_path = tmp_path / "meta" / "compare_report.json"
    _write_json(report_path, report)

    cp = _run(["--report", str(report_path)], cwd=_repo_root())
    assert cp.returncode == 0, cp.stderr
    assert "STATUS=FAIL" in cp.stdout
    assert "EXIT=4" in cp.stdout


def test_consume_fail_strict_exit_equals_report_exit_code(tmp_path: Path) -> None:
    report = _minimal_report(status="FAIL", exit_code=6, reasons=["DATAREFS:MISSING_REQUIRED"])
    report_path = tmp_path / "meta" / "compare_report.json"
    _write_json(report_path, report)

    cp = _run(["--report", str(report_path), "--strict"], cwd=_repo_root())
    assert cp.returncode == 6


def test_consume_deterministic_bytes(tmp_path: Path) -> None:
    report = _minimal_report(status="PASS", exit_code=0, reasons=["B", "A"])
    report_path = tmp_path / "meta" / "compare_report.json"
    _write_json(report_path, report)

    cp1 = _run(["--report", str(report_path)], cwd=_repo_root())
    assert cp1.returncode == 0
    b1 = (report_path.parent / "compare_summary.min.json").read_bytes()

    cp2 = _run(["--report", str(report_path)], cwd=_repo_root())
    assert cp2.returncode == 0
    b2 = (report_path.parent / "compare_summary.min.json").read_bytes()
    assert b1 == b2


def test_consume_invalid_json_exit_2(tmp_path: Path) -> None:
    report_path = tmp_path / "meta" / "compare_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("{not json}\n", encoding="utf-8")

    cp = _run(["--report", str(report_path)], cwd=_repo_root())
    assert cp.returncode == 2
