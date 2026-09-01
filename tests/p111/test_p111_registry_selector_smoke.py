"""P111: Registry + selector smoke (mocks only)."""

from __future__ import annotations

import pytest

from src.execution.adapters.registry_v1 import (
    build_adapter_registry_v1,
    select_execution_adapter_v1,
)


def test_registry_has_expected_adapters() -> None:
    reg = build_adapter_registry_v1()
    assert "mock" in reg
    assert "okx" in reg
    assert set(reg) == {"mock", "okx"}


def test_select_okx_perp_ok() -> None:
    a = select_execution_adapter_v1("okx", market="perp")
    caps = a.capabilities()
    assert caps.name.lower().startswith("okx")


def test_select_unknown_adapter_denied() -> None:
    with pytest.raises((KeyError, ValueError)):
        select_execution_adapter_v1("unknown_adapter", market="perp")
