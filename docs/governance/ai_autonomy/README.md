# AI Autonomy Governance

**Purpose:** Authoritative governance documentation for AI autonomy in Peak_Trade.

---

## Authoritative Documents

### ⚠️ AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md

**Status:** AUTHORITATIVE (Single Source of Truth)  
**Purpose:** Layer→Model Assignment Matrix

Dieses Dokument ist die **verbindliche Referenz** für:
- Layer-Definitionen (L0-L6)
- Autonomiestufen (RO/REC/PROP/EXEC)
- Model-Zuordnungen (Primary/Fallback/Critic)
- Tool-Access pro Layer
- Hard Constraints
- SoD Rules

**Alle Evidence Packs MÜSSEN auf diese Matrix referenzieren.**

---

## Usage

### For Evidence Pack Authors

Wenn Sie ein Evidence Pack erstellen:

1. **Lesen Sie die Matrix:** `AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md`
2. **Verwenden Sie das Template:** `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md`
3. **Referenzieren Sie:**
   - `layer_id` aus der Matrix
   - `primary_model_id` aus der Matrix
   - `critic_model_id` aus der Matrix
   - `autonomy_level` aus der Matrix
4. **Validieren Sie:** SoD Check PASS (Proposer ≠ Critic)

### For CodeGate Integration

CodeGate prüft Evidence Packs gegen die Matrix:
- Layer ID existiert (L0-L6)
- Primary Model entspricht Matrix-Zuordnung
- Critic Model ≠ Primary Model (SoD)
- Autonomy Level entspricht Matrix
- Hard Constraints eingehalten

---

## Related Documentation

### Detailed Specifications
- `docs/architecture/ai_autonomy_layer_map_v1.md` - Detaillierte Spec mit Design-Prinzipien
- `docs/architecture/ai_autonomy_layer_map_gap_analysis.md` - Gap-Analyse + Roadmap
- `docs/architecture/INTEGRATION_SUMMARY.md` - Integration Status + Next Steps

### Configuration
- `config/model_registry.toml` - Detaillierte Model Specs, Budget, Audit
- `config&#47;capability_scopes&#47;*.toml` - Layer-spezifische Enforcement Rules

### Governance
- `docs/governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md` - GoNoGo Prozess
- `docs/governance/LLM_POLICY_CRITIC_CHARTER.md` - Policy Critic Charter (L4)
- `.cursor/rules/peak-trade-governance.mdc` - Governance Guardrails

### Operations & Runbooks
- [AI Autonomy Runbook (Phase 4B · M2)](../../ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M2_CURSOR_MULTI_AGENT.md) - Phase 4B Milestone 2: Cursor Multi-Agent Evidence-First Operator Loop (standardized workflow for Layer Runs with Evidence Pack creation and validation)

---

## Change Control

**Änderungen an der Authoritative Matrix erfordern:**
1. Owner Approval
2. Evidence Pack Updates (alle referenzierenden Packs)
3. CodeGate Re-Validation
4. Version Bump + Changelog Entry

**Aktuelle Version:** v1.0 (2026-01-08)

---

## Questions?

Siehe:
- Integration Summary: `docs/architecture/INTEGRATION_SUMMARY.md`
- Phase Summary: `PHASE_AI_AUTONOMY_LAYER_MAP_V1_SUMMARY.md`
