# RUNBOOK: Pointer Pattern Operations (Root Canonical Runbooks)

**Status:** ACTIVE  
**Scope:** Documentation Patterns / Ops Workflows / Runbook Management  
**Risk:** LOW (docs-only pattern, enables safe root-level runbook integration)  
**Last Updated:** 2026-01-14  
**Version:** v1.0

---

## 1. Purpose

This runbook defines operational procedures for the **Pointer Pattern**: a documentation architecture that allows **root-level canonical runbooks** (e.g., commit salvage workflows, installation guides) to remain at repository root while being **discoverable and navigable** through the structured `docs/ops/runbooks/` hierarchy.

**Problem Statement:**

- Root-level runbooks provide provenance and minimize migration risk for critical operational procedures
- Operators need a **single navigation entry point** at `docs/ops/runbooks/README.md`
- Moving root runbooks breaks existing references and loses git history context

**Solution:**

The Pointer Pattern maintains:
1. **Root Canonical Runbook** (e.g., `RUNBOOK_COMMIT_SALVAGE_CB006C4A.md`) at repo root (source of truth)
2. **Pointer Document** (e.g., `RUNBOOK_COMMIT_SALVAGE_CB006C4A_POINTER.md`) in `docs/ops/runbooks/` (navigation stub)
3. **Index Entry** in `docs/ops/runbooks/README.md` (discoverability)

**Benefits:**

- ✅ Preserves git history and provenance
- ✅ Single source of truth (root runbook)
- ✅ Unified navigation (ops runbook index)
- ✅ No content duplication or drift risk
- ✅ Gates-compliant (token policy + reference targets)

---

## 2. When to Use the Pointer Pattern

### Decision Criteria

**✅ USE Pointer Pattern when:**

| Condition | Rationale |
|-----------|-----------|
| Runbook created at repo root (historically or intentionally) | Preserves provenance, minimizes migration risk |
| Runbook is incident-specific or tied to commit SHA | Context is root-level (e.g., salvage workflows) |
| Moving runbook would break external references | Stability over restructuring |
| Runbook is large (>500 lines) and stable | Avoids costly migrations for mature artifacts |
| Runbook references root-level files extensively | Relative link hygiene (fewer `../../../` patterns) |

**❌ DO NOT USE Pointer Pattern when:**

| Condition | Alternative |
|-----------|-------------|
| New runbook, naturally fits in `docs/ops/runbooks/` | Create directly in `docs/ops/runbooks/` |
| Runbook is small (<200 lines) and easily moved | Migrate to `docs/ops/runbooks/`, update references |
| Root placement has no provenance value | Start in structured location |
| Runbook will change frequently | Keep in `docs/ops/runbooks/` for easier maintenance |

---

## 3. Canonical Layout (Files + Responsibilities)

### File Structure

```
Peak_Trade/
├── RUNBOOK_COMMIT_SALVAGE_CB006C4A.md          ← ROOT CANONICAL (source of truth)
├── docs/
│   └── ops/
│       ├── runbooks/
│       │   ├── README.md                        ← INDEX (discoverability)
│       │   └── RUNBOOK_COMMIT_SALVAGE_CB006C4A_POINTER.md  ← POINTER (navigation stub)
│       └── merge_logs/
│           └── PR_XXX_MERGE_LOG.md              ← (optional) related evidence
```

### Responsibilities

| Artifact | Responsibility | Maintenance Frequency |
|----------|----------------|----------------------|
| **Root Canonical Runbook** | Full operational content, procedures, troubleshooting | As needed (incident-driven or quarterly review) |
| **Pointer Document** | Minimal stub: link to root, summary, context | Created once, updated only on root runbook renames |
| **Index Entry (README)** | Single line link to pointer doc | Created once, no changes unless pattern evolves |
| **Merge Logs (optional)** | Evidence of PR that introduced pointer pattern | Created once (PR merge) |

---

## 4. Implementation Procedure (Operator Steps)

### Pre-Flight Checklist

**Before starting, verify:**

- [ ] Root runbook exists and is finalized (no active editing)
- [ ] Root runbook filename follows convention: `RUNBOOK_<TOPIC>_<IDENTIFIER>.md`
- [ ] Working tree is clean (`git status`)
- [ ] On correct branch (typically feature branch for pointer integration)
- [ ] Docs gates are GREEN on current branch

**Pre-Flight Commands:**

```bash
# Verify working directory
cd /Users/frnkhrz/Peak_Trade
pwd && git rev-parse --show-toplevel

# Check status
git status -sb

# Verify root runbook exists
ls -lh RUNBOOK_*.md

# Verify docs gates baseline (optional, recommended)
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
```

### Step 1: Verify Root Runbook Compliance

**Objective:** Ensure root runbook is gates-compliant before creating pointer.

**Commands:**

```bash
# Check token policy (inline-code with `/` must be real paths or escaped)
python scripts/ops/validate_docs_token_policy.py RUNBOOK_*.md

# Check reference targets (all linked paths must exist)
bash scripts/ops/verify_docs_reference_targets.sh

# Expected output: All checks PASS
```

**If violations found:**

1. Fix token policy issues (see [RUNBOOK_DOCS_TOKEN_POLICY_GATE.md](RUNBOOK_DOCS_TOKEN_POLICY_GATE.md))
2. Fix reference targets (update paths or encode illustrative examples)
3. Re-run verification

### Step 2: Create Pointer Document

**Objective:** Create minimal navigation stub in `docs/ops/runbooks/`.

**Template (copy and customize):**

```markdown
# [RUNBOOK TITLE] — Pointer

**Canonical Location:** [`../../RUNBOOK_<IDENTIFIER>.md`](../../RUNBOOK_<IDENTIFIER>.md)  
**Status:** ACTIVE  
**Pointer Version:** v1.0  
**Last Updated:** [DATE]

---

## Summary

[1-2 sentence summary of what this runbook covers]

**Key Use Cases:**
- [Bullet 1]
- [Bullet 2]
- [Bullet 3]

---

## Quick Access

**⭐ Canonical Runbook (Source of Truth):** [`RUNBOOK_<IDENTIFIER>.md`](../../RUNBOOK_<IDENTIFIER>.md)

This pointer document provides navigation only. All operational content, procedures, and troubleshooting are maintained in the canonical root-level runbook.

---

## Why Root Location?

[1-2 sentences explaining provenance: e.g., "Created during incident response", "Preserves commit history context", "Minimizes migration risk for established references"]

---

## Related Documentation

- [Related link 1]
- [Related link 2]

---

**Maintenance Note:** This pointer is stable. Updates occur only if the root runbook is renamed or moved. Content updates happen in the canonical runbook.
```

**Example (Commit Salvage):**

Save to: `docs/ops/runbooks/RUNBOOK_COMMIT_SALVAGE_CB006C4A_POINTER.md`

```markdown
# Commit Salvage Workflow — Pointer

**Canonical Location:** [`../../RUNBOOK_COMMIT_SALVAGE_CB006C4A.md`](../../RUNBOOK_COMMIT_SALVAGE_CB006C4A.md)  
**Status:** ACTIVE  
**Pointer Version:** v1.0  
**Last Updated:** 2026-01-14

---

## Summary

Operational runbook for salvaging local commits from wrong branch (e.g., committed to main instead of feature branch) and migrating them through the standard PR workflow (feature branch → PR → CI → merge).

**Key Use Cases:**
- Commit accidentally created on main (should be on feature branch)
- Need to reset main to origin/main without losing work
- Must follow PR workflow (no direct pushes to main)

---

## Quick Access

**⭐ Canonical Runbook (Source of Truth):** [`RUNBOOK_COMMIT_SALVAGE_CB006C4A.md`](../../RUNBOOK_COMMIT_SALVAGE_CB006C4A.md)

This pointer document provides navigation only. All operational content, procedures, and troubleshooting are maintained in the canonical root-level runbook.

---

## Why Root Location?

This runbook was created during an active incident (commit cb006c4a salvage operation) and maintains provenance at repository root. Root placement preserves git history context and minimizes risk of breaking references in incident reports and merge logs.

---

## Related Documentation

- [docs/ops/runbooks/README.md](README.md) — Runbook index
- [docs/ops/merge_logs/](../merge_logs/) — PR merge logs referencing salvage workflow

---

**Maintenance Note:** This pointer is stable. Updates occur only if the root runbook is renamed or moved. Content updates happen in the canonical runbook.
```

**Action:**

```bash
# Create pointer document
# (Use template above, customize for your runbook)

# Verify pointer doc created
ls -lh docs/ops/runbooks/RUNBOOK_*_POINTER.md
```

### Step 3: Update Runbook Index (README.md)

**Objective:** Add single link entry to `docs/ops/runbooks/README.md` for discoverability.

**Location:** Find appropriate section in README (typically "CI & Operations" or create "Root Canonical Runbooks" section if pattern is new).

**Entry Format:**

```markdown
- [Runbook Name](RUNBOOK_<IDENTIFIER>_POINTER.md) ⭐ — Brief description (source of truth at root)
```

**Example Addition:**

In `docs/ops/runbooks/README.md`, section "CI & Operations":

```markdown
### CI & Operations

Runbooks for CI operations and general operational procedures:

- [RUNBOOK_CI_STATUS_POLLING_HOWTO.md](RUNBOOK_CI_STATUS_POLLING_HOWTO.md) — CI status polling how-to
- [PHASE4E_STABILITY_MONITORING_CHECKLIST.md](PHASE4E_STABILITY_MONITORING_CHECKLIST.md) — Phase 4E stability monitoring checklist
- [rebase_cleanup_workflow.md](rebase_cleanup_workflow.md) — Rebase cleanup workflow
- [Commit Salvage Workflow](RUNBOOK_COMMIT_SALVAGE_CB006C4A_POINTER.md) ⭐ — Salvaging commits from wrong branch (feature branch → PR → merge workflow)
- [github_rulesets_pr_reviews_policy.md](github_rulesets_pr_reviews_policy.md) — GitHub rulesets PR reviews policy
- [policy_critic_execution_override.md](policy_critic_execution_override.md) — Policy critic execution override
```

**Action:**

```bash
# Edit README.md
# Add entry in appropriate section

# Verify entry added
grep -n "POINTER.md" docs/ops/runbooks/README.md
```

**⚠️ CRITICAL: Minimal Invasive Rule**

- Add EXACTLY ONE line (the pointer link)
- Do NOT rewrite existing entries
- Do NOT restructure sections
- Do NOT change formatting of other content

### Step 4: Verify Gates Locally (Snapshot Mode)

**Objective:** Ensure all gates pass before committing.

**Pre-Flight:**

```bash
# Verify terminal is not stuck in prompt (dquote> / heredoc>)
# If stuck: Ctrl-C and restart

# Ensure working directory
cd /Users/frnkhrz/Peak_Trade
pwd

# Verify git status
git status -sb
```

**Gate Verification Commands:**

```bash
# Docs Token Policy Gate (inline-code `/` encoding)
python scripts/ops/validate_docs_token_policy.py --changed

# Docs Reference Targets Gate (all paths exist)
bash scripts/ops/verify_docs_reference_targets.sh --changed

# (Optional) Full docs gates snapshot
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
```

**Expected Output:**

```
✅ Docs Token Policy Gate: PASS
✅ Docs Reference Targets Gate: PASS (0 missing targets)
✅ Docs Diff Guard Policy Gate: PASS (no mass deletions)
```

**If violations found:**

| Gate | Common Issue | Fix |
|------|--------------|-----|
| Token Policy | Illustrative path not escaped | Replace `/` with `&#47;` in inline-code (`` `docs&#47;example.md` ``) |
| Reference Targets | Link to non-existent file | Update path, escape if illustrative, or add to ignore list |
| Diff Guard | Mass deletion detected | Review changes, split into smaller PRs if intentional |

**Revalidate after fixes:**

```bash
# Re-run gates
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
```

---

## 5. Reference & Token Policy Safety

### Do/Don't Examples

#### ✅ DO: Real Repo Paths (No Escaping)

**Valid inline-code for real files:**

```markdown
- See [`docs/ops/runbooks/README.md`](docs/ops/runbooks/README.md)
- Run [`scripts/ops/pt_docs_gates_snapshot.sh`](scripts/ops/pt_docs_gates_snapshot.sh)
- Refer to [`RUNBOOK_COMMIT_SALVAGE_CB006C4A.md`](RUNBOOK_COMMIT_SALVAGE_CB006C4A.md)
```

**Rationale:** These files exist in the repository. Token Policy Gate classifies them as REAL_REPO_TARGET (exempt from escaping).

#### ✅ DO: Illustrative Paths (Escape `/` with `&#47;`)

**Valid inline-code for examples:**

```markdown
- Create a file like `config&#47;my_strategy.toml`
- Example script: `scripts&#47;custom_backtest.py`
- Generic placeholder: `path&#47;to&#47;your&#47;file.md`
```

**Rationale:** These paths do NOT exist in repo. Escaping prevents Reference Targets Gate from treating them as broken links.

#### ✅ DO: Commands and URLs (No Escaping)

**Valid patterns (auto-exempted):**

```markdown
- Run: `python scripts/run_backtest.py --strategy ma_crossover`
- Branch: `git checkout feature/new-runbook`
- URL: `https://github.com/rauterfrank-ui/Peak_Trade/blob/main/README.md`
- Local path: `./scripts/local_helper.sh`
```

**Rationale:** Token Policy Gate recognizes command prefixes, URLs, local paths, and branch patterns (no escaping needed).

#### ❌ DON'T: Illusory Links (False Targets)

**Violation example:**

```markdown
<!-- BAD: This creates a broken link -->
- See [example guide](docs&#47;example_guide.md) for more details.
```

**Problem:** If `docs&#47;example_guide.md` does NOT exist (as in this illustrative example), Reference Targets Gate fails.

**Fix:**

```markdown
<!-- GOOD: Escape illustrative path -->
- See example guide at `docs&#47;example_guide.md` for more details.

<!-- OR: Create the file first -->
- See [example guide](docs/example_guide.md) for more details.
  (after running: `touch docs/example_guide.md`)
```

#### ❌ DON'T: Mixing Patterns

**Violation example:**

```markdown
<!-- BAD: Real path in pointer, illustrative in description -->
- Pointer: [`RUNBOOK_EXAMPLE.md`](../../RUNBOOK_EXAMPLE.md)  
- Description: Run it via `docs/ops/runbooks/RUNBOOK_EXAMPLE.md` (broken)
```

**Fix:**

```markdown
<!-- GOOD: Consistent escaping -->
- Pointer: [`RUNBOOK_EXAMPLE.md`](../../RUNBOOK_EXAMPLE.md)  
- Description: Run it via `docs&#47;ops&#47;runbooks&#47;RUNBOOK_EXAMPLE.md` (if illustrative)

<!-- OR: Use relative link if real -->
- Pointer: [`RUNBOOK_EXAMPLE.md`](../../RUNBOOK_EXAMPLE.md)  
- Description: Run it via [`docs/ops/runbooks/RUNBOOK_EXAMPLE.md`](docs/ops/runbooks/RUNBOOK_EXAMPLE.md)
```

### Quick Decision Tree

```
Inline-code token contains `/`?
├─ YES → Is this a REAL file in repo?
│   ├─ YES → No escaping needed (e.g., `docs/ops/README.md`)
│   └─ NO → Is it a command/URL/branch/local path?
│       ├─ YES → No escaping needed (e.g., `python scripts/run.py`)
│       └─ NO → MUST escape `/` with `&#47;` (e.g., `config&#47;example.toml`)
└─ NO → No action needed
```

---

## 6. Maintenance & Drift Control

### Single Source of Truth Principle

**Rule:** Root canonical runbook is the ONLY location for operational content. Pointer document contains ONLY navigation metadata.

**Enforcement:**

| Action | Allowed in Root Runbook | Allowed in Pointer |
|--------|------------------------|-------------------|
| Add/update procedures | ✅ YES | ❌ NO |
| Add/update troubleshooting | ✅ YES | ❌ NO |
| Add/update examples | ✅ YES | ❌ NO |
| Update "Last Updated" date | ✅ YES | ❌ NO (only on pointer rename) |
| Update canonical link | ❌ NO | ✅ YES (only on root runbook rename/move) |

### "Pointer Must Not Fork Content" Rule

**Violation Example:**

```markdown
<!-- BAD: Pointer contains operational content -->
# Commit Salvage Workflow — Pointer

**Canonical Location:** [../../RUNBOOK_COMMIT_SALVAGE_CB006C4A.md](../../RUNBOOK_COMMIT_SALVAGE_CB006C4A.md)

## Quick Start (Pointer-Specific)

1. Checkout feature branch
2. Cherry-pick commit
3. Reset main

<!-- This is content duplication! -->
```

**Correct Pattern:**

```markdown
<!-- GOOD: Pointer defers to canonical -->
# Commit Salvage Workflow — Pointer

**Canonical Location:** [../../RUNBOOK_COMMIT_SALVAGE_CB006C4A.md](../../RUNBOOK_COMMIT_SALVAGE_CB006C4A.md)

## Quick Start

See canonical runbook for full procedures. This pointer provides navigation only.
```

### Handling Renames/Moves

**Scenario:** Root runbook is renamed (e.g., `RUNBOOK_OLD.md` → `RUNBOOK_NEW.md`).

**Update Checklist:**

- [ ] Update pointer filename: `RUNBOOK_OLD_POINTER.md` → `RUNBOOK_NEW_POINTER.md`
- [ ] Update pointer canonical link: `..&#47;..&#47;RUNBOOK_OLD.md` → `..&#47;..&#47;RUNBOOK_NEW.md`
- [ ] Update README.md index entry
- [ ] Search all docs for references to old filename: `grep -r "RUNBOOK_OLD" docs/`
- [ ] Update any merge logs or evidence referencing old filename
- [ ] Verify gates pass

**Commands:**

```bash
# Rename pointer
git mv docs/ops/runbooks/RUNBOOK_OLD_POINTER.md docs/ops/runbooks/RUNBOOK_NEW_POINTER.md

# Update canonical link in pointer
sed -i 's|RUNBOOK_OLD.md|RUNBOOK_NEW.md|g' docs/ops/runbooks/RUNBOOK_NEW_POINTER.md

# Update README entry
sed -i 's|RUNBOOK_OLD_POINTER.md|RUNBOOK_NEW_POINTER.md|g' docs/ops/runbooks/README.md

# Search for stale references
grep -r "RUNBOOK_OLD" docs/ --exclude-dir=.git

# Verify gates
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
```

### Quarterly Review (Recommended)

**Objective:** Ensure pointer pattern remains aligned with root canonical runbooks.

**Checklist (once per quarter):**

- [ ] List all root-level runbooks: `ls -lh RUNBOOK_*.md`
- [ ] List all pointer documents: `ls -lh docs/ops/runbooks/RUNBOOK_*_POINTER.md`
- [ ] Verify 1:1 mapping (each root runbook has a pointer if needed)
- [ ] Check for orphaned pointers (pointer exists but root runbook deleted)
- [ ] Verify canonical links in pointers are correct
- [ ] Verify README.md index has all pointers
- [ ] Run full docs gates scan: `scripts/ops/pt_docs_gates_snapshot.sh`

---

## 7. Failure Modes & Recovery

### Failure Mode 1: Token Policy Violation

**Symptom:**

```
❌ Docs Token Policy Gate: FAIL
docs/ops/runbooks/RUNBOOK_EXAMPLE_POINTER.md:12: `docs/ops/example.md` (ILLUSTRATIVE)
  → Illustrative path token must use &#47; encoding
```

**Cause:** Illustrative path in pointer document not escaped.

**Recovery:**

```bash
# Fix: Replace `/` with `&#47;` in inline-code
sed -i 's|`docs/ops/example.md`|`docs&#47;ops&#47;example.md`|g' docs/ops/runbooks/RUNBOOK_EXAMPLE_POINTER.md

# Revalidate
python scripts/ops/validate_docs_token_policy.py --changed
```

### Failure Mode 2: Reference Targets Violation

**Symptom:**

```
❌ Docs Reference Targets Gate: FAIL
Missing targets: 1
  - docs/ops/runbooks/RUNBOOK_EXAMPLE_POINTER.md:5: ../../RUNBOOK_MISSING.md
```

**Cause:** Canonical link in pointer points to non-existent root runbook.

**Recovery:**

```bash
# Verify root runbook exists
ls -lh RUNBOOK_MISSING.md
# Output: No such file or directory

# Option A: Create root runbook (if intended)
touch RUNBOOK_MISSING.md
git add RUNBOOK_MISSING.md

# Option B: Fix pointer link (if typo)
# Edit pointer, correct canonical link to correct filename

# Revalidate
bash scripts/ops/verify_docs_reference_targets.sh --changed
```

### Failure Mode 3: Orphaned Pointer (Root Runbook Deleted)

**Symptom:** Pointer exists but canonical runbook was deleted or moved without updating pointer.

**Detection:**

```bash
# Check all pointer canonical links
grep -h "Canonical Location:" docs/ops/runbooks/RUNBOOK_*_POINTER.md | while read -r line; do
  # Extract path from markdown link syntax
  target=$(echo "$line" | grep -oP '\(\K[^)]+')
  resolved_path="docs/ops/runbooks/$target"
  if [ ! -f "$resolved_path" ]; then
    echo "⚠️  Orphaned pointer: $line → Target missing: $resolved_path"
  fi
done
```

**Recovery:**

```bash
# Option A: Restore root runbook (if deletion was accidental)
git log --all --full-history -- RUNBOOK_DELETED.md
git checkout <commit> -- RUNBOOK_DELETED.md

# Option B: Delete pointer and README entry (if deletion was intentional)
git rm docs/ops/runbooks/RUNBOOK_DELETED_POINTER.md
# Edit README.md, remove pointer entry

# Option C: Update pointer to new location (if runbook was moved)
# Edit pointer, update canonical link
```

### Failure Mode 4: README Entry Missing

**Symptom:** Pointer document exists but no entry in `docs/ops/runbooks/README.md`.

**Detection:**

```bash
# List all pointers
ls docs/ops/runbooks/RUNBOOK_*_POINTER.md

# Check if each pointer is in README
for pointer in docs/ops/runbooks/RUNBOOK_*_POINTER.md; do
  basename_pointer=$(basename "$pointer")
  if ! grep -q "$basename_pointer" docs/ops/runbooks/README.md; then
    echo "⚠️  Missing README entry: $basename_pointer"
  fi
done
```

**Recovery:**

```bash
# Add missing entry to README.md (follow Step 3 format)
# Edit README.md, add pointer link in appropriate section

# Verify
grep "RUNBOOK_EXAMPLE_POINTER.md" docs/ops/runbooks/README.md
```

### Failure Mode 5: Content Duplication (Drift)

**Symptom:** Pointer document contains operational procedures (duplicates root runbook content).

**Detection:** Manual review during quarterly audit (see Maintenance section).

**Recovery:**

```bash
# Remove duplicated content from pointer
# Edit pointer, keep ONLY:
#   - Summary (1-2 sentences)
#   - Canonical link
#   - Why root location (provenance)
#   - Related links (optional)

# Ensure all operational content is in root runbook
# Verify no duplication

# Commit fix
git add docs/ops/runbooks/RUNBOOK_EXAMPLE_POINTER.md
git commit -m "fix(docs): remove content duplication from pointer (defer to canonical)"
```

---

## 8. Templates

### Template A: Pointer Document

**Filename:** `docs&#47;ops&#47;runbooks&#47;RUNBOOK_<IDENTIFIER>_POINTER.md`

```markdown
# [Runbook Title] — Pointer

**Canonical Location:** [`../../RUNBOOK_<IDENTIFIER>.md`](../../RUNBOOK_<IDENTIFIER>.md)  
**Status:** ACTIVE  
**Pointer Version:** v1.0  
**Last Updated:** YYYY-MM-DD

---

## Summary

[1-2 sentence summary of runbook purpose and scope]

**Key Use Cases:**
- [Use case 1]
- [Use case 2]
- [Use case 3]

---

## Quick Access

**⭐ Canonical Runbook (Source of Truth):** [`RUNBOOK_<IDENTIFIER>.md`](../../RUNBOOK_<IDENTIFIER>.md)

This pointer document provides navigation only. All operational content, procedures, and troubleshooting are maintained in the canonical root-level runbook.

---

## Why Root Location?

[1-2 sentences: provenance explanation, e.g., "Created during incident X", "Preserves git history", "Minimizes migration risk"]

---

## Related Documentation

- [Link 1 with description]
- [Link 2 with description]

---

**Maintenance Note:** This pointer is stable. Updates occur only if the root runbook is renamed or moved. Content updates happen in the canonical runbook.
```

### Template B: README.md Entry Snippet

**Location:** `docs/ops/runbooks/README.md` (section: "CI & Operations" or equivalent)

```markdown
- [Runbook Name](RUNBOOK_<IDENTIFIER>_POINTER.md) ⭐ — Brief description (canonical at root: `RUNBOOK_<IDENTIFIER>.md`)
```

**Example:**

```markdown
- [Commit Salvage Workflow](RUNBOOK_COMMIT_SALVAGE_CB006C4A_POINTER.md) ⭐ — Salvaging commits from wrong branch (feature branch → PR → merge workflow)
```

### Template C: Commit Message

**For initial pointer integration:**

```
docs(ops): add pointer for [RUNBOOK_NAME]

Integrates root-level RUNBOOK_<IDENTIFIER>.md into ops runbook index via pointer pattern.

Changes:
- Add docs/ops/runbooks/RUNBOOK_<IDENTIFIER>_POINTER.md (navigation stub)
- Update docs/ops/runbooks/README.md (index entry)

Rationale:
- Preserves provenance of root-level runbook
- Enables discoverability via unified ops runbook index
- No content duplication (pointer defers to canonical)

Verification:
- Docs Token Policy Gate: PASS
- Docs Reference Targets Gate: PASS
- Docs Diff Guard Policy Gate: PASS

Risk: LOW (docs-only, no operational changes)
```

---

## 9. Verification

### Local Pre-Commit Verification

**Checklist:**

- [ ] Pointer document created in `docs/ops/runbooks/`
- [ ] README.md entry added
- [ ] Canonical link in pointer is correct (points to root runbook)
- [ ] Root runbook filename matches pointer reference
- [ ] No content duplication (pointer is navigation-only)
- [ ] All illustrative paths use `&#47;` encoding
- [ ] All real paths are unescaped and exist

**Commands:**

```bash
# Change to repo root
cd /Users/frnkhrz/Peak_Trade

# Verify terminal is clean (no heredoc/dquote prompt)
# If stuck: Ctrl-C

# Check working tree
git status -sb

# Pre-flight: Ensure no stale state
pwd && git rev-parse --show-toplevel

# Run docs gates (snapshot, no watch loops)
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main

# Verify pointer file exists
ls -lh docs/ops/runbooks/RUNBOOK_*_POINTER.md

# Verify README entry exists
grep -n "POINTER.md" docs/ops/runbooks/README.md

# Verify canonical link is correct
grep -A1 "Canonical Location" docs/ops/runbooks/RUNBOOK_*_POINTER.md
```

**Expected Output (Success):**

```
✅ Docs Token Policy Gate: PASS (0 violations)
✅ Docs Reference Targets Gate: PASS (0 missing targets)
✅ Docs Diff Guard Policy Gate: PASS (no mass deletions)

Pointer file:
-rw-r--r-- 1 user staff 1234 Jan 14 10:00 docs/ops/runbooks/RUNBOOK_EXAMPLE_POINTER.md

README entry:
55:- [Example Runbook](RUNBOOK_EXAMPLE_POINTER.md) ⭐ — Description

Canonical link:
**Canonical Location:** [`../../RUNBOOK_EXAMPLE.md`](../../RUNBOOK_EXAMPLE.md)
```

### Expected CI Checks

**When PR is created, expect these CI contexts to run:**

| Check | Expected Result | Notes |
|-------|----------------|-------|
| `docs-token-policy-gate` | ✅ PASS | No illustrative paths unescaped |
| `docs-reference-targets-gate` | ✅ PASS | All links resolve (root runbook exists) |
| `docs-diff-guard-policy-gate` | ✅ PASS | No mass deletions (only additions) |
| `dispatch-guard` | ✅ PASS | No workflow_dispatch changes |
| `CI Required Contexts Contract` | ✅ PASS | Meta-check for required checks |

**How to Check CI Status:**

```bash
# After PR created
PR_NUMBER=<YOUR_PR_NUMBER>

# View checks (snapshot)
gh pr checks $PR_NUMBER --interval 0

# Filter for docs gates
gh pr checks $PR_NUMBER | grep -E "docs-token|docs-reference|docs-diff"
```

### Post-Merge Verification

**After PR is merged, verify integration:**

```bash
# Update local main
git checkout main
git pull --ff-only origin main

# Verify pointer exists
ls -lh docs/ops/runbooks/RUNBOOK_*_POINTER.md

# Verify README entry
grep "POINTER.md" docs/ops/runbooks/README.md

# Verify canonical link resolves
cat docs/ops/runbooks/RUNBOOK_*_POINTER.md | grep "Canonical Location"
# Manually verify: click link in GitHub UI, should navigate to root runbook

# Optional: Full docs gates scan (post-merge sanity)
./scripts/ops/pt_docs_gates_snapshot.sh
```

---

## 10. Anti-Footgun Checklist

**Common mistakes to avoid:**

- [ ] ❌ DON'T duplicate operational content in pointer (use canonical runbook)
- [ ] ❌ DON'T use illustrative paths without `&#47;` encoding
- [ ] ❌ DON'T create pointer before root runbook is finalized
- [ ] ❌ DON'T forget to update README.md index entry
- [ ] ❌ DON'T use absolute paths in canonical links (use relative: `..&#47;..&#47;RUNBOOK_X.md`)
- [ ] ❌ DON'T rename root runbook without updating pointer and README
- [ ] ❌ DON'T create multiple pointers for same root runbook
- [ ] ❌ DON'T skip gate verification before committing
- [ ] ❌ DON'T edit pointer for content updates (edit root runbook instead)
- [ ] ❌ DON'T force-push to main (always use PR workflow)

**Checklist (copy to PR body):**

```markdown
## Pointer Pattern Integration Checklist

- [ ] Root runbook finalized and gates-compliant
- [ ] Pointer document created (navigation-only, no content duplication)
- [ ] Canonical link in pointer is correct (relative path, resolves to root runbook)
- [ ] README.md index entry added (single line, minimal invasive)
- [ ] All illustrative paths use `&#47;` encoding
- [ ] All real paths exist and are unescaped
- [ ] Local docs gates: PASS (token-policy, reference-targets, diff-guard)
- [ ] No orphaned pointers (1:1 mapping with root runbooks)
- [ ] Commit message follows convention (docs(ops): add pointer for X)
- [ ] PR targets main, uses feature branch workflow
```

---

## Exit Criteria

**Success Conditions (all must be met):**

✅ Pointer document exists in `docs&#47;ops&#47;runbooks&#47;RUNBOOK_<IDENTIFIER>_POINTER.md`  
✅ Canonical link in pointer resolves to canonical runbook target  
✅ README.md contains exactly one entry for pointer  
✅ Docs Token Policy Gate: PASS  
✅ Docs Reference Targets Gate: PASS  
✅ Docs Diff Guard Policy Gate: PASS  
✅ No content duplication (pointer is navigation-only)  
✅ No orphaned pointers (canonical runbook exists)  
✅ PR merged via standard workflow (feature branch → PR → CI → merge)

---

## References

### Related Runbooks

- [RUNBOOK_DOCS_TOKEN_POLICY_GATE.md](RUNBOOK_DOCS_TOKEN_POLICY_GATE.md) — Token policy gate operator guide
- [RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md](RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md) — Reference targets gate operator guide
- [RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md](RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md) — Diff guard gate operator guide
- [RUNBOOK_COMMIT_SALVAGE_CB006C4A.md](../archives/repo_root_docs/RUNBOOK_COMMIT_SALVAGE_CB006C4A.md) — Example of canonical runbook (archived from repo root)

### Scripts & Tools

- Token Policy Validator: `scripts/ops/validate_docs_token_policy.py`
- Reference Targets Validator: `scripts/ops/verify_docs_reference_targets.sh`
- Docs Gates Snapshot: `scripts/ops/pt_docs_gates_snapshot.sh`
- Token Policy Allowlist: `scripts/ops/docs_token_policy_allowlist.txt`

### Documentation

- [docs/ops/runbooks/README.md](README.md) — Runbook index and navigation
- [docs/ops/README.md](../README.md) — Ops documentation overview
- [docs/WORKFLOW_FRONTDOOR.md](../../WORKFLOW_FRONTDOOR.md) — Workflow documentation hub

---

**Version:** v1.0  
**Last Updated:** 2026-01-14  
**Maintainer:** ops  
**Status:** ACTIVE
