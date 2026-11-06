"""DEVELOPMENT evaluation surfaces for Bollinger/MR midband reentry-cooldown v8.

IMPLEMENTATION_ONLY wiring bound to Operator Clarification Authority.
No automatic evaluation. No holdout. No runtime/orders.
Control = exact V6 composite midband/max-hold semantics. Treatment = same exits +
same-side reentry cooldown (24 PT1H bars) after forced midband exit.
"""

PACKAGE_MARKER = "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_V8=true"

__all__ = ["PACKAGE_MARKER"]
