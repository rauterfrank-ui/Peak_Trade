# Phase 82 – Live-Track Panel im Web-Dashboard

## 1. Ziel & Kontext

**Ziel von Phase 82** ist die Erweiterung des Web-Dashboards (v0) um ein **Live-Track Panel**, das die letzten Live-Sessions (Shadow/Testnet/Paper/Live) aus der Phase-81 Registry anzeigt.

Das Panel ist **read-only** und nutzt ausschließlich die bestehende Live-Session-Registry (Phase 81) als Datenquelle.

---

## 2. Architektur-Überblick

### 2.1 Neue Komponenten

| Datei | Beschreibung |
|-------|--------------|
| `src/webui/live_track.py` | Service-Layer mit `LiveSessionSummary` Model und `get_recent_live_sessions()` |
| `src/webui/app.py` | Erweiterter FastAPI-App mit `/api/live_sessions` Endpoint |
| `templates/peak_trade_dashboard/index.html` | Live-Track Panel UI (Snapshot-Kachel + Sessions-Tabelle) |
| `tests/test_webui_live_track.py` | 26 Unit-/Integration-Tests |

### 2.2 Datenfluss

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
│ - get_recent_live_sessions()│
│ - LiveSessionSummary Model  │
└──────────────┬──────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌───────────────┐  ┌────────────────────┐
│ /api/         │  │ / (HTML Dashboard) │
│ live_sessions │  │ Live-Track Panel   │
│ (JSON API)    │  │ (Server-Rendered)  │
└───────────────┘  └────────────────────┘
```

---

## 3. LiveSessionSummary – API-Response-Modell

```python
class LiveSessionSummary(BaseModel):
    session_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    mode: str  # shadow, testnet, paper, live
    environment: str  # env_name + symbol
    status: Literal["started", "completed", "failed", "aborted"]
    realized_pnl: Optional[float]
    max_drawdown: Optional[float]
    num_orders: Optional[int]
    report_path: Optional[str]
    notes: Optional[str]  # Fehler-Info falls vorhanden
```

Felder werden aus `LiveSessionRecord` (Phase 81) gemappt:
- `environment` = `env_name + " / " + symbol`
- `notes` = `error` (Fehlermeldung)
- `num_orders` = `metrics.num_orders` oder `metrics.num_trades`

---

## 4. API-Endpoint

### GET /api/live_sessions

```
GET /api/live_sessions?limit=10
```

**Query-Parameter:**
| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `limit` | int | 10 | Max. Anzahl Sessions (1-100) |

**Response:**
```json
[
  {
    "session_id": "session_20251208_shadow_abc123",
    "started_at": "2024-12-08T12:00:00",
    "ended_at": "2024-12-08T13:00:00",
    "mode": "shadow",
    "environment": "kraken_futures_testnet / BTC/USDT",
    "status": "completed",
    "realized_pnl": 150.0,
    "max_drawdown": 0.05,
    "num_orders": 10,
    "report_path": null,
    "notes": null
  }
]
```

**Fehlerbehandlung:**
- Leere Liste falls keine Sessions vorhanden
- Leere Liste falls Registry-Verzeichnis nicht existiert
- Korrupte JSON-Files werden übersprungen

---

## 5. Dashboard UI

### 5.1 Snapshot-Kachel (Letzte Session)

Zeigt hervorgehoben die **letzte abgeschlossene Session**:

- **Mode-Badge:** shadow (purple), testnet (amber), paper (sky), live (rose)
- **Status:** Completed (grün), Failed (rot), Aborted (amber), Running (blau)
- **Zeitspanne:** Start → Ende (oder "laufend")
- **Realized PnL:** Grün bei positiv, rot bei negativ
- **Max Drawdown:** Prozent-Anzeige
- **Environment:** Exchange + Symbol
- **Fehler-Hinweis:** Falls vorhanden (notes)

### 5.2 Sessions-Tabelle

Spalten:
| Session | Mode | Status | Started | Ended | PnL | Max DD | Orders |
|---------|------|--------|---------|-------|-----|--------|--------|

- Session-ID wird bei >25 Zeichen abgekürzt
- PnL farbcodiert (grün/rot)
- Status-Badges: OK, FAIL, ABORT, RUN

### 5.3 Leerer Zustand

Falls keine Sessions vorhanden:
```
Keine Live-Sessions gefunden.
Sessions werden nach dem ersten Shadow-/Testnet-Run hier angezeigt.
```

---

## 6. Tests

### 6.1 Test-Suite

`tests/test_webui_live_track.py` enthält 26 Tests:

**Model-Tests:**
- Minimales/vollständiges Summary erstellen
- JSON-Serialisierung
- Status-Wert-Validierung

**Service-Tests:**
- Leere Registry
- Sessions laden
- Limit-Parameter
- Sortierung (neueste zuerst)
- Optionale Felder
- Korrupte Dateien überspringen
- Environment-Zusammenbau

**API-Tests:**
- 200-Response
- Limit-Validierung (min/max)
- Health-Endpoint

**Dashboard-Tests:**
- HTML-Rendering
- Live-Track-Sektion vorhanden
- Leerer Zustand

**Integration:**
- Zusammenspiel mit echtem Registry-System

### 6.2 Tests ausführen

```bash
# Nur Live-Track Tests
pytest tests/test_webui_live_track.py -v

# Mit Registry-Tests
pytest tests/test_webui_live_track.py tests/test_live_session_registry.py -v
```

---

## 7. Nutzung

### 7.1 Dashboard starten

```bash
# Mit Reload (Entwicklung)
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000

# Produktion
uvicorn src.webui.app:app --host 0.0.0.0 --port 8000
```

### 7.2 Browser öffnen

```
http://127.0.0.1:8000/          # Dashboard mit Live-Track Panel
http://127.0.0.1:8000/docs      # OpenAPI/Swagger UI
http://127.0.0.1:8000/api/live_sessions?limit=5  # JSON API
```

### 7.3 Programmatische Nutzung

```python
from src.webui.live_track import get_recent_live_sessions, LiveSessionSummary

# Letzte 10 Sessions laden
sessions = get_recent_live_sessions(limit=10)

for s in sessions:
    print(f"{s.session_id}: {s.status} - PnL: {s.realized_pnl}")
```

---

## 8. Manuelle Checks

1. **Dashboard mit Sessions:**
   - Shadow-/Testnet-Session ausführen (erzeugt Registry-Einträge)
   - Dashboard öffnen → Live-Track Panel zeigt Session

2. **Dashboard ohne Sessions:**
   - Registry-Verzeichnis leeren/löschen
   - Dashboard zeigt "Keine Live-Sessions gefunden"

3. **API testen:**
   ```bash
   curl http://127.0.0.1:8000/api/live_sessions
   curl http://127.0.0.1:8000/api/live_sessions?limit=3
   curl http://127.0.0.1:8000/api/health
   ```

---

## 9. Nächste Schritte

- **Auto-Refresh:** JS-basiertes Polling für Live-Updates
- **Session-Details:** Click-to-Expand für einzelne Sessions
- **Filterung:** Nach Mode, Status, Zeitraum filtern
- **Charts:** PnL-Verlauf, Drawdown-Visualisierung
- **Notifications:** Browser-Notifications bei Session-Ende
