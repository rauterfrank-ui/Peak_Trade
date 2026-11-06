"""
CMES: Controlled Measurement & Evidence Stream for Risk/Strategy.

Pointer-only, deterministic facts; no payload/raw/transcript/secrets.
"""

from .facts import (
    CMES_FACT_KEYS,
    canonical_facts_sha256,
    canonicalize_facts,
    default_cmes_facts,
    validate_facts,
)
from .l5_adapter import L5Decision, l5_decision_from_facts
from .reason_codes import (
    DATA_QUALITY_FLAGS,
    NO_TRADE_TRIGGER_IDS,
    RISK_REASON_CODES,
    STRATEGY_REASON_CODES,
)

__all__ = [
    "CMES_FACT_KEYS",
    "L5Decision",
    "canonical_facts_sha256",
    "canonicalize_facts",
    "default_cmes_facts",
    "l5_decision_from_facts",
    "validate_facts",
    "DATA_QUALITY_FLAGS",
    "NO_TRADE_TRIGGER_IDS",
    "RISK_REASON_CODES",
    "STRATEGY_REASON_CODES",
]
