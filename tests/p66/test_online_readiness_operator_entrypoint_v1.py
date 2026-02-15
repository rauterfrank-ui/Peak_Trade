from pathlib import Path

import pytest

from src.ops.p66 import P66RunContextV1, run_online_readiness_operator_entrypoint_v1


def test_p66_blocks_live_record() -> None:
    prices = [0.001] * 200
    with pytest.raises(PermissionError):
        run_online_readiness_operator_entrypoint_v1(
            prices, P66RunContextV1(mode="live", run_id="x")
        )
    with pytest.raises(PermissionError):
        run_online_readiness_operator_entrypoint_v1(
            prices, P66RunContextV1(mode="record", run_id="x")
        )


def test_p66_single_shot_returns_dict(tmp_path: Path) -> None:
    prices = [0.001] * 200
    out = run_online_readiness_operator_entrypoint_v1(
        prices,
        P66RunContextV1(mode="paper", run_id="demo", out_dir=tmp_path / "p66_demo"),
    )
    assert isinstance(out, dict)
    assert out["meta"]["phase"] == "p66"
    assert out["meta"]["mode"] == "paper"
    assert out["meta"]["loop"] is False
    assert "p64" in out


def test_p66_loop_mode_returns_p65(tmp_path: Path) -> None:
    prices = [0.001] * 200
    out = run_online_readiness_operator_entrypoint_v1(
        prices,
        P66RunContextV1(
            mode="paper",
            run_id="demo",
            out_dir=tmp_path / "p66_loop",
            loop=True,
            iterations=2,
        ),
    )
    assert out["meta"]["loop"] is True
    assert "p65" in out
    assert out["p65"]["meta"]["loops"] == 2
    assert len(out["p65"]["loops"]) == 2


def test_p66_loop_sleep_seconds_nonzero_raises() -> None:
    prices = [0.001] * 200
    with pytest.raises(ValueError, match="sleep_seconds must be 0.0"):
        run_online_readiness_operator_entrypoint_v1(
            prices,
            P66RunContextV1(
                mode="paper",
                run_id="x",
                loop=True,
                iterations=1,
                sleep_seconds=1.0,
            ),
        )


def test_p66_loop_iterations_zero_raises() -> None:
    prices = [0.001] * 200
    with pytest.raises(ValueError, match="iterations must be >= 1"):
        run_online_readiness_operator_entrypoint_v1(
            prices,
            P66RunContextV1(mode="paper", run_id="x", loop=True, iterations=0),
        )
