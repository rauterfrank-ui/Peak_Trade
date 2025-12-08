# Phase 81 – Live-Session-Registry (Shadow / Testnet / Live)

## 1. Ziel & Kontext

**Ziel von Phase 81** ist es, Live-ähnliche Sessions (Shadow, Testnet, später Live) genauso sauber zu erfassen wie Research-Experimente:

* Jede Session (z.B. `live_session_shadow`, `live_session_testnet`) wird als eigener **Record** persistiert.
* Alle relevanten Infos (Config, Metrics, CLI-Args, Status, Fehler) landen **append-only** in einer Registry.
* Auf dieser Basis können später Reports, Dashboards und Governance-Checks aufgebaut werden.

Die Phase orientiert sich explizit am bestehenden Experiment-System:

* `SweepResultRow` → `LiveSessionRecord`
* Experiment-Registry → Live-Session-Registry
* `reports/experiments/` → `reports/experiments/live_sessions/`

---

## 2. Architektur-Überblick

### 2.1 Kern-Komponenten

* `src/experiments/live_session_registry.py`

  * `LiveSessionRecord` – Dataclass für einen Session-Run (analog zu `SweepResultRow`)
  * `register_live_session_run()` – Persistierung einer Session als JSON
  * `list_session_records()` – Query-Funktion über gespeicherte Sessions
  * `get_session_summary()` – einfache Aggregations-Summary
  * `render_session_markdown()` / `render_sessions_markdown()` – Markdown-Reports
  * `render_session_html()` / `render_sessions_html()` – HTML-Reports
  * `DEFAULT_LIVE_SESSION_DIR` – Basis-Pfad: `reports/experiments/live_sessions`

* `scripts/run_execution_session.py`

  * Orchestriert eine Execution-Session (Shadow / Testnet / später Live).
  * Wrappt die Session in einen `try/except/finally`-Block.
  * Erzeugt am Ende einen `LiveSessionRecord` und ruft `register_live_session_run()` auf.
  * Registry-Fehler werden **nur geloggt**, brechen die Session aber nicht.

* `tests/test_live_session_registry.py`

  * Testet Roundtrip, Persistierung, Queries, Summary und Renderer.
  * Enthält auch ein Safety-/Integration-Szenario.

### 2.2 Speicherort & Dateiformat

* Basis-Verzeichnis:

  * `reports/experiments/live_sessions/`
* Pro Session ein eigenes JSON-File:

  * `YYYYMMDDTHHMMSS_<run_type>_<session_id>.json`
  * Beispiel:

    * `20251208T025243_live_session_shadow_smoke_test_20251208_01.json`

---

## 3. LiveSessionRecord – Struktur & Semantik

```python
@dataclass
class LiveSessionRecord:
    session_id: str
    run_id: Optional[str]
    run_type: str          # z.B. "live_session_shadow", "live_session_testnet"
    mode: str              # z.B. "shadow", "testnet", "live", "paper"
    env_name: str          # z.B. "kraken_futures_testnet"
    symbol: str            # z.B. "BTC/USDT"

    status: str            # "started", "completed", "failed", "aborted"

    started_at: datetime
    finished_at: Optional[datetime] = None

    config: Mapping[str, Any] = field(default_factory=dict)
    metrics: Mapping[str, float] = field(default_factory=dict)
    cli_args: List[str] = field(default_factory=list)
    error: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
```

**Wichtige Felder:**

* **Identität & Typ:**

  * `session_id`: interne Session-ID (z.B. mit Timestamp/UUID)
  * `run_id`: optionaler Link zu einem Experiment/Run
  * `run_type`: semantischer Typ der Session:

    * `live_session_shadow`
    * `live_session_testnet`
    * (erweiterbar, z.B. `live_session_live`)
  * `mode`: generischer Mode (`"shadow"`, `"testnet"`, `"live"`, `"paper"`)

* **Lifecycle:**

  * `status`: `"started" | "completed" | "failed" | "aborted"`
  * `started_at` / `finished_at`: `datetime`
  * `created_at`: Zeitpunkt der Registry-Erstellung (UTC)

* **Inhalt:**

  * `config`: Konfiguration der Session (Strategie, Timeframe, Risk-Profile, Pfade, etc.)
  * `metrics`: Ergebnis-Kennzahlen (`realized_pnl`, `unrealized_pnl`, `max_drawdown`, `num_orders`, `num_trades`, …)
  * `cli_args`: CLI-Aufruf als Liste (z.B. `sys.argv`)
  * `error`: Kurzbeschreibung bei Fehlern/Abbruch

**Serialisierung:**

* `to_dict()` / `from_dict()`:

  * Datumswerte → ISO8601-Strings
  * `config`, `metrics`, `cli_args` → JSON-kompatible Strukturen

---

## 4. Registry-Funktionen

### 4.1 register_live_session_run()

```python
path = register_live_session_run(record)
```

* Speichert einen `LiveSessionRecord` als JSON.
* Verwendet einen Dateinamen mit Timestamp + `run_type` + `session_id`.
* Rückgabewert: `Path` zur erzeugten Datei.

**Wichtig:**
Diese Funktion **darf Exceptions werfen** (z.B. IO-Fehler).
Der Aufrufer (Execution-Session) fängt diese ab und loggt nur – siehe Safety-Design.

---

### 4.2 list_session_records()

```python
records = list_session_records(
    base_dir=None,           # Default: DEFAULT_LIVE_SESSION_DIR
    run_type=None,           # Filter z.B. "live_session_shadow"
    status=None,             # Filter z.B. "completed"
    limit=None,              # Limit, neueste zuerst
)
```

* Lädt alle passenden JSON-Files aus `reports/experiments/live_sessions/`.
* Filter:

  * `run_type`
  * `status`
  * `limit` (neueste zuerst)
* Beschädigte/inkonsistente Dateien werden still übersprungen.

---

### 4.3 get_session_summary()

```python
summary = get_session_summary(
    base_dir=None,
    run_type=None,           # optionaler Filter
)
```

* Aggregiert einfache Kennzahlen über alle passenden Sessions:

  * `num_sessions`
  * `by_status` (Counter pro Status)
  * `total_realized_pnl`
  * `avg_max_drawdown`
  * `first_started_at` / `last_started_at`

* Erwartet (optional) folgende Metrics-Keys:

  * `realized_pnl`
  * `max_drawdown`

---

## 5. Reports – Markdown & HTML

### 5.1 Einzel-Session (Markdown)

```python
md = render_session_markdown(record)
```

* Enthält:

  * Meta-Infos (Run-Type, Mode, Status, Symbol, Env, Start/Ende)
  * Fehlerblock (falls `error` gesetzt)
  * `Config` als JSON-Block
  * `Metrics` als JSON-Block
  * `CLI-Aufruf` als `bash`-Block (falls `cli_args` vorhanden)

Typisches Layout:

```markdown
# Live-Session session_001

**Run-Type:** `live_session_shadow`
**Mode:** `shadow`
**Status:** `completed`
**Symbol:** `BTC/USDT`
**Environment:** `kraken_futures_testnet`
**Started:** `...`
**Finished:** `...`

## Config

```json
{ ... }
```

## Metrics

```json
{ ... }
```

## CLI-Aufruf

```bash
python scripts/run_execution_session.py ...
```
```

### 5.2 Mehrere Sessions (Markdown/HTML)

- `render_sessions_markdown(records)`:
  - Erzeugt einen Sammel-Report mit einer Section pro Session.
- `render_session_html(record)` / `render_sessions_html(records)`:
  - Einfache HTML-Variante für Web-/Dashboard-Integration.

---

## 6. Integration in run_execution_session.py

### 6.1 Lifecycle-Wrapper

Die Hauptfunktion (`run_execution_session(...)`) wurde so erweitert, dass:

- Direkt am Anfang:
  - `started_at = datetime.utcnow()`
  - `status = "started"`
- Am Ende (bei Erfolg):
  - `status = "completed"`
- Bei Exceptions:
  - `status = "failed"`
  - `error = "<ExcName>: <message>"`
- Bei `KeyboardInterrupt`:
  - `status = "aborted"`
  - `error = "KeyboardInterrupt"`
- Im `finally`:
  - `finished_at` wird gesetzt (falls noch `None`)

### 6.2 Record-Erstellung und Registry-Call

Im `finally`-Block (vereinfacht):

```python
record = LiveSessionRecord(
    session_id=session_id,
    run_id=run_id,
    run_type=run_type,  # z.B. "live_session_shadow" oder "live_session_testnet"
    mode=mode,
    env_name=env_name,
    symbol=symbol,
    status=status,
    started_at=started_at,
    finished_at=finished_at,
    config=config,
    metrics=metrics,
    cli_args=cli_args or [],
    error=error,
)

try:
    path = register_live_session_run(record)
    logger.info("Live session recorded at %s", path)
except Exception as registry_exc:
    logger.warning(
        "Failed to record live session: %s",
        registry_exc,
        exc_info=True,
    )
```

**Run-Types:**

* `run_type="live_session_shadow"` für Shadow-Sessions
* `run_type="live_session_testnet"` für Testnet-Sessions
  (später erweiterbar, z.B. `live_session_live`)

CLI-Flags / Konfiguration entscheiden, welchen `run_type` und `mode` die Session erhält.

---

## 7. Tests & Smoke-Tests

### 7.1 Unit-Tests

`tests/test_live_session_registry.py` deckt u.a. ab:

* Roundtrip:

  * `LiveSessionRecord.to_dict()` → `from_dict()` ergibt äquivalentes Objekt
* Persistierung:

  * `register_live_session_run()` erzeugt eine gültige `.json`-Datei
* Queries:

  * `list_session_records()` mit Filtern & Limits
* Summary:

  * `get_session_summary()` für nicht-leere & leere Fälle
* Renderer:

  * Markdown/HTML-Generierung für einzelne und mehrere Sessions
* Safety:

  * Registry-Fehler können isoliert getestet und abgefangen werden
* Exports:

  * `__init__.py` exportiert die relevanten Symbole

### 7.2 Smoketest

Ein Smoketest wurde durchgeführt:

1. Shadow-Session gestartet (Dummy-Run).
2. `LiveSessionRecord` erstellt und registriert.
3. JSON-File in `reports/experiments/live_sessions/` erzeugt.
4. `list_session_records()` findet die Session.
5. `get_session_summary()` zeigt konsistente Aggregation.
6. `render_session_markdown()` liefert einen vollständigen Report-String.

---

## 8. Nutzung & nächste Schritte

### 8.1 Nutzung (Beispiele)

```python
from src.experiments.live_session_registry import (
    LiveSessionRecord,
    register_live_session_run,
    list_session_records,
    get_session_summary,
    render_session_markdown,
)

# Neue Session registrieren
record = LiveSessionRecord(
    session_id="session_001",
    run_id=None,
    run_type="live_session_shadow",
    mode="shadow",
    env_name="kraken_futures_testnet",
    symbol="BTC/USDT",
    status="completed",
    started_at=datetime.utcnow(),
    config={"strategy_name": "ma_crossover"},
    metrics={"realized_pnl": 150.0, "max_drawdown": 0.05},
    cli_args=["python", "scripts/run_execution_session.py", "--shadow"],
)

path = register_live_session_run(record)

# Sessions queryen
records = list_session_records(run_type="live_session_shadow", limit=10)
summary = get_session_summary(run_type="live_session_shadow")

# Report generieren
md_report = render_session_markdown(records[0])
```

### 8.2 CLI-Tool: report_live_sessions.py

Das CLI-Tool `scripts/report_live_sessions.py` generiert Markdown- und HTML-Reports aus der Live-Session-Registry.

**Verfuegbare Argumente:**

| Argument | Typ | Beschreibung |
|----------|-----|--------------|
| `--run-type` | str | Filter nach Run-Type (z.B. `live_session_shadow`) |
| `--status` | str | Filter nach Status (z.B. `completed`, `failed`) |
| `--limit` | int | Limit auf N neueste Sessions |
| `--output-format` | str | `markdown`, `html`, oder `both` (default: `markdown`) |
| `--summary-only` | Flag | Nur Summary generieren (keine Einzel-Reports) |
| `--output-dir` | Path | Verzeichnis fuer Output-Dateien |
| `--stdout` | Flag | Report nach stdout ausgeben |
| `--log-level` | str | DEBUG, INFO, WARNING, ERROR (default: INFO) |

**Beispiele:**

```bash
# Alle Sessions als Markdown-Report:
python scripts/report_live_sessions.py

# Nur Shadow-Sessions:
python scripts/report_live_sessions.py --run-type live_session_shadow

# Nur abgeschlossene Sessions:
python scripts/report_live_sessions.py --status completed

# Limit auf letzte 10 Sessions:
python scripts/report_live_sessions.py --limit 10

# HTML-Report generieren:
python scripts/report_live_sessions.py --output-format html

# Beide Formate:
python scripts/report_live_sessions.py --output-format both

# Nur Summary (keine Einzel-Reports):
python scripts/report_live_sessions.py --summary-only

# Report nach stdout:
python scripts/report_live_sessions.py --stdout

# Report in spezifisches Verzeichnis:
python scripts/report_live_sessions.py --output-dir reports/custom/
```

**Output:**

- Markdown-Reports: `YYYYMMDDTHHMMSS_sessions_report.md`
- HTML-Reports: `YYYYMMDDTHHMMSS_sessions_report.html`
- Summary-Reports: `YYYYMMDDTHHMMSS_sessions_summary.md` / `.html`

---

### 8.3 Moegliche Erweiterungen (Folgephasen)

* Dashboards:

  * Integration in bestehende Reporting-/Dashboard-Infrastruktur.
* Governance:

  * Verknuepfung mit Runbooks/Playbooks (z.B. Pflicht-Registry fuer jede Shadow-/Testnet-Session).
* Alerts:

  * Triggern von Alerts bei bestimmten Registry-Mustern (z.B. viele `failed`-Sessions, extremer Drawdown).
