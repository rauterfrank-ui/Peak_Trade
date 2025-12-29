# REBOOT ROADMAP V2

**Status:** Reboot ab PR #380 Basis  
**Datum:** 29. Dezember 2025  
**Branch:** `docs/reboot-roadmap-v2`

---

## Kontext: Warum Reboot?

Peak_Trade hat ein funktionierendes MVP (Phase 1–86). Die Architektur ist modular, Tests laufen, Backtests funktionieren. **Aber:** Die Roadmap ist historisch gewachsen, fragmentiert über 80+ PHASE-Docs verteilt, und es fehlt ein klares operatives Framework für die nächsten Schritte.

**Reboot bedeutet:**
- **Keine Code-Refactors** – die Architektur bleibt wie sie ist.
- **Docs-Fokus** – klare, operative Phasen für die nächste Entwicklungswelle.
- **Governance-First** – Safety, CI-Gates, deterministische Workflows.
- **Kein "Auto-Live"** – jede Live-Komponente braucht explizite Freigabe.

---

## Was bleibt

- Alle Module in `src/` (Data, Strategy, Backtest, Live, Risk, Execution, etc.)
- Alle Tests in `tests/`
- Alle Config-Files in `config/`
- Die Experiment-Registry und MLflow-Integration
- Die bestehenden Scripts in `scripts/`
- Alle alten Docs (als Legacy markiert, nicht gelöscht)

---

## Was wird eingefroren

- Weitere Expansionen im Strategy-Layer (außer explizite Bugfixes)
- Neue Execution-Modi ohne Governance-Approval
- Auto-Promotion-Loops (bleiben im R&D-Status)
- Neue Live-Tracks ohne Risk-Gate-Reviews

---

## Phasen-Übersicht (P0–P9)

### **P0: Reboot-Basis & Docs-Cleanup**

**Goal:**  
Roadmap-Reboot dokumentieren, Legacy-Docs markieren, Navigation aktualisieren.

**Deliverables:**
- `docs/roadmaps/REBOOT_ROADMAP_V2.md` (diese Datei)
- `docs/roadmaps/REBOOT_PLAN.md` (Prinzipien + Mapping-Tabelle)
- `docs/roadmaps/MIGRATION_NOTES.md` (Scope-Cuts + Legacy-Liste)
- Update in `docs/README.md` (Link auf neue Roadmap)

**Verification:**
```bash
ls docs/roadmaps/REBOOT_*.md
grep -i "REBOOT_ROADMAP_V2" docs/README.md
```

**Exit Criteria:**
- Alle 3 Dateien existieren und sind committed.
- `docs/README.md` verlinkt die neue Roadmap.
- Keine Links sind broken (manueller Check).

**Risk:** LOW  
Nur Docs, kein Code-Impact.

---

### **P1: CI-Hardening & Test-Health-Dashboard**

**Goal:**  
CI auf 100% Green bringen, flaky Tests fixen, Test-Health-Metriken exponieren.

**Deliverables:**
- CI-Pipeline-Fix (GitHub Actions, alle Jobs grün)
- `scripts/check_test_health.py` (Flakiness-Report)
- `docs/ops/CI_HEALTH_REPORT.md` (Template für wöchentliche Updates)
- Smoke-Tests laufen in <5s, Full-Suite in <90s

**Verification:**
```bash
pytest -m smoke --durations=10
pytest -q --tb=short
python scripts/check_test_health.py
```

**Exit Criteria:**
- CI-Status: ✅ All Checks Passed (3 Tage konsistent)
- Flaky-Tests: ≤2% Failure-Rate über 10 Runs
- Test-Health-Report liegt vor

**Risk:** MED  
Flaky Tests können schwer zu isolieren sein.

---

### **P2: Governance-Gate für Live-Execution**

**Goal:**  
Explizite Freigabe-Checklisten für Live-Execution (Testnet + Paper).

**Deliverables:**
- `docs/governance/LIVE_EXECUTION_GATE.md` (Checklist-Template)
- `config/governance/live_approval_template.toml` (Config-Schema)
- `scripts/governance/check_live_readiness.py` (Automated Pre-Flight-Checks)
- Integration in `scripts/live/run_live_session.py` (Gate-Check vor Start)

**Verification:**
```bash
python scripts/governance/check_live_readiness.py --config config/live_policies.toml
# Sollte PASS/FAIL + Checklist ausgeben
```

**Exit Criteria:**
- Script läuft ohne Crash
- Checklist deckt Risk-Limits, Kill-Switch, Testnet-Config ab
- `run_live_session.py` verweigert Start bei failed Gate

**Risk:** MED  
Gate zu strikt → blockiert Testnet-Runs. Gate zu lax → bypassed.

---

### **P3: Execution-Telemetry & Audit-Trail-V2**

**Goal:**  
Lückenlose Telemetrie für alle Order-Events, strukturierte Audit-Logs.

**Deliverables:**
- `src/execution/telemetry.py` (OrderEvent-Logger mit Timestamps)
- `config/execution_telemetry.toml` (Log-Level-Config, Sink-Routing)
- `scripts/audit/export_order_trail.py` (Export nach CSV/JSON/Parquet)
- `docs/execution/TELEMETRY_SPEC.md` (Event-Schema-Doku)

**Verification:**
```bash
python scripts/run_paper_trade.py --strategy ma_crossover --symbol BTC/USDT --duration 10m
python scripts/audit/export_order_trail.py --output /tmp/audit_trail.csv
cat /tmp/audit_trail.csv | head -5  # Sollte Order-Events zeigen
```

**Exit Criteria:**
- Jede Order hat min. 3 Events: REQUESTED, SUBMITTED, FILLED (oder REJECTED/CANCELLED)
- Export-Script erzeugt parseable CSV mit allen Pflichtfeldern
- Telemetry-Overhead <1% Runtime

**Risk:** LOW  
Overhead-Risiko bei High-Frequency-Setups, aber aktuell kein Use-Case.

---

### **P4: Risk-Layer-V2 (Liquidity + Stress Gates)**

**Goal:**  
Erweiterte Risk-Gates für Liquidität und Stress-Szenarien.

**Deliverables:**
- `src/risk_layer/liquidity_gate.py` (Slippage-/Volume-Checks)
- `src/risk_layer/stress_gate.py` (VaR, Max-DD-Projection)
- `config/risk_liquidity_gate_example.toml` (Referenz-Config)
- `config/risk_stress_gate_example.toml` (Referenz-Config)
- `tests/risk_layer/test_liquidity_gate.py` (Unit + Integration)

**Verification:**
```bash
pytest tests/risk_layer/test_liquidity_gate.py -v
pytest tests/risk_layer/test_stress_gate.py -v
```

**Exit Criteria:**
- Liquidity-Gate blockt Orders bei Slippage >Threshold
- Stress-Gate blockt bei VaR-Überschreitung
- Config-Defaults sind konservativ (z.B. VaR 95% = 2% Portfolio)

**Risk:** HIGH  
False-Positives → blockieren valide Trades. False-Negatives → Risk-Leak.

---

### **P5: Shadow-Execution-Replay & Diff-Report**

**Goal:**  
Shadow-Runs abspielen, mit Real-Execution vergleichen (Post-Mortem).

**Deliverables:**
- `scripts/shadow/replay_shadow_run.py` (Replay von Session-Logs)
- `scripts/shadow/diff_shadow_vs_live.py` (Side-by-Side-Vergleich)
- `reports/shadow/SHADOW_DIFF_TEMPLATE.html` (Quarto-basiert)
- `docs/shadow/SHADOW_REPLAY_GUIDE.md` (Nutzerdoku)

**Verification:**
```bash
python scripts/shadow/replay_shadow_run.py --session 20251221_220016_paper_ma_crossover_BTC-EUR_1m
python scripts/shadow/diff_shadow_vs_live.py --shadow <session_id> --live <session_id>
```

**Exit Criteria:**
- Replay erzeugt identische Signal-Timestamps wie Original-Run
- Diff-Report zeigt Abweichungen in Fills, Slippage, PnL
- Template rendert als HTML mit Plotly-Charts

**Risk:** MED  
Replay-Bugs können falsche Diffs erzeugen → irreführende Post-Mortem-Analyse.

---

### **P6: R&D-Experiment-Dashboard (WebUI v0.1)**

**Goal:**  
Read-Only-Dashboard für Experiment-Registry, Sweep-Ergebnisse, Backtest-Vergleiche.

**Deliverables:**
- `src/webui/experiments_dashboard.py` (FastAPI-Routen)
- `templates/experiments/dashboard.html` (Jinja2-Template mit DataTables.js)
- `scripts/webui/start_dashboard.py --port 8501`
- `docs/webui/EXPERIMENTS_DASHBOARD.md` (Setup + Screenshots)

**Verification:**
```bash
python scripts/webui/start_dashboard.py --port 8501 &
curl http://localhost:8501/api/experiments?limit=10
# Sollte JSON mit Experiments zurückgeben
```

**Exit Criteria:**
- Dashboard startet ohne Errors
- Experiment-Liste zeigt min. 10 jüngste Runs
- Filter funktioniert (run_type, symbol, date_range)
- Keine Write-Operations im UI (Read-Only-Modus)

**Risk:** LOW  
Nur Read-Only, keine Execution-Impact.

---

### **P7: Regime-Detection-Integration (Minimal Viable)**

**Goal:**  
Regime-Detection-Modul in Backtest-Engine integrieren, Regime-Aware-Reporting.

**Deliverables:**
- `src/regime/detector.py` (HMM-basiert, 3 States: Bull/Bear/Sideways)
- `src/backtest/regime_aware_engine.py` (Wrapper um BacktestEngine)
- `scripts/run_regime_backtest.py` (CLI-Entry-Point)
- `docs/regime/REGIME_DETECTION_SPEC.md` (Feature-Spec + Algo-Beschreibung)

**Verification:**
```bash
python scripts/run_regime_backtest.py --strategy ma_crossover --symbol BTC/USDT --start 2024-01-01
# Sollte Backtest-Stats + Regime-Transition-Plot ausgeben
```

**Exit Criteria:**
- Detector läuft ohne Crash auf 2 Jahren BTC/USDT-Daten
- Regime-Transitions sind plausibel (min. 3 Transitions in 2 Jahren)
- Backtest-Stats enthalten Regime-Breakdown (Sharpe pro Regime)

**Risk:** MED  
HMM kann instabil konvergieren → Fallback auf Rule-Based (RSI+ATR).

---

### **P8: Multi-Strategy-Portfolio-Backtest**

**Goal:**  
Portfolio aus mehreren Strategien backtesten, mit Korrelations-Metriken.

**Deliverables:**
- `src/portfolio/multi_strategy_portfolio.py` (Portfolio-Klasse)
- `config/portfolios/multi_strategy_example.toml` (3-Strat-Portfolio)
- `scripts/run_portfolio_backtest.py` (CLI für Portfolio-Backtests)
- `docs/portfolio/PORTFOLIO_BACKTEST_GUIDE.md` (Nutzerdoku + Beispiele)

**Verification:**
```bash
python scripts/run_portfolio_backtest.py --config config/portfolios/multi_strategy_example.toml
# Sollte Portfolio-Stats + Correlation-Matrix ausgeben
```

**Exit Criteria:**
- Portfolio-Backtest läuft mit 3 Strategien parallel
- Equity-Curve zeigt aggregierte PnL
- Correlation-Matrix zeigt Strategy-Pair-Korrelationen
- Portfolio-Sharpe wird korrekt berechnet

**Risk:** MED  
Timing-Issues bei gleichzeitigen Orders → Order-Queue-Modul nötig (Out-of-Scope für P8, als Debt notiert).

---

### **P9: Observability-Stack (Prometheus + Grafana)**

**Goal:**  
Metrics exportieren (Orders, PnL, Risk-Events), Grafana-Dashboards.

**Deliverables:**
- `src/obs/prometheus_exporter.py` (Prometheus-Client-Integration)
- `docker/obs/prometheus.yml` (Prometheus-Config)
- `docker/obs/grafana/dashboards/peak_trade_live.json` (Grafana-Dashboard)
- `docs/obs/OBSERVABILITY_SETUP.md` (Setup-Guide + Screenshot)

**Verification:**
```bash
docker compose -f docker/docker-compose.obs.yml up -d
curl http://localhost:9090/metrics | grep peak_trade_orders_total
# Sollte Metrics zeigen
```

**Exit Criteria:**
- Prometheus scrapet Metrics alle 15s
- Grafana zeigt Live-Dashboard mit Order-Rate, PnL, Risk-Events
- Dashboards persistieren in Git (JSON-Export)

**Risk:** LOW  
Nur Monitoring, keine Execution-Impact.

---

## Scope-Exclusions (Bewusst NICHT in diesem Reboot)

- RL-basierte Strategien (bleiben in `archive/` oder separatem Branch)
- Auto-Promotion-Loops ohne manuelles Review
- WebUI mit Write-Operationen (Live-Order-Placement via UI)
- Exchange-Integrationen über Kraken/Binance hinaus
- Real-Money-Live-Execution (nur Testnet + Paper bis auf Weiteres)

---

## Roadmap-Timeline (Geschätzt)

| Phase | Estimated Effort | Cumulative |
|-------|-----------------|------------|
| P0    | 2 Stunden       | 2h         |
| P1    | 1 Woche         | 1w 2h      |
| P2    | 3 Tage          | 1w 3d 2h   |
| P3    | 1 Woche         | 2w 3d 2h   |
| P4    | 2 Wochen        | 4w 3d 2h   |
| P5    | 1 Woche         | 5w 3d 2h   |
| P6    | 1 Woche         | 6w 3d 2h   |
| P7    | 2 Wochen        | 8w 3d 2h   |
| P8    | 1 Woche         | 9w 3d 2h   |
| P9    | 3 Tage          | 10w 2h     |

**Total:** ~10 Wochen (2,5 Monate bei Vollzeit-Äquivalent)

---

## Erfolgskriterien für den Reboot

1. **Alle P0–P9-Exit-Criteria erfüllt** (siehe Phasen oben).
2. **CI bleibt grün** (keine Regression durch neue Features).
3. **Docs sind navigierbar** (keine broken Links, klare Struktur).
4. **Live-Execution läuft nur mit Governance-Approval** (kein Bypass).
5. **Risk-Gates blocken unsichere Setups** (False-Positive-Rate <5%).

---

## Next Steps nach Reboot

Nach P9 (also nach ~10 Wochen):
- **Review-Milestone:** Lessons Learned, Gap-Analyse.
- **Roadmap-V3-Planning:** Nächste Wave (z.B. Multi-Exchange, RL-Strategien, Real-Money-Track).
- **Production-Readiness-Review:** Wenn alle Gates grün → Testnet→Production-Migration-Plan.

---

**Dokument-Ende**
