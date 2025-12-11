# Peak_Trade – Aktueller Stand & Workflow
Stand: 03.12.2025

---

## 1. Aktueller technischer Stand

### 1.1 Data-Layer (`src/data/`)

- Loader / Normalizer / Cache / Kraken-Integration vorhanden und lauffähig.
- Standard-Output ist ein normalisierter OHLCV-DataFrame, der im Backtest verwendet wird.

### 1.2 Strategy-Layer (`src/strategies/`)

- **Basis-API**
  - `base.py`:
    - `StrategyMetadata`
    - `BaseStrategy` mit `generate_signals(data: pd.DataFrame) -> pd.Series`

- **Konkrete Strategien**
  - `MACrossoverStrategy` (`ma_crossover.py`)
  - `RsiReversionStrategy` (`rsi_reversion.py`)
  - `DonchianBreakoutStrategy` (`breakout_donchian.py`)

- Alle Strategien geben diskrete Signals / States zurück (`-1, 0, 1`).

### 1.3 Core-Layer (`src/core/`)

- **Config**
  - `config.py`:
    - `PeakConfig` mit `get("a.b.c")`
    - `load_config("config.toml")` (TOML-basiert)

- **Position Sizing (`position_sizing.py`)**
  - `BasePositionSizer`
  - `NoopPositionSizer` (direktes Mapping Signal → Units)
  - `FixedSizeSizer` (konstante Units pro Signal)
  - `FixedFractionSizer` (fester Equity-Anteil pro Signal)
  - `build_position_sizer_from_config(cfg)` mit `[position_sizing]` in `config.toml`

- **Risk Management (`risk.py`)**
  - `BaseRiskManager`
  - `NoopRiskManager`
  - `MaxDrawdownRiskManager` (Stop bei max. Drawdown, z.B. 25 %)
  - `EquityFloorRiskManager` (Stop unter bestimmter Equity, z.B. 5.000)
  - `build_risk_manager_from_config(cfg)` mit `[risk]` in `config.toml`

### 1.4 Backtest-Layer (`src/backtest/`)

- `BacktestEngine` (in `engine.py`) nutzt:
  - Strategie (`BaseStrategy`)
  - PositionSizer (`BasePositionSizer`)
  - RiskManager (`BaseRiskManager`)
- `stats.py` für Kennzahlen und Auswertungen.

### 1.5 Strategy Registry (`src/strategies/registry.py`)

- Strategy-Keys → Klassen & Config-Sections:
  - `"ma_crossover"` → `MACrossoverStrategy`, Section `strategy.ma_crossover`
  - `"rsi_reversion"` → `RsiReversionStrategy`, Section `strategy.rsi_reversion`
  - `"breakout_donchian"` → `DonchianBreakoutStrategy`, Section `strategy.breakout_donchian`
- `build_strategy_from_config(cfg, key=None)`:
  - liest Key aus `cfg.get("strategy.key", "ma_crossover")`, wenn `key=None`.
  - baut die passende Strategieinstanz.

### 1.6 Runner (`scripts/`)

- Spezifische Runner:
  - `run_ma_realistic.py`
  - `run_rsi_reversion.py`
  - `run_breakout_donchian.py`
- Generischer Runner:
  - `run_strategy_from_config.py`
    - liest `config.toml`
    - wählt Strategie über `[strategy].key` oder `--strategy`
    - lädt PositionSizer & RiskManager aus Config
    - startet Backtest über `BacktestEngine`

**Fazit:**  
System ist **voll modular**: Strategien, Sizing, Risk, Registry, generischer Runner – alles verdrahtet und funktionsfähig.

---

## 2. Unser gemeinsamer Workflow (ChatGPT ↔ Claude Code ↔ Repo)

Damit wir später nahtlos weitermachen können, hier der eingespielte Workflow:

### 2.1 Rollenaufteilung

- **Du (Frank)**
  - Entscheidet den nächsten Block / Fokus: z.B.
    - „weitere Strategien“
    - „Position Sizing“
    - „Risk Management“
    - „Strategy Registry“
    - „Doku & Architektur“
  - Führst den von mir erzeugten Prompt in **Claude Code** (oder einem ähnlichen Tool) aus, direkt im Repo.

- **Ich (ChatGPT / Peak_Trade-Co-Pilot)**
  - Erzeuge immer **EINEN großen, in sich geschlossenen Prompt**, z.B.:
    - „Alles-in-einem-Prompt für Claude Code ab hier …“
  - Der Prompt enthält:
    - Ziel des Tasks (was soll erreicht werden)
    - exakte Datei-Pfade
    - kompletten Inhalt für neue Dateien
    - klare Anweisungen für Änderungen an bestehenden Dateien
    - am Ende einen „Abschlussbericht“-Block, damit Claude dir eine Zusammenfassung ausspuckt

### 2.2 Typischer Ablauf eines Blocks

1. Du sagst den Fokus, z.B.:  
   > „wir machen weiter mit \"weitere Strategien\"“  
   oder  
   > „weiter mit Position Sizing“

2. Ich liefere:
   - einen **großen Textblock** (meist als „Claude-Code-Prompt“ bezeichnet),
   - der alle Schritte von 1️⃣ bis 6️⃣ (inkl. Abschlussbericht) enthält,
   - so, dass du ihn **1:1 kopieren** kannst.

3. Du:
   - kopierst den Prompt in Claude Code,
   - lässt dort die Aktionen im Repo ausführen,
   - führst ggf. die vorgeschlagenen `python scripts/...`-Kommandos aus,
   - meldest mir zurück:
     - z.B. „Alle Aufgaben erfolgreich abgeschlossen!“

4. Ich:
   - gehe davon aus, dass der Block jetzt im Code umgesetzt ist,
   - setze beim *nächsten* Prompt genau auf dieser neuen Struktur auf,
   - liefere den nächsten „Mega-Prompt“ für den folgenden Themenblock.

### 2.3 Stilregeln für die Prompts

- Sprache: **Deutsch** (außer Code/Kommentare/Docs, die ggf. Englisch sind).
- Ton: locker, aber technisch präzise (Emojis erlaubt 😄).
- Struktur der Prompts:
  - Klar getrennte Abschnitte mit Überschriften (1️⃣, 2️⃣, 3️⃣ …).
  - Jeder Abschnitt hat:
    - *Aufgabe* / *Ziel*
    - ggf. exakten Ziel-Code für Dateien
    - Hinweise zu Imports, Zirkularimports, Pfaden
  - Am Ende: **„Abschlussbericht“-Anweisungen**, damit Claude berichten kann:
    - Welche Dateien geändert/erstellt wurden.
    - Wie man Backtests startet.
    - Wie man Einstellungen in `config.toml` ändert.

---

## 3. Geplanter nächster Block (wenn du wieder Zeit/Tokens hast)

Nächster großer Block, den wir bereits angepeilt haben:

- **Doku & Architektur**
  - `docs/PEAK_TRADE_OVERVIEW.md`
  - `docs/BACKTEST_ENGINE.md`
  - `docs/STRATEGY_DEV_GUIDE.md`
  - aktualisiertes `README.md`

Dafür habe ich dir schon einen fertigen Prompt vorbereitet (im Chatverlauf kurz vor dieser Notiz).  
Wenn du weitermachst, kannst du einfach sagen:

> „Weiter mit Doku & Architektur (benutze den letzten Prompt)“

oder ich baue dir nochmal einen aktualisierten All-in-One-Prompt.

---

## 4. Wie du diese Datei nutzen kannst

- Speichere diese Datei z.B. als
  `docs/WORKFLOW_NOTES.md` oder `Peak_Trade_WORKFLOW_NOTES.md`
  in deinem Repo.
- Sie dient als:
  - Snapshot des aktuellen technischen Stands,
  - Dokumentation unseres gemeinsamen Workflows,
  - Einstiegspunkt, um später wieder genau im selben Stil weiterzumachen.

---

## 5. Changelog / Meilensteine

### 2025-12-11 – Repo-Cleanup abgeschlossen

- Neue Doku-Struktur unter `docs/` eingeführt (Overview, Architecture, Phases, Runbooks, Reference, Archive)
- Workflow- und Status-Dokumente nach `docs/00_overview/` verschoben
- PHASE-Dokumente und Runbooks sauber einsortiert
- Caches und temporäre Verzeichnisse entfernt (z.B. `__pycache__/`)
- PR `chore/folder-cleanup` → `main` erstellt und gemerged

**Ergebnis:** Repository ist übersichtlich strukturiert und zukunftssicher organisiert – bereit für die nächsten Peak_Trade-Phasen (InfoStream, TestHealth-Automation, Market-Forecast, Trigger-Training).
