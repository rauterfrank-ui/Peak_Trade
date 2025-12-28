"""Threshold-based Triggers.

Triggers based on metric thresholds (drawdown, loss, volatility, etc.).
"""

import operator as op
from typing import Callable, Dict

from .base import BaseTrigger, TriggerResult


class ThresholdTrigger(BaseTrigger):
    """Trigger based on metric thresholds.

    Examples:
        - Drawdown > -15% → Kill
        - Daily Loss > -5% → Kill
        - Volatility > 10% → Kill

    Config Example:
        {
            "enabled": true,
            "type": "threshold",
            "metric": "portfolio_drawdown",
            "threshold": -0.15,
            "operator": "lt",  # less than
            "cooldown_seconds": 0
        }
    """

    OPERATORS: Dict[str, Callable] = {
        "lt": op.lt,  # less than
        "le": op.le,  # less or equal
        "gt": op.gt,  # greater than
        "ge": op.ge,  # greater or equal
        "eq": op.eq,  # equal
        "ne": op.ne,  # not equal
    }

    def __init__(self, name: str, config: dict):
        """Initialize threshold trigger.

        Args:
            name: Trigger name
            config: Configuration with metric, threshold, operator
        """
        super().__init__(name, config)

        self.metric_name = config["metric"]
        self.threshold = config["threshold"]
        self.operator_name = config.get("operator", "lt")

        if self.operator_name not in self.OPERATORS:
            raise ValueError(
                f"Invalid operator: {self.operator_name}. "
                f"Must be one of: {list(self.OPERATORS.keys())}"
            )

        self.operator = self.OPERATORS[self.operator_name]

    def check(self, context: dict) -> TriggerResult:
        """Check metric against threshold.

        Args:
            context: System context with metrics

        Returns:
            TriggerResult indicating if threshold exceeded
        """
        if not self.enabled:
            return TriggerResult(should_trigger=False, reason=f"Trigger '{self.name}' disabled")

        if self.is_on_cooldown():
            return TriggerResult(
                should_trigger=False,
                reason=f"Trigger '{self.name}' on cooldown "
                f"({self.get_cooldown_remaining():.0f}s remaining)",
            )

        # Get metric from context
        metric_value = context.get(self.metric_name)

        if metric_value is None:
            return TriggerResult(
                should_trigger=False, reason=f"Metric '{self.metric_name}' not found in context"
            )

        # Check threshold
        should_trigger = self.operator(metric_value, self.threshold)

        if should_trigger:
            self.mark_triggered()
            return TriggerResult(
                should_trigger=True,
                reason=(
                    f"{self.metric_name}={metric_value:.4f} {self.operator_name} {self.threshold}"
                ),
                metric_value=metric_value,
                threshold=self.threshold,
                metadata={
                    "trigger_name": self.name,
                    "trigger_type": "threshold",
                    "operator": self.operator_name,
                },
            )

        return TriggerResult(
            should_trigger=False,
            reason=f"Threshold not reached: {metric_value:.4f}",
            metric_value=metric_value,
            threshold=self.threshold,
        )

    def __repr__(self) -> str:
        return (
            f"ThresholdTrigger("
            f"name='{self.name}', "
            f"metric='{self.metric_name}', "
            f"threshold={self.threshold}, "
            f"operator='{self.operator_name}', "
            f"enabled={self.enabled}"
            f")"
        )
