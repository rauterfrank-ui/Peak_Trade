"""
Tests for L4 Critic Determinism (Phase 4C)

Tests deterministic replay behavior:
- critic_report.json byte-identical on repeated runs
- critic_summary.md stable derivation from JSON
- Snapshot-based CI gate validation

Reference:
- docs/governance/ai_autonomy/PHASE4C_CRITIC_HARDENING.md
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.ai_orchestration.l4_critic import L4Critic


class TestL4CriticDeterminism:
    """Test L4 Critic deterministic replay behavior."""

    @pytest.fixture
    def evidence_pack_path(self) -> Path:
        """Path to sample evidence pack."""
        return Path("tests/fixtures/evidence_packs/L1_sample_2026-01-10")

    @pytest.fixture
    def transcript_path(self) -> Path:
        """Path to sample transcript."""
        return Path("tests/fixtures/transcripts/l4_critic_sample.json")

    @pytest.fixture
    def snapshot_dir(self) -> Path:
        """Path to snapshot directory."""
        return Path(
            "tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0"
        )

    @pytest.fixture
    def fixed_clock(self) -> datetime:
        """Fixed clock for determinism."""
        return datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)

    def test_critic_report_json_determinism(
        self,
        evidence_pack_path: Path,
        transcript_path: Path,
        snapshot_dir: Path,
        fixed_clock: datetime,
    ):
        """Test that critic_report.json is byte-identical on repeated runs."""
        with TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "run1"
            out_dir.mkdir(parents=True)

            # Run 1
            runner = L4Critic(clock=fixed_clock, schema_version="1.0.0")
            result = runner.run(
                evidence_pack_path=evidence_pack_path,
                mode="replay",
                transcript_path=transcript_path,
                out_dir=out_dir,
                pack_id="L1_sample_2026-01-10",
                deterministic=True,
                fixture="l4_critic_sample",
            )

            # Verify outputs exist
            report_json = out_dir / "critic_report.json"
            summary_md = out_dir / "critic_summary.md"
            assert report_json.exists(), "critic_report.json not generated"
            assert summary_md.exists(), "critic_summary.md not generated"

            # Load JSON
            with open(report_json) as f:
                report_data = json.load(f)

            # Validate schema
            assert report_data["schema_version"] == "1.0.0"
            assert report_data["pack_id"] == "L1_sample_2026-01-10"
            assert report_data["mode"] == "replay"
            assert report_data["meta"]["deterministic"] is True
            assert report_data["meta"]["created_at"] is None  # No timestamp in deterministic mode
            assert report_data["inputs"]["fixture"] == "l4_critic_sample"

            # Validate findings structure
            assert "findings" in report_data
            assert len(report_data["findings"]) > 0
            for finding in report_data["findings"]:
                assert "id" in finding
                assert "title" in finding
                assert "severity" in finding
                assert "status" in finding
                assert "rationale" in finding

            # Run 2 (identical conditions)
            out_dir2 = Path(tmpdir) / "run2"
            out_dir2.mkdir(parents=True)

            runner2 = L4Critic(clock=fixed_clock, schema_version="1.0.0")
            result2 = runner2.run(
                evidence_pack_path=evidence_pack_path,
                mode="replay",
                transcript_path=transcript_path,
                out_dir=out_dir2,
                pack_id="L1_sample_2026-01-10",
                deterministic=True,
                fixture="l4_critic_sample",
            )

            report_json2 = out_dir2 / "critic_report.json"

            # Byte-identical check
            with open(report_json, "rb") as f1, open(report_json2, "rb") as f2:
                bytes1 = f1.read()
                bytes2 = f2.read()
                assert bytes1 == bytes2, "critic_report.json not deterministic (bytes differ)"

    def test_critic_report_snapshot_match(
        self,
        evidence_pack_path: Path,
        transcript_path: Path,
        snapshot_dir: Path,
        fixed_clock: datetime,
    ):
        """Test that critic_report.json matches snapshot."""
        if not snapshot_dir.exists():
            pytest.skip(f"Snapshot directory not found: {snapshot_dir}")

        with TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "run"
            out_dir.mkdir(parents=True)

            # Run critic
            runner = L4Critic(clock=fixed_clock, schema_version="1.0.0")
            result = runner.run(
                evidence_pack_path=evidence_pack_path,
                mode="replay",
                transcript_path=transcript_path,
                out_dir=out_dir,
                pack_id="L1_sample_2026-01-10",
                deterministic=True,
                fixture="l4_critic_sample",
            )

            # Load actual output
            report_json = out_dir / "critic_report.json"
            with open(report_json) as f:
                actual_data = json.load(f)

            # Load snapshot
            snapshot_json = snapshot_dir / "critic_report.json"
            with open(snapshot_json) as f:
                expected_data = json.load(f)

            # Deep compare (semantic)
            assert actual_data == expected_data, (
                "critic_report.json differs from snapshot. "
                f"Run 'diff {report_json} {snapshot_json}' to see differences."
            )

    def test_critic_summary_md_snapshot_match(
        self,
        evidence_pack_path: Path,
        transcript_path: Path,
        snapshot_dir: Path,
        fixed_clock: datetime,
    ):
        """Test that critic_summary.md matches snapshot."""
        if not snapshot_dir.exists():
            pytest.skip(f"Snapshot directory not found: {snapshot_dir}")

        with TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "run"
            out_dir.mkdir(parents=True)

            # Run critic
            runner = L4Critic(clock=fixed_clock, schema_version="1.0.0")
            result = runner.run(
                evidence_pack_path=evidence_pack_path,
                mode="replay",
                transcript_path=transcript_path,
                out_dir=out_dir,
                pack_id="L1_sample_2026-01-10",
                deterministic=True,
                fixture="l4_critic_sample",
            )

            # Load actual output
            summary_md = out_dir / "critic_summary.md"
            with open(summary_md) as f:
                actual_content = f.read()

            # Load snapshot
            snapshot_md = snapshot_dir / "critic_summary.md"
            with open(snapshot_md) as f:
                expected_content = f.read()

            # Text compare
            assert actual_content == expected_content, (
                "critic_summary.md differs from snapshot. "
                f"Run 'diff {summary_md} {snapshot_md}' to see differences."
            )

    def test_sorted_findings_by_severity(
        self,
        evidence_pack_path: Path,
        transcript_path: Path,
        fixed_clock: datetime,
    ):
        """Test that findings are sorted by severity (HIGH > MEDIUM > LOW > INFO)."""
        with TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "run"
            out_dir.mkdir(parents=True)

            runner = L4Critic(clock=fixed_clock, schema_version="1.0.0")
            result = runner.run(
                evidence_pack_path=evidence_pack_path,
                mode="replay",
                transcript_path=transcript_path,
                out_dir=out_dir,
                pack_id="L1_sample_2026-01-10",
                deterministic=True,
                fixture="l4_critic_sample",
            )

            # Load report
            report_json = out_dir / "critic_report.json"
            with open(report_json) as f:
                report_data = json.load(f)

            # Check sorting
            findings = report_data["findings"]
            severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}

            for i in range(len(findings) - 1):
                current_severity = findings[i]["severity"]
                next_severity = findings[i + 1]["severity"]

                current_rank = severity_order.get(current_severity, 99)
                next_rank = severity_order.get(next_severity, 99)

                assert current_rank <= next_rank, (
                    f"Findings not sorted by severity: {current_severity} before {next_severity}"
                )

    def test_normalized_paths_in_deterministic_mode(
        self,
        evidence_pack_path: Path,
        transcript_path: Path,
        fixed_clock: datetime,
    ):
        """Test that paths are normalized (repo-relative) in deterministic mode."""
        with TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "run"
            out_dir.mkdir(parents=True)

            runner = L4Critic(clock=fixed_clock, schema_version="1.0.0")
            result = runner.run(
                evidence_pack_path=evidence_pack_path,
                mode="replay",
                transcript_path=transcript_path,
                out_dir=out_dir,
                pack_id="L1_sample_2026-01-10",
                deterministic=True,
                fixture="l4_critic_sample",
            )

            # Load report
            report_json = out_dir / "critic_report.json"
            with open(report_json) as f:
                report_data = json.load(f)

            # Check path normalization
            evidence_path = report_data["inputs"]["evidence_pack_path"]

            # Should be relative (no absolute paths with /Users/, /home/, etc.)
            assert not evidence_path.startswith("/Users/"), "Path not normalized (contains /Users/)"
            assert not evidence_path.startswith("/home/"), "Path not normalized (contains /home/)"
            assert not evidence_path.startswith("C:\\"), "Path not normalized (contains C:\\)"

            # Should contain "tests" or "Peak_Trade" as anchor
            assert "tests" in evidence_path or "Peak_Trade" in evidence_path, (
                f"Path not normalized correctly: {evidence_path}"
            )


class TestLegacyOutputPolicy:
    """Test legacy output policy (Phase 4C)."""

    @pytest.fixture
    def evidence_pack_path(self) -> Path:
        """Path to sample evidence pack."""
        return Path("tests/fixtures/evidence_packs/L1_sample_2026-01-10")

    @pytest.fixture
    def transcript_path(self) -> Path:
        """Path to sample transcript."""
        return Path("tests/fixtures/transcripts/l4_critic_sample.json")

    @pytest.fixture
    def fixed_clock(self) -> datetime:
        """Fixed clock for determinism."""
        return datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)

    def test_legacy_output_enabled_by_default(
        self,
        evidence_pack_path: Path,
        transcript_path: Path,
        fixed_clock: datetime,
    ):
        """Test that legacy outputs are generated by default (backward compatibility)."""
        with TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "run"
            out_dir.mkdir(parents=True)

            runner = L4Critic(clock=fixed_clock)
            result = runner.run(
                evidence_pack_path=evidence_pack_path,
                mode="replay",
                transcript_path=transcript_path,
                out_dir=out_dir,
                # legacy_output=True is default, not specified
            )

            # Check standardized outputs (ALWAYS present)
            assert (out_dir / "critic_report.json").exists()
            assert (out_dir / "critic_summary.md").exists()

            # Check legacy outputs (present by default)
            assert (out_dir / "critic_report.md").exists()
            assert (out_dir / "critic_decision.json").exists()
            assert (out_dir / "critic_manifest.json").exists()
            assert (out_dir / "operator_summary.txt").exists()

    def test_legacy_output_suppressed_with_flag(
        self,
        evidence_pack_path: Path,
        transcript_path: Path,
        fixed_clock: datetime,
    ):
        """Test that legacy outputs are suppressed when legacy_output=False."""
        with TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "run"
            out_dir.mkdir(parents=True)

            runner = L4Critic(clock=fixed_clock)
            result = runner.run(
                evidence_pack_path=evidence_pack_path,
                mode="replay",
                transcript_path=transcript_path,
                out_dir=out_dir,
                legacy_output=False,  # Suppress legacy
            )

            # Check standardized outputs (ALWAYS present)
            assert (out_dir / "critic_report.json").exists()
            assert (out_dir / "critic_summary.md").exists()

            # Check legacy outputs (NOT present when suppressed)
            assert not (out_dir / "critic_report.md").exists()
            assert not (out_dir / "critic_decision.json").exists()
            assert not (out_dir / "critic_manifest.json").exists()
            assert not (out_dir / "operator_summary.txt").exists()

    def test_standardized_outputs_always_present(
        self,
        evidence_pack_path: Path,
        transcript_path: Path,
        fixed_clock: datetime,
    ):
        """Test that standardized outputs are ALWAYS generated (regardless of legacy flag)."""
        with TemporaryDirectory() as tmpdir:
            # Test with legacy enabled
            out_dir1 = Path(tmpdir) / "run_legacy_on"
            out_dir1.mkdir(parents=True)

            runner1 = L4Critic(clock=fixed_clock)
            result1 = runner1.run(
                evidence_pack_path=evidence_pack_path,
                mode="replay",
                transcript_path=transcript_path,
                out_dir=out_dir1,
                legacy_output=True,
            )

            assert (out_dir1 / "critic_report.json").exists()
            assert (out_dir1 / "critic_summary.md").exists()

            # Test with legacy disabled
            out_dir2 = Path(tmpdir) / "run_legacy_off"
            out_dir2.mkdir(parents=True)

            runner2 = L4Critic(clock=fixed_clock)
            result2 = runner2.run(
                evidence_pack_path=evidence_pack_path,
                mode="replay",
                transcript_path=transcript_path,
                out_dir=out_dir2,
                legacy_output=False,
            )

            assert (out_dir2 / "critic_report.json").exists()
            assert (out_dir2 / "critic_summary.md").exists()

            # Compare standardized outputs (should be identical)
            with (
                open(out_dir1 / "critic_report.json") as f1,
                open(out_dir2 / "critic_report.json") as f2,
            ):
                assert f1.read() == f2.read()


class TestCriticReportSchema:
    """Test critic report schema validation."""

    def test_schema_version_present(self):
        """Test that schema_version field is always present."""
        from src.ai_orchestration.critic_report_schema import (
            CriticInfo,
            CriticReport,
            InputMetadata,
            MetaInfo,
            RiskLevel,
            SummaryMetrics,
            Verdict,
        )

        report = CriticReport(
            schema_version="1.0.0",
            pack_id="TEST-001",
            mode="replay",
            critic=CriticInfo(name="L4_Test", version="1.0.0"),
            inputs=InputMetadata(
                evidence_pack_path="tests/fixtures/test",
                fixture="test",
                schema_version_in="1.0",
            ),
            summary=SummaryMetrics(
                verdict=Verdict.PASS,
                risk_level=RiskLevel.LOW,
                finding_counts={},
            ),
            findings=[],
            meta=MetaInfo(deterministic=True),
        )

        # Convert to dict
        data = report.to_canonical_dict()
        assert "schema_version" in data
        assert data["schema_version"] == "1.0.0"

    def test_json_write_deterministic(self, tmp_path: Path):
        """Test that JSON write is deterministic (sorted keys)."""
        from src.ai_orchestration.critic_report_schema import (
            CriticInfo,
            CriticReport,
            InputMetadata,
            MetaInfo,
            RiskLevel,
            SummaryMetrics,
            Verdict,
        )

        report = CriticReport(
            schema_version="1.0.0",
            pack_id="TEST-001",
            mode="replay",
            critic=CriticInfo(name="L4_Test", version="1.0.0"),
            inputs=InputMetadata(
                evidence_pack_path="tests/fixtures/test",
                fixture="test",
                schema_version_in="1.0",
            ),
            summary=SummaryMetrics(
                verdict=Verdict.PASS,
                risk_level=RiskLevel.LOW,
                finding_counts={"high": 0, "med": 0, "low": 1, "info": 2},
            ),
            findings=[],
            meta=MetaInfo(deterministic=True),
        )

        # Write JSON
        json_path = tmp_path / "test_report.json"
        report.write_json(json_path, deterministic=True)

        # Verify JSON structure
        with open(json_path) as f:
            data = json.load(f)

        # Check keys are present
        assert "schema_version" in data
        assert "pack_id" in data
        assert "mode" in data
        assert "critic" in data
        assert "inputs" in data
        assert "summary" in data
        assert "findings" in data
        assert "meta" in data

        # Check sorted keys (JSON spec doesn't guarantee order, but our impl does)
        # We can verify by re-reading raw text
        with open(json_path) as f:
            raw_text = f.read()

        # Check that "critic" comes before "findings" (alphabetically)
        assert raw_text.index('"critic"') < raw_text.index('"findings"')
        assert raw_text.index('"inputs"') < raw_text.index('"meta"')
