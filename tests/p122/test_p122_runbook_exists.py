from pathlib import Path


def test_p122_runbook_exists():
    p = Path("docs/ops/runbooks/execution_wiring_runbook_v1.md")
    assert p.exists(), "missing P122 execution wiring runbook"
