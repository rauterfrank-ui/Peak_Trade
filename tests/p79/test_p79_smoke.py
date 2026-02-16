from pathlib import Path

import pytest

from src.ops.p79.supervisor_health_plan_v1 import build_health_plan_v1


def test_p79_smoke() -> None:
    assert True


def test_p79_build_plan_shadow_ok(tmp_path: Path) -> None:
    plan = build_health_plan_v1(
        mode="shadow",
        out_dir=tmp_path / "out",
        max_age_sec=300,
    )
    plan.validate()
    assert plan.mode == "shadow"
    assert plan.max_age_sec == 300


@pytest.mark.parametrize("bad_mode", ["live", "record", "LIVE", ""])
def test_p79_build_plan_blocks_live_record(bad_mode: str, tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        build_health_plan_v1(mode=bad_mode, out_dir=tmp_path)


def test_p79_build_plan_invalid_max_age(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        build_health_plan_v1(
            mode="shadow",
            out_dir=tmp_path,
            max_age_sec=0,
        )
