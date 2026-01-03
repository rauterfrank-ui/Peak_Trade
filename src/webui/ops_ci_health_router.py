"""
Peak_Trade: CI & Governance Health API
======================================

Ops Dashboard v0.2: CI & Governance Health Panel with Interactive Controls

Führt lokale CI-Checks aus und zeigt Status als Ampel:
- Contract Guard (check_required_ci_contexts_present.sh)
- Docs Reference Validation (verify_docs_reference_targets.sh --changed)

v0.2 Features:
- Persistent Last-Known-Health Snapshot
  - JSON: reports/ops/ci_health_latest.json
  - Markdown: reports/ops/ci_health_latest.md
  - Atomic writes (temp file + rename)
  - Snapshot errors do NOT fail the API
- Interactive "Run Now" Buttons (fetch-based, no page reload)
  - POST /ops/ci-health/run (trigger checks)
  - Auto-refresh toggle (15s)
  - Running state + error handling

Endpoints:
- GET  /ops/ci-health        - HTML dashboard page (with interactive controls)
- GET  /ops/ci-health/status - JSON API für health checks (read-only)
- POST /ops/ci-health/run    - Trigger check execution (with lock)

Safety:
- Offline-lokal, keine externen Secrets
- Read-only checks, keine destructive operations
- In-memory lock prevents parallel runs (HTTP 409 on conflict)
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/ops/ci-health", tags=["ops", "ci-health"])

# Global config (set by app during initialization)
_REPO_ROOT: Optional[Path] = None
_TEMPLATES: Optional[Jinja2Templates] = None

# In-memory lock for check execution (prevents parallel runs)
_CHECK_LOCK = threading.Lock()
_LAST_RUN_TIMESTAMP: Optional[datetime] = None


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


def _get_git_head_sha() -> Optional[str]:
    """
    Get current git HEAD SHA.

    Returns:
        Git HEAD SHA (short) or None if not available
    """
    try:
        repo_root = get_repo_root()
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.debug(f"Could not get git HEAD SHA: {e}")
    return None


def _persist_snapshot(status_data: Dict[str, Any]) -> Optional[str]:
    """
    Persist CI health status snapshot to disk (v0.2).

    Writes:
    - reports/ops/ci_health_latest.json (complete status)
    - reports/ops/ci_health_latest.md (human-readable summary)

    Uses atomic writes (temp file + rename) to prevent partial files.

    Args:
        status_data: Complete status dict from API response

    Returns:
        Error message if snapshot failed, None on success

    Safety:
        - Creates directory if missing
        - Atomic writes via temp file
        - Does NOT raise exceptions (logs errors only)
    """
    try:
        repo_root = get_repo_root()
        snapshot_dir = repo_root / "reports" / "ops"

        # Create directory if missing
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        json_path = snapshot_dir / "ci_health_latest.json"
        md_path = snapshot_dir / "ci_health_latest.md"

        # Atomic write: JSON
        json_tmp = snapshot_dir / "ci_health_latest.json.tmp"
        with open(json_tmp, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)
        os.replace(json_tmp, json_path)

        # Atomic write: Markdown
        md_tmp = snapshot_dir / "ci_health_latest.md.tmp"
        with open(md_tmp, "w", encoding="utf-8") as f:
            _write_markdown_summary(f, status_data)
        os.replace(md_tmp, md_path)

        logger.info(f"CI health snapshot persisted: {json_path}, {md_path}")
        return None

    except Exception as e:
        error_msg = f"Failed to persist snapshot: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


def _write_markdown_summary(file, status_data: Dict[str, Any]) -> None:
    """
    Write human-readable Markdown summary (10-20 lines).

    Args:
        file: File handle to write to
        status_data: Complete status dict
    """
    overall = status_data.get("overall_status", "UNKNOWN")
    summary = status_data.get("summary", {})
    checks = status_data.get("checks", [])
    generated_at = status_data.get("generated_at", "unknown")
    git_sha = status_data.get("git_head_sha", "unknown")

    # Header
    file.write("# CI & Governance Health Snapshot\n\n")
    file.write(f"**Generated:** {generated_at}  \n")
    file.write(f"**Git HEAD:** `{git_sha}`  \n")
    file.write(f"**Overall Status:** **{overall}**  \n\n")

    # Summary
    file.write("## Summary\n\n")
    file.write(f"- **Total Checks:** {summary.get('total', 0)}\n")
    file.write(f"- **OK:** {summary.get('ok', 0)}\n")
    file.write(f"- **WARN:** {summary.get('warn', 0)}\n")
    file.write(f"- **FAIL:** {summary.get('fail', 0)}\n")
    file.write(f"- **SKIP:** {summary.get('skip', 0)}\n\n")

    # Checks
    file.write("## Checks\n\n")
    for check in checks:
        status_badge = check.get("status", "UNKNOWN")
        title = check.get("title", "Unknown")
        duration = check.get("duration_ms", 0)
        exit_code = check.get("exit_code", 0)

        file.write(f"### {title} [{status_badge}]\n\n")
        file.write(f"- **Check ID:** `{check.get('check_id', 'unknown')}`\n")
        file.write(f"- **Duration:** {duration}ms\n")
        file.write(f"- **Exit Code:** {exit_code}\n")

        # Error excerpt (first 10 lines if present)
        error_excerpt = check.get("error_excerpt", "")
        if error_excerpt:
            lines = error_excerpt.split("\n")[:10]
            file.write("\n**Error Excerpt:**\n\n```\n")
            file.write("\n".join(lines))
            file.write("\n```\n")

        file.write("\n")


# =============================================================================
# API ENDPOINTS
# =============================================================================


@router.get("/status")
async def get_ci_health_status() -> Dict[str, Any]:
    """
    JSON API: Get CI & Governance health status (v0.2 with snapshot persistence).

    Returns:
        Dict with health check results and summary.

    v0.2 Features:
        - Persists snapshot to reports/ops/ci_health_latest.{json,md}
        - Adds server_timestamp_utc, git_head_sha, app_version
        - snapshot_write_error field if persistence failed
        - Always returns 200 OK (even if snapshot write failed)
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

    # Build response (v0.2: enriched with git/timestamp)
    response = {
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
        "server_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_head_sha": _get_git_head_sha(),
        "app_version": "0.2.0",  # CI Health API version
    }

    # v0.2: Persist snapshot (errors do NOT fail the API)
    snapshot_error = _persist_snapshot(response)
    if snapshot_error:
        response["snapshot_write_error"] = snapshot_error
        logger.warning(f"Snapshot write failed but API returns 200: {snapshot_error}")

    return response


@router.post("/run")
async def run_ci_health_checks() -> Dict[str, Any]:
    """
    JSON API: Trigger CI & Governance health checks (v0.2 interactive controls).

    Executes health checks and returns results (same schema as GET /status).

    Features:
        - In-memory lock prevents parallel runs (HTTP 409 on conflict)
        - Logs run start/end with duration
        - Persists snapshot on success
        - Idempotent: safe to call multiple times

    Returns:
        Dict with health check results and summary (same as GET /status)

    Raises:
        HTTPException 409: If another check run is already in progress
    """
    global _LAST_RUN_TIMESTAMP

    # Try to acquire lock (non-blocking)
    acquired = _CHECK_LOCK.acquire(blocking=False)

    if not acquired:
        # Another run is in progress
        logger.warning("CI health check run rejected: lock held by another request")
        raise HTTPException(
            status_code=409,
            detail={
                "error": "run_already_in_progress",
                "message": "Another CI health check is already running. Please wait.",
                "last_run": _LAST_RUN_TIMESTAMP.isoformat() if _LAST_RUN_TIMESTAMP else None,
            },
        )

    try:
        # Log run start
        run_start = datetime.now(timezone.utc)
        logger.info("CI health check run started")

        # Execute checks
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

        # Build response
        response = {
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
            "server_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "git_head_sha": _get_git_head_sha(),
            "app_version": "0.2.0",
            "run_triggered": True,  # Flag to indicate this was a triggered run
        }

        # Persist snapshot
        snapshot_error = _persist_snapshot(response)
        if snapshot_error:
            response["snapshot_write_error"] = snapshot_error
            logger.warning(f"Snapshot write failed but API returns 200: {snapshot_error}")

        # Log run end
        run_end = datetime.now(timezone.utc)
        duration_ms = int((run_end - run_start).total_seconds() * 1000)
        logger.info(
            f"CI health check run completed: status={overall_status}, duration={duration_ms}ms"
        )

        # Update last run timestamp
        _LAST_RUN_TIMESTAMP = run_end

        return response

    finally:
        # Always release lock
        _CHECK_LOCK.release()


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
