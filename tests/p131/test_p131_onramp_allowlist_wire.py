"""P131 — Onramp allowlist wire tests."""

from __future__ import annotations

from src.execution.networked.allowlist_v1 import NetworkedAllowlistV1
from src.execution.networked.onramp_runner_v1 import run_networked_onramp_v1


def _base_ctx() -> dict:
    return {
        "mode": "shadow",
        "dry_run": True,
        "intent": "place_order",
        "market": "BTC-USD",
        "qty": 0.01,
        "transport_allow": "NO",
        "adapter": "networked_stub",
    }


def test_allowlist_allow_no_denies_before_adapter() -> None:
    """allowlist_allow=NO -> allowlist rc=1, onramp returns early (no adapter step)."""
    report = run_networked_onramp_v1(
        **_base_ctx(),
        allowlist_allow="NO",
    )
    assert report["guards"]["rc"] == 0
    assert report["allowlist"]["rc"] == 1
    assert "allowlist_disabled" in report["allowlist"]["msg"]
    assert report["meta"]["ok"] is False
    assert report["adapter"]["rc"] == 0
    assert report["adapter"]["msg"] == ""


def test_allowlist_allow_yes_but_empty_denied() -> None:
    """allowlist_allow=YES but list empty -> denied."""
    report = run_networked_onramp_v1(
        **_base_ctx(),
        allowlist_allow="YES",
        allowlist=NetworkedAllowlistV1.default_deny(),
    )
    assert report["guards"]["rc"] == 0
    assert report["allowlist"]["rc"] == 1
    assert "allowlist_denied" in report["allowlist"]["msg"]
    assert report["meta"]["ok"] is False


def test_allowlist_allow_yes_and_market_in_allowlist_proceeds() -> None:
    """allowlist_allow=YES and market in allowlist -> proceeds to transport, adapter denied."""
    allowlist = NetworkedAllowlistV1.from_iterables(
        adapters=["networked_stub"],
        markets=["BTC-USD"],
    )
    report = run_networked_onramp_v1(
        **_base_ctx(),
        allowlist_allow="YES",
        allowlist=allowlist,
    )
    assert report["guards"]["rc"] == 0
    assert report["allowlist"]["rc"] == 0
    assert report["allowlist"]["msg"] == "ok"
    assert report["transport"]["rc"] == 0
    assert report["adapter"]["rc"] == 1
    assert "networked_send_denied" in report["adapter"]["msg"]
    assert report["meta"]["ok"] is True
