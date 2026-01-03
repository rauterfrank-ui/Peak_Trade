# Terminal Hang Diagnostics Setup

**Date:** 2026-01-03  
**Status:** Completed  
**Scope:** Operator Tooling + Documentation

---

## Context

Cursor/Terminal hatte gefühlte "Hänger" (keine echten Freezes), vermutlich durch:
- Pager-Blocking (less wartet auf Eingabe)
- `gh watch` / `gh pr checks --watch` Loops
- Output-Blocking durch nicht-geschlossene Quotes/Heredocs

Zur Absicherung wurden Environment-Variablen gesetzt:
```bash
export GH_PAGER=cat
export PAGER=cat
export LESS='-FRX'
```

---

## Investigation Results

### Git Hooks Audit
✅ **Nur ein aktiver Hook:** `.git/hooks/pre-commit`
- Wrapper für pre-commit framework (20 Zeilen)
- Ruft: `.venv/bin/python3 -m pre_commit`
- Config: `.pre-commit-config.yaml`
- Keine verdächtigen Loops oder "pre-hook" Strings

✅ **Alle anderen Hooks:** Inaktive `*.sample` Dateien (Standard Git)

✅ **Keine Probleme gefunden**

---

## Solution Delivered

### 1. Diagnose-Tool
**File:** `scripts/ops/diag_terminal_hang.sh`

**Features:**
- Zeigt Pager-Environment (PAGER, GH_PAGER, LESS)
- Erkennt aktive Pager-Prozesse (less, more, bat)
- Findet Git/GitHub CLI Prozesse
- Erkennt laufende pre-commit Hooks
- Zeigt Shell/TTY Info und File Descriptors
- Gibt Diagnose-Checkliste mit Quick Actions

**Usage:**
```bash
./scripts/ops/diag_terminal_hang.sh
```

**Output:**
- Grüne Checkmarks: ✓ Alles OK
- Warnungen: ⚠️ mit Lösungsvorschlägen

### 2. Operator Runbook
**File:** `docs/ops/PAGER_HOOK_HANG_TRIAGE.md`

**Sections:**
1. **Problem Statement** - Symptom-Übersicht
2. **Diagnose-Checkliste** - 5 häufige Ursachen mit Lösung:
   - Pager wartet auf Eingabe
   - gh watch blockiert
   - pre-commit läuft lange
   - Heredoc/Quote nicht geschlossen
   - Background Job blockiert
3. **Environment Setup** - Empfohlene .zshrc/.bashrc Konfiguration
4. **Verification** - Tests für korrektes Setup
5. **Git Hooks Status** - Aktueller Stand (2026-01-03)
6. **Quick Actions Reference** - Tabelle für schnelle Lösungen

---

## Recommended Environment Setup

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# Peak_Trade: Prevent pager blocking in Cursor/Terminal
export PAGER=cat
export GH_PAGER=cat
export LESS='-FRX'
```

Then reload:
```bash
source ~/.zshrc
```

---

## Files Created/Modified

### Created:
- `scripts/ops/diag_terminal_hang.sh` (executable, 147 lines)
- `docs/ops/PAGER_HOOK_HANG_TRIAGE.md` (operator runbook, ~300 lines)
- `docs/ops/TERMINAL_HANG_DIAGNOSTICS_SETUP.md` (this file)

### Modified:
- None (zero code changes, pure operator tooling)

---

## Verification

Test the diagnostic tool:
```bash
cd /Users/frnkhrz/Peak_Trade
./scripts/ops/diag_terminal_hang.sh
```

Expected output when environment is correctly set:
```
✓ Keine aktiven Pager gefunden
✓ Keine git Prozesse
✓ Keine gh Prozesse
✓ Keine pre-commit Prozesse
✓ Keine python/uv Prozesse
```

Pager environment should show:
```
PAGER=cat
GH_PAGER=cat
LESS=-FRX
```

---

## Risk Assessment

**Risk Level:** None

**Rationale:**
- Pure operator tooling (diagnostic script + docs)
- No code changes
- No runtime changes
- No dependency changes
- Shell script is read-only diagnostics (no modifications)

---

## Future Recommendations

1. **If hangs persist:**
   - Run `./scripts/ops/diag_terminal_hang.sh` to identify cause
   - Check Cursor terminal settings (restart may help)
   - Consider using external terminal (iTerm2/Terminal.app)

2. **For long-running commands:**
   - Use `screen` or `tmux` for persistence
   - Redirect output to files: `command > output.log 2>&1`
   - Monitor in background: `command > /dev/null 2>&1 &`

3. **For CI/GitHub CLI:**
   - Avoid `--watch` flags in scripts
   - Poll status instead: `while true; do gh run view $id; sleep 10; done`
   - Or use webhooks for true async notifications

---

## Related Files

- **Diagnose Tool:** `scripts/ops/diag_terminal_hang.sh`
- **Runbook:** `docs/ops/PAGER_HOOK_HANG_TRIAGE.md`
- **Pre-commit Config:** `.pre-commit-config.yaml`
- **Git Hook Wrapper:** `.git/hooks/pre-commit`

---

## Timeline

**2026-01-03:**
1. Investigated terminal hang symptoms
2. Audited Git hooks (all clean)
3. Searched for "pre-hook" strings (none found)
4. Created diagnostic tool + runbook
5. Verified environment settings (PAGER=cat, GH_PAGER=cat, LESS=-FRX)
6. Tested diagnostic script (working, no false positives)

**Status:** ✅ Complete

---

## Commands Used in Investigation

```bash
# Environment check
export GH_PAGER=cat PAGER=cat LESS='-FRX'

# Search for "pre-hook" strings
grep -RIn --fixed-string "pre-hook" ./scripts ./src ./tests ./docs

# List executable hooks
find .git/hooks -maxdepth 1 -type f -perm -111

# Analyze pre-commit hook
cat .git/hooks/pre-commit
pre-commit --version
cat .pre-commit-config.yaml

# Trace Git hook execution
GIT_TRACE=1 GIT_TRACE_PERFORMANCE=1 git commit --allow-empty -m "test"
```

All investigations completed successfully with no issues found.
