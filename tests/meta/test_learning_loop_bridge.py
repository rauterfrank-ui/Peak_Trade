"""Tests für ``src.meta.learning_loop.bridge.normalize_patches`` (ohne I/O)."""

from __future__ import annotations

import pytest

from src.meta.learning_loop.bridge import normalize_patches


def test_normalize_patches_single_mapping_uses_value_alias() -> None:
    raw = {"target": "portfolio.leverage", "value": 1.5, "reason": "smoke"}
    out = normalize_patches(raw)
    assert out == [
        {"target": "portfolio.leverage", "new_value": 1.5, "reason": "smoke"},
    ]


def test_normalize_patches_wraps_patches_key_and_skips_invalid() -> None:
    raw = {
        "patches": [
            {"target": "a.b", "new_value": 1},
            {"target": "", "new_value": 2},
            {"oops": "no-target"},
            {"target": "c.d", "new_value": {"nested": 1}},
        ],
    }
    out = normalize_patches(raw)
    assert out == [{"target": "a.b", "new_value": 1}]


def test_normalize_patches_sequence() -> None:
    raw = [
        {"target": "x.y", "new_value": True},
    ]
    assert normalize_patches(raw) == [{"target": "x.y", "new_value": True}]


def test_normalize_patches_rejects_wrong_type() -> None:
    with pytest.raises(TypeError):
        normalize_patches("not-a-mapping")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        normalize_patches(42)  # type: ignore[arg-type]
