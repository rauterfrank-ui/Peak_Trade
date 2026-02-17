"""P129 — Execution networked onramp runner (networkless, default-deny)."""

from __future__ import annotations

import os
from typing import Any, Dict

from .entry_contract_v1 import ExecutionEntryGuardError, guard_entry_contract_v1
from .providers.base_stub_v1 import DefaultDenyNetworkedProviderAdapterV1
from .transport_gate_v1 import TransportGateError, guard_transport_gate_v1
from .transport_stub_v1 import (
    HttpRequestV1,
    NetworkedTransportStubV1,
    build_networked_transport_stub_v1,
)


def run_networked_onramp_v1(
    *,
    mode: str,
    dry_run: bool,
    intent: str,
    market: str,
    qty: float,
    transport_allow: str,
    adapter: str = "networked_stub",
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    """
    Run the networked onramp flow: EntryContract -> TransportGate -> Transport(Stub) -> ProviderAdapter(Stub).

    Returns a report dict with meta, guards, transport, adapter.
    """
    env = env or dict(os.environ)
    report: Dict[str, Any] = {
        "meta": {
            "ok": False,
            "mode": mode,
            "dry_run": dry_run,
            "transport_allow": transport_allow,
            "adapter": adapter,
            "intent": intent,
            "market": market,
            "qty": qty,
        },
        "guards": {"rc": 0, "msg": ""},
        "transport": {"rc": 0, "msg": ""},
        "adapter": {"rc": 0, "msg": ""},
    }

    # 1) Entry contract guard
    try:
        guard_entry_contract_v1(
            mode=mode,
            dry_run=dry_run,
            adapter=adapter,
            intent=intent,
            market=market,
            qty=qty,
            env=env,
        )
        report["guards"]["rc"] = 0
        report["guards"]["msg"] = "ok"
    except ExecutionEntryGuardError as e:
        report["guards"]["rc"] = 1
        report["guards"]["msg"] = str(e)
        return report

    # 2) Transport gate guard (transport_allow=YES => deny, exit 3)
    try:
        guard_transport_gate_v1(
            mode=mode,
            dry_run=dry_run,
            adapter=adapter,
            intent=intent,
            market=market,
            qty=qty,
            transport_allow=transport_allow,
        )
    except TransportGateError as e:
        report["transport"]["rc"] = 3
        report["transport"]["msg"] = str(e)
        return report

    # 3) Transport stub (returns deny response)
    ctx: Dict[str, Any] = {
        "mode": mode,
        "dry_run": dry_run,
        "adapter": adapter,
        "intent": intent,
        "market": market,
        "qty": qty,
        "env": env,
    }
    transport = build_networked_transport_stub_v1()
    req = HttpRequestV1(method="GET", url="https://example.invalid", headers={})
    resp = transport.request(request=req, ctx=ctx)
    report["transport"]["rc"] = 0
    report["transport"]["msg"] = resp.error or "stub_deny"

    # 4) Provider adapter (build_request ok, send_request denies)
    try:
        provider = DefaultDenyNetworkedProviderAdapterV1()
        built_req = provider.build_request(
            mode=mode,
            dry_run=dry_run,
            market=market,
            intent=intent,
            qty=qty,
        )
        provider.send_request(built_req)
        report["adapter"]["rc"] = 0
        report["adapter"]["msg"] = "ok"
    except ExecutionEntryGuardError as e:
        report["adapter"]["rc"] = 1
        report["adapter"]["msg"] = str(e)

    report["meta"]["ok"] = (
        report["guards"]["rc"] == 0
        and report["transport"]["rc"] == 0
        and report["adapter"]["rc"] in (0, 1)
    )
    return report
