"""LB-EXE-001 — transport gate v1 (networkless; optional env isolation for tests)."""

import pytest

from src.execution.networked.entry_contract_v1 import ExecutionEntryGuardError
from src.execution.networked.transport_gate_v1 import TransportGateError, guard_transport_gate_v1


def test_guard_networkless_with_isolated_env() -> None:
    d = guard_transport_gate_v1(
        mode="paper",
        dry_run=True,
        adapter="mock",
        intent="place_order",
        market="BTC-USD",
        qty=0.01,
        transport_allow="NO",
        env={},
    )
    assert d.ok is True
    assert d.reason == "NETWORKLESS_V1"
    assert d.transport_allow == "NO"
    assert d.canary_live_gate_v1 is not None
    assert d.canary_live_gate_v1.outbound_live_or_canary_allowed is False


def test_transport_allow_unknown_rejected() -> None:
    with pytest.raises(TransportGateError, match="TRANSPORT_GATE_DENY"):
        guard_transport_gate_v1(
            mode="paper",
            dry_run=True,
            adapter="mock",
            intent="place_order",
            market="BTC-USD",
            qty=0.01,
            transport_allow="MAYBE",
            env={},
        )


def test_transport_allow_yes_requires_shadow_or_paper_mode() -> None:
    with pytest.raises(ExecutionEntryGuardError, match="mode_not_allowed"):
        guard_transport_gate_v1(
            mode="live",
            dry_run=True,
            adapter="mock",
            intent="place_order",
            market="BTC-USD",
            qty=0.01,
            transport_allow="YES",
            env={},
        )


def test_secret_env_in_forwarded_env_rejected() -> None:
    with pytest.raises(ExecutionEntryGuardError, match="secret_env_detected"):
        guard_transport_gate_v1(
            mode="paper",
            dry_run=True,
            adapter="mock",
            intent="place_order",
            market="BTC-USD",
            qty=0.01,
            transport_allow="NO",
            env={"OKX_API_KEY": "secret"},
        )


def test_transport_allow_yes_shadow_still_networkless_audit() -> None:
    d = guard_transport_gate_v1(
        mode="shadow",
        dry_run=True,
        adapter="mock",
        intent="place_order",
        market="BTC-USD",
        qty=0.01,
        transport_allow="YES",
        env={},
    )
    assert d.ok is True
    assert d.transport_allow == "YES"
    assert d.canary_live_gate_v1 is not None
    assert d.canary_live_gate_v1.reason_code == "deny:missing_external_approval_ref_lb_apr_001"
