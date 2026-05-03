"""
CLI contract tests for scripts/ops/docs_graph_snapshot.py (v0).

Complements tests/ops/test_docs_graph.py by driving the script entry via subprocess
(`--help` smoke + fixture-backed runs). All snapshot JSON is written under tmp_path only.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "ops" / "docs_graph_snapshot.py"
_FIXTURE_ROOT = _REPO_ROOT / "tests" / "fixtures" / "docs_graph"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture()
def fixture_root() -> Path:
    assert _FIXTURE_ROOT.is_dir()
    return _FIXTURE_ROOT.resolve()


def test_docs_graph_snapshot_cli_help_exits_zero() -> None:
    proc = _run_cli("--help")
    assert proc.returncode == 0
    assert "snapshot" in proc.stdout.lower() or "graph" in proc.stdout.lower()
    assert proc.stderr == ""


def test_docs_graph_snapshot_cli_writes_json_under_tmp(
    tmp_path: Path,
    fixture_root: Path,
) -> None:
    out = tmp_path / "docs_graph_snapshot.json"
    proc = _run_cli(
        "--repo-root",
        str(fixture_root),
        "--roots",
        "README.md",
        "--out",
        str(out),
    )

    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "snapshot" in proc.stderr.lower() or "JSON" in proc.stderr
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert payload.get("schema_version") == "1.0.0"
    assert payload.get("roots") == ["README.md"]
    assert str(fixture_root) in payload.get("repo_root", "")
    stats = payload.get("stats") or {}
    assert isinstance(stats.get("nodes"), int)
    assert isinstance(stats.get("edges"), int)
    assert isinstance(payload.get("nodes"), list)
    assert isinstance(payload.get("edges"), list)
    assert isinstance(payload.get("broken_targets"), list)


def test_docs_graph_snapshot_cli_fail_on_broken_exits_one(
    tmp_path: Path,
    fixture_root: Path,
) -> None:
    out = tmp_path / "snap_fail.json"

    proc = _run_cli(
        "--repo-root",
        str(fixture_root),
        "--roots",
        "README.md",
        "--out",
        str(out),
        "--fail-on-broken",
    )

    assert proc.returncode == 1
    assert "broken" in proc.stderr.lower()
    assert proc.stdout == ""
    assert out.is_file()


def test_docs_graph_snapshot_cli_missing_repo_root_exits_one(tmp_path: Path) -> None:
    bad_root = tmp_path / "missing_repo"
    out = tmp_path / "snap.json"

    proc = _run_cli(
        "--repo-root",
        str(bad_root),
        "--roots",
        "README.md",
        "--out",
        str(out),
    )

    assert proc.returncode == 1
    assert "Repository root not found" in proc.stderr or "not found" in proc.stderr
    assert proc.stdout == ""


def test_docs_graph_snapshot_cli_max_nodes_cap_exceeds_exits_one(
    tmp_path: Path,
    fixture_root: Path,
) -> None:
    out = tmp_path / "snap_cap.json"

    proc = _run_cli(
        "--repo-root",
        str(fixture_root),
        "--roots",
        "README.md",
        "--out",
        str(out),
        "--max-nodes",
        "2",
    )

    assert proc.returncode == 1
    assert "exceeds safety cap" in proc.stderr.lower() or "cap" in proc.stderr.lower()
    assert proc.stdout == ""
