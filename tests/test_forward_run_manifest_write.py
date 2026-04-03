"""Tests für write_forward_run_manifest (_forward_run_manifest)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import _forward_run_manifest as _frm  # noqa: E402
from _forward_run_manifest import write_forward_run_manifest  # noqa: E402


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
