# Cleanup Changes Log

**Datum:** 2025-12-27  
**Branch:** `chore/repo-cleanup-structured-20251227`

Alle Änderungen werden hier chronologisch dokumentiert.

---

## Phase 1: Neue Ordner erstellen

```bash
mkdir -p docs/architecture
mkdir -p docs/dev/knowledge
mkdir -p docs/features/psychology
mkdir -p docs/ops/reports/phases
mkdir -p docs/learning_promotion
mkdir -p scripts/run
mkdir -p scripts/utils
```

**Status:** ✅ Completed

---

## Phase 2: Markdown-Dateien (Root → docs/)

### Architecture
- ✅ `ADR_0001_Peak_Tool_Stack.md` → `docs/architecture/`

### Dev/Knowledge
- ✅ `IMPLEMENTATION_SUMMARY_KNOWLEDGE_DB.md` → `docs/dev/knowledge/`
- ✅ `KNOWLEDGE_API_IMPLEMENTATION_SUMMARY.md` → `docs/dev/knowledge/`
- ✅ `KNOWLEDGE_API_SMOKE_TESTS.md` → `docs/dev/knowledge/`

### Features/Psychology
- ✅ `PSYCHOLOGY_HEATMAP_README.md` → `docs/features/psychology/`
- ✅ `PSYCHOLOGY_HEURISTICS_IMPLEMENTATION.md` → `docs/features/psychology/`
- ✅ `PSYCHOLOGY_HEURISTICS_README.md` → `docs/features/psychology/`

### Ops
- ✅ `NEXT_STEPS_WORKFLOW_DOCS.md` → `docs/ops/`
- ✅ `P0_GUARDRAILS_QUICK_REFERENCE.md` → `docs/ops/`
- ✅ `Peak_Trade_TOOLING_AND_EVIDENCE_CHAIN_RUNBOOK.md` → `docs/ops/`

### Ops Reports
- ✅ `AUTOMATION_SETUP_REPORT.md` → `docs/ops/reports/`
- ✅ `CI_LARGE_PR_IMPLEMENTATION_REPORT.md` → `docs/ops/reports/`
- ✅ `OPS_DOCTOR_IMPLEMENTATION_SUMMARY.md` → `docs/ops/reports/`

### Ops Reports - Phases
- ✅ `CYCLES_3_5_COMPLETION_REPORT.md` → `docs/ops/reports/phases/`
- ✅ `PHASE_16L_IMPLEMENTATION_SUMMARY.md` → `docs/ops/reports/phases/`
- ✅ `PHASE_16L_VERIFICATION_REPORT.md` → `docs/ops/reports/phases/`

### Risk
- ✅ `RISK_LAYER_ROADMAP.md` → `docs/risk/`
- ✅ `RISK_LAYER_V1_IMPLEMENTATION_REPORT.md` → `docs/risk/`
- ✅ `RISK_LAYER_V1_PRODUCTION_READY_REPORT.md` → `docs/risk/`

### Risk Roadmaps
- ✅ `COMPONENT_VAR_ROADMAP_PATCHED.md` → `docs/risk/roadmaps/`

### Learning Promotion
- ✅ `CHANGELOG_LEARNING_PROMOTION_LOOP.md` → `docs/learning_promotion/`

**Total:** 21 files moved

---

## Phase 3: Scripts (Root scripts/ → Subfolders)

### Ops
- ✅ `scripts/ops/run_audit.sh` → `scripts/ops/`
- ✅ `scripts/ops/pr_audit_scan.sh` → `scripts/ops/`

### Run
- ✅ `scripts/run/run_smoke_tests.sh` → `scripts/run/`
- ✅ `scripts/run/run_phase3_robustness.sh` → `scripts/run/`
- ✅ `scripts/run/run_regime_btcusdt_experiments.sh` → `scripts/run/`

### Utils
- ✅ `scripts/utils/render_last_report.sh` → `scripts/utils/`
- ✅ `scripts/utils/slice_from_backup.sh` → `scripts/utils/`
- ✅ `scripts/utils/install_desktop_shortcuts.sh` → `scripts/utils/`
- ✅ `scripts/utils/check_claude_code_ready.sh` → `scripts/utils/`
- ✅ `scripts/utils/claude_code_auth_reset.sh` → `scripts/utils/`

### Workflows
- ✅ `scripts/workflows/quick_pr_merge.sh` → `scripts/workflows/`
- ✅ `scripts/workflows/finalize_workflow_docs_pr.sh` → `scripts/workflows/`
- ✅ `scripts/workflows/git_push_and_pr.sh` → `scripts/workflows/`
- ✅ `scripts/workflows/post_merge_workflow.sh` → `scripts/workflows/`
- ✅ `scripts/workflows/post_merge_workflow_pr203.sh` → `scripts/workflows/`

### CI
- ✅ `scripts/ci/validate_git_state.sh` → `scripts/ci/`

### Automation
- ✅ `scripts/automation/add_issues_to_project.sh` → `scripts/automation/`
- ✅ `scripts/automation/update_pr_final_report_post_merge.sh` → `scripts/automation/`

### Dev
- ✅ `scripts/dev/test_knowledge_api_smoke.sh` → `scripts/dev/`

**Total:** 19 scripts moved

---

## Phase 4: Config & Patch Consolidation

- ✅ `COMPONENT_VAR_ROADMAP.patch` → `patches/`
- ✅ `docker-compose.obs.yml` → `docker/`

**Note:** `config.toml` (root) kept - it's a "simplified" version, different from `config/config.toml`

---

## Phase 5: Dubletten & Dead Files Removed

### Deleted Files

| Datei | Grund | Reference Check |
|-------|-------|-----------------|
| `run_regime_experiments.sh` | Dublette (existiert in archive/legacy_scripts/) | ✅ rg: 6 hits (nur docs/archive refs) |
| `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md` | Dublette (docs/ops/ ist source of truth) | ✅ Consolidated to docs/ops/ |
| `gitignore` | Obsolet (`.gitignore` existiert) | ✅ No code refs |
| ~~`scripts&sol;cleanup_repo.sh`~~ | Obsolet/Test-Script | ✅ rg: 5 hits (nur self-refs) |

**Total:** 4 files deleted

---

## Phase 6: Reference Updates

Files updated with new paths:

- [ ] `README.md` - Repository Structure section
- [ ] `README_REGISTRY.md` - All doc paths
- [ ] `docs/ops/README.md` - Operator guide links
- [ ] `docs/risk/README.md` - Risk doc links
- [ ] Scripts with hardcoded paths (TBD after grep)

---

## Phase 7: New Documentation Created

- [ ] `docs/architecture/REPO_STRUCTURE.md`
- [ ] `archive&#47;README.md`
- [ ] `config/README.md`
- [ ] Update `docs/README.md`
- [ ] `docs/ops/cleanup/CLEANUP_REPORT.md`
- [ ] `docs/ops/cleanup/INVENTORY_TREE_AFTER.txt`

---

**Status:** 🔄 In Progress
