"""Unit tests for p85_result_reader (artifact-only, read-only)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from unittest.mock import patch

from src.ops.p85_result_reader import (
    READER_SCHEMA_VERSION,
    read_p85_exchange_observation,
)


def _write_p85(base: Path, payload: dict, *, age_offset_sec: float = 0.0) -> Path:
    d = base / "out" / "ops" / "run_x"
    d.mkdir(parents=True)
    p = d / "P85_RESULT.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    if age_offset_sec:
        old = time.time() - age_offset_sec
        os.utime(p, (old, old))
    return p


def test_reader_ok_when_fresh_and_connectivity_true(tmp_path: Path) -> None:
    _write_p85(
        tmp_path,
        {
            "connectivity": {"ok": True},
            "overall_ok": True,
        },
        age_offset_sec=60.0,
    )
    out = read_p85_exchange_observation(tmp_path)
    assert out["exchange"] == "ok"
    assert out["data_source"] == "p85_result_json"
    assert out["stale"] is False
    assert out["observation_reason"] == "p85_connectivity_ok_true"
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION
    assert out["artifact_path"] is not None


def test_reader_degraded_when_connectivity_false(tmp_path: Path) -> None:
    _write_p85(
        tmp_path,
        {"connectivity": {"ok": False, "error": "x"}},
        age_offset_sec=10.0,
    )
    out = read_p85_exchange_observation(tmp_path)
    assert out["exchange"] == "degraded"
    assert out["observation_reason"] == "p85_connectivity_ok_false"


def test_reader_unknown_when_stale(tmp_path: Path) -> None:
    _write_p85(
        tmp_path,
        {"connectivity": {"ok": True}},
        age_offset_sec=4000.0,
    )
    out = read_p85_exchange_observation(tmp_path)
    assert out["exchange"] == "unknown"
    assert out["stale"] is True
    assert out["observation_reason"] == "artifact_stale"


def test_reader_ok_when_artifact_age_equals_max_age_boundary(tmp_path: Path) -> None:
    """Boundary: age_sec == max_age_sec must not use the stale early-return (strict >)."""
    fixed_now = 1_700_000_000.0
    max_age = 250.0
    mtime = fixed_now - max_age
    d = tmp_path / "out" / "ops" / "run_boundary"
    d.mkdir(parents=True)
    p = d / "P85_RESULT.json"
    p.write_text(json.dumps({"connectivity": {"ok": True}}), encoding="utf-8")
    os.utime(p, (mtime, mtime))

    with patch("src.ops.p85_result_reader.time.time", return_value=fixed_now):
        out = read_p85_exchange_observation(tmp_path, max_age_sec=max_age)

    assert out["stale"] is False
    assert out["observation_reason"] != "artifact_stale"
    assert out["observation_reason"] == "p85_connectivity_ok_true"
    assert out["exchange"] == "ok"


def test_reader_unknown_when_malformed_json(tmp_path: Path) -> None:
    d = tmp_path / "out" / "ops" / "bad"
    d.mkdir(parents=True)
    (d / "P85_RESULT.json").write_text("{not json", encoding="utf-8")
    out = read_p85_exchange_observation(tmp_path)
    assert out["exchange"] == "unknown"
    assert out["observation_reason"] == "parse_error"


def test_reader_unknown_when_no_file(tmp_path: Path) -> None:
    (tmp_path / "out" / "ops").mkdir(parents=True)
    out = read_p85_exchange_observation(tmp_path)
    assert out["exchange"] == "unknown"
    assert out["data_source"] == "none"
    assert out["observation_reason"] == "no_p85_artifact"


def test_reader_unknown_when_connectivity_not_dict(tmp_path: Path) -> None:
    _write_p85(tmp_path, {"connectivity": "bad"}, age_offset_sec=10.0)
    out = read_p85_exchange_observation(tmp_path)
    assert out["exchange"] == "unknown"
    assert out["observation_reason"] == "connectivity_missing_or_invalid"


def test_reader_picks_newest_file_by_mtime(tmp_path: Path) -> None:
    old_dir = tmp_path / "out" / "ops" / "old"
    new_dir = tmp_path / "out" / "ops" / "new"
    old_dir.mkdir(parents=True)
    new_dir.mkdir(parents=True)
    p_old = old_dir / "P85_RESULT.json"
    p_new = new_dir / "P85_RESULT.json"
    p_old.write_text(json.dumps({"connectivity": {"ok": True}}), encoding="utf-8")
    old_ts = time.time() - 5000.0
    os.utime(p_old, (old_ts, old_ts))
    p_new.write_text(json.dumps({"connectivity": {"ok": False}}), encoding="utf-8")
    out = read_p85_exchange_observation(tmp_path)
    assert out["exchange"] == "degraded"
    assert "new" in (out.get("artifact_path") or "")


def test_reader_unknown_when_ok_not_boolean(tmp_path: Path) -> None:
    _write_p85(tmp_path, {"connectivity": {"ok": "yes"}}, age_offset_sec=10.0)
    out = read_p85_exchange_observation(tmp_path)
    assert out["exchange"] == "unknown"
    assert out["observation_reason"] == "connectivity_ok_not_boolean"
