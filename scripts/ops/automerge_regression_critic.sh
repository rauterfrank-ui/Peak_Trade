#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# [AGENT:critic] Automerge-Regression: Evidence auswerten (Merge-Actor, Checks, Workflows)
# Erfordert: automerge_regression_implementer.sh vorher ausgeführt
# Erzeugt: likely_automerge_workflows.txt, Konsolen-Zusammenfassung
# ─────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
EVID="out/ops/automerge_regression"
PR="$(cat "$EVID/PR_PICKED.txt" | tr -d '\r\n')"

echo "EVID_DIR=$EVID"
echo "PR=$PR"

python3 - <<'PY'
import json, pathlib, re
E=pathlib.Path("out/ops/automerge_regression")
PR=int((E/"PR_PICKED.txt").read_text().strip())
pr=json.loads((E/f"pr_{PR}.json").read_text(encoding="utf-8"))
merged_by=(pr.get("merged_by") or {}).get("login")
title=pr.get("title")
merged=pr.get("merged")
merge_commit=pr.get("merge_commit_sha")
labels=[x.get("name") for x in pr.get("labels",[])]
print("PR_TITLE=",title)
print("MERGED=",merged)
print("MERGED_BY=",merged_by)
print("MERGE_COMMIT=",merge_commit)
print("LABELS=",labels)

# classify actor
actor=merged_by or ""
if actor in ("github-actions","github-actions[bot]"):
    cls="MERGED_BY_GITHUB_ACTIONS"
elif actor.endswith("[bot]"):
    cls="MERGED_BY_BOT"
elif actor:
    cls="MERGED_BY_HUMAN_OR_SERVICE"
else:
    cls="MERGED_BY_UNKNOWN"
print("MERGE_ACTOR_CLASS=",cls)

# summarize checks presence on that head sha
sha=pr["head"]["sha"]
cr=json.loads((E/f"check_runs_{sha}.json").read_text(encoding="utf-8")).get("check_runs",[])
cs=json.loads((E/f"combined_status_{sha}.json").read_text(encoding="utf-8"))
names=sorted({r.get("name") for r in cr if r.get("name")})
ctx=sorted({s.get("context") for s in cs.get("statuses",[]) if s.get("context")})
print("CHECK_RUNS_COUNT=",len(cr))
print("CHECK_RUN_NAMES_SAMPLE=",names[:25])
print("LEGACY_CONTEXTS_COUNT=",len(ctx))
print("LEGACY_CONTEXTS_SAMPLE=",ctx[:25])

# identify likely "automerge enabler" workflow names
runs=(E/"runs_for_sha.txt").read_text(encoding="utf-8").splitlines()
likely=[ln for ln in runs if re.search(r'(merge|automerge|auto-merge|enable)', ln, re.I)]
(E/"likely_automerge_workflows.txt").write_text("\n".join(likely)+"\n", encoding="utf-8")
print("LIKELY_AUTOMERGE_WORKFLOWS=",len(likely))
for ln in likely[:20]:
    print(" -",ln)
PY

echo "DONE. Open these evidence files:"
ls -la "$EVID" | sed -n '1,120p'
