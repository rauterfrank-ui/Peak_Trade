from pathlib import Path


def test_p116_script_exists_and_is_executable():
    p = Path("scripts/ops/p116_execution_session_evidence_v1.sh")
    assert p.exists()
    assert p.stat().st_mode & 0o111
