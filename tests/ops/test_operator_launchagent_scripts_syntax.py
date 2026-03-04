import subprocess
from pathlib import Path


def test_launchagent_scripts_syntax():
    for p in [
        Path("scripts/ops/install_operator_all_launchagent.sh"),
        Path("scripts/ops/uninstall_operator_all_launchagent.sh"),
    ]:
        assert p.exists()
        subprocess.run(["bash", "-n", str(p)], check=True)
