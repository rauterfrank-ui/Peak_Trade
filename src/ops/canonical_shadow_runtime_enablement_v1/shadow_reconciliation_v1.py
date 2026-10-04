"""Shadow-lane reconciliation — simulated namespace only (no venue truth)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ShadowReconciliationLedgerV1:
    """In-memory ledger for bounded offline Shadow forensic reproof."""

    applied_event_keys: set[str] = field(default_factory=set)
    duplicate_application_count: int = 0
    reconciled_event_count: int = 0

    def record_simulated_execution(
        self,
        *,
        flight_id: str,
        cycle_id: int,
        session_id: str,
    ) -> tuple[bool, str]:
        key = f"{session_id}:{flight_id}:{cycle_id}"
        if key in self.applied_event_keys:
            self.duplicate_application_count += 1
            return False, "DUPLICATE_SIMULATED_EXECUTION"
        self.applied_event_keys.add(key)
        self.reconciled_event_count += 1
        return True, "RECONCILED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "reconciled_event_count": self.reconciled_event_count,
            "duplicate_application_count": self.duplicate_application_count,
            "SHADOW_TO_PRODUCTIVE_STATE_LEAK_COUNT": 0,
        }
