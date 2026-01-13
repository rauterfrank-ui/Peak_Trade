# Docs Graph Remediation — Wave 1

**Date:** 2026-01-13  
**Baseline Snapshot:** `docs&#47;ops&#47;graphs&#47;snapshots&#47;2026-01-13&#47;docs_graph_snapshot.json`  
**Phase:** 9B  
**Status:** In Progress

---

## Executive Summary

This document tracks the first wave of systematic fixes to the docs graph baseline identified in Phase 9A triage. Wave 1 targets:

- **Broken Targets:** Reduce by >=25 (from 181 → <=156)
- **Broken Anchors:** Reduce by >=5 (from 7 → <=2)
- **Orphaned Pages:** Reduce by >=50 (from 610 → <=560)

**Risk:** LOW — Docs-only changes, no runtime impact, no gate modifications

---

## Selection Rationale

### Strategy: Impact × Effort

We prioritize fixes with:
1. **High impact** (frequently referenced, user-facing docs)
2. **Low-to-medium effort** (simple path corrections, bulk linking)
3. **Deterministic outcomes** (verifiable via snapshot re-run)

### Fix Set Categories

#### 1. Broken Targets — "Outside Repo" Paths (Priority: HIGH)

**Count:** 12 instances  
**Pattern:** `../../../` or `../` paths that escape repo boundaries

**Files Affected:**
- `.PR_PHASE0_SUMMARY.md`
- `PHASE6B_RELINK_SUMMARY.md` (5 instances)
- `docs/ops/EVIDENCE_ENTRY_TEMPLATE.md` (4 instances)
- `docs/ops/EVIDENCE_SCHEMA.md` (2 instances)

**Fix Tactic:**
- Correct relative paths to valid repo-relative paths
- If target is genuinely outside repo: convert to plain text (non-link) with `&#47;` escaping

**Expected Reduction:** 12 broken targets

---

#### 2. Broken Targets — High-Frequency Missing Files (Priority: MEDIUM)

**Count:** 15+ instances  
**Pattern:** Commonly referenced but missing/renamed files

**Top Offenders:**
- `PHASE4E_CLOSEOUT_OPERATOR_GUIDE.md` (missing)
- `.cursor&#47;rules&#47;*.mdc` (incorrect paths — files exist in repo root)
- `RESEARCH_PIPELINE.md`, `SCHEDULER.md` (missing)
- `../config.toml`, `../src/...` (relative path issues from `docs/`)

**Fix Tactic:**
- Remove link if target genuinely missing and not critical
- Correct path if file exists elsewhere
- For `.cursor&#47;rules&#47;*.mdc`: update to correct repo-root paths

**Expected Reduction:** 15 broken targets

---

#### 3. Broken Anchors — All Identified (Priority: HIGH)

**Count:** 7 instances  
**Identified in Triage Backlog:**
- AN-001: Missing anchors in `INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md`
- AN-002: `#ev-20260113-runbooks-frontdoor` in EVIDENCE_INDEX

**Fix Tactic:**
- Add missing anchor IDs where appropriate
- Update links to reference correct existing anchors
- Remove anchor fragment if no longer relevant

**Expected Reduction:** 7 broken anchors (all)

---

#### 4. Orphaned Pages — Quick Win: Runbooks (Priority: HIGH)

**Count:** 12 orphaned runbooks in `docs&#47;ops&#47;runbooks&#47;`  
**Fix Tactic:** Add links to `docs&#47;ops&#47;runbooks&#47;README.md`

**Orphaned Runbooks to Link:**
- AI Autonomy Control Center runbooks (4-5 files)
- Phase-specific Cursor Multi-Agent runbooks (3-4 files)
- Incident-specific runbooks (3-4 files)

**Expected Reduction:** 12 orphans

---

#### 5. Orphaned Pages — Quick Win: Merge Logs (Priority: MEDIUM)

**Count:** 40+ orphaned `PR_*_MERGE_LOG.md` files in `docs&#47;ops&#47;`  
**Fix Tactic:** Add bulk reference section in `docs&#47;ops&#47;EVIDENCE_INDEX.md` or create archive index

**Expected Reduction:** 40 orphans

---

## Detailed Fix List

### Broken Targets (27 targeted fixes)

| # | Source File | Broken Target | Fix Action |
|---|-------------|---------------|------------|
| 1 | `.PR_PHASE0_SUMMARY.md` | `../../src/risk_layer/types.py` | Correct to `src&#47;risk_layer&#47;types.py` |
| 2-6 | `PHASE6B_RELINK_SUMMARY.md` | `../../../PHASE6_STRATEGY_SWITCH_SANITY_EVIDENCE.md` (2x), `../STRATEGY_SWITCH_SANITY_CHECK.md` (2x), `../runbooks/RUNBOOK_PHASE6_...md` | Fix paths or remove |
| 7-10 | `docs/ops/EVIDENCE_ENTRY_TEMPLATE.md` | `../../../.github/workflows/ci.yml`, `../../../README.md`, `../../../config/bounded_live.toml`, `../../../scripts/ops/run_audit.sh` | Correct relative paths |
| 11-12 | `docs/ops/EVIDENCE_SCHEMA.md` | `../../../.github/workflows/ci.yml`, `../../../config/bounded_live.toml` | Correct relative paths |
| 13 | `PHASE4E_EXECUTION_SUMMARY.md` | `PHASE4E_CLOSEOUT_OPERATOR_GUIDE.md` | Remove link (file missing) |
| 14-16 | `PHASE8_DOCS_INTEGRITY_HARDENING_IMPLEMENTATION_SUMMARY.md` | `.cursor/rules/*.mdc` (3x) | Fix paths to `.cursor&#47;rules&#47;*.mdc` |
| 17-27 | Various `docs/*.md` | `../config.toml`, `../src/*.py`, `RESEARCH_PIPELINE.md`, etc. | Remove or correct paths |

### Broken Anchors (7 fixes)

| # | Source File | Broken Anchor | Fix Action |
|---|-------------|---------------|------------|
| 1-5 | Various | Anchors in `INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md` | Add missing `<a id="...">` tags or remove references |
| 6-7 | `docs/ops/EVIDENCE_INDEX.md` | `#ev-20260113-runbooks-frontdoor` | Add evidence entry or update anchor |

### Orphaned Pages (52 targeted links)

| # | Orphan File | Link Location | Fix Action |
|---|-------------|---------------|------------|
| 1-12 | `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_*.md`, `RUNBOOK_PHASE*_CURSOR_MULTI_AGENT.md` | `docs/ops/runbooks/README.md` | Add index entries |
| 13-52 | `docs/ops/PR_*_MERGE_LOG.md` (40 files) | `docs/ops/EVIDENCE_INDEX.md` | Add bulk archive section |

---

## Validation Plan

### Pre-Fix Baseline

```bash
./scripts/ops/pt_docs_graph_triage.sh docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot.json
```

**Expected Output:**
- Broken targets: 181
- Broken anchors: 7
- Orphans: 610

### Post-Fix Verification

```bash
./scripts/ops/pt_docs_graph_triage.sh docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot.json
```

**Expected Output:**
- Broken targets: <= 156 (reduction of >= 25)
- Broken anchors: <= 2 (reduction of >= 5)
- Orphans: <= 560 (reduction of >= 50)

---

## Success Criteria

- [x] Selection rationale documented
- [ ] All 27 broken target fixes applied
- [ ] All 7 broken anchor fixes applied
- [ ] All 52 orphan links added
- [ ] Post-fix triage confirms reductions
- [ ] No new token policy violations
- [ ] All CI checks green

---

## References

- **Baseline Snapshot:** `docs&#47;ops&#47;graphs&#47;snapshots&#47;2026-01-13&#47;docs_graph_snapshot.json`
- **Triage Report:** `docs&#47;ops&#47;graphs&#47;TRIAGE_2026-01-13.md`
- **Broken Targets Detail:** `docs&#47;ops&#47;graphs&#47;snapshots&#47;2026-01-13&#47;broken_targets.md`
- **Orphans Detail:** `docs&#47;ops&#47;graphs&#47;snapshots&#47;2026-01-13&#47;orphans.md`
