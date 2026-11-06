"""Contract tests for OKX multi-window foundation v1."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from src.ops.okx_multi_window_foundation_v1.config_v1 import (
    SCHEMA_VERSION,
    default_config_dict,
    load_config,
)
from src.ops.okx_multi_window_foundation_v1.launcher_v1 import LauncherStop, run_launch
from src.ops.okx_multi_window_foundation_v1.safari_v1 import SafariWindow
from src.ops.okx_multi_window_foundation_v1.validate_v1 import (
    validate_slot_url,
    validate_url_bindings,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/ops/okx_multi_window_foundation_v1/foundation_v1.json"

_NEUTRAL = "favorites://"


def _slot(id_: int) -> SafariWindow:
    return SafariWindow(id_, 1, "Startseite", _NEUTRAL)


def test_default_config_on_disk_matches_schema() -> None:
    data = load_config(DEFAULT_CONFIG)
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["workstation"]["required_tab_count"] == 7
    for key in ("SLOT_1_URL", "SLOT_2_URL", "SLOT_3_URL", "SLOT_4_URL"):
        assert key in data["url_bindings"]
        assert data["url_bindings"][key] == ""


def test_validate_slot_url_cases() -> None:
    assert validate_slot_url("")[0] is True
    assert validate_slot_url("https://example.com/path")[0] is True
    assert validate_slot_url("about:blank")[0] is True
    assert validate_slot_url("not-a-url")[0] is False
    assert validate_slot_url("javascript:alert(1)")[0] is False


def test_validate_url_bindings_rejects_invalid() -> None:
    bindings = default_config_dict()["url_bindings"]
    bindings = copy.deepcopy(bindings)
    bindings["SLOT_2_URL"] = "ftp://example.com"
    ok, errors = validate_url_bindings(bindings)
    assert ok is False
    assert any("SLOT_2_URL" in e for e in errors)


def _windows_fixture() -> list[SafariWindow]:
    return [
        SafariWindow(1342, 7, "PEAK TRADE – OKX WORKSTATION — spot", "https://my.okx.com/de"),
        _slot(3192),
        _slot(3194),
        _slot(3196),
        _slot(3198),
    ]


def test_launch_idempotent_no_create() -> None:
    config = default_config_dict()
    windows = _windows_fixture()

    def probe() -> list[SafariWindow]:
        return list(windows)

    def create() -> int:
        raise AssertionError("must not create")

    r1 = run_launch(config, probe=probe, create_window=create)
    assert r1.status == "PASS"
    assert r1.windows_created == 0
    assert r1.slot_window_ids == {
        "SLOT_1": 3192,
        "SLOT_2": 3194,
        "SLOT_3": 3196,
        "SLOT_4": 3198,
    }

    r2 = run_launch(config, probe=probe, create_window=create)
    assert r2.status == "PASS"
    assert r2.windows_created == 0
    assert r2.slot_window_ids == r1.slot_window_ids


def test_launch_does_not_create_when_four_neutral_slots_exist() -> None:
    config = default_config_dict()
    windows = _windows_fixture()

    def create() -> int:
        raise AssertionError("must not create when 4 neutral slots exist")

    result = run_launch(config, probe=lambda: windows, create_window=create)
    assert result.windows_created == 0


def test_launch_creates_missing_slots_once() -> None:
    config = default_config_dict()
    state = {
        "windows": [
            SafariWindow(1342, 7, "PEAK TRADE – OKX WORKSTATION — spot", "https://my.okx.com/de"),
            _slot(5001),
        ]
    }
    next_id = 6000

    def probe() -> list[SafariWindow]:
        return list(state["windows"])

    def create() -> int:
        nonlocal next_id
        wid = next_id
        next_id += 1
        state["windows"].append(_slot(wid))
        return wid

    r1 = run_launch(config, probe=probe, create_window=create)
    assert r1.status == "PASS"
    assert r1.windows_created == 3
    assert len({*r1.slot_window_ids.values()}) == 4

    r2 = run_launch(config, probe=probe, create_window=create)
    assert r2.windows_created == 0


def test_launch_stops_on_ambiguous_workstation() -> None:
    config = default_config_dict()
    windows = [
        SafariWindow(1, 7, "PEAK TRADE – OKX WORKSTATION — a", "https://a"),
        SafariWindow(2, 7, "PEAK TRADE – OKX WORKSTATION — b", "https://b"),
    ]

    with pytest.raises(LauncherStop, match="workstation_ambiguous"):
        run_launch(config, probe=lambda: windows, create_window=lambda: 999)


def test_launch_stops_on_extra_unbound_slot_windows() -> None:
    config = default_config_dict()
    windows = _windows_fixture() + [_slot(9999), _slot(9998)]

    with pytest.raises(LauncherStop, match="slot_identity_ambiguous"):
        run_launch(config, probe=lambda: windows, create_window=lambda: 10000)


def test_launch_ignores_extra_slots_when_registry_bound() -> None:
    config = default_config_dict()
    config["registry"]["slot_window_ids"] = {
        "SLOT_1": 3192,
        "SLOT_2": 3194,
        "SLOT_3": 3196,
        "SLOT_4": 3198,
    }
    config["registry"]["slot_fingerprints"] = {
        slot: f"Startseite|1|{_NEUTRAL}" for slot in ("SLOT_1", "SLOT_2", "SLOT_3", "SLOT_4")
    }
    windows = _windows_fixture() + [_slot(9999)]

    result = run_launch(config, probe=lambda: windows, create_window=lambda: 10000)
    assert result.status == "PASS"
    assert result.windows_created == 0
