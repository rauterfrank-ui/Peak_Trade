"""State Persistence for Kill Switch.

Provides crash-safe state persistence using atomic writes.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .state import KillSwitchState


logger = logging.getLogger(__name__)


class StatePersistence:
    """Persists kill switch state to disk.

    Features:
        - Atomic writes (crash-safe via tmp → rename)
        - Automatic backup before overwrite
        - State recovery on startup

    Usage:
        >>> persistence = StatePersistence("data/kill_switch/state.json")
        >>>
        >>> # Save state
        >>> persistence.save(
        ...     KillSwitchState.KILLED,
        ...     killed_at=datetime.utcnow(),
        ...     trigger_reason="Drawdown limit"
        ... )
        >>>
        >>> # Load state
        >>> state_data = persistence.load()
        >>> if state_data:
        ...     # Restore state
    """

    def __init__(
        self,
        state_file: str,
        backup_dir: Optional[str] = None,
        logger_instance: Optional[logging.Logger] = None,
    ):
        """Initialize state persistence.

        Args:
            state_file: Path to state file
            backup_dir: Path to backup directory (default: {state_file}.parent/backups)
            logger_instance: Optional logger instance
        """
        self.state_file = Path(state_file)
        self.backup_dir = (
            Path(backup_dir)
            if backup_dir
            else self.state_file.parent / "backups"
        )
        self._logger = logger_instance or logger

        # Create directories
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        state: KillSwitchState,
        killed_at: Optional[datetime] = None,
        trigger_reason: Optional[str] = None,
        recovery_started_at: Optional[datetime] = None,
    ):
        """Save current state to disk.

        Uses atomic write pattern (tmp → rename) for crash safety.

        Args:
            state: Current kill switch state
            killed_at: Timestamp when killed (if KILLED)
            trigger_reason: Reason for trigger (if KILLED)
            recovery_started_at: Timestamp when recovery started (if RECOVERING)
        """
        data = {
            "state": state.name,
            "saved_at": datetime.utcnow().isoformat(),
            "killed_at": killed_at.isoformat() if killed_at else None,
            "trigger_reason": trigger_reason,
            "recovery_started_at": (
                recovery_started_at.isoformat() if recovery_started_at else None
            ),
            "version": "1.0",
        }

        # Atomic write: tmp → rename
        tmp_file = self.state_file.with_suffix(".tmp")

        try:
            # Write to temporary file
            with open(tmp_file, "w") as f:
                json.dump(data, f, indent=2)

            # Backup existing file
            if self.state_file.exists():
                backup_name = f"state_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                backup_path = self.backup_dir / backup_name
                shutil.copy(self.state_file, backup_path)
                self._logger.debug(f"State backed up to {backup_name}")

            # Atomic rename
            tmp_file.rename(self.state_file)

            self._logger.debug(f"State saved: {state.name}")

        except Exception as e:
            self._logger.error(f"Failed to save state: {e}", exc_info=True)
            if tmp_file.exists():
                tmp_file.unlink()
            raise

    def load(self) -> Optional[dict]:
        """Load saved state from disk.

        Returns:
            State dictionary or None if not found
        """
        if not self.state_file.exists():
            self._logger.debug("No saved state found")
            return None

        try:
            with open(self.state_file) as f:
                data = json.load(f)

            self._logger.info(f"State loaded: {data.get('state')}")
            return data

        except json.JSONDecodeError as e:
            self._logger.error(f"Corrupt state file: {e}")
            return None

        except Exception as e:
            self._logger.error(f"Failed to load state: {e}", exc_info=True)
            return None

    def clear(self):
        """Clear saved state."""
        if self.state_file.exists():
            self.state_file.unlink()
            self._logger.info("State cleared")

    def list_backups(self) -> list[Path]:
        """List available backup files.

        Returns:
            List of backup file paths, sorted by modification time
        """
        backups = sorted(
            self.backup_dir.glob("state_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return backups

    def restore_from_backup(self, backup_file: Optional[str] = None) -> bool:
        """Restore state from backup.

        Args:
            backup_file: Specific backup file to restore, or None for latest

        Returns:
            True if successful
        """
        if backup_file:
            backup_path = Path(backup_file)
        else:
            # Get latest backup
            backups = self.list_backups()
            if not backups:
                self._logger.warning("No backups available")
                return False
            backup_path = backups[0]

        if not backup_path.exists():
            self._logger.error(f"Backup not found: {backup_path}")
            return False

        try:
            shutil.copy(backup_path, self.state_file)
            self._logger.info(f"State restored from {backup_path.name}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to restore from backup: {e}")
            return False
