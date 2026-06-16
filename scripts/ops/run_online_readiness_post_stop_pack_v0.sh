#!/usr/bin/env bash
# Operator-invoked post-stop pack wrapper for Online Readiness supervisor/daemon evidence.
# Delegates to pack_online_readiness_supervisor_evidence_v0.py; optional P79 ARCHIVE_ROOT verify.
# Does not start/stop supervisor, daemon, or invoke launchctl.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

OUT_DIR=""
ARCHIVE_ROOT=""
RESOLVE=""
P79_ARCHIVE_VERIFY=0
PRIMARY_EVIDENCE_ENFORCE=0
REQUIRE_OPTIONAL=0
OPTIONAL_ARTIFACTS=()

usage() {
  cat <<'EOF'
Usage: run_online_readiness_post_stop_pack_v0.sh --archive-root PATH (--out-dir PATH | --resolve MODE) [options]

Operator-invoked after STOP. Non-authorizing; does not start/stop supervisor or daemon.

Options:
  --out-dir PATH                 Existing supervisor/daemon OUT_DIR to pack
  --resolve MODE                 Resolve OUT_DIR: latest-supervisor | latest-daemon-tick
  --archive-root PATH            Durable destination root for packed evidence (required)
  --optional-artifact PATH       Optional pid/log/lock path (repeatable)
  --primary-evidence-enforce     Pass through to pack script (MANIFEST.sha256 enforce)
  --require-optional-artifacts Fail closed when optional artifacts are missing
  --p79-archive-verify           Run P79 ARCHIVE_ROOT verify after pack (explicit opt-in)
  -h, --help                     Show this help
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --out-dir)
      OUT_DIR="$2"
      shift 2
      ;;
    --archive-root)
      ARCHIVE_ROOT="$2"
      shift 2
      ;;
    --resolve)
      RESOLVE="$2"
      shift 2
      ;;
    --optional-artifact)
      OPTIONAL_ARTIFACTS+=("$2")
      shift 2
      ;;
    --primary-evidence-enforce)
      PRIMARY_EVIDENCE_ENFORCE=1
      shift
      ;;
    --require-optional-artifacts)
      REQUIRE_OPTIONAL=1
      shift
      ;;
    --p79-archive-verify)
      P79_ARCHIVE_VERIFY=1
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "ERR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

{
  echo "ONLINE_DAEMON_POST_STOP_PACK_WRAPPER_V0=true"
  echo "OPERATOR_INVOKED_ONLY=true"
  echo "DAEMON_NOT_STARTED=true"
  echo "DAEMON_NOT_STOPPED=true"
  echo "SUPERVISOR_NOT_STARTED=true"
  echo "SUPERVISOR_NOT_STOPPED=true"
  echo "LAUNCHCTL_CALLED=false"
  echo "PACK_SCRIPT_DELEGATED=true"
  echo "P79_ARCHIVE_VERIFY_EXPLICIT_ONLY=true"
  echo "EVIDENCE_NON_AUTHORIZING=true"
}

if [ -z "${ARCHIVE_ROOT}" ]; then
  echo "ERR: --archive-root is required" >&2
  exit 2
fi

if [ -n "${RESOLVE}" ] && [ -n "${OUT_DIR}" ]; then
  echo "ERR: --out-dir and --resolve are mutually exclusive" >&2
  exit 2
fi

if [ -n "${RESOLVE}" ]; then
  case "${RESOLVE}" in
    latest-supervisor)
      sup_base="out/ops/online_readiness_supervisor"
      latest="$(ls -1 "${sup_base}" 2>/dev/null | grep '^run_' | LC_ALL=C sort | tail -n 1 || true)"
      if [ -n "${latest}" ]; then
        OUT_DIR="${sup_base}/${latest}"
      else
        OUT_DIR="out/ops/p78_supervisor"
      fi
      ;;
    latest-daemon-tick)
      daemon_base="out/ops/online_readiness_daemon"
      latest="$(ls -1 "${daemon_base}" 2>/dev/null | LC_ALL=C sort | tail -n 1 || true)"
      if [ -z "${latest}" ]; then
        echo "ERR: no daemon tick directories under ${daemon_base}" >&2
        exit 3
      fi
      OUT_DIR="${daemon_base}/${latest}"
      ;;
    *)
      echo "ERR: unknown --resolve mode: ${RESOLVE} (latest-supervisor|latest-daemon-tick)" >&2
      exit 2
      ;;
  esac
fi

if [ -z "${OUT_DIR}" ]; then
  echo "ERR: --out-dir or --resolve is required" >&2
  exit 2
fi

if [ ! -d "${OUT_DIR}" ]; then
  echo "ERR: out_dir_missing: ${OUT_DIR}" >&2
  exit 3
fi

pack_cmd=(python3 scripts/ops/pack_online_readiness_supervisor_evidence_v0.py
  --out-dir "${OUT_DIR}"
  --archive-root "${ARCHIVE_ROOT}")
for artifact in "${OPTIONAL_ARTIFACTS[@]+"${OPTIONAL_ARTIFACTS[@]}"}"; do
  pack_cmd+=(--optional-artifact "${artifact}")
done
if [ "${PRIMARY_EVIDENCE_ENFORCE}" -eq 1 ]; then
  pack_cmd+=(--primary-evidence-enforce)
fi
if [ "${REQUIRE_OPTIONAL}" -eq 1 ]; then
  pack_cmd+=(--require-optional-artifacts)
fi

echo "WRAPPER_OUT_DIR=${OUT_DIR}"
echo "WRAPPER_ARCHIVE_ROOT=${ARCHIVE_ROOT}"

"${pack_cmd[@]}"
pack_rc=$?

p79_rc=0
if [ "${P79_ARCHIVE_VERIFY}" -eq 1 ]; then
  ARCHIVE_ROOT="${ARCHIVE_ROOT}" bash scripts/ops/p79_supervisor_health_gate_v1.sh
  p79_rc=$?
else
  echo "P79_ARCHIVE_VERIFY_SKIPPED=true"
fi

wrapper_rc=0
if [ "${pack_rc}" -ne 0 ] || [ "${p79_rc}" -ne 0 ]; then
  wrapper_rc=1
fi
echo "POST_STOP_PACK_WRAPPER_RC=${wrapper_rc}"
exit "${wrapper_rc}"
