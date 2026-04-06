# File Inventory – Repository Cleanup Analysis

**Datum:** 2025-12-27  
**Branch:** `chore/repo-cleanup-structured-20251227`

## Methodik

Für jeden Top-Level Ordner:
- ✅ = Keep as-is
- 📦 = Archive (historischer Wert)
- 🔀 = Move/Consolidate (besserer Platz)
- 🗑️ = Delete (redundant/obsolete)
- ❓ = Unclear (needs investigation)

---

## 📁 ROOT-LEVEL FILES

### Markdown-Dateien auf Root-Level (Kandidaten für Relocation)

| Datei | Status | Analyse | Aktion |
|-------|--------|---------|--------|
| `README.md` | ✅ | Hauptdoku, muss bleiben | Keep |
| `README_REGISTRY.md` | ✅ | Index aller READMEs | Keep |
| `ADR_0001_Peak_Tool_Stack.md` | 🔀 | Architecture Decision Record | **Move** → `docs/architecture/` |
| `AUTOMATION_SETUP_REPORT.md` | 🔀 | Ops/Setup Report | **Move** → `docs/ops/reports/` |
| `CHANGELOG_LEARNING_PROMOTION_LOOP.md` | 🔀 | Changelog für Feature | **Move** → `docs/learning_promotion/` |
| `CI_LARGE_PR_IMPLEMENTATION_REPORT.md` | 🔀 | CI Report | **Move** → `docs/ops/reports/` |
| `COMPONENT_VAR_ROADMAP_PATCHED.md` | 🔀 | Risk Roadmap | **Move** → `docs/risk/roadmaps/` |
| `CYCLES_3_5_COMPLETION_REPORT.md` | 🔀 | Phase Report | **Move** → `docs/ops/reports/phases/` |
| `IMPLEMENTATION_SUMMARY_KNOWLEDGE_DB.md` | 🔀 | Knowledge DB Report | **Move** → `docs/dev/knowledge/` |
| `KNOWLEDGE_API_IMPLEMENTATION_SUMMARY.md` | 🔀 | Knowledge API Report | **Move** → `docs/dev/knowledge/` |
| `KNOWLEDGE_API_SMOKE_TESTS.md` | 🔀 | Test Doku | **Move** → `docs/dev/knowledge/` |
| `NEXT_STEPS_WORKFLOW_DOCS.md` | 🔀 | Workflow Doku | **Move** → `docs/ops/` |
| `OPS_DOCTOR_IMPLEMENTATION_SUMMARY.md` | 🔀 | Ops Doctor Report | **Move** → `docs/ops/reports/` |
| `P0_GUARDRAILS_QUICK_REFERENCE.md` | 🔀 | P0 Quick Ref | **Move** → `docs/ops/` |
| `Peak_Trade_TOOLING_AND_EVIDENCE_CHAIN_RUNBOOK.md` | 🔀 | Tooling Runbook | **Move** → `docs/ops/` |
| `PHASE_16L_IMPLEMENTATION_SUMMARY.md` | 🔀 | Phase Report | **Move** → `docs/ops/reports/phases/` |
| `PHASE_16L_VERIFICATION_REPORT.md` | 🔀 | Phase Report | **Move** → `docs/ops/reports/phases/` |
| `PSYCHOLOGY_HEATMAP_README.md` | 🔀 | Feature README | **Move** → `docs/features/psychology/` |
| `PSYCHOLOGY_HEURISTICS_IMPLEMENTATION.md` | 🔀 | Feature Impl | **Move** → `docs/features/psychology/` |
| `PSYCHOLOGY_HEURISTICS_README.md` | 🔀 | Feature README | **Move** → `docs/features/psychology/` |
| `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md` | 🔀 | **DUBLETTE!** | **Delete** (existiert in docs/ops/) |
| `RISK_LAYER_ROADMAP.md` | 🔀 | **DUBLETTE!** | **Delete** (existiert in docs/risk/) |
| `RISK_LAYER_V1_IMPLEMENTATION_REPORT.md` | 🔀 | **DUBLETTE!** | **Delete** (existiert als docs/risk/...) |
| `RISK_LAYER_V1_PRODUCTION_READY_REPORT.md` | 🔀 | **DUBLETTE!** | **Delete** (existiert als docs/risk/...) |

### Root-Level Config Files

| Datei | Status | Analyse | Aktion |
|-------|--------|---------|--------|
| `config.toml` | ❓ | **DUBLETTE?** config/config.toml | **Check refs** → likely delete or clarify |
| `pyproject.toml` | ✅ | Standard Python Config | Keep |
| `pytest.ini` | ✅ | Test Config | Keep |
| `requirements.txt` | ✅ | Dependencies (uv.lock auch da) | Keep |
| `uv.lock` | ✅ | uv lockfile | Keep |
| `Makefile` | ✅ | Build/Task Runner | Keep |

### Root-Level Scripts

| Datei | Status | Analyse | Aktion |
|-------|--------|---------|--------|
| `run_regime_experiments.sh` | 🔀 | **DUBLETTE!** | **Delete** (existiert in archive/legacy_scripts/) |

### Root-Level Artifacts/Logs

| Datei | Status | Analyse | Aktion |
|-------|--------|---------|--------|
| `audit.log` | ❓ | Log-File | **Check** .gitignore + delete if should be ignored |
| `tests.log` | ❓ | Test Log | **Check** .gitignore + delete if should be ignored |
| `gitignore` | 🔀 | Falscher Name! | **Rename** → `.gitignore` oder delete wenn .gitignore existiert |

### Root-Level Patches

| Datei | Status | Analyse | Aktion |
|-------|--------|---------|--------|
| `COMPONENT_VAR_ROADMAP.patch` | 📦 | Historischer Patch | **Archive** → `patches/` oder delete wenn applied |

---

## 📁 archive/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `archive&#47;full_files_stand_02.12.2025&#47;` | ✅ | Full snapshot, historisch | Keep (Archive) |
| `archive&#47;legacy_docs&#47;` | ✅ | Legacy Docs | Keep (Archive) |
| `archive&#47;legacy_scripts&#47;` | ✅ | Legacy Scripts | Keep (Archive) |
| `archive&#47;PeakTradeRepo&#47;` | ✅ | Altes komplettes Repo | Keep (aber prüfen ob nützlich) |

**Assessment:** Archive ist gut strukturiert. Behalten, aber mit Index/README ausstatten.

---

## 📁 config/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `config/config.toml` | ✅ | Main config template | Keep |
| `config/config.test.toml` | ✅ | Test config | Keep |
| `config/default.toml` | ✅ | Defaults | Keep |
| `config&#47;*_example.toml` | ✅ | Examples (risk gates etc.) | Keep |
| Root `config.toml` | ❓ | **Prüfen ob Dublette** | Check & likely delete |

**Assessment:** Config-Struktur ist gut. Root config.toml klären.

---

## 📁 data/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `data/chroma_db/` | ✅ | Knowledge DB | Check .gitignore (should be ignored) |

**Assessment:** Data sollte in .gitignore sein wenn generated.

---

## 📁 docker/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `docker/compose.yml` | ✅ | Docker Compose | Keep |
| `docker/README.md` | ✅ | Docker Doku | Keep |
| `docker/mlflow/`, `docker/obs/` | ✅ | Service Configs | Keep |
| Root `docker-compose.obs.yml` | 🔀 | Sollte in docker/ sein | **Move** → `docker/` |

**Assessment:** docker/ gut strukturiert. Root docker-compose konsolidieren.

---

## 📁 docs/

**Gesamtstruktur:** 444+ Markdown-Dateien!

### Unterordner

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `docs/ops/` | ✅ | Operator Hub | Keep & ensure current |
| `docs/ops/merge_logs/` | ✅ | PR Merge Logs | Keep |
| `docs/ops/incidents/` | ✅ | Incidents | Keep |
| `docs/risk/` | ✅ | Risk Doku | Keep |
| `docs/risk/roadmaps/` | ✅ | Risk Roadmaps | Keep |
| `docs/audit/` | ✅ | Audit Reports | Keep |
| `docs/_worklogs/` | ✅ | Work Logs | Keep |
| `docs/trigger_training/` | ✅ | Feature Doku | Keep |
| `docs/learning_promotion/` | ✅ | Feature Doku | Keep |
| `docs/runbooks/` | ✅ | Runbooks | Keep |
| `docs/ai/` | ✅ | AI Guides | Keep |

### Root docs/ Dateien (viele direkt in docs/)

**Assessment:** docs/ ist sehr groß aber größtenteils strukturiert.
- Prüfen ob root-level docs/ files in Subfolder gehören
- Sicherstellen docs/README.md existiert als Navigation

### Neu zu erstellende Ordner

- `docs/architecture/` (für ADRs)
- `docs/dev/` (für Developer Guides)
- `docs/features/` (für Feature-spezifische Docs)
- `docs/ops/reports/` (für alle Implementation Reports)
- `docs/ops/reports/phases/` (für Phase Reports)

---

## 📁 examples/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `examples/resilience/` | ✅ | Code Examples | Keep |

**Assessment:** Gut strukturiert, behalten.

---

## 📁 live_runs/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `live_runs/` | ✅ | Runtime Artifacts | Check .gitignore (should likely be ignored) |

**Assessment:** Runtime data sollte nicht committed sein.

---

## 📁 logs/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `logs/` | ✅ | Log Files | Check .gitignore (should be ignored) |

**Assessment:** Logs sollten nicht committed sein.

---

## 📁 notebooks/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `notebooks/r_and_d_experiment_analysis_template.py` | ✅ | Template | Keep |

**Assessment:** Minimal, gut.

---

## 📁 patches/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `patches&#47;*.patch` | ✅ | Git Patches | Keep |
| Root `COMPONENT_VAR_ROADMAP.patch` | 🔀 | Sollte hier sein | **Move** → `patches/` |

---

## 📁 policy_packs/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `policy_packs&#47;*.yml` | ✅ | Policy Configs | Keep |

---

## 📁 reports/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `reports&#47;audit&#47;`, `reports/experiments/`, etc. | ❓ | Generated Reports | **Check .gitignore** - sollten ignored sein |
| `reports&#47;*.tsv` | ❓ | TSV Reports | **Check .gitignore** |

**Assessment:** reports/ sollte großteils in .gitignore sein. README erstellen was committed vs. generated ist.

---

## 📁 results/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `results/` | ❓ | Backtest Results | **Check .gitignore** - sollten ignored sein |

---

## 📁 scripts/

**Gesamtstruktur:** 156 Python + 92 Shell Scripts!

### Unterordner

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `scripts/ops/` | ✅ | Ops Scripts (gut!) | Keep |
| `scripts/obs/` | ✅ | Observability Scripts | Keep |
| `scripts/ci/` | ✅ | CI Scripts | Keep |
| `scripts/automation/` | ✅ | Automation Scripts | Keep |
| `scripts/workflows/` | ✅ | Workflow Scripts | Keep |
| `scripts/dev/` | ✅ | Dev Scripts | Keep |

### Root scripts/ Files (sollten in Subfolders sein)

Viele Scripts direkt in `scripts/`:
- `run_audit.sh`, `pr_audit_scan.sh`, etc.
- `run_smoke_tests.sh`, `render_last_report.sh`, etc.

**Aktion:** Root-level scripts/ files in passende Subfolder sortieren.

---

## 📁 src/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `src/` | ✅ | 341 Python Files, 14 MD | Keep (Produktiv-Code) |

**Assessment:** Struktur prüfen, ob .md Files (READMEs) sinnvoll platziert sind.

---

## 📁 templates/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `templates/bash/`, `templates/ops/`, `templates/peak_trade_dashboard/`, `templates/quarto/` | ✅ | Templates | Keep |

---

## 📁 test_runs/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `test_runs/` | ❓ | Test Artifacts | **Check .gitignore** |

---

## 📁 tests/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `tests/` | ✅ | 264 Test Files | Keep |

---

## 📁 venv/

| Pfad | Status | Analyse | Aktion |
|------|--------|---------|--------|
| `venv&#47;` | ✅ | Virtual Environment | Should be in .gitignore |

---

## SUMMARY: Key Actions

### 🔴 CRITICAL: Dubletten (Delete)

1. `RISK_LAYER_ROADMAP.md` (root) → existiert in `docs/risk/`
2. `RISK_LAYER_V1_IMPLEMENTATION_REPORT.md` (root) → existiert in `docs/risk/`
3. `RISK_LAYER_V1_PRODUCTION_READY_REPORT.md` (root) → existiert in `docs/risk/`
4. `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md` (root) → existiert in `docs/ops/`
5. `run_regime_experiments.sh` (root) → existiert in `archive&#47;legacy_scripts&#47;`
6. `config.toml` (root) → wahrscheinlich Dublette von `config/config.toml`

### 🟡 Move Operations

**Root → docs/:**
- 18 Markdown-Dateien von Root nach passende docs/ Subfolder

**Root → docker/:**
- `docker-compose.obs.yml`

**Root → patches/:**
- `COMPONENT_VAR_ROADMAP.patch`

**scripts/ root → scripts/subfolders:**
- Diverse root-level scripts in passende Subfolder

### 🔵 New Directories to Create

- `docs/architecture/`
- `docs/dev/knowledge/`
- `docs/features/psychology/`
- `docs/ops/reports/`
- `docs/ops/reports/phases/`

### 🟢 .gitignore Updates Needed

Check und ggf. hinzufügen:
- `data/`
- `live_runs/`
- `logs/`
- `reports/` (oder Teile davon)
- `results/`
- `test_runs/`
- `*.log` files in root
- `venv&#47;` (sollte schon drin sein)

### ⚪ Investigate

- `gitignore` file (falscher Name? sollte `.gitignore` sein)
- `audit.log`, `tests.log` in root
- `archive&#47;PeakTradeRepo&#47;` - komplett altes Repo, Nutzen?

---

## Reference Check Status

Für Deletes: Reference-Checks werden vor Ausführung durchgeführt mit:
```bash
rg "FILENAME" -S .
```

Dokumentation in `CLEANUP_PLAN.md`.
