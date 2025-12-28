"""Configuration handling for Kill Switch.

Loads and validates configuration from TOML files.
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib as tomli  # Python 3.11+
except ImportError:
    try:
        import tomli  # Python 3.10 fallback
    except ImportError:
        raise ImportError(
            "No TOML library found. Install tomli: pip install tomli"
        )


logger = logging.getLogger(__name__)


DEFAULT_CONFIG = {
    "kill_switch": {
        "enabled": True,
        "mode": "active",
        "recovery_cooldown_seconds": 300,
        "require_approval_code": True,
        "approval_code_env": "KILL_SWITCH_APPROVAL_CODE",
        "persist_state": True,
        "state_file": "data/kill_switch/state.json",
        "audit_dir": "data/kill_switch/audit",
        "audit_retention_days": 90,
        "log_level": "INFO",
    },
    "kill_switch.recovery": {
        "cooldown_seconds": 300,
        "require_approval_code": True,
        "require_health_check": True,
        "require_trigger_clear": True,
        "gradual_restart_enabled": True,
        "initial_position_limit_factor": 0.5,
        "escalation_intervals": [3600, 7200],
        "escalation_factors": [0.75, 1.0],
        "min_memory_available_mb": 512,
        "max_cpu_percent": 80,
        "require_exchange_connection": True,
        "require_price_feed": True,
    },
}


def load_config(config_path: Optional[str] = None) -> dict:
    """Load Kill Switch configuration from TOML file.

    Args:
        config_path: Path to config file. If None, uses default location.

    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Try multiple default locations
        candidates = [
            "config/risk/kill_switch.toml",
            "../config/risk/kill_switch.toml",
            "../../config/risk/kill_switch.toml",
        ]

        for candidate in candidates:
            path = Path(candidate)
            if path.exists():
                config_path = str(path)
                break

    if config_path and Path(config_path).exists():
        try:
            with open(config_path, "rb") as f:
                loaded = tomli.load(f)

            # Merge with defaults
            config = DEFAULT_CONFIG.copy()
            config.update(loaded)

            logger.info(f"Loaded config from {config_path}")
            return config

        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")

    logger.info("Using default configuration")
    return DEFAULT_CONFIG.copy()


def get_approval_code(config: dict) -> Optional[str]:
    """Get approval code from environment variable.

    Args:
        config: Configuration dictionary

    Returns:
        Approval code or None if not set
    """
    env_var = config.get("kill_switch", {}).get(
        "approval_code_env",
        "KILL_SWITCH_APPROVAL_CODE"
    )

    code = os.getenv(env_var)

    if not code and config.get("kill_switch", {}).get("require_approval_code"):
        logger.warning(
            f"Approval code required but {env_var} not set in environment"
        )

    return code


def get_kill_switch_config(config: dict) -> dict:
    """Extract kill_switch section from config.

    Args:
        config: Full configuration dictionary

    Returns:
        Kill switch configuration
    """
    return config.get("kill_switch", DEFAULT_CONFIG["kill_switch"])


def get_recovery_config(config: dict) -> dict:
    """Extract recovery section from config.

    Args:
        config: Full configuration dictionary

    Returns:
        Recovery configuration
    """
    return config.get("kill_switch.recovery", DEFAULT_CONFIG["kill_switch.recovery"])
