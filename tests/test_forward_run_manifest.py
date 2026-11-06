"""Tests für scripts/_forward_run_manifest (run_id, Writer, try_git_sha). NO-LIVE."""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import _forward_run_manifest as _frm  # noqa: E402
from _forward_run_manifest import (  # noqa: E402
    compute_deterministic_run_id,
    try_git_sha,
    write_forward_run_manifest,
)


# --- compute_deterministic_run_id ---


def test_compute_deterministic_run_id_stable_for_same_inputs() -> None:
    a = compute_deterministic_run_id(
        script_name="x.py",
        argv=["python", "x.py", "--a", "1"],
        config_path="config.toml",
        git_sha="abc",
    )
    b = compute_deterministic_run_id(
        script_name="x.py",
        argv=["python", "x.py", "--a", "1"],
        config_path="config.toml",
        git_sha="abc",
    )
    assert a == b
    assert len(a) == 64


def test_compute_deterministic_run_id_differs_when_argv_differs() -> None:
    r1 = compute_deterministic_run_id(
        script_name="x.py",
        argv=["a", "1"],
        config_path="c.toml",
        git_sha="g",
    )
    r2 = compute_deterministic_run_id(
        script_name="x.py",
        argv=["a", "2"],
        config_path="c.toml",
        git_sha="g",
    )
    assert r1 != r2


def test_compute_deterministic_run_id_none_git_sha_normalized() -> None:
    a = compute_deterministic_run_id(
        script_name="s",
        argv=[],
        config_path="c",
        git_sha=None,
    )
    b = compute_deterministic_run_id(
        script_name="s",
        argv=[],
        config_path="c",
        git_sha=None,
    )
    assert a == b


def test_compute_deterministic_run_id_differs_when_script_name_differs() -> None:
    base = dict(
        argv=["a"],
        config_path="c.toml",
        git_sha="deadbeef",
    )
    r1 = compute_deterministic_run_id(script_name="one.py", **base)
    r2 = compute_deterministic_run_id(script_name="two.py", **base)
    assert r1 != r2


def test_compute_deterministic_run_id_differs_when_config_path_differs() -> None:
    r1 = compute_deterministic_run_id(
        script_name="x.py",
        argv=["a"],
        config_path="first.toml",
        git_sha="g",
    )
    r2 = compute_deterministic_run_id(
        script_name="x.py",
        argv=["a"],
        config_path="second.toml",
        git_sha="g",
    )
    assert r1 != r2


def test_compute_deterministic_run_id_differs_when_git_sha_differs() -> None:
    r1 = compute_deterministic_run_id(
        script_name="x.py",
        argv=["a"],
        config_path="c.toml",
        git_sha="aaa",
    )
    r2 = compute_deterministic_run_id(
        script_name="x.py",
        argv=["a"],
        config_path="c.toml",
        git_sha="bbb",
    )
    assert r1 != r2


def test_compute_deterministic_run_id_git_sha_none_vs_string_differs() -> None:
    with_sha = compute_deterministic_run_id(
        script_name="x.py",
        argv=[],
        config_path="c",
        git_sha="sha",
    )
    without = compute_deterministic_run_id(
        script_name="x.py",
        argv=[],
        config_path="c",
        git_sha=None,
    )
    assert with_sha != without


def test_compute_deterministic_run_id_contract_excludes_generated_at_utc() -> None:
    """Manifest-Zeitstempel fließt nicht in run_id (siehe docs/ops/CLI_RUN_MANIFEST_RUN_ID.md)."""
    sig = inspect.signature(compute_deterministic_run_id)
    assert list(sig.parameters) == [
        "script_name",
        "argv",
        "config_path",
        "git_sha",
    ]


# --- write_forward_run_manifest ---


def test_write_forward_run_manifest_sets_generated_at_when_missing(
    tmp_path: Path,
) -> None:
    fixed = datetime(2024, 6, 1, 10, 30, 45, tzinfo=timezone.utc)

    class FakeDatetime:
        @staticmethod
        def now(tz=None):
            return fixed

    with patch.object(_frm, "datetime", FakeDatetime):
        out = tmp_path / "nested" / "run_manifest.json"
        write_forward_run_manifest(
            out,
            {"run_id": "rid1", "script_name": "s.py"},
        )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["generated_at_utc"] == "2024-06-01T10:30:45Z"
    assert payload["run_id"] == "rid1"
    assert payload["script_name"] == "s.py"


def test_write_forward_run_manifest_preserves_existing_generated_at_utc(
    tmp_path: Path,
) -> None:
    out = tmp_path / "m.json"
    existing = "2019-12-31T23:59:59Z"
    write_forward_run_manifest(
        out,
        {"generated_at_utc": existing, "run_id": "x"},
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["generated_at_utc"] == existing
    assert payload["run_id"] == "x"


def test_write_forward_run_manifest_preserves_payload_and_writes_json(
    tmp_path: Path,
) -> None:
    out = tmp_path / "sub" / "manifest.json"
    data = {
        "run_id": "abc123",
        "script_name": "generate_forward_signals.py",
        "argv": ["python", "generate_forward_signals.py", "--cfg", "c.toml"],
        "config_path": "c.toml",
        "git_sha": "deadbeef",
        "generated_at_utc": "2020-01-01T00:00:00Z",
    }
    write_forward_run_manifest(out, data)

    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload == data


# --- try_git_sha ---


def test_try_git_sha_returns_stripped_stdout_when_git_succeeds() -> None:
    proc = MagicMock()
    proc.returncode = 0
    proc.stdout = "  deadbeef\n"

    with patch.object(_frm.subprocess, "run", return_value=proc) as mock_run:
        assert try_git_sha() == "deadbeef"

    mock_run.assert_called_once_with(
        ["git", "rev-parse", "HEAD"],
        cwd=_frm._REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )


def test_try_git_sha_returns_none_when_git_fails() -> None:
    proc = MagicMock()
    proc.returncode = 128

    with patch.object(_frm.subprocess, "run", return_value=proc):
        assert try_git_sha() is None


def test_try_git_sha_returns_none_on_subprocess_oserror() -> None:
    with patch.object(
        _frm.subprocess,
        "run",
        side_effect=OSError("git not found"),
    ):
        assert try_git_sha() is None


def test_try_git_sha_returns_none_on_subprocess_timeout() -> None:
    exc = subprocess.TimeoutExpired(cmd=["git", "rev-parse", "HEAD"], timeout=5)
    with patch.object(_frm.subprocess, "run", side_effect=exc):
        assert try_git_sha() is None


def test_try_git_sha_returns_none_on_file_not_found_error() -> None:
    with patch.object(
        _frm.subprocess,
        "run",
        side_effect=FileNotFoundError("git"),
    ):
        assert try_git_sha() is None
