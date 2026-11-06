"""
Validator Report Normalizer (Phase 4E)

Normalizes raw validator reports to canonical format.

Design Principles:
- Backward compatibility: supports legacy Phase 4D validator reports
- Deterministic: stable ordering, canonical JSON formatting
- Extensible: can add new normalizers for different report types
- Evidence-first: preserves all information while standardizing format

Reference:
- docs/governance/ai_autonomy/PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md

Usage:
    from src.ai_orchestration.validator_report_normalized import (
        normalize_validator_report,
        normalize_to_json,
        normalize_to_markdown,
    )

    # Normalize legacy report
    normalized = normalize_validator_report(
        raw_report=legacy_report_dict,
        runtime_context={"git_sha": "abc123", "run_id": "12345"},
    )

    # Write outputs
    normalized.write_json(out_dir / "validator_report.normalized.json")
    normalized.write_summary_md(out_dir / "validator_report.normalized.md")
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

from .validator_report_schema import (
    RuntimeContext,
    ValidatorReport,
)


def normalize_validator_report(
    raw_report: Dict[str, Any],
    runtime_context: Optional[Dict[str, Any]] = None,
) -> ValidatorReport:
    """
    Normalize raw validator report to canonical format.

    Args:
        raw_report: Raw validator report dict (legacy Phase 4D format)
        runtime_context: Optional runtime context dict

    Returns:
        Normalized ValidatorReport instance

    Example:
        >>> raw = {
        ...     "validator": {"name": "test_validator", "version": "1.0.0"},
        ...     "contract_version": "1.0.0",
        ...     "inputs": {"baseline": "a.json", "candidate": "b.json"},
        ...     "result": {"equal": True, "baseline_hash": "abc", "candidate_hash": "abc"},
        ... }
        >>> normalized = normalize_validator_report(raw)
        >>> normalized.result
        <ValidationResult.PASS: 'PASS'>
    """
    # Parse runtime context if provided
    runtime_ctx = None
    if runtime_context:
        runtime_ctx = RuntimeContext(**runtime_context)

    # Normalize from legacy format
    normalized = ValidatorReport.from_legacy_validator_report(
        legacy_report=raw_report,
        runtime_context=runtime_ctx,
    )

    return normalized


def normalize_to_json(
    raw_report: Dict[str, Any],
    output_path: Path,
    runtime_context: Optional[Dict[str, Any]] = None,
    deterministic: bool = True,
) -> ValidatorReport:
    """
    Normalize and write validator report as JSON.

    Args:
        raw_report: Raw validator report dict
        output_path: Output JSON path
        runtime_context: Optional runtime context dict
        deterministic: If True, use canonical serialization

    Returns:
        Normalized ValidatorReport instance
    """
    normalized = normalize_validator_report(raw_report, runtime_context)
    normalized.write_json(output_path, deterministic=deterministic)
    return normalized


def normalize_to_markdown(
    raw_report: Dict[str, Any],
    output_path: Path,
    runtime_context: Optional[Dict[str, Any]] = None,
) -> ValidatorReport:
    """
    Normalize and write validator report as Markdown.

    Args:
        raw_report: Raw validator report dict
        output_path: Output Markdown path
        runtime_context: Optional runtime context dict

    Returns:
        Normalized ValidatorReport instance
    """
    normalized = normalize_validator_report(raw_report, runtime_context)
    normalized.write_summary_md(output_path)
    return normalized


def hash_normalized_report(report: ValidatorReport) -> str:
    """
    Compute SHA256 hash of normalized report (canonical representation).

    Args:
        report: ValidatorReport instance

    Returns:
        SHA256 hex digest

    Note:
        Only includes canonical fields (excludes runtime_context).
    """
    canonical_dict = report.to_canonical_dict()
    canonical_json = json.dumps(canonical_dict, indent=2, sort_keys=True, ensure_ascii=False)
    canonical_bytes = canonical_json.encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def validate_determinism(report1: ValidatorReport, report2: ValidatorReport) -> bool:
    """
    Check if two normalized reports are deterministically identical.

    Args:
        report1: First ValidatorReport instance
        report2: Second ValidatorReport instance

    Returns:
        True if reports are deterministically equal (ignoring runtime_context)

    Example:
        >>> report1 = normalize_validator_report(raw_report)
        >>> report2 = normalize_validator_report(raw_report)  # Same input
        >>> validate_determinism(report1, report2)
        True
    """
    hash1 = hash_normalized_report(report1)
    hash2 = hash_normalized_report(report2)
    return hash1 == hash2
