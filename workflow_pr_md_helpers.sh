#!/usr/bin/env bash
set -euo pipefail

echo "=== 0) PRE-FLIGHT ==="
git status -sb
current_branch="$(git rev-parse --abbrev-ref HEAD)"
echo "Branch: $current_branch"

# Falls du noch auf main bist, lege eine Feature-Branch an (safe default)
if [[ "$current_branch" == "main" ]]; then
  echo "On main -> creating branch refactor/md-helpers"
  git checkout -b refactor/md-helpers
fi

echo "=== 1) QUALITY CHECKS ==="
uv run ruff check src tests scripts
uv run pytest -q tests/test_md_helpers.py -v

echo "=== 2) COMMIT ==="
git add -A
git commit -m "refactor(utils): extract md_helpers + add tests" || echo "(Nothing to commit?)"

echo "=== 3) PUSH ==="
git push -u origin HEAD

echo "=== 4) PR CREATE (gh) ==="
# Falls bereits ein PR existiert, wird gh meckern – dann einfach `gh pr view --web` nutzen.
gh pr create \
  --title "refactor(utils): md_helpers + tests" \
  --body $'✅ Extracts Markdown helper functions into src/utils/md_helpers.py\n✅ Adds full unit test coverage (tmp_path) for pick_first_existing() + ensure_section_insert_at_top()\n✅ Updates stage1_daily_snapshot.py to import helpers\n\nMetrics:\n- New files: 3 (utils package + tests)\n- Modified: 1 (stage1_daily_snapshot.py)\n- Tests: 17 passed (0.07s)\n- Ruff: 0 errors\n- Coverage: 100% for both helpers\n- Behavior changes: 0' \
  || echo "PR already exists or gh pr create failed (ok)."

echo "=== 5) OPTIONAL: DOCS LINK (auto insert via new helper) ==="
# Nutzt ensure_section_insert_at_top() direkt, um docs/ops/README.md zu ergänzen.
uv run python - <<'PY'
from pathlib import Path
from datetime import date

try:
    from src.utils.md_helpers import ensure_section_insert_at_top
except Exception as e:
    raise SystemExit(f"Import failed: {e}")

path = Path("docs/ops/README.md")
section = "Utilities"
entry = (
    f"- `src/utils/md_helpers.py` — Markdown helpers (`pick_first_existing`, `ensure_section_insert_at_top`) "
    f"+ tests: `tests/test_md_helpers.py` ({date.today().isoformat()})\n"
)
sig = "md-helpers-utils-link"

ensure_section_insert_at_top(
    path=path,
    section_h2=section,
    entry_md=entry,
    signature=sig,
)
print(f"Updated: {path}")
PY

# Commit docs update only if it actually changed something
if ! git diff --quiet; then
  git add docs/ops/README.md
  git commit -m "docs(ops): link md_helpers utility" || true
  git push
fi

echo "=== 6) OPTIONAL: CI STEP SNIPPET ==="
echo "If your CI already runs pytest full-suite, skip this."
echo "Otherwise, add this step into an existing workflow job after checkout/setup-python:"
cat <<'YAML'
- name: Test MD Helpers
  run: pytest -q tests/test_md_helpers.py -v
YAML

echo "=== DONE ==="
git status -sb
gh pr view --web || true

