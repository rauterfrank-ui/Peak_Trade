#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# [AGENT:implementer] Automerge-Regression: GitHub-API-Daten für gewählten PR holen
# Erfordert: GITHUB_TOKEN, vorher automerge_regression_planner.sh
# Erzeugt: pr_<PR>.json, reviews, issue_events, timeline, check_runs, status, actions_runs
# ─────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
OWNER="${GITHUB_REPOSITORY_OWNER:-rauterfrank-ui}"
REPO="${GITHUB_REPOSITORY_NAME:-Peak_Trade}"
# Falls GITHUB_REPOSITORY gesetzt (owner/repo), daraus parsen
if [[ -n "${GITHUB_REPOSITORY:-}" ]]; then
  OWNER="${GITHUB_REPOSITORY%%/*}"
  REPO="${GITHUB_REPOSITORY#*/}"
fi
API="https://api.github.com/repos/${OWNER}/${REPO}"
EVID="out/ops/automerge_regression"
mkdir -p "$EVID"

test -n "${GITHUB_TOKEN:-}" || { echo "GITHUB_TOKEN_MISSING"; exit 1; }
curl -s -o /dev/null -w "TOKEN_HTTP=%{http_code}\n" -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" https://api.github.com/user | tee "$EVID/token_check.txt"

PR="$(head -n 1 "$EVID/pr_candidates.txt" | tr -d '\r\n')"
test -n "$PR" || { echo "NO_PR_CANDIDATES"; exit 1; }
echo "$PR" > "$EVID/PR_PICKED.txt"

curl -fsS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  "$API/pulls/$PR" -o "$EVID/pr_${PR}.json"

curl -fsS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  "$API/pulls/$PR/reviews?per_page=100" -o "$EVID/pr_${PR}_reviews.json"

curl -fsS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  "$API/issues/$PR/events?per_page=100" -o "$EVID/pr_${PR}_issue_events.json"

curl -fsS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  "$API/pulls/$PR/timeline?per_page=100" -H "X-GitHub-Api-Version: 2022-11-28" \
  -o "$EVID/pr_${PR}_timeline.json" || true

python3 - <<'PY'
import json, pathlib
E=pathlib.Path("out/ops/automerge_regression")
PR=int((E/"PR_PICKED.txt").read_text().strip())
pr=json.loads((E/f"pr_{PR}.json").read_text(encoding="utf-8"))
actor=(pr.get("merged_by") or {}).get("login")
merged=pr.get("merged")
merge_commit=pr.get("merge_commit_sha")
state=pr.get("state")
base=pr.get("base",{}).get("ref")
head=pr.get("head",{}).get("ref")
print("PR=",PR,"state=",state,"merged=",merged,"base=",base,"head=",head,"merged_by=",actor,"merge_commit=",merge_commit)

# timeline sniff (best-effort; may be blocked if previews disabled)
p=E/f"pr_{PR}_timeline.json"
if p.exists():
    try:
        t=json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        t=[]
    def typ(x): return x.get("event") or x.get("__typename") or ""
    hits=[]
    for x in t if isinstance(t,list) else []:
        ev=typ(x)
        if any(k in ev.lower() for k in ("merged","auto_merge","labeled","ready_for_review")):
            hits.append((ev,(x.get("actor") or {}).get("login"), x.get("created_at")))
    if hits:
        (E/f"pr_{PR}_timeline_hits.txt").write_text("\n".join([str(h) for h in hits])+"\n", encoding="utf-8")
        print("TIMELINE_HITS=",len(hits))
    else:
        print("TIMELINE_HITS=0")
PY

python3 - <<'PY'
import json, pathlib
E=pathlib.Path("out/ops/automerge_regression")
PR=int((E/"PR_PICKED.txt").read_text().strip())
pr=json.loads((E/f"pr_{PR}.json").read_text(encoding="utf-8"))
head_sha=pr["head"]["sha"]
(E/"HEAD_SHA.txt").write_text(head_sha+"\n", encoding="utf-8")
print("HEAD_SHA=",head_sha)
PY

SHA="$(cat "$EVID/HEAD_SHA.txt" | tr -d '\r\n')"

curl -fsS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  "$API/commits/$SHA/check-runs?per_page=100" -o "$EVID/check_runs_${SHA}.json"

curl -fsS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  "$API/commits/$SHA/status" -o "$EVID/combined_status_${SHA}.json"

curl -fsS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  "$API/actions/runs?per_page=100" -o "$EVID/actions_runs_100.json"

python3 - <<'PY'
import json, pathlib
E=pathlib.Path("out/ops/automerge_regression")
sha=(E/"HEAD_SHA.txt").read_text().strip()
runs=json.loads((E/"actions_runs_100.json").read_text(encoding="utf-8")).get("workflow_runs",[])
rs=[r for r in runs if r.get("head_sha")==sha]
out=[]
for r in rs:
    out.append((r.get("name"), r.get("event"), r.get("conclusion"), r.get("html_url")))
(E/"runs_for_sha.txt").write_text("\n".join([f"{a} | event={b} | {c} | {d}" for a,b,c,d in out])+"\n", encoding="utf-8")
print("RUNS_FOR_SHA=",len(out))
print("\n".join([f"- {a} ({b}) {c}" for a,b,c,d in out[:30]]))
PY
