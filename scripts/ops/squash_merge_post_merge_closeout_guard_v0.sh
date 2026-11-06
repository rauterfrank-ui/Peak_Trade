#!/usr/bin/env bash
# Canonical squash-merge post-merge closeout guard (v0).
# Fail-closed: pytest/ruff/manifest nonzero rc must propagate even when output is teed.
set -euo pipefail

PACKAGE_MARKER="SQUASH_MERGE_POST_MERGE_CLOSEOUT_GUARD_V0=true"
DEFAULT_PYTEST_K='evidence or manifest or docs or governance'
NON_CLASS_D_ORIGIN_MAIN_POLICY_TEST_REL="tests/research/test_non_class_d_offline_eval_accepted_origin_main_policy_v0.py"
REMOTE="${REMOTE:-origin}"
MAIN_BRANCH="${MAIN_BRANCH:-main}"

usage() {
  cat <<'USAGE'
squash_merge_post_merge_closeout_guard_v0.sh - Post-merge closeout validation (fail-closed)

Usage:
  scripts/ops/squash_merge_post_merge_closeout_guard_v0.sh post-merge-validate [options]

Commands:
  post-merge-validate   Run post-merge HEAD sync, targeted pytest, ruff, optional manifest verify

Options:
  --evidence-dir <dir>     Required. Durable evidence output directory
  --pytest-k <expr>        Pytest -k expression (default: evidence or manifest or docs or governance)
  --pytest-target <path>   Run pytest against an explicit test file path
  --non-class-d-origin-main-policy-test
                           Run canonical Non-Class-D origin-main policy contract test
  --skip-ruff              Skip ruff format/check gates
  --skip-pytest            Skip targeted pytest gate
  --verify-source-manifest Verify SOURCE_MANIFEST path when set in env
  -h, --help               Show help

Env:
  REMOTE=origin
  MAIN_BRANCH=main
  SOURCE_EVIDENCE_DIR      Optional referenced source evidence directory
  PYTHONPATH               Optional; defaults to src when present

Exit codes:
  0   all requested gates passed
  4   HEAD != origin/main
  6   pytest failed (nonzero rc or collection error)
  7   ruff failed
  11  source MANIFEST.sha256 missing
  12  source manifest verify failed
  13  closeout manifest verify failed
  2   usage error
USAGE
}

die_usage() {
  echo "ERROR: $*" >&2
  usage >&2
  exit 2
}

# Run a command with stdout/stderr teed to a log file; return the command's exit code.
# Uses PIPESTATUS so tee success cannot mask pytest/ruff failure.
run_teed() {
  local log_file="$1"
  shift
  mkdir -p "$(dirname "$log_file")"
  set -o pipefail
  "$@" 2>&1 | tee "$log_file"
  return "${PIPESTATUS[0]}"
}

verify_head_equals_origin_main() {
  local remote="$1"
  local branch="$2"
  git fetch "$remote" --prune
  local head origin_main
  head="$(git rev-parse HEAD)"
  origin_main="$(git rev-parse "${remote}/${branch}")"
  printf '%s\n' "$head" >"${EVIDENCE_DIR}/POST_MERGE_HEAD.txt"
  printf '%s\n' "$origin_main" >"${EVIDENCE_DIR}/POST_MERGE_ORIGIN_MAIN.txt"
  if [[ "$head" != "$origin_main" ]]; then
    echo "BLOCKED_POST_MERGE_HEAD_NOT_ORIGIN_MAIN head=${head} origin=${origin_main}" \
      | tee "${EVIDENCE_DIR}/post_merge_main_sync_fail.txt"
    return 4
  fi
  echo "HEAD_EQUALS_ORIGIN_MAIN=true" | tee "${EVIDENCE_DIR}/head_equals_origin_main.txt"
  return 0
}

verify_source_manifest_if_referenced() {
  local source_dir="${SOURCE_EVIDENCE_DIR:-}"
  if [[ -z "$source_dir" ]]; then
    echo "SOURCE_EVIDENCE_NOT_REFERENCED=true" >"${EVIDENCE_DIR}/source_manifest_verify_post_merge.txt"
    return 0
  fi
  if [[ ! -d "$source_dir" ]]; then
    echo "BLOCKED_SOURCE_EVIDENCE_DIR_MISSING=${source_dir}" \
      | tee "${EVIDENCE_DIR}/source_manifest_verify_post_merge.txt"
    return 11
  fi
  if [[ ! -f "${source_dir}/MANIFEST.sha256" ]]; then
    echo "BLOCKED_SOURCE_MANIFEST_SHA256_MISSING=${source_dir}" \
      | tee "${EVIDENCE_DIR}/source_manifest_verify_post_merge.txt"
    return 11
  fi
  (
    cd "$source_dir" && shasum -a 256 -c MANIFEST.sha256
  ) >"${EVIDENCE_DIR}/source_manifest_verify_post_merge.txt" 2>&1
  local rc=$?
  if [[ "$rc" -ne 0 ]]; then
    echo "BLOCKED_SOURCE_MANIFEST_VERIFY_RC=${rc}" | tee -a "${EVIDENCE_DIR}/source_manifest_verify_post_merge.txt"
    return 12
  fi
  echo "SOURCE_MANIFEST_VERIFY_RC=0" | tee -a "${EVIDENCE_DIR}/source_manifest_verify_post_merge.txt"
  return 0
}

resolve_non_class_d_origin_main_policy_test_path() {
  if [[ -f "$NON_CLASS_D_ORIGIN_MAIN_POLICY_TEST_REL" ]]; then
    echo "$NON_CLASS_D_ORIGIN_MAIN_POLICY_TEST_REL"
    return 0
  fi
  echo "BLOCKED_NON_CLASS_D_ORIGIN_MAIN_POLICY_TEST_MISSING=${NON_CLASS_D_ORIGIN_MAIN_POLICY_TEST_REL}" >&2
  return 1
}

run_targeted_pytest() {
  local pytest_k="$1"
  local pytest_target="${2:-}"
  local log_file="${EVIDENCE_DIR}/pytest_targeted_post_merge.log"
  local python_cmd
  if [[ -n "$pytest_target" ]]; then
    python_cmd=(python3 -m pytest "$pytest_target" -q)
    printf '%s\n' "$pytest_target" >"${EVIDENCE_DIR}/pytest_target_path.txt"
  else
    python_cmd=(python3 -m pytest tests -q -k "$pytest_k")
    printf '%s\n' "$pytest_k" >"${EVIDENCE_DIR}/pytest_target_k.txt"
  fi
  if [[ -d src ]]; then
    PYTHONPATH="${PYTHONPATH:-src}" run_teed "$log_file" env PYTHONPATH="${PYTHONPATH:-src}" "${python_cmd[@]}"
  else
    run_teed "$log_file" "${python_cmd[@]}"
  fi
}

run_ruff_gates() {
  local fmt_rc=0
  local chk_rc=0
  if ! run_teed "${EVIDENCE_DIR}/ruff_format_check_post_merge.log" ruff format --check .; then
    fmt_rc=$?
  fi
  if ! run_teed "${EVIDENCE_DIR}/ruff_check_post_merge.log" ruff check .; then
    chk_rc=$?
  fi
  printf '%s\n' "$fmt_rc" >"${EVIDENCE_DIR}/ruff_format_check_post_merge.rc"
  printf '%s\n' "$chk_rc" >"${EVIDENCE_DIR}/ruff_check_post_merge.rc"
  if [[ "$fmt_rc" -ne 0 || "$chk_rc" -ne 0 ]]; then
    return 7
  fi
  return 0
}

verify_closeout_manifest() {
  local manifest_dir="$1"
  if [[ ! -d "$manifest_dir" ]]; then
    echo "BLOCKED_CLOSEOUT_MANIFEST_DIR_MISSING=${manifest_dir}" \
      | tee "${EVIDENCE_DIR}/closeout_manifest_verify.txt"
    return 13
  fi
  (
    cd "$manifest_dir"
    find . -type f ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 shasum -a 256 >MANIFEST.sha256
    shasum -a 256 -c MANIFEST.sha256
  ) >"${EVIDENCE_DIR}/closeout_manifest_verify.txt" 2>&1
  local rc=$?
  printf '%s\n' "$rc" >"${EVIDENCE_DIR}/closeout_manifest_verify.rc"
  if [[ "$rc" -ne 0 ]]; then
    echo "BLOCKED_CLOSEOUT_MANIFEST_VERIFY_RC=${rc}" | tee -a "${EVIDENCE_DIR}/closeout_manifest_verify.txt"
    return 13
  fi
  echo "CLOSEOUT_MANIFEST_VERIFY_RC=0" | tee -a "${EVIDENCE_DIR}/closeout_manifest_verify.txt"
  return 0
}

cmd_post_merge_validate() {
  local pytest_k="$DEFAULT_PYTEST_K"
  local pytest_target=""
  local non_class_d_origin_main_policy_test=0
  local skip_ruff=0
  local skip_pytest=0
  local verify_source=0
  EVIDENCE_DIR=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --evidence-dir)
        shift
        [[ $# -gt 0 ]] || die_usage "Missing value for --evidence-dir"
        EVIDENCE_DIR="$1"
        shift
        ;;
      --pytest-k)
        shift
        [[ $# -gt 0 ]] || die_usage "Missing value for --pytest-k"
        pytest_k="$1"
        shift
        ;;
      --pytest-target)
        shift
        [[ $# -gt 0 ]] || die_usage "Missing value for --pytest-target"
        pytest_target="$1"
        shift
        ;;
      --non-class-d-origin-main-policy-test)
        non_class_d_origin_main_policy_test=1
        shift
        ;;
      --skip-ruff) skip_ruff=1; shift ;;
      --skip-pytest) skip_pytest=1; shift ;;
      --verify-source-manifest) verify_source=1; shift ;;
      -h | --help)
        usage
        exit 0
        ;;
      *)
        die_usage "Unknown option: $1"
        ;;
    esac
  done

  [[ -n "$EVIDENCE_DIR" ]] || die_usage "--evidence-dir is required"
  mkdir -p "$EVIDENCE_DIR"

  if [[ "$non_class_d_origin_main_policy_test" -eq 1 ]]; then
    if ! pytest_target="$(resolve_non_class_d_origin_main_policy_test_path)"; then
      die_usage "Canonical Non-Class-D origin-main policy test missing"
    fi
  fi

  local pytest_rc=0
  local ruff_rc=0
  local head_rc=0
  local source_rc=0
  local manifest_rc=0

  if ! verify_head_equals_origin_main "$REMOTE" "$MAIN_BRANCH"; then
    head_rc=$?
  fi

  if [[ "$verify_source" -eq 1 ]]; then
    if ! verify_source_manifest_if_referenced; then
      source_rc=$?
    fi
  fi

  if [[ "$skip_pytest" -eq 0 ]]; then
    if ! run_targeted_pytest "$pytest_k" "$pytest_target"; then
      pytest_rc=6
    fi
    printf '%s\n' "$pytest_rc" >"${EVIDENCE_DIR}/pytest_targeted_post_merge.rc"
  fi

  if [[ "$skip_ruff" -eq 0 ]]; then
    if ! run_ruff_gates; then
      ruff_rc=7
    fi
  fi

  if ! verify_closeout_manifest "$EVIDENCE_DIR"; then
    manifest_rc=$?
  fi

  local final_rc=0
  if ((head_rc != 0)); then
    final_rc=$head_rc
  elif ((source_rc != 0)); then
    final_rc=$source_rc
  elif ((pytest_rc != 0)); then
    final_rc=$pytest_rc
  elif ((ruff_rc != 0)); then
    final_rc=$ruff_rc
  elif ((manifest_rc != 0)); then
    final_rc=$manifest_rc
  fi
  echo "POST_MERGE_VALIDATE_FINAL_RC=${final_rc}" | tee "${EVIDENCE_DIR}/post_merge_validate_final.rc"
  echo "PYTEST_RC=${pytest_rc} RUFF_RC=${ruff_rc} HEAD_RC=${head_rc} SOURCE_RC=${source_rc} MANIFEST_RC=${manifest_rc}"
  return "$final_rc"
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    post-merge-validate) cmd_post_merge_validate "$@" ;;
    -h | --help | "")
      usage
      exit 0
      ;;
    *)
      die_usage "Unknown command: $cmd"
      ;;
  esac
}

main "$@"
