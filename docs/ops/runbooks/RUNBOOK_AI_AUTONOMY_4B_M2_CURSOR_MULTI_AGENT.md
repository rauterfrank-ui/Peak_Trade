# RUNBOOK — AI Autonomy (Phase 4B · Milestone 2)
## Cursor Multi-Agent Chat: Evidence-First Operator Loop

**Status:** Draft (Operator-ready)  
**Owner:** Ops / Governance  
**Last updated:** 2026-01-09  
**Primary Goal:** Audit-stabile, reproduzierbare AI-Autonomy Runs (Layer-Runs) mit Evidence Pack + CI-Gate + Operator-Review.

---

## 0) Zweck & Leitplanken

### Zweck
Dieses Runbook beschreibt den standardisierten Ablauf, um AI-Autonomy Artefakte (Layer-Konfig, Run-Outputs, Checks, Evidence Pack) **deterministisch** zu erzeugen, **CI-validiert** zu prüfen und **audit-tauglich** zu dokumentieren – mit einem Cursor Multi-Agent Chat als Orchestrierung.

### Leitplanken (nicht verhandelbar)
- **Evidence-first:** Jede Entscheidung und jeder Run muss in einem Evidence Pack nachweisbar sein.
- **No-live / Governance-locked:** Kein Live-Trading, keine „Auto-Switches", keine impliziten Rechteeskalationen.
- **SoD / Rollen-Trennung:** Planung, Umsetzung, Validierung und Risiko-Review sind getrennte Verantwortlichkeiten (auch wenn ein Operator sie ausführt, bleiben die Checks formal getrennt).
- **Determinismus:** Outputs müssen wiederholbar sein (Seeds/Configs/Versions).

### Nicht-Ziele
- Kein Modell-Training, kein Hyperparameter-Tuning im Runbook.
- Keine automatische Freigabe („Go") ohne Operator-Review.
- Keine Änderung von Live-Konfigurationen.

---

## 1) Inputs / Voraussetzungen

### Vorausgesetzt
- Repo ist sauber (kein „dirty" Working Tree) oder Änderungen sind bewusst isoliert.
- CI läuft (mindestens: Lint, Audit, Evidence-Pack Validation, Docs Gates).
- AI Autonomy Artefakte existieren (z.B. Layer Map / Model Registry / Evidence Pack Schema / Validator).

### Benötigte Inputs (pro Run)
- `layer_id` / `scope` (z.B. L0/L1/L2/L4)
- `model_id` / `model_profile` (aus Model Registry)
- `capability_scope` (erlaubte Aktionen des Agents)
- `run_reason` (Why: z.B. "release readiness", "policy regression check")
- `operator_id` (wer führt aus)
- `git_ref` (commit SHA / branch)
- Optional: `seed`, `dataset_snapshot_id`

---

## 2) Rollenmodell (Cursor Multi-Agent)

> Hinweis: Das ist eine logische Rollenstruktur. In Cursor können diese Rollen als Agent-Prompts abgebildet werden.

### ORCHESTRATOR (Lead)
- Führt durch Steps, delegiert an Agents, hält Timeline, entscheidet Reihenfolge.
- Liefert am Ende die **Operator Summary** + **Go/No-Go Empfehlung** (nicht automatisch „Go").

### FACTS_COLLECTOR
- Sammelt Repo-Fakten: Pfade, existierende Skripte, Validatoren, CI-Workflows, aktuelle Konfig-Stände.
- Liefert **konkrete Referenzen** (Dateipfade, Funktionen, CLI-Commands).

### SCOPE_KEEPER
- Verteidigt die Leitplanken: verhindert Scope-Creep, hält Non-Goals ein.
- Erzwingt: keine Live-Änderungen, keine Auto-Switches.

### CI_GUARDIAN
- Definiert/prüft CI-Gates: Welche Checks müssen grün sein, welche Artefakte müssen existieren.
- Liefert „Pass/Fail" Kriterien.

### EVIDENCE_SCRIBE
- Stellt sicher, dass Evidence Pack vollständig und konsistent ist.
- Erstellt/aktualisiert Evidence Index Einträge und Merge-Log-Anker.

### RISK_OFFICER
- Bewertet Änderungen/Runs anhand Risk Layer / Policies.
- Formuliert Risiken + Mitigations + Operator Actions.

---

## 3) Artefakte & Outputs

### Muss-Artefakte (pro Run)
- Evidence Pack (JSON + ggf. Markdown Summary)
- Run Manifest (Inputs, Versionen, Seed, Zeit, Machine info)
- Validator Report (CI-kompatibel)
- Operator Review Notes (kurz, sign-offfähig)

### Optional (wenn vorhanden)
- Layer Smoke Report
- Policy Critic Output
- Docs Reference Targets / Link Debt Trend Resultate

### Operator Drill Pack

Für systematisches Kompetenztraining steht ein strukturiertes Drill Pack zur Verfügung:

**[Operator Drill Pack — AI Autonomy 4B M2](../drills/OPERATOR_DRILL_PACK_AI_AUTONOMY_4B_M2.md)**

Das Pack enthält 8 wiederholbare Drills:
- D01: Pre-Flight Discipline (Repo Hygiene, Branch Hygiene)
- D02: Scope Lock Verification (Docs-only Contract Enforcement)
- D03: Evidence Pack Completeness (Schema Validation, Naming)
- D04: CI Gate Triage (Failing Checks, Remediation)
- D05: Docs Reference Targets Gate (Missing Targets, False Positives)
- D06: Auto-Merge Safety (Required Checks, Merge Readiness)
- D07: Incident Micro-Drill (Timeout Handling, Flaky Checks)
- D08: Closeout Drill (Final Summary, Risk Call, Linking)

Empfohlene Kadenz: 1-2 Drills pro Woche, vollständiger Durchlauf vor Production-nahen Runs.

### Drill Session Logging

Für strukturierte Drill-Session-Dokumentation stehen standardisierte Templates zur Verfügung:

**[Session Template — AI Autonomy 4B M2](../drills/SESSION_TEMPLATE_AI_AUTONOMY_4B_M2.md)**

Das Template enthält:
- Session Metadata (Date/Time, Drill ID, Operator, Roles)
- Run Manifest (Objective, Preconditions, Pass/Fail Criteria)
- Execution Log (Step-by-step with evidence pointers)
- Scorecard (Criterion-based pass/fail with evidence)
- Findings & Operator Actions (Reproducible findings, immediate actions)
- Follow-Ups (Docs-only PR suggestions)

**[Drill Runs README](../drills/runs/README.md)**

Guidelines für Drill Run Logs:
- Naming Convention: `DRILL_RUN_YYYYMMDD_HHMM_<operator>_<drill>.md`
- Quality Bar: Evidence-first, reproducible, concise, SoD-enforced, deterministic
- Storage: `docs/ops/drills/runs/`
- Optional: Commit significant drill runs via docs-only PR

---

## 4) Standardablauf (Milestone 2)

### Step A — Pre-Flight (Repo & Governance)
**Ziel:** Sicherstellen, dass wir in der richtigen Umgebung sind und Governance-Constraints nicht verletzt werden.

Checkliste:
- [ ] Repo Root bestätigt
- [ ] Branch/Commit dokumentiert
- [ ] Working Tree Status dokumentiert
- [ ] Keine Continuation/Herodoc-Hänger in Shell
- [ ] Keine Live-Config Änderungen im Scope

Output:
- `preflight_snapshot` im Evidence Pack (oder in Operator Notes)

---

### Step B — Discovery / Inventory (FACTS_COLLECTOR)
**Ziel:** Herausfinden, was bereits existiert und welche Pfade/Commands „canonical" sind.

Tasks:
- [ ] Finde Evidence Pack Schema + Validator Entry-Points
- [ ] Finde Layer Map Configs + Model Registry
- [ ] Finde CI Workflows, die Evidence Packs prüfen/erzeugen
- [ ] Liste relevante Scripts/Commands für Layer Runs

Output:
- `inventory.md` (kurz) oder Inventory Section im Evidence Pack

---

### Step C — Run Plan (SCOPE_KEEPER + CI_GUARDIAN)
**Ziel:** Einen minimalen, audit-stabilen Run Plan erstellen.

Plan enthält:
- Run-Ziel (1 Satz)
- Run-Inputs (layer_id, model_id, scope, seed)
- Erwartete Outputs (konkret)
- Gates (was muss grün sein)
- Abbruchkriterien (wann stoppen)

Output:
- `run_plan` im Evidence Pack

---

### Step D — Execute Layer Run (ORCHESTRATOR)
**Ziel:** Layer Run ausführen und Outputs erfassen.

Mindestanforderungen:
- Inputs deterministisch gesetzt
- Outputs in definierte Artefaktpfade geschrieben
- Logging/Tracing (falls vorhanden) eingeschaltet

Output:
- Run Artefakte + Logs + Manifest

#### Canonical Commands (Verified)

**Python API (Orchestrator):**
```python
from src.ai_orchestration.orchestrator import Orchestrator
from src.ai_orchestration.evidence_pack import create_evidence_pack, save_evidence_pack
from src.ai_orchestration.models import AutonomyLevel
from pathlib import Path

# Initialize Orchestrator
orchestrator = Orchestrator(
    registry_path="config/model_registry.toml",
    capability_scopes_dir="config/capability_scopes/"
)

# Select models for layer
selection = orchestrator.select_model(
    layer_id="L4",  # Example: L0/L1/L2/L3/L4
    run_reason="Phase 4B M2 Proof"
)

# Create Evidence Pack
pack = create_evidence_pack(
    evidence_pack_id=f"EVP-4B-M2-{layer_id}-YYYYMMDD",
    phase_id="Phase4B-M2",
    layer_id=selection.layer_id,
    autonomy_level=selection.autonomy_level,
    registry_version="1.0",
    description="Milestone 2 PoC: Layer Run with Evidence Pack"
)

# Save Evidence Pack
output_path = Path(f"data/evidence_packs/EVP-4B-M2-{layer_id}-YYYYMMDD.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
save_evidence_pack(pack, output_path)
```

**Expected Artifact Paths:**
- Evidence Pack: `data&#47;evidence_packs&#47;EVP-<run_id>-<YYYYMMDD>.json`
- AI Model Logs: `logs&#47;ai_model_calls.jsonl` (if enabled in config)
- Run Manifest: Embedded in Evidence Pack JSON

**Note:** CLI wrapper script (gap; not yet implemented): `run_layer_evidence_pack.py` (Gap identified in Phase 4B M2 Discovery).

---

### Step E — Validate (CI_GUARDIAN)
**Ziel:** Evidence Pack + Run Artefakte gegen Schema/Policies validieren.

Checks:
- Schema Validation (hart)
- Required Fields (hart)
- Referenz-Targets / Docs Gates (hart, wenn Teil der CI)
- Audit / Dependency Security (hart, wenn Teil der CI)
- Optional: Policy Critic / Layer Smoke (soft → kann „warn" sein)

Output:
- Validator Report (pass/fail + Details)

#### Canonical Commands (Verified)

**Evidence Pack Validation (CLI):**

P5B Evidence Pack (manifest + SHA256):
```bash
# Generate pack from run output
python3 scripts/aiops/generate_evidence_pack.py \
  --base-dir out/ops --in "out/ops/p4c_runs/<run_id>" \
  --out-root out/ops/evidence_packs --pack-id p4c_<id> --deterministic

# Validate (manifest path required; no --latest)
manifest=$(ls -1t out/ops/evidence_packs/*/manifest.json | head -n 1)
python3 scripts/aiops/validate_evidence_pack.py --manifest "$manifest"
```

Legacy schema validator (single JSON file):
```bash
python3 scripts/validate_evidence_pack.py data/evidence_packs/EVP-001.json
python3 scripts/validate_evidence_pack.py data/evidence_packs/EVP-001.json --lenient
```

**Exit Codes:**
- `0` = Validation passed
- `1` = Validation failed
- `2` = File not found or invalid arguments

**CI Gate Verification (Local):**
```bash
# Lint Gate
ruff check src/ tests/ scripts/
ruff format --check src/ tests/ scripts/

# Audit Gate
pip-audit -f json -o pip_audit.json

# Docs Reference Targets Gate
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main

# Policy Critic Gate (if policy-relevant files changed)
python3 scripts/run_policy_critic.py --pr-mode

# Test Suite
python3 -m pytest tests/ai_orchestration/ -q
```

**Schema Reference:**
- Schema Definition: `src/ai_orchestration/evidence_pack.py`
- Mandatory Fields: `docs/governance/ai_autonomy/SCHEMA_MANDATORY_FIELDS.md`
- Template: `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md`

---

### Step F — Evidence Pack Finalize (EVIDENCE_SCRIBE)
**Ziel:** Evidence Pack finalisieren, indexieren und audit-tauglich ablegen.

Tasks:
- [ ] Evidence Pack canonicalize (stable ordering)
- [ ] Pack ID / schema_version / timestamps prüfen
- [ ] Evidence Index Entry aktualisieren
- [ ] Kurze human-readable Summary ergänzen

Output:
- Final Evidence Pack + Index Update

---

### Step G — Risk Review & Operator Sign-Off (RISK_OFFICER + ORCHESTRATOR)
**Ziel:** Risiko sauber dokumentieren und eine Empfehlung geben.

Format (kurz):
- Findings (max 5 bullets)
- Risks (likelihood × impact)
- Mitigations / Next actions
- Go/No-Go Empfehlung (mit Bedingungen)

Output:
- Operator Review Notes (Markdown)

---

## 5) Pass/Fail Kriterien (Milestone 2 Definition of Done)

### PASS wenn
- Evidence Pack existiert und validiert gegen Schema
- Run Manifest vollständig (Inputs, git_ref, tool versions)
- CI-Gates relevant zu Evidence/Docs/Audit sind grün
- Operator Notes enthalten klare Empfehlung + Risiken

### FAIL wenn
- Schema Validation failt
- Required Fields fehlen (pack_id, schema_version, git_ref, run_reason, operator_id)
- Artefakte nicht reproduzierbar oder Pfade/Outputs fehlen
- Governance verletzt (z.B. Live-Config geändert)

---

## 6) CI Gates Reference (Job Names)

**Diese Job-Namen müssen in CI grün sein (Branch Protection Required):**

### Primary Gates (Always Run on PRs)

| Workflow | Job Name (exact) | Purpose | Failure Impact |
|----------|------------------|---------|----------------|
| `lint_gate.yml` | `Lint Gate` | Ruff linting + format check | **BLOCKS MERGE** |
| `audit.yml` | `audit` | pip-audit + security checks | **BLOCKS MERGE** (if deps changed) |
| `policy_critic_gate.yml` | `Policy Critic Gate` | Policy compliance analysis | **BLOCKS MERGE** (if policy files changed) |
| `docs_reference_targets_gate.yml` | `docs-reference-targets-gate` | Docs link validation | **BLOCKS MERGE** (if docs changed) |
| `ci.yml` | `tests (3.11)` | Test suite Python 3.11 | **BLOCKS MERGE** |
| `ci.yml` | `strategy-smoke` | Strategy config smoke tests | **BLOCKS MERGE** |
| `ci.yml` | `ci-required-contexts-contract` | CI naming contract guard | **BLOCKS MERGE** |

### Secondary Gates (Optional for AI Autonomy Runs)

| Workflow | Job Name | Purpose |
|----------|----------|---------|
| `ci.yml` | `tests (3.9)` | Test suite Python 3.9 |
| `ci.yml` | `tests (3.10)` | Test suite Python 3.10 |
| `var_report_regression_gate.yml` | `VaR Report Regression Gate` | VaR report regression detection |
| `merge_log_hygiene.yml` | `Merge Log Hygiene` | Merge log format validation |

### Gate Behavior (Docs-Only PRs)

**On docs-only changes:**
- `tests (*)`: Skip gracefully (report SUCCESS/SKIPPED, not PENDING)
- `lint_gate.yml`: Skip if no Python files changed
- `policy_critic_gate.yml`: Skip if no policy-relevant files changed
- `docs_reference_targets_gate.yml`: Run if Markdown files changed

**Verification:**
```bash
# Check which gates will run
gh pr checks <PR_NUMBER>

# Watch gates live
gh pr checks <PR_NUMBER> --watch
```

---

## 7) Troubleshooting (schnell)

### Symptom: Evidence Pack Validation fail
- Prüfe `schema_version` passt zu Validator
- Prüfe required fields / types
- Prüfe canonicalization (ordering, json stability)

### Symptom: Docs Gates fail (Reference Targets / Link Debt)
- Identifiziere "false positives" (z.B. Branch-Namen wie Pfade)
- Fix: Escapes/Formatting/Policy-konforme Referenzen

### Symptom: Audit / pip-audit fail
- Dependency bump nach Policy
- Lockfile/uv sync prüfen
- Evidence: CVE ID + remediation commit

---

## 8) Operator Output Template (copy/paste)

### Operator Summary
- Run: <layer_id> / <model_id> / <scope>
- Git: <sha> (<branch>)
- Result: PASS/FAIL
- Top Findings: …
- Risks: …
- Recommendation: GO / NO-GO / GO-WITH-CONDITIONS

### Attached Evidence
- Evidence Pack: <path>
- Validator Report: <path>
- Logs/Manifest: <paths>

---

## 9) Change Log
- **2026-01-09 (v1.1):** Added verified canonical commands, CI gate reference, artifact paths (Discovery phase complete)
- **2026-01-09 (v1.0):** Initial draft for Phase 4B Milestone 2 (Cursor Multi-Agent operator loop)
