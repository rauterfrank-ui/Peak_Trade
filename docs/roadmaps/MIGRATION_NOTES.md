# MIGRATION NOTES – Reboot V2

**Zweck:** Dokumentation zu Scope-Cuts, Legacy-Markierungen und Navigation nach dem Reboot.

---

## Scope-Cuts (Bewusst NICHT mehr machen)

Diese Features/Workflows werden **nicht weiter verfolgt** im Reboot V2:

### 1. Auto-Promotion-Loops ohne Manual-Review
- **Alt:** Learning-Promotion-Loop sollte automatisch Top-N-Strategien in Live promoten.
- **Neu:** Bleibt im R&D-Status. Live-Promotion nur nach manuellem Go/No-Go-Review.
- **Begründung:** Safety-First – kein Auto-Deployment ohne Governance-Gate.

### 2. RL-basierte Strategien im Core
- **Alt:** Reinforcement-Learning-Strategien als Teil des Strategy-Layers.
- **Neu:** RL-Strategien bleiben in `archive/` oder separatem Branch (z.B. `experimental/rl`).
- **Begründung:** RL ist Research-heavy, zu instabil für Production-Track.

### 3. WebUI mit Write-Operations
- **Alt:** Dashboard sollte Order-Placement, Config-Edits, Live-Start/Stop erlauben.
- **Neu:** Dashboard bleibt Read-Only (P6). Alle Write-Ops via CLI + Config-Files.
- **Begründung:** Audit-Trail und Governance sind einfacher mit CLI + Git-versioned Configs.

### 4. Multi-Currency-Portfolios
- **Alt:** Portfolios mit Mix aus USD-, EUR-, BTC-denominierten Positionen.
- **Neu:** Nur Single-Currency pro Portfolio (z.B. USD oder EUR).
- **Begründung:** FX-Risk-Management ist out-of-scope für V2.

### 5. Exchange-Expansion (über Kraken/Binance hinaus)
- **Alt:** Unterstützung für 10+ Exchanges (Coinbase, OKX, Bybit, etc.).
- **Neu:** Nur Kraken + Binance (Testnet + Real-Money).
- **Begründung:** Jede Exchange-Integration ist aufwändig (API-Quirks, Testing).

### 6. Sub-Second-Execution (HFT)
- **Alt:** Latenz-Optimierung für High-Frequency-Trading (<100ms Order-to-Fill).
- **Neu:** Kein HFT-Support. Min. Bar-Interval = 1 Minute.
- **Begründung:** HFT braucht Co-Location, spezialisierte Infra → out-of-scope.

### 7. Real-Money-Live ohne Testnet-Phase
- **Alt:** Direkter Sprung von Paper-Trade zu Real-Money.
- **Neu:** Testnet ist mandatory Gate. Mindestens 1 Woche Testnet-Run vor Real-Money.
- **Begründung:** Risk-Mitigation – Testnet deckt Exchange-API-Bugs ab.

---

## Legacy-Markierungsliste

Diese Dokumente sollten als **"Legacy (pre-reboot)"** markiert werden (Header oder Prefix):

### Roadmaps (alte Phasen)
- `docs/Peak_Trade_Roadmap.md` → Header ergänzen: `[LEGACY – pre-reboot v2]`
- `docs/PEAK_TRADE_MINI_ROADMAP_V1_RESEARCH_LIVE_BETA.md` → Legacy-Marker
- `docs/Peak_Trade_Research_Strategy_Roadmap_2025-12-07.md` → Legacy-Marker

### Phase-Docs (Phase 16–86)
- Alle `docs/PHASE_*.md` Dateien (ca. 80 Dateien) → Optional: Footnote einfügen:
  ```markdown
  > **Legacy Note (2025-12-29):** Diese Phase-Docs sind historisch. Siehe `docs/roadmaps/REBOOT_ROADMAP_V2.md` für aktuellen Stand.
  ```
- **NICHT löschen!** Diese Docs sind wichtig für historischen Kontext und Lessons Learned.

### Overviews (Status-Reports)
- `docs/PEAK_TRADE_OVERVIEW_PHASES_1_17.md` → Legacy-Marker
- `docs/PEAK_TRADE_OVERVIEW_PHASES_1_40.md` → Legacy-Marker
- `docs/Peak_Trade_Status_2025-12-31.md` → **Aktuell**, kein Legacy-Marker (ist Snapshot)

### Implementation-Summaries (alte Phasen)
- Alle `PHASE*_IMPLEMENTATION_SUMMARY.md` Files im Root-Dir → Optional: Legacy-Marker.
- **Aktuell relevant:** Diese Docs beschreiben implementierte Features → behalten, aber als "historisch" markieren.

### AI-Guides (teilweise veraltet)
- `docs/ai/CLAUDE_GUIDE.md` → **Aktuell**, kein Legacy-Marker (wird laufend gepflegt).
- `docs/ai/PEAK_TRADE_AI_HELPER_GUIDE.md` → **Aktuell**, kein Legacy-Marker.

---

## How to Navigate After Reboot

### Für neue Entwickler (Onboarding)
1. **Start:** `README.md` (Root) → Quick Start (5 Minuten Backtest).
2. **Architektur:** `docs/PEAK_TRADE_OVERVIEW.md` (System-Überblick).
3. **Roadmap:** `docs/roadmaps/REBOOT_ROADMAP_V2.md` (Aktuelle Phasen).
4. **Dev-Setup:** `docs/DEV_SETUP.md` (Environment, Dependencies, Tests).
5. **First Contribution:** `docs/ai/PEAK_TRADE_AI_HELPER_GUIDE.md` (Workflow-Guide).

### Für Strategie-Entwicklung
1. **Strategy-Dev-Guide:** `docs/STRATEGY_DEV_GUIDE.md` (Schritt-für-Schritt).
2. **Backtest-Engine:** `docs/BACKTEST_ENGINE.md` (Engine-Details).
3. **Registry-Logging:** `docs/CONFIG_REGISTRY_USAGE.md` (Experiment-Tracking).
4. **Beispiel-Strategien:** `src/strategies/` (OOP-Strategien als Referenz).

### Für Live-Deployment
1. **Live-Workflows:** `docs/LIVE_WORKFLOWS.md` (Paper, Testnet, Real-Money).
2. **Risk-Limits:** `docs/LIVE_RISK_LIMITS.md` (Config + Beispiele).
3. **Governance-Gate:** `docs/governance/LIVE_EXECUTION_GATE.md` (Checklist) → **P2** (nach Reboot).
4. **Incident-Runbook:** `docs/DISASTER_RECOVERY_RUNBOOK.md` (Kill-Switch, Rollback).

### Für Observability & Monitoring
1. **Observability-Plan:** `docs/OBSERVABILITY_AND_MONITORING_PLAN.md` (Überblick).
2. **Prometheus-Setup:** `docs/obs/OBSERVABILITY_SETUP.md` → **P9** (nach Reboot).
3. **Live-Track-Dashboard:** `docs/PHASE_82_LIVE_TRACK_DASHBOARD.md` (Legacy-Impl.).

### Für Research & Experiments
1. **Research-Golden-Paths:** `docs/PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md` (Workflows).
2. **Sweeps & Optuna:** `docs/HYPERPARAM_SWEEPS.md` + `docs/OPTUNA_STUDY_RUNNER_GUIDE.md`.
3. **Walk-Forward:** `docs/PHASE_44_WALKFORWARD_TESTING.md` (Legacy-Impl.).
4. **Regime-Analysis:** `docs/REGIME_ANALYSIS.md` (vor P7-Reboot).

---

## Dokument-Struktur nach Reboot

### Top-Level-Struktur (Ziel)
```
docs/
├── README.md                         # Docs-Index mit Links zu Roadmap, Guides, etc.
├── roadmaps/
│   ├── REBOOT_ROADMAP_V2.md          # ← Neue Roadmap (Single-Source-of-Truth)
│   ├── REBOOT_PLAN.md                # ← Prinzipien + Mapping
│   ├── MIGRATION_NOTES.md            # ← Diese Datei
│   └── [Legacy-Roadmaps...]          # Peak_Trade_Roadmap.md, etc. (als Legacy markiert)
├── governance/
│   ├── LIVE_EXECUTION_GATE.md        # ← P2-Deliverable
│   └── ...
├── execution/
│   ├── TELEMETRY_SPEC.md             # ← P3-Deliverable
│   └── ...
├── risk/
│   └── ...
├── ops/
│   ├── CI_HEALTH_REPORT.md           # ← P1-Deliverable
│   └── ...
├── obs/
│   ├── OBSERVABILITY_SETUP.md        # ← P9-Deliverable
│   └── ...
└── [Alte Phase-Docs...]              # PHASE_*.md (mit Legacy-Marker)
```

### Löschen vs. Archivieren
- **NICHTS löschen!** Alle alten Docs bleiben für historischen Kontext.
- **Archivieren:** Optional Unterordner `docs/archive/pre_reboot/` anlegen und alte Roadmaps dorthin verschieben (aber erst nach P0-Abschluss, nicht sofort).

---

## Migration-Checkliste (für P0)

- [x] `docs/roadmaps/` Verzeichnis angelegt
- [x] `REBOOT_ROADMAP_V2.md` erstellt
- [x] `REBOOT_PLAN.md` erstellt
- [x] `MIGRATION_NOTES.md` erstellt (diese Datei)
- [ ] `docs/README.md` aktualisiert (Link auf neue Roadmap)
- [ ] Legacy-Marker in `docs/Peak_Trade_Roadmap.md` eingefügt (optional, nice-to-have)
- [ ] Broken-Link-Check durchgeführt (manuell oder via CI)
- [ ] P0 als abgeschlossen markiert (Commit + PR)

---

## FAQ

### Q: Werden alte PHASE-Docs gelöscht?
**A:** Nein. Sie bleiben für historischen Kontext und Lessons Learned. Optional: Legacy-Marker im Header.

### Q: Was passiert mit alten Roadmap-Dateien?
**A:** Sie bekommen einen Legacy-Marker im Header. Optional: Verschieben nach `docs/archive/pre_reboot/` (aber nicht in P0).

### Q: Kann ich alte Phase-Docs noch referenzieren?
**A:** Ja! Verlinke sie mit Legacy-Hinweis, z.B.:  
`Siehe [PHASE_25_GOVERNANCE_SAFETY_IMPLEMENTATION.md](../PHASE_25_GOVERNANCE_SAFETY_IMPLEMENTATION.md) (Legacy-Impl.) für Details.`

### Q: Was ist mit Code-Refactors?
**A:** **Keine** Code-Refactors im Reboot V2. Nur Docs + neue Features (wie in REBOOT_ROADMAP_V2.md definiert).

### Q: Wann werden RL-Strategien wieder aufgegriffen?
**A:** Frühestens in V3 (nach P9-Abschluss + Review). Siehe `docs/roadmaps/REBOOT_ROADMAP_V2.md` → "Next Steps nach Reboot".

### Q: Wann darf ich Live-Execution starten?
**A:** Erst nach P2 (Governance-Gate) + Testnet-Phase (min. 1 Woche). Siehe `docs/roadmaps/REBOOT_PLAN.md` → "Governance & Release Flow".

---

**Dokument-Ende**
