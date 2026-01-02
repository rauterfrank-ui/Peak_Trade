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

**Cursor Process Snapshot (No-Sudo):**
```bash
echo "=== Cursor Processes (CPU/Memory) ==="
ps aux | grep -E "(Cursor|cursor|extension-host|pty-host|fileWatcher|gitWorker|pyright)" | grep -v grep || true

echo
echo "=== Extension Host Detail ==="
ps aux | grep -E "extension-host" | grep -v grep || true

echo
echo "=== Network Connections (best-effort) ==="
lsof -iTCP -sTCP:ESTABLISHED 2>/dev/null | grep -i -E "cursor|Cursor" | head -n 30 || true

echo
echo "=== System Load ==="
uptime || true
vm_stat | head -n 10 || true

echo
echo "=== Shell Continuation Check ==="
echo "If your prompt shows >, dquote>, or heredoc>, press Ctrl-C before running other commands."
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

---

## Evidence Pack

**Wenn du einen Issue/Chat-Post erstellst, sammle:**

1. **Symptom-Beschreibung** (UI Freeze / Terminal blockiert / CPU Spike)
2. **Prozess-Output** (siehe "Prozess-Analyse" Sektion oben, Output in Datei speichern):
   ```bash
   # Speichere Diagnose in Datei
   {
     echo "=== Cursor Processes (CPU/Memory) ==="
     ps aux | grep -E "(Cursor|cursor|extension-host|pty-host|fileWatcher|gitWorker|pyright)" | grep -v grep || true
     echo
     echo "=== Extension Host Detail ==="
     ps aux | grep -E "extension-host" | grep -v grep || true
     echo
     echo "=== Network Connections (best-effort) ==="
     lsof -iTCP -sTCP:ESTABLISHED 2>/dev/null | grep -i -E "cursor|Cursor" | head -n 30 || true
     echo
     echo "=== System Load ==="
     uptime || true
     vm_stat | head -n 10 || true
   } > /tmp/cursor_triage_$(date +%Y%m%d_%H%M%S).txt
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
# Output: ./artifacts/cursor_logs_YYYYMMDD_HHMMSS.tgz (default)
# Optional: Specify custom output directory as first argument
# ./scripts/ops/collect_cursor_logs.sh /tmp/my_logs
```

---

## Advanced Diagnostics (macOS)

**Wann verwenden:** UI komplett eingefroren, Extension Host hängt dauerhaft, normales Troubleshooting hilft nicht.

**⚠️ Hinweise:**
- Alle Commands erfordern `sudo` (Admin-Rechte)
- macOS kann Security-Prompt zeigen ("System Events wants to access...")
- `spindump` ist LANGSAM (5-10 Sekunden Freeze während Capture)
- Nur verwenden, wenn du den Output für Bug-Report brauchst

### Process Sampling (Profiling)

**Step-by-Step:**

```bash
# 1) Find PID (example: extension-host)
ps aux | grep -E "extension-host|Cursor" | grep -v grep

# 2) SAMPLE (10 seconds, non-invasive)
PID="<PUT_PID_HERE>"
sudo sample "$PID" 10 -file "/tmp/cursor_hang_sample_$(date +%Y%m%d_%H%M%S).txt"
```

**Wann:** Extension Host zeigt dauerhaft hohe CPU, aber UI noch teilweise reaktiv  
**Output:** Call Stack Profiling (zeigt, wo der Code "stuck" ist)

### Spindump (System-weiter Hang)

```bash
# 3) SPINDUMP (use if UI is fully frozen; may take time)
sudo spindump "Cursor" -o "/tmp/cursor_spindump_$(date +%Y%m%d_%H%M%S).txt"
```

**Wann:** Kompletter UI-Freeze, keine Interaktion mehr möglich  
**⚠️ Warning:** Verursacht 5-10 Sekunden zusätzlichen Freeze während Capture  
**Output:** System-weite Stack Traces aller Cursor-Prozesse

### File System Activity

```bash
# 4) FS_USAGE (file system activity; useful for file-watcher suspicion)
sudo fs_usage -f filesys "Cursor" | head -n 200 > "/tmp/cursor_fsusage_$(date +%Y%m%d_%H%M%S).txt"
# Drücke Ctrl-C nach ca. 10 Sekunden
```

**Wann:** Verdacht auf Filewatcher-Loop oder excessive File I/O  
**Output:** Real-time File System Calls (zeigt, welche Dateien/Dirs Cursor liest/schreibt)

### Network Activity

```bash
# Cursor Network Connections (keine sudo nötig, aber detaillierter)
sudo lsof -iTCP -sTCP:ESTABLISHED | grep -i cursor
```

**Wann:** Verdacht auf Network-Timeout oder Polling-Storm  
**Output:** Alle offenen TCP-Verbindungen von Cursor

---

## Escalation

**Wann Issue/Chat eskalieren:**

1. **Soft Fixes helfen nicht** → Systematisches Problem
2. **Reproduzierbar** → Nicht zufällig/transienter Fehler
3. **Daten/Artefakte gesammelt** → Evidence Pack vollständig
4. **Kein User-Error** → Pre-Flight-Check durchgeführt

**Was posten:**
- Symptom-Beschreibung (siehe Evidence Pack)
- Prozess-Snapshot (siehe "Prozess-Analyse" oder "Evidence Pack" Sektionen)
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

- `scripts/ops/collect_cursor_logs.sh` — Log-Sammlung
- `docs/ops/OPS_OPERATOR_CENTER.md` — Operator-Zentrum
- `docs/ops/CLAUDE_CODE_AUTH_RUNBOOK.md` — gh auth Troubleshooting
