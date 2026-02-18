#!/usr/bin/env bash
set -euo pipefail

# Operator UX:
#   scripts/ops/verify_from_registry.sh <pointer> [--download] [--pack]
#
# Examples:
#   scripts/ops/verify_from_registry.sh docs/ops/registry/LATEST_PHASE_M_SMOKE.pointer --download
#   scripts/ops/verify_from_registry.sh docs/ops/registry/LATEST_PHASE_M_SMOKE.pointer --download --pack
#
# Safety rails:
# - refuses if pointer is outside docs/ops/registry unless PT_ALLOW_ARBITRARY_POINTER=YES
# - refuses to overwrite packs unless PT_ALLOW_OVERWRITE_PACK=YES

PTR="${1:-}"
shift || true

if [[ -z "${PTR}" ]]; then
  echo "ERR: pointer required" >&2
  exit 2
fi

if [[ "${PTR}" != docs/ops/registry/* && "${PT_ALLOW_ARBITRARY_POINTER:-NO}" != "YES" ]]; then
  echo "ERR: pointer must be under docs/ops/registry/ (set PT_ALLOW_ARBITRARY_POINTER=YES to override)" >&2
  exit 2
fi

DOWNLOAD="NO"
PACK="NO"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --download) DOWNLOAD="YES" ;;
    --pack) PACK="YES" ;;
    *) echo "ERR: unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

RID="$(rg -m1 '^run_id=' "${PTR}" | cut -d= -f2- || true)"
if [[ -z "${RID}" ]]; then
  echo "ERR: run_id missing in pointer: ${PTR}" >&2
  exit 2
fi

OUT_BASE="out/ops/gh_runs"
PACK_OUT=""
if [[ "${PACK}" == "YES" ]]; then
  PACK_OUT="out/ops/evidence_packs/pack_verify_${RID}"
  if [[ -e "${PACK_OUT}" && "${PT_ALLOW_OVERWRITE_PACK:-NO}" != "YES" ]]; then
    echo "ERR: pack exists: ${PACK_OUT} (set PT_ALLOW_OVERWRITE_PACK=YES to overwrite)" >&2
    exit 2
  fi
fi

ARGS=("${PTR}" --out-base "${OUT_BASE}")
if [[ "${DOWNLOAD}" == "YES" ]]; then
  ARGS+=(--download)
fi
if [[ -n "${PACK_OUT}" ]]; then
  ARGS+=(--pack-out "${PACK_OUT}")
fi

python3 scripts/ops/verify_registry_pointer_artifacts.py "${ARGS[@]}"

if [[ -n "${PACK_OUT}" ]]; then
  echo "OK: pack created: ${PACK_OUT}"
  echo "OK: sha256: ${PACK_OUT}/SHA256SUMS.stable.txt"
fi
