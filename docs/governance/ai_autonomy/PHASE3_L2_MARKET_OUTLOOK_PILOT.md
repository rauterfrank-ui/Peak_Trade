# Phase 3: L2 Market Outlook Pilot (P0)

**Status:** Implementation Ready  
**Date:** 2026-01-10  
**Scope:** P0 (Critical) — Real Model Calls with Governance Controls  
**Risk:** 🟡 MEDIUM (Real API calls, but NO-LIVE enforced)

---

## Executive Summary

Phase 3 implementiert den **L2 Market Outlook Pilot** mit echten Model-API Calls (OpenAI), aber unter strikten Governance-Controls:

**Was:** L2 Runner mit:
- Real Model Calls (OpenAI API) via Opt-In Flag (`--allow-network`)
- Record/Replay Fixtures für deterministisches CI Testing
- Evidence Pack Generation (Run Manifest + Operator Report + Bundle)
- SoD Enforcement (Proposer ≠ Critic)
- Capability Scope Enforcement (L2 darf nur erlaubte Outputs erzeugen)

**Nicht:** Keine Live-Trading Integration, keine L6 Execution, keine Portfolio-Changes

**Guardrails:** NO-LIVE / Evidence-First / Determinism (CI) / SoD / Capability Scope

---

## 1. Threat Model

### 1.1 Threats Identified

| Threat ID | Threat | Impact | Mitigation |
|-----------|--------|--------|------------|
| **T1** | Model outputs unexpected/harmful recommendations | 🔴 HIGH | Capability Scope Enforcement: L2 kann KEINE Execution Commands erzeugen |
| **T2** | Model API unavailable → Pilot fails | 🟡 MEDIUM | Replay Fixtures: CI bleibt deterministisch ohne Netzwerk |
| **T3** | API credentials leaked | 🔴 HIGH | Secrets nie in Code/Fixtures; nur ENV vars; CI nutzt ReplayClient |
| **T4** | Cost explosion (too many API calls) | 🟡 MEDIUM | Budget Limits (Registry); Rate Limiting; Operator Review |
| **T5** | SoD bypassed (Proposer == Critic) | 🔴 HIGH | SoD Check (hard block) in Runner; Tests validieren |
| **T6** | Evidence Pack tampered | 🟡 MEDIUM | Hash-based integrity; Immutable artifacts; Audit logging |
| **T7** | Model drift (behavior changes over time) | 🟡 MEDIUM | 30-Day Pilot: Track KPIs, drift notes, version pinning |

### 1.2 Threat Mitigation Summary

- **T1, T5:** Enforced via Capability Scope + SoD Checker (hard blocks)
- **T2, T3:** Replay Fixtures + Secrets management (ENV only)
- **T4:** Budget limits + Operator review loop
- **T6, T7:** Evidence Pack hashing + 30-Day evaluation

---

## 2. Determinism Strategy (Record/Replay)

### 2.1 CI Must Remain Deterministic

**Problem:** Real model API calls sind nicht-deterministisch (Netzwerk, Model-Drift)

**Solution:** Record/Replay Fixtures

### 2.2 Modes

| Mode | Network | API Calls | Fixtures | Use Case |
|------|---------|-----------|----------|----------|
| **`dry`** (default) | ❌ No | ❌ No | ✅ Read-only | CI, Testing, Validation |
| **`replay`** | ❌ No | ❌ No | ✅ Read-only | Operator Review (offline) |
| **`record`** | ✅ Yes | ✅ Yes | ✅ Write | Operator Recording (einmalig) |
| **`live`** | ✅ Yes | ✅ Yes | ❌ No | 30-Day Pilot (daily runs) |

### 2.3 Transcript Store Format

**Fixture:** `tests/fixtures/transcripts/l2_market_outlook_<scenario>.json`

```json
{
  "transcript_id": "l2-market-outlook-sample-2026-01-10",
  "recorded_at": "2026-01-10T12:00:00+00:00",
  "scenario": "market-outlook-baseline",
  "runs": [
    {
      "run_id": "proposer-run-001",
      "role": "proposer",
      "model_id": "gpt-5.2-pro",
      "prompt_hash": "sha256:abc123...",
      "request": {
        "model": "gpt-5.2-pro",
        "messages": [...],
        "temperature": 0.7,
        "max_tokens": 4000
      },
      "response": {
        "id": "chatcmpl-xyz",
        "choices": [
          {
            "message": {
              "role": "assistant",
              "content": "..."
            },
            "finish_reason": "stop"
          }
        ],
        "usage": {
          "prompt_tokens": 1234,
          "completion_tokens": 567,
          "total_tokens": 1801
        }
      },
      "metadata": {
        "timestamp": "2026-01-10T12:00:01+00:00",
        "latency_ms": 2345
      }
    },
    {
      "run_id": "critic-run-001",
      "role": "critic",
      "model_id": "deepseek-r1",
      "prompt_hash": "sha256:def456...",
      "request": {...},
      "response": {...},
      "metadata": {...}
    }
  ]
}
```

**Features:**
- **Stable Ordering:** Sortierte Keys (deterministisch)
- **Hash-based:** `prompt_hash` für Replay-Lookup
- **Minimal:** Nur notwendige Felder (keine Secrets)

---

## 3. Network Opt-In Policy

### 3.1 Default: No Network

**CI Mode:** Nutzt `ReplayClient` (keine Netzwerk-Calls)

```bash
# CI-safe (default)
python3 scripts/aiops/run_l2_market_outlook.py \
    --mode replay \
    --fixture tests/fixtures/transcripts/l2_market_outlook_sample.json
```

### 3.2 Opt-In: Network Required

**Live Mode:** Erfordert `--allow-network` Flag

```bash
# Live mode (explicit opt-in)
python3 scripts/aiops/run_l2_market_outlook.py \
    --mode live \
    --allow-network \
    --out live_runs/l2_pilot/2026-01-10
```

**Guardrail Banner:**
```
🚨 WARNING: NETWORK MODE ENABLED 🚨
- Real OpenAI API calls will be made
- Costs will be incurred ($$$)
- NO-LIVE trading remains enforced
- Evidence Pack will be generated

Press ENTER to continue or Ctrl-C to abort...
```

### 3.3 Record Mode (One-Time)

**Record Mode:** Operator nimmt Fixture auf (einmalig)

```bash
# Record mode (operator only)
python3 scripts/aiops/run_l2_market_outlook.py \
    --mode record \
    --allow-network \
    --fixture tests/fixtures/transcripts/l2_market_outlook_new.json \
    --out test_runs/l2_record
```

---

## 4. Evidence Pack Schema

### 4.1 Evidence Pack Bundle

Jeder L2 Run erzeugt ein **Evidence Pack Bundle**:

```
evidence_packs/
└── L2_MARKET_OUTLOOK_2026-01-10_001/
    ├── evidence_pack.json        # Bundle metadata
    ├── run_manifest.json          # Run Manifest (Phase 2)
    ├── operator_output.md         # Operator Report (Phase 2)
    ├── proposer_output.json       # Proposer Model Output
    ├── critic_output.json         # Critic Model Output
    ├── sod_check.json             # SoD Check Result
    ├── capability_scope_check.json # Capability Scope Validation
    └── transcript.json            # Optional: Transcript (if recorded)
```

### 4.2 Evidence Pack Metadata (`evidence_pack.json`)

```json
{
  "evidence_pack_id": "EVP-L2-2026-01-10-001",
  "evidence_pack_version": "2.0",
  "creation_timestamp": "2026-01-10T12:00:00+00:00",
  "layer_id": "L2",
  "layer_name": "Market Outlook",
  "run_id": "L2-df1ed6edc6255948",
  "mode": "live",
  "network_used": true,
  "proposer": {
    "model_id": "gpt-5.2-pro",
    "run_id": "proposer-run-001",
    "prompt_hash": "sha256:abc123...",
    "output_hash": "sha256:xyz789...",
    "artifact_path": "proposer_output.json"
  },
  "critic": {
    "model_id": "deepseek-r1",
    "run_id": "critic-run-001",
    "prompt_hash": "sha256:def456...",
    "output_hash": "sha256:uvw012...",
    "artifact_path": "critic_output.json"
  },
  "sod_check": {
    "result": "PASS",
    "reason": "Proposer (gpt-5.2-pro) != Critic (deepseek-r1)",
    "artifact_path": "sod_check.json"
  },
  "capability_scope_check": {
    "result": "PASS",
    "violations": [],
    "artifact_path": "capability_scope_check.json"
  },
  "artifacts": [
    "run_manifest.json",
    "operator_output.md",
    "proposer_output.json",
    "critic_output.json",
    "sod_check.json",
    "capability_scope_check.json"
  ],
  "operator_notes": "",
  "matrix_version": "v1.0",
  "registry_version": "1.0"
}
```

---

## 5. SoD Rules (Phase 3)

### 5.1 SoD Requirements

1. **Proposer != Critic:** Different model IDs (hard block)
2. **Provider Diversity (optional):** Different providers (OpenAI vs DeepSeek)
3. **Critic validates Proposer output:** Critic must reference Proposer artifact
4. **Evidence IDs required:** Critic must provide evidence IDs

### 5.2 SoD Enforcement

```python
# In L2Runner
sod_check = sod_checker.check(
    proposer_model_id="gpt-5.2-pro",
    critic_model_id="deepseek-r1",
)

if sod_check.result == SoDResult.FAIL:
    raise SoDViolationError(sod_check.reason)
```

---

## 6. Capability Scope Enforcement

### 6.1 L2 Capability Scope (from Phase 2)

**Allowed Outputs:**
- `ScenarioReport`
- `RegimeClassification`
- `NoTradeTriggers`
- `RiskContext`
- `MacroOutlook`
- `UncertaintyAssessment`

**Forbidden Outputs:**
- `OrderParameters` ❌
- `ExecutionCommand` ❌
- `RiskLimitChange` ❌
- `LiveToggle` ❌
- `PortfolioRebalance` ❌

### 6.2 Runtime Enforcement

```python
# In L2Runner
scope = scope_loader.load("L2")

# Validate proposer output
for output_type in proposer_outputs:
    if output_type in scope.outputs_forbidden:
        raise CapabilityScopeViolation(
            f"L2 cannot produce {output_type}"
        )
```

---

## 7. 30-Day Pilot Evaluation

### 7.1 Pilot Goals

1. **Validate SoD:** Proposer ≠ Critic in allen Runs
2. **Validate Capability Scope:** Keine Execution Commands
3. **Track Model Drift:** Baseline vs Day 30
4. **Operator Feedback:** Review Workflow, Clarity, Usefulness

### 7.2 Minimal KPIs

| KPI | Metric | Threshold | Frequency |
|-----|--------|-----------|-----------|
| **SoD Compliance** | % Runs mit SoD PASS | 100% | Daily |
| **Scope Compliance** | % Runs ohne Violations | 100% | Daily |
| **Operator Review Time** | Minutes per Run | < 15 min | Daily |
| **Evidence Pack Completeness** | % Complete Packs | 100% | Daily |
| **Model Drift** | Baseline vs Current | < 10% deviation | Weekly |

### 7.3 Drift Notes

**Baseline:** Day 1 Run (Fixed Prompt)  
**Weekly Check:** Re-run same prompt, compare outputs  
**Drift Threshold:** > 10% token-level difference → Flag for review

---

## 8. Implementation Architecture

### 8.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ CLI: run_l2_market_outlook.py                               │
│ Flags: --mode [dry|replay|record|live] --allow-network     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ L2Runner                                                     │
│ - Load Registry + Scope                                     │
│ - SoD Check                                                  │
│ - Orchestrate Proposer + Critic                             │
│ - Capability Scope Enforcement                               │
│ - Evidence Pack Generation                                   │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
             ▼                                ▼
┌────────────────────────┐      ┌────────────────────────────┐
│ ModelClient (Interface)│      │ TranscriptStore            │
│                        │      │ - Load/Save Fixtures       │
│ ┌────────────────────┐ │      │ - Deterministic Replay     │
│ │ OpenAIClient       │ │      └────────────────────────────┘
│ │ (real API calls)   │ │
│ └────────────────────┘ │
│                        │
│ ┌────────────────────┐ │
│ │ ReplayClient       │ │
│ │ (offline fixtures) │ │
│ └────────────────────┘ │
└────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ Evidence Pack Generator                                      │
│ - Bundle artifacts                                           │
│ - Generate evidence_pack.json                                │
│ - Hash all artifacts                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Guardrails Compliance

### ✅ NO-LIVE
- L2 kann KEINE Execution Commands erzeugen (Capability Scope)
- Keine Änderungen an `src/execution/**`
- Keine Änderungen an Portfolio/Risk Configs

### ✅ Evidence-First
- Jeder Run erzeugt Evidence Pack Bundle
- Alle Artifacts hash-basiert
- Audit Trail vollständig

### ✅ Determinism (CI)
- Default Mode: `replay` (keine Netzwerk-Calls)
- CI Tests nutzen ReplayClient
- Fixtures deterministisch (sortierte Keys)

### ✅ SoD
- Proposer ≠ Critic (hard block)
- Evidence IDs required
- Audit Trail in Evidence Pack

### ✅ Capability Scope
- Runtime Enforcement
- Forbidden Outputs: hard block
- Audit Logging bei Violations

---

## 10. Risk Assessment

### 🟡 MEDIUM RISK

**Warum:**
- ✅ Real Model API Calls (kontrolliert via Opt-In)
- ✅ Secrets erforderlich (ENV only, nie in Code)
- ✅ Kosten (Budget Limits + Operator Review)
- ✅ Model Drift (30-Day Evaluation)

**Mitigiert durch:**
- ✅ Replay Fixtures: CI bleibt deterministisch
- ✅ Guardrail Banner: explizite Warnung bei `--allow-network`
- ✅ Capability Scope: KEINE Execution Commands
- ✅ SoD Enforcement: Proposer ≠ Critic
- ✅ Evidence Pack: vollständiger Audit Trail

**Critical Constraint:**
- **L6 Execution bleibt verboten** (keine Änderung)

---

## 11. References

- **Phase 2 MVP:** `PHASE2_MULTIMODEL_ORCHESTRATION_MVP.md`
- **Model Registry:** `config/model_registry.toml`
- **Capability Scopes:** `config/capability_scopes/L2_market_outlook.toml`
- **Evidence Pack Template v2:** `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md`
- **Governance Rules:** `.cursor/rules/peak-trade-governance.mdc`

---

## 12. Artifact Structure & Determinism Guarantees

### 12.1 Evidence Pack Artifacts

Every L2 run generates the following artifacts in a deterministic, reproducible manner:

| Artifact | Format | Determinism | Purpose |
|----------|--------|-------------|---------|
| `evidence_pack.json` | JSON (sorted keys) | ✅ Deterministic | Bundle metadata + index |
| `run_manifest.json` | JSON (sorted keys) | ✅ Deterministic | Run metadata (Phase 2) |
| `operator_output.md` | Markdown | ✅ Deterministic | Operator report (Phase 2) |
| `proposer_output.json` | JSON (sorted keys) | ✅ Deterministic | Proposer model output |
| `critic_output.json` | JSON (sorted keys) | ✅ Deterministic | Critic model output |
| `sod_check.json` | JSON (sorted keys) | ✅ Deterministic | SoD validation result |
| `capability_scope_check.json` | JSON (sorted keys) | ✅ Deterministic | Capability scope validation |

### 12.2 Determinism Guarantees

**For CI and Replay Mode:**

1. **Stable JSON Key Ordering:** All JSON files use `sort_keys=True`
2. **Hash-based Run IDs:** `run_id = SHA256(layer + models + scope)`
3. **Injected Timestamps:** Clock can be fixed via `clock=datetime(...)`
4. **Deterministic Content Hashing:** `output_hash = SHA256(content)`
5. **No Network Calls:** ReplayClient uses pre-recorded fixtures
6. **No Secrets:** API keys never appear in artifacts

**Example (Golden Snapshot):**

```python
from datetime import datetime, timezone
from src.ai_orchestration import EvidencePackGenerator

# Fixed clock for determinism
clock = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
generator = EvidencePackGenerator(clock=clock)

# Generate evidence pack
artifacts = generator.generate(...)

# Verify determinism
with open(artifacts["evidence_pack"]) as f:
    data = json.load(f)
    assert data["creation_timestamp"] == "2026-01-10T12:00:00+00:00"
    assert list(data.keys()) == sorted(data.keys())  # Stable ordering
```

### 12.3 Content Redaction

**Sensitive Fields (Future):**
- PII removal (names, emails)
- Secret redaction (API keys, tokens)
- Output truncation (max length)

**Current Implementation:** Pass-through (no redaction)

**Extension Point:** `EvidencePackGenerator._redact_content()`

---

## 13. Change Log

- **v1.0 (2026-01-10):** Initial Phase 3 Spec
  - Threat Model
  - Record/Replay Strategy
  - Network Opt-In Policy
  - Evidence Pack Schema
  - SoD + Capability Scope Rules
  - 30-Day Pilot Evaluation Plan
- **v1.1 (2026-01-10):** Added Artifact Structure & Determinism Guarantees
  - Evidence Pack artifacts table
  - Determinism guarantees (golden snapshot example)
  - Content redaction extension point

---

**STATUS:** ✅ Phase 3 Spec Complete + Evidence Pack Generator Implemented  
**NEXT:** Implementation (L2Runner, CLI, Integration Tests)
