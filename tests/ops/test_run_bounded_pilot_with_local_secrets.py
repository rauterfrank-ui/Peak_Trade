"""Negative tests: Kraken local-secret bounded-pilot launcher is decommissioned."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "ops" / "run_bounded_pilot_with_local_secrets.py"


def test_kraken_bounded_pilot_secret_launcher_is_absent() -> None:
    """KRAKEN_BOUNDED_PILOT_SECRET_SUCCESS_PATH=false."""
    assert not SCRIPT.is_file()
    ops_scripts = {p.name for p in (ROOT / "scripts" / "ops").iterdir() if p.is_file()}
    assert "run_bounded_pilot_with_local_secrets.py" not in ops_scripts
