"""P87 — supervisor plus ingest gate tests."""

from pathlib import Path

import pytest

from src.ops.p78.online_readiness_supervisor_plan_v1 import build_supervisor_plan_v1


def test_p87_smoke() -> None:
    assert True


def test_p87_plan_gate_variant_default(tmp_path: Path) -> None:
    plan = build_supervisor_plan_v1(mode="shadow", out_dir=tmp_path, run_id="p87", iterations=1)
    assert plan.gate_variant == "p86"


def test_p87_plan_gate_variant_p76(tmp_path: Path) -> None:
    plan = build_supervisor_plan_v1(
        mode="shadow",
        out_dir=tmp_path,
        run_id="p87",
        gate_variant="p76",
    )
    assert plan.gate_variant == "p76"


@pytest.mark.parametrize("bad", ["p85", "p71", "live", ""])
def test_p87_plan_gate_variant_validation(bad: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        build_supervisor_plan_v1(mode="shadow", out_dir=tmp_path, run_id="x", gate_variant=bad)


def test_p87_supervisor_tick_writes_p86_artifacts(tmp_path: Path) -> None:
    """One supervisor tick with CHECK_MODE=p86 produces P86 artifacts in tick dir."""
    root = Path(__file__).resolve().parents[2]
    out_dir = root / "out" / "ops" / f"p87_test_{tmp_path.name}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_str = str(out_dir)

    result = __import__("subprocess").run(
        [
            "bash",
            "scripts/ops/online_readiness_supervisor_v1.sh",
        ],
        env={
            **__import__("os").environ,
            "SUPERVISOR_ENABLE": "YES",
            "OUT_DIR": out_str,
            "ITERATIONS": "1",
            "INTERVAL": "0",
            "CHECK_MODE": "p86",
            "MODE": "shadow",
            "RUN_ID": "p87_test",
        },
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        timeout=180,
    )

    tick_dirs = list(out_dir.glob("tick_*"))
    assert len(tick_dirs) >= 1, f"expected tick dir, got {list(out_dir.iterdir())}"
    tick_dir = tick_dirs[0]
    # P86 gate writes P86_GATE_RESULT.json and/or p86_result.json into tick dir
    assert (tick_dir / "P86_GATE_RESULT.json").exists() or (
        tick_dir / "p86_result.json"
    ).exists(), f"expected P86 artifacts in {tick_dir}, got {list(tick_dir.iterdir())}"
