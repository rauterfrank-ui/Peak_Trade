"""Health Check system for Kill Switch Recovery.

Validates system health before allowing recovery from killed state.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

# Optional dependency: psutil
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore


logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of health checks.

    Attributes:
        is_healthy: Overall health status
        issues: List of health issues found
        checks_passed: Number of checks that passed
        checks_failed: Number of checks that failed
        metadata: Additional health data
    """

    is_healthy: bool
    issues: List[str] = field(default_factory=list)
    checks_passed: int = 0
    checks_failed: int = 0
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "is_healthy": self.is_healthy,
            "issues": self.issues,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class HealthChecker:
    """System health checker for Kill Switch recovery.

    Validates:
        - Memory availability
        - CPU usage
        - Exchange connection
        - Price feed freshness

    Usage:
        >>> config = {"min_memory_available_mb": 512, ...}
        >>> checker = HealthChecker(config)
        >>> result = checker.check_all()
        >>> if result.is_healthy:
        ...     # Proceed with recovery
    """

    def __init__(self, config: dict, logger: Optional[logging.Logger] = None):
        """Initialize health checker.

        Args:
            config: Recovery configuration
            logger: Optional logger instance
        """
        self.config = config
        self._logger = logger or logging.getLogger(__name__)

        # Configuration
        self.min_memory_mb = config.get("min_memory_available_mb", 512)
        self.max_cpu_percent = config.get("max_cpu_percent", 80)
        self.require_exchange = config.get("require_exchange_connection", True)
        self.require_price_feed = config.get("require_price_feed", True)

        if not PSUTIL_AVAILABLE:
            self._logger.warning("psutil not available - memory/CPU checks will be skipped")

    def check_all(self, context: Optional[dict] = None) -> HealthCheckResult:
        """Run all health checks.

        Args:
            context: Optional system context with runtime info

        Returns:
            HealthCheckResult with overall status
        """
        context = context or {}
        issues = []
        metadata = {}
        passed = 0
        failed = 0

        # Check memory
        memory_ok, memory_issue, memory_meta = self._check_memory()
        metadata.update(memory_meta)
        if memory_ok:
            passed += 1
        else:
            failed += 1
            if memory_issue:
                issues.append(memory_issue)

        # Check CPU
        cpu_ok, cpu_issue, cpu_meta = self._check_cpu()
        metadata.update(cpu_meta)
        if cpu_ok:
            passed += 1
        else:
            failed += 1
            if cpu_issue:
                issues.append(cpu_issue)

        # Check exchange connection
        if self.require_exchange:
            exchange_ok = context.get("exchange_connected", False)
            metadata["exchange_connected"] = exchange_ok

            if exchange_ok:
                passed += 1
            else:
                failed += 1
                issues.append("Exchange not connected")

        # Check price feed
        if self.require_price_feed:
            last_update = context.get("last_price_update")

            if last_update:
                age = (datetime.utcnow() - last_update).total_seconds()
                metadata["price_data_age_seconds"] = age

                # Consider stale if >5 minutes old
                if age < 300:
                    passed += 1
                else:
                    failed += 1
                    issues.append(f"Stale price data ({age:.0f}s old)")
            else:
                failed += 1
                issues.append("No price data available")

        is_healthy = failed == 0

        result = HealthCheckResult(
            is_healthy=is_healthy,
            issues=issues,
            checks_passed=passed,
            checks_failed=failed,
            metadata=metadata,
        )

        if is_healthy:
            self._logger.info(f"✅ Health check PASSED ({passed} checks)")
        else:
            self._logger.warning(f"❌ Health check FAILED: {failed} issues - {', '.join(issues)}")

        return result

    def _check_memory(self) -> tuple[bool, Optional[str], dict]:
        """Check memory availability.

        Returns:
            (is_ok, issue_message, metadata)
        """
        if not PSUTIL_AVAILABLE:
            return True, None, {"memory_check": "skipped"}

        try:
            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024 * 1024)

            metadata = {
                "memory_available_mb": available_mb,
                "memory_percent_used": memory.percent,
            }

            if available_mb >= self.min_memory_mb:
                return True, None, metadata
            else:
                return (
                    False,
                    f"Insufficient memory: {available_mb:.0f}MB < {self.min_memory_mb}MB",
                    metadata,
                )

        except Exception as e:
            self._logger.warning(f"Memory check failed: {e}")
            return True, None, {"memory_check": "error"}

    def _check_cpu(self) -> tuple[bool, Optional[str], dict]:
        """Check CPU usage.

        Returns:
            (is_ok, issue_message, metadata)
        """
        if not PSUTIL_AVAILABLE:
            return True, None, {"cpu_check": "skipped"}

        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)

            metadata = {
                "cpu_percent": cpu_percent,
            }

            if cpu_percent <= self.max_cpu_percent:
                return True, None, metadata
            else:
                return (
                    False,
                    f"High CPU usage: {cpu_percent:.1f}% > {self.max_cpu_percent}%",
                    metadata,
                )

        except Exception as e:
            self._logger.warning(f"CPU check failed: {e}")
            return True, None, {"cpu_check": "error"}
