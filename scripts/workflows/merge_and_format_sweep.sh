#!/usr/bin/env bash
set -euo pipefail

# =========================
# CONFIG
# =========================
REPO_DIR="${REPO_DIR:-$HOME/Peak_Trade}"
PR_NUM="${PR_NUM:-216}"

# Optional: zusätzlich einen großen Test-PR (>1200 Files) erzeugen (CI-Test, NICHT mergen)
RUN_LARGE_SIM="${RUN_LARGE_SIM:-0}"   # 0/1
LARGE_SIM_FILES="${LARGE_SIM_FILES:-1250}"

# Label für >1200 Files
LARGE_LABEL="large-pr-approved"

# Sensitive paths (für schnelle Sichtprüfung, nicht als Gate)
SENSITIVE_RE='^(src/(governance|execution|risk|live)/|scripts/live/)'

say() { printf "\n\033[1m%s\033[0m\n" "$*"; }
require_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1"; exit 1; }; }

git_clean_or_die() {
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Working tree is not clean. Please commit/stash first."
    git status
    exit 1
  fi
}

require_cmd git
require_cmd gh
require_cmd uv

say "0) Repo wechseln & Basis-Checks"
cd "$REPO_DIR"
git rev-parse --show-toplevel >/dev/null
git fetch --prune
git status -sb
git_clean_or_die

say "1) PR #$PR_NUM Checks ansehen"
gh pr view "$PR_NUM" >/dev/null || {
  echo "gh konnte PR nicht lesen (TLS/Auth?). Öffne ggf. im Browser."
  exit 1
}
gh pr checks "$PR_NUM" || true

say "2) Merge versuchen (squash + branch delete)"
if gh pr merge "$PR_NUM" --squash --delete-branch; then
  say "✅ PR #$PR_NUM wurde gemerged."
else
  echo "❌ Merge fehlgeschlagen (vermutlich required checks/rote Checks)."
  echo "→ Prüfe Branch protection / required checks in GitHub."
  exit 1
fi

say "3) main aktualisieren"
git checkout main
git pull --ff-only
git status -sb
git_clean_or_die

say "4) Format-Sweep Branch erstellen + pre-commit über alles"
BR="chore/format-sweep-precommit-$(date +%Y-%m-%d)"
git checkout -b "$BR"

uv run pre-commit run --all-files

say "5) Committen, Pushen, PR erstellen"
git add -A

if git diff --cached --quiet; then
  say "ℹ️ Keine Änderungen durch pre-commit. Kein PR nötig."
  exit 0
fi

git commit -m "chore(format): pre-commit format sweep"
git push -u origin "$BR"

CHANGED_FILES="$(git diff --name-only origin/main...HEAD | wc -l | tr -d ' ')"
SENSITIVE_HITS="$(git diff --name-only origin/main...HEAD | grep -E "$SENSITIVE_RE" | wc -l | tr -d ' ')"

say "   Changed files vs origin/main: $CHANGED_FILES"
say "   Sensitive-path hits:         $SENSITIVE_HITS"

BODY=$'Format sweep to test Large-PR handling.\n\nExpected behavior:\n- >250 files => Policy Critic LITE mode\n- >1200 files => add label large-pr-approved to allow LITE_MINIMAL (non-sensitive only)\n\nGenerated via: uv run pre-commit run --all-files\n'

PR_URL="$(gh pr create \
  --title "chore(format): pre-commit format sweep" \
  --body "$BODY" \
  --base main \
  --json url -q .url)"

say "✅ Format-Sweep PR erstellt: $PR_URL"

say "6) Optional: Label setzen, falls >1200 Files"
if [ "$CHANGED_FILES" -gt 1200 ]; then
  say "   >1200 Files erkannt → Label '$LARGE_LABEL' wird gesetzt"
  gh pr edit "$PR_URL" --add-label "$LARGE_LABEL"
else
  say "   <=1200 Files → kein Label nötig"
fi

say "7) Checks beobachten"
gh pr checks "$PR_URL" --watch || true

say "8) OPTIONAL: Large-PR Simulation PR"
if [ "$RUN_LARGE_SIM" = "1" ]; then
  git checkout main
  git pull --ff-only
  git_clean_or_die

  SIM_BR="test/ci-large-pr-${LARGE_SIM_FILES}-$(date +%Y-%m-%d)"
  git checkout -b "$SIM_BR"

  python - <<PY
from pathlib import Path
base = Path("docs/_ci_large_pr_test")
base.mkdir(parents=True, exist_ok=True)
N = int("${LARGE_SIM_FILES}")
for i in range(1, N+1):
    (base / f"dummy_{i:04d}.md").write_text(
        f"# CI Large PR Test File {i}\n\n"
        "Purpose: exercise Policy Critic large-PR modes & Quarto path filter.\n",
        encoding="utf-8",
    )
(base / "README.md").write_text(
    "# CI Large PR Test\n\n"
    "This folder exists to exercise CI large-PR handling (Policy Critic modes, label override, Quarto path filtering).\n"
    "Do not merge into main; close PR after verification.\n",
    encoding="utf-8",
)
print(f"Created {N} dummy files under {base}")
PY

  git add -A
  git commit -m "test(ci): large PR simulation (>1200 files) for policy critic"
  git push -u origin "$SIM_BR"

  SIM_PR_URL="$(gh pr create \
    --title "test(ci): large PR simulation (>1200 files)" \
    --body "CI test only: verifies Policy Critic large-PR mode selection + label override + Quarto path filter. Do not merge." \
    --base main \
    --json url -q .url)"

  say "✅ Large-Sim PR erstellt: $SIM_PR_URL"
  gh pr edit "$SIM_PR_URL" --add-label "$LARGE_LABEL"
  gh pr checks "$SIM_PR_URL" --watch || true

  say "Cleanup (optional):"
  echo "  gh pr close \"$SIM_PR_URL\" --comment \"CI large-PR handling verified. Closing test PR.\""
  echo "  gh pr delete \"$SIM_PR_URL\" --yes"
fi

say "DONE ✅"
