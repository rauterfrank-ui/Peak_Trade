import os
import pytest

from src.execution.networked.entry_contract_v1 import ExecutionEntryGuardError
from src.execution.networked.transport_gate_v1 import (
    TransportGateError,
    guard_transport_gate_v1,
)


def test_ok_path_networkless_v1_allows_only_no():
    d = guard_transport_gate_v1(
        mode="shadow",
        dry_run=True,
        adapter="mock",
        intent="place_order",
        market="BTC-USD",
        qty=0.01,
        transport_allow="NO",
    )
    assert d.ok is True
    assert d.reason == "NETWORKLESS_V1"
    assert d.transport_allow == "NO"


def test_default_transport_allow_is_no():
    d = guard_transport_gate_v1(
        mode="paper",
        dry_run=True,
        adapter="mock",
        intent="cancel_all",
        market="BTC-USD",
        qty=0.01,
    )
    assert d.transport_allow == "NO"


def test_allow_transport_allow_yes_when_shadow_paper_dry_run():
    """P132: transport_allow=YES allowed when mode in (shadow,paper) and dry_run=True."""
    d = guard_transport_gate_v1(
        mode="shadow",
        dry_run=True,
        adapter="mock",
        intent="place_order",
        market="BTC-USD",
        qty=0.01,
        transport_allow="YES",
    )
    assert d.ok is True
    assert d.transport_allow == "YES"


def test_deny_when_secret_env_present():
    os.environ["KRAKEN_API_KEY"] = "x"
    try:
        with pytest.raises(ExecutionEntryGuardError):
            guard_transport_gate_v1(
                mode="shadow",
                dry_run=True,
                adapter="mock",
                intent="place_order",
                market="BTC-USD",
                qty=0.01,
                transport_allow="NO",
            )
    finally:
        os.environ.pop("KRAKEN_API_KEY", None)
