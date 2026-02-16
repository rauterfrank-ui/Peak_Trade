from pathlib import Path
import subprocess


def test_final_done_pin_v1_exists_and_syntax_ok():
    p = Path("scripts/ops/final_done_pin_v1.sh")
    assert p.exists()
    assert p.stat().st_mode & 0o111, "script must be executable"
    subprocess.check_call(["bash", "-n", str(p)])
