"""Tests for kill-switch health CLI ``exchange_connected`` resolution (NO-LIVE)."""

import pytest

from src.risk_layer.kill_switch.cli import resolve_exchange_connected_for_health

_EXCHANGE_CONNECTED_ENV = "PEAK_KILL_SWITCH_EXCHANGE_CONNECTED"


@pytest.mark.parametrize(
    "cli_choice",
    ("true", "false"),
)
def test_resolve_explicit_ignores_env(monkeypatch, cli_choice):
    monkeypatch.setenv(_EXCHANGE_CONNECTED_ENV, "0")
    assert resolve_exchange_connected_for_health(cli_choice) == (cli_choice == "true")


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("", True),
        ("1", True),
        ("true", True),
        ("yes", True),
        ("on", True),
        ("0", False),
        ("false", False),
        ("no", False),
        ("off", False),
    ],
)
def test_resolve_auto_env(monkeypatch, raw, expected):
    if raw:
        monkeypatch.setenv(_EXCHANGE_CONNECTED_ENV, raw)
    else:
        monkeypatch.delenv(_EXCHANGE_CONNECTED_ENV, raising=False)
    assert resolve_exchange_connected_for_health("auto") is expected


def test_resolve_auto_unset_defaults_true(monkeypatch):
    monkeypatch.delenv(_EXCHANGE_CONNECTED_ENV, raising=False)
    assert resolve_exchange_connected_for_health("auto") is True
