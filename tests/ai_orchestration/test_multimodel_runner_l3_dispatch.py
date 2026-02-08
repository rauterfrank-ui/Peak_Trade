"""
MultiModelRunner L3 dispatch tests.

- layer_id="L3" is routed to L3Runner (pointer-only, files-only).
- Return is RunManifest with L3 traits; no execution.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.ai_orchestration import MultiModelRunner, RunManifest


@pytest.fixture
def fixed_clock():
    return datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def tmp_out_dir(tmp_path):
    return tmp_path / "l3_dispatch_output"


def test_multimodel_runner_routes_l3_to_l3_runner(fixed_clock, tmp_out_dir):
    """MultiModelRunner.dry_run(layer_id='L3') returns RunManifest from L3 path."""
    runner = MultiModelRunner(clock=fixed_clock)

    manifest = runner.dry_run(
        layer_id="L3",
        primary_model_id="gpt-5.2-pro",
        critic_model_id="o3",
        out_dir=tmp_out_dir,
    )

    assert isinstance(manifest, RunManifest)
    assert manifest.layer_id == "L3"
    assert manifest.run_id.startswith("L3-")
    assert manifest.run_type == "dry-run"
    assert manifest.sod_result in ("PASS", "FAIL")
    assert any("run_manifest.json" in p for p in manifest.artifacts)
    assert any("operator_output.md" in p for p in manifest.artifacts)


def test_l3_dispatch_writes_artifacts(fixed_clock, tmp_out_dir):
    """L3 path writes run_manifest.json and operator_output.md (files-only)."""
    runner = MultiModelRunner(clock=fixed_clock)

    runner.dry_run(
        layer_id="L3",
        primary_model_id="gpt-5.2-pro",
        critic_model_id="o3",
        out_dir=tmp_out_dir,
    )

    assert (tmp_out_dir / "run_manifest.json").exists()
    assert (tmp_out_dir / "operator_output.md").exists()

    manifest_json = json.loads((tmp_out_dir / "run_manifest.json").read_text())
    assert manifest_json["layer_id"] == "L3"
    assert manifest_json["run_id"].startswith("L3-")


def test_l3_dispatch_pointer_only_no_execution(fixed_clock, tmp_out_dir):
    """L3 path uses pointer-only input (no raw payload); artifacts are paths only."""
    runner = MultiModelRunner(clock=fixed_clock)

    manifest = runner.dry_run(
        layer_id="L3",
        primary_model_id="gpt-5.2-pro",
        critic_model_id="o3",
        out_dir=tmp_out_dir,
    )

    # Artifacts are path strings only (L3Runner enforces pointer-only / files-only)
    for art in manifest.artifacts:
        assert isinstance(art, str)
        assert "path" in art.lower() or art.endswith(".json") or art.endswith(".md")
