"""Tests for Scheduler Boundary Hard-Block Contract v0."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = REPO_ROOT / "docs/ops/specs/SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md"
TAXONOMY = REPO_ROOT / "docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
RUN_SCHEDULER = REPO_ROOT / "scripts/run_scheduler.py"
P67_CLI = REPO_ROOT / "src/ops/p67/shadow_session_scheduler_cli_v1.py"

REQUIRED_MARKERS = (
    "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0=true",
    "SCHEDULER_START_REQUIRES_PREFLIGHT_READY=true",
    "SCHEDULER_START_REQUIRES_SCHEDULER_EXECUTION_AUTHORIZED=true",
    "SCHEDULER_HOLD_NO_PAPER_RUN_BLOCKS_START=true",
    "SCHEDULER_EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true",
    "SCHEDULER_CANNOT_AUTHORIZE_LIVE=true",
    "SCHEDULER_DRY_RUN_REMAINS_ALLOWED=true",
    "SCHEDULER_NON_DRY_RUN_FAILS_CLOSED=true",
    "MASTER_V2_DOUBLE_PLAY_BOUNDARY_PRESERVED=true",
)


def _load_run_scheduler():
    spec = importlib.util.spec_from_file_location("run_scheduler", RUN_SCHEDULER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_scheduler"] = mod
    spec.loader.exec_module(mod)
    return mod


def _allowed_preflight(**overrides: object) -> dict:
    base = {
        "status": "READY",
        "scheduler_execution_authorized": True,
        "hold_context_v0": {"current_state": "CLEAR"},
        "live_authorized": False,
        "broker_authorized": False,
        "exchange_authorized": False,
    }
    if "hold_context_v0" in overrides and isinstance(overrides["hold_context_v0"], dict):
        base["hold_context_v0"].update(overrides.pop("hold_context_v0"))  # type: ignore[arg-type]
    base.update(overrides)
    return base


@pytest.fixture
def rs():
    return _load_run_scheduler()


def test_contract_doc_exists_with_markers() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert "# Scheduler Boundary Hard-Block Contract v0" in text
    for marker in REQUIRED_MARKERS:
        assert marker in text


def test_taxonomy_crosslinks_scheduler_hard_block_contract() -> None:
    text = TAXONOMY.read_text(encoding="utf-8")
    assert "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md" in text


def test_run_scheduler_exposes_guard_function(rs) -> None:
    assert callable(rs.assert_scheduler_start_authorized)


def test_guard_blocks_status_blocked(rs, capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        rs.assert_scheduler_start_authorized(
            {
                "status": "BLOCKED",
                "scheduler_execution_authorized": False,
                "hold_context_v0": {"current_state": "CLEAR"},
            }
        )
    assert exc.value.code == rs.SCHEDULER_START_BLOCKED_EXIT
    out = capsys.readouterr().out
    assert "SCHEDULER_START_BLOCKED_BY_PREFLIGHT=true" in out
    assert "SCHEDULER_EXECUTION_AUTHORIZED=false" in out


def test_guard_blocks_scheduler_execution_authorized_false(rs) -> None:
    with pytest.raises(SystemExit) as exc:
        rs.assert_scheduler_start_authorized(
            _allowed_preflight(scheduler_execution_authorized=False)
        )
    assert exc.value.code == rs.SCHEDULER_START_BLOCKED_EXIT


def test_guard_blocks_missing_scheduler_execution_authorized(rs) -> None:
    payload = _allowed_preflight()
    del payload["scheduler_execution_authorized"]
    with pytest.raises(SystemExit) as exc:
        rs.assert_scheduler_start_authorized(payload)
    assert exc.value.code == rs.SCHEDULER_START_BLOCKED_EXIT


def test_guard_blocks_hold_no_paper_run(rs, capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        rs.assert_scheduler_start_authorized(
            _allowed_preflight(
                hold_context_v0={"current_state": "HOLD_NO_PAPER_RUN"},
            )
        )
    assert exc.value.code == rs.SCHEDULER_START_BLOCKED_EXIT
    assert "HOLD_NO_PAPER_RUN_ACTIVE=true" in capsys.readouterr().out


def test_guard_allows_ready_authorized_no_hold(rs) -> None:
    rs.assert_scheduler_start_authorized(_allowed_preflight())


def test_dry_run_main_skips_guard(rs, monkeypatch) -> None:
    guard_calls: list[object] = []
    loop_calls: list[object] = []

    def _guard(**kwargs):
        guard_calls.append(kwargs)
        raise AssertionError("guard must not run for dry-run")

    monkeypatch.setattr(rs, "assert_scheduler_start_authorized", _guard)
    monkeypatch.setattr(rs, "run_scheduler_loop", lambda **kwargs: loop_calls.append(kwargs) or 0)

    rc = rs.main(["--dry-run", "--once", "--config", "config/scheduler/jobs.toml"])
    assert rc == 0
    assert guard_calls == []
    assert len(loop_calls) == 1


def test_non_dry_run_main_calls_guard_before_loop(rs, monkeypatch) -> None:
    loop_calls: list[object] = []

    monkeypatch.setattr(
        rs,
        "assert_scheduler_start_authorized",
        lambda **kwargs: (_ for _ in ()).throw(SystemExit(rs.SCHEDULER_START_BLOCKED_EXIT)),
    )
    monkeypatch.setattr(rs, "run_scheduler_loop", lambda **kwargs: loop_calls.append(kwargs) or 0)

    with pytest.raises(SystemExit) as exc:
        rs.main(["--once", "--config", "config/scheduler/jobs.toml"])
    assert exc.value.code == rs.SCHEDULER_START_BLOCKED_EXIT
    assert loop_calls == []


def test_non_dry_run_allowed_preflight_reaches_loop(rs, monkeypatch) -> None:
    loop_calls: list[object] = []

    monkeypatch.setattr(rs, "assert_scheduler_start_authorized", lambda *args, **kwargs: None)
    monkeypatch.setattr(rs, "run_scheduler_loop", lambda **kwargs: loop_calls.append(kwargs) or 0)

    rc = rs.main(["--once", "--config", "config/scheduler/jobs.toml"])
    assert rc == 0
    assert len(loop_calls) == 1


def test_guard_module_source_has_no_network(rs) -> None:
    source = RUN_SCHEDULER.read_text(encoding="utf-8")
    assert "urllib" not in source
    assert "requests" not in source
    assert "socket" not in source


def test_allowed_fixture_keeps_live_flags_false() -> None:
    payload = _allowed_preflight()
    assert payload.get("live_authorized") is False
    assert payload.get("broker_authorized") is False


def test_p67_residual_surface_acknowledged_in_spec() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert "shadow_session_scheduler_cli_v1.py" in text
    assert P67_CLI.is_file()
