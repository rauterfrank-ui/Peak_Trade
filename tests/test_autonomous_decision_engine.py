"""
Tests for Autonomous Decision Engine
=====================================
"""

import pytest

from src.autonomous.decision_engine import (
    DecisionEngine,
    DecisionCriteria,
    WorkflowDecision,
    DecisionAction,
)


class TestDecisionCriteria:
    """Tests for DecisionCriteria."""

    def test_criteria_creation(self):
        """Test creating decision criteria."""
        criteria = DecisionCriteria(
            name="test_criteria",
            threshold=0.5,
            weight=0.8,
            metric_name="test_metric",
            comparison="gt",
        )

        assert criteria.name == "test_criteria"
        assert criteria.threshold == 0.5
        assert criteria.weight == 0.8
        assert criteria.comparison == "gt"

    def test_evaluate_greater_than(self):
        """Test evaluation with greater than comparison."""
        criteria = DecisionCriteria(name="test", threshold=0.5, comparison="gt")

        assert criteria.evaluate(0.6) is True
        assert criteria.evaluate(0.5) is False
        assert criteria.evaluate(0.4) is False

    def test_evaluate_greater_than_equal(self):
        """Test evaluation with >= comparison."""
        criteria = DecisionCriteria(name="test", threshold=0.5, comparison="gte")

        assert criteria.evaluate(0.6) is True
        assert criteria.evaluate(0.5) is True
        assert criteria.evaluate(0.4) is False

    def test_evaluate_less_than(self):
        """Test evaluation with less than comparison."""
        criteria = DecisionCriteria(name="test", threshold=0.5, comparison="lt")

        assert criteria.evaluate(0.4) is True
        assert criteria.evaluate(0.5) is False
        assert criteria.evaluate(0.6) is False

    def test_evaluate_less_than_equal(self):
        """Test evaluation with <= comparison."""
        criteria = DecisionCriteria(name="test", threshold=0.5, comparison="lte")

        assert criteria.evaluate(0.4) is True
        assert criteria.evaluate(0.5) is True
        assert criteria.evaluate(0.6) is False

    def test_evaluate_equal(self):
        """Test evaluation with equality comparison."""
        criteria = DecisionCriteria(name="test", threshold=0.5, comparison="eq")

        assert criteria.evaluate(0.5) is True
        assert criteria.evaluate(0.50000001) is True  # Within epsilon
        assert criteria.evaluate(0.6) is False


class TestWorkflowDecision:
    """Tests for WorkflowDecision."""

    def test_decision_creation(self):
        """Test creating a workflow decision."""
        decision = WorkflowDecision(
            action=DecisionAction.EXECUTE,
            confidence=0.85,
            reasoning="Test reasoning",
            criteria_results={"criteria1": True, "criteria2": True},
        )

        assert decision.action == DecisionAction.EXECUTE
        assert decision.confidence == 0.85
        assert decision.reasoning == "Test reasoning"
        assert decision.should_execute is True
        assert decision.should_alert is False

    def test_should_execute_property(self):
        """Test should_execute property."""
        execute_decision = WorkflowDecision(
            action=DecisionAction.EXECUTE, confidence=0.9, reasoning="Execute"
        )

        skip_decision = WorkflowDecision(
            action=DecisionAction.SKIP, confidence=0.3, reasoning="Skip"
        )

        assert execute_decision.should_execute is True
        assert skip_decision.should_execute is False

    def test_should_alert_property(self):
        """Test should_alert property."""
        alert_decision = WorkflowDecision(
            action=DecisionAction.ALERT, confidence=0.5, reasoning="Alert"
        )

        execute_decision = WorkflowDecision(
            action=DecisionAction.EXECUTE, confidence=0.9, reasoning="Execute"
        )

        assert alert_decision.should_alert is True
        assert execute_decision.should_alert is False


class TestDecisionEngine:
    """Tests for DecisionEngine."""

    def test_engine_initialization(self):
        """Test engine initialization with default criteria."""
        engine = DecisionEngine()

        # Should have default criteria for different workflow types
        assert "signal_analysis" in engine.criteria
        assert "risk_check" in engine.criteria
        assert "market_scan" in engine.criteria

        # Check signal_analysis has criteria
        assert len(engine.criteria["signal_analysis"]) > 0

    def test_add_criteria(self):
        """Test adding custom criteria."""
        engine = DecisionEngine()

        new_criteria = DecisionCriteria(
            name="custom_metric", threshold=0.7, weight=0.9, metric_name="custom", comparison="gt"
        )

        engine.add_criteria("custom_workflow", new_criteria)

        assert "custom_workflow" in engine.criteria
        assert len(engine.criteria["custom_workflow"]) == 1
        assert engine.criteria["custom_workflow"][0].name == "custom_metric"

    def test_make_decision_high_confidence(self):
        """Test decision making with high confidence."""
        engine = DecisionEngine()

        # Metrics that meet all criteria for signal_analysis
        metrics = {
            "signal_strength": 0.7,  # > 0.5
            "volatility": 0.2,  # < 0.3
        }

        decision = engine.make_decision(workflow_type="signal_analysis", metrics=metrics)

        assert decision.action == DecisionAction.EXECUTE
        assert decision.confidence >= 0.6  # Should be high confidence
        assert decision.criteria_results["signal_strength"] is True
        assert decision.criteria_results["volatility_acceptable"] is True

    def test_make_decision_low_confidence(self):
        """Test decision making with low confidence."""
        engine = DecisionEngine()

        # Metrics that don't meet criteria
        metrics = {
            "signal_strength": 0.3,  # < 0.5 (fails)
            "volatility": 0.5,  # > 0.3 (fails)
        }

        decision = engine.make_decision(workflow_type="signal_analysis", metrics=metrics)

        assert decision.action in [DecisionAction.SKIP, DecisionAction.ALERT]
        assert decision.confidence < 0.6
        assert decision.criteria_results["signal_strength"] is False
        assert decision.criteria_results["volatility_acceptable"] is False

    def test_make_decision_no_criteria(self):
        """Test decision making when no criteria defined."""
        engine = DecisionEngine()

        decision = engine.make_decision(workflow_type="undefined_workflow", metrics={})

        assert decision.action == DecisionAction.EXECUTE
        assert decision.confidence == 0.3  # Low default confidence
        assert "no criteria" in decision.reasoning.lower()

    def test_make_decision_force_execute(self):
        """Test forced execution via context."""
        engine = DecisionEngine()

        # Metrics that would normally skip
        metrics = {
            "signal_strength": 0.1,
            "volatility": 0.8,
        }

        decision = engine.make_decision(
            workflow_type="signal_analysis", metrics=metrics, context={"force_execute": True}
        )

        assert decision.action == DecisionAction.EXECUTE
        assert decision.confidence == 1.0
        assert "forced" in decision.reasoning.lower()

    def test_make_decision_force_skip(self):
        """Test forced skip via context."""
        engine = DecisionEngine()

        # Metrics that would normally execute
        metrics = {
            "signal_strength": 0.9,
            "volatility": 0.1,
        }

        decision = engine.make_decision(
            workflow_type="signal_analysis", metrics=metrics, context={"force_skip": True}
        )

        assert decision.action == DecisionAction.SKIP
        assert decision.confidence == 1.0
        assert "forced" in decision.reasoning.lower()

    def test_get_criteria_for_workflow(self):
        """Test getting criteria for a workflow type."""
        engine = DecisionEngine()

        criteria = engine.get_criteria_for_workflow("signal_analysis")

        assert len(criteria) > 0
        assert all(isinstance(c, DecisionCriteria) for c in criteria)

    def test_evaluate_market_conditions(self):
        """Test market conditions evaluation."""
        engine = DecisionEngine()

        metrics = engine.evaluate_market_conditions("BTC/EUR")

        assert "volatility" in metrics
        assert "signal_strength" in metrics
        assert isinstance(metrics["volatility"], (int, float))

    def test_evaluate_portfolio_metrics(self):
        """Test portfolio metrics evaluation."""
        engine = DecisionEngine()

        metrics = engine.evaluate_portfolio_metrics()

        assert "current_drawdown" in metrics
        assert "position_size_pct" in metrics
        assert isinstance(metrics["current_drawdown"], (int, float))


class TestDecisionEngineIntegration:
    """Integration tests for DecisionEngine."""

    def test_full_decision_flow(self):
        """Test complete decision flow."""
        engine = DecisionEngine()

        # Get market and portfolio metrics
        market_metrics = engine.evaluate_market_conditions("BTC/EUR")
        portfolio_metrics = engine.evaluate_portfolio_metrics()

        # Combine metrics
        combined_metrics = {**market_metrics, **portfolio_metrics}

        # Make decisions for different workflow types
        decisions = {}
        for workflow_type in ["signal_analysis", "risk_check", "market_scan"]:
            decision = engine.make_decision(workflow_type=workflow_type, metrics=combined_metrics)
            decisions[workflow_type] = decision

        # All should have valid decisions
        assert all(d.action in DecisionAction for d in decisions.values())
        assert all(0.0 <= d.confidence <= 1.0 for d in decisions.values())
        assert all(d.reasoning for d in decisions.values())

    def test_weighted_scoring(self):
        """Test weighted scoring calculation."""
        engine = DecisionEngine()

        # Create custom criteria with different weights
        engine.criteria["test_workflow"] = [
            DecisionCriteria(
                name="high_weight",
                threshold=0.5,
                weight=1.0,
                metric_name="metric1",
                comparison="gt",
            ),
            DecisionCriteria(
                name="low_weight", threshold=0.5, weight=0.2, metric_name="metric2", comparison="gt"
            ),
        ]

        # High weight met, low weight not met
        metrics = {
            "metric1": 0.8,  # Meets high weight criteria
            "metric2": 0.3,  # Fails low weight criteria
        }

        decision = engine.make_decision(workflow_type="test_workflow", metrics=metrics)

        # Should still have relatively high confidence due to weight
        assert decision.confidence > 0.7
