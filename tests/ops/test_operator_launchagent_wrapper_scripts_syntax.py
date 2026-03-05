import subprocess
from pathlib import Path


def test_wrapper_scripts_syntax():
    for p in [
        Path("scripts/ops/install_operator_all_launchagent_full.sh"),
        Path("scripts/ops/install_operator_all_launchagent_registry_only.sh"),
    ]:
        assert p.exists()
        subprocess.run(["bash", "-n", str(p)], check=True)
