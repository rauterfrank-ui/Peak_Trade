"""Unit tests for kill-switch HTTP exchange probe (NO-LIVE)."""

from __future__ import annotations

import urllib.error

import pytest

from src.risk_layer.kill_switch import exchange_probe as ep


def test_is_exchange_probe_disabled(monkeypatch):
    monkeypatch.delenv("PEAK_KILL_SWITCH_EXCHANGE_PROBE_DISABLED", raising=False)
    assert ep.is_exchange_probe_disabled() is False
    monkeypatch.setenv("PEAK_KILL_SWITCH_EXCHANGE_PROBE_DISABLED", "1")
    assert ep.is_exchange_probe_disabled() is True


def test_probe_exchange_http_public_success(monkeypatch):
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

        def getcode(self):
            return 200

    def _fake_urlopen(req, timeout=None):
        return _Resp()

    monkeypatch.setattr(ep.urllib.request, "urlopen", _fake_urlopen)
    monkeypatch.setenv("PEAK_KILL_SWITCH_EXCHANGE_PROBE_URL", "https://example.test/status")
    ok, meta = ep.probe_exchange_http_public()
    assert ok is True
    assert meta["probe_http_status"] == 200
    assert meta["exchange_connected_source"] == "http_probe"


def test_probe_exchange_http_public_http_error(monkeypatch):
    def _fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(
            "https://example.test/", 503, "Service Unavailable", hdrs=None, fp=None
        )

    monkeypatch.setattr(ep.urllib.request, "urlopen", _fake_urlopen)
    ok, meta = ep.probe_exchange_http_public()
    assert ok is False
    assert meta["probe_http_status"] == 503
