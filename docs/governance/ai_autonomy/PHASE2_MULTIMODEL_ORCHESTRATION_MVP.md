# Phase 2: Multi-Model Orchestration Framework MVP

**Status:** Implemented ✅  
**Date:** 2026-01-10  
**Scope:** P0 (Critical) — Foundation for Layer-based AI Autonomy  
**Risk:** 🟢 LOW (No live execution, no model API calls)

---

## Executive Summary

Phase 2 implementiert das **Multi-Model Orchestration Framework MVP** als Foundation für die Layer-based AI Autonomy (L0-L6).

**Was:** Orchestration Framework mit:
- TOML Config Loaders (Model Registry + Capability Scopes)
- SoD (Separation of Duties) Checker
- Run Manifest Generator (deterministische Artefakte)
- Multi-Model Runner mit Dry-Run Modus
- CLI Script für Operator

**Nicht:** Keine echten Modell-API Calls, keine Live-Execution, keine L6-Implementation

**Guardrails:** GOVERNANCE-LOCKED / NO-LIVE / Evidence-First / Deterministisch

---

## Purpose

### Ziel
Ermögliche **deterministisches Orchestration Testing** für AI Layer Runs ohne echte Model-API Calls.

### Non-Goals (explizit ausgeschlossen)
- ❌ Keine echten OpenAI/DeepSeek API Calls
- ❌ Keine Live-Trading Integration
- ❌ Keine L6 Execution Orchestrator Aktivierung
- ❌ Keine Änderungen an Trading/Execution Code

---

## Architecture

### Component Overview

```
src/ai_orchestration/
├── errors.py                      # Custom exceptions
├── model_registry_loader.py       # Lädt config/model_registry.toml
├── capability_scope_loader.py     # Lädt config/capability_scopes/*.toml
├── sod_checker.py                 # SoD validation (Proposer != Critic)
├── run_manifest.py                # Run Manifest dataclass + generator
├── runner.py                      # Multi-Model Runner (dry-run only)
└── models.py                      # Existing data models (Phase 1)

scripts/aiops/
└── run_layer_dry_run.py           # CLI für Operator

tests/ai_orchestration/
├── test_model_registry_loader.py
├── test_capability_scope_loader.py
├── test_sod_checker.py
└── test_runner_dry_run_manifest.py
```

---

## Artifacts

Jeder Layer Run erzeugt **zwei Artefakte** (Evidence-First):

### 1. Run Manifest (`run_manifest.json`)

```json
{
  "run_id": "L2-a1b2c3d4e5f6g7h8",
  "run_type": "dry-run",
  "timestamp": "2026-01-10T12:00:00+00:00",
  "layer_id": "L2",
  "layer_name": "Market Outlook",
  "autonomy_level": "PROP",
  "primary_model_id": "gpt-5.2-pro",
  "fallback_model_ids": ["gpt-5.2"],
  "critic_model_id": "deepseek-r1",
  "capability_scope_id": "L2_market_outlook",
  "capability_scope_version": "1.0",
  "sod_result": "PASS",
  "sod_reason": "SoD PASS: Proposer (gpt-5.2-pro) != Critic (deepseek-r1)",
  "sod_timestamp": "2026-01-10T12:00:00+00:00",
  "matrix_version": "v1.0",
  "registry_version": "1.0",
  "artifacts": [
    "out/run_manifest.json",
    "out/operator_output.md"
  ],
  "operator_output_path": "out/operator_output.md",
  "operator_notes": "",
  "inputs_manifest": [],
  "outputs_manifest": []
}
```

**Features:**
- **Deterministic `run_id`:** SHA256 hash von Layer + Models + Scope
- **Stable JSON:** Sortierte Keys für Diff-Vergleiche
- **SoD Audit Trail:** Proposer ≠ Critic validiert und dokumentiert

### 2. Operator Output (`operator_output.md`)

```markdown
# AI Autonomy — Operator Output (Kurzbericht)

**Run ID:** L2-a1b2c3d4e5f6g7h8  
**Run Type:** dry-run  
**Timestamp:** 2026-01-10T12:00:00+00:00  
**Layer:** L2 (Market Outlook)  
**Autonomy:** PROP

---

## Models

- **Primary:** gpt-5.2-pro
- **Fallback:** gpt-5.2
- **Critic:** deepseek-r1

---

## SoD Check

- **Result:** PASS
- **Reason:** SoD PASS: Proposer (gpt-5.2-pro) != Critic (deepseek-r1)

---

## Findings

- Keine Findings

---

## Actions

- Keine Actions erforderlich

---

**END OF OPERATOR OUTPUT**
```

---

## CLI Usage

### Beispiel: L2 Market Outlook Dry-Run

```bash
python3 scripts/aiops/run_layer_dry_run.py \
    --layer L2 \
    --primary gpt-5.2-pro \
    --critic deepseek-r1 \
    --out out/L2_dry_run
```

**Output:**
```
🔄 Starting dry-run for layer L2...
   Primary: gpt-5.2-pro
   Critic: deepseek-r1
   Output: out/L2_dry_run

✅ Dry-run completed successfully!

📋 Run Manifest:
   Run ID: L2-a1b2c3d4e5f6g7h8
   Layer: L2 (Market Outlook)
   Autonomy: PROP
   Primary: gpt-5.2-pro
   Critic: deepseek-r1
   SoD: PASS

📦 Artifacts:
   - out/L2_dry_run/run_manifest.json
   - out/L2_dry_run/operator_output.md

✅ SUCCESS: Dry-run validation passed
```

### Beispiel: L0 Ops/Docs Dry-Run

```bash
python3 scripts/aiops/run_layer_dry_run.py \
    --layer L0 \
    --primary gpt-5.2 \
    --critic deepseek-r1 \
    --out out/L0_dry_run \
    --notes "Testing L0 orchestration"
```

### Exit Codes

- **0:** Success
- **2:** Validation error (SoD, config, invalid layer)
- **3:** Unexpected error

---

## Validation Rules

### 1. Layer Validation
- Layer ID muss in `config/model_registry.toml` existieren (L0-L6)
- Capability Scope muss in `config/capability_scopes/` existieren

### 2. Model Validation
- Primary/Critic müssen in Model Registry existieren
- Modelle müssen `status = "production"` haben

### 3. SoD Check (Separation of Duties)
- **PASS:** `primary_model_id != critic_model_id`
- **FAIL:** `primary_model_id == critic_model_id` (Error: Exit Code 2)

### 4. Autonomy Level Check
- **EXEC:** Verboten (Error: Exit Code 2)
- **RO/REC/PROP:** Erlaubt (dry-run only)

### 5. Capability Scope Check
- Inputs/Outputs/Tooling müssen in Scope erlaubt sein
- Safety checks müssen vorhanden sein

---

## Design Decisions

### 1. Deterministic Run IDs
**Why:** Reproduzierbare Runs für Testing/Debugging
**How:** SHA256 hash von `layer_id + primary_model + critic_model + scope_id`

### 2. Stable JSON Key Ordering
**Why:** Git diffs für Manifest-Vergleiche
**How:** `json.dumps(data, sort_keys=True)`

### 3. No Model API Calls
**Why:** Governance-Locked / Cost Control / Determinismus
**How:** Dry-run validiert nur Orchestration, erzeugt keine echten Outputs

### 4. Injected Clock
**Why:** Deterministische Timestamps für Testing
**How:** `MultiModelRunner(clock=datetime(...))`

---

## Integration: Phase 3 (L2 Pilot)

Phase 2 legt Foundation für **Phase 3 (L2 Market Outlook Pilot)**:

### Phase 3 Next Steps
1. **Extend Runner:** `live_run()` Modus mit echten Model-API Calls
2. **Capability Scope Enforcement:** Runtime validation von Inputs/Outputs
3. **Evidence Pack Integration:** Run Manifest → Evidence Pack Template v2
4. **30-Day Pilot:** L2 Runs mit Operator Review Loop

### Phase 3 Dependencies (aus Phase 2)
- ✅ Model Registry Loader
- ✅ Capability Scope Loader
- ✅ SoD Checker
- ✅ Run Manifest Generator
- ✅ CLI Script für Operator

---

## Testing

### Unit Tests (alle PASS ✅)

```bash
python3 -m pytest tests/ai_orchestration/test_model_registry_loader.py -v
python3 -m pytest tests/ai_orchestration/test_capability_scope_loader.py -v
python3 -m pytest tests/ai_orchestration/test_sod_checker.py -v
python3 -m pytest tests/ai_orchestration/test_runner_dry_run_manifest.py -v
```

### Dry-Run Tests

```bash
# L2 Market Outlook
python3 scripts/aiops/run_layer_dry_run.py \
    --layer L2 \
    --primary gpt-5.2-pro \
    --critic deepseek-r1 \
    --out test_runs/L2_dry_run

# L0 Ops/Docs
python3 scripts/aiops/run_layer_dry_run.py \
    --layer L0 \
    --primary gpt-5.2 \
    --critic deepseek-r1 \
    --out test_runs/L0_dry_run

# L4 Governance Critic
python3 scripts/aiops/run_layer_dry_run.py \
    --layer L4 \
    --primary o3-pro \
    --critic gpt-5.2-pro \
    --out test_runs/L4_dry_run
```

---

## Guardrails Compliance

### ✅ NO-LIVE
- Keine echten Model-API Calls
- Dry-run Modus: nur Validation + Artifact Generation
- L6 Execution: `ForbiddenAutonomyError` (hard block)

### ✅ Evidence-First
- Jeder Run erzeugt Run Manifest + Operator Output
- Artifacts pfad-stabil (keine temporären lokalen Pfade)

### ✅ Determinism
- Run ID: deterministisch (SHA256 hash)
- Timestamps: injizierbar für Testing
- JSON: stabile Key-Ordering

### ✅ Separation of Duties
- SoD Check: Proposer != Critic (enforced)
- Proposer/Critic Provider Diversity (optional)

---

## Risk Assessment

### 🟢 LOW RISK

**Why:**
- Keine Live-Execution
- Keine echten Model-API Calls
- Keine Änderungen an Trading/Execution Code
- Docs-only + Config-only + Tests

**Mitigations:**
- Unit Tests: alle PASS
- CLI Exit Codes: klare Fehlerbehandlung
- Guardrails: SoD + EXEC forbidden enforced

---

## References

- **Authoritative Matrix:** `docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md`
- **Model Registry:** `config/model_registry.toml`
- **Capability Scopes:** `config&#47;capability_scopes&#47;*.toml`
- **Phase 1 Summary:** `PHASE_AI_AUTONOMY_LAYER_MAP_V1_SUMMARY.md`
- **Governance Rules:** `.cursor/rules/peak-trade-governance.mdc`

---

## Change Log

- **v1.0 (2026-01-10):** Initial MVP implementation
  - Model Registry Loader
  - Capability Scope Loader
  - SoD Checker
  - Run Manifest Generator
  - Multi-Model Runner (dry-run only)
  - CLI Script
  - Tests (all PASS)
  - Documentation

---

**STATUS:** ✅ Phase 2 Complete (MVP)  
**NEXT:** Phase 3 Kick-off (L2 Market Outlook Pilot mit echten Model Calls)
