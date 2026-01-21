# Pager & Hook Hang Triage

**Status:** Operator Runbook  
**Context:** Cursor Terminal macOS (Peak_Trade)  
**Created:** 2026-01-03

---

## Problem Statement

In Cursor/Terminal können gefühlte "Hänger" auftreten, die keine echten Freezes sind, sondern auf Pager-Blocking, Watch-Befehle oder Hook-Ausführung zurückzuführen sind.

### Typische Symptome
- Terminal zeigt keine neue Prompt
- Cursor blinkt nicht / reagiert nicht sofort
- Kein Output, aber auch kein Fehler
- Prompt zeigt `>`, `dquote>`, oder `quote>` (heredoc/quote nicht geschlossen)

---

## Quick Diagnosis Tool

```bash
scripts/ops/diag_terminal_hang.sh
```

Zeigt:
- Environment Variablen (PAGER, GH_PAGER, LESS)
- Aktive Pager/Git/gh/pre-commit Prozesse
- Diagnose-Checkliste mit Quick Actions

---

## Diagnose-Checkliste

### 1. Pager wartet auf Eingabe (less/more)

**Identifizieren:**
```bash
pgrep -fl 'less|more'
```

**Symptome:**
- Terminal "steht", keine Ausgabe
- Keine neue Prompt
- Kein CPU-Load (top/Activity Monitor)

**Lösung:**
```bash
# Im hängenden Terminal:
q          # Quit less/more
Ctrl-C     # Force quit

# In anderem Terminal:
killall less
```

**Prevention:**
```bash
# In Shell-Profil oder vor kritischen Commands:
export PAGER=cat
export GH_PAGER=cat
export LESS='-FRX'  # -F: quit if one screen, -R: raw colors, -X: no init
```

---

### 2. gh watch / gh pr checks --watch blockiert

**Identifizieren:**
```bash
pgrep -fl 'gh'
ps aux | grep 'gh.*watch'
```

**Symptome:**
- Terminal zeigt periodische Updates (alle 3-10 Sekunden)
- "Refreshing..." oder ähnliche Meldungen
- Cursor blinkt zwischen Updates

**Lösung:**
```bash
Ctrl-C  # Stoppt watch loop
```

**Prevention:**
```bash
# Vermeide --watch flags:
gh pr checks          # statt gh pr checks --watch
gh run view <id>      # statt gh run watch <id>

# Oder: Setze GH_PAGER=cat (siehe oben)
```

---

### 3. pre-commit hook läuft lange

**Identifizieren:**
```bash
pgrep -fl 'pre.?commit|pre_commit'
ps aux | grep python | grep pre_commit
```

**Symptome:**
- Nach `git commit`, keine neue Prompt
- Möglicherweise Output wie "checking yaml...", "ruff check..."
- CPU-Load durch Python-Prozesse

**Lösung:**
```bash
# Warten (wenn Hook legitim lange läuft)
# ODER:
Ctrl-C  # Commit wird abgebrochen!
```

**Debug:**
```bash
# Hook mit Trace ausführen:
GIT_TRACE=1 GIT_TRACE_PERFORMANCE=1 git commit -m "test"

# Hook-Konfiguration prüfen:
cat .pre-commit-config.yaml

# Hook-Performance testen (empty commit):
time git commit --allow-empty -m "perf test"
```

**Prevention:**
```bash
# Pre-commit temporär skippen (nur wenn notwendig!):
git commit --no-verify -m "..."

# Oder: Einzelne Hooks deaktivieren via SKIP:
SKIP=ruff-check git commit -m "..."
```

---

### 4. Heredoc/Quote nicht geschlossen

**Identifizieren:**
```bash
# Prompt zeigt:
>           # heredoc oder multi-line command
dquote>     # offene "
quote>      # offene '
```

**Symptome:**
- Jede neue Zeile zeigt nur `>` oder `dquote>`
- Keine Command-Ausführung
- Enter erzeugt nur neue Zeile

**Lösung:**
```bash
Ctrl-C  # Bricht gesamten Command ab
# Dann: Command neu schreiben, Quote/Heredoc korrekt schließen
```

**Prevention:**
```bash
# Vor komplexen Commands mit Heredocs:
echo "Ctrl-C falls du in '>'/'dquote>'/heredoc hängst."

# Quotes/Heredocs in Variablen testen:
cat << 'EOF' > /tmp/test.sh
...
EOF
bash /tmp/test.sh  # Teste erst, bevor du direkt im Terminal tippst
```

---

### 5. Background Job blockiert Terminal

**Identifizieren:**
```bash
jobs -l
ps -j
```

**Symptome:**
- Terminal scheint zu hängen
- Background Job versucht stdin zu lesen
- Meldung: `[1]+ Stopped ...`

**Lösung:**
```bash
jobs -l               # Zeige Background Jobs
fg                    # Bring to foreground
Ctrl-C                # Kill foreground job

# Oder direkt killen:
kill %1               # Kill job #1
kill -9 <PID>         # Force kill
```

**Prevention:**
```bash
# Long-running Commands als Background Job:
./long_script.sh > output.log 2>&1 &

# Oder in Screen/Tmux:
tmux new -s work
# Detach: Ctrl-b d
# Reattach: tmux attach -t work
```

---

## Environment Setup (Empfohlen)

Füge in `~/.zshrc` oder `~/.bashrc` hinzu:

```bash
# Peak_Trade: Prevent pager blocking in Cursor/Terminal
export PAGER=cat
export GH_PAGER=cat
export LESS='-FRX'
export GIT_PAGER='less -FRX'  # Optional: Git-spezifisch

# Oder: Falls du less behalten willst, aber nur für Git:
# git config --global core.pager 'less -FRX'
```

**Nach Änderung:**
```bash
source ~/.zshrc
# Oder: Terminal neu starten
```

---

## Verification

Test, ob Pager korrekt deaktiviert ist:

```bash
# Diese sollten NICHT in less/more hängen:
gh pr list
git log --oneline -20
git diff HEAD~5
cat large_file.log

# Wenn output direkt erscheint (kein ":" am unteren Rand): ✅
# Wenn less startet (unterste Zeile zeigt ":"): ❌ (q drücken)
```

---

## Git Hooks Status (Stand 2026-01-03)

**Aktive Hooks:**
- `.git/hooks/pre-commit` (pre-commit framework wrapper, ~20 Zeilen)
  - Ruft: `.venv&#47;bin&#47;python3 -m pre_commit`
  - Config: `.pre-commit-config.yaml`
  - Hooks: end-of-file-fixer, trailing-whitespace, ruff-check, etc.

**Sample Hooks (inaktiv):**
- `*.sample` Dateien in `.git/hooks/` (Standard Git samples)

**Keine verdächtigen Hooks:**
- Kein "pre-hook" String gefunden
- Keine endlosen Loops
- Keine externen Script-Aufrufe außer pre-commit framework

---

## Quick Actions Reference

| Symptom | Quick Fix | Command |
|---------|-----------|---------|
| Pager wartet | Quit | `q` |
| Prozess läuft | Kill | `Ctrl-C` |
| Heredoc offen | Abort | `Ctrl-C` |
| Background Job | Foreground | `fg` dann `Ctrl-C` |
| Terminal tot | Restart | Cursor: Terminal → Kill Terminal |

---

## Related

- **Diagnose Tool:** `scripts/ops/diag_terminal_hang.sh`
- **Pre-commit Config:** `.pre-commit-config.yaml`
- **Git Hook Wrapper:** `.git/hooks/pre-commit`

---

## Investigation History

**2026-01-03:** Initial triage
- Untersuchte Git-Hooks: Nur pre-commit aktiv, unverdächtig
- Pager-Environment dokumentiert
- Diagnose-Tool erstellt
- Empfehlung: `PAGER=cat`, `GH_PAGER=cat`, `LESS='-FRX'`
