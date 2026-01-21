# Peak_Trade Repository Structure

**Stand:** 2025-12-27  
**Cleanup:** chore/repo-cleanup-structured-20251227

Dieses Dokument erklärt die Organisation des Peak_Trade Repositories.

---

## 📁 Top-Level Struktur

```
Peak_Trade/
├── README.md                    # Haupt-Dokumentation
├── README_REGISTRY.md           # Index aller READMEs
├── pyproject.toml               # Python-Projekt-Konfiguration
├── pytest.ini                   # Test-Konfiguration
├── requirements.txt             # Dependencies
├── uv.lock                      # uv Lockfile
├── Makefile                     # Build/Task-Automation
├── config.toml                  # Simplified Config (OOP Strategy API)
│
├── archive/                     # Historische Snapshots & Legacy-Code
├── config/                      # Config-Templates & Examples
├── docker/                      # Docker-Compose & Container-Configs
├── docs/                        # 📚 Alle Dokumentation
├── examples/                    # Code-Beispiele
├── notebooks/                   # Jupyter/Analysis-Templates
├── patches/                     # Git-Patches
├── policy_packs/                # Policy-Configs (CI, Research, Live)
├── scripts/                     # 🔧 Alle Scripts
├── src/                         # 💻 Produktiv-Code
├── templates/                   # Templates (Bash, Ops, Dashboards, Quarto)
└── tests/                       # 🧪 Test-Suite
```

---

## 📚 docs/ — Dokumentations-Hub

### Struktur

```
docs/
├── README.md                    # Navigation-Hub
│
├── architecture/                # 🏗️ ADRs & Design-Docs
│   ├── ADR_0001_Peak_Tool_Stack.md
│   └── REPO_STRUCTURE.md        # Diese Datei
│
├── dev/                         # 👨‍💻 Developer Guides
│   └── knowledge/               # Knowledge DB Dokumentation
│       ├── IMPLEMENTATION_SUMMARY_KNOWLEDGE_DB.md
│       ├── KNOWLEDGE_API_IMPLEMENTATION_SUMMARY.md
│       └── KNOWLEDGE_API_SMOKE_TESTS.md
│
├── features/                    # 🎯 Feature-spezifische Docs
│   └── psychology/
│       ├── PSYCHOLOGY_HEATMAP_README.md
│       ├── PSYCHOLOGY_HEURISTICS_IMPLEMENTATION.md
│       └── PSYCHOLOGY_HEURISTICS_README.md
│
├── ops/                         # 🔧 Operator Hub
│   ├── README.md                # Ops Navigation
│   ├── P0_GUARDRAILS_QUICK_REFERENCE.md
│   ├── NEXT_STEPS_WORKFLOW_DOCS.md
│   ├── Peak_Trade_TOOLING_AND_EVIDENCE_CHAIN_RUNBOOK.md
│   ├── REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md
│   │
│   ├── reports/                 # Implementation Reports
│   │   ├── AUTOMATION_SETUP_REPORT.md
│   │   ├── CI_LARGE_PR_IMPLEMENTATION_REPORT.md
│   │   ├── OPS_DOCTOR_IMPLEMENTATION_SUMMARY.md
│   │   │
│   │   └── phases/              # Phase Completion Reports
│   │       ├── CYCLES_3_5_COMPLETION_REPORT.md
│   │       ├── PHASE_16L_IMPLEMENTATION_SUMMARY.md
│   │       └── PHASE_16L_VERIFICATION_REPORT.md
│   │
│   ├── cleanup/                 # Repo Cleanup Dokumentation
│   ├── merge_logs/              # PR Merge Logs
│   └── incidents/               # Incident Reports
│
├── risk/                        # 📊 Risk Management Docs
│   ├── README.md                # Risk Navigation
│   ├── RISK_LAYER_ROADMAP.md
│   ├── RISK_LAYER_V1_IMPLEMENTATION_REPORT.md
│   ├── RISK_LAYER_V1_PRODUCTION_READY_REPORT.md
│   ├── RISK_LAYER_V1_OPERATOR_GUIDE.md
│   ├── *_GATE_RUNBOOK.md        # Gate-spezifische Runbooks
│   │
│   └── roadmaps/                # Risk Roadmaps
│       ├── COMPONENT_VAR_ROADMAP_PATCHED.md
│       └── PORTFOLIO_VAR_ROADMAP.md
│
├── learning_promotion/          # 🎓 Learning Promotion Loop
│   └── CHANGELOG_LEARNING_PROMOTION_LOOP.md
│
├── trigger_training/            # 🎯 Trigger Training
├── runbooks/                    # 📖 Operational Runbooks
├── audit/                       # 🔍 Audit Reports
└── _worklogs/                   # 📝 Work Logs
```

### Konventionen

**Wo gehört welche Doku hin?**

| Typ | Ziel | Beispiel |
|-----|------|----------|
| Architecture Decision | `docs/architecture/` | ADRs, Design-Docs |
| Developer Guide | `docs/dev/` | Setup, API-Guides |
| Feature-Dokumentation | `docs&#47;features&#47;<feature>&#47;` | Feature-spezifisch |
| Implementation Report | `docs/ops/reports/` | Abschluss-Reports |
| Phase Completion | `docs/ops/reports/phases/` | Phase-Reports |
| Operator Guide/Runbook | `docs/ops/` oder `docs/runbooks/` | Operational Guides |
| Risk Documentation | `docs/risk/` | Risk Layer, Gates |
| Changelog | Feature-Ordner oder Root | Feature-spezifisch |

---

## 🔧 scripts/ — Script-Organisation

### Struktur

```
scripts/
├── ops/                         # Operator Tools
│   ├── ops_doctor.sh
│   ├── ops_center.sh
│   ├── run_audit.sh
│   ├── pr_audit_scan.sh
│   ├── merge_pr_workflow.sh
│   └── ...
│
├── run/                         # Runner Entrypoints
│   ├── run_smoke_tests.sh
│   ├── run_phase3_robustness.sh
│   └── run_regime_btcusdt_experiments.sh
│
├── utils/                       # Utility Scripts
│   ├── render_last_report.sh
│   ├── slice_from_backup.sh
│   └── install_desktop_shortcuts.sh
│
├── workflows/                   # Workflow Scripts
│   ├── quick_pr_merge.sh
│   ├── git_push_and_pr.sh
│   ├── post_merge_workflow.sh
│   └── ...
│
├── ci/                          # CI-spezifische Scripts
│   ├── validate_git_state.sh
│   ├── guard_no_tracked_reports.sh
│   └── ...
│
├── automation/                  # Automation Scripts
│   ├── generate_merge_log.sh
│   ├── post_merge_verify.sh
│   └── ...
│
├── dev/                         # Developer Tools
│   ├── test_knowledge_api_smoke.sh
│   └── ...
│
└── obs/                         # Observability Scripts
    ├── smoke.sh
    └── ...
```

### Konventionen

**Wo gehört welches Script hin?**

| Typ | Ziel | Beispiel |
|-----|------|----------|
| Operator Tool | `scripts/ops/` | ops_doctor, merge workflows |
| Runner/Entrypoint | `scripts/run/` | run_smoke_tests, run_backtest |
| Utility | `scripts/utils/` | Helper scripts ohne Kategorie |
| Workflow | `scripts/workflows/` | PR workflows, post-merge |
| CI Tool | `scripts/ci/` | CI-spezifische Guards/Checks |
| Automation | `scripts/automation/` | Automated tasks (reports, etc.) |
| Dev Tool | `scripts/dev/` | Developer convenience tools |
| Observability | `scripts/obs/` | Monitoring, metrics |

---

## 💻 src/ — Produktiv-Code

Struktur folgt funktionalen Layern:

```
src/
├── core/                        # Core-Funktionalität
├── data/                        # Data Pipeline
├── strategies/                  # Trading Strategies
├── backtest/                    # Backtest Engine
├── risk/                        # Risk Management
├── portfolio/                   # Portfolio Management
├── execution/                   # Order Execution
├── live/                        # Live Trading
├── governance/                  # Governance & Policy
├── ops/                         # Ops Tools (Python)
├── reporting/                   # Reporting & Dashboards
└── ...
```

**Regel:** Nur produktiver Code in `src/`. Keine Docs, keine Scripts.

---

## 🧪 tests/ — Test-Suite

Struktur spiegelt `src/`:

```
tests/
├── core/
├── data/
├── strategies/
├── backtest/
├── risk/
├── ops/
└── ...
```

**Regel:** Test-Struktur folgt src-Struktur.

---

## 📦 config/ — Konfiguration

```
config/
├── config.toml                  # Haupt-Config-Template
├── config.test.toml             # Test-Config
├── default.toml                 # Defaults
├── *_example.toml               # Examples (Risk Gates, etc.)
├── portfolios/                  # Portfolio Configs
├── sweeps/                      # Sweep Configs
├── scenarios/                   # Scenario Configs
└── ...
```

**Note:** Root `config.toml` ist eine "simplified" Version für OOP Strategy API.

---

## 🗄️ archive/ — Historische Snapshots

```
archive/
├── README.md                    # Index: Was ist archiviert und warum
├── full_files_stand_02.12.2025/ # Snapshot
├── legacy_docs/                 # Alte Docs
├── legacy_scripts/              # Alte Scripts
└── PeakTradeRepo/               # Altes komplettes Repo
```

**Regel:** Nur historisch wertvolle Dinge archivieren, nicht löschen.

---

## 🐳 docker/ — Container-Konfiguration

```
docker/
├── compose.yml                  # Haupt-Compose
├── docker-compose.obs.yml       # Observability Stack
├── README.md                    # Docker Setup Guide
├── mlflow/                      # MLflow Container
└── obs/                         # Observability Container
```

---

## 🎯 Neue Dateien: Wo hin?

### Markdown-Dokumentation

1. **Architecture Decision?** → `docs/architecture/`
2. **Developer Guide?** → `docs/dev/`
3. **Feature-spezifisch?** → `docs&#47;features&#47;<feature>&#47;`
4. **Implementation Report?** → `docs/ops/reports/`
5. **Operator Guide?** → `docs/ops/` oder `docs/runbooks/`
6. **Risk-bezogen?** → `docs/risk/`

### Scripts

1. **Operator Tool?** → `scripts/ops/`
2. **Runner/Entrypoint?** → `scripts/run/`
3. **Workflow?** → `scripts/workflows/`
4. **CI-spezifisch?** → `scripts/ci/`
5. **Utility?** → `scripts/utils/`

### Code

1. **Produktiv-Code?** → `src&#47;<layer>&#47;`
2. **Test?** → `tests&#47;<layer>&#47;`
3. **Example?** → `examples/`

---

## 🚫 Was NICHT ins Repo

Diese Dinge sind in `.gitignore` und sollten NICHT committed werden:

- `data/` (generierte Daten)
- `results/` (Backtest-Ergebnisse)
- `reports/` (generierte Reports)
- `logs/` (Log-Files)
- `live_runs/` (Live-Session-Daten)
- `test_runs/` (Test-Artefakte)
- `*.log` (Log-Files)
- `venv/` (Virtual Environment)

**Ausnahme:** Wenn Reports/Artefakte absichtlich committed werden sollen, muss das klar dokumentiert sein (z.B. `reports&#47;README.md`).

---

## 📖 Weitere Dokumentation

- **Haupt-README:** `README.md`
- **README-Index:** `README_REGISTRY.md`
- **Docs-Navigation:** `docs/README.md`
- **Ops-Hub:** `docs/ops/README.md`
- **Risk-Hub:** `docs/risk/README.md`
- **Config-Guide:** `config/README.md`
- **Archive-Index:** `archive&#47;README.md`

---

## 🔄 Cleanup History

Dieses Dokument wurde im Rahmen des Repository-Cleanups vom 2025-12-27 erstellt.

**Details:** Siehe `docs/ops/cleanup/CLEANUP_REPORT.md`
