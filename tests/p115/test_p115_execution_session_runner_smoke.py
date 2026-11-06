"""P115: Execution session runner smoke (mocks only)."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_p115_smoke_creates_evidence(tmp_path: Path) -> None:
    from src.execution.session.runner_v1 import (
        ExecutionSessionContextV1,
        run_execution_session_v1,
    )

    out_base = str(tmp_path / "execution_sessions")
    ctx = ExecutionSessionContextV1(
        mode="shadow",
        dry_run=True,
        out_base=out_base,
        ts_utc="20990101T000000Z",
    )
    rep = run_execution_session_v1(ctx)

    assert rep["ok"] is True
    evi = Path(rep["evi_dir"])
    assert evi.exists()
    assert (evi / "report.json").exists()
    assert (evi / "manifest.json").exists()
    assert (evi / "SHA256SUMS.txt").exists()
