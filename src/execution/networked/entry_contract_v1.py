"""P124 — Execution Networked Entry Contract v1 (guards only, no transport)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

DENY_ENV_VARS = (
    "LIVE",
    "RECORD",
    "TRADING_ENABLE",
    "EXECUTION_ENABLE",
    "PT_ARMED",
    "PT_CONFIRM",
    "PT_CONFIRM_TOKEN",
)

SECRET_ENV_HINTS = (
    "API_KEY",
    "API_SECRET",
    "KRAKEN_API_KEY",
    "KRAKEN_API_SECRET",
    "COINBASE_API_KEY",
    "OKX_API_KEY",
    "BYBIT_API_KEY",
)


class ExecutionEntryGuardError(RuntimeError):
    """Raised when entry contract guards fail."""

    pass


@dataclass(frozen=True)
class ExecutionNetworkedContextV1:
    """Context for networked execution (shadow/paper only, dry_run enforced)."""

    mode: str  # shadow|paper only
    dry_run: bool  # must be True for v1
    adapter: str  # mock|coinbase|okx|bybit (still mocks until transport exists)
    market: str  # e.g. BTC-USD
    qty: float
    intent: str  # place_order|cancel_all
    extra: Dict[str, str]


def _assert_mode(mode: str) -> None:
    if mode not in ("shadow", "paper"):
        raise ExecutionEntryGuardError(f"mode_not_allowed:{mode}")


def _assert_dry_run(dry_run: bool) -> None:
    if dry_run is not True:
        raise ExecutionEntryGuardError("dry_run_must_be_true")


def _deny_env(env: Dict[str, str]) -> None:
    for k in DENY_ENV_VARS:
        if k in env and str(env.get(k, "")).strip() not in ("", "0", "false", "False"):
            raise ExecutionEntryGuardError(f"deny_env_set:{k}")


def _secret_check(env: Dict[str, str]) -> None:
    # v1 hard rule: if any obvious secret-like env var is present, fail.
    for k in env.keys():
        uk = k.upper()
        if any(h in uk for h in SECRET_ENV_HINTS):
            raise ExecutionEntryGuardError(f"secret_env_detected:{k}")


def validate_execution_networked_context_v1(
    ctx: ExecutionNetworkedContextV1,
    *,
    env: Optional[Dict[str, str]] = None,
) -> None:
    """Validate context against entry contract guards."""
    _assert_mode(ctx.mode)
    _assert_dry_run(ctx.dry_run)
    env = env or {}
    _deny_env(env)
    _secret_check(env)

    if ctx.intent not in ("place_order", "cancel_all"):
        raise ExecutionEntryGuardError(f"intent_invalid:{ctx.intent}")

    if not ctx.market or "/" in ctx.market:
        # keep this conservative; later we can normalize market formats
        raise ExecutionEntryGuardError("market_invalid")

    if ctx.intent == "place_order" and ctx.qty <= 0:
        raise ExecutionEntryGuardError("qty_invalid")


def build_execution_networked_context_v1(
    *,
    mode: str,
    dry_run: bool,
    adapter: str,
    market: str,
    qty: float,
    intent: str,
    extra_kv: Optional[Sequence[str]] = None,
) -> ExecutionNetworkedContextV1:
    """Build context from kwargs; extra_kv items must be 'key=value'."""
    extra: Dict[str, str] = {}
    if extra_kv:
        for item in extra_kv:
            if "=" not in item:
                raise ValueError(f"extra_kv_invalid:{item}")
            k, v = item.split("=", 1)
            extra[k.strip()] = v.strip()

    return ExecutionNetworkedContextV1(
        mode=mode,
        dry_run=dry_run,
        adapter=adapter,
        market=market,
        qty=qty,
        intent=intent,
        extra=extra,
    )
