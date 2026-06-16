"""Contract tests for P67/P72 opt-in library scheduler boundary enforce (no workloads)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
P67_LIBRARY = REPO_ROOT / "src" / "ops" / "p67" / "shadow_session_scheduler_v1.py"
P67_CLI = REPO_ROOT / "src" / "ops" / "p67" / "shadow_session_scheduler_cli_v1.py"
P72_LIBRARY = REPO_ROOT / "src" / "ops" / "p72" / "run_shadowloop_pack_v1.py"
RUN_SCHEDULER = REPO_ROOT / "scripts" / "run_scheduler.py"
SHARED_GUARD = REPO_ROOT / "scripts" / "ops" / "scheduler_start_boundary_guard_v0.py"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ops.p67.shadow_session_scheduler_v1 import (
    P67RunContextV1,
    run_shadow_session_scheduler_v1,
)
from src.ops.p72 import P72PackContextV1, run_shadowloop_pack_v1

P72_MODULE = importlib.import_module("src.ops.p72.run_shadowloop_pack_v1")


def _blocked_preflight() -> dict:
    return {
        "status": "BLOCKED",
        "scheduler_execution_authorized": False,
        "hold_context_v0": {"current_state": "CLEAR"},
    }


def _allowed_preflight() -> dict:
    return {
        "status": "READY",
        "scheduler_execution_authorized": True,
        "hold_context_v0": {"current_state": "CLEAR"},
    }


def test_p67_library_wires_scheduler_boundary_enforce_default_off() -> None:
    text = P67_LIBRARY.read_text(encoding="utf-8")
    assert "scheduler_boundary_enforce: bool = False" in text
    assert "scheduler_preflight_status" in text
    assert "assert_scheduler_start_authorized" in text
    assert "scheduler_start_boundary_guard_v0" in text
    assert "def _maybe_assert_scheduler_boundary" in text


def test_p72_library_wires_scheduler_boundary_pass_through() -> None:
    text = P72_LIBRARY.read_text(encoding="utf-8")
    assert "scheduler_boundary_enforce: bool = False" in text
    assert "scheduler_boundary_enforce=ctx.scheduler_boundary_enforce" in text
    assert "scheduler_preflight_status=ctx.scheduler_preflight_status" in text


def test_p67_cli_and_run_scheduler_unchanged() -> None:
    cli = P67_CLI.read_text(encoding="utf-8")
    guard_idx = cli.index("assert_scheduler_start_authorized")
    run_idx = cli.index("run_shadow_session_scheduler_v1(ctx)")
    assert guard_idx < run_idx
    assert "scheduler_boundary_enforce" not in cli

    rs = RUN_SCHEDULER.read_text(encoding="utf-8")
    assert "scheduler_start_boundary_guard_v0" in rs
    assert "scheduler_boundary_enforce" not in rs


def test_p67_default_context_scheduler_boundary_off() -> None:
    ctx = P67RunContextV1()
    assert ctx.scheduler_boundary_enforce is False
    assert ctx.scheduler_preflight_status is None


def test_p67_enforce_blocks_before_p66_workload(monkeypatch: pytest.MonkeyPatch) -> None:
    p66_calls: list[object] = []

    def _p66_should_not_run(*_args: object, **_kwargs: object) -> dict:
        p66_calls.append(1)
        return {"unexpected": True}

    monkeypatch.setattr(
        "src.ops.p67.shadow_session_scheduler_v1.run_online_readiness_operator_entrypoint_v1",
        _p66_should_not_run,
    )

    with pytest.raises(SystemExit) as exc:
        run_shadow_session_scheduler_v1(
            P67RunContextV1(
                mode="shadow",
                run_id="block",
                iterations=1,
                interval_seconds=0.0,
                scheduler_boundary_enforce=True,
                scheduler_preflight_status=_blocked_preflight(),
            )
        )
    assert exc.value.code == 2
    assert p66_calls == []


def test_p67_enforce_blocks_with_machine_tokens(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "src.ops.p67.shadow_session_scheduler_v1.run_online_readiness_operator_entrypoint_v1",
        lambda *_a, **_k: {"unexpected": True},
    )

    with pytest.raises(SystemExit) as exc:
        run_shadow_session_scheduler_v1(
            P67RunContextV1(
                scheduler_boundary_enforce=True,
                scheduler_preflight_status=_blocked_preflight(),
                iterations=1,
                interval_seconds=0.0,
            )
        )
    assert exc.value.code == 2
    out = capsys.readouterr().out
    assert "SCHEDULER_START_BLOCKED_BY_PREFLIGHT=true" in out


def test_p67_enforce_allows_ready_preflight_without_real_p66(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.ops.p67.shadow_session_scheduler_v1.run_online_readiness_operator_entrypoint_v1",
        lambda _prices, _ctx: {"stub": True},
    )

    out = run_shadow_session_scheduler_v1(
        P67RunContextV1(
            mode="shadow",
            run_id="allow",
            iterations=1,
            interval_seconds=0.0,
            scheduler_boundary_enforce=True,
            scheduler_preflight_status=_allowed_preflight(),
        )
    )
    assert out["events"]
    assert out["meta"]["run_id"] == "allow"


def test_p67_enforce_false_skips_guard_with_blocked_preflight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    guard_calls: list[object] = []

    def _guard_should_not_run(*_args: object, **_kwargs: object) -> None:
        guard_calls.append(1)

    monkeypatch.setattr(
        "scripts.ops.scheduler_start_boundary_guard_v0.assert_scheduler_start_authorized",
        _guard_should_not_run,
    )
    monkeypatch.setattr(
        "src.ops.p67.shadow_session_scheduler_v1.run_online_readiness_operator_entrypoint_v1",
        lambda _prices, _ctx: {"stub": True},
    )

    out = run_shadow_session_scheduler_v1(
        P67RunContextV1(
            scheduler_boundary_enforce=False,
            scheduler_preflight_status=_blocked_preflight(),
            iterations=1,
            interval_seconds=0.0,
        )
    )
    assert guard_calls == []
    assert out["events"]


def test_p72_passes_scheduler_boundary_enforce_to_p67(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: list[P67RunContextV1] = []

    def _capture_p67(ctx: P67RunContextV1) -> dict:
        captured.append(ctx)
        return {"meta": {}, "events": []}

    monkeypatch.setattr(
        P72_MODULE,
        "run_online_readiness_health_gate_v1",
        lambda *_a, **_k: {"overall_ok": True},
    )
    monkeypatch.setattr(
        P72_MODULE,
        "run_shadow_session_scheduler_v1",
        _capture_p67,
    )

    preflight = _allowed_preflight()
    run_shadowloop_pack_v1(
        P72PackContextV1(
            mode="shadow",
            run_id="pack",
            out_dir=tmp_path,
            allow_bull_strategies=["s1"],
            allow_bear_strategies=["s1"],
            iterations=1,
            interval_seconds=0.0,
            scheduler_boundary_enforce=True,
            scheduler_preflight_status=preflight,
        )
    )
    assert len(captured) == 1
    assert captured[0].scheduler_boundary_enforce is True
    assert captured[0].scheduler_preflight_status == preflight


def test_p72_enforce_blocks_via_p67_guard(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        P72_MODULE,
        "run_online_readiness_health_gate_v1",
        lambda *_a, **_k: {"overall_ok": True},
    )
    p66_calls: list[object] = []
    monkeypatch.setattr(
        "src.ops.p67.shadow_session_scheduler_v1.run_online_readiness_operator_entrypoint_v1",
        lambda *_a, **_k: p66_calls.append(1) or {"unexpected": True},
    )

    with pytest.raises(SystemExit) as exc:
        run_shadowloop_pack_v1(
            P72PackContextV1(
                mode="shadow",
                run_id="pack",
                out_dir=tmp_path,
                allow_bull_strategies=["s1"],
                allow_bear_strategies=["s1"],
                iterations=1,
                interval_seconds=0.0,
                scheduler_boundary_enforce=True,
                scheduler_preflight_status=_blocked_preflight(),
            )
        )
    assert exc.value.code == 2
    assert p66_calls == []


def test_shared_guard_module_is_canonical_owner() -> None:
    text = SHARED_GUARD.read_text(encoding="utf-8")
    p67_text = P67_LIBRARY.read_text(encoding="utf-8")
    assert "def assert_scheduler_start_authorized" in text
    assert "scheduler_start_boundary_guard_v0" in p67_text
    assert "def _emit_scheduler_start_block" not in p67_text
