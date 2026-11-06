"""Models for S03 atomic Auth-v2 reissue→consume→execute owner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


class AtomicS03AuthV2ReissueConsumeExecuteError(RuntimeError):
    """Fail-closed atomic orchestration error (never embed confirm-token plaintext)."""


@dataclass
class AtomicOrchestratorResultV1:
    status: str
    verdict: str
    old_authorization_id: str = ""
    old_authorization_revoked: bool = False
    new_authorization_id: str = ""
    new_authorization_revoked_on_failure: bool = False
    authorization_consumed: bool = False
    authorization_consumed_exactly_once: bool = False
    session_lock_created: bool = False
    session_lock_removed: bool = False
    network_activity_occurred: bool = False
    evidence_mutation_occurred: bool = False
    real_session_started: bool = False
    requested_duration_seconds: int = 10860
    actual_monotonic_duration_seconds: float = 0.0
    evidence_root: str = ""
    integrity_manifest_path: str = ""
    terminal_verdict_path: str = ""
    blocker: str = ""
    side_effect_probe: list[str] = field(default_factory=list)
    s03_result: Optional[dict[str, Any]] = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "verdict": self.verdict,
            "old_authorization_id": self.old_authorization_id,
            "old_authorization_revoked": self.old_authorization_revoked,
            "new_authorization_id": self.new_authorization_id,
            "new_authorization_revoked_on_failure": self.new_authorization_revoked_on_failure,
            "authorization_consumed": self.authorization_consumed,
            "authorization_consumed_exactly_once": self.authorization_consumed_exactly_once,
            "session_lock_created": self.session_lock_created,
            "session_lock_removed": self.session_lock_removed,
            "network_activity_occurred": self.network_activity_occurred,
            "evidence_mutation_occurred": self.evidence_mutation_occurred,
            "real_session_started": self.real_session_started,
            "requested_duration_seconds": self.requested_duration_seconds,
            "actual_monotonic_duration_seconds": self.actual_monotonic_duration_seconds,
            "evidence_root": self.evidence_root,
            "integrity_manifest_path": self.integrity_manifest_path,
            "terminal_verdict_path": self.terminal_verdict_path,
            "blocker": self.blocker,
            "side_effect_probe": list(self.side_effect_probe),
            "s03_result": self.s03_result,
            "notes": list(self.notes),
            "token_plaintext_persisted": False,
            "token_exposed": False,
            "issue_and_consume_same_process": True,
            "token_process_boundary_crossed": False,
        }
