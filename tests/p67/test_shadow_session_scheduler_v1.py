from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.p67.shadow_session_scheduler_v1 import (
    P67RunContextV1,
    run_shadow_session_scheduler_v1,
)


def test_p67_denies_live_record() -> None:
    with pytest.raises(PermissionError):
        run_shadow_session_scheduler_v1(
            P67RunContextV1(mode="live", iterations=1, interval_seconds=0.0)
        )
    with pytest.raises(PermissionError):
        run_shadow_session_scheduler_v1(
            P67RunContextV1(mode="record", iterations=1, interval_seconds=0.0)
        )


def test_p67_paper_allowed() -> None:
    out = run_shadow_session_scheduler_v1(
        P67RunContextV1(mode="paper", iterations=1, interval_seconds=0.0)
    )
    assert out["meta"]["mode"] == "paper"


def test_p67_invalid_iterations() -> None:
    with pytest.raises(ValueError):
        run_shadow_session_scheduler_v1(P67RunContextV1(iterations=0))


def test_p67_no_outdir_no_write(tmp_path: Path) -> None:
    out = run_shadow_session_scheduler_v1(
        P67RunContextV1(mode="shadow", iterations=1, interval_seconds=0.0)
    )
    assert "meta" in out and "events" in out
    assert not any(tmp_path.iterdir())


def test_p67_writes_scheduler_manifest_when_outdir_set(tmp_path: Path) -> None:
    ctx = P67RunContextV1(
        mode="shadow",
        iterations=1,
        interval_seconds=0.0,
        out_dir=tmp_path,
        run_id="t",
    )
    out = run_shadow_session_scheduler_v1(ctx)
    root = tmp_path / "p67_shadow_session_t"
    assert (root / "meta.json").exists()
    assert (root / "events.json").exists()
    assert (root / "manifest.json").exists()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["files"] == ["meta.json", "events.json"]
    assert out["meta"]["run_id"] == "t"


def test_p67_deterministic_same_input_same_output(tmp_path: Path) -> None:
    ctx = P67RunContextV1(
        mode="paper",
        iterations=1,
        interval_seconds=0.0,
        out_dir=tmp_path,
        run_id="d",
    )
    a = run_shadow_session_scheduler_v1(ctx)
    b = run_shadow_session_scheduler_v1(ctx)
    # allow timestamp drift in meta; compare stable fields + event structure
    assert a["meta"]["mode"] == b["meta"]["mode"]
    assert a["meta"]["iterations"] == b["meta"]["iterations"]
    assert len(a["events"]) == len(b["events"]) == 1
    assert "p66" in a["events"][0]
