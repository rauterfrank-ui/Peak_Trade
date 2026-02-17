from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .entry_contract_v1 import ExecutionEntryGuardError, guard_entry_contract_v1
from .transport_gate_v1 import TransportGateV1, guard_transport_gate_v1


@dataclass(frozen=True)
class HttpRequestV1:
    method: str
    url: str
    headers: Mapping[str, str]
    body: Optional[bytes] = None
    timeout_sec: float = 10.0


@dataclass(frozen=True)
class HttpResponseV1:
    ok: bool
    status_code: int
    headers: Mapping[str, str]
    body: bytes
    error: Optional[str] = None


class NetworkedTransportStubV1:
    """
    Networkless transport stub.

    Hard guarantees:
    - Enforces entry contract guard (mode, dry_run, deny env, required args).
    - Enforces transport gate guard (default-deny: transport_allow must be "NO").
    - Never performs network I/O (always returns a deterministic deny response).
    """

    def __init__(self, gate: Optional[TransportGateV1] = None) -> None:
        self._gate = gate or TransportGateV1()

    def request(self, *, request: HttpRequestV1, ctx: Mapping[str, Any]) -> HttpResponseV1:
        mode = str(ctx.get("mode", ""))
        dry_run = bool(ctx.get("dry_run", False))
        adapter = str(ctx.get("adapter", "networked_stub"))
        intent = str(ctx.get("intent", ""))
        market = str(ctx.get("market", ""))
        qty = float(ctx.get("qty", 0.0))
        env = dict(ctx.get("env", {}))

        # Entry contract guard (should already be applied by caller, but enforced here too).
        guard_entry_contract_v1(
            mode=mode,
            dry_run=dry_run,
            adapter=adapter,
            intent=intent,
            market=market,
            qty=qty,
            env=env,
        )

        # Transport gate guard (networkless default-deny)
        guard_transport_gate_v1(
            mode=mode,
            dry_run=dry_run,
            adapter=adapter,
            intent=intent,
            market=market,
            qty=qty,
            transport_allow=self._gate.transport_allow,
        )

        # If guard passes, we still refuse to do network I/O (this is a stub).
        return HttpResponseV1(
            ok=False,
            status_code=599,
            headers={},
            body=b"",
            error="NETWORKED_TRANSPORT_STUB_DENY: no network I/O permitted (stub)",
        )


def build_networked_transport_stub_v1() -> NetworkedTransportStubV1:
    return NetworkedTransportStubV1()
