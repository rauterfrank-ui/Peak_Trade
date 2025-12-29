"""
Session Registry - WP1D (Phase 1 Shadow Trading)

Read-only wrapper around existing LiveSessionRegistry for operator UX.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SessionStatus:
    """
    Session status snapshot.

    Attributes:
        session_id: Unique session ID
        status: Status ("started" | "running" | "completed" | "failed")
        started_at: Start timestamp
        last_update: Last update timestamp
        metadata: Additional metadata
    """

    session_id: str
    status: str
    started_at: datetime
    last_update: datetime
    metadata: Dict = None

    def to_dict(self) -> Dict:
        """Convert to dict."""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "last_update": self.last_update.isoformat(),
            "metadata": self.metadata or {},
        }


class SessionRegistry:
    """
    In-memory session registry for operator UX.

    This is a minimal read-only wrapper for Phase 1.
    Full integration with src.experiments.live_session_registry in Phase 2+.

    Usage:
        >>> registry = SessionRegistry()
        >>> registry.create_session("shadow_001", metadata={"strategy": "ma_cross"})
        >>> status = registry.get_status("shadow_001")
        >>> sessions = registry.list_sessions()
    """

    def __init__(self):
        """Initialize empty registry."""
        self._sessions: Dict[str, SessionStatus] = {}

    def create_session(
        self,
        session_id: str,
        metadata: Optional[Dict] = None,
    ) -> SessionStatus:
        """
        Create new session.

        Args:
            session_id: Unique session ID
            metadata: Optional metadata

        Returns:
            SessionStatus
        """
        if session_id in self._sessions:
            logger.warning(f"Session {session_id} already exists")
            return self._sessions[session_id]

        status = SessionStatus(
            session_id=session_id,
            status="started",
            started_at=datetime.utcnow(),
            last_update=datetime.utcnow(),
            metadata=metadata or {},
        )

        self._sessions[session_id] = status
        logger.info(f"Session created: {session_id}")

        return status

    def update_status(
        self,
        session_id: str,
        status: str,
    ) -> Optional[SessionStatus]:
        """
        Update session status.

        Args:
            session_id: Session ID
            status: New status

        Returns:
            Updated SessionStatus or None if not found
        """
        if session_id not in self._sessions:
            logger.warning(f"Session {session_id} not found")
            return None

        session = self._sessions[session_id]
        session.status = status
        session.last_update = datetime.utcnow()

        logger.info(f"Session {session_id} status updated: {status}")

        return session

    def get_status(self, session_id: str) -> Optional[SessionStatus]:
        """
        Get session status.

        Args:
            session_id: Session ID

        Returns:
            SessionStatus or None if not found
        """
        return self._sessions.get(session_id)

    def list_sessions(
        self,
        status_filter: Optional[str] = None,
    ) -> List[SessionStatus]:
        """
        List all sessions.

        Args:
            status_filter: Optional status filter

        Returns:
            List of SessionStatus
        """
        sessions = list(self._sessions.values())

        if status_filter:
            sessions = [s for s in sessions if s.status == status_filter]

        # Sort by started_at (newest first)
        sessions.sort(key=lambda s: s.started_at, reverse=True)

        return sessions

    def get_summary(self) -> Dict:
        """
        Get registry summary.

        Returns:
            Summary dict
        """
        sessions = list(self._sessions.values())

        return {
            "total_sessions": len(sessions),
            "by_status": {
                "started": len([s for s in sessions if s.status == "started"]),
                "running": len([s for s in sessions if s.status == "running"]),
                "completed": len([s for s in sessions if s.status == "completed"]),
                "failed": len([s for s in sessions if s.status == "failed"]),
            },
        }
