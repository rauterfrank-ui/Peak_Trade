"""
L4 Critic Replay: Validator Report Normalization Determinism (Option C)

Contract: Running the normalizer twice on the same input (with or without
varying runtime context such as --timestamp, --run-id) must produce
byte-identical validator_report.normalized.json (canonical output).

This ensures downstream consumers (e.g. aiops-trend-seed-from-normalized-report)
can rely on deterministic artifacts from the L4 Critic Replay Determinism workflow.

Reference:
- docs/governance/ai_autonomy/PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md
- .github/workflows/l4_critic_replay_determinism_v2.yml
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_SCRIPT = REPO_ROOT / "scripts" / "aiops" / "normalize_validator_report.py"
FIXTURE_LEGACY = REPO_ROOT / "tests" / "fixtures" / "validator_reports" / "legacy_report_pass.json"
FIXTURE_GOLDEN = (
    REPO_ROOT / "tests" / "fixtures" / "validator_reports" / "normalized_report_pass.golden.json"
)


def _run_normalize(
    input_path: Path,
    out_dir: Path,
    *extra_args: str,
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(CLI_SCRIPT),
        "--input",
        str(input_path),
        "--out-dir",
        str(out_dir),
        *extra_args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))


# =============================================================================
# Determinism: same input, different runtime context → same canonical JSON
# =============================================================================


def test_normalizer_determinism_same_input_no_context(tmp_path: Path) -> None:
    """Run normalizer twice with same input, no runtime context; outputs must be byte-identical."""
    assert FIXTURE_LEGACY.exists(), f"Fixture missing: {FIXTURE_LEGACY}"

    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    for out_dir in (out1, out2):
        r = _run_normalize(FIXTURE_LEGACY, out_dir)
        assert r.returncode == 0, (r.stdout, r.stderr)

    json1 = (out1 / "validator_report.normalized.json").read_bytes()
    json2 = (out2 / "validator_report.normalized.json").read_bytes()
    assert json1 == json2, "Normalized JSON must be byte-identical across runs (no context)"


def test_normalizer_determinism_same_input_with_timestamp(tmp_path: Path) -> None:
    """Run normalizer twice with --timestamp (different generated_at_utc); canonical JSON must still match."""
    assert FIXTURE_LEGACY.exists(), f"Fixture missing: {FIXTURE_LEGACY}"

    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    for i, out_dir in enumerate((out1, out2)):
        r = _run_normalize(
            FIXTURE_LEGACY,
            out_dir,
            "--git-sha",
            "abc123",
            "--run-id",
            f"run_{i}",
            "--workflow",
            "L4 Critic Replay Determinism",
            "--job",
            "l4_critic_replay_determinism",
            "--timestamp",
        )
        assert r.returncode == 0, (r.stdout, r.stderr)

    json1 = (out1 / "validator_report.normalized.json").read_bytes()
    json2 = (out2 / "validator_report.normalized.json").read_bytes()
    assert json1 == json2, (
        "Normalized JSON must be byte-identical even with different --timestamp/run-id (canonical excludes runtime_context)"
    )


def test_normalizer_canonical_json_excludes_runtime_context(tmp_path: Path) -> None:
    """Written validator_report.normalized.json must not contain runtime_context (deterministic mode)."""
    assert FIXTURE_LEGACY.exists(), f"Fixture missing: {FIXTURE_LEGACY}"

    out_dir = tmp_path / "out"
    r = _run_normalize(
        FIXTURE_LEGACY,
        out_dir,
        "--git-sha",
        "sha",
        "--run-id",
        "123",
        "--timestamp",
    )
    assert r.returncode == 0, (r.stdout, r.stderr)

    data = json.loads((out_dir / "validator_report.normalized.json").read_text(encoding="utf-8"))
    assert "runtime_context" not in data, (
        "Canonical JSON must exclude runtime_context for determinism"
    )


# =============================================================================
# Snapshot / golden contract
# =============================================================================


def test_normalizer_output_matches_golden(tmp_path: Path) -> None:
    """Normalizing the legacy fixture must produce JSON that matches the golden canonical snapshot."""
    assert FIXTURE_LEGACY.exists(), f"Fixture missing: {FIXTURE_LEGACY}"
    assert FIXTURE_GOLDEN.exists(), f"Golden missing: {FIXTURE_GOLDEN}"

    out_dir = tmp_path / "out"
    r = _run_normalize(FIXTURE_LEGACY, out_dir)
    assert r.returncode == 0, (r.stdout, r.stderr)

    produced = (out_dir / "validator_report.normalized.json").read_text(encoding="utf-8")
    golden = FIXTURE_GOLDEN.read_text(encoding="utf-8")

    # Compare as parsed JSON to ignore formatting differences (e.g. trailing newline)
    produced_data = json.loads(produced)
    golden_data = json.loads(golden)
    assert produced_data == golden_data, (
        "Normalized output must match golden snapshot (deterministic contract)"
    )
