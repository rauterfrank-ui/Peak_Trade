"""
Broker abstraction layer (Finish C1).

Scope: mock/fake only, NO-LIVE.
"""

from .adapter import BrokerAdapter
from .base import Broker, BrokerOrderSnapshot, FillCursor
from .errors import (
    BrokerError,
    InvalidOrderError,
    OrderRejectedError,
    PermanentBrokerError,
    RateLimitError,
    TransientBrokerError,
)
from .fake_broker import FakeBroker
from .idempotency import IdempotencyKey, build_idempotency_key
from .retry import RetryConfig, RetryPolicy

__all__ = [
    "Broker",
    "BrokerAdapter",
    "BrokerError",
    "BrokerOrderSnapshot",
    "FakeBroker",
    "FillCursor",
    "IdempotencyKey",
    "InvalidOrderError",
    "OrderRejectedError",
    "PermanentBrokerError",
    "RateLimitError",
    "RetryConfig",
    "RetryPolicy",
    "TransientBrokerError",
    "build_idempotency_key",
]
