import subprocess


def test_mcp_smoke_preflight_bash_syntax():
    r = subprocess.run(
        ["bash", "-n", "scripts/ops/mcp_smoke_preflight.sh"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
