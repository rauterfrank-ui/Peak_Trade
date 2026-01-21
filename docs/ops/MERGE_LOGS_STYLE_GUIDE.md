# Merge Logs Style Guide

## Purpose
Ensure merge logs are **gate-safe** (pass docs-reference-targets gate), readable, and free from false positives or hidden Unicode issues.

---

## Rule 1: Only Reference Existing Paths as Real Paths

**Real paths** (files/directories that currently exist in the repo) should be written normally:

```markdown
✓ scripts/ci/validate_git_state.sh
✓ docs/ops/README.md
✓ src/data/safety/
```

These will be validated by the docs-reference-targets gate and must exist.

---

## Rule 2: De-Pathify Historical/Removed/Non-Existent Paths

If referencing a **historical**, **removed**, or **non-existent** path (e.g., in "before" examples, deprecated scripts, or legacy references), **de-pathify** by escaping forward slashes:

```markdown
✗ scripts&#47;inspect_offline_feed.py (raw, triggers gate: file not found)
✓ scripts&#47;inspect_offline_feed.py (de-pathified, safe)

✗ scripts&#47;validate_git_state.sh (raw, old location, moved)
✓ scripts&#47;validate_git_state.sh (de-pathified, safe)
```

**How:** Replace `/` with `&#47;` (HTML entity).  
**Why:** Prevents the gate from treating these as filesystem targets.  
**Renders as:** Normal `/` in HTML/markdown (invisible to readers).

---

## Rule 3: Simplify rg Examples (No Path Prefixes)

In `rg` (ripgrep) command examples, **omit directory prefixes** to avoid creating path patterns:

```markdown
✗ rg -n "scripts&#47;inspect_offline_feed\.py" docs
✓ rg -n "inspect_offline_feed\.py" docs

✗ rg -n "scripts&#47;validate_git_state\.sh" docs
✓ rg -n "validate_git_state\.sh" docs
```

**Why:** Simpler, more readable, avoids false positives from path scanners.

---

## Rule 4: Unicode Hygiene (No Bidi/Zero-Width Characters)

**Prohibited characters:**
- **Bidi control chars:** LRE/RLE/PDF/LRO/RLO/LRI/RLI/FSI/PDI/LRM/RLM/ALM (`\u202A-\u202E`, `\u2066-\u2069`, `\u200E-\u200F`, `\u061C`)
- **Zero-width chars:** ZWSP/ZWNJ/ZWJ/WJ/BOM (`\u200B-\u200D`, `\u2060`, `\uFEFF`)
- **Soft hyphen:** `\u00AD`

**Why:** GitHub flags these with security warnings; they can obscure content.

**Verification (optional one-liner):**

```bash
python3 - <<'PY'
from pathlib import Path
BIDI = {"\u202A","\u202B","\u202C","\u202D","\u202E","\u2066","\u2067","\u2068","\u2069","\u200E","\u200F","\u061C","\ufeff"}
ZWSP = {"\u200B","\u200C","\u200D","\u2060","\u00AD"}
ALL = BIDI | ZWSP
for p in Path("docs/ops").glob("*.md"):
    txt = p.read_text(encoding="utf-8")
    hits = [(i, f"U+{ord(ch):04X}") for i, ch in enumerate(txt) if ch in ALL]
    if hits: print(f"{p}: {len(hits)} hits")
if not any(Path("docs/ops").glob("*.md")): print("OK: No hidden chars detected")
PY
```

---

## Rule 5: Merge Log Template

Use this structure for all merge logs:

```markdown
# PR #XXX — [Title]

## Summary
[Brief description of what was changed]

## Why
[Motivation: why was this change needed?]

## Changes
- [List of changes]
- [Bullet points preferred]

## Verification
- [How was this verified?]
- [CI checks, manual tests, etc.]

## Risk
[Risk assessment: Minimal/Low/Medium/High + rationale]

## Operator How-To
- [Guidance for operators]
- [How to use/apply these changes]

## References
- PR #XXX
- Related PRs/Issues

---

## Extended

[Optional: Detailed technical notes, full file lists, merge strategy details, etc.]
```

**Compact + Extended Pattern:**
- **Compact** (top): Fast scannable executive summary
- **Extended** (bottom, optional): Deep audit trail, technical context

---

## Quick Checklist

Before committing a merge log:

- [ ] Real paths written normally (e.g., `scripts&#47;ci&#47;...`)
- [ ] Historical/removed paths de-pathified (e.g., `scripts&#47;old-script.sh`)
- [ ] `rg` examples without path prefixes (e.g., `rg -n "pattern"`)
- [ ] No bidi/zero-width characters (run verification script if unsure)
- [ ] Follows template structure (Summary/Why/Changes/Verification/Risk/Operator How-To/References)

---

## Examples

**Good:**

```markdown
## Changes
- De-pathified removed script: `scripts&#47;inspect_offline_feed.py`
- Updated reference to current location: `scripts/ci/validate_git_state.sh`

## Verification
- `rg -n "inspect_offline_feed\.py" docs` returns 0 raw paths ✅
```

**Bad:**

```markdown
## Changes
- De-pathified removed script: scripts&#47;inspect_offline_feed.py
  (triggers gate: file not found!)

## Verification
- `rg -n "scripts&#47;inspect_offline_feed\.py" docs` returns 0 matches
  (path pattern in example)
```

---

## How to Generate

**Automated Generation (Recommended):**

Use the `new_merge_log.py` generator with GitHub CLI integration:

```bash
# Auto-fetch PR metadata via gh CLI
python scripts/ops/new_merge_log.py --pr 450

# Custom output location
python scripts/ops/new_merge_log.py --pr 450 --out docs/ops/custom_name.md

# Fallback mode (template with placeholders)
python scripts/ops/new_merge_log.py --pr 450 --fallback

# Skip README update
python scripts/ops/new_merge_log.py --pr 450 --no-update-readme
```

**Hygiene Check:**

Before committing, run the hygiene checker to catch issues:

```bash
# Check a single file
python scripts/ops/check_merge_log_hygiene.py docs/ops/PR_450_MERGE_LOG.md

# Check multiple files (glob pattern)
python scripts/ops/check_merge_log_hygiene.py docs/ops/PR_*_MERGE_LOG.md

# Verbose mode
python scripts/ops/check_merge_log_hygiene.py -v docs/ops/PR_450_MERGE_LOG.md
```

**What the hygiene checker finds:**
- Forbidden local paths: `/Users/`, `/home/`, `C:\`, `~/`
- Unicode issues: Bidi controls, Zero-Width chars, BOM, Surrogates

**CI Integration:**

The hygiene check runs automatically on PRs that modify merge logs (informational only, non-blocking).

---

## See Also

- [Merge Log Workflow](MERGE_LOG_WORKFLOW.md) — Process for creating merge logs
- [Docs Reference Targets Gate](../ops/README.md#docs-reference-targets) — Gate documentation
- [Verified Merge Logs](../ops/README.md#verified-merge-logs) — Examples (PRs 446-448)

---

**Version:** 1.0  
**Last Updated:** 2025-12-31  
**Maintainer:** Peak_Trade Ops Team
