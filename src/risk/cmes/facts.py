"""
CMES Fact Schema + canonicalization (Runbook Risk/Strategy CMES A→Z, step A).

7 core facts: risk_score, risk_decision, risk_reason_codes, no_trade_triggered,
no_trade_trigger_ids, strategy_state (+ optional strategy_reason_codes), data_quality_flags.
Deterministic: list fields sorted; enums normalized.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

# Required fact keys (7 core)
CMES_FACT_KEYS = (
    "risk_score",
    "risk_decision",
    "risk_reason_codes",
    "no_trade_triggered",
    "no_trade_trigger_ids",
    "strategy_state",
    "data_quality_flags",
)

RISK_DECISION_VALUES = frozenset({"ALLOW", "REDUCE", "BLOCK"})
STRATEGY_STATE_VALUES = frozenset({"ENABLED", "DISABLED", "PAUSED", "DEGRADED"})


class CMESFactsValidationError(ValueError):
    """Raised when facts are missing required keys or have invalid types."""

    pass


def _sorted_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return sorted(str(x).strip() for x in value if x is not None)
    return []


def _normalize_enum(value: Any, allowed: frozenset[str]) -> str:
    if value is None:
        raise CMESFactsValidationError(f"enum required, got None; allowed: {allowed}")
    s = str(value).strip().upper()
    if s not in allowed:
        raise CMESFactsValidationError(f"invalid enum value {s!r}; allowed: {allowed}")
    return s


def canonicalize_facts(facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sort list fields, normalize enums, ensure required keys present.
    Returns a new dict; does not mutate input.
    """
    out: Dict[str, Any] = {}
    for k in CMES_FACT_KEYS:
        v = facts.get(k)
        if k == "risk_score":
            if v is None:
                out[k] = 0.0
            else:
                try:
                    f = float(v)
                except (TypeError, ValueError):
                    raise CMESFactsValidationError(
                        f"risk_score must be float, got {type(v).__name__}"
                    )
                if not (0 <= f <= 100):
                    raise CMESFactsValidationError(f"risk_score must be 0..100, got {f}")
                out[k] = round(f, 6)
        elif k == "risk_decision":
            out[k] = _normalize_enum(v, RISK_DECISION_VALUES)
        elif k == "risk_reason_codes":
            out[k] = _sorted_str_list(v)
        elif k == "no_trade_triggered":
            out[k] = bool(v) if v is not None else False
        elif k == "no_trade_trigger_ids":
            out[k] = _sorted_str_list(v)
        elif k == "strategy_state":
            out[k] = _normalize_enum(v, STRATEGY_STATE_VALUES)
        elif k == "data_quality_flags":
            out[k] = _sorted_str_list(v)
    # Optional: strategy_reason_codes (not in CMES_FACT_KEYS but allowed)
    if "strategy_reason_codes" in facts:
        out["strategy_reason_codes"] = _sorted_str_list(facts["strategy_reason_codes"])
    return out


def canonical_facts_sha256(facts: Dict[str, Any]) -> str:
    """Deterministic SHA256 of canonical facts (for audit/run metadata)."""
    canonical = canonicalize_facts(facts) if facts else default_cmes_facts()
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def default_cmes_facts() -> Dict[str, Any]:
    """Return canonical default CMES facts (ALLOW, score 0, no triggers, ENABLED)."""
    return canonicalize_facts(
        {
            "risk_score": 0.0,
            "risk_decision": "ALLOW",
            "risk_reason_codes": [],
            "no_trade_triggered": False,
            "no_trade_trigger_ids": [],
            "strategy_state": "ENABLED",
            "data_quality_flags": [],
        }
    )


def validate_facts(facts: Dict[str, Any]) -> None:
    """
    Raise CMESFactsValidationError if required keys missing or types invalid.
    Use after canonicalize_facts or on raw dict (canonicalize_facts does validation).
    """
    for k in CMES_FACT_KEYS:
        if k not in facts:
            raise CMESFactsValidationError(f"missing required fact key: {k}")
    # Type checks
    v = facts.get("risk_score")
    if v is not None and not isinstance(v, (int, float)):
        raise CMESFactsValidationError("risk_score must be numeric")
    if str(facts.get("risk_decision", "")).strip().upper() not in RISK_DECISION_VALUES:
        raise CMESFactsValidationError(f"risk_decision must be in {RISK_DECISION_VALUES}")
    if not isinstance(facts.get("risk_reason_codes"), list):
        raise CMESFactsValidationError("risk_reason_codes must be list")
    if not isinstance(facts.get("no_trade_triggered"), bool):
        raise CMESFactsValidationError("no_trade_triggered must be bool")
    if not isinstance(facts.get("no_trade_trigger_ids"), list):
        raise CMESFactsValidationError("no_trade_trigger_ids must be list")
    if str(facts.get("strategy_state", "")).strip().upper() not in STRATEGY_STATE_VALUES:
        raise CMESFactsValidationError(f"strategy_state must be in {STRATEGY_STATE_VALUES}")
    if not isinstance(facts.get("data_quality_flags"), list):
        raise CMESFactsValidationError("data_quality_flags must be list")
