"""
Peak_Trade Stage1 IO Module
============================

Discovery and loading functions for Stage1 reports.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

from .models import Stage1Summary

logger = logging.getLogger(__name__)


def discover_stage1_days(report_root: Path) -> List[Path]:
    """
    Discover available Stage1 daily report directories.
    
    Args:
        report_root: Root directory for Stage1 reports (e.g., reports/obs/stage1)
    
    Returns:
        List of paths to directories containing daily summaries, sorted newest first.
        
    Notes:
        - Looks for directories matching YYYY-MM-DD pattern or files matching YYYY-MM-DD_summary.json
        - Returns parent directories if found via summary files
        - Sorted by name (newest first due to YYYY-MM-DD format)
    """
    if not report_root.exists():
        logger.warning(f"Stage1 report root does not exist: {report_root}")
        return []
    
    # Find all summary JSON files
    summary_files = list(report_root.glob("*_summary.json"))
    
    # Extract unique dates/directories
    day_dirs = set()
    for sf in summary_files:
        # Extract date from filename: YYYY-MM-DD_summary.json
        date_str = sf.stem.replace("_summary", "")
        day_dirs.add(report_root)  # All summaries are in report_root
        
    # Return sorted newest first
    return sorted([report_root], reverse=True) if day_dirs else []


def load_stage1_summary(day_dir: Path, date: Optional[str] = None) -> Optional[Stage1Summary]:
    """
    Load Stage1 summary JSON from a directory.
    
    Args:
        day_dir: Directory containing the summary (e.g., reports/obs/stage1/)
        date: Optional date string (YYYY-MM-DD) to look for specific summary
    
    Returns:
        Stage1Summary object if found and valid, None otherwise.
    """
    # Try to find summary file
    if date:
        summary_path = day_dir / f"{date}_summary.json"
    else:
        # Find any summary file
        summaries = list(day_dir.glob("*_summary.json"))
        if not summaries:
            logger.debug(f"No summary JSON found in {day_dir}")
            return None
        summary_path = summaries[-1]  # Take most recent
    
    if not summary_path.exists():
        logger.debug(f"Summary file not found: {summary_path}")
        return None
    
    try:
        with summary_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        return Stage1Summary.model_validate(data)
    except Exception as e:
        logger.error(f"Failed to load/parse summary from {summary_path}: {e}")
        return None


def load_latest_summary(report_root: Path) -> Optional[Stage1Summary]:
    """
    Load the most recent Stage1 summary.
    
    Args:
        report_root: Root directory for Stage1 reports
    
    Returns:
        Stage1Summary object if found, None otherwise.
    """
    if not report_root.exists():
        logger.warning(f"Stage1 report root does not exist: {report_root}")
        return None
    
    # Find all summary files
    summaries = sorted(report_root.glob("*_summary.json"), reverse=True)
    
    if not summaries:
        logger.info(f"No summary files found in {report_root}")
        return None
    
    # Load the newest
    latest = summaries[0]
    date_str = latest.stem.replace("_summary", "")
    
    return load_stage1_summary(report_root, date=date_str)


def load_all_summaries(report_root: Path, limit: Optional[int] = None) -> List[Stage1Summary]:
    """
    Load all available Stage1 summaries.
    
    Args:
        report_root: Root directory for Stage1 reports
        limit: Maximum number of summaries to load (newest first)
    
    Returns:
        List of Stage1Summary objects, sorted newest first.
    """
    if not report_root.exists():
        logger.warning(f"Stage1 report root does not exist: {report_root}")
        return []
    
    # Find all summary files, sorted newest first
    summaries = sorted(report_root.glob("*_summary.json"), reverse=True)
    
    if limit:
        summaries = summaries[:limit]
    
    results = []
    for sf in summaries:
        date_str = sf.stem.replace("_summary", "")
        summary = load_stage1_summary(report_root, date=date_str)
        if summary:
            results.append(summary)
    
    return results

