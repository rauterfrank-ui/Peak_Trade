# src/live/alert_storage.py
"""
Peak_Trade: Alert Storage Layer (Phase 83)
==========================================

Persistiert Alerts aus der Alert-Pipeline für die Web-Dashboard-Historie.

Features:
- Append-only JSON-Lines-Storage (eine Zeile pro Alert)
- Tägliche Rotation (ein File pro Tag)
- Filter nach Severity, Category, Session, Zeitfenster
- Limitierung für performante UI-Abfragen
- Thread-safe durch File-Locking (best effort)

Storage-Struktur:
    live_runs/alerts/
        alerts_2025-12-09.jsonl
        alerts_2025-12-10.jsonl
        ...

Usage:
    from src.live.alert_storage import AlertStorage, get_default_alert_storage

    # Storage initialisieren
    storage = get_default_alert_storage()

    # Alert speichern (wird von AlertPipelineManager aufgerufen)
    storage.store(alert_message)

    # Alerts abrufen (für Web-Dashboard)
    recent = storage.list_alerts(limit=100, hours=24)
    filtered = storage.list_alerts(
        limit=50,
        severity=[AlertSeverity.WARN, AlertSeverity.CRITICAL],
        category=[AlertCategory.RISK],
    )
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

logger = logging.getLogger(__name__)

# Projekt-Root für Default-Pfad
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_ALERTS_DIR = _PROJECT_ROOT / "live_runs" / "alerts"


# =============================================================================
# STORED ALERT MODEL
# =============================================================================


@dataclass
class StoredAlert:
    """
    Persistierter Alert mit allen Feldern.

    Diese Klasse repräsentiert einen Alert, wie er aus dem Storage gelesen wird.
    Sie ist unabhängig von AlertMessage, um zirkuläre Imports zu vermeiden.
    """

    id: str
    title: str
    body: str
    severity: str  # "INFO", "WARN", "CRITICAL"
    category: str  # "RISK", "EXECUTION", "SYSTEM"
    source: str
    session_id: Optional[str]
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)

    # Zusätzliche Felder für UI
    stored_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dict für JSON-Serialisierung."""
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "severity": self.severity,
            "category": self.category,
            "source": self.source,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "stored_at": self.stored_at.isoformat() if self.stored_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoredAlert":
        """Erstellt StoredAlert aus Dict."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        stored_at = data.get("stored_at")
        if isinstance(stored_at, str):
            stored_at = datetime.fromisoformat(stored_at.replace("Z", "+00:00"))

        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            body=data.get("body", ""),
            severity=data.get("severity", "INFO"),
            category=data.get("category", "SYSTEM"),
            source=data.get("source", ""),
            session_id=data.get("session_id"),
            timestamp=timestamp,
            context=data.get("context", {}),
            stored_at=stored_at,
        )

    @property
    def severity_level(self) -> int:
        """Numerischer Severity-Level für Sortierung."""
        levels = {"INFO": 10, "WARN": 20, "CRITICAL": 30}
        return levels.get(self.severity, 0)


# =============================================================================
# ALERT STORAGE
# =============================================================================


class AlertStorage:
    """
    File-basiertes Storage für Alerts (JSON-Lines).

    Features:
    - Append-only, tägliche Rotation
    - Thread-safe Writes
    - Effiziente Reads mit Filterung
    - Automatische Verzeichnis-Erstellung

    Implementierung:
    - Ein .jsonl File pro Tag: alerts_YYYY-MM-DD.jsonl
    - Alerts werden als JSON-Zeilen angehängt
    - Reads scannen die relevanten Dateien rückwärts
    """

    def __init__(
        self,
        storage_dir: Path,
        max_age_days: int = 30,
        max_alerts_per_query: int = 1000,
    ) -> None:
        """
        Initialisiert AlertStorage.

        Args:
            storage_dir: Verzeichnis für Alert-Files
            max_age_days: Maximales Alter für Cleanup (default: 30 Tage)
            max_alerts_per_query: Maximale Alerts pro Query (default: 1000)
        """
        self._storage_dir = Path(storage_dir)
        self._max_age_days = max_age_days
        self._max_alerts_per_query = max_alerts_per_query
        self._write_lock = threading.Lock()
        self._logger = logging.getLogger(f"{__name__}.AlertStorage")

        # Verzeichnis erstellen
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    @property
    def storage_dir(self) -> Path:
        """Pfad zum Storage-Verzeichnis."""
        return self._storage_dir

    def _get_file_path(self, date: datetime) -> Path:
        """Generiert Dateipfad für ein Datum."""
        date_str = date.strftime("%Y-%m-%d")
        return self._storage_dir / f"alerts_{date_str}.jsonl"

    def _generate_alert_id(self, alert_data: Dict[str, Any]) -> str:
        """Generiert eine eindeutige Alert-ID."""
        import hashlib

        # Kombiniere relevante Felder für Hash
        hash_input = (
            f"{alert_data.get('timestamp', '')}"
            f"{alert_data.get('source', '')}"
            f"{alert_data.get('title', '')}"
            f"{alert_data.get('severity', '')}"
        )
        hash_digest = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
        return f"alert_{hash_digest}"

    def store(self, alert: Any) -> Optional[str]:
        """
        Speichert einen Alert.

        Args:
            alert: AlertMessage-Objekt oder Dict mit Alert-Daten

        Returns:
            Alert-ID wenn erfolgreich, None bei Fehler
        """
        try:
            # Konvertiere AlertMessage zu Dict wenn nötig
            if hasattr(alert, "to_dict"):
                alert_data = alert.to_dict()
            elif isinstance(alert, dict):
                alert_data = alert.copy()
            else:
                self._logger.error(f"Unsupported alert type: {type(alert)}")
                return None

            # Timestamp parsen
            timestamp = alert_data.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            elif timestamp is None:
                timestamp = datetime.now(timezone.utc)

            # ID generieren
            alert_id = self._generate_alert_id(alert_data)
            alert_data["id"] = alert_id
            alert_data["stored_at"] = datetime.now(timezone.utc).isoformat()

            # Dateipfad bestimmen
            file_path = self._get_file_path(timestamp)

            # Thread-safe schreiben
            with self._write_lock:
                with open(file_path, "a", encoding="utf-8") as f:
                    json_line = json.dumps(alert_data, ensure_ascii=False, default=str)
                    f.write(json_line + "\n")

            self._logger.debug(f"Alert stored: {alert_id} → {file_path.name}")
            return alert_id

        except Exception as e:
            self._logger.error(f"Failed to store alert: {e}", exc_info=True)
            return None

    def list_alerts(
        self,
        limit: int = 100,
        hours: Optional[int] = None,
        since: Optional[datetime] = None,
        severity: Optional[Sequence[str]] = None,
        category: Optional[Sequence[str]] = None,
        session_id: Optional[str] = None,
        source: Optional[str] = None,
    ) -> List[StoredAlert]:
        """
        Liest Alerts mit optionalen Filtern.

        Args:
            limit: Maximale Anzahl Alerts (default: 100)
            hours: Zeitfenster in Stunden (z.B. 24 = letzte 24h)
            since: Zeitpunkt ab dem Alerts geladen werden
            severity: Filter nach Severity (z.B. ["WARN", "CRITICAL"])
            category: Filter nach Kategorie (z.B. ["RISK"])
            session_id: Filter nach Session-ID
            source: Filter nach Source

        Returns:
            Liste von StoredAlert-Objekten (neueste zuerst)
        """
        # Limit begrenzen
        limit = min(limit, self._max_alerts_per_query)

        # Zeitfenster bestimmen
        now = datetime.now(timezone.utc)
        if hours is not None:
            since = now - timedelta(hours=hours)
        elif since is None:
            # Default: letzte 7 Tage
            since = now - timedelta(days=7)

        # Severity normalisieren
        if severity:
            severity = [s.upper() for s in severity]

        # Category normalisieren
        if category:
            category = [c.upper() for c in category]

        # Relevante Dateien finden (neueste zuerst)
        relevant_files = self._get_relevant_files(since, now)

        alerts: List[StoredAlert] = []

        for file_path in relevant_files:
            if len(alerts) >= limit:
                break

            try:
                file_alerts = self._read_alerts_from_file(
                    file_path,
                    since=since,
                    severity=severity,
                    category=category,
                    session_id=session_id,
                    source=source,
                )
                alerts.extend(file_alerts)
            except Exception as e:
                self._logger.warning(f"Failed to read {file_path}: {e}")

        # Sortieren (neueste zuerst) und limitieren
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        return alerts[:limit]

    def _get_relevant_files(self, since: datetime, until: datetime) -> List[Path]:
        """
        Findet relevante Alert-Dateien für einen Zeitraum.

        Returns:
            Liste von Dateipfaden (neueste zuerst)
        """
        files: List[Path] = []

        if not self._storage_dir.exists():
            return files

        # Sammle alle .jsonl Dateien
        for file_path in self._storage_dir.glob("alerts_*.jsonl"):
            # Parse Datum aus Dateiname
            try:
                date_str = file_path.stem.replace("alerts_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

                # Prüfe ob File im relevanten Zeitraum
                if file_date.date() >= since.date() and file_date.date() <= until.date():
                    files.append(file_path)
            except ValueError:
                continue

        # Sortieren (neueste zuerst)
        files.sort(key=lambda p: p.stem, reverse=True)
        return files

    def _read_alerts_from_file(
        self,
        file_path: Path,
        since: Optional[datetime] = None,
        severity: Optional[Sequence[str]] = None,
        category: Optional[Sequence[str]] = None,
        session_id: Optional[str] = None,
        source: Optional[str] = None,
    ) -> List[StoredAlert]:
        """
        Liest und filtert Alerts aus einer Datei.

        Returns:
            Liste von StoredAlert-Objekten
        """
        alerts: List[StoredAlert] = []

        if not file_path.exists():
            return alerts

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    alert = StoredAlert.from_dict(data)

                    # Filter anwenden
                    if since and alert.timestamp < since:
                        continue
                    if severity and alert.severity not in severity:
                        continue
                    if category and alert.category not in category:
                        continue
                    if session_id and alert.session_id != session_id:
                        continue
                    if source and source not in alert.source:
                        continue

                    alerts.append(alert)

                except (json.JSONDecodeError, KeyError) as e:
                    self._logger.debug(f"Skipping invalid line in {file_path}: {e}")
                    continue

        return alerts

    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Berechnet Statistiken über Alerts.

        Args:
            hours: Zeitfenster in Stunden

        Returns:
            Dict mit Statistiken (counts, by_severity, by_category, etc.)
        """
        alerts = self.list_alerts(limit=self._max_alerts_per_query, hours=hours)

        # Gruppierung nach Severity
        by_severity: Dict[str, int] = {"INFO": 0, "WARN": 0, "CRITICAL": 0}
        for alert in alerts:
            if alert.severity in by_severity:
                by_severity[alert.severity] += 1

        # Gruppierung nach Category
        by_category: Dict[str, int] = {"RISK": 0, "EXECUTION": 0, "SYSTEM": 0}
        for alert in alerts:
            if alert.category in by_category:
                by_category[alert.category] += 1

        # Gruppierung nach Session
        sessions: set = set()
        for alert in alerts:
            if alert.session_id:
                sessions.add(alert.session_id)

        # Letzter CRITICAL Alert
        critical_alerts = [a for a in alerts if a.severity == "CRITICAL"]
        last_critical = critical_alerts[0] if critical_alerts else None

        return {
            "total": len(alerts),
            "by_severity": by_severity,
            "by_category": by_category,
            "sessions_with_alerts": len(sessions),
            "last_critical": last_critical.to_dict() if last_critical else None,
            "hours": hours,
        }

    def cleanup_old_files(self) -> int:
        """
        Löscht Alert-Dateien die älter als max_age_days sind.

        Returns:
            Anzahl gelöschter Dateien
        """
        if not self._storage_dir.exists():
            return 0

        cutoff = datetime.now(timezone.utc) - timedelta(days=self._max_age_days)
        deleted = 0

        for file_path in self._storage_dir.glob("alerts_*.jsonl"):
            try:
                date_str = file_path.stem.replace("alerts_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

                if file_date < cutoff:
                    file_path.unlink()
                    deleted += 1
                    self._logger.info(f"Deleted old alert file: {file_path.name}")

            except (ValueError, OSError) as e:
                self._logger.warning(f"Failed to process {file_path}: {e}")

        return deleted


# =============================================================================
# SINGLETON / DEFAULT STORAGE
# =============================================================================


_default_storage: Optional[AlertStorage] = None
_storage_lock = threading.Lock()


def get_default_alert_storage(
    storage_dir: Optional[Path] = None,
) -> AlertStorage:
    """
    Gibt die Default-AlertStorage-Instanz zurück (Singleton).

    Args:
        storage_dir: Optionaler Override für Storage-Verzeichnis

    Returns:
        AlertStorage-Instanz
    """
    global _default_storage

    if _default_storage is not None:
        return _default_storage

    with _storage_lock:
        if _default_storage is not None:
            return _default_storage

        dir_path = storage_dir or _DEFAULT_ALERTS_DIR
        _default_storage = AlertStorage(dir_path)
        return _default_storage


def reset_default_storage() -> None:
    """Setzt die Default-Storage-Instanz zurück (für Tests)."""
    global _default_storage
    with _storage_lock:
        _default_storage = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def store_alert(alert: Any) -> Optional[str]:
    """
    Convenience-Funktion zum Speichern eines Alerts.

    Args:
        alert: AlertMessage oder Dict

    Returns:
        Alert-ID wenn erfolgreich
    """
    storage = get_default_alert_storage()
    return storage.store(alert)


def list_recent_alerts(
    limit: int = 100,
    hours: int = 24,
    severity: Optional[Sequence[str]] = None,
    category: Optional[Sequence[str]] = None,
) -> List[StoredAlert]:
    """
    Convenience-Funktion zum Abrufen von Alerts.

    Args:
        limit: Maximale Anzahl
        hours: Zeitfenster in Stunden
        severity: Severity-Filter
        category: Category-Filter

    Returns:
        Liste von StoredAlert-Objekten
    """
    storage = get_default_alert_storage()
    return storage.list_alerts(
        limit=limit,
        hours=hours,
        severity=severity,
        category=category,
    )


def get_alert_stats(hours: int = 24) -> Dict[str, Any]:
    """
    Convenience-Funktion für Alert-Statistiken.

    Args:
        hours: Zeitfenster in Stunden

    Returns:
        Dict mit Statistiken
    """
    storage = get_default_alert_storage()
    return storage.get_stats(hours=hours)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Classes
    "StoredAlert",
    "AlertStorage",
    # Singleton
    "get_default_alert_storage",
    "reset_default_storage",
    # Convenience Functions
    "store_alert",
    "list_recent_alerts",
    "get_alert_stats",
]
