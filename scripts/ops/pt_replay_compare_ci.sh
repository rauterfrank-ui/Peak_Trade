#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
pt_replay_compare_ci.sh

Runs deterministic replay-pack compare and writes compare_report.json.

Args:
  --bundle <BUNDLE_DIR>                  (required)
  --generated-at-utc <ISO8601>           (required; use fixed value in CI)
  --check-outputs                        (optional)
  --resolve-datarefs best_effort|strict  (optional)
  --cache-root <PATH>                    (optional; required by compare when resolve-datarefs is set)
  --out <PATH>                           (optional; default: <BUNDLE_DIR>/meta/compare_report.json)

Behavior:
  - Invokes: python3 scripts/execution/pt_replay_pack.py compare ...
  - Always passes an explicit --out path to ensure a report is written
  - Exits with the exact same exit code as compare (0/2/3/4/5/6)

EOF
}

_die_contract() {
  echo "ContractViolationError: $*" 1>&2
  exit 2
}

bundle=""
generated_at_utc=""
check_outputs="false"
resolve_datarefs=""
cache_root=""
out_path=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle)
      bundle="${2:-}"
      shift 2
      ;;
    --generated-at-utc)
      generated_at_utc="${2:-}"
      shift 2
      ;;
    --check-outputs)
      check_outputs="true"
      shift 1
      ;;
    --resolve-datarefs)
      resolve_datarefs="${2:-}"
      shift 2
      ;;
    --cache-root)
      cache_root="${2:-}"
      shift 2
      ;;
    --out)
      out_path="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      _die_contract "unknown arg: $1"
      ;;
  esac
done

if [[ -z "${bundle}" ]]; then
  _die_contract "missing --bundle"
fi
if [[ -z "${generated_at_utc}" ]]; then
  _die_contract "missing --generated-at-utc (required for deterministic artifacts)"
fi
if [[ ! -d "${bundle}" ]]; then
  _die_contract "bundle dir not found: ${bundle}"
fi

if [[ -z "${out_path}" ]]; then
  out_path="${bundle}/meta/compare_report.json"
fi
if [[ "${out_path}" != /* ]]; then
  out_path="${bundle}/${out_path}"
fi
if [[ -d "${out_path}" ]]; then
  out_path="${out_path}/compare_report.json"
fi

mkdir -p "$(dirname "${out_path}")"

export PYTHONHASHSEED=0

cmd=(python3 scripts/execution/pt_replay_pack.py compare
  --bundle "${bundle}"
  --generated-at-utc "${generated_at_utc}"
  --out "${out_path}"
)

if [[ "${check_outputs}" == "true" ]]; then
  cmd+=(--check-outputs)
fi

if [[ -n "${resolve_datarefs}" ]]; then
  case "${resolve_datarefs}" in
    best_effort|strict) ;;
    *) _die_contract "invalid --resolve-datarefs: ${resolve_datarefs} (expected best_effort|strict)" ;;
  esac
  cmd+=(--resolve-datarefs "${resolve_datarefs}")
fi

if [[ -n "${cache_root}" ]]; then
  cmd+=(--cache-root "${cache_root}")
fi

set +e
"${cmd[@]}"
rc=$?
set -e

echo "pt_replay_compare_ci: exit_code=${rc} report_path=${out_path}"
exit "${rc}"
