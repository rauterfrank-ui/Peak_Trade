#!/bin/bash
# Script to add all open issues to a GitHub Project
# Usage: ./scripts/add_issues_to_project.sh <PROJECT_NUMBER>

set -e

if [ -z "$1" ]; then
  echo "❌ Error: Project number required"
  echo "Usage: $0 <PROJECT_NUMBER>"
  echo "Example: $0 1"
  exit 1
fi

PROJECT_NUMBER="$1"
REPO="rauterfrank-ui/Peak_Trade"

echo "🚀 Adding open issues to Project #${PROJECT_NUMBER}..."
echo ""

# Get all open issue numbers
ISSUE_NUMBERS=$(gh issue list -R "$REPO" --state open --json number --jq '.[].number')

if [ -z "$ISSUE_NUMBERS" ]; then
  echo "⚠️  No open issues found in $REPO"
  exit 0
fi

TOTAL=$(echo "$ISSUE_NUMBERS" | wc -l | tr -d ' ')
CURRENT=0

echo "📋 Found $TOTAL open issue(s) to add"
echo ""

for issue in $ISSUE_NUMBERS; do
  CURRENT=$((CURRENT + 1))
  echo "[$CURRENT/$TOTAL] Adding issue #$issue to project..."

  if gh project item-add "$PROJECT_NUMBER" --owner rauterfrank-ui --url "https://github.com/$REPO/issues/$issue" 2>/dev/null; then
    echo "  ✅ Issue #$issue added"
  else
    echo "  ⚠️  Issue #$issue already in project or failed to add"
  fi
done

echo ""
echo "✅ Done! Added issues to Project #${PROJECT_NUMBER}"
