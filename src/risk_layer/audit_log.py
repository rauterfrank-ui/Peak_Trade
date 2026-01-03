"""
Risk Audit Log Writer
======================

Writes risk decisions to a JSONL (JSON Lines) audit log.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


class AuditLogWriter:
    """
    Writes risk audit events to a JSONL file.

    Each event is written as a single JSON object per line.
    """

    def __init__(self, path: str) -> None:
        """
        Initialize the audit log writer.

        Args:
            path: Path to the audit log file (JSONL format)
        """
        self.path = Path(path)

        # Create parent directories if needed
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: dict) -> None:
        """
        Write an audit event to the log.

        Args:
            event: Dict containing the audit event data

        Raises:
            OSError: If writing to the file fails
        """
        # Add timestamp if not present
        if "timestamp_utc" not in event:
            event["timestamp_utc"] = datetime.now(timezone.utc).isoformat()

        try:
            with self.path.open("a", encoding="utf-8") as f:
                json.dump(event, f, ensure_ascii=False)
                f.write("\n")
                f.flush()
        except OSError as e:
            raise OSError(f"Failed to write audit log to {self.path}: {e}") from e
