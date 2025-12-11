# Phase 83 – Live-Track Operator Workflow

## 1. Ziel & Kontext

**Ziel von Phase 83** ist die Definition eines strukturierten Operator-Workflows für die tägliche Arbeit mit dem Live-Track Panel (Phase 82). Dieses Dokument beschreibt, wie Operatoren die vorhandenen Tools kombinieren, um Shadow- und Testnet-Sessions zu überwachen, Probleme zu erkennen und Governance-Anforderungen zu erfüllen.

**Bausteine:**

| Phase | Komponente | Funktion |
|-------|------------|----------|
| 80 | Strategy-to-Execution Bridge | Führt Sessions aus (Shadow/Testnet/Live) |
| 81 | Live-Session-Registry | Persistiert Session-Records als JSON |
| 82 | Live-Track Dashboard Panel | Visualisiert Sessions im Web-Dashboard |
| 83 | **Dieser Workflow** | Verbindet alles zu einem Operator-Prozess |

---

## 2. Komponenten-Übersicht

### 2.1 Live-Session-Registry (Phase 81)

Die Registry speichert jeden Session-Run als JSON:

```
reports/experiments/live_sessions/
├── 20251208T025243_live_session_shadow_session_001.json
├── 20251208T103012_live_session_testnet_session_002.json
└── ...
```

**Wichtige Felder im LiveSessionRecord:**

| Feld | Beschreibung |
|------|--------------|
| `session_id` | Eindeutige Session-ID |
| `mode` | shadow, testnet, paper, live |
| `status` | started, completed, failed, aborted |
| `env_name` | Exchange-Environment (z.B. kraken_futures_testnet) |
| `symbol` | Handelspaar (z.B. BTC/USDT) |
| `metrics` | PnL, Drawdown, Anzahl Orders |
| `error` | Fehlermeldung (falls vorhanden) |

### 2.2 Live-Track Dashboard Panel (Phase 82)

Das Web-Dashboard zeigt:

1. **Snapshot-Kachel:** Letzte abgeschlossene Session mit Status, PnL, Drawdown
2. **Sessions-Tabelle:** Übersicht der letzten N Sessions

**Zugriff:**

```bash
# Dashboard starten
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000

# Browser öffnen
open http://127.0.0.1:8000/
```

### 2.3 CLI-Tools

| Tool | Zweck |
|------|-------|
| `scripts/run_execution_session.py` | Session starten (Shadow/Testnet) |
| `scripts/report_live_sessions.py` | Registry-Reports generieren |
| `scripts/live_operator_status.py` | Operator-Status-Übersicht |

---

## 3. Typischer Tagesablauf – Shadow/Testnet-Tag

### 3.1 Pre-Session-Check (Morgens)

**Ziel:** Sicherstellen, dass das System bereit ist und keine offenen Probleme vorliegen.

```bash
# 1. Dashboard öffnen
uvicorn src.webui.app:app --host 127.0.0.1 --port 8000 &
open http://127.0.0.1:8000/

# 2. Letzte Sessions prüfen
curl http://127.0.0.1:8000/api/live_sessions?limit=5 | jq .

# 3. Registry-Summary generieren
python scripts/report_live_sessions.py --summary-only --stdout
```

**Checkliste Pre-Session:**

- [ ] Dashboard erreichbar unter http://127.0.0.1:8000/
- [ ] Live-Track Panel zeigt Sessions (oder "Keine Sessions" bei Erststart)
- [ ] Keine `failed`-Sessions in den letzten 24h (oder dokumentiert)
- [ ] Keine unerwarteten `aborted`-Sessions
- [ ] Config-Files aktuell (Strategy, Risk-Limits)

### 3.2 Session starten

**Shadow-Session:**

```bash
python scripts/run_execution_session.py \
    --mode shadow \
    --env kraken_futures_testnet \
    --symbol BTC/USDT \
    --strategy ma_crossover \
    --duration 1h
```

**Testnet-Session:**

```bash
python scripts/run_execution_session.py \
    --mode testnet \
    --env kraken_futures_testnet \
    --symbol BTC/USDT \
    --strategy ma_crossover \
    --duration 4h
```

### 3.3 Während der Session (Monitoring)

**Dashboard-Checks alle 15-30 Minuten:**

1. **Browser-Refresh:** http://127.0.0.1:8000/
2. **Snapshot-Kachel prüfen:**
   - Status sollte `started` oder `completed` sein
   - Bei `failed`: Sofort Fehler untersuchen
3. **PnL-Trend beobachten:**
   - Grün = positiv
   - Rot = negativ (bei größeren Verlusten: Risk-Limits prüfen)

**API-Monitoring (Terminal):**

```bash
# Aktuelle Session prüfen
curl http://127.0.0.1:8000/api/live_sessions?limit=1 | jq '.[0] | {session_id, status, mode, realized_pnl, max_drawdown}'

# Health-Check
curl http://127.0.0.1:8000/api/health
```

### 3.4 Post-Session-Check (Abends)

**Ziel:** Session-Ergebnis dokumentieren und für nächsten Tag vorbereiten.

```bash
# 1. Session-Report generieren
python scripts/report_live_sessions.py \
    --limit 1 \
    --output-format markdown \
    --output-dir reports/daily/

# 2. Summary über den Tag
python scripts/report_live_sessions.py \
    --run-type live_session_shadow \
    --summary-only \
    --stdout
```

**Checkliste Post-Session:**

- [ ] Session-Status ist `completed` (nicht `failed` oder `aborted`)
- [ ] Max Drawdown innerhalb der Limits (typisch: < 5%)
- [ ] Realized PnL dokumentiert
- [ ] Bei Auffälligkeiten: Notiz im Incident-Log

---

## 4. Konkrete Checks im Live-Track Panel

### 4.1 Snapshot-Kachel interpretieren

| Element | Bedeutung | Action bei Problem |
|---------|-----------|-------------------|
| **Mode-Badge** | Session-Typ (shadow/testnet/paper/live) | - |
| **Status: Completed** (grün) | Session erfolgreich beendet | ✓ OK |
| **Status: Failed** (rot) | Session mit Fehler beendet | → Fehler in `notes` prüfen |
| **Status: Aborted** (amber) | Session manuell abgebrochen | → Grund dokumentieren |
| **Status: Running** (blau) | Session läuft noch | → Weiter beobachten |
| **Realized PnL** (grün) | Positiver PnL | ✓ OK |
| **Realized PnL** (rot) | Negativer PnL | → Bei > -2% Risk-Review |
| **Max Drawdown** | Maximaler Verlust während Session | → Bei > 5% Investigation |
| **Notes** | Fehlermeldung | → Sofort untersuchen |

### 4.2 Sessions-Tabelle interpretieren

Die Tabelle zeigt die letzten N Sessions mit:

| Spalte | Prüfung |
|--------|---------|
| Session | ID zur Identifikation |
| Mode | Sollte dem erwarteten Modus entsprechen |
| Status | Keine unerwarteten `failed`/`aborted` |
| Started/Ended | Zeitraum plausibel? |
| PnL | Trend über mehrere Sessions beobachten |
| Max DD | Sollte konsistent unter Limit sein |
| Orders | Plausible Anzahl für Strategie |

**Warnsignale in der Tabelle:**

- Mehrere `failed`-Sessions in Folge → Systemisches Problem
- Stark schwankende PnL-Werte → Strategie-Instabilität
- Drawdown > 10% → Sofortiger Risk-Review
- Keine Orders bei langer Session → Strategie-Bug oder Markt-Anomalie

### 4.3 Leerer Zustand

Falls keine Sessions angezeigt werden:

```
Keine Live-Sessions gefunden.
Sessions werden nach dem ersten Shadow-/Testnet-Run hier angezeigt.
```

**Action:** Erste Shadow-Session starten, um Registry zu initialisieren.

---

## 5. Fehlerbehandlung

### 5.1 Session-Status: Failed

1. **Fehlerdetails abrufen:**
   ```bash
   curl http://127.0.0.1:8000/api/live_sessions?limit=1 | jq '.[0].notes'
   ```

2. **Registry-File direkt prüfen:**
   ```bash
   ls -lt reports/experiments/live_sessions/ | head -5
   cat reports/experiments/live_sessions/<latest>.json | jq .error
   ```

3. **Typische Fehlerursachen:**
   - `ConnectionError`: Exchange-API nicht erreichbar
   - `AuthenticationError`: API-Keys ungültig
   - `InsufficientFunds`: Testnet-Balance aufbrauchen
   - `RateLimitExceeded`: Zu viele API-Requests

### 5.2 Session-Status: Aborted

1. **Grund dokumentieren** (wurde manuell mit Ctrl+C beendet)
2. **Bei unbeabsichtigtem Abbruch:**
   - System-Logs prüfen
   - Netzwerk-Stabilität prüfen
   - Session neu starten

### 5.3 Dashboard nicht erreichbar

```bash
# Process prüfen
pgrep -f uvicorn

# Neu starten
pkill -f uvicorn
uvicorn src.webui.app:app --host 127.0.0.1 --port 8000 &

# Health-Check
curl http://127.0.0.1:8000/api/health
```

---

## 6. Governance-Anforderungen

### 6.1 Dokumentationspflicht

Jede Session wird automatisch in der Registry dokumentiert. Zusätzlich empfohlen:

- **Täglicher Report:** `scripts/report_live_sessions.py --summary-only`
- **Wöchentlicher Review:** Alle Sessions der Woche exportieren
- **Incident-Log:** Alle `failed`/`aborted` Sessions dokumentieren

### 6.2 Aufbewahrung

- Registry-Files: Mindestens 90 Tage
- Daily Reports: Mindestens 30 Tage
- Incident-Logs: Permanent

### 6.3 Eskalationspfad

| Ereignis | Action |
|----------|--------|
| 1x Failed | Untersuchen, dokumentieren |
| 2x Failed in Folge | Pause, Root-Cause-Analyse |
| Drawdown > 5% | Risk-Review, ggf. Strategie anpassen |
| Drawdown > 10% | Sofortige Pause, Escalation |

---

## 7. Quick-Reference

### 7.1 Wichtige URLs

| URL | Beschreibung |
|-----|--------------|
| http://127.0.0.1:8000/ | Dashboard mit Live-Track Panel |
| http://127.0.0.1:8000/api/live_sessions | JSON API |
| http://127.0.0.1:8000/api/health | Health-Check |
| http://127.0.0.1:8000/docs | OpenAPI/Swagger UI |

### 7.2 Wichtige CLI-Befehle

```bash
# Dashboard starten
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000

# Letzte Sessions (JSON)
curl http://127.0.0.1:8000/api/live_sessions?limit=5 | jq .

# Summary-Report
python scripts/report_live_sessions.py --summary-only --stdout

# Vollständiger Report
python scripts/report_live_sessions.py --output-format markdown

# Shadow-Session starten
python scripts/run_execution_session.py --mode shadow --env kraken_futures_testnet --symbol BTC/USDT
```

### 7.3 Tägliche Checkliste (Kurzform)

- [ ] Pre-Session: Dashboard erreichbar, keine offenen Probleme
- [ ] Session starten: Mode und Config korrekt
- [ ] Monitoring: Alle 15-30 Min Dashboard prüfen
- [ ] Post-Session: Status `completed`, Metrics dokumentiert

---

## 8. Nächste Schritte

- **Auto-Refresh:** Automatisches Polling im Dashboard (JS-basiert)
- **Alerts:** Benachrichtigungen bei `failed`-Sessions
- **Session-Details:** Drill-Down-Ansicht für einzelne Sessions
- **Historische Trends:** Charts für PnL und Drawdown über Zeit
