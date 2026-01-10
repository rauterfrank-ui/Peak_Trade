"""
Tests for L2 Runner

Tests L2 Market Outlook orchestration (offline-only, replay mode).
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.ai_orchestration import L2Runner
from src.ai_orchestration.l2_runner import SoDViolation, CapabilityScopeViolation


@pytest.fixture
def fixed_clock():
    """Fixed datetime for determinism."""
    return datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_transcript_path():
    """Path to sample transcript."""
    return Path("tests/fixtures/transcripts/l2_market_outlook_sample.json")


@pytest.fixture
def tmp_evidence_dir(tmp_path):
    """Temporary evidence pack directory."""
    return tmp_path / "l2_evidence"


def test_l2_runner_replay_mode_success(fixed_clock, sample_transcript_path, tmp_evidence_dir):
    """Test L2 runner in replay mode (success case)."""
    runner = L2Runner(clock=fixed_clock)

    result = runner.run(
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
    )

    # Check result
    assert result.run_id.startswith("L2-")
    assert result.evidence_pack_id.startswith("EVP-L2-")
    assert result.layer_id == "L2"
    assert result.mode == "replay"
    assert result.sod_result == "PASS"
    assert result.capability_scope_result == "PASS"

    # Check artifacts exist
    assert len(result.artifacts) == 7
    assert (tmp_evidence_dir / "evidence_pack.json").exists()
    assert (tmp_evidence_dir / "run_manifest.json").exists()
    assert (tmp_evidence_dir / "operator_output.md").exists()
    assert (tmp_evidence_dir / "proposer_output.json").exists()
    assert (tmp_evidence_dir / "critic_output.json").exists()
    assert (tmp_evidence_dir / "sod_check.json").exists()
    assert (tmp_evidence_dir / "capability_scope_check.json").exists()


def test_l2_runner_proposer_output_structure(
    fixed_clock, sample_transcript_path, tmp_evidence_dir
):
    """Test proposer output structure."""
    runner = L2Runner(clock=fixed_clock)

    result = runner.run(
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
    )

    # Load proposer_output.json
    with open(tmp_evidence_dir / "proposer_output.json") as f:
        proposer = json.load(f)

    # Check structure
    assert proposer["model_id"] == "gpt-5.2-pro"
    assert proposer["run_id"].startswith("proposer-run-")
    assert proposer["prompt_hash"].startswith("sha256:")
    assert proposer["output_hash"].startswith("sha256:")
    assert "Market Outlook Q1 2026" in proposer["content"]
    assert "metadata" in proposer


def test_l2_runner_critic_output_structure(fixed_clock, sample_transcript_path, tmp_evidence_dir):
    """Test critic output structure."""
    runner = L2Runner(clock=fixed_clock)

    result = runner.run(
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
    )

    # Load critic_output.json
    with open(tmp_evidence_dir / "critic_output.json") as f:
        critic = json.load(f)

    # Check structure
    assert critic["model_id"] == "deepseek-r1"
    assert critic["run_id"].startswith("critic-run-")
    assert critic["decision"] in ["APPROVE", "APPROVE_WITH_CHANGES", "REJECT"]
    assert "rationale" in critic
    assert "evidence_ids" in critic
    assert isinstance(critic["evidence_ids"], list)
    assert len(critic["evidence_ids"]) > 0


def test_l2_runner_sod_check(fixed_clock, sample_transcript_path, tmp_evidence_dir):
    """Test SoD check in evidence pack."""
    runner = L2Runner(clock=fixed_clock)

    result = runner.run(
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
    )

    # Load sod_check.json
    with open(tmp_evidence_dir / "sod_check.json") as f:
        sod_check = json.load(f)

    # Check structure
    assert sod_check["proposer_model_id"] == "gpt-5.2-pro"
    assert sod_check["critic_model_id"] == "deepseek-r1"
    assert sod_check["result"] == "PASS"
    assert "Proposer (gpt-5.2-pro) != Critic (deepseek-r1)" in sod_check["reason"]


def test_l2_runner_capability_scope_check(
    fixed_clock, sample_transcript_path, tmp_evidence_dir
):
    """Test capability scope check in evidence pack."""
    runner = L2Runner(clock=fixed_clock)

    result = runner.run(
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
    )

    # Load capability_scope_check.json
    with open(tmp_evidence_dir / "capability_scope_check.json") as f:
        scope_check = json.load(f)

    # Check structure
    assert scope_check["result"] == "PASS"
    assert scope_check["violations"] == []
    assert isinstance(scope_check["checked_outputs"], list)


def test_l2_runner_with_findings_and_actions(
    fixed_clock, sample_transcript_path, tmp_evidence_dir
):
    """Test L2 runner with findings and actions."""
    runner = L2Runner(clock=fixed_clock)

    findings = ["Test finding 1", "Test finding 2"]
    actions = ["Test action 1"]

    result = runner.run(
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
        findings=findings,
        actions=actions,
    )

    # Check operator_output.md includes findings/actions
    operator_output = (tmp_evidence_dir / "operator_output.md").read_text()

    assert "Test finding 1" in operator_output
    assert "Test finding 2" in operator_output
    assert "Test action 1" in operator_output


def test_l2_runner_deterministic_run_id(fixed_clock, sample_transcript_path, tmp_path):
    """Test run_id is deterministic."""
    runner = L2Runner(clock=fixed_clock)

    # Run 1
    out_dir1 = tmp_path / "run1"
    result1 = runner.run(
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=out_dir1,
    )

    # Run 2 (same inputs)
    out_dir2 = tmp_path / "run2"
    result2 = runner.run(
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=out_dir2,
    )

    # Same inputs -> same run_id
    assert result1.run_id == result2.run_id


def test_l2_runner_evidence_pack_json_golden(
    fixed_clock, sample_transcript_path, tmp_evidence_dir
):
    """Test evidence_pack.json golden snapshot."""
    runner = L2Runner(clock=fixed_clock)

    result = runner.run(
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
    )

    # Load evidence_pack.json
    with open(tmp_evidence_dir / "evidence_pack.json") as f:
        evidence_pack = json.load(f)

    # Golden snapshot assertions
    assert evidence_pack["evidence_pack_version"] == "2.0"
    assert evidence_pack["layer_id"] == "L2"
    assert evidence_pack["layer_name"] == "Market Outlook"
    assert evidence_pack["mode"] == "replay"
    assert evidence_pack["network_used"] is False
    assert evidence_pack["matrix_version"] == "v1.0"
    assert evidence_pack["registry_version"] == "1.0"

    # Check artifacts list is sorted
    artifacts = evidence_pack["artifacts"]
    assert artifacts == sorted(artifacts)

    # Check keys are sorted
    keys = list(evidence_pack.keys())
    assert keys == sorted(keys)


def test_l2_runner_missing_transcript_error(fixed_clock, tmp_evidence_dir):
    """Test error when transcript is missing."""
    runner = L2Runner(clock=fixed_clock)

    with pytest.raises(Exception, match="(Transcript not found|No transcript found)"):
        runner.run(
            mode="replay",
            transcript_path=Path("nonexistent.json"),
            out_dir=tmp_evidence_dir,
        )


def test_l2_runner_mode_requires_transcript(fixed_clock, tmp_evidence_dir):
    """Test error when replay mode has no transcript."""
    runner = L2Runner(clock=fixed_clock)

    with pytest.raises(Exception, match="Transcript path required"):
        runner.run(
            mode="replay",
            transcript_path=None,
            out_dir=tmp_evidence_dir,
        )
