"""
L3 Trade Plan Advisory Runner: smoke tests.

- Pointer-only input accepted; raw payload refused.
- Deterministic output envelope + artifacts list (no raw).
- Tooling enforced as files only.
"""

from pathlib import Path

import pytest

from src.ai_orchestration.l3_contracts import accepts_l3_pointer_only_input
from src.ai_orchestration.l3_runner import (
    L3PointerOnlyViolation,
    L3Runner,
    L3RunResult,
    L3ToolingViolation,
)


def _pointer_only_input():
    return {
        "run_id": "r1",
        "ts_ms": 0,
        "counts": {},
        "facts": {},
        "artifacts": [{"path": "docs/outlook.md", "sha256": "a" * 64}],
    }


class TestL3RunnerSmoke:
    """Smoke tests for L3Runner scaffold."""

    def test_run_accepts_pointer_only_input(self, tmp_path):
        """Run with pointer-only input returns result with artifacts list (no raw)."""
        runner = L3Runner()
        inputs = _pointer_only_input()
        result = runner.run(inputs=inputs, mode="dry-run", out_dir=tmp_path)
        assert isinstance(result, L3RunResult)
        assert result.layer_id == "L3"
        assert result.run_id.startswith("L3-")
        assert result.evidence_pack_id.startswith("EVP-L3-")
        assert result.sod_result in ("PASS", "FAIL")
        assert isinstance(result.artifacts, list)
        assert all(isinstance(p, str) for p in result.artifacts)
        assert any("run_manifest.json" in p for p in result.artifacts)
        assert any("operator_output.md" in p for p in result.artifacts)
        assert "pointer-only" in result.summary or "Artifacts" in result.summary

    def test_run_refuses_non_pointer_only_input(self, tmp_path):
        """Run with payload key raises L3PointerOnlyViolation."""
        runner = L3Runner()
        inputs = {**_pointer_only_input(), "payload": "raw content"}
        with pytest.raises(L3PointerOnlyViolation):
            runner.run(inputs=inputs, mode="dry-run", out_dir=tmp_path)

    def test_run_refuses_transcript_key(self, tmp_path):
        """Run with transcript key raises L3PointerOnlyViolation."""
        runner = L3Runner()
        inputs = {**_pointer_only_input(), "transcript": "full convo"}
        with pytest.raises(L3PointerOnlyViolation):
            runner.run(inputs=inputs, mode="dry-run", out_dir=tmp_path)

    def test_artifacts_are_paths_only(self, tmp_path):
        """Result artifacts are path strings only (no raw content in envelope)."""
        runner = L3Runner()
        result = runner.run(inputs=_pointer_only_input(), mode="dry-run", out_dir=tmp_path)
        for p in result.artifacts:
            assert isinstance(p, str)
            assert "path" in p.lower() or p.endswith(".json") or p.endswith(".md")

    def test_deterministic_run_id_same_inputs(self, tmp_path):
        """Same inputs + fixed clock produce same run_id."""
        from datetime import datetime, timezone

        clock = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)
        runner_a = L3Runner(clock=clock)
        runner_b = L3Runner(clock=clock)
        inputs = _pointer_only_input()
        result_a = runner_a.run(inputs=inputs, mode="dry-run", out_dir=tmp_path / "a")
        result_b = runner_b.run(inputs=inputs, mode="dry-run", out_dir=tmp_path / "b")
        assert result_a.run_id == result_b.run_id
        assert result_a.evidence_pack_id == result_b.evidence_pack_id
