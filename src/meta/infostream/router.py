"""
InfoStream v1 – Router-Modul.

Routet LearningSnippets in das zentrale Learning-Log (Mindmap-kompatibel).

Das Learning-Log hat folgende Struktur:
```markdown
# InfoStream Learning Log

## 2025-12-11

### INF-20251211_143920_daily_quick
- Learning 1
- Learning 2

### INF-20251211_150000_weekly_core
- Learning 1
- Learning 2
```

Verwendung:
    from src.meta.infostream.router import append_learnings_to_log

    snippets = [LearningSnippet(event_id="INF-...", lines=["Learning 1", "Learning 2"])]
    append_learnings_to_log(snippets, Path("docs/mindmap/INFOSTREAM_LEARNING_LOG.md"))
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from .models import LearningSnippet

logger = logging.getLogger(__name__)


# Header für neue Learning-Log-Dateien
LEARNING_LOG_HEADER = """# InfoStream Learning Log

> **Zweck:** Sammlung aller LEARNING_SNIPPETs aus dem InfoStream-System
> **Aktualisierung:** Kontinuierlich durch InfoStream-Automation
> **Siehe:** [InfoStream README](../infostream/README.md)

---

"""


def append_learnings_to_log(
    snippets: list[LearningSnippet],
    log_path: Path,
    date: datetime | None = None,
) -> None:
    """
    Hängt LearningSnippets an das zentrale Learning-Log an.

    Parameters
    ----------
    snippets : List[LearningSnippet]
        Liste der Learnings zum Anhängen
    log_path : Path
        Pfad zur Learning-Log-Datei, z.B. docs/mindmap/INFOSTREAM_LEARNING_LOG.md
    date : datetime, optional
        Datum für die Gruppierung. Default: heute.

    Notes
    -----
    - Falls log_path nicht existiert, wird ein neues Log mit Header erstellt.
    - Learnings werden unter dem aktuellen Datum (## YYYY-MM-DD) gruppiert.
    - Pro Event wird ein Markdown-Block mit ### <event_id> erstellt.
    - Duplikate (gleiche event_id) werden übersprungen.
    """
    if not snippets:
        logger.info("Keine Learnings zum Anhängen")
        return

    if date is None:
        date = datetime.now()

    date_str = date.strftime("%Y-%m-%d")

    # Sicherstellen, dass das Verzeichnis existiert
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Existierendes Log laden oder neues erstellen
    if log_path.exists():
        content = log_path.read_text(encoding="utf-8")
    else:
        content = LEARNING_LOG_HEADER
        logger.info(f"Neues Learning-Log erstellt: {log_path}")

    # Bereits vorhandene Event-IDs ermitteln (Duplikat-Check)
    existing_event_ids = set(re.findall(r"### (INF-[^\n]+)", content))

    # Neue Snippets filtern
    new_snippets = [s for s in snippets if s.event_id not in existing_event_ids]

    if not new_snippets:
        logger.info("Alle Learnings bereits im Log vorhanden")
        return

    # Datum-Sektion finden oder erstellen
    date_section_pattern = f"## {date_str}"

    if date_section_pattern not in content:
        # Neue Datum-Sektion hinzufügen
        # Finde die beste Position (nach dem Header, vor älteren Einträgen)

        # Suche nach existierenden Datum-Sektionen
        existing_dates = re.findall(r"## (\d{4}-\d{2}-\d{2})", content)

        if existing_dates:
            # Füge vor der ersten existierenden Datum-Sektion ein (neueste zuerst)
            first_date_match = re.search(r"## \d{4}-\d{2}-\d{2}", content)
            if first_date_match:
                insert_pos = first_date_match.start()
                content = (
                    content[:insert_pos] +
                    f"## {date_str}\n\n" +
                    content[insert_pos:]
                )
        else:
            # Keine Datum-Sektionen vorhanden, ans Ende anhängen
            if not content.endswith("\n"):
                content += "\n"
            content += f"\n## {date_str}\n\n"

    # Learnings einfügen unter der passenden Datum-Sektion
    for snippet in new_snippets:
        # Markdown-Block erstellen
        markdown_block = snippet.to_markdown_block()

        # Position zum Einfügen finden (direkt nach ## YYYY-MM-DD)
        date_section_start = content.find(date_section_pattern)
        if date_section_start != -1:
            # Finde das Ende der Zeile mit dem Datum
            line_end = content.find("\n", date_section_start)
            if line_end != -1:
                # Finde die nächste Sektion oder Ende
                next_section = content.find("\n## ", line_end + 1)

                if next_section != -1:
                    # Einfügen vor der nächsten Sektion
                    insert_pos = next_section
                else:
                    # Ans Ende des Dokuments
                    insert_pos = len(content)

                # Sicherstellen, dass genug Leerzeilen vorhanden sind
                # und einfügen direkt nach der Datum-Zeile
                if content[line_end:line_end+2] != "\n\n":
                    content = content[:line_end+1] + "\n" + content[line_end+1:]
                    insert_pos += 1

                # Füge nach der Datum-Zeile und Leerzeile ein
                # Suche die richtige Position
                actual_insert = line_end + 2  # Nach ## YYYY-MM-DD\n\n

                # Prüfe ob schon Content unter diesem Datum ist
                content[actual_insert:next_section if next_section != -1 else len(content)]

                # Füge am Ende des Tages-Abschnitts ein
                if next_section != -1:
                    content = (
                        content[:next_section] +
                        markdown_block + "\n" +
                        content[next_section:]
                    )
                else:
                    if not content.endswith("\n"):
                        content += "\n"
                    content += markdown_block + "\n"

        logger.info(f"Learning angehängt: {snippet.event_id}")

    # Speichern
    log_path.write_text(content, encoding="utf-8")
    logger.info(f"Learning-Log aktualisiert: {log_path} (+{len(new_snippets)} Einträge)")


def get_learning_log_stats(log_path: Path) -> dict:
    """
    Gibt Statistiken über das Learning-Log zurück.

    Parameters
    ----------
    log_path : Path
        Pfad zur Learning-Log-Datei

    Returns
    -------
    dict
        Statistiken mit Keys:
        - total_entries: int
        - dates: List[str]
        - latest_date: str
        - event_ids: List[str]
    """
    stats = {
        "total_entries": 0,
        "dates": [],
        "latest_date": "",
        "event_ids": [],
    }

    if not log_path.exists():
        return stats

    content = log_path.read_text(encoding="utf-8")

    # Event-IDs zählen
    event_ids = re.findall(r"### (INF-[^\n]+)", content)
    stats["event_ids"] = event_ids
    stats["total_entries"] = len(event_ids)

    # Daten extrahieren
    dates = re.findall(r"## (\d{4}-\d{2}-\d{2})", content)
    stats["dates"] = sorted(set(dates), reverse=True)

    if dates:
        stats["latest_date"] = max(dates)

    return stats
