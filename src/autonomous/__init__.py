"""
Peak_Trade Autonomous Workflow System
======================================

AI-gesteuerte autonome Workflows für automatisierte Entscheidungsfindung,
Monitoring und Ausführung von Trading-Research-Workflows.

Modules:
    - decision_engine: AI-enhanced decision logic
    - workflow_engine: Workflow execution and coordination
    - monitors: Market and performance monitoring
    - rules: Decision rules and criteria
"""

from .decision_engine import (
    WorkflowDecision,
    DecisionEngine,
    DecisionCriteria,
)
from .workflow_engine import (
    WorkflowEngine,
    WorkflowState,
    WorkflowStatus,
    WorkflowResult,
)
from .monitors import (
    MarketMonitor,
    SignalMonitor,
    PerformanceMonitor,
)

__all__ = [
    "WorkflowDecision",
    "DecisionEngine",
    "DecisionCriteria",
    "WorkflowEngine",
    "WorkflowState",
    "WorkflowStatus",
    "WorkflowResult",
    "MarketMonitor",
    "SignalMonitor",
    "PerformanceMonitor",
]
