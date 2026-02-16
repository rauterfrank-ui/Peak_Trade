"""P86 combined gate tests."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.p86 import P86RunContextV1, run_online_readiness_plus_ingest_gate_v1

# Module where run_live_data_ingest_readiness_v1 is used (for patching)
_p86_module = sys.modules["src.ops.p86.run_online_readiness_plus_ingest_gate_v1"]


def test_p86_blocks_live_record() -> None:
    with pytest.raises(PermissionError):
        run_online_readiness_plus_ingest_gate_v1(
            P86RunContextV1(mode="live", run_id="x", out_dir=Path("out/ops/p86_t1"))
        )
    with pytest.raises(PermissionError):
        run_online_readiness_plus_ingest_gate_v1(
            P86RunContextV1(mode="record", run_id="x", out_dir=Path("out/ops/p86_t2"))
        )


def test_p86_requires_outdir_under_out_ops() -> None:
    with pytest.raises(ValueError):
        run_online_readiness_plus_ingest_gate_v1(
            P86RunContextV1(mode="shadow", run_id="x", out_dir=Path("/tmp/p86"))
        )


def test_p86_requires_outdir() -> None:
    with pytest.raises(ValueError):
        run_online_readiness_plus_ingest_gate_v1(
            P86RunContextV1(mode="shadow", run_id="x", out_dir=None)
        )


def test_p86_writes_evidence_when_outdir_set(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    out_dir = root / "out" / "ops" / f"p86_test_evi_{tmp_path.name}"
    out_dir.mkdir(parents=True, exist_ok=True)

    p85_ok = {"overall_ok": True, "meta": {}, "checks": []}
    p76_ok = {"ready": True}

    with (
        patch.object(_p86_module, "run_live_data_ingest_readiness_v1", return_value=p85_ok),
        patch.object(_p86_module, "_run_p76_shell", return_value=p76_ok),
    ):
        ctx = P86RunContextV1(mode="shadow", run_id="p86_test", out_dir=out_dir)
        out = run_online_readiness_plus_ingest_gate_v1(ctx)

    assert isinstance(out, dict)
    assert out.get("overall_ok") is True
    assert (out_dir / "p86_result.json").exists()
    assert (out_dir / "manifest.json").exists()
    assert (out_dir / "P86_GATE_RESULT.json").exists()
