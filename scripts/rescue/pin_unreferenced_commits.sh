#!/usr/bin/env bash
set -euo pipefail

report_dir=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --report-dir) report_dir="${2:-}"; shift 2 ;;
    *) echo "WARN: Unbekanntes Argument: $1 (ignored)"; shift ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: Nicht in einem Git-Repo. Bitte im restored Repo ausführen."
  echo "PWD=$(pwd)"
  exit 2
fi

if [[ -z "${report_dir}" ]]; then
  report_dir="$(pwd)"
fi
mkdir -p "${report_dir}"

ts="$(date +%Y%m%d_%H%M%S)"
report="${report_dir}/unreferenced_commits_pinned_${ts}.tsv"

printf "full_sha\tshort_sha\ttag\tcommit_date\tsubject\tstatus\n" > "${report}"

echo "INFO: Scanne unreferenzierte Commits via git fsck ..."
commits="$(git fsck --unreachable --no-reflogs --full --no-progress 2>/dev/null | grep "unreachable commit" | awk '{print $3}' | sort -u)"

count_total=0
count_tagged=0
count_exist=0
count_skipped=0

if [[ -z "${commits}" ]]; then
  echo "INFO: Keine unreferenzierten Commits gefunden."
  echo "INFO: Report: ${report}"
  exit 0
fi

total_commits=$(echo "$commits" | wc -l | tr -d ' ')
echo "INFO: Found $total_commits unreferenced commits. Tagging..."

while IFS= read -r sha; do
  [[ -z "${sha}" ]] && continue
  count_total=$((count_total + 1))

  if [ $((count_total % 50)) -eq 0 ]; then
    echo "  Progress: $count_total/$total_commits (tagged: $count_tagged, exists: $count_exists, skipped: $count_skipped)"
  fi

  short12="$(git rev-parse --short=12 "${sha}" 2>/dev/null || true)"
  if [[ -z "${short12}" ]]; then
    count_skipped=$((count_skipped + 1))
    continue
  fi

  tag="rescue/unref/${short12}"
  tagref="refs/tags/${tag}"

  if git show-ref --verify --quiet "${tagref}" 2>/dev/null; then
    existing_sha="$(git rev-parse "${tag}" 2>/dev/null || true)"
    if [[ "${existing_sha}" == "${sha}" ]]; then
      status="exists"
      count_exists=$((count_exists + 1))
    else
      short16="$(git rev-parse --short=16 "${sha}" 2>/dev/null || true)"
      tag="rescue/unref/${short16}"
      tagref="refs/tags/${tag}"

      if git show-ref --verify --quiet "${tagref}" 2>/dev/null; then
        existing_sha2="$(git rev-parse "${tag}" 2>/dev/null || true)"
        if [[ "${existing_sha2}" == "${sha}" ]]; then
          status="exists"
          count_exists=$((count_exists + 1))
        else
          status="skipped_tag_collision"
          count_skipped=$((count_skipped + 1))
        fi
      else
        git tag -a "${tag}" "${sha}" -m "rescue: pin unreachable commit ${sha} (fsck) @ ${ts}" 2>/dev/null
        status="tagged"
        count_tagged=$((count_tagged + 1))
      fi
    fi
  else
    git tag -a "${tag}" "${sha}" -m "rescue: pin unreachable commit ${sha} (fsck) @ ${ts}" 2>/dev/null
    status="tagged"
    count_tagged=$((count_tagged + 1))
  fi

  commit_date="$(git show -s --date=iso-strict --format='%ad' "${sha}" 2>/dev/null || echo '-')"
  subject="$(git show -s --format='%s' "${sha}" 2>/dev/null | head -c 100 || echo '-')"
  short="$(git rev-parse --short=12 "${sha}" 2>/dev/null || echo '-')"

  printf "%s\t%s\t%s\t%s\t%s\t%s\n" "${sha}" "${short}" "${tag}" "${commit_date}" "${subject}" "${status}" >> "${report}"
done <<< "${commits}"

echo ""
echo "INFO: Done."
echo "INFO: Found commits: ${count_total} | tagged: ${count_tagged} | already tagged: ${count_exists} | skipped: ${count_skipped}"
echo "INFO: Report: ${report}"
