#!/usr/bin/env bash
# TOOL/ORT: Terminal (Shell) im Repo ~/Peak_Trade
# ZIEL: Docs/Runbook updaten (README + Cheat-Sheet) für „DRY_RUN → Real Merge" Workflow
#       und direkt Commit + PR erstellen.

set -euo pipefail

REPO="${REPO:-$HOME/Peak_Trade}"
cd "$REPO"

# 0) Preflight
echo "==> Git Status:"
git status
echo ""

echo "==> Switching to main..."
git switch main || git checkout main
git pull --ff-only

BRANCH="docs/ops-merge-both-prs-dryrun-workflow"
echo "==> Creating branch: $BRANCH"
git switch -c "$BRANCH" || git checkout -b "$BRANCH"

# 1) Upsert: Workflow-Snippet in die beiden Docs (mit stabilen Markern)
echo "==> Updating docs with DRY_RUN workflow snippet..."

python3 - <<'PY'
from pathlib import Path
import re

MARKER_BEGIN = "<!-- BEGIN MERGE_BOTH_PRS_DRYRUN_WORKFLOW -->"
MARKER_END   = "<!-- END MERGE_BOTH_PRS_DRYRUN_WORKFLOW -->"

SNIPPET = f"""{MARKER_BEGIN}

### Workflow: DRY_RUN → Real Merge

```bash
# Step 1: Test erst (DRY_RUN)
DRY_RUN=true DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

# Falls Output: "✅ Done. Both PRs processed."
# → Alle Checks grün!

# Step 2: Echtes Merge
DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh
```

**Warum DRY_RUN?**
- ✅ Testet alle Fail-Fast-Checks (state, draft, base, mergeable, reviewDecision)
- ✅ Kein Merge, keine Git-State-Changes
- ✅ Safe-by-default Testing vor echtem Merge

{MARKER_END}
"""

def upsert_snippet(file_path: Path, insert_after: str):
    """Fügt oder updated Snippet in Datei ein."""
    if not file_path.exists():
        print(f"⚠️  {file_path} does not exist, skipping")
        return

    content = file_path.read_text()

    # Check if snippet already exists
    if MARKER_BEGIN in content:
        # Update: Replace between markers
        pattern = re.compile(
            re.escape(MARKER_BEGIN) + r".*?" + re.escape(MARKER_END),
            re.DOTALL
        )
        new_content = pattern.sub(SNIPPET.strip(), content)
        print(f"✅ Updated snippet in: {file_path}")
    else:
        # Insert: Add after insert_after string
        if insert_after in content:
            new_content = content.replace(insert_after, f"{insert_after}\n\n{SNIPPET.strip()}")
            print(f"✅ Inserted snippet in: {file_path}")
        else:
            print(f"⚠️  Insert marker '{insert_after}' not found in {file_path}, appending at end")
            new_content = content + f"\n\n{SNIPPET.strip()}\n"

    file_path.write_text(new_content)

# Target files
readme = Path("docs/ops/README.md")
cheatsheet = Path("docs/ops/pr_bodies/MERGE_BOTH_PRS_CHEATSHEET.md")

# Update README (insert after Quick Reference section)
upsert_snippet(
    readme,
    "REQUIRE_APPROVAL=false DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh"
)

# Update Cheat-Sheet (insert after Quick Start section)
upsert_snippet(
    cheatsheet,
    "WATCH_CHECKS=false RUN_PYTEST=false DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh"
)

print("\n✅ Docs updated successfully")
PY

echo ""
echo "==> Staged changes:"
git add docs/ops/README.md docs/ops/pr_bodies/MERGE_BOTH_PRS_CHEATSHEET.md
git diff --cached --stat

echo ""
echo "==> Committing..."
git commit -m "docs(ops): add DRY_RUN → Real Merge workflow to merge_both_prs docs

- Add workflow snippet to README.md (Quick Reference section)
- Add workflow snippet to MERGE_BOTH_PRS_CHEATSHEET.md
- Explains: DRY_RUN for testing, then real merge

Why: Document best practice workflow (test first, merge second)
Risk: Low (docs-only)"

echo ""
echo "==> Pushing..."
git push -u origin "$BRANCH"

echo ""
echo "==> Creating PR..."
gh pr create \
  --base main \
  --title "docs(ops): add DRY_RUN → Real Merge workflow" \
  --body "## Summary

Add **DRY_RUN → Real Merge** workflow snippet to merge_both_prs documentation.

## Changes

- \`docs/ops/README.md\`: Add workflow snippet (Quick Reference section)
- \`docs/ops/pr_bodies/MERGE_BOTH_PRS_CHEATSHEET.md\`: Add workflow snippet

## Why

Document best practice: Test with \`DRY_RUN=true\` first, then real merge if checks pass.

## Verification

\`\`\`bash
grep -A 10 'BEGIN MERGE_BOTH_PRS_DRYRUN_WORKFLOW' docs/ops/README.md
grep -A 10 'BEGIN MERGE_BOTH_PRS_DRYRUN_WORKFLOW' docs/ops/pr_bodies/MERGE_BOTH_PRS_CHEATSHEET.md
\`\`\`

**Risk:** Low (docs-only)" \
  --label "docs/ops"

echo ""
echo "✅ Done!"
echo "Branch: $BRANCH"
echo "Next: Review PR and merge"
