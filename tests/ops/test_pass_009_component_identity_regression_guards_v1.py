"""PASS_009 component identity comparison regression guards."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRESH = ROOT / "scripts/ops/peak_trade_v2_fresh_discovery_v1.py"


def _fresh():
    import sys

    spec = importlib.util.spec_from_file_location("peak_trade_v2_fresh_discovery_v1", FRESH)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def test_component_identity_hash_changes_when_module_identity_changes() -> None:
    mod = _fresh()
    base = [
        {
            "COMPONENT_ID": "src/a.py",
            "PATH": "src/a.py",
            "COMPONENT_CLASS": "UNKNOWN_CURRENT",
            "MODULE_OR_SYMBOL_IDENTITY": "a",
            "DISCOVERY_METHODS": ["FILESYSTEM"],
        }
    ]
    alt = [{**base[0], "MODULE_OR_SYMBOL_IDENTITY": "b"}]
    assert mod.component_identity_sha256(base) != mod.component_identity_sha256(alt)


def test_component_count_match_but_identity_change_is_nonzero_delta() -> None:
    mod = _fresh()
    rows_a = [
        {
            "COMPONENT_ID": f"src/m{i}.py",
            "PATH": f"src/m{i}.py",
            "COMPONENT_CLASS": "UNKNOWN_CURRENT",
            "MODULE_OR_SYMBOL_IDENTITY": f"m{i}",
            "DISCOVERY_METHODS": ["FILESYSTEM"],
        }
        for i in range(3)
    ]
    rows_b = list(rows_a)
    rows_b[1] = {**rows_b[1], "MODULE_OR_SYMBOL_IDENTITY": "changed"}
    assert len(rows_a) == len(rows_b)
    assert mod.component_identity_sha256(rows_a) != mod.component_identity_sha256(rows_b)
