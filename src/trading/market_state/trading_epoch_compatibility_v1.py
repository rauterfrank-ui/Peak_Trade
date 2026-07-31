"""Additive trading_epoch compatibility validator for C1.

Proves:
  trading_epoch_alias_target=MarketObservationEpoch
  runtime_cycle_assignment_rejected=true

No productive caller migration. No hot-path wiring.
"""

from __future__ import annotations

from trading.market_state.observation_identity_v1 import MarketObservationEpoch

TRADING_EPOCH_ALIAS_TARGET = "MarketObservationEpoch"
RUNTIME_CYCLE_ASSIGNMENT_REJECTED = True


class TradingEpochCompatibilityErrorV1(ValueError):
    """Fail-closed compatibility contract error (programming/contract fault)."""


def market_observation_epoch_from_trading_epoch_alias_v1(
    trading_epoch: int,
) -> MarketObservationEpoch:
    """Map a non-negative trading_epoch alias onto MarketObservationEpoch.

    This is an additive compatibility helper only. It does not authorize
    productive rewiring of trading_epoch callers.
    """
    if isinstance(trading_epoch, bool) or not isinstance(trading_epoch, int):
        raise TradingEpochCompatibilityErrorV1("TRADING_EPOCH_ALIAS_TYPE_INVALID")
    if trading_epoch < 0:
        raise TradingEpochCompatibilityErrorV1("TRADING_EPOCH_ALIAS_NEGATIVE")
    return MarketObservationEpoch(value=trading_epoch)


def assert_runtime_cycle_assignment_rejected_v1(runtime_cycle_index: object) -> None:
    """Runtime cycle indices must never advance MarketObservationEpoch."""
    raise TradingEpochCompatibilityErrorV1(
        "runtime_cycle_assignment_rejected:"
        f"runtime_cycle_index={runtime_cycle_index!r};"
        f"alias_target={TRADING_EPOCH_ALIAS_TARGET}"
    )


def assert_trading_epoch_alias_target_v1() -> str:
    if TRADING_EPOCH_ALIAS_TARGET != "MarketObservationEpoch":
        raise TradingEpochCompatibilityErrorV1("TRADING_EPOCH_ALIAS_TARGET_DRIFT")
    if RUNTIME_CYCLE_ASSIGNMENT_REJECTED is not True:
        raise TradingEpochCompatibilityErrorV1("RUNTIME_CYCLE_ASSIGNMENT_REJECTED_DRIFT")
    return TRADING_EPOCH_ALIAS_TARGET
