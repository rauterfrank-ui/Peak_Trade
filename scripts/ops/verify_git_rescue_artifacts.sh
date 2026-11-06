#!/usr/bin/env bash
# verify_git_rescue_artifacts.sh
# Purpose: Quick verification for Peak_Trade git rescue artifacts (bundle + backup refs + logs).

set -u
set -o pipefail

warns=0
errs=0

say() { printf "%s\n" "$*"; }
warn() { warns=$((warns+1)); say "WARN: $*"; }
err() { errs=$((errs+1)); say "ERROR: $*"; }

usage() {
  cat <<'EOF'
Usage:
  bash scripts/ops/verify_git_rescue_artifacts.sh \
    --backup-dir /path/to/rescue_dir \
    [--repo /path/to/Peak_Trade] \
    [--restored-repo /path/to/restored_repo]

Exit codes:
  0 = OK
  2 = Warnings (non-fatal)
  1 = Errors (missing/failed checks)
EOF
}

BACKUP_DIR=""
REPO_DIR=""
RESTORED_REPO_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backup-dir) BACKUP_DIR="${2:-}"; shift 2 ;;
    --repo) REPO_DIR="${2:-}"; shift 2 ;;
    --restored-repo) RESTORED_REPO_DIR="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) err "Unknown arg: $1"; shift ;;
  esac
done

[[ -n "$BACKUP_DIR" ]] || { usage; err "--backup-dir is required"; }

# Resolve repo dir
if [[ -z "$REPO_DIR" ]]; then
  REPO_DIR="$(pwd)"
fi

say "== Pre-flight =="
say "repo_dir: $REPO_DIR"
say "backup_dir: $BACKUP_DIR"
[[ -n "$RESTORED_REPO_DIR" ]] && say "restored_repo_dir: $RESTORED_REPO_DIR"

if [[ ! -d "$BACKUP_DIR" ]]; then
  err "Backup directory not found: $BACKUP_DIR"
fi

# Repo checks (non-fatal if not a git repo, but most checks need it)
if [[ -d "$REPO_DIR/.git" ]] || git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  say "git repo: OK"
else
  warn "Not a git repo: $REPO_DIR (bundle verify still possible; refs count will be skipped)"
fi

# Bundle checks
BUNDLE="$(ls -1 "$BACKUP_DIR"/*.bundle 2>/dev/null | head -n 1 || true)"
if [[ -z "$BUNDLE" ]]; then
  err "No bundle (*.bundle) found in $BACKUP_DIR"
else
  say
  say "== Bundle =="
  say "bundle: $BUNDLE"
  ls -lh "$BUNDLE" >/dev/null 2>&1 || warn "Could not stat bundle: $BUNDLE"
  if git bundle verify "$BUNDLE" >/dev/null 2>&1; then
    say "bundle verify: OK"
  else
    err "bundle verify failed (run: git bundle verify \"$BUNDLE\")"
  fi
fi

# Logs/Reports existence
say
say "== Logs/Reports presence =="
GONE_LOG="$(ls -1 "$BACKUP_DIR"/gone_backup_refs_*.tsv 2>/dev/null | head -n 1 || true)"
UNREF_LOG="$(ls -1 "$BACKUP_DIR"/unreferenced_commits_pinned_*.tsv 2>/dev/null | head -n 1 || true)"
if [[ -n "$GONE_LOG" ]]; then say "gone refs log: OK ($GONE_LOG)"; else warn "gone refs log not found (gone_backup_refs_*.tsv)"; fi
if [[ -n "$UNREF_LOG" ]]; then say "unreferenced pinned report: OK ($UNREF_LOG)"; else warn "unreferenced pinned report not found (unreferenced_commits_pinned_*.tsv)"; fi

# Backup refs count (requires original repo)
say
say "== Backup refs count (original repo) =="
if git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  n_refs="$(git -C "$REPO_DIR" for-each-ref refs/backup/gone --format='%(refname)' 2>/dev/null | wc -l | tr -d ' ')"
  say "refs/backup/gone/* : $n_refs"
  if [[ "$n_refs" -lt 1 ]]; then
    warn "No refs found under refs/backup/gone/* (is this the original repo?)"
  fi
else
  warn "Skipping refs count (repo not available)."
fi

# Restored repo checks (optional)
if [[ -n "$RESTORED_REPO_DIR" ]]; then
  say
  say "== Restored repo (optional) =="
  if git -C "$RESTORED_REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    n_tags="$(git -C "$RESTORED_REPO_DIR" tag -l 'rescue/*' 2>/dev/null | wc -l | tr -d ' ')"
    say "rescue/* tags: $n_tags"
    [[ "$n_tags" -lt 1 ]] && warn "No rescue/* tags found in restored repo."
  else
    warn "Not a git repo: $RESTORED_REPO_DIR"
  fi
fi

say
say "== Result =="
say "warnings: $warns"
say "errors:   $errs"

if [[ "$errs" -gt 0 ]]; then
  exit 1
elif [[ "$warns" -gt 0 ]]; then
  exit 2
else
  exit 0
fi
