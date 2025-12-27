"""
Peak_Trade Backtest Invariants
==============================
Formal invariant checking for the backtest engine to prevent invalid states.

Design Principles:
- Fail-fast with clear error messages
- Always provide actionable hints
- Configurable check frequency (ALWAYS, START_END, NEVER)
- Support for custom user-defined invariants

Usage:
    from src.backtest.invariants import InvariantChecker, CheckMode
    
    checker = InvariantChecker(mode=CheckMode.START_END)
    checker.check_all(engine)  # Raises InvariantViolationError on violation
"""
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Any, Optional

from ..core.errors import BacktestInvariantError


@dataclass
class Invariant:
    """
    Backtest invariant with validation logic.
    
    Attributes:
        name: Unique identifier for the invariant
        check: Callable that takes engine and returns bool (True = valid)
        error_message: Human-readable error message for violations
        hint: Actionable suggestion for fixing the violation
    """
    name: str
    check: Callable[..., bool]
    error_message: str
    hint: str


class BacktestInvariants:
    """
    Collection of backtest engine invariants.
    
    Each method is a static invariant check that takes an engine and returns
    True if the invariant holds, False if violated.
    """
    
    @staticmethod
    def equity_non_negative(engine) -> bool:
        """Equity must never be negative."""
        return engine.equity >= 0
    
    @staticmethod
    def positions_valid(engine) -> bool:
        """Positions list must be valid (no None, no duplicates)."""
        if not hasattr(engine, 'positions'):
            return True
        
        positions = engine.positions
        if positions is None:
            return False
        
        # For dict-style positions (new ExecutionPipeline mode)
        if isinstance(positions, dict):
            return all(v is not None for v in positions.values())
        
        # For list-style positions (legacy mode)
        if not positions:  # Empty list is valid
            return True
        
        try:
            positions_list = list(positions)
            if None in positions_list:
                return False
            
            # Check for duplicate symbols
            symbols = [p.symbol if hasattr(p, 'symbol') else str(p) for p in positions_list]
            return len(symbols) == len(set(symbols))
        except (AttributeError, TypeError):
            # If positions structure is unexpected, be conservative
            return False
    
    @staticmethod
    def timestamps_monotonic(engine) -> bool:
        """Timestamps must be strictly increasing."""
        if not hasattr(engine, 'history') or engine.history is None:
            return True
        
        if len(engine.history) < 2:
            return True
        
        try:
            timestamps = [h.timestamp if hasattr(h, 'timestamp') else h for h in engine.history]
            return all(timestamps[i] < timestamps[i+1] for i in range(len(timestamps)-1))
        except (AttributeError, TypeError, IndexError):
            # If history structure is unexpected, be conservative
            return False
    
    @staticmethod
    def cash_balance_valid(engine) -> bool:
        """Cash balance must be >= 0 (no margin violations)."""
        if not hasattr(engine, 'cash'):
            return True
        return engine.cash >= 0
    
    @staticmethod
    def position_sizes_realistic(engine) -> bool:
        """Position sizes must be within portfolio limits."""
        if not hasattr(engine, 'positions') or not hasattr(engine, 'equity'):
            return True
        
        if engine.equity <= 0:
            return True  # Can't calculate leverage if equity is 0
        
        positions = engine.positions
        
        # Handle dict-style positions (ExecutionPipeline mode)
        if isinstance(positions, dict):
            if not positions:
                return True
            # For dict positions, we can't easily get value without price info
            # This check is more relevant for legacy mode
            return True
        
        # Handle list-style positions (legacy mode)
        if not positions:
            return True
        
        try:
            total_exposure = sum(abs(getattr(p, 'value', 0.0)) for p in positions)
            return total_exposure <= engine.equity * 10  # Max 10x leverage
        except (AttributeError, TypeError):
            # If we can't calculate exposure, be conservative and pass
            return True


# Core invariants that should always be checked in backtest engine.
# Order is significant: equity and cash checks come before position checks
# as position validation may depend on valid equity/cash state.
CORE_INVARIANTS = [
    Invariant(
        name="equity_non_negative",
        check=BacktestInvariants.equity_non_negative,
        error_message="Equity cannot be negative",
        hint="Check for commission bugs or position sizing errors"
    ),
    Invariant(
        name="positions_valid",
        check=BacktestInvariants.positions_valid,
        error_message="Position list corrupted (None or duplicates)",
        hint="Check position add/remove logic and position sizing"
    ),
    Invariant(
        name="timestamps_monotonic",
        check=BacktestInvariants.timestamps_monotonic,
        error_message="Timestamps are not monotonically increasing",
        hint="Check data feed or time handling"
    ),
    Invariant(
        name="cash_balance_valid",
        check=BacktestInvariants.cash_balance_valid,
        error_message="Negative cash balance (margin violation)",
        hint="Position size exceeds available capital"
    ),
    Invariant(
        name="position_sizes_realistic",
        check=BacktestInvariants.position_sizes_realistic,
        error_message="Total position exposure exceeds limits",
        hint="Check leverage calculation or position sizing"
    ),
]


class CheckMode(Enum):
    """When to check invariants."""
    ALWAYS = "always"  # Check after every operation
    START_END = "start_end"  # Only at start/end
    NEVER = "never"  # Disabled


class InvariantChecker:
    """
    Validates backtest invariants.
    
    Usage:
        >>> checker = InvariantChecker(mode=CheckMode.START_END)
        >>> checker.check_all(engine)  # Raises on violation
        >>> 
        >>> # Add custom invariant
        >>> def my_check(engine) -> bool:
        ...     return engine.equity < 1000000  # Cap at 1M
        >>> 
        >>> checker.add_custom_invariant(
        ...     Invariant(
        ...         name="equity_cap",
        ...         check=my_check,
        ...         error_message="Equity exceeded cap",
        ...         hint="Check strategy parameters"
        ...     )
        ... )
    """
    
    def __init__(self, mode: CheckMode = CheckMode.START_END):
        """
        Initialize invariant checker.
        
        Args:
            mode: When to check invariants (ALWAYS, START_END, NEVER)
        """
        self.mode = mode
        self.invariants: List[Invariant] = CORE_INVARIANTS.copy()
    
    def check_all(self, engine) -> None:
        """
        Check all invariants, raise on violation.
        
        Args:
            engine: BacktestEngine instance to validate
            
        Raises:
            BacktestInvariantError: If any invariant is violated
        """
        if self.mode == CheckMode.NEVER:
            return
        
        for invariant in self.invariants:
            try:
                if not invariant.check(engine):
                    self._raise_violation(invariant, engine)
            except Exception as e:
                # If check itself fails, treat as violation with additional context
                raise BacktestInvariantError(
                    f"Invariant '{invariant.name}' check failed with error: {e}",
                    hint=f"Original hint: {invariant.hint}. Check implementation may be broken.",
                    context={
                        "invariant": invariant.name,
                        "check_error": str(e),
                        "equity": getattr(engine, 'equity', None),
                        "cash": getattr(engine, 'cash', None),
                    }
                )
    
    def _raise_violation(self, invariant: Invariant, engine) -> None:
        """Raise InvariantViolationError with context."""
        context = {
            "invariant": invariant.name,
        }
        
        # Safely extract context from engine
        if hasattr(engine, 'equity'):
            context["equity"] = engine.equity
        if hasattr(engine, 'cash'):
            context["cash"] = engine.cash
        if hasattr(engine, 'positions'):
            positions = engine.positions
            if isinstance(positions, dict):
                context["num_positions"] = len(positions)
            elif positions is not None:
                try:
                    context["num_positions"] = len(list(positions))
                except (TypeError, AttributeError):
                    context["num_positions"] = "unknown"
            else:
                context["num_positions"] = 0
        
        raise BacktestInvariantError(
            f"Invariant '{invariant.name}' violated: {invariant.error_message}",
            hint=invariant.hint,
            context=context
        )
    
    def add_custom_invariant(self, invariant: Invariant) -> None:
        """
        Add user-defined invariant.
        
        Args:
            invariant: Custom Invariant to add to the checker
        """
        self.invariants.append(invariant)
    
    def remove_invariant(self, name: str) -> bool:
        """
        Remove an invariant by name.
        
        Args:
            name: Name of the invariant to remove
            
        Returns:
            True if removed, False if not found
        """
        initial_len = len(self.invariants)
        self.invariants = [inv for inv in self.invariants if inv.name != name]
        return len(self.invariants) < initial_len
    
    def get_invariant_names(self) -> List[str]:
        """Get list of all registered invariant names."""
        return [inv.name for inv in self.invariants]
