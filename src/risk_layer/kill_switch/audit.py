"""Audit Trail for Kill Switch Events.

Provides append-only audit logging with rotation and retention.
"""

import gzip
import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from .state import KillSwitchEvent


logger = logging.getLogger(__name__)


class AuditTrail:
    """Append-only audit log for kill switch events.

    Features:
        - JSONL format (one event per line)
        - Automatic rotation (daily + size-based)
        - Retention policy with auto-cleanup
        - Compression for old logs

    Usage:
        >>> audit = AuditTrail("data/kill_switch/audit")
        >>>
        >>> # Log event
        >>> event = KillSwitchEvent(...)
        >>> audit.log_event(event)
        >>>
        >>> # Query events
        >>> events = audit.get_events(since=datetime(...), limit=50)
    """

    def __init__(
        self,
        audit_dir: str,
        retention_days: int = 90,
        max_file_size_mb: int = 10,
        logger_instance: Optional[logging.Logger] = None,
    ):
        """Initialize audit trail.

        Args:
            audit_dir: Directory for audit logs
            retention_days: Days to keep audit logs
            max_file_size_mb: Max file size before rotation
            logger_instance: Optional logger instance
        """
        self.audit_dir = Path(audit_dir)
        self.retention_days = retention_days
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self._logger = logger_instance or logger

        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self._current_file = self._get_current_file()

    def _get_current_file(self) -> Path:
        """Get current audit file path.

        Returns:
            Path to current audit file
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return self.audit_dir / f"kill_switch_audit_{today}.jsonl"

    def log_event(self, event: KillSwitchEvent):
        """Log an event to audit trail.

        Args:
            event: Kill switch event to log
        """
        # Check if rotation needed
        self._maybe_rotate()

        # Serialize event
        event_data = event.to_dict()

        # Append to file
        try:
            with open(self._current_file, "a") as f:
                f.write(json.dumps(event_data) + "\n")

            self._logger.debug(f"Audit event logged: {event.new_state.name}")

        except Exception as e:
            self._logger.error(f"Failed to log audit event: {e}", exc_info=True)

    def get_events(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[dict]:
        """Read events from audit trail.

        Args:
            since: Events from this timestamp
            until: Events until this timestamp
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        events = []

        # Find all relevant audit files
        audit_files = sorted(self.audit_dir.glob("kill_switch_audit_*.jsonl"))

        # Also check compressed files
        gz_files = sorted(self.audit_dir.glob("kill_switch_audit_*.jsonl.gz"))

        for audit_file in list(audit_files) + list(gz_files):
            if len(events) >= limit:
                break

            try:
                # Open regular or gzipped file
                if audit_file.suffix == ".gz":
                    file_obj = gzip.open(audit_file, "rt")
                else:
                    file_obj = open(audit_file, "r")

                with file_obj as f:
                    for line in f:
                        if len(events) >= limit:
                            break

                        try:
                            event = json.loads(line.strip())
                            event_time = datetime.fromisoformat(event["timestamp"])

                            # Filter by time
                            if since and event_time < since:
                                continue
                            if until and event_time > until:
                                continue

                            events.append(event)

                        except (json.JSONDecodeError, KeyError, ValueError):
                            continue

            except Exception as e:
                self._logger.warning(f"Error reading {audit_file}: {e}")
                continue

        return events

    def get_events_by_state(
        self,
        state: str,
        limit: int = 100,
    ) -> List[dict]:
        """Get events for a specific state.

        Args:
            state: State name (e.g., "KILLED", "ACTIVE")
            limit: Maximum number of events

        Returns:
            List of matching events
        """
        all_events = self.get_events(limit=limit * 2)  # Get more to filter
        return [e for e in all_events if e.get("new_state") == state][:limit]

    def get_latest_event(self) -> Optional[dict]:
        """Get the most recent audit event.

        Returns:
            Latest event dict or None
        """
        # Find all audit files (regular and compressed) in reverse order (newest first)
        audit_files = sorted(self.audit_dir.glob("kill_switch_audit_*.jsonl"), reverse=True)
        gz_files = sorted(self.audit_dir.glob("kill_switch_audit_*.jsonl.gz"), reverse=True)

        all_files = []
        # Merge files by modification time, newest first
        for f in list(audit_files) + list(gz_files):
            all_files.append((f.stat().st_mtime, f))
        all_files.sort(reverse=True, key=lambda x: x[0])

        # Read last line from newest file
        for _, audit_file in all_files:
            try:
                # Open regular or gzipped file
                if audit_file.suffix == ".gz":
                    file_obj = gzip.open(audit_file, "rt")
                else:
                    file_obj = open(audit_file, "r")

                with file_obj as f:
                    lines = f.readlines()
                    if not lines:
                        continue

                    # Try lines from bottom up (in case last line is corrupt)
                    for line in reversed(lines):
                        try:
                            event = json.loads(line.strip())
                            return event
                        except (json.JSONDecodeError, ValueError):
                            continue

            except Exception as e:
                self._logger.warning(f"Error reading {audit_file}: {e}")
                continue

        return None

    def _maybe_rotate(self):
        """Rotate log file if needed."""
        # Check if new day (new file needed)
        new_file = self._get_current_file()
        if new_file != self._current_file:
            self._compress_old_file(self._current_file)
            self._current_file = new_file
            self._logger.info(f"Rotated to new audit file: {new_file.name}")

        # Check file size
        if self._current_file.exists():
            size = self._current_file.stat().st_size
            if size > self.max_file_size_bytes:
                # Rotate with timestamp suffix
                suffix = datetime.utcnow().strftime("%H%M%S")
                rotated = self._current_file.with_suffix(f".{suffix}.jsonl")
                self._current_file.rename(rotated)
                self._compress_old_file(rotated)
                self._logger.info(f"Rotated large file: {rotated.name}")

    def _compress_old_file(self, file: Path):
        """Compress an old audit file.

        Args:
            file: File to compress
        """
        if not file.exists():
            return

        try:
            gz_file = file.with_suffix(file.suffix + ".gz")

            with open(file, "rb") as f_in:
                with gzip.open(gz_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            file.unlink()
            self._logger.debug(f"Compressed: {file.name} → {gz_file.name}")

        except Exception as e:
            self._logger.warning(f"Failed to compress {file}: {e}")

    def cleanup_old_files(self):
        """Delete files older than retention period."""
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        deleted_count = 0

        for file in self.audit_dir.glob("kill_switch_audit_*"):
            try:
                # Extract date from filename
                # Format: kill_switch_audit_YYYY-MM-DD.jsonl[.gz]
                name_parts = file.stem.split("_")
                if len(name_parts) < 4:
                    continue

                date_str = name_parts[3]  # YYYY-MM-DD part
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff:
                    file.unlink()
                    deleted_count += 1
                    self._logger.info(f"Deleted old audit file: {file.name}")

            except (ValueError, IndexError) as e:
                self._logger.debug(f"Skipping file {file.name}: {e}")
                continue

        if deleted_count > 0:
            self._logger.info(
                f"Cleaned up {deleted_count} old audit files "
                f"(retention: {self.retention_days} days)"
            )

    def get_statistics(self) -> dict:
        """Get audit trail statistics.

        Returns:
            Dictionary with statistics
        """
        files = list(self.audit_dir.glob("kill_switch_audit_*"))

        total_size = sum(f.stat().st_size for f in files)
        total_events = 0

        for f in files:
            try:
                if f.suffix == ".gz":
                    with gzip.open(f, "rt") as file:
                        total_events += sum(1 for _ in file)
                else:
                    with open(f) as file:
                        total_events += sum(1 for _ in file)
            except Exception:
                continue

        return {
            "total_files": len(files),
            "total_size_mb": total_size / (1024 * 1024),
            "total_events": total_events,
            "oldest_file": (
                min(f.stat().st_mtime for f in files) if files else None
            ),
            "newest_file": (
                max(f.stat().st_mtime for f in files) if files else None
            ),
        }
