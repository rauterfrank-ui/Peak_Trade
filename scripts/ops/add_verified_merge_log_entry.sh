#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  ./scripts/ops/add_verified_merge_log_entry.sh <PR_NUM> "<PR_TITLE>" [--no-commit]

Examples:
  ./scripts/ops/add_verified_merge_log_entry.sh 999 "Risk Layer: Phase 6 Integration (VaR Validation Pipeline)"
  ./scripts/ops/add_verified_merge_log_entry.sh 413 "VaR Validation Phase 2 (Kupiec + Traffic Light)" --no-commit
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || "${#}" -lt 2 ]]; then
  usage
  exit 0
fi

PR_NUM="$1"
PR_TITLE="$2"
NO_COMMIT="0"
if [[ "${3:-}" == "--no-commit" ]]; then
  NO_COMMIT="1"
fi

# Paths
README_PATH="docs/ops/README.md"
MERGE_LOG_PATH="docs/ops/PR_${PR_NUM}_MERGE_LOG.md"

if [[ ! -f "$README_PATH" ]]; then
  echo "❌ Expected $README_PATH to exist. Run from repo root?"
  exit 1
fi

# Safety: don't stomp on dirty trees by default (keep it simple: warn only)
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "⚠️ Working tree is not clean. Script will proceed, but commit may include unrelated changes."
fi

# 1) Create merge log file if missing
if [[ -f "$MERGE_LOG_PATH" ]]; then
  echo "ℹ️ Merge log already exists: $MERGE_LOG_PATH (no overwrite)"
else
  mkdir -p "$(dirname "$MERGE_LOG_PATH")"
  cat > "$MERGE_LOG_PATH" <<MD
# PR #${PR_NUM} — ${PR_TITLE}

Summary
- <One-line summary of what changed. Keep it operator-readable.>

Why
- <Reason / problem solved / roadmap gate satisfied.>

Changes
- Code
  - [ ] <path/to/main_change_1>
  - [ ] <path/to/main_change_2>
- Tests
  - [ ] <path/to/tests>
- Docs
  - [ ] <path/to/docs>

Verification
- Local:
  - \`pytest -q <subset>\`
- CI:
  - <required checks green>

Risk
- LOW — <one sentence why low risk.>
- Remaining risks:
  - <edgecase> → Mitigation: <test/doc/policy>

Operator How-To
- <how to run it / where to find output>
- Example:
  - <one-liner command or python snippet>

References
- PR: #${PR_NUM}
- Branch: <branch-name>
- Commit: <sha>
- Docs:
  - <roadmap link / operator hub link>
MD
  echo "✅ Created: $MERGE_LOG_PATH"
fi

# 2) Update docs/ops/README.md (idempotent)
python3 - <<PY
from pathlib import Path

readme = Path("${README_PATH}")
text = readme.read_text(encoding="utf-8")

header = "## Verified Merge Logs"
line = f"- **PR #${PR_NUM} (${PR_TITLE}, verified)** → \`${MERGE_LOG_PATH}\`"

# Ensure header exists
if header not in text:
    text = text.rstrip() + "\\n\\n" + header + "\\n"

# Avoid duplicates (by PR number)
if f"PR #${PR_NUM}" in text:
    # If PR already listed, do nothing
    readme.write_text(text, encoding="utf-8")
    print("ℹ️ README already contains entry for PR #${PR_NUM} (no duplicate).")
    raise SystemExit(0)

lines = text.splitlines()

# Insert line right after header
out = []
inserted = False
for i, ln in enumerate(lines):
    out.append(ln)
    if (not inserted) and ln.strip() == header:
        out.append(line)
        inserted = True

new_text = "\\n".join(out).rstrip() + "\\n"
readme.write_text(new_text, encoding="utf-8")
print("✅ Updated README with verified merge log link.")
PY

# 3) Stage changes
git add "$README_PATH" "$MERGE_LOG_PATH" || true

# 4) Commit (optional / idempotent)
if [[ "$NO_COMMIT" == "1" ]]; then
  echo "ℹ️ --no-commit set. Staged changes only."
  exit 0
fi

if git diff --cached --quiet; then
  echo "ℹ️ No staged changes to commit."
  exit 0
fi

git commit -m "docs(ops): add verified merge log for PR #${PR_NUM}"
echo "✅ Committed."
