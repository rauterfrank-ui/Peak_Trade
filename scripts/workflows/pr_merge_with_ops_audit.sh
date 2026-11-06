#!/usr/bin/env bash
# ============================================================
# PR Merge Workflow mit Ops Audit
# Führt den vollständigen Merge-Prozess mit Pre/Post-Audits durch
# ============================================================
set -euo pipefail

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================
# Pre-flight Checks
# ============================================================
log_info "Phase 1: Pre-flight Checks"

# Check: Repo Root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"
log_info "Repository: $REPO_ROOT"

# Check: Git Status
if ! git diff-index --quiet HEAD --; then
    log_error "Uncommitted changes detected. Commit or stash first."
    exit 1
fi
log_success "Git working tree is clean"

# Check: Current Branch
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT_BRANCH" == "main" ]]; then
    log_error "Already on main. Switch to PR branch first."
    exit 1
fi
log_info "Current branch: $CURRENT_BRANCH"

# Check: Remote status
git fetch origin main
BEHIND="$(git rev-list --count HEAD..origin/main)"
if [[ "$BEHIND" -gt 0 ]]; then
    log_warning "Branch is $BEHIND commit(s) behind origin/main. Consider rebasing."
fi

# ============================================================
# Phase 2: Pre-Merge Audit
# ============================================================
log_info "Phase 2: Pre-Merge Audit"

log_info "Running Ops Merge Log audit..."
if uv run python scripts/audit/check_ops_merge_logs.py; then
    log_success "All existing merge logs are compliant"
else
    log_warning "Some legacy merge logs have violations (non-blocking)"
fi

# Weitere Pre-Merge Checks können hier hinzugefügt werden
# z.B. Tests, Linting, etc.

# ============================================================
# Phase 3: Merge
# ============================================================
log_info "Phase 3: Merge to main"

# Switch to main
git switch main
log_success "Switched to main"

# Update main
git pull --ff-only origin main
log_success "Updated main from origin"

# Merge PR branch (fast-forward if possible, or merge commit)
log_info "Merging $CURRENT_BRANCH into main..."
if git merge --ff "$CURRENT_BRANCH" 2>/dev/null; then
    log_success "Fast-forward merge completed"
else
    log_warning "Fast-forward not possible, creating merge commit..."
    git merge --no-ff "$CURRENT_BRANCH" -m "Merge branch '$CURRENT_BRANCH' into main"
    log_success "Merge commit created"
fi

# ============================================================
# Phase 4: Post-Merge Verification
# ============================================================
log_info "Phase 4: Post-Merge Verification"

# Zeige letzten Commit
log_info "Latest commit:"
git log -1 --oneline

# Status check
git status -sb

# Run audit again
log_info "Running post-merge audit..."
if uv run python scripts/audit/check_ops_merge_logs.py; then
    log_success "Post-merge audit passed"
else
    log_warning "Post-merge audit found violations (check reports)"
fi

# ============================================================
# Phase 5: Cleanup & Push
# ============================================================
log_info "Phase 5: Cleanup"

log_warning "Ready to push to origin/main?"
log_info "Run: git push origin main"
log_info "To delete merged branch: git branch -d $CURRENT_BRANCH"

log_success "Merge workflow completed!"
echo ""
echo "Next steps:"
echo "  1. Review the merge with: git log -1 --stat"
echo "  2. Push to remote: git push origin main"
echo "  3. Delete PR branch: git branch -d $CURRENT_BRANCH"
echo "  4. Create merge log: docs/ops/PR_XXX_MERGE_LOG.md"
