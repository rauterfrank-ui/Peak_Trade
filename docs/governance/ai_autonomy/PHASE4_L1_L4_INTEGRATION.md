# Phase 4: L1 DeepResearch + L4 Governance Integration

**Status:** Phase 4A Implemented ✅ | Phase 4B Planning  
**Date:** 2026-01-10  
**Scope:** P0 (Critical) — Research Layer + Governance Critic Integration  
**Risk:** 🟢 LOW (Phase 4A: Offline/Replay only) | 🟡 MEDIUM (Phase 4B: Real Model Calls)

---

## Executive Summary

Phase 4 extends the AI Autonomy framework with:
- **Phase 4A:** L1 DeepResearch Runner (offline/replay, CI-safe)
- **Phase 4B:** L4 Governance Critic integration (planned)

**What's in Phase 4A:**
- L1 Runner with Record/Replay fixtures
- Evidence Pack generation + validation
- SoD Enforcement (Proposer ≠ Critic)
- Capability Scope Enforcement (research-only outputs)
- CLI script for operators

**Not in Phase 4A:**
- Real model API calls (offline/replay only)
- L4 Governance Critic runner (Phase 4B)
- Live-mode execution

**Guardrails:** NO-LIVE / Evidence-First / Determinism (CI) / SoD / Capability Scope

---

## 1. Purpose

### Goals (Phase 4A)
Implement L1 DeepResearch Runner on the same quality level as L2 Market Outlook:
- Deterministic offline/replay mode for CI
- Opt-in network mode for operator recording
- Evidence Pack generation with full audit trail
- SoD and Capability Scope enforcement

### Goals (Phase 4B - Planned)
- L4 Governance Critic runner
- L1 ↔ L4 integration (L4 reviews L1 outputs)
- Cross-layer evidence chain

---

## 2. Architecture

### 2.1 Component Overview (Phase 4A)

```
src/ai_orchestration/
├── l1_runner.py                   # NEW: L1 DeepResearch Runner
├── l2_runner.py                   # Existing: L2 Market Outlook
├── model_client.py                # Shared: Replay/Live client
├── transcript_store.py            # Shared: Record/Replay fixtures
├── evidence_pack_generator.py     # Shared: Evidence Pack bundle
├── capability_scope_loader.py     # Shared: Scope enforcement
├── model_registry_loader.py       # Shared: Model registry
├── sod_checker.py                 # Shared: SoD validation
└── run_manifest.py                # Shared: Run manifest generation

scripts/aiops/
├── run_l1_deepresearch.py         # NEW: L1 CLI
└── run_l2_market_outlook.py       # Existing: L2 CLI

tests/ai_orchestration/
├── test_l1_runner.py              # NEW: L1 Runner tests
└── test_l2_runner.py              # Existing: L2 Runner tests

tests/fixtures/transcripts/
├── l1_deepresearch_sample.json    # NEW: L1 fixture
└── l2_market_outlook_sample.json  # Existing: L2 fixture

config/capability_scopes/
├── L1_deep_research.toml          # Existing: L1 scope
└── L2_market_outlook.toml         # Existing: L2 scope
```

---

## 3. L1 DeepResearch Runner

### 3.1 Layer Specification

**From Authoritative Matrix:**
- **Layer ID:** L1
- **Layer Name:** DeepResearch
- **Autonomy Level:** PROP (Propose)
- **Primary Model:** o3-deep-research (OpenAI)
- **Fallback Models:** o4-mini-deep-research, deepseek-r1
- **Critic Model:** o3-pro (OpenAI)
- **Capability Scope:** config/capability_scopes/L1_deep_research.toml

**Purpose:**
- Literature review
- Methodology research
- Evidence synthesis
- Best practices documentation

**NOT Allowed:**
- Execution instructions
- Live trading advice
- Portfolio changes
- Risk limit modifications

### 3.2 Capability Scope Enforcement

**Allowed Outputs:**
- ResearchReport
- LiteratureReview
- MethodologyProposal
- EvidenceSummary
- BestPracticesGuide
- CitationList

**Forbidden Outputs:**
- ExecutionCommand
- ConfigChange
- LiveToggle
- OrderParameters
- RiskLimitChange

**Validation Rules:**
- Minimum 3 citations required
- Limitations statement mandatory
- No execution keywords allowed
- Research-only classification

### 3.3 SoD (Separation of Duties)

**Enforced:**
- Proposer: o3-deep-research
- Critic: o3-pro
- **SoD Check:** o3-deep-research ≠ o3-pro → PASS

**Rationale:**
- Different model families prevent self-review
- o3-pro provides conservative reasoning for research validation
- Hard block if Proposer == Critic

---

## 4. Usage

### 4.1 Offline/Replay Mode (CI-Safe, Default)

**Use Case:** CI testing, deterministic validation, operator review

```bash
# Replay mode with fixture ID (recommended)
python scripts/aiops/run_l1_deepresearch.py \
    --question "What are the best practices for VaR backtesting?" \
    --mode replay \
    --fixture l1_deepresearch_sample \
    --out evidence_packs/L1_demo

# Replay mode with full transcript path
python scripts/aiops/run_l1_deepresearch.py \
    --question "Research momentum factor literature" \
    --mode replay \
    --transcript tests/fixtures/transcripts/l1_deepresearch_sample.json \
    --out evidence_packs/L1_var_research
```

**Behavior:**
- ✅ No network calls
- ✅ Deterministic outputs (CI green)
- ✅ Uses pre-recorded transcript fixtures
- ✅ Evidence Pack generated
- ✅ SoD + Capability Scope checks run

### 4.2 Network Mode with Recording (Operator Only)

**⚠️ WARNING:** Real model API calls will be made. Costs will be incurred.

**Use Case:** Operator recording new fixtures for CI

```bash
# Record mode (allow-network + record)
# NOT YET IMPLEMENTED IN CLI (Phase 4B)
# Will require:
# - OPENAI_API_KEY environment variable
# - --allow-network flag
# - --record flag to save transcript

# Example (future):
# export OPENAI_API_KEY="sk-..."
# python scripts/aiops/run_l1_deepresearch.py \
#     --question "Research VaR backtesting" \
#     --allow-network \
#     --record \
#     --out evidence_packs/L1_live_recording
```

**NOT Implemented Yet:** Live/Record modes are planned for Phase 4B.

---

## 5. Evidence Pack Structure

Each L1 run generates an Evidence Pack with 7 artifacts:

```
evidence_packs/L1_DEEPRESEARCH_20260110_120000/
├── evidence_pack.json              # Bundle (all artifacts combined)
├── run_manifest.json               # Run metadata + timestamps
├── operator_output.md              # Human-readable summary
├── proposer_output.json            # Proposer (o3-deep-research) output
├── critic_output.json              # Critic (o3-pro) output
├── sod_check.json                  # SoD validation result
└── capability_scope_check.json     # Capability scope validation
```

### 5.1 Evidence Pack Fields (JSON)

```json
{
  "evidence_pack_id": "EVP-L1-20260110_120000-a1b2c3d4",
  "layer_id": "L1",
  "layer_name": "DeepResearch",
  "run_id": "L1-sha256hash",
  "mode": "replay",
  "network_used": false,
  "sod_result": "PASS",
  "capability_scope_result": "PASS",
  "proposer_model_id": "o3-deep-research",
  "critic_model_id": "o3-pro",
  "research_question": "What are the best practices for VaR backtesting?",
  "run_manifest": { ... },
  "proposer": { ... },
  "critic": { ... },
  "sod_check": { ... },
  "capability_scope_check": { ... },
  "artifacts": [ ... ],
  "operator_notes": "",
  "findings": [],
  "actions": []
}
```

---

## 6. CI/Testing

### 6.1 Determinism Strategy

**CI Must Remain Green:**
- All tests run in **replay mode** (no network)
- Fixed clock injection for deterministic timestamps
- Stable hashing for run_id generation
- Pre-recorded transcripts in `tests/fixtures/transcripts/`

### 6.2 Test Coverage

**Tests (tests/ai_orchestration/test_l1_runner.py):**
- ✅ Replay mode success
- ✅ Proposer output structure
- ✅ Critic output structure
- ✅ SoD check (o3-deep-research ≠ o3-pro)
- ✅ Capability scope check (citations, limitations)
- ✅ Deterministic run_id generation
- ✅ Evidence Pack JSON structure
- ✅ Findings and actions
- ✅ Error cases (missing transcript, empty question)

### 6.3 Running Tests

```bash
# Run all L1 tests
pytest tests/ai_orchestration/test_l1_runner.py -v

# Run specific test
pytest tests/ai_orchestration/test_l1_runner.py::test_l1_runner_replay_mode_success -v

# Run with coverage
pytest tests/ai_orchestration/test_l1_runner.py --cov=src/ai_orchestration/l1_runner
```

---

## 7. Risk Analysis

### 7.1 Phase 4A Risk: 🟢 LOW (Offline/Replay)

**Why Low:**
- No real model API calls
- No network access required
- Deterministic, reproducible outputs
- Evidence Pack fully auditable
- NO-LIVE enforcement (no execution pathways)

**Mitigations:**
- All tests run offline
- Capability Scope enforces research-only outputs
- SoD check hard-blocks self-review
- Forbidden keywords detection

### 7.2 Phase 4B Risk (Planned): 🟡 MEDIUM (Real Model Calls)

**Threats (when network mode enabled):**
- Model API costs
- Non-deterministic outputs (model drift)
- Potential for unexpected research outputs

**Mitigations (Phase 4B):**
- Opt-in `--allow-network` flag (explicit)
- Budget limits in model registry
- Rate limiting (50 requests/hour for L1)
- Record/Replay captures for CI determinism
- Capability Scope enforcement remains active

---

## 8. Verification

### 8.1 Operator Verification Steps

**Step 1: Offline Run**
```bash
python scripts/aiops/run_l1_deepresearch.py \
    --question "Research VaR backtesting best practices" \
    --mode replay \
    --fixture l1_deepresearch_sample \
    --out evidence_packs/L1_verify
```

**Expected Output:**
```
✅ L1 DeepResearch run completed successfully!
  Run ID: L1-a1b2c3d4e5f6
  Evidence Pack ID: EVP-L1-20260110_120000-a1b2c3d4
  Mode: replay
  SoD: PASS
  Capability Scope: PASS
  Proposer: o3-deep-research
  Critic: o3-pro (Decision: APPROVE_WITH_CHANGES)
  Artifacts: 7 files
```

**Step 2: Validate Evidence Pack**
```bash
# Check evidence pack structure
ls -lh evidence_packs/L1_verify/

# Validate JSON
python -m json.tool evidence_packs/L1_verify/evidence_pack.json > /dev/null
echo "✅ Evidence Pack JSON valid"

# Check SoD
jq '.sod_result' evidence_packs/L1_verify/evidence_pack.json
# Expected: "PASS"

# Check Capability Scope
jq '.capability_scope_result' evidence_packs/L1_verify/evidence_pack.json
# Expected: "PASS"
```

### 8.2 CI Verification

**GitHub Actions:** Tests run automatically on PR
```yaml
# .github/workflows/ci.yml (excerpt)
- name: Run L1 Runner Tests
  run: pytest tests/ai_orchestration/test_l1_runner.py -v
```

**Expected CI Behavior:**
- ✅ All tests green (offline/replay)
- ✅ No network calls
- ✅ Deterministic outputs
- ✅ Evidence Packs validated

---

## 9. Phase 4B: L4 Governance Critic Integration (Planned)

### 9.1 Goals
- Implement L4 Governance Critic Runner
- L4 reviews L1 research outputs for policy compliance
- Cross-layer evidence chain (L1 → L4 → Evidence Pack)

### 9.2 Architecture (Planned)
```
src/ai_orchestration/
└── l4_runner.py                   # NEW: L4 Governance Critic Runner

scripts/aiops/
└── run_l4_governance_critic.py    # NEW: L4 CLI
```

### 9.3 Integration Pattern
```bash
# Step 1: L1 Research
python scripts/aiops/run_l1_deepresearch.py \
    --question "Research VaR backtesting" \
    --out evidence_packs/L1_var_research

# Step 2: L4 Governance Review (Phase 4B)
# python scripts/aiops/run_l4_governance_critic.py \
#     --input evidence_packs/L1_var_research/evidence_pack.json \
#     --out evidence_packs/L4_governance_review
```

---

## 10. Operator How-To (1-Screen Cheatsheet)

### 10.1 Quick Start: Offline/Replay (Default, CI-Safe)

**✅ Recommended:** Offline mode, no network, deterministic

```bash
# Basic replay with fixture
python scripts/aiops/run_l1_deepresearch.py \
    --question "What are the best practices for VaR backtesting?" \
    --mode replay \
    --fixture l1_deepresearch_sample \
    --out evidence_packs/L1_var_research

# With operator notes and findings
python scripts/aiops/run_l1_deepresearch.py \
    --question "Research momentum factor literature" \
    --mode replay \
    --fixture l1_deepresearch_sample \
    --notes "Research for strategy improvement" \
    --finding "Citation quality excellent" \
    --action "Review quantitative details" \
    --out evidence_packs/L1_momentum
```

**Behavior:**
- ✅ No network calls
- ✅ No API costs
- ✅ Deterministic (CI green)
- ✅ Evidence Pack generated
- ✅ SoD + Capability Scope validated

**Output Location:** `evidence_packs/L1_*/` (7 files)

---

### 10.2 Evidence Pack Validation

**After run, validate Evidence Pack:**

```bash
# Check artifacts exist
ls evidence_packs/L1_var_research/
# Expected: 7 files (evidence_pack.json, run_manifest.json, etc.)

# Validate JSON structure
python -m json.tool evidence_packs/L1_var_research/evidence_pack.json > /dev/null
echo "✅ Evidence Pack JSON valid"

# Check SoD result
jq '.sod_check.result' evidence_packs/L1_var_research/evidence_pack.json
# Expected: "PASS"

# Check Capability Scope result
jq '.capability_scope_check.result' evidence_packs/L1_var_research/evidence_pack.json
# Expected: "PASS"

# Check citations count
jq '.proposer.content' evidence_packs/L1_var_research/evidence_pack.json | grep -o "\[Source:" | wc -l
# Expected: ≥ 3 citations
```

---

### 10.3 ⚠️ Allow-Network + Record Mode (Operator Only, NOT IMPLEMENTED)

**Status:** 🚫 NOT AVAILABLE IN PHASE 4A

**Planned for Phase 4B:**
- Real model API calls (o3-deep-research, o3-pro)
- Costs incurred (~$0.025/1K input, $0.100/1K output)
- Non-deterministic outputs
- Requires `OPENAI_API_KEY` environment variable

**Intended Usage (Phase 4B):**
```bash
# NOT IMPLEMENTED YET
# export OPENAI_API_KEY="sk-..."
# python scripts/aiops/run_l1_deepresearch.py \
#     --question "Research VaR backtesting" \
#     --allow-network \
#     --record \
#     --out evidence_packs/L1_live_recording
```

**Risks:**
- 🔴 Real API costs
- 🔴 Model drift (non-deterministic)
- 🔴 Network dependency

**Mitigations (Phase 4B):**
- Explicit `--allow-network` flag required
- Budget limits enforced
- Rate limiting (50 req/hour)
- Record/Replay for CI determinism

---

### 10.4 Troubleshooting

**Issue: Fixture not found**
```bash
❌ ERROR: Fixture not found: l1_deepresearch_xyz
```

**Solution:** Check available fixtures
```bash
ls tests/fixtures/transcripts/
# Expected:
# - l1_deepresearch_sample.json
# - l2_market_outlook_sample.json
```

**Issue: SoD Violation**
```bash
❌ VALIDATION ERROR: SoD Violation
   SoD check failed: Proposer (o3-pro) must be different from Critic (o3-pro).
```

**Solution:** This indicates a config error. L1 should use:
- Proposer: o3-deep-research
- Critic: o3-pro

Check `config/model_registry.toml` and `config/capability_scopes/L1_deep_research.toml`.

**Issue: Capability Scope Violation**
```bash
❌ VALIDATION ERROR: Capability Scope Violation
   Forbidden keyword detected: ExecutionCommand
```

**Solution:** The proposer output contained forbidden keywords. This is expected behavior (hard block). Review the research prompt to avoid execution-related language.

---

## 11. Next Steps

### Phase 4A: Complete ✅
- [x] L1 Runner implementation
- [x] CLI script (`run_l1_deepresearch.py`)
- [x] Sample fixture (`l1_deepresearch_sample.json`)
- [x] Tests (`test_l1_runner.py`)
- [x] Documentation (this file)

### Phase 4B: Planned
- [ ] L4 Governance Critic Runner
- [ ] L4 CLI script
- [ ] L4 sample fixtures
- [ ] L4 tests
- [ ] L1 ↔ L4 integration
- [ ] Cross-layer evidence chain
- [ ] Live/Record mode implementation for L1

---

## 12. References

- **Authoritative Matrix:** `docs/governance/ai_autonomy/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md`
- **Model Registry:** `config/model_registry.toml`
- **L1 Capability Scope:** `config/capability_scopes/L1_deep_research.toml`
- **Phase 2 (Orchestration MVP):** `docs/governance/ai_autonomy/PHASE2_MULTIMODEL_ORCHESTRATION_MVP.md`
- **Phase 3 (L2 Pilot):** `docs/governance/ai_autonomy/PHASE3_L2_MARKET_OUTLOOK_PILOT.md`
- **Control Center Operations:** `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md`

---

**Last Updated:** 2026-01-10  
**Phase:** 4A (Implementation Complete)  
**Status:** ✅ READY FOR PR
