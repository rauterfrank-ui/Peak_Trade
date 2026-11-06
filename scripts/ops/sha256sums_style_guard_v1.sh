#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/ops/sha256sums_style_guard_v1.sh <SHA256SUMS.txt>
# Exit: 0 if style OK, 3 if absolute/parent paths or malformed lines.
# Enforces repo-root-relative paths (no /, no ../) so verify must run from repo root.

SHA_FILE="${1:-}"
if [[ -z "${SHA_FILE}" ]] || [[ ! -f "${SHA_FILE}" ]]; then
  echo "SHA256SUMS_STYLE_GUARD_FAIL: missing_or_invalid sha_file=${SHA_FILE}" >&2
  exit 2
fi

python3 - "${SHA_FILE}" <<'PY'
import re, sys
p=sys.argv[1]
bad=[]
with open(p,"r",encoding="utf-8") as f:
    for i,l in enumerate(f,1):
        l=l.rstrip("\n")
        if not l.strip():
            continue
        m=re.fullmatch(r"([0-9a-f]{64})\s+(.+)", l.strip())
        if not m:
            bad.append((i,"format",l))
            continue
        path=m.group(2)
        if path.startswith("/"):
            bad.append((i,"absolute_path",l))
        if path.startswith("../"):
            bad.append((i,"parent_path",l))
if bad:
    print("SHA256SUMS_STYLE_FAIL", p, file=sys.stderr)
    for i,k,l in bad[:20]:
        print(f"line={i} kind={k} :: {l}", file=sys.stderr)
    sys.exit(3)
print("SHA256SUMS_STYLE_OK", p, "style=repo_root_relative")
PY
