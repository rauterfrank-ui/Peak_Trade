"""Research-only MACD histogram-countertrend entry eligibility gate (no Master-V2 mutation).

Reuses the generic mapped-signal gate helper from the prior entry-effective
evaluation package (read-only); the side-aware eligibility decision itself
comes from the frozen MACD filter in this package (``is_entry_eligible``).
"""

from __future__ import annotations

from src.research.entry_effective_mr_eligibility_development_evaluation_v1.entry_eligibility_gate_v1 import (
    apply_eligibility_gate_to_signals,
    apply_eligibility_to_mapped_position_signal,
)

__all__ = [
    "apply_eligibility_gate_to_signals",
    "apply_eligibility_to_mapped_position_signal",
]
