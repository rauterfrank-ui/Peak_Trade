from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def test_update_index(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[3]
    gen = repo / "scripts" / "aiops" / "generate_evidence_pack.py"
    upd = repo / "scripts" / "aiops" / "update_evidence_index.py"
    base = repo
    sample = repo / "tests" / "fixtures" / "p5b" / "sample_dir"
    assert gen.is_file()
    assert upd.is_file()

    out_root = tmp_path / "packs"
    out_root.mkdir(parents=True, exist_ok=True)

    # create two packs (deterministic for stable ordering)
    subprocess.run(
        [
            sys.executable,
            str(gen),
            "--base-dir",
            str(base),
            "--in",
            str(sample),
            "--pack-id",
            "a",
            "--out-root",
            str(out_root),
            "--deterministic",
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(gen),
            "--base-dir",
            str(base),
            "--in",
            str(sample),
            "--pack-id",
            "b",
            "--out-root",
            str(out_root),
            "--deterministic",
        ],
        check=True,
        capture_output=True,
    )

    out_index = tmp_path / "index_all.json"
    subprocess.run(
        [
            sys.executable,
            str(upd),
            "--root",
            str(out_root),
            "--out",
            str(out_index),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert out_index.is_file()

    data = json.loads(out_index.read_text(encoding="utf-8"))
    assert data["count"] == 2
    assert len(data["packs"]) == 2
    # stable sort: created_at equal (deterministic), then pack_id reverse => b before a
    assert data["packs"][0]["pack_id"].endswith("b")
