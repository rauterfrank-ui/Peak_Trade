"""
Peak_Trade Resilience Integration Helpers
========================================
Helper functions and decorators for easy resilience integration.

Provides pre-configured circuit breakers and rate limiters for common use cases.

Usage:
    from src.core.resilience_helpers import (
        create_module_circuit_breaker,
        create_module_rate_limiter,
        with_resilience
    )

    # Create circuit breaker for a module
    backtest_breaker = create_module_circuit_breaker("backtest")

    # Protect a function
    @backtest_breaker.call
    def load_data():
        pass

    # Or use convenience wrapper
    @with_resilience("backtest", "data_load")
    def load_data():
        pass
"""

import logging
import functools
from typing import Callable, Optional, Dict, Any
import toml
from pathlib import Path

from .resilience import CircuitBreaker, health_check
from .rate_limiter import RateLimiter
from .metrics import metrics

logger = logging.getLogger(__name__)


# Global registry of circuit breakers and rate limiters
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_rate_limiters: Dict[str, RateLimiter] = {}
_config: Optional[Dict[str, Any]] = None


def load_resilience_config() -> Dict[str, Any]:
    """
    Load resilience configuration from config.toml.

    Returns:
        Dict with resilience configuration
    """
    global _config

    if _config is not None:
        return _config

    # Try to find config.toml starting from this file location
    # Search up the directory tree for config.toml
    current_path = Path(__file__).resolve()

    # Search up to 5 levels
    for _ in range(5):
        current_path = current_path.parent
        config_path = current_path / "config.toml"
        if config_path.exists():
            break
    else:
        # Not found, use defaults
        logger.warning(f"Config file not found, using defaults")
        _config = {
            "resilience": {
                "circuit_breaker_threshold": 5,
                "circuit_breaker_timeout": 60,
                "circuit_breaker_enabled": True,
                "rate_limit_requests": 100,
                "rate_limit_window": 60,
                "rate_limit_enabled": True,
            }
        }
        return _config

    try:
        with open(config_path, "r") as f:
            config = toml.load(f)
            _config = config
            return config
    except Exception as e:
        logger.error(f"Failed to load config.toml: {e}")
        _config = {"resilience": {}}
        return _config


def get_module_config(module_name: str) -> Dict[str, Any]:
    """
    Get resilience configuration for a specific module.

    Args:
        module_name: Name of module (e.g., 'backtest', 'portfolio', 'risk', 'live')

    Returns:
        Dict with module-specific configuration merged with global defaults
    """
    config = load_resilience_config()

    # Get global defaults
    global_config = config.get("resilience", {})

    # Get module-specific config
    module_config = config.get("resilience", {}).get(module_name, {})

    # Merge (module-specific overrides global)
    merged = {
        "circuit_breaker_threshold": global_config.get("circuit_breaker_threshold", 5),
        "circuit_breaker_timeout": global_config.get("circuit_breaker_timeout", 60),
        "circuit_breaker_enabled": global_config.get("circuit_breaker_enabled", True),
        "rate_limit_requests": global_config.get("rate_limit_requests", 100),
        "rate_limit_window": global_config.get("rate_limit_window", 60),
        "rate_limit_enabled": global_config.get("rate_limit_enabled", True),
    }
    merged.update(module_config)

    return merged


def create_module_circuit_breaker(module_name: str, operation: str = "default") -> CircuitBreaker:
    """
    Create or get a circuit breaker for a module.

    Args:
        module_name: Name of module (e.g., 'backtest', 'portfolio')
        operation: Optional operation name for more specific breaker

    Returns:
        CircuitBreaker instance
    """
    breaker_name = f"{module_name}_{operation}"

    # Return existing if available
    if breaker_name in _circuit_breakers:
        return _circuit_breakers[breaker_name]

    # Get config
    module_config = get_module_config(module_name)

    if not module_config.get("circuit_breaker_enabled", True):
        logger.info(f"Circuit breaker disabled for {module_name}")
        # Return a no-op breaker that always allows calls
        breaker = CircuitBreaker(failure_threshold=999999, recovery_timeout=1, name=breaker_name)
    else:
        breaker = CircuitBreaker(
            failure_threshold=module_config.get("circuit_breaker_threshold", 5),
            recovery_timeout=module_config.get("circuit_breaker_timeout", 60),
            name=breaker_name,
        )

    # Register in global registry
    _circuit_breakers[breaker_name] = breaker

    # Register health check
    def check_breaker_health():
        from .resilience import CircuitState

        is_closed = breaker.state == CircuitState.CLOSED
        return is_closed, f"Circuit breaker '{breaker_name}' state: {breaker.state.value}"

    health_check.register(f"circuit_breaker_{breaker_name}", check_breaker_health)

    logger.info(f"Created circuit breaker for {breaker_name}")

    return breaker


def create_module_rate_limiter(module_name: str, operation: str = "default") -> RateLimiter:
    """
    Create or get a rate limiter for a module.

    Args:
        module_name: Name of module (e.g., 'backtest', 'portfolio')
        operation: Optional operation name for more specific limiter

    Returns:
        RateLimiter instance
    """
    limiter_name = f"{module_name}_{operation}"

    # Return existing if available
    if limiter_name in _rate_limiters:
        return _rate_limiters[limiter_name]

    # Get config
    module_config = get_module_config(module_name)

    if not module_config.get("rate_limit_enabled", True):
        logger.info(f"Rate limiter disabled for {module_name}")
        # Return a limiter with very high limits
        limiter = RateLimiter(max_requests=999999, window_seconds=1, name=limiter_name)
    else:
        limiter = RateLimiter(
            max_requests=module_config.get("rate_limit_requests", 100),
            window_seconds=module_config.get("rate_limit_window", 60),
            name=limiter_name,
        )

    # Register in global registry
    _rate_limiters[limiter_name] = limiter

    logger.info(f"Created rate limiter for {limiter_name}")

    return limiter


def with_resilience(
    module_name: str,
    operation: str = "default",
    use_circuit_breaker: bool = True,
    use_rate_limiter: bool = False,
    record_metrics: bool = True,
) -> Callable:
    """
    Decorator to add resilience to a function.

    Args:
        module_name: Name of module (e.g., 'backtest', 'portfolio')
        operation: Operation name for logging and metrics
        use_circuit_breaker: Enable circuit breaker protection
        use_rate_limiter: Enable rate limiting
        record_metrics: Record metrics for this operation

    Returns:
        Decorator function

    Example:
        @with_resilience("backtest", "data_load")
        def load_data():
            # Your code here
            pass
    """

    def decorator(func: Callable) -> Callable:
        # Get or create circuit breaker and rate limiter
        breaker = None
        limiter = None

        if use_circuit_breaker:
            breaker = create_module_circuit_breaker(module_name, operation)

        if use_rate_limiter:
            limiter = create_module_rate_limiter(module_name, operation)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            operation_name = f"{module_name}.{operation}"

            # Rate limiting check
            if limiter:
                if not limiter.acquire():
                    if record_metrics:
                        metrics.record_rate_limit_rejection(module_name, operation)
                    raise Exception(f"Rate limit exceeded for {operation_name}")

                if record_metrics:
                    metrics.record_rate_limit_hit(module_name, operation)

            # Execute with circuit breaker and metrics
            try:
                if record_metrics:
                    with metrics.track_latency(operation_name):
                        if breaker:
                            result = breaker.call(func)(*args, **kwargs)
                        else:
                            result = func(*args, **kwargs)
                else:
                    if breaker:
                        result = breaker.call(func)(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                if record_metrics:
                    metrics.record_operation_success(operation_name)

                return result

            except Exception as e:
                if record_metrics:
                    metrics.record_operation_failure(operation_name, type(e).__name__)
                    if breaker:
                        metrics.record_circuit_breaker_failure(breaker.name)
                raise

        return wrapper

    return decorator


def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Get all registered circuit breakers."""
    return dict(_circuit_breakers)


def get_all_rate_limiters() -> Dict[str, RateLimiter]:
    """Get all registered rate limiters."""
    return dict(_rate_limiters)


def reset_all_resilience() -> None:
    """Reset all circuit breakers and rate limiters (for testing)."""
    for breaker in _circuit_breakers.values():
        breaker.reset()

    for limiter in _rate_limiters.values():
        limiter.reset()

    logger.info("Reset all circuit breakers and rate limiters")


__all__ = [
    "create_module_circuit_breaker",
    "create_module_rate_limiter",
    "with_resilience",
    "get_module_config",
    "get_all_circuit_breakers",
    "get_all_rate_limiters",
    "reset_all_resilience",
]
