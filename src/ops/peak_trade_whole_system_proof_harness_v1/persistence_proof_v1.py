"""Persistence proof scenarios (isolated temp roots only — no productive mutation)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any


def describe_persistence_proof_v1() -> dict[str, Any]:
    """Documents harness capability; safe temp-root scenarios for CI self-test."""
    return {
        "SCENARIOS_SUPPORTED": [
            "COLD_START",
            "RESTART",
            "REPEATED_INITIALIZATION",
            "PARTIAL_STATE",
            "CORRUPT_STATE",
            "SCHEMA_MISMATCH",
            "READ_AFTER_WRITE",
        ],
        "PRODUCTIVE_STATE_MUTATION": False,
        "TEMP_ROOT_POLICY": "tempfile.TemporaryDirectory only",
        "OWNER_MODULES": [
            "src/ops/single_selected_future_policy_v1/persistence_v1.py",
            "src/ops/paper_shadow_bounded_orchestrator_v1/run_evidence_v1.py",
        ],
    }


def run_temp_root_smoke_v1() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="pt_wsph_persist_") as tmp:
        root = Path(tmp)
        marker = root / "cold_start.marker"
        marker.write_text("1", encoding="utf-8")
        restart_read = marker.read_text(encoding="utf-8")
        return {
            "COLD_START": marker.is_file(),
            "RESTART_READ": restart_read == "1",
            "TEMP_ROOT": str(root),
            "PRODUCTIVE_ROOT_TOUCHED": False,
        }
