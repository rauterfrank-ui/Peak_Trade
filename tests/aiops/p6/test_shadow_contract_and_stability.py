import json
from pathlib import Path


def test_shadow_spec_fixture_is_valid_json():
    p = Path("tests/fixtures/p6/shadow_spec_min.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "name" in data


def test_shadow_session_min_v0_fixture_has_required_fields():
    p = Path("tests/fixtures/p6/shadow_session_min_v0.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    for k in ["capsule_path", "p5a_input_path", "asof_utc"]:
        assert k in data
