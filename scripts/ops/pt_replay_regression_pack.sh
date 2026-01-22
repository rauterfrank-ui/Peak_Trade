#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
pt_replay_regression_pack.sh

End-to-end offline deterministic replay regression pack:
  1) Build a deterministic replay bundle (or accept an existing bundle)
  2) Run compare (writes compare_report.json)
  3) Run consumer (deterministic stdout summary + minified summary JSON)
  4) Place all outputs under a single OUT_DIR with a stable layout

Args:
  --out-dir <OUT_DIR>                          (required)

Bundle selection:
  --bundle <BUNDLE_DIR>                        (optional; if omitted, --run-id-or-dir is required)
  --bundle-mode symlink|copy                   (optional; default: symlink; applies to --bundle)
  --run-id-or-dir <RUN_ID_OR_DIR>              (optional; used only when building)
  --include-outputs                            (optional; build: include expected outputs in bundle)
  --keep-temp                                  (optional; keep tmp_bundle and link bundle to it)

Determinism:
  --generated-at-utc <ISO8601>                 (optional; if omitted, derived from bundle manifest created_at_utc)

Compare options:
  --check-outputs                              (optional)
  --resolve-datarefs none|best_effort|strict   (optional; default: none)
  --cache-root <PATH>                          (optional; also supports PEAK_TRADE_DATA_CACHE_ROOT)

Consumer options:
  --strict-consumer                            (optional; if compare passes, fail on consumer/report FAIL)

Output layout (stable):
  OUT_DIR/
    bundle/
    reports/
      compare_report.json
      compare_summary.min.json
    logs/
      regression_pack.log

Exit code:
  - Primary outcome is the compare exit code (passed through 1:1).
  - Consumer is informational unless --strict-consumer is set.

EOF
}

_die_contract() {
  echo "ContractViolationError: $*" 1>&2
  exit 2
}

_require_cmd() {
  local cmd="$1"
  command -v "${cmd}" >/dev/null 2>&1 || _die_contract "missing required command: ${cmd}"
}

_repo_root_cd() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    cd "$(git rev-parse --show-toplevel)"
    return 0
  fi
  # Fallback: assume scripts/ops layout.
  cd "${script_dir}/../.."
}

_abspath() {
  python3 - "$1" <<'PY'
import sys
from pathlib import Path
print(str(Path(sys.argv[1]).expanduser().resolve()))
PY
}

_relpath() {
  python3 - "$1" "$2" <<'PY'
import os
import sys
print(os.path.relpath(sys.argv[1], start=sys.argv[2]))
PY
}

_manifest_created_at_utc() {
  python3 - "$1" <<'PY'
import json
import sys
from pathlib import Path

bundle = Path(sys.argv[1])
mp = bundle / "manifest.json"
try:
  obj = json.loads(mp.read_text(encoding="utf-8"))
except Exception:
  print("")
  raise SystemExit(0)

v = obj.get("created_at_utc") or ""
print(str(v))
PY
}

_normalize_iso8601_or_die() {
  python3 - "$1" <<'PY'
import sys
from datetime import datetime

s = str(sys.argv[1] or "").strip()
if not s:
    print("")
    raise SystemExit(0)

# Python 3.9 datetime.fromisoformat does not accept 'Z' suffix; normalize to '+00:00'.
if s.endswith("Z"):
    s = s[:-1] + "+00:00"

try:
    datetime.fromisoformat(s)
except Exception:
    print("")
    raise SystemExit(0)

print(s)
PY
}

bundle=""
bundle_mode="symlink"
run_id_or_dir=""
out_dir=""
generated_at_utc=""
check_outputs="false"
resolve_datarefs="none"
cache_root=""
strict_consumer="false"
keep_temp="false"
include_outputs="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle)
      bundle="${2:-}"
      shift 2
      ;;
    --bundle-mode)
      bundle_mode="${2:-}"
      shift 2
      ;;
    --run-id-or-dir)
      run_id_or_dir="${2:-}"
      shift 2
      ;;
    --out-dir)
      out_dir="${2:-}"
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
    --strict-consumer)
      strict_consumer="true"
      shift 1
      ;;
    --keep-temp)
      keep_temp="true"
      shift 1
      ;;
    --include-outputs)
      include_outputs="true"
      shift 1
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

if [[ -z "${out_dir}" ]]; then
  _die_contract "missing --out-dir"
fi

case "${bundle_mode}" in
  symlink|copy) ;;
  *)
    _die_contract "invalid --bundle-mode: ${bundle_mode} (expected symlink|copy)"
    ;;
esac

case "${resolve_datarefs}" in
  none|best_effort|strict) ;;
  *)
    _die_contract "invalid --resolve-datarefs: ${resolve_datarefs} (expected none|best_effort|strict)"
    ;;
esac

_require_cmd git
_require_cmd python3

_repo_root_cd

out_dir="$(_abspath "${out_dir}")"
mkdir -p "${out_dir}"

# Guard against obvious foot-guns.
if [[ "${out_dir}" == "/" ]]; then
  _die_contract "--out-dir must not be /"
fi

mkdir -p "${out_dir}/reports" "${out_dir}/logs"

export LC_ALL=C
export LANG=C
export TZ=UTC
export PYTHONHASHSEED=0

bundle_mode="provided"
tmp_root="${out_dir}/tmp_bundle"
bundle_dir=""

if [[ -n "${bundle}" ]]; then
  bundle="$(_abspath "${bundle}")"
  if [[ ! -d "${bundle}" ]]; then
    _die_contract "bundle dir not found: ${bundle}"
  fi
  bundle_mode="provided"

  # Provide a stable local path under OUT_DIR.
  rm -rf "${out_dir}/bundle"
  if [[ "${bundle_mode}" == "copy" ]]; then
    python3 - "${bundle}" "${out_dir}/bundle" <<'PY'
import shutil
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
if dst.exists():
    shutil.rmtree(dst)
shutil.copytree(src, dst, symlinks=True)
PY
  else
    rel="$(_relpath "${bundle}" "${out_dir}")"
    ln -s "${rel}" "${out_dir}/bundle"
  fi
  bundle_dir="${out_dir}/bundle"
else
  if [[ -z "${run_id_or_dir}" ]]; then
    _die_contract "missing --bundle (or provide --run-id-or-dir to build)"
  fi
  bundle_mode="built"
  if [[ -z "${generated_at_utc}" ]]; then
    _die_contract "missing --generated-at-utc (required for deterministic build)"
  fi
  generated_at_utc="$(_normalize_iso8601_or_die "${generated_at_utc}")"
  if [[ -z "${generated_at_utc}" ]]; then
    _die_contract "invalid --generated-at-utc (expected ISO8601 parseable by python datetime.fromisoformat)"
  fi
  rm -rf "${tmp_root}"
  mkdir -p "${tmp_root}"

  build_cmd=(python3 scripts/execution/pt_replay_pack.py build
    --run-id-or-dir "${run_id_or_dir}"
    --out "${tmp_root}"
    --created-at-utc "${generated_at_utc}"
  )

  if [[ "${include_outputs}" == "true" || "${check_outputs}" == "true" ]]; then
    build_cmd+=(--include-outputs)
  fi

  "${build_cmd[@]}"

  if [[ ! -d "${tmp_root}/replay_pack" ]]; then
    _die_contract "build did not produce expected bundle dir: ${tmp_root}/replay_pack"
  fi

  rm -rf "${out_dir}/bundle"
  if [[ "${keep_temp}" == "true" ]]; then
    ln -s "tmp_bundle/replay_pack" "${out_dir}/bundle"
    bundle_dir="${out_dir}/bundle"
  else
    mv "${tmp_root}/replay_pack" "${out_dir}/bundle"
    bundle_dir="${out_dir}/bundle"
    # Best-effort cleanup (empty dir).
    rmdir "${tmp_root}" >/dev/null 2>&1 || true
  fi
fi

if [[ -z "${generated_at_utc}" ]]; then
  generated_at_utc="$(_manifest_created_at_utc "${bundle_dir}")"
fi
if [[ -z "${generated_at_utc}" ]]; then
  _die_contract "missing --generated-at-utc and manifest created_at_utc not available"
fi
generated_at_utc="$(_normalize_iso8601_or_die "${generated_at_utc}")"
if [[ -z "${generated_at_utc}" ]]; then
  _die_contract "invalid generated_at_utc (expected ISO8601 parseable by python datetime.fromisoformat)"
fi

log_path="${out_dir}/logs/regression_pack.log"
report_path="${out_dir}/reports/compare_report.json"
summary_path="${out_dir}/reports/compare_summary.min.json"

{
  printf '%s\n' "schema=PT_REPLAY_REGRESSION_PACK_V1"
  printf '%s\n' "bundle_mode=${bundle_mode}"
  printf '%s\n' "bundle_dir=bundle"
  printf '%s\n' "generated_at_utc=${generated_at_utc}"
  printf '%s\n' "check_outputs=${check_outputs}"
  printf '%s\n' "resolve_datarefs=${resolve_datarefs}"
  printf '%s\n' "strict_consumer=${strict_consumer}"
  printf '%s\n' "report=reports/compare_report.json"
  printf '%s\n' "summary=reports/compare_summary.min.json"
} > "${log_path}"

set +e
python3 scripts/execution/pt_replay_pack.py validate --bundle "${bundle_dir}"
validate_rc=$?
set -e

{
  printf '%s\n' "validate_exit=${validate_rc}"
} >> "${log_path}"

compare_cmd=(python3 scripts/execution/pt_replay_pack.py compare
  --bundle "${bundle_dir}"
  --generated-at-utc "${generated_at_utc}"
  --out "${report_path}"
)

if [[ "${check_outputs}" == "true" ]]; then
  compare_cmd+=(--check-outputs)
fi
if [[ "${resolve_datarefs}" != "none" ]]; then
  compare_cmd+=(--resolve-datarefs "${resolve_datarefs}")
fi
if [[ -n "${cache_root}" ]]; then
  compare_cmd+=(--cache-root "${cache_root}")
fi

set +e
"${compare_cmd[@]}"
compare_rc=$?
set -e

{
  printf '%s\n' "compare_exit=${compare_rc}"
} >> "${log_path}"

consume_cmd=(python3 scripts/ops/pt_compare_consume.py
  --report "${report_path}"
  --out "${summary_path}"
  --mode ci
)
if [[ "${strict_consumer}" == "true" ]]; then
  consume_cmd+=(--strict)
fi

set +e
"${consume_cmd[@]}"
consume_rc=$?
set -e

{
  printf '%s\n' "consumer_exit=${consume_rc}"
} >> "${log_path}"

# Exit behavior:
# - Preserve compare exit code 1:1 as the primary outcome.
# - Consumer is informational unless strict-consumer is enabled.
if [[ "${compare_rc}" -ne 0 ]]; then
  exit "${compare_rc}"
fi
if [[ "${strict_consumer}" == "true" && "${consume_rc}" -ne 0 ]]; then
  exit "${consume_rc}"
fi
exit 0
