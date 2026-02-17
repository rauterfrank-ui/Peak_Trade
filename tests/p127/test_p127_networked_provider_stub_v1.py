import pytest

from src.execution.networked.entry_contract_v1 import ExecutionEntryGuardError
from src.execution.networked.providers.base_stub_v1 import DefaultDenyNetworkedProviderAdapterV1


def test_build_request_ok_shadow_dry_run_yes_default_deny_transport():
    a = DefaultDenyNetworkedProviderAdapterV1()
    req = a.build_request(
        mode="shadow", dry_run=True, market="BTC-USD", intent="place_order", qty=0.01
    )
    assert req.url.startswith("https://")


def test_build_request_rejects_live_mode():
    a = DefaultDenyNetworkedProviderAdapterV1()
    with pytest.raises(ExecutionEntryGuardError):
        a.build_request(mode="live", dry_run=True, market="BTC-USD", intent="place_order", qty=0.01)


def test_build_request_rejects_dry_run_false():
    a = DefaultDenyNetworkedProviderAdapterV1()
    with pytest.raises(ExecutionEntryGuardError):
        a.build_request(
            mode="shadow",
            dry_run=False,
            market="BTC-USD",
            intent="place_order",
            qty=0.01,
        )


def test_send_request_always_denied():
    a = DefaultDenyNetworkedProviderAdapterV1()
    req = a.build_request(
        mode="shadow", dry_run=True, market="BTC-USD", intent="place_order", qty=0.01
    )
    with pytest.raises(ExecutionEntryGuardError):
        a.send_request(req)
