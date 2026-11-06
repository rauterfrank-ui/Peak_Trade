from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
import tempfile


def test_validate_ok_and_fail() -> None:
    repo = Path(__file__).resolve().parents[3]
    gen = repo / "scripts" / "aiops" / "generate_evidence_pack.py"
    val = repo / "scripts" / "aiops" / "validate_evidence_pack.py"
    sample = repo / "tests" / "fixtures" / "p5b" / "sample_dir"
    assert gen.is_file()
    assert val.is_file()

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        sample_copy = base / "sample_dir"
        shutil.copytree(sample, sample_copy)
        out_root = base / "packs"
        out_root.mkdir(parents=True, exist_ok=True)

        p = subprocess.run(
            [
                sys.executable,
                str(gen),
                "--base-dir",
                str(base),
                "--in",
                str(sample_copy),
                "--pack-id",
                "fixed",
                "--out-root",
                str(out_root),
                "--deterministic",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        lines = [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]
        assert len(lines) == 2
        manifest = Path(lines[0])
        assert manifest.name == "manifest.json"

        ok = subprocess.run(
            [sys.executable, str(val), "--manifest", str(manifest)],
            capture_output=True,
            text=True,
        )
        assert ok.returncode == 0
        assert "VALIDATION_OK" in ok.stdout

        # Tamper source file and re-validate => fail
        (sample_copy / "a.txt").write_text("tamper\n", encoding="utf-8")
        bad = subprocess.run(
            [sys.executable, str(val), "--manifest", str(manifest)],
            capture_output=True,
            text=True,
        )
        assert bad.returncode == 2
        assert "VALIDATION_FAIL" in bad.stdout
