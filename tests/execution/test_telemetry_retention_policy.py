"""
Tests for Telemetry Retention & Compression - Phase 16E

Tests cover:
- Session discovery
- Retention policy (age, count, size)
- Compression logic
- Dry-run mode
- Root safety
- Edge cases
"""

import gzip
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.execution.telemetry_retention import (
    Action,
    RetentionPolicy,
    SessionMeta,
    apply_plan,
    build_plan,
    discover_sessions,
    is_safe_telemetry_root,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def telemetry_root(tmp_path):
    """Create a temporary telemetry logs directory."""
    root = tmp_path / "logs" / "execution"
    root.mkdir(parents=True)
    return root


def create_log_file(root: Path, session_id: str, age_days: int, size_kb: int = 10):
    """
    Create a fake telemetry log file with specific age.
    
    Args:
        root: Log directory
        session_id: Session ID (filename stem)
        age_days: Age in days (sets mtime)
        size_kb: File size in KB
    
    Returns:
        Path to created file
    """
    path = root / f"{session_id}.jsonl"
    
    # Write fake content (create approximately size_kb KB)
    line = '{"ts": "2025-12-20T10:00:00Z", "kind": "test"}\n'
    line_size = len(line.encode('utf-8'))
    num_lines = (size_kb * 1024) // line_size
    content = line * num_lines
    path.write_text(content)
    
    # Set mtime to simulate age
    mtime = datetime.now(timezone.utc) - timedelta(days=age_days)
    mtime_timestamp = mtime.timestamp()
    os.utime(path, (mtime_timestamp, mtime_timestamp))
    
    return path


# ==============================================================================
# Test: Root Safety
# ==============================================================================


def test_root_safety_valid(telemetry_root):
    """Valid telemetry root should pass safety check."""
    assert is_safe_telemetry_root(telemetry_root)


def test_root_safety_system_dir():
    """System directories should fail safety check."""
    assert not is_safe_telemetry_root(Path("/"))
    assert not is_safe_telemetry_root(Path("/home"))
    assert not is_safe_telemetry_root(Path("/usr"))


def test_root_safety_nonexistent():
    """Nonexistent directory should fail safety check."""
    assert not is_safe_telemetry_root(Path("/tmp/does_not_exist_telemetry"))


def test_root_safety_no_keywords(tmp_path):
    """Directory without safe keywords should fail (with warning)."""
    unsafe = tmp_path / "unsafe_dir"
    unsafe.mkdir()
    # Should return False because no "execution"/"telemetry"/"logs" in path
    assert not is_safe_telemetry_root(unsafe)


# ==============================================================================
# Test: Session Discovery
# ==============================================================================


def test_discover_sessions_empty(telemetry_root):
    """Empty directory should return empty list."""
    sessions = discover_sessions(telemetry_root)
    assert len(sessions) == 0


def test_discover_sessions_basic(telemetry_root):
    """Discover basic .jsonl files."""
    create_log_file(telemetry_root, "session_001", age_days=1)
    create_log_file(telemetry_root, "session_002", age_days=2)
    create_log_file(telemetry_root, "session_003", age_days=3)
    
    sessions = discover_sessions(telemetry_root)
    
    assert len(sessions) == 3
    assert all(isinstance(s, SessionMeta) for s in sessions)
    assert all(not s.is_compressed for s in sessions)
    
    # Should be sorted by mtime (oldest first)
    assert sessions[0].session_id == "session_003"  # 3 days old
    assert sessions[1].session_id == "session_002"  # 2 days old
    assert sessions[2].session_id == "session_001"  # 1 day old


def test_discover_sessions_compressed(telemetry_root):
    """Discover compressed .jsonl.gz files."""
    # Create .jsonl file
    path = create_log_file(telemetry_root, "session_001", age_days=10)
    
    # Compress it manually
    gz_path = path.with_suffix(".jsonl.gz")
    with open(path, "rb") as f_in:
        with gzip.open(gz_path, "wb") as f_out:
            f_out.write(f_in.read())
    
    # Set mtime on compressed file
    stat = path.stat()
    os.utime(gz_path, (stat.st_atime, stat.st_mtime))
    
    # Remove original
    path.unlink()
    
    sessions = discover_sessions(telemetry_root, include_compressed=True)
    
    assert len(sessions) == 1
    assert sessions[0].is_compressed
    assert sessions[0].path.suffix == ".gz"


def test_discover_sessions_mixed(telemetry_root):
    """Discover mix of .jsonl and .jsonl.gz files."""
    create_log_file(telemetry_root, "session_001", age_days=1)
    
    # Create compressed file
    path = create_log_file(telemetry_root, "session_002", age_days=10)
    gz_path = path.with_suffix(".jsonl.gz")
    with open(path, "rb") as f_in:
        with gzip.open(gz_path, "wb") as f_out:
            f_out.write(f_in.read())
    stat = path.stat()
    os.utime(gz_path, (stat.st_atime, stat.st_mtime))
    path.unlink()
    
    sessions = discover_sessions(telemetry_root)
    
    assert len(sessions) == 2
    assert sessions[0].is_compressed  # Older
    assert not sessions[1].is_compressed  # Newer


# ==============================================================================
# Test: Build Plan - Age-based Deletion
# ==============================================================================


def test_plan_age_based_deletion(telemetry_root):
    """Delete logs older than max_age_days."""
    create_log_file(telemetry_root, "session_old_1", age_days=40)
    create_log_file(telemetry_root, "session_old_2", age_days=35)
    create_log_file(telemetry_root, "session_new", age_days=10)
    
    sessions = discover_sessions(telemetry_root)
    policy = RetentionPolicy(
        enabled=True,
        max_age_days=30,
        keep_last_n_sessions=0,  # Disable protection
        compress_after_days=0,  # Disable compression
    )
    
    plan = build_plan(sessions, policy)
    
    assert len(plan.actions) == 2
    assert all(a.kind == "delete" for a in plan.actions)
    assert plan.sessions_kept == 1


def test_plan_keep_last_n_protection(telemetry_root):
    """Keep last N sessions even if old."""
    create_log_file(telemetry_root, "session_1", age_days=50)
    create_log_file(telemetry_root, "session_2", age_days=45)
    create_log_file(telemetry_root, "session_3", age_days=10)
    
    sessions = discover_sessions(telemetry_root)
    policy = RetentionPolicy(
        enabled=True,
        max_age_days=30,
        keep_last_n_sessions=2,  # Protect last 2
        compress_after_days=0,
    )
    
    plan = build_plan(sessions, policy)
    
    # Should delete oldest (session_1), but keep session_2 (protected by keep_last_n)
    assert len(plan.actions) == 1
    assert plan.actions[0].kind == "delete"
    assert "session_1" in str(plan.actions[0].path)
    assert plan.sessions_kept == 2


# ==============================================================================
# Test: Build Plan - Size-based Deletion
# ==============================================================================


def test_plan_size_limit_enforcement(telemetry_root):
    """Delete oldest logs when total size exceeds limit."""
    # Create files (10 KB each)
    create_log_file(telemetry_root, "session_1", age_days=10, size_kb=10)
    create_log_file(telemetry_root, "session_2", age_days=9, size_kb=10)
    create_log_file(telemetry_root, "session_3", age_days=8, size_kb=10)
    create_log_file(telemetry_root, "session_4", age_days=7, size_kb=10)
    
    sessions = discover_sessions(telemetry_root)
    policy = RetentionPolicy(
        enabled=True,
        max_age_days=100,  # Don't delete by age
        keep_last_n_sessions=2,  # Protect last 2
        max_total_mb=0.02,  # 20 KB limit (should delete 2 oldest)
        compress_after_days=0,
    )
    
    plan = build_plan(sessions, policy)
    
    # Should delete 2 oldest (session_1, session_2)
    # But keep last 2 (session_3, session_4)
    delete_actions = [a for a in plan.actions if a.kind == "delete"]
    assert len(delete_actions) == 2
    assert "session_1" in str(delete_actions[0].path)
    assert "session_2" in str(delete_actions[1].path)


# ==============================================================================
# Test: Build Plan - Compression
# ==============================================================================


def test_plan_compression_by_age(telemetry_root):
    """Compress logs older than compress_after_days."""
    create_log_file(telemetry_root, "session_old", age_days=10)
    create_log_file(telemetry_root, "session_new", age_days=3)
    
    sessions = discover_sessions(telemetry_root)
    policy = RetentionPolicy(
        enabled=True,
        max_age_days=100,
        compress_after_days=7,  # Compress after 7 days
    )
    
    plan = build_plan(sessions, policy)
    
    compress_actions = [a for a in plan.actions if a.kind == "compress"]
    assert len(compress_actions) == 1
    assert "session_old" in str(compress_actions[0].path)


def test_plan_compression_protect_last_n(telemetry_root):
    """Don't compress last N sessions if protected."""
    create_log_file(telemetry_root, "session_1", age_days=20)
    create_log_file(telemetry_root, "session_2", age_days=15)
    create_log_file(telemetry_root, "session_3", age_days=10)
    
    sessions = discover_sessions(telemetry_root)
    policy = RetentionPolicy(
        enabled=True,
        max_age_days=100,
        keep_last_n_sessions=2,
        compress_after_days=5,
        protect_keep_last_from_compress=True,  # Protect last 2
    )
    
    plan = build_plan(sessions, policy)
    
    compress_actions = [a for a in plan.actions if a.kind == "compress"]
    # Should only compress session_1 (oldest, not in last 2)
    assert len(compress_actions) == 1
    assert "session_1" in str(compress_actions[0].path)


def test_plan_skip_already_compressed(telemetry_root):
    """Don't compress already compressed files."""
    # Create compressed file
    path = create_log_file(telemetry_root, "session_old", age_days=10)
    gz_path = path.with_suffix(".jsonl.gz")
    with open(path, "rb") as f_in:
        with gzip.open(gz_path, "wb") as f_out:
            f_out.write(f_in.read())
    stat = path.stat()
    os.utime(gz_path, (stat.st_atime, stat.st_mtime))
    path.unlink()
    
    sessions = discover_sessions(telemetry_root)
    policy = RetentionPolicy(
        enabled=True,
        compress_after_days=5,
    )
    
    plan = build_plan(sessions, policy)
    
    # Should not try to compress already compressed file
    compress_actions = [a for a in plan.actions if a.kind == "compress"]
    assert len(compress_actions) == 0


# ==============================================================================
# Test: Apply Plan
# ==============================================================================


def test_apply_plan_dry_run(telemetry_root):
    """Dry-run should not modify files."""
    path = create_log_file(telemetry_root, "session_001", age_days=10)
    
    sessions = discover_sessions(telemetry_root)
    policy = RetentionPolicy(compress_after_days=5)
    plan = build_plan(sessions, policy)
    
    stats = apply_plan(plan, dry_run=True)
    
    assert stats["dry_run"] is True
    assert stats["compressed"] == 1
    assert stats["deleted"] == 0
    assert path.exists()  # File should still exist
    assert not path.with_suffix(".jsonl.gz").exists()


def test_apply_plan_compress(telemetry_root):
    """Apply compression."""
    path = create_log_file(telemetry_root, "session_001", age_days=10)
    original_mtime = path.stat().st_mtime
    
    sessions = discover_sessions(telemetry_root)
    policy = RetentionPolicy(compress_after_days=5)
    plan = build_plan(sessions, policy)
    
    stats = apply_plan(plan, dry_run=False)
    
    assert stats["dry_run"] is False
    assert stats["compressed"] == 1
    assert not path.exists()  # Original should be deleted
    
    gz_path = path.with_suffix(".jsonl.gz")
    assert gz_path.exists()  # Compressed file should exist
    
    # Check mtime preserved
    assert abs(gz_path.stat().st_mtime - original_mtime) < 1.0


def test_apply_plan_delete(telemetry_root):
    """Apply deletion."""
    path = create_log_file(telemetry_root, "session_old", age_days=40)
    
    sessions = discover_sessions(telemetry_root)
    policy = RetentionPolicy(
        max_age_days=30,
        keep_last_n_sessions=0,
        compress_after_days=0,
    )
    plan = build_plan(sessions, policy)
    
    stats = apply_plan(plan, dry_run=False)
    
    assert stats["deleted"] == 1
    assert not path.exists()


# ==============================================================================
# Test: Edge Cases
# ==============================================================================


def test_policy_disabled(telemetry_root):
    """Disabled policy should not produce actions."""
    create_log_file(telemetry_root, "session_old", age_days=100)
    
    sessions = discover_sessions(telemetry_root)
    policy = RetentionPolicy(enabled=False)
    
    plan = build_plan(sessions, policy)
    
    assert len(plan.actions) == 0
    assert plan.sessions_kept == len(sessions)


def test_empty_sessions_list():
    """Empty sessions list should produce empty plan."""
    policy = RetentionPolicy()
    plan = build_plan([], policy)
    
    assert len(plan.actions) == 0
    assert plan.sessions_total == 0


def test_discover_unsafe_root():
    """Discover should raise ValueError for unsafe root."""
    with pytest.raises(ValueError, match="Unsafe or invalid"):
        discover_sessions(Path("/"))


def test_session_meta_age_calculation():
    """SessionMeta.age_days should calculate correctly."""
    now = datetime.now(timezone.utc)
    ten_days_ago = now - timedelta(days=10)
    
    session = SessionMeta(
        path=Path("/tmp/test.jsonl"),
        session_id="test",
        size_bytes=1024,
        mtime=ten_days_ago,
        is_compressed=False,
    )
    
    assert 9.9 < session.age_days < 10.1  # Allow small float tolerance


def test_session_meta_size_mb():
    """SessionMeta.size_mb should calculate correctly."""
    session = SessionMeta(
        path=Path("/tmp/test.jsonl"),
        session_id="test",
        size_bytes=2 * 1024 * 1024,  # 2 MB
        mtime=datetime.now(timezone.utc),
        is_compressed=False,
    )
    
    assert abs(session.size_mb - 2.0) < 0.01
