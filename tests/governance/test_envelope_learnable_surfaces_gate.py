"""
Envelope boundary: learnable_surfaces gate (runtime).

- validate_envelope_learnable_surfaces(envelope, layer_id): missing key => [];
  if learnable_surfaces or requested_surfaces present, assert_surfaces_allowed.
- L2->L3 disallowed surface blocks (e.g. scenario_priors not in L3 allowlist).
"""

import pytest

from src.governance.learning.learnable_surfaces_policy import (
    LearnableSurfacesViolation,
    validate_envelope_learnable_surfaces,
)


class TestEnvelopeGateMissingKeyTreatedAsEmpty:
    """Missing learnable_surfaces / requested_surfaces => treated as [] (no-op)."""

    def test_no_key_no_op(self):
        """Envelope with neither key does not raise."""
        validate_envelope_learnable_surfaces({"run_id": "r1"}, "L3")

    def test_empty_learnable_surfaces_no_op(self):
        """Envelope with learnable_surfaces=[] does not raise."""
        validate_envelope_learnable_surfaces({"learnable_surfaces": []}, "L3")

    def test_empty_requested_surfaces_no_op(self):
        """Envelope with requested_surfaces=[] does not raise."""
        validate_envelope_learnable_surfaces({"requested_surfaces": []}, "L2")


class TestEnvelopeGateAllowlistedPasses:
    """Allowlisted surfaces for the layer pass."""

    def test_l3_prompt_template_variants_passes(self):
        """L3 envelope with learnable_surfaces=['prompt_template_variants'] passes."""
        validate_envelope_learnable_surfaces(
            {"learnable_surfaces": ["prompt_template_variants"]},
            "L3",
        )

    def test_l2_scenario_priors_passes(self):
        """L2 envelope with requested_surfaces=['scenario_priors'] passes."""
        validate_envelope_learnable_surfaces(
            {"requested_surfaces": ["scenario_priors"]},
            "L2",
        )


class TestL2ToL3DisallowedSurfaceBlocks:
    """L2->L3 handoff: disallowed surface in envelope blocks (raises)."""

    def test_l3_envelope_with_l2_surface_raises(self):
        """L3 envelope with learnable_surfaces=['scenario_priors'] raises (L2 surface)."""
        with pytest.raises(LearnableSurfacesViolation) as exc_info:
            validate_envelope_learnable_surfaces(
                {"learnable_surfaces": ["scenario_priors"]},
                "L3",
            )
        assert exc_info.value.layer_id == "L3"
        assert "scenario_priors" in exc_info.value.requested

    def test_l3_envelope_with_unknown_surface_raises(self):
        """L3 envelope with learnable_surfaces=['other'] raises."""
        with pytest.raises(LearnableSurfacesViolation):
            validate_envelope_learnable_surfaces(
                {"learnable_surfaces": ["other"]},
                "L3",
            )

    def test_l3_envelope_mixed_allowlisted_and_disallowed_raises(self):
        """L3 with prompt_template_variants + scenario_priors raises (one disallowed)."""
        with pytest.raises(LearnableSurfacesViolation):
            validate_envelope_learnable_surfaces(
                {"learnable_surfaces": ["prompt_template_variants", "scenario_priors"]},
                "L3",
            )


class TestDenyAllLayers:
    """L0/L4/L5/L6: any non-empty surfaces raise."""

    def test_l4_envelope_with_any_surface_raises(self):
        """L4 has no learnable surfaces; envelope with surfaces raises."""
        with pytest.raises(LearnableSurfacesViolation):
            validate_envelope_learnable_surfaces(
                {"learnable_surfaces": ["prompt_template_variants"]},
                "L4",
            )
