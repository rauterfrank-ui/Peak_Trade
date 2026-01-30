# Phase 85 – Live-Track Web-Dashboard v1 (Session Explorer)

## 1. Ziel & Kontext

**Ziel von Phase 85** ist die Erweiterung des Web-Dashboards von v0 (Status-Anzeige) zu einem **Live-Track Session-Explorer** mit:

- Filter nach Mode/Status
- Klickbare Sessions für Detail-Ansicht
- Vollständige Session-Details (Config, Metrics, CLI-Args)
- Safety-First: Live-Warnung für Live-Sessions

**Bausteine der Live-Track-Pipeline:**

| Phase | Komponente | Funktion |
|-------|------------|----------|
| 80 | Strategy-to-Execution Bridge | LiveSessionRunner für Shadow/Testnet |
| 81 | Live-Session-Registry | Persistiert Session-Records als JSON |
| 82 | Live-Track Dashboard v0 | Zeigt Sessions im Web-Dashboard |
| 83 | Operator Workflow | Täglicher Ablauf mit Panel-Checks |
| 84 | Demo-Walkthrough | End-to-End-Demo-Dokumentation |
| **85** | **Session Explorer** | Filter, Detail-View, klickbare Zeilen |

---

## 2. Neue Features

### 2.1 Filter nach Mode & Status

Die Session-Liste kann jetzt gefiltert werden:

- **Mode-Filter:** shadow, testnet, paper, (live)
- **Status-Filter:** completed, failed, aborted, started (running)

Filter werden als Query-Parameter übergeben:

```
GET /?mode=shadow&status=completed
GET /api/live_sessions?mode=testnet&status=failed&limit=20
```

### 2.2 Session-Detail-Ansicht

Klick auf eine Session öffnet die Detail-Page:

```
GET /session/{session_id}
GET /api/live_sessions/{session_id}
```

**Detail-View enthält:**

- Meta-Informationen (ID, Mode, Environment, Symbol, Zeitraum, Dauer)
- Haupt-Metriken (Status, PnL, Drawdown, Orders)
- Alle Metrics als Tabelle
- Session-Config als JSON
- CLI-Aufruf (wenn vorhanden)
- Fehler-Anzeige bei failed/aborted

### 2.3 Session-Statistiken

Aggregierte Statistiken über alle Sessions:

```
GET /api/live_sessions/stats
```

**Response:**

```json
{
  "total_sessions": 42,
  "by_mode": {"shadow": 30, "testnet": 10, "paper": 2},
  "by_status": {"completed": 38, "failed": 3, "aborted": 1},
  "total_pnl": 1250.50,
  "avg_drawdown": 0.032
}
```

### 2.4 Safety-First: Live-Warnung

Sessions im Mode `live` werden besonders markiert:

- **Tabelle:** Roter Hintergrund, ⚠️-Icon
- **Detail-Page:** Warnung-Banner oben
- **Flag:** `is_live_warning: true` im API-Response

---

## 3. Architektur

### 3.1 Neue Dateien

| Datei | Beschreibung |
|-------|--------------|
| `src/webui/live_track.py` | Erweitert um `LiveSessionDetail`, Filter-/Detail-Funktionen |
| `src/webui/app.py` | Neue Endpoints für Filter, Detail, Stats |
| `templates/.../session_detail.html` | HTML-Template für Detail-Ansicht |
| `templates/.../index.html` | Erweitert um Filter-UI und klickbare Zeilen |
| `tests/test_webui_live_track.py` | Erweitert um Phase 85 Tests (54 Tests) |

### 3.2 Datenfluss

```
┌─────────────────────────────┐
│ Live-Session-Registry       │  (Phase 81)
│ reports/experiments/        │
│   live_sessions/*.json      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ live_track.py               │
│ - get_filtered_sessions()   │
│ - get_session_by_id()       │
│ - get_session_stats()       │
│ - LiveSessionDetail Model   │
└──────────────┬──────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌───────────────┐  ┌────────────────────┐
│ /api/         │  │ / (Dashboard)      │
│ live_sessions │  │ /session/{id}      │
│ (JSON API)    │  │ (HTML Detail)      │
└───────────────┘  └────────────────────┘
```

---

## 4. API-Referenz

### 4.1 GET /api/live_sessions

**Query-Parameter:**

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `limit` | int | 10 | Max. Anzahl Sessions (1-100) |
| `mode` | string | null | Filter: shadow, testnet, paper, live |
| `status` | string | null | Filter: completed, failed, aborted, started |

**Beispiel:**

```bash
curl "http://127.0.0.1:8000/api/live_sessions?mode=shadow&status=completed&limit=5"
```

### 4.2 GET /api/live_sessions/{session_id}

**Pfad-Parameter:**

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `session_id` | string | Session-ID |

**Response:** `LiveSessionDetail` (alle Felder inkl. Config, Metrics, CLI)

**Fehler:** 404 wenn Session nicht gefunden

### 4.3 GET /api/live_sessions/stats

**Response:**

```json
{
  "total_sessions": 42,
  "by_mode": {"shadow": 30, "testnet": 10},
  "by_status": {"completed": 38, "failed": 4},
  "total_pnl": 1250.50,
  "avg_drawdown": 0.032
}
```

---

## 5. Pydantic-Modelle

### 5.1 LiveSessionSummary (erweitert)

```python
class LiveSessionSummary(BaseModel):
    session_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    mode: str
    environment: str
    status: Literal["started", "completed", "failed", "aborted"]
    realized_pnl: Optional[float]
    max_drawdown: Optional[float]
    num_orders: Optional[int]
    report_path: Optional[str]
    notes: Optional[str]
    # Phase 85:
    duration_seconds: Optional[int]
    is_live_warning: bool
```

### 5.2 LiveSessionDetail (neu)

```python
class LiveSessionDetail(BaseModel):
    # Alle Felder von Summary, plus:
    run_id: Optional[str]
    run_type: str
    env_name: str
    symbol: str
    config: dict
    metrics: dict
    cli_args: List[str]
    created_at: Optional[datetime]
```

---

## 6. UI-Komponenten

### 6.1 Filter-Leiste

- Mode-Buttons: Alle | Shadow | Testnet | Paper
- Status-Buttons: Alle | Completed | Failed | Running
- Reset-Link bei aktivem Filter

### 6.2 Sessions-Tabelle

| Spalte | Beschreibung |
|--------|--------------|
| Session | ID (klickbar, Link zur Detail-Page) |
| Mode | Badge (purple=shadow, amber=testnet, sky=paper, rose=live) |
| Status | ✓ OK, ✕ FAIL, ⊘ ABORT, ● RUN |
| Started | Datum/Uhrzeit |
| Duration | Berechnete Dauer (z.B. "1h 30m") |
| PnL | Grün/Rot je nach Vorzeichen |
| Max DD | Prozent |
| Orders | Anzahl |

### 6.3 Detail-Page

- Breadcrumb mit Zurück-Link
- Live-Warnung-Banner (wenn mode=live)
- Meta-Kacheln (Status, PnL, Drawdown, Orders)
- Meta-Informationen (Environment, Symbol, Zeitraum, Dauer)
- Fehler-Anzeige (bei failed/aborted)
- Metrics-Tabelle
- Config als JSON
- CLI-Aufruf

---

## 7. Tests

**Test-Suite:** `tests/test_webui_live_track.py`

**Neue Test-Klassen (Phase 85):**

- `TestLiveSessionDetailModel` (3 Tests)
- `TestGetFilteredSessions` (4 Tests)
- `TestGetSessionById` (4 Tests)
- `TestGetSessionStats` (3 Tests)
- `TestPhase85ApiEndpoints` (6 Tests)
- `TestDashboardWithFilters` (4 Tests)
- `TestComputeDurationSeconds` (4 Tests)

**Gesamt:** 54 Tests (alle grün)

```bash
python3 -m pytest tests/test_webui_live_track.py -v
```

---

## 8. Nutzung

### 8.1 Dashboard starten

```bash
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000
```

### 8.2 URLs

| URL | Beschreibung |
|-----|--------------|
| http://127.0.0.1:8000/ | Dashboard mit Session Explorer |
| http://127.0.0.1:8000/?mode=shadow | Gefiltert nach Shadow |
| http://127.0.0.1:8000/session/{id} | Session Detail-Page |
| http://127.0.0.1:8000/api/live_sessions | JSON API |
| http://127.0.0.1:8000/api/live_sessions/stats | Statistiken |
| http://127.0.0.1:8000/docs | OpenAPI/Swagger UI |

### 8.3 Golden Path (Phase 84 Demo)

1. Shadow-Session starten (Phase 80)
2. Dashboard öffnen → Session erscheint in der Tabelle
3. Auf Session klicken → Detail-Ansicht öffnet sich
4. Config, Metrics, CLI-Args einsehen

---

## 9. Safety-First

### 9.1 Live-Mode Handling

- Live-Sessions werden mit ⚠️-Icon und rotem Hintergrund markiert
- Detail-Page zeigt Warnung-Banner
- Keine "Start"-Buttons für Live-Mode
- API-Response enthält `is_live_warning: true`

### 9.2 Read-Only

Das gesamte Dashboard ist **read-only**:

- Keine Buttons zum Starten/Stoppen von Sessions
- Keine Config-Änderungen
- Nur Anzeige und Navigation

---

## 10. Nächste Schritte

- **Auto-Refresh:** JS-basiertes Polling für Live-Updates
- **Charts:** PnL-Verlauf, Drawdown-Visualisierung
- **Export:** Session-Reports als PDF/CSV
- **Notifications:** Browser-Notifications bei Session-Ende
- **Dark-Theme:** Bereits vorhanden, ggf. Light-Mode Toggle
