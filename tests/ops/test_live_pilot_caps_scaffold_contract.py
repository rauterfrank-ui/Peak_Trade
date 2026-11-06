from pathlib import Path


def test_caps_scaffold_present():
    p = Path("config/ops/live_pilot_caps.toml")
    assert p.exists()
    t = p.read_text(encoding="utf-8")
    assert "max_notional_per_order" in t
    assert "kill_switch_required" in t
