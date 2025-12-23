#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Peak_Trade – Stash Triage Tool (Safe-by-Default)
#
# Purpose: Inspect, export, and optionally drop Git stashes
#
# Usage:
#   stash_triage.sh [--help]
#   stash_triage.sh [--list]                             (default)
#   stash_triage.sh --export-all [OPTIONS]
#
# Options:
#   --help                    Show this help and exit
#   --list                    List all stashes (default, exit 0)
#   --export-all              Export all stashes as patches + metadata
#   --filter <keyword>        Filter stashes by message substring
#   --export-dir <path>       Export directory (default: docs/ops/stash_refs)
#   --session-report <path>   Session report path (default: docs/ops/STASH_TRIAGE_SESSION_<timestamp>.md)
#   --drop-after-export       Drop stashes after export (requires --confirm-drop)
#   --confirm-drop            Confirmation flag for dropping (mandatory with --drop-after-export)
#
# Safety:
#   - No deletion without explicit flags (--drop-after-export + --confirm-drop)
#   - Exit 2 if --drop-after-export without --confirm-drop
#   - Exit 0 if no stashes found
#
# Dependencies:
#   - git
#   - Optional: scripts/ops/run_helpers.sh (for logging, fallback available)
# ─────────────────────────────────────────────────────────────

set -euo pipefail

# ─────────────────────────────────────────────────────────────
# Fallback logging (if run_helpers.sh not available)
# ─────────────────────────────────────────────────────────────

pt_ts() {
  date +"%Y-%m-%d %H:%M:%S"
}

pt_log() {
  echo "[$(pt_ts)] $*"
}

pt_warn() {
  echo "[$(pt_ts)] ⚠️  $*" >&2
}

pt_die() {
  echo "[$(pt_ts)] ❌ $*" >&2
  exit 1
}

pt_section() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "$*"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ─────────────────────────────────────────────────────────────
# Optional: source run_helpers.sh (if available)
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_HELPERS="${SCRIPT_DIR}/run_helpers.sh"

if [[ -f "$RUN_HELPERS" ]]; then
  # shellcheck source=run_helpers.sh
  source "$RUN_HELPERS"
  pt_log "✅ Sourced run_helpers.sh"
fi

# ─────────────────────────────────────────────────────────────
# Defaults
# ─────────────────────────────────────────────────────────────

ACTION="list"
FILTER=""
EXPORT_DIR="docs/ops/stash_refs"
SESSION_REPORT=""
DROP_AFTER_EXPORT=0
CONFIRM_DROP=0

# ─────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────

show_help() {
  cat <<'EOF'
stash_triage.sh – Safe Stash Management Tool

Usage:
  stash_triage.sh [--help]
  stash_triage.sh [--list]                             (default)
  stash_triage.sh --export-all [OPTIONS]

Options:
  --help                    Show this help and exit
  --list                    List all stashes (default, exit 0)
  --export-all              Export all stashes as patches + metadata
  --filter <keyword>        Filter stashes by message substring
  --export-dir <path>       Export directory (default: docs/ops/stash_refs)
  --session-report <path>   Session report path (default: docs/ops/STASH_TRIAGE_SESSION_<timestamp>.md)
  --drop-after-export       Drop stashes after export (requires --confirm-drop)
  --confirm-drop            Confirmation flag for dropping (mandatory with --drop-after-export)

Safety:
  - No deletion without explicit flags (--drop-after-export + --confirm-drop)
  - Exit 2 if --drop-after-export without --confirm-drop
  - Exit 0 if no stashes found

Examples:
  # List all stashes
  stash_triage.sh --list

  # Export all stashes
  stash_triage.sh --export-all

  # Export filtered stashes
  stash_triage.sh --export-all --filter "my-feature"

  # Export and drop (with confirmation)
  stash_triage.sh --export-all --drop-after-export --confirm-drop
EOF
  exit 0
}

# ─────────────────────────────────────────────────────────────
# Parse arguments
# ─────────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      show_help
      ;;
    --list)
      ACTION="list"
      shift
      ;;
    --export-all)
      ACTION="export-all"
      shift
      ;;
    --filter)
      FILTER="$2"
      shift 2
      ;;
    --export-dir)
      EXPORT_DIR="$2"
      shift 2
      ;;
    --session-report)
      SESSION_REPORT="$2"
      shift 2
      ;;
    --drop-after-export)
      DROP_AFTER_EXPORT=1
      shift
      ;;
    --confirm-drop)
      CONFIRM_DROP=1
      shift
      ;;
    *)
      pt_die "Unknown option: $1 (use --help for usage)"
      ;;
  esac
done

# ─────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────

# Check if git is available
command -v git >/dev/null 2>&1 || pt_die "git not found in PATH"

# Check if --drop-after-export requires --confirm-drop
if [[ "$DROP_AFTER_EXPORT" -eq 1 && "$CONFIRM_DROP" -ne 1 ]]; then
  pt_die "🛑 --drop-after-export requires --confirm-drop (safety check) – exit 2"
  exit 2
fi

# ─────────────────────────────────────────────────────────────
# Action: list
# ─────────────────────────────────────────────────────────────

if [[ "$ACTION" == "list" ]]; then
  pt_section "📋 Git Stash List"

  # Check if any stashes exist
  if ! git stash list | grep -q .; then
    pt_log "ℹ️  No stashes found"
    exit 0
  fi

  git stash list
  exit 0
fi

# ─────────────────────────────────────────────────────────────
# Action: export-all
# ─────────────────────────────────────────────────────────────

if [[ "$ACTION" == "export-all" ]]; then
  pt_section "📦 Export All Stashes"

  # Get stash list
  STASH_LIST=$(git stash list || true)

  if [[ -z "$STASH_LIST" ]]; then
    pt_log "ℹ️  No stashes found – nothing to export"

    # Create empty session report (optional)
    if [[ -z "$SESSION_REPORT" ]]; then
      TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
      SESSION_REPORT="docs/ops/STASH_TRIAGE_SESSION_${TIMESTAMP}.md"
    fi

    mkdir -p "$(dirname "$SESSION_REPORT")"
    cat > "$SESSION_REPORT" <<EOF
# Stash Triage Session Report

- **Date:** $(date +"%Y-%m-%d %H:%M:%S")
- **Filter:** ${FILTER:-none}
- **Export Dir:** $EXPORT_DIR
- **Drop After Export:** $([ "$DROP_AFTER_EXPORT" -eq 1 ] && echo "yes" || echo "no")

## Result

No stashes found.
EOF

    pt_log "✅ Session report: $SESSION_REPORT"
    exit 0
  fi

  # Apply filter if specified
  if [[ -n "$FILTER" ]]; then
    pt_log "🔍 Filtering stashes by: $FILTER"
    STASH_LIST=$(echo "$STASH_LIST" | grep -i "$FILTER" || true)

    if [[ -z "$STASH_LIST" ]]; then
      pt_log "ℹ️  No stashes match filter: $FILTER"
      exit 0
    fi
  fi

  # Create export directory
  mkdir -p "$EXPORT_DIR"
  pt_log "📂 Export directory: $EXPORT_DIR"

  # Generate session report path
  if [[ -z "$SESSION_REPORT" ]]; then
    TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
    SESSION_REPORT="docs/ops/STASH_TRIAGE_SESSION_${TIMESTAMP}.md"
  fi

  mkdir -p "$(dirname "$SESSION_REPORT")"

  # Initialize session report
  cat > "$SESSION_REPORT" <<EOF
# Stash Triage Session Report

- **Date:** $(date +"%Y-%m-%d %H:%M:%S")
- **Filter:** ${FILTER:-none}
- **Export Dir:** $EXPORT_DIR
- **Drop After Export:** $([ "$DROP_AFTER_EXPORT" -eq 1 ] && echo "yes ✅" || echo "no")

## Exported Stashes

| Ref | Message | Patch | Metadata | Dropped |
|-----|---------|-------|----------|---------|
EOF

  # Export each stash
  EXPORT_COUNT=0
  TIMESTAMP=$(date +"%Y%m%d-%H%M%S")

  while IFS= read -r line; do
    # Parse stash ref (e.g., stash@{0})
    STASH_REF=$(echo "$line" | sed -E 's/^(stash@\{[0-9]+\}).*$/\1/')
    STASH_MSG=$(echo "$line" | sed -E 's/^stash@\{[0-9]+\}: //')

    # Generate export filenames
    IDX=$EXPORT_COUNT
    PATCH_FILE="${EXPORT_DIR}/stash_ref_${TIMESTAMP}_${IDX}.patch"
    META_FILE="${EXPORT_DIR}/stash_ref_${TIMESTAMP}_${IDX}.md"

    pt_log "📄 Exporting $STASH_REF → $(basename "$PATCH_FILE")"

    # Export patch
    git stash show -p "$STASH_REF" > "$PATCH_FILE"

    # Export metadata
    cat > "$META_FILE" <<EOF
# Stash Export Metadata

- **Ref:** $STASH_REF
- **Message:** $STASH_MSG
- **Exported:** $(date +"%Y-%m-%d %H:%M:%S")
- **Patch:** $(basename "$PATCH_FILE")

## Diffstat

\`\`\`
$(git stash show --stat "$STASH_REF" 2>/dev/null || echo "N/A")
\`\`\`

## Files Changed

\`\`\`
$(git stash show --name-only "$STASH_REF" 2>/dev/null || echo "N/A")
\`\`\`
EOF

    # Append to session report
    DROPPED_STATUS="no"
    if [[ "$DROP_AFTER_EXPORT" -eq 1 ]]; then
      pt_log "🗑️  Dropping $STASH_REF (--drop-after-export + --confirm-drop)"
      git stash drop "$STASH_REF"
      DROPPED_STATUS="yes ✅"
    fi

    echo "| $STASH_REF | $STASH_MSG | $(basename "$PATCH_FILE") | $(basename "$META_FILE") | $DROPPED_STATUS |" >> "$SESSION_REPORT"

    EXPORT_COUNT=$((EXPORT_COUNT + 1))
  done <<< "$STASH_LIST"

  # Finalize session report
  cat >> "$SESSION_REPORT" <<EOF

## Summary

- **Total Exported:** $EXPORT_COUNT
- **Export Directory:** $EXPORT_DIR
- **Dropped After Export:** $([ "$DROP_AFTER_EXPORT" -eq 1 ] && echo "yes ✅" || echo "no")

## Usage

To apply a stash patch:

\`\`\`bash
git apply $EXPORT_DIR/stash_ref_${TIMESTAMP}_0.patch
\`\`\`

To view metadata:

\`\`\`bash
cat $EXPORT_DIR/stash_ref_${TIMESTAMP}_0.md
\`\`\`
EOF

  pt_section "✅ Export Complete"
  pt_log "📊 Exported: $EXPORT_COUNT stash(es)"
  pt_log "📂 Export directory: $EXPORT_DIR"
  pt_log "📋 Session report: $SESSION_REPORT"

  if [[ "$DROP_AFTER_EXPORT" -eq 1 ]]; then
    pt_log "🗑️  Dropped: $EXPORT_COUNT stash(es)"
  fi

  exit 0
fi

# ─────────────────────────────────────────────────────────────
# Fallback (should not reach here)
# ─────────────────────────────────────────────────────────────

pt_die "Unknown action: $ACTION"
