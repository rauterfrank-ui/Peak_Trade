#!/usr/bin/env bash
# === Peak_Trade: GitHub Setup — current-state extraction (CLI+API) ===
# Goal: Export the *actual* repo/rules/required-checks/workflows/security state into a local evidence dir.
# Requires: gh auth status OK, jq installed.

set -euo pipefail

OWNER="rauterfrank-ui"
REPO="Peak_Trade"
BRANCH="main"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR="out/ops/github_setup_snapshot_${TS}"
mkdir -p "$EVIDENCE_DIR"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# ----------------------------
# Planner: repo identity + basics
# ----------------------------
gh repo view "$OWNER/$REPO" --json name,owner,visibility,defaultBranchRef,isPrivate,isFork,createdAt,updatedAt,url,sshUrl,homepageUrl,description \
  | jq . > "$EVIDENCE_DIR/repo_basics.json"

gh api "repos/$OWNER/$REPO" \
  | jq '{
      full_name, private, fork, visibility, default_branch,
      has_issues, has_projects, has_wiki,
      allow_squash_merge, allow_merge_commit, allow_rebase_merge,
      delete_branch_on_merge, allow_auto_merge, allow_update_branch,
      squash_merge_commit_title, squash_merge_commit_message,
      merge_commit_title, merge_commit_message,
      security_and_analysis,
      archived, disabled
    }' > "$EVIDENCE_DIR/repo_settings.json"

# ----------------------------
# Implementer: branch protection + required checks
# ----------------------------
# Classic branch protection (may be absent if repo uses Rulesets only)
gh api -H "Accept: application/vnd.github+json" "repos/$OWNER/$REPO/branches/$BRANCH/protection" \
  | jq . > "$EVIDENCE_DIR/branch_protection_full.json" 2>/dev/null || true

# Extract key protection fields (if present)
if [[ -s "$EVIDENCE_DIR/branch_protection_full.json" ]]; then
  jq '{
    required_status_checks: .required_status_checks,
    enforce_admins: .enforce_admins,
    required_pull_request_reviews: .required_pull_request_reviews,
    restrictions: .restrictions,
    required_linear_history: .required_linear_history,
    allow_force_pushes: .allow_force_pushes,
    allow_deletions: .allow_deletions,
    required_signatures: .required_signatures,
    lock_branch: .lock_branch
  }' "$EVIDENCE_DIR/branch_protection_full.json" > "$EVIDENCE_DIR/branch_protection_summary.json"

  # Required contexts (if strict list exists)
  jq -r '.required_status_checks.contexts[]? // empty' "$EVIDENCE_DIR/branch_protection_full.json" \
    | sort -u > "$EVIDENCE_DIR/required_status_checks_contexts.txt" 2>/dev/null || true
fi

# ----------------------------
# Implementer: Rulesets (modern replacement/supplement)
# ----------------------------
# Repo rulesets list
gh api -H "Accept: application/vnd.github+json" "repos/$OWNER/$REPO/rulesets" \
  | jq . > "$EVIDENCE_DIR/rulesets_list.json" 2>/dev/null || true

# Fetch each ruleset detail (if any)
if [[ -s "$EVIDENCE_DIR/rulesets_list.json" ]]; then
  jq -r '.[].id? // empty' "$EVIDENCE_DIR/rulesets_list.json" 2>/dev/null \
    | while read -r RID; do
        [[ -n "$RID" ]] || continue
        gh api -H "Accept: application/vnd.github+json" "repos/$OWNER/$REPO/rulesets/$RID" \
          | jq . > "$EVIDENCE_DIR/ruleset_${RID}.json" 2>/dev/null || true
      done
fi

# ----------------------------
# Verifier: merge policy (squash/rebase/merge commit) + auto-merge + delete branch on merge
# ----------------------------
jq '{
  allow_squash_merge, allow_merge_commit, allow_rebase_merge,
  delete_branch_on_merge, allow_auto_merge, allow_update_branch,
  squash_merge_commit_title, squash_merge_commit_message,
  merge_commit_title, merge_commit_message
}' "$EVIDENCE_DIR/repo_settings.json" > "$EVIDENCE_DIR/merge_policy.json"

# ----------------------------
# Implementer: CODEOWNERS + PR templates (repo files)
# ----------------------------
# CODEOWNERS (common locations)
for P in ".github/CODEOWNERS" "CODEOWNERS" "docs/CODEOWNERS"; do
  if gh api "repos/$OWNER/$REPO/contents/$P" >/dev/null 2>&1; then
    gh api "repos/$OWNER/$REPO/contents/$P" \
      | jq -r '.content' | base64 --decode > "$EVIDENCE_DIR/$(echo "$P" | tr '/' '_')"
  fi
done

# PR templates directory listing + download
if gh api "repos/$OWNER/$REPO/contents/.github/PULL_REQUEST_TEMPLATE" >/dev/null 2>&1; then
  gh api "repos/$OWNER/$REPO/contents/.github/PULL_REQUEST_TEMPLATE" \
    | jq . > "$EVIDENCE_DIR/pr_templates_index.json"

  jq -r '.[].path? // empty' "$EVIDENCE_DIR/pr_templates_index.json" \
    | while read -r PATH_; do
        [[ -n "$PATH_" ]] || continue
        FILE_OUT="$EVIDENCE_DIR/$(echo "$PATH_" | tr '/' '_')"
        gh api "repos/$OWNER/$REPO/contents/$PATH_" \
          | jq -r '.content' | base64 --decode > "$FILE_OUT"
      done
else
  # Single PR template file (legacy)
  if gh api "repos/$OWNER/$REPO/contents/.github/PULL_REQUEST_TEMPLATE.md" >/dev/null 2>&1; then
    gh api "repos/$OWNER/$REPO/contents/.github/PULL_REQUEST_TEMPLATE.md" \
      | jq -r '.content' | base64 --decode > "$EVIDENCE_DIR/.github_PULL_REQUEST_TEMPLATE.md"
  fi
fi

# ----------------------------
# Implementer: workflows inventory (counts + names + paths)
# ----------------------------
gh api "repos/$OWNER/$REPO/actions/workflows" \
  | jq '{
      total_count,
      workflows: [.workflows[] | {id,name,path,state,created_at,updated_at}]
    }' > "$EVIDENCE_DIR/workflows.json"

jq -r '.workflows[] | "\(.id)\t\(.state)\t\(.name)\t\(.path)"' "$EVIDENCE_DIR/workflows.json" \
  | sort -k2,2 -k3,3 > "$EVIDENCE_DIR/workflows.tsv"

# ----------------------------
# Implementer: security & analysis flags (Dependabot / secret scanning / code scanning)
# ----------------------------
jq '.security_and_analysis' "$EVIDENCE_DIR/repo_settings.json" > "$EVIDENCE_DIR/security_and_analysis.json"

# Code scanning alerts (requires permissions; may be empty/403)
gh api -H "Accept: application/vnd.github+json" "repos/$OWNER/$REPO/code-scanning/alerts?state=open&per_page=100" \
  | jq '. | if type == "array" then {open_alerts: length} else . end' > "$EVIDENCE_DIR/code_scanning_open_alerts.json" 2>/dev/null || true

# Secret scanning alerts (requires permissions; may be empty/403)
gh api -H "Accept: application/vnd.github+json" "repos/$OWNER/$REPO/secret-scanning/alerts?state=open&per_page=100" \
  | jq '. | if type == "array" then {open_alerts: length} else . end' > "$EVIDENCE_DIR/secret_scanning_open_alerts.json" 2>/dev/null || true

# Dependabot alerts (requires permissions; may be empty/403)
gh api -H "Accept: application/vnd.github+json" "repos/$OWNER/$REPO/dependabot/alerts?state=open&per_page=100" \
  | jq '. | if type == "array" then {open_alerts: length} else . end' > "$EVIDENCE_DIR/dependabot_open_alerts.json" 2>/dev/null || true

# ----------------------------
# Verifier: required check names observed recently (empirical via recent PRs)
# ----------------------------
# Pull latest 30 merged PRs and collect check runs names (best-effort)
gh pr list -R "$OWNER/$REPO" --state merged -L 30 --json number,mergedAt \
  | jq -r '.[].number' > "$EVIDENCE_DIR/recent_merged_pr_numbers.txt"

: > "$EVIDENCE_DIR/recent_required_checks_observed.txt"
while read -r N; do
  gh pr checks -R "$OWNER/$REPO" "$N" --json name,state 2>/dev/null \
    | jq -r '.[].name // empty' >> "$EVIDENCE_DIR/recent_required_checks_observed.txt" || true
done < "$EVIDENCE_DIR/recent_merged_pr_numbers.txt"

sort -u "$EVIDENCE_DIR/recent_required_checks_observed.txt" > "$EVIDENCE_DIR/recent_required_checks_observed.sorted.txt"

# ----------------------------
# Final: human-readable snapshot MD
# ----------------------------
cat > "$EVIDENCE_DIR/SNAPSHOT_GITHUB_SETUP.md" <<'MD'
# Peak_Trade — GitHub Setup Snapshot

This directory contains an extracted, current-state snapshot from GitHub via `gh` + REST API.

## Files
- `repo_basics.json` — identity, default branch, visibility
- `repo_settings.json` — merge policies, auto-merge, delete-branch-on-merge, security_and_analysis
- `merge_policy.json` — extracted merge policy fields
- `branch_protection_full.json` / `branch_protection_summary.json` — classic branch protection (if enabled)
- `required_status_checks_contexts.txt` — strict required contexts (if present)
- `rulesets_list.json` + `ruleset_<id>.json` — repo rulesets (if configured)
- `workflows.json` / `workflows.tsv` — workflow inventory
- `security_and_analysis.json` — dependabot/secret scanning/code scanning toggles
- `*_open_alerts.json` — counts for open alerts (best-effort; may be missing due to permissions)
- `recent_required_checks_observed.sorted.txt` — empirically observed check names from last merged PRs (best-effort)
- `*_CODEOWNERS` + `pr_templates_*` — downloaded repo templates if present

## Notes
- If `branch_protection_full.json` is missing, the repo may rely primarily on Rulesets.
- Some alert endpoints require elevated permissions; files may be absent if 403/404.
MD

# Hashes for audit trail
( cd "$EVIDENCE_DIR" && find . -type f -maxdepth 1 -print0 | xargs -0 shasum -a 256 ) > "$EVIDENCE_DIR/SHA256SUMS.txt"

echo "OK: $EVIDENCE_DIR"
ls -la "$EVIDENCE_DIR"
