import json
from pathlib import Path


def test_shadow_spec_fixture_is_valid_json():
    p = Path("tests/fixtures/p6/shadow_spec_min.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "name" in data
