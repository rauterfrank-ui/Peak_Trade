#!/usr/bin/env bash
set -euo pipefail

# Grafana Dashpack Verify v2
# - Hermetic (JSON-only) checks always run.
# - Grafana API checks run only if Grafana is reachable.
#
# Output:
# - Prints PASS|... lines on success
# - Writes evidence artifacts to docs/ops/evidence/assets/EV_GRAFANA_DASHPACK_VERIFY_V2_<timestamp> (or VERIFY_OUT_DIR)

cd "$(git rev-parse --show-toplevel)"

GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"
# Auth options (choose ONE):
# - Preferred: Bearer token via GRAFANA_TOKEN
# - Legacy:    Basic auth via GRAFANA_AUTH="user:pass"
# If neither is set, auth-required API checks are skipped (hermetic checks still PASS).
GRAFANA_TOKEN="${GRAFANA_TOKEN:-}"
GRAFANA_AUTH="${GRAFANA_AUTH:-}"

HERMETIC="0"
if [ "${1:-}" = "--hermetic" ] || [ "${1:-}" = "--no-api" ]; then
  HERMETIC="1"
  shift || true
fi
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  echo "usage: $0 [--hermetic|--no-api]" >&2
  echo "" >&2
  echo "  --hermetic: run JSON-only checks; skip Grafana API checks even if reachable" >&2
  echo "  --no-api:   alias for --hermetic" >&2
  echo "" >&2
  echo "env:" >&2
  echo "  GRAFANA_URL=http://127.0.0.1:3000" >&2
  echo "  GRAFANA_TOKEN=<bearer_token>      (preferred; enables auth-required API checks)" >&2
  echo "  GRAFANA_AUTH=user:pass            (legacy; enables auth-required API checks)" >&2
  exit 0
fi

VERIFY_OUT_DIR="${VERIFY_OUT_DIR:-}"
RUN_TS_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
if [ -z "$VERIFY_OUT_DIR" ]; then
  VERIFY_OUT_DIR="docs/ops/evidence/assets/EV_GRAFANA_DASHPACK_VERIFY_V2_${RUN_TS_UTC}"
fi
mkdir -p "$VERIFY_OUT_DIR"
export VERIFY_OUT_DIR

pass() { echo "PASS|$1|$2"; }
fail() {
  echo "FAIL|$1|$2" >&2
  echo "EVIDENCE_DIR|$VERIFY_OUT_DIR" >&2
  echo "NEXT|$3" >&2
  echo "RESULT=FAIL" >&2
  exit 1
}

require_tool() {
  command -v "$1" >/dev/null 2>&1 || fail "preflight.tool" "Missing required tool: $1" "Install $1 and re-run"
}

require_tool python3
if [ "$HERMETIC" != "1" ]; then
  require_tool curl
  GRAFANA_HELPER="./scripts/obs/_grafana_api_json.sh"
  if [ ! -f "$GRAFANA_HELPER" ]; then
    fail "preflight.helper" "Missing helper: $GRAFANA_HELPER" "Ensure scripts are present"
  fi
fi

echo "== Grafana Dashpack Verify v2 =="
echo "EVIDENCE_DIR|$VERIFY_OUT_DIR"
echo "EVIDENCE|grafana=$GRAFANA_URL"

echo "==> A) Hermetic dashpack checks (repo JSON only)"
dashpack_report="$VERIFY_OUT_DIR/dashpack_integrity_report.txt"
python3 - <<'PY'
import json
import os
import re
from pathlib import Path

out_dir = Path(os.environ["VERIFY_OUT_DIR"])
dash_dir = Path("docs") / "webui" / "observability" / "grafana" / "dashboards"
files = sorted(dash_dir.glob("*/*.json"))
if not files:
    raise SystemExit(f"no dashboards found under {dash_dir}")

uid_to_path: dict[str, Path] = {}
docs = []
for p in files:
    doc = json.loads(p.read_text(encoding="utf-8"))
    uid = doc.get("uid")
    title = doc.get("title")
    if not isinstance(uid, str) or not uid:
        raise SystemExit(f"missing uid in {p}")
    if uid in uid_to_path:
        raise SystemExit(f"duplicate uid={uid} in {uid_to_path[uid]} and {p}")
    if not isinstance(title, str) or not title:
        raise SystemExit(f"missing title in {p}")
    uid_to_path[uid] = p
    docs.append((p, doc))

expected_defaults = {
    "DS_LOCAL": "peaktrade-prometheus-local",
    "DS_MAIN": "peaktrade-prometheus-main",
    "DS_SHADOW": "peaktrade-prometheus-shadow",
}
need_vars = set(expected_defaults.keys())

uid_re = re.compile(r"^/d/([^/?]+)(?:/[^?]+)?(?:\\?.*)?$")

problems: list[str] = []

def walk_urls(x):
    if isinstance(x, dict):
        for k, v in x.items():
            if k == "url" and isinstance(v, str):
                yield v
            else:
                yield from walk_urls(v)
    elif isinstance(x, list):
        for it in x:
            yield from walk_urls(it)

for p, doc in docs:
    # DS_* invariants
    templ = (doc.get("templating") or {}).get("list") or []
    ds_items = [t for t in templ if isinstance(t, dict) and t.get("type") == "datasource"]
    by_name = {t.get("name"): t for t in ds_items if isinstance(t.get("name"), str)}
    missing = sorted(need_vars - set(by_name.keys()))
    if missing:
        problems.append(f"{p}: missing ds vars {missing}")
    else:
        for name, want_uid in expected_defaults.items():
            t = by_name[name]
            if t.get("hide") != 2:
                problems.append(f"{p}: {name}.hide={t.get('hide')!r} expected=2")
            cur = t.get("current") or {}
            cur_val = cur.get("value") if isinstance(cur, dict) else None
            if cur_val != want_uid:
                problems.append(f"{p}: {name}.current.value={cur_val!r} expected={want_uid!r}")

    # Link reachability
    for url in walk_urls(doc):
        m = uid_re.match(url)
        if not m:
            continue
        target = m.group(1)
        if target not in uid_to_path:
            problems.append(f"{p}: url={url!r} -> missing uid={target}")

report = out_dir / "dashpack_integrity_report.txt"
if problems:
    report.write_text("\n".join(problems) + "\n", encoding="utf-8")
    raise SystemExit("dashpack integrity FAIL (see report)")
report.write_text("ok\n", encoding="utf-8")
print("ok")
PY
pass "dashpack.integrity.hermetic" "$dashpack_report"

echo "==> B) Optional Grafana API checks (only if reachable)"
if [ "$HERMETIC" = "1" ]; then
  pass "grafana.api" "SKIP (--hermetic)"
  echo "RESULT=PASS"
  exit 0
fi

grafana_api_auth_mode() {
  if [ -n "${GRAFANA_TOKEN:-}" ]; then
    echo "bearer"
  elif [ -n "${GRAFANA_AUTH:-}" ]; then
    echo "basic"
  else
    echo "none"
  fi
}

grafana_api_json_authed() {
  # Minimal JSON fetcher for auth-required endpoints.
  # Args: <path> <out> <retries> <timeout_s>
  local path="$1"
  local out="$2"
  local retries="${3:-2}"
  local timeout_s="${4:-2}"
  local url="${GRAFANA_URL%/}${path}"

  local tmp_hdr tmp_body
  tmp_hdr="$(mktemp -t pt_grafana_hdr.XXXXXX)"
  tmp_body="$(mktemp -t pt_grafana_body.XXXXXX)"
  trap 'rm -f "$tmp_hdr" "$tmp_body"' RETURN

  local i=1
  local http_code ctype bytes
  while [ "$i" -le "$retries" ]; do
    : >"$tmp_hdr"; : >"$tmp_body"

    http_code=""
    case "$(grafana_api_auth_mode)" in
      bearer)
        http_code="$(
          curl -sS -L --compressed \
            -D "$tmp_hdr" -o "$tmp_body" -w "%{http_code}" \
            -H "Authorization: Bearer ${GRAFANA_TOKEN}" \
            --connect-timeout "$timeout_s" --max-time "$timeout_s" \
            "$url" || true
        )"
        ;;
      basic)
        http_code="$(
          curl -sS -L --compressed \
            -D "$tmp_hdr" -o "$tmp_body" -w "%{http_code}" \
            -u "$GRAFANA_AUTH" \
            --connect-timeout "$timeout_s" --max-time "$timeout_s" \
            "$url" || true
        )"
        ;;
      *)
        http_code="0"
        ;;
    esac

    ctype="$(python3 - <<PY
from pathlib import Path
p=Path("$tmp_hdr")
txt=p.read_text(errors="ignore") if p.exists() else ""
ctype=""
for line in txt.splitlines():
  if line.lower().startswith("content-type:"):
    parts=line.split(":",1)[1].strip().split()
    ctype=parts[0] if parts else ""
print(ctype)
PY
)"
    bytes="$(python3 - <<PY
from pathlib import Path
p=Path("$tmp_body")
print(p.stat().st_size if p.exists() else 0)
PY
)"

    if [ "$http_code" = "200" ] && echo "${ctype:-}" | grep -qi "^application/json" && [ "${bytes:-0}" -gt 0 ]; then
      mkdir -p "$(dirname "$out")" 2>/dev/null || true
      cat "$tmp_body" | tee "$out" >/dev/null
      echo "GRAFANA_API_OK bytes=$bytes content_type=${ctype:-NONE} http_code=$http_code" >&2
      return 0
    fi

    echo "GRAFANA_API_RETRY attempt=$i http_code=$http_code content_type=${ctype:-NONE} body_bytes=${bytes:-0} url=$url" >&2
    python3 - <<PY >&2
from pathlib import Path
h=Path("$tmp_hdr").read_text(errors="ignore").splitlines()
b=Path("$tmp_body").read_bytes() if Path("$tmp_body").exists() else b""
print("--- hdr (first 20) ---")
print("\\n".join(h[:20]))
print("--- body (first 200 bytes) ---")
print(b[:200].decode("utf-8","replace"))
PY
    sleep "$i"
    i=$((i+1))
  done

  echo "GRAFANA_API_FAIL retries=$retries url=$url" >&2
  return 1
}

health_out="$VERIFY_OUT_DIR/grafana_api_health.json"
if bash "$GRAFANA_HELPER" --base "$GRAFANA_URL" --path "/api/health" --out "$health_out" --retries 1 --timeout 1 >/dev/null; then
  pass "grafana.health" "$health_out"

  case "$(grafana_api_auth_mode)" in
    none)
      pass "grafana.auth" "SKIP (set GRAFANA_TOKEN or GRAFANA_AUTH to enable auth-required API checks)"
      pass "grafana.dashboards.uid_fetch" "SKIP (no auth provided)"
      echo "RESULT=PASS"
      exit 0
      ;;
    bearer|basic)
      user_out="$VERIFY_OUT_DIR/grafana_api_user.json"
      if ! grafana_api_json_authed "/api/user" "$user_out" 2 2 >/dev/null; then
        fail "grafana.auth" "Grafana reachable but auth failed (set GRAFANA_TOKEN or GRAFANA_AUTH=user:pass)" "Set correct Grafana credentials: export GRAFANA_TOKEN=... (preferred) or export GRAFANA_AUTH=user:pass"
      fi
      pass "grafana.auth" "$user_out"
      ;;
  esac

  # Fetch each dashboard by UID and validate JSON
  uids_txt="$VERIFY_OUT_DIR/dashpack_uids.txt"
  python3 - <<'PY'
import json
import os
from pathlib import Path

out_dir = Path(os.environ["VERIFY_OUT_DIR"])
dash_dir = Path("docs") / "webui" / "observability" / "grafana" / "dashboards"
uids = []
for p in sorted(dash_dir.glob("*/*.json")):
    doc = json.loads(p.read_text(encoding="utf-8"))
    uid = doc.get("uid")
    if not isinstance(uid, str) or not uid:
        raise SystemExit(f"missing uid in {p}")
    uids.append(uid)
(out_dir / "dashpack_uids.txt").write_text("\n".join(uids) + "\n", encoding="utf-8")
print(f"uids={len(uids)}")
PY

  api_dir="$VERIFY_OUT_DIR/grafana_dashboards_by_uid"
  mkdir -p "$api_dir"
  while IFS= read -r uid; do
    [ -n "$uid" ] || continue
    out="$api_dir/${uid}.json"
    if ! grafana_api_json_authed "/api/dashboards/uid/${uid}" "$out" 3 5 >/dev/null; then
      fail "grafana.dashboard.get" "Failed to fetch dashboard uid=${uid}" "Restart Grafana to reload provisioned dashboards (grafana_local_down/up) and re-run"
    fi
    if ! python3 - <<PY
import json
from pathlib import Path
p=Path("$out")
doc=json.loads(p.read_text(encoding="utf-8"))
d=doc.get("dashboard") or {}
uid = d.get("uid")
if uid != "$uid":
  raise SystemExit(f"uid mismatch: expected={\"$uid\"} got={uid!r}")
PY
    then
      fail "grafana.dashboard.json" "Invalid dashboard JSON or uid mismatch for uid=$uid" "Inspect $out"
    fi
  done <"$uids_txt"
  pass "grafana.dashboards.uid_fetch" "$api_dir"
else
  pass "grafana.api" "SKIP (Grafana not reachable at $GRAFANA_URL)"
fi

echo "RESULT=PASS"
