"""
E2E smoke: Ingress -> Orchestrator -> L3 dry-run (no network, no external tools).

- Temp out dir under repo cwd
- Run ingress with empty input -> FeatureView + EvidenceCapsule
- Feed capsule (pointer-only) into L3 path; assert artifacts exist, no raw keys, files-only
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ai_orchestration import MultiModelRunner
from src.ai_orchestration.l3_contracts import accepts_l3_pointer_only_input
from src.ai_orchestration.l3_runner import L3Runner
from src.ingress.orchestrator import OrchestratorConfig, run_ingress


@pytest.fixture
def e2e_out_dir(tmp_path: Path) -> Path:
    """Temp out dir for e2e (ingress + L3 artifacts)."""
    return tmp_path / "e2e_out"


@pytest.fixture
def fixed_clock():
    """Fixed clock for determinism."""
    from datetime import datetime, timezone

    return datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)


def test_ingress_empty_input_produces_feature_view_and_capsule(e2e_out_dir: Path) -> None:
    """Run ingress with empty input; FeatureView and Capsule files exist, pointer-only."""
    ops_base = e2e_out_dir / "ops"
    config = OrchestratorConfig(
        base_dir=ops_base,
        run_id="e2e_smoke",
        input_jsonl_path="",
    )
    fv_path, cap_path = run_ingress(config)
    assert fv_path.exists()
    assert cap_path.exists()
    fv_data = json.loads(fv_path.read_text(encoding="utf-8"))
    cap_data = json.loads(cap_path.read_text(encoding="utf-8"))
    assert "payload" not in fv_data and "payload" not in cap_data
    assert fv_data.get("run_id") == "e2e_smoke"
    assert cap_data.get("run_id") == "e2e_smoke"
    assert accepts_l3_pointer_only_input(cap_data), "Capsule must be pointer-only for L3"


def test_feed_capsule_into_l3_runner_then_multimodel_dry_run(
    e2e_out_dir: Path, fixed_clock
) -> None:
    """
    Ingress (empty) -> capsule; feed capsule to L3Runner.run(); then MultiModelRunner.dry_run(L3).
    Assert artifacts exist, no raw keys, files-only tooling implied.
    """
    ops_base = e2e_out_dir / "ops"
    l3_out = e2e_out_dir / "l3_out"
    l3_out.mkdir(parents=True, exist_ok=True)

    config = OrchestratorConfig(
        base_dir=ops_base,
        run_id="e2e_l3",
        input_jsonl_path="",
    )
    fv_path, cap_path = run_ingress(config)
    assert cap_path.exists()
    capsule_dict = json.loads(cap_path.read_text(encoding="utf-8"))
    assert accepts_l3_pointer_only_input(capsule_dict)

    # Feed capsule (pointer-only) into L3Runner
    l3_runner = L3Runner(clock=fixed_clock)
    l3_result = l3_runner.run(inputs=capsule_dict, mode="dry-run", out_dir=l3_out)
    assert l3_result.layer_id == "L3"
    assert l3_result.run_id.startswith("L3-")
    assert any("run_manifest.json" in p for p in l3_result.artifacts)
    assert any("operator_output.md" in p for p in l3_result.artifacts)
    for art in l3_result.artifacts:
        assert isinstance(art, str)
    assert (l3_out / "run_manifest.json").exists()
    assert (l3_out / "operator_output.md").exists()

    # MultiModelRunner.dry_run(L3) with separate out_dir
    l3_dispatch_out = e2e_out_dir / "l3_dispatch_out"
    l3_dispatch_out.mkdir(parents=True, exist_ok=True)
    runner = MultiModelRunner(clock=fixed_clock)
    manifest = runner.dry_run(
        layer_id="L3",
        primary_model_id="gpt-5.2-pro",
        critic_model_id="o3",
        out_dir=l3_dispatch_out,
    )
    assert manifest.layer_id == "L3"
    assert manifest.run_id.startswith("L3-")
    assert any("run_manifest.json" in a for a in manifest.artifacts)
    assert any("operator_output.md" in a for a in manifest.artifacts)
    assert (l3_dispatch_out / "run_manifest.json").exists()
    assert (l3_dispatch_out / "operator_output.md").exists()
    # Files-only tooling: L3 scope allows only files; artifacts are path strings (no raw)
    for art in manifest.artifacts:
        assert isinstance(art, str)
        assert "path" in art.lower() or art.endswith(".json") or art.endswith(".md")
