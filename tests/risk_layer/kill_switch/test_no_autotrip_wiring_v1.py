"""KS_THIN_01: unwired auto-trip library is absent; durable FILEGATE path remains.

Does not split killswitch_blocked. Does not authorize Live, Testnet, Canary,
or auto-trip re-wiring. Does not execute venue I/O.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from src.ops.gates.risk_gate import kill_switch_should_block_trading
from src.risk_layer.kill_switch import KillSwitch, __all__ as KILL_SWITCH_PUBLIC_API

REPO_ROOT = Path(__file__).resolve().parents[3]
TRIGGER_PACKAGE = "src.risk_layer.kill_switch.triggers"
REMOVED_TRIGGER_SYMBOLS = (
    "TriggerRegistry",
    "ThresholdTrigger",
    "WatchdogTrigger",
    "ExternalTrigger",
    "ManualTrigger",
)


def test_autotrip_trigger_package_is_absent() -> None:
    with pytest.raises((ModuleNotFoundError, ImportError)):
        importlib.import_module(TRIGGER_PACKAGE)


@pytest.mark.parametrize("symbol", REMOVED_TRIGGER_SYMBOLS)
def test_kill_switch_public_api_does_not_export_autotrip_symbols(symbol: str) -> None:
    assert symbol not in KILL_SWITCH_PUBLIC_API
    assert not hasattr(importlib.import_module("src.risk_layer.kill_switch"), symbol)


def test_kill_switch_toml_has_no_autotrip_stanzas() -> None:
    text = (REPO_ROOT / "config" / "risk" / "kill_switch.toml").read_text(encoding="utf-8")
    assert "[kill_switch.triggers" not in text
    assert 'type = "threshold"' not in text
    assert 'type = "watchdog"' not in text
    assert 'type = "external"' not in text
    assert 'type = "manual"' not in text


def test_src_has_no_productive_autotrip_import() -> None:
    src_root = REPO_ROOT / "src"
    hits: list[str] = []
    for path in src_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "kill_switch.triggers" in text or "kill_switch/triggers" in text:
            hits.append(str(path.relative_to(REPO_ROOT)))
        for symbol in REMOVED_TRIGGER_SYMBOLS:
            if symbol in text:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{symbol}")
    assert hits == []


def test_filegate_reader_and_cli_writer_remain_the_durable_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "state.json"
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(path))
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    ks = KillSwitch(
        {
            "persist_state": True,
            "require_approval_code": False,
            "recovery_cooldown_seconds": 1,
        }
    )
    assert ks.trigger("KS_THIN_01_contract", triggered_by="manual_cli") is True
    assert path.is_file()
    assert kill_switch_should_block_trading(explicit_active=False) is True
    assert ks.request_recovery(approved_by="operator") is True
    assert kill_switch_should_block_trading(explicit_active=False) is True
