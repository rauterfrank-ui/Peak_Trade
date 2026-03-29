"""Tests for kill-switch health CLI ``exchange_connected`` resolution (NO-LIVE)."""

import pytest

from src.risk_layer.kill_switch.cli import resolve_exchange_connected_for_health

_EXCHANGE_CONNECTED_ENV = "PEAK_KILL_SWITCH_EXCHANGE_CONNECTED"
_PROBE_DISABLED_ENV = "PEAK_KILL_SWITCH_EXCHANGE_PROBE_DISABLED"


@pytest.mark.parametrize(
    "cli_choice",
    ("true", "false"),
)
def test_resolve_explicit_ignores_env(monkeypatch, cli_choice):
    monkeypatch.setenv(_EXCHANGE_CONNECTED_ENV, "0")
    ok, meta = resolve_exchange_connected_for_health(cli_choice)
    assert ok == (cli_choice == "true")
    assert meta.get("exchange_connected_source") == (
        "cli_true" if cli_choice == "true" else "cli_false"
    )


@pytest.mark.parametrize(
    "raw, expected",
    [
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
    monkeypatch.delenv(_PROBE_DISABLED_ENV, raising=False)
    monkeypatch.setenv(_EXCHANGE_CONNECTED_ENV, raw)
    ok, meta = resolve_exchange_connected_for_health("auto")
    assert ok is expected
    assert meta.get("exchange_connected_source") == "env"


def test_resolve_auto_unset_uses_probe_disabled_fallback(monkeypatch):
    monkeypatch.delenv(_EXCHANGE_CONNECTED_ENV, raising=False)
    monkeypatch.setenv(_PROBE_DISABLED_ENV, "1")
    ok, meta = resolve_exchange_connected_for_health("auto")
    assert ok is True
    assert meta.get("exchange_connected_source") == "probe_disabled_fallback"


def test_resolve_auto_unset_runs_http_probe(monkeypatch):
    monkeypatch.delenv(_EXCHANGE_CONNECTED_ENV, raising=False)
    monkeypatch.delenv(_PROBE_DISABLED_ENV, raising=False)

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

        def getcode(self):
            return 200

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=None: _Resp())
    ok, meta = resolve_exchange_connected_for_health("auto")
    assert ok is True
    assert meta.get("exchange_connected_source") == "http_probe"
    assert meta.get("probe_http_status") == 200
