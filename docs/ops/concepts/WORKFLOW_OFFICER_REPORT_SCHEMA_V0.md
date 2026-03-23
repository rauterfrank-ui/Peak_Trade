# Workflow Officer Report Schema v0

**Output-Ort:** `out/ops/workflow_officer/<timestamp>/`  
**Keine Vermischung** mit Paper-/Shadow-/Evidence-Produktion.

---

## 1. JSON Report Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "WorkflowOfficerReport",
  "type": "object",
  "required": ["tool", "mode", "timestamp", "exit_code", "summary", "checks"],
  "properties": {
    "tool": { "const": "workflow_officer" },
    "version": { "type": "string", "pattern": "^v0\\." },
    "mode": { "enum": ["audit", "preflight", "advise"] },
    "profile": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "repo_root": { "type": "string" },
    "exit_code": { "type": "integer", "minimum": 0, "maximum": 3 },
    "summary": {
      "type": "object",
      "required": ["ok", "warn", "fail", "skip"],
      "properties": {
        "ok": { "type": "integer", "minimum": 0 },
        "warn": { "type": "integer", "minimum": 0 },
        "fail": { "type": "integer", "minimum": 0 },
        "skip": { "type": "integer", "minimum": 0 }
      }
    },
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "status", "source"],
        "properties": {
          "id": { "type": "string" },
          "severity": { "enum": ["fail", "warn", "info"] },
          "status": { "enum": ["ok", "warn", "fail", "skip"] },
          "source": { "type": "string", "description": "Bestehendes Modul/Script, z.B. src.ops.doctor" },
          "message": { "type": "string" },
          "fix_hint": { "type": "string" },
          "evidence": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

---

## 2. Markdown Summary (optional)

Datei: `out/ops/workflow_officer/<ts>/summary.md`

```
# Workflow Officer Report — <mode> / <profile>
Timestamp: <ISO8601>

## Summary
- OK: <n>
- Warn: <n>
- Fail: <n>
- Skip: <n>
Exit Code: <0|1|2|3>

## Checks
| ID | Status | Source | Message |
|----|--------|--------|---------|
...
```

---

## 3. JSONL Event/Log Schema (optional, für Audit Trail)

Datei: `out/ops/workflow_officer/<ts>/events.jsonl`  
Nur append, keine Mutation bestehender Zeilen.

```json
{"ts": "2025-03-23T12:00:00Z", "event": "run_start", "mode": "audit", "profile": "default"}
{"ts": "2025-03-23T12:00:01Z", "event": "check_done", "id": "repo.git_root", "status": "ok", "source": "src.ops.doctor"}
{"ts": "2025-03-23T12:00:02Z", "event": "run_end", "exit_code": 0}
```

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| ts | string (ISO8601) | Zeitstempel |
| event | string | run_start, check_done, run_end |
| mode | string | audit/preflight/advise |
| profile | string | Profilname |
| id | string | Check-ID (bei check_done) |
| status | string | ok/warn/fail/skip (bei check_done) |
| source | string | Aufrufquelle (bei check_done) |
| exit_code | integer | Nur bei run_end |

---

## 4. Abgrenzung

| Art | Ort | Workflow Officer |
|-----|-----|------------------|
| Evidence Packs | `.artifacts/evidence_packs/`, `out/ops/evidence_packs/` | Nicht verwendet |
| Paper/Shadow Runs | `reports/`, `live_runs/` | Kein Zugriff |
| Doctor Report | In-Memory / stdout | Workflow Officer kann Doctor als Sub-Check aufrufen, aggregiert |
