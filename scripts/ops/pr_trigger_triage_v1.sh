#!/usr/bin/env bash
# === Cursor Multi-Agent Orchestrator: Trigger greift nicht (PR Checks fehlen) ===
# Ziel: feststellen ob "Waiting for status to be reported"/nur 1-3 Checks → EINMAL retriggern → required checks watchen
# Usage: ./scripts/ops/pr_trigger_triage_v1.sh
# Voraussetzung: auf Feature-Branch (nicht main), gh verfügbar

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# ---------------------------
# Agent 0 — Preflight
# ---------------------------
git status -sb
git fetch origin --prune

# Aktuellen Branch ermitteln (sollte dein Feature-Branch sein, NICHT main)
BR="$(git branch --show-current)"
if [ "${BR}" = "main" ]; then
  echo "ERR: du bist auf main. Bitte auf den Feature-Branch wechseln." >&2
  exit 2
fi
echo "BR=${BR}"

# ---------------------------
# Agent 1 — PR Nummer finden (HEAD Branch)
# ---------------------------
PR_NUM="$(gh pr list --state open --head "${BR}" --json number --jq '.[0].number' 2>/dev/null || true)"
if [ -z "${PR_NUM}" ]; then
  # fallback: evtl. schon closed/merged oder anderer head-name
  echo "WARN: Kein offener PR für head=${BR} gefunden. Suche in closed..." >&2
  PR_NUM="$(gh pr list --state closed --head "${BR}" --json number --jq '.[0].number' 2>/dev/null || true)"
fi
if [ -z "${PR_NUM}" ]; then
  echo "ERR: PR nicht gefunden für head=${BR}. Öffne PR Liste: gh pr list --state open" >&2
  exit 3
fi
echo "PR_NUM=${PR_NUM}"
gh pr view "${PR_NUM}" --json url,state,mergeStateStatus,headRefName,baseRefName,title \
  --jq '"url="+.url+"\nstate="+.state+"\nmergeStateStatus="+.mergeStateStatus+"\nhead="+.headRefName+"\nbase="+.baseRefName+"\ntitle="+.title'

# ---------------------------
# Agent 2 — Checks Snapshot (Diagnose)
# ---------------------------
EVI="out/ops/pr${PR_NUM}_trigger_triage_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${EVI}"
gh pr checks "${PR_NUM}" > "${EVI}/PR_CHECKS.txt" 2>/dev/null || true
wc -l "${EVI}/PR_CHECKS.txt" 2>/dev/null | awk '{print "CHECK_LINES="$1}' || echo "CHECK_LINES=0"
grep -nE "Expected|Waiting for status to be reported|pending|in_progress" "${EVI}/PR_CHECKS.txt" 2>/dev/null || true

CHECK_LINES="$(wc -l < "${EVI}/PR_CHECKS.txt" 2>/dev/null | tr -d ' \n' || echo 0)"
CHECK_LINES="${CHECK_LINES:-0}"
HAS_WAITING="NO"
if grep -qE "Expected|Waiting for status to be reported" "${EVI}/PR_CHECKS.txt" 2>/dev/null; then HAS_WAITING="YES"; fi
echo "CHECK_LINES=${CHECK_LINES} HAS_WAITING=${HAS_WAITING}" | tee "${EVI}/DECISION.txt"

# ---------------------------
# Agent 3 — Retrigger (nur wenn wirklich nötig)
# Regel: retrigger wenn (LINES <= 3) ODER (Expected/Waiting)
# ---------------------------
if [ "${HAS_WAITING}" = "YES" ] || [ "${CHECK_LINES}" -le 3 ]; then
  echo "ACTION: RETRIGGER (empty commit) — weil Checks fehlen/Waiting" | tee "${EVI}/ACTION.txt"

  # bevorzugt: kanonisches Retrigger-Script (sicher: nur feature-branch, clean tree)
  if [ -x "./scripts/ops/ci_pr_checks_retrigger_v1.sh" ]; then
    ./scripts/ops/ci_pr_checks_retrigger_v1.sh
  else
    # fallback: direkt empty commit
    git commit --allow-empty -m "ci: retrigger required PR checks (synchronize)"
    git push origin HEAD
  fi
else
  echo "ACTION: NO_RETRIGGER — Checks laufen/werden reported" | tee "${EVI}/ACTION.txt"
fi

# ---------------------------
# Agent 4 — Required Checks Watch (blocking, bis grün/rot)
# ---------------------------
# Wenn required checks noch gar nicht reported werden, ist das EIN Indikator, dass Trigger nicht gegriffen hat.
# Dann nach retrigger sollte das kommen.
./scripts/ops/pr_ops_v1.sh "${PR_NUM}" --watch --retrigger-on-waiting

# ---------------------------
# Agent 5 — Ergebnis ausgeben
# ---------------------------
gh pr view "${PR_NUM}" --json state,mergeStateStatus,mergedAt,url \
  --jq '"state="+.state+"\nmergeStateStatus="+.mergeStateStatus+"\nmergedAt="+( .mergedAt // "null")+"\nurl="+.url' \
  | tee "${EVI}/PR_VIEW_POST.txt"

echo "OK: triage done → ${EVI}"
