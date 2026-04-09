"""LB-EXE-001 — transport gate v1 (networkless; optional env isolation for tests)."""

import pytest

from src.execution.networked.canary_live_gate_v1 import ENV_PT_CANARY_SCOPE_REF
from src.execution.networked.entry_contract_v1 import ExecutionEntryGuardError
from src.execution.networked.transport_gate_v1 import (
    TransportGateError,
    assert_networkless_v1,
    guard_transport_gate_v1,
)


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


def test_transport_allow_omitted_defaults_to_no() -> None:
    d = guard_transport_gate_v1(
        mode="paper",
        dry_run=True,
        adapter="mock",
        intent="place_order",
        market="BTC-USD",
        qty=0.01,
        env={},
    )
    assert d.transport_allow == "NO"


def test_transport_allow_whitespace_normalized_to_no() -> None:
    d = guard_transport_gate_v1(
        mode="paper",
        dry_run=True,
        adapter="mock",
        intent="place_order",
        market="BTC-USD",
        qty=0.01,
        transport_allow="  no  ",
        env={},
    )
    assert d.transport_allow == "NO"


def test_transport_allow_yes_requires_dry_run_true_via_entry_guard() -> None:
    with pytest.raises(ExecutionEntryGuardError, match="dry_run_must_be_true"):
        guard_transport_gate_v1(
            mode="paper",
            dry_run=False,
            adapter="mock",
            intent="place_order",
            market="BTC-USD",
            qty=0.01,
            transport_allow="YES",
            env={},
        )


def test_canary_gate_uses_forwarded_env_not_only_process_environ() -> None:
    """Canary decision must use the same resolved env mapping as the entry guard."""
    d = guard_transport_gate_v1(
        mode="paper",
        dry_run=True,
        adapter="mock",
        intent="place_order",
        market="BTC-USD",
        qty=0.01,
        transport_allow="NO",
        env={ENV_PT_CANARY_SCOPE_REF: "scope-ref-phase2"},
    )
    assert d.canary_live_gate_v1 is not None
    assert d.canary_live_gate_v1.reason_code == "deny:v1_networkless_no_outbound_transport"
    assert d.canary_live_gate_v1.external_approval_ref_present is True


def test_assert_networkless_v1_is_noop() -> None:
    assert assert_networkless_v1() is None
