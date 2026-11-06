#!/bin/bash
set -euo pipefail

REPO="${REPO:-rauterfrank-ui/Peak_Trade}"
START="${1:-230}"
END="${2:-}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1" >&2; exit 1; }; }
need gh
need jq

if [[ -z "${END}" ]]; then
  END="$(gh pr list --repo "$REPO" --state all --limit 1 --json number -q '.[0].number')"
fi

TS="$(date +%Y%m%d_%H%M%S)"
OUT="reports/pr_audit_scan_${START}_${END}_${TS}.tsv"
mkdir -p "$(dirname "$OUT")"
echo -e "pr\tstate\tmergedAt\tconclusion\tcheck_name\tcheck_url\tpr_url\ttitle" > "$OUT"

first_bad=""
for pr in $(seq "$START" "$END"); do
  json="$(gh pr view "$pr" --repo "$REPO" --json number,state,mergedAt,title,url,statusCheckRollup 2>/dev/null || true)"
  [[ -z "$json" ]] && continue

  state="$(jq -r '.state' <<<"$json")"
  mergedAt="$(jq -r '.mergedAt // ""' <<<"$json")"
  title="$(jq -r '.title' <<<"$json" | tr '\t' ' ' | tr '\n' ' ')"
  prurl="$(jq -r '.url' <<<"$json")"

  rows="$(jq -r '
    .statusCheckRollup
    | map(select(.name | test("(^|\\s)audit(\\s|$|\\()"; "i")))
    | if length==0 then "" else
        .[] | "\(.name)\t\(.conclusion // .state // "UNKNOWN")\t\(.detailsUrl // "")"
      end
  ' <<<"$json")"

  if [[ -z "$rows" ]]; then
    echo -e "${pr}\t${state}\t${mergedAt}\tNO_AUDIT\t\t\t${prurl}\t${title}" >> "$OUT"
    [[ -z "$first_bad" ]] && first_bad="$pr"
    continue
  fi

  while IFS=$'\t' read -r name conclusion details; do
    echo -e "${pr}\t${state}\t${mergedAt}\t${conclusion}\t${name}\t${details}\t${prurl}\t${title}" >> "$OUT"
    if [[ "$conclusion" != "SUCCESS" && "$conclusion" != "success" ]]; then
      [[ -z "$first_bad" ]] && first_bad="$pr"
    fi
  done <<<"$rows"
done

echo "OK -> $OUT"
echo
echo "== Auffälligkeiten (≠ SUCCESS oder NO_AUDIT) =="
awk -F'\t' 'NR==1{next} ($4!="SUCCESS" && $4!="success"){print}' "$OUT" | head -n 60

echo
echo "== Erste auffällige PR =="
if [[ -n "$first_bad" ]]; then
  echo "PR #$first_bad"
  echo "Open: gh pr view $first_bad --repo $REPO --web"
else
  echo "Keine Auffälligkeiten in PR $START..$END."
fi
