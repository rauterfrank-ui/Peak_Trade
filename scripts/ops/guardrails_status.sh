#!/usr/bin/env bash
set -euo pipefail

OWNER="${OWNER:-rauterfrank-ui}"
REPO="${REPO:-Peak_Trade}"
BRANCH="${BRANCH:-main}"

echo "🔒 Guardrails Status — ${OWNER}/${REPO} (${BRANCH})"
echo

# Fetch branch protection
PROT_JSON="$(gh api "repos/${OWNER}/${REPO}/branches/${BRANCH}/protection")"

# Parse and display using jq
echo "$PROT_JSON" | jq -r '
"Branch protection: ENABLED",
"enforce_admins: \(.enforce_admins.enabled)",
"strict: \(.required_status_checks.strict)",
"approvals_required: \(.required_pull_request_reviews.required_approving_review_count)",
"codeowner_reviews_required: \(.required_pull_request_reviews.require_code_owner_reviews)",
"allow_force_pushes: \(.allow_force_pushes.enabled)",
"allow_deletions: \(.allow_deletions.enabled)",
"",
"Required contexts:"
'

echo "$PROT_JSON" | jq -r '.required_status_checks.contexts[] | " - \(.)"'
