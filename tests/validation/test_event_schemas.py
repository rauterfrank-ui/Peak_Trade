from __future__ import annotations

from pathlib import Path

import pytest

from scripts.validate_events import validate_jsonl


def test_execution_events_fixture_validates() -> None:
    root = Path(__file__).resolve().parents[2]
    validate_jsonl(
        root / "tests/fixtures/events/execution_events.valid.jsonl",
        root / "schemas/events/execution_event.schema.json",
        strict=True,
    )


def test_ai_events_fixture_validates() -> None:
    root = Path(__file__).resolve().parents[2]
    validate_jsonl(
        root / "tests/fixtures/events/ai_events.valid.jsonl",
        root / "schemas/events/ai_event.schema.json",
        strict=True,
    )


def test_invalid_fixture_fails() -> None:
    root = Path(__file__).resolve().parents[2]
    with pytest.raises(Exception):
        validate_jsonl(
            root / "tests/fixtures/events/execution_events.invalid.jsonl",
            root / "schemas/events/execution_event.schema.json",
            strict=True,
        )
