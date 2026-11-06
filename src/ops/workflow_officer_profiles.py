"""Workflow Officer profile plans: check commands + v1 metadata (surface, category, description, severity)."""

from __future__ import annotations

import sys
from typing import Any


def _py(*args: str) -> list[str]:
    return [sys.executable, *args]


def _bash(script: str) -> list[str]:
    return ["bash", script]


DOCS_ONLY_PR: list[dict[str, Any]] = [
    {
        "check_id": "docs_token_policy",
        "command": _py("scripts/ops/validate_docs_token_policy.py"),
        "severity": "hard_fail",
        "surface": "docs",
        "category": "documentation",
        "description": "Validates docs token policy for changed Markdown (inline path tokens).",
    },
    {
        "check_id": "docs_graph_triage",
        "command": _py("scripts/ops/docs_graph_triage.py"),
        "severity": "warn",
        "surface": "docs",
        "category": "documentation",
        "description": "Docs graph triage for broken references and structural issues.",
    },
    {
        "check_id": "error_taxonomy_adoption",
        "command": _py("scripts/audit/check_error_taxonomy_adoption.py"),
        "severity": "warn",
        "surface": "docs",
        "category": "governance",
        "description": "Audit adoption of the error taxonomy across the codebase.",
    },
]

OPS_LOCAL_ENV: list[dict[str, Any]] = [
    {
        "check_id": "ops_doctor_shell",
        "command": _bash("scripts/ops/ops_doctor.sh"),
        "severity": "warn",
        "surface": "local_ops",
        "category": "environment",
        "description": "Local ops doctor shell checks (read-only diagnostics).",
    },
    {
        "check_id": "docker_desktop_preflight_readonly",
        "command": _bash("scripts/ops/docker_desktop_preflight_readonly.sh"),
        "severity": "warn",
        "surface": "local_ops",
        "category": "environment",
        "description": "Docker Desktop preflight in read-only mode.",
    },
    {
        "check_id": "mcp_smoke_preflight",
        "command": _bash("scripts/ops/mcp_smoke_preflight.sh"),
        "severity": "warn",
        "surface": "local_ops",
        "category": "tooling",
        "description": "MCP smoke preflight for configured integrations.",
    },
    {
        "check_id": "failure_analysis",
        "command": _bash("scripts/ops/analyze_failures.sh"),
        "severity": "info",
        "surface": "local_ops",
        "category": "diagnostics",
        "description": "Failure analysis helper output (informational).",
    },
]

LIVE_PILOT_PREFLIGHT: list[dict[str, Any]] = [
    {
        "check_id": "docker_desktop_preflight_readonly",
        "command": _bash("scripts/ops/docker_desktop_preflight_readonly.sh"),
        "severity": "hard_fail",
        "surface": "pilot_preflight",
        "category": "environment",
        "description": "Docker Desktop preflight (required before pilot-related work).",
    },
    {
        "check_id": "mcp_smoke_preflight",
        "command": _bash("scripts/ops/mcp_smoke_preflight.sh"),
        "severity": "warn",
        "surface": "pilot_preflight",
        "category": "tooling",
        "description": "MCP smoke preflight for pilot workflows.",
    },
]

PROFILES: dict[str, list[dict[str, Any]]] = {
    "docs_only_pr": DOCS_ONLY_PR,
    "ops_local_env": OPS_LOCAL_ENV,
    "live_pilot_preflight": LIVE_PILOT_PREFLIGHT,
}

PROFILE_POLICY: dict[str, dict[str, str]] = {
    profile: {entry["check_id"]: entry["severity"] for entry in checks}
    for profile, checks in PROFILES.items()
}

__all__ = ["PROFILES", "PROFILE_POLICY"]
