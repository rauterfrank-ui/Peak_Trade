from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_manifest_paths_are_base_dir_relative(tmp_path: Path) -> None:
    """Manifest stores base_dir relative to pack dir; relpaths are base_dir-relative."""
    base_dir = tmp_path / "out" / "ops"
    inp = base_dir / "prj_smoke" / "X"
    inp.mkdir(parents=True)
    f = inp / "summary.json"
    f.write_text('{"ok":true}', encoding="utf-8")

    out_root = base_dir / "evidence_packs"
    out_root.mkdir(parents=True)

    subprocess.check_call(
        [
            "python3",
            "scripts/aiops/generate_evidence_pack.py",
            "--base-dir",
            str(base_dir),
            "--in",
            str(inp),
            "--out-root",
            str(out_root),
        ],
        cwd=str(Path(__file__).resolve().parents[2]),
    )

    manifest = next(out_root.rglob("manifest.json"))
    data = json.loads(manifest.read_text(encoding="utf-8"))

    for item in data.get("files", []):
        p = item.get("relpath", "")
        assert p and not p.startswith("/")
        assert "home/runner" not in p
        assert "Peak_Trade/Peak_Trade" not in p

    meta = data.get("meta", {})
    base_dir_stored = meta.get("base_dir", "")
    assert base_dir_stored and not base_dir_stored.startswith("/")
    assert "home/runner" not in base_dir_stored

    subprocess.check_call(
        ["python3", "scripts/aiops/validate_evidence_pack.py", "--manifest", str(manifest)],
        cwd=str(Path(__file__).resolve().parents[2]),
    )
