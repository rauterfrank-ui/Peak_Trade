#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

OPENPTS_DEFAULT="docs/UEBERSICHT_OFFENE_PUNKTE.md"

# Pick newest runbook by mtime (macOS/BSD stat)
pick_runbook() {
  find docs -type f \( -path 'docs/ops/runbooks/*.md' -o -iname '*runbook*.md' \) 2>/dev/null \
    | while IFS= read -r f; do
        printf "%s %s\n" "$(stat -f '%m' "$f" 2>/dev/null || echo 0)" "$f"
      done \
    | sort -rn \
    | head -1 \
    | cut -d' ' -f2-
}

RUNBOOK="${RUNBOOK:-$(pick_runbook)}"
OPENPTS="${OPENPTS:-$OPENPTS_DEFAULT}"

echo "RUNBOOK=$RUNBOOK"
echo "OPENPTS=$OPENPTS"

mkdir -p artifacts/closeout

python3 - <<'PY'
from pathlib import Path
import re, json, time, subprocess, os

root = Path(subprocess.check_output(["git","rev-parse","--show-toplevel"], text=True).strip())
runbook = Path(os.environ.get("RUNBOOK",""))
if not runbook.is_absolute():
    runbook = (root / runbook) if str(runbook) else None
openpts = Path(os.environ.get("OPENPTS","docs/UEBERSICHT_OFFENE_PUNKTE.md"))
if not openpts.is_absolute():
    openpts = root / openpts

def read(p: Path) -> str:
    if not p or not p.exists(): return ""
    return p.read_text(encoding="utf-8", errors="replace")

def extract_headings(md: str):
    hs = []
    for m in re.finditer(r'^(#{1,4})\s+(.+?)\s*$', md, flags=re.M):
        hs.append({"level": len(m.group(1)), "title": m.group(2)})
    return hs

def extract_checkbox_todos(md: str):
    return [m.group(1).strip() for m in re.finditer(r'^\s*[-*]\s+\[ \]\s+(.+)\s*$', md, flags=re.M)]

def extract_bullets(md: str):
    out = []
    for m in re.finditer(r'^\s*[-*]\s+(?!\[[ xX]\])(.+)\s*$', md, flags=re.M):
        s = m.group(1).strip()
        if s and not s.startswith("|"):
            out.append(s)
    return out

def extract_table_rows(md: str):
    rows = []
    for line in md.splitlines():
        if line.count("|") >= 2 and not re.match(r'^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$', line):
            rows.append(line.strip())
    return rows

def openpoints_tasks(md: str):
    tasks = []
    tasks += [{"source":"checkbox","text":t} for t in extract_checkbox_todos(md)]
    tasks += [{"source":"bullet","text":t} for t in extract_bullets(md)]
    markers = re.compile(r'\b(todo|offen|open|blocked|wip|in progress|pending)\b', re.I)
    for row in extract_table_rows(md):
        if markers.search(row):
            tasks.append({"source":"table_row","text":row})
    seen = set()
    uniq = []
    for t in tasks:
        key = t["text"]
        if key in seen: continue
        seen.add(key)
        uniq.append(t)
    return uniq

rb_text = read(runbook) if runbook else ""
op_text = read(openpts)

out = {
  "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  "runbook_path": str(runbook.relative_to(root)) if runbook and runbook.exists() else None,
  "open_points_path": str(openpts.relative_to(root)) if openpts.exists() else None,
  "runbook_headings": extract_headings(rb_text),
  "runbook_todos": extract_checkbox_todos(rb_text),
  "open_points_tasks": openpoints_tasks(op_text),
}

dst = root/"artifacts/closeout/PHASE_H_TODO_INDEX.json"
dst.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("wrote", dst)
print("runbook_exists", bool(runbook and runbook.exists()))
print("open_points_exists", openpts.exists())
PY

python3 - <<'PY'
import json
p="artifacts/closeout/PHASE_H_TODO_INDEX.json"
d=json.load(open(p,"r",encoding="utf-8"))
print("runbook_path:", d["runbook_path"])
print("headings:", len(d["runbook_headings"]))
print("runbook_todos:", len(d["runbook_todos"]))
print("open_points_tasks:", len(d["open_points_tasks"]))
PY
