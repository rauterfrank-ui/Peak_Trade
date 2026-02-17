from pathlib import Path


def test_p121_script_exists():
    p = Path("scripts/ops/p121_execution_wiring_proof_v1.sh")
    assert p.exists(), "missing P121 script"
