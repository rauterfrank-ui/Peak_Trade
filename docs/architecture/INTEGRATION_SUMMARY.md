# AI Autonomy Layer Map – Integration Summary

**Datum:** 2026-01-08  
**Status:** Phase 1 Complete (Doc + Schema)  
**Nächste Phase:** Phase 2 (SoD Framework Implementation)

---

## Was wurde erstellt (Phase 1)

### 1. Authoritative Spezifikationen

| Dokument | Pfad | Zweck |
|---|---|---|
| **Layer Map Matrix** ⚠️ | `docs/governance/ai_autonomy/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md` | **AUTHORITATIVE:** Single source of truth für Layer→Model Assignments |
| **Layer Map v1** | `docs/architecture/ai_autonomy_layer_map_v1.md` | Detailed Spec: 7 Layer (L0-L6), Modellzuweisung, SoD, Safety-First |
| **Gap-Analyse** | `docs/architecture/ai_autonomy_layer_map_gap_analysis.md` | Gap-Analyse, Bestands-Assessment, 7-Phasen Roadmap |
| **Integration Summary** | `docs/architecture/INTEGRATION_SUMMARY.md` | Dieses Dokument: Zusammenfassung + Next Steps |

---

### 2. Capability Scope Schemas (Config)

| Layer | Datei | Beschreibung |
|---|---|---|
| **L0** | `config/capability_scopes/L0_ops_docs.toml` | Ops/Docs: Runbooks, Checklisten (REC, Files only) |
| **L1** | `config/capability_scopes/L1_deep_research.toml` | DeepResearch: Literatur, Evidenz (PROP, Web + Files) |
| **L2** | `config/capability_scopes/L2_market_outlook.toml` | Market Outlook: Makro/Szenarien (PROP, Web optional) |
| **L4** | `config/capability_scopes/L4_governance_critic.toml` | Governance Critic: Policy Checks (RO/REC, Files only) |

**Hinweis:** L3, L5, L6 folgen in Phase 5/6 (siehe Roadmap).

---

### 3. Model Registry (Authoritative)

| Datei | Beschreibung |
|---|---|
| **Model Registry** | `config/model_registry.toml` | Alle Modelle (OpenAI + DeepSeek), Layer-to-Model Mapping, Fallback Rules, Cost/Budget Tracking, Audit Config |

**Enthält:**
- OpenAI: `gpt-5.2-pro`, `gpt-5.2`, `gpt-5-mini`, `o3-deep-research`, `o3-pro`, `o3`, `o4-mini-deep-research`
- DeepSeek: `deepseek-r1` (heterogener Verifier)
- Layer-to-Model Mapping (L0-L6)
- Fallback Policy (Fail-Closed)
- Budget Tracking (Daily/Monthly Limits)
- Audit Logging Config

---

### 4. Evidence Pack Template v2 (Layer-Map kompatibel)

| Datei | Beschreibung |
|---|---|
| **Evidence Pack Template v2** | `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md` | Erweitert um: `layer_id`, `model_id`, `capability_scope_id`, SoD Check Status, Run Artifacts (Hashes, Run IDs) |

**Neu in v2:**
- Metadata Section: Layer Info, Model Assignment, SoD Status
- Run Artifacts: Proposer/Critic Run IDs, Artifact Hashes
- Layer-Specific Compliance: Inputs/Outputs/Tooling Validation
- Capability Scope Enforcement Checklist

---

## Integration mit bestehenden Komponenten

### ✅ Bereits kompatibel (keine Änderung nötig)

1. **Execution Orchestrator** (`src/execution/orchestrator.py`) → L6 (Execution)
   - Bereits **EXEC (forbidden)** mit `GovernanceViolationError`
   - Keine Änderung nötig

2. **Risk Hook / Kill Switch** (`src/execution/risk_hook.py`, `src&#47;killswitch&#47;`) → L5 (Risk Gate)
   - Deterministisch, kein LLM
   - Keine Änderung nötig

3. **Evidence Schema** (`docs/ops/EVIDENCE_SCHEMA.md`)
   - Direkt kompatibel mit Layer Map
   - Keine Änderung nötig

---

### 🟡 Erweiterung erforderlich (Phase 2-4)

1. **Policy Critic** (`src/governance/policy_critic/`) → L4 (Governance Critic)
   - **Erforderlich:** `model_id` Logging, SoD Check Integration
   - **Phase:** Phase 2 (SoD Framework)

2. **Market Sentinel** (`src/market_sentinel/v0_daily_outlook.py`) → L2 (Market Outlook)
   - **Erforderlich:** Capability Scope Enforcement, Multi-Model Support (Proposer + Critic)
   - **Phase:** Phase 3 (L2 Pilot)

3. **InfoStream / Knowledge API** (`src/meta/infostream/`, `src/knowledge/`) → L1/L2 Context
   - **Erforderlich:** Layer-aware Logging
   - **Phase:** Phase 4 (L1 Integration)

---

### ❌ Neu zu implementieren (Phase 2-7)

1. **Multi-Model Orchestration Framework** (`src/ai_orchestration/`)
   - **Phase 2:** `ProposerCriticRunner`, `SoDChecker`, Logging
   - **Priority:** 🔴 HIGH (P0)

2. **DeepResearch Runner** ("DeepResearch Runner" (Phase 3+))
   - **Phase 4:** L1 DeepResearch mit `o3-deep-research` API
   - **Priority:** 🟡 MEDIUM (P1)

3. **Trade Plan Advisor** ("Trade Plan Advisor" (Phase 3+))
   - **Phase 5:** L3 Intraday Hypothesen (Files only, REC/PROP)
   - **Priority:** 🟡 MEDIUM (P1)

4. **Runbook Generator** ("Runbook Generator" (Phase 3+))
   - **Phase 5:** L0 Docs/Runbooks (Repo-Text only)
   - **Priority:** 🟢 LOW (P2)

---

## Nächste Schritte (unmittelbar)

### Phase 2 (Diese Woche): SoD Framework

**Ziel:** Multi-Model Orchestration mit SoD Checks implementieren.

**Tasks:**
1. Erstelle `src/ai_orchestration/` Modul
2. Implementiere `ProposerCriticRunner` (orchestriert 2 Models)
3. Implementiere `SoDChecker` (validiert unterschiedliche `model_id`)
4. Logging: `run_id`, `model_id`, `prompt_hash`, `artifact_hash`
5. Tests: `tests/ai_orchestration/test_sod_checker.py`, `test_multi_model_runner.py`

**Erfolgskriterien:**
- ✅ SoD Check erkennt gleiche `model_id` (FAIL)
- ✅ SoD Check akzeptiert unterschiedliche `model_id` (PASS)
- ✅ Logging enthält alle Pflichtfelder
- ✅ Tests grün (100% Coverage für SoD Logic)

---

## Operator Checkliste (Vor Phase 2 Start)

- [ ] **Review:** Layer Map v1 + Gap-Analyse gelesen und verstanden
- [ ] **Approval:** Freigabe für Phase 2 (SoD Framework Implementation)
- [ ] **Config Validation:** TOML Syntax Check für Capability Scopes + Model Registry
- [ ] **Dependencies:** Prüfe OpenAI API Access (o3-deep-research, gpt-5.2-pro)
- [ ] **Budget:** Daily/Monthly Cost Limits festlegen (aktuell: $50/day, $1000/month)
- [ ] **Alerts:** Alert Channels konfigurieren (ops-safety, governance-safety, market-outlook-safety)
- [ ] **Roles:** Wer arbeitet an Phase 2? (Agent Allocation)

---

## Validation Commands (jetzt ausführbar)

```bash
# 1. TOML Syntax Check (alle Capability Scopes + Model Registry)
python3 -c "import tomli; [tomli.load(open(f, 'rb')) for f in ['config/model_registry.toml', 'config/capability_scopes/L0_ops_docs.toml', 'config/capability_scopes/L1_deep_research.toml', 'config/capability_scopes/L2_market_outlook.toml', 'config/capability_scopes/L4_governance_critic.toml']]" && echo "✅ TOML Syntax: PASS"

# 2. Model Registry: Check Layer Mapping Completeness
python3 -c "
import tomli
reg = tomli.load(open('config/model_registry.toml', 'rb'))
layers = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6']
missing = [l for l in layers if l not in reg['layer_mapping']]
print('✅ Layer Mapping Complete' if not missing else f'❌ Missing: {missing}')
"

# 3. Capability Scope: Check required fields
python3 -c "
import tomli
from pathlib import Path
scopes = list(Path('config/capability_scopes').glob('*.toml'))
required = ['scope', 'models', 'inputs', 'outputs', 'tooling', 'logging', 'safety']
for s in scopes:
    cfg = tomli.load(open(s, 'rb'))
    missing = [r for r in required if r not in cfg]
    print(f'{s.name}: {'✅ OK' if not missing else f'❌ Missing: {missing}'}')
"
```

---

## Risiken & Mitigations (Phase 2)

| Risk | Impact | Mitigation |
|---|---|---|
| **Model API Unavailable** (o3-deep-research Outage) | 🔴 HIGH | Fallback Models implementiert in Model Registry |
| **SoD Implementation Bug** (Proposer == Critic nicht erkannt) | 🔴 HIGH | 100% Test Coverage für SoD Logic + Manual Review |
| **Logging Overhead** (zu viele Logs, Performance Impact) | 🟡 MEDIUM | Async Logging, Log Rotation, Budget Monitoring |
| **Config Drift** (Capability Scope vs Code mismatch) | 🟡 MEDIUM | Runtime Enforcement (Phase 2), Schema Validation Tests |

---

## Success Metrics (Phase 2)

- ✅ SoD Framework implementiert (3 Module: `multi_model_runner`, `sod_checker`, `models`)
- ✅ Tests grün (100% Coverage für SoD)
- ✅ Logging funktioniert (`logs&#47;ai_model_calls.jsonl` vorhanden)
- ✅ Ready für Phase 3 (L2 Pilot)

---

## Referenzen

- **Layer Map v1:** `docs/architecture/ai_autonomy_layer_map_v1.md`
- **Gap-Analyse:** `docs/architecture/ai_autonomy_layer_map_gap_analysis.md`
- **Model Registry:** `config/model_registry.toml`
- **Capability Scopes:** `config&#47;capability_scopes&#47;*.toml`
- **Evidence Pack Template v2:** `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md`

---

**STATUS:** Phase 1 Complete ✅  
**NEXT:** Phase 2 (SoD Framework) – Waiting for Operator Approval

---

**END OF DOCUMENT**
