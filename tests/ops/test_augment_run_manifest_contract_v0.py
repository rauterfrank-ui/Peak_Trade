"""Contract tests for ``scripts/ops/augment_run_manifest`` (v0).

Uses ``tmp_path`` only; no real ``out/l3`` or repo manifests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ops.augment_run_manifest import main


def test_run_manifest_missing_returns_zero_without_creating_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUT_DIR", str(tmp_path))
    monkeypatch.delenv("IMAGE", raising=False)
    monkeypatch.delenv("CACHE_DIR", raising=False)
    mf = tmp_path / "run_manifest.json"
    assert not mf.exists()

    assert main() == 0
    assert not mf.exists()


def test_run_manifest_minimal_json_gets_defaults_and_sorted_dump(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OUT_DIR", str(tmp_path))
    monkeypatch.delenv("IMAGE", raising=False)
    monkeypatch.delenv("CACHE_DIR", raising=False)
    mf = tmp_path / "run_manifest.json"
    mf.write_text(json.dumps({"existing": True}), encoding="utf-8")

    assert main() == 0

    expected = {
        "existing": True,
        "image": "peaktrade-l3:latest",
        "no_net": True,
        "repo_mode": "ro",
        "out_dir": str(tmp_path),
        "cache_dir": ".cache/l3",
    }
    body = mf.read_text(encoding="utf-8")
    assert json.loads(body) == expected
    assert body == json.dumps(expected, indent=2, sort_keys=True) + "\n"
