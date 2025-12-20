"""
Peak_Trade Autonomous Decision Engine
======================================

AI-enhanced decision logic for autonomous workflow execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


class DecisionAction(str, Enum):
    """Possible workflow actions."""
    EXECUTE = "execute"
    SKIP = "skip"
    ALERT = "alert"
    WAIT = "wait"


@dataclass
class DecisionCriteria:
    """
    Criteria for workflow decision-making.
    
    Attributes:
        name: Criteria name
        threshold: Decision threshold
        weight: Importance weight (0.0-1.0)
        metric_name: Name of metric to evaluate
        comparison: Comparison operator (gt, lt, eq, gte, lte)
    """
    name: str
    threshold: float
    weight: float = 1.0
    metric_name: str = ""
    comparison: Literal["gt", "lt", "eq", "gte", "lte"] = "gt"
    
    def evaluate(self, value: float) -> bool:
        """
        Evaluate criteria against a value.
        
        Args:
            value: Value to compare against threshold
            
        Returns:
            True if criteria is met
        """
        if self.comparison == "gt":
            return value > self.threshold
        elif self.comparison == "gte":
            return value >= self.threshold
        elif self.comparison == "lt":
            return value < self.threshold
        elif self.comparison == "lte":
            return value <= self.threshold
        elif self.comparison == "eq":
            return abs(value - self.threshold) < 1e-6
        return False


@dataclass
class WorkflowDecision:
    """
    Decision outcome for workflow execution.
    
    Attributes:
        action: Recommended action
        confidence: Confidence score (0.0-1.0)
        reasoning: Human-readable reasoning
        criteria_results: Results from individual criteria
        metadata: Additional decision metadata
    """
    action: DecisionAction
    confidence: float
    reasoning: str
    criteria_results: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def should_execute(self) -> bool:
        """Check if workflow should be executed."""
        return self.action == DecisionAction.EXECUTE
    
    @property
    def should_alert(self) -> bool:
        """Check if alert should be sent."""
        return self.action == DecisionAction.ALERT


class DecisionEngine:
    """
    AI-enhanced decision engine for autonomous workflows.
    
    Makes intelligent decisions about when and how to execute workflows
    based on market conditions, performance metrics, and predefined rules.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize decision engine.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.criteria: Dict[str, List[DecisionCriteria]] = {}
        self._initialize_default_criteria()
        
    def _initialize_default_criteria(self) -> None:
        """Initialize default decision criteria."""
        # Signal analysis criteria
        self.criteria["signal_analysis"] = [
            DecisionCriteria(
                name="signal_strength",
                threshold=0.5,
                weight=0.8,
                metric_name="signal_strength",
                comparison="gt"
            ),
            DecisionCriteria(
                name="volatility_acceptable",
                threshold=0.3,
                weight=0.6,
                metric_name="volatility",
                comparison="lt"
            ),
        ]
        
        # Risk check criteria
        self.criteria["risk_check"] = [
            DecisionCriteria(
                name="max_drawdown_limit",
                threshold=0.2,
                weight=1.0,
                metric_name="current_drawdown",
                comparison="lt"
            ),
            DecisionCriteria(
                name="position_size_limit",
                threshold=0.15,
                weight=0.9,
                metric_name="position_size_pct",
                comparison="lt"
            ),
        ]
        
        # Market scan criteria
        self.criteria["market_scan"] = [
            DecisionCriteria(
                name="market_hours",
                threshold=1.0,
                weight=0.7,
                metric_name="is_market_hours",
                comparison="eq"
            ),
            DecisionCriteria(
                name="recent_activity",
                threshold=0.1,
                weight=0.5,
                metric_name="activity_level",
                comparison="gt"
            ),
        ]
        
    def add_criteria(
        self,
        workflow_type: str,
        criteria: DecisionCriteria
    ) -> None:
        """
        Add decision criteria for a workflow type.
        
        Args:
            workflow_type: Type of workflow
            criteria: Criteria to add
        """
        if workflow_type not in self.criteria:
            self.criteria[workflow_type] = []
        self.criteria[workflow_type].append(criteria)
    
    def make_decision(
        self,
        workflow_type: str,
        metrics: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowDecision:
        """
        Make a decision about workflow execution.
        
        Args:
            workflow_type: Type of workflow
            metrics: Current metrics to evaluate
            context: Optional additional context
            
        Returns:
            WorkflowDecision with recommended action
        """
        context = context or {}
        
        # Get criteria for this workflow type
        workflow_criteria = self.criteria.get(workflow_type, [])
        
        if not workflow_criteria:
            # No criteria defined, default to execute with low confidence
            return WorkflowDecision(
                action=DecisionAction.EXECUTE,
                confidence=0.3,
                reasoning=f"No criteria defined for {workflow_type}, executing with default behavior",
                metadata={"workflow_type": workflow_type}
            )
        
        # Evaluate each criterion
        criteria_results = {}
        total_weight = 0.0
        weighted_score = 0.0
        
        for criterion in workflow_criteria:
            metric_value = metrics.get(criterion.metric_name, 0.0)
            is_met = criterion.evaluate(metric_value)
            criteria_results[criterion.name] = is_met
            
            total_weight += criterion.weight
            if is_met:
                weighted_score += criterion.weight
        
        # Calculate confidence score
        confidence = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Determine action based on confidence
        if confidence >= 0.8:
            action = DecisionAction.EXECUTE
            reasoning = f"High confidence ({confidence:.2f}): All key criteria met"
        elif confidence >= 0.6:
            action = DecisionAction.EXECUTE
            reasoning = f"Moderate confidence ({confidence:.2f}): Most criteria met"
        elif confidence >= 0.4:
            action = DecisionAction.ALERT
            reasoning = f"Low confidence ({confidence:.2f}): Some criteria not met, alerting"
        else:
            action = DecisionAction.SKIP
            reasoning = f"Very low confidence ({confidence:.2f}): Criteria not met, skipping"
        
        # Check for override conditions in context
        if context.get("force_execute"):
            action = DecisionAction.EXECUTE
            reasoning = "Forced execution via context override"
            confidence = 1.0
        elif context.get("force_skip"):
            action = DecisionAction.SKIP
            reasoning = "Forced skip via context override"
            confidence = 1.0
        
        return WorkflowDecision(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            criteria_results=criteria_results,
            metadata={
                "workflow_type": workflow_type,
                "evaluated_criteria": len(workflow_criteria),
                "total_weight": total_weight,
                "weighted_score": weighted_score,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    def evaluate_market_conditions(
        self,
        symbol: str,
        timeframe: str = "1h",
    ) -> Dict[str, float]:
        """
        Evaluate current market conditions.
        
        This is a placeholder that returns mock metrics.
        In production, this would integrate with real market data.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for evaluation
            
        Returns:
            Dictionary of market metrics
        """
        # Placeholder implementation
        # In production, this would fetch real market data
        return {
            "volatility": 0.15,
            "signal_strength": 0.6,
            "activity_level": 0.3,
            "is_market_hours": 1.0,
        }
    
    def evaluate_portfolio_metrics(
        self,
        portfolio_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Evaluate current portfolio metrics.
        
        This is a placeholder that returns mock metrics.
        In production, this would integrate with portfolio tracking.
        
        Args:
            portfolio_id: Optional portfolio identifier
            
        Returns:
            Dictionary of portfolio metrics
        """
        # Placeholder implementation
        # In production, this would fetch real portfolio data
        return {
            "current_drawdown": 0.08,
            "position_size_pct": 0.12,
            "sharpe_ratio": 1.2,
            "win_rate": 0.55,
        }
    
    def get_criteria_for_workflow(
        self,
        workflow_type: str
    ) -> List[DecisionCriteria]:
        """
        Get all criteria for a workflow type.
        
        Args:
            workflow_type: Type of workflow
            
        Returns:
            List of criteria
        """
        return self.criteria.get(workflow_type, [])
