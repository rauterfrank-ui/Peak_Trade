#!/usr/bin/env bash
# Peak_Trade: Terminal Hang Diagnostics
# Hilft bei der Triage von gefühlten "Hängern" in Cursor/Terminal
# Usage: ./scripts/ops/diag_terminal_hang.sh

set -euo pipefail

echo "=========================================="
echo "Terminal Hang Diagnostics (Peak_Trade)"
echo "=========================================="
echo

# 1) Environment Check
echo "== 1) Pager Environment =="
echo "PAGER=${PAGER:-<not set>}"
echo "GH_PAGER=${GH_PAGER:-<not set>}"
echo "LESS=${LESS:-<not set>}"
echo "GIT_PAGER=${GIT_PAGER:-<not set>}"
echo

# 2) Active Pager Processes
echo "== 2) Active Pager Processes =="
PAGER_PROCS=$(pgrep -fl '(^|/)less |(/|^)more |(/|^)bat ' 2>/dev/null || true)
if [ -n "$PAGER_PROCS" ]; then
    echo "⚠️  PAGER DETECTED - möglicherweise wartet 'less' auf Eingabe!"
    echo "$PAGER_PROCS" | sed 's/^/  /'
    echo "   → Drücke 'q' um zu beenden"
    echo "   → oder Ctrl-C für Abbruch"
else
    echo "✓ Keine aktiven Pager gefunden"
fi
echo

# 3) Git/GitHub CLI Processes
echo "== 3) Git & GitHub CLI Processes =="
GIT_PROCS=$(pgrep -fl '(^|/)git ' 2>/dev/null | grep -v 'git@' || true)
if [ -n "$GIT_PROCS" ]; then
    echo "Git processes:"
    echo "$GIT_PROCS" | sed 's/^/  /'
else
    echo "✓ Keine git Prozesse"
fi

GH_PROCS=$(pgrep -fl '(^|/)gh ' 2>/dev/null || true)
if [ -n "$GH_PROCS" ]; then
    echo "gh processes:"
    echo "$GH_PROCS" | sed 's/^/  /'
    echo "⚠️  'gh watch' oder 'gh pr checks --watch' blockiert möglicherweise"
    echo "   → Drücke Ctrl-C um zu stoppen"
else
    echo "✓ Keine gh Prozesse"
fi
echo

# 4) Pre-commit / Python Processes
echo "== 4) Pre-commit & Python Processes =="
PC_PROCS=$(pgrep -fl 'pre.?commit|pre_commit' 2>/dev/null || true)
if [ -n "$PC_PROCS" ]; then
    echo "Pre-commit processes:"
    echo "$PC_PROCS" | sed 's/^/  /'
    echo "⚠️  Pre-commit hook läuft noch"
else
    echo "✓ Keine pre-commit Prozesse"
fi

PY_PROCS=$(pgrep -fl 'python|uv' 2>/dev/null | grep -v "$(basename "$0")" || true)
if [ -n "$PY_PROCS" ]; then
    echo "Python/uv processes:"
    echo "$PY_PROCS" | sed 's/^/  /' | head -10
else
    echo "✓ Keine python/uv Prozesse"
fi
echo

# 5) Terminal File Descriptors (stdin/stdout blocking?)
echo "== 5) Current Shell Info =="
echo "Shell PID: $$"
echo "Shell: $SHELL"
echo "TTY: $(tty 2>/dev/null || echo '<no tty>')"
if command -v lsof >/dev/null 2>&1; then
    echo "Open FDs for this shell:"
    lsof -p $$ 2>/dev/null | grep -E '(CHR|PIPE|REG)' | head -5 || echo "  (lsof failed)"
fi
echo

# 6) Recommendations
echo "=========================================="
echo "== Diagnose-Checkliste =="
echo "=========================================="
echo
echo "Häufige Ursachen für 'Terminal hängt':"
echo
echo "1) PAGER wartet auf Eingabe (less/more)"
echo "   Symptom: Keine neue Prompt, aber kein CPU-Load"
echo "   Lösung: 'q' drücken oder Ctrl-C"
echo "   Prevention: export PAGER=cat GH_PAGER=cat LESS='-FRX'"
echo
echo "2) gh watch / gh pr checks --watch blockiert"
echo "   Symptom: Terminal zeigt Live-Updates alle paar Sekunden"
echo "   Lösung: Ctrl-C"
echo "   Prevention: Keine --watch flags verwenden"
echo
echo "3) pre-commit hook läuft lange"
echo "   Symptom: Nach 'git commit', keine neue Prompt"
echo "   Check: Siehe 'Pre-commit processes' oben"
echo "   Lösung: Warten oder Ctrl-C (commit wird abgebrochen)"
echo "   Debug: GIT_TRACE=1 git commit --allow-empty -m test"
echo
echo "4) Heredoc/Quote nicht geschlossen"
echo "   Symptom: Prompt zeigt '>' oder 'dquote>' oder 'quote>'"
echo "   Lösung: Ctrl-C und Command neu schreiben"
echo
echo "5) Background Job blockiert Terminal"
echo "   Check: jobs -l"
echo "   Lösung: fg (bring to foreground) dann Ctrl-C"
echo
echo "=========================================="
echo "Quick Actions:"
echo "  - Pager beenden: q"
echo "  - Prozess abbrechen: Ctrl-C"
echo "  - Background Jobs: jobs -l"
echo "  - Prozesse killen: killall less"
echo "  - In Cursor: Terminal neu starten (Mülleimer-Icon)"
echo "=========================================="
