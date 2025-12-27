# Peak_Trade – Runner Index (Canonical Tiers A/B/C)

Ziel: Aus vielen ausführbaren Scripts eine **kanonische Menge** von „Main Entry" Runnern definieren, damit Ops/CI/Docs stabil bleiben.

## Definitionen

### Tier A — Canonical "Main Entry" Runner
Diese Runner gelten als **offiziell** (Docs/CI/Ops). Änderungen daran sind „must not break".

### Tier B — Ops/Automation
Automation, Maintenance, Health Checks, CI/Release Helper.

### Tier C — Utility/Dev/One-off
Hilfsskripte, Experimente, Migrations, ad-hoc Tools.

---

## Quellen für die Tiering-Entscheidung

Wir gewichten Signale in dieser Reihenfolge:
1) **CI Workflows** (`.github/workflows/*`)  
2) **Docs/README/Runbooks** (`README*`, `docs/**`)  
3) **Makefile / Task Runner**  
4) **Recent changes** (nur schwaches Signal)

---

## Tier A (Canonical Runner Set)

> Auto-kuratiert aus Repo-Referenzen (Docs/CI). Sortiert nach P1 Priority + Doc-Referenzen.

| Shortname | Pfad | Zweck | Beispiel-Command | Inputs | Outputs | Readiness | P1 |
|---|---|---|---|---|---|---|---|
| research_cli.py | `scripts/research_cli.py` | Research CLI: sweep, report, promote, walkforward, montecarlo, stress, portfolio, pipeline, strategy-profile... | `python scripts/research_cli.py --help` | strategy config, data files, sweep params | run_id, results/* (partial) | 🟡 PARTIAL | **MUST** |
| run_backtest.py | `scripts/run_backtest.py` | Run backtest with strategy config, data file, date range | `python scripts/run_backtest.py --help` | strategy config, data file, date range | run_id, results/*/config_snapshot, stats.json, equity.csv | ✅ READY | **MUST** |
| live_ops.py | `scripts/live_ops.py` | Peak_Trade Live-/Testnet Operations CLI | `python scripts/live_ops.py --help` | live/testnet credentials, strategy configs | logs, session reports (no results/ yet) | ❌ TODO | **MUST** |
| run_execution_session.py | `scripts/run_execution_session.py` | Execute live/testnet session with strategy + symbol | `python scripts/run_execution_session.py --help` | strategy name, symbol, live/testnet mode | run_id, session logs (partial results/) | 🟡 PARTIAL | SHOULD |
| preview_live_portfolio.py | `scripts/preview_live_portfolio.py` | Preview live portfolio allocation, JSON export, starting cash config | `python scripts/preview_live_portfolio.py --help` | portfolio config, starting cash | JSON preview (no results/) | ❌ TODO | LATER |
| run_test_health_profile.py | `scripts/run_test_health_profile.py` | Run test health profiling/reporting | `python scripts/run_test_health_profile.py --help` | test suite results | health reports (no results/) | ❌ TODO | LATER |
| report_live_sessions.py | `scripts/report_live_sessions.py` | Generate live session reports (markdown/html) | `python scripts/report_live_sessions.py --help` | session logs, trade data | markdown/html reports (no results/) | ❌ TODO | LATER |
| run_promotion_proposal_cycle.py | `scripts/run_promotion_proposal_cycle.py` | Run promotion loop v0: build promotion candidates from config patches | `python scripts/run_promotion_proposal_cycle.py --help` | config patches, promotion criteria | promotion candidates (no results/) | ❌ TODO | LATER |
| run_strategy_sweep.py | `scripts/run_strategy_sweep.py` | Run strategy parameter sweep | `python scripts/run_strategy_sweep.py --help` | strategy name, param grid | sweep results (no results/) | ❌ TODO | LATER |
| experiments_explorer.py | `scripts/experiments_explorer.py` | Explore experiments: list, top, details, sweep-summary, sweeps, compare, export | `python scripts/experiments_explorer.py --help` | experiment database/results | queries, comparisons, exports (reads results/) | 🟡 PARTIAL | LATER |
| testnet_orchestrator_cli.py | `scripts/testnet_orchestrator_cli.py` | Testnet orchestration: start-shadow, start-testnet, status, stop, tail | `python scripts/testnet_orchestrator_cli.py --help` | testnet configs, orchestration commands | run_id, orchestration logs (partial results/) | 🟡 PARTIAL | LATER |
| run_offline_realtime_ma_crossover.py | `scripts/run_offline_realtime_ma_crossover.py` | Run offline realtime MA crossover with n-regimes | `python scripts/run_offline_realtime_ma_crossover.py --help` | data file, n-regimes param | run_id, backtest results (partial results/) | 🟡 PARTIAL | LATER |

### Auto-Curation Notes

**Analysiert:** 12 Tier-A Runner
**Readiness:** 1 READY, 5 PARTIAL, 6 TODO

**Kuratierungs-Details:**
- ✅ Alle Runner haben `--help` Support (außer `run_promotion_proposal_cycle.py`)
- 🔍 Static scan erfolgreich für alle Scripts
- 📊 Doc-Referenzen gezählt aus `docs/`, `.github/`, `README.md`
- 🎯 P1 Priority basiert auf: Doc-Referenzen (gewichtet: CI×2, README×3) + Readiness

**Top 3 P1 MUST integrate first:**
1. **research_cli.py** – 43 doc refs, PARTIAL readiness, zentrale Research-Entry
2. **run_backtest.py** – 22 doc refs, READY (run_id + results/), häufigster Backtest
3. **live_ops.py** – 20 doc refs, TODO readiness, zentrale Live-Ops Entry

**P1 SHOULD integrate next:**
- **run_execution_session.py** – 16 doc refs, PARTIAL readiness, core execution

**Required Artifacts (READY/PARTIAL runners):**
- `config_snapshot.*`
- `stats.json`
- `equity.csv`

**Reproduce Curation:**
```bash
python scripts/dev/curate_runner_index.py
# Output: results/dev/runner_index_curation.json
```

---

## Tier B (Ops/Automation) — Startliste (bitte kuratieren)

Typische Kandidaten:
- `scripts/automation/*`
- `scripts/validate_*`
- `scripts/post_merge_*`
- CI/Release Helper

> Ergänze hier eure tatsächlichen Pfade nach Sichtung.

---

## Tier C (Utility/Dev/One-off) — Startliste (bitte kuratieren)

Typische Kandidaten:
- `scripts/dev/*`
- `scripts/scratch/*`
- einmalige Migrationen/Ad-hoc Tools

---

## Evidence Chain Readiness (P1 Mapping)

Für Tier A gilt langfristig als Minimum:
- `run_id` erzeugen
- `results/<run_id>/config_snapshot.*`
- `results/<run_id>/stats.json`
- `results/<run_id>/equity.csv`
- optional: `results/<run_id>/trades.parquet`

✅ Wenn ein Runner das erfüllt: **READY**
🟡 teilweise: **PARTIAL**
❌ noch nicht: **TODO**

### P1 Must Integrate First (Top 3)

Diese 3 Runner haben höchste Priority für Evidence Chain Integration:

1. **research_cli.py** (P1: MUST)
   - **Warum:** Zentrale Research-Entry mit 43 Docs-Referenzen, umfasst sweep/report/promote/walkforward/montecarlo Workflows
   - **Readiness:** PARTIAL (hat run_id, braucht results/ Integration)
   - **Impact:** Höchster ROI – alle Research-Workflows profitieren

2. **run_backtest.py** (P1: MUST)
   - **Warum:** Häufigster Backtest-Runner (22 Docs-Refs), bereits READY mit run_id + results/
   - **Readiness:** READY ✅
   - **Impact:** Template für andere Runner, sofort einsatzbereit

3. **live_ops.py** (P1: MUST)
   - **Warum:** Zentrale Live-Ops Entry (20 Docs-Refs), kritisch für Production/Testnet
   - **Readiness:** TODO (keine Evidence Chain)
   - **Impact:** Live-Operations Audit Trail, regulatorisch wichtig

**SHOULD-Priority:**
- **run_execution_session.py** (16 refs, PARTIAL) – Live-Execution, hoher Wert für Audit

---

## Wie man einen Runner zu Tier A hinzufügt

1) Der Runner wird in **Docs** und/oder **CI** referenziert.
2) Er hat stabile CLI-Args (mind. `--help`).
3) Er ist test-/smoke-fähig (kurze Laufzeit, deterministic wenn möglich).
4) Evidence Chain Plan ist definiert (READY/PARTIAL/TODO).

---

## Deprecation Policy

- Markiere Runner als `DEPRECATED` im Index + Doku.
- Behalte ihn mindestens 1 Release-Zyklus (oder N Wochen) drin.
- Entferne erst, wenn CI/Docs/Runbooks aktualisiert sind.


## Appendix: Signals (auto-extracted)

- **CI referenced scripts:**
  - `scripts/automation/run_offline_daily_suite.py scripts/automation/run_offline_weekly_suite.py scripts/automation/validate_all_pr_reports.sh scripts/ci/check_quarto_no_exec.sh scripts/generate_infostream_packet.py scripts/generate_market_outlook_daily.py scripts/ops/run_audit.sh scripts/run_policy_critic.py scripts/run_test_health_profile.py scripts/show_test_health_history.py scripts/strategy_smoke_check.py scripts/validate_pr_report_format.sh scripts/validate_rl_v0_1.sh `

- **Recently changed scripts (last 30 days, top 20):**
  - `scripts/research_cli.py scripts/run_stress_tests.py scripts/run_offline_trigger_training_drill_example.py scripts/run_live_dry_run_drills.py scripts/profile_research_and_portfolio.py scripts/live_operator_status.py scripts/generate_strategy_sweep_report.py scripts/generate_live_status_report.py scripts/run/run_regime_btcusdt_experiments.sh scripts/ops/run_audit.sh scripts/run_portfolio_backtest.py scripts/preview_live_portfolio.py scripts/automation/post_merge_verify.sh scripts/automation/generate_pr_report.sh scripts/view_r_and_d_experiments.py scripts/testnet_orchestrator_cli.py scripts/strategy_smoke_check.py scripts/utils/slice_from_backup.sh `
