"""
Idempotency helpers (Finish C1).

We keep this minimal and deterministic:
- input -> stable key (sha256 over canonical string)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from src.execution.contracts import Order


@dataclass(frozen=True)
class IdempotencyKey:
    value: str


def build_idempotency_key(order: Order, idempotency_key: str) -> IdempotencyKey:
    """
    Build a stable idempotency key for (order, idempotency_key).

    Uses deterministic serialization of Order via Order.to_json().
    """

    canonical = f"{idempotency_key}|{order.to_json()}"
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return IdempotencyKey(digest)
