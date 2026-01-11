"""
Validator Report Schema (Phase 4E)

Normalized, versioned schema for determinism contract validator reports.

Design Principles:
- Schema-first: validator_report.normalized.json is canonical
- Deterministic: stable ordering, sorted keys, no volatile fields in canonical section
- Versioned: schema_version field for forward compatibility
- Machine-readable: structured checks[] array with stable IDs
- Evidence-first: clear separation of canonical vs runtime_context

Reference:
- docs/governance/ai_autonomy/PHASE4E_VALIDATOR_REPORT_NORMALIZATION.md

Usage:
    from src.ai_orchestration.validator_report_schema import (
        ValidatorReport,
        ValidationCheck,
        ValidationResult,
    )

    report = ValidatorReport(
        schema_version="1.0.0",
        tool=ToolInfo(name="l4_critic_determinism_contract_validator", version="1.0.0"),
        subject="l4_critic_determinism_contract",
        result=ValidationResult.PASS,
        checks=[...],
        summary=SummaryMetrics(passed=1, failed=0, total=1),
    )

    # Write deterministic JSON
    report.write_json(out_dir / "validator_report.normalized.json")

    # Generate derived markdown
    report.write_summary_md(out_dir / "validator_report.normalized.md")
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field
    from pydantic import __version__ as pydantic_version

    PYDANTIC_V2 = pydantic_version.startswith("2.")
except ImportError:
    raise ImportError("Pydantic is required for validator report schema")


# =============================================================================
# Constants
# =============================================================================

VALIDATOR_REPORT_SCHEMA_VERSION = "1.0.0"


# =============================================================================
# Enums
# =============================================================================


class ValidationResult(str, Enum):
    """Validation result values."""

    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"  # Invalid input / runtime error


class CheckStatus(str, Enum):
    """Individual check status values."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


# =============================================================================
# Models
# =============================================================================


class ToolInfo(BaseModel):
    """Tool information."""

    name: str = Field(..., description="Tool name")
    version: str = Field(..., description="Tool version (semver)")

    if PYDANTIC_V2:
        model_config = {"extra": "forbid"}
    else:

        class Config:
            extra = "forbid"


class ValidationCheck(BaseModel):
    """Individual validation check."""

    id: str = Field(..., description="Stable check ID (snake_case)")
    status: CheckStatus = Field(..., description="Check status")
    message: str = Field(..., description="Short message")
    metrics: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional metrics (deterministic values only)"
    )

    if PYDANTIC_V2:
        model_config = {"extra": "forbid"}
    else:

        class Config:
            extra = "forbid"


class SummaryMetrics(BaseModel):
    """Summary metrics."""

    passed: int = Field(..., description="Number of checks passed")
    failed: int = Field(..., description="Number of checks failed")
    total: int = Field(..., description="Total number of checks")

    if PYDANTIC_V2:
        model_config = {"extra": "forbid"}
    else:

        class Config:
            extra = "forbid"


class Evidence(BaseModel):
    """Evidence references."""

    baseline: Optional[str] = Field(default=None, description="Baseline artifact path")
    candidate: Optional[str] = Field(default=None, description="Candidate artifact path")
    diff: Optional[str] = Field(default=None, description="Diff artifact path (if available)")

    if PYDANTIC_V2:
        model_config = {"extra": "forbid"}
    else:

        class Config:
            extra = "forbid"


class RuntimeContext(BaseModel):
    """
    Runtime context (volatile fields allowed).

    This section is isolated from canonical comparison.
    Fields here may vary between runs and should not affect determinism.
    """

    git_sha: Optional[str] = Field(default=None, description="Git commit SHA")
    run_id: Optional[str] = Field(default=None, description="CI run ID")
    workflow: Optional[str] = Field(default=None, description="CI workflow name")
    job: Optional[str] = Field(default=None, description="CI job name")
    generated_at_utc: Optional[str] = Field(
        default=None, description="Generation timestamp (ISO 8601 UTC)"
    )

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}  # Allow additional context fields
    else:

        class Config:
            extra = "allow"


class ValidatorReport(BaseModel):
    """
    Normalized Validator Report (Schema v1.0.0).

    This is the canonical artifact for validator runs.
    All other outputs (validator_report.normalized.md) are derived from this.
    """

    schema_version: str = Field(..., description="Schema version (semver)")
    tool: ToolInfo = Field(..., description="Tool information")
    subject: str = Field(..., description="Subject being validated (e.g., 'l4_critic_determinism_contract')")
    result: ValidationResult = Field(..., description="Overall validation result")
    checks: List[ValidationCheck] = Field(default_factory=list, description="Individual checks")
    summary: SummaryMetrics = Field(..., description="Summary metrics")
    evidence: Optional[Evidence] = Field(default=None, description="Evidence references")
    runtime_context: Optional[RuntimeContext] = Field(
        default=None, description="Runtime context (volatile fields)"
    )

    if PYDANTIC_V2:
        model_config = {"extra": "forbid"}
    else:

        class Config:
            extra = "forbid"

    def to_canonical_dict(self) -> Dict[str, Any]:
        """
        Convert to canonical dictionary for deterministic serialization.

        Ensures:
        - Stable key ordering (sorted)
        - Stable list ordering (checks sorted by id)
        - Runtime context excluded from canonical representation
        """
        if PYDANTIC_V2:
            data = self.model_dump()
        else:
            data = self.dict()

        # Sort checks by id for stable ordering
        if "checks" in data and data["checks"]:
            data["checks"] = sorted(data["checks"], key=lambda c: c["id"])

        # Remove runtime_context from canonical dict (volatile)
        if "runtime_context" in data:
            del data["runtime_context"]

        return data

    def write_json(self, path: Path, deterministic: bool = True) -> None:
        """
        Write report as JSON.

        Args:
            path: Output path
            deterministic: If True, use canonical serialization (sorted keys, no runtime_context)
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        if deterministic:
            data = self.to_canonical_dict()
        else:
            if PYDANTIC_V2:
                data = self.model_dump()
            else:
                data = self.dict()

        json_str = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
        path.write_text(json_str + "\n", encoding="utf-8")

    def write_summary_md(self, path: Path) -> None:
        """
        Write human-readable summary as Markdown.

        Derived from JSON (not a source of truth).
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Validator Report Summary",
            "",
            f"**Schema Version:** {self.schema_version}",
            f"**Tool:** {self.tool.name} v{self.tool.version}",
            f"**Subject:** {self.subject}",
            f"**Result:** {self.result.value}",
            "",
            "## Summary",
            "",
            f"- **Passed:** {self.summary.passed}",
            f"- **Failed:** {self.summary.failed}",
            f"- **Total:** {self.summary.total}",
            "",
        ]

        if self.checks:
            lines.extend([
                "## Checks",
                "",
            ])
            for check in sorted(self.checks, key=lambda c: c.id):
                status_emoji = "✅" if check.status == CheckStatus.PASS else "❌"
                lines.append(f"### {status_emoji} {check.id}")
                lines.append("")
                lines.append(f"**Status:** {check.status.value}")
                lines.append(f"**Message:** {check.message}")
                if check.metrics:
                    lines.append("")
                    lines.append("**Metrics:**")
                    for key, value in sorted(check.metrics.items()):
                        lines.append(f"- `{key}`: {value}")
                lines.append("")

        if self.evidence:
            lines.extend([
                "## Evidence",
                "",
            ])
            if self.evidence.baseline:
                lines.append(f"- **Baseline:** `{self.evidence.baseline}`")
            if self.evidence.candidate:
                lines.append(f"- **Candidate:** `{self.evidence.candidate}`")
            if self.evidence.diff:
                lines.append(f"- **Diff:** `{self.evidence.diff}`")
            lines.append("")

        if self.runtime_context:
            lines.extend([
                "## Runtime Context",
                "",
            ])
            if self.runtime_context.git_sha:
                lines.append(f"- **Git SHA:** `{self.runtime_context.git_sha}`")
            if self.runtime_context.run_id:
                lines.append(f"- **Run ID:** `{self.runtime_context.run_id}`")
            if self.runtime_context.workflow:
                lines.append(f"- **Workflow:** `{self.runtime_context.workflow}`")
            if self.runtime_context.job:
                lines.append(f"- **Job:** `{self.runtime_context.job}`")
            if self.runtime_context.generated_at_utc:
                lines.append(f"- **Generated At (UTC):** {self.runtime_context.generated_at_utc}")
            lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")

    @classmethod
    def from_legacy_validator_report(
        cls,
        legacy_report: Dict[str, Any],
        runtime_context: Optional[RuntimeContext] = None,
    ) -> ValidatorReport:
        """
        Convert legacy validator report (Phase 4D) to normalized format.

        Args:
            legacy_report: Legacy validator report dict (from Phase 4D)
            runtime_context: Optional runtime context to attach

        Returns:
            Normalized ValidatorReport instance
        """
        # Extract fields from legacy format
        validator_info = legacy_report.get("validator", {})
        tool_name = validator_info.get("name", "unknown_validator")
        tool_version = validator_info.get("version", "unknown")

        contract_version = legacy_report.get("contract_version", "unknown")
        inputs = legacy_report.get("inputs", {})
        result_data = legacy_report.get("result", {})

        # Determine overall result
        is_equal = result_data.get("equal", False)
        overall_result = ValidationResult.PASS if is_equal else ValidationResult.FAIL

        # Build checks array
        checks = []

        # Check 1: Determinism check
        determinism_check = ValidationCheck(
            id="determinism_contract_validation",
            status=CheckStatus.PASS if is_equal else CheckStatus.FAIL,
            message=result_data.get("diff_summary", "No summary available"),
            metrics={
                "baseline_hash": result_data.get("baseline_hash", "unknown"),
                "candidate_hash": result_data.get("candidate_hash", "unknown"),
                "first_mismatch_path": result_data.get("first_mismatch_path", None),
            },
        )
        checks.append(determinism_check)

        # Summary metrics
        summary = SummaryMetrics(
            passed=1 if is_equal else 0,
            failed=0 if is_equal else 1,
            total=1,
        )

        # Evidence
        evidence = Evidence(
            baseline=inputs.get("baseline"),
            candidate=inputs.get("candidate"),
        )

        return cls(
            schema_version=VALIDATOR_REPORT_SCHEMA_VERSION,
            tool=ToolInfo(name=tool_name, version=tool_version),
            subject=f"l4_critic_determinism_contract_v{contract_version}",
            result=overall_result,
            checks=checks,
            summary=summary,
            evidence=evidence,
            runtime_context=runtime_context,
        )
