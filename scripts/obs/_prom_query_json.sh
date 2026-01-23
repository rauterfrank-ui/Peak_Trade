#!/usr/bin/env bash
set -euo pipefail

# Shared helper: robust Prometheus /api/v1/query JSON fetch.
#
# Requirements:
# - token-policy safe diagnostics (headers + first 200 bytes only)
# - retries with backoff
# - validates: http_code=200, content-type=application/json*, body_bytes>0
#
# Usage:
#   bash scripts/obs/_prom_query_json.sh --base http://127.0.0.1:9092 --query 'up' [--out /tmp/body.json] [--retries 5]
#

usage() {
  cat <<'EOF'
Usage:
  scripts/obs/_prom_query_json.sh --base <url> --query <promql> [--out <path>] [--retries N]

Emits:
  - On success: JSON body to stdout (or writes to --out and also prints to stdout).
  - On failure: deterministic diagnostics to stderr and exits non-zero.
EOF
}

BASE=""
QUERY=""
OUT=""
RETRIES="5"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base)
      BASE="${2:-}"; shift 2 ;;
    --query)
      QUERY="${2:-}"; shift 2 ;;
    --out)
      OUT="${2:-}"; shift 2 ;;
    --retries)
      RETRIES="${2:-}"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown arg: $1" >&2
      usage >&2
      exit 2 ;;
  esac
done

if [[ -z "${BASE:-}" || -z "${QUERY:-}" ]]; then
  usage >&2
  exit 2
fi

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/pt-promq.XXXXXX")"
hdr="$tmpdir/headers.txt"
body="$tmpdir/body.bin"
meta="$tmpdir/meta.txt"
trap "rm -rf '$tmpdir' >/dev/null 2>&1 || true" EXIT

sleep_s="${PROM_QUERY_SLEEP_S:-0.2}"
attempt=0

for _ in $(seq 1 "$RETRIES"); do
  attempt=$((attempt + 1))
  rm -f "$hdr" "$body" "$meta" || true

  # Best-effort curl: we want body/headers even on non-200.
  curl -sS -L --compressed \
    -D "$hdr" -o "$body" \
    -w "http_code=%{http_code}\ncontent_type=%{content_type}\n" \
    -G "${BASE%/}/api/v1/query" --data-urlencode "query=$QUERY" \
    >"$meta" 2>/dev/null || true

  http_code="$(awk -F= '$1=="http_code"{print $2}' "$meta" 2>/dev/null | tail -n 1 || true)"
  content_type="$(awk -F= '$1=="content_type"{print $2}' "$meta" 2>/dev/null | tail -n 1 || true)"
  body_bytes="$(wc -c "$body" 2>/dev/null | awk '{print $1}' || echo 0)"

  if [[ "${http_code:-}" == "200" ]] && [[ "${content_type:-}" == application/json* ]] && [[ "${body_bytes:-0}" -gt 0 ]]; then
    # Success: print a single deterministic OK line to stderr, then emit body.
    echo "PROM_QUERY_OK bytes=${body_bytes} content_type=${content_type}" >&2
    if [[ -n "${OUT:-}" ]]; then
      mkdir -p "$(dirname "$OUT")" 2>/dev/null || true
      cp "$body" "$OUT"
    fi
    cat "$body"
    exit 0
  fi

  echo "PROM_QUERY_RETRY attempt=${attempt}/${RETRIES} http_code=${http_code:-<empty>} content_type=${content_type:-<empty>} body_bytes=${body_bytes:-0}" >&2
  sed -n '1,12p' "$hdr" 2>/dev/null >&2 || true
  python3 -c 'import sys; b=sys.stdin.buffer.read()[:200]; sys.stderr.write(b.decode("utf-8","replace")+"\n")' <"$body" 2>/dev/null || true

  sleep "$sleep_s"
  # bounded backoff
  sleep_s="$(python3 -c 'import sys; s=float(sys.argv[1]); print(min(2.0, s*1.6))' "$sleep_s" 2>/dev/null || echo "$sleep_s")"
done

echo "PROM_QUERY_FAIL after=${RETRIES} attempts query=$(python3 -c 'import sys; print(sys.argv[1][:120])' "$QUERY" 2>/dev/null || echo "<redacted>")" >&2
exit 1
