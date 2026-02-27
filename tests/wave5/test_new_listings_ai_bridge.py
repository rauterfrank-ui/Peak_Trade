from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_new_listings_ai_bridge_builds_contract_artifact() -> None:
    root = Path.cwd()
    out_file = root / "out/ops/new_listings_ai_bridge/new_listings_ai_bridge.json"
    if out_file.exists():
        out_file.unlink()

    result = subprocess.run(
        [sys.executable, "scripts/wave5/new_listings_to_ai_bridge.py"],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
        env={"PYTHONPATH": str(root)},
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert out_file.exists()

    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["contract_version"] == "wave5.bridge.v1"
    assert payload["status"] == "SMOKE_OK"
    assert payload["component"] == "new_listings_ai_bridge"
    assert payload["source_component"] == "new_listings"
    assert payload["listing_count"] == 2
    assert payload["top_symbol"] == "ABCUSDT"
    assert payload["policy_view"]["mode"] == "paper_only"
    assert payload["switch_view"]["regime"] in {"neutral", "volatile"}
