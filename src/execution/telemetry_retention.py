"""
Telemetry Retention & Compression - Phase 16E

Automated log lifecycle management for execution telemetry logs.

Features:
- Age-based deletion (with session-count protection)
- Size-based deletion (enforce total size limits)
- Automatic compression (gzip after N days)
- Dry-run mode (safe planning)
- Deterministic sorting (oldest first)

Safety:
- Root directory validation
- Dry-run default
- Session-count protection (keep last N sessions)
- No silent failures (all errors logged/raised)
"""

import gzip
import logging
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SessionMeta:
    """Metadata for a single telemetry session log file."""
    
    path: Path
    session_id: str
    size_bytes: int
    mtime: datetime  # UTC
    is_compressed: bool
    
    @property
    def age_days(self) -> float:
        """Age in days (from mtime to now UTC)."""
        now = datetime.now(timezone.utc)
        # Handle both aware and naive datetimes
        if self.mtime.tzinfo is None:
            # Assume UTC if naive
            mtime_utc = self.mtime.replace(tzinfo=timezone.utc)
        else:
            mtime_utc = self.mtime
        return (now - mtime_utc).total_seconds() / 86400.0
    
    @property
    def size_mb(self) -> float:
        """Size in MB."""
        return self.size_bytes / (1024 * 1024)


@dataclass
class RetentionPolicy:
    """Retention policy configuration."""
    
    enabled: bool = True
    max_age_days: int = 30
    keep_last_n_sessions: int = 200
    max_total_mb: int = 2048
    compress_after_days: int = 7
    protect_keep_last_from_compress: bool = False


@dataclass
class Action:
    """A single retention action (compress or delete)."""
    
    kind: str  # "compress" | "delete"
    path: Path
    reason: str
    size_bytes: int = 0
    
    @property
    def size_mb(self) -> float:
        """Size in MB."""
        return self.size_bytes / (1024 * 1024)


@dataclass
class RetentionPlan:
    """A plan of retention actions to execute."""
    
    actions: List[Action] = field(default_factory=list)
    sessions_total: int = 0
    sessions_kept: int = 0
    size_before_mb: float = 0.0
    size_after_mb: float = 0.0
    
    @property
    def compression_savings_mb(self) -> float:
        """Estimated compression savings (assumes 80% reduction)."""
        compress_bytes = sum(a.size_bytes for a in self.actions if a.kind == "compress")
        return (compress_bytes * 0.8) / (1024 * 1024)
    
    @property
    def deleted_mb(self) -> float:
        """Total MB deleted."""
        return sum(a.size_mb for a in self.actions if a.kind == "delete")


def is_safe_telemetry_root(path: Path) -> bool:
    """
    Validate that path is a safe telemetry log directory.
    
    Safety checks:
    - Path exists and is a directory
    - Path name contains "execution" or "telemetry" or "logs"
    - Not a system directory (/, /home, /usr, etc.)
    
    Args:
        path: Directory to validate
        
    Returns:
        True if safe, False otherwise
    """
    if not path.exists():
        return False
    
    if not path.is_dir():
        return False
    
    # Resolve to absolute path
    abs_path = path.resolve()
    
    # Check for dangerous root paths
    dangerous_roots = {
        Path("/"),
        Path("/home"),
        Path("/usr"),
        Path("/etc"),
        Path("/var"),
        Path("/tmp"),
        Path.home(),
    }
    
    if abs_path in dangerous_roots:
        logger.error(f"Refusing to operate on system directory: {abs_path}")
        return False
    
    # Check path contains telemetry/execution/logs keywords
    path_str = str(abs_path).lower()
    safe_keywords = ["execution", "telemetry", "logs", "log"]
    
    if not any(keyword in path_str for keyword in safe_keywords):
        logger.warning(f"Path does not contain safe keywords: {abs_path}")
        return False
    
    return True


def discover_sessions(
    root: Path,
    include_compressed: bool = True
) -> List[SessionMeta]:
    """
    Discover all telemetry session log files in root directory.
    
    Args:
        root: Directory to scan (e.g., logs/execution)
        include_compressed: If True, include .jsonl.gz files
        
    Returns:
        List of SessionMeta objects, sorted by mtime (oldest first)
        
    Raises:
        ValueError: If root is not a safe telemetry directory
    """
    if not is_safe_telemetry_root(root):
        raise ValueError(f"Unsafe or invalid telemetry root: {root}")
    
    sessions: List[SessionMeta] = []
    
    # Find .jsonl files
    for path in root.glob("*.jsonl"):
        if not path.is_file():
            continue
        
        stat = path.stat()
        session_id = path.stem  # filename without extension
        
        sessions.append(SessionMeta(
            path=path,
            session_id=session_id,
            size_bytes=stat.st_size,
            mtime=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            is_compressed=False,
        ))
    
    # Find .jsonl.gz files (if enabled)
    if include_compressed:
        for path in root.glob("*.jsonl.gz"):
            if not path.is_file():
                continue
            
            stat = path.stat()
            # Remove .jsonl.gz to get session_id
            session_id = path.name.replace(".jsonl.gz", "")
            
            sessions.append(SessionMeta(
                path=path,
                session_id=session_id,
                size_bytes=stat.st_size,
                mtime=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                is_compressed=True,
            ))
    
    # Sort by mtime (oldest first) for deterministic processing
    sessions.sort(key=lambda s: s.mtime)
    
    return sessions


def build_plan(
    sessions: List[SessionMeta],
    policy: RetentionPolicy,
) -> RetentionPlan:
    """
    Build a retention plan based on discovered sessions and policy.
    
    Args:
        sessions: List of session metadata (should be sorted by mtime)
        policy: Retention policy configuration
        
    Returns:
        RetentionPlan with actions to execute
    """
    if not policy.enabled:
        return RetentionPlan(
            sessions_total=len(sessions),
            sessions_kept=len(sessions),
            size_before_mb=sum(s.size_mb for s in sessions),
            size_after_mb=sum(s.size_mb for s in sessions),
        )
    
    plan = RetentionPlan(
        sessions_total=len(sessions),
        size_before_mb=sum(s.size_mb for s in sessions),
    )
    
    # Identify "protected" sessions (last N sessions by mtime)
    # These are protected from age-based deletion
    sessions_by_mtime = sorted(sessions, key=lambda s: s.mtime, reverse=True)
    protected_sessions = set(
        s.path for s in sessions_by_mtime[:policy.keep_last_n_sessions]
    )
    
    # Phase 1: Age-based deletion (with protection)
    age_cutoff = datetime.now(timezone.utc) - timedelta(days=policy.max_age_days)
    
    for session in sessions:
        # Handle both aware and naive datetimes
        if session.mtime.tzinfo is None:
            mtime_utc = session.mtime.replace(tzinfo=timezone.utc)
        else:
            mtime_utc = session.mtime
        
        if mtime_utc < age_cutoff and session.path not in protected_sessions:
            plan.actions.append(Action(
                kind="delete",
                path=session.path,
                reason=f"Older than {policy.max_age_days} days (age: {session.age_days:.1f}d)",
                size_bytes=session.size_bytes,
            ))
    
    # Calculate remaining sessions after age-based deletion
    deleted_paths = {a.path for a in plan.actions if a.kind == "delete"}
    remaining_sessions = [s for s in sessions if s.path not in deleted_paths]
    
    # Phase 2: Size-based deletion (if over limit)
    if policy.max_total_mb > 0:
        current_size_mb = sum(s.size_mb for s in remaining_sessions)
        
        if current_size_mb > policy.max_total_mb:
            # Delete oldest sessions first (already sorted)
            # But respect keep_last_n_sessions protection
            for session in remaining_sessions:
                if session.path in protected_sessions:
                    continue
                
                if current_size_mb <= policy.max_total_mb:
                    break
                
                # Check if already marked for deletion
                if session.path in deleted_paths:
                    continue
                
                plan.actions.append(Action(
                    kind="delete",
                    path=session.path,
                    reason=f"Total size limit exceeded ({current_size_mb:.1f}MB > {policy.max_total_mb}MB)",
                    size_bytes=session.size_bytes,
                ))
                
                deleted_paths.add(session.path)
                current_size_mb -= session.size_mb
    
    # Recalculate remaining sessions after size-based deletion
    remaining_sessions = [s for s in sessions if s.path not in deleted_paths]
    
    # Phase 3: Compression (if enabled)
    if policy.compress_after_days > 0:
        compress_cutoff = datetime.now(timezone.utc) - timedelta(days=policy.compress_after_days)
        
        for session in remaining_sessions:
            # Skip if already compressed
            if session.is_compressed:
                continue
            
            # Handle both aware and naive datetimes
            if session.mtime.tzinfo is None:
                mtime_utc = session.mtime.replace(tzinfo=timezone.utc)
            else:
                mtime_utc = session.mtime
            
            # Check age
            if mtime_utc >= compress_cutoff:
                continue
            
            # Check protection
            if policy.protect_keep_last_from_compress and session.path in protected_sessions:
                continue
            
            plan.actions.append(Action(
                kind="compress",
                path=session.path,
                reason=f"Older than {policy.compress_after_days} days (age: {session.age_days:.1f}d)",
                size_bytes=session.size_bytes,
            ))
    
    # Calculate final stats
    plan.sessions_kept = len(remaining_sessions)
    
    # Estimate size after compression (80% reduction)
    compressed_bytes = sum(a.size_bytes for a in plan.actions if a.kind == "compress")
    deleted_bytes = sum(a.size_bytes for a in plan.actions if a.kind == "delete")
    remaining_bytes = sum(s.size_bytes for s in remaining_sessions) - compressed_bytes - deleted_bytes
    
    plan.size_after_mb = (remaining_bytes + compressed_bytes * 0.2) / (1024 * 1024)
    
    return plan


def apply_plan(
    plan: RetentionPlan,
    dry_run: bool = True,
) -> dict:
    """
    Apply a retention plan (compress/delete files).
    
    Args:
        plan: Retention plan to execute
        dry_run: If True, don't actually modify files (default: True)
        
    Returns:
        Stats dict with results
        
    Raises:
        IOError: If file operations fail
    """
    stats = {
        "dry_run": dry_run,
        "actions_planned": len(plan.actions),
        "actions_executed": 0,
        "compressed": 0,
        "deleted": 0,
        "errors": [],
    }
    
    for action in plan.actions:
        try:
            if action.kind == "compress":
                if not dry_run:
                    # Compress .jsonl -> .jsonl.gz
                    gz_path = action.path.with_suffix(action.path.suffix + ".gz")
                    
                    with open(action.path, "rb") as f_in:
                        with gzip.open(gz_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Preserve mtime
                    stat = action.path.stat()
                    os.utime(gz_path, (stat.st_atime, stat.st_mtime))
                    
                    # Delete original
                    action.path.unlink()
                    
                    logger.info(f"Compressed: {action.path} -> {gz_path}")
                
                stats["compressed"] += 1
            
            elif action.kind == "delete":
                if not dry_run:
                    action.path.unlink()
                    logger.info(f"Deleted: {action.path}")
                
                stats["deleted"] += 1
            
            stats["actions_executed"] += 1
        
        except Exception as e:
            error_msg = f"Failed to {action.kind} {action.path}: {e}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
    
    return stats
