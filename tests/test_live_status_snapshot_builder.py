# tests/test_live_status_snapshot_builder.py
"""
Tests for Live Status Snapshot Builder (Phase 57 Extension).

Tests:
- Default fallback behavior (no providers)
- Deterministic panel ordering
- Deterministic details ordering
- Provider return formats (dict/tuple/PanelSnapshot)
- Provider exception handling → error panel
- Status mapping (str/bool/int)
- Meta passthrough
- Snapshot version
- Generated_at exists and ISO-ish

Run:
    pytest tests/test_live_status_snapshot_builder.py -v
"""

from __future__ import annotations

import pytest
from datetime import datetime

from src.reporting.live_status_snapshot_builder import (
    build_live_status_snapshot,
    build_live_status_snapshot_auto,
    _invoke_provider_safely,
    _panel_from_dict,
)
from src.reporting.status_snapshot_schema import (
    PanelSnapshot,
    normalize_status,
    normalize_details,
    model_dump_helper,
)


# =============================================================================
# Tests: normalize_status
# =============================================================================


@pytest.mark.parametrize(
    "input_status,expected",
    [
        ("ok", "ok"),
        ("OK", "ok"),
        ("warn", "warn"),
        ("WARNING", "warn"),
        ("error", "error"),
        ("FAIL", "error"),
        ("unknown", "unknown"),
        (True, "ok"),
        (False, "error"),
        (0, "ok"),
        (1, "warn"),
        (2, "error"),
        (None, "unknown"),
    ],
)
def test_normalize_status(input_status, expected):
    """Test status normalization for various inputs."""
    assert normalize_status(input_status) == expected


# =============================================================================
# Tests: normalize_details
# =============================================================================


def test_normalize_details_sorts_keys():
    """Test that details keys are sorted alphabetically."""
    details = {"z": 1, "a": 2, "m": 3}
    normalized = normalize_details(details)
    assert list(normalized.keys()) == ["a", "m", "z"]


def test_normalize_details_recursive():
    """Test that nested dicts are also normalized."""
    details = {
        "outer_z": {"inner_z": 1, "inner_a": 2},
        "outer_a": {"inner_m": 3},
    }
    normalized = normalize_details(details)
    assert list(normalized.keys()) == ["outer_a", "outer_z"]
    assert list(normalized["outer_z"].keys()) == ["inner_a", "inner_z"]


# =============================================================================
# Tests: build_live_status_snapshot (default behavior)
# =============================================================================


def test_build_snapshot_no_providers():
    """Test snapshot with no providers returns default system panel."""
    snapshot = build_live_status_snapshot({})

    assert snapshot.version == "0.1"
    assert len(snapshot.panels) == 1
    assert snapshot.panels[0].id == "system"
    assert snapshot.panels[0].status in (
        "ok",
        "unknown",
    )  # Status can be either depending on implementation
    assert "message" in snapshot.panels[0].details


def test_build_snapshot_version():
    """Test snapshot has correct version."""
    snapshot = build_live_status_snapshot_auto()
    assert snapshot.version == "0.1"


def test_build_snapshot_generated_at_iso():
    """Test snapshot has generated_at in ISO format."""
    snapshot = build_live_status_snapshot_auto()

    # Should be parseable as ISO datetime
    dt = datetime.fromisoformat(snapshot.generated_at.replace("Z", "+00:00"))
    assert isinstance(dt, datetime)

    # Should be recent (within last minute)
    now = datetime.now(dt.tzinfo)
    delta_seconds = abs((now - dt).total_seconds())
    assert delta_seconds < 60


# =============================================================================
# Tests: Provider Return Formats
# =============================================================================


def test_provider_returns_dict():
    """Test provider returning dict is converted to PanelSnapshot."""

    def provider():
        return {"id": "test", "title": "Test", "status": "ok", "details": {"key": "value"}}

    snapshot = build_live_status_snapshot(panel_providers={"test": provider})

    assert len(snapshot.panels) == 1
    panel = snapshot.panels[0]
    assert panel.id == "test"
    assert panel.title == "Test"
    assert panel.status == "ok"
    assert panel.details["key"] == "value"


def test_provider_returns_tuple():
    """Test provider returning tuple (status, title, details)."""

    def provider():
        return ("ok", "Test Title", {"metric": 42})

    snapshot = build_live_status_snapshot(panel_providers={"my_panel": provider})

    assert len(snapshot.panels) == 1
    panel = snapshot.panels[0]
    assert panel.id == "my_panel"
    assert panel.title == "Test Title"
    assert panel.status == "ok"
    assert panel.details["metric"] == 42


def test_provider_returns_panel_snapshot():
    """Test provider returning PanelSnapshot is passed through."""

    def provider():
        return PanelSnapshot(
            id="direct", title="Direct Panel", status="warn", details={"alert": "check this"}
        )

    snapshot = build_live_status_snapshot(panel_providers={"direct": provider})

    assert len(snapshot.panels) == 1
    panel = snapshot.panels[0]
    assert panel.id == "direct"
    assert panel.title == "Direct Panel"
    assert panel.status == "warn"


# =============================================================================
# Tests: Provider Exception Handling
# =============================================================================


def test_provider_exception_creates_error_panel():
    """Test that provider exceptions create error panels (no crash)."""

    def failing_provider():
        raise ValueError("Provider crashed!")

    snapshot = build_live_status_snapshot(panel_providers={"broken": failing_provider})

    assert len(snapshot.panels) == 1
    panel = snapshot.panels[0]
    assert panel.id == "broken"
    assert panel.status == "error"
    assert "ValueError" in panel.details.get("error", "")
    assert "Provider crashed!" in panel.details.get("error", "")


def test_multiple_providers_one_fails():
    """Test that one failing provider doesn't break others."""

    def good_provider():
        return {"status": "ok", "details": {"healthy": True}}

    def bad_provider():
        raise RuntimeError("Boom!")

    providers = {
        "good": good_provider,
        "bad": bad_provider,
    }

    snapshot = build_live_status_snapshot(panel_providers=providers)

    assert len(snapshot.panels) == 2

    # Check good panel
    good_panel = next(p for p in snapshot.panels if p.id == "good")
    assert good_panel.status == "ok"

    # Check bad panel became error panel
    bad_panel = next(p for p in snapshot.panels if p.id == "bad")
    assert bad_panel.status == "error"
    assert "RuntimeError" in bad_panel.details.get("error", "")


# =============================================================================
# Tests: Determinism
# =============================================================================


def test_panels_sorted_by_id():
    """Test that panels are sorted by ID for deterministic output."""

    def provider_z():
        return {"status": "ok"}

    def provider_a():
        return {"status": "ok"}

    def provider_m():
        return {"status": "ok"}

    providers = {
        "z_panel": provider_z,
        "a_panel": provider_a,
        "m_panel": provider_m,
    }

    snapshot = build_live_status_snapshot(panel_providers=providers)

    panel_ids = [p.id for p in snapshot.panels]
    assert panel_ids == ["a_panel", "m_panel", "z_panel"]


def test_details_keys_sorted():
    """Test that panel details have sorted keys."""

    def provider():
        return {"status": "ok", "details": {"z": 1, "a": 2, "m": 3}}

    snapshot = build_live_status_snapshot(panel_providers={"test": provider})

    panel = snapshot.panels[0]
    assert list(panel.details.keys()) == ["a", "m", "z"]


# =============================================================================
# Tests: Meta Passthrough
# =============================================================================


def test_meta_passthrough():
    """Test that meta dict is passed through to snapshot."""
    meta = {"config_path": "config/test.toml", "tag": "daily", "custom": 123}

    snapshot = build_live_status_snapshot_auto(meta=meta)

    assert snapshot.meta["config_path"] == "config/test.toml"
    assert snapshot.meta["tag"] == "daily"
    assert snapshot.meta["custom"] == 123


def test_meta_keys_sorted():
    """Test that meta keys are sorted for determinism."""
    meta = {"z": 1, "a": 2, "m": 3}

    snapshot = build_live_status_snapshot_auto(meta=meta)

    assert list(snapshot.meta.keys()) == ["a", "m", "z"]


# =============================================================================
# Tests: Panel Conversion Helpers
# =============================================================================


def test_panel_from_dict_minimal():
    """Test _panel_from_dict with minimal data (only status)."""
    panel = _panel_from_dict("my_panel", {"status": "ok"})

    assert panel.id == "my_panel"
    assert panel.title == "My Panel"  # Auto-generated from ID
    assert panel.status == "ok"
    assert panel.details == {}


def test_panel_from_dict_full():
    """Test _panel_from_dict with all fields."""
    data = {"id": "custom_id", "title": "Custom Title", "status": "warn", "details": {"metric": 42}}

    panel = _panel_from_dict("fallback_id", data)

    assert panel.id == "custom_id"
    assert panel.title == "Custom Title"
    assert panel.status == "warn"
    assert panel.details["metric"] == 42


def test_invoke_provider_safely_dict():
    """Test _invoke_provider_safely with dict return."""

    def provider():
        return {"status": "ok", "details": {"test": True}}

    panel = _invoke_provider_safely("test_id", provider)

    assert isinstance(panel, PanelSnapshot)
    assert panel.id == "test_id"
    assert panel.status == "ok"


def test_invoke_provider_safely_tuple():
    """Test _invoke_provider_safely with tuple return."""

    def provider():
        return ("warn", "Warning Title", {"reason": "low memory"})

    panel = _invoke_provider_safely("mem_check", provider)

    assert isinstance(panel, PanelSnapshot)
    assert panel.id == "mem_check"
    assert panel.title == "Warning Title"
    assert panel.status == "warn"


def test_invoke_provider_safely_panel_snapshot():
    """Test _invoke_provider_safely with PanelSnapshot return."""

    def provider():
        return PanelSnapshot(id="direct", title="Direct", status="error", details={"code": 500})

    panel = _invoke_provider_safely("should_be_ignored", provider)

    assert isinstance(panel, PanelSnapshot)
    assert panel.id == "direct"  # Uses PanelSnapshot's ID, not the function arg
    assert panel.title == "Direct"
    assert panel.status == "error"


def test_invoke_provider_safely_invalid_type():
    """Test _invoke_provider_safely with invalid return type raises error."""

    def provider():
        return "invalid string return"

    with pytest.raises(ValueError, match="unsupported type"):
        _invoke_provider_safely("bad_provider", provider)


# =============================================================================
# Tests: Model Dump
# =============================================================================


def test_model_dump_helper():
    """Test model_dump_helper works for Pydantic v1/v2."""
    snapshot = build_live_status_snapshot_auto()

    snapshot_dict = model_dump_helper(snapshot)

    assert isinstance(snapshot_dict, dict)
    assert "version" in snapshot_dict
    assert "generated_at" in snapshot_dict
    assert "panels" in snapshot_dict
    assert isinstance(snapshot_dict["panels"], list)


# =============================================================================
# Tests: Integration Scenarios
# =============================================================================


def test_full_scenario_multiple_providers():
    """Integration test with multiple providers, different formats."""

    def system_provider():
        return PanelSnapshot(
            id="system", title="System Health", status="ok", details={"cpu": 25.5, "memory": 60.2}
        )

    def portfolio_provider():
        return {
            "id": "portfolio",
            "title": "Portfolio Status",
            "status": "warn",
            "details": {"positions": 5, "exposure": 12500},
        }

    def risk_provider():
        return ("ok", "Risk Limits", {"within_limits": True, "max_drawdown": 0.05})

    providers = {
        "system": system_provider,
        "portfolio": portfolio_provider,
        "risk": risk_provider,
    }

    meta = {"config": "live.toml", "environment": "production"}

    snapshot = build_live_status_snapshot(panel_providers=providers, meta=meta)

    # Check structure
    assert snapshot.version == "0.1"
    assert len(snapshot.panels) == 3
    assert snapshot.meta["config"] == "live.toml"

    # Check panels are sorted
    panel_ids = [p.id for p in snapshot.panels]
    assert panel_ids == ["portfolio", "risk", "system"]

    # Check each panel
    portfolio = next(p for p in snapshot.panels if p.id == "portfolio")
    assert portfolio.status == "warn"
    assert portfolio.details["positions"] == 5

    risk = next(p for p in snapshot.panels if p.id == "risk")
    assert risk.status == "ok"
    assert risk.details["within_limits"] is True

    system = next(p for p in snapshot.panels if p.id == "system")
    assert system.status == "ok"
    assert system.details["cpu"] == 25.5


def test_snapshot_json_serializable():
    """Test that snapshot can be serialized to JSON."""
    import json

    def provider():
        return {
            "status": "ok",
            "details": {"number": 42, "text": "test", "nested": {"key": "value"}},
        }

    snapshot = build_live_status_snapshot(panel_providers={"test": provider})
    snapshot_dict = model_dump_helper(snapshot)

    # Should be JSON serializable
    json_str = json.dumps(snapshot_dict, sort_keys=True)

    # Should be parseable
    parsed = json.loads(json_str)
    assert parsed["version"] == "0.1"
    assert len(parsed["panels"]) == 1
    assert parsed["panels"][0]["details"]["number"] == 42
