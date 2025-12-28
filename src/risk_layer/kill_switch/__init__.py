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

__all__ = [
    # Core
    "KillSwitch",
    "TradingBlockedError",
    # State
    "KillSwitchState",
    "KillSwitchEvent",
    "StateTransitionError",
    # Config
    "load_config",
    "get_approval_code",
]
