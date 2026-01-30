# Runbook: Docs Reference Targets False Positives

**Purpose:** Diagnose and fix docs-reference-targets-gate failures caused by illustrative example paths.

**Audience:** Docs maintainers, PR authors, CI troubleshooters

**Last Updated:** 2026-01-13

---

## Problem Statement

The `docs-reference-targets-gate` CI check validates that all file paths mentioned in Markdown docs actually exist in the repository. This prevents broken references.

**False Positive:** When docs include **illustrative example paths** (hypothetical examples, templates, placeholders), the gate treats them as missing files and fails.

**Example:**
```markdown
# Tutorial: Custom Config
Run with your custom config:
`bash python3 scripts/run_strategy_from_config.py --config config&#47;my_custom.toml`
```

**Gate failure:**
```
Missing targets: 1
  - docs/tutorial.md:42: config/my_custom.toml
```

**Reality:** `config&#47;my_custom.toml` is a hypothetical example, not a real file.

---

## Diagnosis

### Step 1: Identify Failed Check

**In GitHub Actions:**
1. Navigate to PR → Checks tab
2. Find `docs-reference-targets-gate` check
3. Click "Details" → View logs

**Example log:**
```
Docs Reference Targets: scanned 5 md file(s), found 59 reference(s).
Missing targets: 4
  - /path/to/docs/OVERVIEW.md:99: config/my_backtest.toml
  - /path/to/docs/OVERVIEW.md:381: scripts/run_walkforward.py
  - /path/to/docs/OVERVIEW.md:392: src/data/data_loader.py
  - /path/to/docs/UPDATE_SUMMARY.md:339: scripts/run_walkforward.py
```

### Step 2: Verify Path Existence

**Check each flagged path:**
```bash
# Navigate to repo root
cd /path/to/Peak_Trade

# Check if path exists
ls -la config/my_backtest.toml

# If "No such file or directory" → Illustrative path (needs neutralization)
# If file exists → Real path (investigate why gate flagged it)
```

### Step 3: Classify Path Type

| Path Type | Exists in Repo? | Action |
|-----------|----------------|--------|
| **Real path** | ✅ Yes | Investigate gate bug, check ignore list |
| **Illustrative example** | ❌ No | Neutralize with `&#47;` |
| **Typo** | ❌ No | Fix typo to correct path |
| **Deleted file** | ❌ No (was deleted) | Update docs or add to ignore list |

---

## Resolution

### Fix A: Neutralize Illustrative Paths (Recommended)

**Method:** Replace `/` with HTML entity `&#47;` in inline code spans

**Before:**
```markdown
Example: `config/my_custom.toml`
Command: `python3 scripts/example.py --config config/my_custom.toml`
```

**After:**
```markdown
Example: `config&#47;my_custom.toml`
Command: `bash python3 scripts/example.py --config config&#47;my_custom.toml`
```

**Rendering:** Both display identically in GitHub/Quarto (entity decoded to `/`)

**Copy/paste behavior:**
- From rendered view (GitHub UI): ✅ Gets correct path
- From raw Markdown: ⚠️ Gets entity (user must fix manually, rare case)

**Trade-off:** Acceptable for docs consumed via rendered Markdown (majority use case)

#### Bulk Neutralization

**Manual:**
```bash
# Find all inline code with paths in a file
grep -o '`[^`]*`' docs/my_file.md | grep '/'

# For each illustrative path:
# 1. Verify it doesn't exist: ls -la path/to/file
# 2. Replace in editor: config/my_custom.toml → config&#47;my_custom.toml
```

**Note:** Prefer doing this in an editor for one-off fixes; avoid bulk escaping that accidentally touches real repo paths.

### Fix B: Add to Ignore List

**When to use:**
- Path is intentionally referenced but doesn't exist (e.g., external examples)
- Path is generated at runtime (e.g., timestamped logs)

**Method:**
```bash
# Add to ignore list
echo "config/my_custom.toml" >> docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt

# Commit
git add docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt
git commit -m "docs(ops): exempt illustrative path from reference targets gate"
```

**Note:** Use sparingly. Neutralization (`&#47;`) is preferred for one-off illustrative examples.

### Fix C: Fix Typos or Update Docs

**If path is a typo:**
```markdown
# Before (typo):
`src&#47;strategys&#47;ma_crossover.py`

# After (fixed):
`src&#47;strategies&#47;ma_crossover.py`
```

**If file was deleted:**
- Update docs to reference new path
- Or remove outdated references

---

## Prevention

### Policy: Illustrative Path Encoding

**Establish repo-wide policy:**
1. **Real paths** → Keep as-is (gate should track them)
2. **Illustrative paths** → Encode with `&#47;`

**File:** `docs/ops/workflows/WORKFLOW_NOTES_FRONTDOOR.md` documents this policy

**Automated Enforcement:** The [Docs Token Policy Gate](RUNBOOK_DOCS_TOKEN_POLICY_GATE.md) automatically checks changed Markdown files and enforces this encoding policy, preventing false positives before they reach CI

### Pre-Commit Check (Optional)

**Script:** `bash scripts/ops/verify_docs_reference_targets.sh --changed`

**Usage:**
```bash
# Check changed docs in PR
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main

# Exit code 0 = all clear
# Exit code 1 = missing targets found
```

**Integrate in pre-commit hook:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: docs-reference-targets
        name: Docs Reference Targets
        entry: ./scripts/ops/verify_docs_reference_targets.sh --changed
        language: system
        files: \.md$
```

### Documentation Guidelines

**When writing docs:**
1. For real repo paths → Use as-is (e.g., `src/core/config.py`)
2. For hypothetical examples → Encode (e.g., `config&#47;my_example.toml`)
3. In code examples → Prefer fenced blocks for complex examples
4. Test before PR → Run verification script locally

**Quick test:**
```bash
# Before committing docs:
ls -la path/mentioned/in/docs

# If not found → It's illustrative → Encode it
```

---

## Common Patterns

### Pattern 1: Tutorial Examples

**Scenario:** Tutorial showing how to create custom config

**Before:**
```markdown
1. Create your config: `config&#47;my_backtest.toml`
2. Run: `bash python3 scripts/run_strategy_from_config.py --config config&#47;my_backtest.toml`
```

**After:**
```markdown
1. Create your config: `config/config.toml`
2. Run: `bash python3 scripts/run_strategy_from_config.py --config config/config.toml`
```

### Pattern 2: Walk-Through with Placeholders

**Scenario:** Workflow showing backup with timestamp

**Before:**
```markdown
Backup docs to `docs/ops/_archive/repo_cleanup/2026-01-12/` directory.
```

**After:**
```markdown
Backup docs to `docs/ops/_archive/repo_cleanup/2026-01-12/` directory.
```

### Pattern 3: Script Examples

**Scenario:** Showing hypothetical script invocation

**Before:**
```markdown
For walk-forward validation:
`bash python3 scripts/run_sweep.py --config config/config.toml --strategy ma_crossover --grid config/sweeps/ma_crossover.toml`
```

**Note:** Bevorzuge Beispiele mit existierenden Targets (Scripts/Configs), damit Reference‑Targets strikt bleiben können.

---

## Troubleshooting

### Issue: Gate still fails after neutralization

**Possible causes:**
1. Missed some occurrences (search more thoroughly)
2. Path in fenced code block (check block contents)
3. Path in heading or link text (less common, but possible)

**Solution:**
```bash
# Find ALL occurrences of problematic path
rg -n "config/my_custom.toml" docs/

# Check each occurrence:
# - Inline code → Neutralize
# - Fenced block → Usually safe, but may need neutralization
# - Link → Check if link target exists
```

### Issue: Neutralized path doesn't copy correctly

**Scenario:** User copies command from raw Markdown

**Problem:** Gets `scripts&#47;example.py` instead of:

```text
scripts/example.py
```

**Solution:**
- Educate users: Copy from **rendered view** (GitHub UI), not raw
- For critical commands: Provide both inline and fenced block versions

**Example:**
```markdown
Quick command: `bash python3 scripts&#47;example.py`

Or copy from block below:
~~~bash
python3 scripts/example.py
~~~
```

### Issue: Real path flagged as missing

**Possible causes:**
1. File exists but gate script has bug
2. File in ignored directory (e.g., `reports&#47;`)
3. Path is relative, gate expects different base

**Solution:**
1. Verify file exists: `ls -la <path>`
2. Check gate script: `./scripts/ops/verify_docs_reference_targets.sh --changed --verbose`
3. Check ignore list: `docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt`
4. If legitimate bug → Fix gate script or add to ignore list

---

## References

### Documentation
- [Workflow Notes Frontdoor](../workflows/WORKFLOW_NOTES_FRONTDOOR.md) – Policy explanation
- [Docs Token Policy Gate](RUNBOOK_DOCS_TOKEN_POLICY_GATE.md) – **Automated enforcement** of `&#47;` encoding policy
- [Docs Reference Targets Gate Style Guide](../DOCS_REFERENCE_TARGETS_GATE_STYLE_GUIDE.md) – Comprehensive style guide (if exists)

### Scripts
- `scripts/ops/verify_docs_reference_targets.sh` – Local verification
- Gate implementation: `.github/workflows/docs_reference_targets_gate.yml`

### Example PRs
- PR #690 – Docs frontdoor + crosslink hardening (includes gate fix examples)

---

## Quick Reference Card

```
╔═══════════════════════════════════════════════════════════════╗
║  DOCS REFERENCE TARGETS FALSE POSITIVES - QUICK REF           ║
╠═══════════════════════════════════════════════════════════════╣
║  PROBLEM: Gate fails on illustrative example paths            ║
║                                                               ║
║  DIAGNOSIS:                                                   ║
║    1. Check gate logs for missing targets                    ║
║    2. Verify: ls -la <path>                                  ║
║    3. Classify: Real path vs Illustrative                    ║
║                                                               ║
║  FIX: Neutralize illustrative paths                          ║
║    Before: `config/my_custom.toml`                            ║
║    After:  `config&#47;my_custom.toml`                          ║
║                                                               ║
║  PREVENTION:                                                  ║
║    • Policy: Encode illustrative paths with &#47;            ║
║    • Test: ./scripts/ops/verify_docs_reference_targets.sh    ║
║    • Document: Link to WORKFLOW_NOTES_FRONTDOOR.md           ║
╚═══════════════════════════════════════════════════════════════╝
```

---

**Contact:** Peak_Trade Docs Team  
**See also:** [Ops Hub](../README.md) | [Documentation Frontdoor](../../README.md)
