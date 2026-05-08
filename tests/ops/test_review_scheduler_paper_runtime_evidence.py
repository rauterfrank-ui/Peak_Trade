"""Tests for scheduler paper-runtime evidence review helper."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "ops" / "review_scheduler_paper_runtime_evidence.py"


def _load_mod():
    spec = importlib.util.spec_from_file_location("review_scheduler_paper_runtime_evidence", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_pass_fixture(
    tmp_path: Path,
    *,
    timeout_text: str = "run_with_timeout: exceeded --timeout-seconds=3600.0; terminated: []\n",
) -> tuple[Path, Path]:
    outroot = tmp_path / "out"
    logroot = tmp_path / "logs"
    outroot.mkdir()
    logroot.mkdir()

    account = outroot / "account.json"
    fills = outroot / "fills.json"
    account.write_text(
        json.dumps(
            {
                "schema_version": "p7.account.v0",
                "cash": 999.6,
                "positions": {"BTC": 0.0},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    fills.write_text(
        json.dumps(
            {
                "schema_version": "p7.fills.v0",
                "fills": [
                    {"symbol": "BTC", "side": "BUY", "qty": 1.0, "price": 100.1},
                    {"symbol": "BTC", "side": "SELL", "qty": 1.0, "price": 99.9},
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (outroot / "evidence_manifest.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "name": "account.json",
                        "relpath": "account.json",
                        "sha256": _sha256(account),
                    },
                    {
                        "name": "fills.json",
                        "relpath": "fills.json",
                        "sha256": _sha256(fills),
                    },
                ],
                "meta": {"kind": "p7_paper_manifest"},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (logroot / "scheduler_stdout.log").write_text("scheduler output\n", encoding="utf-8")
    (logroot / "scheduler_stderr.log").write_text(timeout_text, encoding="utf-8")
    return outroot, logroot


def _argv(outroot: Path, logroot: Path, *extra: str) -> list[str]:
    return [
        "review_scheduler_paper_runtime_evidence.py",
        "--outroot",
        str(outroot),
        "--logroot",
        str(logroot),
        "--expected-timeout-seconds",
        "3600",
        *extra,
    ]


def test_script_exists() -> None:
    assert SCRIPT.is_file()


def test_pass_fixture_with_manifest_hashes_and_timeout_text(tmp_path: Path) -> None:
    mod = _load_mod()
    outroot, logroot = _write_pass_fixture(tmp_path)

    result = mod.review_evidence(
        outroot=outroot,
        logroot=logroot,
        expected_timeout_seconds=3600,
    )

    assert result["verdict"] == mod.PASS
    assert result["metrics"]["fills_count"] == 2
    assert result["metrics"]["account_cash"] == 999.6
    assert result["metrics"]["positions_count"] == 1
    assert result["metrics"]["timeout_observed"] is True
    assert result["metrics"]["manifest_references_computed_hashes"] is True


def test_accepts_float_timeout_text(tmp_path: Path) -> None:
    mod = _load_mod()
    outroot, logroot = _write_pass_fixture(
        tmp_path,
        timeout_text="run_with_timeout: exceeded --timeout-seconds=3600.0; terminated: ['x']\n",
    )

    assert mod.main(_argv(outroot, logroot)) == 0


def test_rejects_missing_files(tmp_path: Path) -> None:
    mod = _load_mod()
    outroot, logroot = _write_pass_fixture(tmp_path)
    (outroot / "fills.json").unlink()

    result = mod.review_evidence(
        outroot=outroot,
        logroot=logroot,
        expected_timeout_seconds=3600,
    )

    assert result["verdict"] == mod.REVIEW_REQUIRED
    assert any("missing required file" in issue for issue in result["issues"])
    assert mod.main(_argv(outroot, logroot)) == mod.REVIEW_REQUIRED_EXIT


def test_rejects_hash_mismatch(tmp_path: Path) -> None:
    mod = _load_mod()
    outroot, logroot = _write_pass_fixture(tmp_path)
    (outroot / "account.json").write_text(
        json.dumps({"cash": 1000.0, "positions": {}}),
        encoding="utf-8",
    )

    result = mod.review_evidence(
        outroot=outroot,
        logroot=logroot,
        expected_timeout_seconds=3600,
    )

    assert result["verdict"] == mod.REVIEW_REQUIRED
    assert result["metrics"]["manifest_references_computed_hashes"] is False
    assert any("sha256" in issue for issue in result["issues"])


def test_rejects_missing_timeout_text(tmp_path: Path) -> None:
    mod = _load_mod()
    outroot, logroot = _write_pass_fixture(tmp_path)
    (logroot / "scheduler_stderr.log").write_text("completed without timeout\n", encoding="utf-8")

    result = mod.review_evidence(
        outroot=outroot,
        logroot=logroot,
        expected_timeout_seconds=3600,
    )

    assert result["verdict"] == mod.REVIEW_REQUIRED
    assert result["metrics"]["timeout_observed"] is False
    assert any("timeout semantics" in issue for issue in result["issues"])


def test_json_output_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    mod = _load_mod()
    outroot, logroot = _write_pass_fixture(tmp_path)

    err = StringIO()
    monkeypatch.setattr(sys, "stderr", err)
    assert mod.main(_argv(outroot, logroot, "--json")) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["verdict"] == "PASS"
    assert payload["issues"] == []
    assert payload["inputs"]["expected_timeout_seconds"] == 3600
    assert payload["metrics"] == {
        "account_cash": 999.6,
        "fills_count": 2,
        "manifest_references_computed_hashes": True,
        "positions_count": 1,
        "stderr_bytes": len(
            "run_with_timeout: exceeded --timeout-seconds=3600.0; terminated: []\n".encode()
        ),
        "stdout_bytes": len("scheduler output\n".encode()),
        "timeout_observed": True,
    }


def test_human_output_includes_verdict_and_metrics(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    mod = _load_mod()
    outroot, logroot = _write_pass_fixture(tmp_path)

    assert mod.main(_argv(outroot, logroot)) == 0

    out = capsys.readouterr().out
    assert "VERDICT: PASS" in out
    assert "fills_count: 2" in out
    assert "account_cash: 999.6" in out
    assert "timeout_observed: True" in out


@pytest.mark.parametrize("expected_timeout", ("0", "-1", "0.0"))
def test_invalid_expected_timeout_exits_2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    expected_timeout: str,
) -> None:
    mod = _load_mod()
    outroot, logroot = _write_pass_fixture(tmp_path)
    err = StringIO()
    monkeypatch.setattr(sys, "stderr", err)

    argv = [
        "review_scheduler_paper_runtime_evidence.py",
        "--outroot",
        str(outroot),
        "--logroot",
        str(logroot),
        "--expected-timeout-seconds",
        expected_timeout,
    ]

    assert mod.main(argv) == mod.USAGE_EXIT == 2
    assert "expected-timeout-seconds" in err.getvalue()


def test_missing_directory_returns_invalid_input(tmp_path: Path) -> None:
    mod = _load_mod()
    outroot = tmp_path / "nope"
    logroot = tmp_path / "logs"
    logroot.mkdir()

    assert (
        mod.main(
            [
                "review_scheduler_paper_runtime_evidence.py",
                "--outroot",
                str(outroot),
                "--logroot",
                str(logroot),
                "--expected-timeout-seconds",
                "1",
            ]
        )
        == mod.USAGE_EXIT
    )


def test_cli_invocation_matches_module_returncode(tmp_path: Path) -> None:
    outroot, logroot = _write_pass_fixture(
        tmp_path,
        timeout_text="run_with_timeout: exceeded --timeout-seconds=5.0; terminated: []\n",
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--outroot",
            str(outroot),
            "--logroot",
            str(logroot),
            "--expected-timeout-seconds",
            "5",
        ],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "VERDICT: PASS" in proc.stdout
