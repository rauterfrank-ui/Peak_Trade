# Docs Audit Tracker (docs/**/*.md) — Doku ↔ Repo Abgleich

## Ziel
Alle Markdown-Dateien unter `docs/` werden **nach und nach** analysiert und mit dem **aktuellen Repo-Stand** abgeglichen.

- **Output pro Datei**: (a) was die Doku behauptet/contracted, (b) wo das im Code/Tests abgedeckt ist, (c) welche Gaps existieren, (d) konkrete ToDos.
- **Arbeitsweise**: wir arbeiten „step by step“ in Batches (z.B. Runbooks → Playbooks → Phase-Dokus → Guides → Rest).

---

## Status-Definitionen
- **done**: geprüft, Findings dokumentiert, keine offenen Gaps *oder* Gaps sind als ToDos erfasst.
- **needs_fix**: Gap gefunden, Fix nötig (Code/Tests/Doku).
- **unknown**: noch nicht geprüft.

---

## Bereits geprüft (bisherige Session)

### 1) `docs/PORTFOLIO_RECIPES_AND_PRESETS.md` — **done (vorläufig)**
- **Implementiert**:
  - `src/experiments/portfolio_recipes.py` (Loader + Validierung, inkl. `strategies` (Phase 53))
  - `config/portfolio_recipes.toml` (Recipes, inkl. Phase 53/75 Abschnitte)
  - `scripts/run_portfolio_robustness.py` (Preset-Loading + Override-Merge für sweep-basierte Rezepte)
  - Tests: `tests/test_portfolio_recipes.py`, `tests/test_research_cli_portfolio_presets.py`
- **Fix (applied)**:
  - Phase‑53-Recipes mit `strategies=[...]` laufen end-to-end im Portfolio-Runner (aktuell **offline-fähig via `--use-dummy-data`**).
- **Hinweis (Format-Envs)**:
  - `--format` ist nicht überall gleich: viele Runner nutzen `md|html|both`, einige Report-Generatoren nutzen `markdown|html|both` (z.B. Sweep-Report / Live-Status-Report).

### 2) `docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md` — **done (vorläufig)**
- **Fixes (applied)**:
  - Copy/Paste-Härtung: Commands auf `python3` umgestellt.
  - Token-Policy: illustrative Pfade in Inline-Code (`results/reports/...`) auf `&#47;` Encoding umgestellt.

### 3) `docs/PHASE_42_TOPN_PROMOTION.md` — **done (vorläufig)**
- **Fixes (applied)**:
  - Copy/Paste-Härtung: Commands auf `python3` umgestellt.
  - Tests: `.venv/bin/pytest ...` auf `python3 -m pytest ...` umgestellt.
  - Workflow-Skizze: `run_strategy_sweep.py` → `scripts/run_sweep.py` (korrekter Runner).

### 4) `docs/PHASE_41B_STRATEGY_ROBUSTNESS_AND_TIERING.md` — **done (vorläufig)**
- **Fixes (applied)**:
  - Copy/Paste-Härtung: Commands auf `python3` umgestellt.
  - Tests: `pytest ...` auf `python3 -m pytest ...` umgestellt.

### 5) `docs/KNOWLEDGE_SOURCES_REGISTRY.md` — **done (vorläufig)**
- **Befund**:
  - Eher Registry/Prozessdoku, kein harter Runtime-Contract. Später prüfen: ob erwähnte Ingestion-Skripte real/illustrativ sind.

### 6) `docs/KNOWLEDGE_BASE_INDEX.md` — **done (vorläufig)**
- **Fixes (applied)**:
  - Quick-Reference „Common Commands“: `python` → `python3` (copy/paste-robust).

### 7) `docs/Peak_Trade_Research_Strategy_Roadmap_2025-12-07.md` — **done (vorläufig)**
- **Fixes (applied)**:
  - Lesbarkeit/Encoding: kaputte Sonderzeichen (`�`) und Range-Control-Chars (`13`, etc.) bereinigt, inhaltlich unverändert.

### 8) Batch 4: Live Ops / Readiness / Gating — **done (vorläufig)**
- `docs/PHASE_51_LIVE_OPS_CLI.md`
  - **Fixes (applied)**: `python` → `python3`, `pytest ...` → `python3 -m pytest ...` (copy/paste-robust).
- `docs/LIVE_STATUS_REPORTS.md`
  - **Fixes (applied)**: `python` → `python3`; Token-Policy-konforme Inline-Code Pfade (z.B. `scripts&#47;...`) in data-source bullets.
- `docs/PHASE_83_LIVE_GATING_AND_RISK_POLICIES.md`
  - **Fixes (applied)**: `python -c` → `python3 -c`; Tests auf `python3 -m pytest ...`.
- `docs/PHASE_82_LIVE_TRACK_DASHBOARD.md`
  - **Fixes (applied)**: Tests auf `python3 -m pytest ...`; Token-Policy: Inline-Code `" / "` → `" &#47; "`.
- `docs/LIVE_RISK_LIMITS.md`
  - **Fixes (applied)**: Referenzen auf `config.toml` → `config/config.toml`; CLI-Beispiele auf `python3 ...`; Token-Policy: `true/false` → `true&#47;false`.
- `docs/LIVE_READINESS_CHECKLISTS.md`
  - **Fixes (applied)**: Token-Policy: `python3 -m pytest tests&#47; -v` (Slash-Encoding für illustrative Pfade); Config-Referenzen auf `config/config.toml`.

### 9) Batch 5: Incident / Kill Switch / Rollback — **done (vorläufig)**
- `docs/INCIDENT_SIMULATION_AND_DRILLS.md`
  - **Fixes (applied)**: alle `python scripts/...` Commands auf `python3 scripts/...` umgestellt (copy/paste-robust).
- `docs/runbooks/KILL_SWITCH_DRILL_PROCEDURE.md`
  - **Fixes (applied)**: `python -m ...` auf `python3 -m ...` umgestellt (Status/Trigger/Recover/History).
- `docs/runbooks/ROLLBACK_PROCEDURE.md`
  - **Fixes (applied)**: `python` → `python3` für Kill-Switch CLI (`-m ...`) und Repo-Scripts (`scripts/live/*`, `scripts/ops/*`).

### 10) Batch 6: Observability / WebUI / Dashboard — **done (vorläufig)**
- `docs/PHASE_84_OPERATOR_DASHBOARD.md`
  - **Fixes (applied)**: `python` → `python3`, `python -c` → `python3 -c`, `pytest ...` → `python3 -m pytest ...`.
- `docs/webui/LIVE_STATUS_PANELS.md`
  - **Fixes (applied)**: `python ...` → `python3 ...`.
- `docs/webui/DASHBOARD_OVERVIEW.md`
  - **Fixes (applied)**: `python scripts/run_web_dashboard.py`/`python scripts/live_web_server.py ...` → `python3 ...`.

### 11) Batch 7: Execution / Alerts / Shadow Execution — **done (vorläufig)**
- `docs/runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md`
  - **Fixes (applied)**: `python` → `python3` (Commands & `python -c`), `pytest` → `python3 -m pytest`.
- `docs/PHASE_24_SHADOW_EXECUTION.md`
  - **Fixes (applied)**: CLI-Commands auf `python3`; Config-Referenzen auf `config/config.toml`.
- `docs/PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md`
  - **Fixes (applied)**: Examples/Tests auf `python3`/`python3 -m pytest`.
- `docs/PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md`
  - **Fixes (applied)**: Troubleshooting/Tests auf `python3`/`python3 -m pytest`.
- `docs/execution/EXECUTION_SIMPLE_V1.md`
  - **Fixes (applied)**: `load_config("config/config.toml")`; Tests auf `python3 -m pytest`.

### 12) Batch 8: Exchange/Testnet/Execution Telemetry — **done (vorläufig)**
- `docs/PHASE_35_TESTNET_EXCHANGE_INTEGRATION.md`
  - **Fixes (applied)**: Tests auf `python3 -m pytest ...`.
- `docs/PHASE_38_EXCHANGE_V0_TESTNET.md`
  - **Fixes (applied)**: Tests auf `python3 -m pytest ...`; Token-Policy: `tests&#47;test_exchange_*.py` in Inline-Code.
- `docs/execution/EXECUTION_TELEMETRY_LIVE_TRACK_V1.md`
  - **Fixes (applied)**: Tests auf `python3 -m pytest ...`.
- `docs/ops/EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md`
  - **Fixes (applied)**: Diagnostic commands auf `python3` (inkl. `python3 -c`), copy/paste-robust.

### 13) Batch 9: Execution — Replay Pack / Recon / Telemetry Viewer / Ledger — **done (vorläufig)**
- `docs/execution/REPLAY_PACK_VNEXT.md`
  - **Fixes (applied)**: `python` → `python3` für ReplayPack CLI Beispiele.
- `docs/execution/DETERMINISTIC_REPLAY_PACK.md`
  - **Fixes (applied)**: `python` → `python3` in allen ReplayPack CLI Examples (build/validate/replay/resolve/compare).
- `docs/execution/RUNBOOK_RECON_DIFFS.md`
  - **Fixes (applied)**: `python` → `python3` inkl. `python3 -c` (Quickstart + Quick Commands).
- `docs/execution/TELEMETRY_VIEWER.md`
  - **Fixes (applied)**: `python` → `python3` in CLI/ops snippets (Viewer + session runner).
- `docs/execution/LEDGER_SLICE2.md`
  - **Fixes (applied)**: `pytest ...` → `python3 -m pytest ...`.
- `docs/execution/phase4/WP4A_LIVE_READINESS_GOVERNANCE_LOCK_PACKET.md`
  - **Fixes (applied)**: Gate- und Evidence-Commands auf `python3 -m pytest` + Report-Commands auf `python3`.

---

## Nächste Batch (Start)
**Runbooks / Frontdoor / Ops** (Priorität: operational & viele Quer-Verweise)
- `docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`
- `docs/WORKFLOW_FRONTDOOR.md`
- `docs/RUNBOOK_TO_FINISH_MASTER.md`
- `docs/ops/runbooks/README.md`
- `docs/ops/runbooks/RUNBOOK_TO_FINISH_MASTER.md` (falls abweichend)

---

## Offene Top-Gaps (Priorisierung)
1) **Phase‑53 `strategies` in Portfolio-Runner end-to-end** (Preset → Portfolio-Build → Robustness/Report)
2) **Doku/CLI Value-Mismatches** (v.a. `--format` Enum: `md` vs `markdown` je nach CLI)

---

## Runbooks/Frontdoor Batch — Findings (laufend)

### `docs/RUNBOOKS_AND_INCIDENT_HANDLING.md` — **needs_fix → teilweise gefixt**
- **Gefundene Mismatches (fix applied)**:
  - `scripts/experiments_explorer.py` benötigt einen Subcommand, z.B. `list` (statt direkte Flags ohne Subcommand).
  - `scripts/report_experiment.py` verwendet `--id` (nicht `--run-id`).
- **Status**:
  - Commands im Abschnitt „Ergebnisse prüfen“ wurden korrigiert (doc-only).

### `docs/WORKFLOW_FRONTDOOR.md` — **done (navigation only)**
- **Befund**:
  - Referenzierte Ziele (Runbook Overview, Ops README, Runbooks Landscape, etc.) existieren im Repo.

### `docs/RUNBOOK_TO_FINISH_MASTER.md` und `docs/ops/runbooks/RUNBOOK_TO_FINISH_MASTER.md` — **done (docs-only runbook)**
- **Befund**:
  - Referenzierte Runbooks/Targets existieren (D2/D3/D4, Finish-C pointer, Option-B Pfade, etc.).

---

## Implementierte Fixes (Code)

### Phase‑53 `strategies`‑Presets in Portfolio-Robustness — **done (v1, dummy-returns)**
- **Implementiert in**: `scripts/run_portfolio_robustness.py`
- **Verhalten**:
  - Wenn ein Preset `strategies = [...]` definiert, wird das Portfolio aus diesen Komponenten gebaut (ohne Sweep/Top‑N).
  - Aktuell ist dafür **`--use-dummy-data` erforderlich** (offline-fähig; data-backed Returns-Loader ist noch offen).
- **Test**:
  - `tests/test_research_cli_portfolio_presets.py` (neuer Test: strategies-mode nutzt nicht `load_top_n_configs_for_sweep`)

## Batch 2 (Phase-/Research/Portfolio) — Status
- `docs/PHASE_47_PORTFOLIO_ROBUSTNESS_AND_STRESS_TESTING.md`: aktualisiert um Phase‑53 `strategies`-Pfad + Hinweis auf `--use-dummy-data` + Beispielkommando.

### Batch 2 (Phase Docs) — Quick Audit Ergebnis (vorläufig done)
- `docs/PHASE_41_STRATEGY_SWEEPS_AND_RESEARCH_PLAYGROUND.md`: ✅ Beispiele matchen `scripts/run_strategy_sweep.py` + `scripts/generate_strategy_sweep_report.py` (inkl. `--format markdown|html|both`, Output mit Timestamp).
- `docs/PHASE_43_VISUALIZATION_AND_SWEEP_DASHBOARDS.md`: ✅ CLI/Flags matchen `scripts/generate_strategy_sweep_report.py` (`--with-plots`, `--plot-metric`, `--format markdown|html|both`).
- `docs/PHASE_44_WALKFORWARD_TESTING.md`: ✅ Runner/Flags matchen `scripts/run_walkforward_backtest.py` (inkl. Output-Pfade).
- `docs/PHASE_45_MONTE_CARLO_ROBUSTNESS_AND_STRESS_TESTS.md`: ✅ Runner/Flags + Output-Struktur matchen `scripts/run_monte_carlo_robustness.py` + `src/reporting/monte_carlo_report.py`.
- `docs/PHASE_46_STRESS_TESTS_AND_CRASH_SCENARIOS.md`: ✅ Runner/Flags + Output-Struktur matchen `scripts/run_stress_tests.py`.

---

## Batch 3 (Research Playbooks) — Findings (laufend)

### `docs/PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md` — **needs_fix → teilweise gefixt**
- **Fixes (applied)**:
  - Stress-/Pipeline-Beispiele nutzen jetzt implementierte Stress-Szenarien (`single_crash_bar`, `vol_spike`, `drawdown_extension`) statt nicht vorhandener (`flash_crash`, `high_volatility`, `trend_reversal`).
  - `preview_live_portfolio.py` wird korrekt als Snapshot/Risk-Check per `--config`/`--no-risk` dokumentiert (kein `--portfolio-preset`/`--validate-only`).
  - Strategy-Profile: Umgestellt auf `research_cli.py strategy-profile` (statt `profile_research_and_portfolio.py`, das ein Benchmark-Tool ist).
  - Strategy Registry Snippet: auf `StrategySpec`/`_STRATEGY_REGISTRY` angepasst; Listing nutzt `get_available_strategy_keys()`.
  - Erwartete Output-Pfade im Sweep/Report korrigiert (`reports/experiments/`, `reports/sweeps/{sweep}_report_<timestamp>.*`).

### `docs/STRATEGY_RESEARCH_PLAYBOOK.md` — **done (quick audit)**
- **Befund**:
  - Referenzierte Scripts existieren (`research_run_strategy.py`, `research_compare_strategies.py`, `list_experiments.py`, `show_experiment.py`) und die verwendeten Flags matchen die Parser.

### `docs/EXPERIMENT_EXPLORER.md` — **done (quick audit)**
- **Befund**:
  - CLI-Beispiele nutzen korrekte Subcommands (`list`, `top`, `details`, etc.) und matchen `scripts/experiments_explorer.py`.

---

## Batch 4 (Portfolio/Tiering) — Findings (laufend)

### `docs/PHASE_80_TIERED_PORTFOLIO_PRESETS.md` — **done (vorläufig)**
- **Fixes (applied)**:
  - Doku ergänzt: `stress_scenarios` müssen zu `src/experiments/stress_tests.py` passen.
  - Preset-/Recipe-Konfigs bereinigt: alte Scenario-Namen entfernt (z.B. `flash_crash`, `high_volatility`, `trend_reversal`, `liquidity_gap`) zugunsten der implementierten (`single_crash_bar`, `vol_spike`, `drawdown_extension`, `gap_down_open`).

### `scripts/run_research_golden_path.py` — **fix (high impact)**
- **Fixes (applied)**:
  - Pipeline-Flags aktualisiert (`--walkforward-train-window/--walkforward-test-window`).
  - Stress-Szenarien auf implementierte Typen umgestellt (`single_crash_bar`, `vol_spike`, `drawdown_extension`, `gap_down_open`).
  - Strategy-Profile Schritt nutzt `research_cli.py strategy-profile` (statt Benchmark-Tool `profile_research_and_portfolio.py`).
  - Portfolio-Golden-Path nutzt `--use-dummy-data` für preset-basierte (Phase‑53/Phase‑80) `strategies=[...]` Presets.
  - Output-Pfad-Hinweis im Log korrigiert (`reports/portfolio_robustness/{preset}/portfolio_robustness_report.html`).

### `docs/PHASE_86_RESEARCH_V1_FREEZE.md` — **fix (CLI drift)**
- **Fixes (applied)**:
  - Quick-Reference: Golden-Path Invocation auf echtes Interface umgestellt.
  - Stress-Szenarien in Pipeline auf implementierte Typen umgestellt.
  - Tiered-Preset Robustness Call ergänzt um `--use-dummy-data`.

### `docs/CASE_STUDY_REGIME_BTCUSDT_V1.md` — **fix (CLI drift)**
- **Fixes (applied)**:
  - `run_stress_tests.py` Beispiel auf echte Flags/Scenarios umgestellt (`--scenarios single_crash_bar vol_spike`, kein `--scenario/--output`).

### `docs/PHASE_82_RESEARCH_QA_AND_SCENARIOS.md` — **fix (Konzept-/CLI-Alignment)**
- **Fixes (applied)**:
  - Klarstellung: Scenario-Library (`config/scenarios/*.toml`) ist für QA/E2E/Regressions-Checks; Stress-Tests (Phase 46) nutzen eigene Scenario-Typen (`single_crash_bar`, `vol_spike`, `drawdown_extension`, `gap_down_open`).
  - CLI-Beispiel entsprechend korrigiert (kein `flash_crash` als `research_cli.py stress --scenarios`).

### Risk-Layer Dokus — **fix (Begriffsabgrenzung)**
- **Fixes (applied)**:
  - `docs/risk/RISK_LAYER_V1_OPERATOR_GUIDE.md`: Abgrenzungs-Block zwischen Risk-Layer Stress (`src/risk/stress.py`), Research Stress-Tests (Phase 46/47) und Scenario-Library (Phase 82) ergänzt.
  - `docs/risk/RISK_LAYER_V1_IMPLEMENTATION_REPORT.md`: Hinweis zur Namensüberschneidung/Trennung ergänzt.
  - `docs/risk/roadmaps/PORTFOLIO_VAR_ROADMAP.md`: Stress-Testing Bullet eindeutig auf `src/risk/stress.py` referenziert.
  - `docs/risk/roadmaps/RISK_LAYER_ROADMAP.md`: Verweis auf nicht existente `src/risk/scenarios/*.yaml` als Konzeptbeispiel markiert + Trennhinweis ergänzt.

### `docs/PEAK_TRADE_COMPLETE_OVERVIEW_2025-12-07.md` — **fix (CLI drift, high impact)**
- **Fixes (applied)**:
  - Beispiele auf existierende CLIs umgestellt (`research_run_strategy.py`, `run_strategy_sweep.py --sweep-name`, korrekte Portfolio-Robustness Flags).
  - `--config` bei `generate_live_status_report.py` ergänzt.
  - Preset-basierte Portfolio-Calls mit `--use-dummy-data` ergänzt (strategies-basierte Presets).

### `docs/KNOWLEDGE_BASE_INDEX.md` — **fix (CLI completeness)**
- **Fixes (applied)**:
  - Live-Status-Report Beispiel um `--config`, `--output-dir`, `--tag` ergänzt (damit es copy/paste-fähig ist).

### `docs/R_AND_D_OPERATOR_FLOW.md` — **fix (CLI drift)**
- **Fixes (applied)**:
  - Nicht existierenden `research_cli.py run-batch` Subcommand entfernt → Batch-Läufe als Shell-Loop über `run-experiment` dokumentiert.

### `docs/PHASE_75_STRATEGY_LIBRARY_V1_1.md` — **fix (Sweep CLI drift)**
- **Fixes (applied)**:
  - Sweep-Ausführung auf `scripts/run_sweep.py --grid config/sweeps/*.toml` umgestellt (statt `run_strategy_sweep.py --sweep-config ...`).

### `docs/CASE_STUDY_REGIME_BTCUSDT_V1.md` — **fix (CLI drift)**
- **Fixes (applied)**:
  - Pipeline-Beispiel: `--mc-simulations` → `--mc-num-runs`, entferntes `--output` Flag.

### `docs/LIVE_DEPLOYMENT_PLAYBOOK.md` — **fix (run_sweep CLI drift)**
- **Fixes (applied)**:
  - `run_sweep.py` Beispiel: falsches `--config config/sweeps/...` ersetzt durch korrektes `--grid config/sweeps/...` + explizite Basis-Config (`--config config/config.toml`).

### `scripts/run_sweep.py` + `scripts/run_market_scan.py` + `docs/SWEEPS_MARKET_SCANS.md` — **fix (Default-Config Konsistenz)**
- **Fixes (applied)**:
  - Default-Config-Pfad für `run_sweep.py` und `run_market_scan.py` auf `config/config.toml` vereinheitlicht.
  - `docs/SWEEPS_MARKET_SCANS.md` Beispiele auf `--config config/config.toml` ergänzt (copy/paste-fähig).

### `docs/AUTO_PORTFOLIOS.md` — **fix (Sweep examples)**
- **Fixes (applied)**:
  - `run_sweep.py` Beispiele um `--config config/config.toml` ergänzt (konsistent, copy/paste-fähig).

### `docs/CLI_CHEATSHEET.md` + `docs/PEAK_TRADE_PROJECT_SUMMARY_CURRENT_2026-01-27.md` — **fix (run_sweep examples)**
- **Fixes (applied)**:
  - `run_sweep.py` Beispiele um `--config config/config.toml` ergänzt (copy/paste-fähig).

### `docs/CLI_CHEATSHEET.md` + `docs/SWEEPS_MARKET_SCANS.md` — **fix (run_market_scan examples)**
- **Fixes (applied)**:
  - `run_market_scan.py` Beispiele um `--config config/config.toml` ergänzt (copy/paste-fähig).

### Docs Reference Targets Gate — **grün**
- **Fixes (applied)**:
  - Links auf `scripts/generate_live_status_report.py` so angepasst, dass der Docs-Reference-Targets Check sie akzeptiert (keine `../scripts/...` Link-Targets mehr).
  - Verifikation: `scripts/ops/verify_docs_reference_targets.sh` läuft grün.

### Docs Links: Outside-Repo-Tree Targets — **bereinigt**
- **Fixes (applied)**:
  - `../scripts/*`, `../src/*`, `../config/*` Links in Docs auf **Text/Code-Referenzen** umgestellt (z.B. `src/...`, `config/...`, `scripts/...`), damit Doku-Links nicht an Tree-Grenzen hängen.
  - Verifikation: `scripts/ops/verify_docs_reference_targets.sh` läuft weiterhin grün.

### CLI Copy/Paste: Config-Pfad vereinheitlicht — **bereinigt**
- **Fixes (applied)**:
  - Alle verbleibenden Doku-Commands mit `--config config.toml` auf `--config config/config.toml` umgestellt (Setup/Install/Runbooks/Worklogs), um Copy/Paste mit dem Repo-SSoT zu garantieren.
  - Verifikation: `scripts/ops/verify_docs_reference_targets.sh` läuft weiterhin grün.

### Reference Scenario + Decision Log — **aktualisiert**
- **Fixes (applied)**:
  - `docs/REFERENCE_SCENARIO_MULTI_STYLE_MODERATE.md`: Verweis auf den Decision Log als interner Doc-Link (`PORTFOLIO_DECISION_LOG.md`) statt als reiner Pfad-Text.
  - `docs/PORTFOLIO_DECISION_LOG.md`: „Copy/Paste“-Sektion ergänzt mit korrekten Report-Commands und expliziter `--format`-Enum-Abgrenzung (Research CLI vs Live Status Report).
  - Verifikation: `scripts/ops/verify_docs_reference_targets.sh` läuft weiterhin grün.

### Format-Enums: `md` vs `markdown` — **validiert**
- **Ergebnis**:
  - Keine Docs-Commands gefunden, die `research_cli.py` / `run_portfolio_robustness.py` mit `--format markdown` verwenden (wäre falsch; dort gilt `md|html|both`).
  - Verbleibende `--format markdown` Stellen sind bewusst bei Scripts, die `choices=["markdown","html","both"]` nutzen (z.B. `generate_live_status_report.py`, `generate_strategy_sweep_report.py`).
  - Verifikation: `scripts/ops/verify_docs_reference_targets.sh` läuft weiterhin grün.

### Python-Binary: `python` vs `python3` — **robuster Einstieg**
- **Fixes (applied)**:
  - `docs/GETTING_STARTED.md`: Version-Check und venv-Erstellung auf `python3` umgestellt (mit Hinweis, dass `python` auch okay ist, falls vorhanden).
  - `docs/CLI_CHEATSHEET.md`: kurzer Hinweis ergänzt („falls `python` fehlt → `python3`“).
  - `docs/PEAK_TRADE_COMPLETE_OVERVIEW_2025-12-07.md`: Quickstart-venv-Erstellung auf `python3 -m venv` umgestellt.
  - `docs/ops/README.md`: `python --version` als kommentierter Fallback belassen, primär `python3 --version`.
  - `docs/ops/KILL_SWITCH_TROUBLESHOOTING.md`: `python --version` aus Diagnose entfernt (pyenv-Fall), `python3 --version` bleibt.
  - `docs/ops/runbooks/RUNBOOK_OPERATOR_DASHBOARD_WATCH_ONLY_START_TO_FINISH.md`: `python3 -m venv` statt `python -m venv`.
  - `docs/ops/_archive/installation_roadmap/..._ORIGINAL.md`: python checks/venv auf `python3` umgestellt.
  - Verifikation: `scripts/ops/verify_docs_reference_targets.sh` läuft weiterhin grün.

### Runbooks/ops: „non-existent script refs“ — **reduziert (High-Impact)**
- **Fixes (applied)**:
  - `docs/runbooks/LIVE_MODE_TRANSITION_RUNBOOK.md`: fehlende `scripts/live/*.py` Commands auf existierende CLIs/Skripte umgestellt (insb. `live_ops.py`, `run_live_dry_run_drills.py`, `test_bounded_live_limits.py`) und fehlende Runner explizit als „nicht im Repo“ markiert.
  - `docs/runbooks/KILL_SWITCH_DRILL_PROCEDURE.md`: fehlendes `start_shadow_session.py` entfernt/ersetzt durch `run_live_dry_run_drills.py` bzw. Kill-Switch-Status-Checks; Session-Integration als „TBD“ markiert.
  - `docs/runbooks/ROLLBACK_PROCEDURE.md`: `show_positions.py`/`start_shadow_session.py`/`verify_shadow_mode.py` durch `live_ops.py` Snapshots + Dry-Run Drills ersetzt (keine Phantom-CLIs mehr).
  - `docs/runbooks/OFFLINE_REALTIME_PIPELINE_RUNBOOK_V1.md`: optionales Meta-Report-Script als nicht vorhanden gekennzeichnet; Workaround (Listing von `summary.json`) angegeben; Gate-kompatibel formuliert.
  - `docs/ops/Peak_Trade_TOOLING_AND_EVIDENCE_CHAIN_RUNBOOK.md`: „Lake“-Beispiele von nicht existenten `scripts/query_lake.py`/`build_lake_from_results.py` auf `src/data/lake/client.py` (DuckDB LakeClient) umgestellt.
  - `docs/ops/OPS_SCRIPT_TEMPLATE_GUIDE.md`: Beispiel-Command von nicht existenter `scripts/generate_report.py` auf existentes Script (`generate_live_status_report.py --help`) umgestellt.
  - `docs/ops/WAVE3_MERGE_READINESS_MATRIX.md`: Hinweis auf nicht existentes `scripts/ci/check_docs_reference_targets.py` ersetzt durch `scripts/ops/verify_docs_reference_targets.sh`.
  - `docs/ops/WP5A_PHASE5_NO_LIVE_DRILL_PACK.md`: Phantom-Commands (`health_check.py`, `test_data_feed.py`) durch existierende, read-only Checks ersetzt (`live_ops.py health`, `inspect_exchange.py status/ohlcv`) inkl. `--config config/config.toml`.
  - `docs/ops/runbooks/finish_c/RUNBOOK_FINISH_C_MASTER.md`: kommentierte Verweise auf nicht existierende `check_docs_*` Scripts ersetzt durch echte Gate-Commands (`validate_docs_token_policy.py`, `verify_docs_reference_targets.sh`).
  - Verifikation: `scripts/ops/verify_docs_reference_targets.sh` läuft weiterhin grün.

### Docs Gates Runbooks: illustrative Inline-Tokens — **neutralisiert**
- **Fixes (applied)**:
  - `docs/ops/runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md`: illustrative `scripts/example.py` „Before“-Beispiele mit `<!-- pt:ref-target-ignore -->` markiert (damit sie nicht als realer Target-Treffer zählen, aber als „Before“ lesbar bleiben).
  - `docs/ops/runbooks/RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md`: dito (`scripts/example.py` + „Change: scripts/old_name.py …“) mit `<!-- pt:ref-target-ignore -->`.
  - `docs/ops/runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md`: illustrative `scripts/old_name.py` / `scripts/helper.py` innerhalb von Log-/Command-Beispielen auf `scripts&#47;...` neutralisiert (und „Before/After“ für Encoding klar gemacht).
  - `docs/ops/runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_FALSE_POSITIVES.md`: illustrative `scripts/run_walkforward.py` im Log-Beispiel auf `scripts&#47;...` neutralisiert; „Before“-Inline-Commands mit `<!-- pt:ref-target-ignore -->` markiert.
  - `docs/ops/PR_691_MERGE_LOG.md`: „Initial Failure“-Block auf `scripts&#47;...` neutralisiert (weil hier die CI-Log-Ausgabe als Beispiel zitiert wird).
  - `docs/runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md`: fehlendes `smoke_test_paper.py` als Beispiel markiert und gate-sicher neutralisiert (`scripts&#47;...`).
  - `docs/runbooks/OFFLINE_TRIGGER_TRAINING_DRILL_V1.md`: fehlendes `run_offline_paper_drill_with_reports.py` durch vorhandenes `run_offline_trigger_training_drill_example.py` ersetzt.
  - `docs/ops/WAVE3_QUICKSTART.md`: fehlendes `run_live.py` als Beispiel markiert und gate-sicher neutralisiert (`scripts&#47;...`).
  - `docs/ops/runbooks/RUNBOOK_POINTER_PATTERN_OPERATIONS.md`: exemplarisches `python scripts/run.py` auf reales Beispiel `python3 scripts/run_backtest.py` umgestellt.
  - `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md`: Policy-Critic-Call auf reales `python3 scripts/run_policy_critic.py --pr-mode` umgestellt.
  - `docs/ops/workflows/WORKFLOW_NOTES_FRONTDOOR.md`: Log-Beispiel `scripts/my_script.py` auf `scripts&#47;...` neutralisiert.
  - `docs/ops/runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE.md`: „Violation“-Fenced-Blocks auf `scripts&#47;example.py` umgestellt (damit auch in Raw-Scans keine Phantom-Targets entstehen).
  - Archive/Logs: `DOCS_GATES_OPERATOR_PACK_V1_1_*` und `PR_703_MERGE_LOG.md` „Before“-Tokens mit `<!-- pt:ref-target-ignore -->` markiert.
  - Verifikation: `scripts/ops/verify_docs_reference_targets.sh` läuft weiterhin grün.
