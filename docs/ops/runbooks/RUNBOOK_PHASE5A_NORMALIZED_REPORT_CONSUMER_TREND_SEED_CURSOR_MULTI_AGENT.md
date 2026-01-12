# RUNBOOK — Phase 5A: Normalized Report Consumer + Trend Seed (Cursor Multi-Agent)

Stand: 2026-01-11  
Owner: Ops / AIOps  
Risk: LOW (tooling + artifacts only)  
Scope: CI Artifact Consumption + deterministic Trend-Seed Generation  
Audience: Operator, CI_GUARDIAN, EVIDENCE_SCRIBE

---

## 0) Purpose & Guardrails

### Purpose
Phase 5A operationalisiert den Übergang von **"Normalized Validator Report"** (Phase 4E Output) zu einem **Trend-Seed** (maschinenlesbarer, deterministischer Zeitreihen-Record).  
Der Trend-Seed ist ein **kleines, stabiles "Event/Record" Artefakt**, das später in Phase 5B/5C zu Trends aggregiert wird (z.B. Pass-Rate, Determinism-Hash-Stabilität, Schema-Migrationsquote, Policy-Finding Counts).

### Guardrails (nicht verhandelbar)
- **No-Live Trading / No Order Execution.** Reine AIOps-Tooling-/Docs-/CI-Artefakt-Arbeit.
- **Determinismus:** Trend-Seed muss bei gleicher Input-Report-Version deterministisch sein (stable JSON, stable ordering).
- **SoD:** Rollen strikt trennen (Plan/Implement/Verify/Sign-off).
- **Keine Secrets:** Keine Tokens, URLs mit Secrets oder Runner-Env-Daten in Artefakten/Logs persistieren.
- **Backward Compatibility:** Consumer darf alte Reports nicht zerstören; bei Inkompatibilität: "fail closed" + klare Fehlermeldung.

---

## 1) Inputs & Prerequisites

### Inputs
- CI-Artefakt aus Phase 4E:
  - `validator_report.normalized.json` (canonical, schema v1.0.0)
  - optional: `validator_report.normalized.md`
- Kontext aus CI Run:
  - run_id, workflow name, repository, sha, branch, created_at

### Prerequisites
- Repo-Zugriff (read) + Ability, in PR zu arbeiten
- Cursor Multi-Agent Chat aktiviert (6-Rollen Modell)
- Phase 4E ist merged & produziert normalized artifacts stabil
- (Optional) GitHub CLI verfügbar lokal für Debug: `gh run view`, `gh run download`

---

## 2) Multi-Agent Role Model (Cursor Multi-Agent)

### ORCHESTRATOR
- Führt die Session, verteilt Tasks, erzwingt Guardrails.
- Entscheidet "Docs-Only" vs "Tooling+CI".

### FACTS_COLLECTOR
- Sammelt harte Fakten aus Repo:
  - Wo Phase 4E Artefakte erzeugt werden (Workflow-Name, Artifact-Name)
  - Welche Felder im normalized report garantiert sind
  - Bestehende Trend-/Report-Ordnerstrukturen

### SCOPE_KEEPER
- Hält Scope klein: Trend Seed nur "Minimum Viable Record".
- Verhindert Feature-Creep (kein Dashboard, keine Aggregation in 5A).

### CI_GUARDIAN
- Definiert CI-Integration & Gates (required vs optional).
- Validiert Job-Names, artifact download path, permissions.

### EVIDENCE_SCRIBE
- Schreibt/aktualisiert Docs, Runbook, Operator-Template.
- Stellt sicher: audit-stabil, referenzierbar, verlinkt.

### RISK_OFFICER
- Risikoanalyse: Datenleaks, nondeterminism, flakey CI.
- Definiert "Fail-Closed" Policy und Recovery Steps.

---

## 3) Required Artifacts (Phase 5A Deliverables)

### A) Trend Seed (Primary)
- `trend_seed.normalized_report.json` (single JSON record)
  - deterministic key ordering
  - schema versioned
  - minimal but sufficient for future aggregation

### B) Trend Seed Summary (Optional human-readable)
- `trend_seed.normalized_report.md` (short summary)

### C) Run Manifest (Recommended)
- `trend_seed.run_manifest.json`
  - source run metadata + consumer version

### D) Evidence Notes (Operator)
- short "Operator Notes" section in PR body or dedicated doc entry

---

## 4) Data Contract — Trend Seed Schema (v0.1.0)

### Design Principles
- "Append-only record" mindset: später als JSONL/NDJSON aggregierbar.
- Stable fields + explicit `schema_version`.
- Keine unnötigen Felder; keine großen payloads; keine raw logs.

### Proposed Schema (v0.1.0)
Required:
- `schema_version`: "0.1.0"
- `generated_at`: ISO-8601 UTC (Z)
- `source`:
  - `repo`
  - `workflow_name`
  - `run_id`
  - `run_attempt` (if available; else 1)
  - `head_sha`
  - `ref` (branch/tag)
- `normalized_report`:
  - `schema_version` (z.B. "1.0.0")
  - `report_id` (wenn vorhanden; sonst derive)
  - `conclusion` ("pass"/"fail"/"error")
  - `determinism`:
    - `hash` (wenn vorhanden; sonst null)
    - `is_deterministic` (bool, wenn ableitbar; sonst null)
  - `counts`:
    - `checks_total`
    - `checks_passed`
    - `checks_failed`
    - `policy_findings_total` (wenn vorhanden; sonst 0/null)
Optional:
- `notes`: short string (bounded length, e.g. <= 280)
- `consumer`:
  - `name`
  - `version`
  - `commit_sha`

### Fail-Closed Rules
- Wenn `normalized_report.schema_version` unbekannt → **hard fail** mit klarer Meldung:
  - "Unsupported normalized report schema version: X"
- Wenn required fields fehlen → **hard fail** + list missing keys.

---

## 5) Standard Workflow (A → H)

### A) Pre-Flight (ORCHESTRATOR + CI_GUARDIAN)
- Confirm scope: **Phase 5A = Consumer + Seed only**
- Confirm: No strategy/backtest/live code touched
- Decide:
  - Option 1: Docs-only runbook (minimal)
  - Option 2: Add consumer script + CI job producing Trend Seed artifact (recommended)

### B) Discovery (FACTS_COLLECTOR)
- Locate Phase 4E workflow file(s) and artifact name(s)
- Identify normalized report schema fields available
- Identify existing conventions (folders, naming, schema modules)

### C) Plan (SCOPE_KEEPER + RISK_OFFICER)
- Define minimal Trend Seed fields required for phase 5B+
- Define determinism approach:
  - canonical JSON dumps
  - sorted keys, stable floats/ints, stable timestamp formatting
- Define CI strategy:
  - On `workflow_run` after Phase 4E completes OR
  - On push to main / schedule (less ideal)

### D) Implement (assigned engineer/agent)
- Add consumer module/script (recommended paths):
  - `src/ai_orchestration/` or `scripts/aiops/` depending on repo conventions
- Add tests:
  - schema enforcement, missing fields, unsupported versions, deterministic output
- Add CI workflow:
  - downloads normalized artifact
  - runs consumer
  - uploads Trend Seed artifact(s)

### E) Validate Locally (CI_GUARDIAN)
- Run unit tests
- Run a local "sample consumption" against fixture normalized report JSON
- Validate deterministic output by re-running and diffing

### F) CI Verification (CI_GUARDIAN)
- Verify workflow produces artifacts:
  - `trend_seed.normalized_report.json`
  - optional: `.md`, `run_manifest.json`
- Ensure job is **non-flaky** and has clear failures

### G) Docs + Evidence (EVIDENCE_SCRIBE)
- Update runbook references / ops index
- Add operator notes template in PR body
- Ensure docs reference targets gate won't misinterpret branch names/paths

### H) Sign-Off (RISK_OFFICER + ORCHESTRATOR)
- Risk assessment: LOW
- Confirm "No trading code touched"
- Confirm "Fail-Closed" behavior
- Confirm "No secrets" guarantee

---

## 6) Pass/Fail Criteria

### PASS
- Trend Seed JSON generated deterministically
- Schema v0.1.0 validated
- CI workflow succeeds and uploads artifacts
- Consumer fails closed on schema mismatch (tested)

### FAIL
- Trend Seed differs across runs with same inputs
- Missing required fields without hard fail
- Sensitive data leakage into artifacts/logs
- CI flakiness (timeouts, unstable download, brittle assumptions)

---

## 7) CI Gates Reference (Guidance)

- Trend Seed workflow should be:
  - **Required?** Usually NO at start (optional gate) to avoid blocking until stable
  - Upgrade to required once stability is demonstrated
- Use explicit timeouts and retries only where justified (download step)
- Ensure permissions are minimal:
  - read actions/artifacts; no write needed unless committing back (out of scope)

---

## 8) Troubleshooting

### Artifact download fails
- Causes:
  - wrong artifact name
  - run has no artifacts (Phase 4E failed)
  - insufficient permissions
- Fix:
  - re-check workflow artifact names
  - add "list artifacts" debug step in CI
  - ensure workflow_run trigger targets correct workflow

### Schema mismatch / missing keys
- Fix:
  - update consumer mapping
  - add explicit migration adapter (but keep minimal in 5A)
  - fail closed with actionable message

### Non-deterministic output
- Fix:
  - stable JSON serialization with sorted keys
  - normalize timestamps (use CI provided time, not "now" unless required; if "now" required, use run created_at)

---

## 9) Operator Output Template (Paste into PR / Run Notes)

**Phase 5A Operator Notes**
- Run Type: (Docs-only | Tooling+CI)
- Inputs:
  - Phase 4E Run ID:
  - Artifact:
- Outputs:
  - Trend Seed Artifact:
  - Manifest:
- Verification:
  - Determinism check:
  - Unit tests:
  - CI job link:
- Risk:
  - Data leakage risk:
  - Flakiness risk:
- Decision:
  - PASS / FAIL
- Follow-ups (Phase 5B+):
  - (list)

---

## 10) Implementation Notes (EVIDENCE_SCRIBE)

### Delivered Artifacts

**Consumer Library:**
- `src/ai_orchestration/trends/trend_seed_consumer.py` (428 lines)
  - load_normalized_report(), generate_trend_seed(), write_deterministic_json(), render_markdown_summary()
  - Fail-closed validation (schema mismatch, missing keys)
  - Deterministic JSON serialization (sorted keys, stable timestamps)

**CLI Script:**
- `scripts/aiops/generate_trend_seed_from_normalized_report.py` (180 lines)
  - Accepts normalized report + workflow metadata
  - Outputs: trend_seed.normalized_report.json, trend_seed.run_manifest.json, trend_seed.normalized_report.md
  - Exit codes: 0 (success), 1 (error)

**Tests:**
- `tests/ai_orchestration/test_trend_seed_from_normalized_report.py` (17 tests, 100% pass)
  - Determinism verified (byte-identical output on repeated runs)
  - Fail-closed validation (missing schema_version, unsupported version, missing fields)
  - Conclusion normalization, counts extraction, markdown rendering

**CI Workflow:**
- `.github/workflows/aiops-trend-seed-from-normalized-report.yml`
  - Trigger: workflow_run on "L4 Critic Replay Determinism" (success only, main only)
  - Downloads Phase 4E artifact (validator-report-normalized-{run_id})
  - Runs consumer with workflow_run metadata
  - Uploads Trend Seed artifacts (trend-seed-{run_id}, 30-day retention)

**Test Fixture:**
- `tests/fixtures/validator_report.normalized.sample.json`
  - Sample Phase 4E normalized report (schema v1.0.0, 2 checks, PASS)

### Verification

All verification criteria met:
- ✅ Unit tests: 17/17 passed
- ✅ Determinism: Verified via diff of two identical runs (byte-identical)
- ✅ Fail-closed: Schema mismatch and missing fields raise ValidationError
- ✅ No secrets: No tokens, env vars, or sensitive data in outputs
- ✅ CLI smoke test: Passed with sample fixture

---

## 11) Change Log
- 2026-01-11: Initial version (Phase 5A runbook draft)
- 2026-01-11: Implementation complete (Consumer + CLI + Tests + CI + Fixture)
