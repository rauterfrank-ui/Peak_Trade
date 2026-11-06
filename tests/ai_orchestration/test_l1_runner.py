"""
Tests for L1 Runner

Tests L1 DeepResearch orchestration (offline-only, replay mode).
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.ai_orchestration import L1Runner
from src.ai_orchestration.l1_runner import SoDViolation, CapabilityScopeViolation


@pytest.fixture
def fixed_clock():
    """Fixed datetime for determinism."""
    return datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_transcript_path():
    """Path to sample transcript."""
    return Path("tests/fixtures/transcripts/l1_deepresearch_sample.json")


@pytest.fixture
def tmp_evidence_dir(tmp_path):
    """Temporary evidence pack directory."""
    return tmp_path / "l1_evidence"


def test_l1_runner_replay_mode_success(fixed_clock, sample_transcript_path, tmp_evidence_dir):
    """Test L1 runner in replay mode (success case)."""
    runner = L1Runner(clock=fixed_clock)

    result = runner.run(
        question="What are the best practices for VaR backtesting in quantitative finance?",
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
    )

    # Check result
    assert result.run_id.startswith("L1-")
    assert result.evidence_pack_id.startswith("EVP-L1-")
    assert result.layer_id == "L1"
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


def test_l1_runner_proposer_output_structure(fixed_clock, sample_transcript_path, tmp_evidence_dir):
    """Test proposer output structure."""
    runner = L1Runner(clock=fixed_clock)

    result = runner.run(
        question="What are the best practices for VaR backtesting in quantitative finance?",
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
    )

    # Load proposer_output.json
    with open(tmp_evidence_dir / "proposer_output.json") as f:
        proposer = json.load(f)

    # Check structure
    assert proposer["model_id"] == "o3-deep-research"
    assert proposer["run_id"].startswith("proposer-run-")
    assert proposer["prompt_hash"].startswith("sha256:")
    assert proposer["output_hash"].startswith("sha256:")
    assert "VaR Backtesting Best Practices" in proposer["content"]
    assert "metadata" in proposer
    assert "research_question" in proposer["metadata"]


def test_l1_runner_critic_output_structure(fixed_clock, sample_transcript_path, tmp_evidence_dir):
    """Test critic output structure."""
    runner = L1Runner(clock=fixed_clock)

    result = runner.run(
        question="What are the best practices for VaR backtesting in quantitative finance?",
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
    )

    # Load critic_output.json
    with open(tmp_evidence_dir / "critic_output.json") as f:
        critic = json.load(f)

    # Check structure
    assert critic["model_id"] == "o3-pro"
    assert critic["run_id"].startswith("critic-run-")
    assert critic["prompt_hash"].startswith("sha256:")
    assert critic["output_hash"].startswith("sha256:")
    assert "decision" in critic
    assert critic["decision"] == "APPROVE_WITH_CHANGES"
    assert "rationale" in critic
    assert "evidence_ids" in critic


def test_l1_runner_sod_check(fixed_clock, sample_transcript_path, tmp_evidence_dir):
    """Test SoD check result."""
    runner = L1Runner(clock=fixed_clock)

    result = runner.run(
        question="What are the best practices for VaR backtesting in quantitative finance?",
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
    )

    # Load sod_check.json
    with open(tmp_evidence_dir / "sod_check.json") as f:
        sod = json.load(f)

    # Check SoD
    assert sod["result"] == "PASS"
    assert sod["proposer_model_id"] == "o3-deep-research"
    assert sod["critic_model_id"] == "o3-pro"
    assert "o3-deep-research" in sod["reason"]
    assert "o3-pro" in sod["reason"]


def test_l1_runner_capability_scope_check(fixed_clock, sample_transcript_path, tmp_evidence_dir):
    """Test capability scope check."""
    runner = L1Runner(clock=fixed_clock)

    result = runner.run(
        question="What are the best practices for VaR backtesting in quantitative finance?",
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
    )

    # Load capability_scope_check.json
    with open(tmp_evidence_dir / "capability_scope_check.json") as f:
        scope = json.load(f)

    # Check scope
    assert scope["result"] == "PASS"
    assert scope["violations"] == []
    assert len(scope["checked_outputs"]) > 0
    # Should detect ResearchReport or LiteratureReview
    assert any("Research" in output for output in scope["checked_outputs"])


def test_l1_runner_with_findings_and_actions(fixed_clock, sample_transcript_path, tmp_evidence_dir):
    """Test L1 runner with findings and actions."""
    runner = L1Runner(clock=fixed_clock)

    result = runner.run(
        question="What are the best practices for VaR backtesting in quantitative finance?",
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
        findings=["Finding 1: Citations sufficient", "Finding 2: Methodology clear"],
        actions=["Action 1: Review quantitative details"],
    )

    # Load operator_output.md
    with open(tmp_evidence_dir / "operator_output.md") as f:
        operator_output = f.read()

    # Check findings and actions
    assert "Finding 1: Citations sufficient" in operator_output
    assert "Finding 2: Methodology clear" in operator_output
    assert "Action 1: Review quantitative details" in operator_output


def test_l1_runner_deterministic_run_id(fixed_clock, sample_transcript_path, tmp_path):
    """Test that run_id is deterministic."""
    runner = L1Runner(clock=fixed_clock)

    # Run twice with same inputs
    result1 = runner.run(
        question="What are the best practices for VaR backtesting in quantitative finance?",
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_path / "run1",
    )

    result2 = runner.run(
        question="What are the best practices for VaR backtesting in quantitative finance?",
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_path / "run2",
    )

    # Run IDs should be identical (deterministic)
    assert result1.run_id == result2.run_id
    assert result1.proposer_run_id == result2.proposer_run_id
    assert result1.critic_run_id == result2.critic_run_id


def test_l1_runner_evidence_pack_json_golden(fixed_clock, sample_transcript_path, tmp_evidence_dir):
    """Test evidence pack JSON structure (golden test)."""
    runner = L1Runner(clock=fixed_clock)

    result = runner.run(
        question="What are the best practices for VaR backtesting in quantitative finance?",
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
        operator_notes="Test run for Phase 4A",
    )

    # Load evidence_pack.json
    with open(tmp_evidence_dir / "evidence_pack.json") as f:
        pack = json.load(f)

    # Check structure
    assert pack["evidence_pack_id"] == result.evidence_pack_id
    assert pack["layer_id"] == "L1"
    assert pack["layer_name"] == "DeepResearch"
    assert pack["mode"] == "replay"
    assert pack["sod_check"]["result"] == "PASS"
    assert pack["capability_scope_check"]["result"] == "PASS"
    assert "run_id" in pack
    assert "proposer" in pack
    assert "critic" in pack
    assert "sod_check" in pack
    assert "capability_scope_check" in pack
    assert "artifacts" in pack
    assert pack["operator_notes"] == "Test run for Phase 4A"


def test_l1_runner_missing_transcript_error(fixed_clock, tmp_evidence_dir):
    """Test error when transcript missing in replay mode."""
    runner = L1Runner(clock=fixed_clock)

    with pytest.raises(Exception) as excinfo:
        runner.run(
            question="What are the best practices for VaR backtesting in quantitative finance?",
            mode="replay",
            transcript_path=None,
            out_dir=tmp_evidence_dir,
        )

    assert "transcript" in str(excinfo.value).lower()


def test_l1_runner_mode_requires_transcript(fixed_clock, tmp_evidence_dir):
    """Test that replay/dry modes require transcript."""
    runner = L1Runner(clock=fixed_clock)

    with pytest.raises(Exception) as excinfo:
        runner.run(
            question="What are the best practices for VaR backtesting in quantitative finance?",
            mode="dry",
            transcript_path=None,
            out_dir=tmp_evidence_dir,
        )

    assert "transcript" in str(excinfo.value).lower()


def test_l1_runner_empty_question_error(fixed_clock, sample_transcript_path, tmp_evidence_dir):
    """Test error when question is empty."""
    runner = L1Runner(clock=fixed_clock)

    with pytest.raises(Exception) as excinfo:
        runner.run(
            question="",
            mode="replay",
            transcript_path=sample_transcript_path,
            out_dir=tmp_evidence_dir,
        )

    assert "question" in str(excinfo.value).lower()


def test_l1_runner_citations_check(fixed_clock, sample_transcript_path, tmp_evidence_dir):
    """Test that capability scope checks for minimum citations."""
    runner = L1Runner(clock=fixed_clock)

    result = runner.run(
        question="What are the best practices for VaR backtesting in quantitative finance?",
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
    )

    # Load capability_scope_check.json
    with open(tmp_evidence_dir / "capability_scope_check.json") as f:
        scope = json.load(f)

    # The sample fixture has 5 citations, so should PASS
    assert scope["result"] == "PASS"
    # Should not have citation violation
    assert not any("citation" in v.lower() for v in scope.get("violations", []))


def test_l1_runner_run_manifest_structure(fixed_clock, sample_transcript_path, tmp_evidence_dir):
    """Test run manifest structure."""
    runner = L1Runner(clock=fixed_clock)

    result = runner.run(
        question="What are the best practices for VaR backtesting in quantitative finance?",
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_evidence_dir,
    )

    # Load run_manifest.json
    with open(tmp_evidence_dir / "run_manifest.json") as f:
        manifest = json.load(f)

    # Check structure
    assert "run_id" in manifest
    assert manifest["run_id"].startswith("L1-")
    assert manifest["layer_id"] == "L1"
    assert manifest["layer_name"] == "DeepResearch"
    assert manifest["autonomy_level"] == "PROP"
    assert manifest["primary_model_id"] == "o3-deep-research"
    assert manifest["critic_model_id"] == "o3-pro"
    assert manifest["capability_scope_id"] == "L1"
    assert manifest["sod_result"] == "PASS"
    assert "artifacts" in manifest
