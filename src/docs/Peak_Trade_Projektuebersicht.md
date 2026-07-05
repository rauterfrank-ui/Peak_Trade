# Peak_Trade – Projektübersicht (Stand 2025-12-03)

## 1. Projektkontext: Peak_Trade

**Peak_Trade** ist ein Trading-/Backtesting-Projekt mit Fokus auf:

- saubere **Data-Pipeline** (u.a. Kraken, CSV, Caching)
- modulare **Backtest-Engine**
- klar definierten **Risk-Layer** (Limits, Position Sizing)
- gut strukturierte **Dokumentation** und Projektorganisation

Aktueller Entwicklungsstand (Stand: 2025-12-03):

- **Phase 1 + Phase 2** sind abgeschlossen:
  - Data-Layer funktionsfähig
  - Backtest-Engine vorhanden
  - Risk-Layer implementiert und dokumentiert
- Projekt ist als **sauberes Python-Repo** mit venv + Tests aufgesetzt.

---

## 2. Aktuelle Projektstruktur (High-Level)

Verzeichnisstruktur nach dem Aufräumen / Reorganize-Skript:

```text
Peak_Trade/
├─ README.md
├─ pyproject.toml
├─ requirements.txt
├─ .gitignore
├─ config/
│  └─ config.toml
├─ src/
│  ├─ core/
│  ├─ data/
│  ├─ risk/
│  ├─ backtest/
│  └─ strategies/
├─ scripts/
│  ├─ demo_complete_pipeline.py
│  ├─ demo_risk_limits.py
│  ├─ demo_kraken_simple.py
│  └─ debug_signals.py
├─ tests/
├─ data/
├─ results/
├─ docs/
│  ├─ architecture/
│  │  └─ architecture_diagram.png
│  ├─ reports/
│  │  ├─ peak_trade_documentation.pdf
│  │  ├─ PeakTrade_enhanced.pdf
│  │  ├─ peak_trade_documentation.html
│  │  └─ dashboard.html
│  └─ project_docs/
│     ├─ CHANGELOG.md
│     ├─ RISK_MANAGEMENT.md
│     ├─ CLAUDE_NOTES.md
│     ├─ FINAL_SUMMARY.md
│     ├─ IMPLEMENTATION_SUMMARY.md
│     ├─ CONFIG_SYSTEM.md
│     ├─ RISK_LIMITS_UPDATE.md
│     ├─ NEXT_STEPS.md
│     └─ Peak_Trade_Data_Layer_Doku.md
└─ archive/
   ├─ PeakTradeRepo/
   ├─ noch_einordnen/
   └─ full_files_stand_02.12.2025
```

**Wichtig:**  
- Alles Produktive ist in `src/`, `scripts/`, `config/`, `tests/`.  
- Dokumentation ist zentral in `docs/` organisiert.  
- Historische Stände / Altmaterial liegen in `archive&#47;`.

---

## 3. Wichtige neue/überarbeitete Dateien

### 3.1. `docs/project_docs/CHANGELOG.md`

- Enthält eine **chronologische Änderungshistorie**.
- Aktuell v.a. **Phase 2** dokumentiert:
  - neue Risk-Module (`src/risk/limits.py`, `src/risk/position_sizer.py`, Backup-Version)
  - neue Data-Pipeline (`src/data/kraken_pipeline.py`)
  - neue Demo-Skripte (`demo_complete_pipeline.py`, `demo_kraken_simple.py`)
  - geänderte Exports in `src/risk/__init__.py`, `src/data/__init__.py`
  - Anpassungen an `config/config.toml` (Risk-Section)
- Ein Platzhalter für frühere Stände (z.B. `full_files_stand_02.12.2025`) ist vorgesehen.

### 3.2. `docs/project_docs/RISK_MANAGEMENT.md`

- Vollständige **Risk-Management-Doku** des Projekts:
  - Zweck & Scope des Risk-Layers
  - zentrale Risiko-Kennzahlen:
    - `max_risk_per_trade`
    - `max_daily_loss`
    - `max_drawdown`
    - Exposure-Limits
  - **Position Sizing** inkl. optionaler **Kelly-Logik**
  - globale Portfolio-Limits & Safeguards:
    - Kill-Switch, Trading-Pause, Circuit-Breaker
  - Konfiguration über `[risk]` in `config/config.toml`
  - Demos (`demo_risk_limits.py`, `demo_complete_pipeline.py`) und Tests (`tests&#47;test_risk.py`, falls vorhanden)
- Dokument ist als **produktive Referenz** ausgelegt – „Production-Ready“.

### 3.3. `docs/project_docs/CLAUDE_NOTES.md`

- Strukturierte **AI Session Log** Datei:
  - Zweck: alle relevanten KI-Interaktionen (Claude, ChatGPT, Gemini, etc.) zu Peak_Trade sammeln.
  - Abschnitte:
    - Meta (Projekt, Start, Tools)
    - Konventionen (Session-Struktur: Key Outcomes, Decisions, TODOs)
    - Aktuelle Sessions (u.a. Reorg des Projekts)
    - Archivierte Sessions (frühe Phase)
    - Best Practices für KI-Sessions
    - Geplante Verbesserungen (Tags, Links, „Hall of Fame“-Prompts)

### 3.4. `README.md` (neu aufgesetzt)

- Neue, saubere **Projekt-README** mit:
  - Projektbeschreibung und Feature-Überblick
  - Architektur-Summary (Data Layer, Strategy, Risk, Backtest, Doku)
  - Projektstruktur (Auszug)
  - Installationsanleitung (venv, `pip install -e .`)
  - Quickstart (Tests, Demos, komplette Pipeline)
  - Konfiguration (`config/config.toml`, Verweise auf Dokus)
  - Linkliste zu den zentralen Doku-Dateien
  - Roadmap (Phase 1+2 erledigt, Phase 3 geplant)
  - kurzer Support-/Kontakt-Teil

---

## 4. Tooling & Umgebung

### 4.1. VS Code

- **VS Code ist installiert und eingerichtet**:
  - Projektordner `Peak_Trade` in VS Code geöffnet
  - integriertes Terminal wird genutzt
  - Python-Extension & Pylance installiert
  - Python-Interpreter ist auf dein `.venv` gesetzt (`Python: Select Interpreter`)

### 4.2. Virtuelle Umgebung & Tests

- `.venv` existiert im Projekt.
- Typischer Ablauf im integrierten Terminal:

```bash
cd /Users/frnkhrz/Peak_Trade
source .venv/bin/activate
pytest
python scripts/demo_risk_limits.py
python scripts/demo_complete_pipeline.py
```

### 4.3. Git & Ignore-Regeln

- Git-Repo ist initialisiert, `main`-Branch aktiv.
- **Lokale KI-/Tool-Settings werden ignoriert**:
  - `.claude&#47;` in `.gitignore` eingetragen
  - `git rm --cached -r .claude` ausgeführt und committet
- Kontrollbefehle (für zukünftige Checks):

```bash
git status --short --untracked-files=all
git ls-files .claude
git check-ignore -v .claude/settings.local.json
```

---

## 5. Projektstatus nach Bereichen (Überblick)

Grober Status nach Bereichen (Ampel-Logik):

- **Data-Layer** ✅  
  - Loader, Normalizer, Cache, Kraken-Pipeline vorhanden  
  - Demos für Kraken & komplette Pipeline existieren

- **Backtest-Layer** ✅  
  - Backtest-Engine implementiert (`src/backtest/engine.py`)  
  - Stats-Modul (`stats.py`) existiert  
  - Integration mit Data- & Risk-Layer vorbereitet

- **Risk-Layer** ✅  
  - Limits & Position Sizing implementiert  
  - Konfiguration zentral in `[risk]`  
  - Doku + Demos vorhanden

- **Strategy-Layer** 🟡  
  - Mindestens eine Beispielstrategie existiert  
  - Erweiterungen für komplexere Strategien möglich/offen

- **Dokumentation** ✅  
  - Kern-Dokumente sauber strukturiert:  
    `README.md`, `RISK_MANAGEMENT.md`, `CHANGELOG.md`, `CLAUDE_NOTES.md`,  
    `IMPLEMENTATION_SUMMARY.md`, `CONFIG_SYSTEM.md`, `NEXT_STEPS.md`,  
    `Peak_Trade_Data_Layer_Doku.md`

- **Tooling / Dev-Setup** ✅  
  - VS Code, venv, pytest, Git-Setup  
  - Lokale KI-Einstellungen (`.claude&#47;`) sauber ignoriert

---

## 6. Nächste sinnvolle Schritte

Für die weitere Arbeit / nächste Chat-Runde bieten sich an:

1. **Fein-Übersicht / Roadmap je Layer**  
   - Data, Backtest, Risk, Strategy, Reporting  
   - Was ist stabil? Was ist experimentell? Was fehlt?

2. **Detail-Status der Strategien**  
   - Welche Strategien sind bereits implementiert?  
   - Wo fehlen noch Beispiele / Tests?

3. **Quantitative Übersicht in %**  
   - z.B. „Data-Layer 90 %, Risk-Layer 85 %, Backtest 80 %, Strategy 40 %, Doku 70 %“.

4. **Konkrete Next Steps für Phase 3**  
   - z.B. erweiterter Quant-Layer (El-Karoui-inspirierte Modelle, zusätzliche Strategien),
   - Monitoring/Reporting ausbauen,
   - eventuell Live-Trading-Integration vorbereiten.
