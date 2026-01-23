#!/usr/bin/env bash
set -euo pipefail

# Robust Grafana API JSON helper.
#
# Supports BOTH:
# A) flags: --base URL --path /api/health [--auth user:pass] [--out PATH] [--retries N] [--timeout S]
# B) positional alias: _grafana_api_json.sh "<base>" "<path>" [--auth user:pass] [--out PATH] [--retries N] [--timeout S]
#
# Output:
# - stdout: JSON body (only) on success
# - stderr: evidence lines (retries, header/body snippets), plus:
#   GRAFANA_API_OK bytes=... content_type=application/json http_code=200

BASE=""
PATH_QS=""
AUTH=""
OUT=""
RETRIES="8"
TIMEOUT_S=""

usage() {
  echo "usage: $0 --base <http://127.0.0.1:3000> --path </api/health> [--auth <admin:admin>] [--out <path>] [--retries N] [--timeout S]" >&2
  echo "   or: $0 <base_url> <path> [--auth <admin:admin>] [--out <path>] [--retries N] [--timeout S]" >&2
}

if [ $# -ge 1 ] && [ "${1#--}" = "$1" ]; then
  if [ $# -lt 2 ]; then
    usage
    exit 2
  fi
  BASE="$1"
  PATH_QS="$2"
  shift 2
fi

while [ $# -gt 0 ]; do
  case "$1" in
    --base) BASE="${2:-}"; shift 2;;
    --path) PATH_QS="${2:-}"; shift 2;;
    --auth) AUTH="${2:-}"; shift 2;;
    --out) OUT="${2:-}"; shift 2;;
    --retries) RETRIES="${2:-}"; shift 2;;
    --timeout) TIMEOUT_S="${2:-}"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "unknown arg: $1" >&2; usage; exit 2;;
  esac
done

if [ -z "${BASE:-}" ] || [ -z "${PATH_QS:-}" ]; then
  usage
  exit 2
fi

tmp_hdr="$(mktemp -t pt_grafana_hdr.XXXXXX)"
tmp_body="$(mktemp -t pt_grafana_body.XXXXXX)"
cleanup() { rm -f "$tmp_hdr" "$tmp_body"; }
trap cleanup EXIT

base_url="${BASE%/}${PATH_QS}"

ok="NO"
i=1
while [ "$i" -le "$RETRIES" ]; do
  : >"$tmp_hdr"; : >"$tmp_body"

  http_code="$(
    curl -sS -L --compressed \
      -D "$tmp_hdr" -o "$tmp_body" -w "%{http_code}" \
      ${AUTH:+-u "$AUTH"} \
      ${TIMEOUT_S:+--connect-timeout "$TIMEOUT_S"} \
      ${TIMEOUT_S:+--max-time "$TIMEOUT_S"} \
      "$base_url" || true
  )"

  ctype="$(grep -i "^content-type:" "$tmp_hdr" | tail -n 1 | tr -d "\r" | awk "{print \$2}" || true)"
  bytes="$(wc -c "$tmp_body" 2>/dev/null | awk "{print \$1}" || echo 0)"

  if [ "$http_code" = "200" ] && echo "${ctype:-}" | grep -qi "^application/json" && [ "${bytes:-0}" -gt 0 ]; then
    ok="YES"
    break
  fi

  echo "GRAFANA_API_RETRY attempt=$i http_code=$http_code content_type=${ctype:-NONE} body_bytes=${bytes:-0} url=$base_url" >&2
  echo "--- hdr (first 20) ---" >&2; sed -n "1,20p" "$tmp_hdr" >&2 || true
  echo "--- body (first 200 bytes) ---" >&2
  python3 - << PY >&2
from pathlib import Path
p=Path("$tmp_body")
b=p.read_bytes() if p.exists() else b""
print(b[:200].decode("utf-8","replace"))
PY
  sleep "$i"
  i=$((i+1))
done

if [ "$ok" != "YES" ]; then
  echo "GRAFANA_API_FAIL retries=$RETRIES url=$base_url" >&2
  exit 1
fi

echo "GRAFANA_API_OK bytes=$bytes content_type=${ctype:-NONE} http_code=$http_code" >&2

if [ -n "${OUT:-}" ]; then
  mkdir -p "$(dirname "$OUT")" 2>/dev/null || true
  cat "$tmp_body" | tee "$OUT" >/dev/null
else
  cat "$tmp_body"
fi
