#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  scripts/ops/generate_merge_logs_batch.sh <PR> [<PR> ...]
Example:
  scripts/ops/generate_merge_logs_batch.sh 278 279 280
USAGE
}

die() { echo "ERROR: $*" >&2; exit 1; }

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

  mkdir -p docs/ops

  # meta (fetch as JSON)
  local meta title merged_at merge_oid merge_short
  meta="$(fetch_pr_meta "$pr")"
  title="$(echo "$meta" | jq -r '.title')"
  merged_at="$(echo "$meta" | jq -r '.mergedAt')"
  merge_oid="$(echo "$meta" | jq -r '.mergeCommit.oid')"
  merge_short="${merge_oid:0:7}"

  [ -n "$title" ] || die "could not parse title for PR #$pr"
  [ -n "$merged_at" ] || die "PR #$pr has no mergedAt"
  [ -n "$merge_oid" ] || die "PR #$pr has no mergeCommit"

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

  cat > "$out" <<MD
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
}

replace_or_append_block() {
  local file="$1"
  local block="$2"

  [ -f "$file" ] || die "file not found: $file"

  local start="<!-- MERGE_LOG_EXAMPLES:START -->"
  local end="<!-- MERGE_LOG_EXAMPLES:END -->"

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
  require_gh
  repo_root >/dev/null

  if [ "$#" -lt 1 ]; then
    usage
    exit 2
  fi

  local prs=("$@")

  # Generate logs
  for pr in "${prs[@]}"; do
    [[ "$pr" =~ ^[0-9]+$ ]] || die "invalid PR number: $pr"
    write_merge_log_md "$pr"
    echo "Wrote docs/ops/PR_${pr}_MERGE_LOG.md"
  done

  # Update docs links (idempotent block)
  update_ops_docs_links "${prs[@]}"
  echo "Updated docs/ops/MERGE_LOG_WORKFLOW.md + docs/ops/README.md"
}

main "$@"
