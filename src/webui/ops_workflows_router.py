"""
Peak_Trade: Ops Workflow Hub API
=================================

Phase: Ops Workflow Dashboard
Read-only listing of ops workflow scripts with metadata and copy-paste commands.

Endpoints:
- GET /ops/workflows - HTML dashboard page
- GET /api/ops/workflows - JSON API for automation/tooling

Safety:
- Read-only, no script execution
- No GitHub API calls, no side effects
- File metadata only (exists, size, mtime)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/ops/workflows", tags=["ops", "workflows"])

# Global config (set by app during initialization)
_REPO_ROOT: Optional[Path] = None
_TEMPLATES: Optional[Jinja2Templates] = None


@dataclass
class WorkflowScript:
    """Metadata for an ops workflow script."""

    id: str
    title: str
    description: str
    script_path: str
    commands: List[str]
    docs_refs: List[str]
    exists: bool = False
    size_bytes: Optional[int] = None
    last_modified: Optional[str] = None


def set_workflows_config(repo_root: Path, templates: Jinja2Templates) -> None:
    """
    Configure Workflows router with paths.

    Args:
        repo_root: Path to repository root
        templates: Jinja2Templates instance
    """
    global _REPO_ROOT, _TEMPLATES
    _REPO_ROOT = repo_root
    _TEMPLATES = templates
    logger.info(f"Workflows router configured: repo_root={repo_root}")


def get_repo_root() -> Path:
    """Get configured repo root or raise error."""
    if _REPO_ROOT is None:
        raise RuntimeError("Workflows router not configured. Call set_workflows_config() first.")
    return _REPO_ROOT


def get_templates() -> Jinja2Templates:
    """Get configured templates or raise error."""
    if _TEMPLATES is None:
        raise RuntimeError("Workflows router not configured. Call set_workflows_config() first.")
    return _TEMPLATES


def _get_workflow_definitions() -> List[Dict[str, Any]]:
    """
    Define the 4 core ops workflow scripts.

    Returns:
        List of workflow definitions (without filesystem metadata).
    """
    return [
        {
            "id": "post_merge_pr203",
            "title": "Post-Merge Workflow PR203",
            "description": (
                "Vollständiger Post-Merge Workflow für PR #203 (Phase 16L). "
                "Führt Tests aus, generiert Reports und erstellt finale Dokumentation."
            ),
            "script_path": "scripts/post_merge_workflow_pr203.sh",
            "commands": [
                "bash scripts/post_merge_workflow_pr203.sh",
            ],
            "docs_refs": [
                "docs/ops/WORKFLOW_SCRIPTS.md",
                "docs/ops/PR_203_MERGE_LOG.md",
            ],
        },
        {
            "id": "quick_pr_merge",
            "title": "Quick PR Merge",
            "description": (
                "Schnelles PR-Merge Script. Merged einen PR via GitHub CLI (gh) "
                "und checkt lokal den main-Branch aus."
            ),
            "script_path": "scripts/quick_pr_merge.sh",
            "commands": [
                "bash scripts/quick_pr_merge.sh <PR_NUMBER>",
            ],
            "docs_refs": [
                "docs/ops/WORKFLOW_SCRIPTS.md",
                "docs/ops/README.md",
            ],
        },
        {
            "id": "post_merge_workflow",
            "title": "Post-Merge Workflow (Generic)",
            "description": (
                "Generischer Post-Merge Workflow. Führt Tests aus, generiert Reports "
                "und erstellt Dokumentation nach jedem PR-Merge."
            ),
            "script_path": "scripts/post_merge_workflow.sh",
            "commands": [
                "bash scripts/post_merge_workflow.sh",
            ],
            "docs_refs": [
                "docs/ops/WORKFLOW_SCRIPTS.md",
                "docs/ops/README.md",
                "docs/PEAK_TRADE_STATUS_OVERVIEW.md",
            ],
        },
        {
            "id": "finalize_workflow_docs_pr",
            "title": "Finalize Workflow Docs PR",
            "description": (
                "Finalisiert Workflow-Dokumentation und erstellt PR. "
                "Generiert Zusammenfassungen und bereitet Merge-Log vor."
            ),
            "script_path": "scripts/finalize_workflow_docs_pr.sh",
            "commands": [
                "bash scripts/finalize_workflow_docs_pr.sh",
            ],
            "docs_refs": [
                "docs/ops/WORKFLOW_SCRIPTS.md",
            ],
        },
    ]


def _enrich_with_filesystem_metadata(workflows: List[Dict[str, Any]]) -> List[WorkflowScript]:
    """
    Enrich workflow definitions with filesystem metadata.

    Args:
        workflows: List of workflow definitions

    Returns:
        List of WorkflowScript objects with filesystem metadata
    """
    repo_root = get_repo_root()
    enriched = []

    for wf in workflows:
        script_path = repo_root / wf["script_path"]

        # Check existence and metadata
        exists = script_path.exists()
        size_bytes = None
        last_modified = None

        if exists:
            try:
                stat = script_path.stat()
                size_bytes = stat.st_size
                last_modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                logger.warning(f"Failed to get metadata for {script_path}: {e}")

        enriched.append(
            WorkflowScript(
                id=wf["id"],
                title=wf["title"],
                description=wf["description"],
                script_path=wf["script_path"],
                commands=wf["commands"],
                docs_refs=wf["docs_refs"],
                exists=exists,
                size_bytes=size_bytes,
                last_modified=last_modified,
            )
        )

    return enriched


# =============================================================================
# API ENDPOINTS
# =============================================================================


@router.get("/list")
async def get_workflows_json() -> List[Dict[str, Any]]:
    """
    JSON API: Get list of workflow scripts with metadata.

    Returns:
        List of workflow objects (id, title, description, script_path, commands, docs_refs, exists, size_bytes, last_modified).
    """
    workflow_defs = _get_workflow_definitions()
    workflows = _enrich_with_filesystem_metadata(workflow_defs)

    return [asdict(wf) for wf in workflows]


# =============================================================================
# HTML DASHBOARD ENDPOINTS
# =============================================================================


@router.get("", response_class=HTMLResponse)
async def workflows_dashboard(request: Request) -> Any:
    """
    HTML Dashboard: Ops Workflow Hub.

    Lists all ops workflow scripts with metadata and copy-paste commands.
    """
    workflow_defs = _get_workflow_definitions()
    workflows = _enrich_with_filesystem_metadata(workflow_defs)

    templates = get_templates()
    repo_root = get_repo_root()

    context = {
        "request": request,
        "workflows": workflows,
        "repo_root": str(repo_root),
    }

    return templates.TemplateResponse(request, "ops_workflows.html", context)
