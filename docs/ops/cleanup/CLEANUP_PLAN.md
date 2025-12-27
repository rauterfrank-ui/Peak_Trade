# Repository Cleanup Plan

**Datum:** 2025-12-27  
**Branch:** `chore/repo-cleanup-structured-20251227`  
**Base Commit:** `a4850c66b8974281c8f18204ed48813c4352b995`

---

## Executive Summary

Nach vollständiger Inventur und Reference-Checks:
- **18 Root-Level Markdown-Dateien** → in docs/ organisieren
- **20 Root-Level Scripts** in scripts/ → in Subfolder organisieren  
- **3 Artifacts** (logs, patches) → bereinigen
- **1 Config-Dublette** → konsolidieren
- **1 Script-Dublette** → entfernen
- **Neue Ordner-Struktur** für bessere Organisation
- **.gitignore** bereits gut konfiguriert (verified)

**Risiko:** 🟢 LOW - Alle Moves sind non-breaking, Reference-Checks durchgeführt

---

## Zielstruktur (After Tree)

```
Peak_Trade/
├── README.md                    # Bleibt
├── README_REGISTRY.md           # Bleibt
├── pyproject.toml               # Bleibt
├── pytest.ini                   # Bleibt
├── requirements.txt             # Bleibt
├── uv.lock                      # Bleibt
├── Makefile                     # Bleibt
│
├── archive/                     # ✅ Bereits gut strukturiert
│   ├── README.md                # NEU: Index
│   ├── full_files_stand_02.12.2025/
│   ├── legacy_docs/
│   ├── legacy_scripts/
│   └── PeakTradeRepo/
│
├── config/                      # ✅ Gut strukturiert
│   ├── README.md                # NEU: Config Guide
│   └── ... (existing)
│
├── docker/                      # Konsolidiert
│   ├── compose.yml
│   ├── docker-compose.obs.yml   # MOVED from root
│   └── ...
│
├── docs/
│   ├── README.md                # Updated: Navigation
│   │
│   ├── architecture/            # NEU
│   │   ├── ADR_0001_Peak_Tool_Stack.md
│   │   └── REPO_STRUCTURE.md    # NEU: Erklärt Repo-Layout
│   │
│   ├── dev/                     # NEU
│   │   ├── knowledge/
│   │   │   ├── IMPLEMENTATION_SUMMARY_KNOWLEDGE_DB.md
│   │   │   ├── KNOWLEDGE_API_IMPLEMENTATION_SUMMARY.md
│   │   │   └── KNOWLEDGE_API_SMOKE_TESTS.md
│   │   └── guides/              # für später
│   │
│   ├── features/                # NEU
│   │   └── psychology/
│   │       ├── PSYCHOLOGY_HEATMAP_README.md
│   │       ├── PSYCHOLOGY_HEURISTICS_IMPLEMENTATION.md
│   │       └── PSYCHOLOGY_HEURISTICS_README.md
│   │
│   ├── ops/                     # ✅ Erweitert
│   │   ├── README.md            # Updated
│   │   ├── P0_GUARDRAILS_QUICK_REFERENCE.md
│   │   ├── NEXT_STEPS_WORKFLOW_DOCS.md
│   │   ├── Peak_Trade_TOOLING_AND_EVIDENCE_CHAIN_RUNBOOK.md
│   │   ├── REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md  # Root-Version consolidated
│   │   │
│   │   ├── reports/             # NEU
│   │   │   ├── AUTOMATION_SETUP_REPORT.md
│   │   │   ├── CI_LARGE_PR_IMPLEMENTATION_REPORT.md
│   │   │   ├── OPS_DOCTOR_IMPLEMENTATION_SUMMARY.md
│   │   │   │
│   │   │   └── phases/          # NEU
│   │   │       ├── CYCLES_3_5_COMPLETION_REPORT.md
│   │   │       ├── PHASE_16L_IMPLEMENTATION_SUMMARY.md
│   │   │       └── PHASE_16L_VERIFICATION_REPORT.md
│   │   │
│   │   ├── cleanup/             # Dieser Cleanup
│   │   ├── merge_logs/          # ✅ Existing
│   │   └── incidents/           # ✅ Existing
│   │
│   ├── risk/                    # ✅ Erweitert
│   │   ├── README.md            # ✅ Existing
│   │   ├── RISK_LAYER_ROADMAP.md         # Root Version
│   │   ├── RISK_LAYER_V1_IMPLEMENTATION_REPORT.md
│   │   ├── RISK_LAYER_V1_PRODUCTION_READY_REPORT.md
│   │   │
│   │   └── roadmaps/            # ✅ Existing
│   │       └── COMPONENT_VAR_ROADMAP_PATCHED.md
│   │
│   ├── learning_promotion/      # ✅ Erweitert
│   │   └── CHANGELOG_LEARNING_PROMOTION_LOOP.md
│   │
│   ├── audit/                   # ✅ Existing
│   ├── runbooks/                # ✅ Existing
│   ├── trigger_training/        # ✅ Existing
│   └── ...
│
├── patches/
│   ├── COMPONENT_VAR_ROADMAP.patch  # MOVED from root
│   └── ... (existing)
│
├── scripts/
│   ├── ops/                     # ✅ Erweitert
│   │   ├── run_audit.sh         # MOVED from scripts/
│   │   ├── pr_audit_scan.sh     # MOVED from scripts/
│   │   └── ... (existing)
│   │
│   ├── run/                     # NEU
│   │   ├── run_smoke_tests.sh   # MOVED from scripts/
│   │   ├── run_phase3_robustness.sh
│   │   └── run_regime_btcusdt_experiments.sh
│   │
│   ├── utils/                   # NEU
│   │   ├── slice_from_backup.sh
│   │   ├── install_desktop_shortcuts.sh
│   │   ├── check_claude_code_ready.sh
│   │   ├── claude_code_auth_reset.sh
│   │   └── render_last_report.sh
│   │
│   ├── workflows/               # ✅ Existing, erweitert
│   │   ├── quick_pr_merge.sh    # MOVED from scripts/
│   │   ├── finalize_workflow_docs_pr.sh
│   │   ├── git_push_and_pr.sh
│   │   ├── post_merge_workflow.sh
│   │   ├── post_merge_workflow_pr203.sh
│   │   └── ... (existing)
│   │
│   ├── dev/                     # ✅ Existing
│   ├── ci/                      # ✅ Existing
│   ├── obs/                     # ✅ Existing
│   └── automation/              # ✅ Existing
│
├── src/                         # ✅ No changes (produktiv code)
├── tests/                       # ✅ No changes
├── templates/                   # ✅ No changes
├── examples/                    # ✅ No changes
├── policy_packs/                # ✅ No changes
└── notebooks/                   # ✅ No changes
```

---

## Move/Consolidate Operations

### Phase 1: Neue Ordner erstellen

```bash
mkdir -p docs/architecture
mkdir -p docs/dev/knowledge
mkdir -p docs/features/psychology
mkdir -p docs/ops/reports/phases
mkdir -p docs/learning_promotion
mkdir -p scripts/run
mkdir -p scripts/utils
```

### Phase 2: Markdown-Dateien (Root → docs/)

| Datei (Root) | Ziel | Begründung |
|--------------|------|------------|
| `ADR_0001_Peak_Tool_Stack.md` | `docs/architecture/` | Architecture Decision Record |
| `AUTOMATION_SETUP_REPORT.md` | `docs/ops/reports/` | Implementation Report |
| `CHANGELOG_LEARNING_PROMOTION_LOOP.md` | `docs/learning_promotion/` | Feature Changelog |
| `CI_LARGE_PR_IMPLEMENTATION_REPORT.md` | `docs/ops/reports/` | CI Report |
| `COMPONENT_VAR_ROADMAP_PATCHED.md` | `docs/risk/roadmaps/` | Risk Roadmap |
| `CYCLES_3_5_COMPLETION_REPORT.md` | `docs/ops/reports/phases/` | Phase Report |
| `IMPLEMENTATION_SUMMARY_KNOWLEDGE_DB.md` | `docs/dev/knowledge/` | Knowledge DB Doku |
| `KNOWLEDGE_API_IMPLEMENTATION_SUMMARY.md` | `docs/dev/knowledge/` | Knowledge API Doku |
| `KNOWLEDGE_API_SMOKE_TESTS.md` | `docs/dev/knowledge/` | Knowledge Tests Doku |
| `NEXT_STEPS_WORKFLOW_DOCS.md` | `docs/ops/` | Workflow Guide |
| `OPS_DOCTOR_IMPLEMENTATION_SUMMARY.md` | `docs/ops/reports/` | Ops Report |
| `P0_GUARDRAILS_QUICK_REFERENCE.md` | `docs/ops/` | Ops Quick Ref |
| `Peak_Trade_TOOLING_AND_EVIDENCE_CHAIN_RUNBOOK.md` | `docs/ops/` | Runbook |
| `PHASE_16L_IMPLEMENTATION_SUMMARY.md` | `docs/ops/reports/phases/` | Phase Report |
| `PHASE_16L_VERIFICATION_REPORT.md` | `docs/ops/reports/phases/` | Phase Report |
| `PSYCHOLOGY_HEATMAP_README.md` | `docs/features/psychology/` | Feature Doku |
| `PSYCHOLOGY_HEURISTICS_IMPLEMENTATION.md` | `docs/features/psychology/` | Feature Impl |
| `PSYCHOLOGY_HEURISTICS_README.md` | `docs/features/psychology/` | Feature Doku |
| `RISK_LAYER_ROADMAP.md` | `docs/risk/` | Risk Roadmap |
| `RISK_LAYER_V1_IMPLEMENTATION_REPORT.md` | `docs/risk/` | Risk Report |
| `RISK_LAYER_V1_PRODUCTION_READY_REPORT.md` | `docs/risk/` | Risk Report |

**Commands:**
```bash
# Architecture
git mv ADR_0001_Peak_Tool_Stack.md docs/architecture/

# Dev/Knowledge
git mv IMPLEMENTATION_SUMMARY_KNOWLEDGE_DB.md docs/dev/knowledge/
git mv KNOWLEDGE_API_IMPLEMENTATION_SUMMARY.md docs/dev/knowledge/
git mv KNOWLEDGE_API_SMOKE_TESTS.md docs/dev/knowledge/

# Features
git mv PSYCHOLOGY_HEATMAP_README.md docs/features/psychology/
git mv PSYCHOLOGY_HEURISTICS_IMPLEMENTATION.md docs/features/psychology/
git mv PSYCHOLOGY_HEURISTICS_README.md docs/features/psychology/

# Ops
git mv NEXT_STEPS_WORKFLOW_DOCS.md docs/ops/
git mv P0_GUARDRAILS_QUICK_REFERENCE.md docs/ops/
git mv Peak_Trade_TOOLING_AND_EVIDENCE_CHAIN_RUNBOOK.md docs/ops/

# Ops Reports
git mv AUTOMATION_SETUP_REPORT.md docs/ops/reports/
git mv CI_LARGE_PR_IMPLEMENTATION_REPORT.md docs/ops/reports/
git mv OPS_DOCTOR_IMPLEMENTATION_SUMMARY.md docs/ops/reports/

# Ops Reports - Phases
git mv CYCLES_3_5_COMPLETION_REPORT.md docs/ops/reports/phases/
git mv PHASE_16L_IMPLEMENTATION_SUMMARY.md docs/ops/reports/phases/
git mv PHASE_16L_VERIFICATION_REPORT.md docs/ops/reports/phases/

# Risk
git mv RISK_LAYER_ROADMAP.md docs/risk/
git mv RISK_LAYER_V1_IMPLEMENTATION_REPORT.md docs/risk/
git mv RISK_LAYER_V1_PRODUCTION_READY_REPORT.md docs/risk/

# Risk Roadmaps
git mv COMPONENT_VAR_ROADMAP_PATCHED.md docs/risk/roadmaps/

# Learning Promotion
git mv CHANGELOG_LEARNING_PROMOTION_LOOP.md docs/learning_promotion/
```

### Phase 3: Scripts (Root scripts/ → Subfolders)

| Script | Ziel | Begründung |
|--------|------|------------|
| `scripts/run_audit.sh` | `scripts/ops/` | Ops Tool |
| `scripts/pr_audit_scan.sh` | `scripts/ops/` | Ops Tool |
| `scripts/run_smoke_tests.sh` | `scripts/run/` | Runner |
| `scripts/run_phase3_robustness.sh` | `scripts/run/` | Runner |
| `scripts/run_regime_btcusdt_experiments.sh` | `scripts/run/` | Runner |
| `scripts/render_last_report.sh` | `scripts/utils/` | Utility |
| `scripts/slice_from_backup.sh` | `scripts/utils/` | Utility |
| `scripts/install_desktop_shortcuts.sh` | `scripts/utils/` | Utility |
| `scripts/check_claude_code_ready.sh` | `scripts/utils/` | Utility |
| `scripts/claude_code_auth_reset.sh` | `scripts/utils/` | Utility |
| `scripts/quick_pr_merge.sh` | `scripts/workflows/` | Workflow |
| `scripts/finalize_workflow_docs_pr.sh` | `scripts/workflows/` | Workflow |
| `scripts/git_push_and_pr.sh` | `scripts/workflows/` | Workflow |
| `scripts/post_merge_workflow.sh` | `scripts/workflows/` | Workflow |
| `scripts/post_merge_workflow_pr203.sh` | `scripts/workflows/` | Workflow |
| `scripts/validate_git_state.sh` | `scripts/ci/` | CI Tool |
| `scripts/add_issues_to_project.sh` | `scripts/automation/` | Automation |
| `scripts/update_pr_final_report_post_merge.sh` | `scripts/automation/` | Automation |
| `scripts/test_knowledge_api_smoke.sh` | `scripts/dev/` | Dev Test |

**Commands:**
```bash
# Ops
git mv scripts/run_audit.sh scripts/ops/
git mv scripts/pr_audit_scan.sh scripts/ops/

# Run
git mv scripts/run_smoke_tests.sh scripts/run/
git mv scripts/run_phase3_robustness.sh scripts/run/
git mv scripts/run_regime_btcusdt_experiments.sh scripts/run/

# Utils
git mv scripts/render_last_report.sh scripts/utils/
git mv scripts/slice_from_backup.sh scripts/utils/
git mv scripts/install_desktop_shortcuts.sh scripts/utils/
git mv scripts/check_claude_code_ready.sh scripts/utils/
git mv scripts/claude_code_auth_reset.sh scripts/utils/

# Workflows
git mv scripts/quick_pr_merge.sh scripts/workflows/
git mv scripts/finalize_workflow_docs_pr.sh scripts/workflows/
git mv scripts/git_push_and_pr.sh scripts/workflows/
git mv scripts/post_merge_workflow.sh scripts/workflows/
git mv scripts/post_merge_workflow_pr203.sh scripts/workflows/

# CI
git mv scripts/validate_git_state.sh scripts/ci/

# Automation
git mv scripts/add_issues_to_project.sh scripts/automation/
git mv scripts/update_pr_final_report_post_merge.sh scripts/automation/

# Dev
git mv scripts/test_knowledge_api_smoke.sh scripts/dev/
```

### Phase 4: Config & Patch Consolidation

| Operation | Reason |
|-----------|--------|
| Resolve `config.toml` vs `config/config.toml` | Determine which is active, consolidate or delete |
| `git mv COMPONENT_VAR_ROADMAP.patch patches/` | Patches gehören in patches/ |
| `git mv docker-compose.obs.yml docker/` | Docker files in docker/ |

### Phase 5: Dubletten & Dead Files

| Datei | Aktion | Reference Check | Begründung |
|-------|--------|-----------------|------------|
| `run_regime_experiments.sh` (root) | **DELETE** | ✅ Nur in docs erwähnt | Existiert in `archive/legacy_scripts/` |
| `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md` (root) | **CONSOLIDATE** | ⚠️ 20 Refs! | Root vs docs/ops/ differ - consolidate newer → docs/ops/ |
| `cleanup_repo.sh` (scripts/) | **DELETE?** | ❓ Check refs | Wahrscheinlich obsolet/test-script |
| `validate_rl_v0_1.sh` (scripts/) | **MOVE** | - | → scripts/dev/ oder scripts/run/ |

**Special: `gitignore` file in root**
- Check if this is a typo (should be `.gitignore`)
- `.gitignore` exists → delete `gitignore`

---

## Consolidation: REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md

**Problem:** Root version ≠ docs/ops/ version, 20 references!

**Solution:**
1. Compare both versions (identify newer/better)
2. Consolidate into docs/ops/ (single source of truth)
3. Delete root version
4. Update all references (20 files):
   - scripts/ops/setup_drift_guard_pr_workflow.sh
   - docs/ops/REQUIRED_CHECKS_DRIFT_GUARD_PR_WORKFLOW.md
   - docs/ops/README.md
   - docs/ops/PR_*.md (mehrere)
   - docs/ops/DRIFT_GUARD_QUICK_START.md
   - docs/PEAK_TRADE_STATUS_OVERVIEW.md

---

## Reference Updates

Nach Moves müssen folgende Referenzen aktualisiert werden:

### 1. docs/ops/README.md
- Links zu verschobenen Operator-Guides

### 2. docs/risk/README.md
- Links zu verschobenen Risk-Reports

### 3. README.md (Root)
- "Repository Structure" Sektion aktualisieren
- Links zu wichtigen Docs

### 4. README_REGISTRY.md
- Pfade aller verschobenen READMEs

### 5. Scripts mit Pfad-Referenzen
- Überprüfen mit: `rg "P0_GUARDRAILS|NEXT_STEPS|etc" scripts/`
- Update hardcoded paths

---

## New Documentation to Create

### 1. docs/architecture/REPO_STRUCTURE.md
Erklärt die Repo-Organisation:
- Was ist wo und warum
- Konventionen (wo neue Dateien hin)
- Scripts-Struktur
- Docs-Struktur

### 2. docs/README.md (Update)
Navigation-Hub für alle Docs

### 3. archive/README.md
Index was archiviert ist und warum

### 4. config/README.md
Erklärt Config-Templates und Verwendung

### 5. scripts/README.md (Update falls existiert)
Struktur der Scripts erklärt

---

## .gitignore Verification

**Already Covered (✅):**
- `/data/`
- `/results/`
- `/reports/`
- `logs/`
- `live_runs/`
- `test_runs/`
- `*.log`
- `venv/`
- Guards: `/*_REPORT.md`, `/*_SUMMARY.md`

**No Action Needed** - .gitignore ist bereits gut konfiguriert!

---

## Risks & Mitigations

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Broken doc links | Medium | Medium | Reference-Updates in README/docs hub |
| Script path breaks | Low | Medium | Scripts nutzen meist relative paths; grep verify |
| CI workflow breaks | Low | High | Check .github/workflows/ für hardcoded paths |
| Import breaks | Very Low | High | Nur Docs/Scripts bewegt, kein Python src/ |

**Overall Risk: 🟢 LOW**

---

## Validation Checklist

Nach Cleanup:

- [ ] `python -m compileall src` → No errors
- [ ] `pytest tests/` → All pass
- [ ] `ruff check .` → No new errors
- [ ] `ruff format --check .` → Format consistent
- [ ] Important doc links (spot check):
  - [ ] README.md links work
  - [ ] docs/ops/README.md links work
  - [ ] docs/risk/README.md links work
- [ ] Scripts executable: `find scripts/ -name "*.sh" -not -perm -u+x`
- [ ] No broken imports: `ruff check --select F401,F811`

---

## Commit Strategy

```bash
# Commit 1: Preparation
git add docs/ops/cleanup/
git commit -m "chore(repo): add cleanup inventory and plan

- SAFETY_SNAPSHOT.md: cleanup safety documentation
- INVENTORY_FILES.md: complete file inventory with analysis
- CLEANUP_PLAN.md: detailed cleanup execution plan
- INVENTORY_TREE_BEFORE.txt: repo structure snapshot

All changes are planned and documented before execution."

# Commit 2: New directories
git add docs/architecture/ docs/dev/ docs/features/ docs/ops/reports/ docs/learning_promotion/
git add scripts/run/ scripts/utils/
git commit -m "chore(repo): create new organizational directories

Prepare directory structure for file reorganization:
- docs/architecture/: ADRs and design docs
- docs/dev/knowledge/: developer guides
- docs/features/psychology/: feature-specific docs
- docs/ops/reports/: implementation reports
- docs/ops/reports/phases/: phase completion reports
- docs/learning_promotion/: feature changelogs
- scripts/run/: runner scripts
- scripts/utils/: utility scripts"

# Commit 3: Move docs
git commit -m "chore(repo): move root-level docs to proper locations

Move 21 markdown files from root to organized docs/ structure:
- Architecture docs → docs/architecture/
- Implementation reports → docs/ops/reports/
- Phase reports → docs/ops/reports/phases/
- Risk docs → docs/risk/
- Feature docs → docs/features/
- Knowledge DB docs → docs/dev/knowledge/
- Operator guides → docs/ops/

All moves use 'git mv' to preserve history."

# Commit 4: Move scripts
git commit -m "chore(repo): organize scripts/ into subfolders

Move 19 scripts from scripts/ root to organized subfolders:
- Runner scripts → scripts/run/
- Utility scripts → scripts/utils/
- Workflow scripts → scripts/workflows/
- Ops scripts → scripts/ops/
- CI scripts → scripts/ci/
- Automation scripts → scripts/automation/
- Dev scripts → scripts/dev/"

# Commit 5: Consolidate & remove duplicates
git commit -m "chore(repo): consolidate configs and remove duplicates

- Consolidate REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md
- Move patches to patches/
- Move docker-compose files to docker/
- Remove obsolete run_regime_experiments.sh (exists in archive)
- Remove or consolidate config.toml"

# Commit 6: Update references
git commit -m "docs: update references after file reorganization

Update links and paths in:
- README.md: repository structure section
- README_REGISTRY.md: all doc paths
- docs/ops/README.md: operator guide links
- docs/risk/README.md: risk doc links
- Scripts with hardcoded paths"

# Commit 7: Add new documentation
git commit -m "docs: add cleanup documentation and structure guides

- docs/architecture/REPO_STRUCTURE.md: explain repo organization
- archive/README.md: index of archived content
- config/README.md: config template guide
- docs/README.md: update navigation
- docs/ops/cleanup/CLEANUP_REPORT.md: final cleanup report
- docs/ops/cleanup/INVENTORY_TREE_AFTER.txt: final structure"
```

---

## Next Steps After Cleanup

1. **PR Creation:**
   ```bash
   git push -u origin chore/repo-cleanup-structured-20251227
   # Create PR with this CLEANUP_PLAN.md and CLEANUP_REPORT.md
   ```

2. **CI Checks:**
   - Ensure all required CI checks pass
   - Review any new linter warnings

3. **Team Review:**
   - Walk through CLEANUP_REPORT.md
   - Validate new structure makes sense

4. **Merge & Communicate:**
   - Merge to main
   - Notify team of new structure
   - Update team wikis/guides if needed

---

## Questions / Uncertainties

1. **config.toml:** Root vs config/ - welche ist aktiv? → Resolve before delete
2. **cleanup_repo.sh:** Behalten oder löschen? → Check references
3. **validate_rl_v0_1.sh:** scripts/run/ oder scripts/dev/? → Check usage
4. **archive/PeakTradeRepo/:** Komplett altes Repo - noch nützlich? → Keep for now, assess later

---

**Status:** 📋 PLAN COMPLETE - Ready for Execution  
**Next:** Execute Phase 1-7, update references, validate, commit
