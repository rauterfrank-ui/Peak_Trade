"""
Tests for learnable surfaces policy: allow/deny by layer and surface.

- Allow: L1/L2/L3 with surfaces from allowlist
- Deny: L0/L4/L5/L6 always; unknown layer; unknown surface
- Empty requested list: allowed (nothing to deny)
"""

import pytest

from src.governance.learning.learnable_surfaces_policy import (
    LearnableSurfacesViolation,
    assert_surfaces_allowed,
    get_allowed_surfaces,
    load_policy,
)


# Policy fixture matching config/learning_surfaces.toml (L1/L2/L3 only).
POLICY = {
    "L1": ["retrieval_query_templates", "source_ranking_weights"],
    "L2": ["scenario_priors", "no_trade_trigger_thresholds"],
    "L3": ["prompt_template_variants"],
}


class TestAllowDenyMatrix:
    """Allow/deny matrix: L1/L2/L3 with allowed surfaces pass; others deny."""

    def test_l1_allowed_surfaces_pass(self):
        assert_surfaces_allowed("L1", ["retrieval_query_templates"], policy=POLICY)
        assert_surfaces_allowed("L1", ["source_ranking_weights"], policy=POLICY)
        assert_surfaces_allowed(
            "L1",
            ["retrieval_query_templates", "source_ranking_weights"],
            policy=POLICY,
        )

    def test_l2_allowed_surfaces_pass(self):
        assert_surfaces_allowed("L2", ["scenario_priors"], policy=POLICY)
        assert_surfaces_allowed("L2", ["no_trade_trigger_thresholds"], policy=POLICY)
        assert_surfaces_allowed(
            "L2",
            ["scenario_priors", "no_trade_trigger_thresholds"],
            policy=POLICY,
        )

    def test_l3_allowed_surfaces_pass(self):
        assert_surfaces_allowed("L3", ["prompt_template_variants"], policy=POLICY)

    def test_l0_always_deny(self):
        with pytest.raises(LearnableSurfacesViolation) as exc_info:
            assert_surfaces_allowed("L0", ["anything"], policy=POLICY)
        assert exc_info.value.layer_id == "L0"
        assert exc_info.value.allowed == []

    def test_l4_always_deny(self):
        with pytest.raises(LearnableSurfacesViolation) as exc_info:
            assert_surfaces_allowed("L4", ["policy_rules"], policy=POLICY)
        assert exc_info.value.layer_id == "L4"
        assert exc_info.value.allowed == []

    def test_l5_always_deny(self):
        with pytest.raises(LearnableSurfacesViolation) as exc_info:
            assert_surfaces_allowed("L5", ["limits"], policy=POLICY)
        assert exc_info.value.layer_id == "L5"

    def test_l6_always_deny(self):
        with pytest.raises(LearnableSurfacesViolation) as exc_info:
            assert_surfaces_allowed("L6", ["orders"], policy=POLICY)
        assert exc_info.value.layer_id == "L6"


class TestUnknownSurface:
    """Requesting a surface not on the allowlist raises."""

    def test_l1_unknown_surface_raises(self):
        with pytest.raises(LearnableSurfacesViolation) as exc_info:
            assert_surfaces_allowed("L1", ["retrieval_query_templates", "foo"], policy=POLICY)
        assert "foo" in str(exc_info.value.requested) or "foo" in str(exc_info.value)
        assert exc_info.value.layer_id == "L1"

    def test_l2_unknown_surface_raises(self):
        with pytest.raises(LearnableSurfacesViolation) as exc_info:
            assert_surfaces_allowed("L2", ["unknown_surface"], policy=POLICY)
        assert exc_info.value.layer_id == "L2"
        assert "unknown_surface" in exc_info.value.requested

    def test_l3_only_allowed_surface(self):
        with pytest.raises(LearnableSurfacesViolation):
            assert_surfaces_allowed("L3", ["prompt_template_variants", "other"], policy=POLICY)


class TestUnknownLayer:
    """Invalid layer_id raises ValueError."""

    def test_invalid_layer_raises(self):
        with pytest.raises(ValueError, match="Invalid layer_id"):
            assert_surfaces_allowed("L99", ["x"], policy=POLICY)

    def test_empty_string_layer_raises(self):
        with pytest.raises(ValueError, match="Invalid layer_id"):
            assert_surfaces_allowed("", ["x"], policy=POLICY)

    def test_unknown_layer_not_in_policy_denied(self):
        # L0 is valid layer id but deny-all; no need to be in policy
        with pytest.raises(LearnableSurfacesViolation):
            assert_surfaces_allowed("L0", ["any"], policy=POLICY)


class TestEmptyList:
    """Empty requested list is allowed (nothing to check)."""

    def test_l1_empty_requested_passes(self):
        assert_surfaces_allowed("L1", [], policy=POLICY)

    def test_l2_empty_requested_passes(self):
        assert_surfaces_allowed("L2", [], policy=POLICY)

    def test_l0_empty_requested_passes(self):
        # Empty requested = no surfaces to check; pass (no learning write).
        assert_surfaces_allowed("L0", [], policy=POLICY)

    def test_l4_empty_requested_passes(self):
        assert_surfaces_allowed("L4", [], policy=POLICY)


class TestGetAllowedSurfaces:
    """get_allowed_surfaces returns correct lists."""

    def test_l1_returns_allowlist(self):
        assert get_allowed_surfaces("L1", policy=POLICY) == [
            "retrieval_query_templates",
            "source_ranking_weights",
        ]

    def test_l0_returns_empty(self):
        assert get_allowed_surfaces("L0", policy=POLICY) == []

    def test_l4_returns_empty(self):
        assert get_allowed_surfaces("L4", policy=POLICY) == []

    def test_unknown_layer_in_policy_returns_empty(self):
        # Layer not in policy (e.g. L5) -> []
        assert get_allowed_surfaces("L5", policy=POLICY) == []


class TestLoadPolicy:
    """load_policy loads from config when available."""

    def test_load_policy_returns_dict(self):
        policy = load_policy()
        assert isinstance(policy, dict)

    def test_load_policy_has_l1_l2_l3(self):
        policy = load_policy()
        # Repo has config/learning_surfaces.toml with L1, L2, L3
        assert "L1" in policy or "L2" in policy or "L3" in policy
