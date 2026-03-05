from pathlib import Path


def test_runbook_exists():
    p = Path("docs/ops/runbooks/live_pilot_execution_plan.md")
    assert p.exists()
    t = p.read_text(encoding="utf-8")
    assert "Live Pilot Execution Plan" in t
    assert "PT_LIVE_ENABLED" in t
    assert "PT_LIVE_ARMED" in t
