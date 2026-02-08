"""
L2 -> L3 handoff contract: pointer-only envelope + learnable surfaces gating.

- Minimal L2 output capsule (pointer-only) must be accepted by L3.
- Learnable surfaces metadata: absent or explicit + allowlisted (L3: prompt_template_variants only).
"""

from pathlib import Path

import pytest

from src.ai_orchestration.l3_contracts import accepts_l3_pointer_only_input
from src.ai_orchestration.l3_runner import L3Runner
from src.governance.learning.learnable_surfaces_policy import get_allowed_surfaces


def _l2_handoff_envelope_valid_for_l3(envelope: dict) -> bool:
    """
    Contract: envelope is valid for L3 handoff iff pointer-only and
    any learnable_surfaces are allowlisted for L3 (prompt_template_variants only).
    """
    if not accepts_l3_pointer_only_input(envelope):
        return False
    surfaces = envelope.get("learnable_surfaces")
    if surfaces is None:
        return True
    if not isinstance(surfaces, list):
        return False
    allowed = set(get_allowed_surfaces("L3"))
    return all(s in allowed for s in surfaces)


def _minimal_l2_output_capsule(
    run_id: str = "l2-out-1",
    ts_ms: int = 0,
    artifacts: list = None,
    learnable_surfaces: list = None,
) -> dict:
    """Build minimal L2 output capsule (pointer-only) as would be handed to L3."""
    if artifacts is None:
        artifacts = [{"path": "out/l2/scenario.json", "sha256": "a" * 64}]
    out = {
        "run_id": run_id,
        "ts_ms": ts_ms,
        "artifacts": artifacts,
    }
    if learnable_surfaces is not None:
        out["learnable_surfaces"] = learnable_surfaces
    return out


class TestL2OutputCapsuleL3Accepts:
    """Minimal L2 output capsule (pointer-only) is accepted by L3."""

    def test_minimal_l2_capsule_pointer_only_accepted(self):
        """L2-style minimal capsule (run_id, ts_ms, artifacts path+sha256) is L3 pointer-only accepted."""
        capsule = _minimal_l2_output_capsule()
        assert accepts_l3_pointer_only_input(capsule) is True

    def test_minimal_l2_capsule_l3_runner_accepts(self, tmp_path):
        """L3Runner.run() accepts minimal L2 output capsule (pointer-only)."""
        capsule = _minimal_l2_output_capsule()
        runner = L3Runner()
        result = runner.run(inputs=capsule, mode="dry-run", out_dir=tmp_path)
        assert result.layer_id == "L3"
        assert result.run_id.startswith("L3-")

    def test_l2_capsule_empty_artifacts_accepted(self):
        """L2 capsule with empty artifacts list is still pointer-only and accepted."""
        capsule = _minimal_l2_output_capsule(artifacts=[])
        assert accepts_l3_pointer_only_input(capsule) is True


class TestLearnableSurfacesAllowlistedForL3:
    """Learnable surfaces metadata must be absent or explicit + allowlisted (L3: prompt_template_variants only)."""

    def test_l3_allowed_surfaces_is_prompt_template_variants_only(self):
        """L3 allowlist is exactly ['prompt_template_variants'] from policy."""
        allowed = get_allowed_surfaces("L3")
        assert allowed == ["prompt_template_variants"]

    def test_handoff_envelope_without_learnable_surfaces_valid(self):
        """Envelope with no learnable_surfaces key is valid for L3 handoff."""
        envelope = _minimal_l2_output_capsule()
        assert "learnable_surfaces" not in envelope
        assert _l2_handoff_envelope_valid_for_l3(envelope) is True

    def test_handoff_envelope_with_empty_learnable_surfaces_valid(self):
        """Envelope with learnable_surfaces=[] is valid."""
        envelope = _minimal_l2_output_capsule(learnable_surfaces=[])
        assert _l2_handoff_envelope_valid_for_l3(envelope) is True

    def test_handoff_envelope_with_allowlisted_surface_valid(self):
        """Envelope with learnable_surfaces=['prompt_template_variants'] is valid."""
        envelope = _minimal_l2_output_capsule(learnable_surfaces=["prompt_template_variants"])
        assert _l2_handoff_envelope_valid_for_l3(envelope) is True

    def test_handoff_envelope_with_disallowed_surface_invalid(self):
        """Envelope with learnable_surfaces including non-L3 surface is invalid for handoff."""
        envelope = _minimal_l2_output_capsule(
            learnable_surfaces=["scenario_priors"]  # L2 surface, not in L3 allowlist
        )
        assert _l2_handoff_envelope_valid_for_l3(envelope) is False

    def test_handoff_envelope_mixed_surfaces_invalid_unless_all_allowlisted(self):
        """Envelope with prompt_template_variants + other must be invalid (other not allowlisted)."""
        envelope = _minimal_l2_output_capsule(
            learnable_surfaces=["prompt_template_variants", "other"]
        )
        assert _l2_handoff_envelope_valid_for_l3(envelope) is False
