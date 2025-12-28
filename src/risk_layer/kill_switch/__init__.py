"""Peak_Trade Emergency Kill Switch.

Layer 4 of Defense-in-Depth Risk Management System.
Last line of defense against uncontrolled trading losses.

Public API:
    - KillSwitch: Main kill switch class
    - KillSwitchState: State enum
    - KillSwitchEvent: Event dataclass
    - TradingBlockedError: Exception when trading is blocked

Usage:
    >>> from src.risk_layer.kill_switch import KillSwitch
    >>>
    >>> config = load_config()
    >>> ks = KillSwitch(config)
    >>>
    >>> # Trigger emergency stop
    >>> ks.trigger("Drawdown limit exceeded")
    >>>
    >>> # Check if blocked
    >>> if ks.check_and_block():
    ...     raise TradingBlockedError()
    >>>
    >>> # Recovery
    >>> ks.request_recovery("operator", "APPROVAL_CODE")
    >>> time.sleep(300)  # Cooldown
    >>> ks.complete_recovery()
"""

__version__ = "1.0.0"
__author__ = "Peak_Trade Risk Team"

from .config import load_config, get_approval_code
from .core import KillSwitch, TradingBlockedError
from .state import KillSwitchEvent, KillSwitchState, StateTransitionError
from .execution_gate import ExecutionGate
from .adapter import KillSwitchAdapter, KillSwitchStatus


# Legacy compatibility stubs for old risk_gate integration
def to_violations(kill_switch_status):
    """Convert kill switch status to violations (legacy compatibility stub)."""
    from src.risk_layer.models import Violation

    if hasattr(kill_switch_status, "armed") and kill_switch_status.armed:
        return [
            Violation(
                code="KILL_SWITCH_ARMED",
                message=getattr(kill_switch_status, "reason", "Kill switch is armed"),
                severity="CRITICAL",
                details={},
            )
        ]
    return []


# Legacy aliases for backwards compatibility with old code
def KillSwitchLayer(config):
    """Legacy factory: returns KillSwitchAdapter for old Evaluator API.

    Args:
        config: Config dict or PeakConfig instance

    Returns:
        KillSwitchAdapter wrapping a KillSwitch
    """
    # Extract kill_switch config from PeakConfig if needed
    if hasattr(config, "get"):
        # PeakConfig instance
        kill_switch_config = config.get("risk.kill_switch", {})
    elif isinstance(config, dict) and "risk" in config:
        # Dict with nested structure
        kill_switch_config = config.get("risk", {}).get("kill_switch", {})
    else:
        # Already a kill_switch config dict
        kill_switch_config = config if isinstance(config, dict) else {}

    return KillSwitchAdapter(KillSwitch(kill_switch_config))


__all__ = [
    # Core
    "KillSwitch",
    "TradingBlockedError",
    "ExecutionGate",
    # State
    "KillSwitchState",
    "KillSwitchEvent",
    "StateTransitionError",
    # Config
    "load_config",
    "get_approval_code",
    # Legacy compatibility
    "to_violations",
    "KillSwitchLayer",
    "KillSwitchStatus",
    "KillSwitchAdapter",
]
