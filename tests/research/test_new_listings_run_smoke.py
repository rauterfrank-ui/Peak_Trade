from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_new_listings_run_help_smoke() -> None:
    """Verify run --help works."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.research.new_listings",
            "run",
            "--help",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "--config" in result.stdout


def test_new_listings_run_smoke(tmp_path: Path) -> None:
    """Run full pipeline with config fixture; verify output."""
    config_path = Path("tests/fixtures/research/new_listings/config.json")
    assert config_path.exists(), f"config fixture missing: {config_path}"

    out_dir = tmp_path / "new_listings_out"
    db_path = tmp_path / "nl.sqlite"
    events_path = tmp_path / "events.jsonl"

    cmd = [
        sys.executable,
        "-m",
        "src.research.new_listings",
        "run",
        "--config",
        str(config_path),
        "--out-dir",
        str(out_dir),
        "--db",
        str(db_path),
        "--events",
        str(events_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"
    out = json.loads(result.stdout)
    assert out.get("ok") is True
    assert "run_id" in out
    assert "manifest_path" in out

    manifest_path = Path(out["manifest_path"])
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("ok") is True
    assert "outputs" in manifest
