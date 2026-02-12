# AI Autonomy Layer Map – Quickstart

**Für:** Operators, Evidence Pack Authors, Integration Engineers

---

## 1-Minute Overview

**Peak_Trade AI Autonomy Layer Map:**
- **7 Layer (L0-L6):** Ops/Docs → DeepResearch → Market Outlook → Trade Plan Advisory → Governance Critic → Risk Gate → Execution
- **Safety-First:** Execution (L6) bleibt verboten bis Evidence Packs + CodeGate + Go/NoGo
- **Separation of Duties (SoD):** Proposer ≠ Critic (unterschiedliche Modelle)
- **Authoritative Matrix:** `AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md` ist single source of truth

---

## Quick Reference

### Layer Overview (Compact)

| Layer | Name | Autonomy | Primary Model | Critic | Tools |
|---|---|---|---|---|---|
| L0 | Ops/Docs | REC | gpt-5.2 | deepseek-r1 | files |
| L1 | DeepResearch | PROP | o3-deep-research | o3-pro | web, files |
| L2 | Market Outlook | PROP | gpt-5.2-pro | deepseek-r1 | web?, files |
| L3 | Trade Plan Advisory | REC/PROP | gpt-5.2-pro | o3 | files |
| L4 | Governance Critic | RO/REC | o3-pro | gpt-5.2-pro | files |
| L5 | Risk Gate | RO | (kein LLM) | — | — |
| L6 | Execution | EXEC | (verboten) | — | — |

---

## 5-Minute Walkthrough

### Step 1: Read the Authoritative Matrix

```bash
cat docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md
```

**Key Sections:**
- AUTHORITATIVE MATRIX (Tabelle mit allen 7 Layern)
- MODEL SPECIFICATIONS (8 Modelle: OpenAI + DeepSeek)
- SEPARATION OF DUTIES (SoD Rules)
- EVIDENCE PACK INTEGRATION (wie Evidence Packs die Matrix referenzieren)

---

### Step 2: Validate Configuration

```bash
python3 scripts/validate_layer_map_config.py
```

**Should output:**
```
✅ model_registry.toml: Syntax VALID
✅ All 7 layers mapped (L0-L6)
✅ All 8 models defined
✅ L0_ops_docs.toml: All required sections present
✅ L1_deep_research.toml: All required sections present
✅ L2_market_outlook.toml: All required sections present
✅ L4_governance_critic.toml: All required sections present
✅ VALIDATION PASSED: All configurations valid
```

---

### Step 3: Create an Evidence Pack (Example: L2 Market Outlook)

1. **Copy Template:**
   ```bash
   cp docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md \
      docs/governance/evidence/EVP_20260108_L2_OUTLOOK_001.md
   ```

2. **Fill in Metadata (from Matrix):**
   ```markdown
   **Evidence Pack ID:** EVP_20260108_L2_OUTLOOK_001
   **Layer ID:** L2
   **Layer Name:** Market Outlook
   **Autonomy Level:** PROP
   **Primary Model:** gpt-5.2-pro
   **Fallback Model:** gpt-5.2
   **Critic Model:** deepseek-r1
   **SoD Check:** PASS
   **Matrix Version:** v1.0 (2026-01-08)
   **Capability Scope:** config/capability_scopes/L2_market_outlook.toml
   ```

3. **Run Layer Logic:**
   ```bash
   # Example: Run Market Outlook with Proposer + Critic
   python3 src/market_sentinel/v0_daily_outlook.py --layer L2 \
     --primary-model gpt-5.2-pro \
     --critic-model deepseek-r1 \
     --evidence-pack-id EVP_20260108_L2_OUTLOOK_001
   ```

4. **Validate SoD:**
   ```python
   # In your runner code:
   from src.ai_orchestration.sod_checker import check_sod

   result = check_sod(
       proposer_run_id="run_abc123",
       proposer_model_id="gpt-5.2-pro",
       critic_run_id="run_def456",
       critic_model_id="deepseek-r1"
   )
   assert result.status == "PASS"  # gpt-5.2-pro ≠ deepseek-r1
   ```

---

### Step 4: CodeGate Validation (Future)

**CodeGate checks Evidence Pack against Matrix:**
```python
# Pseudocode (Phase 4 implementation)
from src.governance.codegate import validate_evidence_pack

validation = validate_evidence_pack("docs/governance/evidence/EVP_20260108_L2_OUTLOOK_001.md")

assert validation.layer_id_valid  # L2 exists in Matrix
assert validation.model_assignment_valid  # gpt-5.2-pro is L2 Primary
assert validation.sod_valid  # gpt-5.2-pro ≠ deepseek-r1
assert validation.autonomy_valid  # PROP is L2 Autonomy
assert validation.status == "APPROVED"
```

---

## Common Tasks

### Task: Check which Model to use for Layer X

```bash
# Read Matrix
grep "L2" docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md

# Or use config
python3 -c "
import tomli
reg = tomli.load(open('config/model_registry.toml', 'rb'))
layer = reg['layer_mapping']['L2']
print(f'Layer L2: Primary={layer[\"primary\"]}, Critic={layer[\"critic\"]}')
"
```

---

### Task: Verify SoD Compliance

```python
# In your code
proposer_model = "gpt-5.2-pro"
critic_model = "deepseek-r1"

if proposer_model == critic_model:
    raise ValueError("SoD FAIL: Proposer == Critic")
else:
    print(f"SoD PASS: {proposer_model} ≠ {critic_model}")
```

---

### Task: Check Capability Scope for Layer

```bash
# Read Capability Scope
cat config/capability_scopes/L2_market_outlook.toml

# Check inputs_allowed, outputs_forbidden, tooling_allowed
```

---

## Phase Roadmap (Cliff Notes)

| Phase | Status | Key Deliverable |
|---|---|---|
| Phase 1 | ✅ Complete | Docs + Schemas (diese Files) |
| Phase 2 | 🔜 Next | SoD Framework (`src/ai_orchestration/`) |
| Phase 3 | 📅 Week 3 | L2 Pilot (Market Outlook) |
| Phase 4 | 📅 Week 4 | L1 + L4 Integration |
| Phase 5 | 📅 Week 5-6 | L0 + L3 |
| Phase 6 | 📅 Week 7-8 | Model Fallbacks + DeepSeek-R1 |
| Phase 7 | 📅 Week 9-10 | 30-Day Pilot + Go/NoGo |

---

## Emergency Contacts

**Fragen zur Matrix:**
- Owner: ops
- Docs: `docs/architecture/INTEGRATION_SUMMARY.md`

**Fragen zu Evidence Packs:**
- Template: `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md`
- Examples: `docs/governance/evidence/` (nach Phase 3)

**Fragen zu Implementation:**
- Gap-Analyse: `docs/architecture/ai_autonomy_layer_map_gap_analysis.md`
- Phase Summary: `PHASE_AI_AUTONOMY_LAYER_MAP_V1_SUMMARY.md`

---

## Red Flags 🚨

**STOP und frage nach, wenn:**
1. Evidence Pack referenziert **nicht** die Matrix (`AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md`)
2. Proposer Model == Critic Model (SoD FAIL)
3. Layer L6 (Execution) wird "enabled" ohne Go/NoGo Freigabe
4. Capability Scope wird ignoriert (z.B. L3 greift auf Web zu, obwohl verboten)
5. Model ID existiert nicht in `config/model_registry.toml`

---

**Ready to start?**  
→ Phase 2 Kick-off: `docs/architecture/INTEGRATION_SUMMARY.md` (Next Steps Section)
