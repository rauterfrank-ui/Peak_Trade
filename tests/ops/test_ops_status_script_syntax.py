import subprocess


def test_ops_status_bash_syntax():
    r = subprocess.run(["bash", "-n", "scripts/ops/ops_status.sh"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
