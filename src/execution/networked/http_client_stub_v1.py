from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.execution.networked.entry_contract_v1 import guard_entry_contract_v1
from src.execution.networked.transport_gate_v1 import guard_transport_gate_v1


class NetworkTransportDisabledError(RuntimeError):
    """Raised when any networked transport is attempted while disabled."""


@dataclass(frozen=True)
class HttpRequestV1:
    method: str
    url: str
    headers: Dict[str, str]
    json: Optional[Dict[str, Any]] = None
    timeout_sec: int = 10


@dataclass(frozen=True)
class HttpResponseV1:
    ok: bool
    status_code: int
    text: str
    json: Optional[Dict[str, Any]] = None


def http_request_stub_v1(
    *,
    mode: str,
    dry_run: bool,
    adapter: str,
    intent: str,
    market: str,
    qty: float,
    transport_allow: str,
    request: HttpRequestV1,
    test_allow_network_stub: bool = False,
) -> HttpResponseV1:
    """
    Network boundary (stub).
    Default behavior: DENY_ALWAYS unless test_allow_network_stub=True.
    Also enforces entry_contract + transport_gate before any "would-be" network step.
    """
    guard_entry_contract_v1(
        mode=mode,
        dry_run=dry_run,
        adapter=adapter,
        intent=intent,
        market=market,
        qty=qty,
    )

    # transport gate: still default-deny unless caller explicitly asks for YES (which will still be denied in v1)
    guard_transport_gate_v1(
        mode=mode,
        dry_run=dry_run,
        adapter=adapter,
        intent=intent,
        market=market,
        qty=qty,
        transport_allow=transport_allow,
    )

    if not test_allow_network_stub:
        raise NetworkTransportDisabledError(
            "NETWORK_TRANSPORT_DISABLED: http_client_stub_v1 is networkless; "
            "enable only in dedicated transport v2 with allowlists + audited evidence."
        )

    # Test-only placeholder response
    return HttpResponseV1(ok=True, status_code=200, text="STUB_OK", json={"stub": True})
