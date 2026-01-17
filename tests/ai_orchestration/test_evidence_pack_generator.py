"""
Tests for Evidence Pack Generator

Tests evidence pack generation with deterministic artifacts (offline-only).
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.ai_orchestration import (
    RunManifest,
    RunManifestGenerator,
)
from src.ai_orchestration.evidence_pack_generator import (
    EvidencePackGenerator,
    ProposerArtifact,
    CriticArtifact,
    CapabilityScopeCheck,
)
from src.ai_orchestration.models import SoDResult


@pytest.fixture
def fixed_clock():
    """Fixed datetime for determinism."""
    return datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def tmp_evidence_dir(tmp_path):
    """Temporary evidence pack directory."""
    return tmp_path / "evidence_pack"


@pytest.fixture
def sample_run_manifest(fixed_clock):
    """Sample run manifest."""
    generator = RunManifestGenerator(clock=fixed_clock)
    return generator.generate(
        layer_id="L2",
        layer_name="Market Outlook",
        autonomy_level="PROP",
        primary_model_id="gpt-5.2-pro",
        fallback_model_ids=["gpt-5.2"],
        critic_model_id="deepseek-r1",
        capability_scope_id="L2_market_outlook",
        capability_scope_version="1.0",
        sod_result=SoDResult.PASS,
        sod_reason="SoD PASS: Proposer (gpt-5.2-pro) != Critic (deepseek-r1)",
    )


@pytest.fixture
def sample_proposer_artifact():
    """Sample proposer artifact."""
    content = (
        "# Market Outlook Q1 2026\n\n"
        "## Scenario Analysis\n\n"
        "**Base Case:** Moderate growth.\n\n"
        "**No-Trade Triggers:** VIX > 30\n\n"
        "**Uncertainty Level:** HIGH"
    )
    return ProposerArtifact(
        model_id="gpt-5.2-pro",
        run_id="proposer-run-001",
        prompt_hash="sha256:abc123def456",
        output_hash=EvidencePackGenerator.compute_output_hash(content),
        content=content,
        metadata={"timestamp": "2026-01-10T12:00:01+00:00", "latency_ms": 2345},
    )


@pytest.fixture
def sample_critic_artifact():
    """Sample critic artifact."""
    content = (
        "# Critic Review\n\n"
        "**Decision:** APPROVE_WITH_CHANGES\n\n"
        "**Rationale:** Comprehensive analysis, appropriate no-trade triggers.\n\n"
        "**Evidence IDs:** [proposer-run-001, baseline-scenario-2026-01]"
    )
    return CriticArtifact(
        model_id="deepseek-r1",
        run_id="critic-run-001",
        prompt_hash="sha256:xyz789uvw012",
        output_hash=EvidencePackGenerator.compute_output_hash(content),
        content=content,
        decision="APPROVE_WITH_CHANGES",
        rationale="Comprehensive analysis, appropriate no-trade triggers.",
        evidence_ids=["proposer-run-001", "baseline-scenario-2026-01"],
        metadata={"timestamp": "2026-01-10T12:00:05+00:00", "latency_ms": 1567},
    )


@pytest.fixture
def sample_capability_scope_check(fixed_clock):
    """Sample capability scope check."""
    return CapabilityScopeCheck(
        result="PASS",
        violations=[],
        checked_outputs=["ScenarioReport", "NoTradeTriggers", "UncertaintyAssessment"],
        timestamp=fixed_clock.isoformat(),
    )


def test_generate_evidence_pack_bundle(
    fixed_clock,
    tmp_evidence_dir,
    sample_run_manifest,
    sample_proposer_artifact,
    sample_critic_artifact,
    sample_capability_scope_check,
):
    """Test evidence pack bundle generation."""
    generator = EvidencePackGenerator(clock=fixed_clock)

    artifacts = generator.generate(
        evidence_pack_id="EVP-L2-2026-01-10-001",
        layer_id="L2",
        layer_name="Market Outlook",
        run_manifest=sample_run_manifest,
        proposer_artifact=sample_proposer_artifact,
        critic_artifact=sample_critic_artifact,
        sod_result=SoDResult.PASS,
        sod_reason="SoD PASS: Proposer (gpt-5.2-pro) != Critic (deepseek-r1)",
        capability_scope_check=sample_capability_scope_check,
        out_dir=tmp_evidence_dir,
        mode="replay",
        network_used=False,
    )

    # Check all artifacts were created
    assert "evidence_pack" in artifacts
    assert "run_manifest" in artifacts
    assert "operator_output" in artifacts
    assert "proposer_output" in artifacts
    assert "critic_output" in artifacts
    assert "sod_check" in artifacts
    assert "capability_scope_check" in artifacts

    # Check files exist
    assert (tmp_evidence_dir / "evidence_pack.json").exists()
    assert (tmp_evidence_dir / "run_manifest.json").exists()
    assert (tmp_evidence_dir / "operator_output.md").exists()
    assert (tmp_evidence_dir / "proposer_output.json").exists()
    assert (tmp_evidence_dir / "critic_output.json").exists()
    assert (tmp_evidence_dir / "sod_check.json").exists()
    assert (tmp_evidence_dir / "capability_scope_check.json").exists()


def test_evidence_pack_json_structure(
    fixed_clock,
    tmp_evidence_dir,
    sample_run_manifest,
    sample_proposer_artifact,
    sample_critic_artifact,
    sample_capability_scope_check,
):
    """Test evidence pack JSON structure (golden snapshot)."""
    generator = EvidencePackGenerator(clock=fixed_clock)

    generator.generate(
        evidence_pack_id="EVP-L2-2026-01-10-001",
        layer_id="L2",
        layer_name="Market Outlook",
        run_manifest=sample_run_manifest,
        proposer_artifact=sample_proposer_artifact,
        critic_artifact=sample_critic_artifact,
        sod_result=SoDResult.PASS,
        sod_reason="SoD PASS: Proposer (gpt-5.2-pro) != Critic (deepseek-r1)",
        capability_scope_check=sample_capability_scope_check,
        out_dir=tmp_evidence_dir,
        mode="replay",
        network_used=False,
    )

    # Load evidence_pack.json
    with open(tmp_evidence_dir / "evidence_pack.json") as f:
        evidence_pack = json.load(f)

    # Golden snapshot assertions
    assert evidence_pack["evidence_pack_id"] == "EVP-L2-2026-01-10-001"
    assert evidence_pack["evidence_pack_version"] == "2.0"
    assert evidence_pack["creation_timestamp"] == "2026-01-10T12:00:00+00:00"
    assert evidence_pack["layer_id"] == "L2"
    assert evidence_pack["layer_name"] == "Market Outlook"
    assert evidence_pack["mode"] == "replay"
    assert evidence_pack["network_used"] is False

    # Check proposer
    assert evidence_pack["proposer"]["model_id"] == "gpt-5.2-pro"
    assert evidence_pack["proposer"]["run_id"] == "proposer-run-001"
    assert evidence_pack["proposer"]["prompt_hash"] == "sha256:abc123def456"
    assert evidence_pack["proposer"]["artifact_path"] == "proposer_output.json"

    # Check critic
    assert evidence_pack["critic"]["model_id"] == "deepseek-r1"
    assert evidence_pack["critic"]["run_id"] == "critic-run-001"
    assert evidence_pack["critic"]["prompt_hash"] == "sha256:xyz789uvw012"
    assert evidence_pack["critic"]["artifact_path"] == "critic_output.json"

    # Check SoD
    assert evidence_pack["sod_check"]["result"] == "PASS"
    assert "Proposer (gpt-5.2-pro) != Critic (deepseek-r1)" in evidence_pack["sod_check"]["reason"]

    # Check capability scope
    assert evidence_pack["capability_scope_check"]["result"] == "PASS"
    assert evidence_pack["capability_scope_check"]["violations"] == []

    # Check artifacts list is sorted
    artifacts = evidence_pack["artifacts"]
    assert artifacts == sorted(artifacts)
    assert "evidence_pack.json" in artifacts
    assert "run_manifest.json" in artifacts


def test_proposer_output_json_structure(
    fixed_clock,
    tmp_evidence_dir,
    sample_run_manifest,
    sample_proposer_artifact,
    sample_critic_artifact,
    sample_capability_scope_check,
):
    """Test proposer_output.json structure."""
    generator = EvidencePackGenerator(clock=fixed_clock)

    generator.generate(
        evidence_pack_id="EVP-L2-2026-01-10-001",
        layer_id="L2",
        layer_name="Market Outlook",
        run_manifest=sample_run_manifest,
        proposer_artifact=sample_proposer_artifact,
        critic_artifact=sample_critic_artifact,
        sod_result=SoDResult.PASS,
        sod_reason="Test",
        capability_scope_check=sample_capability_scope_check,
        out_dir=tmp_evidence_dir,
    )

    # Load proposer_output.json
    with open(tmp_evidence_dir / "proposer_output.json") as f:
        proposer_output = json.load(f)

    # Check structure
    assert proposer_output["model_id"] == "gpt-5.2-pro"
    assert proposer_output["run_id"] == "proposer-run-001"
    assert proposer_output["prompt_hash"] == "sha256:abc123def456"
    assert proposer_output["output_hash"].startswith("sha256:")
    assert "Market Outlook Q1 2026" in proposer_output["content"]
    assert "metadata" in proposer_output


def test_critic_output_json_structure(
    fixed_clock,
    tmp_evidence_dir,
    sample_run_manifest,
    sample_proposer_artifact,
    sample_critic_artifact,
    sample_capability_scope_check,
):
    """Test critic_output.json structure."""
    generator = EvidencePackGenerator(clock=fixed_clock)

    generator.generate(
        evidence_pack_id="EVP-L2-2026-01-10-001",
        layer_id="L2",
        layer_name="Market Outlook",
        run_manifest=sample_run_manifest,
        proposer_artifact=sample_proposer_artifact,
        critic_artifact=sample_critic_artifact,
        sod_result=SoDResult.PASS,
        sod_reason="Test",
        capability_scope_check=sample_capability_scope_check,
        out_dir=tmp_evidence_dir,
    )

    # Load critic_output.json
    with open(tmp_evidence_dir / "critic_output.json") as f:
        critic_output = json.load(f)

    # Check structure
    assert critic_output["model_id"] == "deepseek-r1"
    assert critic_output["run_id"] == "critic-run-001"
    assert critic_output["decision"] == "APPROVE_WITH_CHANGES"
    assert "Comprehensive analysis" in critic_output["rationale"]
    assert critic_output["evidence_ids"] == sorted(critic_output["evidence_ids"])
    assert "proposer-run-001" in critic_output["evidence_ids"]


def test_sod_check_json_structure(
    fixed_clock,
    tmp_evidence_dir,
    sample_run_manifest,
    sample_proposer_artifact,
    sample_critic_artifact,
    sample_capability_scope_check,
):
    """Test sod_check.json structure."""
    generator = EvidencePackGenerator(clock=fixed_clock)

    generator.generate(
        evidence_pack_id="EVP-L2-2026-01-10-001",
        layer_id="L2",
        layer_name="Market Outlook",
        run_manifest=sample_run_manifest,
        proposer_artifact=sample_proposer_artifact,
        critic_artifact=sample_critic_artifact,
        sod_result=SoDResult.PASS,
        sod_reason="SoD PASS: Proposer (gpt-5.2-pro) != Critic (deepseek-r1)",
        capability_scope_check=sample_capability_scope_check,
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
    assert sod_check["timestamp"] == "2026-01-10T12:00:00+00:00"


def test_capability_scope_check_json_structure(
    fixed_clock,
    tmp_evidence_dir,
    sample_run_manifest,
    sample_proposer_artifact,
    sample_critic_artifact,
    sample_capability_scope_check,
):
    """Test capability_scope_check.json structure."""
    generator = EvidencePackGenerator(clock=fixed_clock)

    generator.generate(
        evidence_pack_id="EVP-L2-2026-01-10-001",
        layer_id="L2",
        layer_name="Market Outlook",
        run_manifest=sample_run_manifest,
        proposer_artifact=sample_proposer_artifact,
        critic_artifact=sample_critic_artifact,
        sod_result=SoDResult.PASS,
        sod_reason="Test",
        capability_scope_check=sample_capability_scope_check,
        out_dir=tmp_evidence_dir,
    )

    # Load capability_scope_check.json
    with open(tmp_evidence_dir / "capability_scope_check.json") as f:
        scope_check = json.load(f)

    # Check structure
    assert scope_check["result"] == "PASS"
    assert scope_check["violations"] == []
    assert scope_check["checked_outputs"] == sorted(scope_check["checked_outputs"])
    assert "ScenarioReport" in scope_check["checked_outputs"]
    assert scope_check["timestamp"] == "2026-01-10T12:00:00+00:00"


def test_deterministic_output_hash():
    """Test output hash is deterministic."""
    content = "Test content for hashing"

    hash1 = EvidencePackGenerator.compute_output_hash(content)
    hash2 = EvidencePackGenerator.compute_output_hash(content)

    assert hash1 == hash2
    assert hash1.startswith("sha256:")


def test_json_key_ordering_stable(
    fixed_clock,
    tmp_evidence_dir,
    sample_run_manifest,
    sample_proposer_artifact,
    sample_critic_artifact,
    sample_capability_scope_check,
):
    """Test JSON keys are stably ordered."""
    generator = EvidencePackGenerator(clock=fixed_clock)

    generator.generate(
        evidence_pack_id="EVP-L2-2026-01-10-001",
        layer_id="L2",
        layer_name="Market Outlook",
        run_manifest=sample_run_manifest,
        proposer_artifact=sample_proposer_artifact,
        critic_artifact=sample_critic_artifact,
        sod_result=SoDResult.PASS,
        sod_reason="Test",
        capability_scope_check=sample_capability_scope_check,
        out_dir=tmp_evidence_dir,
    )

    # Load evidence_pack.json
    with open(tmp_evidence_dir / "evidence_pack.json") as f:
        evidence_pack = json.load(f)

    # Check keys are sorted
    keys = list(evidence_pack.keys())
    assert keys == sorted(keys)


def test_evidence_pack_with_findings_and_actions(
    fixed_clock,
    tmp_evidence_dir,
    sample_run_manifest,
    sample_proposer_artifact,
    sample_critic_artifact,
    sample_capability_scope_check,
):
    """Test evidence pack generation with findings and actions."""
    generator = EvidencePackGenerator(clock=fixed_clock)

    findings = ["Test finding 1", "Test finding 2"]
    actions = ["Test action 1"]

    generator.generate(
        evidence_pack_id="EVP-L2-2026-01-10-001",
        layer_id="L2",
        layer_name="Market Outlook",
        run_manifest=sample_run_manifest,
        proposer_artifact=sample_proposer_artifact,
        critic_artifact=sample_critic_artifact,
        sod_result=SoDResult.PASS,
        sod_reason="Test",
        capability_scope_check=sample_capability_scope_check,
        out_dir=tmp_evidence_dir,
        findings=findings,
        actions=actions,
    )

    # Check operator_output.md includes findings/actions
    operator_output = (tmp_evidence_dir / "operator_output.md").read_text()

    assert "Test finding 1" in operator_output
    assert "Test finding 2" in operator_output
    assert "Test action 1" in operator_output
