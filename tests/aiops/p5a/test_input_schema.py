from __future__ import annotations

import json
from pathlib import Path

from src.aiops.p5a.input_schema import validate_input


def test_fixture_valid() -> None:
    repo = Path(__file__).resolve().parents[3]
    p = repo / "tests" / "fixtures" / "p5a" / "input_min_v0.json"
    obj = json.loads(p.read_text(encoding="utf-8"))
    validate_input(obj)
