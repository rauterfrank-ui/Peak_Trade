# Workflow Officer v0 Plan

**Branch:** feat/workflow-officer-v0-plan  
**Status:** Design freeze (docs-only)  
**Letzte Änderung:** 2025-03-23

---

## 1. Zielbild

Der **Workflow Officer** ist ein orchestrierender Entrypoint, der bestehende Ops-/Doctor-/Preflight-/Gate-/Triage-Bausteine bündelt. Er führt **keine** neuen Checks ein, sondern ruft vorhandene Skripte/Module auf und aggregiert deren Ergebnisse.

**Kernprinzip:** Reuse first. Kein Parallel-Stack.

---

## 2. Modi

| Modus | Zweck | Typische Nutzung |
|-------|-------|------------------|
| **audit** | Bestehende Checks ausführen, Report erstellen, Exit-Code aggregieren | CI, lokale Vor-PR-Prüfung |
| **preflight** | Gezielte Checks vor riskanten Ops (Live-Pilot, Docker, MCP) | Vor `run_live_pilot_session.sh`, vor Docker-Start |
| **advise** | Read-only Empfehlungen, keine Checks ausführen | Operator-Hilfe, "was soll ich prüfen?" |

---

## 3. Nicht-Ziele (v0)

- **Keine** Auto-Remediation
- **Keine** Änderung an Paper-/Shadow-/Evidence-Produktion
- **Keine** neuen Gates neben den vorhandenen
- **Kein** self-healing oder magischer Sandbox-Agent
- **Keine** Änderung an bestehenden produktiven Pfaden (Doctor, CI, Obs)

---

## 4. CLI-/Entrypoint-Vorschlag

```
python -m src.ops.workflow_officer [--mode audit|preflight|advise] [--profile <name>] [--json]
```

| Option | Default | Beschreibung |
|--------|---------|--------------|
| `--mode` | audit | audit / preflight / advise |
| `--profile` | default | Profil für Check-Subset (siehe unten) |
| `--json` | false | Machine-readable JSON-Report |
| `--out-dir` | out/ops/workflow_officer/<ts> | Output-Verzeichnis (nur audit/preflight) |

---

## 5. Profiles

| Profil | Zweck | Checks (Beispiele, via bestehende Bausteine) |
|--------|-------|----------------------------------------------|
| **docs_only_pr** | Vor PR: Docs-Token-Policy, Links, Reference-Targets | `validate_docs_token_policy.py`, `check_markdown_links.py`, `verify_docs_reference_targets.sh` |
| **ops_local_env** | Lokales Setup: Doctor + Docker-Preflight | `src.ops.doctor`, `docker_desktop_preflight_readonly.sh` |
| **live_pilot_preflight** | Vor Live-Pilot: Readiness + Ops-Status | `run_live_pilot_preflight.sh` (oder dessen Sub-Checks) |
| **default** | Alle Doctor-Checks | `src.ops.doctor` (run_all_checks) |

Profiles wählen einen **Subset** vorhandener Checks; es werden keine neuen Checks definiert.

---

## 6. Exit-Codes

| Code | Bedeutung |
|------|-----------|
| 0 | Alle Checks ok |
| 1 | Mindestens ein Check fail |
| 2 | Mindestens ein Check warn (kein fail) |
| 3 | Invalid arguments / Mode nicht verfügbar |

Aggregation analog zu `src/ops/doctor.py` (fail > warn > ok).

---

## 7. Abhängigkeiten

- Python 3.11+
- Bestehende Skripte/Module: Doctor, Preflight-Scripts, Policy-Validatoren (siehe WORKFLOW_OFFICER_EXISTING_BUILDING_BLOCKS_MAP.md)

---

## 8. Rollout-Phasen

Siehe `WORKFLOW_OFFICER_V0_ROLLOUT_RUNBOOK.md`.
