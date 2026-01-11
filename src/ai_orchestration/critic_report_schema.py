"""
L4 Governance Critic Report Schema (Phase 4C)

Pydantic models for standardized, deterministic, schema-versioned critic reports.

Design Principles:
- Schema-first: critic_report.json is the source of truth
- Deterministic: stable ordering, canonical JSON, no volatile fields
- Versioned: schema_version field for evolution
- Derived outputs: critic_summary.md generated from JSON

Reference:
- docs/governance/ai_autonomy/PHASE4C_CRITIC_HARDENING.md
- docs/governance/ai_autonomy/PHASE4_L1_L4_INTEGRATION.md

Usage:
    from src.ai_orchestration.critic_report_schema import CriticReport, CriticFinding

    report = CriticReport(
        schema_version="1.0.0",
        pack_id="L1_sample_2026-01-10",
        mode="replay",
        ...
    )

    # Write deterministic JSON
    report.write_json(out_dir / "critic_report.json")

    # Generate derived markdown
    report.write_summary_md(out_dir / "critic_summary.md")
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
    raise ImportError("Pydantic is required for critic report schema")


# =============================================================================
# Enums
# =============================================================================


class Verdict(str, Enum):
    """Critic verdict values."""

    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


class RiskLevel(str, Enum):
    """Risk level values."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Severity(str, Enum):
    """Finding severity values."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FindingStatus(str, Enum):
    """Finding status values."""

    OPEN = "OPEN"
    ACK = "ACK"
    CLOSED = "CLOSED"


# =============================================================================
# Models
# =============================================================================


class CriticInfo(BaseModel):
    """Critic identity information."""

    name: str = Field(..., description="Critic name (e.g., 'L4_Governance_Critic')")
    version: str = Field(..., description="Critic version")

    if PYDANTIC_V2:
        model_config = {"extra": "forbid"}
    else:

        class Config:
            extra = "forbid"


class InputMetadata(BaseModel):
    """Input metadata for the critic run."""

    evidence_pack_path: str = Field(..., description="Path to evidence pack (normalized)")
    fixture: Optional[str] = Field(None, description="Fixture ID if used")
    schema_version_in: str = Field(..., description="Input evidence pack schema version")

    if PYDANTIC_V2:
        model_config = {"extra": "forbid"}
    else:

        class Config:
            extra = "forbid"


class SummaryMetrics(BaseModel):
    """Summary metrics for the critic report."""

    verdict: Verdict = Field(..., description="Overall verdict (PASS/FAIL/WARN)")
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    score: Optional[float] = Field(None, description="Numeric score if applicable")
    finding_counts: Dict[str, int] = Field(
        default_factory=dict, description="Counts by severity (high/med/low/info)"
    )

    if PYDANTIC_V2:
        model_config = {"extra": "forbid"}
    else:

        class Config:
            extra = "forbid"


class CriticFinding(BaseModel):
    """A single finding from the critic."""

    id: str = Field(..., description="Unique finding ID")
    title: str = Field(..., description="Finding title")
    severity: Severity = Field(..., description="Severity level")
    status: FindingStatus = Field(default=FindingStatus.OPEN, description="Finding status")
    rationale: str = Field(..., description="Rationale for this finding")
    evidence_refs: List[str] = Field(default_factory=list, description="Evidence IDs referenced")
    metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Associated metrics (scalar values)"
    )

    if PYDANTIC_V2:
        model_config = {"extra": "forbid"}
    else:

        class Config:
            extra = "forbid"


class CanonicalRules(BaseModel):
    """Canonicalization rules applied for determinism."""

    rules: List[str] = Field(
        default_factory=lambda: ["sorted_keys", "sorted_lists", "normalized_paths"],
        description="List of canonicalization rules applied",
    )

    if PYDANTIC_V2:
        model_config = {"extra": "forbid"}
    else:

        class Config:
            extra = "forbid"


class MetaInfo(BaseModel):
    """Meta-information about the report generation."""

    deterministic: bool = Field(..., description="Whether deterministic mode was used")
    canonicalization: CanonicalRules = Field(
        default_factory=CanonicalRules, description="Canonicalization rules"
    )
    created_at: Optional[str] = Field(
        None, description="Creation timestamp (ISO8601, optional in deterministic mode)"
    )

    if PYDANTIC_V2:
        model_config = {"extra": "forbid"}
    else:

        class Config:
            extra = "forbid"


class CriticReport(BaseModel):
    """
    L4 Governance Critic Report (Schema v1.0.0).

    This is the authoritative artifact for critic runs.
    All other outputs (critic_summary.md) are derived from this.
    """

    schema_version: str = Field(..., description="Schema version (semver)")
    pack_id: str = Field(..., description="Evidence pack ID being reviewed")
    mode: str = Field(..., description="Run mode (replay/live_disabled/dry)")
    critic: CriticInfo = Field(..., description="Critic information")
    inputs: InputMetadata = Field(..., description="Input metadata")
    summary: SummaryMetrics = Field(..., description="Summary metrics")
    findings: List[CriticFinding] = Field(default_factory=list, description="Detailed findings")
    meta: MetaInfo = Field(..., description="Meta-information")

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
        - Stable list ordering (findings sorted by severity desc, then id)
        - Normalized paths (repo-relative if deterministic)
        """
        if PYDANTIC_V2:
            data = self.model_dump()
        else:
            data = self.dict()

        # Sort findings: severity desc (HIGH > MEDIUM > LOW > INFO), then by id
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
        if "findings" in data and data["findings"]:
            data["findings"] = sorted(
                data["findings"],
                key=lambda f: (severity_order.get(f["severity"], 99), f["id"]),
            )

        return data

    def write_json(self, path: Path, deterministic: bool = True) -> None:
        """
        Write critic report to JSON file (deterministic, canonical).

        Args:
            path: Output file path
            deterministic: If True, use canonical ordering and stable formatting
        """
        data = self.to_canonical_dict()

        with open(path, "w") as f:
            json.dump(
                data,
                f,
                indent=2,
                sort_keys=True,  # Deterministic key ordering
                ensure_ascii=False,
            )
            f.write("\n")  # Trailing newline for git-friendliness

    def write_summary_md(self, path: Path) -> None:
        """
        Write human-readable summary markdown (derived from JSON).

        This is a pure derivation - no additional computation.
        """
        lines = [
            "# L4 Governance Critic Summary",
            "",
            f"**Schema Version:** {self.schema_version}  ",
            f"**Pack ID:** {self.pack_id}  ",
            f"**Mode:** {self.mode}  ",
            f"**Deterministic:** {self.meta.deterministic}  ",
            "",
            "---",
            "",
            "## Verdict",
            "",
            f"- **Overall:** {self.summary.verdict.value}",
            f"- **Risk Level:** {self.summary.risk_level.value}",
        ]

        if self.summary.score is not None:
            lines.append(f"- **Score:** {self.summary.score:.2f}")

        lines.extend(
            [
                "",
                "## Finding Counts",
                "",
            ]
        )

        for sev in ["high", "med", "low", "info"]:
            count = self.summary.finding_counts.get(sev, 0)
            lines.append(f"- **{sev.upper()}:** {count}")

        lines.extend(
            [
                "",
                "## Top Findings",
                "",
            ]
        )

        if not self.findings:
            lines.append("*No findings.*")
        else:
            for finding in self.findings[:10]:  # Top 10
                lines.extend(
                    [
                        f"### {finding.id}: {finding.title}",
                        "",
                        f"- **Severity:** {finding.severity.value}",
                        f"- **Status:** {finding.status.value}",
                        f"- **Rationale:** {finding.rationale}",
                    ]
                )

                if finding.evidence_refs:
                    lines.append(f"- **Evidence:** {', '.join(finding.evidence_refs)}")

                if finding.metrics:
                    lines.append("- **Metrics:**")
                    for k, v in sorted(finding.metrics.items()):
                        lines.append(f"  - `{k}`: {v}")

                lines.append("")

        lines.extend(
            [
                "---",
                "",
                "## Statistics",
                "",
                f"- **Total Findings:** {len(self.findings)}",
                f"- **Critic:** {self.critic.name} v{self.critic.version}",
                f"- **Input Schema:** {self.inputs.schema_version_in}",
            ]
        )

        if self.inputs.fixture:
            lines.append(f"- **Fixture:** {self.inputs.fixture}")

        lines.extend(
            [
                "",
                "---",
                "",
                f"*Generated from `critic_report.json` (schema v{self.schema_version})*",
                "",
            ]
        )

        with open(path, "w") as f:
            f.write("\n".join(lines))


# =============================================================================
# Helper Functions
# =============================================================================


def normalize_path_for_determinism(path: Path, deterministic: bool) -> str:
    """
    Normalize path for deterministic output.

    In deterministic mode:
    - Use repo-relative paths (no absolute paths)
    - Strip volatile components (temp dirs, timestamps in paths)

    Args:
        path: Input path
        deterministic: If True, apply normalization

    Returns:
        Normalized path string
    """
    if not deterministic:
        return str(path)

    # Convert to relative path if absolute
    path_str = str(path)

    # Try to make relative to common repo roots
    for prefix in ["/Users/", "/home/", "/tmp/", "C:\\Users\\"]:
        if path_str.startswith(prefix):
            # Extract relevant parts after user/temp dirs
            parts = Path(path_str).parts
            if "Peak_Trade" in parts:
                idx = parts.index("Peak_Trade")
                return str(Path(*parts[idx:]))
            if "tests" in parts:
                idx = parts.index("tests")
                return str(Path(*parts[idx:]))

    return path_str
