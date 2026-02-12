#!/usr/bin/env bash
# Extract exact CI commands from .github/workflows + reproduce locally.
set -euo pipefail
cd /Users/frnkhrz/Peak_Trade

BR="feat/metrics-ulcer-recovery"
PR=1271

git checkout "$BR"
git fetch origin --prune
git status -sb

OUT="out/ops/pr_${PR}_ci_exact_cmds"
mkdir -p "$OUT"

# 0) Snapshot current workflow files
ls -la .github/workflows 2>/dev/null | tee "$OUT/workflows_ls.txt"

# 1) Find workflow/job definitions
rg -n "Docs Token Policy|docs-token-policy|validate_docs_token_policy|L4 Critic Replay Determinism|run_l4_governance_critic|validate_l4_critic_determinism" \
  .github/workflows/*.yml 2>/dev/null | tee "$OUT/workflow_hits.txt" || true

# 2) Print run blocks from relevant workflows
{
python3 - <<'PY'
from pathlib import Path
import re
paths = sorted(Path(".github/workflows").glob("*.yml"))
need = re.compile(r"(docs[-_]token|token[-_]policy|validate_docs_token_policy|L4 Critic Replay|run_l4_governance_critic|validate_l4_critic_determinism)", re.I)
for p in paths:
    txt = p.read_text(encoding="utf-8")
    if not need.search(txt):
        continue
    print(f"\n##### {p} #####")
    lines = txt.splitlines()
    for i, l in enumerate(lines, 1):
        if re.search(r"^\s*-?\s*run:\s*$", l) or re.search(r"^\s*run:\s*\|\s*$", l):
            s = max(1, i - 1)
            e = min(len(lines), i + 25)
            print(f"\n-- run block around line {i} --")
            for j in range(s, e + 1):
                print(f"{j:4d} {lines[j-1]}")
PY
} | tee "$OUT/run_blocks.txt"

# 3) Exact Docs Token Policy command (from docs-token-policy-gate.yml)
# CI: python scripts/ops/validate_docs_token_policy.py --base "${base}" --json docs-token-policy-report.json
# Default when no --all/--changed is: --changed (see --help)
echo "=== Reproduce Docs Token Policy Gate (exact CI command) ===" | tee "$OUT/repro_token.txt"
python3 scripts/ops/validate_docs_token_policy.py --help 2>&1 | tee "$OUT/token_help.txt" || true

BASE_REF="origin/main"
python3 scripts/ops/validate_docs_token_policy.py --base "$BASE_REF" --json "$OUT/docs-token-policy-report.json" 2>&1 | tee "$OUT/token_ci_repro.txt" || true

# 4) Exact L4 Critic Replay Determinism commands (from l4_critic_replay_determinism_v2.yml)
# CI does NOT run pytest; it runs:
#   uv run python scripts/aiops/run_l4_governance_critic.py ... (then diff vs snapshot, then run twice and diff)
echo "=== Reproduce L4 Critic Replay Determinism (exact CI steps) ===" | tee "$OUT/repro_l4.txt"
cat >> "$OUT/repro_l4.txt" <<'L4CMDS'
# Step 1: Run L4 critic (replay mode)
rm -rf .tmp/l4_critic_out
uv run python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay \
  --fixture l4_critic_sample \
  --out .tmp/l4_critic_out \
  --pack-id L1_sample_2026-01-10 \
  --schema-version 1.0.0 \
  --deterministic \
  --no-legacy-output

# Step 2: Verify output files
test -f .tmp/l4_critic_out/critic_report.json
test -f .tmp/l4_critic_out/critic_summary.md

# Step 3: Compare with snapshot
SNAP_DIR="tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0"
diff -u "$SNAP_DIR/critic_report.json" ".tmp/l4_critic_out/critic_report.json"
diff -u "$SNAP_DIR/critic_summary.md" ".tmp/l4_critic_out/critic_summary.md"
L4CMDS

# Run the L4 steps locally (if uv available)
if command -v uv >/dev/null 2>&1; then
  echo "=== Running L4 Step 1 (run_l4_governance_critic) ===" | tee -a "$OUT/l4_local_run.txt"
  rm -rf .tmp/l4_critic_out
  uv run python scripts/aiops/run_l4_governance_critic.py \
    --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
    --mode replay \
    --fixture l4_critic_sample \
    --out .tmp/l4_critic_out \
    --pack-id L1_sample_2026-01-10 \
    --schema-version 1.0.0 \
    --deterministic \
    --no-legacy-output 2>&1 | tee -a "$OUT/l4_local_run.txt" || true
  echo "=== Step 2: Verify files ===" | tee -a "$OUT/l4_local_run.txt"
  test -f .tmp/l4_critic_out/critic_report.json && echo "critic_report.json OK" | tee -a "$OUT/l4_local_run.txt"
  test -f .tmp/l4_critic_out/critic_summary.md && echo "critic_summary.md OK" | tee -a "$OUT/l4_local_run.txt"
  echo "=== Step 3: diff vs snapshot ===" | tee -a "$OUT/l4_local_run.txt"
  SNAP_DIR="tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0"
  diff -u "$SNAP_DIR/critic_report.json" ".tmp/l4_critic_out/critic_report.json" 2>&1 | tee -a "$OUT/l4_local_run.txt" || true
  diff -u "$SNAP_DIR/critic_summary.md" ".tmp/l4_critic_out/critic_summary.md" 2>&1 | tee -a "$OUT/l4_local_run.txt" || true
else
  echo "uv not found; skip L4 run. Install uv and re-run." | tee "$OUT/l4_local_run.txt"
fi

# 5) gh: pull failing job logs
if command -v gh >/dev/null 2>&1; then
  gh pr checks "$PR" 2>&1 | tee "$OUT/gh_pr_checks.txt" || true
  gh run list --branch "$BR" --limit 20 2>&1 | tee "$OUT/gh_run_list.txt" || true
  RUN_ID=$(awk 'NR==1{print $1}' "$OUT/gh_run_list.txt" 2>/dev/null || true)
  if test -n "${RUN_ID:-}"; then
    gh run view "$RUN_ID" --log-failed 2>&1 | tee "$OUT/gh_run_log_failed.txt" || true
  fi
fi

# 6) Summary: exact commands for copy-paste
cat > "$OUT/EXACT_CI_COMMANDS.md" <<'MD'
# Exact CI commands (from .github/workflows)

## Docs Token Policy Gate
- **Workflow:** `.github/workflows/docs-token-policy-gate.yml`
- **Base ref:** `origin/main` (or `origin/${GITHUB_BASE_REF}` for PRs)
- **Command:**
```bash
python scripts/ops/validate_docs_token_policy.py \
  --base origin/main \
  --json docs-token-policy-report.json
```
- **Note:** No `--changed` or `--all` in workflow; script default is changed-only when no mode given.

## L4 Critic Replay Determinism
- **Workflow:** `.github/workflows/l4_critic_replay_determinism_v2.yml`
- **Not pytest.** Steps:
  1. Run critic: `uv run python scripts/aiops/run_l4_governance_critic.py` (see run_blocks.txt)
  2. Verify .tmp/l4_critic_out/critic_report.json and critic_summary.md exist
  3. diff vs snapshot in tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0/
  4. validate_l4_critic_determinism_contract.py
  5. normalize_validator_report.py
  6. Run critic twice, diff the two outputs

**Reproduce locally (step 1–3):**
```bash
rm -rf .tmp/l4_critic_out
uv run python scripts/aiops/run_l4_governance_critic.py \
  --evidence-pack tests/fixtures/evidence_packs/L1_sample_2026-01-10 \
  --mode replay --fixture l4_critic_sample --out .tmp/l4_critic_out \
  --pack-id L1_sample_2026-01-10 --schema-version 1.0.0 \
  --deterministic --no-legacy-output
test -f .tmp/l4_critic_out/critic_report.json
test -f .tmp/l4_critic_out/critic_summary.md
SNAP_DIR="tests/fixtures/l4_critic_determinism/l4_critic_sample__pack-L1_sample_2026-01-10__schema-1.0.0"
diff -u "$SNAP_DIR/critic_report.json" ".tmp/l4_critic_out/critic_report.json"
diff -u "$SNAP_DIR/critic_summary.md" ".tmp/l4_critic_out/critic_summary.md"
```
MD
cat "$OUT/EXACT_CI_COMMANDS.md" | tee -a "$OUT/run_blocks.txt"

echo "Done. See $OUT/EXACT_CI_COMMANDS.md and $OUT/run_blocks.txt"
