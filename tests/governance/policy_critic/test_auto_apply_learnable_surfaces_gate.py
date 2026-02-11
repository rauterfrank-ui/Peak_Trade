"""
Tests for learnable surfaces gate in auto-apply flow.

When context has layer_id and/or requested_surfaces, the gate denies auto-apply
unless surfaces are explicitly allowed. Missing or disallowed => deny (no crash).
"""

import pytest

from src.governance.policy_critic.auto_apply_gate import (
    ApplyMode,
    evaluate_policy_critic_before_apply,
)


class TestLearnableSurfacesGateDeny:
    """Gate denies when surfaces not allowed or not explicit."""

    def test_missing_layer_id_denies(self):
        """Context with requested_surfaces but no layer_id => deny (__unknown__)."""
        decision = evaluate_policy_critic_before_apply(
            "diff",
            ["file.txt"],
            context={"requested_surfaces": ["retrieval_query_templates"]},
        )
        assert decision.allowed is False
        assert decision.mode == ApplyMode.MANUAL_ONLY
        assert "Learnable surfaces" in decision.reason
        assert decision.inputs_summary.get("learnable_surfaces_violation")
        assert decision.inputs_summary.get("layer_id") == "L0"
        assert decision.inputs_summary.get("requested_surfaces") == ["__unknown__"]

    def test_missing_requested_surfaces_denies(self):
        """Context with layer_id but no requested_surfaces => deny (__unknown__)."""
        decision = evaluate_policy_critic_before_apply(
            "diff",
            ["file.txt"],
            context={"layer_id": "L1"},
        )
        assert decision.allowed is False
        assert decision.mode == ApplyMode.MANUAL_ONLY
        assert "Learnable surfaces" in decision.reason
        assert decision.inputs_summary.get("requested_surfaces") == ["__unknown__"]

    def test_l0_with_any_surface_denies(self):
        """L0 has no learnable surfaces => deny."""
        decision = evaluate_policy_critic_before_apply(
            "diff",
            ["file.txt"],
            context={"layer_id": "L0", "requested_surfaces": ["anything"]},
        )
        assert decision.allowed is False
        assert "Learnable surfaces" in decision.reason

    def test_l1_disallowed_surface_denies(self):
        """L1 with surface not on allowlist => deny."""
        decision = evaluate_policy_critic_before_apply(
            "diff",
            ["file.txt"],
            context={
                "layer_id": "L1",
                "requested_surfaces": ["retrieval_query_templates", "forbidden_surface"],
            },
        )
        assert decision.allowed is False
        assert "Learnable surfaces" in decision.reason
        assert "learnable_surfaces_violation" in (decision.inputs_summary or {})


class TestLearnableSurfacesGateAllow:
    """Gate allows when layer_id + requested_surfaces are explicit and allowed."""

    def test_l1_allowed_surfaces_passes_gate(self):
        """L1 with only allowed surfaces passes gate (policy critic still runs)."""
        decision = evaluate_policy_critic_before_apply(
            "+++ b/docs/readme\n+line\n",
            ["docs/readme"],
            context={
                "layer_id": "L1",
                "requested_surfaces": ["retrieval_query_templates"],
            },
        )
        # Gate passes; no surfaces violation in report
        assert decision.inputs_summary is not None
        assert "learnable_surfaces_violation" not in decision.inputs_summary

    def test_l2_allowed_surfaces_passes_gate(self):
        """L2 with allowed surfaces passes gate."""
        decision = evaluate_policy_critic_before_apply(
            "+++ b/config/foo\n+bar\n",
            ["config/foo"],
            context={
                "layer_id": "L2",
                "requested_surfaces": ["scenario_priors"],
            },
        )
        assert decision.inputs_summary is not None
        assert "learnable_surfaces_violation" not in decision.inputs_summary

    def test_empty_requested_surfaces_passes_gate(self):
        """Explicit empty list is allowed (nothing to check)."""
        decision = evaluate_policy_critic_before_apply(
            "+++ b/readme\n+text\n",
            ["readme"],
            context={"layer_id": "L1", "requested_surfaces": []},
        )
        assert "learnable_surfaces_violation" not in (decision.inputs_summary or {})


class TestLearnableSurfacesGateNoContext:
    """When context has no layer_id or requested_surfaces, gate is skipped."""

    def test_no_context_skips_gate(self):
        """No layer_id/requested_surfaces in context => gate not applied."""
        decision = evaluate_policy_critic_before_apply(
            "+++ b/src/strategies/test.py\n+def f(): pass\n",
            ["src/strategies/test.py"],
        )
        # Should be allowed by policy critic (clean change); no surfaces violation
        assert "learnable_surfaces_violation" not in (decision.inputs_summary or {})
        assert decision.allowed is True
