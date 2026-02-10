#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# [AGENT:planner] Automerge-Regression: Kandidaten aus main-Log ermitteln
# Erzeugt: out/ops/automerge_regression/main_log_last80.txt,
#          auto_merge_hits.txt, pr_candidates.txt
# ─────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
mkdir -p out/ops/automerge_regression

git checkout main
git fetch origin --prune
git reset --hard origin/main

git log -80 --oneline --decorate > out/ops/automerge_regression/main_log_last80.txt
rg -n 'auto: .* -> main \(#' out/ops/automerge_regression/main_log_last80.txt > out/ops/automerge_regression/auto_merge_hits.txt || true

python3 - <<'PY'
import re, pathlib, sys
p=pathlib.Path("out/ops/automerge_regression/auto_merge_hits.txt")
s=p.read_text(encoding="utf-8") if p.exists() else ""
prs=[int(m.group(1)) for m in re.finditer(r'\(#(\d+)\)', s)]
prs=sorted(set(prs), reverse=True)
pathlib.Path("out/ops/automerge_regression/pr_candidates.txt").write_text("\n".join(map(str,prs))+"\n", encoding="utf-8")
print("PR_CANDIDATES=", prs[:20])
print("PICKED=", prs[0] if prs else "NONE")
PY
