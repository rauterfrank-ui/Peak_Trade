from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Set

from .entry_contract_v1 import ExecutionEntryGuardError


@dataclass(frozen=True)
class NetworkedAllowlistV1:
    """
    Default-deny allowlist for networked execution.

    This is intentionally conservative:
    - transport_allow must still be explicitly enabled elsewhere (TransportGateV1).
    - allowlist here is an additional gate: adapter + market must be explicitly allowed.
    """

    allowed_adapters: Set[str]
    allowed_markets: Set[str]

    @classmethod
    def default_deny(cls) -> "NetworkedAllowlistV1":
        return cls(allowed_adapters=set(), allowed_markets=set())

    @classmethod
    def from_iterables(
        cls,
        *,
        adapters: Iterable[str] | None = None,
        markets: Iterable[str] | None = None,
    ) -> "NetworkedAllowlistV1":
        return cls(
            allowed_adapters=set(adapters or []),
            allowed_markets=set(markets or []),
        )

    def is_allowed(self, *, adapter: str, market: str) -> bool:
        return (adapter in self.allowed_adapters) and (market in self.allowed_markets)


def guard_allowlist_v1(*, allowlist: NetworkedAllowlistV1, adapter: str, market: str) -> None:
    if not allowlist.is_allowed(adapter=adapter, market=market):
        raise ExecutionEntryGuardError(f"allowlist_denied adapter={adapter} market={market}")
