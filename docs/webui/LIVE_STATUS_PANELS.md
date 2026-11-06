# Live Status Panels – Custom Panel Guide

## Überblick

Das Live Status Snapshot System ermöglicht es, benutzerdefinierte Status-Panels zu erstellen, die sowohl im Web-Dashboard als auch in generierten Reports angezeigt werden.

**Service-Layer-Architektur (Phase Service-Layer Integration)**:
- **Single Source of Truth**: Panel-Provider und API-Endpunkte nutzen gemeinsame Service-Funktionen
- **Konsistenz**: Gleiche Daten in `/api/live/status/snapshot.json` und `/api/live_sessions/stats`
- **Read-Only**: Alle Panel-Provider sind rein lesend, keine Side-Effects

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    WebUI API Endpoints                       │
│  /api/live/alerts/stats  /api/live_sessions/stats           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ uses
                 ▼
┌─────────────────────────────────────────────────────────────┐
│            Service Layer (Single Source of Truth)            │
│         src/webui/services/live_panel_data.py                │
│  • get_alerts_stats()                                        │
│  • get_live_sessions_stats()                                 │
│  • get_telemetry_summary()                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ uses
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                Panel Providers (Discovery)                   │
│             src/live/status_providers.py                     │
│  • get_live_panel_providers()                                │
│  • _panel_alerts()                                           │
│  • _panel_live_sessions()                                    │
│  • _panel_telemetry()                                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ discovered by
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Snapshot Builder (Auto-Discovery)               │
│       src/reporting/live_status_snapshot_builder.py          │
│  • build_live_status_snapshot_auto()                         │
└─────────────────────────────────────────────────────────────┘
```

## Wie Auto-Discovery funktioniert

1. **Snapshot Builder** ruft `get_auto_panel_providers()` auf
2. Diese Funktion versucht, `src.live.status_providers` zu importieren
3. Falls erfolgreich, ruft sie `get_live_panel_providers()` auf
4. Diese liefert ein Dict `{panel_id: provider_callable}`
5. Snapshot Builder ruft jeden Provider auf und sammelt die Results

**Defensive Imports**: Wenn `status_providers.py` nicht vorhanden ist, läuft das System weiter (nur mit dem System-Panel).

## Neue Custom Panels hinzufügen

### Schritt 1: Service-Funktion erstellen (empfohlen)

Füge eine neue Funktion in `src/webui/services/live_panel_data.py` hinzu:

```python
def get_my_custom_stats() -> Dict[str, Any]:
    """
    Get custom statistics.

    Returns:
        Dict with stats data
    """
    try:
        from src.my_module import get_stats

        stats = get_stats()
        return {
            "metric_1": stats.get("metric_1", 0),
            "metric_2": stats.get("metric_2", 0),
        }
    except ImportError:
        return {
            "metric_1": 0,
            "metric_2": 0,
            "_fallback": True,
            "message": "Custom stats not available",
        }
```

**Export** nicht vergessen in `__init__.py`:

```python
from .live_panel_data import (
    get_alerts_stats,
    get_live_sessions_stats,
    get_telemetry_summary,
    get_my_custom_stats,  # NEU
)
```

### Schritt 2: Panel-Provider registrieren

Bearbeite `src/live/status_providers.py`:

```python
def get_live_panel_providers() -> Dict[str, PanelProvider]:
    return {
        "alerts": _panel_alerts,
        "live_sessions": _panel_live_sessions,
        "telemetry": _panel_telemetry,
        "my_custom": _panel_my_custom,  # NEU
        # ...
    }

def _panel_my_custom(*args: Any, **kwargs: Any) -> Any:
    """
    Provide custom panel data.
    """
    try:
        from src.webui.services.live_panel_data import get_my_custom_stats

        stats = get_my_custom_stats()

        is_fallback = stats.get("_fallback", False)
        status = "unknown" if is_fallback else "ok"

        return {
            "id": "my_custom",
            "title": "My Custom Panel",
            "status": status,
            "details": stats,
        }
    except ImportError:
        pass

    return {
        "id": "my_custom",
        "title": "My Custom Panel",
        "status": "unknown",
        "details": {"message": "Not available"},
    }
```

### Schritt 3: Optional - API-Endpoint hinzufügen

Falls du einen dedizierten API-Endpoint möchtest, füge ihn in `src/webui/app.py` hinzu:

```python
@app.get("/api/my_custom/stats")
async def api_my_custom_stats() -> Dict[str, Any]:
    """Get my custom stats."""
    from src.webui.services.live_panel_data import get_my_custom_stats
    return get_my_custom_stats()
```

## Panel-Response-Format

Jeder Panel-Provider **muss** ein Dict mit diesen Feldern zurückgeben:

```python
{
    "id": "panel_id",          # REQUIRED: Eindeutige Panel-ID (stable!)
    "title": "Panel Title",    # REQUIRED: Anzeige-Titel
    "status": "ok",            # REQUIRED: ok|active|warning|error|unknown
    "details": {...},          # REQUIRED: Beliebige Detail-Daten (dict)
    "note": "...",             # OPTIONAL: Zusätzliche Hinweise
}
```

**Status-Werte**:
- `ok`: Alles gut
- `active`: System aktiv (z.B. laufende Sessions)
- `warning`: Warnung (z.B. kritische Alerts)
- `error`: Fehler
- `unknown`: Keine Daten verfügbar

## Best Practices

### ✅ DO:
- **Read-Only**: Panel-Provider niemals schreiben lassen
- **Defensive**: Immer try/except und Fallback-Dicts
- **Service-Layer nutzen**: Für wiederverwendbare Logik
- **Stabile IDs**: Panel-IDs nie ändern (UI-Abhängigkeiten)
- **Schnell**: Panels dürfen keine langen Operationen durchführen

### ❌ DON'T:
- Keine Netzwerk-Calls
- Keine Datenbank-Schreiboperationen
- Keine langen Berechnungen (>100ms)
- Keine Exceptions werfen (immer graceful fallback)
- Keine Abhängigkeit von Live-Sessions (muss auch offline laufen)

## Testing

Teste deine Panels mit `python3 -m pytest`:

```python
def test_my_custom_panel_stable():
    """Test custom panel never crashes."""
    from src.live.status_providers import _panel_my_custom

    result = _panel_my_custom()

    assert isinstance(result, dict)
    assert result["id"] == "my_custom"
    assert "status" in result
    assert result["status"] in ("ok", "warning", "error", "unknown")
```

Siehe `tests/test_live_status_snapshot_panels.py` für weitere Beispiele.

## Operator How-To

### Snapshot abfragen

```bash
# Server starten (falls nicht läuft)
python3 -m uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000

# Snapshot JSON abrufen
curl http://localhost:8000/api/live/status/snapshot.json | jq '.panels'

# Oder im Browser
open http://localhost:8000/api/live/status/snapshot.json
```

### Alerts Stats prüfen

```bash
curl http://localhost:8000/api/live/alerts/stats | jq
```

### Live Sessions Stats prüfen

```bash
curl http://localhost:8000/api/live_sessions/stats | jq
```

### Shadow Session starten und Panels beobachten

```bash
# Terminal 1: Shadow Session starten
python3 scripts/run_shadow_paper_session.py

# Terminal 2: Stats beobachten
watch -n 5 'curl -s http://localhost:8000/api/live_sessions/stats | jq'
```

## Troubleshooting

### Panel zeigt "unknown" / "fallback"

**Ursache**: Service-Layer oder Datenspeicher nicht verfügbar.

**Lösung**:
1. Prüfe, ob die benötigten Module importiert werden können
2. Prüfe Logs: `grep "not available" logs/*.log`
3. Prüfe, ob Sessions/Alerts tatsächlich existieren

### Panel-Daten sind veraltet

**Ursache**: Snapshot wird gecacht oder Datenspeicher nicht aktualisiert.

**Lösung**:
1. Service neu starten: `python3 -m uvicorn src.webui.app:app --reload`
2. Prüfe Registry-Updates: `ls -lt live_runs/sessions/`
3. Prüfe Alert-Storage: `ls -lt live_runs/alerts/`

### Tests schlagen fehl

**Ursache**: Mock-Daten passen nicht zur erwarteten Struktur.

**Lösung**:
1. Prüfe `tests/test_live_status_snapshot_panels.py`
2. Aktualisiere Mock-Fixtures auf aktuelle Struktur
3. Nutze `monkeypatch` für defensive Tests

## Siehe auch

- [Service Layer API](../../src/webui/services/live_panel_data.py)
- [Panel Providers](../../src/live/status_providers.py)
- [Snapshot Builder](../../src/reporting/live_status_snapshot_builder.py)
- [Tests](../../tests/test_live_status_snapshot_panels.py)
