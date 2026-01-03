# PR 518: Ops WebUI - CI Health Snapshots (v0.2)

**Status:** ✅ Ready for Review  
**Type:** Feature Enhancement  
**Component:** Ops WebUI / CI & Governance Health Panel  
**Phase:** Ops Tooling v0.2  
**Risk:** LOW (read-only, local-only, atomic writes)

---

## Summary

Erweitert das CI & Governance Health Panel um **persistente Last-Known-Health Snapshots**.

Bei jedem erfolgreichen `/ops/ci-health/status` API Call wird automatisch ein Snapshot gespeichert:
- **JSON:** `reports/ops/ci_health_latest.json` (vollständiger Status)
- **Markdown:** `reports/ops/ci_health_latest.md` (human-readable Summary, 10-20 Zeilen)

**Atomic Writes:** Temp-File + `os.replace()` → keine partial files.

**Fehlerverhalten:** Snapshot-Persistenz-Fehler failen die API NICHT (HTTP 200 + `snapshot_write_error` Feld).

---

## Why / Motivation

**Problem:**
- CI Health Status war bisher nur live abrufbar (WebUI oder API Call)
- Kein "Last Known Good" Snapshot für Debugging/Audits
- Operator muss WebUI öffnen um Status zu sehen

**Lösung:**
- Persistent Snapshot → kann jederzeit gelesen werden (auch wenn WebUI nicht läuft)
- Markdown-Format → direkt lesbar in Terminal/Editor
- JSON-Format → maschinenlesbar für Monitoring/Alerting

**Use Cases:**
- Operator prüft CI Health via `cat reports/ops/ci_health_latest.md`
- Monitoring-System liest JSON und triggert Alerts
- Post-Mortem: Letzter bekannter Status vor Incident

---

## Changes

### Code Changes

#### 1. `src/webui/ops_ci_health_router.py`

**Neue Funktionen:**
- `_get_git_head_sha()`: Liest aktuellen Git HEAD SHA (short)
- `_persist_snapshot(status_data)`: Schreibt JSON + Markdown Snapshots (atomic)
- `_write_markdown_summary(file, status_data)`: Generiert human-readable Markdown

**Erweiterte API Response (`/ops/ci-health/status`):**
```json
{
  "overall_status": "OK",
  "summary": { ... },
  "checks": [ ... ],
  "generated_at": "2025-01-03T12:34:56.789",
  "server_timestamp_utc": "2025-01-03T12:34:56.789Z",  // NEU
  "git_head_sha": "abc1234",                            // NEU
  "app_version": "0.2.0",                               // NEU
  "snapshot_write_error": "..."                         // NEU (nur bei Fehler)
}
```

**Snapshot-Pfade:**
- JSON: `reports/ops/ci_health_latest.json`
- Markdown: `reports/ops/ci_health_latest.md`

**Atomic Write:**
```python
# 1. Schreibe in temp file
json_tmp = snapshot_dir / "ci_health_latest.json.tmp"
with open(json_tmp, "w") as f:
    json.dump(data, f)

# 2. Atomic rename
os.replace(json_tmp, json_path)  # POSIX atomic operation
```

**Error Handling:**
- Snapshot-Fehler werden geloggt (`logger.error`)
- API Response enthält `snapshot_write_error` Feld
- HTTP Status bleibt **200 OK** (API-Funktion nicht beeinträchtigt)

#### 2. `tests/webui/test_ops_ci_health_router.py`

**Neue Tests (8 zusätzliche):**
- `test_ci_health_status_includes_v02_fields`: Validiert neue API-Felder
- `test_ci_health_snapshot_files_created`: Prüft Datei-Erstellung
- `test_ci_health_snapshot_json_content`: Validiert JSON-Struktur
- `test_ci_health_snapshot_md_content`: Validiert Markdown-Format
- `test_ci_health_snapshot_atomic_write`: Prüft, dass keine .tmp Files bleiben
- `test_ci_health_snapshot_error_handling`: Simuliert unwritable directory
- `test_ci_health_snapshot_multiple_calls`: Prüft Overwrite-Verhalten
- `test_ci_health_snapshot_directory_creation`: Prüft mkdir -p Logik

**Test Coverage:**
- ✅ Snapshot-Persistenz bei erfolgreicher API-Call
- ✅ Atomic writes (keine partial files)
- ✅ Error handling (API bleibt 200)
- ✅ Directory auto-creation
- ✅ Multiple calls (latest wins)

**Test Results:**
```bash
$ python3 -m pytest tests/webui/test_ops_ci_health_router.py -v
============================= test session starts ==============================
...
20 passed in 0.60s
```

---

## Snapshot Format Examples

### JSON Snapshot (`ci_health_latest.json`)

```json
{
  "overall_status": "OK",
  "summary": {
    "total": 2,
    "ok": 2,
    "warn": 0,
    "fail": 0,
    "skip": 0
  },
  "checks": [
    {
      "check_id": "contract_guard",
      "title": "Contract Guard",
      "description": "Verifiziert, dass alle required CI contexts korrekt konfiguriert sind",
      "status": "OK",
      "exit_code": 0,
      "output": "✅ CI required context contract looks good.",
      "error_excerpt": "",
      "duration_ms": 123,
      "timestamp": "2025-01-03T12:34:56.789",
      "script_path": "/path/to/check_required_ci_contexts_present.sh",
      "docs_refs": ["docs/ops/runbooks/github_rulesets_pr_reviews_policy.md"]
    },
    {
      "check_id": "docs_reference_validation",
      "title": "Docs Reference Validation",
      "description": "Prüft, ob alle Markdown-Links auf existierende Dateien zeigen",
      "status": "OK",
      "exit_code": 0,
      "output": "✅ All docs references valid.",
      "error_excerpt": "",
      "duration_ms": 456,
      "timestamp": "2025-01-03T12:34:57.123",
      "script_path": "/path/to/verify_docs_reference_targets.sh",
      "docs_refs": ["docs/ops/README.md"]
    }
  ],
  "generated_at": "2025-01-03T12:34:57.500",
  "server_timestamp_utc": "2025-01-03T12:34:57.500Z",
  "git_head_sha": "abc1234",
  "app_version": "0.2.0"
}
```

### Markdown Snapshot (`ci_health_latest.md`)

```markdown
# CI & Governance Health Snapshot

**Generated:** 2025-01-03T12:34:57.500  
**Git HEAD:** `abc1234`  
**Overall Status:** **OK**  

## Summary

- **Total Checks:** 2
- **OK:** 2
- **WARN:** 0
- **FAIL:** 0
- **SKIP:** 0

## Checks

### Contract Guard [OK]

- **Check ID:** `contract_guard`
- **Duration:** 123ms
- **Exit Code:** 0

### Docs Reference Validation [OK]

- **Check ID:** `docs_reference_validation`
- **Duration:** 456ms
- **Exit Code:** 0
```

---

## Verification / Testing

### Automated Tests

```bash
# Run CI Health Panel tests
python3 -m pytest tests/webui/test_ops_ci_health_router.py -v

# Expected: 20 passed (8 new v0.2 tests)
```

### Manual Verification (Operator How-To)

#### 1. Start WebUI

```bash
cd /Users/frnkhrz/Peak_Trade
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000
```

#### 2. Trigger Snapshot via API

```bash
# Call status endpoint
curl -s http://127.0.0.1:8000/ops/ci-health/status | jq .

# Expected: JSON response with v0.2 fields
# - server_timestamp_utc
# - git_head_sha
# - app_version: "0.2.0"
```

#### 3. Verify Snapshot Files

```bash
# Check JSON snapshot
cat reports/ops/ci_health_latest.json | jq .overall_status

# Check Markdown snapshot
cat reports/ops/ci_health_latest.md

# Expected: Both files exist and contain current status
```

#### 4. Verify Atomic Writes

```bash
# Check for leftover temp files (should be empty)
ls -la reports/ops/*.tmp

# Expected: No .tmp files
```

#### 5. Test Error Handling (Optional)

```bash
# Make reports dir read-only
chmod 444 reports/ops

# Call API (should still return 200)
curl -s http://127.0.0.1:8000/ops/ci-health/status | jq .snapshot_write_error

# Expected: Error message in response, but HTTP 200

# Restore permissions
chmod 755 reports/ops
```

#### 6. Verify Multiple Calls (Latest Wins)

```bash
# Call API twice
curl -s http://127.0.0.1:8000/ops/ci-health/status > /dev/null
sleep 2
curl -s http://127.0.0.1:8000/ops/ci-health/status > /dev/null

# Check timestamps
cat reports/ops/ci_health_latest.json | jq .generated_at

# Expected: Latest timestamp
```

---

## Risk Assessment

**Risk Level:** 🟢 LOW

### Safety Guarantees

1. **Read-Only Checks:**
   - CI Health Checks sind read-only (keine destructive operations)
   - Snapshot-Persistenz ist write-only (keine Daten gelöscht)

2. **Atomic Writes:**
   - Temp-File + `os.replace()` → POSIX atomic operation
   - Keine partial files bei Crash/Interrupt

3. **Error Isolation:**
   - Snapshot-Fehler failen API NICHT
   - Logging statt Exception-Propagation

4. **Local-Only:**
   - Keine externen API Calls
   - Keine Secrets/Credentials benötigt

5. **Gitignore:**
   - `reports/` bereits in `.gitignore`
   - Snapshots werden NICHT committed

### Potential Issues

1. **Disk Space:**
   - Snapshots sind klein (~5-10 KB pro File)
   - Nur 2 Files (JSON + MD), keine Historie
   - **Mitigation:** Operator kann Files manuell löschen

2. **Permissions:**
   - Wenn `reports/ops/` nicht writable → `snapshot_write_error`
   - **Mitigation:** API bleibt 200, Fehler nur geloggt

3. **Concurrency:**
   - Mehrere gleichzeitige API Calls → Race Condition möglich
   - **Mitigation:** Atomic writes via `os.replace()` (POSIX garantiert)

---

## Rollout / Deployment

### Prerequisites

- ✅ WebUI läuft (FastAPI)
- ✅ CI Health Panel v0.1 deployed
- ✅ `reports/` in `.gitignore` (bereits vorhanden)

### Deployment Steps

1. **Merge PR:**
   ```bash
   git checkout main
   git merge ops/ci-governance-health-panel-v0_2-snapshot
   ```

2. **Restart WebUI:**
   ```bash
   # Stop existing WebUI
   pkill -f "uvicorn src.webui.app"

   # Start with new code
   uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000
   ```

3. **Verify:**
   ```bash
   # Trigger snapshot
   curl http://127.0.0.1:8000/ops/ci-health/status

   # Check files
   ls -lh reports/ops/ci_health_latest.*
   ```

### Rollback

```bash
# Revert to v0.1
git revert <commit-sha>

# Restart WebUI
uvicorn src.webui.app:app --reload
```

---

## Future Enhancements (Out of Scope)

**v0.3 Kandidaten:**
- Snapshot-Historie (z.B. letzte 10 Snapshots behalten)
- Trend-Analyse (Verschlechterung über Zeit)
- Alerting bei Status-Änderung (OK → FAIL)
- Prometheus-Exporter für Monitoring
- Scheduled Health Checks (cron-like)

---

## Documentation Updates

**Neue Docs:**
- ✅ `docs/ops/PR_518_CI_HEALTH_PANEL_V0_2.md` (dieses Dokument)

**Zu aktualisieren (optional):**
- `docs/ops/README.md`: Erwähne v0.2 Snapshot-Feature bei Bedarf

---

## Checklist

- [x] Code implementiert (`ops_ci_health_router.py`)
- [x] Tests geschrieben (8 neue Tests)
- [x] Tests grün (20/20 passed)
- [x] Linter clean (no errors)
- [x] Atomic writes implementiert
- [x] Error handling implementiert
- [x] Gitignore geprüft (`reports/` bereits drin)
- [x] PR-Dokumentation erstellt
- [ ] Branch erstellt
- [ ] Commit erstellt
- [ ] PR erstellt (GitHub)
- [ ] Manuelle Verification durchgeführt

---

## Commit Message

```
ops(webui): persist CI health snapshot (v0.2)

Erweitert CI & Governance Health Panel um persistente Snapshots:

Features:
- Snapshot bei jedem /ops/ci-health/status Call
- JSON: reports/ops/ci_health_latest.json (vollständig)
- Markdown: reports/ops/ci_health_latest.md (human-readable)
- Atomic writes (temp file + os.replace)
- Error handling (snapshot errors do NOT fail API)

API Response v0.2:
- server_timestamp_utc (ISO 8601)
- git_head_sha (short)
- app_version ("0.2.0")
- snapshot_write_error (optional, bei Fehler)

Tests:
- 8 neue Tests für Snapshot-Persistenz
- Coverage: atomic writes, error handling, directory creation
- 20/20 tests passed

Risk: LOW (read-only checks, atomic writes, local-only)

Refs: PR #518, Ops Tooling v0.2
```

---

## PR Title

```
Ops WebUI: CI health snapshots (v0.2)
```

---

## PR Description (GitHub)

```markdown
## Summary

Erweitert das CI & Governance Health Panel um **persistente Last-Known-Health Snapshots**.

Bei jedem `/ops/ci-health/status` API Call wird automatisch ein Snapshot gespeichert:
- **JSON:** `reports/ops/ci_health_latest.json` (vollständiger Status)
- **Markdown:** `reports/ops/ci_health_latest.md` (human-readable, 10-20 Zeilen)

## Why

- **Problem:** CI Health Status war nur live abrufbar (WebUI/API)
- **Lösung:** Persistent Snapshot → jederzeit lesbar (auch wenn WebUI nicht läuft)
- **Use Cases:** Operator-Debugging, Monitoring, Post-Mortem

## Changes

### Code
- `src/webui/ops_ci_health_router.py`: Snapshot-Persistenz + atomic writes
- `tests/webui/test_ops_ci_health_router.py`: 8 neue Tests

### API Response (v0.2)
```json
{
  "overall_status": "OK",
  "summary": { ... },
  "checks": [ ... ],
  "server_timestamp_utc": "2025-01-03T12:34:56.789Z",  // NEU
  "git_head_sha": "abc1234",                            // NEU
  "app_version": "0.2.0",                               // NEU
  "snapshot_write_error": "..."                         // NEU (nur bei Fehler)
}
```

## Verification

### Automated Tests
```bash
python3 -m pytest tests/webui/test_ops_ci_health_router.py -v
# ✅ 20 passed (8 new v0.2 tests)
```

### Manual Verification
```bash
# 1. Start WebUI
uvicorn src.webui.app:app --reload

# 2. Trigger snapshot
curl http://127.0.0.1:8000/ops/ci-health/status

# 3. Verify files
cat reports/ops/ci_health_latest.md
cat reports/ops/ci_health_latest.json | jq .
```

## Risk

🟢 **LOW**
- Read-only checks, atomic writes, local-only
- Snapshot errors do NOT fail API (HTTP 200 + error field)
- `reports/` already in `.gitignore`

## Operator How-To

**View latest CI health:**
```bash
cat reports/ops/ci_health_latest.md
```

**Machine-readable status:**
```bash
jq .overall_status reports/ops/ci_health_latest.json
```

## Documentation

- ✅ `docs/ops/PR_518_CI_HEALTH_PANEL_V0_2.md` (full spec)
- 📝 TODO: Update `docs/ops/README.md` (mention v0.2)

## Refs

- Phase: Ops Tooling v0.2
- Component: Ops WebUI / CI & Governance Health Panel
- Related: PR #510 (CI Health Panel v0.1)
```

---

**End of PR Documentation**
