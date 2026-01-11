"""
Tests for L4 Governance Critic Runner

Tests verify:
- Evidence pack loading and review
- SoD enforcement (proposer != critic)
- Capability scope checks (no forbidden outputs)
- Decision extraction and validation
- Deterministic artifact generation
- Offline/replay mode (CI-safe)

Reference:
- docs/governance/ai_autonomy/PHASE4_L1_L4_INTEGRATION.md
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ai_orchestration.l4_critic import (
    CapabilityScopeViolation,
    L4Critic,
    L4CriticError,
    SoDViolation,
)


@pytest.fixture
def fixed_clock():
    """Fixed clock for deterministic tests."""
    return datetime(2026, 1, 10, 12, 30, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_evidence_pack_path(tmp_path):
    """Create a sample evidence pack for testing."""
    evidence_pack_dir = tmp_path / "L1_sample_2026-01-10"
    evidence_pack_dir.mkdir(parents=True)

    # Create evidence_pack.json
    evidence_pack_data = {
        "evidence_pack_id": "L1-DEEPRESEARCH-SAMPLE-2026-01-10",
        "layer_id": "L1",
        "layer_name": "Deep Research",
        "schema_version": "1.0",
        "timestamp": "2026-01-10T12:00:00+00:00",
        "models": {
            "proposer": {
                "model_id": "o3-deep-research",
                "role": "proposer"
            },
            "critic": {
                "model_id": "o3-pro",
                "role": "critic"
            }
        },
        "sod_check": {
            "result": "PASS",
            "proposer_model_id": "o3-deep-research",
            "critic_model_id": "o3-pro",
            "reason": "Distinct models",
            "timestamp": "2026-01-10T12:00:10+00:00"
        },
        "capability_scope_check": {
            "result": "PASS",
            "violations": [],
            "checked_outputs": ["Research Report"],
            "timestamp": "2026-01-10T12:00:30+00:00"
        }
    }

    with open(evidence_pack_dir / "evidence_pack.json", "w") as f:
        json.dump(evidence_pack_data, f, indent=2)

    return evidence_pack_dir


@pytest.fixture
def sample_transcript_path():
    """Path to sample L4 critic transcript."""
    return Path(__file__).parent.parent / "fixtures" / "transcripts" / "l4_critic_sample.json"


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Temporary output directory for artifacts."""
    out_dir = tmp_path / "l4_output"
    out_dir.mkdir(parents=True)
    return out_dir


def test_l4_critic_replay_mode_success(
    sample_evidence_pack_path, sample_transcript_path, tmp_output_dir, fixed_clock
):
    """Test L4 critic in replay mode (offline, deterministic)."""
    runner = L4Critic(clock=fixed_clock)

    result = runner.run(
        evidence_pack_path=sample_evidence_pack_path,
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_output_dir,
        operator_notes="Test run",
    )

    # Verify result structure
    assert result.run_id.startswith("L4-")
    assert result.layer_id == "L4"
    assert result.mode == "replay"
    assert result.sod_result == "PASS"
    assert result.capability_scope_result == "PASS"

    # Verify decision
    assert result.decision.decision in ["ALLOW", "REVIEW_REQUIRED", "AUTO_APPLY_DENY", "REJECT"]
    assert result.decision.severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert len(result.decision.rationale) > 0

    # Verify artifacts
    assert len(result.artifacts) >= 3
    assert "critic_report" in result.artifacts
    assert "critic_decision" in result.artifacts
    assert "critic_manifest" in result.artifacts


def test_l4_critic_decision_structure(
    sample_evidence_pack_path, sample_transcript_path, tmp_output_dir, fixed_clock
):
    """Test L4 critic decision has required fields."""
    runner = L4Critic(clock=fixed_clock)

    result = runner.run(
        evidence_pack_path=sample_evidence_pack_path,
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_output_dir,
    )

    # Verify decision structure
    decision = result.decision
    assert decision.decision in ["ALLOW", "REVIEW_REQUIRED", "AUTO_APPLY_DENY", "REJECT"]
    assert decision.severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert isinstance(decision.rationale, str)
    assert isinstance(decision.policy_references, list)
    assert isinstance(decision.evidence_ids, list)
    assert isinstance(decision.risk_notes, list)
    assert isinstance(decision.timestamp, str)

    # Verify decision JSON artifact
    decision_json_path = result.artifacts["critic_decision"]
    assert decision_json_path.exists()

    with open(decision_json_path) as f:
        decision_data = json.load(f)

    assert "decision" in decision_data
    assert "severity" in decision_data
    assert "rationale" in decision_data
    assert "sod_check" in decision_data
    assert "capability_scope_check" in decision_data


def test_l4_critic_sod_check_enforced(
    sample_evidence_pack_path, sample_transcript_path, tmp_output_dir, fixed_clock
):
    """Test SoD check is enforced (proposer != critic)."""
    runner = L4Critic(clock=fixed_clock)

    result = runner.run(
        evidence_pack_path=sample_evidence_pack_path,
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_output_dir,
    )

    # Verify SoD check passed
    assert result.sod_result == "PASS"

    # Verify proposer != critic
    assert result.proposer_model_id != result.critic_model_id


def test_l4_critic_sod_violation_on_self_review(
    sample_evidence_pack_path, sample_transcript_path, tmp_output_dir, fixed_clock
):
    """Test SoD violation when proposer == critic (self-review)."""
    # Modify evidence pack to have same model for proposer and critic
    evidence_pack_json = sample_evidence_pack_path / "evidence_pack.json"
    with open(evidence_pack_json) as f:
        data = json.load(f)

    # Set proposer = critic = o3-pro (self-review)
    data["models"]["proposer"]["model_id"] = "o3-pro"

    with open(evidence_pack_json, "w") as f:
        json.dump(data, f, indent=2)

    runner = L4Critic(clock=fixed_clock)

    # Should raise SoDViolation
    with pytest.raises(SoDViolation):
        runner.run(
            evidence_pack_path=sample_evidence_pack_path,
            mode="replay",
            transcript_path=sample_transcript_path,
            out_dir=tmp_output_dir,
        )


def test_l4_critic_capability_scope_no_forbidden_outputs(
    sample_evidence_pack_path, sample_transcript_path, tmp_output_dir, fixed_clock
):
    """Test capability scope check rejects forbidden outputs."""
    runner = L4Critic(clock=fixed_clock)

    result = runner.run(
        evidence_pack_path=sample_evidence_pack_path,
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_output_dir,
    )

    # Verify capability scope check passed
    assert result.capability_scope_result == "PASS"

    # Read critic report and ensure no forbidden keywords
    critic_report_path = result.artifacts["critic_report"]
    with open(critic_report_path) as f:
        report_content = f.read()

    forbidden_keywords = [
        "UnlockCommand",
        "ExecutionCommand",
        "LiveToggle",
        "RiskLimitChange",
    ]

    for keyword in forbidden_keywords:
        assert keyword not in report_content


def test_l4_critic_deterministic_run_id(
    sample_evidence_pack_path, sample_transcript_path, tmp_output_dir, fixed_clock
):
    """Test run ID is deterministic with fixed clock."""
    runner1 = L4Critic(clock=fixed_clock)
    runner2 = L4Critic(clock=fixed_clock)

    result1 = runner1.run(
        evidence_pack_path=sample_evidence_pack_path,
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_output_dir / "run1",
    )

    result2 = runner2.run(
        evidence_pack_path=sample_evidence_pack_path,
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_output_dir / "run2",
    )

    # Run IDs should be deterministic
    assert result1.run_id == result2.run_id


def test_l4_critic_artifacts_generated(
    sample_evidence_pack_path, sample_transcript_path, tmp_output_dir, fixed_clock
):
    """Test all required artifacts are generated."""
    runner = L4Critic(clock=fixed_clock)

    result = runner.run(
        evidence_pack_path=sample_evidence_pack_path,
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_output_dir,
    )

    # Verify all artifacts exist
    required_artifacts = [
        "critic_report",
        "critic_decision",
        "critic_manifest",
        "operator_summary",
    ]

    for artifact_name in required_artifacts:
        assert artifact_name in result.artifacts
        artifact_path = result.artifacts[artifact_name]
        assert artifact_path.exists()
        assert artifact_path.stat().st_size > 0


def test_l4_critic_missing_evidence_pack_error(tmp_output_dir, fixed_clock):
    """Test error when evidence pack not found."""
    runner = L4Critic(clock=fixed_clock)

    non_existent_path = Path("/tmp/non_existent_evidence_pack")

    with pytest.raises(L4CriticError, match="Evidence pack not found"):
        runner.run(
            evidence_pack_path=non_existent_path,
            mode="dry",
            out_dir=tmp_output_dir,
        )


def test_l4_critic_mode_requires_transcript(sample_evidence_pack_path, tmp_output_dir, fixed_clock):
    """Test replay mode requires transcript path."""
    runner = L4Critic(clock=fixed_clock)

    with pytest.raises(L4CriticError, match="Transcript path required"):
        runner.run(
            evidence_pack_path=sample_evidence_pack_path,
            mode="replay",
            transcript_path=None,
            out_dir=tmp_output_dir,
        )


def test_l4_critic_evidence_ids_required(
    sample_evidence_pack_path, sample_transcript_path, tmp_output_dir, fixed_clock
):
    """Test critic output must reference evidence IDs."""
    runner = L4Critic(clock=fixed_clock)

    result = runner.run(
        evidence_pack_path=sample_evidence_pack_path,
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_output_dir,
    )

    # Verify evidence IDs are present
    decision = result.decision
    assert len(decision.evidence_ids) > 0


def test_l4_critic_manifest_structure(
    sample_evidence_pack_path, sample_transcript_path, tmp_output_dir, fixed_clock
):
    """Test critic manifest has required structure."""
    runner = L4Critic(clock=fixed_clock)

    result = runner.run(
        evidence_pack_path=sample_evidence_pack_path,
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_output_dir,
    )

    # Read manifest
    manifest_path = result.artifacts["critic_manifest"]
    with open(manifest_path) as f:
        manifest = json.load(f)

    # Verify required fields
    assert manifest["run_id"] == result.run_id
    assert manifest["layer_id"] == "L4"
    assert manifest["critic_model_id"] == result.critic_model_id
    assert manifest["mode"] == "replay"
    assert "timestamp" in manifest
    assert "inputs" in manifest
    assert "outputs" in manifest
    assert manifest["inputs"]["evidence_pack_id"] == result.evidence_pack_id


def test_l4_critic_policy_references_present(
    sample_evidence_pack_path, sample_transcript_path, tmp_output_dir, fixed_clock
):
    """Test critic decision includes policy references."""
    runner = L4Critic(clock=fixed_clock)

    result = runner.run(
        evidence_pack_path=sample_evidence_pack_path,
        mode="replay",
        transcript_path=sample_transcript_path,
        out_dir=tmp_output_dir,
    )

    # Verify policy references are present
    decision = result.decision
    assert len(decision.policy_references) > 0
