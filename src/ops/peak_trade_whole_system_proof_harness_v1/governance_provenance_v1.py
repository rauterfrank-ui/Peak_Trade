"""Governance / provenance normalization for proof manifest."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.peak_trade_whole_system_proof_harness_v1.baseline_v1 import capture_baseline_v1


def build_governance_provenance_v1(repo: Path) -> dict[str, Any]:
    baseline = capture_baseline_v1(repo)
    deps = [
        {
            "DEPENDENCY": "origin/main SHA pin",
            "CLASSIFICATION": "GOVERNANCE_REQUIRED",
            "EVIDENCE": baseline.get("ORIGIN_MAIN_SHA"),
        },
        {
            "DEPENDENCY": "Master Runbook",
            "CLASSIFICATION": "NAVIGATION_ONLY",
            "PATH": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        },
        {
            "DEPENDENCY": "Map of Truth",
            "CLASSIFICATION": "NAVIGATION_ONLY",
            "PATH": "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md",
        },
        {
            "DEPENDENCY": "CI required checks",
            "CLASSIFICATION": "CI_ONLY",
            "PATH": "config/ci/required_status_checks.json",
        },
        {
            "DEPENDENCY": "Python runtime contract",
            "CLASSIFICATION": "START_PRECONDITION_REQUIRED",
            "PATH": "docs/runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md",
        },
    ]
    return {
        "BASELINE": baseline,
        "GOVERNANCE_DEPENDENCIES": deps,
        "PROVENANCE_AUTHORITY": "NONE",
    }
