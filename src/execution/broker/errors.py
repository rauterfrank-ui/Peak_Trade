"""
Broker errors (Finish C1).

Design goals:
- Explicit retry semantics (transient vs permanent)
- NO-LIVE: errors are used by FakeBroker + tests only in C1
"""


class BrokerError(Exception):
    """Base class for broker-layer exceptions."""


class TransientBrokerError(BrokerError):
    """Retryable error (timeouts, temporary unavailable, rate limits)."""


class RateLimitError(TransientBrokerError):
    """Retryable error: broker/venue rate limit exceeded."""


class PermanentBrokerError(BrokerError):
    """Non-retryable error (invalid params, rejected)."""


class InvalidOrderError(PermanentBrokerError):
    """Order request is invalid."""


class OrderRejectedError(PermanentBrokerError):
    """Order was rejected by the broker/venue."""
