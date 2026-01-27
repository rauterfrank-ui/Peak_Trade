# Peak_Trade — Projekt-Zusammenfassung (Ist-Stand)

**Stand:** 2026-01-27  
**Workspace:** `/Users/frnkhrz/Peak_Trade`  
**Repo:** rauterfrank-ui/Peak_Trade (GitHub)  
**Branch/SHA:** `main` @ `06dff918`  
**Tracked Files:** 2915  

## Purpose & Audience
Zweck: **Repo-Einstieg**, **CI/Gates Index**, **Governance/Safety-Vertrag** und **Output/Artefakt-Landkarte** – mit **prüfbaren Referenzen** (keine Spekulation).

**Personas (Jump links):**
- **Developer** → [Start Here](#start-here-by-persona)
- **Operator (Ops)** → [CI & Gates Matrix](#9-ci--gates-matrix) · [Outputs & Artefacts](#outputs--artefacts-landkarte)
- **Research/Quant** → [Happy Paths](#10-happy-paths-typische-nutzung) · [Outputs & Artefacts](#outputs--artefacts-landkarte)
- **Audit/Reviewer** → [Governance/Safety Vertrag](#8-governance--safety-vertrag-non-negotiables) · [Glossar](#glossary--conventions)

**Non-Goals:**
- Kein vollständiges Runbook (dafür: Runbook-Index im Ops Hub).
- Keine Spekulation in „Known gaps“: nur belegbare Items (Docs/TODOs/Runbooks).

---

## Inhaltsverzeichnis
- [Quick Links (One-Page)](#quick-links-one-page)
- [Start Here (by persona)](#start-here-by-persona)
- [1) Kurzbeschreibung](#1-kurzbeschreibung)
- [2) GitHub/Repo-Umfeld (inkl. Schutzmechanismen)](#2-githubrepo-umfeld-inkl-schutzmechanismen)
- [3) System Map (Mermaid)](#3-system-map-mermaid)
- [4) Architektur (High-Level)](#4-architektur-high-level)
- [5) Codebase-Layer (Auszug der wichtigsten Bereiche)](#5-codebase-layer-auszug-der-wichtigsten-bereiche)
- [6) Config Map (SSoT)](#6-config-map-ssot)
- [7) Risk & Safety (Defense in Depth)](#7-risk--safety-defense-in-depth)
- [8) Governance & Safety Vertrag (Non-Negotiables)](#8-governance--safety-vertrag-non-negotiables)
- [9) CI & Gates Matrix](#9-ci--gates-matrix)
- [9a) Change Impact Map (Pfad → Gates/Owner/Approval)](#9a-change-impact-map-pfad--gatesownerapproval)
- [10) Happy Paths (typische Nutzung)](#10-happy-paths-typische-nutzung)
- [11) Ops, Runbooks, Evidence](#11-ops-runbooks-evidence-betriebs-ökosystem)
- [Outputs & Artefacts (Landkarte)](#outputs--artefacts-landkarte)
- [Toolchain Standard & Common Pitfalls](#toolchain-standard--common-pitfalls)
- [Stability/Readiness Table](#stabilityreadiness-table)
- [Known gaps (documented only) + Next steps](#known-gaps-documented-only--next-steps)
- [FAQ / Troubleshooting (Top 10)](#faq--troubleshooting-top-10)
- [Glossary & Conventions](#glossary--conventions)

---

## Quick Links (One-Page)

**Frontdoors:**
- [../README.md](../README.md)
- [PEAK_TRADE_OVERVIEW.md](PEAK_TRADE_OVERVIEW.md)
- [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)
- [../WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md](../WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md)
- Ops Hub: [ops/README.md](ops/README.md)

**Key run flows:**
- Docs Gates Snapshot (vor PRs): `./scripts/ops/pt_docs_gates_snapshot.sh --changed`
- Evidence: Index [ops/EVIDENCE_INDEX.md](ops/EVIDENCE_INDEX.md) · Merge Logs `docs&#47;ops&#47;merge_logs&#47;`

---

## Start Here (by persona)

### Developer
- **Frontdoor**: [../README.md](../README.md)
- **Architektur**: [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) · [PEAK_TRADE_OVERVIEW.md](PEAK_TRADE_OVERVIEW.md)
- **Dev Guides**: z.B. `DEV_GUIDE_ADD_STRATEGY.md`, `DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md` (in `docs/`)
- **Local repro (kurz)**:

```bash
python3 -m pytest -q
ruff check src/ tests/ scripts/
ruff format --check src/ tests/ scripts/
```

### Operator (Ops)
- **Ops Hub**: [ops/README.md](ops/README.md)
- **Required Checks Snapshot**: [ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md](ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md)
- **Docs Gates Quickstart**: [ops/runbooks/RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md](ops/runbooks/RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md)
- **Local repro (Docs Gates, PR-Workflow)**:

```bash
./scripts/ops/pt_docs_gates_snapshot.sh --changed
bash scripts/ops/verify_docs_reference_targets.sh
python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_required_checks_drift.sh
```

### Research/Quant
- **CLI Einstieg**: [CLI_CHEATSHEET.md](CLI_CHEATSHEET.md)
- **Research → Live Playbook**: [PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md)
- **Live-/Testnet Track Status**: [LIVE_TESTNET_TRACK_STATUS.md](LIVE_TESTNET_TRACK_STATUS.md)
- **Local repro (Research, kurz – Details siehe Links oben):**

```bash
# 1) Einzel-Backtest (Beispiel aus CLI Cheatsheet)
python scripts/run_backtest.py --strategy ma_crossover --symbol BTC/EUR

# 2) Parameter-Sweep (TOML-Grid, optional dry-run)
python scripts/run_sweep.py --strategy ma_crossover --symbol BTC/EUR --grid config/sweeps/ma_crossover.toml --dry-run

# 3) Portfolio-Research (Playbook Phase 54)
python scripts/research_cli.py portfolio --config config/config.toml --portfolio-preset rsi_reversion_conservative --format both

# 4) Research-Pipeline v2 (Playbook Phase 54; Parameter/Name anpassen)
python scripts/research_cli.py pipeline --sweep-name rsi_reversion_basic --config config/config.toml --format both --top-n 5

# 5) Reporting (Beispiel: Backtest-Report Generator)
python scripts/generate_backtest_report.py --help
```

### Audit/Reviewer
- **Governance Overview**: [GOVERNANCE_AND_SAFETY_OVERVIEW.md](GOVERNANCE_AND_SAFETY_OVERVIEW.md)
- **AI Autonomy Go/No-Go (Policy Doc)**: [governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md)
- **Execution Governance Runbook**: [runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md](runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md)
- **Evidence Index**: [ops/EVIDENCE_INDEX.md](ops/EVIDENCE_INDEX.md) · **Schema**: [ops/EVIDENCE_SCHEMA.md](ops/EVIDENCE_SCHEMA.md)
- **Local repro (Audit, kurz – read-only / docs-only):**

```bash
# Docs Integrity (vor PRs)
./scripts/ops/pt_docs_gates_snapshot.sh --changed
bash scripts/ops/verify_docs_reference_targets.sh
python scripts/ops/validate_docs_token_policy.py --tracked-docs

# Branch protection drift / hygiene (SSoT vs Workflows)
bash scripts/ops/verify_required_checks_drift.sh
python scripts/ci/validate_required_checks_hygiene.py --config config/ci/required_status_checks.json --workflows .github/workflows --strict

# Evidence Pack Gate (Smoke + Validator; schreibt nur in .artifacts/)
python scripts/run_layer_smoke_with_evidence_pack.py --layer L0 --autonomy REC --verbose
python scripts/validate_evidence_pack_ci.py --root .artifacts/evidence_packs --strict --verbose
```

---

## 1) Kurzbeschreibung

**Peak_Trade** ist ein modulares, research-getriebenes Trading-Framework (Python ≥ 3.9) für Krypto-Strategien mit konsequentem **Safety-First-/Governance-First**-Ansatz.

Kernidee: **Research → Evidenz → (Shadow/Paper/Testnet) → erst dann Live**, mit mehreren technischen und prozessualen Schutzschichten (Defense-in-Depth).

**Wichtige Einstiege:**
- [../README.md](../README.md) (Frontdoor, Quickstart, zentrale Links)
- [PEAK_TRADE_OVERVIEW.md](PEAK_TRADE_OVERVIEW.md) (Architektur-Map + Extensibility Points)
- [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) (Layer-Deep-Dive)
- [../WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md](../WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md) (autoritative Ops-/Runbook-Übersicht)

---

## 2) GitHub/Repo-Umfeld (inkl. Schutzmechanismen)

### Remote & Ownership
- **Remote:** git@github.com:rauterfrank-ui/Peak_Trade.git
- **CODEOWNERS** (../.github/CODEOWNERS):
  - Kritische Pfade: `src/governance/`, `src/risk/`, `src/live/`, `src/execution/`
  - Ops-Skripte: `scripts/ops/` (zusätzlicher Owner zur Vermeidung von „self-approval deadlocks“)

### CI-/Governance-Philosophie
- **Required Checks sollen immer „materialisieren“** (keine „missing contexts“ durch workflow-level path filters bei required checks).
- **Docs-only PRs**: Viele Checks laufen als **No-op/Skip mit SUCCESS**, während Docs-Integritätsgates weiterhin relevant sind.

### Explizit verboten (Governance-locked; nur belegbare Prinzipien)
- **Live-Execution „by default“ aktivieren oder Safety-Gates umgehen** (fail-closed, Defense-in-Depth) → [GOVERNANCE_AND_SAFETY_OVERVIEW.md](GOVERNANCE_AND_SAFETY_OVERVIEW.md) · [runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md](runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md)
- **Secrets/Credentials ins Repo committen** → [../.gitignore](../.gitignore) · [LIVE_OPERATIONAL_RUNBOOKS.md](LIVE_OPERATIONAL_RUNBOOKS.md)
- **Risk-relevante Defaults „aufweichen“ ohne Review/Freigabe** (z.B. Risk Layer Master Switch / Live Risk Limits) → [../config/config.toml](../config/config.toml) · [GOVERNANCE_AND_SAFETY_OVERVIEW.md](GOVERNANCE_AND_SAFETY_OVERVIEW.md)
- **Branch-Protection / Required Checks „entschärfen“** (SSoT + Drift Guard) → [../config/ci/required_status_checks.json](../config/ci/required_status_checks.json) · [ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md](ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md)

**Branch Protection (SSoT + Drift Guard):**
- **SSoT (Konfig):** [`../config/ci/required_status_checks.json`](../config/ci/required_status_checks.json)
- **Snapshot (Doku):** [ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md](ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md)
- **Drift Guard (live vs doc):** `scripts/ops/verify_required_checks_drift.sh`

---

## 3) System Map (Mermaid)

```mermaid
flowchart LR
  %% Runtime pipeline (fachlich/technisch)
  Data[Data] --> Strategy[Strategy]
  Strategy --> Sizing[Position Sizing]
  Sizing --> Risk[Risk]
  Risk --> Exec[Execution / Orders]
  Exec --> Artefacts[Artefacts: results/, reports/, logs/, live_runs/]

  %% Change -> Gates -> Merge
  Change[Change (Docs/Code/Config/Workflows)] --> Gates[CI / Gates]
  Gates --> Merge[Merge to main]

  Change -.md.-> DocsTargets[docs-reference-targets-gate]
  Change -.md.-> DocsDiff[Docs Diff Guard Policy Gate]
  Change -.md.-> TokenPolicy[docs-token-policy-gate (optional)]
  Change -.py.-> Lint[Lint Gate]
  Change -.code.-> Tests[tests (3.11)]
  Change -.code.-> StrategySmoke[strategy-smoke]
  Change -.policy paths.-> PolicyCritic[Policy Critic Gate]
  Change -.workflows.-> DispatchGuard[dispatch-guard]
  Change -.deps.-> Audit[audit]
  Change -.reports.-> ReportsGuard[Guard tracked files in reports directories]
```

---

## 4) Architektur (High-Level)

Pipeline-Logik (fachlich/technisch):

**Data → Strategy → Sizing → Risk → Backtest/Research → Reporting → Governance/Ops/Live-Track**

Wesentliche Eigenschaften:
- **No look-ahead** im realistischen Backtest (bar-by-bar).
- **Strategien liefern States** (persistente Positions-States), nicht nur Events.
- **Sizing vs Risk**: Sizing = „wie viel“, Risk = „ob überhaupt“ (orthogonal).

---

## 5) Codebase-Layer (Auszug der wichtigsten Bereiche)

Die Codebase ist breit aufgestellt (u.a. Execution, Live, Risk, Governance, Observability, AI-Orchestration).

| Domain (src/) | Responsibility | Key modules (Beispiele) | Primary consumers | Tests/Runbook link |
|---|---|---|---|---|
| `src/core/` | Basisschicht: Config/Environment, Errors/Taxonomie, Repro/Resilience, Tracking | core primitives (konkret: siehe Architekturdocs) | nahezu alle `scripts&#47;*.py` | [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) |
| `src/data/` | Data ingest/loader/normalizer/cache | Data Layer | Backtests, Research CLI, Market scans | [CLI_CHEATSHEET.md](CLI_CHEATSHEET.md) |
| `src/strategies/` | Strategy library + registry | Strategy registry | Backtest, Sweep, Research pipeline | [CLI_CHEATSHEET.md](CLI_CHEATSHEET.md) |
| `src/backtest/` | Backtest engine + stats | Backtest engine | `scripts/run_backtest.py`, `scripts/run_portfolio_backtest.py` | [CLI_CHEATSHEET.md](CLI_CHEATSHEET.md) |
| `src/portfolio/` / `src/experiments/` | Portfolio manager + experiments/robustness/sweeps/promotion | Experiment/sweep orchestration | `scripts/research_cli.py`, sweeps/reports | [PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) |
| `src/risk/` / `src/risk_layer/` | Risk checks + kill switch + risk-layer gate | Risk layer + kill switch | Live/Testnet/Execution, risk reports | [risk/KILL_SWITCH_ARCHITECTURE.md](risk/KILL_SWITCH_ARCHITECTURE.md) · [risk/KILL_SWITCH_RUNBOOK.md](risk/KILL_SWITCH_RUNBOOK.md) |
| `src/execution/` / `src/execution_pipeline/` / `src/execution_simple/` | Execution/pipeline/adapter architektur (hoch-sensitiv) | Execution pipeline | Shadow/Paper/Testnet runner | [runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md](runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md) |
| `src/live/` / `src/orders/` / `src/exchange/` | Live ops, order/routing, exchange integration | Live ops + exchange adapters | Live operational workflows | [LIVE_OPERATIONAL_RUNBOOKS.md](LIVE_OPERATIONAL_RUNBOOKS.md) |
| `src/observability/` / `src/obs/` | Logging/metrics/drift/telemetry | Observability | Ops monitoring + health | [OBSERVABILITY_AND_MONITORING_PLAN.md](OBSERVABILITY_AND_MONITORING_PLAN.md) |
| `src/ai_orchestration/` / `src/governance/` / `src/autonomous/` | Evidence packs + policy + autonomy guardrails | Evidence pack & governance glue | AI/Ops + CI evidence gate | [ai/EVIDENCE_PACK_CI_GATE.md](ai/EVIDENCE_PACK_CI_GATE.md) · [governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md) |

---

## 6) Config Map (SSoT)

**Ziel:** „Welche Config ist wofür?“ + klare **Single Source of Truth** je Bereich.

| Datei | Rolle / Scope | Wichtige Inhalte (Auszug) | Safety critical? | Approval required? | Hinweise / Quelle |
|---|---|---|---:|---:|---|
| [`../config.toml`](../config.toml) | Root-Konfig (vereinfachte Defaults) | `[environment]` (paper + `enable_live_trading=false` + `testnet_dry_run=true`), `[shadow]`, `[risk]`, `[data]` | Yes | Yes (TBD: je nach Änderung) | Governance-Prinzipien & Prozesse: [GOVERNANCE_AND_SAFETY_OVERVIEW.md](GOVERNANCE_AND_SAFETY_OVERVIEW.md) |
| [`../config/config.toml`](../config/config.toml) | Ops/Live-Track Konfig (umfangreich) | `[environment]` (No-Live Defaults), `[live_risk]`, `[live_alerts]`, `[shadow_paper_logging]`, `[risk_layer]` (enabled=false), `[escalation]` | Yes | Yes | Two-Augen/Approval Prozess (Risk-Limits): [GOVERNANCE_AND_SAFETY_OVERVIEW.md](GOVERNANCE_AND_SAFETY_OVERVIEW.md) |
| [`../config/risk/kill_switch.toml`](../config/risk/kill_switch.toml) | Kill Switch (Layer 4) | Trigger/Recovery/State/Audit (z.B. persistente state/audit unter `data&#47;kill_switch&#47;`) | Yes | Yes | Architektur/Runbook: [risk/KILL_SWITCH_ARCHITECTURE.md](risk/KILL_SWITCH_ARCHITECTURE.md) · [risk/KILL_SWITCH_RUNBOOK.md](risk/KILL_SWITCH_RUNBOOK.md) |
| [`../config/ci/required_status_checks.json`](../config/ci/required_status_checks.json) | Branch-Protection Required Checks (SSoT) | Liste der required contexts | Yes (CI safety) | Yes | Snapshot/Drift Guard: [ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md](ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md) |

---

## 7) Risk & Safety (Defense in Depth)

**Governance-Prinzipien (Doku):** [`GOVERNANCE_AND_SAFETY_OVERVIEW.md`](GOVERNANCE_AND_SAFETY_OVERVIEW.md)

**Kill Switch (Layer 4):**
- Config: [`../config/risk/kill_switch.toml`](../config/risk/kill_switch.toml)
- Architektur: [risk/KILL_SWITCH_ARCHITECTURE.md](risk/KILL_SWITCH_ARCHITECTURE.md)

---

## 8) Governance & Safety Vertrag (Non-Negotiables)

### Non-Negotiables (belegt)
- **No-Live Defaults (fail-closed):** `enable_live_trading=false` in [`../config.toml`](../config.toml) und [`../config/config.toml`](../config/config.toml)
- **Risk gewinnt immer:** Risk kann blockieren; keine „Overrides“ als Default-Mechanik (siehe Prinzipien in [`GOVERNANCE_AND_SAFETY_OVERVIEW.md`](GOVERNANCE_AND_SAFETY_OVERVIEW.md))
- **Live-Execution ist Governance-locked, bis explizit freigegeben:** Runbook beschreibt den Lock als Safety-Prinzip (siehe [runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md](runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md))
- **Two-Man-Rule / Freigabeprozesse:** Live-Runbooks und Governance-Doku verankern explizite Freigaben (siehe [`LIVE_OPERATIONAL_RUNBOOKS.md`](LIVE_OPERATIONAL_RUNBOOKS.md) und [`GOVERNANCE_AND_SAFETY_OVERVIEW.md`](GOVERNANCE_AND_SAFETY_OVERVIEW.md))
- **Keine Secrets ins Repo:** `.env`/Keys sind gitignored (siehe [`../.gitignore`](../.gitignore))

### Operator Approval Required (belegt)
Diese Changes gelten als „operator-/risk-relevant“ (mind. Review/Sign-off, je nach Policy/Runbook):
- **Kritische Codepfade (CODEOWNERS):** `src/governance/`, `src/risk/`, `src/live/`, `src/execution/`, `scripts/ops/` → [`../.github/CODEOWNERS`](../.github/CODEOWNERS)
- **Risk Layer Master Switch:** `risk_layer.enabled` ist **MUST remain false by default** (Kommentar im File) → [`../config/config.toml`](../config/config.toml)
- **Kill Switch Recovery (Approval Code / Persistenz):** `require_approval_code`, `state_file`, `audit_dir` → [`../config/risk/kill_switch.toml`](../config/risk/kill_switch.toml)
- **Live Operational Schritte:** „Live-Run (Small Size)“ ist im Runbook explizit als „echtes Geld“ gekennzeichnet → [`LIVE_OPERATIONAL_RUNBOOKS.md`](LIVE_OPERATIONAL_RUNBOOKS.md)

---

## 9) CI & Gates Matrix

**Hinweis:** „Required“ bezieht sich auf die SSoT-Liste in [`../config/ci/required_status_checks.json`](../config/ci/required_status_checks.json). Zusätzlich existiert ein Branch-Protection Snapshot in [ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md](ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md).

| Gate (Check Context) | Required (main) | Trigger | Docs-only behavior | Fail-Semantik | Local repro (kurz) |
|---|---:|---|---|---|---|
| **CI Health Gate (weekly_core)** | ✅ | `pull_request` / `push` (Job), `merge_group` (Workflow) / schedule / dispatch → [`../.github/workflows/test_health.yml`](../.github/workflows/test_health.yml) | Läuft auch bei Docs-only PRs (kein Docs-Skip im Job) | Hard fail, wenn `weekly_core` Profil fehlschlägt | `python scripts/run_test_health_profile.py --profile weekly_core` |
| **Guard tracked files in reports directories** | ✅ | always-run PR/push/merge_group → [`../.github/workflows/policy_tracked_reports_guard.yml`](../.github/workflows/policy_tracked_reports_guard.yml) | immer relevant | Hard fail, wenn unter `reports/` etwas tracked ist | `bash scripts/ci/guard_no_tracked_reports.sh` |
| **audit** | ✅ | PR/push/merge_group/schedule/dispatch → [`../.github/workflows/audit.yml`](../.github/workflows/audit.yml) | `pip-audit` ist **nicht-blocking** bei docs-only scope; blocking bei dependency-relevanten Änderungen | Blocking nur bei enforce=true (deps) | `bash scripts/automation/validate_all_pr_reports.sh` + `pip-audit` |
| **tests (3.11)** | ✅ | Matrix in [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Docs-only PR: Job wird erstellt, Tests werden übersprungen | Hard fail bei Test-Failures | `python -m pytest tests/ -v` |
| **strategy-smoke** | ✅ | in [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Docs-only PR: No-op/skip | Hard fail bei Smoke-Failures (wenn applicable) | `python scripts/strategy_smoke_check.py --output-json test_results/strategy_smoke/local.json --output-md test_results/strategy_smoke/local.md` |
| **Policy Critic Gate** | ✅ | always-run PR/merge_group → [`../.github/workflows/policy_critic_gate.yml`](../.github/workflows/policy_critic_gate.yml) | No-op pass wenn keine policy-sensitiven Pfade geändert wurden | Fail wenn applicable und Critic Findings | Local repro (optional): `git diff | python scripts/run_policy_critic.py --diff-stdin --changed-files \"$(git diff --name-only)\"` |
| **Lint Gate** | ✅ | always-run PR/merge_group → [`../.github/workflows/lint_gate.yml`](../.github/workflows/lint_gate.yml) | No-op pass wenn keine `.py` Änderungen | Hard fail bei Ruff/Lint/Format Fehlern | `bash -lc "ruff check src/ tests/ scripts/ && ruff format --check src/ tests/ scripts/"` |
| **Docs Diff Guard Policy Gate** | ✅ | PR/merge_group/dispatch → [`../.github/workflows/docs_diff_guard_policy_gate.yml`](../.github/workflows/docs_diff_guard_policy_gate.yml) | immer relevant | Hard fail bei fehlendem Marker/Policy-Verletzung | `python scripts/ci/check_docs_diff_guard_section.py` |
| **docs-reference-targets-gate** | ✅ | PR/merge_group/dispatch → [`../.github/workflows/docs_reference_targets_gate.yml`](../.github/workflows/docs_reference_targets_gate.yml) | No-op pass wenn keine Markdown-Dateien geändert wurden | Hard fail bei fehlenden Targets | `bash scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main` |
| **dispatch-guard** | ✅ | PR always-run; Push path-filtered → [`../.github/workflows/ci-workflow-dispatch-guard.yml`](../.github/workflows/ci-workflow-dispatch-guard.yml) | No-op pass wenn keine Workflow-Dateien geändert | Fail wenn workflow_dispatch Inputs inkonsistent | `python scripts/ops/validate_workflow_dispatch_guards.py --paths .github/workflows --fail-on-warn` |
| **docs-token-policy-gate** | ❌ (Signal) | PR/merge_group/dispatch → [`../.github/workflows/docs-token-policy-gate.yml`](../.github/workflows/docs-token-policy-gate.yml) | Nur bei Markdown-Änderungen | Fail bei nicht-encoded illustrative inline-code tokens | `python scripts/ops/validate_docs_token_policy.py --base origin/main` |

### Weitere wichtige Gates (nicht in der Required-Checks-SSoT-Liste)
| Gate (Workflow) | Trigger | Verhalten | Local repro (kurz) |
|---|---|---|---|
| Evidence Pack Validation Gate → [`../.github/workflows/evidence_pack_gate.yml`](../.github/workflows/evidence_pack_gate.yml) | PR/push/merge_group/dispatch | Always-run Jobs, aber „skip gracefully“ wenn Evidence-Pack-Code unverändert; fail-closed wenn applicable (Validator) | `python scripts/run_layer_smoke_with_evidence_pack.py --layer L0 --autonomy REC --verbose` + `python scripts/validate_evidence_pack_ci.py --root .artifacts/evidence_packs --strict` |
| Required Checks Hygiene Gate → [`../.github/workflows/required-checks-hygiene-gate.yml`](../.github/workflows/required-checks-hygiene-gate.yml) | PR/push | Verhindert path-filtered required checks (Validator gegen `config/ci/required_status_checks.json`) | `python scripts/ci/validate_required_checks_hygiene.py --config config/ci/required_status_checks.json --workflows .github/workflows --strict` |
| Docs Integrity Snapshot → [`../.github/workflows/docs-integrity-snapshot.yml`](../.github/workflows/docs-integrity-snapshot.yml) | PR (path-filtered auf `docs&#47;**`) | Informational Snapshot (bricht PR nicht) | `python scripts/ops/docs_graph_snapshot.py --out docs_graph.snapshot.json` |

---

## 9a) Change Impact Map (Pfad → Gates/Owner/Approval)

**Ziel:** schnelle Einschätzung „welche Gates/Reviews werden (typisch) relevant?“ – basierend auf Workflows + CODEOWNERS.

| Änderungspfad (Beispiele) | Gates (zusätzlich „applicable“) | Owner/Review | Hinweis |
|---|---|---|---|
| `docs&#47;**` | `docs-reference-targets-gate`, `Docs Diff Guard Policy Gate`, optional `docs-token-policy-gate` | (Doku) + Ops-Gates | Local: `./scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| `src&#47;governance&#47;**` | `Policy Critic Gate` | CODEOWNERS: `@rauterfrank-ui` | policy-sensitiv |
| `src&#47;risk&#47;**`, `src&#47;risk_layer&#47;**` | `Policy Critic Gate` | CODEOWNERS: `@rauterfrank-ui` | risk-sensitiv |
| `src&#47;live&#47;**`, `src&#47;execution&#47;**`, `src&#47;exchange&#47;**` | `Policy Critic Gate` | CODEOWNERS: `@rauterfrank-ui` | execution/live-sensitiv |
| `scripts&#47;ops&#47;**` | `Policy Critic Gate` | CODEOWNERS: `@rauterfrank-ui` + `@HrzFrnk` | ops-sensitiv |
| `.github&#47;workflows&#47;**` | `dispatch-guard` (applicable) | (Ops/CI) | workflows müssen dispatch inputs konsistent definieren |
| `reports&#47;**` (tracked) | `Guard tracked files in reports directories` | (Ops) | `reports/` muss gitignored bleiben |

---

## 10) Happy Paths (typische Nutzung)

### Developer (Edit → Test → Format → Docs Gates → PR)
- **Tests/Lint lokal:** siehe [Start Here](#start-here-by-persona) (Developer)
- **Docs Gates (wenn Docs geändert):** `./scripts/ops/pt_docs_gates_snapshot.sh --changed`

### Operator/Ops (Verify → Evidence → Index → Merge Log)
- **Runbooks & Ops Hub:** [ops/README.md](ops/README.md)
- **Evidence:** [ops/EVIDENCE_INDEX.md](ops/EVIDENCE_INDEX.md) (Schema/Template siehe §11)
- **Merge Logs:** `docs&#47;ops&#47;merge_logs&#47;`

### Research/Quant
- **CLI Einstieg:** [CLI_CHEATSHEET.md](CLI_CHEATSHEET.md)
- **Research → Live Playbook:** [PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md)
- **Shadow/Paper/Testnet:** siehe [LIVE_OPERATIONAL_RUNBOOKS.md](LIVE_OPERATIONAL_RUNBOOKS.md) und [LIVE_TESTNET_TRACK_STATUS.md](LIVE_TESTNET_TRACK_STATUS.md)
- **Live Status Reports:** [LIVE_STATUS_REPORTS.md](LIVE_STATUS_REPORTS.md)

---

## 11) Ops, Runbooks, Evidence (Betriebs-Ökosystem)

Peak_Trade hat eine ausgeprägte Ops-/Runbook-/Evidence-Kultur (Einstiegspunkte):
- **Ops Hub:** [ops/README.md](ops/README.md)
- **Control Center:** [ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md](ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md)
- **Evidence Index:** [ops/EVIDENCE_INDEX.md](ops/EVIDENCE_INDEX.md) (mit Schema/Template: [ops/EVIDENCE_SCHEMA.md](ops/EVIDENCE_SCHEMA.md), [ops/EVIDENCE_ENTRY_TEMPLATE.md](ops/EVIDENCE_ENTRY_TEMPLATE.md))
- **Branch Protection Required Checks:** [ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md](ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md)
- **Execution Governance Runbook:** [runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md](runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md)

### Incident / Triage (nur belegbare Einstiege)
- **Incident-Runbooks (Ops):** [LIVE_OPERATIONAL_RUNBOOKS.md](LIVE_OPERATIONAL_RUNBOOKS.md) (enthält expliziten Incident-Runbook-Index)
- **Incident Simulation & Drills (Phase 56):** [INCIDENT_SIMULATION_AND_DRILLS.md](INCIDENT_SIMULATION_AND_DRILLS.md) · **Drill-Log:** [INCIDENT_DRILL_LOG.md](INCIDENT_DRILL_LOG.md)
- **Incident Runbook Integration (Phase 84):** [PHASE_84_INCIDENT_RUNBOOK_INTEGRATION_V1.md](PHASE_84_INCIDENT_RUNBOOK_INTEGRATION_V1.md)
- **Incident Handling Hub:** [RUNBOOKS_AND_INCIDENT_HANDLING.md](RUNBOOKS_AND_INCIDENT_HANDLING.md)
- **Kill Switch Runbook:** [risk/KILL_SWITCH_RUNBOOK.md](risk/KILL_SWITCH_RUNBOOK.md)

---

## Outputs & Artefacts (Landkarte)

**Gitignored (soll nicht committed werden):** siehe [`../.gitignore`](../.gitignore)

| Artefakt | Typischer Pfad | Git | Quelle / Beispiel |
|---|---|---:|---|
| Daten (lokal) | `data/` | ❌ | Root `data/` ist ignored (nicht `src/data/`) |
| Backtest/Research Ergebnisse | `results/` | ❌ | viele Research-/Backtest-Skripte schreiben hierhin |
| Reports (lokal) | `reports/` | ❌ | u.a. `reports&#47;audit&#47;**`, `reports&#47;live_status&#47;` |
| Test-Artefakte | `test_results&#47;`, `test_runs&#47;` | ❌ | CI/Local Smoke Outputs |
| Live Runs / Sessions | `live_runs/` | ❌ | Run-Logging (z.B. `shadow_paper_logging.base_dir`) |
| Logs | `logs/`, `*.log` | ❌ | lokale Logs/Runbooks |
| MLflow Tracking | `mlruns&#47;` | ❌ | lokale MLflow Artefakte |
| Evidence Index / Entries | `docs&#47;ops&#47;EVIDENCE_INDEX.md`, `docs&#47;ops&#47;evidence&#47;EV-*.md` | ✅ | Evidence Contract (Schema/Template) |
| Merge Logs (Ops) | `docs/ops/merge_logs/` | ✅ | PR Closeouts / Merge Logs |

**Mini-Flow (Run → Evidence → Merge Log):**
1. **Run** erzeugt lokale Artefakte (`results/`, `reports/`, `test_results&#47;`, `live_runs/`)
2. **Evidence** (optional) wird als `docs&#47;ops&#47;evidence&#47;EV-*.md` und Eintrag in [ops/EVIDENCE_INDEX.md](ops/EVIDENCE_INDEX.md) dokumentiert
3. **Merge Log** (Ops-PRs) dokumentiert Merge/Verifikation in `docs/ops/merge_logs/`

---

## Toolchain Standard & Common Pitfalls

### Standards (Repo/CI-konform)
- **Python Interpreter:** lokal bevorzugt `python3` (wenn `python` fehlt)
- **Lint/Format:** `ruff` (CI Lint Gate nutzt `ruff check` + `ruff format --check`) → [`../.github/workflows/lint_gate.yml`](../.github/workflows/lint_gate.yml)
- **Pre-commit:** Hooks für EOF/Whitespace/YAML/TOML/JSON + Ruff → [`../.pre-commit-config.yaml`](../.pre-commit-config.yaml)
- **Pytest Marker:** siehe [`../pytest.ini`](../pytest.ini)

### Docs Gates Pitfalls (häufig)
- **Broken repo links:** `docs-reference-targets-gate` blockiert Merge → [ops/runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md](ops/runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md)
- **Illustrative Pfade in Inline-Code:** müssen ggf. encoded werden (sonst Token Policy Gate / false positives) → [ops/runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md](ops/runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md)

---

## Stability/Readiness Table

**Quelle:** Status-Dokus (keine Ableitung/Schätzung).

| Area | Readiness (Dok) | Tests present | Runbook present | Evidence flow | Notes / Quelle |
|---|---|---:|---:|---:|---|
| Live-/Testnet-Track (gesamt) | ~95% | Yes | Yes | Yes | Status: [LIVE_TESTNET_TRACK_STATUS.md](LIVE_TESTNET_TRACK_STATUS.md) |
| Environment & Safety | 95% | Yes | Yes | TBD | Runbooks/Governance: [LIVE_OPERATIONAL_RUNBOOKS.md](LIVE_OPERATIONAL_RUNBOOKS.md) · [GOVERNANCE_AND_SAFETY_OVERVIEW.md](GOVERNANCE_AND_SAFETY_OVERVIEW.md) |
| Live Risk Limits | 95% | Yes | Yes | TBD | Status: [LIVE_TESTNET_TRACK_STATUS.md](LIVE_TESTNET_TRACK_STATUS.md) |
| Order-/Execution-Layer & Exchange-Anbindung | 85% | Yes | Yes | TBD | Governance: [runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md](runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md) |
| Shadow-/Paper-/Testnet-Orchestrierung | 85% | Yes | Yes | TBD | Runbooks: [LIVE_OPERATIONAL_RUNBOOKS.md](LIVE_OPERATIONAL_RUNBOOKS.md) |
| Run-Logging & Live-Reporting | 90% | Yes | Yes | TBD | Live status reporting: [LIVE_STATUS_REPORTS.md](LIVE_STATUS_REPORTS.md) |
| Live-/Portfolio-Monitoring & Risk Bridge | 95% | Yes | Yes | TBD | Status: [LIVE_TESTNET_TRACK_STATUS.md](LIVE_TESTNET_TRACK_STATUS.md) |
| Live Alerts & Notifications | 95% | Yes | Yes | TBD | Phase-Doku: [PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md](PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md) |
| Governance, Runbooks & Checklisten | 94% | TBD | Yes | Yes | Evidence: [ops/EVIDENCE_SCHEMA.md](ops/EVIDENCE_SCHEMA.md) |
| Incident Drills | TBD | TBD | Yes | Yes | Drills: [INCIDENT_SIMULATION_AND_DRILLS.md](INCIDENT_SIMULATION_AND_DRILLS.md) · Log: [INCIDENT_DRILL_LOG.md](INCIDENT_DRILL_LOG.md) |
| AI Autonomy / Evidence Packs | TBD | Yes | TBD | Yes | Evidence Gate: [ai/EVIDENCE_PACK_CI_GATE.md](ai/EVIDENCE_PACK_CI_GATE.md) |
| Gesamtprojekt (Phasen 1–86) | ~98% | Yes | TBD | TBD | Status: [PEAK_TRADE_STATUS_OVERVIEW.md](PEAK_TRADE_STATUS_OVERVIEW.md) |

---

## Known gaps (documented only) + Next steps

### Known gaps (nur belegt)
- **Kill Switch Notifications/Monitoring default disabled:** [`../config/risk/kill_switch.toml`](../config/risk/kill_switch.toml)
- **Escalation ist Phase-85 Stub, keine echten API-Calls:** `enable_real_calls=false` in [`../config/config.toml`](../config/config.toml)
- **Risk Layer bleibt default disabled (Governance-gated):** Kommentar + `enabled=false` in [`../config/config.toml`](../config/config.toml)
- **Policy Critic Gate hat „placeholder/no-op“ Pfad, falls Script fehlt:** [`../.github/workflows/policy_critic_gate.yml`](../.github/workflows/policy_critic_gate.yml)
- **Docs Token Policy Gate ist (derzeit) non-required Signal:** [`../.github/workflows/docs-token-policy-gate.yml`](../.github/workflows/docs-token-policy-gate.yml) + Ops Runbook

### Next steps (short, governance-safe)
- **Drift prüfen (required checks):** `scripts/ops/verify_required_checks_drift.sh` (rein read-only)
- **Docs Gates vor PRs:** `./scripts/ops/pt_docs_gates_snapshot.sh --changed`
- **Artefakt-Hygiene:** sicherstellen, dass `reports/` & `results/` nicht versehentlich committed werden (Guards existieren)

---

## FAQ / Troubleshooting (Top 10)

1) **Docs Reference Targets Gate fail (missing targets)**  
→ Lokal: `bash scripts/ops/verify_docs_reference_targets.sh`  
→ Operator-Guide: [ops/runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md](ops/runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md)

2) **Docs Token Policy Gate fail (inline-code Pfade)**  
→ Lokal: `python scripts/ops/validate_docs_token_policy.py --tracked-docs`  
→ Fix: illustrative Pfade in Inline-Code mit `&#47;` escapen  
→ Operator-Guide: [ops/runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md](ops/runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md)

3) **Ruff failures (Lint/Format Gate)**  
→ Lokal: `bash -lc "ruff check src/ tests/ scripts/ && ruff format --check src/ tests/ scripts/"`

4) **Pytest env/marker issues**  
→ Marker: [../pytest.ini](../pytest.ini)  
→ Lokal: `python -m pytest -q`

5) **dispatch-guard failure (workflow_dispatch inputs)**  
→ Lokal: `python scripts/ops/validate_workflow_dispatch_guards.py --paths .github/workflows --fail-on-warn`

6) **Required checks drift / missing contexts**  
→ Drift Guard: `bash scripts/ops/verify_required_checks_drift.sh`  
→ Snapshot: [ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md](ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md)

7) **Policy Critic Gate Findings / applicability**  
→ Workflow: [../.github/workflows/policy_critic_gate.yml](../.github/workflows/policy_critic_gate.yml)

8) **Evidence Pack Gate: skip vs fail**  
→ Workflow: [../.github/workflows/evidence_pack_gate.yml](../.github/workflows/evidence_pack_gate.yml)

9) **Tracked files in reports/**  
→ Lokal: `bash scripts/ci/guard_no_tracked_reports.sh`

10) **Docs Diff Guard Policy Gate**  
→ Lokal: `python scripts/ci/check_docs_diff_guard_section.py`

---

## Glossary & Conventions

### Evidence IDs
- Format: `EV-YYYYMMDD-<TAG>` (z.B. `EV-20260107-SEED`)  
  → Schema: [ops/EVIDENCE_SCHEMA.md](ops/EVIDENCE_SCHEMA.md)

### Merge Logs
- Ops Merge Logs sind **committed** (Audit Trail) und leben unter `docs/ops/merge_logs/` (siehe Ops Hub [ops/README.md](ops/README.md)).

### Runbooks
- „Runbook“ = Schritt-für-Schritt Operator-Anleitung (z.B. Live Ops) → [`LIVE_OPERATIONAL_RUNBOOKS.md`](LIVE_OPERATIONAL_RUNBOOKS.md)

### Policy Packs
- Policy-Konfigurationen für Policy Critic: `policy_packs/` (z.B. `ci.yml`, `live_adjacent.yml`, `research.yml`) – siehe Repo-Root.

### Required Check / Gate
- **Required check**: Status-Check, der in Branch Protection als zwingend konfiguriert ist (SSoT: [`../config/ci/required_status_checks.json`](../config/ci/required_status_checks.json)).
- **Gate**: Workflow/Check, der bei Failure (oder bei „applicable + failure“) Merge blockieren kann.

### „docs-only PR“
- PR ohne „code_changed“ (CI erkennt das in [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml)); Tests/Smoke/Lint können als No-op SUCCESS laufen, Docs-Gates bleiben relevant.
