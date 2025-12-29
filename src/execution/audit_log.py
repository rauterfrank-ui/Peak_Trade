"""
Audit Log (WP0A - Phase 0 Execution Core)

Append-only audit trail for all execution events.

Design Goals:
- Append-only (immutable)
- Deterministic ordering (sequence + timestamp)
- Structured format (JSON-serializable)
- Fast writes, infrequent reads
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

from src.execution.contracts import LedgerEntry


# ============================================================================
# Audit Log
# ============================================================================


class AuditLog:
    """
    Append-only audit log.

    Features:
    - Store all ledger entries
    - Query by client_order_id, event_type, time range
    - Export to JSON/file
    """

    def __init__(self):
        """Initialize empty audit log"""
        self._entries: List[LedgerEntry] = []
        self._sequence = 0

    def append(self, entry: LedgerEntry) -> None:
        """
        Append entry to log.

        Args:
            entry: Ledger entry to append
        """
        # Ensure sequential ordering
        self._sequence += 1
        entry.sequence = self._sequence

        # Append (immutable)
        self._entries.append(entry)

    def append_many(self, entries: List[LedgerEntry]) -> None:
        """
        Append multiple entries.

        Args:
            entries: List of ledger entries
        """
        for entry in entries:
            self.append(entry)

    def get_all_entries(self) -> List[LedgerEntry]:
        """Get all entries (chronological)"""
        return self._entries.copy()

    def get_entries_for_order(self, client_order_id: str) -> List[LedgerEntry]:
        """
        Get all entries for a specific order.

        Args:
            client_order_id: Client order ID

        Returns:
            List of entries (chronological)
        """
        return [e for e in self._entries if e.client_order_id == client_order_id]

    def get_entries_by_event_type(self, event_type: str) -> List[LedgerEntry]:
        """
        Get all entries of a specific event type.

        Args:
            event_type: Event type (e.g., "ORDER_SUBMITTED")

        Returns:
            List of entries
        """
        return [e for e in self._entries if e.event_type == event_type]

    def get_entries_in_range(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[LedgerEntry]:
        """
        Get entries in time range.

        Args:
            start_time: Start time (inclusive)
            end_time: End time (inclusive)

        Returns:
            List of entries
        """
        entries = self._entries

        if start_time:
            entries = [e for e in entries if e.timestamp >= start_time]

        if end_time:
            entries = [e for e in entries if e.timestamp <= end_time]

        return entries

    def get_entry_count(self) -> int:
        """Get total number of entries"""
        return len(self._entries)

    def export_to_json(self) -> str:
        """
        Export all entries to JSON.

        Returns:
            JSON string
        """
        entries_dict = [entry.to_dict() for entry in self._entries]
        return json.dumps(entries_dict, indent=2)

    def export_to_file(self, file_path: str) -> None:
        """
        Export audit log to file.

        Args:
            file_path: Output file path
        """
        with open(file_path, "w") as f:
            f.write(self.export_to_json())

    def to_dict(self) -> Dict[str, Any]:
        """
        Export audit log summary.

        Returns:
            Dict with audit log statistics
        """
        event_type_counts: Dict[str, int] = {}
        for entry in self._entries:
            event_type_counts[entry.event_type] = event_type_counts.get(entry.event_type, 0) + 1

        return {
            "total_entries": len(self._entries),
            "sequence": self._sequence,
            "event_type_counts": event_type_counts,
            "first_entry": self._entries[0].timestamp.isoformat() if self._entries else None,
            "last_entry": self._entries[-1].timestamp.isoformat() if self._entries else None,
        }
