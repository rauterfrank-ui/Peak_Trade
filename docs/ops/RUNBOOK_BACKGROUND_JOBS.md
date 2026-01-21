# Runbook — Background Jobs (Cursor Timeout Workaround)

## Zweck
Cursor-Terminal-Ausführungen können bei Long-Runs (Full Scans, lange Tests, Watches) in Timeouts laufen.  
Dieses Repo-Tool startet solche Befehle als Background-Job mit Logging, PID und Exitcode.

## Tool
Script: `scripts/ops/bg_job.sh`  
Artefakte: `<repo>&#47;.logs&#47;`

Erzeugte Dateien pro Run (Label + Timestamp):
- `.logs&#47;<label>_<ts>.log` — stdout/stderr
- `.logs&#47;<label>_<ts>.pid` — PID
- `.logs&#47;<label>_<ts>.exit` — Exitcode (nach Ende)
- `.logs&#47;<label>_<ts>.meta` — Metadaten (cmd, git sha/branch, pgid)
- `.logs&#47;jobs&#47;<label>_<ts>.sh` — Ausführbares Job-Script (wiederholbar)

## Quick Commands

### Start Job
```bash
bash scripts/ops/bg_job.sh run <label> -- <command>
```

### Follow Log (Live)
```bash
bash scripts/ops/bg_job.sh follow <label>
# Ctrl+C beendet nur die Anzeige, Job läuft weiter!
```

### Check Status
```bash
bash scripts/ops/bg_job.sh status <label>
```

### Stop Job
```bash
bash scripts/ops/bg_job.sh stop <label>
```

### List Jobs
```bash
bash scripts/ops/bg_job.sh list <label>
```

### Get Latest Log Path
```bash
bash scripts/ops/bg_job.sh latest <label>
```

---

## Beispiele

### A) Docs Reference Targets (Full Scan)
```bash
# Start
bash scripts/ops/bg_job.sh run docs_refs_full -- ./scripts/ops/verify_docs_reference_targets.sh

# Follow
bash scripts/ops/bg_job.sh follow docs_refs_full

# Status
bash scripts/ops/bg_job.sh status docs_refs_full

# Exit-Code nach Fertigstellung
cat "$(ls -t .logs/docs_refs_full_*.exit | head -1)"

# Stop (bei Bedarf)
bash scripts/ops/bg_job.sh stop docs_refs_full
```

**Erwartetes Ergebnis:**
- Scannt 593+ MD-Dateien ohne Timeout
- Findet 4000+ Referenzen
- Exit-Code: 0 = keine Missing Targets, 1 = Missing Targets gefunden

### B) Tests (Full Suite)
```bash
# Start
bash scripts/ops/bg_job.sh run pytest_full -- pytest tests/ -v

# Follow
bash scripts/ops/bg_job.sh follow pytest_full

# Status
bash scripts/ops/bg_job.sh status pytest_full

# Nach Fertigstellung - Failures suchen
grep "FAILED" "$(bash scripts/ops/bg_job.sh latest pytest_full)"

# Zusammenfassung
tail -50 "$(bash scripts/ops/bg_job.sh latest pytest_full)" | grep -A 20 "==="
```

### C) PR Checks Watch
```bash
# Start (läuft indefinitely)
bash scripts/ops/bg_job.sh run pr_watch_485 -- gh pr checks 485 --watch

# Follow
bash scripts/ops/bg_job.sh follow pr_watch_485

# Stop wenn alle Checks grün
bash scripts/ops/bg_job.sh stop pr_watch_485

# Finales Ergebnis
tail -50 "$(bash scripts/ops/bg_job.sh latest pr_watch_485)"
```

### D) Backtest
```bash
bash scripts/ops/bg_job.sh run backtest_ma -- python scripts/run_backtest.py --strategy ma_crossover --days 365
bash scripts/ops/bg_job.sh follow backtest_ma
```

### E) Parallele Jobs
```bash
# Mehrere Jobs gleichzeitig starten
bash scripts/ops/bg_job.sh run tests_unit -- pytest tests/unit/ -v
bash scripts/ops/bg_job.sh run tests_integration -- pytest tests/integration/ -v
bash scripts/ops/bg_job.sh run docs_check -- ./scripts/ops/verify_docs_reference_targets.sh

# Status aller Jobs
for label in tests_unit tests_integration docs_check; do
  echo "=== $label ==="
  bash scripts/ops/bg_job.sh status "$label" 2>/dev/null || echo "Not started"
  echo
done

# Verschiedene Logs in verschiedenen Terminals verfolgen
bash scripts/ops/bg_job.sh follow tests_unit      # Terminal 1
bash scripts/ops/bg_job.sh follow tests_integration  # Terminal 2
bash scripts/ops/bg_job.sh follow docs_check      # Terminal 3
```

---

## Features

### Automatic Enhancements
- ✅ **caffeinate** - Mac bleibt wach während der Job läuft (nur macOS)
- ✅ **venv auto-detection** - Aktiviert automatisch `venv/` oder `.venv/`
- ✅ **Exit-code capture** - Sauberer Exit-Code auch bei Ctrl+C
- ✅ **Process group kill** - Stoppt auch Child-Prozesse sauber
- ✅ **Git metadata** - Tracked git sha/branch für Reproduzierbarkeit
- ✅ **PYTHONUNBUFFERED=1** - Sofortiges Logging ohne Buffer
- ✅ **GH_PAGER=cat, GIT_PAGER=cat** - Keine interaktiven Pager

### Environment Variables
Der Job-Runner setzt automatisch:
```bash
export PYTHONUNBUFFERED=1
export GH_PAGER=cat
export GIT_PAGER=cat
```

---

## Verifikation (nach dem Einbau)

**Einsatzort:** Cursor Terminal.

1) Full-Scan als Job starten:
```bash
bash scripts/ops/bg_job.sh run docs_refs_full -- ./scripts/ops/verify_docs_reference_targets.sh
```

2) Log live verfolgen (Ctrl+C zum Abbrechen der Anzeige, Job läuft weiter):
```bash
bash scripts/ops/bg_job.sh follow docs_refs_full
```

3) Status prüfen:
```bash
bash scripts/ops/bg_job.sh status docs_refs_full
```

**Erwartetes Ergebnis:**
- Status zeigt `RUNNING` während der Job läuft
- Nach Fertigstellung: `NOT RUNNING` mit `EXITCODE 0` oder `1`
- Log zeigt "Docs Reference Targets: scanned X md file(s)..."

4) Exit-Code nach Fertigstellung:
```bash
cat "$(ls -t .logs/docs_refs_full_*.exit | head -1)"
# Erwartung: 0 (keine Missing) oder 1 (Missing Targets gefunden)
```

5) Metadaten prüfen:
```bash
cat "$(ls -t .logs/docs_refs_full_*.meta | head -1)"
# Zeigt: ts, label, repo_dir, shell, venv, cmd, git_sha, git_branch, pgid
```

**Erfolg:** Job läuft ohne Timeout durch, alle Artefakte (.log/.pid/.exit/.meta) werden korrekt angelegt.

---

## Troubleshooting

### Job läuft nicht mehr, aber kein Exit-Code
Prozess wurde manuell gekillt oder crashed. Check Log:
```bash
cat "$(bash scripts/ops/bg_job.sh latest <label>)"
tail -50 "$(bash scripts/ops/bg_job.sh latest <label>)"
```

### Stop funktioniert nicht
Force-kill mit PID:
```bash
kill -9 "$(cat .logs/<label>_*.pid | tail -1)"
```

Oder mit PGID (killt auch Child-Prozesse):
```bash
# PGID aus Meta-File holen
PGID=$(grep "^pgid=" "$(ls -t .logs/<label>_*.meta | head -1)" | cut -d= -f2)
kill -9 -"$PGID"
```

### Alte Logs aufräumen
```bash
# Logs älter als 7 Tage löschen
find .logs -name "*.log" -mtime +7 -delete
find .logs -name "*.pid" -mtime +7 -delete
find .logs -name "*.exit" -mtime +7 -delete
find .logs -name "*.meta" -mtime +7 -delete
find .logs/jobs -name "*.sh" -mtime +7 -delete
```

### caffeinate nicht verfügbar (Linux/Windows)
Das Script erkennt automatisch, ob `caffeinate` verfügbar ist. Auf nicht-macOS-Systemen läuft der Job ohne caffeinate (funktioniert trotzdem, aber System kann einschlafen).

### "No log found for label=X"
Job wurde noch nie gestartet oder Label falsch geschrieben. Check:
```bash
ls -lth .logs/*.log
```

---

## Aliases (Optional)

Für häufige Nutzung in `~/.zshrc` oder `~/.bashrc`:

```bash
# Absolute Pfade - funktionieren von überall
alias bgrun='bash ~/Peak_Trade/scripts/ops/bg_job.sh run'
alias bgfollow='bash ~/Peak_Trade/scripts/ops/bg_job.sh follow'
alias bgstatus='bash ~/Peak_Trade/scripts/ops/bg_job.sh status'
alias bgstop='bash ~/Peak_Trade/scripts/ops/bg_job.sh stop'
alias bglist='bash ~/Peak_Trade/scripts/ops/bg_job.sh list'
alias bglatest='bash ~/Peak_Trade/scripts/ops/bg_job.sh latest'

# Dann einfach:
bgrun docs_refs_full -- ./scripts/ops/verify_docs_reference_targets.sh
bgfollow docs_refs_full
bgstatus docs_refs_full
```

---

## Architektur

### Job-Lifecycle
1. **Start:** `bg_job.sh run` erstellt Job-Script + Meta-File, startet mit `nohup`
2. **Running:** Job läuft detached, schreibt in Log-File, PID/PGID werden getrackt
3. **Completion:** `trap EXIT` schreibt Exit-Code in `.exit` File
4. **Cleanup:** Optional mit `find ... -mtime +N -delete`

### File Layout
```
.logs/
  ├── <label>_<timestamp>.log      # stdout/stderr
  ├── <label>_<timestamp>.pid      # Process ID
  ├── <label>_<timestamp>.exit     # Exit code (nach Job-Ende)
  ├── <label>_<timestamp>.meta     # Metadata (git, cmd, env)
  └── jobs/
      └── <label>_<timestamp>.sh   # Ausführbares Job-Script (wiederholbar)
```

### Safety Features
- `set -euo pipefail` - Fail-fast bei Fehlern
- `trap EXIT` - Exit-Code wird immer captured
- Process Group Tracking (PGID) - Sauberes Cleanup auch bei Child-Prozessen
- Label Validation - Nur alphanumerische Zeichen + `.` `-` `_`

---

## Related

- `scripts/ops/bg_job.sh` - Tool implementation
- `.logs/` - Artefakte (in `.gitignore`)
- `docs/ops/README.md` - Ops tools overview

---

## Changelog

**2026-01-01** - Initial version
- Core functionality: run, follow, status, stop, list, latest
- Auto-detection: venv, caffeinate, shell
- Metadata tracking: git sha/branch, cmd, env
- Process group kill support
