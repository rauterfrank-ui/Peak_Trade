"""System Watchdog Trigger.

Monitors system health: heartbeat, memory, CPU usage.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from .base import BaseTrigger, TriggerResult

# Optional dependency: psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore


logger = logging.getLogger(__name__)


class WatchdogTrigger(BaseTrigger):
    """System health watchdog.

    Monitors:
        - Heartbeat (process is alive)
        - Memory usage
        - CPU usage

    Config Example:
        {
            "enabled": true,
            "type": "watchdog",
            "heartbeat_interval_seconds": 60,
            "max_missed_heartbeats": 3,
            "memory_threshold_percent": 90,
            "cpu_threshold_percent": 95
        }

    Note:
        Requires psutil package. If not installed, this trigger
        will be disabled with a warning.
    """

    def __init__(self, name: str, config: dict):
        """Initialize watchdog trigger.

        Args:
            name: Trigger name
            config: Configuration with thresholds
        """
        super().__init__(name, config)

        if not PSUTIL_AVAILABLE:
            logger.warning(
                f"Watchdog trigger '{name}' disabled: psutil not installed. "
                f"Install with: pip install psutil"
            )
            self.enabled = False

        self.heartbeat_interval = timedelta(
            seconds=config.get("heartbeat_interval_seconds", 60)
        )
        self.max_missed = config.get("max_missed_heartbeats", 3)
        self.memory_threshold = config.get("memory_threshold_percent", 90)
        self.cpu_threshold = config.get("cpu_threshold_percent", 95)

        self._last_heartbeat: Optional[datetime] = None
        self._missed_heartbeats = 0

    def heartbeat(self):
        """Register a heartbeat.

        This should be called periodically by the main trading loop
        to indicate the system is alive and responsive.
        """
        self._last_heartbeat = datetime.utcnow()
        self._missed_heartbeats = 0

    def check(self, context: dict) -> TriggerResult:
        """Check system health.

        Args:
            context: System context

        Returns:
            TriggerResult indicating if system health is critical
        """
        if not self.enabled or not PSUTIL_AVAILABLE:
            return TriggerResult(
                should_trigger=False,
                reason=f"Watchdog '{self.name}' disabled or psutil not available"
            )

        issues = []
        metadata = {}

        # Check heartbeat
        if self._last_heartbeat:
            elapsed = datetime.utcnow() - self._last_heartbeat
            if elapsed > self.heartbeat_interval:
                self._missed_heartbeats += 1
                if self._missed_heartbeats >= self.max_missed:
                    issues.append(
                        f"Missed {self._missed_heartbeats} heartbeats "
                        f"(>{self.max_missed} threshold)"
                    )
                metadata["missed_heartbeats"] = self._missed_heartbeats

        # Check memory
        try:
            memory = psutil.virtual_memory()
            metadata["memory_percent"] = memory.percent

            if memory.percent > self.memory_threshold:
                issues.append(
                    f"Memory critical: {memory.percent:.1f}% > "
                    f"{self.memory_threshold}%"
                )
        except Exception as e:
            logger.warning(f"Failed to check memory: {e}")

        # Check CPU
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            metadata["cpu_percent"] = cpu

            if cpu > self.cpu_threshold:
                issues.append(
                    f"CPU critical: {cpu:.1f}% > {self.cpu_threshold}%"
                )
        except Exception as e:
            logger.warning(f"Failed to check CPU: {e}")

        if issues:
            self.mark_triggered()
            return TriggerResult(
                should_trigger=True,
                reason="; ".join(issues),
                metadata={
                    "trigger_name": self.name,
                    "trigger_type": "watchdog",
                    **metadata,
                }
            )

        return TriggerResult(
            should_trigger=False,
            reason="System health OK",
            metadata=metadata,
        )

    def __repr__(self) -> str:
        return (
            f"WatchdogTrigger("
            f"name='{self.name}', "
            f"memory_threshold={self.memory_threshold}%, "
            f"cpu_threshold={self.cpu_threshold}%, "
            f"max_missed={self.max_missed}, "
            f"enabled={self.enabled}"
            f")"
        )
