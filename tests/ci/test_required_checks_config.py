"""Tests for shared required checks config semantics."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts" / "ci"))
from required_checks_config import load_effective_required_contexts, load_required_checks_config


def test_load_effective_required_contexts_filters_ignored_and_whitespace(tmp_path: Path) -> None:
    cfg = tmp_path / "required_status_checks.json"
    cfg.write_text(
        """
{
  "required_contexts": ["  A  ", "B", "", "C"],
  "ignored_contexts": ["B", "  "]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    assert load_effective_required_contexts(cfg) == ["A", "C"]


def test_load_effective_required_contexts_rejects_non_list_fields(tmp_path: Path) -> None:
    cfg = tmp_path / "required_status_checks.json"
    cfg.write_text(
        '{"required_contexts": "A", "ignored_contexts": []}\n',
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="required_contexts must be a list"):
        load_effective_required_contexts(cfg)


def test_load_effective_required_contexts_rejects_non_json_config(tmp_path: Path) -> None:
    cfg = tmp_path / "required_status_checks.txt"
    cfg.write_text("legacy-line-based-format-is-not-supported\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_effective_required_contexts(cfg)


def test_load_required_checks_config_returns_canonical_semantics(tmp_path: Path) -> None:
    cfg = tmp_path / "required_status_checks.json"
    cfg.write_text(
        """
{
  "required_contexts": ["strategy-smoke", "tests (3.11)", "strategy-smoke"],
  "ignored_contexts": ["strategy-smoke"]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    semantics = load_required_checks_config(cfg)
    assert semantics["required_contexts"] == ["strategy-smoke", "tests (3.11)", "strategy-smoke"]
    assert semantics["ignored_contexts"] == ["strategy-smoke"]
    assert semantics["effective_required_contexts"] == ["tests (3.11)"]
