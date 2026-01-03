"""
Live Mode Gate - Phase 0 WP0C

Provides governance layer for live execution:
- Blocked-by-default (explicit opt-in required)
- Environment separation (dev/shadow/testnet/prod)
- Fail-fast config validation
- Audit trail for mode transitions

Design Principles:
1. Safety-first: Live mode requires explicit approval
2. Environment isolation: Clear boundaries between envs
3. Validation: Config must be valid before mode switch
4. Auditability: All mode transitions are logged
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
import os


class ExecutionEnvironment(str, Enum):
    """Execution environment types."""

    DEV = "dev"
    SHADOW = "shadow"
    TESTNET = "testnet"
    PROD = "prod"

    def is_live(self) -> bool:
        """Check if environment is considered 'live' (real capital at risk)."""
        return self in {ExecutionEnvironment.TESTNET, ExecutionEnvironment.PROD}

    def requires_extra_validation(self) -> bool:
        """Check if environment requires extra validation steps."""
        return self in {ExecutionEnvironment.TESTNET, ExecutionEnvironment.PROD}


class LiveModeStatus(str, Enum):
    """Live mode status."""

    BLOCKED = "blocked"  # Default: live mode not allowed
    APPROVED = "approved"  # Explicitly approved for live execution
    SUSPENDED = "suspended"  # Temporarily suspended (after approval)
    FAILED_VALIDATION = "failed_validation"  # Config validation failed


@dataclass
class ValidationResult:
    """Result of config validation."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


@dataclass
class LiveModeGateState:
    """Current state of the live mode gate."""

    environment: ExecutionEnvironment
    status: LiveModeStatus
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    reason: str = ""
    config_hash: Optional[str] = None
    validation_result: Optional[ValidationResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_allowed(self) -> bool:
        """Check if live execution is currently allowed."""
        return self.status == LiveModeStatus.APPROVED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "environment": self.environment.value,
            "status": self.status.value,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "reason": self.reason,
            "config_hash": self.config_hash,
            "validation_result": self.validation_result.to_dict()
            if self.validation_result
            else None,
            "metadata": self.metadata,
        }


class LiveModeGate:
    """
    Gate controller for live execution mode.

    Enforces blocked-by-default policy and validates config before
    allowing live execution.
    """

    def __init__(
        self,
        environment: ExecutionEnvironment,
        config: Optional[Dict[str, Any]] = None,
        audit_log_path: Optional[Path] = None,
    ):
        self.environment = environment
        self.config = config or {}
        self.audit_log_path = audit_log_path
        self._state = LiveModeGateState(
            environment=environment,
            status=LiveModeStatus.BLOCKED,  # Default: blocked
            reason="Live mode blocked by default (not yet approved)",
        )

    def get_state(self) -> LiveModeGateState:
        """Get current gate state."""
        return self._state

    def validate_config(self) -> ValidationResult:
        """
        Validate configuration for the current environment.

        Phase 0: Basic validation (extensible for future phases).
        """
        errors: List[str] = []
        warnings: List[str] = []
        metadata: Dict[str, Any] = {}

        # 1. Environment-specific checks
        if self.environment.is_live():
            # Live environments require explicit config keys
            required_keys = ["session_id", "strategy_id", "risk_limits"]
            for key in required_keys:
                if key not in self.config:
                    errors.append(f"Missing required config key for live env: {key}")

            # Risk limits must be set
            if "risk_limits" in self.config:
                risk_limits = self.config["risk_limits"]
                if not isinstance(risk_limits, dict):
                    errors.append("risk_limits must be a dict")
                elif not risk_limits:
                    errors.append("risk_limits cannot be empty for live env")

        # 2. General config sanity checks
        if "strategy_id" in self.config:
            if not isinstance(self.config["strategy_id"], str):
                errors.append("strategy_id must be a string")
            elif not self.config["strategy_id"]:
                errors.append("strategy_id cannot be empty")

        if "session_id" in self.config:
            if not isinstance(self.config["session_id"], str):
                errors.append("session_id must be a string")

        # 3. Warnings for dev/shadow envs (not blocking)
        if self.environment in {ExecutionEnvironment.DEV, ExecutionEnvironment.SHADOW}:
            if "risk_limits" not in self.config:
                warnings.append("risk_limits recommended even for non-live envs")

        metadata["environment"] = self.environment.value
        metadata["config_keys"] = list(self.config.keys())

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata=metadata,
        )

    def request_approval(
        self,
        requester: str,
        reason: str = "",
        config_hash: Optional[str] = None,
    ) -> bool:
        """
        Request approval for live mode.

        Args:
            requester: Identity of the requester (user, system, etc.)
            reason: Justification for live mode approval
            config_hash: Optional hash of the config being approved

        Returns:
            True if approved, False otherwise
        """
        # 1. Validate config first (fail-fast)
        validation_result = self.validate_config()
        self._state.validation_result = validation_result

        if not validation_result.valid:
            self._state.status = LiveModeStatus.FAILED_VALIDATION
            self._state.reason = f"Validation failed: {', '.join(validation_result.errors)}"
            self._log_audit_event(
                "approval_rejected",
                {
                    "requester": requester,
                    "reason": "Config validation failed",
                    "errors": validation_result.errors,
                },
            )
            return False

        # 2. Grant approval
        self._state.status = LiveModeStatus.APPROVED
        self._state.approved_at = datetime.now()
        self._state.approved_by = requester
        self._state.reason = reason or "Approved for live execution"
        self._state.config_hash = config_hash

        self._log_audit_event(
            "approval_granted",
            {
                "requester": requester,
                "reason": self._state.reason,
                "config_hash": config_hash,
                "warnings": validation_result.warnings,
            },
        )

        return True

    def revoke_approval(self, reason: str = "") -> None:
        """
        Revoke live mode approval (suspend).

        Args:
            reason: Reason for revocation
        """
        prev_status = self._state.status
        self._state.status = LiveModeStatus.SUSPENDED
        self._state.reason = reason or "Live mode suspended"

        self._log_audit_event(
            "approval_revoked",
            {
                "previous_status": prev_status.value,
                "reason": self._state.reason,
            },
        )

    def reset(self) -> None:
        """Reset gate to default blocked state."""
        self._state = LiveModeGateState(
            environment=self.environment,
            status=LiveModeStatus.BLOCKED,
            reason="Live mode blocked by default (reset)",
        )
        self._log_audit_event("gate_reset", {})

    def _log_audit_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log audit event (Phase 0: minimal implementation).

        Future: Integrate with WP0A AuditLog.
        """
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "environment": self.environment.value,
            "status": self._state.status.value,
            "details": details,
        }

        # Phase 0: Simple logging (extend in future phases)
        if self.audit_log_path:
            # Write to audit log file (append-only)
            import json

            with open(self.audit_log_path, "a") as f:
                f.write(json.dumps(audit_entry) + "\n")


def create_gate(
    environment: str | ExecutionEnvironment,
    config: Optional[Dict[str, Any]] = None,
    audit_log_path: Optional[Path] = None,
) -> LiveModeGate:
    """
    Factory function to create a LiveModeGate.

    Args:
        environment: Environment name or enum value
        config: Configuration dict
        audit_log_path: Path to audit log file

    Returns:
        LiveModeGate instance
    """
    if isinstance(environment, str):
        environment = ExecutionEnvironment(environment)

    return LiveModeGate(
        environment=environment,
        config=config,
        audit_log_path=audit_log_path,
    )


def is_live_allowed(gate: LiveModeGate) -> bool:
    """
    Check if live execution is currently allowed.

    Convenience function for simple checks.
    """
    return gate.get_state().is_allowed()


class LiveModeViolationError(Exception):
    """Exception raised when live mode gate rules are violated."""

    pass


def enforce_live_mode_gate(config: Dict[str, Any], env: str) -> None:
    """
    Enforce live mode gate rules (fail-fast).

    Raises LiveModeViolationError if any rule is violated.

    Rules:
    1. live.enabled defaults to False
    2. If live.enabled is True:
       - env must be "prod" (or "live")
       - operator_ack_token must be present and match expected value
       - risk_runtime must be importable (basic check)

    Args:
        config: Configuration dict with structure:
            {
                "live": {
                    "enabled": bool,
                    "operator_ack": str,  # Must be "I_UNDERSTAND_LIVE_TRADING"
                },
                "env": str,  # Optional, can also be passed as arg
                ...
            }
        env: Environment name (overrides config["env"] if present)

    Raises:
        LiveModeViolationError: If live mode rules are violated

    Example:
        >>> config = {
        ...     "live": {
        ...         "enabled": True,
        ...         "operator_ack": "I_UNDERSTAND_LIVE_TRADING",
        ...     },
        ...     "session_id": "test",
        ...     "strategy_id": "ma_crossover",
        ...     "risk_limits": {"max_position_size": 1000},
        ... }
        >>> enforce_live_mode_gate(config, env="prod")  # OK
        >>> enforce_live_mode_gate(config, env="dev")   # Raises!
    """
    # 1. Check if live mode is enabled
    live_config = config.get("live", {})
    live_enabled = live_config.get("enabled", False)  # Default: False

    if not live_enabled:
        # Live mode disabled => always safe
        return

    # 2. Live mode is enabled => enforce strict rules
    errors = []

    # Rule 2.1: env must be "prod" or "live"
    valid_live_envs = {"prod", "live"}
    if env not in valid_live_envs:
        errors.append(
            f"Live mode enabled but env is '{env}'. "
            f"Live mode requires env to be one of: {valid_live_envs}"
        )

    # Rule 2.2: operator_ack_token must be present and correct
    expected_ack = "I_UNDERSTAND_LIVE_TRADING"
    operator_ack = live_config.get("operator_ack", "")
    if operator_ack != expected_ack:
        errors.append(
            f"Live mode enabled but operator_ack is missing or incorrect. "
            f"Required: operator_ack = '{expected_ack}'"
        )

    # Rule 2.3: risk_runtime must be importable (basic sanity check)
    try:
        import src.execution.risk_runtime  # noqa: F401
    except ImportError as e:
        errors.append(f"Live mode enabled but risk_runtime module cannot be imported: {e}")

    # If any errors, raise with all violations listed
    if errors:
        raise LiveModeViolationError(
            "Live mode gate violation(s):\n" + "\n".join(f"  - {err}" for err in errors)
        )

    # All checks passed => live mode allowed
