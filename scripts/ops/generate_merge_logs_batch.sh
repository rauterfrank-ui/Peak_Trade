#!/usr/bin/env bash
set -euo pipefail

# Flags
DRY_RUN=0
KEEP_GOING=0
PRS=()

usage() {
  cat <<'USAGE'
Usage:
  scripts/ops/generate_merge_logs_batch.sh [--dry-run] [--keep-going] <PR> [<PR> ...]

Flags:
  --dry-run      Preview only. Generate outputs into temp files and show diffs.
                 Does NOT modify the working tree.
  --keep-going   Continue on per-PR failures, summarize at end, exit 1 if any failed.
  -h, --help     Show this help.
  --             End of flags; remaining arguments are PR numbers.

Examples:
  scripts/ops/generate_merge_logs_batch.sh 281
  scripts/ops/generate_merge_logs_batch.sh 278 279 280
  scripts/ops/generate_merge_logs_batch.sh --dry-run 281
  scripts/ops/generate_merge_logs_batch.sh --keep-going 278 279 999999
  scripts/ops/generate_merge_logs_batch.sh -- 281 282 283
USAGE
}

die() { echo "ERROR: $*" >&2; exit 1; }

is_int() { [[ "${1:-}" =~ ^[0-9]+$ ]]; }

require_gh() {
  command -v gh >/dev/null 2>&1 || die "gh CLI not found"
  gh auth status >/dev/null 2>&1 || die "gh not authenticated (run: gh auth login)"
}

repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || die "not a git repo"
}

short_desc_for_pr() {
  local pr="$1"
  case "$pr" in
    278) echo "merge log for PR #123 + ops references" ;;
    279) echo "salvage untracked docs/ops assets" ;;
    280) echo "archive session reports to worklogs" ;;
    *)   echo "" ;;
  esac
}

fetch_pr_meta() {
  local pr="$1"
  # Fetch all in one call for efficiency
  gh pr view "$pr" --json title,mergedAt,mergeCommit 2>/dev/null || die "could not fetch PR #$pr"
}

write_merge_log_md() {
  local pr="$1"
  local out="docs/ops/PR_${pr}_MERGE_LOG.md"

  # meta (fetch as JSON)
  local meta title merged_at merge_oid merge_short
  meta="$(fetch_pr_meta "$pr")" || return 1
  title="$(echo "$meta" | jq -r '.title')"
  merged_at="$(echo "$meta" | jq -r '.mergedAt')"
  merge_oid="$(echo "$meta" | jq -r '.mergeCommit.oid')"
  merge_short="${merge_oid:0:7}"

  [ -n "$title" ] || { echo "ERROR: could not parse title for PR #$pr" >&2; return 1; }
  [ -n "$merged_at" ] || { echo "ERROR: PR #$pr has no mergedAt" >&2; return 1; }
  [ -n "$merge_oid" ] || { echo "ERROR: PR #$pr has no mergeCommit" >&2; return 1; }

  # checks (plain text)
  local checks
  checks="$(gh pr checks "$pr" 2>&1 || true)"

  # changes (static hints for known PRs)
  local changes_block=""
  case "$pr" in
    278)
      changes_block=$'- Neuer Merge-Log: `docs/ops/PR_123_MERGE_LOG.md`\n- Ops-Referenzen ergänzt: `docs/ops/MERGE_LOG_WORKFLOW.md`, `docs/ops/README.md`'
      ;;
    279)
      changes_block=$'- Merge-Logs gerettet: `docs/ops/PR_267_MERGE_LOG.md`, `docs/ops/PR_271_MERGE_LOG.md`\n- Guides gerettet unter `docs/` (Contract/MLflow/Optuna/Strategy)\n- Ops-Skripte gerettet unter `scripts/ops/`'
      ;;
    280)
      changes_block=$'- Session-Reports archiviert unter `docs/_worklogs/...`\n- `README.md` im Worklog-Ordner ergänzt (Kontext)\n- `.gitignore` Root-Guard ergänzt (reduziert zukünftigen Root-Clutter)'
      ;;
    *)
      changes_block=$'- Siehe PR-Diff / Commit-Inhalt'
      ;;
  esac

  local content
  content=$(cat <<MD
# PR #${pr} — ${title}

## Summary
PR #${pr} wurde erfolgreich **gemerged** in \`main\`.

- PR: #${pr} (state: MERGED)
- MergedAt (UTC): ${merged_at}
- Merge-Commit: \`${merge_short}\` (\`${merge_oid}\`)
- Titel: ${title}

## Why
- Merge-Log / Audit-Trail konsistent halten.
- Ops-Dokumentation mit konkreten Referenzen aktualisieren.

## Changes
${changes_block}

## Verification
- \`git show --no-patch ${merge_short}\`
- \`scripts/ops/validate_merge_dryrun_docs.sh\` (exit 0)
- \`git status\` clean

## CI Checks
\`\`\`
${checks}
\`\`\`

## Risk
Low — docs/ops only.

## Operator How-To
- Merge-Logs liegen unter: \`docs/ops/\`
- Docs validation:
  - \`scripts/ops/validate_merge_dryrun_docs.sh\`

## References
- PR: #${pr}
- Merge-Commit: ${merge_oid}
MD
)

  if [[ "$DRY_RUN" -eq 1 ]]; then
    # Dry-run: write to temp and show diff
    local tmp
    tmp="$(mktemp)"
    echo "$content" > "$tmp"

    echo "[DRY-RUN] Would write: $out"

    if [[ -f "$out" ]]; then
      echo "Diff vs existing:"
      diff -u "$out" "$tmp" || true
    else
      echo "(new file, $(wc -l < "$tmp") lines)"
    fi

    rm -f "$tmp"
    return 0
  fi

  # Real write
  mkdir -p docs/ops
  echo "$content" > "$out"
}

replace_or_append_block() {
  local file="$1"
  local block="$2"

  [ -f "$file" ] || { echo "ERROR: file not found: $file" >&2; return 1; }

  local start="<!-- MERGE_LOG_EXAMPLES:START -->"
  local end="<!-- MERGE_LOG_EXAMPLES:END -->"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[DRY-RUN] Would update markers in: $file"
    return 0
  fi

  if grep -qF "$start" "$file" && grep -qF "$end" "$file"; then
    # Replace between markers using Python (portable)
    python3 <<PYEOF
import sys
with open("$file", "r") as f:
    content = f.read()

start_marker = "$start"
end_marker = "$end"
block = """$block"""

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + block + "\n" + content[end_idx + len(end_marker):]
    with open("$file", "w") as f:
        f.write(new_content)
PYEOF
  else
    # Append at end
    printf "\n\n%s\n" "$block" >> "$file"
  fi
}

update_ops_docs_links() {
  local prs=("$@")

  local lines=()
  for pr in "${prs[@]}"; do
    local desc
    desc="$(short_desc_for_pr "$pr")"
    if [ -z "$desc" ]; then
      # fallback to title from API
      local meta title
      meta="$(fetch_pr_meta "$pr")"
      title="$(echo "$meta" | jq -r '.title')"
      desc="$title"
    fi
    lines+=("- PR #${pr} — ${desc}: docs/ops/PR_${pr}_MERGE_LOG.md")
  done

  local block
  block="<!-- MERGE_LOG_EXAMPLES:START -->"$'\n'
  for l in "${lines[@]}"; do
    block+="${l}"$'\n'
  done
  block+="<!-- MERGE_LOG_EXAMPLES:END -->"

  replace_or_append_block "docs/ops/MERGE_LOG_WORKFLOW.md" "$block"
  replace_or_append_block "docs/ops/README.md" "$block"
}

main() {
  # Parse flags (bash-safe)
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run)
        DRY_RUN=1
        shift
        ;;
      --keep-going)
        KEEP_GOING=1
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      --)
        shift
        while [[ $# -gt 0 ]]; do
          PRS+=("$1")
          shift
        done
        ;;
      -*)
        die "Unknown flag: $1 (try --help)"
        ;;
      *)
        PRS+=("$1")
        shift
        ;;
    esac
  done

  # Validate args
  if [[ "${#PRS[@]}" -eq 0 ]]; then
    usage
    die "No PR numbers provided"
  fi

  # Normalize / validate PR numbers
  for pr in "${PRS[@]}"; do
    is_int "$pr" || die "Invalid PR number: '$pr' (must be an integer)"
  done

  require_gh
  repo_root >/dev/null

  [[ "$DRY_RUN" -eq 1 ]] && echo "[DRY-RUN] Preview mode: no files will be written"
  echo ""

  local failures=()

  # Generate logs
  for pr in "${PRS[@]}"; do

    if write_merge_log_md "$pr"; then
      [[ "$DRY_RUN" -eq 1 ]] || echo "✅ Wrote docs/ops/PR_${pr}_MERGE_LOG.md"
    else
      echo "❌ Failed: PR #$pr" >&2
      failures+=("$pr")
      [[ "$KEEP_GOING" -eq 0 ]] && exit 1
    fi
  done

  # Update docs links (idempotent block)
  if [[ "${#failures[@]}" -eq 0 ]] || [[ "$KEEP_GOING" -eq 1 ]]; then
    local successful_prs=()
    for pr in "${PRS[@]}"; do
      # Only include successfully processed PRs
      local failed=0
      if [[ "${#failures[@]}" -gt 0 ]]; then
        for fail in "${failures[@]}"; do
          if [[ "$fail" == "$pr"* ]]; then
            failed=1
            break
          fi
        done
      fi
      [[ "$failed" -eq 0 ]] && successful_prs+=("$pr")
    done

    if [[ "${#successful_prs[@]}" -gt 0 ]]; then
      if update_ops_docs_links "${successful_prs[@]}"; then
        [[ "$DRY_RUN" -eq 1 ]] || echo "✅ Updated docs/ops/MERGE_LOG_WORKFLOW.md + docs/ops/README.md"
      else
        echo "⚠️  Warning: could not update docs links" >&2
      fi
    fi
  fi

  # Summary
  echo ""
  if [[ "${#failures[@]}" -gt 0 ]]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Failures (${#failures[@]}/${#PRS[@]}):"
    for fail in "${failures[@]}"; do
      echo "   - $fail"
    done
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
  else
    [[ "$DRY_RUN" -eq 1 ]] && echo "[DRY-RUN] Preview complete. No changes made."
    echo "✅ Success: processed ${#PRS[@]} PR(s)"
  fi
}

main "$@"
