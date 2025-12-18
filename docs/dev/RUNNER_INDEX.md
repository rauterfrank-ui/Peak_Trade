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

> Diese Liste ist initial automatisch aus Repo-Referenzen erzeugt (Docs/CI). Bitte nachprüfen und bei Bedarf anpassen.

| Shortname | Pfad | Zweck | Beispiel-Command | Evidence Chain Readiness |
|---|---|---|---|---|
| preview_live_portfolio.py  | `scripts/research_cli.py scripts/live_ops.py scripts/experiments_explorer.py scripts/run_test_health_profile.py scripts/run_backtest.py scripts/run_promotion_proposal_cycle.py scripts/run_execution_session.py scripts/run_strategy_sweep.py scripts/report_live_sessions.py scripts/testnet_orchestrator_cli.py scripts/run_offline_realtime_ma_crossover.py scripts/preview_live_portfolio.py ` | TBD | `python scripts/research_cli.py scripts/live_ops.py scripts/experiments_explorer.py scripts/run_test_health_profile.py scripts/run_backtest.py scripts/run_promotion_proposal_cycle.py scripts/run_execution_session.py scripts/run_strategy_sweep.py scripts/report_live_sessions.py scripts/testnet_orchestrator_cli.py scripts/run_offline_realtime_ma_crossover.py scripts/preview_live_portfolio.py  --help` | TBD |

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
  - `scripts/automation/run_offline_daily_suite.py scripts/automation/run_offline_weekly_suite.py scripts/automation/validate_all_pr_reports.sh scripts/ci/check_quarto_no_exec.sh scripts/generate_infostream_packet.py scripts/generate_market_outlook_daily.py scripts/run_audit.sh scripts/run_policy_critic.py scripts/run_test_health_profile.py scripts/show_test_health_history.py scripts/strategy_smoke_check.py scripts/validate_pr_report_format.sh scripts/validate_rl_v0_1.sh `

- **Recently changed scripts (last 30 days, top 20):**
  - `scripts/build_todo_board_html.py scripts/research_cli.py scripts/run_stress_tests.py scripts/run_offline_trigger_training_drill_example.py scripts/run_live_dry_run_drills.py scripts/profile_research_and_portfolio.py scripts/live_operator_status.py scripts/generate_strategy_sweep_report.py scripts/generate_live_status_report.py scripts/run_regime_btcusdt_experiments.sh scripts/run_audit.sh scripts/run_portfolio_backtest.py scripts/preview_live_portfolio.py scripts/inject_todo_board_shortcuts.py scripts/automation/post_merge_verify.sh scripts/automation/generate_pr_report.sh scripts/view_r_and_d_experiments.py scripts/testnet_orchestrator_cli.py scripts/strategy_smoke_check.py scripts/slice_from_backup.sh `
