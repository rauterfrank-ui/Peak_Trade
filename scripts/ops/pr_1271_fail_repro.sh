#!/usr/bin/env bash
# Fastest path: map failing jobs to local entrypoints; prepare CI_COMMANDS_FROM_UI.sh for paste.
set -euo pipefail
cd /Users/frnkhrz/Peak_Trade

PR=1271
BR="feat/metrics-ulcer-recovery"

# 0) Local snapshot
git status -sb
git log -5 --oneline

OUT="out/ops/pr_${PR}_fail_repro"
mkdir -p "$OUT"

# 1) Workflow name map
rg -n "name:\s*CI / PR Gate|name:\s*CI / tests|Docs Token Policy Gate|L4 Critic Replay Determinism|PR Gate|docs-token-policy|run_l4_governance_critic|pytest" \
  .github/workflows/*.yml 2>/dev/null | tee "$OUT/workflow_name_map.txt" || true

# 2) Run blocks for failing-job workflows
{
python3 - <<'PY'
from pathlib import Path
import re
need = re.compile(r"(CI / PR Gate|CI / tests|Docs Token Policy Gate|L4 Critic Replay Determinism|docs-token-policy|run_l4_governance_critic|pytest)", re.I)
for p in sorted(Path(".github/workflows").glob("*.yml")):
    txt = p.read_text(encoding="utf-8")
    if not need.search(txt):
        continue
    print(f"\n##### {p} #####")
    lines = txt.splitlines()
    for i, l in enumerate(lines, 1):
        if re.search(r"^\s*-?\s*run:\s*", l):
            s = max(1, i - 1)
            e = min(len(lines), i + 28)
            print(f"\n-- run block around line {i} --")
            for j in range(s, e + 1):
                print(f"{j:4d} {lines[j-1]}")
PY
} | tee "$OUT/run_blocks_for_failing_jobs.txt"

# 3) PR Gate clues
rg -n "pr gate|PR Gate|required checks|status check|branch behind|mergeable|labels|policy critic|dispatch-guard" \
  scripts .github/workflows 2>/dev/null | tee "$OUT/pr_gate_clues.txt" || true

# 4) Branch vs origin/main
git fetch origin --prune 2>/dev/null || true
git rev-list --left-right --count origin/main...HEAD 2>/dev/null | tee "$OUT/ahead_behind.txt" || true
git merge-base origin/main HEAD 2>/dev/null | tee "$OUT/merge_base.txt" || true

# 5) Docs Token Policy (exact CI command)
python3 scripts/ops/validate_docs_token_policy.py --base origin/main --json "$OUT/docs-token-policy-report.json" 2>&1 \
  | tee "$OUT/docs_token_policy_local.txt" || true

# 6) Pytest: quick run with maxfail=1 to get first failure fast; then full -ra for summary
python3 -m pytest -q --maxfail=1 2>&1 | tee "$OUT/pytest_full_local.txt" || true
python3 -m pytest -q -ra 2>&1 | tail -80 | tee "$OUT/pytest_full_local_ra.txt" || true

# 7) Template for pasting exact commands from GitHub UI
cat > "$OUT/CI_COMMANDS_FROM_UI.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Paste exact failing commands from the GitHub Actions UI here.
# Replace any leading "uv run python" with "python3" if uv is broken locally.
# Example:
# python3 scripts/aiops/run_l4_governance_critic.py <ARGS...>
EOF
chmod +x "$OUT/CI_COMMANDS_FROM_UI.sh"
echo "Created: $OUT/CI_COMMANDS_FROM_UI.sh"
