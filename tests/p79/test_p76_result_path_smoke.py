from pathlib import Path


def test_p79_gate_uses_p76_subdir_path() -> None:
    """P79 health gate must accept P76 artifacts in tick/p76/ (P86 gate layout)."""
    p = Path("scripts/ops/p79_supervisor_health_gate_v1.sh")
    assert p.exists()
    s = p.read_text(encoding="utf-8")
    assert "p76/P76_RESULT.txt" in s
