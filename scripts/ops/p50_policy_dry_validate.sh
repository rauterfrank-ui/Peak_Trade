#!/usr/bin/env bash
# CURSOR_MULTI_AGENT_ORCHESTRATOR (P50 dry-validate, no live calls)
# Assumptions:
# - Repo: Peak_Trade
# - main is clean & synced
# - We do NOT enable live model calls; we only validate policy+audit+token flows locally.
# - PEAKTRADE_AI_CONFIRM_SECRET must be set for mint/verify (e.g. export PEAKTRADE_AI_CONFIRM_SECRET=test-secret)

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# ------------------------------------------------------------------------------
# Agent 0 — Preflight (must be clean)
# ------------------------------------------------------------------------------
git checkout main
git fetch origin --prune
git reset --hard origin/main
git status -sb
git diff --quiet && git diff --cached --quiet || { echo "ERROR: working tree has modified tracked files"; exit 1; }

# ------------------------------------------------------------------------------
# Agent 1 — Locate P50 CLI + run status (JSON)
# ------------------------------------------------------------------------------
python3 - <<'PY'
import importlib
m = importlib.import_module("src.ops.p50.ai_model_policy_cli_v1")
print("OK: imported", m.__name__)
PY

python3 -m src.ops.p50.ai_model_policy_cli_v1 --json status | tee /tmp/p50_policy_status.json

# ------------------------------------------------------------------------------
# Agent 2 — Mint token + verify token (still no model call)
#   - Token minted locally; verify should succeed deterministically.
#   - We keep artifacts in /tmp and out/ops for evidence.
# ------------------------------------------------------------------------------
TS="$(date -u +%Y%m%dT%H%M%SZ)"
EVI="out/ops/p50_policy_dry_validate_${TS}"
mkdir -p "${EVI}"

# Mint token (capture JSON) — CLI requires --reason
python3 -m src.ops.p50.ai_model_policy_cli_v1 --json mint-token --reason "p50_dry_validate" | tee "${EVI}/mint_token.json"

# Extract token string (mint --json outputs JSON string; may also be dict with token key)
TOKEN="$(
python3 - <<'PY' "${EVI}/mint_token.json"
import json,sys
p=sys.argv[1]
d=json.load(open(p,"r",encoding="utf-8"))
if isinstance(d,str) and d:
    print(d)
    raise SystemExit(0)
for k in ("token","confirm_token","enable_token","arm_token","minted_token"):
    if isinstance(d,dict) and k in d and isinstance(d[k],str) and d[k]:
        print(d[k])
        raise SystemExit(0)
print("")
PY
)"
test -n "${TOKEN}" || { echo "ERROR: could not extract token from ${EVI}/mint_token.json"; exit 1; }

# ------------------------------------------------------------------------------
# Agent 3 — Enable + Arm (policy state transition)
#   - enable/arm do NOT take --token; they toggle internal policy state.
#   - Must be done BEFORE verify (policy_allows_ai_call_v1 requires enabled+armed).
# ------------------------------------------------------------------------------
python3 -m src.ops.p50.ai_model_policy_cli_v1 --json enable | tee "${EVI}/enable.json"
python3 -m src.ops.p50.ai_model_policy_cli_v1 --json arm    | tee "${EVI}/arm.json"

# Verify token (capture JSON) — now enabled+armed, verify should succeed
python3 -m src.ops.p50.ai_model_policy_cli_v1 --json verify --token "${TOKEN}" | tee "${EVI}/verify_token.json"

python3 -m src.ops.p50.ai_model_policy_cli_v1 --json status | tee "${EVI}/status_after_enable_arm.json"

# ------------------------------------------------------------------------------
# Agent 4 — Audit trail smoke (expect evidence of transitions)
#   - We don't know your exact audit storage, so we snapshot repo-local likely locations.
# ------------------------------------------------------------------------------
{
  echo "TS=${TS}"
  echo "MAIN_HEAD=$(git rev-parse HEAD)"
  echo "STATUS_JSON=/tmp/p50_policy_status.json"
  echo "EVI=${EVI}"
} | tee "${EVI}/META.txt"

# Snapshot likely audit dirs (best-effort; ignore if missing)
for d in out/ops out/audit out/logs .tmp tmp; do
  if [ -d "$d" ]; then
    find "$d" -maxdepth 4 -type f \( -iname '*ai*model*policy*audit*' -o -iname '*policy*audit*' \) 2>/dev/null | head -n 200 > "${EVI}/AUDIT_FILE_CANDIDATES_${d//\//_}.txt" || true
  fi
done

# ------------------------------------------------------------------------------
# Agent 5 — Safety: reset policy back to deny-by-default (recommended)
# ------------------------------------------------------------------------------
if python3 -m src.ops.p50.ai_model_policy_cli_v1 --help 2>/dev/null | grep -qE 'disable'; then
  python3 -m src.ops.p50.ai_model_policy_cli_v1 --json disable | tee "${EVI}/disable.json"
fi
if python3 -m src.ops.p50.ai_model_policy_cli_v1 --help 2>/dev/null | grep -qE 'disarm'; then
  python3 -m src.ops.p50.ai_model_policy_cli_v1 --json disarm | tee "${EVI}/disarm.json"
fi

python3 -m src.ops.p50.ai_model_policy_cli_v1 --json status | tee "${EVI}/status_final.json"

# ------------------------------------------------------------------------------
# Agent 6 — Evidence bundle + hashes (ARG_MAX-safe)
# ------------------------------------------------------------------------------
find "${EVI}" -maxdepth 1 -type f ! -name 'SHA256SUMS.txt' -print0 \
  | LC_ALL=C sort -z \
  | while IFS= read -r -d '' f; do shasum -a 256 "$f"; done > "${EVI}/SHA256SUMS.txt"

tar -czf "${EVI}.bundle.tgz" "${EVI}"
shasum -a 256 "${EVI}.bundle.tgz" | tee "${EVI}.bundle.tgz.sha256"

echo "P50_DRY_VALIDATE_OK evi=${EVI} bundle=${EVI}.bundle.tgz main_head=$(git rev-parse HEAD)"
