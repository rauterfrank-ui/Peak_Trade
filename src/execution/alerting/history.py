"""
Alert History - Phase 16J

Persistent alert history with retention and query capabilities.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from .models import AlertEvent

logger = logging.getLogger(__name__)


class AlertHistory:
    """
    Alert history store (JSONL-based).
    
    Features:
    - Append-only JSONL storage
    - Time-based filtering
    - Automatic retention cleanup
    - Separate from in-memory cache (always persists)
    """
    
    def __init__(
        self,
        history_path: Path,
        retain_days: int = 14,
        enabled: bool = True,
    ):
        """
        Initialize alert history.
        
        Args:
            history_path: Path to history JSONL file
            retain_days: Days to retain history
            enabled: Whether history is enabled
        """
        self.history_path = history_path
        self.retain_days = retain_days
        self.enabled = enabled
    
    def append(self, alert: AlertEvent, delivery_status: str = "unknown") -> bool:
        """
        Append alert to history.
        
        Args:
            alert: Alert event to append
            delivery_status: Delivery status (sent/failed/skipped)
        
        Returns:
            True if append succeeded, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build history entry
            entry = {
                **alert.to_dict(),
                "delivery_status": delivery_status,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
            
            with open(self.history_path, "a", encoding="utf-8") as f:
                json.dump(entry, f)
                f.write("\n")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to append to alert history: {e}")
            return False
    
    def query(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        severity: Optional[str] = None,
        rule_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[dict]:
        """
        Query alert history.
        
        Args:
            since: Start time (inclusive)
            until: End time (inclusive)
            severity: Filter by severity
            rule_id: Filter by rule ID
            limit: Maximum results to return
        
        Returns:
            List of alert history entries (dicts)
        """
        if not self.enabled or not self.history_path.exists():
            return []
        
        results = []
        
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        
                        # Parse timestamp
                        ts_str = entry.get("timestamp_utc", "")
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        
                        # Apply time filters
                        if since and ts < since:
                            continue
                        if until and ts > until:
                            continue
                        
                        # Apply severity filter
                        if severity and entry.get("severity") != severity:
                            continue
                        
                        # Apply rule_id filter
                        if rule_id:
                            labels = entry.get("labels", {})
                            if labels.get("rule_id") != rule_id:
                                continue
                        
                        results.append(entry)
                    
                    except Exception as e:
                        logger.warning(f"Failed to parse history entry at line {line_no}: {e}")
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda e: e.get("timestamp_utc", ""), reverse=True)
            
            # Apply limit
            if limit and len(results) > limit:
                results = results[:limit]
            
            return results
        
        except Exception as e:
            logger.error(f"Failed to query alert history: {e}")
            return []
    
    def cleanup_old(self) -> int:
        """
        Remove history entries older than retain_days.
        
        Returns:
            Number of entries removed
        """
        if not self.enabled or not self.history_path.exists():
            return 0
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retain_days)
        
        try:
            # Read all entries
            all_entries = []
            
            with open(self.history_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        ts_str = entry.get("timestamp_utc", "")
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        
                        if ts >= cutoff:
                            all_entries.append(entry)
                    except Exception:
                        # Keep entry if parse fails (don't lose data)
                        all_entries.append(json.loads(line))
            
            # Rewrite file with recent entries only
            removed_count = 0
            
            with open(self.history_path, "r", encoding="utf-8") as f:
                original_count = sum(1 for line in f if line.strip())
            
            removed_count = original_count - len(all_entries)
            
            if removed_count > 0:
                with open(self.history_path, "w", encoding="utf-8") as f:
                    for entry in all_entries:
                        json.dump(entry, f)
                        f.write("\n")
                
                logger.info(f"Cleaned up {removed_count} old alert history entries")
            
            return removed_count
        
        except Exception as e:
            logger.error(f"Failed to cleanup alert history: {e}")
            return 0
    
    def get_stats(self, since: Optional[datetime] = None) -> dict:
        """
        Get alert history statistics.
        
        Args:
            since: Start time for stats (default: all time)
        
        Returns:
            Dict with counts per severity, rule, etc.
        """
        entries = self.query(since=since)
        
        stats = {
            "total": len(entries),
            "by_severity": {},
            "by_rule": {},
            "by_status": {},
        }
        
        for entry in entries:
            # Count by severity
            severity = entry.get("severity", "unknown")
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
            
            # Count by rule
            labels = entry.get("labels", {})
            rule_id = labels.get("rule_id", "unknown")
            stats["by_rule"][rule_id] = stats["by_rule"].get(rule_id, 0) + 1
            
            # Count by delivery status
            status = entry.get("delivery_status", "unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        return stats
