"""E2E: L2→L3 handoff dry-run (pointer-only, deterministic, learnable gate)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ingress.orchestrator.l2_to_l3_handoff import run_l3_dry_run_from_l2_capsule


def _minimal_l2_capsule(*, learnable_surfaces=None):
    d = {
        "run_id": "L2-test",
        "ts_ms": 0,
        "artifacts": [],
        "labels": {"source": "unit"},
    }
    if learnable_surfaces is not None:
        d["learnable_surfaces"] = learnable_surfaces
    return d


@pytest.mark.parametrize("lsurfaces", [None, [], ["prompt_template_variants"]])
def test_l2_to_l3_handoff_dry_run_smoke(tmp_path: Path, lsurfaces) -> None:
    out_dir = tmp_path / "l3_out"
    res = run_l3_dry_run_from_l2_capsule(
        _minimal_l2_capsule(learnable_surfaces=lsurfaces),
        out_dir=out_dir,
    )

    assert res.run_id.startswith("L3-")
    assert "l3_out" in res.out_dir
    assert len(res.artifacts) >= 2

    manifest = out_dir / "run_manifest.json"
    op = out_dir / "operator_output.md"
    assert manifest.exists()
    assert op.exists()

    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data.get("layer_id") == "L3"
    assert str(data.get("run_id", "")).startswith("L3-")

    arts = data.get("artifacts", [])
    assert isinstance(arts, list)
    for a in arts:
        assert isinstance(a, str)

    # pointer-only scan (best-effort)
    blob = (manifest.read_text(encoding="utf-8") + "\n" + op.read_text(encoding="utf-8")).lower()
    for bad in ["payload", "raw", "transcript", "api_key", "secret", "token", "content"]:
        assert bad not in blob


def test_l2_to_l3_handoff_disallowed_surface_blocks(tmp_path: Path) -> None:
    out_dir = tmp_path / "l3_out"
    with pytest.raises(Exception) as exc_info:
        run_l3_dry_run_from_l2_capsule(
            _minimal_l2_capsule(learnable_surfaces=["scenario_priors"]),
            out_dir=out_dir,
        )
    msg = str(exc_info.value).lower()
    assert "learnable" in msg
