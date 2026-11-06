from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "ops" / "run_shadow_observation_supervised_timed_v0.py"
_CONFIRM = "NO_RUNTIME_NO_SCHEDULER_NO_BROKER_NO_ORDERS"
_MSCHEMA = "supervised_timed_observer_input_manifest_v0"
_MSOURCE = "operator_supplied_static_manifest"
_CSCHEMA = "captured_realistic_snapshot_observation_input_v0"
_BSCHEMA = "bounded_file_snapshot_observation_input_v0"

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
    "time.sleep",
    "subprocess",
    "datetime.now",
    "while True",
    "import schedule",
)

_MANIFEST_BASE = {
    "schema": _MSCHEMA,
    "source": _MSOURCE,
    "cadence_seconds": 60,
}


def _run_script(
    args: List[str], *, cwd: Union[Path, None] = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        cwd=cwd or _REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _prov_ok() -> Dict[str, Any]:
    return {
        "captured_by": "operator",
        "captured_at_utc": "2026-05-01T00:00:00Z",
        "redacted": True,
        "network_fetch_during_test": False,
        "contains_credentials": False,
        "contains_orders": False,
        "contains_fills": False,
    }


def _cap_payload(sequence: str) -> Dict[str, object]:
    return {
        "bid": "100.10",
        "ask": "100.15",
        "last": "100.12",
        "spread_bps": "4.99",
        "sequence": sequence,
    }


def _snap(symbol: str, ts: str, sequence: str) -> Dict[str, object]:
    return {"symbol": symbol, "observed_at_utc": ts, "payload": _cap_payload(sequence)}


def captured_envelope(
    snaps: List[Dict[str, object]], *, source: str = "operator_supplied_static"
) -> Dict[str, Any]:
    return {
        "schema": _CSCHEMA,
        "source": source,
        "provenance": _prov_ok(),
        "snapshots": snaps,
    }


def _manifest(
    inputs: List[Dict[str, Any]], *, max_obs: int = 20, cadence: int = 60
) -> Dict[str, Any]:
    return {
        **_MANIFEST_BASE,
        "cadence_seconds": cadence,
        "max_observations": max_obs,
        "inputs": inputs,
    }


def test_script_source_forbids_high_risk_patterns() -> None:
    text = _SCRIPT.read_text(encoding="utf-8").lower()
    for bad in _FORBIDDEN_SUBSTRINGS:
        assert bad.lower() not in text, f"forbidden pattern: {bad!r}"


def test_requires_input_manifest() -> None:
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
    assert "input-manifest" in (r.stderr + r.stdout).lower() or "required" in r.stderr.lower()


def test_requires_output_dir(tmp_path: Path) -> None:
    m = tmp_path / "m.json"
    m.write_text(json.dumps(_manifest([])), encoding="utf-8")
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--run-id",
            "safe_run_id",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0


def test_requires_run_id(tmp_path: Path) -> None:
    m = tmp_path / "m.json"
    m.write_text(
        json.dumps(
            _manifest(
                [{"sequence": 1, "input_file": str(tmp_path / "x"), "expected_schema": _CSCHEMA}]
            )
        ),
        encoding="utf-8",
    )
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(tmp_path / "out"),
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0


def test_requires_exact_confirmation_token(tmp_path: Path) -> None:
    m = tmp_path / "m.json"
    m.write_text("{}", encoding="utf-8")
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            "WRONG",
        ]
    )
    assert r.returncode != 0


def test_rejects_missing_manifest(tmp_path: Path) -> None:
    r = _run_script(
        [
            "--input-manifest",
            str(tmp_path / "nope.json"),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
    assert "not found" in r.stderr.lower()


def test_rejects_directory_manifest(tmp_path: Path) -> None:
    d = tmp_path / "mdir"
    d.mkdir()
    r = _run_script(
        [
            "--input-manifest",
            str(d),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0


def test_rejects_unsafe_run_id(tmp_path: Path) -> None:
    m = tmp_path / "m.json"
    m.write_text("{}", encoding="utf-8")
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "../evil",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0


def test_rejects_wrong_manifest_schema(tmp_path: Path) -> None:
    raw = dict(_MANIFEST_BASE)
    raw["schema"] = "wrong"
    raw["max_observations"] = 10
    raw["inputs"] = []
    m = tmp_path / "m.json"
    m.write_text(json.dumps(raw), encoding="utf-8")
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0


def test_rejects_wrong_manifest_source(tmp_path: Path) -> None:
    m = tmp_path / "m.json"
    man = _manifest([])
    man["source"] = "evil"
    m.write_text(json.dumps(man), encoding="utf-8")
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0


def test_rejects_glob_input_path(tmp_path: Path) -> None:
    man = _manifest(
        [
            {
                "sequence": 1,
                "input_file": str(tmp_path / "*.json"),
                "expected_schema": _CSCHEMA,
            }
        ]
    )
    m = tmp_path / "m.json"
    m.write_text(json.dumps(man), encoding="utf-8")
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
    assert "glob" in r.stderr.lower()


def test_rejects_missing_listed_input_file(tmp_path: Path) -> None:
    man = _manifest(
        [
            {
                "sequence": 1,
                "input_file": str(tmp_path / "missing.json"),
                "expected_schema": _CSCHEMA,
            }
        ],
        max_obs=10,
    )
    m = tmp_path / "m.json"
    m.write_text(json.dumps(man), encoding="utf-8")
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0


def test_rejects_directory_listed_input_file(tmp_path: Path) -> None:
    d = tmp_path / "notfile"
    d.mkdir()
    man = _manifest(
        [{"sequence": 1, "input_file": str(d), "expected_schema": _CSCHEMA}],
        max_obs=10,
    )
    m = tmp_path / "m.json"
    m.write_text(json.dumps(man), encoding="utf-8")
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0


def test_rejects_duplicate_sequence(tmp_path: Path) -> None:
    p = tmp_path / "i.json"
    snaps = [
        _snap("Z", "2026-01-01T00:00:00Z", "1"),
        _snap("Z", "2026-01-01T00:01:00Z", "2"),
        _snap("Z", "2026-01-01T00:02:00Z", "3"),
    ]
    p.write_text(json.dumps(captured_envelope(snaps)), encoding="utf-8")
    man = _manifest(
        [
            {"sequence": 1, "input_file": str(p), "expected_schema": _CSCHEMA},
            {"sequence": 1, "input_file": str(p), "expected_schema": _CSCHEMA},
        ],
        max_obs=10,
    )
    m = tmp_path / "m.json"
    m.write_text(json.dumps(man), encoding="utf-8")
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0


def test_rejects_too_many_manifest_input_entries(tmp_path: Path) -> None:
    p = tmp_path / "i.json"
    snaps = [
        _snap("Z", "2026-01-01T00:00:00Z", "1"),
        _snap("Z", "2026-01-01T00:01:00Z", "2"),
        _snap("Z", "2026-01-01T00:02:00Z", "3"),
    ]
    p.write_text(json.dumps(captured_envelope(snaps)), encoding="utf-8")
    inputs = [
        {"sequence": k, "input_file": str(p), "expected_schema": _CSCHEMA} for k in range(1, 12)
    ]
    man = _manifest(inputs, max_obs=100)
    m = tmp_path / "m.json"
    m.write_text(json.dumps(man), encoding="utf-8")
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0


def test_rejects_total_snapshots_over_max_observations(tmp_path: Path) -> None:
    p1 = tmp_path / "a.json"
    p2 = tmp_path / "b.json"
    snaps = [
        _snap("Z", "2026-01-01T00:00:00Z", "1"),
        _snap("Z", "2026-01-01T00:01:00Z", "2"),
        _snap("Z", "2026-01-01T00:02:00Z", "3"),
    ]
    p1.write_text(json.dumps(captured_envelope(snaps)), encoding="utf-8")
    p2.write_text(json.dumps(captured_envelope(snaps)), encoding="utf-8")
    man = _manifest(
        [
            {"sequence": 1, "input_file": str(p1), "expected_schema": _CSCHEMA},
            {"sequence": 2, "input_file": str(p2), "expected_schema": _CSCHEMA},
        ],
        max_obs=5,
    )
    m = tmp_path / "m.json"
    m.write_text(json.dumps(man), encoding="utf-8")
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
    assert "exceeds" in r.stderr.lower()


def test_happy_path_one_captured_realistic_file(tmp_path: Path) -> None:
    inp = tmp_path / "cap.json"
    snaps = [
        _snap("DEMO-X", "2026-01-01T00:00:00Z", "1"),
        _snap("DEMO-X", "2026-01-01T00:01:00Z", "2"),
        _snap("DEMO-X", "2026-01-01T00:02:00Z", "3"),
    ]
    inp.write_text(json.dumps(captured_envelope(snaps)), encoding="utf-8")
    man = _manifest(
        [{"sequence": 1, "input_file": str(inp), "expected_schema": _CSCHEMA}],
        max_obs=10,
    )
    m = tmp_path / "manifest.json"
    m.write_text(json.dumps(man), encoding="utf-8")
    out = tmp_path / "out"
    rid = "sup_timed_run_happy_v0"
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(out),
            "--run-id",
            rid,
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode == 0, r.stderr + r.stdout
    run_dir = out / rid
    assert (run_dir / "local_run_result.json").is_file()
    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "MANIFEST.sha256").is_file()
    co = run_dir / "SUPERVISED_TIMED_OBSERVER_V0_CLOSEOUT.md"
    assert co.is_file()
    txt = co.read_text(encoding="utf-8")
    assert "VERDICT=SUPERVISED_TIMED_OBSERVER_V0_PASSED" in txt
    assert "SUPERVISED_TIMED_OBSERVER_EXECUTED=true" in txt
    assert "DECISION=not_approved" in txt
    assert "SCHEDULER_ALLOWED=false" in txt


def test_happy_path_multiple_files_sorted_by_sequence(tmp_path: Path) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    snaps_a = [
        _snap("A", "2026-02-01T00:00:00Z", "1"),
        _snap("A", "2026-02-01T00:01:00Z", "2"),
        _snap("A", "2026-02-01T00:02:00Z", "3"),
    ]
    snaps_b = [
        _snap("B", "2026-03-01T00:00:00Z", "1"),
        _snap("B", "2026-03-01T00:01:00Z", "2"),
        _snap("B", "2026-03-01T00:02:00Z", "3"),
    ]
    first.write_text(json.dumps(captured_envelope(snaps_a)), encoding="utf-8")
    second.write_text(json.dumps(captured_envelope(snaps_b)), encoding="utf-8")
    man = _manifest(
        [
            {"sequence": 2, "input_file": str(second), "expected_schema": _CSCHEMA},
            {"sequence": 1, "input_file": str(first), "expected_schema": _CSCHEMA},
        ],
        max_obs=10,
    )
    m = tmp_path / "manifest.json"
    m.write_text(json.dumps(man), encoding="utf-8")
    out = tmp_path / "out"
    rid = "sup_timed_multi_v0"
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(out),
            "--run-id",
            rid,
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode == 0, r.stderr + r.stdout
    run_dir = out / rid
    lr = json.loads((run_dir / "local_run_result.json").read_text(encoding="utf-8"))
    recs = lr.get("records")
    assert isinstance(recs, list) and len(recs) == 6
    feb = "2026-02-01"
    mar = "2026-03-01"
    for rec in recs[:3]:
        oat = rec.get("observed_at_utc", "")
        assert isinstance(oat, str) and oat.startswith(feb)
    for rec in recs[3:]:
        oat = rec.get("observed_at_utc", "")
        assert isinstance(oat, str) and oat.startswith(mar)


def test_rejects_expected_schema_mismatch_with_file_payload(tmp_path: Path) -> None:
    p = tmp_path / "i.json"
    snaps = [
        _snap("Z", "2026-01-01T00:00:00Z", "1"),
        _snap("Z", "2026-01-01T00:01:00Z", "2"),
        _snap("Z", "2026-01-01T00:02:00Z", "3"),
    ]
    p.write_text(json.dumps(captured_envelope(snaps)), encoding="utf-8")
    man = _manifest(
        [{"sequence": 1, "input_file": str(p), "expected_schema": _BSCHEMA}],
        max_obs=10,
    )
    m = tmp_path / "m.json"
    m.write_text(json.dumps(man), encoding="utf-8")
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
    assert "does not match" in r.stderr.lower()


def test_happy_path_one_bounded_file(tmp_path: Path) -> None:
    inp = tmp_path / "bounded.json"
    inp.write_text(
        json.dumps(
            {
                "schema": _BSCHEMA,
                "source": "bounded_file_captured_static",
                "snapshots": [
                    {
                        "symbol": "BX",
                        "observed_at_utc": "2026-04-01T00:00:00Z",
                        "payload": {
                            "bid": "1",
                            "ask": "2",
                            "last": "1.5",
                            "spread_bps": "1",
                            "note": "x",
                        },
                    },
                    {
                        "symbol": "BX",
                        "observed_at_utc": "2026-04-01T00:01:00Z",
                        "payload": {
                            "bid": "1",
                            "ask": "2",
                            "last": "1.5",
                            "spread_bps": "1",
                        },
                    },
                    {
                        "symbol": "BX",
                        "observed_at_utc": "2026-04-01T00:02:00Z",
                        "payload": {
                            "bid": "1",
                            "ask": "2",
                            "last": "1.5",
                            "spread_bps": "1",
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    man = _manifest(
        [{"sequence": 1, "input_file": str(inp), "expected_schema": _BSCHEMA}],
        max_obs=10,
    )
    m = tmp_path / "manifest.json"
    m.write_text(json.dumps(man), encoding="utf-8")
    out = tmp_path / "out"
    rid = "sup_bounded_v0"
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(out),
            "--run-id",
            rid,
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert (out / rid / "SUPERVISED_TIMED_OBSERVER_V0_CLOSEOUT.md").is_file()


def test_manifest_inputs_empty_rejected(tmp_path: Path) -> None:
    m = tmp_path / "m.json"
    m.write_text(json.dumps(_manifest([])), encoding="utf-8")
    r = _run_script(
        [
            "--input-manifest",
            str(m),
            "--output-dir",
            str(tmp_path / "o"),
            "--run-id",
            "safe_rid",
            "--confirm-no-runtime",
            _CONFIRM,
        ]
    )
    assert r.returncode != 0
