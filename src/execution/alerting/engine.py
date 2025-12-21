"""
Alert Engine - Phase 16I + 16J

Core alerting engine with deduplication, cooldown, rate limiting, and operator state.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .models import AlertEvent, AlertSeverity
from .rules import AlertRule, DEFAULT_RULES

if TYPE_CHECKING:
    from .operator_state import OperatorState

logger = logging.getLogger(__name__)


class AlertEngine:
    """
    Telemetry alert engine.

    Features:
    - Rule evaluation against health + trend reports
    - Deduplication (same dedupe_key within window)
    - Cooldown (per-rule minimum time between fires)
    - Rate limiting (max alerts per run)
    - Deterministic ordering (by severity, then timestamp)
    """

    def __init__(
        self,
        rules: Optional[List[AlertRule]] = None,
        max_alerts_per_run: int = 20,
        operator_state: Optional["OperatorState"] = None,
    ):
        """
        Initialize alert engine.

        Args:
            rules: List of alert rules (defaults to DEFAULT_RULES)
            max_alerts_per_run: Maximum alerts to emit per run
            operator_state: Optional operator state (for ACK/SNOOZE) - Phase 16J
        """
        self.rules = rules if rules is not None else DEFAULT_RULES.copy()
        self.max_alerts_per_run = max_alerts_per_run
        self.operator_state = operator_state

        # State tracking
        self._last_alert_by_dedupe_key: Dict[str, datetime] = {}
        self._last_fire_by_rule_id: Dict[str, datetime] = {}

    def evaluate(
        self,
        health_report: Optional[Dict[str, Any]] = None,
        trend_report: Optional[Dict[str, Any]] = None,
    ) -> List[AlertEvent]:
        """
        Evaluate all rules and return triggered alerts.

        Args:
            health_report: Health check report (from telemetry_health)
            trend_report: Trend analysis report (from telemetry_health_trends)

        Returns:
            List of AlertEvent objects (deduplicated, cooldown-applied, rate-limited)
        """
        now = datetime.now(timezone.utc)

        # Build evaluation context
        context = self._build_context(health_report, trend_report)

        # Evaluate all rules
        candidate_alerts = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Check operator state: SNOOZE (Phase 16J)
            if self.operator_state and self.operator_state.is_snoozed(rule.rule_id):
                logger.debug(f"Rule {rule.rule_id} is snoozed, skipping")
                continue

            # Check cooldown
            if not self._check_cooldown(rule, now):
                logger.debug(f"Rule {rule.rule_id} in cooldown, skipping")
                continue

            # Evaluate rule
            alert = rule.evaluate(context)

            if alert:
                candidate_alerts.append((rule, alert))

        # Apply deduplication + operator state (ACK)
        alerts = []

        for rule, alert in candidate_alerts:
            # Check operator state: ACK (Phase 16J)
            if self.operator_state and self.operator_state.is_acked(
                alert.dedupe_key, severity=alert.severity.value
            ):
                logger.debug(f"Alert acked: {alert.dedupe_key}")
                continue

            if self._check_dedupe(rule, alert, now):
                alerts.append(alert)

                # Update state
                self._last_alert_by_dedupe_key[alert.dedupe_key] = now
                self._last_fire_by_rule_id[rule.rule_id] = now
            else:
                logger.debug(f"Alert deduplicated: {alert.dedupe_key}")

        # Sort by severity (critical first), then timestamp
        alerts.sort(key=lambda a: (-a.severity.priority, a.timestamp_utc))

        # Apply rate limiting
        if len(alerts) > self.max_alerts_per_run:
            logger.warning(
                f"Rate limit exceeded: {len(alerts)} alerts, limiting to {self.max_alerts_per_run}"
            )
            alerts = alerts[: self.max_alerts_per_run]

        return alerts

    def _build_context(
        self,
        health_report: Optional[Dict[str, Any]],
        trend_report: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build evaluation context from health + trend reports."""
        context = {}

        if health_report:
            context["health_report"] = health_report
            context["health_status"] = health_report.get("status", "unknown")
            context["health_exit_code"] = health_report.get("exit_code", 0)

            # Extract metrics from checks
            checks = health_report.get("checks", [])
            for check in checks:
                name = check.get("name", "")
                value = check.get("value")
                if name and value is not None:
                    context[f"health_{name}_value"] = value

        if trend_report:
            context["trend_report"] = trend_report

            # Extract degradation info
            degradation = trend_report.get("degradation", {})
            context["degradation"] = degradation
            context["degradation_degrading"] = degradation.get("degrading", False)
            context["degradation_reasons"] = ", ".join(
                str(r) for r in degradation.get("reasons", [])
            )
            context["degradation_critical_count"] = degradation.get("critical_count", 0)
            context["degradation_warn_count"] = degradation.get("warn_count", 0)
            context["degradation_window_size"] = degradation.get("window_size", 0)

            # Extract rollup metrics
            overall = trend_report.get("overall", {})
            if overall:
                context["trend_worst_severity"] = overall.get("worst_severity", "ok")
                context["trend_critical_count"] = overall.get("critical_count", 0)
                context["trend_warn_count"] = overall.get("warn_count", 0)

        return context

    def _check_cooldown(self, rule: AlertRule, now: datetime) -> bool:
        """Check if rule is past cooldown period."""
        last_fire = self._last_fire_by_rule_id.get(rule.rule_id)

        if last_fire is None:
            return True

        cooldown_delta = timedelta(seconds=rule.cooldown_seconds)
        return (now - last_fire) >= cooldown_delta

    def _check_dedupe(self, rule: AlertRule, alert: AlertEvent, now: datetime) -> bool:
        """Check if alert should be deduplicated."""
        if not alert.dedupe_key:
            return True

        last_alert = self._last_alert_by_dedupe_key.get(alert.dedupe_key)

        if last_alert is None:
            return True

        dedupe_window = timedelta(seconds=rule.dedupe_window_seconds)
        return (now - last_alert) >= dedupe_window

    def clear_state(self):
        """Clear engine state (cooldown + dedupe tracking)."""
        self._last_alert_by_dedupe_key.clear()
        self._last_fire_by_rule_id.clear()

    def get_enabled_rules(self) -> List[AlertRule]:
        """Get list of enabled rules."""
        return [r for r in self.rules if r.enabled]

    def get_rule_by_id(self, rule_id: str) -> Optional[AlertRule]:
        """Get rule by ID."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def enable_rule(self, rule_id: str):
        """Enable a rule."""
        rule = self.get_rule_by_id(rule_id)
        if rule:
            rule.enabled = True
            logger.info(f"Enabled rule: {rule_id}")

    def disable_rule(self, rule_id: str):
        """Disable a rule."""
        rule = self.get_rule_by_id(rule_id)
        if rule:
            rule.enabled = False
            logger.info(f"Disabled rule: {rule_id}")
