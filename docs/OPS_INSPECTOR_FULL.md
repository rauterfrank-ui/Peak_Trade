# Peak_Trade Ops Inspector

## Was ist der Ops Inspector?

Der **Ops Inspector** ist Peak_Trades zentraler "Doctor"-Tool für automatisierte Health Checks der Repository-Infrastruktur. Inspiriert von `brew doctor`, führt es eine Serie von Validierungen durch, um sicherzustellen, dass das Development-Setup korrekt und funktional ist.

### Kernprinzipien

- **Zero-Network by Default**: Keine externen API-Calls im Standard-Modus
- **CI-Ready**: Klare Exit Codes und stabiler JSON Contract mit Evidence-Trail
- **Safety-First**: Checks sind read-only und verändern nichts
- **Dump-Ready**: Optional Diagnostic Bundle für Support/Debugging
- **Extensible**: Contract-basierte Architektur für zukünftige Erweiterungen

---

## Quickstart

```bash
# Standard Health Check (human-readable)
./scripts/ops/ops_doctor.sh
./scripts/ops/ops_doctor.sh doctor  # equivalent

# JSON Output für CI/Automation
./scripts/ops/ops_doctor.sh --json

# Extended Diagnostics (MVP: minimal extras)
./scripts/ops/ops_doctor.sh --full

# Diagnostic Bundle erstellen
./scripts/ops/ops_doctor.sh --dump-dir /tmp/peak_trade_debug

# Hilfe anzeigen
./scripts/ops/ops_doctor.sh --help
```

---

## Exit Codes

Der Ops Inspector kommuniziert seinen Status über standardisierte Exit Codes:

| Code | Status | Bedeutung | Aktion |
|------|--------|-----------|--------|
| `0` | **HEALTHY** | Alle Checks erfolgreich | Keine Aktion erforderlich |
| `1` | **DEGRADED** | Warnings vorhanden, System funktional | Review empfohlen |
| `2` | **FAILED** | Kritische Probleme gefunden | Sofortige Behebung erforderlich |

### Verwendung in CI

```yaml
# GitHub Actions Beispiel
- name: Run Ops Inspector
  run: ./scripts/ops/ops_doctor.sh --json
  # Fails CI bei exit code 2, warnt bei exit code 1
```

---

## Durchgeführte Checks

### 1. Git Repository Root (A)

**Check ID**: `git_root`

- ✓ Findet Git-Root ausgehend von Script-Location
- ✓ Wechselt automatisch in Repository-Root (`cd`)
- ✓ Validiert Repository-Namen (`Peak_Trade` erwartet)
- ✗ **FAIL** wenn kein Git-Repository gefunden

**Evidence**: `repo_path`, `repo_name`

**Warum**: Alle weiteren Checks benötigen die korrekte Repository-Root.

---

### 2. Git Working Tree Status (B)

**Check ID**: `git_status`

- ✓ Führt `git status --porcelain` aus
- ⚠ **WARN** wenn uncommitted changes (dirty tree)
- ✓ **OK** wenn working tree clean

**Evidence**: `dirty_files` (Anzahl), `status`

**Warum**: Uncommitted Changes können zu unerwarteten Deployments oder verlorenen Änderungen führen.

---

### 3. Lockfiles Present (F)

**Check IDs**: `pyproject`, `uv_lock`

- ✗ **FAIL** wenn `pyproject.toml` fehlt (kritisch)
- ✗ **FAIL** wenn `uv.lock` fehlt (kritisch für Reproduzierbarkeit)

**Evidence**: Datei-Existenz

**Warum**: Ohne Lockfiles sind Builds nicht reproduzierbar, Dependencies können driften.

**Fix Hints**:
- `pyproject.toml`: Projekt-Initialisierung prüfen
- `uv.lock`: `uv sync` ausführen

---

### 4. Key Ops Scripts Presence (D)

**Check ID**: `ops_scripts`

Prüft Existenz folgender Scripts (⚠ **WARN** wenn fehlend):
- `check_run_helpers_adoption.sh`
- `knowledge_smoke_runner_auto.sh`
- `knowledge_deployment_drill_e2e.sh`
- `run_merge_log_workflow_robust.sh`
- `pr_inventory_full.sh`
- `label_merge_log_prs.sh`

**Evidence**: Liste fehlender Scripts

**Warum**: Diese Scripts sind Teil der Ops-Toolchain. Fehlende Scripts können Workflows blockieren.

---

### 5. Bash Script Syntax (E)

**Check ID**: `script_syntax`

- ✓ Scannt alle `*.sh` in `scripts/ops/`
- ✓ Scannt alle `*.sh` in `scripts/workflows/` (falls vorhanden)
- ✓ Führt `bash -n` Syntax-Check aus
- ✗ **FAIL** bei Syntax-Fehlern

**Evidence**: Liste fehlerhafter Scripts mit Pfaden

**Warum**: Syntax-Fehler crashen Scripts zur Laufzeit. Early detection verhindert Production-Incidents.

---

### 6. Tool Versions (C)

**Check IDs**: `tool_python`, `tool_uv`, `tool_ruff`, `tool_gh`

- ✓ **OK** wenn Tool gefunden (mit Version)
- ⚠ **WARN** wenn kritisches Tool fehlt (python, uv)
- ○ **SKIP** wenn optionales Tool fehlt (ruff, gh)

**Evidence**: `version` für jedes Tool

**Warum**: Transparenz über verfügbare Tools, keine Hard-Requirements für optionale Tools.

---

## Output-Formate

### Human-Readable (Default)

```
════════════════════════════════════════════════════════════════
  Peak_Trade Ops Inspector - Doctor Report
════════════════════════════════════════════════════════════════

✓  OK
────────────────────────────────────────────────────────────────
  ✓ Git repository root detected: /Users/frank/Peak_Trade
  ✓ Working tree clean
  ✓ pyproject.toml present
  ✓ uv.lock present
  ✓ All 6 key ops scripts present
  ✓ All 42 scripts have valid syntax
  ✓ Python 3.11.7
  ✓ uv 0.5.11

ℹ️  SKIPPED
────────────────────────────────────────────────────────────────
  ○ ruff not found (optional)
  ○ gh CLI not found (optional)

════════════════════════════════════════════════════════════════
  SUMMARY
════════════════════════════════════════════════════════════════
  Total Checks: 10
  ✓ OK:        8
  ⚠ Warnings:  0
  ✗ Failures:  0
  ○ Skipped:   2

  STATUS: 🟢 HEALTHY - All checks passed

════════════════════════════════════════════════════════════════
  NEXT ACTIONS
════════════════════════════════════════════════════════════════

  ✓ No actions required - system is healthy
```

### JSON Output (--json)

```json
{
  "tool": "ops_inspector",
  "mode": "json",
  "timestamp": "2024-12-22T15:30:00Z",
  "summary": {
    "status": "healthy",
    "exit_code": 0,
    "total_checks": 10
  },
  "checks": [
    {
      "id": "git_root",
      "severity": "INFO",
      "status": "OK",
      "message": "Git repository root detected: /Users/frank/Peak_Trade",
      "fix_hint": "",
      "evidence": ["repo_path=/Users/frank/Peak_Trade"]
    },
    {
      "id": "git_status",
      "severity": "INFO",
      "status": "OK",
      "message": "Working tree clean",
      "fix_hint": "",
      "evidence": ["status=clean"]
    },
    {
      "id": "ops_scripts",
      "severity": "WARN",
      "status": "WARN",
      "message": "Missing 2 key ops scripts",
      "fix_hint": "Consider adding missing operational scripts",
      "evidence": [
        "knowledge_smoke_runner_auto.sh",
        "run_merge_log_workflow_robust.sh"
      ]
    }
  ]
}
```

### JSON Contract

Jeder Check folgt diesem Contract:

```typescript
interface Check {
  id: string;              // Eindeutiger Identifier (z.B. "git_root")
  severity: "INFO"|"WARN"|"FAIL";
  status: "OK"|"WARN"|"FAIL"|"SKIP";
  message: string;         // Human-readable Beschreibung
  fix_hint: string;        // Actionable suggestion (kann leer sein)
  evidence: string[];      // Structured evidence (z.B. ["version=3.11.7"])
}

interface Response {
  tool: "ops_inspector";
  mode: string;            // "doctor"|"json"
  timestamp: string;       // ISO 8601 UTC
  summary: {
    status: "healthy"|"degraded"|"failed";
    exit_code: 0|1|2;
    total_checks: number;
  };
  checks: Check[];
}
```

**Evidence Array**:
- Strukturierte Daten für programmatische Auswertung
- Format: `"key=value"` oder einfache Strings
- Beispiele:
  - `["version=3.11.7"]`
  - `["dirty_files=5"]`
  - `["missing_script1.sh", "missing_script2.sh"]`

---

## Dump Mode (--dump-dir)

### Verwendung

```bash
./scripts/ops/ops_doctor.sh --dump-dir /tmp/peak_trade_debug
```

### Was wird geschrieben?

Der Dump Mode erstellt ein **Diagnostic Bundle** für Support/Debugging:

```
/tmp/peak_trade_debug/
├── git_status.txt           # git status --porcelain
├── git_log_recent.txt       # git log --oneline -20
├── git_head.txt             # git rev-parse HEAD
├── ops_inspector.json       # JSON output der Checks
└── system_info.txt          # Timestamp, Hostname, PWD, User, uname
```

**Wichtig**: Keine sensitiven Daten (API Keys, Secrets) werden geschrieben!

### Use Cases

1. **Bug Reports**: Bundle an Support-Team schicken
2. **CI Artifacts**: Archivieren für Post-Mortem-Analyse
3. **Debugging**: Offline-Analyse des System-States

---

## Troubleshooting

### Exit Code 2: Critical Failures

**Symptom**: Script beendet mit `STATUS: 🔴 FAILED`

#### Git Root nicht gefunden

```bash
Error: Not in a git repository
→ Ensure you're in the Peak_Trade repository root

# Fix:
cd ~/Peak_Trade
./scripts/ops/ops_doctor.sh
```

#### uv.lock fehlt

```bash
Error: uv.lock not found
→ Run: uv sync

# Fix:
uv sync
```

#### Bash Syntax Errors

```bash
Error: Syntax errors in 2/40 scripts: broken_script.sh test_fail.sh
→ Fix bash syntax errors: bash -n <script>

# Debug:
bash -n scripts/ops/broken_script.sh

# Nach Fix:
chmod +x scripts/ops/*.sh
```

---

### Exit Code 1: Warnings

**Symptom**: Script beendet mit `STATUS: 🟡 DEGRADED`

#### Uncommitted Changes

```bash
Warning: Uncommitted changes detected (5 files)
→ Consider committing or stashing changes

# Fix Option 1: Commit
git add .
git commit -m "fix: update configs"

# Fix Option 2: Stash
git stash push -m "WIP: temporary changes"
```

#### Fehlende Key Scripts

```bash
Warning: Missing 2 key ops scripts
→ Consider adding missing operational scripts

# Check welche fehlen:
./scripts/ops/ops_doctor.sh --json | jq '.checks[] | select(.id=="ops_scripts") | .evidence'

# Entscheidung:
# - Scripts sind noch nicht implementiert → OK, Warning akzeptieren
# - Scripts sollten vorhanden sein → Implementierung prüfen
```

---

### "Unknown option" Error

**Symptom**: `Unknown option: --xyz`

**Fix**:
- Valide Optionen: `doctor`, `--json`, `--full`, `--dump-dir <path>`, `--help`
- Prüfe Tippfehler
- Space nach `--dump-dir` erforderlich

---

### JSON Output nicht parsebar

**Symptom**: `jq` oder andere Tools können JSON nicht parsen

**Fix**:
1. Prüfe Exit Code: `echo $?` nach Script-Ausführung
2. Teste lokal: `./scripts/ops/ops_doctor.sh --json | jq .`
3. Validiere JSON: `./scripts/ops/ops_doctor.sh --json | python3 -m json.tool`

Bei reproduzierbaren Fehlern: Issue in Peak_Trade öffnen mit:
```bash
./scripts/ops/ops_doctor.sh --dump-dir /tmp/bug_report
# Bundle an Issue anhängen
```

---

## Integration

### Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running Ops Inspector..."
./scripts/ops/ops_doctor.sh

EXIT_CODE=$?

if [ $EXIT_CODE -eq 2 ]; then
  echo "❌ Critical failures detected. Commit blocked."
  exit 1
elif [ $EXIT_CODE -eq 1 ]; then
  echo "⚠️ Warnings detected. Proceeding with commit."
  # Optional: Block auch bei Warnings
  # exit 1
fi

exit 0
```

### GitHub Actions

```yaml
name: Ops Health Check

on: [push, pull_request]

jobs:
  ops-inspector:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Ops Inspector
        id: doctor
        run: |
          ./scripts/ops/ops_doctor.sh --json | tee ops_report.json
          echo "status=$(cat ops_report.json | jq -r '.summary.status')" >> $GITHUB_OUTPUT
          echo "exit_code=$(cat ops_report.json | jq -r '.summary.exit_code')" >> $GITHUB_OUTPUT

      - name: Check Result
        run: |
          if [ "${{ steps.doctor.outputs.exit_code }}" = "2" ]; then
            echo "❌ Critical failures detected"
            exit 1
          elif [ "${{ steps.doctor.outputs.exit_code }}" = "1" ]; then
            echo "⚠️ Warnings present"
            # Optional: auch bei Warnings failen
            # exit 1
          else
            echo "✅ All checks passed"
          fi

      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: ops-report
          path: ops_report.json

      - name: Create Dump on Failure
        if: failure()
        run: |
          ./scripts/ops/ops_doctor.sh --dump-dir /tmp/ops_dump

      - name: Upload Dump
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: ops-dump
          path: /tmp/ops_dump
```

### Desktop Commander Integration

```bash
# ~/.zshrc oder ~/.bashrc

alias pt-doctor="cd ~/Peak_Trade && ./scripts/ops/ops_doctor.sh"
alias pt-doctor-json="cd ~/Peak_Trade && ./scripts/ops/ops_doctor.sh --json | jq ."

# Quick Status Check
pt-status() {
  cd ~/Peak_Trade
  STATUS=$(./scripts/ops/ops_doctor.sh --json | jq -r '.summary.status')
  case "$STATUS" in
    healthy)  echo "🟢 HEALTHY" ;;
    degraded) echo "🟡 DEGRADED" ;;
    failed)   echo "🔴 FAILED" ;;
  esac
}
```

---

## Erweiterungsplan

### Phase 82B: Preflight Mode

**Zweck**: Pre-Deployment Validation mit erweiterten Checks

```bash
./scripts/ops/ops_doctor.sh --preflight
```

**Zusätzliche Checks**:
- Test-Suite erfolgreich gelaufen (letzter CI-Run)
- Branch protection erfüllt (main/develop geschützt)
- Keine offenen TODO/FIXME in kritischen Pfaden
- Config-Dateien valide (TOML-Syntax)
- Secrets nicht im Repo (git-secrets integration)

### Phase 82C: Dump Mode Enhancement

**Zweck**: Comprehensive Support Bundle

**Zusätzliche Dumps**:
- Dependency Tree (`uv tree`)
- Test Results Summary
- Recent CI Logs (via API)
- Config Auszüge (sanitized)

### Phase 82D: Web UI Dashboard

**Zweck**: Visual Health Monitoring

- Real-time Doctor Results
- Historical Trends (Grafana/Prometheus)
- Interactive Fix-Hints
- Team Health Score

---

## FAQ

### Q: Muss ich Ops Inspector vor jedem Commit laufen lassen?

**A**: Empfohlen, aber nicht zwingend:
- Bei großen Changes: **Ja**
- Bei kleinen Fixes: Optional
- In CI/CD: **Immer automatisch**

### Q: Kann ich eigene Checks hinzufügen?

**A**: Ja, Erweiterung geplant:
- **MVP (jetzt)**: Fork & extend `check_*` functions
- **Phase 82B**: Custom Check Plugins via Config
- **Roadmap**: TOML-based Check Registry

### Q: Warum wird git_root als FAIL markiert?

**A**: Der Check findet kein Git-Repository. Mögliche Ursachen:
- Nicht im Peak_Trade Repository
- `.git` Verzeichnis fehlt/gelöscht
- Script nicht aus Repository heraus aufgerufen

### Q: Was bedeutet "Evidence Array"?

**A**: Strukturierte Zusatzinformationen für programmatische Auswertung:
- `["version=3.11.7"]` → Python-Version extrahierbar
- `["dirty_files=5"]` → Anzahl uncommitted files
- Ermöglicht advanced CI-Workflows (z.B. "fail nur bei >10 dirty files")

### Q: Kann ich Checks deaktivieren?

**A**: MVP: Nein  
Roadmap (Phase 82B): Config-File für Check-Whitelisting:

```toml
# .ops_inspector.toml
[checks]
disable = ["git_status", "tool_ruff"]
```

---

## Siehe auch

- `docs/ops/README.md` - Ops-Dokumentation Overview
- `scripts\/ops\/run_tests.sh` - Test-Runner
- `.github/workflows/` - CI/CD Pipelines

---

## Changelog

### Phase 82A MVP (2024-12-22)
- ✅ Core Doctor Mode mit 6 Check-Kategorien
- ✅ JSON Output mit Evidence-Trail
- ✅ Exit Code Contract (0/1/2)
- ✅ Zero-Network Default
- ✅ --dump-dir für Diagnostic Bundles
- ✅ Smoke Tests (9 Tests)
- ✅ Comprehensive Documentation

### Roadmap
- [ ] Phase 82B: Preflight Mode + Custom Checks
- [ ] Phase 82C: Enhanced Dump Mode
- [ ] Phase 82D: Web UI Dashboard
- [ ] TOML-based Check Configuration
- [ ] Plugin System für Custom Checks
