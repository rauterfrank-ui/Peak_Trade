# AI Autonomy Layer Map – Gap-Analyse & Integrationsstrategie

**Datum:** 2026-01-08  
**Status:** Gap-Analyse v1  
**Bezug:** `docs/architecture/ai_autonomy_layer_map_v1.md`

---

## Executive Summary

Die **AI Autonomy Layer Map v1** definiert 7 Layer (L0-L6) mit klarer Modellzuweisung, SoD-Prinzipien und Safety-First Guardrails. Diese Gap-Analyse identifiziert bestehende Komponenten, fehlende Teile und schlägt eine phasenweise Integrationsstrategie vor.

**Hauptergebnis:** ~60% der Foundations existieren bereits (Evidence Packs, Policy Critic, Execution Orchestrator). Die Hauptlücken sind Multi-Model Orchestration, Layer-spezifische Capability Scopes und die Integration in den GoNoGo-Prozess.

---

## 1) Bestehende Komponenten (✅ Vorhanden)

### 1.1 Evidence Pack Infrastructure

| Komponente | Pfad | Status | Kompatibilität mit Layer Map |
|---|---|---|---|
| Evidence Pack Template | `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE.md` | ✅ Vorhanden | 🟡 Muss erweitert werden um `layer_id`, `model_id`, `capability_scope_id` |
| Evidence Schema | `docs/ops/EVIDENCE_SCHEMA.md` | ✅ Vorhanden | 🟢 Direkt kompatibel |
| Evidence Index | `docs/audit/EVIDENCE_INDEX.md`, `docs/ops/EVIDENCE_INDEX.md` | ✅ Vorhanden | 🟢 Direkt kompatibel |

**Action Items:**
- Erweitere Evidence Pack Template um Layer-Map Felder (siehe Abschnitt 3.1)

---

### 1.2 Governance & Policy Critic

| Komponente | Pfad | Status | Mapping zu Layer Map |
|---|---|---|---|
| LLM Policy Critic Charter | `docs/governance/LLM_POLICY_CRITIC_CHARTER.md` | ✅ Vorhanden | 🟢 Entspricht **L4 Governance / Policy Critic** |
| Policy Critic Implementation | `src/governance/policy_critic/` | ✅ Vorhanden | 🟢 Deterministischer Teil von L4 |
| Policy Packs | `policy_packs&#47;*.yml` | ✅ Vorhanden | 🟢 Kann für Layer-spezifische Rules erweitert werden |

**Erkenntnisse:**
- Der bestehende Policy Critic ist **read-only** und **evidence-based** → perfekt für L4
- Proposer/Critic Separation ist konzeptionell vorhanden, aber **nicht explizit** multi-model orchestriert
- **Gap:** Keine explizite `model_id` Tracking oder SoD Checks in Code

**Action Items:**
- Ergänze Policy Critic um `model_id` Logging
- Implementiere SoD Check Funktion (siehe Abschnitt 3.2)

---

### 1.3 Execution Pipeline (L6 Reference)

| Komponente | Pfad | Status | Mapping zu Layer Map |
|---|---|---|---|
| Execution Orchestrator | `src/execution/orchestrator.py` | ✅ Vorhanden | 🟢 Entspricht **L6 Execution** |
| Risk Hook | `src/execution/risk_hook.py` | ✅ Vorhanden | 🟢 Entspricht **L5 Risk Gate** |
| Kill Switch | `src&#47;killswitch&#47;` | ✅ Vorhanden | 🟢 Teil von L5 |

**Erkenntnisse:**
- L6 ist korrekt als **EXEC (forbidden)** markiert → `GovernanceViolationError` bei Live
- L5 ist deterministisch (kein LLM) → Layer Map korrekt
- **Gap:** Keine explizite Referenz auf Layer Map in Execution Code

**Action Items:**
- Dokumentiere Layer-Mapping in Execution-Docs
- Keine Code-Änderung nötig (bereits compliant)

---

### 1.4 Market Outlook & Research (L1/L2 Foundations)

| Komponente | Pfad | Status | Mapping zu Layer Map |
|---|---|---|---|
| Market Sentinel (Daily Outlook) | `src/market_sentinel/v0_daily_outlook.py` | ✅ Vorhanden | 🟡 Teilweise L2, aber **nicht Layer-aware** |
| Knowledge API Manager | `src/knowledge/api_manager.py` | ✅ Vorhanden | 🟡 Kann für L1 DeepResearch genutzt werden |
| InfoStream (Intel Evaluation) | `src/meta/infostream/evaluator.py` | ✅ Vorhanden | 🟡 Relevant für L2/L3 Context |

**Erkenntnisse:**
- Market Sentinel nutzt bereits OpenAI API (`call_llm()`) → Basis für L2
- **Gap:** Keine explizite Capability Scope Enforcement
- **Gap:** Keine Multi-Model Orchestration (nur ein Model pro Run)
- **Gap:** Keine SoD (Proposer/Critic) in Research/Outlook

**Action Items:**
- Erweitere Market Sentinel um Capability Scope Config
- Implementiere Multi-Model Support (Proposer + Critic)

---

## 2) Fehlende Komponenten (❌ Gaps)

### 2.1 Layer-spezifische Capability Scopes

**Gap:** Es gibt **keine** formale Definition von Capability Scopes als Config-Dateien.

**Erforderlich:**
- Schema: `config&#47;capability_scopes&#47;*.toml`
- Enforcement: Runtime Check vor Layer-Runs

**Beispiel (fehlt):**
```toml
[capability_scope.L2_market_outlook_v1]
layer_id = "L2"
inputs_allowed = ["docs/market_outlook/**/*.yaml", "config/macro_regimes/**/*.toml"]
outputs_allowed = ["ScenarioReport", "RegimeClassification", "NoTradeTriggers"]
tooling_allowed = ["files", "web"]
forbidden = ["Order senden", "Risk Limits ändern", "Secrets anfassen"]
```

**Priorität:** 🔴 HIGH (P0) – Notwendig für Safety-First Garantien

**Action Items:** Siehe Abschnitt 3.3

---

### 2.2 Multi-Model Orchestration Framework

**Gap:** Es gibt **keine** Infrastruktur für:
- Explizite Proposer/Critic Model Orchestration
- SoD Checks (unterschiedliche `model_id` enforcement)
- Logging von `model_id`, `prompt_hash`, `artifact_hash` per Run

**Erforderlich:**
- Modul: "Multi-Model Runner" (Phase 3+)
- SoD Checker: "SoD Checker" (Phase 3+)
- Model Registry: `config/model_registry.toml`

**Priorität:** 🔴 HIGH (P0) – Core für Layer Map v1

**Action Items:** Siehe Abschnitt 3.4

---

### 2.3 Layer-Map Integration in GoNoGo Prozess

**Gap:** Die bestehenden GoNoGo Docs (z.B. `docs/governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md`) erwähnen **nicht** die Layer Map explizit.

**Erforderlich:**
- Aktualisiere GoNoGo Docs mit Layer-Map Referenzen
- CodeGate muss Evidence Packs mit `layer_id` + `model_id` validieren

**Priorität:** 🟡 MEDIUM (P1) – Wichtig für Operator Clarity

**Action Items:** Siehe Abschnitt 3.5

---

### 2.4 Model API Wrappers (o3-deep-research, DeepSeek-R1)

**Gap:** Derzeit nur OpenAI-Integration vorhanden (`src/market_sentinel/v0_daily_outlook.py`).

**Fehlend:**
- `o3-deep-research` API Wrapper
- `DeepSeek-R1` API Wrapper (local oder API)
- Model Fallback Logic

**Priorität:** 🟡 MEDIUM (P1) – Kann schrittweise nachgerüstet werden

**Action Items:** Siehe Abschnitt 3.6

---

## 3) Implementierungs-Roadmap (Phase-by-Phase)

### Phase 1 (P0, Woche 1): Schema & Config Foundation

**Ziel:** Capability Scopes und Model Registry als Config definieren.

**Tasks:**
1. Erstelle `config/capability_scopes/` Verzeichnis
2. Definiere Schemas für L0-L6 (je eine `.toml` Datei)
3. Erstelle `config/model_registry.toml` mit Primary/Fallback/Critic Models
4. Erweitere Evidence Pack Template um Layer-Map Felder

**Deliverables:**
- `config&#47;capability_scopes&#47;*.toml` (7 Dateien)
- `config/model_registry.toml`
- `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE.md` (updated)

**Tests:**
- TOML Syntax Validation
- Schema Vollständigkeit Check

---

### Phase 2 (P0, Woche 2): SoD Framework

**Ziel:** Multi-Model Orchestration mit SoD Checks implementieren.

**Tasks:**
1. Erstelle `src/ai_orchestration/` Modul
2. Implementiere `ProposerCriticRunner` (orchestriert 2 Models)
3. Implementiere `SoDChecker` (validiert unterschiedliche `model_id`)
4. Logging: `run_id`, `model_id`, `prompt_hash`, `artifact_hash`

**Deliverables:**
- "Multi-Model Runner" (Phase 3+)
- "SoD Checker" (Phase 3+)
- `src/ai_orchestration/models.py` (Dataclasses)

**Tests:**
- `tests/ai_orchestration/test_sod_checker.py`
- `tests&#47;ai_orchestration&#47;test_multi_model_runner.py`

---

### Phase 3 (P0, Woche 3): Layer 2 Pilot (Market Outlook)

**Ziel:** L2 Market Outlook als erster Layer mit Layer-Map Compliance.

**Tasks:**
1. Erweitere `src/market_sentinel/v0_daily_outlook.py` um Capability Scope Enforcement
2. Integriere `ProposerCriticRunner` (GPT-5.2 pro als Proposer, DeepSeek-R1 als Critic)
3. Generiere Evidence Packs mit `layer_id=L2`, `model_id`, `capability_scope_id`

**Deliverables:**
- Updated `src/market_sentinel/v0_daily_outlook.py`
- Erstes Evidence Pack: "L2 Pilot Evidence Pack" (Phase 3+)

**Tests:**
- `tests&#47;market_sentinel&#47;test_layer_compliance.py`
- Manuelle Pilot-Runs (3-5 Tage)

---

### Phase 4 (P1, Woche 4): Layer 1 & Layer 4 Integration

**Ziel:** L1 DeepResearch und L4 Governance Critic integrieren.

**Tasks:**
1. Implementiere L1 DeepResearch Wrapper (`o3-deep-research` API)
2. Erweitere Policy Critic um `model_id` Logging und SoD Support
3. Integriere L4 in CodeGate Pipeline

**Deliverables:**
- "DeepResearch Runner" (Phase 3+)
- Updated `src/governance/policy_critic/critic.py`
- "CodeGate Layer Map Integration" (Phase 3+)

**Tests:**
- `tests&#47;research&#47;test_deep_research_runner.py`
- `tests&#47;governance&#47;test_policy_critic_layer_compliance.py`

---

### Phase 5 (P1, Woche 5-6): Layer 0 & Layer 3 (Docs + Trade Plan Advisory)

**Ziel:** Vollständige Layer-Map Abdeckung für Read-Only/Advisory Layers.

**Tasks:**
1. L0 Ops/Docs: Runbook-Generator mit Capability Scope
2. L3 Trade Plan Advisory: Intraday Hypothesen-Generator (Files only, REC/PROP)

**Deliverables:**
- "Runbook Generator" (Phase 3+) (L0)
- "Trade Plan Advisor" (Phase 3+) (L3)

**Tests:**
- `tests&#47;ops&#47;test_runbook_generator_layer_compliance.py`
- `tests&#47;trading&#47;test_trade_plan_advisor_layer_compliance.py`

---

### Phase 6 (P2, Woche 7-8): Model Fallbacks & Heterogene Verification

**Ziel:** DeepSeek-R1 und Fallback-Models operationalisieren.

**Tasks:**
1. Implementiere DeepSeek-R1 API Wrapper (lokal oder API)
2. Fallback-Logik: Proposer fällt auf Fallback Model zurück bei Failure
3. Heterogene Verification: DeepSeek-R1 als Critic für OpenAI Proposer

**Deliverables:**
- "DeepSeek-R1 Wrapper" (Phase 3+)
- "OpenAI Wrapper" (Phase 3+)
- Fallback Tests

**Tests:**
- `tests&#47;ai_orchestration&#47;test_model_fallbacks.py`
- `tests&#47;ai_orchestration&#47;test_heterogeneous_verification.py`

---

### Phase 7 (P2, Woche 9-10): 30-Day Pilot & Evaluation

**Ziel:** L1 + L2 + L4 im 30-Tage Pilot, Evaluation, Go/NoGo für L3.

**Tasks:**
1. Tägliche Runs: L2 Market Outlook + L1 Research (bei Bedarf)
2. Policy Critic (L4) bei jeder Config-Änderung
3. Sammle Metriken: SoD Pass Rate, False Positives, Operator Feedback
4. Go/NoGo Review für L3 (Trade Plan Advisory)

**Deliverables:**
- "30-Day Pilot Report" (Phase 3+)
- Go/NoGo Decision Document für L3

**Tests:**
- Retrospektive: Lessons Learned
- Operator Umfrage

---

## 4) Risk & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **Model API Unavailability** (z.B. o3-deep-research Outage) | 🔴 HIGH | Fallback Models (GPT-5.2, o4-mini, DeepSeek-R1) + Fail-Closed |
| **SoD False Positives** (zu viele REJECT bei validen Proposals) | 🟡 MEDIUM | Kalibrierung über Pilot, Operator-Feedback Loop |
| **Capability Scope Bypasses** (Layer greift auf verbotene Tools zu) | 🔴 HIGH | Runtime Enforcement + Audit Logging + Alert bei Violation |
| **Model Drift** (neue Model Versions ändern Verhalten) | 🟡 MEDIUM | Model Version Pinning + Regression Tests |
| **Operator Confusion** (zu viele Layer, zu komplex) | 🟡 MEDIUM | Klare Docs, Runbooks, Layer-specific Checklists |

---

## 5) Success Criteria (Phase 7 Go/NoGo)

**Go für L3 (Trade Plan Advisory), wenn:**
1. ✅ L1 + L2 laufen seit 30 Tagen ohne Safety Violations
2. ✅ SoD Pass Rate > 95% (weniger als 5% False Rejects)
3. ✅ Capability Scope Violations = 0 (Runtime Enforcement funktioniert)
4. ✅ Operator Feedback: "hilfreich, nicht störend"
5. ✅ Alle Evidence Packs haben `layer_id`, `model_id`, `capability_scope_id`
6. ✅ CodeGate integriert Layer-Map Validierung

**NoGo Bedingungen:**
- Jede Safety Violation (z.B. L2 versucht Order zu senden)
- Capability Scope Bypass (z.B. L3 greift auf Web zu, obwohl verboten)
- SoD Check Failures (z.B. Proposer == Critic Model)

---

## 6) Nächste Schritte (sofort)

### Operator Action Items (diese Woche)

1. **Review & Approval:** Prüfe diese Gap-Analyse und Layer Map v1
2. **Kick-off Phase 1:** Freigabe für Capability Scope Schemas (siehe Phase 1 Tasks)
3. **Resource Allocation:** Welche Agents/Roles arbeiten an welchen Phasen?

### Agent Action Items (sofort nach Approval)

1. **Phase 1 Task 1-4:** Erstelle Schemas (siehe Abschnitt 3.1-3.3)
2. **Tests:** TOML Syntax Validation
3. **Docs:** Erweitere Evidence Pack Template

---

## 7) Referenzen

- Layer Map v1: `docs/architecture/ai_autonomy_layer_map_v1.md`
- Evidence Pack Template: `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE.md`
- LLM Policy Critic Charter: `docs/governance/LLM_POLICY_CRITIC_CHARTER.md`
- GoNoGo Overview: `docs/governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md`
- Execution Orchestrator: `src/execution/orchestrator.py`
- Market Sentinel: `src/market_sentinel/v0_daily_outlook.py`

---

**END OF DOCUMENT**
