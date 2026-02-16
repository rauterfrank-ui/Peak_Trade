from pathlib import Path

import os
import subprocess


def test_p72_shadowloop_pack_env_contract_bash_n() -> None:
    p = Path("scripts/ops/p72_shadowloop_pack_v1.sh")
    assert p.exists()
    subprocess.check_call(["bash", "-n", str(p)])


def test_p72_env_contract_resolves_override_vars(tmp_path: Path) -> None:
    p = Path("scripts/ops/p72_shadowloop_pack_v1.sh")
    assert p.exists()
    env = os.environ.copy()
    env["OUT_DIR_OVERRIDE"] = str(tmp_path / "out")
    env["RUN_ID_OVERRIDE"] = "p74_probe"
    env["MODE_OVERRIDE"] = "shadow"
    env["ITERATIONS_OVERRIDE"] = "1"
    env["INTERVAL_OVERRIDE"] = "0"
    env["P72_PROBE_ONLY"] = "1"
    result = subprocess.run(
        ["bash", str(p)],
        env=env,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    assert "P72_PROBE_OK" in result.stdout
    assert "out_dir=" in result.stdout
    assert (tmp_path / "out").exists()


def test_p72_env_contract_resolves_legacy_vars(tmp_path: Path) -> None:
    """Legacy OUT_DIR (no _OVERRIDE) should work as fallback."""
    p = Path("scripts/ops/p72_shadowloop_pack_v1.sh")
    assert p.exists()
    env = os.environ.copy()
    env["OUT_DIR"] = str(tmp_path / "legacy_out")
    env["RUN_ID"] = "p74_legacy"
    env["MODE"] = "shadow"
    env["P72_PROBE_ONLY"] = "1"
    result = subprocess.run(
        ["bash", str(p)],
        env=env,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )
    assert result.returncode == 0
    assert "P72_PROBE_OK" in result.stdout
    assert (tmp_path / "legacy_out").exists()
