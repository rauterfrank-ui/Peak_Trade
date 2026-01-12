"""
Tests for Phase 5B Trend Ledger Consumer

Test Coverage:
- Load trend seed from JSON
- Generate ledger from seed
- Canonical JSON serialization (determinism)
- Markdown summary rendering
- Schema validation (fail-closed)
- Error handling (missing fields, unsupported schema)

Fixtures:
- tests/fixtures/trend_seed.sample.json (valid Phase 5A seed)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ai_orchestration.trends.trend_ledger import (
    SchemaVersionError,
    TrendLedgerSnapshot,
    ValidationError,
    compute_canonical_hash,
    ledger_from_seed,
    load_trend_seed,
    render_markdown_summary,
    to_canonical_json,
)

# Fixtures path
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
SAMPLE_SEED_PATH = FIXTURES_DIR / "trend_seed.sample.json"


class TestLoadTrendSeed:
    """Tests for load_trend_seed()."""

    def test_load_valid_seed(self):
        """Load valid trend seed from fixture."""
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))

        assert isinstance(seed, dict)
        assert seed["schema_version"] == "0.1.0"
        assert "source" in seed
        assert "normalized_report" in seed
        assert seed["source"]["run_id"] == "12345"

    def test_load_missing_file(self):
        """Fail on missing file."""
        with pytest.raises(FileNotFoundError, match="Trend seed not found"):
            load_trend_seed("nonexistent.json")

    def test_load_invalid_json(self, tmp_path):
        """Fail on invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_trend_seed(str(bad_file))


class TestLedgerFromSeed:
    """Tests for ledger_from_seed()."""

    def test_generate_ledger_from_valid_seed(self):
        """Generate ledger from valid seed."""
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))
        ledger = ledger_from_seed(seed)

        assert isinstance(ledger, TrendLedgerSnapshot)
        assert ledger.schema_version == "0.1.0"
        assert ledger.generated_at == "2026-01-11T12:00:00Z"
        assert ledger.source_run["run_id"] == "12345"
        assert ledger.source_run["workflow_name"] == "L4 Critic Replay Determinism"
        assert len(ledger.items) > 0
        assert len(ledger.counters) > 0

    def test_ledger_items_structure(self):
        """Verify ledger items have expected structure."""
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))
        ledger = ledger_from_seed(seed)

        assert len(ledger.items) == 1  # Phase 5B: single item per seed
        item = ledger.items[0]
        assert item["category"] == "validator_report"
        assert item["key"] == "overall_status"
        assert item["conclusion"] == "pass"
        assert item["is_deterministic"] is True

    def test_ledger_counters_structure(self):
        """Verify ledger counters have expected structure."""
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))
        ledger = ledger_from_seed(seed)

        counters = ledger.counters
        assert counters["checks_total"] == 2
        assert counters["checks_passed"] == 2
        assert counters["checks_failed"] == 0
        assert counters["policy_findings_total"] == 0
        assert counters["items_total"] == 1

    def test_fail_on_missing_schema_version(self):
        """Fail if seed is missing schema_version."""
        seed = {"source": {}, "normalized_report": {}}
        with pytest.raises(ValidationError, match="Missing required field: schema_version"):
            ledger_from_seed(seed)

    def test_fail_on_unsupported_schema_version(self):
        """Fail if seed has unsupported schema_version."""
        seed = {
            "schema_version": "99.0.0",
            "source": {},
            "normalized_report": {},
            "generated_at": "2026-01-11T12:00:00Z",
        }
        with pytest.raises(SchemaVersionError, match="Unsupported schema_version: 99.0.0"):
            ledger_from_seed(seed)

    def test_fail_on_missing_source_field(self):
        """Fail if seed is missing 'source' field."""
        seed = {
            "schema_version": "0.1.0",
            "normalized_report": {},
            "generated_at": "2026-01-11T12:00:00Z",
        }
        with pytest.raises(ValidationError, match="Missing or invalid 'source' field"):
            ledger_from_seed(seed)

    def test_fail_on_missing_normalized_report_field(self):
        """Fail if seed is missing 'normalized_report' field."""
        seed = {
            "schema_version": "0.1.0",
            "source": {
                "repo": "owner/repo",
                "workflow_name": "test",
                "run_id": "123",
                "head_sha": "abc",
                "ref": "refs/heads/main",
            },
            "generated_at": "2026-01-11T12:00:00Z",
        }
        with pytest.raises(ValidationError, match="Missing or invalid 'normalized_report' field"):
            ledger_from_seed(seed)


class TestCanonicalJSON:
    """Tests for canonical JSON serialization."""

    def test_to_canonical_json_structure(self):
        """Verify canonical JSON structure."""
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))
        ledger = ledger_from_seed(seed)
        json_str = to_canonical_json(ledger)

        # Parse back to verify structure
        parsed = json.loads(json_str)
        assert parsed["schema_version"] == "0.1.0"
        assert "generated_at" in parsed
        assert "source_run" in parsed
        assert "items" in parsed
        assert "counters" in parsed

    def test_canonical_json_determinism(self):
        """Verify repeated calls produce identical JSON."""
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))
        ledger = ledger_from_seed(seed)

        json1 = to_canonical_json(ledger)
        json2 = to_canonical_json(ledger)

        assert json1 == json2
        assert json1[-1] == "\n"  # Single trailing newline

    def test_canonical_json_sorted_keys(self):
        """Verify keys are sorted at all levels."""
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))
        ledger = ledger_from_seed(seed)
        json_str = to_canonical_json(ledger)

        # Top-level keys should be sorted
        lines = json_str.strip().split("\n")
        top_keys = []
        for line in lines:
            if '":' in line and not line.strip().startswith('"'):
                key = line.split('"')[1]
                if key not in ["repo", "workflow_name"]:  # Skip nested keys
                    top_keys.append(key)

        # Check that counters comes before generated_at, etc. (alphabetical)
        assert "counters" in json_str
        assert "generated_at" in json_str
        assert json_str.index("counters") < json_str.index("source_run")

    def test_compute_canonical_hash_determinism(self):
        """Verify canonical hash is deterministic."""
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))
        ledger = ledger_from_seed(seed)

        hash1 = compute_canonical_hash(ledger)
        hash2 = compute_canonical_hash(ledger)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest
        assert hash1.islower()  # Lowercase hex

    def test_different_ledgers_different_hashes(self):
        """Verify different ledgers produce different hashes."""
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))
        ledger1 = ledger_from_seed(seed)

        # Modify seed slightly
        seed2 = seed.copy()
        seed2["source"] = seed["source"].copy()
        seed2["source"]["run_id"] = "99999"
        ledger2 = ledger_from_seed(seed2)

        hash1 = compute_canonical_hash(ledger1)
        hash2 = compute_canonical_hash(ledger2)

        assert hash1 != hash2


class TestMarkdownSummary:
    """Tests for Markdown summary rendering."""

    def test_render_markdown_structure(self):
        """Verify markdown summary has expected structure."""
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))
        ledger = ledger_from_seed(seed)
        markdown = render_markdown_summary(ledger)

        # Check for expected sections
        assert "# Trend Ledger Summary" in markdown
        assert "## Metadata" in markdown
        assert "## Counters" in markdown
        assert "## Items" in markdown

        # Check for key values
        assert "Schema Version:" in markdown
        assert "0.1.0" in markdown
        assert "Source Run ID:** 12345" in markdown
        assert "**Checks Total:** 2" in markdown
        assert "validator_report/overall_status" in markdown

    def test_markdown_includes_source_metadata(self):
        """Verify markdown includes source run metadata."""
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))
        ledger = ledger_from_seed(seed)
        markdown = render_markdown_summary(ledger)

        assert "L4 Critic Replay Determinism" in markdown
        assert "owner/repo" in markdown
        assert "refs/heads/main" in markdown
        assert "12345" in markdown  # run_id

    def test_markdown_includes_counters(self):
        """Verify markdown includes counters."""
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))
        ledger = ledger_from_seed(seed)
        markdown = render_markdown_summary(ledger)

        assert "**Items Total:** 1" in markdown
        assert "**Checks Total:** 2" in markdown
        assert "**Checks Passed:** 2" in markdown
        assert "**Checks Failed:** 0" in markdown
        assert "**Policy Findings Total:** 0" in markdown


class TestIntegration:
    """Integration tests for full workflow."""

    def test_full_workflow_seed_to_ledger_to_json(self, tmp_path):
        """Test full workflow: load seed → generate ledger → write JSON."""
        # Load seed
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))

        # Generate ledger
        ledger = ledger_from_seed(seed)

        # Write canonical JSON
        output_json = tmp_path / "ledger.json"
        json_str = to_canonical_json(ledger)
        output_json.write_text(json_str)

        # Verify file contents
        assert output_json.exists()
        parsed = json.loads(output_json.read_text())
        assert parsed["schema_version"] == "0.1.0"
        assert parsed["source_run"]["run_id"] == "12345"

    def test_full_workflow_with_markdown(self, tmp_path):
        """Test full workflow: load seed → generate ledger → write JSON + markdown."""
        # Load seed
        seed = load_trend_seed(str(SAMPLE_SEED_PATH))

        # Generate ledger
        ledger = ledger_from_seed(seed)

        # Write outputs
        output_json = tmp_path / "ledger.json"
        output_markdown = tmp_path / "ledger.md"

        output_json.write_text(to_canonical_json(ledger))
        output_markdown.write_text(render_markdown_summary(ledger))

        # Verify both files
        assert output_json.exists()
        assert output_markdown.exists()

        # Verify markdown is readable
        markdown = output_markdown.read_text()
        assert "Trend Ledger Summary" in markdown
        assert "Source Run ID:** 12345" in markdown

    def test_determinism_across_multiple_runs(self):
        """Verify determinism: same seed → same ledger → same hash."""
        # Load seed 3 times, generate ledger, compute hash
        hashes = []
        for _ in range(3):
            seed = load_trend_seed(str(SAMPLE_SEED_PATH))
            ledger = ledger_from_seed(seed)
            hash_val = compute_canonical_hash(ledger)
            hashes.append(hash_val)

        # All hashes should be identical
        assert len(set(hashes)) == 1
        assert all(h == hashes[0] for h in hashes)
