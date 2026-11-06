# Ops Doctor – Repository Health Check

Der **Ops Doctor** ist ein umfassendes Diagnose-Tool für Peak_Trade, das verschiedene Repository-Checks durchführt und einen strukturierten Statusbericht liefert.

## 🎯 Überblick

Der Ops Doctor prüft:

- **Repository-Status**: Git-Root, uncommitted changes
- **Dependencies**: uv.lock, requirements.txt Sync
- **Konfiguration**: pyproject.toml, config-Files
- **Dokumentation**: docs/README.md
- **Test-Infrastruktur**: pytest.ini, tests/
- **CI/CD**: GitHub Actions, Makefile, Policy Packs

## 🚀 Quick Start

### Alle Checks ausführen

```bash
# Shell-Wrapper (empfohlen)
./scripts/ops/ops_doctor.sh

# Oder direkt via Python
python3 -m src.ops.doctor
```

### JSON-Output

```bash
./scripts/ops/ops_doctor.sh --json
```

### Spezifische Checks

```bash
./scripts/ops/ops_doctor.sh --check repo.git_root --check deps.uv_lock
```

## 📊 Output-Format

### Human-Readable (Standard)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏥 Peak_Trade Ops Inspector – Doctor Mode
⏰ 2025-12-23T10:30:00Z
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Summary:
   ✅ OK:   7
   ⚠️  WARN: 2
   ❌ FAIL: 0
   ⏭️  SKIP: 0

🔍 Checks:

✅ [repo.git_root] Git repository root found: /Users/frnkhrz/Peak_Trade
      /Users/frnkhrz/Peak_Trade/.git

⚠️  [repo.git_status] Uncommitted changes: 3 files
   💡 Fix: Commit or stash changes: git commit -m '...' or git stash
      M src/ops/doctor.py
      ?? scripts/ops/ops_doctor.sh
      ?? docs/ops/OPS_DOCTOR_README.md

✅ [deps.uv_lock] uv.lock up to date

...
```

### JSON-Format

```json
{
  "tool": "ops_inspector",
  "mode": "doctor",
  "timestamp": "2025-12-23T10:30:00Z",
  "summary": {
    "ok": 7,
    "warn": 2,
    "fail": 0
  },
  "checks": [
    {
      "id": "repo.git_root",
      "severity": "fail",
      "status": "ok",
      "message": "Git repository root found: /Users/frnkhrz/Peak_Trade",
      "fix_hint": "",
      "evidence": ["/Users/frnkhrz/Peak_Trade/.git"]
    }
  ]
}
```

## 🔍 Verfügbare Checks

| Check ID | Severity | Beschreibung |
|----------|----------|--------------|
| `repo.git_root` | fail | Prüft ob wir in einem Git-Repo sind |
| `repo.git_status` | warn | Prüft auf uncommitted changes |
| `deps.uv_lock` | fail | Prüft ob uv.lock existiert und aktuell ist |
| `deps.requirements_sync` | warn | Prüft ob requirements.txt mit uv.lock synchronisiert ist |
| `config.pyproject` | fail | Prüft pyproject.toml auf valide Syntax |
| `config.files` | warn | Prüft wichtige Config-Dateien im config/ |
| `docs.registry` | info | Prüft ob docs/README.md existiert |
| `tests.infrastructure` | warn | Prüft Test-Infrastruktur (pytest.ini, tests/) |
| `ci.files` | info | Prüft CI/CD-Konfiguration |

## 📋 Check-Details

### repo.git_root

**Severity**: `fail`  
**Was wird geprüft**: Existenz von `.git/` im Repository-Root

**Mögliche Ergebnisse**:
- ✅ **ok**: Git-Repository gefunden
- ❌ **fail**: Kein Git-Repository

**Fix-Hint**: `Run: git init`

---

### repo.git_status

**Severity**: `warn`  
**Was wird geprüft**: Uncommitted changes via `git status --porcelain`

**Mögliche Ergebnisse**:
- ✅ **ok**: Working directory clean
- ⚠️ **warn**: Uncommitted changes vorhanden
- ⏭️ **skip**: Git nicht verfügbar

**Fix-Hint**: `Commit or stash changes: git commit -m '...' or git stash`

---

### deps.uv_lock

**Severity**: `fail`  
**Was wird geprüft**: Existenz und Aktualität von `uv.lock`

**Mögliche Ergebnisse**:
- ✅ **ok**: uv.lock up to date
- ⚠️ **warn**: uv.lock älter als pyproject.toml
- ❌ **fail**: uv.lock nicht gefunden

**Fix-Hint**: `Run: uv lock`

---

### deps.requirements_sync

**Severity**: `warn`  
**Was wird geprüft**: Synchronisation zwischen `requirements.txt` und `uv.lock`

**Mögliche Ergebnisse**:
- ✅ **ok**: requirements.txt in sync
- ⚠️ **warn**: requirements.txt out of sync
- ⏭️ **skip**: requirements.txt oder uv.lock nicht gefunden

**Fix-Hint**: `Run: uv export --no-dev > requirements.txt`

**Hinweis**: Verwendet das vorhandene Script `scripts/ops/check_requirements_synced_with_uv.sh` falls verfügbar.

---

### config.pyproject

**Severity**: `fail`  
**Was wird geprüft**: Valide TOML-Syntax und wichtige Felder in `pyproject.toml`

**Mögliche Ergebnisse**:
- ✅ **ok**: pyproject.toml valid
- ⚠️ **warn**: Fehlende Felder (z.B. `[project]` oder `project.name`)
- ❌ **fail**: Parse-Fehler oder Datei nicht gefunden

**Fix-Hint**: `Fix TOML syntax errors` oder `Add [project] section with name and version`

---

### config.files

**Severity**: `warn`  
**Was wird geprüft**: Existenz wichtiger Config-Dateien

**Erwartete Files**:
- `config/default.toml`
- `config/config.toml`

**Mögliche Ergebnisse**:
- ✅ **ok**: Alle erwarteten Configs vorhanden
- ⚠️ **warn**: Fehlende Config-Files
- ⏭️ **skip**: `config/` Verzeichnis nicht gefunden

---

### docs.registry

**Severity**: `info`  
**Was wird geprüft**: Existenz von `docs/README.md`

**Mögliche Ergebnisse**:
- ✅ **ok**: docs/README.md gefunden
- ⚠️ **warn**: Datei nicht gefunden

---

### tests.infrastructure

**Severity**: `warn`  
**Was wird geprüft**: Test-Infrastruktur (pytest.ini, tests/)

**Mögliche Ergebnisse**:
- ✅ **ok**: Test infrastructure OK
- ⚠️ **warn**: Fehlende pytest.ini oder tests/

**Fix-Hint**: `Set up pytest: pip install pytest && touch pytest.ini`

---

### ci.files

**Severity**: `info`  
**Was wird geprüft**: CI/CD-Konfiguration

**Erwartete Files**:
- `.github/workflows/` (directory)
- `Makefile`
- `policy_packs/ci.yml`

**Mögliche Ergebnisse**:
- ✅ **ok**: CI/CD infrastructure present
- ⚠️ **warn**: Keine CI/CD-Infrastruktur gefunden

---

## 🎯 Exit Codes

| Exit Code | Bedeutung |
|-----------|-----------|
| `0` | Alle Checks OK |
| `1` | Mindestens ein Check mit Status `fail` |
| `2` | Mindestens ein Check mit Status `warn` (aber keine `fail`) |

## 🎯 Noise-Free Standard

### Zielbild

Ops Doctor gilt als **Noise-Free**, wenn:
- Alle **Core Checks**: ✅ OK (0 WARN / 0 FAIL)
- Checks mit **optionalen Live-Dependencies** (z.B. `gh` + Auth) zeigen bei fehlenden Dependencies **⏭️ SKIP** (nicht ❌ FAIL).
- "Warn-only" Bereiche (z.B. Docs Navigation) sind idealerweise ✅ PASS, damit kein Output-Noise entsteht.
- Fix-Hints sind **canonical** (entsprechen exakt der vom Check erwarteten Commandline).

### Status-Semantik

| Status | Bedeutung | Operator-Aktion |
|--------|-----------|-----------------|
| ✅ **OK** | Check erfolgreich | Keine Aktion nötig |
| ⚠️ **WARN** | Warnung, aber nicht kritisch | Optional beheben (empfohlen) |
| ❌ **FAIL** | Kritischer Fehler | **Sofort beheben** |
| ⏭️ **SKIP** | Check konnte nicht ausgeführt werden (fehlende Abhängigkeiten, Offline-Modus) | Keine Aktion nötig (nicht als Fehler interpretieren) |

**Kernprinzip**: Optionale Live-Dependency-Checks sollten **SKIP** zeigen, wenn sie nicht laufen können (z.B. `gh` CLI nicht authentifiziert), **nicht FAIL**. Dies verhindert "Hint-Drift" und Operator-Verwirrung.

### Operator Workflow Checklist

**1. Ops Doctor ausführen**:
```bash
scripts/ops/ops_center.sh doctor
```

**2. Output interpretieren**:
- **❌ FAIL**: Sofort beheben (blockiert weitere Arbeit)
- **⚠️ WARN**: Optional beheben (empfohlen, aber nicht blockierend)
- **⏭️ SKIP**: Ignorieren (externe Abhängigkeiten fehlen, z.B. Offline-Modus)

**3. Häufige Fixes**:

#### `deps.requirements_sync` (WARN)

**Canonical Fix**:
```bash
# Sync requirements.txt from uv.lock (canonical flags: all extras/groups, locked, no hashes)
uv export --format requirements.txt --all-extras --all-groups --locked --no-hashes -o requirements.txt
```

**Wann nötig**: Nach `uv.lock` Updates (z.B. nach `uv add`, `uv lock`)

**Verification**:
```bash
scripts/ops/ops_center.sh doctor
```

#### `required_checks_drift` (SKIP)

**Ursache**: `gh` CLI nicht authentifiziert oder nicht installiert

**Canonical Fix (Live-Check aktivieren)**:
```bash
# GitHub CLI einmalig authentifizieren
gh auth login
```

**Wann SKIP OK ist**: Offline-Entwicklung, CI-Umgebungen ohne GitHub-Token

**Wann Live-Check nötig**: Vor Branch Protection Updates (Änderungen an `.github/workflows/`)

## 🔧 Integration

### Pre-Commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
./scripts/ops/ops_doctor.sh --check repo.git_status
```

### CI/CD Pipeline

```yaml
# .github/workflows/health-check.yml
name: Repository Health Check

on: [push, pull_request]

jobs:
  doctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install uv
        run: pip install uv
      - name: Run Ops Doctor
        run: ./scripts/ops/ops_doctor.sh --json
```

### Makefile Integration

```makefile
.PHONY: doctor
doctor:
	@./scripts/ops/ops_doctor.sh

.PHONY: doctor-json
doctor-json:
	@./scripts/ops/ops_doctor.sh --json
```

## 📝 Erweiterung

### Neuen Check hinzufügen

1. **Check-Methode in `src/ops/doctor.py` hinzufügen**:

```python
def check_my_custom_check(self):
    """Prüft XYZ."""
    check = Check(
        id="custom.my_check",
        severity="warn",
    )

    # Prüflogik hier
    if condition_ok:
        check.status = "ok"
        check.message = "Everything OK"
    else:
        check.status = "warn"
        check.message = "Something wrong"
        check.fix_hint = "Run: fix_command"

    self.report.add_check(check)
```

2. **Check in `run_all_checks()` registrieren**:

```python
def run_all_checks(self) -> DoctorReport:
    self.check_git_root()
    self.check_git_status()
    # ...
    self.check_my_custom_check()  # NEU
    return self.report
```

3. **Check in `run_specific_checks()` registrieren**:

```python
check_map = {
    "repo.git_root": self.check_git_root,
    # ...
    "custom.my_check": self.check_my_custom_check,  # NEU
}
```

## 🐛 Troubleshooting

### "Not a git repository"

**Problem**: Check `repo.git_root` schlägt fehl.

**Lösung**:
```bash
cd /Users/frnkhrz/Peak_Trade
git init
```

### "uv.lock not found"

**Problem**: Check `deps.uv_lock` schlägt fehl.

**Lösung**:
```bash
uv lock
```

### "requirements.txt out of sync"

**Problem**: Check `deps.requirements_sync` warnt.

**Lösung**:
```bash
uv export --no-dev > requirements.txt
```

### "TOML parser not available"

**Problem**: Python < 3.11 ohne `tomli` package.

**Lösung**:
```bash
pip install tomli
```

## 🔗 Verwandte Tools

- **Test Health Runner**: `src/ops/test_health_runner.py` – Test-Health-Checks
- **Knowledge Smoke Tests**: `scripts/ops/knowledge_smoke_runner_auto.sh` – Knowledge DB Checks
- **Run Helpers Adoption Guard**: `scripts/ops/check_run_helpers_adoption.sh` – Script-Konsistenz

## 📚 Weitere Dokumentation

- [Developer Workflow Guide](../DEVELOPER_WORKFLOW_GUIDE.md)
- [Peak_Trade Tooling & Evidence Chain Runbook](Peak_Trade_TOOLING_AND_EVIDENCE_CHAIN_RUNBOOK.md)
- [Knowledge Smoke Tests](../../scripts/ops/KNOWLEDGE_SMOKE_README.md)

---

**Autor**: Peak_Trade Ops Team  
**Stand**: Dezember 2024  
**Version**: v1.0

## Docs navigation Guardrail (ops doctor)
Der Ops-Doctor-Registry-Check (`docs.registry`) erwartet, dass `docs/README.md` existiert.
Dieser Check ist informational (`info`) und ersetzt den früheren Root-`README_REGISTRY.md`-Check.
