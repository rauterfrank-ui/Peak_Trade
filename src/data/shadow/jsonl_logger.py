"""
JSONL Rotating Logger — Minimale Implementation ohne externe Dependencies.

Schreibt JSON Lines mit Size-basierter Rotation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class JsonlRotatingLogger:
    """
    JSONL Logger mit Size-basierter Rotation.

    Rotation: file.jsonl → file.jsonl.1 → file.jsonl.2 → ...
    """

    def __init__(self, path: str, max_bytes: int = 1_000_000, backup_count: int = 5) -> None:
        """
        Args:
            path: Log-File Path
            max_bytes: Max Size vor Rotation
            backup_count: Anzahl Backups (älteste wird gelöscht)
        """
        self.path = Path(path)
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        # Erstelle Verzeichnis
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, record: dict[str, Any]) -> None:
        """
        Schreibt ein JSON-Record.

        Args:
            record: Dict (muss JSON-serializable sein)
        """
        # Check Rotation
        if self.path.exists() and self.path.stat().st_size >= self.max_bytes:
            self._rotate()

        # Write JSONL
        with open(self.path, "a", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)
            f.write("\n")

    def _rotate(self) -> None:
        """Rotiert Log-Files."""
        # Lösche ältestes Backup falls nötig
        oldest_backup = self.path.with_suffix(f"{self.path.suffix}.{self.backup_count}")
        if oldest_backup.exists():
            oldest_backup.unlink()

        # Shift alle Backups um 1
        for i in range(self.backup_count - 1, 0, -1):
            src = self.path.with_suffix(f"{self.path.suffix}.{i}")
            dst = self.path.with_suffix(f"{self.path.suffix}.{i + 1}")
            if src.exists():
                src.rename(dst)

        # Rename current → .1
        if self.path.exists():
            backup = self.path.with_suffix(f"{self.path.suffix}.1")
            self.path.rename(backup)
