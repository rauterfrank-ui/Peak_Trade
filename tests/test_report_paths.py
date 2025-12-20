#!/usr/bin/env python3
"""
Peak_Trade – Phase 16L: Tests for report_paths utilities
"""
import os
from pathlib import Path

import pytest

from src.utils.report_paths import ensure_dir, get_repo_root, get_reports_root


def test_get_repo_root():
    """Test that get_repo_root finds a valid repo root."""
    root = get_repo_root()
    assert root.is_dir()
    # Should have pyproject.toml or uv.lock
    assert (root / "pyproject.toml").exists() or (root / "uv.lock").exists()


def test_get_reports_root_default(monkeypatch):
    """Test default behavior: repo_root/reports."""
    monkeypatch.delenv("PEAK_REPORTS_DIR", raising=False)
    
    root = get_reports_root()
    repo_root = get_repo_root()
    expected = repo_root / "reports"
    
    assert root == expected.resolve()


def test_get_reports_root_env_relative(monkeypatch, tmp_path):
    """Test ENV with relative path."""
    monkeypatch.setenv("PEAK_REPORTS_DIR", "custom_reports")
    
    root = get_reports_root()
    repo_root = get_repo_root()
    expected = repo_root / "custom_reports"
    
    assert root == expected.resolve()


def test_get_reports_root_env_absolute(monkeypatch, tmp_path):
    """Test ENV with absolute path."""
    abs_path = tmp_path / "absolute_reports"
    monkeypatch.setenv("PEAK_REPORTS_DIR", str(abs_path))
    
    root = get_reports_root()
    
    assert root == abs_path.resolve()


def test_get_reports_root_env_empty_string(monkeypatch):
    """Test that empty ENV string falls back to default."""
    monkeypatch.setenv("PEAK_REPORTS_DIR", "")
    
    root = get_reports_root()
    repo_root = get_repo_root()
    expected = repo_root / "reports"
    
    assert root == expected.resolve()


def test_get_reports_root_custom_default(monkeypatch):
    """Test custom default_rel parameter."""
    monkeypatch.delenv("PEAK_REPORTS_DIR", raising=False)
    
    root = get_reports_root(default_rel="output")
    repo_root = get_repo_root()
    expected = repo_root / "output"
    
    assert root == expected.resolve()


def test_ensure_dir_creates_directory(tmp_path):
    """Test that ensure_dir creates missing directories."""
    target = tmp_path / "nested" / "path" / "to" / "dir"
    
    assert not target.exists()
    
    result = ensure_dir(target)
    
    assert target.exists()
    assert target.is_dir()
    assert result == target


def test_ensure_dir_idempotent(tmp_path):
    """Test that ensure_dir is idempotent (can be called multiple times)."""
    target = tmp_path / "test_dir"
    
    ensure_dir(target)
    assert target.exists()
    
    # Call again - should not raise
    ensure_dir(target)
    assert target.exists()

