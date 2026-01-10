"""
Tests for MultiModelRunner Dry-Run and Manifest Generation

Tests orchestration validation and artifact generation (no real model calls).
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.ai_orchestration import (
    MultiModelRunner,
    RunManifest,
    RunManifestGenerator,
    InvalidLayerError,
    ForbiddenAutonomyError,
    DryRunError,
    generate_operator_output,
)
from src.ai_orchestration.models import SoDResult


@pytest.fixture
def fixed_clock():
    """Fixed datetime for determinism."""
    return datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def tmp_out_dir(tmp_path):
    """Temporary output directory."""
    return tmp_path / "dry_run_output"


def test_runner_dry_run_l2_success(fixed_clock, tmp_out_dir):
    """Test successful L2 dry-run."""
    runner = MultiModelRunner(clock=fixed_clock)

    manifest = runner.dry_run(
        layer_id="L2",
        primary_model_id="gpt-5.2-pro",
        critic_model_id="deepseek-r1",
        out_dir=tmp_out_dir,
    )

    # Check manifest
    assert manifest.layer_id == "L2"
    assert manifest.layer_name == "Market Outlook"
    assert manifest.autonomy_level == "PROP"
    assert manifest.primary_model_id == "gpt-5.2-pro"
    assert manifest.critic_model_id == "deepseek-r1"
    assert manifest.sod_result == SoDResult.PASS.value
    assert manifest.run_type == "dry-run"

    # Check artifacts were created
    assert (tmp_out_dir / "run_manifest.json").exists()
    assert (tmp_out_dir / "operator_output.md").exists()

    # Check manifest JSON is valid
    manifest_json = json.loads((tmp_out_dir / "run_manifest.json").read_text())
    assert manifest_json["layer_id"] == "L2"
    assert manifest_json["sod_result"] == "PASS"


def test_runner_dry_run_l0_success(fixed_clock, tmp_out_dir):
    """Test successful L0 dry-run."""
    runner = MultiModelRunner(clock=fixed_clock)

    manifest = runner.dry_run(
        layer_id="L0",
        primary_model_id="gpt-5.2",
        critic_model_id="deepseek-r1",
        out_dir=tmp_out_dir,
    )

    assert manifest.layer_id == "L0"
    assert manifest.layer_name == "Ops/Docs"
    assert manifest.autonomy_level == "REC"


def test_runner_dry_run_invalid_layer(tmp_out_dir):
    """Test dry-run fails with invalid layer."""
    runner = MultiModelRunner()

    with pytest.raises(InvalidLayerError):
        runner.dry_run(
            layer_id="L99",
            primary_model_id="gpt-5.2-pro",
            critic_model_id="deepseek-r1",
            out_dir=tmp_out_dir,
        )


def test_runner_dry_run_invalid_model(tmp_out_dir):
    """Test dry-run fails with invalid model."""
    runner = MultiModelRunner()

    with pytest.raises(DryRunError, match="Model validation failed"):
        runner.dry_run(
            layer_id="L2",
            primary_model_id="nonexistent-model",
            critic_model_id="deepseek-r1",
            out_dir=tmp_out_dir,
        )


def test_runner_dry_run_sod_violation(tmp_out_dir):
    """Test dry-run fails with SoD violation."""
    runner = MultiModelRunner()

    with pytest.raises(DryRunError, match="SoD check failed"):
        runner.dry_run(
            layer_id="L2",
            primary_model_id="gpt-5.2-pro",
            critic_model_id="gpt-5.2-pro",  # Same as primary
            out_dir=tmp_out_dir,
        )


def test_manifest_generator_deterministic_run_id(fixed_clock):
    """Test run_id is deterministic."""
    generator = RunManifestGenerator(clock=fixed_clock)

    manifest1 = generator.generate(
        layer_id="L2",
        layer_name="Market Outlook",
        autonomy_level="PROP",
        primary_model_id="gpt-5.2-pro",
        fallback_model_ids=["gpt-5.2"],
        critic_model_id="deepseek-r1",
        capability_scope_id="L2_market_outlook",
        capability_scope_version="1.0",
        sod_result=SoDResult.PASS,
        sod_reason="Test",
    )

    manifest2 = generator.generate(
        layer_id="L2",
        layer_name="Market Outlook",
        autonomy_level="PROP",
        primary_model_id="gpt-5.2-pro",
        fallback_model_ids=["gpt-5.2"],
        critic_model_id="deepseek-r1",
        capability_scope_id="L2_market_outlook",
        capability_scope_version="1.0",
        sod_result=SoDResult.PASS,
        sod_reason="Test",
    )

    # Same inputs -> same run_id
    assert manifest1.run_id == manifest2.run_id
    assert manifest1.timestamp == manifest2.timestamp


def test_manifest_to_json_stable_keys(fixed_clock):
    """Test manifest JSON has stable sorted keys."""
    generator = RunManifestGenerator(clock=fixed_clock)

    manifest = generator.generate(
        layer_id="L2",
        layer_name="Market Outlook",
        autonomy_level="PROP",
        primary_model_id="gpt-5.2-pro",
        fallback_model_ids=["gpt-5.2"],
        critic_model_id="deepseek-r1",
        capability_scope_id="L2_market_outlook",
        capability_scope_version="1.0",
        sod_result=SoDResult.PASS,
        sod_reason="Test",
    )

    json_str = manifest.to_json()
    data = json.loads(json_str)

    # Keys should be sorted (JSON spec: sort_keys=True)
    keys = list(data.keys())
    assert keys == sorted(keys)


def test_generate_operator_output(fixed_clock):
    """Test operator output markdown generation."""
    generator = RunManifestGenerator(clock=fixed_clock)

    manifest = generator.generate(
        layer_id="L2",
        layer_name="Market Outlook",
        autonomy_level="PROP",
        primary_model_id="gpt-5.2-pro",
        fallback_model_ids=["gpt-5.2"],
        critic_model_id="deepseek-r1",
        capability_scope_id="L2_market_outlook",
        capability_scope_version="1.0",
        sod_result=SoDResult.PASS,
        sod_reason="Test SoD",
    )

    output = generate_operator_output(
        manifest=manifest,
        findings=["Test finding 1"],
        actions=["Test action 1"],
    )

    # Check markdown structure
    assert "AI Autonomy — Operator Output" in output
    assert manifest.run_id in output
    assert manifest.layer_id in output
    assert manifest.primary_model_id in output
    assert "Test finding 1" in output
    assert "Test action 1" in output
    assert "END OF OPERATOR OUTPUT" in output


def test_runner_with_findings_and_actions(fixed_clock, tmp_out_dir):
    """Test dry-run with findings and actions."""
    runner = MultiModelRunner(clock=fixed_clock)

    manifest = runner.dry_run(
        layer_id="L2",
        primary_model_id="gpt-5.2-pro",
        critic_model_id="deepseek-r1",
        out_dir=tmp_out_dir,
        findings=["Test finding"],
        actions=["Test action"],
    )

    # Check operator output includes findings/actions
    output_path = tmp_out_dir / "operator_output.md"
    output_text = output_path.read_text()

    assert "Test finding" in output_text
    assert "Test action" in output_text


def test_manifest_artifacts_list_populated(fixed_clock, tmp_out_dir):
    """Test that manifest artifacts list is populated."""
    runner = MultiModelRunner(clock=fixed_clock)

    manifest = runner.dry_run(
        layer_id="L2",
        primary_model_id="gpt-5.2-pro",
        critic_model_id="deepseek-r1",
        out_dir=tmp_out_dir,
    )

    # Check artifacts list
    assert len(manifest.artifacts) == 2
    assert any("run_manifest.json" in a for a in manifest.artifacts)
    assert any("operator_output.md" in a for a in manifest.artifacts)
    assert manifest.operator_output_path is not None
