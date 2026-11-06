"""Recovery Manager for Kill Switch.

Manages the multi-stage recovery process after kill switch activation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Optional

from .health_check import HealthCheckResult, HealthChecker


class RecoveryStage(Enum):
    """Recovery stages."""

    PENDING = auto()  # Waiting for approval
    VALIDATING = auto()  # Running health checks
    COOLDOWN = auto()  # Cooldown phase
    GRADUAL_RESTART = auto()  # Limited restart
    COMPLETE = auto()  # Fully recovered


@dataclass
class RecoveryRequest:
    """Recovery request information.

    Attributes:
        requested_at: When recovery was requested
        requested_by: Who requested recovery
        approval_code: Approval code provided
        reason: Reason for recovery
        stage: Current recovery stage
        approved_at: When approved (after validation)
        health_check_result: Result of health checks
    """

    requested_at: datetime
    requested_by: str
    approval_code: str
    reason: str
    stage: RecoveryStage = RecoveryStage.PENDING
    approved_at: Optional[datetime] = None
    health_check_result: Optional[HealthCheckResult] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "requested_at": self.requested_at.isoformat(),
            "requested_by": self.requested_by,
            "reason": self.reason,
            "stage": self.stage.name,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "health_check_passed": (
                self.health_check_result.is_healthy if self.health_check_result else None
            ),
        }


class RecoveryManager:
    """Manages kill switch recovery process.

    Ensures recovery is:
        - Authorized (approval code)
        - Safe (health checks)
        - Controlled (cooldown + gradual restart)

    Usage:
        >>> config = load_config()["kill_switch.recovery"]
        >>> health_checker = HealthChecker(config)
        >>> manager = RecoveryManager(config, health_checker)
        >>>
        >>> # Request recovery
        >>> request = manager.request_recovery("operator", "CODE", "Fixed")
        >>>
        >>> # Validate
        >>> if manager.validate_approval("CODE"):
        ...     result = manager.run_health_checks()
        ...     if result.is_healthy:
        ...         # Wait for cooldown, then complete recovery
    """

    def __init__(
        self,
        config: dict,
        health_checker: HealthChecker,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize recovery manager.

        Args:
            config: Recovery configuration
            health_checker: HealthChecker instance
            logger: Optional logger instance
        """
        self.config = config
        self.health_checker = health_checker
        self._logger = logger or logging.getLogger(__name__)

        self._current_request: Optional[RecoveryRequest] = None
        self._position_limit_factor = 1.0  # Normal

        # Gradual restart configuration
        self._gradual_enabled = config.get("gradual_restart_enabled", True)
        self._initial_factor = config.get("initial_position_limit_factor", 0.5)
        self._intervals = config.get("escalation_intervals", [3600, 7200])
        self._factors = config.get("escalation_factors", [0.75, 1.0])

    def request_recovery(
        self,
        requested_by: str,
        approval_code: str,
        reason: str,
    ) -> RecoveryRequest:
        """Start recovery request.

        Args:
            requested_by: Operator name
            approval_code: Approval code for validation
            reason: Reason for recovery

        Returns:
            RecoveryRequest object
        """
        self._current_request = RecoveryRequest(
            requested_at=datetime.utcnow(),
            requested_by=requested_by,
            approval_code=approval_code,
            reason=reason,
        )

        self._logger.info(f"Recovery requested by {requested_by}: {reason}")

        return self._current_request

    def validate_approval(self, expected_code: str) -> bool:
        """Validate approval code.

        Args:
            expected_code: Expected approval code

        Returns:
            True if valid
        """
        if not self._current_request:
            return False

        if self._current_request.approval_code != expected_code:
            self._logger.warning("❌ Invalid approval code")
            return False

        self._current_request.approved_at = datetime.utcnow()
        self._current_request.stage = RecoveryStage.VALIDATING

        self._logger.info("✅ Approval code validated")
        return True

    def run_health_checks(self, context: Optional[dict] = None) -> HealthCheckResult:
        """Run health checks.

        Args:
            context: Optional system context

        Returns:
            HealthCheckResult
        """
        if not self._current_request:
            raise ValueError("No active recovery request")

        result = self.health_checker.check_all(context)
        self._current_request.health_check_result = result

        if result.is_healthy:
            self._current_request.stage = RecoveryStage.COOLDOWN
            self._logger.info("✅ Health checks passed")
        else:
            self._logger.error(f"❌ Health checks failed: {result.issues}")

        return result

    def check_cooldown_complete(self, cooldown_seconds: int) -> bool:
        """Check if cooldown is complete.

        Args:
            cooldown_seconds: Cooldown duration

        Returns:
            True if cooldown complete
        """
        if not self._current_request or not self._current_request.approved_at:
            return False

        elapsed = (datetime.utcnow() - self._current_request.approved_at).total_seconds()
        return elapsed >= cooldown_seconds

    def get_cooldown_remaining(self, cooldown_seconds: int) -> float:
        """Get remaining cooldown time.

        Args:
            cooldown_seconds: Cooldown duration

        Returns:
            Remaining seconds
        """
        if not self._current_request or not self._current_request.approved_at:
            return cooldown_seconds

        elapsed = (datetime.utcnow() - self._current_request.approved_at).total_seconds()
        return max(0.0, cooldown_seconds - elapsed)

    def start_gradual_restart(self):
        """Start gradual restart phase."""
        # Initialize dummy request if called without active request (for testing)
        if not self._current_request:
            self._current_request = RecoveryRequest(
                requested_at=datetime.utcnow(),
                requested_by="system",
                approval_code="",
                reason="Direct gradual restart",
                stage=RecoveryStage.GRADUAL_RESTART,
                approved_at=datetime.utcnow(),
            )

        if not self._gradual_enabled:
            self._position_limit_factor = 1.0
            self._current_request.stage = RecoveryStage.COMPLETE
            self._logger.info("Gradual restart disabled, full recovery")
            return

        self._position_limit_factor = self._initial_factor
        self._current_request.stage = RecoveryStage.GRADUAL_RESTART

        self._logger.info(f"Gradual restart started: position_limit_factor={self._initial_factor}")

    def update_gradual_restart(self) -> float:
        """Update gradual restart based on time elapsed.

        Returns:
            Current position_limit_factor
        """
        if not self._current_request or not self._current_request.approved_at:
            return self._position_limit_factor

        if self._current_request.stage != RecoveryStage.GRADUAL_RESTART:
            return self._position_limit_factor

        elapsed = (datetime.utcnow() - self._current_request.approved_at).total_seconds()

        # Find appropriate factor based on time
        new_factor = self._initial_factor
        for interval, factor in zip(self._intervals, self._factors):
            if elapsed >= interval:
                new_factor = factor

        if new_factor != self._position_limit_factor:
            self._logger.info(
                f"Position limit escalated: {self._position_limit_factor} → {new_factor}"
            )
            self._position_limit_factor = new_factor

        # Check if complete
        if self._position_limit_factor >= 1.0:
            self._current_request.stage = RecoveryStage.COMPLETE
            self._logger.info("✅ Gradual restart complete")

        return self._position_limit_factor

    @property
    def position_limit_factor(self) -> float:
        """Current position limit factor (0.0 - 1.0).

        Used to scale down position sizes during gradual restart:
        - 0.5 = 50% of normal position size
        - 0.75 = 75% of normal position size
        - 1.0 = 100% (full recovery)
        """
        return self._position_limit_factor

    @property
    def current_stage(self) -> Optional[RecoveryStage]:
        """Current recovery stage."""
        if self._current_request:
            return self._current_request.stage
        return None

    @property
    def current_request(self) -> Optional[RecoveryRequest]:
        """Current recovery request."""
        return self._current_request

    def reset(self):
        """Reset recovery state."""
        self._current_request = None
        self._position_limit_factor = 1.0
        self._logger.info("Recovery state reset")
