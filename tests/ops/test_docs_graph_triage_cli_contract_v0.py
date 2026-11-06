"""
CLI contract tests for scripts/ops/docs_graph_triage.py (v0).

Uses subprocess against the script entrypoint; does not duplicate unit coverage
in test_docs_graph_triage.py (ordering, escaping, categorize helpers).

Does not mutate repo paths — all artifacts live under pytest tmp_path.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "ops" / "docs_graph_triage.py"

_MIN_EMPTY_SNAPSHOT = {
    "metadata": {"nodes": 0, "edges": 0},
    "broken_targets": [],
    "broken_anchors": [],
    "orphans": [],
}


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture()
def cli_minimal_snapshot(tmp_path: Path) -> Path:
    p = tmp_path / "docs_graph_snapshot.json"
    p.write_text(json.dumps(_MIN_EMPTY_SNAPSHOT), encoding="utf-8")
    return p


def test_docs_graph_triage_cli_importable_main() -> None:
    """Main entry is importable from the ops script package path (public surface)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("docs_graph_triage_cli", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.main)


def test_docs_graph_triage_cli_success_minimal_snapshot(
    tmp_path: Path, cli_minimal_snapshot: Path
) -> None:
    out_dir = tmp_path / "triage_out"
    p = _run_cli(
        "--snapshot",
        str(cli_minimal_snapshot),
        "--out-dir",
        str(out_dir),
    )
    assert p.returncode == 0, (p.stdout, p.stderr)
    assert "DOCS GRAPH TRIAGE SUMMARY" in p.stdout
    assert "Broken targets:  0" in p.stdout
    assert "Orphaned pages:  0" in p.stdout
    assert p.stderr == ""

    assert (out_dir / "broken_targets.md").is_file()
    assert (out_dir / "orphans.md").is_file()


def test_docs_graph_triage_cli_missing_snapshot_exits_1(tmp_path: Path) -> None:
    out_dir = tmp_path / "triage_out"
    missing = tmp_path / "nope.json"
    p = _run_cli(
        "--snapshot",
        str(missing),
        "--out-dir",
        str(out_dir),
    )
    assert p.returncode == 1
    assert "Snapshot file not found" in p.stderr
    assert p.stdout == ""


def test_docs_graph_triage_cli_malformed_snapshot_exits_1(tmp_path: Path) -> None:
    snap = tmp_path / "bad.json"
    snap.write_text("{not json", encoding="utf-8")
    out_dir = tmp_path / "triage_out"

    p = _run_cli(
        "--snapshot",
        str(snap),
        "--out-dir",
        str(out_dir),
    )
    assert p.returncode == 1
    assert "Failed to load snapshot" in p.stderr
    assert p.stdout == ""
