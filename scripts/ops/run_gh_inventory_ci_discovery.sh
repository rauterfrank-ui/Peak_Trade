#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "GIT-KONTEXT: main (GitHub/CI full inventory; read-only; writes only to out/ops/gh_inventory_*)"

OUT="out/ops/gh_inventory_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT"

echo "1) Repo + auth snapshot"
{
  echo "ts_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
  echo "default_branch=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)"
  echo "head=$(git rev-parse HEAD)"
  echo "branch=$(git rev-parse --abbrev-ref HEAD)"
} | tee "$OUT/snapshot.env"

gh auth status | tee "$OUT/gh_auth_status.txt" || true
gh api rate_limit | tee "$OUT/rate_limit.json" >/dev/null || true

echo "2) Branch protection + required checks (GraphQL)"
gh api graphql -f query='
query {
  repository(owner:"rauterfrank-ui", name:"Peak_Trade") {
    nameWithOwner
    defaultBranchRef {
      name
      branchProtectionRule {
        requiresApprovingReviews
        requiredApprovingReviewCount
        requiresCodeOwnerReviews
        requiresConversationResolution
        requiresStatusChecks
        requiresStrictStatusChecks
        requiredStatusCheckContexts
        requiresLinearHistory
        restrictsPushes
        allowsForcePushes
        lockBranch
      }
    }
  }
}' | tee "$OUT/branch_protection_default_branch.json" >/dev/null

echo "3) Workflows inventory (names, paths, state)"
gh workflow list --all --json id,name,path,state | tee "$OUT/workflows.json" >/dev/null
python3 - <<PY | tee "$OUT/workflows_summary.txt" >/dev/null
import json, pathlib
p=pathlib.Path("$OUT")/"workflows.json"
w=json.loads(p.read_text(encoding="utf-8"))
print("workflows:", len(w))
states=sorted(set(x.get("state") for x in w))
print("by_state:", {s:sum(1 for x in w if x.get("state")==s) for s in states})
PY

echo "4) Parse workflow YAML for triggers + concurrency + permissions + job names"
python3 - <<PY
from pathlib import Path
import yaml, json

root=Path(".github/workflows")
rows=[]
for f in sorted(root.glob("*.yml")) + sorted(root.glob("*.yaml")):
    try:
        d=yaml.safe_load(f.read_text(encoding="utf-8"))
    except Exception as e:
        rows.append({"path": str(f), "yaml_ok": False, "error": str(e)})
        continue
    on=d.get("on")
    conc=d.get("concurrency")
    perms=d.get("permissions")
    jobs=d.get("jobs") or {}
    job_names=sorted(list(jobs.keys()))
    has_strategy_smoke=any("strategy" in j.lower() and "smoke" in j.lower() for j in job_names)
    rows.append({
        "path": str(f),
        "name": d.get("name"),
        "yaml_ok": True,
        "on": on,
        "has_schedule": isinstance(on, dict) and "schedule" in on,
        "has_workflow_dispatch": isinstance(on, dict) and "workflow_dispatch" in on,
        "has_pull_request": isinstance(on, dict) and "pull_request" in on,
        "has_push": isinstance(on, dict) and "push" in on,
        "concurrency": conc,
        "permissions": perms,
        "job_count": len(job_names),
        "job_names": job_names,
        "has_strategy_smoke_job": has_strategy_smoke,
    })
out=Path("$OUT")/"workflows_parsed.json"
out.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
print(out)
PY

echo "5) Required checks reconciliation check (capture stdout/stderr to file)"
test -f config/ci/required_status_checks.json && cp config/ci/required_status_checks.json "$OUT/required_status_checks.json" || true
mkdir -p "$OUT/required_checks_reconcile"
python3 scripts/ops/reconcile_required_checks_branch_protection.py \
  --check \
  --required-config config/ci/required_status_checks.json \
  --owner rauterfrank-ui \
  --repo Peak_Trade \
  --branch main \
  2>&1 | tee "$OUT/required_checks_reconcile/reconcile_output.txt" || true

echo "6) Recent runs for core pipelines (last 20 each, JSON; best-effort)"
for WF in \
  prk-prj-status-report.yml \
  pro-prk-nightly-selfcheck.yml \
  prbc-stability-gate.yml \
  prbd-live-readiness-scorecard.yml \
  prbe-shadow-testnet-scorecard.yml \
  prbg-execution-evidence.yml \
  prbi-live-pilot-scorecard.yml \
  prbj-testnet-exec-events.yml \
  prcc-aws-export-smoke.yml \
  prcd-aws-export-write-smoke.yml \
  ci.yml
do
  gh run list --workflow "$WF" --branch main --limit 20 \
    --json databaseId,status,conclusion,event,createdAt,updatedAt,url \
    > "$OUT/runs_${WF//\//_}.json" 2>/dev/null || true
done

echo "7) Concurrency grep"
rg -n "concurrency:|cancel-in-progress:" .github/workflows -S > "$OUT/concurrency_grep.txt" || true

echo "8) Index"
ls -la "$OUT" > "$OUT/ls.txt"
echo "$OUT" > "$OUT/OUTDIR.txt"

echo "DONE: inventory written to $OUT"
