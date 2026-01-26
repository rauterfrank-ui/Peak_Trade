#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# AI Live Local Verify Wrapper (Single Source of Truth)
# - NO-LIVE HARD. Snapshot-only. No watch loops.
# - No pipes in this wrapper script.
# - File-backed evidence: wrapper OUT + pointers to canonical verify/activity evidence dirs.
#
# This wrapper intentionally composes the proven workflow:
# - (Optional) deterministic activity demo (uses existing exporter; does NOT start exporter here)
# - Canonical verify: scripts/obs/ai_live_ops_verify.sh

STAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
OUT=".local_tmp/ai_live_local_verify_${STAMP_UTC}"
mkdir -p "$OUT"

PROM_URL="${PROM_URL:-http://127.0.0.1:9092}"
GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"

# Port Contract v1 strict: exporter :9110 only.
AI_LIVE_PORT_FIXED="9110"
if [[ -n "${AI_LIVE_PORT:-}" && "${AI_LIVE_PORT}" != "${AI_LIVE_PORT_FIXED}" ]]; then
  echo "ERROR: Port Contract v1 strict. AI_LIVE_PORT must be ${AI_LIVE_PORT_FIXED} (got: ${AI_LIVE_PORT})" >&2
  echo "NEXT: Stop the process on :9110 (or free it) and rerun." >&2
  exit 2
fi
AI_LIVE_PORT="${AI_LIVE_PORT_FIXED}"

EXPORTER_URL_DEFAULT="http://127.0.0.1:${AI_LIVE_PORT}/metrics"
if [[ -n "${EXPORTER_URL:-}" && "${EXPORTER_URL}" != "${EXPORTER_URL_DEFAULT}" ]]; then
  echo "ERROR: Port Contract v1 strict. EXPORTER_URL must be ${EXPORTER_URL_DEFAULT} (got: ${EXPORTER_URL})" >&2
  echo "NEXT: Ensure exporter is on :9110 and use default EXPORTER_URL." >&2
  exit 2
fi
EXPORTER_URL="${EXPORTER_URL_DEFAULT}"

RUN_ID="${RUN_ID:-demo}"
COMPONENT="${COMPONENT:-execution_watch}"

# Deterministic activity uses a repo-backed file path; wrapper enforces existence + truncation.
EVENTS_JSONL="${EVENTS_JSONL:-logs/ai/ai_events.jsonl}"

verify_rc=0
exporter_ok=0

finalize_evidence() {
  set +e

  {
    echo "timestamp_utc=$STAMP_UTC"
    echo "repo_root=$(pwd)"
    echo "out_dir=$OUT"
    echo "prom_url=$PROM_URL"
    echo "grafana_url=$GRAFANA_URL"
    echo "exporter_url=$EXPORTER_URL"
    echo "ai_live_port=$AI_LIVE_PORT"
    echo "run_id=$RUN_ID"
    echo "component=$COMPONENT"
    echo "events_jsonl=$EVENTS_JSONL"
    echo "exporter_ok=$exporter_ok"
    echo "verify_rc=$verify_rc"
    echo "git_rev=$(git rev-parse HEAD 2>/dev/null || true)"
  } >"$OUT/META.txt"

  # Latest evidence dirs (no pipes)
  python3 - "$OUT" <<'PY'
from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

out_dir = Path(sys.argv[1])

def latest(glob_pat: str, limit: int = 5) -> list[str]:
    paths = [Path(p) for p in glob.glob(glob_pat)]
    paths = [p for p in paths if p.exists()]
    paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(p) for p in paths[:limit]]

lines = []
lines.append("LATEST_DIRS (most recent first)")
lines.append("")
lines.append("ai_live_ops_verify:")
for p in latest(".local_tmp/ai_live_ops_verify_*", limit=5):
    lines.append(f"  {p}")
lines.append("")
lines.append("ai_live_activity_demo:")
for p in latest(".local_tmp/ai_live_activity_demo_*", limit=5):
    lines.append(f"  {p}")
lines.append("")

(out_dir / "LATEST_DIRS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote: {out_dir / 'LATEST_DIRS.txt'}")
PY

  # Operator note template
  if [[ ! -f "$OUT/OPERATOR_NOTE.txt" ]]; then
    cat >"$OUT/OPERATOR_NOTE.txt" <<EOF
AI LIVE LOCAL VERIFY — OPERATOR NOTE
timestamp_utc=$STAMP_UTC
repo_root=$(pwd)
run_id=$RUN_ID
component=$COMPONENT

WHO:
- <name/handle>

WHY:
- <what are you verifying?>

WHAT CHANGED (if any):
- <notes>

RESULT:
- verify_rc=$verify_rc

ARTIFACTS:
- wrapper_out=$OUT
- see LATEST_DIRS.txt for latest ai_live_ops_verify_* and ai_live_activity_demo_* dirs
EOF
  fi

  # Manifest (sha256) for wrapper OUT (no pipes)
  python3 - "$OUT" <<'PY'
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

out_dir = Path(sys.argv[1]).resolve()
rows = []
for root, _, files in os.walk(out_dir):
    for fn in files:
        p = Path(root) / fn
        rel = p.relative_to(out_dir)
        h = hashlib.sha256()
        try:
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            rows.append((str(rel), h.hexdigest()))
        except Exception as e:
            rows.append((str(rel), f"ERROR:{e.__class__.__name__}"))

rows.sort(key=lambda t: t[0])
manifest = out_dir / "MANIFEST_SHA256.txt"
manifest.write_text(
    "\n".join(f"{sha256}  {rel}" for rel, sha256 in rows) + "\n",
    encoding="utf-8",
)
print(f"wrote: {manifest}")
PY

  # Key material scan (head-only heuristic; no pipes)
  python3 - "$OUT" <<'PY'
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

out_dir = Path(sys.argv[1]).resolve()

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private_key_block", re.compile(r"BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY", re.I)),
    ("aws_access_key_id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("aws_secret_key", re.compile(r"AWS_SECRET_ACCESS_KEY", re.I)),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z\\-_]{20,}")),
    ("bearer_token", re.compile(r"Authorization\\s*:\\s*Bearer\\s+\\S+", re.I)),
    ("generic_token", re.compile(r"\\b(token|api[_-]?key|secret|password)\\b", re.I)),
]

MAX_BYTES = 4096  # head-only heuristic
hits: list[str] = []

def scan_file(p: Path) -> None:
    try:
        b = p.open("rb").read(MAX_BYTES)
    except Exception:
        return
    txt = b.decode("utf-8", errors="replace")
    lines = txt.splitlines()
    for i, ln in enumerate(lines, start=1):
        for name, rx in PATTERNS:
            if rx.search(ln):
                hits.append(f"{p.relative_to(out_dir)}:{i}:{name}:{ln[:240]}")

for root, _, files in os.walk(out_dir):
    for fn in files:
        scan_file(Path(root) / fn)

hits.sort()
out = out_dir / "KEY_MATERIAL_SCAN.txt"
if hits:
    out.write_text("HITS (head-only heuristic)\n" + "\n".join(hits) + "\n", encoding="utf-8")
else:
    out.write_text("NO_HITS (head-only heuristic)\n", encoding="utf-8")
print(f"wrote: {out}")
PY

  set -e
  return 0
}

trap finalize_evidence EXIT

echo "==> AI Live Local Verify Wrapper (snapshot-only)"
echo "OUT=$OUT"

echo "==> Preconditions probes (health/ready/metrics; timeouts; file-backed)"
curl --fail --silent --show-error --connect-timeout 1 --max-time 2 \
  "$PROM_URL/-/healthy" >"$OUT/prom_healthy.txt" 2>"$OUT/prom_healthy.err" || true
curl --fail --silent --show-error --connect-timeout 1 --max-time 2 \
  "$PROM_URL/-/ready" >"$OUT/prom_ready.txt" 2>"$OUT/prom_ready.err" || true
curl --fail --silent --show-error --connect-timeout 1 --max-time 2 \
  "$PROM_URL/metrics" >"$OUT/prom_metrics.txt" 2>"$OUT/prom_metrics.err" || true

curl --fail --silent --show-error --connect-timeout 1 --max-time 2 \
  "$GRAFANA_URL/api/health" >"$OUT/grafana_health.json" 2>"$OUT/grafana_health.err" || true

set +e
curl --fail --silent --show-error --connect-timeout 1 --max-time 2 \
  "$EXPORTER_URL" >"$OUT/exporter_metrics_probe.txt" 2>"$OUT/exporter_metrics_probe.err"
exporter_probe_rc=$?
set -e
if [[ "$exporter_probe_rc" = "0" ]]; then
  exporter_ok=1
else
  exporter_ok=0
fi
echo "$exporter_ok" >"$OUT/exporter_ok.txt"

echo "==> Deterministic activity prerequisites (repo file)"
mkdir -p "$(dirname "$EVENTS_JSONL")"
: >"$EVENTS_JSONL"
echo "$EVENTS_JSONL" >"$OUT/events_jsonl_path.txt"

echo "==> Activity demo (deterministic; only if exporter OK; no exporter start)"
if [[ "$exporter_ok" = "1" ]]; then
  set +e
  SKIP_EXPORTER_START=1 \
  EXPORTER_URL="$EXPORTER_URL" \
  EVENTS_JSONL="$EVENTS_JSONL" \
  RUN_ID="$RUN_ID" \
  COMPONENT="$COMPONENT" \
    bash scripts/obs/ai_live_activity_demo.sh >"$OUT/activity_demo.stdout" 2>"$OUT/activity_demo.stderr"
  activity_rc=$?
  set -e
  echo "$activity_rc" >"$OUT/activity_rc.txt"
  python3 - "$OUT/activity_demo.stdout" "$OUT/ACTIVITY_DEMO_EVIDENCE_DIR.txt" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
txt = src.read_text(encoding="utf-8", errors="replace")
evidence = ""
for ln in txt.splitlines():
    if ln.strip().startswith("Evidence dir:"):
        evidence = ln.split("Evidence dir:", 1)[1].strip()
        break
dst.write_text((evidence + "\n") if evidence else "UNKNOWN\n", encoding="utf-8")
print(f"wrote: {dst}")
PY
else
  echo "SKIPPED: exporter not reachable at $EXPORTER_URL" >"$OUT/activity_demo.stdout"
  : >"$OUT/activity_demo.stderr"
  echo "SKIPPED" >"$OUT/ACTIVITY_DEMO_EVIDENCE_DIR.txt"
fi

echo "==> Canonical verify (snapshot-only; exit code preserved)"
set +e
bash scripts/obs/ai_live_ops_verify.sh >"$OUT/ai_live_ops_verify.stdout" 2>"$OUT/ai_live_ops_verify.stderr"
verify_rc=$?
set -e
echo "$verify_rc" >"$OUT/verify_rc.txt"
python3 - "$OUT/ai_live_ops_verify.stdout" "$OUT/VERIFY_EVIDENCE_DIR.txt" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
txt = src.read_text(encoding="utf-8", errors="replace")
evidence = ""
for ln in txt.splitlines():
    if ln.strip().startswith("Evidence dir:"):
        evidence = ln.split("Evidence dir:", 1)[1].strip()
        break
dst.write_text((evidence + "\n") if evidence else "UNKNOWN\n", encoding="utf-8")
print(f"wrote: {dst}")
PY

echo "==> DONE"
echo "OUT=$OUT"
exit "$verify_rc"
