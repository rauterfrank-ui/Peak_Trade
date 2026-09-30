"""Launcher integration tests for N=1 standing PRE_EXTERNAL runtime supervisor."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)

REPO = Path(__file__).resolve().parents[2]
LAUNCHER = REPO / "scripts/ops/run_n1_standing_pre_external_runtime_supervisor_v1.py"
OWNER_GO_BASELINE_SHA = "7a3597e61966749a9e30d06f3514e23a9179fb9e"


def _run_launcher(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(LAUNCHER), *args]
    return subprocess.run(
        cmd,
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )


def test_t_plus_launcher_01_offline_inject_invokes_supervisor(tmp_path: Path) -> None:
    proc = _run_launcher(
        "--offline-inject-session",
        "--max-cycles",
        "2",
        "--public-store",
        str(tmp_path / "public_store"),
        "--private-store",
        str(tmp_path / "private_store"),
        "--lane-state",
        str(tmp_path / "lane_state"),
        "--evidence-root",
        str(tmp_path / "evidence"),
        "--origin-main-sha",
        OWNER_GO_BASELINE_SHA,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["launcher_invoked_supervisor"] is True
    assert payload["ok"] is True
    assert payload["governed_cycle_count"] == 2
    assert payload["accepted_c1_count"] == 2
    assert payload["POST_COUNT"] == 0
    assert payload["post_allowed"] is False
    assert payload["external_effect_authorized"] is False
    assert payload["real_venue_post_allowed"] is False
    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False


def test_t_minus_launcher_01_invalid_owner_go_lineage_fail_closed(tmp_path: Path) -> None:
    proc = _run_launcher(
        "--offline-inject-session",
        "--max-cycles",
        "1",
        "--public-store",
        str(tmp_path / "public_store"),
        "--private-store",
        str(tmp_path / "private_store"),
        "--lane-state",
        str(tmp_path / "lane_state"),
        "--evidence-root",
        str(tmp_path / "evidence"),
        "--origin-main-sha",
        "f770a434e5a3f3e95630b236fa29f3536dc9b855",
    )
    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "OWNER_GO" in combined or "ok" in proc.stdout
    if proc.stdout.strip():
        payload = json.loads(proc.stdout)
        assert payload.get("ok") is False
        assert payload.get("launcher_invoked_supervisor") is True
