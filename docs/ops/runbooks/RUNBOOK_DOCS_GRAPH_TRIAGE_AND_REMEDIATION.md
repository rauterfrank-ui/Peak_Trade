# RUNBOOK: Docs Graph Triage & Remediation

**Version:** 1.0.0  
**Last Updated:** 2026-01-13  
**Owner:** Docs Infrastructure Team  
**Scope:** Docs-only / Ops tooling (no runtime impact)

---

## Purpose

This runbook guides operators through the process of:
1. Generating docs graph snapshots
2. Running triage analysis (broken targets + orphans)
3. Interpreting triage outputs
4. Remediating broken links and orphaned pages
5. Verifying fixes locally
6. Opening safe docs-only PRs

---

## Pre-Flight Checklist

Before running triage or remediation:

- [ ] **Working directory:** Ensure you are in repo root (`Peak_Trade/`)
- [ ] **Clean working tree:** Run `git status` — no unexpected uncommitted changes
- [ ] **Dependencies:** `uv` available (for Python tooling)
- [ ] **Branch hygiene:** On `main` or a clean feature branch
- [ ] **Snapshot exists:** Verify baseline snapshot at `docs&#47;ops&#47;graphs&#47;snapshots&#47;2026-01-13&#47;`

---

## Step 1: Regenerate Snapshot (Optional)

**When to run:**  
After merging docs PRs or when you want to measure improvement from baseline.

**Command:**
```bash
uv run python scripts/ops/docs_graph_snapshot.py \
    --out docs/ops/graphs/snapshots/$(date +%Y-%m-%d)/docs_graph_snapshot.json \
    --fail-on-broken
```

**Expected Artifacts:**
- New snapshot JSON at `docs&#47;ops&#47;graphs&#47;snapshots&#47;YYYY-MM-DD&#47;docs_graph_snapshot.json`
- Exit code 1 if broken links found (expected during triage phase)

**Success Criteria:**
- Snapshot file created
- File size >10KB (957 nodes baseline ~= ~130KB)
- Valid JSON structure

**Notes:**
- Snapshot generation is **deterministic** — running twice on same repo state produces identical output
- Tool includes default roots: `docs&#47;WORKFLOW_FRONTDOOR.md`, `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md`, `docs&#47;ops&#47;README.md`, `docs&#47;INSTALLATION_QUICKSTART.md`

---

## Step 2: Run Triage Analysis

**When to run:**  
After generating or receiving a new snapshot; as part of weekly docs hygiene.

### 2.1 Quick Triage (Using Wrapper Script)

**Command:**
```bash
./scripts/ops/pt_docs_graph_triage.sh
```

**What it does:**
- Reads latest snapshot (`docs&#47;ops&#47;graphs&#47;snapshots&#47;2026-01-13&#47;docs_graph_snapshot.json`)
- Generates two markdown reports:
  - `broken_targets.md` (categorized by reason)
  - `orphans.md` (categorized by doc area)
- Prints summary to stdout

**Expected Output:**
```
======================================================================
PEAK_TRADE DOCS GRAPH TRIAGE
======================================================================
Snapshot: docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot.json
Output:   docs/ops/graphs/snapshots/2026-01-13
======================================================================

======================================================================
DOCS GRAPH TRIAGE SUMMARY
======================================================================
Snapshot: docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot.json
Output:   docs/ops/graphs/snapshots/2026-01-13

Broken targets:  181
Broken anchors:  7
Orphaned pages:  610

Reports generated:
  - docs/ops/graphs/snapshots/2026-01-13/broken_targets.md
  - docs/ops/graphs/snapshots/2026-01-13/orphans.md
======================================================================
```

**Exit Code:** Always 0 (this is triage, not a gate)

### 2.2 Manual Triage (Direct Python Call)

**Command:**
```bash
uv run python scripts/ops/docs_graph_triage.py \
    --snapshot docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot.json \
    --out-dir docs/ops/graphs/snapshots/2026-01-13
```

**Use case:** Custom snapshot path or output directory.

---

## Step 3: Interpret Triage Outputs

### 3.1 Broken Targets Report

**Location:** `docs&#47;ops&#47;graphs&#47;snapshots&#47;2026-01-13&#47;broken_targets.md`

**Structure:**
- Summary by reason (e.g., "file not found", "outside repo")
- Detailed breakdown with source file, raw target, resolved path

**How to prioritize:**
1. **User-facing first:** Fix broken links in `docs&#47;INSTALLATION_QUICKSTART.md`, `docs&#47;WORKFLOW_FRONTDOOR.md`
2. **By reason:**
   - `file not found` → Likely renamed or deleted files (easy fix: update path or remove link)
   - `outside repo` → Relative path escapes; fix with correct relative path
   - Placeholder paths (e.g., `...`) → Replace or remove

### 3.2 Orphans Report

**Location:** `docs&#47;ops&#47;graphs&#47;snapshots&#47;2026-01-13&#47;orphans.md`

**Structure:**
- Summary by area (e.g., "root", "docs/ops", "docs/ops/runbooks")
- Detailed list of orphaned files by area

**How to prioritize:**
1. **Runbooks and user guides:** Medium priority — should be linked from relevant index
2. **Historical artifacts (PHASE*.md in root):** Low priority — archive candidates
3. **Old merge logs:** Very low priority — verify EVIDENCE_INDEX coverage; archive if old

**Remediation strategies:**
- **Link:** Add to relevant README or index page
- **Archive:** Move to `docs&#47;ops&#47;_archive&#47;` subdirectories
- **Delete:** If fully superseded and no historical value

---

## Step 4: Remediation Workflow

### 4.1 Fixing Broken Targets

**Example: File not found**

Issue: `PHASE4E_EXECUTION_SUMMARY.md` links to `PHASE4E_CLOSEOUT_OPERATOR_GUIDE.md` (missing)

**Investigation:**
```bash
# Search for the file (maybe renamed?)
find . -name "*CLOSEOUT*OPERATOR*" -type f

# Search for similar content
grep -r "PHASE4E.*closeout" docs/
```

**Resolution options:**
1. **File was renamed:** Update link to new filename
2. **Content was merged:** Update link to consolidated doc
3. **Link is obsolete:** Remove link

**Fix:**
```bash
# Edit source file
vim PHASE4E_EXECUTION_SUMMARY.md

# Remove or update the broken link
# Commit with descriptive message
git commit -m "docs: fix broken link to PHASE4E closeout guide"
```

---

### 4.2 Fixing Orphaned Pages

**Example: Orphaned runbook**

Issue: `docs&#47;ops&#47;runbooks&#47;RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md` is not linked.

**Resolution:**
1. Open `docs&#47;ops&#47;runbooks&#47;README.md` (runbooks index)
2. Add entry in appropriate section:
   ```markdown
   - [AI Autonomy Control Center Operations](RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md)
   ```
3. Commit:
   ```bash
   git commit -m "docs: link control center operations runbook from index"
   ```

---

### 4.3 Archiving Obsolete Docs

**Example: Archive old phase reports**

Issue: 50+ `PHASE*_IMPLEMENTATION_*.md` files in root, all orphaned.

**Resolution:**
```bash
# Create archive directory
mkdir -p docs/ops/_archive/phase_reports

# Move files
mv PHASE*_IMPLEMENTATION_*.md docs/ops/_archive/phase_reports/
mv PHASE*_CHANGED_FILES.txt docs/ops/_archive/phase_reports/

# Create index in archive
cat > docs/ops/_archive/phase_reports/README.md <<'EOF'
# Phase Implementation Reports (Archive)

Historical implementation reports from Peak_Trade development phases.

**Status:** Archived (read-only, historical context only)
EOF

# Commit
git commit -m "docs: archive historical phase implementation reports"
```

---

## Step 5: Validate Locally

### 5.1 Lint Check (If Applicable)

**Command:**
```bash
# Check for common markdown issues (if linter exists)
# Example placeholder - adapt to your linter
# markdownlint docs/
```

### 5.2 Verify Docs Gates (If Implemented)

**Command:**
```bash
# Example: If docs reference targets gate exists
./scripts/ops/verify_docs_reference_targets.sh
```

**Notes:**
- Docs gates are informational during triage phase
- Broken links are **expected** during remediation; gate should not block merges

### 5.3 Re-run Triage

After making fixes, regenerate snapshot and triage to measure improvement:

```bash
# Regenerate snapshot
uv run python scripts/ops/docs_graph_snapshot.py \
    --out docs/ops/graphs/snapshots/$(date +%Y-%m-%d)/docs_graph_snapshot.json

# Run triage
./scripts/ops/pt_docs_graph_triage.sh docs/ops/graphs/snapshots/$(date +%Y-%m-%d)/docs_graph_snapshot.json
```

**Success criteria:**
- Broken targets count decreased
- Orphans count decreased (or unchanged if intentionally left)

---

## Step 6: Open Docs-Only PR

### 6.1 Branch Naming

**Convention:** `docs/triage-YYYY-MM-DD-description`

**Example:**
```bash
git checkout -b docs/triage-2026-01-13-broken-links-runbooks
```

### 6.2 Commit Style

**Format:**
```
docs: <action> <subject>

- Specific change 1
- Specific change 2
```

**Examples:**
```
docs: fix broken links in installation quickstart

- Update path to PHASE4E closeout guide
- Remove obsolete link to missing runbook

docs: link orphaned control center runbooks

- Add links to runbooks/README.md for AI autonomy runbooks
```

### 6.3 PR Description Template

```markdown
## Type
- [x] Docs-only (no runtime impact)

## Summary
Docs graph triage remediation — addressing broken links and orphaned pages.

## Changes
- **Broken links fixed:** 5 (file not found)
- **Orphans linked:** 3 (runbooks)
- **Files archived:** 0

## Triage Evidence
- Baseline snapshot: `docs/ops/graphs/snapshots/2026-01-13/`
- Triage reports: `broken_targets.md`, `orphans.md`

## Verification
- [x] Locally validated broken links resolved
- [x] Re-ran triage — improvement confirmed
- [x] No new broken links introduced

## Related
- Part of Phase 9A: Docs Graph Triage initiative
- See: docs/ops/graphs/TRIAGE_2026-01-13.md
```

### 6.4 Safe Merge Criteria

**Required:**
- [x] Docs-only changes (no `.py`, `.sh`, `.yaml` except docs tooling)
- [x] No CI/CD changes
- [x] Passes existing CI checks (linters, if any)
- [x] Self-review: all links manually verified

**Optional (for high-impact PRs):**
- [ ] Second reviewer (for changes to main docs frontdoor)

---

## Step 7: Rollback / Revert Guidance

### 7.1 If Broken Links Introduced

**Symptom:** CI fails on docs gate, or manual testing reveals broken link

**Resolution:**
```bash
# Revert specific commit
git revert <commit-sha>

# Or revert entire PR merge
git revert -m 1 <merge-commit-sha>

# Push revert
git push origin main
```

### 7.2 If Wrong Files Archived

**Symptom:** User reports missing documentation

**Resolution:**
```bash
# Restore from archive
git mv docs/ops/_archive/phase_reports/FILE.md ./

# Re-link in appropriate index
# Commit restoration
git commit -m "docs: restore FILE.md from archive (still in use)"
```

---

## Troubleshooting

### Issue: Triage script fails with "Snapshot file not found"

**Cause:** Incorrect path or snapshot not yet generated

**Resolution:**
```bash
# Check if snapshot exists
ls -la docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot.json

# If missing, generate it
uv run python scripts/ops/docs_graph_snapshot.py \
    --out docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot.json
```

### Issue: Triage script exits with code 1

**Cause:** Unexpected error (snapshot corrupt, invalid JSON)

**Resolution:**
```bash
# Validate JSON
python3 -m json.tool docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot.json > /dev/null

# If invalid, regenerate snapshot
uv run python scripts/ops/docs_graph_snapshot.py \
    --out docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot.json
```

### Issue: Token policy violations in generated reports

**Cause:** Triage script not escaping paths correctly

**Resolution:**
- Report issue to Docs Infrastructure team
- Manually fix escaped paths in generated `.md` files (replace `/` with `&#47;` in inline code)

---

## Automation & Cadence

### Recommended Schedule

- **Weekly:** Run triage on `main` branch (snapshot + triage)
- **Per-PR:** Optional; only for large docs refactors
- **Quarterly:** Full remediation sprint (target: <50 broken, <200 orphans)

### Future Enhancements

- [ ] CI integration: Auto-comment triage summary on docs PRs
- [ ] Trend tracking: Store metrics over time in `docs&#47;ops&#47;graphs&#47;trends&#47;`
- [ ] Auto-archive: Script to batch-move old orphaned phase reports

---

## References

- **Triage Baseline:** [`docs&#47;ops&#47;graphs&#47;TRIAGE_2026-01-13.md`](../graphs/TRIAGE_2026-01-13.md)
- **Snapshot Tool:** [`scripts&#47;ops&#47;docs_graph_snapshot.py`](../../../scripts/ops/docs_graph_snapshot.py)
- **Triage Tool:** [`scripts&#47;ops&#47;docs_graph_triage.py`](../../../scripts/ops/docs_graph_triage.py)
- **Triage Wrapper:** [`scripts&#47;ops&#47;pt_docs_graph_triage.sh`](../../../scripts/ops/pt_docs_graph_triage.sh)

---

## Contact & Escalation

**Docs Infrastructure Team:** See `docs&#47;ops&#47;README.md` for maintainer list  
**Escalation:** For critical broken links in production-facing docs, file urgent issue with `docs-critical` label
