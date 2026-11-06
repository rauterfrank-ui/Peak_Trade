#!/usr/bin/env bash
set -euo pipefail

echo "GIT-KONTEXT: main (pull latest PR-BG execution evidence artifact into out/ops/prbg_latest)"

OUT="out/ops/prbg_latest"
rm -rf "${OUT}" || true
mkdir -p "${OUT}"

RUN_ID="$(gh run list --workflow prbg-execution-evidence.yml --branch main --limit 10 --json databaseId,status,conclusion,createdAt,event --jq '.[] | select(.status=="completed") | select(.conclusion=="success") | .databaseId' | head -n 1)"
echo "RUN_ID=${RUN_ID}"
test -n "${RUN_ID}"

gh run download "${RUN_ID}" --dir "${OUT}" >/dev/null 2>&1 || true

P_JSON="$(find "${OUT}" -type f -name execution_evidence.json | head -n 1 || true)"
echo "execution_evidence.json=${P_JSON}"
test -n "${P_JSON}"

python3 - <<PY
import json
from pathlib import Path
p=Path("${P_JSON}")
o=json.loads(p.read_text(encoding="utf-8"))
print("status:", o.get("status"))
print("sample_size:", o.get("sample_size"))
print("anomaly_count:", o.get("anomaly_count"))
print("error_count:", o.get("error_count"))
PY

echo "OK: updated ${OUT}"
