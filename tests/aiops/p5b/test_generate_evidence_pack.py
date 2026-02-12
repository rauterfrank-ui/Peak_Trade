from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


def test_pack_generation_deterministic() -> None:
    repo = Path(__file__).resolve().parents[3]
    cli = repo / "scripts" / "aiops" / "generate_evidence_pack.py"
    base = repo
    sample = repo / "tests" / "fixtures" / "p5b" / "sample_dir"
    assert cli.is_file()
    assert sample.is_dir()

    with tempfile.TemporaryDirectory() as td:
        out_root = Path(td) / "packs"
        out_root.mkdir(parents=True, exist_ok=True)

        def run():
            p = subprocess.run(
                [
                    sys.executable,
                    str(cli),
                    "--base-dir",
                    str(base),
                    "--in",
                    str(sample),
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
            m = json.loads(Path(lines[0]).read_text(encoding="utf-8"))
            idx = json.loads(Path(lines[1]).read_text(encoding="utf-8"))
            return m, idx

        m1, i1 = run()
        m2, i2 = run()

        assert m1 == m2
        assert i1 == i2
        assert m1["meta"]["kind"] == "evidence_pack"
        assert len(m1["files"]) == 2
