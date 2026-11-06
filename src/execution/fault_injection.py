"""
Fault Injection for Execution Hardening (Phase B).

Deterministic, seed-based fault injection for testing broker/API edge cases.
Controlled via PT_FAULT_INJECT=1. Safe by default when disabled.

Scenarios: latency, timeout, rate_limit, http_500, malformed_response.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from enum import Enum
from typing import Literal


class FaultScenario(str, Enum):
    """Injectable fault scenarios."""

    LATENCY = "latency"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    HTTP_500 = "http_500"
    MALFORMED_RESPONSE = "malformed_response"


@dataclass(frozen=True)
class FaultConfig:
    """Configuration for fault injection."""

    enabled: bool
    seed: int
    latency_ms: int
    timeout_after_ms: int
    rate_limit_after_n: int
    http_500_probability: float
    malformed_probability: float


def _parse_env() -> FaultConfig:
    """Parse env and return config. Safe defaults when disabled."""
    enabled = os.getenv("PT_FAULT_INJECT", "0").strip() == "1"
    seed_str = os.getenv("PT_FAULT_INJECT_SEED", "42")
    try:
        seed = int(seed_str)
    except ValueError:
        seed = 42
    return FaultConfig(
        enabled=enabled,
        seed=seed,
        latency_ms=int(os.getenv("PT_FAULT_INJECT_LATENCY_MS", "100")),
        timeout_after_ms=int(os.getenv("PT_FAULT_INJECT_TIMEOUT_MS", "5000")),
        rate_limit_after_n=int(os.getenv("PT_FAULT_INJECT_RATE_LIMIT_AFTER", "3")),
        http_500_probability=float(os.getenv("PT_FAULT_INJECT_500_PROB", "0.1")),
        malformed_probability=float(os.getenv("PT_FAULT_INJECT_MALFORMED_PROB", "0.05")),
    )


def _deterministic_hash(seed: int, key: str) -> int:
    """Deterministic hash for reproducible behavior."""
    h = hashlib.sha256(f"{seed}:{key}".encode()).hexdigest()
    return int(h[:16], 16)


def should_inject(config: FaultConfig, scenario: FaultScenario, call_id: str) -> bool:
    """
    Deterministic decision: should we inject this scenario for this call?

    Args:
        config: Fault config
        scenario: Scenario to check
        call_id: Unique call identifier (e.g., endpoint + sequence)

    Returns:
        True if fault should be injected
    """
    if not config.enabled:
        return False
    h = _deterministic_hash(config.seed, f"{scenario.value}:{call_id}")
    prob = 0.0
    if scenario == FaultScenario.HTTP_500:
        prob = config.http_500_probability
    elif scenario == FaultScenario.MALFORMED_RESPONSE:
        prob = config.malformed_probability
    elif scenario == FaultScenario.RATE_LIMIT:
        # Deterministic: inject on every Nth call
        return (h % config.rate_limit_after_n) == 0
    return (h % 10000) / 10000.0 < prob


def get_latency_ms(config: FaultConfig, call_id: str) -> int:
    """Return deterministic latency in ms for this call. 0 when disabled."""
    if not config.enabled:
        return 0
    h = _deterministic_hash(config.seed, f"latency:{call_id}")
    return (h % config.latency_ms) + 1


def get_config() -> FaultConfig:
    """Return current fault injection config (from env)."""
    return _parse_env()


def is_enabled() -> bool:
    """Return True iff PT_FAULT_INJECT=1."""
    return get_config().enabled
