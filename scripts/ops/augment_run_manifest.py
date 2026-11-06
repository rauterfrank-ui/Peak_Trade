"""Augment out/l3/run_manifest.json with container-run metadata (image, no_net, repo_mode, etc.)."""

from __future__ import annotations

import json
import os
from pathlib import Path


def main() -> int:
    out_dir = Path(os.environ.get("OUT_DIR", "out/l3"))
    mf = out_dir / "run_manifest.json"
    if not mf.exists():
        return 0
    data = json.loads(mf.read_text())
    data.setdefault("image", os.environ.get("IMAGE", "peaktrade-l3:latest"))
    data.setdefault("no_net", True)
    data.setdefault("repo_mode", "ro")
    data.setdefault("out_dir", str(out_dir))
    data.setdefault("cache_dir", os.environ.get("CACHE_DIR", ".cache/l3"))
    mf.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
