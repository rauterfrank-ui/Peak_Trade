# Cursor Timeout & Hang Triage Runbook

**Ziel:** Schnelle Diagnose und Behebung von Cursor UI/Terminal-Hängern ohne Datenverlust.  
**Zielgruppe:** Operator (lokale macOS-Entwicklung)  
**Ausführungszeit:** 2–5 Minuten  
**Repo:** Peak_Trade

---

## Symptome

Cursor zeigt eines oder mehrere dieser Verhalten:

1. **UI Freeze** – Editor reagiert nicht, Menüs öffnen langsam/gar nicht
2. **Terminal blockiert** – Eingabe wird nicht verarbeitet, keine Response auf Ctrl-C
3. **Extension Host CPU** – Extension Host Process dauerhaft >80% CPU
4. **Filewatcher/Indexing** – `fileWatcher`, `gitWorker`, `pyright` dauerhaft aktiv
5. **Network-Timeout** – gh-CLI oder pytest-watch laufen "ewig"
6. **Prompt Continuation** – Shell zeigt `>` oder `dquote>` statt normalem Prompt

---

## Pre-Flight: Prompt-Continuation-Check

**Bevor** du Diagnose startest:

```bash
# Wenn dein Prompt so aussieht:
# >
# dquote>
# heredoc>

# → Du befindest dich in einer unvollständigen Shell-Eingabe!
# → NICHT CURSOR KILLEN, sondern:

# 1. Drücke Ctrl-C (mehrfach, falls nötig)
# 2. Wenn Ctrl-C nicht hilft: Ctrl-D (EOF)
# 3. Falls immer noch hängend: Terminal-Tab schließen (nicht ganzer Cursor!)
```

**Wenn normaler Prompt sichtbar ist** → weiter mit Diagnose.

---

## Diagnose

### Repo-Status

```bash
# 1. Check Working Directory
pwd
# Expected: /Users/<user>/Peak_Trade

# 2. Check Git State
git rev-parse --abbrev-ref HEAD
git status -sb
# Expected: wip/cursor-timeout-triage-20260102, clean oder bekannte WIP
```

### Prozess-Analyse

**Automatisch:**
```bash
./scripts/ops/triage_cursor_hang.sh
```

**Manuell:**
```bash
# Cursor-relevante Prozesse (CPU/Memory/PID)
ps aux | grep -E "(Cursor|extension-host|pty-host|fileWatcher|gitWorker|pyright)" | grep -v grep

# Netzwerk-Verbindungen (Top 50)
lsof -iTCP -sTCP:ESTABLISHED | head -50

# Speziell: Extension Host
ps aux | grep extension-host | grep -v grep
```

**Interpretation:**
- CPU >80% dauerhaft → Runaway Process (Extension/Language Server)
- Viele ESTABLISHED Connections → Netzwerk-Timeout oder Polling-Storm
- Mehrere `extension-host` Prozesse → Potentieller Memory-Leak

---

## Soft Fixes (in Cursor)

**Diese Schritte ändern NICHTS am Repo-State.**

### 1. Developer: Reload Window

```
Cmd+Shift+P → "Developer: Reload Window"
```

**Wann:** UI-Freeze ohne CPU-Spike  
**Effekt:** Reloaded Extension Host, behält offene Dateien  
**Dauer:** 5–10 Sekunden

### 2. Extension Isolation

```
1. Cmd+Shift+P → "Extensions: Disable All Installed Extensions"
2. Cmd+Shift+P → "Developer: Reload Window"
3. Teste, ob Problem weg ist
4. Re-enable Extensions einzeln (Start mit: Python, GitLens, etc.)
5. Nach jedem Enable: Reload + Test
```

**Wann:** Extension Host CPU-Spike  
**Effekt:** Identifiziert problematische Extension  
**Dauer:** 2–5 Minuten (je nach Anzahl Extensions)

### 3. Disable File Watchers (temporär)

```
Cmd+, (Settings) → Suche "files.watcherExclude"
→ Füge temporär hinzu:
  "**/venv/**": true
  "**/.venv/**": true
  "**/node_modules/**": true
  "**/.git/**": true
```

**Wann:** `fileWatcher` dauerhaft aktiv, große Repos  
**Effekt:** Reduziert File-System-Polling  
**Dauer:** Sofort wirksam

---

## Targeted Reset (Mild)

**Extension Host beenden, OHNE Cursor komplett zu killen.**

```bash
# 1. Find Extension Host PID(s)
ps aux | grep extension-host | grep -v grep | awk '{print $2}'

# 2. Soft Terminate (SIGTERM, nicht SIGKILL)
kill -TERM <PID>

# 3. Cursor restartet Extension Host automatisch
# 4. Verify
ps aux | grep extension-host | grep -v grep
```

**Wann:** Extension Host hängt, UI sonst reaktiv  
**Effekt:** Extension Host Restart, keine Cursor-App-Restart  
**Dauer:** 2–5 Sekunden

**Automatisch (mit Skript):**
```bash
SOFT_RESET_EXTENSION_HOST=1 ./scripts/ops/triage_cursor_hang.sh
```

---

## Evidence Pack

**Wenn du einen Issue/Chat-Post erstellst, sammle:**

1. **Symptom-Beschreibung** (UI Freeze / Terminal blockiert / CPU Spike)
2. **Prozess-Output**
   ```bash
   ./scripts/ops/triage_cursor_hang.sh > /tmp/cursor_triage_$(date +%Y%m%d_%H%M%S).txt
   ```
3. **Git State**
   ```bash
   git rev-parse HEAD
   git status -sb
   git log --oneline -5
   ```
4. **Logs** (siehe unten)
5. **Reproduzierbarkeit** (immer / nach X Minuten / bei bestimmter Aktion)

---

## Logs

### Standard-Pfad (macOS)

```bash
~/Library/Application Support/Cursor/logs/
```

### Neueste Session identifizieren

```bash
ls -1t ~/Library/Application\ Support/Cursor/logs/ | head -1
```

### Relevante Log-Dateien

```
main.log              # Cursor App Main Process
renderer.log          # UI/Renderer Process
extensionHost.log     # Extension Host (Python, GitLens, etc.)
ptyhost.log           # Terminal/PTY
```

### Logs sammeln (automatisch)

```bash
./scripts/ops/collect_cursor_logs.sh
# Output: /tmp/cursor_logs_YYYYMMDD_HHMMSS.zip
```

---

## Escalation

**Wann Issue/Chat eskalieren:**

1. **Soft Fixes helfen nicht** → Systematisches Problem
2. **Reproduzierbar** → Nicht zufällig/transienter Fehler
3. **Daten/Artefakte gesammelt** → Evidence Pack vollständig
4. **Kein User-Error** → Pre-Flight-Check durchgeführt

**Was posten:**
- Symptom-Beschreibung (siehe Evidence Pack)
- Triage-Output (`triage_cursor_hang.sh`)
- Log-Sammlung (`collect_cursor_logs.sh`)
- Git-State (Branch, HEAD, Status)
- Cursor-Version (`Cmd+Shift+P → "About"`)
- macOS-Version (`sw_vers`)

**Wo posten:**
- **Cursor-spezifisch:** https://github.com/getcursor/cursor/issues
- **Internal Peak_Trade:** Docs-Issue oder Chat (wenn Repo-spezifisch)

---

## Quick Reference

| Symptom                  | Erste Aktion                                | Dauer      |
|--------------------------|---------------------------------------------|------------|
| UI Freeze                | Developer: Reload Window                    | 10 Sekunden|
| Terminal blockiert       | Ctrl-C (mehrfach), dann Ctrl-D              | Sofort     |
| Extension Host CPU       | Extension Isolation Workflow                | 2–5 Min    |
| Filewatcher dauerhaft    | Disable File Watchers (Settings)            | Sofort     |
| Network-Timeout          | Check lsof, dann gh auth status             | 1 Min      |
| Prompt Continuation (>)  | Ctrl-C (NICHT Cursor killen!)               | Sofort     |

---

## Related

- `scripts/ops/triage_cursor_hang.sh` — Automatische Diagnose
- `scripts/ops/collect_cursor_logs.sh` — Log-Sammlung
- `docs/ops/OPS_OPERATOR_CENTER.md` — Operator-Zentrum
- `docs/ops/CLAUDE_CODE_AUTH_RUNBOOK.md` — gh auth Troubleshooting
