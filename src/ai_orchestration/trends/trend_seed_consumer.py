"""
Trend Seed Consumer (Phase 5A)

Consumes Phase 4E normalized validator reports and generates deterministic Trend Seeds.

Design Principles:
- Fail-closed: schema mismatch or missing required keys → hard fail
- Deterministic: stable JSON ordering, stable timestamps from workflow meta
- Minimal: single record per run (append-only mindset for future aggregation)
- No secrets: no tokens, no runner env data in artifacts

Reference:
- docs/ops/runbooks/RUNBOOK_PHASE5A_NORMALIZED_REPORT_CONSUMER_TREND_SEED_CURSOR_MULTI_AGENT.md

Usage:
    from src.ai_orchestration.trends.trend_seed_consumer import (
        load_normalized_report,
        generate_trend_seed,
        write_deterministic_json,
        render_markdown_summary,
    )

    # Load normalized report
    report = load_normalized_report("validator_report.normalized.json")

    # Generate trend seed
    meta = {
        "repo": "owner/repo",
        "workflow_name": "L4 Critic Replay Determinism",
        "run_id": "12345",
        "run_attempt": 1,
        "head_sha": "abc123",
        "ref": "refs/heads/main",
        "run_created_at": "2026-01-11T12:00:00Z",
        "consumer_name": "trend_seed_consumer",
        "consumer_version": "0.1.0",
        "consumer_commit_sha": "def456",
    }
    seed = generate_trend_seed(report, meta=meta)

    # Write outputs
    write_deterministic_json("trend_seed.normalized_report.json", seed)
    summary = render_markdown_summary(seed)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


class TrendSeedError(Exception):
    """Base exception for Trend Seed consumer errors."""


class SchemaVersionError(TrendSeedError):
    """Raised when normalized report schema version is unsupported."""


class ValidationError(TrendSeedError):
    """Raised when required fields are missing or invalid."""


def load_normalized_report(path: str) -> Dict[str, Any]:
    """
    Load normalized validator report from JSON file.

    Args:
        path: Path to validator_report.normalized.json

    Returns:
        Parsed JSON dict

    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file is not valid JSON
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Normalized report not found: {path}")

    with open(path_obj, "r", encoding="utf-8") as f:
        return json.load(f)


def _validate_schema_version(report: Dict[str, Any]) -> str:
    """
    Validate and extract schema_version from normalized report.

    Args:
        report: Normalized report dict

    Returns:
        Schema version string

    Raises:
        ValidationError: If schema_version is missing
        SchemaVersionError: If schema_version is unsupported
    """
    if "schema_version" not in report:
        raise ValidationError("Missing required field: schema_version")

    schema_version = report["schema_version"]

    # Accept only schema versions starting with "1."
    if not isinstance(schema_version, str) or not schema_version.startswith("1."):
        raise SchemaVersionError(
            f"Unsupported normalized report schema version: {schema_version}. "
            f"Expected version starting with '1.' (e.g. '1.0.0')"
        )

    return schema_version


def _extract_conclusion(report: Dict[str, Any]) -> str:
    """
    Extract and normalize conclusion from normalized report.

    Args:
        report: Normalized report dict

    Returns:
        Normalized conclusion ("pass", "fail", or "error")

    Raises:
        ValidationError: If conclusion field is missing or invalid
    """
    # Phase 4E uses "result" field with values: PASS, FAIL, ERROR
    if "result" not in report:
        raise ValidationError("Missing required field: result")

    result = report["result"]
    if not isinstance(result, str):
        raise ValidationError(f"Invalid result type: {type(result)}")

    # Normalize to lowercase
    normalized = result.lower()

    # Map common variants
    if normalized in ("pass", "success"):
        return "pass"
    elif normalized in ("fail", "failure"):
        return "fail"
    elif normalized in ("error",):
        return "error"
    else:
        raise ValidationError(
            f"Invalid result value: {result}. Expected PASS, FAIL, or ERROR"
        )


def _extract_counts(report: Dict[str, Any]) -> Dict[str, int]:
    """
    Extract check counts from normalized report.

    Args:
        report: Normalized report dict

    Returns:
        Dict with keys: checks_total, checks_passed, checks_failed

    Raises:
        ValidationError: If counts cannot be extracted
    """
    # Phase 4E provides summary.passed, summary.failed, summary.total
    if "summary" not in report:
        raise ValidationError("Missing required field: summary")

    summary = report["summary"]

    if not isinstance(summary, dict):
        raise ValidationError(f"Invalid summary type: {type(summary)}")

    # Extract counts (fail-closed)
    if "total" not in summary:
        raise ValidationError("Missing required field: summary.total")
    if "passed" not in summary:
        raise ValidationError("Missing required field: summary.passed")
    if "failed" not in summary:
        raise ValidationError("Missing required field: summary.failed")

    return {
        "checks_total": summary["total"],
        "checks_passed": summary["passed"],
        "checks_failed": summary["failed"],
    }


def _extract_determinism_info(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract determinism hash and status from normalized report.

    Args:
        report: Normalized report dict

    Returns:
        Dict with keys: hash (str or None), is_deterministic (bool or None)
    """
    # Phase 4E may include determinism_hash at top level
    determinism_hash = report.get("determinism_hash")

    # Derive is_deterministic if we have checks
    is_deterministic = None
    if "checks" in report and isinstance(report["checks"], list):
        # Check if all checks passed
        checks = report["checks"]
        if checks:
            is_deterministic = all(
                check.get("status") == "pass" for check in checks if isinstance(check, dict)
            )

    return {
        "hash": determinism_hash,
        "is_deterministic": is_deterministic,
    }


def _extract_policy_findings_count(report: Dict[str, Any]) -> Optional[int]:
    """
    Extract policy findings count from normalized report.

    Args:
        report: Normalized report dict

    Returns:
        Policy findings count or None if not available
    """
    # Phase 4E may include policy_findings in evidence
    if "evidence" in report and isinstance(report["evidence"], dict):
        evidence = report["evidence"]
        if "policy_findings" in evidence:
            findings = evidence["policy_findings"]
            if isinstance(findings, list):
                return len(findings)

    return None


def generate_trend_seed(
    normalized_report: Dict[str, Any],
    *,
    meta: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate deterministic Trend Seed from normalized report.

    Args:
        normalized_report: Parsed Phase 4E normalized validator report
        meta: Workflow run metadata dict with required keys:
            - repo: str (e.g. "owner/repo")
            - workflow_name: str
            - run_id: str or int
            - run_attempt: int (optional; default 1)
            - head_sha: str
            - ref: str (e.g. "refs/heads/main")
            - run_created_at: str (ISO-8601 UTC with Z suffix)
            - consumer_name: str (optional; default "trend_seed_consumer")
            - consumer_version: str (optional; default "0.1.0")
            - consumer_commit_sha: str (optional; default None)

    Returns:
        Trend Seed dict (schema v0.1.0)

    Raises:
        SchemaVersionError: If normalized_report schema is unsupported
        ValidationError: If required fields are missing or invalid
    """
    # Validate schema version (fail-closed)
    schema_version = _validate_schema_version(normalized_report)

    # Extract required fields (fail-closed)
    conclusion = _extract_conclusion(normalized_report)
    counts = _extract_counts(normalized_report)
    determinism = _extract_determinism_info(normalized_report)
    policy_findings_total = _extract_policy_findings_count(normalized_report)

    # Validate meta (fail-closed)
    required_meta_keys = [
        "repo",
        "workflow_name",
        "run_id",
        "head_sha",
        "ref",
        "run_created_at",
    ]
    for key in required_meta_keys:
        if key not in meta:
            raise ValidationError(f"Missing required meta key: {key}")

    # Build Trend Seed (schema v0.1.0)
    seed = {
        "schema_version": "0.1.0",
        "generated_at": meta["run_created_at"],  # Use workflow created_at (deterministic)
        "source": {
            "repo": meta["repo"],
            "workflow_name": meta["workflow_name"],
            "run_id": str(meta["run_id"]),
            "run_attempt": meta.get("run_attempt", 1),
            "head_sha": meta["head_sha"],
            "ref": meta["ref"],
        },
        "normalized_report": {
            "schema_version": schema_version,
            "report_id": normalized_report.get("report_id"),
            "conclusion": conclusion,
            "determinism": {
                "hash": determinism["hash"],
                "is_deterministic": determinism["is_deterministic"],
            },
            "counts": {
                "checks_total": counts["checks_total"],
                "checks_passed": counts["checks_passed"],
                "checks_failed": counts["checks_failed"],
                "policy_findings_total": policy_findings_total,
            },
        },
    }

    # Optional: consumer metadata
    consumer_name = meta.get("consumer_name", "trend_seed_consumer")
    consumer_version = meta.get("consumer_version", "0.1.0")
    consumer_commit_sha = meta.get("consumer_commit_sha")

    seed["consumer"] = {
        "name": consumer_name,
        "version": consumer_version,
    }
    if consumer_commit_sha:
        seed["consumer"]["commit_sha"] = consumer_commit_sha

    # Optional: notes (bounded length)
    notes = meta.get("notes")
    if notes:
        seed["notes"] = str(notes)[:280]

    return seed


def write_deterministic_json(path: str, payload: Dict[str, Any]) -> None:
    """
    Write JSON with deterministic formatting.

    Args:
        path: Output file path
        payload: JSON-serializable dict

    Notes:
        - Sorted keys (stable ordering)
        - No trailing whitespace
        - Single trailing newline
        - Compact separators
        - UTF-8 encoding (ensure_ascii=False)
    """
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    json_str = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        indent=2,
    )

    with open(path_obj, "w", encoding="utf-8") as f:
        f.write(json_str)
        f.write("\n")


def render_markdown_summary(seed: Dict[str, Any]) -> str:
    """
    Render human-readable Markdown summary of Trend Seed.

    Args:
        seed: Trend Seed dict

    Returns:
        Markdown string
    """
    source = seed.get("source", {})
    report = seed.get("normalized_report", {})
    counts = report.get("counts", {})
    determinism = report.get("determinism", {})
    consumer = seed.get("consumer", {})

    lines = [
        "# Trend Seed Summary",
        "",
        f"**Generated:** {seed.get('generated_at', 'N/A')}  ",
        f"**Schema:** v{seed.get('schema_version', 'N/A')}",
        "",
        "## Source",
        "",
        f"- **Repository:** {source.get('repo', 'N/A')}",
        f"- **Workflow:** {source.get('workflow_name', 'N/A')}",
        f"- **Run ID:** {source.get('run_id', 'N/A')}",
        f"- **Run Attempt:** {source.get('run_attempt', 'N/A')}",
        f"- **Commit:** {source.get('head_sha', 'N/A')[:8]}",
        f"- **Ref:** {source.get('ref', 'N/A')}",
        "",
        "## Normalized Report",
        "",
        f"- **Schema:** v{report.get('schema_version', 'N/A')}",
        f"- **Conclusion:** {report.get('conclusion', 'N/A').upper()}",
        "",
        "### Counts",
        "",
        f"- **Total Checks:** {counts.get('checks_total', 'N/A')}",
        f"- **Passed:** {counts.get('checks_passed', 'N/A')}",
        f"- **Failed:** {counts.get('checks_failed', 'N/A')}",
        f"- **Policy Findings:** {counts.get('policy_findings_total', 'N/A')}",
        "",
        "### Determinism",
        "",
        f"- **Hash:** {determinism.get('hash', 'N/A')}",
        f"- **Is Deterministic:** {determinism.get('is_deterministic', 'N/A')}",
        "",
        "## Consumer",
        "",
        f"- **Name:** {consumer.get('name', 'N/A')}",
        f"- **Version:** {consumer.get('version', 'N/A')}",
    ]

    if consumer.get("commit_sha"):
        lines.append(f"- **Commit:** {consumer['commit_sha'][:8]}")

    if seed.get("notes"):
        lines.extend(["", "## Notes", "", seed["notes"]])

    return "\n".join(lines) + "\n"
