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
OWNER_GO_BASELINE_SHA = "8da476238040545d2c1e5c1bf2e950d4388dba68"


def _run_launcher(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(LAUNCHER), *args]
    return subprocess.run(
        cmd,
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )


def _root_args(tmp_path):
    return [
        "--public-store",
        str(tmp_path / "public_store"),
        "--private-store",
        str(tmp_path / "private_store"),
        "--lane-state",
        str(tmp_path / "lane_state"),
        "--evidence-root",
        str(tmp_path / "evidence"),
    ]


@pytest.mark.parametrize("persistent_paths", [True, False])
@pytest.mark.parametrize("explicit_baseline", [True, False])
def test_t_plus_launcher_01_offline_inject_invokes_supervisor(
    tmp_path: Path, explicit_baseline: bool, persistent_paths: bool
) -> None:
    proc = _run_launcher(
        "--offline-inject-session",
        "--max-cycles",
        "2",
        *(_root_args(tmp_path) if persistent_paths else []),
        *(["--origin-main-sha", OWNER_GO_BASELINE_SHA] if explicit_baseline else []),
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
    assert payload["origin_main_sha_used"] == OWNER_GO_BASELINE_SHA
    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False


@pytest.mark.parametrize("persistent_paths", [True, False])
def test_t_minus_launcher_01_invalid_owner_go_lineage_fail_closed(
    tmp_path: Path, persistent_paths: bool
) -> None:
    proc = _run_launcher(
        "--offline-inject-session",
        "--max-cycles",
        "1",
        *(_root_args(tmp_path) if persistent_paths else []),
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


@pytest.mark.parametrize("baseline", [None, "", "not-a-commit"])
def test_missing_or_invalid_declared_baseline_cannot_default_to_admission(
    monkeypatch, capsys, baseline
):
    from scripts.ops import run_n1_standing_pre_external_runtime_supervisor_v1 as entry
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_bounded_continuous_run_owner_go_wiring_v1 as owner,
    )

    monkeypatch.setattr(sys, "argv", ["supervisor", "--offline-inject-session"])
    monkeypatch.setattr(
        owner,
        "load_bounded_continuous_run_owner_go_decision_v1",
        lambda **_: {"baseline_origin_main_sha": baseline},
    )
    monkeypatch.setattr(
        entry,
        "_run_offline_inject_session",
        lambda **_: pytest.fail("unproven baseline reached session"),
    )
    assert entry.main() == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"] == "OWNER_GO_BASELINE_INVALID"
    assert payload["launcher_invoked_supervisor"] is False
