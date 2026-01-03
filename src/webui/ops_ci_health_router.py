"""
Peak_Trade: CI & Governance Health API
======================================

Ops Dashboard v0.1: CI & Governance Health Panel

Führt lokale CI-Checks aus und zeigt Status als Ampel:
- Contract Guard (check_required_ci_contexts_present.sh)
- Docs Reference Validation (verify_docs_reference_targets.sh --changed)

Endpoints:
- GET /ops/ci-health - HTML dashboard page
- GET /ops/ci-health/status - JSON API für health checks

Safety:
- Offline-lokal, keine externen Secrets
- Read-only checks, keine destructive operations
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/ops/ci-health", tags=["ops", "ci-health"])

# Global config (set by app during initialization)
_REPO_ROOT: Optional[Path] = None
_TEMPLATES: Optional[Jinja2Templates] = None


@dataclass
class HealthCheckResult:
    """Result of a single health check."""

    check_id: str
    title: str
    description: str
    status: str  # "OK", "FAIL", "WARN", "SKIP"
    exit_code: int
    output: str
    error_excerpt: str  # First 20 lines of output on failure
    duration_ms: int
    timestamp: str
    script_path: str
    docs_refs: List[str]


def set_ci_health_config(repo_root: Path, templates: Jinja2Templates) -> None:
    """
    Configure CI Health router with paths.

    Args:
        repo_root: Path to repository root
        templates: Jinja2Templates instance
    """
    global _REPO_ROOT, _TEMPLATES
    _REPO_ROOT = repo_root
    _TEMPLATES = templates
    logger.info(f"CI Health router configured: repo_root={repo_root}")


def get_repo_root() -> Path:
    """Get configured repo root or raise error."""
    if _REPO_ROOT is None:
        raise RuntimeError("CI Health router not configured. Call set_ci_health_config() first.")
    return _REPO_ROOT


def get_templates() -> Jinja2Templates:
    """Get configured templates or raise error."""
    if _TEMPLATES is None:
        raise RuntimeError("CI Health router not configured. Call set_ci_health_config() first.")
    return _TEMPLATES


def _run_check(
    check_id: str,
    title: str,
    description: str,
    script_path: Path,
    args: List[str],
    docs_refs: List[str],
    timeout: int = 30,
) -> HealthCheckResult:
    """
    Run a single health check script.

    Args:
        check_id: Unique identifier for the check
        title: Human-readable title
        description: Short description
        script_path: Path to the script
        args: Arguments to pass to the script
        docs_refs: List of documentation references
        timeout: Timeout in seconds

    Returns:
        HealthCheckResult object
    """
    start_time = datetime.now()

    if not script_path.exists():
        return HealthCheckResult(
            check_id=check_id,
            title=title,
            description=description,
            status="SKIP",
            exit_code=-1,
            output=f"Script not found: {script_path}",
            error_excerpt="",
            duration_ms=0,
            timestamp=start_time.isoformat(),
            script_path=str(script_path),
            docs_refs=docs_refs,
        )

    try:
        cmd = ["bash", str(script_path)] + args
        result = subprocess.run(
            cmd,
            cwd=str(get_repo_root()),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Combine stdout and stderr
        output = result.stdout + result.stderr
        output = output.strip()

        # Determine status
        if result.returncode == 0:
            status = "OK"
        elif result.returncode == 2:
            status = "WARN"
        else:
            status = "FAIL"

        # Extract error excerpt (first 20 lines on failure)
        error_excerpt = ""
        if status in ["FAIL", "WARN"]:
            lines = output.split("\n")
            error_excerpt = "\n".join(lines[:20])

        return HealthCheckResult(
            check_id=check_id,
            title=title,
            description=description,
            status=status,
            exit_code=result.returncode,
            output=output,
            error_excerpt=error_excerpt,
            duration_ms=duration_ms,
            timestamp=start_time.isoformat(),
            script_path=str(script_path),
            docs_refs=docs_refs,
        )

    except subprocess.TimeoutExpired:
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        return HealthCheckResult(
            check_id=check_id,
            title=title,
            description=description,
            status="FAIL",
            exit_code=-1,
            output=f"Timeout after {timeout}s",
            error_excerpt=f"Script timed out after {timeout} seconds",
            duration_ms=duration_ms,
            timestamp=start_time.isoformat(),
            script_path=str(script_path),
            docs_refs=docs_refs,
        )

    except Exception as e:
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        return HealthCheckResult(
            check_id=check_id,
            title=title,
            description=description,
            status="FAIL",
            exit_code=-1,
            output=str(e),
            error_excerpt=str(e),
            duration_ms=duration_ms,
            timestamp=start_time.isoformat(),
            script_path=str(script_path),
            docs_refs=docs_refs,
        )


def _run_all_checks() -> List[HealthCheckResult]:
    """
    Run all configured CI & Governance health checks.

    Returns:
        List of HealthCheckResult objects
    """
    repo_root = get_repo_root()
    results = []

    # Check 1: Contract Guard (required CI contexts)
    check1 = _run_check(
        check_id="contract_guard",
        title="Contract Guard",
        description="Verifiziert, dass alle required CI contexts korrekt konfiguriert sind",
        script_path=repo_root / "scripts/ops/check_required_ci_contexts_present.sh",
        args=[],
        docs_refs=[
            "docs/ops/runbooks/github_rulesets_pr_reviews_policy.md",
            "docs/ops/README.md",
        ],
    )
    results.append(check1)

    # Check 2: Docs Reference Validation (changed files only)
    check2 = _run_check(
        check_id="docs_reference_validation",
        title="Docs Reference Validation",
        description="Prüft, ob alle Markdown-Links auf existierende Dateien zeigen (nur geänderte Dateien)",
        script_path=repo_root / "scripts/ops/verify_docs_reference_targets.sh",
        args=["--changed", "--warn-only"],
        docs_refs=[
            "docs/ops/README.md",
        ],
    )
    results.append(check2)

    return results


# =============================================================================
# API ENDPOINTS
# =============================================================================


@router.get("/status")
async def get_ci_health_status() -> Dict[str, Any]:
    """
    JSON API: Get CI & Governance health status.

    Returns:
        Dict with health check results and summary.
    """
    results = _run_all_checks()

    # Compute summary
    total = len(results)
    ok_count = sum(1 for r in results if r.status == "OK")
    warn_count = sum(1 for r in results if r.status == "WARN")
    fail_count = sum(1 for r in results if r.status == "FAIL")
    skip_count = sum(1 for r in results if r.status == "SKIP")

    overall_status = "OK"
    if fail_count > 0:
        overall_status = "FAIL"
    elif warn_count > 0:
        overall_status = "WARN"

    return {
        "overall_status": overall_status,
        "summary": {
            "total": total,
            "ok": ok_count,
            "warn": warn_count,
            "fail": fail_count,
            "skip": skip_count,
        },
        "checks": [
            {
                "check_id": r.check_id,
                "title": r.title,
                "description": r.description,
                "status": r.status,
                "exit_code": r.exit_code,
                "output": r.output,
                "error_excerpt": r.error_excerpt,
                "duration_ms": r.duration_ms,
                "timestamp": r.timestamp,
                "script_path": r.script_path,
                "docs_refs": r.docs_refs,
            }
            for r in results
        ],
        "generated_at": datetime.now().isoformat(),
    }


# =============================================================================
# HTML DASHBOARD ENDPOINT
# =============================================================================


@router.get("", response_class=HTMLResponse)
async def ci_health_dashboard(request: Request) -> Any:
    """
    HTML Dashboard: CI & Governance Health Panel.

    Shows:
    - Status cards (OK/FAIL/WARN) für jeden Check
    - Letzte Laufzeit
    - Kurzer Fehlerauszug (max 20 Zeilen)
    - Links zu Dokumentation
    """
    templates = get_templates()
    results = _run_all_checks()

    # Compute summary
    total = len(results)
    ok_count = sum(1 for r in results if r.status == "OK")
    warn_count = sum(1 for r in results if r.status == "WARN")
    fail_count = sum(1 for r in results if r.status == "FAIL")
    skip_count = sum(1 for r in results if r.status == "SKIP")

    overall_status = "OK"
    if fail_count > 0:
        overall_status = "FAIL"
    elif warn_count > 0:
        overall_status = "WARN"

    context = {
        "request": request,
        "results": results,
        "summary": {
            "total": total,
            "ok": ok_count,
            "warn": warn_count,
            "fail": fail_count,
            "skip": skip_count,
        },
        "overall_status": overall_status,
        "repo_root": str(get_repo_root()),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return templates.TemplateResponse(request, "ops_ci_health.html", context)
