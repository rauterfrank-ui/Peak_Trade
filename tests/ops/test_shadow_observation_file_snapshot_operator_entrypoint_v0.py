from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "ops" / "run_shadow_observation_file_snapshot_v0.py"
_CONFIRM = "NO_RUNTIME_NO_SCHEDULER_NO_BROKER_NO_ORDERS"
_bounded_schema = "bounded_file_snapshot_observation_input_v0"
_bounded_source = "bounded_file_captured_static"
_captured_schema = "captured_realistic_snapshot_observation_input_v0"

_FORBIDDEN_SUBSTRINGS = (
    "import subprocess",
    "import requests",
    "import httpx",
    "import aiohttp",
    "import websocket",
    "from socket ",
    " import socket",
    "import click",
    "import typer",
)


def _run_script(args: list[str], *, cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        cwd=cwd or _REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_script_source_forbids_high_risk_imports() -> None:
    text = _SCRIPT.read_text(encoding="utf-8")
    lowered = text.lower()
    for bad in _FORBIDDEN_SUBSTRINGS:
        assert bad.lower() not in lowered, f"forbidden pattern: {bad!r}"


def test_requires_input_file() -> None:
    r = _run_script(
        [
            "--output-dir",
            "/tmp",
            "--run-id",
            "safe_run_id",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
    assert "--input-file" in (r.stderr + r.stdout) or "required" in r.stderr.lower()


def test_requires_output_dir(tmp_path: Path) -> None:
    p = tmp_path / "in.json"
    p.write_text("{}", encoding="utf-8")
    r = _run_script(
        [
            "--input-file",
            str(p),
            "--run-id",
            "safe_run_id",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0


def test_requires_run_id(tmp_path: Path) -> None:
    p = tmp_path / "in.json"
    p.write_text(
        '{"schema":"bounded_file_snapshot_observation_input_v0","source":"bounded_file_captured_static","snapshots":[]}',
        encoding="utf-8",
    )
    r = _run_script(
        [
            "--input-file",
            str(p),
            "--output-dir",
            str(tmp_path / "out"),
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0


def test_requires_exact_confirmation_token(tmp_path: Path) -> None:
    p = tmp_path / "in.json"
    p.write_text('{"schema":"x"}', encoding="utf-8")
    r = _run_script(
        [
            "--input-file",
            str(p),
            "--output-dir",
            str(tmp_path / "out"),
            "--run-id",
            "operator_run_v0",
            "--confirm-no-runtime",
            "WRONG",
        ]
    )
    assert r.returncode != 0


def test_rejects_directory_input(tmp_path: Path) -> None:
    d = tmp_path / "notafile"
    d.mkdir()
    r = _run_script(
        [
            "--input-file",
            str(d),
            "--output-dir",
            str(tmp_path / "out"),
            "--run-id",
            "operator_run_v0",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
    assert "directory" in r.stderr.lower() or "directory" in r.stdout.lower()


def test_rejects_unsafe_run_id(tmp_path: Path) -> None:
    p = tmp_path / "in.json"
    p.write_text(
        '{"schema":"bounded_file_snapshot_observation_input_v0","source":"bounded_file_captured_static","snapshots":[]}',
        encoding="utf-8",
    )
    r = _run_script(
        [
            "--input-file",
            str(p),
            "--output-dir",
            str(tmp_path / "out"),
            "--run-id",
            "../evil",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0


@pytest.fixture
def valid_input() -> dict:
    return {
        "schema": "bounded_file_snapshot_observation_input_v0",
        "source": "bounded_file_captured_static",
        "snapshots": [
            {
                "symbol": "FILE-CAPTURED-OBS",
                "observed_at_utc": "2026-01-01T00:00:00Z",
                "payload": {
                    "bid": "100.10",
                    "ask": "100.15",
                    "last": "100.12",
                    "volume": "12.5",
                    "spread_bps": "4.99",
                    "state": "bounded_file_captured_static",
                    "sequence": "1",
                },
            },
            {
                "symbol": "FILE-CAPTURED-OBS",
                "observed_at_utc": "2026-01-01T00:01:00Z",
                "payload": {
                    "bid": "100.18",
                    "ask": "100.23",
                    "last": "100.20",
                    "volume": "14.0",
                    "spread_bps": "4.98",
                    "state": "bounded_file_captured_static",
                    "sequence": "2",
                },
            },
            {
                "symbol": "FILE-CAPTURED-OBS",
                "observed_at_utc": "2026-01-01T00:02:00Z",
                "payload": {
                    "bid": "100.05",
                    "ask": "100.11",
                    "last": "100.09",
                    "volume": "11.7",
                    "spread_bps": "5.99",
                    "state": "bounded_file_captured_static",
                    "sequence": "3",
                },
            },
        ],
    }


def _prov_ok(extra: Optional[dict] = None) -> dict:
    p = {
        "captured_by": "operator",
        "captured_at_utc": "2026-05-01T00:00:00Z",
        "redacted": True,
        "network_fetch_during_test": False,
        "contains_credentials": False,
        "contains_orders": False,
        "contains_fills": False,
    }
    if extra:
        p.update(extra)
    return p


def _cap_payload(sequence: str) -> dict[str, object]:
    return {
        "bid": "100.10",
        "ask": "100.15",
        "last": "100.12",
        "spread_bps": "4.99",
        "sequence": sequence,
        "volume": "12.5",
        "state": "captured_realistic_static_like",
    }


def _snap(symbol: str, ts: str, sequence: str) -> dict[str, object]:
    return {"symbol": symbol, "observed_at_utc": ts, "payload": _cap_payload(sequence)}


def captured_envelope(
    snaps: list[dict[str, object]], *, source: str = "operator_supplied_static"
) -> dict:
    return {
        "schema": _captured_schema,
        "source": source,
        "provenance": _prov_ok(),
        "snapshots": snaps,
    }


@pytest.fixture
def valid_captured_input() -> dict:
    snaps = [
        _snap("DEMO-X", "2026-01-01T00:00:00Z", "1"),
        _snap("DEMO-X", "2026-01-01T00:01:00Z", "2"),
        _snap("DEMO-X", "2026-01-01T00:02:00Z", "3"),
    ]
    return captured_envelope(snaps)


def test_happy_path_writes_evidence_and_closeout(tmp_path: Path, valid_input: dict) -> None:
    inp = tmp_path / "captured_snapshots.json"
    out = tmp_path / "evidence"
    inp.write_text(
        json.dumps(valid_input, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    run_id = "operator_file_snapshot_observation_v0"
    r = _run_script(
        [
            "--input-file",
            str(inp),
            "--output-dir",
            str(out),
            "--run-id",
            run_id,
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode == 0, r.stderr + r.stdout
    run_dir = out / run_id
    assert (run_dir / "local_run_result.json").is_file()
    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "MANIFEST.sha256").is_file()
    co = run_dir / "SHADOW_OBSERVATION_FILE_SNAPSHOT_OPERATOR_ENTRYPOINT_V0_CLOSEOUT.md"
    assert co.is_file()
    body = co.read_text(encoding="utf-8")
    assert "DECISION=not_approved" in body
    assert "LOCAL_OBSERVATION_RUN_APPROVED=false" in body
    assert "PROVEN_SHADOW_NO_ORDER_ENTRYPOINT_FOUND=false" in body
    assert "EXECUTABLE_COMMAND_CREATED=false" in body
    assert "SHADOW_OBSERVATION_OPERATOR_ENTRYPOINT_IMPLEMENTED=true" in body
    assert "LIVE_ALLOWED=false" in body
    assert "DECISION=not_approved" in r.stdout
    assert str(out.resolve()).startswith(str(tmp_path.resolve()))


def test_captured_realistic_happy_path_writes_evidence(
    tmp_path: Path, valid_captured_input: dict
) -> None:
    inp = tmp_path / "cap.json"
    out = tmp_path / "ev"
    inp.write_text(
        json.dumps(valid_captured_input, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    run_id = "captured_operator_run_v0"
    r = _run_script(
        [
            "--input-file",
            str(inp),
            "--output-dir",
            str(out),
            "--run-id",
            run_id,
            "--confirm-no-runtime",
            _CONFIRM,
        ],
    )
    assert r.returncode == 0, r.stderr + r.stdout
    run_dir = out / run_id
    assert (run_dir / "local_run_result.json").is_file()


def test_captured_requires_provenance(tmp_path: Path, valid_captured_input: dict) -> None:
    del valid_captured_input["provenance"]
    inp = tmp_path / "x.json"
    inp.write_text(json.dumps(valid_captured_input), encoding="utf-8")
    r = _run_script(
        [
            "--input-file",
            str(inp),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
    assert "provenance" in r.stderr.lower()


def test_captured_rejects_network_fetch_during_test(
    tmp_path: Path, valid_captured_input: dict
) -> None:
    valid_captured_input["provenance"] = _prov_ok({"network_fetch_during_test": True})
    inp = tmp_path / "x.json"
    inp.write_text(json.dumps(valid_captured_input), encoding="utf-8")
    r = _run_script(
        [
            "--input-file",
            str(inp),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
    assert "network_fetch_during_test" in r.stderr


@pytest.mark.parametrize("field", ["contains_credentials", "contains_orders", "contains_fills"])
def test_captured_rejects_truthy_sensitive_flags(
    tmp_path: Path, valid_captured_input: dict, field: str
) -> None:
    prov = _prov_ok()
    prov[field] = True
    valid_captured_input["provenance"] = prov
    inp = tmp_path / "x.json"
    inp.write_text(json.dumps(valid_captured_input), encoding="utf-8")
    r = _run_script(
        [
            "--input-file",
            str(inp),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
    assert field in r.stderr


def test_captured_rejects_too_few_snapshots(tmp_path: Path) -> None:
    snaps = [_snap("A", "2026-01-01T00:00:00Z", "1"), _snap("A", "2026-01-01T00:01:00Z", "2")]
    env = captured_envelope(snaps)
    inp = tmp_path / "x.json"
    inp.write_text(json.dumps(env), encoding="utf-8")
    r = _run_script(
        [
            "--input-file",
            str(inp),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
    assert "3 and 20" in r.stderr


def test_captured_rejects_too_many_snapshots(tmp_path: Path) -> None:
    snaps = [_snap("A", f"2026-05-02T{k:02d}:00:01Z", str(k)) for k in range(21)]
    env = captured_envelope(snaps)
    inp = tmp_path / "x.json"
    inp.write_text(json.dumps(env), encoding="utf-8")
    r = _run_script(
        [
            "--input-file",
            str(inp),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
    assert "3 and 20" in r.stderr


def test_captured_rejects_forbidden_payload_key(tmp_path: Path, valid_captured_input: dict) -> None:
    snaps = valid_captured_input["snapshots"]
    assert isinstance(snaps, list) and snaps
    pl = snaps[0]["payload"]
    assert isinstance(pl, dict)
    pl["my_api_key"] = "bad"
    inp = tmp_path / "x.json"
    inp.write_text(json.dumps(valid_captured_input), encoding="utf-8")
    r = _run_script(
        [
            "--input-file",
            str(inp),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
    assert "forbidden payload key" in r.stderr.lower()


def test_captured_rejects_forbidden_source_class(
    tmp_path: Path, valid_captured_input: dict
) -> None:
    valid_captured_input["source"] = "live_exchange_api"
    inp = tmp_path / "x.json"
    inp.write_text(json.dumps(valid_captured_input), encoding="utf-8")
    r = _run_script(
        [
            "--input-file",
            str(inp),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
