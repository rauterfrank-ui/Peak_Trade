"""
Trend Ledger (Phase 5B)

Consumes Phase 5A Trend Seeds and generates a stable, canonical Trend Ledger snapshot.

Design Principles:
- Deterministic: canonical JSON with stable ordering (sort by category/key/severity)
- Fail-closed: schema mismatch → hard fail
- Single-source: one seed → one ledger (future: multi-seed aggregation)
- Minimal: lightweight, append-oriented design for future time-series
- No secrets: no tokens, no PII

Reference:
- docs/ops/runbooks/RUNBOOK_PHASE5B_TREND_LEDGER_FROM_SEED.md

Usage:
    from src.ai_orchestration.trends.trend_ledger import (
        load_trend_seed,
        ledger_from_seed,
        to_canonical_json,
        render_markdown_summary,
    )

    # Load trend seed
    seed = load_trend_seed("trend_seed.json")

    # Generate ledger
    ledger = ledger_from_seed(seed)

    # Write canonical JSON
    json_str = to_canonical_json(ledger)
    Path("trend_ledger.json").write_text(json_str)

    # Render markdown summary
    summary = render_markdown_summary(ledger)
    Path("trend_ledger.md").write_text(summary)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


class TrendLedgerError(Exception):
    """Base exception for Trend Ledger errors."""


class SchemaVersionError(TrendLedgerError):
    """Raised when trend seed schema version is unsupported."""


class ValidationError(TrendLedgerError):
    """Raised when required fields are missing or invalid."""


@dataclass
class TrendLedgerSnapshot:
    """
    Canonical Trend Ledger Snapshot.

    Attributes:
        schema_version: Ledger schema version (e.g. "0.1.0")
        generated_at: ISO-8601 UTC timestamp (from source seed)
        source_run: Source workflow run metadata
        items: List of trend items (sorted canonically)
        counters: Aggregated counters (checks, findings, etc.)
    """

    schema_version: str
    generated_at: str
    source_run: Dict[str, Any]
    items: List[Dict[str, Any]] = field(default_factory=list)
    counters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source_run": self.source_run,
            "items": self.items,
            "counters": self.counters,
        }


def load_trend_seed(path: str) -> Dict[str, Any]:
    """
    Load Trend Seed from JSON file.

    Args:
        path: Path to trend_seed.json

    Returns:
        Parsed JSON dict

    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file is not valid JSON
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Trend seed not found: {path}")

    with open(path_obj, "r", encoding="utf-8") as f:
        return json.load(f)


def _validate_seed_schema(seed: Dict[str, Any]) -> str:
    """
    Validate and extract schema_version from trend seed.

    Args:
        seed: Trend seed dict

    Returns:
        Schema version string

    Raises:
        ValidationError: If schema_version is missing
        SchemaVersionError: If schema_version is unsupported
    """
    if "schema_version" not in seed:
        raise ValidationError("Missing required field: schema_version")

    version = seed["schema_version"]
    if not isinstance(version, str):
        raise ValidationError(f"Invalid schema_version type: {type(version)}")

    # Phase 5B supports Phase 5A schema v0.1.0
    supported_versions = ["0.1.0"]
    if version not in supported_versions:
        raise SchemaVersionError(
            f"Unsupported schema_version: {version}. Supported: {supported_versions}"
        )

    return version


def _extract_source_metadata(seed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract source workflow run metadata from seed.

    Args:
        seed: Trend seed dict

    Returns:
        Source metadata dict

    Raises:
        ValidationError: If required fields are missing
    """
    if "source" not in seed or not isinstance(seed["source"], dict):
        raise ValidationError("Missing or invalid 'source' field")

    source = seed["source"]
    required_keys = ["repo", "workflow_name", "run_id", "head_sha", "ref"]
    for key in required_keys:
        if key not in source:
            raise ValidationError(f"Missing required source field: {key}")

    return {
        "repo": source["repo"],
        "workflow_name": source["workflow_name"],
        "run_id": str(source["run_id"]),
        "run_attempt": source.get("run_attempt", 1),
        "head_sha": source["head_sha"],
        "ref": source["ref"],
    }


def _extract_normalized_report_summary(seed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract summary from normalized_report in seed.

    Args:
        seed: Trend seed dict

    Returns:
        Normalized report summary dict

    Raises:
        ValidationError: If required fields are missing
    """
    if "normalized_report" not in seed or not isinstance(seed["normalized_report"], dict):
        raise ValidationError("Missing or invalid 'normalized_report' field")

    report = seed["normalized_report"]

    # Extract conclusion (PASS, FAIL, ERROR)
    if "conclusion" not in report:
        raise ValidationError("Missing required field: normalized_report.conclusion")
    conclusion = report["conclusion"]

    # Extract determinism info
    determinism_info = {}
    if "determinism" in report and isinstance(report["determinism"], dict):
        determinism_info = {
            "hash": report["determinism"].get("hash"),
            "is_deterministic": report["determinism"].get("is_deterministic"),
        }

    # Extract counts
    counts = {}
    if "counts" in report and isinstance(report["counts"], dict):
        counts = {
            "checks_total": report["counts"].get("checks_total", 0),
            "checks_passed": report["counts"].get("checks_passed", 0),
            "checks_failed": report["counts"].get("checks_failed", 0),
            "policy_findings_total": report["counts"].get("policy_findings_total"),
        }

    return {
        "conclusion": conclusion,
        "determinism": determinism_info,
        "counts": counts,
        "report_id": report.get("report_id"),
    }


def _build_ledger_items(seed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build canonical ledger items from seed.

    For Phase 5B, we create a single item per seed representing the overall status.
    Future phases may expand this to include per-check items.

    Args:
        seed: Trend seed dict

    Returns:
        List of ledger items (sorted canonically)
    """
    report_summary = _extract_normalized_report_summary(seed)

    # Single item for overall status
    item = {
        "category": "validator_report",
        "key": "overall_status",
        "conclusion": report_summary["conclusion"],
        "determinism_hash": report_summary["determinism"].get("hash"),
        "is_deterministic": report_summary["determinism"].get("is_deterministic"),
        "report_id": report_summary["report_id"],
    }

    # Sort items canonically (by category, then key)
    # For single item, this is trivial, but prepares for multi-item expansion
    items = [item]
    items.sort(key=lambda x: (x["category"], x["key"]))

    return items


def _build_counters(seed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build aggregated counters from seed.

    Args:
        seed: Trend seed dict

    Returns:
        Counters dict
    """
    report_summary = _extract_normalized_report_summary(seed)
    counts = report_summary["counts"]

    return {
        "checks_total": counts.get("checks_total", 0),
        "checks_passed": counts.get("checks_passed", 0),
        "checks_failed": counts.get("checks_failed", 0),
        "policy_findings_total": counts.get("policy_findings_total"),
        "items_total": 1,  # Single item for Phase 5B
    }


def ledger_from_seed(seed: Dict[str, Any]) -> TrendLedgerSnapshot:
    """
    Generate Trend Ledger from Trend Seed.

    Args:
        seed: Parsed Phase 5A trend seed dict

    Returns:
        TrendLedgerSnapshot

    Raises:
        SchemaVersionError: If seed schema is unsupported
        ValidationError: If required fields are missing or invalid
    """
    # Validate schema (fail-closed)
    _validate_seed_schema(seed)

    # Extract components
    source_run = _extract_source_metadata(seed)
    items = _build_ledger_items(seed)
    counters = _build_counters(seed)

    # Use seed's generated_at as ledger generated_at (deterministic)
    generated_at = seed.get("generated_at")
    if not generated_at:
        raise ValidationError("Missing required field: generated_at")

    return TrendLedgerSnapshot(
        schema_version="0.1.0",
        generated_at=generated_at,
        source_run=source_run,
        items=items,
        counters=counters,
    )


def to_canonical_json(ledger: TrendLedgerSnapshot) -> str:
    """
    Serialize ledger to canonical JSON (deterministic).

    Args:
        ledger: TrendLedgerSnapshot

    Returns:
        JSON string with stable ordering, no trailing whitespace

    Notes:
        - Sorted keys at all levels
        - 2-space indent
        - Single trailing newline
        - Deterministic: repeated calls produce identical bytes
    """
    payload = ledger.to_dict()
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def compute_canonical_hash(ledger: TrendLedgerSnapshot) -> str:
    """
    Compute deterministic hash of canonical JSON representation.

    Args:
        ledger: TrendLedgerSnapshot

    Returns:
        SHA-256 hex digest (lowercase)

    Notes:
        Useful for determinism tests (compare hashes across runs)
    """
    canonical = to_canonical_json(ledger)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def render_markdown_summary(ledger: TrendLedgerSnapshot) -> str:
    """
    Render human-friendly Markdown summary of ledger.

    Args:
        ledger: TrendLedgerSnapshot

    Returns:
        Markdown string
    """
    lines = []
    lines.append("# Trend Ledger Summary\n")

    # Metadata
    lines.append("## Metadata")
    lines.append(f"- **Schema Version:** {ledger.schema_version}")
    lines.append(f"- **Generated At:** {ledger.generated_at}")
    lines.append(f"- **Source Run ID:** {ledger.source_run['run_id']}")
    lines.append(f"- **Workflow:** {ledger.source_run['workflow_name']}")
    lines.append(f"- **Repo:** {ledger.source_run['repo']}")
    lines.append(f"- **Ref:** {ledger.source_run['ref']}")
    lines.append(f"- **Head SHA:** {ledger.source_run['head_sha'][:8]}")
    lines.append("")

    # Counters
    lines.append("## Counters")
    counters = ledger.counters
    lines.append(f"- **Items Total:** {counters.get('items_total', 0)}")
    lines.append(f"- **Checks Total:** {counters.get('checks_total', 0)}")
    lines.append(f"- **Checks Passed:** {counters.get('checks_passed', 0)}")
    lines.append(f"- **Checks Failed:** {counters.get('checks_failed', 0)}")
    policy_findings = counters.get("policy_findings_total")
    if policy_findings is not None:
        lines.append(f"- **Policy Findings Total:** {policy_findings}")
    lines.append("")

    # Items summary
    lines.append("## Items")
    if ledger.items:
        for item in ledger.items:
            lines.append(f"- **{item['category']}/{item['key']}**")
            lines.append(f"  - Conclusion: `{item['conclusion']}`")
            lines.append(f"  - Deterministic: `{item.get('is_deterministic')}`")
            if item.get("report_id"):
                lines.append(f"  - Report ID: `{item['report_id']}`")
    else:
        lines.append("*(No items)*")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("*Generated by Phase 5B Trend Ledger Consumer*")
    lines.append("")

    return "\n".join(lines)
