from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_evidence_registry_hook_writes_manifest_and_index() -> None:
    root = Path.cwd()

    prereq = subprocess.run(
        [sys.executable, "scripts/wave4/aggregate_smoke_contracts.py"],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
        env={"PYTHONPATH": str(root)},
    )
    assert prereq.returncode == 0, prereq.stderr or prereq.stdout

    manifest = root / "out/ops/evidence_registry/manifest.json"
    index = root / "out/ops/evidence_registry/index.jsonl"

    if manifest.exists():
        manifest.unlink()

    before_lines = []
    if index.exists():
        before_lines = index.read_text(encoding="utf-8").splitlines()

    result = subprocess.run(
        [sys.executable, "scripts/wave6/write_evidence_registry_hook.py"],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
        env={"PYTHONPATH": str(root)},
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert manifest.exists()
    assert index.exists()

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["contract_version"] == "wave6.evidence.v1"
    assert payload["component"] == "evidence_registry_hook"
    assert payload["status"] == "SMOKE_OK"
    assert payload["source_component"] == "shared_smoke_summary"
    assert payload["source_contract_version"] == "wave4.summary.v1"

    after_lines = index.read_text(encoding="utf-8").splitlines()
    assert len(after_lines) == len(before_lines) + 1
    last = json.loads(after_lines[-1])
    assert last["component"] == "evidence_registry_hook"
    assert last["status"] == "SMOKE_OK"
