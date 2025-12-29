"""
Config Validation - Phase 0 WP0C

Validates execution configuration before deployment.
Ensures required fields are present and valid.
"""

from typing import Dict, Any, List


class ConfigValidationError(Exception):
    """Exception raised when config validation fails."""
    pass


def validate_execution_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate execution configuration.

    Returns list of error messages (empty if valid).
    Can also be used with raise_on_error flag in wrapper function.

    Args:
        config: Configuration dict to validate

    Returns:
        List of error messages (empty if config is valid)

    Example:
        >>> config = {
        ...     "env": "prod",
        ...     "session_id": "test_session",
        ...     "strategy_id": "ma_crossover",
        ...     "risk_limits": {"max_position_size": 1000},
        ... }
        >>> errors = validate_execution_config(config)
        >>> assert len(errors) == 0
    """
    errors: List[str] = []

    # 1. Environment validation
    valid_envs = {"dev", "shadow", "testnet", "prod"}
    env = config.get("env", "")
    if not env:
        errors.append("Missing required field: 'env'")
    elif env not in valid_envs:
        errors.append(
            f"Invalid env '{env}'. Must be one of: {valid_envs}"
        )

    # 2. Session/Strategy ID validation (basic presence check)
    if not config.get("session_id"):
        errors.append("Missing required field: 'session_id'")

    if not config.get("strategy_id"):
        errors.append("Missing required field: 'strategy_id'")

    # 3. Risk limits validation
    risk_limits = config.get("risk_limits")
    if risk_limits is None:
        errors.append("Missing required field: 'risk_limits'")
    elif not isinstance(risk_limits, dict):
        errors.append("Field 'risk_limits' must be a dict")
    elif not risk_limits:
        # Empty dict is allowed for non-live envs, but we warn
        # (actual enforcement happens in LiveModeGate)
        pass

    # 4. Soft check: R&D strategies in live (TODO: make configurable)
    # This is a placeholder for future enhancement
    strategy_id = config.get("strategy_id", "")
    if env in {"prod", "live"}:
        r_and_d_patterns = ["test_", "debug_", "experimental_"]
        if any(pattern in strategy_id.lower() for pattern in r_and_d_patterns):
            # Soft warning (not blocking, but logged)
            # In production: this could be a hard error or require extra approval
            errors.append(
                f"Warning: Strategy '{strategy_id}' appears to be R&D "
                f"(contains test/debug/experimental pattern) but env is '{env}'. "
                f"This may require additional review."
            )

    return errors


def validate_execution_config_strict(config: Dict[str, Any]) -> None:
    """
    Validate execution configuration (strict mode - raises on error).

    Raises:
        ConfigValidationError: If validation fails (with aggregated errors)

    Example:
        >>> config = {"env": "invalid"}
        >>> validate_execution_config_strict(config)  # Raises!
        Traceback (most recent call last):
        ...
        ConfigValidationError: Config validation failed with 4 error(s):
          - Invalid env 'invalid'. Must be one of: ...
          - Missing required field: 'session_id'
          - Missing required field: 'strategy_id'
          - Missing required field: 'risk_limits'
    """
    errors = validate_execution_config(config)
    if errors:
        raise ConfigValidationError(
            f"Config validation failed with {len(errors)} error(s):\n"
            + "\n".join(f"  - {err}" for err in errors)
        )
