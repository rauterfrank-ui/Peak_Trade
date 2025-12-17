# src/infra/runbooks/models.py
"""
Peak_Trade: Runbook Models (Phase 84)
=====================================

Datenmodelle für Incident-Runbooks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RunbookLink:
    """
    Repräsentiert einen Link zu einem Incident-Runbook.

    Attributes:
        id: Eindeutiger Identifier (z.B. "live_alert_pipeline_v1")
        title: Kurzer, lesbarer Titel (z.B. "Live Alert Pipeline Runbook")
        url: Vollständige URL zur Dokumentation
        description: Optionale Kurzbeschreibung des Runbook-Inhalts
    """

    id: str
    title: str
    url: str
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert RunbookLink zu Dict für JSON-Serialisierung."""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunbookLink:
        """Erstellt RunbookLink aus Dict."""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            url=data.get("url", ""),
            description=data.get("description"),
        )

    def __repr__(self) -> str:
        return f"RunbookLink(id={self.id!r}, title={self.title!r})"
