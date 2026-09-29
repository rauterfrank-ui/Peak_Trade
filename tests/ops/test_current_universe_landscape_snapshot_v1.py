"""Contract tests for CURRENT_UNIVERSE_LANDSCAPE_SNAPSHOT_V1 (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO / "config/governance/current_universe_landscape_snapshot_v1/source_v1.json"


def test_universe_landscape_snapshot_baseline_and_coverage() -> None:
    doc = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert doc["evidence_baseline_sha"] == "dfcf4d04b8400763bee6ab0b465fa182927dea75"
    assert doc["architecture_fixpoint"]["closure"] == "PROVEN_CURRENT"
    counts = doc["coverage_counts"]
    assert counts["unmapped_material_surface_count"] == 0
    assert counts["material_surface_count"] == len(doc["surfaces"])


def test_universe_landscape_snapshot_validator_exit_zero() -> None:
    proc = subprocess.run(
        [
            str(REPO / "scripts/pt"),
            "scripts/ops/validate_current_universe_landscape_snapshot_v1.py",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "UNIVERSE_LANDSCAPE_SNAPSHOT_OK" in proc.stdout
