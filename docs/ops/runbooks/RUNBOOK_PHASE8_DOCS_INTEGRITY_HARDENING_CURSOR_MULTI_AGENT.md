# RUNBOOK — Phase 8: Docs Integrity Hardening

**Date:** 2026-01-12  
**Scope:** docs-only + scripts/ops (analysis + reports)  
**Risk:** LOW  
**Version:** v1.0.0

---

## 0) Purpose & Guardrails

**Purpose:**
- Establish preventive docs hygiene for Peak_Trade documentation
- Detect broken links, orphaned pages, missing reference targets
- Generate deterministic snapshots for trend tracking
- Provide operator-friendly reports without modifying content

**Guardrails:**
- ✅ **KEEP EVERYTHING:** No deletions, no content edits
- ✅ **Analysis-only:** Reports + suggestions, no auto-fixes
- ✅ **CI optional:** GitHub Action is NOT required for branch protection
- ✅ **Archive-safe:** Respects `docs/ops/_archive/**` exclusion (default)
- ✅ **Deterministic:** Sorted output, stable JSON (sort keys)
- ✅ **No network:** Repo-internal only, no external URL validation
- ✅ **No watch loops:** Snapshot-only usage, not continuous monitoring

---

## 1) Inputs & Root Sources (Docs Graph)

**Default Root Sources:**
- `docs/WORKFLOW_FRONTDOOR.md`
- `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md`
- `docs/ops/README.md`
- `docs/INSTALLATION_QUICKSTART.md`

**These are the starting points for BFS graph traversal to find reachable docs.**

---

## 2) Multi-Agent Roles

| Role | Responsibility |
|------|---------------|
| **ORCHESTRATOR** | Plan scope, coordinate execution |
| **FACTS_COLLECTOR** | Discover existing gates + scripts |
| **CI_GUARDIAN** | Ensure workflow is optional (not required) |
| **DOCS_AUDITOR** | Define root sources, validate graph logic |
| **EVIDENCE_SCRIBE** | Document findings, create reports |
| **RISK_OFFICER** | Assess rollback risk (LOW) |

---

## 3) Operator Quickstart Commands

### Generate Snapshot (Default)
```bash
cd /Users/frnkhrz/Peak_Trade

# Using uv (recommended)
uv run python scripts/ops/docs_graph_snapshot.py \
  --out docs/_generated/docs_graph_snapshot.json

# Or using python3
python3 scripts/ops/docs_graph_snapshot.py \
  --out docs/_generated/docs_graph_snapshot.json
```

### Include Archives
```bash
python3 scripts/ops/docs_graph_snapshot.py \
  --out docs/_generated/docs_graph_snapshot.json \
  --include-archives
```

### Fail on Broken (for CI)
```bash
python3 scripts/ops/docs_graph_snapshot.py \
  --out docs/_generated/docs_graph_snapshot.json \
  --fail-on-broken
```

### Custom Roots
```bash
python3 scripts/ops/docs_graph_snapshot.py \
  --roots docs/WORKFLOW_FRONTDOOR.md README.md \
  --out docs/_generated/docs_graph_snapshot.json
```

---

## 4) How to Interpret Snapshot Fields

### Schema v1.0.0 Structure
```json
{
  "schema_version": "1.0.0",
  "generated_at_utc": "...",
  "repo_root": "...",
  "roots": [...],
  "config": {"include_archives": false, "docs_dir": "docs"},
  "stats": {
    "nodes": N,
    "edges": M,
    "broken_targets": X,
    "broken_anchors": Y,
    "orphaned_pages": Z,
    "runtime_seconds": T
  },
  "nodes": [{"path": "...", "is_root": bool}],
  "edges": [{"src": "...", "dst": "...", "kind": "md", "anchor": null|"...", "raw": "..."}],
  "broken_targets": [{"src": "...", "raw": "...", "resolved": "...", "reason": "..."}],
  "broken_anchors": [{"src": "...", "dst": "...", "anchor": "...", "reason": "..."}],
  "orphans": [{"path": "..."}]
}
```

### Field Meanings

**nodes:**
- `path`: Repo-relative path to markdown file
- `is_root`: True if file is in root sources list

**edges:**
- `src`: Source file path
- `dst`: Destination file path (markdown only)
- `kind`: Always "md" (markdown link)
- `anchor`: Heading anchor (e.g., "section-one") or null
- `raw`: Original link text from markdown

**broken_targets:**
- `src`: File containing the broken link
- `raw`: Original link text
- `resolved`: Attempted resolution path
- `reason`: Why it's broken ("file not found", "outside repo")

**broken_anchors:**
- `src`: File containing the link
- `dst`: Target file (exists, but anchor doesn't)
- `anchor`: Missing anchor slug
- `reason`: Error message

**orphans:**
- `path`: File not reachable from any root source via BFS

---

## 5) Triage Workflow

### For Broken Targets

**Priority:** HIGH (link points to non-existent file)

**Triage Steps:**
1. Check if target was moved/renamed
   - Fix: Update link to new location
2. Check if target was deleted intentionally
   - Fix: Remove link or add note
3. Check if target is in archive
   - Fix: Add compatibility stub/target if needed (rare)
4. Check if link is typo
   - Fix: Correct link path

**Recommended Fix Pattern:**
```markdown
<!-- Before -->
[Link](docs/missing.md)

<!-- After (if file moved) -->
[Link](docs/new_location/file.md)

<!-- After (if file deleted) -->
<!-- Link removed: target file deleted in PR #123 -->
```

### For Broken Anchors

**Priority:** MEDIUM (file exists, but heading doesn't)

**Triage Steps:**
1. Check if heading was renamed
   - Fix: Update anchor in link
2. Check if heading was removed
   - Fix: Link to different section or file top
3. Check anchor slugification
   - Fix: Use correct GitHub slug (lowercase, hyphens, no punctuation)

**Anchor Slugification Rules:**
- Lowercase
- Remove backticks, asterisks, underscores
- Replace spaces with hyphens
- Remove other punctuation
- Collapse multiple hyphens
- Strip leading/trailing hyphens

**Example:**
```markdown
<!-- Heading in target file -->
## **Setup** for `config.toml`

<!-- Correct anchor -->
[Link](file.md#setup-for-configtoml)

<!-- Incorrect anchors -->
[Link](file.md#setup-for-config.toml)  ❌
[Link](file.md#Setup-for-config.toml)  ❌
```

### For Orphaned Pages

**Priority:** LOW (informational, not broken)

**Triage Steps:**
1. Check if page should be linked
   - Fix: Add link from appropriate parent (WORKFLOW_FRONTDOOR, ops/README, etc.)
2. Check if page is intentionally standalone
   - Action: No fix needed, document reason
3. Check if page is obsolete
   - Action: Consider moving to archive (with approval)

**Recommended Link Points:**
- Same directory README.md
- Parent directory README.md
- docs/WORKFLOW_FRONTDOOR.md (for high-level pages)
- docs/ops/README.md (for ops tools)

---

## 6) Recommended Fix Patterns

### Compatibility Stubs/Targets

**When to use:** Archive link needs to work, but target was moved

**Pattern:**
```markdown
<!-- In archive file (DO NOT MODIFY) -->
[Link](../old_location/file.md)

<!-- Create stub at old location -->
<!-- old_location/file.md -->
# [MOVED] Original Title

**This page has moved to:** [new_location/file.md](../../new_location/file.md)

**Reason:** Reorganization in PR #123

**Archive compatibility:** This stub maintains links from archived docs.
```

### Crosslinking

**When to use:** Reduce orphans by adding navigation links

**Pattern:**
```markdown
<!-- In docs/WORKFLOW_FRONTDOOR.md -->
## Related Documentation

- [Orphaned Page](path/to/orphan.md) — Description

<!-- Or in parent README.md -->
## Contents

- [Orphaned Page](orphan.md) — Description
```

### Moving Pages Out of Orphan Status

**When to use:** Page should be discoverable from root sources

**Steps:**
1. Identify appropriate parent (WORKFLOW_FRONTDOOR, ops/README, directory README)
2. Add link with clear description
3. Verify page is now reachable (re-run snapshot)

---

## 7) Safety Notes

### No Network Requests
- Script analyzes repo-internal links only
- External URLs (http://, https://, mailto:) are ignored
- No rate limiting needed
- Fast execution (< 1 second for 1000 files)

### Deterministic Output
- Run twice → identical JSON (byte-for-byte)
- Sorted nodes, edges, broken items, orphans
- Stable for diff/trend tracking
- No timestamps in content (only metadata)

### Archive Include Toggle
- **Default:** `--include-archives` is FALSE
- Archives excluded: `docs/ops/_archive/**`
- Always excluded: `docs/_generated/**`
- **When to include:** Full inventory, archive link validation

### No Watch Loops
- Snapshot-only tool (not continuous monitoring)
- Run manually or in CI (on docs changes)
- No daemon/background process
- No file watching

---

## 8) Troubleshooting

### Issue: docs-reference-targets-gate failures

**Symptoms:** CI gate fails with "missing reference targets"

**Causes:**
- Backticks in headings (GitHub slugifies differently)
- Path-like tokens in text (false positives)
- Relative links in archived docs

**Solutions:**
1. Check if target is intentionally missing → add to `docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt`
2. Create stub file or add heading/anchor if target should exist
3. Fix link path if incorrect
4. For inline code with "/" that's NOT a repo path, use HTML entity: `docs&#47;branch-name`

### Issue: False positive broken anchors

**Symptoms:** Anchor exists in file but reported as broken

**Diagnosis:**
```bash
# Check actual heading in target file
grep "^#" target_file.md

# Check slugification
python3 -c "
import re
heading = '## Your Heading Here'
slug = heading.lower().strip('#').strip()
slug = re.sub(r'[\`\*_~]+', '', slug)
slug = re.sub(r'[^a-z0-9\s\-]', '', slug)
slug = re.sub(r'\s+', '-', slug)
slug = re.sub(r'-{2,}', '-', slug)
print(slug.strip('-'))
"
```

**Solutions:**
- Use correct GitHub slug format
- Check for duplicate headings (suffix -1, -2, etc.)
- Verify heading exists in target file

### Issue: Orphan false positives

**Symptoms:** Page reported as orphan but appears to be linked

**Diagnosis:**
```bash
# Search for links to the page
grep -r "path/to/page.md" docs/

# Check if link is in code block (ignored)
# Check if link source is not in root sources
```

**Solutions:**
- Add linking page to root sources (if appropriate)
- Verify link is not in code block
- Check if page is linked from non-markdown file (ignored)

---

## 9) Operator Output Template

```markdown
## Phase 8 Docs Integrity Check — [DATE]

**Operator:** [Name]
**Git SHA:** [hash]
**Branch:** [branch]
**Duration:** [seconds]

### Command
\`\`\`bash
python3 scripts/ops/docs_graph_snapshot.py \
  --out docs/_generated/docs_graph_snapshot.json
\`\`\`

### Results
- **Nodes:** [N] files
- **Edges:** [M] links
- **Broken targets:** [X]
- **Broken anchors:** [Y]
- **Orphaned pages:** [Z]
- **Runtime:** [T] seconds

### Top Issues

1. **Broken link:** `[source]` → `[target]`
   - **Reason:** [file not found / anchor not found]
   - **Action:** [Fix link / Add ignore / Create target]

2. **Orphaned page:** `[path]`
   - **Suggested link point:** `[parent file]`
   - **Action:** [Link from parent / Keep orphaned]

### Decision

- [ ] No fixes applied (report-only run)
- [ ] Fixes applied (see follow-up PR #[number])

### Notes

[Any additional observations or context]

### Artifacts

- `docs/_generated/docs_graph_snapshot.json` (not committed)
```

---

## 10) Related Documentation

### Existing Tools
- `scripts/ops/check_markdown_links.py` — Link validation (used by CI gate)
- `scripts/ops/collect_docs_reference_targets_fullscan.py` — Reference targets baseline

### CI Workflows
- `.github/workflows/docs_reference_targets_gate.yml` — Required CI gate
- `.github/workflows/docs_reference_targets_trend.yml` — Trend tracking
- `.github/workflows/docs-integrity-snapshot.yml` — Optional snapshot workflow (if deployed)

### Navigation
- `docs/WORKFLOW_FRONTDOOR.md` — Central navigation hub
- `docs/ops/README.md` — Ops tools index
- `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md` — Authoritative operational reference

---

## 11) Maintenance

**Review Frequency:** Quarterly or after major docs restructuring

**Update Triggers:**
- New root source added (update default `--roots` list)
- Archive structure changes (verify exclude patterns)
- CI gate failures increase (investigate root cause)

**Version History:**
- v1.0.0 (2026-01-12): Initial release (Phase 8, schema v1.0.0)

---

**Last Updated:** 2026-01-12  
**Next Review:** Q2 2026 or after major docs changes  
**Owner:** Peak_Trade Ops Team
