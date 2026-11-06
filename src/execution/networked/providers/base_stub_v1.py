from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from src.execution.networked.entry_contract_v1 import (
    ExecutionEntryGuardError,
    guard_entry_contract_v1,
)
from src.execution.networked.transport_gate_v1 import guard_transport_gate_v1


@dataclass(frozen=True)
class NetworkedRequestV1:
    method: str
    url: str
    body: Optional[str] = None


@dataclass(frozen=True)
class NetworkedResponseV1:
    ok: bool
    status_code: int
    body: str


class NetworkedProviderAdapterV1(Protocol):
    name: str

    def build_request(
        self, *, mode: str, dry_run: bool, market: str, intent: str, qty: float
    ) -> NetworkedRequestV1: ...

    def send_request(self, req: NetworkedRequestV1) -> NetworkedResponseV1: ...


class DefaultDenyNetworkedProviderAdapterV1:
    """
    Stub adapter: validates entry contract + transport gate, then DENIES any actual network send.
    """

    name = "networked_stub_default_deny_v1"

    def build_request(
        self, *, mode: str, dry_run: bool, market: str, intent: str, qty: float
    ) -> NetworkedRequestV1:
        adapter = "networked_stub"
        # Contract guards (mode/dry_run/deny-env/secrets hints)
        guard_entry_contract_v1(
            mode=mode,
            dry_run=dry_run,
            adapter=adapter,
            intent=intent,
            market=market,
            qty=qty,
        )

        # Transport gate must remain default-deny (transport_allow must be NO for now)
        guard_transport_gate_v1(
            mode=mode,
            dry_run=dry_run,
            adapter=adapter,
            intent=intent,
            market=market,
            qty=qty,
            transport_allow="NO",
        )

        # Build a placeholder request (never sent)
        return NetworkedRequestV1(
            method="POST", url="https://example.invalid/networked_stub", body="{}"
        )

    def send_request(self, req: NetworkedRequestV1) -> NetworkedResponseV1:
        raise ExecutionEntryGuardError("networked_send_denied: stub adapter cannot send requests")
